"""AUDIT 2026-10-08: reproduce the oct7 finalists with the PRODUCTION code path (HeatStrategy / LabStrategy
.signals -> engine.simulate with config costs, extended-tier slippage, next-bar fills, stop-first), on
sessions 2026-07-15..2026-09-15 only. Bars are loaded with end='2026-09-16' (locked dates never read).
Per-symbol loop: heat/lab signals depend only on the symbol's own history (rank/in-play only affect orb and
the extended tier, which ADV >= 95M names never are), so this equals Backtester.run's candidate set.
Speed-only pre-checks equal to the live prefilters: gap <= -0.88 for gapdn modules, gap > 0 for the hfl modules
(regime_5's own gap+ gate makes the mask false otherwise). Output data/cands.pkl. Educational only - not financial advice."""
import pickle
import sys
import time
from dataclasses import asdict
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, ".")
from mcf.backtest.engine import SymbolHistory, is_extended, simulate, universe_ok, Backtester  # noqa: E402
from mcf.config import load_config  # noqa: E402
from mcf.data.store import BarStore  # noqa: E402
from mcf.strategies.setups import build_strategies  # noqa: E402

FIRST, LAST_EXCL = "2026-07-15", "2026-09-16"
cfg = load_config()
S = {
    "hfl_base": dict(type="heat", formula="research/heat/candidates/regime_5.py", sides="long", min_adv=125e6,
                     window=[1105, 1330], gate="gap+", scale_out_r=None),
    "hfl_deep4": dict(type="heat", formula="research/oct7/autopsy/candidates/regime_5_deep4.py", sides="long",
                      min_adv=125e6, window=[1105, 1330], gate="gap+", scale_out_r=None),
    "hfl_pdl": dict(type="lab", module="research/oct7/innovation/BD-hfl-nearPDL.py", min_adv=125e6,
                    window=[1105, 1330], scale_out_r=None),
    "hfl_pdl_95m": dict(type="lab", module="research/oct7/innovation/BD-hfl-nearPDL.py", min_adv=95e6,
                        window=[1105, 1330], scale_out_r=None),
    "gapdn": dict(type="lab", module="research/oct7/innovation/BD-gapdn-reclaim.py", min_adv=95e6,
                  window=[1300, 1430], prefilter="gap_le:-0.88", scale_out_r=None),
    "gapdn_rsi3": dict(type="lab", module="research/oct7/innovation/BD-gapdn-reclaim-rsi3.py", min_adv=95e6,
                       window=[1300, 1430], prefilter="gap_le:-0.88", scale_out_r=None),
}
CFG = {**cfg, "strategies": S}
STRATS = None
BT = None


def init():
    global STRATS, BT
    STRATS = build_strategies(CFG)
    BT = Backtester([], cfg)


def work(sym):
    store = BarStore(cfg["data"]["cache_dir"])
    try:
        df = store.load(sym, start="2026-05-20", end=LAST_EXCL)
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
        g = c.gap_pct
        ext = bool(is_extended(c, cfg))
        for s in STRATS:
            if s.name.startswith("gapdn") and not g <= -0.88:
                continue
            if s.name.startswith("hfl") and not g > 0:
                continue
            if not s.eligible(c):
                continue
            for sig in s.signals(c):
                tr = simulate(sig, c.bars, BT.flatten, BT.costs_ext if ext else BT.costs)
                if tr is None:
                    continue
                b = c.bars
                i = sig.bar_index
                o = float(b["open"].iloc[0])
                px = float(b["close"].iloc[i])
                out.append({"setup": s.name, "date": str(d), "symbol": sym, "ext": ext, "atr": c.atr,
                            "adv": c.avg_dollar_volume, "gap": g, "fo_sig": (px / o - 1) * 100,
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
            if n % 100 == 0:
                print(n, len(syms), len(res), round(time.time() - t0), flush=True)
    pickle.dump({"cands": res, "errors": errs, "strategies": S}, open("research/oct7/audit/data/cands.pkl", "wb"))
    print("done", len(res), "errors", len(errs), round(time.time() - t0), flush=True)
