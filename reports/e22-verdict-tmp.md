# Kodiak eval report

Eval set: `data/eval/kodiak-eval-v0.2.jsonl`; examples compared: 6102


## overall

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e22-xl-skills3-s0 | 7389 | 0.736 | 0.753 | 0.859 | 0.051 | 0.034 | 0.372 | 0.94 | 0.61 | 0.203 | 1.00 | 0.73 | 38 |
| e22-xl-skills3-s1 | 7389 | 0.721 | 0.738 | 0.849 | 0.048 | 0.028 | 0.384 | 0.96 | 0.59 | 0.206 | 1.00 | 0.71 | 38 |
| e22-xl-skills3-s2 | 7389 | 0.732 | 0.750 | 0.845 | 0.054 | 0.037 | 0.385 | 0.89 | 0.63 | 0.202 | 1.00 | 0.73 | 38 |

## eval:indomain

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e22-xl-skills3-s0 | 2578 | 0.884 | 0.887 | 0.937 | 0.026 | 0.023 | 0.174 | 0.95 | 0.78 | 0.143 | 1.00 | 0.94 | 39 |
| e22-xl-skills3-s1 | 2578 | 0.873 | 0.883 | 0.927 | 0.023 | 0.019 | 0.179 | 0.92 | 0.72 | 0.147 | 1.00 | 0.93 | 39 |
| e22-xl-skills3-s2 | 2578 | 0.879 | 0.884 | 0.921 | 0.013 | 0.013 | 0.171 | 0.91 | 0.81 | 0.145 | 1.00 | 0.92 | 39 |

## eval:heldout

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e22-xl-skills3-s0 | 4450 | 0.654 | 0.694 | 0.671 | 0.073 | 0.045 | 0.489 | 0.00 | 0.00 | 0.276 | 1.00 | 0.47 | 38 |
| e22-xl-skills3-s1 | 4450 | 0.638 | 0.675 | 0.701 | 0.074 | 0.040 | 0.503 | 0.00 | 0.00 | 0.278 | 1.00 | 0.45 | 38 |
| e22-xl-skills3-s2 | 4450 | 0.650 | 0.691 | 0.673 | 0.081 | 0.053 | 0.507 | 0.07 | 0.02 | 0.272 | 1.00 | 0.50 | 38 |

## eval:heldout_v01

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e22-xl-skills3-s0 | 1250 | 0.821 | 0.835 | 0.743 | 0.091 | 0.040 | 0.325 | 0.00 | – | 0.244 | 1.00 | 0.62 | 38 |
| e22-xl-skills3-s1 | 1250 | 0.864 | 0.869 | 0.792 | 0.074 | 0.041 | 0.274 | 0.00 | – | 0.255 | 1.00 | 0.54 | 37 |
| e22-xl-skills3-s2 | 1250 | 0.812 | 0.833 | 0.737 | 0.099 | 0.059 | 0.330 | 0.00 | – | 0.254 | 1.00 | 0.56 | 38 |

## eval:heldout_v02

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e22-xl-skills3-s0 | 3200 | 0.609 | 0.653 | 0.515 | 0.086 | 0.060 | 0.533 | 0.00 | 0.00 | 0.316 | 1.00 | 0.28 | 38 |
| e22-xl-skills3-s1 | 3200 | 0.578 | 0.619 | 0.504 | 0.090 | 0.050 | 0.565 | 0.00 | 0.00 | 0.308 | 1.00 | 0.33 | 38 |
| e22-xl-skills3-s2 | 3200 | 0.606 | 0.651 | 0.533 | 0.086 | 0.059 | 0.554 | 0.17 | 0.02 | 0.295 | 1.00 | 0.42 | 38 |

## eval:null_construct

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e22-xl-skills3-s0 | 300 | 0.923 | – | 0.053 | 0.023 | – | 0.038 | 1.00 | 0.92 | – | – | – | 36 |
| e22-xl-skills3-s1 | 300 | 0.903 | – | 0.043 | 0.033 | – | 0.039 | 1.00 | 0.90 | – | – | – | 36 |
| e22-xl-skills3-s2 | 300 | 0.940 | – | 0.065 | 0.018 | – | 0.049 | 1.00 | 0.94 | – | – | – | 36 |

## eval:synthetic

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e22-xl-skills3-s0 | 61 | 1.000 | 1.000 | 1.000 | 0.026 | 0.021 | 0.006 | 1.00 | 0.88 | 0.084 | 1.00 | 1.00 | 63 |
| e22-xl-skills3-s1 | 61 | 0.964 | 0.980 | 0.941 | 0.024 | 0.009 | 0.081 | 1.00 | 0.75 | 0.084 | 1.00 | 1.00 | 64 |
| e22-xl-skills3-s2 | 61 | 0.964 | 0.980 | 0.941 | 0.034 | 0.040 | 0.069 | 1.00 | 0.75 | 0.078 | 1.00 | 1.00 | 63 |

## null:gold_removed

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e22-xl-skills3-s0 | 150 | 0.847 | – | 0.051 | 0.056 | – | 0.077 | 1.00 | 0.85 | – | – | – | 36 |
| e22-xl-skills3-s1 | 150 | 0.807 | – | 0.041 | 0.066 | – | 0.079 | 1.00 | 0.81 | – | – | – | 36 |
| e22-xl-skills3-s2 | 150 | 0.880 | – | 0.062 | 0.039 | – | 0.098 | 1.00 | 0.88 | – | – | – | 36 |

## null:mismatch

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e22-xl-skills3-s0 | 150 | 1.000 | – | 1.000 | 0.000 | – | 0.000 | 1.00 | 1.00 | – | – | – | 36 |
| e22-xl-skills3-s1 | 150 | 1.000 | – | 1.000 | 0.001 | – | 0.000 | 1.00 | 1.00 | – | – | – | 36 |
| e22-xl-skills3-s2 | 150 | 1.000 | – | 1.000 | 0.000 | – | 0.000 | 1.00 | 1.00 | – | – | – | 36 |

## null:nli_neutral

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e22-xl-skills3-s0 | 30 | 0.767 | – | 0.289 | 0.120 | – | 0.148 | 1.00 | 0.77 | – | – | – | 38 |
| e22-xl-skills3-s1 | 30 | 0.667 | – | 0.267 | 0.171 | – | 0.196 | 1.00 | 0.67 | – | – | – | 38 |
| e22-xl-skills3-s2 | 30 | 0.800 | – | 0.296 | 0.108 | – | 0.133 | 1.00 | 0.80 | – | – | – | 38 |

## null:not_mentioned

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e22-xl-skills3-s0 | 186 | 0.000 | – | 0.000 | 0.621 | – | 1.268 | – | 0.00 | – | – | – | 56 |
| e22-xl-skills3-s1 | 186 | 0.000 | – | 0.000 | 0.682 | – | 1.470 | – | 0.00 | – | – | – | 56 |
| e22-xl-skills3-s2 | 186 | 0.016 | – | 0.011 | 0.643 | – | 1.458 | 1.00 | 0.02 | – | – | – | 55 |

## null:oos

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e22-xl-skills3-s0 | 22 | 0.909 | – | 0.317 | 0.063 | – | 0.101 | 1.00 | 0.91 | – | – | – | 39 |
| e22-xl-skills3-s1 | 22 | 0.818 | – | 0.180 | 0.054 | – | 0.033 | 1.00 | 0.82 | – | – | – | 38 |
| e22-xl-skills3-s2 | 22 | 0.864 | – | 0.232 | 0.076 | – | 0.113 | 1.00 | 0.86 | – | – | – | 38 |

## null:synthetic

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e22-xl-skills3-s0 | 8 | 1.000 | – | 1.000 | 0.016 | – | 0.002 | 1.00 | 0.88 | – | – | – | 63 |
| e22-xl-skills3-s1 | 8 | 0.857 | – | 0.462 | 0.133 | – | 0.213 | 1.00 | 0.75 | – | – | – | 64 |
| e22-xl-skills3-s2 | 8 | 0.857 | – | 0.462 | 0.128 | – | 0.191 | 1.00 | 0.75 | – | – | – | 63 |

## null:unanswerable

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e22-xl-skills3-s0 | 41 | 0.854 | – | 0.307 | 0.066 | – | 0.098 | 1.00 | 0.85 | – | – | – | 116 |
| e22-xl-skills3-s1 | 41 | 0.829 | – | 0.302 | 0.082 | – | 0.134 | 1.00 | 0.83 | – | – | – | 117 |
| e22-xl-skills3-s2 | 41 | 0.902 | – | 0.316 | 0.047 | – | 0.102 | 1.00 | 0.90 | – | – | – | 116 |

## Per source (accuracy / ECE / score MAE)

| source | e22-xl-skills3-s0 | e22-xl-skills3-s1 | e22-xl-skills3-s2 |
|---|---|---|---|
| arxiv_field | 0.682 / 0.080 | 0.645 / 0.083 | 0.675 / 0.096 |
| banking77 | 0.808 / 0.108 | 0.820 / 0.077 | 0.784 / 0.110 |
| bias_in_bios | 0.792 / 0.129 | 0.832 / 0.158 | 0.792 / 0.144 |
| casehold | 0.552 / 0.091 | 0.448 / 0.070 | 0.547 / 0.067 |
| civil_comments | 1.000 / 0.000 / MAE 0.090 | 1.000 / 0.004 / MAE 0.090 | 1.000 / 0.001 / MAE 0.088 |
| clickbait17 | – / – / MAE 0.316 | – / – / MAE 0.308 | – / – / MAE 0.295 |
| clinc_oos | 0.968 / 0.014 | 0.936 / 0.028 | 0.962 / 0.019 |
| commonsense_qa | 0.824 / 0.057 | 0.817 / 0.053 | 0.782 / 0.077 |
| contract_nli | 0.427 / 0.272 | 0.425 / 0.325 | 0.470 / 0.248 |
| ethics_commonsense | 0.552 / 0.186 | 0.510 / 0.207 | 0.542 / 0.181 |
| fin_tweets_sentiment | 0.710 / 0.173 | 0.725 / 0.139 | 0.708 / 0.165 |
| fin_tweets_topic | 0.623 / 0.083 | 0.593 / 0.088 | 0.593 / 0.094 |
| glaive_fc_v2 | 0.992 / 0.006 | 0.992 / 0.008 | 0.992 / 0.015 |
| go_emotions | 0.762 / 0.092 | 0.752 / 0.079 | 0.734 / 0.062 |
| helpsteer2 | 1.000 / 0.000 / MAE 0.145 | 1.000 / 0.000 / MAE 0.154 | 1.000 / 0.000 / MAE 0.152 |
| jailbreak_classification | 0.864 / 0.093 | 0.940 / 0.061 | 0.860 / 0.076 |
| kodiak_synth_v1 | 1.000 / 0.026 / MAE 0.084 | 0.964 / 0.024 / MAE 0.084 | 0.964 / 0.034 / MAE 0.078 |
| massive | 0.895 / 0.027 | 0.877 / 0.028 | 0.917 / 0.024 |
| measuring_hate_speech | – / – / MAE 0.244 | – / – / MAE 0.255 | – / – / MAE 0.254 |
| mnli | 0.880 / 0.086 | 0.860 / 0.101 | 0.880 / 0.068 |
| openbookqa | 0.803 / 0.125 | 0.752 / 0.071 | 0.795 / 0.078 |
| poem_sentiment | 0.718 / 0.047 | 0.698 / 0.066 | 0.708 / 0.085 |
| prompt_injections | 0.897 / 0.056 | 0.936 / 0.056 | 0.910 / 0.064 |
| qasper | 0.800 / 0.082 | 0.790 / 0.073 | 0.850 / 0.058 |
| scitail | 0.980 / 0.031 | 0.960 / 0.019 | 0.960 / 0.035 |
| sms_spam | 0.990 / 0.005 | 0.990 / 0.007 | 0.990 / 0.004 |
| toolace | 1.000 / 0.012 | 1.000 / 0.014 | 1.000 / 0.009 |
| ultrafeedback | 1.000 / 0.000 / MAE 0.166 | 1.000 / 0.000 / MAE 0.167 | 1.000 / 0.000 / MAE 0.165 |
| winogrande | 0.843 / 0.079 | 0.843 / 0.079 | 0.861 / 0.073 |

## Systems

- **e22-xl-skills3-s0**: `{"system": "e22-xl-skills3-s0", "model": "runs/b-xl-s1-e22-s0/checkpoints/step_0006000.pt", "batched_ms_per_example": 20.094114248294375, "eval": "data/eval/kodiak-eval-v0.2.jsonl"}`
- **e22-xl-skills3-s1**: `{"system": "e22-xl-skills3-s1", "model": "runs/b-xl-s1-e22-s1/checkpoints/step_0006000.pt", "batched_ms_per_example": 20.05345785824911, "eval": "data/eval/kodiak-eval-v0.2.jsonl"}`
- **e22-xl-skills3-s2**: `{"system": "e22-xl-skills3-s2", "model": "runs/b-xl-s1-e22-s2/checkpoints/step_0006000.pt", "batched_ms_per_example": 19.99257718013268, "eval": "data/eval/kodiak-eval-v0.2.jsonl"}`
