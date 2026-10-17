"""Re-score each module in modules/ on the raw open frames with the module's own mask (prev-bar logic included), the
YAML min_adv, LabStrategy refire semantics and production cost; compare with the scan. Educational only - not
financial advice."""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from mcf.research.gates import prod_r, summary  # noqa: E402
from mcf.strategies.setups import refire_select  # noqa: E402
from research.history2y import lib  # noqa: E402

SPEC = {"RWR1-exh150-gapdn-spyup-pm-short-t05s1": (150e6, None),
        "RWR2-exh-monday-slopedn-long-t1s1": (95e6, None),
        "RWR3-ns3-adv150-qqqup-early-short-refire": (150e6, 1),
        "RWR4-ns2-up3-qqqup-slopedn-am-short-t05s1": (95e6, None)}
MODS = {}
for n in SPEC:
    sp = importlib.util.spec_from_file_location(n, HERE / "modules" / f"{n}.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    MODS[n] = m
COLS = ["symbol", "date", "tod", "rsi", "rsi5", "sma20_dist_pct", "bear_div", "gap", "fromOpen", "vwapDistPct",
        "sma50_dist_pct", "sma20_slope_pct", "close", "atr_d", "adv20"]
GE = sorted({(m.SIDE, m.GEOM) for m in MODS.values()})
OUTC = sorted({f"{k}_{s}_{g}" for s, g in GE for k in ("r", "win")})
res = {n: [] for n in SPEC}
for mo in lib.months():
    d = lib.load_month(mo, COLS + OUTC)
    for sym in ("SPY", "QQQ"):
        x = d.loc[d.symbol == sym, ["date", "tod", "fromOpen"]].rename(columns={"fromOpen": f"{sym.lower()}_fo"})
        d = d.merge(x, on=["date", "tod"], how="left")
    d = d.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    for n, m in MODS.items():
        a, rf = SPEC[n]
        mk = np.asarray(m.mask(d), bool) & (d.adv20.to_numpy() >= a) & (d.atr_d.to_numpy() > 0)
        mk &= (d.tod.to_numpy() >= 950) & (d.tod.to_numpy() <= 1500)
        r = d[f"r_{m.SIDE}_{m.GEOM}"].to_numpy(float)
        mk &= np.isfinite(r)
        idx = np.flatnonzero(mk)
        if not len(idx):
            continue
        key = d.symbol.to_numpy()[idx].astype(str) + "|" + d.date.astype(str).to_numpy()[idx]
        tod = d.tod.to_numpy()[idx]
        bi = ((tod // 100) * 60 + tod % 100 - 570) // 5
        keep = []
        for k in pd.unique(key):
            j = np.flatnonzero(key == k)
            if rf is None:
                keep.append(idx[j[0]])
            else:
                sel = refire_select(bi[j], rf)
                keep += [idx[j[list(bi[j]).index(b)]] for b in sel]
        keep = np.sort(np.asarray(keep))
        pr = prod_r(r[keep], d[f"win_{m.SIDE}_{m.GEOM}"].to_numpy(float)[keep], d.close.to_numpy(float)[keep],
                    d.atr_d.to_numpy(float)[keep], m.GEOM, tod=d.tod.to_numpy(float)[keep])
        res[n].append(pd.DataFrame({"date": d.date.to_numpy()[keep], "r": pr}))
    print(mo, flush=True)
out = {}
for n, L in res.items():
    t = pd.concat(L, ignore_index=True)
    tr = pd.to_datetime(t.date) < "2026-01-01"
    out[n] = {"all": summary(t), "train": summary(t[tr]), "valid": summary(t[~tr])}
    print(n, out[n]["all"]["n"], out[n]["all"]["exp_r"], out[n]["all"]["t"], "| tr", out[n]["train"]["n"],
          out[n]["train"]["exp_r"], "| va", out[n]["valid"]["n"], out[n]["valid"]["exp_r"])
json.dump(out, open(HERE / "verify.json", "w"), indent=1, default=str)
