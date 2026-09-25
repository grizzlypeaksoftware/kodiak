# Runbook: operating Kodiak on the DGX Spark

Practical steps for building data, running the teacher, and training on one NVIDIA DGX Spark
(GB10, aarch64, 121 GiB unified memory). Commands run from the repo root.

## 1. Environment

```bash
uv sync --extra data --extra train     # Python 3.12 venv; PyTorch CUDA 13 aarch64 wheels from download.pytorch.org
uv run pytest                          # ~40 tests, a few seconds
KODIAK_SLOW=1 uv run pytest -k modernbert   # parity vs Hugging Face ModernBERT (downloads ~600 MB)
```

No NGC container is needed; it's the fallback if the pip wheels ever break (Docker reaches the GPU via CDI:
`docker run --device nvidia.com/gpu=all ...`).

## 2. Memory and heat: the two rules

**Unified memory.** CPU, GPU, desktop, and Ollama all share one pool. If it runs out, the system swaps and slows to a crawl
instead of failing cleanly. So:
- Don't train while Ollama models are loaded. Pause the teacher first (§4), then `ollama stop <model>`.
- The trainer caps itself with `--mem-fraction` (default 0.6).
- Check with `free -h` and `ollama ps`.

**Heat.** Sustained load runs the GPU at 65–80 °C, which is normal. The trainer pauses above `--max-temp-c` (85) and resumes
at `--resume-temp-c` (75), logging `thermal_pause` / `thermal_resume` events. Quick check:
`nvidia-smi --query-gpu=temperature.gpu,power.draw --format=csv`.

## 3. Data

```bash
uv run python -m kodiak_s1.data.build          # public datasets -> data/processed/ (~10 min, deterministic)
uv run python -m kodiak_s1.data.evalset --synthetic data/eval/synthetic_reviewed_v0.1.jsonl   # frozen eval set
```

Details and guarantees: [data/README.md](../data/README.md). Licenses: [data/LICENSES.md](../data/LICENSES.md).

## 4. The teacher (synthetic data via Ollama)

**Ollama settings** live in systemd drop-ins under `/etc/systemd/system/ollama.service.d/`. Kodiak added `parallel.conf`:

```ini
[Service]
Environment="OLLAMA_NUM_PARALLEL=4"
```

After editing a drop-in: `sudo systemctl daemon-reload && sudo systemctl restart ollama`.
To undo: `sudo rm /etc/systemd/system/ollama.service.d/parallel.conf`, then restart Ollama.

**Bulk generation** (MoE writer + dense verifier, detached so it survives the terminal closing):

```bash
nohup setsid uv run python -m kodiak_s1.data.synth --n 12500 --start 1000 --seed 1 --workers 4 \
  --model qwen3.6:35b-a3b --verifier qwen3.8:27b \
  --out data/synthetic/synth_v1.jsonl >> data/synthetic/synth_v1.log 2>&1 < /dev/null &
```

- **Progress:** `tail -f data/synthetic/synth_v1.log` (a line every 10 jobs, with jobs/hour).
- **Pause:** `pkill -f "m kodiak_s1[.]data[.]synth"`. Run it on its own; see the gotcha in §7.
- **Resume:** rerun the exact same command. Finished jobs are skipped; interrupted ones rerun.
- **Seeds:** seed 1 = training data, seed 2 = eval candidates, seed 3 = benchmarks, seed 4 = cloud-teacher pilot, seed 5 = cloud training run. Never train on seed 2.

**Cloud teacher (DigitalOcean serverless inference).** Prefix a model with `do:` to route it to
`inference.do-ai.run` (OpenAI-compatible); everything else goes to local Ollama. The key is read only from
`$DO_INFERENCE_KEY` (a *model access key*: INFERENCE → Manage → Model Access Keys; the secret is shown once).
Use only permissively licensed open-weight models for training data (see DECISIONS.md D20).

```bash
uv run python -m kodiak_s1.data.synth --n 50 --seed 4 --workers 4 \
  --model do:openai-gpt-oss-120b --verifier qwen3.8:27b --out data/synthetic/pilot_do.jsonl
```

Token usage per job (`gen_tokens`, `gen_prompt_tokens`, `verify_tokens`, ...) is recorded for cost tracking.
HTTP errors (including 401/402) mark the job `retry`, so rerunning the command resumes cleanly.

**Human review** of synthetic eval candidates: open `tools/review.html` in a browser, load the candidates JSONL,
mark each question (`a` OK / `x` wrong), export, and save as `data/eval/synthetic_reviewed_*.jsonl`.

**Generator v2** (`src/kodiak_s1/data/gen2/`, design in `docs/GENERATOR_V2.md`): spec-driven, ~45% grounded in real
FineWeb-Edu passages, writer `do:openai-gpt-oss-120b` + blind checker `do:deepseek-3.2` (the defaults). Load the key first:
`eval "$(grep -E '^\s*export DO_INFERENCE_KEY=' ~/.bashrc | tail -1)" && export DO_INFERENCE_KEY` (never echo it).

```bash
uv run python -m kodiak_s1.data.gen2 show --seed 8 --n 10          # taxonomy summary + what sample jobs will ask for
nohup setsid uv run python -m kodiak_s1.data.gen2 run --n 11000 --seed 6 --workers 16 \
  --out data/synthetic/gen2_v20.jsonl --max-usd 20 > data/synthetic/gen2_v20.log 2>&1 < /dev/null &
uv run python -m kodiak_s1.data.gen2 stats --in data/synthetic/gen2_v20.jsonl   # yield, inferred/null share, $ per 1k
uv run python -m kodiak_s1.data.gen2 queue --in data/synthetic/gen2_v20.jsonl --n 50   # disagreements for human review
```

- **Budget cap:** `--max-usd` counts the whole output file (token counts × prices in `docs/progress.json`). When reached, running
  jobs finish, the run exits with a message, and rerunning with a higher cap continues.
- **Resume:** rerun the same command (finished jobs are skipped; `retry` jobs rerun). Specs are deterministic per (seed, job id), and
  the coverage snapshot is frozen per output file (`<out>.coverage.json`).
- **Near-duplicates** (MinHash, Jaccard > 0.8 against v1 + all `gen2_*.jsonl` files) are written with `status: near_duplicate` and not trained on.
- **Seeds:** 6 = training data, 7 = eval candidates (human review; never train on them), 8 = pilots. File names: `gen2_*` (training;
  feeds the coverage map `data/gen2/coverage.json`), `eval_gen2_*`, `pilot_gen2_*`.
- **Taxonomy:** `data/gen2/taxonomy_v2.json` (16 sectors, 320 domains, 971 document types), generated once with
  `... gen2 taxonomy` (refuses to overwrite without `--force`; it's versioned).
- Register every run in `docs/progress.json` → `synthetic.runs` so the dashboard shows it.

## 5. Training

```bash
# Track B, stage S1 (short states), ModernBERT-base backbone
# (current best recipe = R1; D25 defaults: --max-epochs 3 --patience 0 are built in)
nohup setsid uv run python -m kodiak_s1.train --run runs/b-small-s1-R1-cap3 --preset small --init modernbert \
  --synthetic data/synthetic/synth_v1.jsonl,data/synthetic/synth_v1_cloud.jsonl --steps 6000 --lr 5e-5 --head-lr 5e-4 \
  --warmup 300 > runs/b-small-s1-R1-cap3.log 2>&1 < /dev/null &
# then calibrate the final checkpoint and tune the abstain threshold on validation:
uv run python -m kodiak_s1.eval.run calibrate --model runs/b-small-s1-R1-cap3/checkpoints/step_0006000.pt \
  --synthetic data/synthetic/synth_v1.jsonl,data/synthetic/synth_v1_cloud.jsonl --tune-threshold \
  --out runs/b-small-s1-R1-cap3/calibration-final-thr.json
```

A run directory contains:

| File | What |
|---|---|
| `config.json`, `model_config.json` | Exact settings (a resume with different *learning* settings is refused) |
| `metrics.jsonl` | One JSON line per log step (loss parts, accuracy, lr, tokens/s, memory, GPU temp) and per eval |
| `checkpoints/step_*.pt` | Model + optimizer + scheduler (last 3 kept; written atomically) |
| `best.pt`, `best.json` | Best model by macro validation loss |

- **Resume:** rerun the same command. Data order is a function of (seed, step), so a resumed run sees the same batches.
- **Stop cleanly:** send SIGTERM (`kill <pid>`). The trainer finishes the step, checkpoints, and exits (`"event": "stopped"`).
- **Repeat cap (D25):** `--max-epochs 3` (default): no dataset is seen more than ~3 times per run; small sets were memorized otherwise.
- **Early stop is off by default (D25):** `--patience 0`. The final checkpoint beat "best" in every run we measured; `best.pt` is still
  saved for reference. `--patience N` turns early stopping back on.
- **Plumbing check:** `--overfit 32` trains on 32 fixed examples. Any healthy setup memorizes them within ~50 steps.

**Reading progress** (validation summary):
```bash
grep '"event": "eval"' runs/b-small-s1-v0/metrics.jsonl | python3 -c "
import sys, json
for l in sys.stdin:
    r = json.loads(l); print(r['step'], r['macro_loss'])"
```

**Reference numbers** (Phase 3): b-small ≈ 34k tokens/s with `torch.compile` (≈ 28k during eval-heavy stretches),
~11 GB. One epoch of the public data (≈ 53M tokens) ≈ 25 minutes.

## 5b. Exporting and publishing a model

```bash
# checkpoint + calibration -> a self-contained model folder (weights with temperatures baked in, config, calibration, tokenizer)
uv run python -m kodiak_s1.hub export --ckpt runs/b-small-s1-R1-cap3/checkpoints/step_0006000.pt \
  --calibration runs/b-small-s1-R1-cap3/calibration-final-thr.json --out dist/kodiak-small-r1
uv run python examples/quickstart.py dist/kodiak-small-r1          # smoke test (CPU or GPU)
# push to the Hugging Face org (D28); the token is HUGGINGFACE_API_KEY in ~/.bashrc, never printed
eval "$(grep -E '^\s*export HUGGINGFACE_API_KEY=' ~/.bashrc | tail -1)" && export HF_TOKEN="$HUGGINGFACE_API_KEY"
nohup setsid uv run python -m kodiak_s1.hub push --folder dist/kodiak-small-r1 \
  --repo cortex-agent-llc/kodiak-small-r1-preview --private > dist/push.log 2>&1 < /dev/null &
```

- Uploads of ~600 MB take 10–20 minutes over this machine's WiFi; run them detached and verify with the Hub API (file list + SHA-256).
- `Kodiak.from_pretrained(repo_or_folder)` *assigns* the calibration temperatures and uses the tuned abstain threshold as the default.
  (Before 2026-09-25, raw checkpoints carried temperatures of 1.0; only the eval harness applied calibration.)
- The public model card draft is `docs/MODEL_CARD.md`. Model repos use `library_name: kodiak` and `inference: false` (no generic widget).
- **Inference Endpoints:** `release/handler.py` + `release/requirements.txt` are copied into every export; test locally with
  `cd dist/<model> && uv run --project ../.. python -c "from handler import EndpointHandler; ..."`.
- **Demo Space:** `spaces/kodiak-demo/` (Gradio). Test locally: `KODIAK_MODEL=dist/kodiak-small-r1 uv run --with "gradio>=5" python spaces/kodiak-demo/app.py`.
  **Live (private):** `comgen42/kodiak-demo` (Shane's personal account, covered by HF Pro; private Spaces in the org need a paid Team plan).
  On launch day: Settings → "Rename or transfer" to `cortex-agent-llc` and make it public (public Spaces are free), then drop the `HF_TOKEN`
  secret once the model is public. Update the app with `HfApi().upload_folder(repo_id=..., repo_type="space", folder_path="spaces/kodiak-demo")`.
  Deploy a new one by creating a Gradio Space and uploading the folder; set the variable `KODIAK_MODEL`, and while the
  model is private, an `HF_TOKEN` secret with read access.

## 6. Track A pretraining corpus (deferred)

Track A is deferred (DECISIONS.md D19). A partial FineWeb-Edu `sample/10BT` download (19 of 28.5 GB, ODC-By) remains in
`data/pretrain/fineweb-edu/` (git-ignored). Free the space with `rm -rf data/pretrain/fineweb-edu`, or finish the download by
rerunning `snapshot_download('HuggingFaceFW/fineweb-edu', repo_type='dataset', allow_patterns=['sample/10BT/*'], local_dir='data/pretrain/fineweb-edu')`.

## 7. Status dashboard

```bash
uv run python -m kodiak_s1.status            # one-screen summary in the terminal
nohup setsid uv run python -m kodiak_s1.status --serve > /dev/null 2>&1 < /dev/null &   # http://localhost:8787
```

The dashboard shows phase progress, milestones, every synthetic run (progress toward the 10k-example goal, rate,
ETA, and dollar cost for cloud models), training runs with validation curves, the latest eval report, and machine health
(GPU temperature and load, unified memory, disk, loaded Ollama models). It only reads existing logs, refreshes every
15 seconds, and listens on `127.0.0.1` only.

`docs/progress.json` drives the parts that aren't in logs:
- `phases`: the checklist (update the status as work moves).
- `synthetic.runs`: one entry per synthetic run (output file, log, target jobs, writer and checker models; `"pilot": true`
  keeps a run out of the goal count). **Add an entry whenever a new run starts**, or the dashboard won't show it.
- `synthetic.prices_per_million`: `[input, output]` USD per million tokens for cloud models, used for the cost column.
- `milestones`: dated one-liners, shown newest first.

After changing `status.py`, restart the server (`pkill -f "kodiak_s1[.]status --serve"`, then relaunch).

## 8. Gotchas we hit

- **`pkill -f` can kill its own shell.** If the pattern also appears later in the same command line (for example, you pkill
  and then relaunch the same module in one command), `pkill` matches the shell running it. Run `pkill` on its own line,
  and use a bracket trick like `kodiak_s1[.]data` so the pattern doesn't match its own text.
- **Changing Ollama's context size reloads the model.** Requests with a different `num_ctx` than the loaded one trigger a
  reload. Kodiak's scripts always use 8192.
- **Measure throughput on an idle GPU.** The bf16 matmul benchmark read 26 TFLOP/s with Ollama busy and 94 idle.
- **`torch.compile` takes about a minute** on the first steps (and autotunes FlexAttention). That's expected.
