"""ex30/levels report: TRAIN / VALID avg R, day-clustered t, trades/session, random-control excess, avg R w/o best day and
its share, R by SPY up / down / quiet day (eod3 at +-0.25% open-to-close, SIP 1-minute SPY cache), light-gate verdict.

    python report.py <scratch>   -> results.csv here
Educational only - not financial advice.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT)]
from mcf.research import gates as G  # noqa: E402

S = Path(sys.argv[1])
T = pd.read_parquet(S / "trades.parquet")
C = pd.read_parquet(S / "ctrl.parquet")
par = pd.read_csv(HERE / "parity.csv", index_col=0)

b = pd.read_parquet(ROOT / "data" / "cache_hist" / "1Min" / "SPY.parquet")
b.index = pd.to_datetime(b.index).tz_convert("America/New_York")
b = b[(b.index.time >= pd.Timestamp("09:30").time()) & (b.index.time < pd.Timestamp("16:00").time())]
g = b.groupby(b.index.date)
o2c = (g.close.last() / g.open.first() - 1) * 100
eod3 = pd.Series(np.where(o2c >= 0.25, "up", np.where(o2c <= -0.25, "down", "quiet")), index=o2c.index)
s = pd.Series(eod3.index.astype(str), index=eod3.index)
eod3 = eod3[~((s >= "2024-11-01") & (s <= "2025-02-28"))]   # locked block dates never used
T["eod3"] = T["date"].map(eod3)

sessions = {sp: C[C.split == sp].date.nunique() for sp in ("TRAIN", "VALID")}
rows = []
for (setup, form), x in T.groupby(["setup", "form"], sort=False):
    r = {"setup": setup, "form": form, "side": x.side.iloc[0]}
    for sp in ("TRAIN", "VALID"):
        y = x[x.split == sp]
        sm = G.summary(y) if len(y) else {"n": 0}
        r[f"{sp}_n"] = sm.get("n", 0)
        r[f"{sp}_avgR"] = sm.get("exp_r")
        r[f"{sp}_t"] = sm.get("t")
        r[f"{sp}_tps"] = round(len(y) / sessions[sp], 2)
        r[f"{sp}_exbest"] = sm.get("ex_best_day")
        if len(y):
            ds = y.groupby("date").r.sum()
            r[f"{sp}_bestday_share"] = round(float(ds.max() / ds.sum()), 2) if ds.sum() > 0 else None
        for dt in ("up", "down", "quiet"):
            z = y[y.eod3 == dt]
            r[f"{sp}_{dt}_n"] = len(z)
            r[f"{sp}_{dt}_R"] = round(float(z.r.mean()), 4) if len(z) else None
    r["_x"] = x
    rows.append(r)
R = pd.DataFrame(rows)

# random-control excess per config
import score  # noqa: E402

key = {}
for name, (side, geom, w, *_r) in score.SETUPS.items():
    key[name] = (side, geom, str(w))
for i, r in R.iterrows():
    x = r["_x"]
    side, geom, w = key[r.setup]
    cc = C[(C.side == side) & (C.geom == geom) & (C.win == w)][["date", "split", "ctrl"]]
    y = x.merge(cc, on=["date", "split"], how="left")
    y["ex"] = y.r - y.ctrl
    for sp in ("TRAIN", "VALID"):
        z = y[y.split == sp].dropna(subset=["ex"])
        if len(z):
            sm = G.summary(z.assign(r=z.ex))
            R.loc[i, f"{sp}_vs_random"] = sm.get("exp_r")
            R.loc[i, f"{sp}_vs_random_t"] = sm.get("t")
    a = x.r.mean()
    R.loc[i, "ALL_n"] = len(x)
    R.loc[i, "ALL_avgR"] = round(float(a), 4)
    R.loc[i, "ALL_tps"] = round(len(x) / (sessions["TRAIN"] + sessions["VALID"]), 2)
    for dt in ("up", "down", "quiet"):
        z = x[x.eod3 == dt]
        R.loc[i, f"ALL_{dt}_R"] = round(float(z.r.mean()), 4) if len(z) else None
    if r.form == "primary":
        p = par.loc[r.setup]
        R.loc[i, "parity"] = bool(p.harness == p.module == p.both)
R = R.drop(columns="_x")
R["gate_pass"] = (R.TRAIN_avgR >= -0.02) & (R.VALID_avgR >= -0.02) & R.ALL_tps.between(1.5, 25) & \
    np.where(R.form == "primary", R.get("parity", False).fillna(False).astype(bool), True)
R.to_csv(HERE / "results.csv", index=False)
print("sessions", sessions, "configs", len(R))
pd.set_option("display.width", 250)
show = ["setup", "form", "TRAIN_n", "TRAIN_avgR", "TRAIN_t", "VALID_n", "VALID_avgR", "VALID_t", "ALL_tps", "TRAIN_vs_random",
        "VALID_vs_random", "ALL_up_R", "ALL_down_R", "ALL_quiet_R", "VALID_exbest", "VALID_bestday_share", "gate_pass"]
print(R[show].to_string())
