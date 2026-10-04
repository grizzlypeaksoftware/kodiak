# Kodiak eval report

Eval set: `data/eval/kodiak-eval-v0.2.jsonl`; examples compared: 6102


## overall

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 7389 | 0.723 | 0.741 | 0.853 | 0.060 | 0.038 | 0.390 | 0.87 | 0.63 | 0.203 | 1.00 | 0.75 | 40 |
| e21-xl-skills2-s1 | 7389 | 0.725 | 0.737 | 0.858 | 0.054 | 0.034 | 0.381 | 0.94 | 0.64 | 0.205 | 1.00 | 0.74 | 38 |

## eval:indomain

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 2578 | 0.877 | 0.879 | 0.928 | 0.017 | 0.017 | 0.172 | 0.91 | 0.83 | 0.148 | 1.00 | 0.94 | 40 |
| e21-xl-skills2-s1 | 2578 | 0.878 | 0.882 | 0.935 | 0.021 | 0.020 | 0.178 | 0.94 | 0.79 | 0.149 | 1.00 | 0.94 | 39 |

## eval:heldout

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 4450 | 0.635 | 0.680 | 0.671 | 0.094 | 0.052 | 0.516 | 0.00 | 0.00 | 0.271 | 1.00 | 0.51 | 39 |
| e21-xl-skills2-s1 | 4450 | 0.637 | 0.674 | 0.674 | 0.078 | 0.048 | 0.501 | 0.27 | 0.04 | 0.274 | 1.00 | 0.50 | 38 |

## eval:heldout_v01

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 1250 | 0.821 | 0.845 | 0.735 | 0.050 | 0.048 | 0.298 | 0.00 | – | 0.252 | 1.00 | 0.54 | 39 |
| e21-xl-skills2-s1 | 1250 | 0.851 | 0.864 | 0.751 | 0.077 | 0.045 | 0.273 | 0.00 | – | 0.257 | 1.00 | 0.55 | 37 |

## eval:heldout_v02

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 3200 | 0.585 | 0.633 | 0.529 | 0.120 | 0.078 | 0.575 | 0.00 | 0.00 | 0.295 | 1.00 | 0.47 | 40 |
| e21-xl-skills2-s1 | 3200 | 0.580 | 0.619 | 0.511 | 0.099 | 0.062 | 0.562 | 0.70 | 0.04 | 0.296 | 1.00 | 0.43 | 38 |

## eval:null_construct

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 300 | 0.957 | – | 0.081 | 0.025 | – | 0.041 | 1.00 | 0.96 | – | – | – | 37 |
| e21-xl-skills2-s1 | 300 | 0.957 | – | 0.075 | 0.014 | – | 0.026 | 1.00 | 0.96 | – | – | – | 37 |

## eval:synthetic

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 61 | 0.982 | 1.000 | 0.979 | 0.037 | 0.019 | 0.050 | 1.00 | 0.75 | 0.084 | 1.00 | 1.00 | 71 |
| e21-xl-skills2-s1 | 61 | 0.982 | 1.000 | 0.979 | 0.037 | 0.027 | 0.046 | 1.00 | 0.75 | 0.086 | 1.00 | 1.00 | 62 |

## null:gold_removed

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 150 | 0.913 | – | 0.080 | 0.052 | – | 0.082 | 1.00 | 0.91 | – | – | – | 35 |
| e21-xl-skills2-s1 | 150 | 0.913 | – | 0.073 | 0.032 | – | 0.051 | 1.00 | 0.91 | – | – | – | 37 |

## null:mismatch

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 150 | 1.000 | – | 1.000 | 0.002 | – | 0.000 | 1.00 | 1.00 | – | – | – | 38 |
| e21-xl-skills2-s1 | 150 | 1.000 | – | 1.000 | 0.001 | – | 0.000 | 1.00 | 1.00 | – | – | – | 36 |

## null:nli_neutral

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 30 | 0.833 | – | 0.303 | 0.118 | – | 0.183 | 1.00 | 0.83 | – | – | – | 42 |
| e21-xl-skills2-s1 | 30 | 0.767 | – | 0.289 | 0.126 | – | 0.169 | 1.00 | 0.77 | – | – | – | 38 |

## null:not_mentioned

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 186 | 0.000 | – | 0.000 | 0.689 | – | 1.517 | – | 0.00 | – | – | – | 57 |
| e21-xl-skills2-s1 | 186 | 0.038 | – | 0.024 | 0.669 | – | 1.423 | 1.00 | 0.04 | – | – | – | 56 |

## null:oos

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 22 | 0.909 | – | 0.317 | 0.041 | – | 0.096 | 1.00 | 0.91 | – | – | – | 38 |
| e21-xl-skills2-s1 | 22 | 0.909 | – | 0.317 | 0.059 | – | 0.105 | 1.00 | 0.91 | – | – | – | 38 |

## null:synthetic

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 8 | 0.857 | – | 0.462 | 0.139 | – | 0.272 | 1.00 | 0.75 | – | – | – | 71 |
| e21-xl-skills2-s1 | 8 | 0.857 | – | 0.462 | 0.129 | – | 0.225 | 1.00 | 0.75 | – | – | – | 62 |

## null:unanswerable

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 41 | 0.902 | – | 0.316 | 0.047 | – | 0.093 | 1.00 | 0.90 | – | – | – | 129 |
| e21-xl-skills2-s1 | 41 | 0.878 | – | 0.312 | 0.060 | – | 0.116 | 1.00 | 0.88 | – | – | – | 115 |

## Per source (accuracy / ECE / score MAE)

| source | e18-xl-wording-s1 | e21-xl-skills2-s1 |
|---|---|---|
| arxiv_field | 0.665 / 0.071 | 0.637 / 0.085 |
| banking77 | 0.784 / 0.077 | 0.796 / 0.099 |
| bias_in_bios | 0.792 / 0.089 | 0.816 / 0.123 |
| casehold | 0.445 / 0.108 | 0.453 / 0.092 |
| civil_comments | 1.000 / 0.002 / MAE 0.090 | 1.000 / 0.002 / MAE 0.089 |
| clickbait17 | – / – / MAE 0.295 | – / – / MAE 0.296 |
| clinc_oos | 0.975 / 0.008 | 0.981 / 0.012 |
| commonsense_qa | 0.824 / 0.042 | 0.824 / 0.082 |
| contract_nli | 0.463 / 0.301 | 0.430 / 0.339 |
| ethics_commonsense | 0.520 / 0.230 | 0.525 / 0.218 |
| fin_tweets_sentiment | 0.715 / 0.151 | 0.710 / 0.142 |
| fin_tweets_topic | 0.595 / 0.111 | 0.620 / 0.103 |
| glaive_fc_v2 | 0.992 / 0.017 | 0.992 / 0.017 |
| go_emotions | 0.734 / 0.072 | 0.743 / 0.057 |
| helpsteer2 | 1.000 / 0.000 / MAE 0.154 | 1.000 / 0.000 / MAE 0.154 |
| jailbreak_classification | 0.888 / 0.077 | 0.940 / 0.056 |
| kodiak_synth_v1 | 0.982 / 0.037 / MAE 0.084 | 0.982 / 0.037 / MAE 0.086 |
| massive | 0.917 / 0.021 | 0.913 / 0.028 |
| measuring_hate_speech | – / – / MAE 0.252 | – / – / MAE 0.257 |
| mnli | 0.880 / 0.081 | 0.900 / 0.063 |
| openbookqa | 0.803 / 0.073 | 0.803 / 0.094 |
| poem_sentiment | 0.690 / 0.069 | 0.688 / 0.045 |
| prompt_injections | 0.962 / 0.043 | 0.923 / 0.052 |
| qasper | 0.820 / 0.098 | 0.790 / 0.049 |
| scitail | 0.960 / 0.027 | 0.970 / 0.041 |
| sms_spam | 0.980 / 0.018 | 0.990 / 0.005 |
| toolace | 0.990 / 0.006 | 1.000 / 0.015 |
| ultrafeedback | 1.000 / 0.000 / MAE 0.169 | 1.000 / 0.000 / MAE 0.172 |
| winogrande | 0.809 / 0.091 | 0.817 / 0.096 |

## Systems

- **e18-xl-wording-s1**: `{"system": "e18-xl-wording-s1", "model": "runs/b-xl-s1-e18-s1/checkpoints/step_0006000.pt", "batched_ms_per_example": 22.07695977546834, "eval": "data/eval/kodiak-eval-v0.2.jsonl"}`
- **e21-xl-skills2-s1**: `{"system": "e21-xl-skills2-s1", "model": "runs/b-xl-s1-e21-s1/checkpoints/step_0006000.pt", "batched_ms_per_example": 19.963214093250272, "eval": "data/eval/kodiak-eval-v0.2.jsonl"}`
