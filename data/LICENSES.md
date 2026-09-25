# Data and Weight Licenses

Every dataset, generator, and set of pretrained weights that goes into a Kodiak model is listed here.
Every training record carries `meta.source` and `meta.license`, and `source` must match an **ID** below.
Anything not listed here is not used.

**Policy:** permissive licenses only (Apache-2.0, MIT, BSD, CC0, CC-BY, ODC-By, CDLA-Permissive).
Share-alike (CC-BY-SA) and non-commercial (NC) sources are **excluded** from v0.1 unless explicitly
approved and marked here, because Kodiak's weights are released under Apache-2.0.

## Pretrained weights

| ID | Name | License | URL | Used by |
|---|---|---|---|---|
| `modernbert-base` | answerdotai/ModernBERT-base (149M) | Apache-2.0 | https://huggingface.co/answerdotai/ModernBERT-base | Track B (b-small) |
| `modernbert-large` | answerdotai/ModernBERT-large (396M) | Apache-2.0 | https://huggingface.co/answerdotai/ModernBERT-large | Track B (b-base, later) |
| `ettin-encoder` | jhu-clsp/ettin-encoder-{17m…1b} | MIT | https://huggingface.co/jhu-clsp | Track B size-matched control (optional) |

The ModernBERT **tokenizer** (Apache-2.0) is shared by both tracks. See docs/ARCHITECTURE.md §7.

## Pretraining corpora (Track A)

_To be selected before Track A pretraining (Phase 4)._

| ID | Name | License | URL | Tokens used | Notes |
|---|---|---|---|---|---|

## Decision-tuning datasets (both tracks)

License column = what we verified against the **upstream** source, not just the Hugging Face tag.
"Held out" sources are never trained on; they appear only in the eval set (zero-shot).

| ID | Name | Family | License | URL | Use | Notes |
|---|---|---|---|---|---|---|
| `mnli` | MultiNLI | NLI | OANC (permissive) + CC-BY-3.0 | https://huggingface.co/datasets/nyu-mll/multi_nli | train/eval | **Fiction genre excluded**: it includes CC-BY-SA text (*Seven Swords*) we can't separate out |
| `scitail` | SciTail | NLI | Apache-2.0 | https://github.com/allenai/scitail | train/eval | |
| `commonsense_qa` | CommonsenseQA | MC reasoning | MIT | https://huggingface.co/datasets/tau/commonsense_qa | train/eval | |
| `openbookqa` | OpenBookQA | MC reasoning | Apache-2.0 | https://github.com/allenai/OpenBookQA | train/eval | |
| `winogrande` | WinoGrande (XL) | MC reasoning | Apache-2.0 | https://github.com/allenai/winogrande | train/eval | |
| `clinc_oos` | CLINC150 (plus) | Intent | CC-BY-3.0 | https://huggingface.co/datasets/clinc/clinc_oos | train/eval | Out-of-scope queries → null |
| `massive` | MASSIVE (en-US) | Intent | CC-BY-4.0 | https://github.com/alexa/massive | train/eval | Loaded from the Hub's parquet conversion |
| `banking77` | Banking77 | Intent | CC-BY-4.0 | https://github.com/PolyAI-LDN/task-specific-datasets | **held out** | Read from the upstream CSVs |
| `go_emotions` | GoEmotions (simplified) | Emotion / sentiment | Apache-2.0 | https://github.com/google-research/google-research/tree/master/goemotions | train/eval | Single-label rows only; sentiment from the authors' published grouping |
| `civil_comments` | Civil Comments | Moderation (scores) | CC0-1.0 | https://huggingface.co/datasets/google/civil_comments | train/eval | All rows with toxicity ≥ 0.3 plus a 10% sample of the rest |
| `sms_spam` | SMS Spam Collection | Spam | CC-BY-4.0 | https://archive.ics.uci.edu/dataset/228/sms+spam+collection | train/eval | |
| `prompt_injections` | deepset prompt-injections | Safety | Apache-2.0 | https://huggingface.co/datasets/deepset/prompt-injections | train/eval | German rows filtered out (English-only v0.1) |
| `jailbreak_classification` | Jailbreak classification | Safety | Apache-2.0 | https://huggingface.co/datasets/jackhhao/jailbreak-classification | **held out** | |
| `measuring_hate_speech` | Measuring Hate Speech | Moderation (scores) | CC-BY-4.0 | https://huggingface.co/datasets/ucberkeley-dlab/measuring-hate-speech | **held out** | Aggregated per comment across annotators |
| `helpsteer2` | HelpSteer2 | Response quality (scores) | CC-BY-4.0 | https://huggingface.co/datasets/nvidia/HelpSteer2 | train/eval | Five 0–4 attributes per response |
| `ultrafeedback` | UltraFeedback | Response quality (scores) | MIT | https://github.com/OpenBMB/UltraFeedback | train/eval | Ratings are GPT-4 annotations; "N/A" → null |
| `glaive_fc_v2` | Glaive function calling v2 | Tool routing | Apache-2.0 | https://huggingface.co/datasets/glaiveai/glaive-function-calling-v2 | train/eval | First move: call a tool / ask for missing details / no tool |
| `toolace` | ToolACE | Tool routing | Apache-2.0 | https://huggingface.co/datasets/Team-ACE/ToolACE | train/eval | Single-tool calls only |
| `bias_in_bios` | Bias in Bios | Occupation | MIT | https://github.com/microsoft/biosbias | **held out** | Known gender bias; we'll report accuracy by gender in Phase 5 |
| `qasper` | Qasper | Document QA (long) | CC-BY-4.0 | https://allenai.org/data/qasper | train/eval | Unanimous yes/no or unanimous unanswerable; ~700-word excerpts |

### Pending access (gated on Hugging Face: needs a token and accepting the terms)

| ID | Name | Family | License | URL |
|---|---|---|---|---|
| `wildguardmix` | WildGuardMix | Safety (prompt harm, response harm, refusal) | ODC-By | https://huggingface.co/datasets/allenai/wildguardmix |
| `xlam_fc` | xLAM function calling 60k | Tool routing | CC-BY-4.0 | https://huggingface.co/datasets/Salesforce/xlam-function-calling-60k |

### Considered and excluded (v0.1)

| Dataset | Reason |
|---|---|
| SNLI, BoolQ, SQuAD v2, ARC, DBpedia-14, HotpotQA, FEVER, VitaminC | CC-BY-SA (share-alike) |
| ANLI, SciQ, SciFact, ToxicChat, Financial PhraseBank, climate_detection | Non-commercial |
| AG News, IMDB, SST-2, Rotten Tomatoes, Yelp, TweetEval, Yahoo Answers, RACE, STS-B | No clear license, or terms of use restrict reuse |
| amazon_polarity | HF card says Apache-2.0, but the upstream review data's terms are unclear |
| HellaSwag, PIQA | Probably permissive (MIT / AFL-3.0), but we couldn't verify the upstream license. Can be added once confirmed |
| PAWS | Wiki portion is derived from Wikipedia (CC-BY-SA) |

## Synthetic data

| ID | Generator | Teacher | License | Notes |
|---|---|---|---|---|
| `kodiak_synth_v1` | `src/kodiak_s1/data/synth.py` | `qwen3.8:27b` via Ollama (model license: Apache-2.0) | Apache-2.0 | Generated states + questions (including deliberately unanswerable ones); kept only where an independent verification pass agrees |
| `kodiak_gen2` | `src/kodiak_s1/data/gen2/` (Generator v2) | writer `openai/gpt-oss-120b` (Apache-2.0), checker `deepseek-ai/DeepSeek-V3.2` (MIT), both via DigitalOcean serverless inference | Apache-2.0 (synthetic states, all questions and labels); grounded states: ODC-By-1.0 (see below) | Spec-driven (taxonomy in `data/gen2/taxonomy_v2.json`); ~45% of jobs use a real FineWeb-Edu passage as the state; kept only where the blind checker agrees |

### Grounding text

| ID | Name | License | URL | Use |
|---|---|---|---|---|
| `fineweb_edu` | FineWeb-Edu (sample-10BT) | ODC-By-1.0 (drawn from Common Crawl; subject to CommonCrawl terms of use) | https://huggingface.co/datasets/HuggingFaceFW/fineweb-edu | 100–450-word passages used as states for Generator v2 grounded examples (record meta carries the FineWeb id). Per GENERATOR_V2.md §7, the published dataset will ship FineWeb ids + a rebuild script, not the excerpts. Also downloaded for the deferred Track A pretraining. |
