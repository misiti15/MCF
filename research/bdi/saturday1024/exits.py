"""saturday1024: exit minute for every cached signal of the scored books (the gates1021 cache keeps exit_tod only for
L3). Re-simulates each bracket on the history2y 5-min frames (entry = signal bar close, stop / target = geometry x 0.25
daily ATR, stop first inside a bar, else 15:55), and checks it against the cached outcome (win). Locked months are
never loaded. Usage: python exits.py <out.parquet>   Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "gates1021" / "scripts"))
from common import lib, no_locked  # noqa: E402
from load import load_sig  # noqa: E402
from mcf.research.gates import GEOMK  # noqa: E402

U = pd.read_csv(HERE.parent / "gates1021" / "setups_scored.csv").set_index("setup")
ASG = json.loads((ROOT / "docs/live/assignments.json").read_text())["accounts"]
members = sorted({s for k in ("primary", "testing", "testing2") for s in ASG[k] if s in U.index})
sig = load_sig(members)
sig["month"] = pd.to_datetime(sig["date"]).dt.strftime("%Y-%m")
out = []
for mo, g in sig.groupby("month"):
    assert mo in lib.months(), mo
    f = lib.load_month(mo, columns=["symbol", "date", "tod", "high", "low", "close"])
    no_locked(f["date"].unique())
    fi = {k: v for k, v in f.groupby(["symbol", "date"]).indices.items()}
    H, L, T = f["high"].to_numpy(), f["low"].to_numpy(), f["tod"].to_numpy()
    xt = np.full(len(g), 1555.0); xw = np.full(len(g), np.nan)
    for j, (sy, d, tod, px, atr, st) in enumerate(zip(g.symbol, g.date, g.tod, g.close, g.atr_d, g.setup)):
        ix = fi.get((sy, d))
        if ix is None or not np.isfinite(atr):
            continue
        up, dn = GEOMK[U.loc[st, "geom"]]
        side = 1 if U.loc[st, "side"] == "long" else -1
        R = 0.25 * atr
        stop, tgt = px - side * dn * R, px + side * up * R
        t = T[ix]; k = ix[t > tod]
        if not len(k):
            continue
        if side == 1:
            hs, ht = L[k] <= stop, H[k] >= tgt
        else:
            hs, ht = H[k] >= stop, L[k] <= tgt
        a = np.flatnonzero(hs | ht)
        if len(a):
            xt[j] = T[k[a[0]]]; xw[j] = 0.0 if hs[a[0]] else 1.0
    out.append(pd.DataFrame({"i": g.index, "exit_sim": xt, "win_sim": xw}))
    print(mo, len(g), flush=True)
X = pd.concat(out).set_index("i")
s = sig.join(X)
both = s["win_sim"].notna()
agree = (s.loc[both, "win_sim"] == (s.loc[both, "win"] == 1)).mean()
print(f"signals {len(s)}, bracket hit {both.mean():.3f}, win agreement where hit {agree:.3f}")
print("exit_sim == 1555 share", round(float((s.exit_sim >= 1555).mean()), 3))
s[["setup", "symbol", "date", "tod", "exit_sim", "win_sim"]].to_parquet(sys.argv[1])
print("Educational only - not financial advice.")
