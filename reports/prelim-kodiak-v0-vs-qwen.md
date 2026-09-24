# Kodiak eval report

Eval set: `data/eval/kodiak-eval-v0.1.jsonl`; examples compared: 200


## overall

| system | n | acc | macro-F1 | ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-b-small-v0-last | 280 | 0.732 | 0.625 | 0.095 | 0.384 | 0.90 | 0.79 | 0.168 | 1.00 | 0.86 | 8 |
| qwen3.8-27b (constrained JSON) | 280 | 0.732 | 0.695 | 0.230 | 0.494 | 0.17 | 0.70 | 0.042 | 0.04 | – | 3191 |
| qwen3.8-27b v2 prompt | 280 | 0.760 | 0.723 | 0.197 | 0.438 | 0.15 | 0.48 | 0.127 | 0.09 | – | 3337 |
| qwen3.8-27b (v3 prompt) | 280 | 0.765 | 0.726 | 0.192 | 0.428 | 0.68 | 0.39 | 0.213 | 1.00 | – | 3431 |

## eval:indomain

| system | n | acc | macro-F1 | ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-b-small-v0-last | 172 | 0.755 | 0.716 | 0.068 | 0.344 | 1.00 | 0.75 | 0.173 | 1.00 | 0.90 | 8 |
| qwen3.8-27b (constrained JSON) | 172 | 0.633 | 0.646 | 0.304 | 0.670 | 0.09 | 0.67 | 0.000 | 0.03 | – | 3534 |
| qwen3.8-27b v2 prompt | 172 | 0.755 | 0.720 | 0.201 | 0.431 | 0.09 | 0.58 | 0.175 | 0.06 | – | 3602 |
| qwen3.8-27b (v3 prompt) | 172 | 0.765 | 0.725 | 0.191 | 0.412 | 0.71 | 0.42 | 0.210 | 1.00 | – | 3716 |

## eval:heldout

| system | n | acc | macro-F1 | ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-b-small-v0-last | 79 | 0.649 | 0.527 | 0.271 | 0.531 | 0.00 | – | 0.153 | 1.00 | 0.73 | 8 |
| qwen3.8-27b (constrained JSON) | 79 | 0.877 | 0.774 | 0.129 | 0.241 | 0.00 | – | 0.083 | 0.09 | – | 2872 |
| qwen3.8-27b v2 prompt | 79 | 0.860 | 0.765 | 0.139 | 0.263 | 0.00 | – | 0.079 | 0.18 | – | 2990 |
| qwen3.8-27b (v3 prompt) | 79 | 0.860 | 0.765 | 0.132 | 0.263 | 0.00 | – | 0.226 | 1.00 | – | 3021 |

## eval:null_construct

| system | n | acc | macro-F1 | ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-b-small-v0-last | 19 | 0.895 | 0.315 | 0.102 | 0.095 | 1.00 | 0.89 | – | – | – | 7 |
| qwen3.8-27b (constrained JSON) | 19 | 0.684 | 0.116 | 0.284 | 0.578 | 1.00 | 0.68 | – | – | – | 2128 |
| qwen3.8-27b v2 prompt | 19 | 0.368 | 0.060 | 0.603 | 1.204 | 1.00 | 0.37 | – | – | – | 1982 |
| qwen3.8-27b (v3 prompt) | 19 | 0.368 | 0.060 | 0.603 | 1.204 | 1.00 | 0.37 | – | – | – | 1986 |

## eval:synthetic

| system | n | acc | macro-F1 | ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-b-small-v0-last | 10 | 0.667 | 0.500 | 0.266 | 0.501 | – | 0.00 | – | – | – | 12 |
| qwen3.8-27b (constrained JSON) | 10 | 1.000 | 1.000 | 0.000 | 0.000 | 1.00 | 1.00 | – | – | – | 6648 |
| qwen3.8-27b v2 prompt | 10 | 1.000 | 1.000 | 0.000 | 0.000 | 1.00 | 1.00 | – | – | – | 6699 |
| qwen3.8-27b (v3 prompt) | 10 | 1.000 | 1.000 | 0.000 | 0.000 | 1.00 | 0.50 | – | – | – | 6769 |

## null:gold_removed

| system | n | acc | macro-F1 | ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-b-small-v0-last | 11 | 0.818 | 0.300 | 0.177 | 0.165 | 1.00 | 0.82 | – | – | – | 7 |
| qwen3.8-27b (constrained JSON) | 11 | 0.455 | 0.089 | 0.509 | 0.999 | 1.00 | 0.45 | – | – | – | 2217 |
| qwen3.8-27b v2 prompt | 11 | 0.273 | 0.054 | 0.691 | 1.366 | 1.00 | 0.27 | – | – | – | 2079 |
| qwen3.8-27b (v3 prompt) | 11 | 0.273 | 0.054 | 0.691 | 1.366 | 1.00 | 0.27 | – | – | – | 2110 |

## null:mismatch

| system | n | acc | macro-F1 | ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-b-small-v0-last | 8 | 1.000 | 1.000 | 0.000 | 0.000 | 1.00 | 1.00 | – | – | – | 8 |
| qwen3.8-27b (constrained JSON) | 8 | 1.000 | 1.000 | 0.000 | 0.000 | 1.00 | 1.00 | – | – | – | 2020 |
| qwen3.8-27b v2 prompt | 8 | 0.500 | 0.333 | 0.494 | 0.982 | 1.00 | 0.50 | – | – | – | 1846 |
| qwen3.8-27b (v3 prompt) | 8 | 0.500 | 0.333 | 0.494 | 0.982 | 1.00 | 0.50 | – | – | – | 1841 |

## null:nli_neutral

| system | n | acc | macro-F1 | ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-b-small-v0-last | 2 | 1.000 | 1.000 | 0.145 | 0.071 | 1.00 | 1.00 | – | – | – | 7 |
| qwen3.8-27b (constrained JSON) | 2 | 0.500 | 0.333 | 0.475 | 0.927 | 1.00 | 0.50 | – | – | – | 2238 |
| qwen3.8-27b v2 prompt | 2 | 0.500 | 0.333 | 0.475 | 0.927 | 1.00 | 0.50 | – | – | – | 2098 |
| qwen3.8-27b (v3 prompt) | 2 | 0.500 | 0.333 | 0.475 | 0.927 | 1.00 | 0.50 | – | – | – | 2164 |

## null:oos

| system | n | acc | macro-F1 | ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-b-small-v0-last | 4 | 1.000 | 1.000 | 0.116 | 0.037 | 1.00 | 1.00 | – | – | – | 7 |
| qwen3.8-27b (constrained JSON) | 4 | 0.500 | 0.222 | 0.600 | 1.016 | 1.00 | 0.50 | – | – | – | 2317 |
| qwen3.8-27b v2 prompt | 4 | 0.500 | 0.222 | 0.525 | 0.977 | 1.00 | 0.50 | – | – | – | 2104 |
| qwen3.8-27b (v3 prompt) | 4 | 0.500 | 0.222 | 0.525 | 0.977 | 1.00 | 0.50 | – | – | – | 2174 |

## null:synthetic

| system | n | acc | macro-F1 | ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-b-small-v0-last | 2 | 0.000 | 0.000 | 0.886 | 1.675 | – | 0.00 | – | – | – | 11 |
| qwen3.8-27b (constrained JSON) | 2 | 1.000 | 1.000 | 0.000 | 0.000 | 1.00 | 1.00 | – | – | – | 6229 |
| qwen3.8-27b v2 prompt | 2 | 1.000 | 1.000 | 0.000 | 0.000 | 1.00 | 1.00 | – | – | – | 6311 |
| qwen3.8-27b (v3 prompt) | 2 | 1.000 | 1.000 | 0.000 | 0.000 | 1.00 | 0.50 | – | – | – | 6298 |

## null:unanswerable

| system | n | acc | macro-F1 | ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-b-small-v0-last | 4 | 0.750 | 0.429 | 0.165 | 0.378 | 1.00 | 0.75 | – | – | – | 26 |
| qwen3.8-27b (constrained JSON) | 4 | 0.750 | 0.429 | 0.237 | 0.463 | 1.00 | 0.75 | – | – | – | 3676 |
| qwen3.8-27b v2 prompt | 4 | 0.500 | 0.222 | 0.463 | 0.892 | 1.00 | 0.50 | – | – | – | 3735 |
| qwen3.8-27b (v3 prompt) | 4 | 0.500 | 0.222 | 0.463 | 0.892 | 1.00 | 0.50 | – | – | – | 3717 |

## Per source (accuracy / ECE / score MAE)

| source | kodiak-b-small-v0-last | qwen3.8-27b (constrained JSON) | qwen3.8-27b v2 prompt | qwen3.8-27b (v3 prompt) |
|---|---|---|---|---|
| banking77 | 0.750 / 0.276 | 0.850 / 0.155 | 0.850 / 0.150 | 0.850 / 0.148 |
| bias_in_bios | 0.727 / 0.320 | 0.864 / 0.165 | 0.818 / 0.182 | 0.818 / 0.182 |
| civil_comments | – / – / MAE 0.196 | – / – / MAE 0.000 | – / – / MAE 0.175 | – / – / MAE 0.257 |
| clinc_oos | 1.000 / 0.044 | 0.833 / 0.204 | 0.833 / 0.179 | 0.833 / 0.179 |
| commonsense_qa | 0.727 / 0.307 | 0.273 / 0.718 | 0.545 / 0.445 | 0.545 / 0.455 |
| glaive_fc_v2 | 1.000 / 0.014 | 0.800 / 0.200 | 0.600 / 0.400 | 0.600 / 0.400 |
| go_emotions | 0.667 / 0.464 | 0.333 / 0.521 | 0.333 / 0.542 | 0.333 / 0.533 |
| helpsteer2 | – / – / MAE 0.167 | – / – | – / – | – / – / MAE 0.100 |
| jailbreak_classification | 0.400 / 0.515 | 0.933 / 0.070 | 0.933 / 0.070 | 0.933 / 0.070 |
| kodiak_synth_v1 | 0.667 / 0.266 | 1.000 / 0.000 | 1.000 / 0.000 | 1.000 / 0.000 |
| massive | 0.812 / 0.134 | 0.625 / 0.397 | 0.562 / 0.462 | 0.562 / 0.462 |
| measuring_hate_speech | – / – / MAE 0.153 | – / – / MAE 0.083 | – / – / MAE 0.079 | – / – / MAE 0.226 |
| mnli | 0.800 / 0.313 | 0.600 / 0.390 | 0.600 / 0.390 | 0.600 / 0.390 |
| openbookqa | 0.636 / 0.417 | 0.273 / 0.736 | 1.000 / 0.034 | 1.000 / 0.034 |
| prompt_injections | 1.000 / 0.037 | 1.000 / 0.013 | 1.000 / 0.018 | 1.000 / 0.018 |
| qasper | 0.500 / 0.445 | 0.875 / 0.131 | 0.750 / 0.244 | 0.750 / 0.244 |
| scitail | 1.000 / 0.154 | 0.857 / 0.171 | 0.714 / 0.300 | 0.714 / 0.300 |
| sms_spam | 0.857 / 0.146 | 0.857 / 0.186 | 0.857 / 0.179 | 0.857 / 0.179 |
| toolace | 0.875 / 0.089 | 1.000 / 0.028 | 1.000 / 0.030 | 1.000 / 0.030 |
| ultrafeedback | 1.000 / 0.000 / MAE 0.167 | 1.000 / 0.000 | 0.000 / 0.950 | 0.000 / 0.950 / MAE 0.250 |
| winogrande | 0.500 / 0.425 | 0.600 / 0.350 | 0.600 / 0.405 | 0.700 / 0.305 |

## Systems

- **kodiak-b-small-v0-last**: `{"system": "kodiak-b-small-v0-last", "model": "runs/b-small-s1-v0/checkpoints/step_0003250.pt", "batched_ms_per_example": 7.036134509336355, "eval": "data/eval/kodiak-eval-v0.1.jsonl"}`
- **qwen3.8-27b (constrained JSON)**: `{"system": "qwen3.8-27b (constrained JSON)", "llm": "qwen3.8:27b", "eval": "data/eval/kodiak-eval-v0.1.jsonl", "limit": 200, "confidence": "verbalized", "prompt": "evidence quote, answer, confidence"}`
- **qwen3.8-27b v2 prompt**: `{"system": "qwen3.8-27b v2 prompt", "llm": "qwen3.8:27b", "eval": "data/eval/kodiak-eval-v0.1.jsonl", "limit": 200, "confidence": "verbalized", "prompt": "v2: judgments answerable; quote, answer, confidence"}`
- **qwen3.8-27b (v3 prompt)**: `{"system": "qwen3.8-27b (v3 prompt)", "llm": "qwen3.8:27b", "eval": "data/eval/kodiak-eval-v0.1.jsonl", "limit": 200, "confidence": "verbalized", "prompt": "v3: judgments answerable; numeric score schema; quote, answer, confidence"}`
