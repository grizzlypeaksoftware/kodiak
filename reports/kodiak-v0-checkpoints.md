# Kodiak eval report

Eval set: `data/eval/kodiak-eval-v0.1.jsonl`; examples compared: 2902


## overall

| system | n | acc | macro-F1 | ECE | Brier | abst-P | abst-R | score MAE | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-b-small-v0-best | 4189 | 0.746 | 0.763 | 0.065 | 0.371 | 0.92 | 0.76 | 0.203 | 0.51 | 8 |
| kodiak-b-small-v0-last | 4189 | 0.772 | 0.772 | 0.062 | 0.338 | 0.83 | 0.87 | 0.193 | 0.50 | 8 |
| kodiak-b-small-v0-last-uncal | 4189 | 0.772 | 0.772 | 0.093 | 0.347 | 0.83 | 0.87 | 0.193 | 0.49 | 8 |

## eval:indomain

| system | n | acc | macro-F1 | ECE | Brier | abst-P | abst-R | score MAE | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-b-small-v0-best | 2578 | 0.796 | 0.886 | 0.031 | 0.280 | 0.79 | 0.72 | 0.181 | 0.52 | 8 |
| kodiak-b-small-v0-last | 2578 | 0.813 | 0.900 | 0.036 | 0.272 | 0.78 | 0.81 | 0.174 | 0.50 | 8 |
| kodiak-b-small-v0-last-uncal | 2578 | 0.813 | 0.900 | 0.075 | 0.282 | 0.78 | 0.81 | 0.174 | 0.50 | 8 |

## eval:heldout

| system | n | acc | macro-F1 | ECE | Brier | abst-P | abst-R | score MAE | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-b-small-v0-best | 1250 | 0.635 | 0.632 | 0.164 | 0.574 | 0.00 | – | 0.252 | 0.50 | 7 |
| kodiak-b-small-v0-last | 1250 | 0.651 | 0.625 | 0.141 | 0.541 | 0.00 | – | 0.236 | 0.48 | 8 |
| kodiak-b-small-v0-last-uncal | 1250 | 0.651 | 0.625 | 0.142 | 0.543 | 0.00 | – | 0.236 | 0.47 | 8 |

## eval:null_construct

| system | n | acc | macro-F1 | ECE | Brier | abst-P | abst-R | score MAE | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-b-small-v0-best | 300 | 0.787 | 0.023 | 0.080 | 0.278 | 1.00 | 0.79 | – | – | 7 |
| kodiak-b-small-v0-last | 300 | 0.907 | 0.048 | 0.049 | 0.109 | 1.00 | 0.91 | – | – | 7 |
| kodiak-b-small-v0-last-uncal | 300 | 0.907 | 0.048 | 0.037 | 0.121 | 1.00 | 0.91 | – | – | 7 |

## eval:synthetic

| system | n | acc | macro-F1 | ECE | Brier | abst-P | abst-R | score MAE | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-b-small-v0-best | 61 | 0.696 | 0.567 | 0.222 | 0.539 | 0.60 | 0.38 | 0.162 | 0.75 | 12 |
| kodiak-b-small-v0-last | 61 | 0.625 | 0.480 | 0.272 | 0.597 | 0.50 | 0.38 | 0.138 | 0.75 | 12 |
| kodiak-b-small-v0-last-uncal | 61 | 0.625 | 0.480 | 0.301 | 0.634 | 0.50 | 0.38 | 0.138 | 0.75 | 13 |

## null:gold_removed

| system | n | acc | macro-F1 | ECE | Brier | abst-P | abst-R | score MAE | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-b-small-v0-best | 150 | 0.580 | 0.019 | 0.171 | 0.550 | 1.00 | 0.58 | – | – | 7 |
| kodiak-b-small-v0-last | 150 | 0.820 | 0.045 | 0.099 | 0.214 | 1.00 | 0.82 | – | – | 7 |
| kodiak-b-small-v0-last-uncal | 150 | 0.820 | 0.045 | 0.086 | 0.239 | 1.00 | 0.82 | – | – | 7 |

## null:mismatch

| system | n | acc | macro-F1 | ECE | Brier | abst-P | abst-R | score MAE | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-b-small-v0-best | 150 | 0.993 | 0.498 | 0.002 | 0.007 | 1.00 | 0.99 | – | – | 7 |
| kodiak-b-small-v0-last | 150 | 0.993 | 0.498 | 0.002 | 0.003 | 1.00 | 0.99 | – | – | 8 |
| kodiak-b-small-v0-last-uncal | 150 | 0.993 | 0.498 | 0.003 | 0.004 | 1.00 | 0.99 | – | – | 7 |

## null:nli_neutral

| system | n | acc | macro-F1 | ECE | Brier | abst-P | abst-R | score MAE | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-b-small-v0-best | 30 | 0.833 | 0.303 | 0.172 | 0.182 | 1.00 | 0.83 | – | – | 7 |
| kodiak-b-small-v0-last | 30 | 0.833 | 0.303 | 0.116 | 0.181 | 1.00 | 0.83 | – | – | 7 |
| kodiak-b-small-v0-last-uncal | 30 | 0.833 | 0.303 | 0.137 | 0.197 | 1.00 | 0.83 | – | – | 7 |

## null:oos

| system | n | acc | macro-F1 | ECE | Brier | abst-P | abst-R | score MAE | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-b-small-v0-best | 22 | 0.545 | 0.071 | 0.266 | 0.615 | 1.00 | 0.55 | – | – | 7 |
| kodiak-b-small-v0-last | 22 | 0.955 | 0.488 | 0.104 | 0.081 | 1.00 | 0.95 | – | – | 7 |
| kodiak-b-small-v0-last-uncal | 22 | 0.955 | 0.488 | 0.085 | 0.086 | 1.00 | 0.95 | – | – | 7 |

## null:synthetic

| system | n | acc | macro-F1 | ECE | Brier | abst-P | abst-R | score MAE | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-b-small-v0-best | 8 | 0.286 | 0.074 | 0.681 | 1.170 | 1.00 | 0.38 | – | – | 10 |
| kodiak-b-small-v0-last | 8 | 0.429 | 0.120 | 0.514 | 1.004 | 1.00 | 0.38 | – | – | 11 |
| kodiak-b-small-v0-last-uncal | 8 | 0.429 | 0.120 | 0.519 | 1.051 | 1.00 | 0.38 | – | – | 11 |

## null:unanswerable

| system | n | acc | macro-F1 | ECE | Brier | abst-P | abst-R | score MAE | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|
| kodiak-b-small-v0-best | 41 | 0.854 | 0.461 | 0.099 | 0.220 | 1.00 | 0.85 | – | – | 26 |
| kodiak-b-small-v0-last | 41 | 0.854 | 0.307 | 0.110 | 0.212 | 1.00 | 0.85 | – | – | 26 |
| kodiak-b-small-v0-last-uncal | 41 | 0.854 | 0.307 | 0.122 | 0.236 | 1.00 | 0.85 | – | – | 26 |

## Per source (accuracy / ECE / score MAE)

| source | kodiak-b-small-v0-best | kodiak-b-small-v0-last | kodiak-b-small-v0-last-uncal |
|---|---|---|---|
| banking77 | 0.720 / 0.060 | 0.692 / 0.116 | 0.692 / 0.147 |
| bias_in_bios | 0.644 / 0.105 | 0.624 / 0.128 | 0.624 / 0.085 |
| civil_comments | 1.000 / 0.003 / MAE 0.124 | 1.000 / 0.003 / MAE 0.104 | 1.000 / 0.001 / MAE 0.104 |
| clinc_oos | 0.847 / 0.066 | 0.955 / 0.035 | 0.955 / 0.029 |
| commonsense_qa | 0.613 / 0.095 | 0.676 / 0.115 | 0.676 / 0.118 |
| glaive_fc_v2 | 0.992 / 0.011 | 0.967 / 0.023 | 0.967 / 0.015 |
| go_emotions | 0.710 / 0.076 | 0.752 / 0.079 | 0.752 / 0.108 |
| helpsteer2 | 1.000 / 0.001 / MAE 0.170 | 1.000 / 0.000 / MAE 0.170 | 1.000 / 0.000 / MAE 0.170 |
| jailbreak_classification | 0.540 / 0.403 | 0.636 / 0.221 | 0.636 / 0.248 |
| kodiak_synth_v1 | 0.696 / 0.222 / MAE 0.162 | 0.625 / 0.272 / MAE 0.138 | 0.625 / 0.301 / MAE 0.138 |
| massive | 0.801 / 0.065 | 0.892 / 0.046 | 0.892 / 0.051 |
| measuring_hate_speech | – / – / MAE 0.252 | – / – / MAE 0.236 | – / – / MAE 0.236 |
| mnli | 0.720 / 0.135 | 0.780 / 0.101 | 0.780 / 0.111 |
| openbookqa | 0.615 / 0.138 | 0.632 / 0.156 | 0.632 / 0.192 |
| prompt_injections | 0.974 / 0.047 | 0.885 / 0.061 | 0.885 / 0.075 |
| qasper | 0.700 / 0.131 | 0.610 / 0.284 | 0.610 / 0.321 |
| scitail | 0.860 / 0.117 | 0.940 / 0.049 | 0.940 / 0.052 |
| sms_spam | 0.980 / 0.015 | 0.990 / 0.017 | 0.990 / 0.013 |
| toolace | 0.981 / 0.011 | 0.981 / 0.011 | 0.981 / 0.010 |
| ultrafeedback | 1.000 / 0.002 / MAE 0.225 | 1.000 / 0.001 / MAE 0.216 | 1.000 / 0.000 / MAE 0.216 |
| winogrande | 0.600 / 0.201 | 0.626 / 0.164 | 0.626 / 0.207 |

## Systems

- **kodiak-b-small-v0-best**: `{"system": "kodiak-b-small-v0-best", "model": "runs/b-small-s1-v0", "batched_ms_per_example": 7.041356812900691, "eval": "data/eval/kodiak-eval-v0.1.jsonl"}`
- **kodiak-b-small-v0-last**: `{"system": "kodiak-b-small-v0-last", "model": "runs/b-small-s1-v0/checkpoints/step_0003250.pt", "batched_ms_per_example": 7.036134509336355, "eval": "data/eval/kodiak-eval-v0.1.jsonl"}`
- **kodiak-b-small-v0-last-uncal**: `{"system": "kodiak-b-small-v0-last-uncal", "model": "runs/b-small-s1-v0/checkpoints/step_0003250.pt", "batched_ms_per_example": 7.051471250130443, "eval": "data/eval/kodiak-eval-v0.1.jsonl"}`
