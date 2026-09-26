"""Decision-tuning trainer (docs/ARCHITECTURE.md §8, stage S1/S2).

    # Phase 3 plumbing test: memorize 32 examples with a tiny from-scratch model
    uv run python -m kodiak_s1.train --run runs/overfit-tiny --preset tiny --overfit 32 --steps 400

    # Track B: ModernBERT-base backbone
    uv run python -m kodiak_s1.train --run runs/b-small-s1 --preset small --init modernbert --steps 20000

Every run directory holds: config.json, metrics.jsonl, checkpoints/ (model + optimizer + scheduler +
step, pruned to the last few). Rerunning the same command resumes from the latest checkpoint.
Data order is a pure function of (seed, step), so a resumed run sees exactly the batches it would have.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import random
import signal
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import torch

from kodiak_s1.data.augment import gold_removed, mismatch
from kodiak_s1.data.sources import SOURCES, hash_split
from kodiak_s1.model import PRESETS, HeadConfig, KodiakModel, ModelConfig, decision_loss
from kodiak_s1.schema import render_state
from kodiak_s1.model.encoder import load_modernbert
from kodiak_s1.packing import Limits, Packed, collate, pack_example


@dataclass
class TrainConfig:
    run: str
    preset: str = "tiny"
    init: str = "scratch"  # "scratch" (Track A) or "modernbert" (Track B)
    data: str = "data/processed"
    synthetic: str = ""  # comma-separated synth JSONL files (generator output; status == ok records are used)
    synthetic_max: int = -1  # use at most this many synthetic training examples (a fixed random subset); -1 = all
    overfit: int = 0  # >0: train on only this many examples, repeatedly
    steps: int = 1000
    max_len: int = 2048  # tokens per packed row
    rows: int = 8  # rows per batch
    max_state: int = 512  # S1 trains on short states; S2 raises this
    lr: float = 5e-5
    head_lr: float = 5e-4  # new, randomly initialized heads learn faster than the pretrained encoder
    warmup: int = 200
    weight_decay: float = 0.01
    grad_clip: float = 1.0
    sample_temp: float = 0.3  # source sampling probability ∝ size^temp
    # Cap on expected passes over any one source during the run (0 = no cap). Default 3 from the recipe test (D25):
    # held-out +3.9 points; without it, small datasets were seen 20-30 times and memorized.
    max_epochs: float = 3.0
    # Train-time null augmentation (docs/ARCHITECTURE.md §9). Gold removal only applies to intent/occupation/MC
    # sources (~25% of samples), so its rate is higher to land near ~4% of all examples.
    p_gold_removed: float = 0.15
    p_mismatch: float = 0.04
    eval_every: int = 250
    val_per_source: int = 300
    # Stop after this many evals without a new best validation loss (0 = never). Off by default (D25): in every run so far,
    # the full LR schedule's final checkpoint beat early stopping's pick. Validation is still logged, and best.pt still saved.
    patience: int = 0
    seed: int = 0
    log_every: int = 10
    ckpt_every: int = 500
    keep_ckpts: int = 3
    grad_checkpointing: bool = False
    compile: bool = True  # ~2x faster on the Spark: fuses the many memory-bound elementwise ops
    max_temp_c: int = 85  # pause when the GPU is hotter than this...
    resume_temp_c: int = 75  # ...until it cools to this
    mem_fraction: float = 0.6  # cap on unified memory for this process (the desktop needs the rest)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


class Mixture:
    """Raw JSON lines per source, sampled with temperature. Parsing happens on demand."""

    def __init__(self, cfg: TrainConfig):
        self.lines: dict[str, list[str]] = {}
        for sid, src in SOURCES.items():
            p = Path(cfg.data) / sid / "train.jsonl.gz"
            if src.heldout or not p.exists():
                continue
            with gzip.open(p, "rt", encoding="utf-8") as f:
                self.lines[sid] = f.readlines()
        self.val_lines: dict[str, list[str]] = {}
        for sid, src in SOURCES.items():
            p = Path(cfg.data) / sid / "val.jsonl.gz"
            if not src.heldout and p.exists():
                with gzip.open(p, "rt", encoding="utf-8") as f:
                    self.val_lines[sid] = f.readlines()
        if cfg.synthetic:
            syn, syn_val, seen = [], [], set()
            for path in cfg.synthetic.split(","):
                for line in open(path.strip(), encoding="utf-8"):
                    r = json.loads(line)
                    if r.get("status") != "ok" or (path, r["job"]) in seen:
                        continue
                    seen.add((path, r["job"]))
                    ex = r["example"]
                    # Hold out ~3% of synthetic states for validation (by content, so it's stable as files grow).
                    # Contrast twins (Stage 3) split by their shared pair id, so both halves land on the same side.
                    split = hash_split(r.get("pair_id") or render_state(ex["state"]), val=0.03, test=0)
                    for e in [ex] + ([r["variant_example"]] if r.get("variant_example") else []):
                        (syn_val if split == "val" else syn).append(json.dumps(e, ensure_ascii=False))
            if cfg.synthetic_max >= 0:
                # A fixed random subset, so data-scaling runs differ only in *how much* synthetic data they see.
                random.Random(12345).shuffle(syn)
                syn = syn[: cfg.synthetic_max]
            if syn:
                self.lines["kodiak_synth_v1"] = syn
            if syn_val:
                self.val_lines["kodiak_synth_v1"] = syn_val  # same val set for every scaling run
        self.names = sorted(self.lines)
        sizes = [len(self.lines[n]) for n in self.names]
        w = [s ** cfg.sample_temp for s in sizes]
        self.probs = [x / sum(w) for x in w]
        self.epochs: dict[str, float] = {}
        if cfg.max_epochs > 0 and not cfg.overfit:
            self.probs = self._cap_repeats(cfg)
        self.family = {n: (SOURCES[n].family if n in SOURCES else "synthetic") for n in self.names}
        self.donors = [line for n in ("mnli", "scitail") for line in self.lines.get(n, []) if '"id": "yes"' in line]
        self.p_gold_removed, self.p_mismatch = cfg.p_gold_removed, cfg.p_mismatch
        self.fixed: list[str] | None = None
        if cfg.overfit:
            rng = random.Random(cfg.seed)
            self.fixed = [rng.choice(self.lines[rng.choices(self.names, self.probs)[0]]) for _ in range(cfg.overfit)]

    def _cap_repeats(self, cfg: TrainConfig) -> list[float]:
        """Lower the sampling share of sources that would otherwise be repeated more than `max_epochs` times.

        Temperature sampling boosts small datasets (good for diversity), but over a whole run a 558-example dataset
        was being seen dozens of times and memorized (Qasper, OpenBookQA). The freed probability mass is spread
        over the uncapped sources in proportion to their current share.
        """
        rng = random.Random(cfg.seed + 99)
        sample = [pack_example(self.sample_raw(rng), Limits(max_state=cfg.max_state)) for _ in range(400)]
        mean_len = sum(len(p) for p in sample) / len(sample)
        total = cfg.steps * cfg.rows * cfg.max_len * 0.97 / mean_len  # examples seen over the run
        sizes = [len(self.lines[n]) for n in self.names]
        caps = [cfg.max_epochs * n / total for n in sizes]
        p = list(self.probs)
        capped: set[int] = set()
        for _ in range(len(p)):
            over = [i for i in range(len(p)) if i not in capped and p[i] > caps[i]]
            if not over:
                break
            capped.update(over)
            fixed = sum(caps[i] for i in capped)
            free = [i for i in range(len(p)) if i not in capped]
            free_mass = sum(p[i] for i in free)
            for i in capped:
                p[i] = caps[i]
            for i in free:
                p[i] = p[i] / free_mass * (1 - fixed) if free_mass else 0.0
        total_p = sum(p)
        p = [x / total_p for x in p]
        self.epochs = {n: round(pi * total / sz, 2) for n, pi, sz in zip(self.names, p, sizes)}
        return p

    def sample_raw(self, rng: random.Random) -> dict:
        src = rng.choices(self.names, self.probs)[0]
        return json.loads(rng.choice(self.lines[src]))

    def describe(self) -> dict:
        return {n: {"examples": len(self.lines[n]), "p": round(p, 4), **({"epochs": self.epochs[n]} if n in self.epochs else {})}
                for n, p in zip(self.names, self.probs)}

    def sample(self, rng: random.Random) -> dict:
        if self.fixed is not None:
            return json.loads(rng.choice(self.fixed))
        src = rng.choices(self.names, self.probs)[0]
        ex = json.loads(rng.choice(self.lines[src]))
        u = rng.random()
        if u < self.p_gold_removed:
            ex = gold_removed(ex, self.family[src], rng) or ex
        elif u < self.p_gold_removed + self.p_mismatch and self.donors:
            ex = mismatch(ex, json.loads(rng.choice(self.donors)), rng) or ex
        return ex


def make_batch(mix: Mixture, cfg: TrainConfig, step: int, limits: Limits):
    """Deterministic in (seed, step): fill `rows` rows of `max_len` tokens."""
    rng = random.Random(cfg.seed * 1_000_003 + step)
    budget = cfg.rows * cfg.max_len
    packed: list[Packed] = []
    used = skipped = 0
    if mix.fixed is not None:  # overfit mode: the same examples every step
        for line in mix.fixed:
            packed.append(pack_example(json.loads(line), limits))
        return collate(packed, cfg.max_len), 0
    tries = 0
    while used < 0.97 * budget and tries < 10 * cfg.rows * 64:
        tries += 1
        p = pack_example(mix.sample(rng), limits)
        if len(p) > cfg.max_len or used + len(p) > budget:
            skipped += len(p) > cfg.max_len
            continue
        packed.append(p)
        used += len(p)
    b = collate(packed, cfg.max_len, pad_to=cfg.max_len)
    while b.input_ids.shape[0] > cfg.rows:  # greedy packing overflowed: drop the last example and retry
        packed.pop()
        b = collate(packed, cfg.max_len, pad_to=cfg.max_len)
    return b, skipped


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def build_val(mix: Mixture, cfg: TrainConfig, limits: Limits) -> dict[str, list]:
    """Fixed validation batches per source, plus a constructed-null group. Built once."""
    rng = random.Random(cfg.seed + 7)
    groups: dict[str, list[dict]] = {}
    for sid, lines in mix.val_lines.items():
        take = lines[:]
        rng.shuffle(take)
        groups[sid] = [json.loads(line) for line in take[: cfg.val_per_source]]
    nulls = []
    donors = [ex for ex in groups.get("mnli", []) + groups.get("scitail", []) if ex["questions"][0]["id"] == "claim"]
    for sid, exs in groups.items():
        for ex in exs[:40]:
            made = gold_removed(ex, mix.family.get(sid, ""), rng) or (mismatch(ex, rng.choice(donors), rng) if donors else None)
            if made:
                nulls.append(made)
    groups["null_construct"] = nulls
    batches = {}
    for g, exs in groups.items():
        packed = [p for p in (pack_example(ex, limits) for ex in exs) if len(p) <= cfg.max_len]
        batches[g] = []
        for i in range(0, len(packed), 64):
            batches[g].append(collate(packed[i:i + 64], cfg.max_len))
    return batches


@torch.no_grad()
def evaluate(model: KodiakModel, val: dict[str, list], device: str, min_questions: int = 50) -> dict:
    model.eval()
    res = {}
    sizes = {g: sum(b.q_type.shape[0] for b in bs) for g, bs in val.items()}
    for g, batches in val.items():
        tot: dict[str, float] = {}
        n = 0
        for b in batches:
            b = b.to(device)
            with torch.autocast("cuda", dtype=torch.bfloat16):
                out = model(b, impl="sdpa")  # fixed-shape-free path; matches flex (tests/test_model.py)
            _, st = decision_loss(out, b)
            w = st["n_q"]
            for k, v in st.items():
                if k != "n_q":
                    tot[k] = tot.get(k, 0.0) + v * w
            n += w
        if n:
            res[g] = {k: round(v / n, 5) for k, v in tot.items()}
    model.train()
    # Early stopping uses only groups big enough to be stable: in the first Track B run a 7-example
    # synthetic group swung the macro loss and stopped training while every real task was still improving.
    stable = [r["loss"] for g, r in res.items() if sizes.get(g, 0) >= min_questions]
    res["macro_loss"] = round(sum(stable) / max(1, len(stable)), 5)
    res["macro_groups"] = len(stable)
    return res


# ---------------------------------------------------------------------------
# Hardware guard
# ---------------------------------------------------------------------------


def gpu_status() -> dict:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=temperature.gpu,power.draw", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=10).stdout.strip().split(",")
        return {"gpu_temp_c": int(out[0]), "gpu_power_w": float(out[1])}
    except Exception:
        return {}


def thermal_guard(cfg: TrainConfig, log) -> None:
    s = gpu_status()
    if s.get("gpu_temp_c", 0) <= cfg.max_temp_c:
        return
    log({"event": "thermal_pause", **s})
    while gpu_status().get("gpu_temp_c", 0) > cfg.resume_temp_c:
        time.sleep(30)
    log({"event": "thermal_resume", **gpu_status()})


# ---------------------------------------------------------------------------
# Checkpoints
# ---------------------------------------------------------------------------


def save_ckpt(run: Path, model, opt, sched, step: int, keep: int) -> None:
    d = run / "checkpoints"
    d.mkdir(exist_ok=True)
    tmp = d / f"step_{step:07d}.pt.tmp"
    torch.save({"model": model.state_dict(), "opt": opt.state_dict(), "sched": sched.state_dict(), "step": step}, tmp)
    tmp.rename(d / f"step_{step:07d}.pt")  # atomic: a crash mid-save never leaves a corrupt "latest"
    for old in sorted(d.glob("step_*.pt"))[:-keep]:
        old.unlink()


def latest_ckpt(run: Path) -> Path | None:
    cks = sorted((run / "checkpoints").glob("step_*.pt")) if (run / "checkpoints").exists() else []
    return cks[-1] if cks else None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def build_model(cfg: TrainConfig) -> KodiakModel:
    model = KodiakModel(ModelConfig(PRESETS[cfg.preset], HeadConfig()))
    if cfg.init == "modernbert":
        repo = {"small": "answerdotai/ModernBERT-base", "base": "answerdotai/ModernBERT-large"}[cfg.preset]
        load_modernbert(model.encoder, repo)
    model.encoder.gradient_checkpointing = cfg.grad_checkpointing
    return model


def train(cfg: TrainConfig) -> dict:
    run = Path(cfg.run)
    run.mkdir(parents=True, exist_ok=True)
    cfg_path = run / "config.json"
    if cfg_path.exists():
        saved = json.loads(cfg_path.read_text())
        # Settings that don't change what is learned may differ on resume.
        operational = {"steps", "log_every", "ckpt_every", "keep_ckpts", "max_temp_c", "resume_temp_c", "mem_fraction"}
        changed = {k: (saved.get(k), v) for k, v in asdict(cfg).items() if saved.get(k) != v and k not in operational}
        if changed:
            sys.exit(f"config differs from the saved run config {changed}; use a new --run directory")
    cfg_path.write_text(json.dumps(asdict(cfg), indent=2) + "\n")

    device = "cuda"
    torch.cuda.set_per_process_memory_fraction(cfg.mem_fraction)
    torch.manual_seed(cfg.seed)
    torch.backends.cuda.matmul.allow_tf32 = True

    metrics_f = open(run / "metrics.jsonl", "a")

    def log(rec: dict) -> None:
        rec = {"time": round(time.time(), 1), **rec}
        metrics_f.write(json.dumps(rec) + "\n")
        metrics_f.flush()
        print(json.dumps(rec), flush=True)

    mix = Mixture(cfg)
    model = build_model(cfg).to(device)
    model.cfg.save(run / "model_config.json")
    n_params = sum(p.numel() for p in model.parameters())
    n_emb = model.encoder.embeddings.tok_embeddings.weight.numel()

    no_decay = lambda n, p: p.dim() == 1  # noqa: E731  norms and biases
    groups = [
        {"params": [p for n, p in model.encoder.named_parameters() if not no_decay(n, p)], "lr": cfg.lr, "weight_decay": cfg.weight_decay},
        {"params": [p for n, p in model.encoder.named_parameters() if no_decay(n, p)], "lr": cfg.lr, "weight_decay": 0.0},
        {"params": list(model.heads.parameters()), "lr": cfg.head_lr, "weight_decay": 0.0},
    ]
    opt = torch.optim.AdamW(groups, betas=(0.9, 0.98), eps=1e-6, fused=True)

    def lr_lambda(step: int) -> float:  # linear warmup, then cosine decay to 10%
        if step < cfg.warmup:
            return (step + 1) / cfg.warmup
        t = min(1.0, (step - cfg.warmup) / max(1, cfg.steps - cfg.warmup))
        return 0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * t))

    sched = torch.optim.lr_scheduler.LambdaLR(opt, lr_lambda)
    step = 0
    ck = latest_ckpt(run)
    if ck:
        state = torch.load(ck, map_location=device, weights_only=False)
        model.load_state_dict(state["model"])
        opt.load_state_dict(state["opt"])
        sched.load_state_dict(state["sched"])
        step = state["step"]
    log({"event": "start" if not ck else "resume", "step": step, "params": n_params, "embedding_params": n_emb,
         "sources": mix.describe(), **gpu_status()})

    stop = {"flag": False}

    def on_signal(signum, frame):
        stop["flag"] = True  # finish the current step, checkpoint, exit

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)

    fwd = torch.compile(model) if cfg.compile else model
    limits = Limits(max_state=cfg.max_state)
    val = build_val(mix, cfg, limits) if not cfg.overfit else {}
    best_path = run / "best.json"
    best = json.loads(best_path.read_text()) if best_path.exists() else {"macro_loss": float("inf"), "step": 0}
    bad_evals = 0
    model.train()
    t_last, tok_acc, last = time.time(), 0, {}
    while step < cfg.steps and not stop["flag"]:
        batch, skipped = make_batch(mix, cfg, step, limits)
        batch = batch.to(device)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            out = fwd(batch)
        loss, stats = decision_loss(out, batch)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        gnorm = torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.grad_clip).item()
        opt.step()
        sched.step()
        step += 1
        tok_acc += batch.n_tokens
        if not math.isfinite(stats["loss"]):
            log({"event": "nonfinite_loss", "step": step, **stats})
            break
        if step % cfg.log_every == 0 or step == cfg.steps:
            torch.cuda.synchronize()
            dt = time.time() - t_last
            last = {"step": step, **{k: round(v, 5) if isinstance(v, float) else v for k, v in stats.items()},
                    "grad_norm": round(gnorm, 3), "lr": sched.get_last_lr()[0], "tok_per_s": round(tok_acc / dt),
                    "rows": batch.input_ids.shape[0], "skipped_long": skipped,
                    "mem_gb": round(torch.cuda.max_memory_allocated() / 2**30, 2), **gpu_status()}
            log(last)
            t_last, tok_acc = time.time(), 0
            thermal_guard(cfg, log)
        if val and (step % cfg.eval_every == 0 or step == cfg.steps):
            ev = evaluate(model, val, device)
            log({"event": "eval", "step": step, **ev})
            if ev["macro_loss"] < best["macro_loss"]:
                best = {"macro_loss": ev["macro_loss"], "step": step}
                torch.save(model.state_dict(), run / "best.pt.tmp")
                (run / "best.pt.tmp").rename(run / "best.pt")
                best_path.write_text(json.dumps(best) + "\n")
                bad_evals = 0
            else:
                bad_evals += 1
                if cfg.patience and bad_evals >= cfg.patience:
                    log({"event": "early_stop", "step": step, "best": best})
                    break
        if step % cfg.ckpt_every == 0:
            save_ckpt(run, model, opt, sched, step, cfg.keep_ckpts)
    save_ckpt(run, model, opt, sched, step, cfg.keep_ckpts)
    log({"event": "stopped" if stop["flag"] else "done", "step": step})
    metrics_f.close()
    return last


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for name, fld in TrainConfig.__dataclass_fields__.items():
        flag, default = f"--{name.replace('_', '-')}", fld.default
        if name == "run":
            ap.add_argument(flag, required=True, help="run directory (resumes if it exists)")
        elif isinstance(default, bool):
            ap.add_argument(flag, action=argparse.BooleanOptionalAction, default=default)
        else:
            ap.add_argument(flag, type=type(default), default=default)
    args = ap.parse_args(argv)
    train(TrainConfig(**vars(args)))


if __name__ == "__main__":
    main()
