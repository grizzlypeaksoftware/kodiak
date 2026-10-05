# Kodiak eval report

Eval set: `data/eval/kodiak-eval-v0.2.jsonl`; examples compared: 6102


## overall

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 7389 | 0.723 | 0.741 | 0.853 | 0.060 | 0.038 | 0.390 | 0.87 | 0.63 | 0.203 | 1.00 | 0.75 | 40 |

## eval:indomain

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 2578 | 0.877 | 0.879 | 0.928 | 0.017 | 0.017 | 0.172 | 0.91 | 0.83 | 0.148 | 1.00 | 0.94 | 40 |

## eval:heldout

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 4450 | 0.635 | 0.680 | 0.671 | 0.094 | 0.052 | 0.516 | 0.00 | 0.00 | 0.271 | 1.00 | 0.51 | 39 |

## eval:heldout_v01

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 1250 | 0.821 | 0.845 | 0.735 | 0.050 | 0.048 | 0.298 | 0.00 | – | 0.252 | 1.00 | 0.54 | 39 |

## eval:heldout_v02

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 3200 | 0.585 | 0.633 | 0.529 | 0.120 | 0.078 | 0.575 | 0.00 | 0.00 | 0.295 | 1.00 | 0.47 | 40 |

## eval:null_construct

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 300 | 0.957 | – | 0.081 | 0.025 | – | 0.041 | 1.00 | 0.96 | – | – | – | 37 |

## eval:synthetic

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 61 | 0.982 | 1.000 | 0.979 | 0.037 | 0.019 | 0.050 | 1.00 | 0.75 | 0.084 | 1.00 | 1.00 | 71 |

## null:gold_removed

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 150 | 0.913 | – | 0.080 | 0.052 | – | 0.082 | 1.00 | 0.91 | – | – | – | 35 |

## null:mismatch

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 150 | 1.000 | – | 1.000 | 0.002 | – | 0.000 | 1.00 | 1.00 | – | – | – | 38 |

## null:nli_neutral

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 30 | 0.833 | – | 0.303 | 0.118 | – | 0.183 | 1.00 | 0.83 | – | – | – | 42 |

## null:not_mentioned

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 186 | 0.000 | – | 0.000 | 0.689 | – | 1.517 | – | 0.00 | – | – | – | 57 |

## null:oos

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 22 | 0.909 | – | 0.317 | 0.041 | – | 0.096 | 1.00 | 0.91 | – | – | – | 38 |

## null:synthetic

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 8 | 0.857 | – | 0.462 | 0.139 | – | 0.272 | 1.00 | 0.75 | – | – | – | 71 |

## null:unanswerable

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e18-xl-wording-s1 | 41 | 0.902 | – | 0.316 | 0.047 | – | 0.093 | 1.00 | 0.90 | – | – | – | 129 |

## Per source (accuracy / ECE / score MAE)

| source | e18-xl-wording-s1 |
|---|---|
| arxiv_field | 0.665 / 0.071 |
| banking77 | 0.784 / 0.077 |
| bias_in_bios | 0.792 / 0.089 |
| casehold | 0.445 / 0.108 |
| civil_comments | 1.000 / 0.002 / MAE 0.090 |
| clickbait17 | – / – / MAE 0.295 |
| clinc_oos | 0.975 / 0.008 |
| commonsense_qa | 0.824 / 0.042 |
| contract_nli | 0.463 / 0.301 |
| ethics_commonsense | 0.520 / 0.230 |
| fin_tweets_sentiment | 0.715 / 0.151 |
| fin_tweets_topic | 0.595 / 0.111 |
| glaive_fc_v2 | 0.992 / 0.017 |
| go_emotions | 0.734 / 0.072 |
| helpsteer2 | 1.000 / 0.000 / MAE 0.154 |
| jailbreak_classification | 0.888 / 0.077 |
| kodiak_synth_v1 | 0.982 / 0.037 / MAE 0.084 |
| massive | 0.917 / 0.021 |
| measuring_hate_speech | – / – / MAE 0.252 |
| mnli | 0.880 / 0.081 |
| openbookqa | 0.803 / 0.073 |
| poem_sentiment | 0.690 / 0.069 |
| prompt_injections | 0.962 / 0.043 |
| qasper | 0.820 / 0.098 |
| scitail | 0.960 / 0.027 |
| sms_spam | 0.980 / 0.018 |
| toolace | 0.990 / 0.006 |
| ultrafeedback | 1.000 / 0.000 / MAE 0.169 |
| winogrande | 0.809 / 0.091 |

## Systems

- **e18-xl-wording-s1**: `{"system": "e18-xl-wording-s1", "model": "runs/b-xl-s1-e18-s1/checkpoints/step_0006000.pt", "batched_ms_per_example": 22.07695977546834, "eval": "data/eval/kodiak-eval-v0.2.jsonl"}`
