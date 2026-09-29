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
import urllib.parse
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
    c = {"key": key, "done": len(done),
         "ok": sum(r["status"] == "ok" for r in done) + sum(bool(r.get("variant_example")) for r in done),  # + contrast twins
         "retry": sum(r.get("status") == "retry" for r in jobs.values()),
         "gen_in": tok("gen_prompt_tokens"), "gen_out": tok("gen_tokens"),
         "ver_in": tok("verify_prompt_tokens"), "ver_out": tok("verify_tokens"), "critic": {}}
    c["extra"] = {}
    for r in jobs.values():  # Generator v2 critic calls, and Stage 3's second blind rater ("extra")
        for key, usage in (("critic", r.get("critic_usage", [])), ("extra", r.get("extra_usage", []))):
            for u in usage:
                m = c[key].setdefault(u["model"], [0, 0])
                m[0] += u.get("prompt_tokens") or 0
                m[1] += u.get("tokens") or 0
    _synth_cache[path] = c
    return c


def synth_status(procs: list[str], cfg: dict) -> dict:
    prices = cfg.get("prices_per_million", {})
    runs, total_ok, ok_by_file = [], 0, {}
    for run in cfg.get("runs", []):
        path = ROOT / run["file"]
        # Only a generator process writing this file counts (a shell whose command text merely mentions the file doesn't).
        running = any(("kodiak_s1.data.synth" in c or "kodiak_s1.data.gen2" in c) and f"--out {run['file']}" in c
                      and not c.lstrip().startswith(("/bin/bash", "bash")) for c in procs)
        r = {"name": run["name"], "pilot": run.get("pilot", False), "writer": run.get("writer"),
             "verifier": run.get("verifier"), "target_jobs": run.get("target_jobs"), "running": running}
        if path.exists():
            c = _read_run(path)
            parts = {"writer": 0.0, "checker": 0.0, "critics": 0.0, "extra": 0.0}
            by_model: dict[str, float] = {}
            for role, model, (i, o) in (("writer", run.get("writer"), (c["gen_in"], c["gen_out"])),
                                        ("checker", run.get("verifier"), (c["ver_in"], c["ver_out"])),
                                        *(("critics", m, tuple(t)) for m, t in c.get("critic", {}).items()),
                                        *(("extra", m, tuple(t)) for m, t in c.get("extra", {}).items())):
                if model in prices:
                    usd = i / 1e6 * prices[model][0] + o / 1e6 * prices[model][1]
                    parts[role] += usd
                    by_model[model] = by_model.get(model, 0.0) + usd
            cost = sum(parts.values())
            r.update(done_jobs=c["done"], ok_examples=c["ok"], retry=c["retry"], cost_usd=round(cost, 4) if cost else None,
                     cost_parts={k: round(v, 4) for k, v in parts.items()}, cost_by_model={k: round(v, 4) for k, v in by_model.items()},
                     date=time.strftime("%Y-%m-%d", time.localtime(path.stat().st_mtime)))
            total_ok += c["ok"] if not run.get("pilot") else 0
            if not run.get("pilot"):
                ok_by_file[run["file"]] = c["ok"]
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
        r["file"] = run["file"]
        runs.append(r)
    # Staged goals: each generator version has its own target, counted from its own (non-pilot) output files.
    stages, current_found = [], False
    for st in cfg.get("stages", []):
        n = sum(ok_by_file.get(f, 0) for f in st.get("files", []))
        running = any(r["state"] == "running" and r["file"] in st.get("files", []) for r in runs)
        # A stage marked done stays done (a process whose command line merely mentions its file isn't a run), and a stage whose work
        # isn't counted in files (e.g. a training test) can set its own state.
        state = ("done" if st.get("done") else st.get("state") or ("running" if running else "done" if n >= st["goal"]
                                                                   else "in progress" if n else "planned"))
        if running and not st.get("done"):
            state = "running"
        current = not current_found and state != "done"
        current_found = current_found or current
        stages.append({"name": st["name"], "why": st.get("why", ""), "goal": st["goal"], "examples": n, "state": state,
                       "current": current})
    # Pilots are experiments; their examples aren't counted toward the goal (they may still be used later).
    spent = round(sum(r.get("cost_usd") or 0 for r in runs), 2)
    budget = cfg.get("budget") or {}
    return {"goal_examples": cfg.get("goal_examples"), "total_examples": total_ok, "stages": stages, "runs": runs,
            "spent_usd": spent, "budget_usd": budget.get("total_usd"), "budget_note": budget.get("note", "")}


def training_runs(procs: list[str]) -> list[dict]:
    runs = []
    for mf in sorted((ROOT / "runs").glob("*/metrics.jsonl")):
        run = mf.parent
        cfg = json.loads((run / "config.json").read_text()) if (run / "config.json").exists() else {}
        last, evals, events, first_t, powers = {}, [], [], None, []
        for line in open(mf):
            r = json.loads(line)
            if "time" in r:
                first_t = first_t if first_t is not None else r["time"]
            if r.get("gpu_power_w"):
                powers.append(r["gpu_power_w"])
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
                     "loss": last.get("loss"), "best": best, "evals": evals, "overfit": bool(cfg.get("overfit")),
                     "wall_hours": round((last.get("time", first_t or 0) - (first_t or 0)) / 3600, 2) if first_t else 0.0,
                     "avg_power_w": round(sum(powers) / len(powers), 1) if powers else None,
                     "started": time.strftime("%Y-%m-%d %H:%M", time.localtime(first_t)) if first_t else None,
                     "ended": time.strftime("%H:%M", time.localtime(last["time"])) if last.get("time") else None,
                     "started_ts": first_t or 0})
    return runs


def queue_status(queue: list[dict], procs: list[str]) -> list[dict]:
    """Upcoming work from docs/progress.json → queue. A scripted item is running while its script process lives and its log shows
    work, waiting while the script only waits for its turn, and done once the log has its completion marker."""
    out = []
    for q in queue:
        q = dict(q)
        log = ROOT / q["log"] if q.get("log") else None
        text = log.read_text(errors="replace") if log and log.exists() else ""
        alive = bool(q.get("script")) and any(q["script"] in c and not c.lstrip().startswith("/bin/bash -c") for c in procs)
        lines = [line for line in text.splitlines() if line.strip()]
        if q.get("done_marker") and q["done_marker"] in text:
            q["state"] = "done"
        elif "training failed" in text:
            q["state"] = "failed"
        elif alive and lines:
            q["state"] = "running"
        elif alive:
            q["state"] = "waiting"
        else:
            q["state"] = "planned"
        q["last_line"] = lines[-1][:200] if lines else ""
        out.append(q)
    return out


def group_runs(runs: list[dict], experiments: list[dict], published: list[dict]) -> list[dict]:
    """Attach each training run to its experiment (first matching pattern) and to any public release made from it."""
    by_run: dict[str, list[dict]] = {}
    for p in published:  # "run" may be one run name or a list (an ensemble such as accuracy mode)
        for name in ([p["run"]] if isinstance(p.get("run"), str) else p.get("run") or []):
            by_run.setdefault(name, []).append(p)
    for r in runs:
        exp = next((e for e in experiments if re.search(e["match"], r["name"])), None)
        r["experiment"] = exp["name"] if exp else "Other"
        r["published"] = [{"name": p["name"], "link": p.get("link"), "superseded": p.get("superseded", False), "badge": p.get("badge")}
                          for p in by_run.get(r["name"], [])]
    return runs


def finance(synth: dict, runs: list[dict], cfg: dict) -> dict:
    """Money in one place: cloud API spend (logged tokens × list prices), fixed subscriptions, and the free local compute."""
    def category(r: dict) -> str:
        n = r["name"].lower()
        return "pilots" if r.get("pilot") else "eval data" if "eval candidates" in n else "side batches" if n.startswith(("side batch", "calibration")) \
            else "training data"
    items = []
    for r in synth["runs"]:
        if not r.get("cost_usd"):
            continue
        kept = r.get("ok_examples") or 0
        items.append({"name": r["name"], "category": category(r), "date": r.get("date"), "usd": r["cost_usd"], "kept": kept,
                      "usd_per_1k": round(1000 * r["cost_usd"] / kept, 2) if kept else None, "parts": r.get("cost_parts", {}),
                      "running": r.get("state") == "running"})
    by = lambda key: {k: round(sum(i["usd"] for i in items if i[key] == k), 2) for k in dict.fromkeys(i[key] for i in items)}  # noqa: E731
    models: dict[str, float] = {}
    for r in synth["runs"]:
        for m, v in (r.get("cost_by_model") or {}).items():
            models[m] = round(models.get(m, 0.0) + v, 2)
    daily: dict[str, float] = {}
    for i in items:
        daily[i["date"]] = round(daily.get(i["date"], 0.0) + i["usd"], 2)
    hours, kwh = 0.0, 0.0
    for r in runs:
        h = r.get("wall_hours") or 0.0
        hours += h
        kwh += h * (r.get("avg_power_w") or 0.0) / 1000
    fin = cfg.get("finance", {})
    return {"budget_usd": synth.get("budget_usd"), "spent_usd": synth.get("spent_usd"), "items": items, "by_category": by("category"),
            "by_model": models, "daily": dict(sorted(daily.items())), "fixed": fin.get("fixed", []), "note": fin.get("note", ""),
            "gpu_hours": round(hours, 1), "gpu_kwh": round(kwh, 1), "training_runs": len(runs),
            "kept_examples": sum(i["kept"] for i in items if i["category"] in ("training data", "side batches"))}


def report_list() -> list[dict]:
    return [{"name": p.stem, "updated": time.strftime("%Y-%m-%d %H:%M", time.localtime(p.stat().st_mtime))}
            for p in sorted((ROOT / "reports").glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)]


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
    published = progress.get("published", [])
    synth, runs = synth_status(procs, progress.get("synthetic", {})), training_runs(procs)
    return {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "phases": progress["phases"],
            "synth": synth, "milestones": progress.get("milestones", []), "finance": finance(synth, runs, progress),
            "runs": group_runs(runs, progress.get("experiments", []), published), "reports": eval_reports(),
            "report_list": report_list(), "queue": queue_status(progress.get("queue", []), procs), "published": published,
            "experiments": progress.get("experiments", []), "machine": machine()}


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
        elif self.path.startswith("/api/report/"):
            name = urllib.parse.unquote(self.path.split("/api/report/", 1)[1])
            path = ROOT / "reports" / f"{name}.md"
            if not re.fullmatch(r"[\w.\-]+", name) or not path.is_file():  # report names only, no paths
                self.send_error(404)
                return
            body, ctype = path.read_bytes(), "text/markdown; charset=utf-8"
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
