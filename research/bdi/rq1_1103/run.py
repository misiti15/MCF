"""RQ1 replay audit 2026-11-03 (research rule 21): the night-1102 fixed replay (FB = full live universe + recorded
NBBO + recorded borrow, research/bdi/night1102/replay/run.py) on 10 sessions with recordings, most recent first.

Sessions before 2026-10-27 ran live with the pre-GX1 lab gate (len(bars) % 5 == 0). For those sessions the replay is
run like-for-like with that gate (research/ops/gx1clockgate1026_oldgate.py: the same monkeypatch of
mcf.strategies.setups.lab_decision_buckets, in the replay process only). On 2026-10-26 every live account started at
~10:39, so that replay's clock starts at 10:39. Nothing else differs from night1102 FB.

    MCF_REPLAY_STORE=<full store> python run.py FB <dates> --accounts primary,testing,testing2 --journals <dir>

Research only; nothing here trades and the live code is not changed. Educational only - not financial advice."""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NIGHT = ROOT / "research/bdi/night1102/replay"
sys.path.insert(0, str(NIGHT))
sp = importlib.util.spec_from_file_location("night1102_run", NIGHT / "run.py")
N = importlib.util.module_from_spec(sp)
sp.loader.exec_module(N)
FIX = "2026-10-27"
LATE = {"2026-10-26": "2026-10-26 10:39:00"}   # first live poll 10:39 (restart after the GX1 merge window)


def _one(job: dict) -> dict:
    import pandas as pd
    if job["day"] < FIX:             # live ran the old bar-count gate before GX1: replay it the same way
        from mcf.strategies import setups as S
        f = pd.Timedelta(minutes=4)

        def old(index):
            n = len(index)
            return [index[-1] - f] if n >= 5 and n % 5 == 0 else []
        S.lab_decision_buckets = old
    if job["day"] in LATE:            # live started late that session (all five accounts): start the replay clock then
        from mcf.replay import broker, harness
        t = LATE[job["day"]]

        class LateClock(broker.SimClock):
            def __init__(self, now):
                super().__init__(max(pd.Timestamp(now).tz_convert(broker.NY), pd.Timestamp(t, tz=broker.NY)))
        harness.SimClock = LateClock
    return N._one(job)


if __name__ == "__main__":
    import argparse
    import time
    from multiprocessing import get_context
    from mcf.replay import store
    from mcf.replay.__main__ import _line, parse_dates
    ap = argparse.ArgumentParser()
    ap.add_argument("confs")
    ap.add_argument("dates")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--accounts", default="primary,testing,testing2")
    ap.add_argument("--journals", required=True)
    a = ap.parse_args()
    out = store.STORE / "runs" / "rq1_1103"
    jobs = [dict(day=str(d), account=ac, conf=c, out=str(out), journals=a.journals)
            for d in parse_dates(a.dates) for ac in a.accounts.split(",") for c in a.confs.split(",")]
    print(len(jobs), "jobs", flush=True)
    t0 = time.time()
    with get_context("fork").Pool(a.jobs, maxtasksperchild=1) as pool:
        for st in pool.imap_unordered(_one, jobs):
            print(f"[{time.time() - t0:.0f}s]", st.get("conf"), _line(st), st.get("quote_source", ""),
                  st.get("borrow_overrides", ""), flush=True)
            if "error" in st:
                print(st.get("trace"), flush=True)
    print("done", flush=True)
