"""GB-GENTRAIL live walk (descriptive): replay every run-1 GEN hold / holdtr trade (10-06..11-19) on 1-minute SIP bars
from the minute after entry to the 15:55 open under C1..C7 (PLAN.md). Live LR8 cost (gross journal R - journal R) is
subtracted from every arm; exits caused by a rule that is not the setup's own geometry also pay half spread + 1c + 1 bp.
Usage: python live_walk.py live_trades.parquet live_bars.parquet OUT.parquet. Educational only - not financial advice."""
import sys

import numpy as np
import pandas as pd

from lab_walk import walk

T = pd.read_parquet(sys.argv[1])
B = pd.read_parquet(sys.argv[2])
OUT = sys.argv[3]
T = T[T.strategy.str.startswith("GEN") & T.strategy.str.contains("-hold")].copy()
T["geom"] = np.where(T.strategy.str.contains("holdtr"), "holdtr", "hold")
et = pd.to_datetime(T.entry_time.astype(str).str[:19])
T["m_in"] = et.dt.hour * 60 + et.dt.minute
need = set(zip(T.date.astype(str), T.symbol))
B["day"] = B["day"].astype(str)
B = B[[k in need for k in zip(B.day, B.symbol)]]
M0, M1, FL = 570, 960, 955
GR = {}
for (day, sym), g in B.groupby(["day", "symbol"]):
    a = np.full((4, M1 - M0), np.nan)
    i = g.m.to_numpy() - M0
    ok = (i >= 0) & (i < M1 - M0)
    for k, col in enumerate("ohlc"):
        a[k, i[ok]] = g[col].to_numpy()[ok]
    GR[(day, sym)] = a
SIMS = {"C1": (0.0, 0.0, 0.0, 0.0, 0.0), "C2": (0.0, 1.0, 1.0, 0.0, 0.0), "C3": (0.0, 0.0, 1.0, 0.5, 0.0),
        "C4": (1.0, 0.0, 0.0, 0.0, 0.0), "C6": (0.0, 0.0, 0.0, 0.0, 2.0), "C7": (0.0, 0.0, 0.0, 0.0, 3.0)}
rows = []
for r in T.itertuples():
    a = GR.get((str(r.date), r.symbol))
    rps = abs(r.entry - r.stop)
    s = int(np.sign(r.side))
    base = [r.id, r.account]
    if a is None or not rps > 0 or r.m_in >= FL - 1 or r.R != r.R:
        rows.append(base + [np.nan] * 9)
        continue
    i0 = r.m_in - M0
    seg = a[:, i0 + 1:FL - M0]
    o955 = a[0, FL - M0]
    if not o955 == o955:
        o955 = pd.Series(a[3, :FL - M0]).ffill().iloc[-1]
    h = pd.Series(seg[1]).ffill().to_numpy()
    l = pd.Series(seg[2]).ffill().to_numpy()
    c = pd.Series(seg[3]).ffill().to_numpy()
    h = np.nan_to_num(np.r_[r.entry, h, o955], nan=r.entry)
    l = np.nan_to_num(np.r_[r.entry, l, o955], nan=r.entry)
    c = np.nan_to_num(np.r_[r.entry, c, o955], nan=r.entry)
    # ATR5: last 6 five-minute buckets ending at the entry minute
    w = a[:, max(0, i0 - 29):i0 + 1]
    trs = []
    for b0 in range(0, w.shape[1], 5):
        bb = w[:, b0:b0 + 5]
        if np.isfinite(bb[1]).any():
            trs.append(np.nanmax(bb[1]) - np.nanmin(bb[2]))
    atr5 = float(np.mean(trs)) if trs else np.nan
    gross_live = s * (r.exit - r.entry) / rps
    cost = gross_live - r.R
    xc = ((r.spread_bps if r.spread_bps == r.spread_bps else 5) / 2e4 * r.entry + 0.01 + 1e-4 * r.entry) / rps
    own = "C1" if r.geom == "hold" else "C2"
    res = {}
    for cfg, (up, trr, tra, gb, chk) in SIMS.items():
        g, rule = walk(h, l, c, 0, len(c) - 1, r.entry, rps, s, up, trr, tra, gb, chk,
                       atr5 if atr5 == atr5 else 0.0, 0.0, 0.0, 0.0)
        res[cfg] = g - cost - (xc * rule if cfg != own else 0.0)
    res["C5"] = 0.5 * res["C4"] + 0.5 * res["C2"]
    rows.append(base + [atr5 / rps] + [res[k] for k in ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]] + [gross_live])
X = pd.DataFrame(rows, columns=["id", "account", "atr5_R", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "gross_live"])
P = T[["id", "account", "strategy", "geom", "side", "date", "symbol", "R", "exit_reason"]].merge(X, on=["id", "account"])
P.to_parquet(OUT, index=False)
ok = P.C1.notna()
P["own"] = np.where(P.geom == "hold", P.C1, P.C2)
print(len(P), ok.sum(), "journal R", P.R[ok].mean().round(4), "replay own", P.own[ok].mean().round(4),
      "corr", np.corrcoef(P.R[ok], P.own[ok])[0, 1].round(3))
print(P[ok].groupby("geom")[["R", "C1", "C2", "C3", "C4", "C5", "C6", "C7"]].mean().round(4))
