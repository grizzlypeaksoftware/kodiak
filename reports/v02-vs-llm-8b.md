# Kodiak eval report

Eval set: `data/eval/kodiak-eval-v0.2.jsonl`; examples compared: 5151; **choice questions only**


## overall

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 5384 | 0.625 | 0.632 | 0.780 | 0.092 | 0.074 | 0.511 | 0.91 | 0.61 | – | – | – | 8 |
| large-v2-s0 | 5384 | 0.675 | 0.678 | 0.825 | 0.072 | 0.066 | 0.433 | 0.92 | 0.67 | – | – | – | 17 |
| zs-nli-modernbert-large | 5384 | 0.385 | 0.596 | 0.454 | 0.414 | 0.094 | 1.020 | 0.18 | 0.94 | – | – | – | 17 |
| qwen3-8b | 5384 | 0.658 | 0.709 | 0.766 | 0.287 | 0.244 | 0.638 | 0.80 | 0.26 | – | – | – | 2274 |

## eval:indomain

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 1478 | 0.813 | 0.816 | 0.899 | 0.017 | 0.024 | 0.252 | 0.91 | 0.84 | – | – | – | 8 |
| large-v2-s0 | 1478 | 0.855 | 0.856 | 0.932 | 0.015 | 0.017 | 0.200 | 0.93 | 0.88 | – | – | – | 17 |
| zs-nli-modernbert-large | 1478 | 0.304 | 0.647 | 0.351 | 0.530 | 0.058 | 1.191 | 0.09 | 0.99 | – | – | – | 12 |
| qwen3-8b | 1478 | 0.710 | 0.751 | 0.807 | 0.239 | 0.206 | 0.538 | 0.55 | 0.17 | – | – | – | 2316 |

## eval:heldout

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 3550 | 0.519 | 0.552 | 0.556 | 0.130 | 0.098 | 0.662 | 0.00 | 0.00 | – | – | – | 8 |
| large-v2-s0 | 3550 | 0.574 | 0.601 | 0.612 | 0.110 | 0.092 | 0.567 | 0.52 | 0.16 | – | – | – | 17 |
| zs-nli-modernbert-large | 3550 | 0.365 | 0.569 | 0.560 | 0.414 | 0.118 | 1.037 | 0.10 | 0.94 | – | – | – | 22 |
| qwen3-8b | 3550 | 0.651 | 0.688 | 0.716 | 0.293 | 0.263 | 0.651 | 0.11 | 0.02 | – | – | – | 2314 |

## eval:heldout_v01

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 750 | 0.703 | 0.721 | 0.638 | 0.088 | 0.061 | 0.454 | 0.00 | – | – | – | – | 7 |
| large-v2-s0 | 750 | 0.713 | 0.725 | 0.674 | 0.138 | 0.099 | 0.454 | 0.00 | – | – | – | – | 16 |
| zs-nli-modernbert-large | 750 | 0.360 | 0.708 | 0.631 | 0.520 | 0.095 | 1.151 | 0.00 | – | – | – | – | 18 |
| qwen3-8b | 750 | 0.827 | 0.835 | 0.766 | 0.126 | 0.105 | 0.324 | 0.00 | – | – | – | – | 2350 |

## eval:heldout_v02

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 2800 | 0.469 | 0.503 | 0.383 | 0.177 | 0.143 | 0.718 | 0.00 | 0.00 | – | – | – | 8 |
| large-v2-s0 | 2800 | 0.537 | 0.565 | 0.468 | 0.112 | 0.097 | 0.598 | 0.78 | 0.16 | – | – | – | 18 |
| zs-nli-modernbert-large | 2800 | 0.367 | 0.529 | 0.382 | 0.382 | 0.128 | 1.007 | 0.12 | 0.94 | – | – | – | 24 |
| qwen3-8b | 2800 | 0.604 | 0.646 | 0.603 | 0.337 | 0.309 | 0.739 | 0.60 | 0.02 | – | – | – | 2305 |

## eval:null_construct

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 300 | 0.910 | – | 0.048 | 0.037 | – | 0.070 | 1.00 | 0.91 | – | – | – | 7 |
| large-v2-s0 | 300 | 0.923 | – | 0.048 | 0.026 | – | 0.051 | 1.00 | 0.92 | – | – | – | 15 |
| zs-nli-modernbert-large | 300 | 0.930 | – | 0.057 | 0.042 | – | 0.094 | 1.00 | 0.93 | – | – | – | 11 |
| qwen3-8b | 300 | 0.430 | – | 0.012 | 0.514 | – | 1.069 | 1.00 | 0.43 | – | – | – | 1726 |

## eval:synthetic

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 56 | 0.911 | 0.918 | 0.835 | 0.044 | 0.039 | 0.100 | 1.00 | 0.86 | – | – | – | 14 |
| large-v2-s0 | 56 | 0.964 | 0.959 | 0.923 | 0.019 | 0.035 | 0.055 | 1.00 | 1.00 | – | – | – | 28 |
| zs-nli-modernbert-large | 56 | 0.804 | 1.000 | 0.775 | 0.193 | 0.098 | 0.344 | 0.38 | 0.86 | – | – | – | 89 |
| qwen3-8b | 56 | 0.946 | 1.000 | 0.938 | 0.028 | 0.005 | 0.123 | 1.00 | 0.57 | – | – | – | 5606 |

## null:gold_removed

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 150 | 0.827 | – | 0.045 | 0.090 | – | 0.138 | 1.00 | 0.83 | – | – | – | – |
| large-v2-s0 | 150 | 0.847 | – | 0.046 | 0.062 | – | 0.101 | 1.00 | 0.85 | – | – | – | – |
| zs-nli-modernbert-large | 150 | 0.860 | – | 0.054 | 0.079 | – | 0.183 | 1.00 | 0.86 | – | – | – | 13 |
| qwen3-8b | 150 | 0.220 | – | 0.007 | 0.721 | – | 1.460 | 1.00 | 0.22 | – | – | – | 1867 |

## null:mismatch

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 150 | 0.993 | – | 0.498 | 0.002 | – | 0.003 | 1.00 | 0.99 | – | – | – | 7 |
| large-v2-s0 | 150 | 1.000 | – | 1.000 | 0.001 | – | 0.000 | 1.00 | 1.00 | – | – | – | 15 |
| zs-nli-modernbert-large | 150 | 1.000 | – | 1.000 | 0.030 | – | 0.005 | 1.00 | 1.00 | – | – | – | 10 |
| qwen3-8b | 150 | 0.640 | – | 0.260 | 0.313 | – | 0.679 | 1.00 | 0.64 | – | – | – | 1549 |

## null:nli_neutral

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 30 | 0.767 | – | 0.289 | 0.151 | – | 0.147 | 1.00 | 0.77 | – | – | – | – |
| large-v2-s0 | 30 | 0.867 | – | 0.310 | 0.087 | – | 0.117 | 1.00 | 0.87 | – | – | – | – |
| zs-nli-modernbert-large | 30 | 1.000 | – | 1.000 | 0.076 | – | 0.030 | 1.00 | 1.00 | – | – | – | 9 |
| qwen3-8b | 30 | 0.000 | – | 0.000 | 0.947 | – | 1.844 | – | 0.00 | – | – | – | 2001 |

## null:not_mentioned

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 186 | 0.000 | – | 0.000 | 0.715 | – | 1.605 | – | 0.00 | – | – | – | 12 |
| large-v2-s0 | 186 | 0.156 | – | 0.090 | 0.437 | – | 0.895 | 1.00 | 0.16 | – | – | – | 27 |
| zs-nli-modernbert-large | 186 | 0.941 | – | 0.323 | 0.036 | – | 0.080 | 1.00 | 0.94 | – | – | – | 25 |
| qwen3-8b | 186 | 0.016 | – | 0.011 | 0.934 | – | 1.824 | 1.00 | 0.02 | – | – | – | 3159 |

## null:oos

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 22 | 0.864 | – | 0.232 | 0.100 | – | 0.126 | 1.00 | 0.86 | – | – | – | – |
| large-v2-s0 | 22 | 0.909 | – | 0.317 | 0.057 | – | 0.103 | 1.00 | 0.91 | – | – | – | – |
| zs-nli-modernbert-large | 22 | 0.955 | – | 0.488 | 0.041 | – | 0.028 | 1.00 | 0.95 | – | – | – | 14 |
| qwen3-8b | 22 | 0.409 | – | 0.041 | 0.530 | – | 1.075 | 1.00 | 0.41 | – | – | – | 1895 |

## null:synthetic

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 7 | 0.857 | – | 0.462 | 0.070 | – | 0.070 | 1.00 | 0.86 | – | – | – | 14 |
| large-v2-s0 | 7 | 1.000 | – | 1.000 | 0.009 | – | 0.000 | 1.00 | 1.00 | – | – | – | 28 |
| zs-nli-modernbert-large | 7 | 0.857 | – | 0.462 | 0.103 | – | 0.195 | 1.00 | 0.86 | – | – | – | 120 |
| qwen3-8b | 7 | 0.571 | – | 0.182 | 0.600 | – | 0.982 | 1.00 | 0.57 | – | – | – | 5816 |

## null:unanswerable

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 41 | 0.878 | – | 0.312 | 0.084 | – | 0.126 | 1.00 | 0.88 | – | – | – | 30 |
| large-v2-s0 | 41 | 0.878 | – | 0.312 | 0.061 | – | 0.106 | 1.00 | 0.88 | – | – | – | 57 |
| zs-nli-modernbert-large | 41 | 1.000 | – | 1.000 | 0.044 | – | 0.004 | 1.00 | 1.00 | – | – | – | 28 |
| qwen3-8b | 41 | 0.171 | – | 0.097 | 0.779 | – | 1.538 | 1.00 | 0.17 | – | – | – | 4406 |

## Per source (accuracy / ECE / score MAE)

| source | ab-B-v2 | large-v2-s0 | zs-nli-modernbert-large | qwen3-8b |
|---|---|---|---|---|
| arxiv_field | 0.448 / 0.100 | 0.568 / 0.073 | 0.525 / 0.178 | 0.755 / 0.196 |
| banking77 | 0.692 / 0.118 | 0.764 / 0.126 | 0.560 / 0.283 | 0.824 / 0.130 |
| bias_in_bios | 0.616 / 0.115 | 0.764 / 0.120 | 0.516 / 0.341 | 0.780 / 0.180 |
| casehold | 0.453 / 0.135 | 0.450 / 0.121 | 0.113 / 0.699 | 0.632 / 0.317 |
| civil_comments | 1.000 / 0.019 | 1.000 / 0.002 | 1.000 / 0.026 | 0.750 / 0.269 |
| clinc_oos | 0.930 / 0.037 | 0.955 / 0.021 | 0.796 / 0.111 | 0.720 / 0.227 |
| commonsense_qa | 0.697 / 0.065 | 0.782 / 0.076 | 0.289 / 0.625 | 0.592 / 0.363 |
| contract_nli | 0.440 / 0.324 | 0.510 / 0.189 | 0.535 / 0.342 | 0.372 / 0.577 |
| ethics_commonsense | 0.542 / 0.249 | 0.507 / 0.289 | 0.030 / 0.853 | 0.497 / 0.449 |
| fin_tweets_sentiment | 0.705 / 0.140 | 0.760 / 0.086 | 0.780 / 0.059 | 0.710 / 0.230 |
| fin_tweets_topic | 0.438 / 0.064 | 0.562 / 0.080 | 0.365 / 0.229 | 0.632 / 0.317 |
| glaive_fc_v2 | 0.983 / 0.013 | 1.000 / 0.020 | 0.306 / 0.608 | 0.826 / 0.149 |
| go_emotions | 0.715 / 0.097 | 0.748 / 0.089 | 0.360 / 0.313 | 0.463 / 0.463 |
| helpsteer2 | 1.000 / 0.002 | 1.000 / 0.000 | 1.000 / 0.020 | 0.778 / 0.246 |
| jailbreak_classification | 0.800 / 0.094 | 0.612 / 0.259 | 0.004 / 0.947 | 0.876 / 0.087 |
| kodiak_synth_v1 | 0.911 / 0.044 | 0.964 / 0.019 | 0.804 / 0.193 | 0.946 / 0.028 |
| massive | 0.877 / 0.045 | 0.892 / 0.024 | 0.581 / 0.243 | 0.635 / 0.311 |
| mnli | 0.800 / 0.079 | 0.830 / 0.057 | 0.430 / 0.469 | 0.750 / 0.199 |
| openbookqa | 0.581 / 0.174 | 0.598 / 0.177 | 0.145 / 0.805 | 0.684 / 0.266 |
| poem_sentiment | 0.260 / 0.316 | 0.400 / 0.164 | 0.220 / 0.438 | 0.627 / 0.293 |
| prompt_injections | 0.936 / 0.064 | 0.923 / 0.059 | 0.013 / 0.943 | 0.641 / 0.325 |
| qasper | 0.700 / 0.095 | 0.830 / 0.111 | 0.440 / 0.464 | 0.570 / 0.387 |
| scitail | 0.910 / 0.046 | 0.960 / 0.024 | 0.390 / 0.441 | 0.740 / 0.219 |
| sms_spam | 0.980 / 0.014 | 0.990 / 0.020 | 0.188 / 0.786 | 0.624 / 0.326 |
| toolace | 0.990 / 0.027 | 1.000 / 0.020 | 0.171 / 0.711 | 0.895 / 0.104 |
| ultrafeedback | 1.000 / 0.001 | 1.000 / 0.001 | 1.000 / 0.038 | 0.731 / 0.313 |
| winogrande | 0.687 / 0.139 | 0.800 / 0.076 | 0.487 / 0.255 | 0.661 / 0.290 |

## Systems

- **ab-B-v2**: `{"system": "ab-B-v2", "model": "runs/b-small-s1-B-v2/checkpoints/step_0006000.pt", "batched_ms_per_example": 6.996118311407927, "eval": "data/eval/kodiak-eval-v0.2.jsonl"}`
- **large-v2-s0**: `{"system": "large-v2-s0", "model": "runs/b-base-s1-v2-s0/checkpoints/step_0006000.pt", "batched_ms_per_example": 11.71031278402092, "eval": "data/eval/kodiak-eval-v0.2.jsonl"}`
- **zs-nli-modernbert-large**: `{"system": "zs-nli-modernbert-large", "model": "MoritzLaurer/ModernBERT-large-zeroshot-v2.0", "kind": "nli", "eval": "data/eval/kodiak-eval-v0.2.jsonl", "types": "choice only", "abstain_rule": "abstain if best label's independent probability < 0.5", "latency": "one example (all choice questions) per batch, CUDA-synchronized"}`
- **qwen3-8b**: `{"system": "qwen3-8b", "llm": "qwen3:8b", "eval": "data/eval/kodiak-eval-v0.2.jsonl", "limit": 0, "confidence": "verbalized", "prompt": "v3: judgments answerable; numeric score schema; quote, answer, confidence"}`
