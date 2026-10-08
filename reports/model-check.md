# Kodiak eval report

Eval set: `data/eval/heldout-v02-only.jsonl`; examples compared: 3550; **choice questions only**


## overall

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-e22-s1 | 3550 | 0.637 | 0.674 | 0.699 | 0.072 | 0.039 | 0.503 | 0.00 | 0.00 | – | – | – | 43 |
| kodiak-e24-s1 | 3550 | 0.639 | 0.676 | 0.686 | 0.061 | 0.042 | 0.493 | 0.00 | 0.00 | – | – | – | 43 |
| qwen3-1.7b | 3550 | 0.548 | 0.572 | 0.597 | 0.330 | 0.340 | 0.762 | 0.29 | 0.18 | – | – | – | 966 |
| qwen3-0.6b | 3550 | 0.427 | 0.455 | 0.399 | 0.491 | 0.468 | 1.077 | 0.00 | 0.00 | – | – | – | 652 |

## eval:heldout

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-e22-s1 | 3550 | 0.637 | 0.674 | 0.699 | 0.072 | 0.039 | 0.503 | 0.00 | 0.00 | – | – | – | 43 |
| kodiak-e24-s1 | 3550 | 0.639 | 0.676 | 0.686 | 0.061 | 0.042 | 0.493 | 0.00 | 0.00 | – | – | – | 43 |
| qwen3-1.7b | 3550 | 0.548 | 0.572 | 0.597 | 0.330 | 0.340 | 0.762 | 0.29 | 0.18 | – | – | – | 966 |
| qwen3-0.6b | 3550 | 0.427 | 0.455 | 0.399 | 0.491 | 0.468 | 1.077 | 0.00 | 0.00 | – | – | – | 652 |

## eval:heldout_v01

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-e22-s1 | 750 | 0.864 | 0.869 | 0.792 | 0.073 | 0.041 | 0.274 | 0.00 | – | – | – | – | 42 |
| kodiak-e24-s1 | 750 | 0.844 | 0.851 | 0.758 | 0.075 | 0.033 | 0.286 | 0.00 | – | – | – | – | 42 |
| qwen3-1.7b | 750 | 0.753 | 0.757 | 0.631 | 0.132 | 0.151 | 0.395 | 0.00 | – | – | – | – | 2588 |
| qwen3-0.6b | 750 | 0.497 | 0.509 | 0.429 | 0.305 | 0.328 | 0.818 | 0.00 | – | – | – | – | 668 |

## eval:heldout_v02

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-e22-s1 | 2800 | 0.576 | 0.617 | 0.499 | 0.089 | 0.052 | 0.565 | 0.00 | 0.00 | – | – | – | 43 |
| kodiak-e24-s1 | 2800 | 0.585 | 0.626 | 0.529 | 0.080 | 0.055 | 0.548 | 0.00 | 0.00 | – | – | – | 43 |
| qwen3-1.7b | 2800 | 0.494 | 0.518 | 0.518 | 0.380 | 0.394 | 0.861 | 0.48 | 0.18 | – | – | – | 880 |
| qwen3-0.6b | 2800 | 0.408 | 0.439 | 0.329 | 0.540 | 0.518 | 1.146 | 0.00 | 0.00 | – | – | – | 649 |

## null:not_mentioned

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-e22-s1 | 186 | 0.000 | – | 0.000 | 0.682 | – | 1.470 | – | 0.00 | – | – | – | 57 |
| kodiak-e24-s1 | 186 | 0.000 | – | 0.000 | 0.599 | – | 1.204 | – | 0.00 | – | – | – | 58 |
| qwen3-1.7b | 186 | 0.177 | – | 0.100 | 0.633 | – | 1.316 | 1.00 | 0.18 | – | – | – | 1269 |
| qwen3-0.6b | 186 | 0.000 | – | 0.000 | 0.976 | – | 1.946 | – | 0.00 | – | – | – | 807 |

## Per source (accuracy / ECE / score MAE)

| source | kodiak-e22-s1 | kodiak-e24-s1 | qwen3-1.7b | qwen3-0.6b |
|---|---|---|---|---|
| arxiv_field | 0.645 / 0.082 | 0.640 / 0.068 | 0.685 / 0.253 | 0.375 / 0.619 |
| banking77 | 0.820 / 0.077 | 0.784 / 0.066 | 0.656 / 0.193 | 0.388 / 0.142 |
| bias_in_bios | 0.832 / 0.158 | 0.824 / 0.140 | 0.780 / 0.121 | 0.616 / 0.342 |
| casehold | 0.448 / 0.071 | 0.463 / 0.060 | 0.550 / 0.343 | 0.383 / 0.598 |
| contract_nli | 0.425 / 0.325 | 0.400 / 0.294 | 0.370 / 0.470 | 0.312 / 0.659 |
| ethics_commonsense | 0.510 / 0.207 | 0.515 / 0.219 | 0.505 / 0.388 | 0.458 / 0.387 |
| fin_tweets_sentiment | 0.725 / 0.141 | 0.748 / 0.131 | 0.477 / 0.317 | 0.590 / 0.379 |
| fin_tweets_topic | 0.585 / 0.081 | 0.632 / 0.123 | 0.505 / 0.400 | 0.405 / 0.587 |
| jailbreak_classification | 0.940 / 0.061 | 0.924 / 0.082 | 0.824 / 0.102 | 0.488 / 0.512 |
| poem_sentiment | 0.695 / 0.066 | 0.695 / 0.067 | 0.362 / 0.488 | 0.333 / 0.655 |

## Systems

- **kodiak-e22-s1**: `{"system": "kodiak-e22-s1", "model": "runs/b-xl-s1-e22-s1/checkpoints/step_0006000.pt", "batched_ms_per_example": 21.297843419569766, "eval": "data/eval/heldout-v02-only.jsonl"}`
- **kodiak-e24-s1**: `{"system": "kodiak-e24-s1", "model": "runs/b-xl-s1-e24-s1/checkpoints/step_0006000.pt", "batched_ms_per_example": 20.994983204817842, "eval": "data/eval/heldout-v02-only.jsonl"}`
- **qwen3-1.7b**: `{"system": "qwen3-1.7b", "llm": "qwen3:1.7b", "eval": "data/eval/heldout-v02-only.jsonl", "limit": 0, "confidence": "verbalized", "prompt": "v3: judgments answerable; numeric score schema; quote, answer, confidence"}`
- **qwen3-0.6b**: `{"system": "qwen3-0.6b", "llm": "qwen3:0.6b", "eval": "data/eval/heldout-v02-only.jsonl", "limit": 0, "confidence": "verbalized", "prompt": "v3: judgments answerable; numeric score schema; quote, answer, confidence"}`
