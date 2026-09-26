"""Mean ± spread over seeds for the generator A/B (v1 vs v2 at equal size)."""
import statistics as st

from kodiak_s1.eval.metrics import report
from kodiak_s1.eval.run import load_preds

GROUPS = {"v1 (equal size)": ["ab-A-eq", "ab-A-eq-s1", "ab-A-eq-s2"], "v2.0": ["ab-B-v2", "ab-B-v2-s1", "ab-B-v2-s2"]}
ROWS = [("eval:heldout", "accuracy", "Never-seen tasks, accuracy"), ("eval:heldout", "forced_accuracy", "Never-seen tasks, forced"),
        ("overall", "accuracy", "Overall accuracy"), ("eval:indomain", "accuracy", "Familiar tasks"), ("overall", "ece", "Calibration error (ECE)"),
        ("overall", "abstain_precision", "Abstain precision"), ("eval:null_construct", "accuracy", "Constructed unanswerables"),
        ("source:banking77", "forced_accuracy", "Banking77 (forced)"), ("source:bias_in_bios", "forced_accuracy", "Bias in Bios (forced)"),
        ("source:jailbreak_classification", "forced_accuracy", "Jailbreak (forced)")]
from pathlib import Path
res = {g: [report(load_preds(f"reports/preds/{f}.jsonl")[1]) for f in files if Path(f"reports/preds/{f}.jsonl").exists()]
       for g, files in GROUPS.items()}
print("# Generator A/B: v1 vs v2.0 at equal size (9,137 synthetic examples), 3 training seeds each\n")
print("| Measure | " + " | ".join(GROUPS) + " | Difference (v2 - v1) |\n|---|---|---|---|")
for sl, key, label in ROWS:
    cells, means = [], []
    for g in GROUPS:
        vals = [r[sl][key] for r in res[g] if sl in r and key in r[sl]]
        m, s = st.mean(vals), (st.stdev(vals) if len(vals) > 1 else 0.0)
        means.append(m)
        cells.append(f"{m:.3f} ± {s:.3f} (n={len(vals)})")
    print(f"| {label} | " + " | ".join(cells) + f" | {means[1] - means[0]:+.3f} |")
print("\n± is the standard deviation across seeds (training noise). Same data subset for every seed.")
