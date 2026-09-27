# Cascade: large-v2-s0 first, llm-qwen3-8b when Kodiak's top probability < t

Eval v0.2, choice questions with a gold label; accuracy = top label (forced). t = 0 is Kodiak alone, t > 1 is the LLM alone.

## all (4798 questions)

| t | sent to LLM | accuracy |
|---|---|---|
| Kodiak only | 0% | 0.678 |
| 0.50 | 21% | 0.717 |
| 0.60 | 32% | 0.728 |
| 0.70 | 43% | 0.740 |
| 0.80 | 54% | 0.744 |
| 0.90 | 67% | 0.732 |
| 0.95 | 76% | 0.728 |
| LLM only | 100% | 0.709 |

## never-seen (3364 questions)

| t | sent to LLM | accuracy |
|---|---|---|
| Kodiak only | 0% | 0.601 |
| 0.50 | 27% | 0.652 |
| 0.60 | 40% | 0.670 |
| 0.70 | 52% | 0.688 |
| 0.80 | 65% | 0.697 |
| 0.90 | 79% | 0.691 |
| 0.95 | 89% | 0.689 |
| LLM only | 100% | 0.688 |

## familiar (1385 questions)

| t | sent to LLM | accuracy |
|---|---|---|
| Kodiak only | 0% | 0.856 |
| 0.50 | 8% | 0.866 |
| 0.60 | 16% | 0.859 |
| 0.70 | 23% | 0.856 |
| 0.80 | 29% | 0.850 |
| 0.90 | 40% | 0.824 |
| 0.95 | 48% | 0.813 |
| LLM only | 100% | 0.751 |

