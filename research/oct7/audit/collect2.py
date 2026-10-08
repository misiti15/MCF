"""AUDIT pass 2 (train/valid only, bars end 2026-09-16): (a) BD-gapdn-reclaim family by a direct re-implementation
of LabStrategy for this gap/fromOpen-only mask (verified trade-for-trade against pass 1), giving cheap plateau
neighbours and baselines (rule 6); (b) BD-hfl-nearPDL neighbours pdl<0 and pdl<0.5 through LabStrategy.
Educational only - not financial advice."""
import pickle
import sys
import time
from dataclasses import asdict
from multiprocessing import Pool

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from mcf.backtest.engine import SymbolHistory, is_extended, simulate, universe_ok, Backtester  # noqa: E402
from mcf.config import load_config  # noqa: E402
from mcf.data.bars import resample  # noqa: E402
from mcf.data.store import BarStore  # noqa: E402
from mcf.strategies.base import Signal, t  # noqa: E402
from mcf.strategies.setups import build_strategies  # noqa: E402

FIRST, LAST_EXCL = "2026-07-15", "2026-09-16"
cfg = load_config()
S = {"hfl_pdl_00": dict(type="lab", module="research/oct7/audit/mods/hfl_pdl_00.py", min_adv=125e6, window=[1105, 1330], scale_out_r=None),
     "hfl_pdl_05": dict(type="lab", module="research/oct7/audit/mods/hfl_pdl_05.py", min_adv=125e6, window=[1105, 1330], scale_out_r=None)}
# gapdn family: (gap threshold, window, condition)
G = {}
for g in (0.5, 0.88, 1.66):
    for w in ((1300, 1430), (1230, 1430), (1330, 1430), (1300, 1500), (1300, 1400)):
        if g != 0.88 and w != (1300, 1430):
            continue
        G[f"gd_g{g}_w{w[0]}-{w[1]}"] = (g, w, "fo>0")
G["ctrl_gd_g0.88_first_bar"] = (0.88, (1300, 1430), "any")      # same names, same window, no reclaim condition
G["ctrl_all_first_bar"] = (None, (1300, 1430), "any")            # every name, short at the first window bar
G["ctrl_fo>0_nogap"] = (None, (1300, 1430), "fo>0")              # reclaim condition without the gap-down layer
STRATS = BT = None


def init():
    global STRATS, BT
    STRATS = build_strategies({**cfg, "strategies": S})
    BT = Backtester([], cfg)


def work(sym):
    try:
        df = BarStore(cfg["data"]["cache_dir"]).load(sym, start="2026-05-20", end=LAST_EXCL)
    except Exception as e:  # noqa: BLE001
        return sym, [], str(e)
    if df is None or df.empty:
        return sym, [], None
    assert str(df.index.max().date()) < LAST_EXCL
    h = SymbolHistory(sym, df)
    out = []
    for d in sorted(h.by_day):
        if not (FIRST <= str(d) < LAST_EXCL):
            continue
        c = h.context(d)
        if c is None or not universe_ok(c, cfg) or not (c.avg_dollar_volume >= 95e6):
            continue
        ext = bool(is_extended(c, cfg))
        costs = BT.costs_ext if ext else BT.costs
        g = c.gap_pct
        bars = c.bars
        d5 = resample(bars, "5min")
        d5 = d5[d5.index + pd.Timedelta(minutes=5) <= bars.index[-1] + pd.Timedelta(minutes=1)]
        end = d5.index + pd.Timedelta(minutes=5)
        tod = end.hour * 100 + end.minute
        o = float(d5["open"].iloc[0])
        fo = (d5["close"].to_numpy() / o - 1) * 100
        for name, (gt, w, cond) in G.items():
            if gt is not None and not g <= -gt:
                continue
            m = (tod >= max(950, w[0])) & (tod <= min(1500, w[1]))
            if cond == "fo>0":
                m &= fo > 0
            hit = np.flatnonzero(m)
            if not len(hit):
                continue
            i = hit[0]
            j = min(bars.index.searchsorted(d5.index[i] + pd.Timedelta(minutes=4)), len(bars) - 1)
            px, r = float(d5["close"].iloc[i]), 0.25 * c.atr
            sig = Signal(sym, name, -1, int(j), stop=px + r, target=px - r, exit_by=t("15:55"))
            tr = simulate(sig, bars, BT.flatten, costs)
            if tr is not None:
                out.append({"setup": name, "date": str(d), "symbol": sym, "ext": ext, "atr": c.atr, "adv": c.avg_dollar_volume,
                            "gap": g, "fo_sig": fo[i], "sig_px": px, "sig_stop": sig.stop, "trade": asdict(tr)})
        if g > 0 and c.avg_dollar_volume >= 125e6:
            for s in STRATS:
                if not s.eligible(c):
                    continue
                for sig in s.signals(c):
                    tr = simulate(sig, bars, BT.flatten, costs)
                    if tr is not None:
                        px = float(bars["close"].iloc[sig.bar_index])
                        out.append({"setup": s.name, "date": str(d), "symbol": sym, "ext": ext, "atr": c.atr,
                                    "adv": c.avg_dollar_volume, "gap": g, "fo_sig": (px / float(bars["open"].iloc[0]) - 1) * 100,
                                    "sig_px": px, "sig_stop": sig.stop, "trade": asdict(tr)})
    return sym, out, None


if __name__ == "__main__":
    t0 = time.time()
    syms = BarStore(cfg["data"]["cache_dir"]).symbols()
    res, errs = [], []
    with Pool(3, initializer=init) as p:
        for n, (sym, out, err) in enumerate(p.imap_unordered(work, syms, chunksize=4)):
            res.extend(out)
            if err:
                errs.append((sym, err))
            if n % 200 == 0:
                print(n, len(syms), len(res), round(time.time() - t0), flush=True)
    pickle.dump({"cands": res, "errors": errs, "G": G, "S": S}, open("research/oct7/audit/data/cands2.pkl", "wb"))
    print("done", len(res), "errors", len(errs), round(time.time() - t0), flush=True)
