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

### Eval v0.2 held-out sources (added 2026-09-26, evaluation only, never trained on; D30)

| ID | Name | Task | License (verified upstream) | URL | Notes |
|---|---|---|---|---|---|
| `contract_nli` | ContractNLI (Hitachi America, Ltd.) | Does an NDA excerpt state a hypothesis? yes / no / not mentioned (null) | CC-BY-4.0 (official site + TERMS file in the zip) | https://stanfordnlp.github.io/contract-nli/ | Upstream zip only (the HF mirror is mislabeled CC-BY-NC-SA); 320-word windows |
| `ethics_commonsense` | ETHICS, commonsense morality | Is the narrator's action clearly wrong? | MIT (repo LICENSE) | https://github.com/hendrycks/ethics | Reddit-sourced; culturally biased (per the authors) |
| `fin_tweets_topic` | Twitter Financial News (topic) | 20 finance topics | MIT (creator's dataset card) | https://huggingface.co/datasets/zeroshot/twitter-financial-news-topic | Underlying tweets are subject to X's terms |
| `fin_tweets_sentiment` | Twitter Financial News (sentiment) | bearish / bullish / neutral | MIT (creator's dataset card) | https://huggingface.co/datasets/zeroshot/twitter-financial-news-sentiment | Underlying tweets are subject to X's terms |
| `arxiv_field` | arXiv metadata snapshot | Abstract → primary field (13 of 15 fields present) | CC0-1.0 (arXiv API terms: metadata incl. abstracts) | https://info.arxiv.org/help/api/tou.html | Via the HF mirror `librarian-bots/arxiv-metadata-snapshot` (one shard); economics and EESS appear only as distractors |
| `casehold` | CaseHOLD | Which of 5 holdings a citation stands for | Apache-2.0 (repo); opinions are public domain | https://github.com/reglab/casehold | Holdings truncated to 200 characters |
| `clickbait17` | Webis Clickbait Corpus 2017 | Clickbait score 0–1 (mean of 5 annotators) | CC-BY-4.0 (Zenodo record) | https://zenodo.org/records/5530410 | train-170331 file; tweet text subject to X's terms |
| `poem_sentiment` | Poem Sentiment (Google) | negative / positive / no impact / mixed | CC-BY-4.0 (repo) | https://github.com/google-research-datasets/poem-sentiment | All splits used (held out) |

Considered and rejected for v0.2: PubMedQA (abstracts carry no license of their own), FNC-1 (no license), PubMed 200k RCT, SciCite (no data
license), CFPB narratives, the only real urgency/priority ticket set (CC-BY-NC-4.0), HWU64/SNIPS (too close to MASSIVE/CLINC).

## Synthetic data

| ID | Generator | Teacher | License | Notes |
|---|---|---|---|---|
| `kodiak_synth_v1` | `src/kodiak_s1/data/synth.py` | `qwen3.8:27b` via Ollama (model license: Apache-2.0) | Apache-2.0 | Generated states + questions (including deliberately unanswerable ones); kept only where an independent verification pass agrees |
| `kodiak_gen2` | `src/kodiak_s1/data/gen2/` (Generator v2) | writer `openai/gpt-oss-120b` (Apache-2.0), checker `deepseek-ai/DeepSeek-V3.2` (MIT), both via DigitalOcean serverless inference | Apache-2.0 (synthetic states, all questions and labels); grounded states: ODC-By-1.0 (see below) | Spec-driven (taxonomy in `data/gen2/taxonomy_v2.json`); ~45% of jobs use a real FineWeb-Edu passage as the state; kept only where the blind checker agrees |

### Grounding text

| ID | Name | License | URL | Use |
|---|---|---|---|---|
| `fineweb_edu` | FineWeb-Edu (sample-10BT) | ODC-By-1.0 (drawn from Common Crawl; subject to CommonCrawl terms of use) | https://huggingface.co/datasets/HuggingFaceFW/fineweb-edu | 100–450-word passages used as states for Generator v2 grounded examples (record meta carries the FineWeb id). Per GENERATOR_V2.md §7, the published training dataset will ship FineWeb ids + a rebuild script, not the excerpts. **Exception:** `data/eval/synthetic_reviewed_gen2_v0.1.jsonl` (the human-graded v2 eval candidates) includes excerpts verbatim; see the attribution below. Also downloaded for the deferred Track A pretraining. |

#### Attribution: FineWeb-Edu excerpts in this repository

`data/eval/synthetic_reviewed_gen2_v0.1.jsonl` contains short excerpts (100–450 words) from **FineWeb-Edu** by Hugging Face
(Lozhkov, Ben Allal, von Werra, Wolf, 2024; https://huggingface.co/datasets/HuggingFaceFW/fineweb-edu), made available under the
**Open Data Commons Attribution License (ODC-By) v1.0** (https://opendatacommons.org/licenses/by/1-0/). FineWeb-Edu is derived from
Common Crawl, and use is also subject to the Common Crawl terms of use (https://commoncrawl.org/terms-of-use). Each grounded record
identifies its source document: `passage.id` / `passage.url` in the record and `fineweb-edu <id>` in `example.meta.notes`.
The questions, labels and review verdicts in that file are Kodiak's (Apache-2.0).
