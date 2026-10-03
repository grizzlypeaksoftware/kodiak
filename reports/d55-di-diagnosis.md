# D56: Decision Index diagnosis: which E17 swings are real?

Fixed sample: up to 1,000 rows from each of the 12 benchmarks that moved most between XL v2 and E17 (11,979 rows, chosen by a hash of the
row id). Chance-corrected skill. Seed 1 of each comes from the full runs, rescored on the same rows; seeds 0 and 2 were run on the sample.

| Benchmark | XL v2 s1 | XL v2 s0 | XL v2 s2 | **XL v2 mean** | E17 s1 | E17 s0 | E17 s2 | **E17 mean** | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| Amazon ESCI | 0.045 | 0.080 | 0.007 | **0.044** | 0.201 | 0.189 | 0.178 | **0.189** | real gain (all 3 seeds) |
| HoVer claim verification | 0.080 | 0.066 | 0.222 | **0.123** | 0.260 | 0.196 | 0.184 | **0.213** | real gain |
| CLINC150+OOS | 0.757 | 0.869 | 0.879 | **0.835** | 0.924 | 0.910 | 0.890 | **0.908** | real gain |
| BFCL | 0.200 | 0.200 | 0.189 | **0.196** | 0.317 | 0.206 | 0.218 | **0.247** | small gain (mostly seed 1) |
| ANLI | 0.020 | 0.000 | 0.000 | **0.007** | 0.073 | 0.000 | 0.000 | **0.024** | noise |
| BANKING77 | 0.595 | 0.603 | 0.597 | **0.598** | 0.527 | 0.613 | 0.618 | **0.586** | no change (E17 s1 was low) |
| BPoMP | 0.590 | 0.282 | 0.179 | **0.350** | 0.385 | 0.385 | 0.256 | **0.342** | no change (XL v2 s1 was high) |
| FinEntity | 0.578 | 0.278 | 0.218 | **0.358** | 0.388 | 0.380 | 0.226 | **0.331** | no change (XL v2 s1 was high) |
| VAST | 0.120 | 0.007 | 0.073 | **0.067** | 0.023 | 0.072 | 0.109 | **0.068** | no change |
| Humicroedit | 0.090 | 0.090 | 0.066 | **0.082** | 0.014 | 0.114 | 0.108 | **0.079** | no change |
| When2Call MCQ | 0.169 | 0.156 | 0.051 | **0.125** | 0.085 | 0.136 | 0.080 | **0.100** | no change (within spread) |
| PhishNChips | 0.384 | 0.316 | 0.126 | **0.275** | 0.082 | 0.018 | 0.138 | **0.079** | real drop |

## PhishNChips: the same email, asked four ways (share of 1,000 emails)

| Model | verdict = phishing | minimal = phishing | click = no | is_phishing yes |
|---|---|---|---|---|
| XL v2 s1 | 32% | 31% | 9% | 8% |
| XL v2 s0 | 19% | 13% | 6% | 2% |
| XL v2 s2 | **87%** | 29% | 4% | 4% |
| E17 s1 | **96%** | 24% | 2% | 1% |
| E17 s0 | **99%** | 20% | 6% | 38% |
| E17 s2 | **91%** | 15% | 39% | 8% |

The "verdict" question (two options with long descriptions) flips to "phishing" while the other wordings of the same question say "safe".
It already happens in XL v2 seed 2, so it's a fragility of how Kodiak reads long option descriptions, which E17 makes consistent, not
something E17 created. It is the label-overlap / wording-trap family (GOAL.md open goal).

## Conclusions

1. **The Decision Index is noisy per benchmark across training seeds:** XL v2's three seeds differ by up to 0.36 (FinEntity 0.22-0.58,
   BPoMP 0.18-0.59). One run is a weak measure of a single benchmark; the published XL v2 (seed 1) was the luckiest seed on several
   classification benchmarks, which made E17 look like it regressed.
2. **Real E17 gains, all three seeds:** product relevance (ESCI) +0.15, claim verification (HoVer) +0.09, intent (CLINC) +0.07, function
   calling (BFCL) +0.05. **The regressions were noise**, except PhishNChips (-0.20), which is the option-wording fragility above.
3. **Not fixed by E17:** RAGTruth (0), API-Bank, ANLI, When2Call.
