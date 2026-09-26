# Kodiak eval report

Eval set: `data/eval/kodiak-eval-v0.2.jsonl`; examples compared: 5151; **choice questions only**


## overall

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 5384 | 0.625 | 0.632 | 0.780 | 0.092 | 0.074 | 0.511 | 0.91 | 0.61 | – | – | – | 8 |
| large-v2-s0 | 5384 | 0.675 | 0.678 | 0.825 | 0.072 | 0.066 | 0.433 | 0.92 | 0.67 | – | – | – | 17 |
| zs-gliclass-instruct-large | 5384 | 0.502 | 0.573 | 0.657 | 0.192 | 0.149 | 0.732 | 0.20 | 0.09 | – | – | – | 27 |
| zs-gliclass-large-v3 | 5384 | 0.481 | 0.550 | 0.673 | 0.228 | 0.187 | 0.776 | 0.22 | 0.21 | – | – | – | 27 |
| zs-nli-deberta-v3-large-28heldout | 5384 | 0.266 | 0.587 | 0.403 | 0.550 | 0.074 | 1.216 | 0.14 | 0.97 | – | – | – | 62 |
| zs-nli-deberta-v3-large | 5384 | 0.355 | 0.590 | 0.508 | 0.463 | 0.120 | 1.078 | 0.17 | 0.98 | – | – | – | 62 |
| zs-nli-modernbert-large | 5384 | 0.385 | 0.596 | 0.454 | 0.414 | 0.094 | 1.020 | 0.18 | 0.94 | – | – | – | 17 |

## eval:indomain

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 1478 | 0.813 | 0.816 | 0.899 | 0.017 | 0.024 | 0.252 | 0.91 | 0.84 | – | – | – | 8 |
| large-v2-s0 | 1478 | 0.855 | 0.856 | 0.932 | 0.015 | 0.017 | 0.200 | 0.93 | 0.88 | – | – | – | 17 |
| zs-gliclass-instruct-large | 1478 | 0.553 | 0.619 | 0.680 | 0.160 | 0.145 | 0.668 | 0.15 | 0.17 | – | – | – | 25 |
| zs-gliclass-large-v3 | 1478 | 0.536 | 0.591 | 0.675 | 0.176 | 0.131 | 0.689 | 0.20 | 0.40 | – | – | – | 25 |
| zs-nli-deberta-v3-large-28heldout | 1478 | 0.223 | 0.594 | 0.359 | 0.592 | 0.084 | 1.298 | 0.08 | 0.99 | – | – | – | 35 |
| zs-nli-deberta-v3-large | 1478 | 0.322 | 0.657 | 0.494 | 0.495 | 0.074 | 1.151 | 0.10 | 1.00 | – | – | – | 34 |
| zs-nli-modernbert-large | 1478 | 0.304 | 0.647 | 0.351 | 0.530 | 0.058 | 1.191 | 0.09 | 0.99 | – | – | – | 12 |

## eval:heldout

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 3550 | 0.519 | 0.552 | 0.556 | 0.130 | 0.098 | 0.662 | 0.00 | 0.00 | – | – | – | 8 |
| large-v2-s0 | 3550 | 0.574 | 0.601 | 0.612 | 0.110 | 0.092 | 0.567 | 0.52 | 0.16 | – | – | – | 17 |
| zs-gliclass-instruct-large | 3550 | 0.508 | 0.550 | 0.651 | 0.208 | 0.154 | 0.741 | 0.00 | 0.00 | – | – | – | 28 |
| zs-gliclass-large-v3 | 3550 | 0.470 | 0.528 | 0.629 | 0.247 | 0.213 | 0.792 | 0.00 | 0.00 | – | – | – | 28 |
| zs-nli-deberta-v3-large-28heldout | 3550 | 0.214 | 0.579 | 0.341 | 0.596 | 0.076 | 1.299 | 0.07 | 0.94 | – | – | – | 83 |
| zs-nli-deberta-v3-large | 3550 | 0.311 | 0.556 | 0.440 | 0.497 | 0.153 | 1.147 | 0.09 | 1.00 | – | – | – | 83 |
| zs-nli-modernbert-large | 3550 | 0.365 | 0.569 | 0.560 | 0.414 | 0.118 | 1.037 | 0.10 | 0.94 | – | – | – | 22 |

## eval:heldout_v01

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 750 | 0.703 | 0.721 | 0.638 | 0.088 | 0.061 | 0.454 | 0.00 | – | – | – | – | 7 |
| large-v2-s0 | 750 | 0.713 | 0.725 | 0.674 | 0.138 | 0.099 | 0.454 | 0.00 | – | – | – | – | 16 |
| zs-gliclass-instruct-large | 750 | 0.689 | 0.705 | 0.741 | 0.170 | 0.183 | 0.528 | 0.00 | – | – | – | – | 28 |
| zs-gliclass-large-v3 | 750 | 0.605 | 0.681 | 0.709 | 0.241 | 0.162 | 0.637 | 0.00 | – | – | – | – | 27 |
| zs-nli-deberta-v3-large-28heldout | 750 | 0.247 | 0.671 | 0.363 | 0.626 | 0.147 | 1.297 | 0.00 | – | – | – | – | 69 |
| zs-nli-deberta-v3-large | 750 | 0.291 | 0.712 | 0.483 | 0.566 | 0.168 | 1.209 | 0.00 | – | – | – | – | 70 |
| zs-nli-modernbert-large | 750 | 0.360 | 0.708 | 0.631 | 0.520 | 0.095 | 1.151 | 0.00 | – | – | – | – | 18 |

## eval:heldout_v02

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 2800 | 0.469 | 0.503 | 0.383 | 0.177 | 0.143 | 0.718 | 0.00 | 0.00 | – | – | – | 8 |
| large-v2-s0 | 2800 | 0.537 | 0.565 | 0.468 | 0.112 | 0.097 | 0.598 | 0.78 | 0.16 | – | – | – | 18 |
| zs-gliclass-instruct-large | 2800 | 0.459 | 0.505 | 0.438 | 0.223 | 0.154 | 0.798 | 0.00 | 0.00 | – | – | – | 30 |
| zs-gliclass-large-v3 | 2800 | 0.434 | 0.484 | 0.442 | 0.266 | 0.236 | 0.834 | 0.00 | 0.00 | – | – | – | 29 |
| zs-nli-deberta-v3-large-28heldout | 2800 | 0.205 | 0.552 | 0.276 | 0.591 | 0.060 | 1.299 | 0.08 | 0.94 | – | – | – | 95 |
| zs-nli-deberta-v3-large | 2800 | 0.316 | 0.511 | 0.326 | 0.476 | 0.159 | 1.130 | 0.11 | 1.00 | – | – | – | 95 |
| zs-nli-modernbert-large | 2800 | 0.367 | 0.529 | 0.382 | 0.382 | 0.128 | 1.007 | 0.12 | 0.94 | – | – | – | 24 |

## eval:null_construct

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 300 | 0.910 | – | 0.048 | 0.037 | – | 0.070 | 1.00 | 0.91 | – | – | – | 7 |
| large-v2-s0 | 300 | 0.923 | – | 0.048 | 0.026 | – | 0.051 | 1.00 | 0.92 | – | – | – | 15 |
| zs-gliclass-instruct-large | 300 | 0.113 | – | 0.004 | 0.454 | – | 1.027 | 1.00 | 0.11 | – | – | – | 23 |
| zs-gliclass-large-v3 | 300 | 0.267 | – | 0.015 | 0.442 | – | 1.105 | 1.00 | 0.27 | – | – | – | 23 |
| zs-nli-deberta-v3-large-28heldout | 300 | 0.980 | – | 0.165 | 0.048 | – | 0.028 | 1.00 | 0.98 | – | – | – | 33 |
| zs-nli-deberta-v3-large | 300 | 0.960 | – | 0.109 | 0.038 | – | 0.059 | 1.00 | 0.96 | – | – | – | 33 |
| zs-nli-modernbert-large | 300 | 0.930 | – | 0.057 | 0.042 | – | 0.094 | 1.00 | 0.93 | – | – | – | 11 |

## eval:synthetic

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 56 | 0.911 | 0.918 | 0.835 | 0.044 | 0.039 | 0.100 | 1.00 | 0.86 | – | – | – | 14 |
| large-v2-s0 | 56 | 0.964 | 0.959 | 0.923 | 0.019 | 0.035 | 0.055 | 1.00 | 1.00 | – | – | – | 28 |
| zs-gliclass-instruct-large | 56 | 0.821 | 0.898 | 0.761 | 0.180 | 0.187 | 0.322 | 1.00 | 0.29 | – | – | – | 81 |
| zs-gliclass-large-v3 | 56 | 0.893 | 0.939 | 0.850 | 0.122 | 0.165 | 0.263 | 1.00 | 0.57 | – | – | – | 76 |
| zs-nli-deberta-v3-large-28heldout | 56 | 0.857 | 1.000 | 0.833 | 0.129 | 0.045 | 0.197 | 0.47 | 1.00 | – | – | – | 323 |
| zs-nli-deberta-v3-large | 56 | 0.821 | 1.000 | 0.792 | 0.117 | 0.037 | 0.249 | 0.41 | 1.00 | – | – | – | 331 |
| zs-nli-modernbert-large | 56 | 0.804 | 1.000 | 0.775 | 0.193 | 0.098 | 0.344 | 0.38 | 0.86 | – | – | – | 89 |

## null:gold_removed

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 150 | 0.827 | – | 0.045 | 0.090 | – | 0.138 | 1.00 | 0.83 | – | – | – | – |
| large-v2-s0 | 150 | 0.847 | – | 0.046 | 0.062 | – | 0.101 | 1.00 | 0.85 | – | – | – | – |
| zs-gliclass-instruct-large | 150 | 0.100 | – | 0.003 | 0.327 | – | 0.839 | 1.00 | 0.10 | – | – | – | 23 |
| zs-gliclass-large-v3 | 150 | 0.533 | – | 0.027 | 0.289 | – | 0.738 | 1.00 | 0.53 | – | – | – | 23 |
| zs-nli-deberta-v3-large-28heldout | 150 | 0.960 | – | 0.163 | 0.053 | – | 0.043 | 1.00 | 0.96 | – | – | – | 48 |
| zs-nli-deberta-v3-large | 150 | 0.947 | – | 0.139 | 0.036 | – | 0.073 | 1.00 | 0.95 | – | – | – | 48 |
| zs-nli-modernbert-large | 150 | 0.860 | – | 0.054 | 0.079 | – | 0.183 | 1.00 | 0.86 | – | – | – | 13 |

## null:mismatch

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 150 | 0.993 | – | 0.498 | 0.002 | – | 0.003 | 1.00 | 0.99 | – | – | – | 7 |
| large-v2-s0 | 150 | 1.000 | – | 1.000 | 0.001 | – | 0.000 | 1.00 | 1.00 | – | – | – | 15 |
| zs-gliclass-instruct-large | 150 | 0.127 | – | 0.075 | 0.581 | – | 1.215 | 1.00 | 0.13 | – | – | – | 24 |
| zs-gliclass-large-v3 | 150 | 0.000 | – | 0.000 | 0.595 | – | 1.473 | – | 0.00 | – | – | – | 23 |
| zs-nli-deberta-v3-large-28heldout | 150 | 1.000 | – | 1.000 | 0.059 | – | 0.013 | 1.00 | 1.00 | – | – | – | 29 |
| zs-nli-deberta-v3-large | 150 | 0.973 | – | 0.329 | 0.039 | – | 0.046 | 1.00 | 0.97 | – | – | – | 30 |
| zs-nli-modernbert-large | 150 | 1.000 | – | 1.000 | 0.030 | – | 0.005 | 1.00 | 1.00 | – | – | – | 10 |

## null:nli_neutral

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 30 | 0.767 | – | 0.289 | 0.151 | – | 0.147 | 1.00 | 0.77 | – | – | – | – |
| large-v2-s0 | 30 | 0.867 | – | 0.310 | 0.087 | – | 0.117 | 1.00 | 0.87 | – | – | – | – |
| zs-gliclass-instruct-large | 30 | 0.233 | – | 0.126 | 0.597 | – | 1.081 | 1.00 | 0.23 | – | – | – | 23 |
| zs-gliclass-large-v3 | 30 | 0.000 | – | 0.000 | 0.671 | – | 1.567 | – | 0.00 | – | – | – | 25 |
| zs-nli-deberta-v3-large-28heldout | 30 | 1.000 | – | 1.000 | 0.069 | – | 0.014 | 1.00 | 1.00 | – | – | – | 31 |
| zs-nli-deberta-v3-large | 30 | 1.000 | – | 1.000 | 0.064 | – | 0.025 | 1.00 | 1.00 | – | – | – | 30 |
| zs-nli-modernbert-large | 30 | 1.000 | – | 1.000 | 0.076 | – | 0.030 | 1.00 | 1.00 | – | – | – | 9 |

## null:not_mentioned

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 186 | 0.000 | – | 0.000 | 0.715 | – | 1.605 | – | 0.00 | – | – | – | 12 |
| large-v2-s0 | 186 | 0.156 | – | 0.090 | 0.437 | – | 0.895 | 1.00 | 0.16 | – | – | – | 27 |
| zs-gliclass-instruct-large | 186 | 0.000 | – | 0.000 | 0.828 | – | 1.639 | – | 0.00 | – | – | – | 59 |
| zs-gliclass-large-v3 | 186 | 0.000 | – | 0.000 | 0.654 | – | 1.485 | – | 0.00 | – | – | – | 59 |
| zs-nli-deberta-v3-large-28heldout | 186 | 0.941 | – | 0.323 | 0.160 | – | 0.111 | 1.00 | 0.94 | – | – | – | 126 |
| zs-nli-deberta-v3-large | 186 | 1.000 | – | 1.000 | 0.065 | – | 0.013 | 1.00 | 1.00 | – | – | – | 127 |
| zs-nli-modernbert-large | 186 | 0.941 | – | 0.323 | 0.036 | – | 0.080 | 1.00 | 0.94 | – | – | – | 25 |

## null:oos

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 22 | 0.864 | – | 0.232 | 0.100 | – | 0.126 | 1.00 | 0.86 | – | – | – | – |
| large-v2-s0 | 22 | 0.909 | – | 0.317 | 0.057 | – | 0.103 | 1.00 | 0.91 | – | – | – | – |
| zs-gliclass-instruct-large | 22 | 0.227 | – | 0.026 | 0.346 | – | 0.744 | 1.00 | 0.23 | – | – | – | 25 |
| zs-gliclass-large-v3 | 22 | 0.818 | – | 0.225 | 0.106 | – | 0.188 | 1.00 | 0.82 | – | – | – | 25 |
| zs-nli-deberta-v3-large-28heldout | 22 | 0.955 | – | 0.488 | 0.041 | – | 0.023 | 1.00 | 0.95 | – | – | – | 59 |
| zs-nli-deberta-v3-large | 22 | 1.000 | – | 1.000 | 0.047 | – | 0.009 | 1.00 | 1.00 | – | – | – | 58 |
| zs-nli-modernbert-large | 22 | 0.955 | – | 0.488 | 0.041 | – | 0.028 | 1.00 | 0.95 | – | – | – | 14 |

## null:synthetic

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 7 | 0.857 | – | 0.462 | 0.070 | – | 0.070 | 1.00 | 0.86 | – | – | – | 14 |
| large-v2-s0 | 7 | 1.000 | – | 1.000 | 0.009 | – | 0.000 | 1.00 | 1.00 | – | – | – | 28 |
| zs-gliclass-instruct-large | 7 | 0.286 | – | 0.089 | 0.463 | – | 0.929 | 1.00 | 0.29 | – | – | – | 179 |
| zs-gliclass-large-v3 | 7 | 0.571 | – | 0.242 | 0.322 | – | 0.622 | 1.00 | 0.57 | – | – | – | 181 |
| zs-nli-deberta-v3-large-28heldout | 7 | 1.000 | – | 1.000 | 0.056 | – | 0.007 | 1.00 | 1.00 | – | – | – | 672 |
| zs-nli-deberta-v3-large | 7 | 1.000 | – | 1.000 | 0.033 | – | 0.003 | 1.00 | 1.00 | – | – | – | 670 |
| zs-nli-modernbert-large | 7 | 0.857 | – | 0.462 | 0.103 | – | 0.195 | 1.00 | 0.86 | – | – | – | 120 |

## null:unanswerable

| system | n | acc | forced acc | macro-F1 | ECE | forced ECE | Brier | abst-P | abst-R | score MAE | score given | 90%-int cov | p50 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ab-B-v2 | 41 | 0.878 | – | 0.312 | 0.084 | – | 0.126 | 1.00 | 0.88 | – | – | – | 30 |
| large-v2-s0 | 41 | 0.878 | – | 0.312 | 0.061 | – | 0.106 | 1.00 | 0.88 | – | – | – | 57 |
| zs-gliclass-instruct-large | 41 | 0.098 | – | 0.059 | 0.380 | – | 0.741 | 1.00 | 0.10 | – | – | – | 283 |
| zs-gliclass-large-v3 | 41 | 0.463 | – | 0.211 | 0.259 | – | 0.596 | 1.00 | 0.46 | – | – | – | 282 |
| zs-nli-deberta-v3-large-28heldout | 41 | 1.000 | – | 1.000 | 0.033 | – | 0.003 | 1.00 | 1.00 | – | – | – | 178 |
| zs-nli-deberta-v3-large | 41 | 1.000 | – | 1.000 | 0.022 | – | 0.002 | 1.00 | 1.00 | – | – | – | 179 |
| zs-nli-modernbert-large | 41 | 1.000 | – | 1.000 | 0.044 | – | 0.004 | 1.00 | 1.00 | – | – | – | 28 |

## Per source (accuracy / ECE / score MAE)

| source | ab-B-v2 | large-v2-s0 | zs-gliclass-instruct-large | zs-gliclass-large-v3 | zs-nli-deberta-v3-large-28heldout | zs-nli-deberta-v3-large | zs-nli-modernbert-large |
|---|---|---|---|---|---|---|---|
| arxiv_field | 0.448 / 0.100 | 0.568 / 0.073 | 0.512 / 0.058 | 0.530 / 0.238 | 0.370 / 0.339 | 0.445 / 0.225 | 0.525 / 0.178 |
| banking77 | 0.692 / 0.118 | 0.764 / 0.126 | 0.816 / 0.215 | 0.724 / 0.208 | 0.252 / 0.551 | 0.376 / 0.439 | 0.560 / 0.283 |
| bias_in_bios | 0.616 / 0.115 | 0.764 / 0.120 | 0.788 / 0.100 | 0.640 / 0.319 | 0.476 / 0.438 | 0.476 / 0.416 | 0.516 / 0.341 |
| casehold | 0.453 / 0.135 | 0.450 / 0.121 | 0.328 / 0.169 | 0.360 / 0.233 | 0.080 / 0.740 | 0.043 / 0.834 | 0.113 / 0.699 |
| civil_comments | 1.000 / 0.019 | 1.000 / 0.002 | 0.000 / 0.869 | 0.000 / 0.537 | 1.000 / 0.046 | 1.000 / 0.043 | 1.000 / 0.026 |
| clinc_oos | 0.930 / 0.037 | 0.955 / 0.021 | 0.567 / 0.128 | 0.732 / 0.120 | 0.707 / 0.163 | 0.764 / 0.129 | 0.796 / 0.111 |
| commonsense_qa | 0.697 / 0.065 | 0.782 / 0.076 | 0.423 / 0.166 | 0.423 / 0.369 | 0.303 / 0.600 | 0.303 / 0.624 | 0.289 / 0.625 |
| contract_nli | 0.440 / 0.324 | 0.510 / 0.189 | 0.100 / 0.724 | 0.130 / 0.496 | 0.532 / 0.240 | 0.487 / 0.415 | 0.535 / 0.342 |
| ethics_commonsense | 0.542 / 0.249 | 0.507 / 0.289 | 0.455 / 0.487 | 0.463 / 0.368 | 0.025 / 0.841 | 0.018 / 0.897 | 0.030 / 0.853 |
| fin_tweets_sentiment | 0.705 / 0.140 | 0.760 / 0.086 | 0.797 / 0.063 | 0.802 / 0.087 | 0.068 / 0.822 | 0.757 / 0.103 | 0.780 / 0.059 |
| fin_tweets_topic | 0.438 / 0.064 | 0.562 / 0.080 | 0.425 / 0.195 | 0.450 / 0.238 | 0.328 / 0.313 | 0.338 / 0.187 | 0.365 / 0.229 |
| glaive_fc_v2 | 0.983 / 0.013 | 1.000 / 0.020 | 0.744 / 0.204 | 0.686 / 0.185 | 0.579 / 0.295 | 0.736 / 0.183 | 0.306 / 0.608 |
| go_emotions | 0.715 / 0.097 | 0.748 / 0.089 | 0.486 / 0.148 | 0.379 / 0.206 | 0.192 / 0.500 | 0.294 / 0.367 | 0.360 / 0.313 |
| helpsteer2 | 1.000 / 0.002 | 1.000 / 0.000 | 0.111 / 0.629 | 0.000 / 0.550 | 1.000 / 0.139 | 0.778 / 0.208 | 1.000 / 0.020 |
| jailbreak_classification | 0.800 / 0.094 | 0.612 / 0.259 | 0.464 / 0.405 | 0.452 / 0.277 | 0.012 / 0.875 | 0.020 / 0.886 | 0.004 / 0.947 |
| kodiak_synth_v1 | 0.911 / 0.044 | 0.964 / 0.019 | 0.821 / 0.180 | 0.893 / 0.122 | 0.857 / 0.129 | 0.821 / 0.117 | 0.804 / 0.193 |
| massive | 0.877 / 0.045 | 0.892 / 0.024 | 0.491 / 0.098 | 0.498 / 0.259 | 0.397 / 0.443 | 0.516 / 0.350 | 0.581 / 0.243 |
| mnli | 0.800 / 0.079 | 0.830 / 0.057 | 0.430 / 0.332 | 0.520 / 0.251 | 0.230 / 0.611 | 0.270 / 0.577 | 0.430 / 0.469 |
| openbookqa | 0.581 / 0.174 | 0.598 / 0.177 | 0.350 / 0.276 | 0.359 / 0.490 | 0.154 / 0.782 | 0.162 / 0.793 | 0.145 / 0.805 |
| poem_sentiment | 0.260 / 0.316 | 0.400 / 0.164 | 0.598 / 0.131 | 0.302 / 0.406 | 0.033 / 0.858 | 0.128 / 0.709 | 0.220 / 0.438 |
| prompt_injections | 0.936 / 0.064 | 0.923 / 0.059 | 0.385 / 0.463 | 0.359 / 0.238 | 0.013 / 0.928 | 0.000 / 0.958 | 0.013 / 0.943 |
| qasper | 0.700 / 0.095 | 0.830 / 0.111 | 0.380 / 0.155 | 0.500 / 0.132 | 0.430 / 0.501 | 0.430 / 0.517 | 0.440 / 0.464 |
| scitail | 0.910 / 0.046 | 0.960 / 0.024 | 0.480 / 0.329 | 0.430 / 0.264 | 0.150 / 0.669 | 0.310 / 0.509 | 0.390 / 0.441 |
| sms_spam | 0.980 / 0.014 | 0.990 / 0.020 | 0.317 / 0.565 | 0.455 / 0.410 | 0.010 / 0.971 | 0.168 / 0.764 | 0.188 / 0.786 |
| toolace | 0.990 / 0.027 | 1.000 / 0.020 | 0.771 / 0.365 | 0.743 / 0.171 | 0.400 / 0.413 | 0.581 / 0.244 | 0.171 / 0.711 |
| ultrafeedback | 1.000 / 0.001 | 1.000 / 0.001 | 0.038 / 0.496 | 0.000 / 0.606 | 1.000 / 0.144 | 0.923 / 0.152 | 1.000 / 0.038 |
| winogrande | 0.687 / 0.139 | 0.800 / 0.076 | 0.504 / 0.298 | 0.487 / 0.217 | 0.478 / 0.229 | 0.530 / 0.236 | 0.487 / 0.255 |

## Systems

- **ab-B-v2**: `{"system": "ab-B-v2", "model": "runs/b-small-s1-B-v2/checkpoints/step_0006000.pt", "batched_ms_per_example": 6.996118311407927, "eval": "data/eval/kodiak-eval-v0.2.jsonl"}`
- **large-v2-s0**: `{"system": "large-v2-s0", "model": "runs/b-base-s1-v2-s0/checkpoints/step_0006000.pt", "batched_ms_per_example": 11.71031278402092, "eval": "data/eval/kodiak-eval-v0.2.jsonl"}`
- **zs-gliclass-instruct-large**: `{"system": "zs-gliclass-instruct-large", "model": "knowledgator/gliclass-instruct-large-v1.0", "kind": "gliclass", "eval": "data/eval/kodiak-eval-v0.2.jsonl", "types": "choice only", "abstain_rule": "abstain if best label's independent probability < 0.5", "latency": "one example (all choice questions) per batch, CUDA-synchronized"}`
- **zs-gliclass-large-v3**: `{"system": "zs-gliclass-large-v3", "model": "knowledgator/gliclass-large-v3.0", "kind": "gliclass", "eval": "data/eval/kodiak-eval-v0.2.jsonl", "types": "choice only", "abstain_rule": "abstain if best label's independent probability < 0.5", "latency": "one example (all choice questions) per batch, CUDA-synchronized"}`
- **zs-nli-deberta-v3-large-28heldout**: `{"system": "zs-nli-deberta-v3-large-28heldout", "model": "MoritzLaurer/deberta-v3-large-zeroshot-v2.0-28heldout", "kind": "nli", "eval": "data/eval/kodiak-eval-v0.2.jsonl", "types": "choice only", "abstain_rule": "abstain if best label's independent probability < 0.5", "latency": "one example (all choice questions) per batch, CUDA-synchronized"}`
- **zs-nli-deberta-v3-large**: `{"system": "zs-nli-deberta-v3-large", "model": "MoritzLaurer/deberta-v3-large-zeroshot-v2.0", "kind": "nli", "eval": "data/eval/kodiak-eval-v0.2.jsonl", "types": "choice only", "abstain_rule": "abstain if best label's independent probability < 0.5", "latency": "one example (all choice questions) per batch, CUDA-synchronized"}`
- **zs-nli-modernbert-large**: `{"system": "zs-nli-modernbert-large", "model": "MoritzLaurer/ModernBERT-large-zeroshot-v2.0", "kind": "nli", "eval": "data/eval/kodiak-eval-v0.2.jsonl", "types": "choice only", "abstain_rule": "abstain if best label's independent probability < 0.5", "latency": "one example (all choice questions) per batch, CUDA-synchronized"}`
