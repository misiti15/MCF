"""Live-shaped check: the 9 Testing 2 setups (LD1-LD8 + M1) built by build_strategies from config/account_testing2.yaml
run through the live LabStrategy on real 1-minute bars (SymbolHistory contexts as the backtester builds them, peers =
the lab universe's bars that day, so breadth / spy_fo / qqq_fo come from mcf.strategies.lab_context exactly as live),
over open-history sessions of one month (L20_DAYS: a subset). Signals are compared with the research scans (b_trades / trades_A for LD*, the module
mask on the lab frames for M1). Not exact by design: the live frame is rebuilt from 1-minute bars with PRIOR5_BARS of
warm-up, while the lab frames used full history. Locked block never read (common.load_1min filters it at read).
Educational only - not financial advice."""
import json
import os
import sys
import time

import numpy as np
import pandas as pd

from common import HERE, ROOT, SCR, lib, load_1min
from mcf.research import gates

MONTH = os.environ.get("L20_MONTH", "2026-06")


def main():
    os.environ["MCF_ACCOUNT"] = "testing2"
    from mcf.backtest.engine import SymbolHistory
    from mcf.config import load_config
    from mcf.strategies.setups import _LAB_FRAMES, build_strategies

    cfg = load_config()
    names = [n for n, v in cfg["strategies"].items() if v.get("enabled") and n.startswith(("LD", "NM-MF3"))]
    st = [s for s in build_strategies(cfg) if s.name in names]
    assert len(st) == 9, [s.name for s in st]
    m0 = pd.Timestamp(MONTH + "-01")
    lo, hi = (m0 - pd.Timedelta(days=70)).date(), (m0 + pd.offsets.MonthEnd(0)).date()
    syms = (ROOT / "research" / "lab_symbols.txt").read_text().split()
    data = {}
    t0 = time.time()
    for s in syms:
        d = load_1min(s)
        if d is None:
            continue
        d = d[(d.index.date >= lo) & (d.index.date <= hi)]
        if len(d):
            data[s] = d
    print("loaded", len(data), round(time.time() - t0), flush=True)
    hist = {s: SymbolHistory(s, d) for s, d in data.items()}
    days = sorted({d for h in hist.values() for d in h.by_day if d.strftime("%Y-%m") == MONTH})
    if os.environ.get("L20_DAYS"):          # a subset of the month's sessions (the research comparison uses the same subset)
        keep = set(os.environ["L20_DAYS"].split(","))
        days = [d for d in days if str(d) in keep]
    got = {s.name: set() for s in st}
    for d in days:
        peers = {s: h.by_day[d] for s, h in hist.items() if d in h.by_day}
        _LAB_FRAMES.clear()
        for sym, h in hist.items():
            c = h.context(d)
            if c is None:
                continue
            c.peers = peers
            for s in st:
                if not s.eligible(c):
                    continue
                for sig in s.signals(c):
                    end = c.bars.index[sig.bar_index] + pd.Timedelta(minutes=1)
                    got[s.name].add((sym, str(d), end.hour * 100 + end.minute))
        print(d, {k[:4]: len(v) for k, v in got.items()}, flush=True)
    # research signals in the month
    T = pd.read_parquet(SCR / "b_trades.parquet")
    T["date"] = pd.to_datetime(T["date"]).dt.date.astype(str)
    A = pd.read_csv(HERE / "trades_A.csv.gz")
    ref = {}
    bmap = {"LD1": "B5-NS1-BRDUP", "LD3": "B5-ST2-IDXTURN", "LD4": "B5-ST4-BRDUP", "LD5": "B5-ST2-BRDUP", "LD7": "B5-NS1-IDXTURN"}
    amap = {"LD2": ("A-QQQ-abs015-brd-t05s1", "TQQQ"), "LD6": ("A-SPY-rel020-brd-holdtr", "SPXL"),
            "LD8": ("A-SPY-abs030-brd-holdtr", "SPXL")}
    for n in got:
        k = n[:3]
        if k in bmap:
            t = T[(T.base == bmap[k]) & T.date.isin({str(d) for d in days})]
            ref[n] = set(zip(t.symbol, t.date, t.tod.astype(int)))
        elif k in amap:
            t = A[(A.cfg == amap[k][0]) & A.date.astype(str).isin({str(d) for d in days})]
            ref[n] = {(amap[k][1], str(dd), int(tt)) for dd, tt in zip(t.date, t.tod)}
    # M1: its module on the lab frames (the mf3swarm1020 scan reproduced it exactly: 2,099 trades)
    m1 = next(s for s in st if s.name.startswith("NM-MF3"))
    df = lib.load_month(MONTH, columns=["symbol", "date", "tod", "heat", "buyPressure", "rsi5", "gap", "adv20", "r_long_t1s1"],
                        context=True)
    df = df[(df.adv20 >= 95e6) & df.date.astype(str).isin({str(d) for d in days})].reset_index(drop=True)
    mk = m1.mod.mask(df) & (df.tod.to_numpy() >= 950) & (df.tod.to_numpy() <= 1500) & np.isfinite(df.r_long_t1s1.to_numpy())
    i = gates.first_per_symbol_day(df.symbol.to_numpy(), df.date.to_numpy(), mk)
    ref[m1.name] = set(zip(df.symbol.to_numpy()[i], df.date.astype(str).to_numpy()[i], df.tod.to_numpy()[i].astype(int)))
    out = {"_note": __doc__, "month": MONTH, "days": [str(d) for d in days], "peers_symbols": len(data)}
    for n in got:
        a, b = got[n], ref.get(n, set())
        sd = lambda x: {(s, d) for s, d, _ in x}
        out[n] = {"live_signals": len(a), "research_signals": len(b), "same_bar": len(a & b),
                  "same_symbol_day": len(sd(a) & sd(b)), "live_only": sorted(map(str, a - b))[:8],
                  "research_only": sorted(map(str, b - a))[:8]}
        print(n, {k: v for k, v in out[n].items() if not isinstance(v, list)})
    json.dump(out, open(HERE / "verify_live.json", "w"), indent=1)


if __name__ == "__main__":
    main()
