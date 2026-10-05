"""Experiment gate (docs/GOAL.md): refuse a proposal that is missing a kill line, a one-variable change, a budget, two cited killed ideas,
or (for a full run) Shane's approval.

    uv run python scripts/gate.py docs/experiments/E16-something.md            # check the paperwork (smoke test allowed)
    uv run python scripts/gate.py docs/experiments/E16-something.md --full     # also require "Approved: Shane"
Exit code 0 = allowed; 1 = refused, with the reasons.
"""
import re
import sys
from pathlib import Path

REQUIRED = {
    "product sentence": r"\*\*Product sentence[^*]*\*\*[ \t]*(?!<)[A-Za-z].{40,}",
    "exact failure (Q1)": r"## 1\..*\n(?!<)\S.{15,}",
    "mechanism (Q2)": r"## 2\..*\n(?!<)\S.{15,}",
    "metric": r"- Metric:\s*(?!<)\S+",
    "baseline": r"- Baseline:\s*(?!<)\S+",
    "smoke kill condition": r"- Smoke test.*kill if\s*(?!<)\S+",
    "full-run keep condition": r"- Full run: keep only if\s*(?!<)\S+",
    "one-variable change": r"## Change.*\n(?!<)\S.{10,}",
    "budget": r"- Cloud: \$(?!<)\S+",
}


# From E22 on (D65): rules against "folly" experiments: a written prediction, a zero-training check, an attempt count (max 2 per
# problem), and guards taken from the noise table.
REQUIRED_D65 = {
    "prediction (rule 4)": r"- Prediction:\s*(?!<)\S.{10,}",
    "zero-training check (rule 5)": r"- Zero-training check:\s*(?!<)\S.{10,}",
    "attempt count (rule 6)": r"- Attempt:\s*[12] of 2",
    "noise-based guards (rules 1-3)": r"- Noise:.*NOISE\.md",
}


def check(path: Path, full: bool) -> list[str]:
    text = path.read_text()
    problems = [f"missing or unfilled: {name}" for name, pat in REQUIRED.items() if not re.search(pat, text)]
    m = re.match(r"E(\d+)", path.name)
    if m and int(m.group(1)) >= 22:
        problems += [f"missing or unfilled: {name}" for name, pat in REQUIRED_D65.items() if not re.search(pat, text)]
    cited = set(re.findall(r"- Not (E\d+)", text))
    log = Path("docs/EXPERIMENTS.md").read_text()
    killed = {e for e in re.findall(r"^\| (E\d+) \|.*\| (?:kill|park)", log, re.M)}
    if len(cited & killed) < 2:
        problems.append(f"must cite two killed/parked experiments from docs/EXPERIMENTS.md it is not repeating (cited: {sorted(cited) or 'none'})")
    if full and not re.search(r"^Approved: Shane", text, re.M):
        problems.append('a full run needs a line "Approved: Shane"')
    return problems


if __name__ == "__main__":
    p = Path(sys.argv[1])
    problems = check(p, "--full" in sys.argv)
    if problems:
        print(f"REFUSED {p}:\n  - " + "\n  - ".join(problems))
        sys.exit(1)
    print(f"OK {p}" + (" (full run approved)" if "--full" in sys.argv else " (smoke test allowed)"))
