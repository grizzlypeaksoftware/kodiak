# Kodiak eval report

Eval set: `data/eval/kodiak-eval-v0.2.jsonl`; examples compared: 6102


## overall

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 7389 | 0.723 | 0.741 | 0.853 | 0.060 | 0.038 | 0.390 | 0.87 | 0.63 | 0.203 | 1.00 | 0.75 | 40 |
| e20-xl-consistency-s1 | 7389 | 0.721 | 0.737 | 0.832 | 0.062 | 0.034 | 0.394 | 0.89 | 0.63 | 0.205 | 1.00 | 0.75 | 39 |

## eval:indomain

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 2578 | 0.877 | 0.879 | 0.928 | 0.017 | 0.017 | 0.172 | 0.91 | 0.83 | 0.148 | 1.00 | 0.94 | 40 |
| e20-xl-consistency-s1 | 2578 | 0.863 | 0.870 | 0.910 | 0.024 | 0.024 | 0.187 | 0.89 | 0.79 | 0.152 | 1.00 | 0.92 | 39 |

## eval:heldout

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 4450 | 0.635 | 0.680 | 0.671 | 0.094 | 0.052 | 0.516 | 0.00 | 0.00 | 0.271 | 1.00 | 0.51 | 39 |
| e20-xl-consistency-s1 | 4450 | 0.639 | 0.678 | 0.662 | 0.090 | 0.047 | 0.515 | 0.08 | 0.02 | 0.269 | 1.00 | 0.54 | 39 |

## eval:heldout_v01

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 1250 | 0.821 | 0.845 | 0.735 | 0.050 | 0.048 | 0.298 | 0.00 | – | 0.252 | 1.00 | 0.54 | 39 |
| e20-xl-consistency-s1 | 1250 | 0.829 | 0.840 | 0.737 | 0.072 | 0.065 | 0.294 | 0.00 | – | 0.257 | 1.00 | 0.55 | 38 |

## eval:heldout_v02

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 3200 | 0.585 | 0.633 | 0.529 | 0.120 | 0.078 | 0.575 | 0.00 | 0.00 | 0.295 | 1.00 | 0.47 | 40 |
| e20-xl-consistency-s1 | 3200 | 0.588 | 0.632 | 0.498 | 0.113 | 0.067 | 0.575 | 0.12 | 0.02 | 0.284 | 1.00 | 0.53 | 40 |

## eval:null_construct

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 300 | 0.957 | – | 0.081 | 0.025 | – | 0.041 | 1.00 | 0.96 | – | – | – | 37 |
| e20-xl-consistency-s1 | 300 | 0.947 | – | 0.061 | 0.020 | – | 0.045 | 1.00 | 0.95 | – | – | – | 37 |

## eval:synthetic

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 61 | 0.982 | 1.000 | 0.979 | 0.037 | 0.019 | 0.050 | 1.00 | 0.75 | 0.084 | 1.00 | 1.00 | 71 |
| e20-xl-consistency-s1 | 61 | 0.982 | 1.000 | 0.979 | 0.033 | 0.017 | 0.040 | 1.00 | 0.75 | 0.077 | 1.00 | 1.00 | 66 |

## null:gold_removed

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 150 | 0.913 | – | 0.080 | 0.052 | – | 0.082 | 1.00 | 0.91 | – | – | – | 35 |
| e20-xl-consistency-s1 | 150 | 0.893 | – | 0.059 | 0.040 | – | 0.089 | 1.00 | 0.89 | – | – | – | 38 |

## null:mismatch

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 150 | 1.000 | – | 1.000 | 0.002 | – | 0.000 | 1.00 | 1.00 | – | – | – | 38 |
| e20-xl-consistency-s1 | 150 | 1.000 | – | 1.000 | 0.000 | – | 0.000 | 1.00 | 1.00 | – | – | – | 37 |

## null:nli_neutral

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 30 | 0.833 | – | 0.303 | 0.118 | – | 0.183 | 1.00 | 0.83 | – | – | – | 42 |
| e20-xl-consistency-s1 | 30 | 0.867 | – | 0.310 | 0.104 | – | 0.138 | 1.00 | 0.87 | – | – | – | 38 |

## null:not_mentioned

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 186 | 0.000 | – | 0.000 | 0.689 | – | 1.517 | – | 0.00 | – | – | – | 57 |
| e20-xl-consistency-s1 | 186 | 0.016 | – | 0.011 | 0.685 | – | 1.403 | 1.00 | 0.02 | – | – | – | 60 |

## null:oos

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 22 | 0.909 | – | 0.317 | 0.041 | – | 0.096 | 1.00 | 0.91 | – | – | – | 38 |
| e20-xl-consistency-s1 | 22 | 0.727 | – | 0.120 | 0.125 | – | 0.172 | 1.00 | 0.73 | – | – | – | 39 |

## null:synthetic

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 8 | 0.857 | – | 0.462 | 0.139 | – | 0.272 | 1.00 | 0.75 | – | – | – | 71 |
| e20-xl-consistency-s1 | 8 | 0.857 | – | 0.462 | 0.139 | – | 0.268 | 1.00 | 0.75 | – | – | – | 66 |

## null:unanswerable

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 41 | 0.902 | – | 0.316 | 0.047 | – | 0.093 | 1.00 | 0.90 | – | – | – | 129 |
| e20-xl-consistency-s1 | 41 | 0.878 | – | 0.312 | 0.070 | – | 0.119 | 1.00 | 0.88 | – | – | – | 115 |

## Per source (accuracy / ECE / score MAE)

| source | e18-xl-wording-s1 | e20-xl-consistency-s1 |
|---|---|---|
| arxiv_field | 0.665 / 0.071 | 0.645 / 0.083 |
| banking77 | 0.784 / 0.077 | 0.804 / 0.085 |
| bias_in_bios | 0.792 / 0.089 | 0.796 / 0.157 |
| casehold | 0.445 / 0.108 | 0.492 / 0.089 |
| civil_comments | 1.000 / 0.002 / MAE 0.090 | 1.000 / 0.001 / MAE 0.092 |
| clickbait17 | – / – / MAE 0.295 | – / – / MAE 0.284 |
| clinc_oos | 0.975 / 0.008 | 0.917 / 0.030 |
| commonsense_qa | 0.824 / 0.042 | 0.824 / 0.088 |
| contract_nli | 0.463 / 0.301 | 0.427 / 0.343 |
| ethics_commonsense | 0.520 / 0.230 | 0.550 / 0.242 |
| fin_tweets_sentiment | 0.715 / 0.151 | 0.757 / 0.081 |
| fin_tweets_topic | 0.595 / 0.111 | 0.583 / 0.115 |
| glaive_fc_v2 | 0.992 / 0.017 | 0.992 / 0.007 |
| go_emotions | 0.734 / 0.072 | 0.729 / 0.080 |
| helpsteer2 | 1.000 / 0.000 / MAE 0.154 | 1.000 / 0.000 / MAE 0.158 |
| jailbreak_classification | 0.888 / 0.077 | 0.888 / 0.086 |
| kodiak_synth_v1 | 0.982 / 0.037 / MAE 0.084 | 0.982 / 0.033 / MAE 0.077 |
| massive | 0.917 / 0.021 | 0.910 / 0.039 |
| measuring_hate_speech | – / – / MAE 0.252 | – / – / MAE 0.257 |
| mnli | 0.880 / 0.081 | 0.860 / 0.083 |
| openbookqa | 0.803 / 0.073 | 0.752 / 0.122 |
| poem_sentiment | 0.690 / 0.069 | 0.660 / 0.080 |
| prompt_injections | 0.962 / 0.043 | 0.910 / 0.069 |
| qasper | 0.820 / 0.098 | 0.800 / 0.084 |
| scitail | 0.960 / 0.027 | 0.980 / 0.029 |
| sms_spam | 0.980 / 0.018 | 0.980 / 0.013 |
| toolace | 0.990 / 0.006 | 1.000 / 0.009 |
| ultrafeedback | 1.000 / 0.000 / MAE 0.169 | 1.000 / 0.000 / MAE 0.176 |
| winogrande | 0.809 / 0.091 | 0.809 / 0.092 |

## Systems

- **e18-xl-wording-s1**: `{"system": "e18-xl-wording-s1", "model": "runs/b-xl-s1-e18-s1/checkpoints/step_0006000.pt", "batched_ms_per_example": 22.07695977546834, "eval": "data/eval/kodiak-eval-v0.2.jsonl"}`
- **e20-xl-consistency-s1**: `{"system": "e20-xl-consistency-s1", "model": "runs/b-xl-s1-e20-s1/checkpoints/step_0006000.pt", "batched_ms_per_example": 21.11463286344332, "eval": "data/eval/kodiak-eval-v0.2.jsonl"}`
