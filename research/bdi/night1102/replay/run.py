"""Replay audit re-run 2026-11-02 night: every (account, post-fix session) through mcf.replay.harness.run_session (the
real PaperRunner, frozen setups, config at the open, lab universe ∩ live universe, Alpaca-paper fills), in one of
three input configurations:
  A  base      as the 10-29 audit: synthetic spread draw, session universe.csv ETB flags
  B  recorded  the NBBO live journaled at the same symbol + minute (recorded.py), the account's own recorded borrow
               answers (others' as fallback), else as A
  C  newsetup  what a NEW setup would get: recorded quotes of the symbol only >= 2 min away from its own minute and
               the OTHER accounts' borrow answers, else as A
  FA / FB / FC the same on the full live universe (prep_full.py store: ~4,700 names, live-prep priors)
    MCF_REPLAY_STORE=<store> python run.py <config> <dates> --jobs 2 --journals <dir>
Educational only - not financial advice."""
import argparse
import json
import sys
import time
import traceback
from multiprocessing import get_context
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from mcf.replay import store  # noqa: E402
from mcf.replay.__main__ import _line, parse_dates  # noqa: E402

ACCTS = ["gen", "graveyard", "testing2", "testing", "primary"]


def _one(job: dict) -> dict:
    from mcf.replay import harness
    import recorded
    import importlib.util
    sp = importlib.util.spec_from_file_location("audit1029_run", HERE.parents[1] / "replay_audit1029" / "run.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    session_flags = m.session_flags

    d, ac, full_conf = job["day"], job["account"], job["conf"]
    out = Path(job["out"]) / full_conf / ac / d
    conf = full_conf[-1]
    if full_conf.startswith("F"):   # full live universe: the store's universe/<d>.txt (prep_full.py), not the lab list
        u = (store.STORE / "universe" / f"{d}.txt").read_text().split()
        store.symbols = lambda u=u: u
    if (out / "stats.json").exists():
        return json.loads((out / "stats.json").read_text())
    try:
        cfg = harness.account_config(ac, d, as_live=True)
        branch = harness.data_branch(ac)
        bars, priors, notes = harness.session_inputs(cfg, d, universe="live", branch=branch)
        fl = session_flags(d, branch)
        extra = {}
        if conf in ("B", "C"):
            rec = recorded.build(d, Path(job["journals"]))
            if conf == "C":
                rec["borrow"] = {k: v for k, v in rec["borrow"].items() if k != ac}
            fl, extra["borrow_overrides"] = recorded.borrow_flags(rec, ac, fl)
            recorded.RecordedQuotes.rec = rec["quotes"]
            recorded.RecordedQuotes.mode = "exact" if conf == "B" else "near"
            recorded.RecordedQuotes.used = {}
            harness.SimDataClient = recorded.RecordedQuotes
        res = harness.run_session(cfg, d, bars, priors, fills="paper", limit_fill="touch", check=0,
                                  shortable=fl, log=lambda m: None)
        if conf in ("B", "C"):
            extra["quote_source"] = dict(recorded.RecordedQuotes.used)
        res["stats"].update(inputs=notes, conf=full_conf, missing_modules=cfg.get("_replay_missing_modules", []),
                            config_commit=cfg.get("_replay_config_commit"), **extra)
        harness.write(res, out)
        return res["stats"]
    except Exception as e:
        return {"day": d, "account": ac, "conf": full_conf, "error": f"{type(e).__name__}: {e}",
                "trace": traceback.format_exc()[-1500:]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("confs")
    ap.add_argument("dates")
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--accounts", default=",".join(ACCTS))
    ap.add_argument("--journals", required=True)
    a = ap.parse_args()
    out = store.STORE / "runs" / "night1102"
    jobs = [dict(day=str(d), account=ac, conf=c, out=str(out), journals=a.journals)
            for ac in a.accounts.split(",") for d in parse_dates(a.dates) for c in a.confs.split(",")]
    print(len(jobs), "jobs", flush=True)
    t0 = time.time()
    with get_context("fork").Pool(a.jobs, maxtasksperchild=1) as pool:
        for st in pool.imap_unordered(_one, jobs):
            print(f"[{time.time() - t0:.0f}s]", st.get("conf"), _line(st), st.get("quote_source", ""),
                  st.get("borrow_overrides", ""), flush=True)
            if "error" in st:
                print(st.get("trace"), flush=True)
    print("done", flush=True)
