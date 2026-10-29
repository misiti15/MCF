"""bar90_1029: re-score RST1 / RST2 in their NATIVE swarm1017 rework-st harness (copied from
research/swarm1017/rework-st/verify_modules.py, which reproduced the scan exactly), and dump per-trade rows
(date, symbol, tod, r, same-minute random control) for the full BAR90 gate check in evaluate.py.

Frames: research/history2y lib.load_month (refuses the locked block unless MCF_HIST_ALLOW_LOCKED=1).
--locked scores ONLY the four locked months (the lead's single look per version) and writes *_locked.parquet.
Costs: mcf.research.gates.prod_r (production: 1c + 1 bp x time-of-day entry, +2c stops, x3 extended tier).
Random control: same-date same-minute mean prod R of the same side x geometry over the same eligible rows.
Educational only - not financial advice.
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from mcf.research.gates import prod_r  # noqa: E402
from research.history2y import lib  # noqa: E402

SRC = ROOT / "research/swarm1017/rework-st/modules"
OUTD = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else HERE
LOCKED = "--locked" in sys.argv
NAMES = [a for a in sys.argv[1:] if a.startswith("RST")]
idx = json.load(open(SRC / "index.json"))
mods = {}
for name in NAMES:
    spec = importlib.util.spec_from_file_location(name, SRC / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    mods[name] = m
months = lib.LOCKED_MONTHS if LOCKED else lib.months()
rows = {n: [] for n in mods}
for mo in months:
    d = lib.load_month(mo)
    spy = d.loc[d.symbol == "SPY", ["date", "tod", "fromOpen"]].rename(columns={"fromOpen": "spy_fo"})
    d = d.merge(spy, on=["date", "tod"], how="left")
    d = d.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    tod = d.tod.to_numpy()
    for n, m in mods.items():
        meta = idx[n]
        g, s = m.GEOM, m.SIDE
        rr = d[f"r_{s}_{g}"].to_numpy(float)
        base = (d.adv20.to_numpy(float) >= meta["min_adv"]) & (d.atr_d.to_numpy(float) > 0) & np.isfinite(rr)
        ok = base & (tod >= meta["window"][0]) & (tod <= meta["window"][1])
        if meta.get("prefilter"):
            ok &= d.gap.to_numpy(float) <= float(meta["prefilter"].split(":")[1])
        hit = np.flatnonzero(np.asarray(m.mask(d), bool) & ok)
        if not len(hit):
            continue
        key = d.symbol.to_numpy()[hit].astype(str) + "|" + d.date.astype(str).to_numpy()[hit]
        _, first = np.unique(key, return_index=True)
        sel = np.sort(hit[first])
        r = prod_r(rr[sel], d[f"win_{s}_{g}"].to_numpy(float)[sel], d.close.to_numpy(float)[sel],
                   d.atr_d.to_numpy(float)[sel], g, tod=tod[sel].astype(float))
        # same-minute random control over all eligible rows of that minute (adv20 >= $95M, as the arena baseline)
        cm = base & (d.adv20.to_numpy(float) >= 95e6)
        allr = prod_r(rr[cm], d[f"win_{s}_{g}"].to_numpy(float)[cm], d.close.to_numpy(float)[cm],
                      d.atr_d.to_numpy(float)[cm], g, tod=tod[cm].astype(float))
        ctl = pd.DataFrame({"date": d.date.to_numpy()[cm], "tod": tod[cm], "c": allr}).groupby(["date", "tod"])["c"].mean()
        k2 = pd.MultiIndex.from_arrays([d.date.to_numpy()[sel], tod[sel]])
        rows[n].append(pd.DataFrame({"date": d.date.to_numpy()[sel], "symbol": d.symbol.to_numpy()[sel], "tod": tod[sel],
                                     "r": r, "ctrl": ctl.reindex(k2).to_numpy()}))
    print(mo, {n: sum(len(x) for x in v) for n, v in rows.items()}, flush=True)
    del d
for n, v in rows.items():
    t = pd.concat(v, ignore_index=True) if v else pd.DataFrame(columns=["date", "symbol", "tod", "r", "ctrl"])
    t.to_parquet(OUTD / f"{n}{'_locked' if LOCKED else ''}.parquet", index=False)
    print(n, len(t), round(float(t.r.mean()), 4) if len(t) else None)
print("Educational only - not financial advice.")
