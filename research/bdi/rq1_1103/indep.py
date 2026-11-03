"""REG1 independent sessions: Primary's CURRENT setups and account config (today's config files, MCF_ACCOUNT=primary)
replayed through the real PaperRunner (mcf.replay.harness.run_session, Alpaca-paper fills, touch limits) on sessions
BEFORE Primary's first live session (2026-10-06), so no day overlaps the live sample. Lab universe (1,226 names; Primary's
setups need ADV >= $95M, which the lab list covers), synthetic spread draw from the journaled live spreads, default
borrow flags, no earnings blackout on record. The replay has NOT cleared rule 21 for these inputs (night1102 config A
matched 72-78% on Primary); results are a second opinion, never a filter.
    MCF_REPLAY_STORE=<lab store> python indep.py <dates> --out <dir> [--jobs 2]
Educational only - not financial advice."""
import argparse
import json
import time
import traceback
from multiprocessing import get_context
from pathlib import Path


def _one(job):
    from mcf.replay import harness
    d, out = job["day"], Path(job["out"]) / job["day"]
    if (out / "stats.json").exists():
        return json.loads((out / "stats.json").read_text())
    try:
        cfg = harness.account_config("primary")
        bars, priors, notes = harness.session_inputs(cfg, d, universe="lab")
        res = harness.run_session(cfg, d, bars, priors, fills="paper", limit_fill="touch", check=0, log=lambda m: None)
        res["stats"].update(inputs=notes)
        harness.write(res, out)
        return res["stats"]
    except Exception as e:
        return {"day": d, "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()[-1500:]}


if __name__ == "__main__":
    from mcf.replay.__main__ import parse_dates
    ap = argparse.ArgumentParser()
    ap.add_argument("dates")
    ap.add_argument("--out", required=True)
    ap.add_argument("--jobs", type=int, default=2)
    a = ap.parse_args()
    jobs = [dict(day=str(d), out=a.out) for d in parse_dates(a.dates)]
    t0 = time.time()
    with get_context("fork").Pool(a.jobs, maxtasksperchild=1) as pool:
        for st in pool.imap_unordered(_one, jobs):
            print(f"[{time.time() - t0:.0f}s]", st.get("day"), st.get("error") or (st.get("seconds"), st.get("setups") and len(st["setups"])), flush=True)
    print("done")
