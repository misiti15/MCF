"""Task 1 (NOTES 1.4): hedged scoring of every existing setup - 33 full-day lists, 30 current-window lists, 40 Reddit
base rules - net of SPY and of the sector ETF, betas from prior sessions only, both legs' costs.
Writes data/existing_trades.parquet (per trade, git-ignored) and existing_results.csv. Educational only - not financial advice."""
import importlib.util
import json
import math

import numpy as np
import pandas as pd

from common import DATA, HERE, ROOT, SECTOR, bars, lib
from hedge import GEOMK, bar_check, hedge_r, score, sim_exit
from mcf.research import gates

FD = ROOT / "research" / "bdi" / "fullday"
B = bars()
syms, dates = B["syms"], B["dates"]
si = {s: i for i, s in enumerate(syms)}
di = {d: i for i, d in enumerate(dates)}
BT = np.load(DATA / "betas.npz")
reg = lib.regimes()


def modinfo(path):
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------- trade lists
geom = {}
for f in FD.glob("*-FD.py"):
    nm = f.name[:-6]
    if nm.startswith("heat_fade"):
        geom[nm] = "t1s1"
    else:
        geom[nm] = modinfo(f).GEOM
geom["RW8-sma50up-spikefade-short"] = "t1s1"
tod_tr = pd.read_parquet(ROOT / "research" / "bdi" / "timeofday" / "data" / "trades.parquet")
tod_tr = tod_tr[tod_tr["set"].isin(["full", "current"])].copy()
tod_tr["geom"] = tod_tr["setup"].map(geom)
assert tod_tr["geom"].notna().all(), set(tod_tr.loc[tod_tr.geom.isna(), "setup"])
tod_tr["list"] = np.where(tod_tr["set"] == "full", tod_tr["setup"] + "-FD", tod_tr["setup"] + "-cur")
tod_tr.loc[(tod_tr["setup"] == "RW8-sma50up-spikefade-short") & (tod_tr["set"] == "full"), "list"] = "RW8-sma50up-spikefade-short-FD"

# L3 FD lists + the atr_d table (first row per symbol-day) from the frames, month by month
l3 = {f.name[:-6]: modinfo(f) for f in FD.glob("L3-*-FD.py")}
cols = ["symbol", "date", "tod", "close", "atr_d", "gap", "sma20_slope_pct", "fromOpen", "dist_lod_atr", "rsi5",
        "r_short_t1s1", "win_short_t1s1", "r_short_t05s1", "win_short_t05s1"]
atr_parts, l3_parts = [], []
for mo in lib.months():
    df = lib.load_month(mo, cols)
    first = np.r_[True, (df["symbol"].to_numpy()[1:] != df["symbol"].to_numpy()[:-1]) | (df["date"].to_numpy()[1:] != df["date"].to_numpy()[:-1])]
    atr_parts.append(df.loc[first, ["symbol", "date", "atr_d", "close"]])
    for nm, m in l3.items():
        t = gates.lab_trades(df, m.mask(df) & (df["tod"].to_numpy() >= 950) & (df["tod"].to_numpy() <= 1500), m.SIDE, m.GEOM)
        t["setup"], t["side"], t["geom"], t["list"], t["set"] = nm, m.SIDE, m.GEOM, nm + "-FD", "full"
        l3_parts.append(t)
    print("frames", mo, flush=True)
ATR = pd.concat(atr_parts, ignore_index=True)
ATR.to_parquet(DATA / "atr.parquet")
L3 = pd.concat(l3_parts, ignore_index=True)
ATRA = np.full((len(dates), len(syms)), np.nan, np.float32)
_a = ATR[ATR["symbol"].isin(si) & ATR["date"].isin(di)]
ATRA[_a["date"].map(di).to_numpy(), _a["symbol"].map(si).to_numpy()] = _a["atr_d"].to_numpy(np.float32)
KEEP = ["tod", "r", "setup", "side", "geom", "list", "set"]


def lean(x):
    x = x.copy()
    x["date"] = pd.to_datetime(x["date"]).dt.date
    x["s"] = x["symbol"].map(si).fillna(-1).astype(np.int32)
    x["d"] = x["date"].map(di).fillna(-1).astype(np.int32)
    x = x[(x["s"] >= 0) & (x["d"] >= 0)]
    out = x[["s", "d"] + KEEP].copy()
    out["tod"] = out["tod"].astype(np.int32)
    out["r"] = out["r"].astype(np.float32)
    for c in ("setup", "side", "geom", "list", "set"):
        out[c] = out[c].astype(str).astype("category")
    return out


parts = [lean(tod_tr), lean(L3)]
del tod_tr, L3
rd = pd.read_parquet(DATA / "reddit_trades.parquet")
rd["geom"], rd["list"], rd["set"] = "t1s1", rd["setup"].astype(str), "reddit"
parts.append(lean(rd))
del rd
T = pd.concat(parts, ignore_index=True)
del parts
for c in ("setup", "side", "geom", "list", "set"):
    T[c] = T[c].astype(str).astype("category")
print("trades", len(T), T["list"].nunique(), flush=True)
assert T["list"].nunique() == 103, T["list"].nunique()

# ---------------------------------------------------------------- exits, hedges
s = T["s"].to_numpy(np.int64)
d = T["d"].to_numpy(np.int64)
b = (((T["tod"].to_numpy() // 100) * 60 + T["tod"].to_numpy() % 100 - 575) // 5).astype(np.int64)
T["atr_d"] = ATRA[d, s]
side = np.where(T["side"].to_numpy() == "long", 1.0, -1.0)
upk = T["geom"].map(lambda g: GEOMK[g][0]).to_numpy(float)
dnk = T["geom"].map(lambda g: GEOMK[g][1]).to_numpy(float)
R = 0.25 * T["atr_d"].to_numpy(float)
ent, ex, lab, win = sim_exit(B["C"], B["H"], B["L"], s, d, b, side, upk, dnk, R)
T["r_sim"] = np.nan
for g in GEOMK:
    m = (T["geom"] == g).to_numpy() & np.isfinite(lab)
    T.loc[m, "r_sim"] = gates.prod_r(lab[m], win[m], ent[m], T["atr_d"].to_numpy()[m], g)
T["ent"], T["ex"] = ent, ex
dev = (T["r_sim"] - T["r"]).abs()
par = {"trades": int(len(T)), "match_1e-3": float((dev < 1e-3).mean()), "match_0.02": float((dev < 0.02).mean()),
       "nan_sim": float(T["r_sim"].isna().mean())}
par["by_set"] = {k: float((dev[T["set"] == k] < 0.02).mean()) for k in T["set"].unique()}
print("parity", par, flush=True)

spy = si["SPY"]
beta_spy = BT["beta_spy"][d, s].astype(float)
sec = BT["sec"][d, s].astype(int)
secsym = np.array([si[e] for e in SECTOR] + [spy])           # index -1 -> SPY
h_sec = np.where(sec >= 0, secsym[np.maximum(sec, 0)], np.where(sec == -1, spy, -1))
beta_sec = BT["beta_sec"][d, s].astype(float)
T["beta_spy"], T["beta_sec"], T["hsec"] = beta_spy, beta_sec, sec
T["h_spy"] = hedge_r(B["C"], side, ent, R, beta_spy, np.full(len(T), spy), d, b, ex)
T["h_sec"] = hedge_r(B["C"], side, ent, R, beta_sec, h_sec, d, b, ex)
# market move (SPY) over each trade, in stock-R per unit beta, for the diagnostic
T["r_spy"] = T["r"] + T["h_spy"]
T["r_sec"] = T["r"] + T["h_sec"]
T["date"] = np.array(dates, dtype=object)[d]
T.drop(columns=["date"]).to_parquet(DATA / "existing_trades.parquet")

(DATA / "parity.json").write_text(json.dumps(par, indent=1))
print("trades written; scoring: python score_existing_results.py")
