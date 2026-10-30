"""REPS audit: replay every (account, session) as live through mcf.replay (the real PaperRunner, frozen setups of the
session from the account's data branch, live universe ∩ lab universe, Alpaca-paper fills: half-spread market/stop,
touch limits). One process pool over all (account, day) jobs, slowest account first.

    MCF_REPLAY_STORE=<private store> python research/bdi/replay_audit1029/run.py 2026-10-27..2026-10-29 [--jobs 4]

Output: $MCF_REPLAY_STORE/runs/reps1029/<account>/<day>/... Educational only - not financial advice."""
import argparse
import json
import sys
import time
from multiprocessing import get_context
from pathlib import Path

from mcf.replay import store
from mcf.replay.__main__ import _line, parse_dates

ACCTS = ["testing2", "testing", "graveyard", "gen", "primary"]
START = {"primary": "2026-10-07", "testing": "2026-10-09", "testing2": "2026-10-12", "graveyard": "2026-10-21",
         "gen": "2026-10-19"}          # first frozen setups/<d>.json on each data branch

def session_flags(day: str, branch: str) -> dict | None:
    """symbol -> (shortable, easy_to_borrow) from the account's universe.csv of that session (latest commit on or before
    the day) instead of the harness default (today's data/universe.csv, which here is 2026-10-05's)."""
    import io
    import subprocess

    import pandas as pd

    r = subprocess.run(["git", "-C", str(store.ROOT), "log", "--format=%H %ad", "--date=short", branch, "--",
                        "universe.csv"], capture_output=True, text=True)
    for line in r.stdout.splitlines():
        sha, d = line.split()
        if d <= day:
            csv = subprocess.run(["git", "-C", str(store.ROOT), "show", f"{sha}:universe.csv"], capture_output=True,
                                 text=True).stdout
            u = pd.read_csv(io.StringIO(csv), usecols=["symbol", "shortable", "easy_to_borrow"])
            return {str(s): (bool(a), bool(b)) for s, a, b in zip(u.symbol, u.shortable, u.easy_to_borrow)}
    return None


def _one(job: dict) -> dict:
    """mcf.replay.__main__._one plus the session's own shortable / ETB flags."""
    import traceback

    from mcf.replay import harness

    d = job["day"]
    out = Path(job["out"]) / job["account"] / d
    if (out / "stats.json").exists():
        return json.loads((out / "stats.json").read_text())
    try:
        cfg = harness.account_config(job["account"], d, as_live=True)
        branch = harness.data_branch(job["account"])
        bars, priors, notes = harness.session_inputs(cfg, d, universe="live", branch=branch)
        fl = session_flags(d, branch)
        notes["etb_flags"] = "session universe.csv" if fl else "today's data/universe.csv (fallback)"
        res = harness.run_session(cfg, d, bars, priors, fills="paper", limit_fill="touch", check=0,
                                  shortable=fl, log=lambda m: None)
        res["stats"]["inputs"] = notes
        res["stats"]["missing_modules"] = cfg.get("_replay_missing_modules", [])
        res["stats"]["config_commit"] = cfg.get("_replay_config_commit")
        harness.write(res, out)
        return res["stats"]
    except Exception as e:  # one bad session must not stop the run
        return {"day": d, "account": job["account"], "error": f"{type(e).__name__}: {e}",
                "trace": traceback.format_exc()[-1500:]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("dates")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--accounts", default=",".join(ACCTS))
    a = ap.parse_args()
    out = store.STORE / "runs" / "reps1029"
    days = parse_dates(a.dates)
    jobs = [dict(day=str(d), account=ac, as_live=True, setup=None, module=None, alone=False, block=None,
                 universe="live", fills="paper", limit_fill="touch", exact=False, check=0, out=str(out), force=False)
            for ac in a.accounts.split(",") for d in days if str(d) >= START[ac]]
    print(len(jobs), "jobs", flush=True)
    t0 = time.time()
    with get_context("fork").Pool(a.jobs, maxtasksperchild=1) as pool:
        for st in pool.imap_unordered(_one, jobs):
            print(f"[{time.time() - t0:.0f}s]", _line(st), flush=True)
            if "error" in st:
                print(st.get("trace"), flush=True)
    print("done", flush=True)
