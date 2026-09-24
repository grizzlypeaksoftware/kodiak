"""Project status: phases, long-running jobs, training runs, eval results, and machine health.

    uv run python -m kodiak_s1.status                 # one-screen summary in the terminal
    uv run python -m kodiak_s1.status --serve         # dashboard at http://localhost:8787 (this machine only)

Everything is read from files the project already writes (logs, metrics.jsonl, reports) plus
nvidia-smi, /proc/meminfo, and Ollama's /api/ps. Nothing here changes any state.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _processes() -> list[str]:
    cmds = []
    for pid in os.listdir("/proc"):
        if pid.isdigit():
            try:
                cmds.append(Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace"))
            except OSError:
                pass
    return cmds


_synth_cache: dict = {}


def _read_run(path: Path) -> dict:
    """Latest record per job in a synth output file: counts and token totals. Cached until the file changes."""
    st = path.stat()
    key = (st.st_size, st.st_mtime)
    c = _synth_cache.get(path)
    if c and c["key"] == key:
        return c
    jobs: dict[int, dict] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue  # a line being written right now
            jobs[r["job"]] = r
    done = [r for r in jobs.values() if r.get("status") != "retry"]
    tok = lambda k: sum(r.get(k) or 0 for r in jobs.values())  # noqa: E731
    c = {"key": key, "done": len(done), "ok": sum(r["status"] == "ok" for r in done),
         "retry": sum(r.get("status") == "retry" for r in jobs.values()),
         "gen_in": tok("gen_prompt_tokens"), "gen_out": tok("gen_tokens"),
         "ver_in": tok("verify_prompt_tokens"), "ver_out": tok("verify_tokens")}
    _synth_cache[path] = c
    return c


def synth_status(procs: list[str], cfg: dict) -> dict:
    prices = cfg.get("prices_per_million", {})
    runs, total_ok = [], 0
    for run in cfg.get("runs", []):
        path = ROOT / run["file"]
        running = any("kodiak_s1.data.synth" in c and run["file"].rsplit("/", 1)[-1] in c for c in procs)
        r = {"name": run["name"], "pilot": run.get("pilot", False), "writer": run.get("writer"),
             "verifier": run.get("verifier"), "target_jobs": run.get("target_jobs"), "running": running}
        if path.exists():
            c = _read_run(path)
            cost = 0.0
            for model, (i, o) in ((run.get("writer"), (c["gen_in"], c["gen_out"])),
                                  (run.get("verifier"), (c["ver_in"], c["ver_out"]))):
                if model in prices:
                    cost += i / 1e6 * prices[model][0] + o / 1e6 * prices[model][1]
            r.update(done_jobs=c["done"], ok_examples=c["ok"], retry=c["retry"], cost_usd=round(cost, 4) if cost else None)
            total_ok += c["ok"] if not run.get("pilot") else 0
            log = ROOT / run["log"] if run.get("log") else None
            if log and log.exists():
                rates = re.findall(r"~(\d+) jobs/h", log.read_text()[-4000:])
                if rates:
                    rate = int(rates[-1])
                    r["jobs_per_hour"] = rate
                    if running and rate and run.get("target_jobs"):
                        r["eta_hours"] = round((run["target_jobs"] - c["done"]) / rate, 1)
            if not running:
                r["state"] = "done" if run.get("target_jobs") and c["done"] >= run["target_jobs"] else "stopped"
        r["state"] = "running" if running else r.get("state", "not started")
        runs.append(r)
    # Pilots are experiments; their examples aren't counted toward the goal (they may still be used later).
    return {"goal_examples": cfg.get("goal_examples"), "total_examples": total_ok, "runs": runs}


def training_runs(procs: list[str]) -> list[dict]:
    runs = []
    for mf in sorted((ROOT / "runs").glob("*/metrics.jsonl")):
        run = mf.parent
        cfg = json.loads((run / "config.json").read_text()) if (run / "config.json").exists() else {}
        last, evals, events = {}, [], []
        for line in open(mf):
            r = json.loads(line)
            if r.get("event") == "eval":
                evals.append({"step": r["step"], "macro_loss": r["macro_loss"]})
            elif "event" in r:
                events.append(r["event"])
            else:
                last = r
        running = any("kodiak_s1.train" in c and f"--run runs/{run.name} " in c + " " for c in procs)
        state = ("running" if running else "early stop" if "early_stop" in events
                 else next((e for e in reversed(events) if e in ("done", "stopped")), "stopped"))
        best = json.loads((run / "best.json").read_text()) if (run / "best.json").exists() else None
        runs.append({"name": run.name, "state": state, "step": last.get("step", 0), "steps": cfg.get("steps"),
                     "preset": cfg.get("preset"), "init": cfg.get("init"), "tok_per_s": last.get("tok_per_s"),
                     "loss": last.get("loss"), "best": best, "evals": evals, "overfit": bool(cfg.get("overfit"))})
    return runs


def eval_reports() -> list[dict]:
    out = []
    for p in sorted((ROOT / "reports").glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        res = json.loads(p.read_text())
        rows = []
        for system, slices in res.items():
            o = slices.get("overall", {})
            rows.append({"system": system, **{k: o.get(k) for k in ("n_questions", "accuracy", "ece", "abstain_precision",
                                                                     "abstain_recall", "latency_p50_ms")},
                         "heldout_accuracy": slices.get("eval:heldout", {}).get("accuracy")})
        out.append({"report": p.stem, "updated": time.strftime("%Y-%m-%d %H:%M", time.localtime(p.stat().st_mtime)),
                    "systems": rows})
    return out


def machine() -> dict:
    m: dict = {}
    try:
        q = subprocess.run(["nvidia-smi", "--query-gpu=temperature.gpu,power.draw,utilization.gpu",
                            "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=10).stdout.split(",")
        m.update(gpu_temp_c=int(q[0]), gpu_power_w=float(q[1]), gpu_util_pct=int(q[2]))
    except Exception:
        pass
    info = {k: int(v.split()[0]) for k, v in (line.split(":", 1) for line in open("/proc/meminfo")) if k in ("MemTotal", "MemAvailable")}
    m.update(mem_total_gb=round(info["MemTotal"] / 2**20, 1), mem_used_gb=round((info["MemTotal"] - info["MemAvailable"]) / 2**20, 1))
    du = shutil.disk_usage(ROOT)
    m.update(disk_free_gb=round(du.free / 1e9))
    try:
        ps = json.load(urllib.request.urlopen("http://localhost:11434/api/ps", timeout=3))
        m["ollama_models"] = [{"name": x["name"], "gb": round(x.get("size", 0) / 1e9, 1)} for x in ps.get("models", [])]
    except Exception:
        m["ollama_models"] = None
    return m


def collect() -> dict:
    procs = _processes()
    progress = json.loads((ROOT / "docs/progress.json").read_text())
    return {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "phases": progress["phases"],
            "synth": synth_status(procs, progress.get("synthetic", {})), "milestones": progress.get("milestones", []),
            "runs": training_runs(procs), "reports": eval_reports(), "machine": machine()}


def print_summary(s: dict) -> None:
    icon = {"done": "✓", "in_progress": "…", "pending": " ", "deferred": "–"}
    print(f"Kodiak status  {s['time']}\n")
    for p in s["phases"]:
        print(f" [{icon.get(p['status'], '?')}] Phase {p['id']}: {p['name']}")
        for st in p.get("steps", []):
            print(f"       [{icon.get(st['status'], '?')}] {st['name']}")
    y = s["synth"]
    print(f"\nSynthetic data: {y['total_examples']:,} / {y['goal_examples']:,} examples toward the goal")
    for r in y["runs"]:
        eta = f", ETA {r['eta_hours']} h" if r.get("eta_hours") else ""
        cost = f", ${r['cost_usd']:.2f}" if r.get("cost_usd") else ""
        print(f"  - {r['name']}: {r['state']}, {r.get('done_jobs', 0):,}/{r['target_jobs']:,} jobs, "
              f"{r.get('ok_examples', 0):,} examples, ~{r.get('jobs_per_hour', '?')} jobs/h{eta}{cost}")
    for r in [r for r in s["runs"] if not r["overfit"]]:
        best = f", best val {r['best']['macro_loss']} @ {r['best']['step']}" if r["best"] else ""
        print(f"Run {r['name']}: {r['state']}, step {r['step']}/{r['steps']}{best}")
    m = s["machine"]
    models = ", ".join(x["name"] for x in (m.get("ollama_models") or [])) or "none"
    print(f"\nGPU {m.get('gpu_temp_c')}°C {m.get('gpu_power_w')} W {m.get('gpu_util_pct')}% | memory {m['mem_used_gb']}/"
          f"{m['mem_total_gb']} GB | disk free {m['disk_free_gb']} GB | Ollama: {models}")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/status"):
            body, ctype = json.dumps(collect()).encode(), "application/json"
        elif self.path in ("/", "/index.html"):
            body, ctype = (ROOT / "tools/dashboard.html").read_bytes(), "text/html; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # quiet
        pass


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--port", type=int, default=8787)
    a = ap.parse_args(argv)
    if a.serve:
        print(f"Kodiak dashboard: http://localhost:{a.port}")
        ThreadingHTTPServer(("127.0.0.1", a.port), Handler).serve_forever()  # localhost only
    else:
        print_summary(collect())


if __name__ == "__main__":
    main()
