"""Download, convert, validate, dedupe, and write the public-dataset training data.

    uv run python -m kodiak_s1.data.build                     # all sources
    uv run python -m kodiak_s1.data.build --sources mnli sms_spam --train-cap 2000

Output: data/processed/<source>/<split>.jsonl.gz, plus data/processed/manifest.json
with counts, rejects, and a sha256 per file. Held-out sources only produce `test`.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

from pydantic import ValidationError

from kodiak_s1.data.sources import SOURCES, rng_for, stable_hash
from kodiak_s1.schema import Example, render_state

DEFAULT_CAPS = {"train": 50_000, "val": 1_000, "test": 2_000}
SPLIT_ORDER = ("test", "val", "train")  # test first, so train can drop anything that leaks into it


def state_key(ex: dict) -> int:
    return stable_hash(render_state(ex["state"]).strip().casefold())


def build_source(src_id: str, out_dir: Path, caps: dict[str, int]) -> dict:
    src = SOURCES[src_id]
    t0 = time.time()
    splits = src.load()
    seen_states: dict[int, str] = {}  # state hash -> split where it first appeared
    stats: dict = {"source": src_id, "family": src.family, "license": src.license, "heldout": src.heldout, "splits": {}}
    (out_dir / src_id).mkdir(parents=True, exist_ok=True)

    for split in SPLIT_ORDER:
        if split not in splits:
            continue
        if src.heldout and split != "test":
            continue
        cap = caps[split]
        rejects: Counter = Counter()
        tags: Counter = Counter()
        seen_examples: set[int] = set()
        path = out_dir / src_id / f"{split}.jsonl.gz"
        n = rows = 0
        with gzip.open(path, "wt", encoding="utf-8") as f:
            for row in splits[split]:
                rows += 1
                if n >= cap:
                    break
                rng = rng_for(src_id, split, row.get("__key", rows))
                try:
                    exs = src.convert(row, split, rng)
                except (KeyError, TypeError, ValueError, IndexError) as e:
                    rejects[f"convert:{type(e).__name__}"] += 1
                    continue
                if not exs:
                    rejects["skipped"] += 1
                for ex in exs:
                    sk = state_key(ex)
                    first = seen_states.setdefault(sk, split)
                    if first != split:
                        rejects[f"leak:{first}"] += 1  # same state already in an earlier (eval) split
                        continue
                    ek = stable_hash(sk, json.dumps(ex["questions"], sort_keys=True))
                    if ek in seen_examples:
                        rejects["duplicate"] += 1
                        continue
                    try:
                        Example.model_validate(ex)
                    except ValidationError as e:
                        rejects[f"invalid:{e.errors()[0]['type']}"] += 1
                        continue
                    seen_examples.add(ek)
                    tags.update(ex["meta"]["tags"])
                    f.write(json.dumps(ex, ensure_ascii=False) + "\n")
                    n += 1
                    if n >= cap:
                        break
        stats["splits"][split] = {"examples": n, "rows_read": rows, "rejects": dict(rejects), "tags": dict(tags),
                                  "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        print(f"  {src_id}/{split}: {n} examples from {rows} rows; rejects={dict(rejects)}", flush=True)
    stats["seconds"] = round(time.time() - t0, 1)
    return stats


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sources", nargs="*", default=list(SOURCES))
    ap.add_argument("--out", default="data/processed")
    ap.add_argument("--train-cap", type=int, default=DEFAULT_CAPS["train"])
    ap.add_argument("--val-cap", type=int, default=DEFAULT_CAPS["val"])
    ap.add_argument("--test-cap", type=int, default=DEFAULT_CAPS["test"])
    a = ap.parse_args(argv)
    unknown = set(a.sources) - set(SOURCES)
    if unknown:
        sys.exit(f"unknown sources: {sorted(unknown)}")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    caps = {"train": a.train_cap, "val": a.val_cap, "test": a.test_cap}
    for sid in a.sources:
        print(f"[{sid}]", flush=True)
        try:
            manifest[sid] = build_source(sid, out, caps)
        except Exception as e:  # keep going; report at the end
            print(f"  FAILED: {type(e).__name__}: {e}", flush=True)
            manifest[sid] = {"source": sid, "error": f"{type(e).__name__}: {e}"}
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    failed = [k for k, v in manifest.items() if "error" in v]
    print(f"done; manifest at {manifest_path}" + (f"; FAILED: {failed}" if failed else ""))


if __name__ == "__main__":
    main()
