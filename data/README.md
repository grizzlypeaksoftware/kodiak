# Kodiak data

Everything here is reproducible from code. Large outputs are git-ignored; only the eval set and the license ledger are committed.

| Path | What | In git |
|---|---|---|
| [LICENSES.md](LICENSES.md) | Source and license of every dataset, plus what we excluded and why | yes |
| `processed/<source>/{train,val,test}.jsonl.gz` | Public datasets converted to the `Example` schema | no (rebuild) |
| `processed/manifest.json` | Counts, reject reasons, tags, and sha256 per shard | no (rebuild) |
| `synthetic/*.jsonl` | Teacher-generated examples, including rejected jobs, kept for auditing | no |
| `eval/kodiak-eval-v0.1.jsonl` | The frozen eval set, plus `.stats.json` | yes |
| `eval/synthetic_reviewed_v0.1.jsonl` | Human review verdicts for the synthetic eval slice (from `tools/review.html`) | yes |
| `eval/synthetic_reviewed_gen2_v0.1.jsonl` | Human review of 55 Generator v2 eval candidates (seed 7; 92.7% label precision). Contains FineWeb-Edu excerpts (ODC-By; attribution in LICENSES.md) | yes |

## Rebuild

```bash
uv sync --extra data
uv run python -m kodiak_s1.data.build                  # public datasets -> data/processed (~10 min)
uv run python -m kodiak_s1.data.evalset --synthetic data/eval/synthetic_reviewed_v0.1.jsonl   # frozen eval set
uv run python -m kodiak_s1.data.synth --n 1000 --workers 2 --out data/synthetic/synth_v1.jsonl   # needs Ollama
```

The build is deterministic. Every random choice (upstream shuffling, label subsets, question phrasing, splits for
datasets without one) is seeded from the source id and row, so rebuilding produces identical files.
Compare the `sha256` values in `manifest.json`.

## Guarantees the build enforces

- Every record validates against `kodiak_s1.schema.Example`; rejects are counted by reason in the manifest.
- **No state leaks across splits.** Test is built first; a state that already appears in test or val is dropped from train.
- Duplicates (same state + same questions) are removed.
- Held-out sources only produce `test` and are never trained on.
- Eval examples fit the v0.1 limits (state ≤ 2,048 tokens, packed request ≤ 4,096) and their states don't appear in any training shard.

## Tags

`meta.tags` lets the eval report slice results:

| Tag | Meaning |
|---|---|
| `null:nli_neutral` | A yes/no claim question where the text neither supports nor contradicts the claim |
| `null:oos` | Out-of-scope request: none of the offered intents apply (CLINC) |
| `null:unanswerable` | Annotators agreed the paper doesn't answer it (Qasper) |
| `null:mismatch` | A claim about a different text, asked about this state |
| `null:gold_removed` | The correct option was removed from the choices |
| `null:synthetic` | Teacher-written question the state can't answer |
| `multiq` | More than one question about the same state |
| `tool:call` / `tool:none` / `tool:clarify` | Tool routing: call a tool / answer directly / ask for missing details |
| `heldout` | Source never trained on |
| `eval:*` | Eval slice (`indomain`, `heldout`, `null_construct`, `synthetic`) |
