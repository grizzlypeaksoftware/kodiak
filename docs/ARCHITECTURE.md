# Kodiak Architecture (v0.1)

> **Status: APPROVED 2026-09-23** (v0.1 design). Nothing here is implemented beyond the request/response schema yet.
> Every sizing number below is an estimate until Phase 3 measures it on the DGX Spark.

## 1. Goals and constraints

Kodiak is a "System One" decision model: a fast, single-pass answer to a set of typed questions about a state.

| Requirement | How this design meets it |
|---|---|
| Input: state (text, list, or JSON) + typed questions | `render_state()` serializes the state; questions are packed after it (§3) |
| All questions answered in **one forward pass** | One packed sequence, with a structured attention mask (§4) |
| State encoded **once** | State tokens never attend to question tokens, so their representations don't depend on the questions (§4) |
| **Open-set** Choice labels, zero-shot | Each label is encoded as text in the same pass and scored by a matching head (§5.2) |
| **Score** with uncertainty | Beta distribution head (§5.4) |
| **Null** as a first-class learned answer | Per-question abstain head, trained jointly (§5.3) |
| Calibrated probabilities | Proper scoring rules end to end, plus post-hoc temperature scaling (§8, §10) |
| **Cannot** emit outside the answer space | Outputs are logits indexed by the provided labels, and a Beta distribution on [0,1] mapped to [min,max]. There is no vocabulary head and no text output (§5.5) |
| No autoregressive backbone | Bidirectional encoder only (ModernBERT architecture) |

## 2. Overview

```
 request ──► render + tokenize ──► ONE packed sequence ──► bidirectional encoder ──► hidden states
                                   [state | q1 + labels | q2 + labels | …]          (N × d)
                                              │                                         │
                          structured attention mask + position ids                     ▼
                                                                    gather marker tokens:
                                                                    h_q (one per question)
                                                                    h_l (one per label)
                                                                              │
                              ┌───────────────────────────┬───────────────────┴────────────┐
                              ▼                           ▼                                ▼
                     null head: z_null(h_q)     choice head: z(h_q, h_l)         score head: (μ, κ)(h_q)
                              │                           │                                │
                              └────────── calibrated temperatures (post-hoc) ──────────────┘
                                                          ▼
                                   probabilities → decision rule → Response JSON
```

The encoder does all the reasoning, because its attention lets every question read the state.
The heads are small, just a few MLP layers, and turn the encoder's hidden vectors into scores.

## 3. Input packing

### 3.1 Token layout

Special marker tokens reuse ModernBERT's `[unused0]`…`[unused82]` slots, so the vocabulary and embedding
matrix don't change. Both tracks use the same tokenizer (§7.3).

```
[CLS] <state tokens …>
[CHOICE] <question 1 text> [LABEL] <label 1.1 text> [LABEL] <label 1.2 text> …
[SCORE]  <question 2 text> (min: <min_label>; max: <max_label>)
[CHOICE] <question 3 text> [LABEL] …
```

- **Items in a list state** are rendered as `[1] …\n[2] …`, and JSON is rendered compactly (`render_state`).
  One function does this for both training and inference, so the model sees the same format at inference as in training.
- **The type marker** (`[CHOICE]` / `[SCORE]`) starts each question block. Its final hidden state `h_q` is the question's
  representation: it has read the state, the question, and (for choice) the options.
- **`[LABEL]`** starts each label. Its final hidden state `h_l` is that label's representation.
- **Score anchors** (`min_label`/`max_label`) go into the question text, so the model knows what 0 and 1 mean.
  Numeric ranges are *not* shown; the model always predicts on [0,1] and we map to [min,max] afterward.

### 3.2 Position ids

The encoder uses RoPE (rotary position embeddings), which encode each token's position relative to others.
We choose position ids so that the ordering of questions and labels doesn't matter:

- State: positions `0 … S-1`.
- **Every** question block starts at position `S`, as if it were the only question.
- **Every** label of question *i* starts at position `S + len(q_i)`, as if it were the only label.

## 4. The attention mask

Token *a* may attend to token *b* if and only if:

| a \ b | state | own question | own labels | other questions / their labels |
|---|---|---|---|---|
| **state** | ✅ | ❌ | ❌ | ❌ |
| **question *i*** | ✅ | ✅ | ✅ (all labels of *i*) | ❌ |
| **label *i.j*** | ✅ | ✅ | only itself (*i.j*) | ❌ |

On local-attention layers (ModernBERT alternates two local layers with one global layer), the rule is
additionally limited to `|pos(a) − pos(b)| ≤ 64`, measured in **position ids**, not array index.

Example with a 4-token state, one choice question (2 tokens), and two labels (1 token each), where rows attend to columns:

```
            s0 s1 s2 s3 | Q  q1 | L1 a | L2 b
   s0..s3    ■  ■  ■  ■ |  ·  · |  ·  · |  ·  ·
   Q, q1     ■  ■  ■  ■ |  ■  ■ |  ■  ■ |  ■  ■
   L1, a     ■  ■  ■  ■ |  ■  ■ |  ■  ■ |  ·  ·
   L2, b     ■  ■  ■  ■ |  ■  ■ |  ·  · |  ■  ■
```

### Why this shape (properties we get for free and will test)

1. **State encoded once.** The state rows only look at the state, so the state's hidden states are
   identical whether you ask 1 question or 30. Later this also lets us **cache** a state's per-layer keys and values
   and add questions without re-encoding the state, the encoder equivalent of an LLM prefix cache.
2. **Questions are independent.** A question's answer is bit-for-bit the same whether it's asked
   alone or with others, in any order. This is the contract users expect, and it also simplifies training:
   single-question examples teach exactly what multi-question requests need (§9).
3. **Label order doesn't matter.** Labels share the same position range and can't see each other, so
   shuffling the options can't change any probability. A classic LLM bias ("prefers option A") is impossible by construction.
4. **Labels can still be compared.** The question token reads *all* its labels at every layer, and every label reads the
   question token, so information about the whole option set flows between them. The null head can therefore notice
   "none of these fit," and a label's score can depend on its competitors.

An **ablation flag** lets us disable question→label attention in experiments (pure matching, with no option awareness).

### 4.1 Cost

With block-sparse attention (PyTorch FlexAttention), cost scales with the number of *allowed* token pairs:
roughly `S² + Σ_i (len(q_i) + labels_i) · S`, not `N²`. A 2,000-token state with ten 60-token question
blocks costs about 1.3× the state alone, not 1.7×. When we pack several training examples into one row, the mask is block-diagonal
across examples, so padding costs nothing and examples can't see each other.

## 5. Heads

`d` is the encoder's hidden size (768 for ModernBERT-base). The heads are identical in both tracks, scaled by `d`.

### 5.1 Pooling

`h_q` = final hidden state at the question's `[CHOICE]`/`[SCORE]` marker. `h_l` = final hidden state at each `[LABEL]` marker.
We use marker tokens rather than mean pooling because the marker's attention can learn which parts
of the state matter for *this* question.

### 5.2 Choice head (matching)

```
z_ij = w · GELU( W [ h_li ; h_qi ; h_li ⊙ h_qi ] + b )        (scalar logit per label)
```

The label's representation has already read the state and the question, so the head only has to
read off how well the label matches. The `[a; b; a⊙b]` feature is a standard matching layout (used in InferSent/ESIM-style models).
Unseen labels work because they are represented by their text, not by a learned per-class weight.

### 5.3 Null head

```
z_null,i = MLP_null(h_qi)          p_null = σ(z_null / T_null)     (forced to 0 if allow_null = false)
```

### 5.4 Score head (Beta distribution)

```
μ = σ(MLP_μ(h_q))        κ = softplus(MLP_κ(h_q)) + ε
α = μκ,  β = (1 − μ)κ    →   value ~ Beta(α, β) on [0, 1], mapped to [min, max]
```

**Why Beta instead of regression:** a regression head outputs a single number and gives no uncertainty.
A Beta distribution lives exactly on [0,1], so the answer can't go out of bounds, and it can express
"about 0.8, fairly sure" (high κ), "no idea" (κ ≈ 2, nearly flat), or even "either very low or very high" (κ < 2, U-shaped).
We parameterize it by mean and concentration because those are easier to learn and interpret than raw (α, β).

### 5.5 From logits to an answer

For choice question *i* with labels *j*:

```
q_ij    = softmax_j(z_ij / T_choice)            # conditional on "answerable"
probs_ij = (1 − p_null,i) · q_ij                  # unconditional; Σ_j probs_ij + p_null,i = 1
```

Decision rule (thresholds come from the request's `options`):

1. If `p_null ≥ null_threshold`, the answer is `null` with `abstain_reason = "unanswerable"`.
2. Otherwise, j* = argmax probs. If `probs_j* < min_confidence`, the answer is `null` with `abstain_reason = "low_confidence"`.
3. Otherwise, the answer is label j*.

For scores: `answer = min + mean·(max−min)` (rounded to `step` if given), `std`, and a central `interval`
from Beta quantiles, all computed in post-processing.

**Why it can't go outside the answer space:** the network's outputs are one logit per *provided* label, one null logit,
and (μ, κ) per score question. The code that builds the response can only index into the request's own label list
or map a number in [0,1] into [min,max]. There's no path by which text could be produced.

## 6. Training objective

For each question, the model defines a full probability distribution over {labels…, null} (or {values in [0,1], null}).
We train by **maximizing the log-likelihood of the correct outcome**:

```
choice, answerable:  −log(1 − p_null) − log q_y
choice, null:        −log p_null
score, answerable:   −log(1 − p_null) − log Beta(ỹ; α, β)
score, null:         −log p_null
```

That is exactly the null head's binary cross-entropy plus a cross-entropy or Beta negative log-likelihood when the question
is answerable. **Log loss is a strictly proper scoring rule**: the model gets the best expected score only by reporting its
true belief, which is the foundation for calibration.

Details:
- `ỹ = (y·(n−1) + 0.5)/n` squeezes targets of exactly 0 or 1 inward (Smithson & Verkuilen, 2006), because a Beta's log-density is infinite at the endpoints.
- **Soft targets** (teacher probabilities, when available) replace the one-hot target with the teacher's distribution
  (a distillation cross-entropy), mixed with hard labels.
- **Per-source weights and temperature sampling** (sampling probability ∝ dataset size^0.3) stop the large datasets
  from drowning out the small, diverse ones.

## 7. Backbones and the two tracks

### 7.1 Track B: pragmatic

`kodiak-b-small` starts from **ModernBERT-base** (149M params, Apache-2.0, 8,192-token native context, RoPE,
alternating local and global attention, trained on about 2T tokens). We implement the ModernBERT architecture in our own
module and load its weights, which gives us full control over position ids and masks for §3–§4
(the stock Hugging Face class assumes one ordinary sequence). A test checks that our module reproduces the HF model's outputs
on ordinary inputs before we rely on it.

### 7.2 Track A: pure

Same module, randomly initialized, then pretrained with **masked language modeling** (30% masking, the ModernBERT
recipe) on permissive English text (Phase 2 selects the corpora). MLM is the default because it's simple and matches the
recipe of Track B's backbone, so the comparison is about *pretraining budget*, not recipe. ELECTRA-style replaced-token
detection is a known compute-efficient alternative and is our first fallback if MLM underperforms at our scale.

### 7.3 Shared tokenizer

Both tracks use the ModernBERT tokenizer. A tokenizer is a word-piece dictionary, not learned neural weights, and sharing
it means both tracks see identical inputs, so the comparison isolates what matters: pretrained vs. from-scratch weights.
Training our own tokenizer later is a small, separate experiment.

### 7.4 Sizes and rough compute

| Checkpoint | Track | Backbone | Params | Phase |
|---|---|---|---|---|
| `kodiak-a-tiny` | A | 4 layers, d=256 | ~15M (13M of it embeddings) | 3 (plumbing test only) |
| `kodiak-a-mini` | A | 12 layers, d=512 | ~50M | 4 |
| `kodiak-a-small` | A | ModernBERT-base shape, from scratch | ~150M | 4, stretch goal |
| `kodiak-b-small` | B | ModernBERT-base | ~150M | 4, primary |
| `kodiak-b-base` | B | ModernBERT-large | ~396M | later |

The fair size-matched comparison is **a-small vs. b-small** (identical architecture). If a-small is out of budget,
**a-mini vs. an Ettin encoder of similar size** (MIT; ModernBERT recipe, 17M–1B sizes) is the fallback.

Training cost is estimated with the standard rule **FLOPs ≈ 6 × params × tokens**, assuming the Spark sustains
**about 30 TFLOP/s in bf16**. That's an assumption; Phase 3 measures the real number.

| Job | Params × tokens | Estimate |
|---|---|---|
| Decision tuning, b-small | 150M × 2B | ~17 hours |
| MLM pretraining, a-mini | 50M × 20B | ~2–3 days |
| MLM pretraining, a-small | 150M × 30B | ~10 days |

For scale: ModernBERT-base saw about 2T tokens, 60–100× what Track A can see here. Track A is expected to trail
Track B; the interesting number is *by how much*, per GPU-day.

## 8. Training stages

| Stage | Track | What | Loss |
|---|---|---|---|
| **A0** Pretrain | A only | MLM at 512 tokens, then a short 2,048-token phase | MLM cross-entropy |
| **S1** Decision tuning | both | All weights (encoder + heads). States ≤ 512 tokens, packed into 2,048-token rows | §6 |
| **S2** Long-state tuning | both | Short continuation with states up to 2,048 tokens | §6 |
| **S3** Post-hoc calibration | both | Fit `T_choice`, `T_null`, and a κ scale on a held-out calibration split; weights frozen | NLL |
| **S4** Decision-cost tuning *(optional, experimental)* | both | §10.3 | expected utility + §6 |

All jobs are **resumable**: they checkpoint model, optimizer, scheduler, RNG, and data-loader position every
N minutes, log to JSONL + TensorBoard, and log GPU temperature, power, and memory headroom, pausing if limits are exceeded.

## 9. Training data shape and augmentation

Public datasets (NLI, sentiment, topic, intent, yes/no QA, extraction-as-choice, …) are converted to the
`Example` schema (`src/kodiak_s1/schema.py`). Most have one question per state; §4 property 2 means that's fine.

Augmentations that teach the *contract* rather than any one dataset:
- **Label rewriting:** paraphrased label names, labels with descriptions, and opaque ids with descriptive text,
  so the model reads label *meaning* rather than memorizing strings.
- **Label-set resampling:** drop some wrong labels and add distractors from other datasets, so the model sees varied set sizes.
- **Question paraphrases:** several phrasings per dataset.
- **Null construction** (several kinds, so the model can't learn a single shortcut):
  - *mismatched*: a question from another dataset asked against this state (easy);
  - *gold removed*: the correct label is removed, so "none of these" becomes null (tagged, so we can measure it separately);
  - *hard synthetic*: Qwen-written questions on the same topic whose answer the state does not contain (e.g. asking for the card
    brand when only "my card" is mentioned).
- **Synthetic multi-question states** from Qwen, so real multi-question requests appear in training and eval too.

## 10. Calibration: published methods and our plan

### 10.1 What the literature says

- Modern deep networks are often **overconfident**; a single **temperature** fit on held-out data fixes much of it
  (Guo et al., 2017).
- Pretrained transformers fine-tuned for classification are fairly well calibrated **in-domain** with temperature
  scaling, but calibration degrades **out of domain** (Desai & Durrett, 2020). That's our main risk, since zero-shot labels
  are out of domain by design, so we measure it separately (§11).
- Training-time alternatives: focal loss (Mukhoti et al., 2020), differentiable calibration penalties such as
  MMCE (Kumar et al., 2018). We keep these as ablations, not defaults: plain log loss plus temperature scaling is a strong,
  simple baseline, and we should beat it on evidence before adding complexity.
- **Selective prediction / abstention:** reject when uncertain, evaluated with risk-coverage curves
  (Geifman & El-Yaniv, 2017); calibrators for abstaining under domain shift (Kamath et al., 2020).
- **RL for calibration:** RLCR (Damani et al., arXiv 2507.16806) trains LLMs with a reward of correctness plus a
  **Brier score** on the model's stated confidence, because a binary correctness reward rewards confident guessing.

### 10.2 What applies to Kodiak

An LLM's confidence is *generated text*, so improving it needs RL. Kodiak's confidence **is** its output
distribution, so training with a proper scoring rule (§6) directly optimizes the thing RLCR's Brier reward targets,
with exact gradients instead of sampled rewards. S1 + S3 is therefore our main calibration method.

### 10.3 Optional RL-style stage (S4): decision-cost tuning

What proper scoring rules do *not* optimize is the **decision**: when to abstain. S4 treats each question as a
one-step policy over actions {label₁ … labelₖ, abstain} with reward `+1` for correct, `−c` for wrong, and `0` for abstaining,
with the cost `c` sampled per example. We optimize expected reward with REINFORCE (with a baseline), *mixed with the §6 loss*
so calibration isn't sacrificed. We adopt it only if it improves the held-out risk-coverage curve at equal or better ECE.

We make **no claim** that this matches RLCD or any other unpublished method.

## 11. Evaluation

| Split | What it measures |
|---|---|
| In-domain test | Held-out rows of training datasets |
| **Held-out tasks** | Entire datasets never trained on, with new label sets (the zero-shot claim) |
| Null test | Human-verified unanswerable and answerable pairs, by null type |
| Long-state test | States of 1–2k tokens |
| Multi-question test | 5–20 questions per state (checks property 2 and throughput) |

Metrics: accuracy and macro-F1; ECE (15 equal-mass bins, top-label) and Brier score; abstain precision and recall
and risk-coverage (AURC); for scores MAE, Beta NLL, and interval coverage (does the 90% interval contain the truth about 90%
of the time?); latency p50/p95 at batch 1 and throughput at batch 32, on the same Spark.

**Headline numbers use human-labeled data only.** Results on Qwen-labeled data are reported separately, since a student
can't be fairly scored against its own teacher's labels.

**Baseline:** `qwen3.8:27b` through Ollama with a JSON-schema-constrained output (`format`), same prompts, same eval.
Confidence comes from token log-probabilities if Ollama exposes them for the chosen answer, otherwise from verbalized
confidence, and we say which.

## 12. Inference and ONNX

- **Graph inputs:** `input_ids`, `position_ids`, a boolean attention mask `[N, N]` built by the client from token roles,
  and the indices of question and label marker tokens (plus which question each label belongs to). **Outputs:** raw logits
  and (μ, κ); calibration temperatures ship in the model config.
- FlexAttention isn't exportable, so the export path uses standard scaled-dot-product attention with the explicit mask.
  A parity test checks that both paths agree on fixture requests.
- **Post-processing** (grouped softmax, thresholds, Beta quantiles) is a few dozen lines, implemented in both
  Python and JavaScript and tested against the same fixtures.
- Node.js server: `onnxruntime-node`, the tokenizer from `tokenizer.json`, validation with the JSON Schemas in `schema/`.

## 13. v0.1 limits

| Limit | Value |
|---|---|
| State | ≤ 2,048 tokens (requests over budget are rejected with a clear error; truncation strategies later) |
| Packed total | ≤ 4,096 tokens |
| Questions / labels | ≤ 32 questions, ≤ 32 labels per question |
| Question / label text | ≤ 128 / ≤ 32 tokens (500 / 200 characters in the schema) |
| Language | English |

## 14. Alternatives considered

| Alternative | Why not (for v0.1) |
|---|---|
| One forward pass per question (plain cross-encoder) | Violates one-pass, and re-encodes the state N times |
| Encode the state alone, then add a light cross-attention "decision decoder" on top | Cheaper per question and label embeddings could be cached, but question-state interaction is shallow and the decoder layers start from scratch. **Kept as a v0.2 option** for requests with hundreds of labels |
| Null as an extra softmax class | Fine for choice but doesn't extend to scores; our factored form is the same joint likelihood and works for both |
| Score as regression (MSE) | No uncertainty |
| Score as a histogram over bins | Can represent any shape, but coarse and needs a bin count; kept as an ablation if Beta fits poorly |
| Fixed per-dataset classification heads | Can't do open-set labels |
| Constrained decoding of an LLM | Explicitly out of scope; it's the baseline we're trying to beat |

## 15. Risks and open questions

1. **FlexAttention on GB10 (aarch64 + Triton on a new GPU).** If it's unsupported or slow, the fallback is SDPA with a dense
   mask (more memory, slower). Phase 3 verifies this first.
2. **Null shortcuts.** The model may learn "topic mismatch → null" instead of real answerability. Mitigation: multiple
   null types (§9) and per-type eval.
3. **Out-of-domain calibration** of zero-shot labels (§10.1). Measured separately; S4 and an OOD-aware temperature are options.
4. **Teacher noise and bias** from Qwen labels. Mitigation: human-labeled headline eval; per-source loss weights.
5. **Questions don't see each other** (property 2), so the model can't enforce consistency across related questions
   (e.g. "is it spam?" vs. "category?"). This is accepted for v0.1 and is the price of order-independence.
6. **Track A's compute gap** is large and expected; the report will present it per GPU-day, not as a failure.

## 16. References

- Guo, Pleiss, Sun, Weinberger. *On Calibration of Modern Neural Networks.* ICML 2017.
- Desai, Durrett. *Calibration of Pre-trained Transformers.* EMNLP 2020.
- Mukhoti et al. *Calibrating Deep Neural Networks using Focal Loss.* NeurIPS 2020.
- Kumar, Sarawagi, Jain. *Trainable Calibration Measures for Neural Networks from Kernel Mean Embeddings.* ICML 2018.
- Geifman, El-Yaniv. *Selective Classification for Deep Neural Networks.* NeurIPS 2017.
- Kamath, Jia, Liang. *Selective Question Answering under Domain Shift.* ACL 2020.
- Damani et al. *Beyond Binary Rewards: Training LMs to Reason About Their Uncertainty.* arXiv:2507.16806.
- Smithson, Verkuilen. *A Better Lemon Squeezer? Maximum-Likelihood Regression with Beta-Distributed Dependent Variables.* Psychological Methods, 2006.
- Warner et al. *Smarter, Better, Faster, Longer: A Modern Bidirectional Encoder (ModernBERT).* 2024.
- Weller et al. *Seq vs Seq: An Open Suite of Paired Encoders and Decoders (Ettin).* 2025.
- Clark et al. *ELECTRA: Pre-training Text Encoders as Discriminators Rather Than Generators.* ICLR 2020.
