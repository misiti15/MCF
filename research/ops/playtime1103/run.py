"""Playtime 2026-11-03 (owner GY-BP refined): Graveyard and Gen replays 10-27..11-03 under three variants.

Base = research/bdi/night1102/replay FB (real PaperRunner via mcf.replay.harness.run_session, frozen setups/<d>.json,
account config committed before the open, full live universe + live-prep priors, recorded NBBO + recorded borrow,
Alpaca-paper fills, limits touch). Variants (3 configurations, fixed before any result was read):
  V0 today   rules as live ran them
  V1 cap12   account.max_positions_per_strategy -> 12 (Graveyard 25 -> 12; Gen 48 -> 12, same absolute cap)
  V2 rot3    the account's top-3 setups by live trade count 10-27..11-03 benched (enabled: false) on alternating
             sessions 10-27 / 10-29 / 11-02, on as usual 10-28 / 10-30 / 11-03
Buying power: the simulated broker never rejects for buying power, live Graveyard did. Every variant gets the same
per-session ceiling on gross open notional (+ working entries), calibrated from live: ceiling = live gross open notional
at that session's first live 'insufficient buying power' reject + the buying power Alpaca reported in it
(GY 10-28 $263.5k, 10-29 $208.1k, 11-02 $242.2k, 11-03 $231.9k; no ceiling where live never hit one, and none for Gen:
its 12 rejects on 10-30 were the HK-RECON booking lag). An entry over the ceiling raises the Alpaca 40310000 message, which
the runner journals as 'rejected', as live.

    MCF_REPLAY_STORE=<store> python run.py V0,V1,V2 2026-10-27..2026-11-03 --accounts graveyard,gen --journals <dir>
Research only; nothing here trades and the live code is not changed. Educational only - not financial advice."""
import importlib.util
import os
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("MCF_ROOT", "/home/user/MCF"))
NIGHT = ROOT / "research/bdi/night1102/replay"
sys.path.insert(0, str(NIGHT))
CEIL = {"graveyard": {"2026-10-28": 263496.0, "2026-10-29": 208147.0, "2026-11-02": 242231.0, "2026-11-03": 231897.0}}
TOP3 = {"graveyard": ["CWT14-failbrk-orl-p05-long", "CWT14-failbrk-orl-p05-lowvol-long", "CWT12-coil-k4-long"],
        "gen": ["GEN-261021-06-ORBfailUp-Gapge1p2-MID-BRopgt0p5-hold-long",
                "GEN-261020-07-RSIslopege19-LowWickge0p33-ATRdge4p4-AM-BRvwgt0p7-hold-long",
                "GEN-261022-07-Z12lem1p9-FlowShiftlem0p96-ATRdge3p6-AM-BRopgt0p5-t1s1-short"]}
BENCH_DAYS = {"2026-10-27", "2026-10-29", "2026-11-02"}


def _one(job: dict) -> dict:
    from mcf.replay import broker, harness
    v, ac, d = job["var"], job["account"], job["day"]
    ceil = CEIL.get(ac, {}).get(d)
    if ceil:
        orig = broker.SimTradingClient.submit_order

        def submit(self, req, _o=orig, _c=ceil):
            oc = broker._v(getattr(req, "order_class", None) or "simple")
            if oc in ("bracket", "oto"):
                k = self.mkt.minute(self.clock.now)
                px = float(getattr(req, "limit_price", None) or self.mkt.last_close(req.symbol, k) or 0.0)
                used = sum(abs(q) * (self.mkt.last_close(s, k) or self.avg.get(s, 0.0)) for s, q in self.pos.items())
                used += sum(abs(float(o.qty)) * float(o.limit_price or self.mkt.last_close(o.symbol, k) or 0.0)
                            for o in self.orders if o._role == "entry" and o.status in broker.OPEN)
                cost = abs(float(req.qty)) * px
                if used + cost > _c:
                    raise RuntimeError(json.dumps({"buying_power": f"{max(0.0, _c - used):.2f}", "code": 40310000,
                                                   "cost_basis": f"{cost:.2f}", "message": "insufficient buying power"}))
            return _o(self, req)
        broker.SimTradingClient.submit_order = submit
    ac_orig = harness.account_config

    def account_config(account, day=None, as_live=False, branch=None):
        cfg = ac_orig(account, day, as_live=as_live, branch=branch)
        if v == "V1":
            cfg["account"]["max_positions_per_strategy"] = 12
        if v == "V2" and d in BENCH_DAYS:
            for n in TOP3[account]:
                if n in cfg["strategies"]:
                    cfg["strategies"][n] = {**(cfg["strategies"][n] or {}), "enabled": False}
        return cfg
    harness.account_config = account_config
    sp = importlib.util.spec_from_file_location("night1102_run", NIGHT / "run.py")
    N = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(N)
    st = N._one(dict(day=d, account=ac, conf=job.get("conf", "FB"), out=str(Path(job["out"]) / v), journals=job["journals"]))
    st["var"] = v
    return st


if __name__ == "__main__":
    import argparse
    import time
    from multiprocessing import get_context
    from mcf.replay import store
    from mcf.replay.__main__ import _line, parse_dates
    ap = argparse.ArgumentParser()
    ap.add_argument("vars")
    ap.add_argument("dates")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--accounts", default="graveyard,gen")
    ap.add_argument("--journals", required=True)
    ap.add_argument("--conf", default="FB")
    a = ap.parse_args()
    out = store.STORE / "runs" / "playtime1103"
    jobs = [dict(day=str(d), account=ac, var=v, out=str(out), journals=a.journals, conf=a.conf)
            for d in parse_dates(a.dates) for ac in a.accounts.split(",") for v in a.vars.split(",")]
    jobs.sort(key=lambda j: j["account"] != "gen")      # the slow account first
    print(len(jobs), "jobs", flush=True)
    t0 = time.time()
    with get_context("fork").Pool(a.jobs, maxtasksperchild=1) as pool:
        for st in pool.imap_unordered(_one, jobs):
            print(f"[{time.time() - t0:.0f}s]", st.get("var"), _line(st), flush=True)
            if "error" in st:
                print(st.get("trace"), flush=True)
    print("done", flush=True)
