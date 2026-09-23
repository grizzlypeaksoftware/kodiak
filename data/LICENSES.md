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

_To be filled in Phase 2._

| ID | Name | License | URL | Tokens used | Notes |
|---|---|---|---|---|---|

## Decision-tuning datasets (both tracks)

_To be filled in Phase 2._

| ID | Name | Task family | License | URL | Examples used | Converted by |
|---|---|---|---|---|---|---|

## Synthetic data

| ID | Generator | Teacher | Terms | Notes |
|---|---|---|---|---|
| _Phase 2_ | `scripts/…` | `qwen3.8:27b` via Ollama | _Check the Qwen model license for output-use terms in Phase 2._ | Includes deliberately unanswerable questions |
