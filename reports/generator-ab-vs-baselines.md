# Kodiak eval report

Eval set: `data/eval/kodiak-eval-v0.1.jsonl`; examples compared: 2351; **choice questions only**


## overall

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-eq | 2584 | 0.780 | 0.772 | 0.828 | 0.040 | 0.033 | 0.304 | 0.84 | 0.94 | – | – | – | 8 |
| B-v2 | 2584 | 0.795 | 0.786 | 0.822 | 0.028 | 0.019 | 0.286 | 0.92 | 0.89 | – | – | – | 8 |
| C-v1v2 | 2584 | 0.789 | 0.787 | 0.831 | 0.028 | 0.027 | 0.288 | 0.82 | 0.94 | – | – | – | 8 |
| zs-gliclass-instruct-large | 2584 | 0.548 | 0.655 | 0.677 | 0.156 | 0.154 | 0.662 | 0.31 | 0.13 | – | – | – | 27 |
| zs-gliclass-large-v3 | 2584 | 0.533 | 0.630 | 0.695 | 0.203 | 0.139 | 0.713 | 0.34 | 0.30 | – | – | – | 26 |
| zs-nli-deberta-v3-large-28heldout | 2584 | 0.332 | 0.629 | 0.413 | 0.515 | 0.097 | 1.127 | 0.20 | 0.98 | – | – | – | 48 |
| zs-nli-deberta-v3-large | 2584 | 0.398 | 0.684 | 0.524 | 0.450 | 0.098 | 1.022 | 0.22 | 0.97 | – | – | – | 47 |
| zs-nli-modernbert-large | 2584 | 0.404 | 0.676 | 0.460 | 0.451 | 0.065 | 1.034 | 0.22 | 0.94 | – | – | – | 14 |

## eval:indomain

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-eq | 1478 | 0.814 | 0.819 | 0.902 | 0.026 | 0.021 | 0.252 | 0.83 | 0.89 | – | – | – | 8 |
| B-v2 | 1478 | 0.813 | 0.816 | 0.899 | 0.017 | 0.024 | 0.252 | 0.91 | 0.84 | – | – | – | 8 |
| C-v1v2 | 1478 | 0.821 | 0.821 | 0.892 | 0.023 | 0.025 | 0.243 | 0.85 | 0.92 | – | – | – | 7 |
| zs-gliclass-instruct-large | 1478 | 0.553 | 0.619 | 0.680 | 0.160 | 0.145 | 0.668 | 0.15 | 0.17 | – | – | – | 26 |
| zs-gliclass-large-v3 | 1478 | 0.536 | 0.591 | 0.675 | 0.176 | 0.131 | 0.689 | 0.20 | 0.40 | – | – | – | 25 |
| zs-nli-deberta-v3-large-28heldout | 1478 | 0.223 | 0.594 | 0.359 | 0.592 | 0.084 | 1.298 | 0.08 | 0.99 | – | – | – | 35 |
| zs-nli-deberta-v3-large | 1478 | 0.322 | 0.657 | 0.494 | 0.495 | 0.074 | 1.151 | 0.10 | 1.00 | – | – | – | 35 |
| zs-nli-modernbert-large | 1478 | 0.304 | 0.647 | 0.351 | 0.530 | 0.058 | 1.191 | 0.09 | 0.99 | – | – | – | 12 |

## eval:heldout

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-eq | 750 | 0.635 | 0.672 | 0.609 | 0.110 | 0.071 | 0.515 | 0.00 | – | – | – | – | 8 |
| B-v2 | 750 | 0.703 | 0.721 | 0.638 | 0.088 | 0.061 | 0.454 | 0.00 | – | – | – | – | 9 |
| C-v1v2 | 750 | 0.652 | 0.711 | 0.617 | 0.068 | 0.041 | 0.477 | 0.00 | – | – | – | – | 8 |
| zs-gliclass-instruct-large | 750 | 0.689 | 0.705 | 0.741 | 0.170 | 0.183 | 0.528 | 0.00 | – | – | – | – | 29 |
| zs-gliclass-large-v3 | 750 | 0.605 | 0.681 | 0.709 | 0.241 | 0.162 | 0.637 | 0.00 | – | – | – | – | 28 |
| zs-nli-deberta-v3-large-28heldout | 750 | 0.247 | 0.671 | 0.363 | 0.626 | 0.147 | 1.297 | 0.00 | – | – | – | – | 69 |
| zs-nli-deberta-v3-large | 750 | 0.291 | 0.712 | 0.483 | 0.566 | 0.168 | 1.209 | 0.00 | – | – | – | – | 68 |
| zs-nli-modernbert-large | 750 | 0.360 | 0.708 | 0.631 | 0.520 | 0.095 | 1.151 | 0.00 | – | – | – | – | 18 |

## eval:null_construct

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-eq | 300 | 0.950 | – | 0.070 | 0.015 | – | 0.070 | 1.00 | 0.95 | – | – | – | 8 |
| B-v2 | 300 | 0.910 | – | 0.048 | 0.037 | – | 0.070 | 1.00 | 0.91 | – | – | – | 9 |
| C-v1v2 | 300 | 0.940 | – | 0.081 | 0.014 | – | 0.075 | 1.00 | 0.94 | – | – | – | 7 |
| zs-gliclass-instruct-large | 300 | 0.113 | – | 0.004 | 0.454 | – | 1.027 | 1.00 | 0.11 | – | – | – | 24 |
| zs-gliclass-large-v3 | 300 | 0.267 | – | 0.015 | 0.442 | – | 1.105 | 1.00 | 0.27 | – | – | – | 24 |
| zs-nli-deberta-v3-large-28heldout | 300 | 0.980 | – | 0.165 | 0.048 | – | 0.028 | 1.00 | 0.98 | – | – | – | 33 |
| zs-nli-deberta-v3-large | 300 | 0.960 | – | 0.109 | 0.038 | – | 0.059 | 1.00 | 0.96 | – | – | – | 34 |
| zs-nli-modernbert-large | 300 | 0.930 | – | 0.057 | 0.042 | – | 0.094 | 1.00 | 0.93 | – | – | – | 11 |

## eval:synthetic

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-eq | 56 | 0.929 | 0.959 | 0.884 | 0.057 | 0.047 | 0.122 | 0.86 | 0.86 | – | – | – | 16 |
| B-v2 | 56 | 0.911 | 0.918 | 0.835 | 0.044 | 0.039 | 0.100 | 1.00 | 0.86 | – | – | – | 15 |
| C-v1v2 | 56 | 0.964 | 0.980 | 0.940 | 0.034 | 0.009 | 0.071 | 0.88 | 1.00 | – | – | – | 15 |
| zs-gliclass-instruct-large | 56 | 0.821 | 0.898 | 0.761 | 0.180 | 0.187 | 0.322 | 1.00 | 0.29 | – | – | – | 87 |
| zs-gliclass-large-v3 | 56 | 0.893 | 0.939 | 0.850 | 0.122 | 0.165 | 0.263 | 1.00 | 0.57 | – | – | – | 79 |
| zs-nli-deberta-v3-large-28heldout | 56 | 0.857 | 1.000 | 0.833 | 0.129 | 0.045 | 0.197 | 0.47 | 1.00 | – | – | – | 327 |
| zs-nli-deberta-v3-large | 56 | 0.821 | 1.000 | 0.792 | 0.117 | 0.037 | 0.249 | 0.41 | 1.00 | – | – | – | 322 |
| zs-nli-modernbert-large | 56 | 0.804 | 1.000 | 0.775 | 0.193 | 0.098 | 0.344 | 0.38 | 0.86 | – | – | – | 90 |

## null:gold_removed

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-eq | 150 | 0.900 | – | 0.068 | 0.034 | – | 0.138 | 1.00 | 0.90 | – | – | – | 7 |
| B-v2 | 150 | 0.827 | – | 0.045 | 0.090 | – | 0.138 | 1.00 | 0.83 | – | – | – | 8 |
| C-v1v2 | 150 | 0.880 | – | 0.078 | 0.035 | – | 0.150 | 1.00 | 0.88 | – | – | – | 7 |
| zs-gliclass-instruct-large | 150 | 0.100 | – | 0.003 | 0.327 | – | 0.839 | 1.00 | 0.10 | – | – | – | 23 |
| zs-gliclass-large-v3 | 150 | 0.533 | – | 0.027 | 0.289 | – | 0.738 | 1.00 | 0.53 | – | – | – | 24 |
| zs-nli-deberta-v3-large-28heldout | 150 | 0.960 | – | 0.163 | 0.053 | – | 0.043 | 1.00 | 0.96 | – | – | – | 47 |
| zs-nli-deberta-v3-large | 150 | 0.947 | – | 0.139 | 0.036 | – | 0.073 | 1.00 | 0.95 | – | – | – | 50 |
| zs-nli-modernbert-large | 150 | 0.860 | – | 0.054 | 0.079 | – | 0.183 | 1.00 | 0.86 | – | – | – | 13 |

## null:mismatch

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-eq | 150 | 1.000 | – | 1.000 | 0.006 | – | 0.003 | 1.00 | 1.00 | – | – | – | 10 |
| B-v2 | 150 | 0.993 | – | 0.498 | 0.002 | – | 0.003 | 1.00 | 0.99 | – | – | – | 11 |
| C-v1v2 | 150 | 1.000 | – | 1.000 | 0.005 | – | 0.001 | 1.00 | 1.00 | – | – | – | 10 |
| zs-gliclass-instruct-large | 150 | 0.127 | – | 0.075 | 0.581 | – | 1.215 | 1.00 | 0.13 | – | – | – | 25 |
| zs-gliclass-large-v3 | 150 | 0.000 | – | 0.000 | 0.595 | – | 1.473 | – | 0.00 | – | – | – | 25 |
| zs-nli-deberta-v3-large-28heldout | 150 | 1.000 | – | 1.000 | 0.059 | – | 0.013 | 1.00 | 1.00 | – | – | – | 31 |
| zs-nli-deberta-v3-large | 150 | 0.973 | – | 0.329 | 0.039 | – | 0.046 | 1.00 | 0.97 | – | – | – | 31 |
| zs-nli-modernbert-large | 150 | 1.000 | – | 1.000 | 0.030 | – | 0.005 | 1.00 | 1.00 | – | – | – | 10 |

## null:nli_neutral

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-eq | 30 | 0.867 | – | 0.310 | 0.101 | – | 0.186 | 1.00 | 0.87 | – | – | – | – |
| B-v2 | 30 | 0.767 | – | 0.289 | 0.151 | – | 0.147 | 1.00 | 0.77 | – | – | – | – |
| C-v1v2 | 30 | 0.933 | – | 0.322 | 0.085 | – | 0.093 | 1.00 | 0.93 | – | – | – | – |
| zs-gliclass-instruct-large | 30 | 0.233 | – | 0.126 | 0.597 | – | 1.081 | 1.00 | 0.23 | – | – | – | 23 |
| zs-gliclass-large-v3 | 30 | 0.000 | – | 0.000 | 0.671 | – | 1.567 | – | 0.00 | – | – | – | 23 |
| zs-nli-deberta-v3-large-28heldout | 30 | 1.000 | – | 1.000 | 0.069 | – | 0.014 | 1.00 | 1.00 | – | – | – | 30 |
| zs-nli-deberta-v3-large | 30 | 1.000 | – | 1.000 | 0.064 | – | 0.025 | 1.00 | 1.00 | – | – | – | 29 |
| zs-nli-modernbert-large | 30 | 1.000 | – | 1.000 | 0.076 | – | 0.030 | 1.00 | 1.00 | – | – | – | 9 |

## null:oos

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-eq | 22 | 0.955 | – | 0.488 | 0.084 | – | 0.091 | 1.00 | 0.95 | – | – | – | – |
| B-v2 | 22 | 0.864 | – | 0.232 | 0.100 | – | 0.126 | 1.00 | 0.86 | – | – | – | – |
| C-v1v2 | 22 | 0.909 | – | 0.317 | 0.049 | – | 0.114 | 1.00 | 0.91 | – | – | – | – |
| zs-gliclass-instruct-large | 22 | 0.227 | – | 0.026 | 0.346 | – | 0.744 | 1.00 | 0.23 | – | – | – | 25 |
| zs-gliclass-large-v3 | 22 | 0.818 | – | 0.225 | 0.106 | – | 0.188 | 1.00 | 0.82 | – | – | – | 25 |
| zs-nli-deberta-v3-large-28heldout | 22 | 0.955 | – | 0.488 | 0.041 | – | 0.023 | 1.00 | 0.95 | – | – | – | 59 |
| zs-nli-deberta-v3-large | 22 | 1.000 | – | 1.000 | 0.047 | – | 0.009 | 1.00 | 1.00 | – | – | – | 59 |
| zs-nli-modernbert-large | 22 | 0.955 | – | 0.488 | 0.041 | – | 0.028 | 1.00 | 0.95 | – | – | – | 15 |

## null:synthetic

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-eq | 7 | 0.857 | – | 0.462 | 0.091 | – | 0.136 | 1.00 | 0.86 | – | – | – | – |
| B-v2 | 7 | 0.857 | – | 0.462 | 0.070 | – | 0.070 | 1.00 | 0.86 | – | – | – | – |
| C-v1v2 | 7 | 1.000 | – | 1.000 | 0.041 | – | 0.008 | 1.00 | 1.00 | – | – | – | – |
| zs-gliclass-instruct-large | 7 | 0.286 | – | 0.089 | 0.463 | – | 0.929 | 1.00 | 0.29 | – | – | – | 187 |
| zs-gliclass-large-v3 | 7 | 0.571 | – | 0.242 | 0.322 | – | 0.622 | 1.00 | 0.57 | – | – | – | 184 |
| zs-nli-deberta-v3-large-28heldout | 7 | 1.000 | – | 1.000 | 0.056 | – | 0.007 | 1.00 | 1.00 | – | – | – | 678 |
| zs-nli-deberta-v3-large | 7 | 1.000 | – | 1.000 | 0.033 | – | 0.003 | 1.00 | 1.00 | – | – | – | 666 |
| zs-nli-modernbert-large | 7 | 0.857 | – | 0.462 | 0.103 | – | 0.195 | 1.00 | 0.86 | – | – | – | 120 |

## null:unanswerable

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-eq | 41 | 0.878 | – | 0.312 | 0.077 | – | 0.133 | 1.00 | 0.88 | – | – | – | 26 |
| B-v2 | 41 | 0.878 | – | 0.312 | 0.084 | – | 0.126 | 1.00 | 0.88 | – | – | – | 27 |
| C-v1v2 | 41 | 0.927 | – | 0.481 | 0.052 | – | 0.092 | 1.00 | 0.93 | – | – | – | 26 |
| zs-gliclass-instruct-large | 41 | 0.098 | – | 0.059 | 0.380 | – | 0.741 | 1.00 | 0.10 | – | – | – | 297 |
| zs-gliclass-large-v3 | 41 | 0.463 | – | 0.211 | 0.259 | – | 0.596 | 1.00 | 0.46 | – | – | – | 287 |
| zs-nli-deberta-v3-large-28heldout | 41 | 1.000 | – | 1.000 | 0.033 | – | 0.003 | 1.00 | 1.00 | – | – | – | 179 |
| zs-nli-deberta-v3-large | 41 | 1.000 | – | 1.000 | 0.022 | – | 0.002 | 1.00 | 1.00 | – | – | – | 176 |
| zs-nli-modernbert-large | 41 | 1.000 | – | 1.000 | 0.044 | – | 0.004 | 1.00 | 1.00 | – | – | – | 28 |

## Per source (accuracy / ECE / score MAE)

| source | A-eq | B-v2 | C-v1v2 | zs-gliclass-instruct-large | zs-gliclass-large-v3 | zs-nli-deberta-v3-large-28heldout | zs-nli-deberta-v3-large | zs-nli-modernbert-large |
|---|---|---|---|---|---|---|---|---|
| banking77 | 0.652 / 0.161 | 0.692 / 0.118 | 0.668 / 0.116 | 0.816 / 0.215 | 0.724 / 0.208 | 0.252 / 0.551 | 0.376 / 0.439 | 0.560 / 0.283 |
| bias_in_bios | 0.604 / 0.142 | 0.616 / 0.115 | 0.556 / 0.087 | 0.788 / 0.100 | 0.640 / 0.319 | 0.476 / 0.438 | 0.476 / 0.416 | 0.516 / 0.341 |
| civil_comments | 1.000 / 0.007 | 1.000 / 0.019 | 1.000 / 0.027 | 0.000 / 0.869 | 0.000 / 0.537 | 1.000 / 0.046 | 1.000 / 0.043 | 1.000 / 0.026 |
| clinc_oos | 0.968 / 0.032 | 0.930 / 0.037 | 0.955 / 0.014 | 0.567 / 0.128 | 0.732 / 0.120 | 0.707 / 0.163 | 0.764 / 0.129 | 0.796 / 0.111 |
| commonsense_qa | 0.704 / 0.090 | 0.697 / 0.065 | 0.683 / 0.079 | 0.423 / 0.166 | 0.423 / 0.369 | 0.303 / 0.600 | 0.303 / 0.624 | 0.289 / 0.625 |
| glaive_fc_v2 | 0.992 / 0.013 | 0.983 / 0.013 | 0.983 / 0.006 | 0.744 / 0.204 | 0.686 / 0.185 | 0.579 / 0.295 | 0.736 / 0.183 | 0.306 / 0.608 |
| go_emotions | 0.724 / 0.094 | 0.715 / 0.097 | 0.743 / 0.088 | 0.486 / 0.148 | 0.379 / 0.206 | 0.192 / 0.500 | 0.294 / 0.367 | 0.360 / 0.313 |
| helpsteer2 | 1.000 / 0.002 | 1.000 / 0.002 | 1.000 / 0.002 | 0.111 / 0.629 | 0.000 / 0.550 | 1.000 / 0.139 | 0.778 / 0.208 | 1.000 / 0.020 |
| jailbreak_classification | 0.648 / 0.094 | 0.800 / 0.094 | 0.732 / 0.074 | 0.464 / 0.405 | 0.452 / 0.277 | 0.012 / 0.875 | 0.020 / 0.886 | 0.004 / 0.947 |
| kodiak_synth_v1 | 0.929 / 0.057 | 0.911 / 0.044 | 0.964 / 0.034 | 0.821 / 0.180 | 0.893 / 0.122 | 0.857 / 0.129 | 0.821 / 0.117 | 0.804 / 0.193 |
| massive | 0.892 / 0.025 | 0.877 / 0.045 | 0.881 / 0.031 | 0.491 / 0.098 | 0.498 / 0.259 | 0.397 / 0.443 | 0.516 / 0.350 | 0.581 / 0.243 |
| mnli | 0.820 / 0.092 | 0.800 / 0.079 | 0.820 / 0.091 | 0.430 / 0.332 | 0.520 / 0.251 | 0.230 / 0.611 | 0.270 / 0.577 | 0.430 / 0.469 |
| openbookqa | 0.564 / 0.141 | 0.581 / 0.174 | 0.607 / 0.140 | 0.350 / 0.276 | 0.359 / 0.490 | 0.154 / 0.782 | 0.162 / 0.793 | 0.145 / 0.805 |
| prompt_injections | 0.910 / 0.054 | 0.936 / 0.064 | 0.923 / 0.070 | 0.385 / 0.463 | 0.359 / 0.238 | 0.013 / 0.928 | 0.000 / 0.958 | 0.013 / 0.943 |
| qasper | 0.710 / 0.100 | 0.700 / 0.095 | 0.760 / 0.090 | 0.380 / 0.155 | 0.500 / 0.132 | 0.430 / 0.501 | 0.430 / 0.517 | 0.440 / 0.464 |
| scitail | 0.930 / 0.047 | 0.910 / 0.046 | 0.940 / 0.021 | 0.480 / 0.329 | 0.430 / 0.264 | 0.150 / 0.669 | 0.310 / 0.509 | 0.390 / 0.441 |
| sms_spam | 0.990 / 0.008 | 0.980 / 0.014 | 0.990 / 0.019 | 0.317 / 0.565 | 0.455 / 0.410 | 0.010 / 0.971 | 0.168 / 0.764 | 0.188 / 0.786 |
| toolace | 0.981 / 0.014 | 0.990 / 0.027 | 0.971 / 0.016 | 0.771 / 0.365 | 0.743 / 0.171 | 0.400 / 0.413 | 0.581 / 0.244 | 0.171 / 0.711 |
| ultrafeedback | 1.000 / 0.002 | 1.000 / 0.001 | 1.000 / 0.001 | 0.038 / 0.496 | 0.000 / 0.606 | 1.000 / 0.144 | 0.923 / 0.152 | 1.000 / 0.038 |
| winogrande | 0.670 / 0.144 | 0.687 / 0.139 | 0.678 / 0.119 | 0.504 / 0.298 | 0.487 / 0.217 | 0.478 / 0.229 | 0.530 / 0.236 | 0.487 / 0.255 |

## Systems

- **A-eq**: `{"system": "A-eq", "model": "runs/b-small-s1-A-eq/checkpoints/step_0006000.pt", "batched_ms_per_example": 7.096891402158447, "eval": "data/eval/kodiak-eval-v0.1.jsonl"}`
- **B-v2**: `{"system": "B-v2", "model": "runs/b-small-s1-B-v2/checkpoints/step_0006000.pt", "batched_ms_per_example": 7.180290917020617, "eval": "data/eval/kodiak-eval-v0.1.jsonl"}`
- **C-v1v2**: `{"system": "C-v1v2", "model": "runs/b-small-s1-C-v1v2/checkpoints/step_0006000.pt", "batched_ms_per_example": 7.08540178771849, "eval": "data/eval/kodiak-eval-v0.1.jsonl"}`
- **zs-gliclass-instruct-large**: `{"system": "zs-gliclass-instruct-large", "model": "knowledgator/gliclass-instruct-large-v1.0", "kind": "gliclass", "eval": "data/eval/kodiak-eval-v0.1.jsonl", "types": "choice only", "abstain_rule": "abstain if best label's independent probability < 0.5", "latency": "one example (all choice questions) per batch, CUDA-synchronized"}`
- **zs-gliclass-large-v3**: `{"system": "zs-gliclass-large-v3", "model": "knowledgator/gliclass-large-v3.0", "kind": "gliclass", "eval": "data/eval/kodiak-eval-v0.1.jsonl", "types": "choice only", "abstain_rule": "abstain if best label's independent probability < 0.5", "latency": "one example (all choice questions) per batch, CUDA-synchronized"}`
- **zs-nli-deberta-v3-large-28heldout**: `{"system": "zs-nli-deberta-v3-large-28heldout", "model": "MoritzLaurer/deberta-v3-large-zeroshot-v2.0-28heldout", "kind": "nli", "eval": "data/eval/kodiak-eval-v0.1.jsonl", "types": "choice only", "abstain_rule": "abstain if best label's independent probability < 0.5", "latency": "one example (all choice questions) per batch, CUDA-synchronized"}`
- **zs-nli-deberta-v3-large**: `{"system": "zs-nli-deberta-v3-large", "model": "MoritzLaurer/deberta-v3-large-zeroshot-v2.0", "kind": "nli", "eval": "data/eval/kodiak-eval-v0.1.jsonl", "types": "choice only", "abstain_rule": "abstain if best label's independent probability < 0.5", "latency": "one example (all choice questions) per batch, CUDA-synchronized"}`
- **zs-nli-modernbert-large**: `{"system": "zs-nli-modernbert-large", "model": "MoritzLaurer/ModernBERT-large-zeroshot-v2.0", "kind": "nli", "eval": "data/eval/kodiak-eval-v0.1.jsonl", "types": "choice only", "abstain_rule": "abstain if best label's independent probability < 0.5", "latency": "one example (all choice questions) per batch, CUDA-synchronized"}`
