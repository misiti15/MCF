"""longs1013 scoring: Q1 (opposite side of MF1-MF5) and Q2 (open flush -> swing-up long), as PLAN.md sections 1-3.

Open history only (data/frames.parquet, data/day.parquet from prep.py; the locked block is never loaded).
Writes data/trades_<cfg>.parquet for finalists, results.csv (every configuration), summary.json.
Educational only - not financial advice.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research" / "history2y"))
sys.path.insert(0, str(ROOT))
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402

DATA = HERE / "data"
GEO = ("t1s1", "t05s1", "t1s05")
EXITS = GEO + ("HTC",)
SPLIT = pd.Timestamp("2025-12-31")
N_STUDY = 580
N_Q1, N_Q2 = 96 + 9132, 484 + 30970
MF = {"MF1": ("MF-945-flowsell-vwapup", 950, 1030), "MF2": ("MF-open-rsimidhi-flowsell", 950, 1100),
      "MF3": ("MF-open-flowsell-rsi5hi", 950, 1100), "MF4": ("MF-h40-open-flowsell", 950, 1100),
      "MF5": ("MF-flowsell-vwapup-rsi5hi", 950, 1500)}


def load_module(name):
    p = ROOT / "research" / "primitives" / "marcoflow" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------------------------------------ data
F = pd.read_parquet(DATA / "frames.parquet")
F = F.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
DAY = pd.read_parquet(DATA / "day.parquet")
print("frames", len(F), flush=True)
key = F["symbol"].to_numpy().astype(object) + "|" + F["date"].dt.strftime("%Y%m%d").to_numpy().astype(object)
F["key"] = pd.factorize(key)[0]
REG = lib.regimes()
REG.index = pd.to_datetime(REG.index)
spy = F[F.symbol == "SPY"].set_index(["date", "tod"])["fromOpen"]
ELIG = (F["adv20"].to_numpy() >= 95e6) & (F["atr_d"].to_numpy() > 0)

c = F["close"].to_numpy(float)
atr = F["atr_d"].to_numpy(float)
R = 0.25 * atr
tod = F["tod"].to_numpy(int)
gap = F["gap"].to_numpy(float)
ext = (np.abs(gap) >= 20) | (c < 5)
c1555 = F[["symbol", "date"]].merge(DAY[["symbol", "date", "c1555"]], on=["symbol", "date"], how="left")["c1555"].to_numpy(float)
mult = gates.tod_cost_mult(tod)
SP, BP, SX = gates.SLIP_PS, gates.SLIP_BPS, gates.STOP_EXTRA


def r_and_gross(side: str, ex: str, idx: np.ndarray, entry_idx_tod=None):
    """Production R (x3 cost on the extended tier) and gross R for rows idx."""
    px, rr, mm, ee = c[idx], R[idx], mult[idx], ext[idx]
    if ex == "HTC":
        s = 1 if side == "long" else -1
        gross = s * (c1555[idx] - px) / rr
        cost = ((SP + px * BP) * mm + (SP + c1555[idx] * BP)) / rr
    else:
        lab = F[f"r_{side}_{ex}"].to_numpy(float)[idx]
        win = F[f"win_{side}_{ex}"].to_numpy(float)[idx]
        gross = lab + 2 * SP / rr
        prod = gates.prod_r(lab, win, px, atr[idx], ex, tod=tod[idx])
        cost = gross - prod
    r = gross - np.where(ee, 3.0, 1.0) * cost
    return r, gross


# same-time control: mean production R of every eligible row at the same (date, tod), per side x exit
CTRL = {}
eidx = np.flatnonzero(ELIG & np.isfinite(c1555))
for side in ("long", "short"):
    for ex in EXITS:
        r, _ = r_and_gross(side, ex, eidx)
        s = pd.DataFrame({"date": F["date"].to_numpy()[eidx], "tod": tod[eidx], "r": r}).dropna()
        CTRL[(side, ex)] = s.groupby(["date", "tod"])["r"].mean()
print("controls done", flush=True)


def first_per_key(mask):
    idx = np.flatnonzero(mask)
    if not len(idx):
        return idx
    k = F["key"].to_numpy()[idx]
    _, first = np.unique(k, return_index=True)
    return np.sort(idx[first])


def trades(idx, side, ex):
    ok = np.isfinite(c1555[idx]) if ex == "HTC" else np.isfinite(F[f"r_{side}_{ex}"].to_numpy(float)[idx])
    idx = idx[ok]
    r, g = r_and_gross(side, ex, idx)
    t = pd.DataFrame({"date": F["date"].to_numpy()[idx], "symbol": F["symbol"].to_numpy()[idx], "tod": tod[idx],
                      "r": r, "gross": g})
    ct = CTRL[(side, ex)]
    t["ctrl"] = ct.reindex(pd.MultiIndex.from_arrays([t["date"], t["tod"]])).to_numpy()
    return t.dropna(subset=["r"])


def stats(t: pd.DataFrame, n_lineage: int) -> dict:
    out = {}
    if not len(t):
        return {"n": 0}
    tr, va = t[t.date <= SPLIT], t[t.date > SPLIT]
    for nm, x in (("train", tr), ("valid", va), ("open", t)):
        s = gates.summary(x.assign(date=x.date.dt.date)) if len(x) else {"n": 0}
        out[f"{nm}_n"], out[f"{nm}_exp"], out[f"{nm}_t"] = s.get("n", 0), s.get("exp_r"), s.get("t")
    s = gates.summary(t.assign(date=t.date.dt.date))
    out["ex_best"] = s.get("ex_best_day")
    out["gross"] = round(float(t.gross.mean()), 4)
    gs = gates.summary(t.assign(date=t.date.dt.date, r=t.gross))
    out["gross_t"] = gs.get("t")
    for nm, x in (("train", tr), ("valid", va)):
        out[f"{nm}_gross"] = round(float(x.gross.mean()), 4) if len(x) else None
        out[f"{nm}_gross_t"] = gates.summary(x.assign(date=x.date.dt.date, r=x.gross)).get("t") if len(x) > 1 else None
    reg = t.date.map(REG["regime"])
    for k in ("up", "flat", "down"):
        x = t[reg.to_numpy() == k]
        out[f"{k}_n"], out[f"{k}_exp"] = len(x), round(float(x.r.mean()), 4) if len(x) else None
        out[f"{k}_gross"] = round(float(x.gross.mean()), 4) if len(x) else None
    rs = gates.regime_split(t.assign(date=t.date), REG)
    wf = gates.walk_forward(t, exclude_months=lib.LOCKED_MONTHS)
    out["wf"] = wf.get("share_positive")
    out["busiest"] = round(float(t.groupby("date").size().max() / len(t)), 3)
    out["excess"] = round(float((t.r - t.ctrl).mean()), 4)
    ex_t = gates.summary(t.assign(date=t.date.dt.date, r=t.r - t.ctrl))
    out["excess_t"] = ex_t.get("t")
    out["per_day"] = round(len(t) / t.date.nunique(), 2)
    v, fails = gates.verdict({"n": len(t), "exp_r": out["open_exp"], "t": out["open_t"]}, rs, wf, n_lineage)
    out["verdict"], out["fails"] = v, "; ".join(fails)
    return out


rows, TR = [], {}

# ------------------------------------------------------------------------------------------------ Q1
mf_masks = {}
for k, (mod, lo, hi) in MF.items():
    m = load_module(mod).mask(F)
    mf_masks[k] = np.asarray(m, bool) & (tod >= lo) & (tod <= hi) & ELIG
mf_masks["FAM"] = np.logical_or.reduce([mf_masks[k] for k in MF])
keyarr = F["key"].to_numpy()
for k, m in mf_masks.items():
    base = first_per_key(m)
    for ex in EXITS:
        t = trades(base, "short", ex)
        cfg = f"Q1-{k}-short-d0-{ex}"
            rows.append({"cfg": cfg, "q": "Q1", "set": k, "side": "short", "d": 0, "exit": ex, **stats(t, N_Q1)})
    for d in (0, 1, 3):
        j = base + d
        j = j[(j < len(F))]
        src = j - d
        ok = (keyarr[j] == keyarr[src]) & (tod[j] <= 1500)
        j = j[ok]
        for ex in EXITS:
            t = trades(j, "long", ex)
            cfg = f"Q1-{k}-long-d{d}-{ex}"
                    rows.append({"cfg": cfg, "q": "Q1", "set": k, "side": "long", "d": d, "exit": ex, **stats(t, N_Q1)})
    print("Q1", k, flush=True)

# ------------------------------------------------------------------------------------------------ Q2
win = (tod >= 950) & (tod <= 1030) & ELIG
W = F.loc[win, ["symbol", "date", "tod", "close", "high", "low", "fromOpen", "gap", "vwapDistPct", "atr_d", "key"]].copy()
W["fidx"] = np.flatnonzero(win)
W = W.merge(DAY[["symbol", "date", "h935", "h940", "h945", "h950", "l935", "l940", "l945", "l950", "c945", "vwap945",
                 "pcl"]], on=["symbol", "date"], how="left")
W = W.sort_values(["key", "tod"]).reset_index(drop=True)
W["open"] = W.close / (1 + W.fromOpen / 100)
W["pc"] = W.open / (1 + W.gap / 100)
W["vwap"] = W.close / (1 + W.vwapDistPct / 100)
W["fl10"] = W[["l935", "l940"]].min(axis=1, skipna=False)
W["fl20"] = W[["l935", "l940", "l945", "l950"]].min(axis=1, skipna=False)
g = W.groupby("key", sort=False)
first = W.tod == 950
W["pclose"] = np.where(first, W.c945, g["close"].shift(1))
W["pvwap"] = np.where(first, W.vwap945, g["vwap"].shift(1))
W["phigh"] = np.where(first, W.h945, g["high"].shift(1))
prevt = np.where(W.tod % 100 == 0, W.tod - 45, W.tod - 5)
W.loc[~first & (g["tod"].shift(1) != prevt), ["pclose", "pvwap", "phigh"]] = np.nan
# LOD path: head bars then frame bars
headlow = W[["l935", "l940", "l945"]].min(axis=1, skipna=False)
W["lowc"] = g["low"].cummin()
W["lod"] = np.fmin(headlow, W["lowc"])
lod945 = headlow
lod940 = W[["l935", "l940"]].min(axis=1, skipna=False)
W["lod_2ago"] = g["lod"].shift(2)
W.loc[W.tod == 950, "lod_2ago"] = lod940[W.tod == 950]
W.loc[W.tod == 955, "lod_2ago"] = lod945[W.tod == 955]
W["rbh"] = W[["h945", "h950"]].max(axis=1, skipna=False)
trig = {
    "RB": (W.tod >= 955) & (W.close > W.rbh),
    "VR": (W.close > W.vwap) & (W.pclose <= W.pvwap),
    "HL": (W.lod >= W.lod_2ago - 1e-9) & (W.close > W.phigh),
}
spy_up = pd.Series(spy.reindex(pd.MultiIndex.from_arrays([W.date, W.tod])).to_numpy() > 0)
filt = {"none": np.ones(len(W), bool), "pdcl": (W.pcl >= 0.5).to_numpy(), "spy": spy_up.to_numpy()}
wkey = W["key"].to_numpy()
wf_idx = W["fidx"].to_numpy()


def wfirst(mask):
    idx = np.flatnonzero(mask)
    if not len(idx):
        return idx
    _, f1 = np.unique(wkey[idx], return_index=True)
    return wf_idx[np.sort(idx[f1])]


XS = (0.5, 0.75, 1.0)
for ref in ("O", "PC"):
    refv = (W.open if ref == "O" else W.pc).to_numpy()
    for x in XS:
        for Wn in (10, 20):
            fl = W[f"fl{Wn}"].to_numpy()
            flush = (refv - fl) / W.atr_d.to_numpy() >= x
            for tg, tm in trig.items():
                for fn, fm in filt.items():
                    idx = wfirst(flush & tm.to_numpy() & fm)
                    for ex in EXITS:
                        t = trades(idx, "long", ex)
                        cfg = f"Q2-{ref}-x{x}-W{Wn}-{tg}-{fn}-{ex}"
                                            rows.append({"cfg": cfg, "q": "Q2", "ref": ref, "x": x, "W": Wn, "trig": tg, "filt": fn,
                                     "side": "long", "exit": ex, **stats(t, N_Q2)})
            # flush-only control: entry at the 09:50 bar close
            idx = wfirst(flush & (W.tod == 950).to_numpy())
            for ex in EXITS:
                t = trades(idx, "long", ex)
                cfg = f"Q2-{ref}-x{x}-W{Wn}-FLUSHONLY-none-{ex}"
                            rows.append({"cfg": cfg, "q": "Q2c", "ref": ref, "x": x, "W": Wn, "trig": "FLUSHONLY", "filt": "none",
                             "side": "long", "exit": ex, **stats(t, N_Q2)})
    print("Q2", ref, flush=True)

# random long bar per symbol-day in 09:50-10:30
rng = np.random.default_rng(1013)
wi = np.flatnonzero(win)
perm = rng.permutation(len(wi))
kk = keyarr[wi][perm]
_, f1 = np.unique(kk, return_index=True)
ridx = np.sort(wi[perm][f1])
for ex in EXITS:
    t = trades(ridx, "long", ex)
    cfg = f"Q2-RANDOM-long-{ex}"
    rows.append({"cfg": cfg, "q": "Q2c", "trig": "RANDOM", "side": "long", "exit": ex, **stats(t, N_Q2)})

res = pd.DataFrame(rows)
res.to_csv(HERE / "results.csv", index=False)
print("configs", len(res), "(Q1", (res.q == "Q1").sum(), "Q2", res.q.isin(["Q2", "Q2c"]).sum(), ")")

# selection: report.py
