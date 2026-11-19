"""ULT-11 LR-RANK - learned ranker backtest (ultimate_1119 round2/PLAN.md sec. 2-6, "ULT-11").

Features: modules/ULT-11.py raw_features / side_ok / predict (the SAME code the live module runs) on the lab frames
(research/history2y/data/frames + context), plus the point-in-time sector-ETF columns sec_fo / sec_r30 / sec_beta built
here (sector = argmax corr of daily close-to-close returns over the prior <= 60 open non-locked sessions, min 20; beta OLS
clipped [0.3, 3]; ETF intraday fromOpen from the same frames).
Training target (FIT only): after-cost R (u = 0.25 dATR units) of entering at the decision close and exiting at the
5-min close h min later (frames + headtail tail rows), LR8 market both legs + 1.2 bp borrow for shorts, winsorised +-4.
Models per side: ridge a=1e3 / 1e5 (exact, from X'X, X'y accumulated month by month) or HistGBR(depth 3, 200 it, lr .05,
leaf 5000, l2 1, no early stopping) on a fixed 2M-row subsample (seed 1119). Walk-forward folds 2025-05..09 inside FIT.
Trading (chassis): best eligible side per name; pred > tau; <= 3 entries per bar (highest pred first); session cap 2k;
one lot per symbol; refire >= 30 min after the exit; max 2 per symbol-session. tau = in-sample prediction threshold that
gives k entries/session through this chassis (approximate exits at entry + h) on the training months.
Scoring: entry = OPEN of the 1-minute bar starting at the decision close; 2u catastrophic stop from the entry; time exit at
the close of minute entry + h - 1 (flat 15:50); LR8 costs (entry (1c+1bp) x tod mult; exit 1c+1bp; +2c on stops) + 1.2 bp
borrow on shorts; shorts only easy_to_borrow (data/universe.csv, today's flag). R per 2u (actual risk).
Halves: FIT = 2024-10 + 2025-03..09; CHECK = 2025-10-01..latest. Locked 2024-11-01..2025-02-28 never read.
    python bt.py WORK fit | check | plateau
Educational only - not financial advice."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import time
from datetime import datetime, timezone
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

HERE = Path(__file__).resolve().parent
ULT = HERE.parents[1]
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "never reads the locked block"
from mcf.research.gates import tod_cost_mult  # noqa: E402

DATA = Path("/home/user/MCF/research/history2y/data")
CACHE = Path("/home/user/MCF/data/cache_hist/1Min")
HT = Path("/home/user/MCF/research/bdi/cwt/test_b/data/headtail.parquet")
UNIV = Path("/home/user/MCF/data/universe.csv")
LOCK = ("2024-11-01", "2025-02-28")
FIT_MONTHS = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 10)]
FOLDS = [f"2025-{m:02d}" for m in range(5, 10)]
MOD = ULT / "modules" / "ULT-11.py"
ETFS = ["SPY", "QQQ", "IWM", "XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC", "SMH", "XBI",
        "KRE", "GDX", "XOP", "ITB", "IBIT", "ARKK"]
BORROW = 1.2e-4
FORBIDDEN = ("win_", "r_long", "r_short", "heat", "Heat")
SEED = 1119


def no_locked(dates):
    s = pd.Series([str(x)[:10] for x in dates])
    assert not ((s >= LOCK[0]) & (s <= LOCK[1])).any(), "locked block row found"


def load_mod():
    spec = importlib.util.spec_from_file_location("ult11", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def m2(t):
    t = np.asarray(t, int)
    return (t // 100) * 60 + t % 100


def check_months():
    import research.history2y.lib as lib
    lib.DATA = DATA
    return [m for m in lib.months() if m >= "2025-10" and m not in lib.LOCKED_MONTHS]


# ------------------------------------------------------------------------------------------------ sector map
def sector_map(work: Path, half: str):
    """half 'fit': daily rows <= 2025-09-30 only (no check-period data before the freeze); 'check': all rows."""
    p = Path(work) / f"secmap_{half}.parquet"
    if p.exists():
        return
    d = pd.read_parquet(DATA / "daily.parquet", columns=["symbol", "date", "close"],
                        filters=[("date", "<", pd.Timestamp("2024-11-01").date())])
    d2 = pd.read_parquet(DATA / "daily.parquet", columns=["symbol", "date", "close"],
                         filters=[("date", ">", pd.Timestamp("2025-02-28").date())])
    d = pd.concat([d, d2])
    if half == "fit":
        d = d[d["date"] <= pd.Timestamp("2025-09-30").date()]
    d["date"] = pd.to_datetime(d["date"]).dt.date.astype(str)
    no_locked(d.date.unique())
    px = d.pivot_table(index="date", columns="symbol", values="close").sort_index()
    ret = px.pct_change(fill_method=None)
    gap_rows = [i for i, x in enumerate(px.index) if x >= "2025-03-01"][:1]   # first session after the locked gap
    ret.iloc[gap_rows] = np.nan
    ret.iloc[0] = np.nan
    dates = list(ret.index)
    syms = list(ret.columns)
    E = [e for e in ETFS if e in ret.columns]
    R = ret.to_numpy(float)
    Ei = [syms.index(e) for e in E]
    rows = []
    for i, dd in enumerate(dates):
        if dd < "2024-10-01":
            continue
        W = R[max(0, i - 60):i]
        if len(W) < 20:
            continue
        M = np.isfinite(W)
        best_c = np.full(len(syms), -np.inf)
        best_e = np.full(len(syms), -1)
        best_b = np.full(len(syms), np.nan)
        for j, ei in zip(range(len(E)), Ei):
            x = W[:, ei]
            mm = M & np.isfinite(x)[:, None]
            cnt = mm.sum(0)
            xw = np.where(mm, x[:, None], 0.0)
            yw = np.where(mm, W, 0.0)
            with np.errstate(invalid="ignore", divide="ignore"):
                mx, my = xw.sum(0) / cnt, yw.sum(0) / cnt
                cxy = (np.where(mm, (x[:, None] - mx) * (W - my), 0)).sum(0)
                cxx = (np.where(mm, (x[:, None] - mx) ** 2, 0)).sum(0)
                cyy = (np.where(mm, (W - my) ** 2, 0)).sum(0)
                cor = cxy / np.sqrt(cxx * cyy)
                beta = cxy / cxx
            cor = np.where((cnt >= 20) & np.isfinite(cor), cor, -np.inf)
            cor[ei] = -np.inf              # never map an ETF to itself
            upd = cor > best_c
            best_c = np.where(upd, cor, best_c)
            best_e = np.where(upd, j, best_e)
            best_b = np.where(upd, beta, best_b)
        ok = best_e >= 0
        rows.append(pd.DataFrame({"symbol": np.array(syms)[ok], "date": dd, "sec": np.array(E)[best_e[ok]],
                                  "sec_beta": np.clip(best_b[ok], 0.3, 3.0)}))
    out = pd.concat(rows, ignore_index=True)
    no_locked(out.date.unique())
    out.to_parquet(p)


# ------------------------------------------------------------------------------------------------ month frames
def month_frame(month, work):
    import research.history2y.lib as lib
    lib.DATA = DATA
    f = lib.load_month(month, context=True)
    f["symbol"] = f["symbol"].astype(str)
    no_locked(f["date"].unique())
    f["date"] = f["date"].astype(str)
    half = "fit" if month in FIT_MONTHS else "check"
    sm = pd.read_parquet(Path(work) / f"secmap_{half}.parquet", filters=[("date", ">=", month + "-01"), ("date", "<=", month + "-31")])
    e = f[f.symbol.isin(ETFS)][["symbol", "date", "tod", "fromOpen"]].rename(columns={"symbol": "sec", "fromOpen": "sec_fo"})
    e = e.sort_values(["sec", "date", "tod"])
    k = e.sec + "|" + e.date
    lagv = pd.Series(e.sec_fo.to_numpy(), index=pd.MultiIndex.from_arrays([k.to_numpy(), m2(e.tod)]))
    lagv = lagv[~lagv.index.duplicated()]
    prev = lagv.reindex(pd.MultiIndex.from_arrays([k.to_numpy(), m2(e.tod) - 30])).to_numpy()
    e["sec_r30"] = ((1 + e.sec_fo / 100) / (1 + prev / 100) - 1) * 100
    f = f.merge(sm, on=["symbol", "date"], how="left").merge(e, on=["sec", "date", "tod"], how="left")
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    return f


def guard_cols(df):
    """Forbidden outcome / heat columns are dropped before any feature is computed (look-ahead guard)."""
    bad = [c for c in df.columns if c.startswith(("win_", "r_long", "r_short")) or "heat" in c.lower()]
    return df.drop(columns=bad)


def exit_close(f, h):
    """5-min close of the same symbol-day at tod + h (frames + headtail rows after 15:00); NaN if missing."""
    return f["_lookup"].reindex(pd.MultiIndex.from_arrays([f["_key"].to_numpy(), m2(f.tod) + h])).to_numpy(float)


def fit_month_job(args):
    month, work = args
    mod = load_mod()
    f = guard_cols(month_frame(month, work))
    etb = set(pd.read_csv(UNIV).query("easy_to_borrow == True").symbol.astype(str))
    X = mod.raw_features(f)
    okL, okS = mod.side_ok(f, 1), mod.side_ok(f, -1) & f.symbol.isin(etb).to_numpy()
    base = mod.intake(f)
    a = pd.Timestamp(month + "-01")
    ht = pd.read_parquet(HT, columns=["symbol", "date", "tod", "c"],
                         filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1)), ("tod", ">", 1500)])
    ht["symbol"] = ht["symbol"].astype(str)
    ht["date"] = pd.to_datetime(ht["date"]).dt.date.astype(str)
    no_locked(ht.date.unique())
    P = pd.concat([f[["symbol", "date", "tod", "close"]], ht.rename(columns={"c": "close"})])
    lk = pd.Series(P.close.to_numpy(float), index=pd.MultiIndex.from_arrays([(P.symbol + "|" + P.date).to_numpy(), m2(P.tod)]))
    lk = lk[~lk.index.duplicated()]
    key = (f.symbol + "|" + f.date).to_numpy()
    e = f.close.to_numpy(float)
    u = 0.25 * f.atr_d.to_numpy(float)
    mult = tod_cost_mult(f.tod.to_numpy())
    Y = {}
    for h in (30, 45):
        px = lk.reindex(pd.MultiIndex.from_arrays([key, m2(f.tod) + h])).to_numpy(float)
        for s, nm in ((1, "L"), (-1, "S")):
            cost = (0.01 + e * 1e-4) * mult + 0.01 + px * 1e-4 + (BORROW * e if s < 0 else 0.0)
            with np.errstate(invalid="ignore", divide="ignore"):
                Y[f"y{nm}{h}"] = np.clip((s * (px - e) - cost) / u, -4, 4)
    sel = np.flatnonzero(base & (okL | okS))
    meta = f.loc[sel, ["symbol", "date", "tod", "close", "atr_d", "adv20"]].reset_index(drop=True)
    meta["okL"], meta["okS"] = okL[sel], okS[sel]
    for kk, v in Y.items():
        meta[kk] = v[sel].astype(np.float32)
    days = sorted(f.date.unique())
    return month, meta, X[sel].astype(np.float32), days


# ------------------------------------------------------------------------------------------------ models
def scaler_from(stats_list):
    n = sum(s[0] for s in stats_list); s1 = sum(s[1] for s in stats_list); s2 = sum(s[2] for s in stats_list)
    m = s1 / n
    sd = np.sqrt(np.maximum(s2 / n - m * m, 1e-12))
    return {"mean": m.tolist(), "sd": sd.tolist()}


def month_stats(X):
    M = np.isfinite(X)
    X0 = np.where(M, X, 0.0).astype(np.float64)
    return M.sum(0).astype(float), X0.sum(0), (X0 * X0).sum(0)


def ridge_fit(acc, alpha):
    n, sx, sy, xx, xy = acc
    mx, my = sx / n, sy / n
    Sxx = xx - n * np.outer(mx, mx)
    Sxy = xy - n * mx * my
    w = np.linalg.solve(Sxx + alpha * np.eye(len(mx)), Sxy)
    return {"kind": "ridge", "w": w.tolist(), "b": float(my - mx @ w)}


def gb_export(est):
    trees = []
    for it in est._predictors:
        nd = it[0].nodes
        trees.append({"f": nd["feature_idx"].astype(int).tolist(), "thr": nd["num_threshold"].astype(float).tolist(),
                      "l": nd["left"].astype(int).tolist(), "r": nd["right"].astype(int).tolist(),
                      "leaf": nd["is_leaf"].astype(bool).tolist(), "v": nd["value"].astype(float).tolist(),
                      "depth": int(nd["depth"].max())})
    return {"kind": "gb", "baseline": float(np.ravel(est._baseline_prediction)[0]), "trees": trees}


def gb_fit(Z, y):
    from sklearn.ensemble import HistGradientBoostingRegressor
    est = HistGradientBoostingRegressor(max_depth=3, max_iter=200, learning_rate=0.05, min_samples_leaf=5000,
                                        l2_regularization=1.0, early_stopping=False, random_state=SEED)
    est.fit(Z, y)
    return est


MODELS = ("R3", "R5", "GB")


def configs():
    out, names = {}, iter("abcdefghijkl")
    for mdl in MODELS:
        for h in (30, 45):
            for k in (8, 20):
                out["11" + next(names)] = dict(model=mdl, h=h, k=k, label=f"{mdl}-h{h}-k{k}")
    return out


# ------------------------------------------------------------------------------------------------ chassis
def chassis(c, k, exit_min, cap_bar=3):
    """c: DataFrame (date, symbol, tod, pred) sorted by date, tod, pred desc; exit_min: exit minute per row.
    Returns the kept row positions (one lot per symbol, refire >= 30 min after exit, max 2/symbol-session,
    <= cap_bar per bar, session cap 2k)."""
    keep = []
    dt, sy, tt = c.date.to_numpy(), c.symbol.to_numpy(), m2(c.tod.to_numpy())
    cur, state, nday, bar_t, nbar = None, {}, 0, -1, 0
    for i in range(len(c)):
        if dt[i] != cur:
            cur, state, nday, bar_t, nbar = dt[i], {}, 0, -1, 0
        if nday >= 2 * k:
            continue
        if tt[i] != bar_t:
            bar_t, nbar = tt[i], 0
        if nbar >= cap_bar:
            continue
        n, free = state.get(sy[i], (0, -1))
        if n >= 2 or tt[i] < free:
            continue
        keep.append(i)
        state[sy[i]] = (n + 1, exit_min[i] + 30)
        nday += 1; nbar += 1
    return np.asarray(keep, int)


def best_side(pL, pS):
    side = np.where(pL >= pS, 1, -1)
    return np.maximum(pL, pS), side


def calibrate_tau(meta, pL, pS, k, h, n_sessions):
    best, side = best_side(pL, pS)
    ok = np.isfinite(best)
    c = pd.DataFrame({"date": meta.date.to_numpy()[ok], "symbol": meta.symbol.to_numpy()[ok], "tod": meta.tod.to_numpy()[ok],
                      "pred": best[ok]})
    c = c.sort_values("pred", ascending=False).groupby("date").head(15 * k)
    c = c.sort_values(["date", "tod", "pred"], ascending=[True, True, False], kind="mergesort").reset_index(drop=True)
    ex = m2(c.tod.to_numpy()) + h
    pv = c.pred.to_numpy()
    lo, hi = float(np.min(pv)), float(np.max(pv))
    for _ in range(30):
        mid = (lo + hi) / 2
        sub = c[pv > mid]
        n = len(chassis(sub, k, ex[pv > mid])) / n_sessions
        if n > k:
            lo = mid
        else:
            hi = mid
    return hi


# ------------------------------------------------------------------------------------------------ 1-minute walk
def walk_job(args):
    sym, T = args
    d = pads.dataset(str(CACHE / f"{sym}.parquet"), format="parquet")
    fld = pads.field("__index_level_0__")
    tz = "America/New_York"
    L0, L1 = pd.Timestamp("2024-11-01", tz=tz), pd.Timestamp("2025-03-01", tz=tz)
    ds_ = sorted(T.date.unique())
    a, b_ = pd.Timestamp(ds_[0], tz=tz), pd.Timestamp(ds_[-1], tz=tz) + pd.Timedelta(days=1)
    b = d.to_table(filter=((fld < L0) | (fld >= L1)) & (fld >= a) & (fld < b_)).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(tz)
    b = b.sort_index()
    no_locked(np.unique(b.index.date))
    hhmm = (b.index.hour * 100 + b.index.minute).to_numpy()
    day = np.array([str(x) for x in b.index.date])
    O, H, L, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    byday = {dd: np.flatnonzero(day == dd) for dd in np.unique(day)}
    res = []
    for r in T.itertuples():
        ix = byday.get(r.date)
        if ix is None:
            res.append((r.Index, np.nan, -1, -1, np.nan, np.nan)); continue
        hm = m2(hhmm[ix])
        tend = min(m2(r.tod) + r.h - 1, m2(1549))
        sel = ix[(hm >= m2(r.tod)) & (hm <= tend)]
        if not len(sel):
            res.append((r.Index, np.nan, -1, -1, np.nan, np.nan)); continue
        s, u = r.side, r.u
        outs = []
        for e in (O[sel[0]], r.close):       # A: next-minute open (chassis); B: signal close (bias diagnostic)
            stop = e - s * 2 * u
            px = None
            for kk in sel:
                if (s > 0 and L[kk] <= stop) or (s < 0 and H[kk] >= stop):
                    px = min(O[kk], stop) if s > 0 else max(O[kk], stop)
                    kd, xt = 1, m2(hhmm[kk]) + 1; break
            if px is None:
                px, kd, xt = C[sel[-1]], 0, m2(hhmm[sel[-1]]) + 1
            outs.append((e, px, kd, xt))
        (eA, pA, kA, xA), (eB, pB, kB, _) = outs
        mult = float(tod_cost_mult(np.array([r.tod]))[0])
        rA = (s * (pA - eA) - ((0.01 + eA * 1e-4) * mult + 0.01 + pA * 1e-4 + 0.02 * (kA == 1) + (BORROW * eA if s < 0 else 0))) / (2 * u)
        rB = (s * (pB - eB) - ((0.01 + eB * 1e-4) * mult + 0.01 + pB * 1e-4 + 0.02 * (kB == 1))) / (2 * u)
        res.append((r.Index, rA, kA, xA, rB, eA))
    return res


def walk(T, procs=4):
    T = T.reset_index(drop=True)
    jobs = [(s, g) for s, g in T.groupby("symbol") if (CACHE / f"{s}.parquet").exists()]
    with Pool(procs) as p:
        out = [x for r in p.imap_unordered(walk_job, jobs, chunksize=2) for x in r]
    a = pd.DataFrame(out, columns=["i", "r", "kind", "xmin", "r_sigclose", "entry"]).set_index("i")
    return T.join(a)


WKEY = ["symbol", "date", "tod", "side", "h"]


class Walker:
    """Caches walked rows by (symbol, date, tod, side, h)."""
    def __init__(self):
        self.done = None

    def get(self, T):
        T = T[WKEY + ["close", "u"]].drop_duplicates(WKEY)
        if self.done is not None:
            T = T.merge(self.done[WKEY], on=WKEY, how="left", indicator=True)
            T = T[T._merge == "left_only"].drop(columns="_merge")
        if len(T):
            no_locked(T.date.unique())
            W = walk(T)
            self.done = W if self.done is None else pd.concat([self.done, W], ignore_index=True)
        return self.done


def trade_book(cand, walked, k, h):
    """cand: rows with best-side pred > tau (date, symbol, tod, side, pred, close, u). Real exits -> chassis."""
    c = cand.assign(h=h).merge(walked[WKEY + ["r", "kind", "xmin", "r_sigclose"]], on=WKEY, how="left")
    c = c[c.kind >= 0]
    c = c.sort_values(["date", "tod", "pred"], ascending=[True, True, False], kind="mergesort").reset_index(drop=True)
    kept = chassis(c, k, c.xmin.to_numpy())
    return c.iloc[kept].reset_index(drop=True)


# ------------------------------------------------------------------------------------------------ statistics
def spy_types():
    f = pads.field("__index_level_0__")
    tz = "America/New_York"
    b = pads.dataset(str(CACHE / "SPY.parquet"), format="parquet").to_table(
        filter=(f < pd.Timestamp("2024-11-01", tz=tz)) | (f >= pd.Timestamp("2025-03-01", tz=tz))).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(tz)
    b = b[(b.index.hour * 100 + b.index.minute >= 930) & (b.index.hour * 100 + b.index.minute <= 1559)]
    b["date"] = [str(x) for x in b.index.date]
    no_locked(b.date.unique())
    g = b.groupby("date").agg(o=("open", "first"), c=("close", "last"))
    ret = (g.c / g.o - 1) * 100
    return pd.Series(np.where(ret >= 0.3, "up", np.where(ret <= -0.3, "down", "flat")), index=g.index)


def stats(t, sessions, col="r", spy=None):
    t = t[t[col].notna()]
    n_s = len(sessions)
    if not len(t):
        return {"trades": 0, "sessions": n_s}
    day = t.groupby("date")[col].sum()
    tot = float(t[col].sum())
    avg = tot / len(t)
    best = day.idxmax()
    dev = (t[col] - avg).groupby(t.date).sum()
    se = float(np.sqrt((dev ** 2).sum())) / len(t)
    tps = len(t) / day.size
    o = {"trades": int(len(t)), "sessions": n_s, "sessions_traded": int(day.size), "trades_per_session": round(len(t) / n_s, 3),
         "win": round(float((t[col] > 0).mean()), 3), "avg_r": round(avg, 4), "avg_r_u": round(2 * avg, 4),
         "avg_r_wo_best_day": round(float(t.loc[t.date != best, col].mean()), 4), "best_day": best,
         "best_day_share": round(float(day.max()) / tot, 3) if tot > 0 else None, "total_r": round(tot, 2),
         "total_r_wo_best_day": round(tot - float(day.max()), 2),
         "total_r_per_session": round(tot / n_s, 4), "worst_day": round(float(day.min()), 2),
         "worst_day_per_trade_session": round(float(day.min()) / tps, 3), "t_day_clustered": round(avg / se, 3) if se > 0 else None}
    ex = t[(t.date < "2025-04-03") | (t.date > "2025-04-09")]
    o["avg_r_ex_0403_0409"] = round(float(ex[col].mean()), 4) if len(ex) else None
    if "side" in t:
        for s, nm in ((1, "long"), (-1, "short")):
            x = t[t.side == s]
            o[f"{nm}_trades"] = int(len(x)); o[f"{nm}_avg_r"] = round(float(x[col].mean()), 4) if len(x) else None
    if spy is not None:
        ty = t.date.map(spy)
        for nm in ("up", "flat", "down"):
            x = t[ty == nm]
            o[f"spy_{nm}_avg_r"] = round(float(x[col].mean()), 4) if len(x) else None
    if "xmin" in t:
        o["median_hold_min"] = float(np.median(t.xmin - m2(t.tod)))
    ss = sorted(sessions)
    mid = ss[len(ss) // 2]
    o["first_half_avg_r"] = round(float(t.loc[t.date < mid, col].mean()), 4) if (t.date < mid).any() else None
    o["second_half_avg_r"] = round(float(t.loc[t.date >= mid, col].mean()), 4) if (t.date >= mid).any() else None
    return o


def rand_table(meta, okL, okS, rng):
    """One random eligible decision bar per (symbol, date, side) (same-name random-entry control pool)."""
    out = []
    for s, ok in ((1, okL), (-1, okS)):
        m = meta.loc[ok, ["symbol", "date", "tod", "close", "atr_d"]].copy()
        m["rk"] = rng.random(len(m))
        m = m.sort_values("rk").groupby(["symbol", "date"]).head(1)
        out.append(m.assign(side=s).drop(columns="rk"))
    return pd.concat(out, ignore_index=True)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def jdump(o, p):
    Path(p).write_text(json.dumps(o, indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x)))


# ------------------------------------------------------------------------------------------------ FIT stage
def stage_fit(work):
    t0 = time.time()
    mod = load_mod()
    assert not any(f'_col(d, "{c}' in MOD.read_text() for c in FORBIDDEN), "forbidden column read by a feature"
    sector_map(work, "fit")
    metas, Xs, days = {}, {}, {}
    with Pool(3) as p:
        for m, meta, X, dd in p.imap_unordered(fit_month_job, [(m, str(work)) for m in FIT_MONTHS]):
            metas[m], Xs[m], days[m] = meta, X, dd
            print(m, len(meta), f"{time.time() - t0:.0f}s", flush=True)
    for m in FIT_MONTHS:
        no_locked(days[m])
    mstats = {m: month_stats(Xs[m]) for m in FIT_MONTHS}
    cfgs = configs()
    folds = {fm: [m for m in FIT_MONTHS if m < fm] for fm in FOLDS}
    folds["final"] = list(FIT_MONTHS)
    rng = np.random.default_rng(SEED)
    walker = Walker()
    spy = spy_types()
    oof_sessions = sorted(sum((days[m] for m in FOLDS), []))
    fit_sessions = sorted(sum((days[m] for m in FIT_MONTHS), []))
    cands = {c: [] for c in cfgs}           # OOF candidate rows per config
    final_models, final_tau, insample = {}, {}, {}
    for fk, train in folds.items():
        sc = scaler_from([mstats[m] for m in train])
        Zm = {m: mod.zscore(Xs[m].astype(np.float64), sc) for m in (train + ([fk] if fk != "final" else []))}
        models = {}
        for side, okc in ((1, "okL"), (-1, "okS")):
            nm = "L" if side > 0 else "S"
            for h in (30, 45):
                yk = f"y{nm}{h}"
                acc = None
                for m in train:
                    ok = metas[m][okc].to_numpy() & np.isfinite(metas[m][yk].to_numpy())
                    Z, y = Zm[m][ok], metas[m][yk].to_numpy(np.float64)[ok]
                    a = (len(y), Z.sum(0), y.sum(), Z.T @ Z, Z.T @ y)
                    acc = a if acc is None else tuple(x + z for x, z in zip(acc, a))
                models[("R3", side, h)] = ridge_fit(acc, 1e3)
                models[("R5", side, h)] = ridge_fit(acc, 1e5)
                # GB: fixed 2M-row random subsample of the training rows
                idx = [(m, np.flatnonzero(metas[m][okc].to_numpy() & np.isfinite(metas[m][yk].to_numpy()))) for m in train]
                tot = sum(len(i) for _, i in idx)
                take = min(1.0, 2_000_000 / tot)
                rs = np.random.default_rng(SEED)
                Zs, ys = [], []
                for m, i in idx:
                    pick = i[rs.random(len(i)) < take]
                    Zs.append(Zm[m][pick]); ys.append(metas[m][yk].to_numpy(np.float64)[pick])
                est = gb_fit(np.vstack(Zs), np.concatenate(ys))
                models[("GB", side, h)] = gb_export(est)
                models[("GB", side, h)]["_est"] = est
                print(fk, nm, h, "trained", f"{time.time() - t0:.0f}s", flush=True)

        def pred(mdl, side, h, Z):
            sm = models[(mdl, side, h)]
            if sm["kind"] == "gb":
                return sm["_est"].predict(Z)
            return mod.predict_z(Z, sm)

        # verify the numpy tree evaluator (the live module path) against sklearn on a sample
        Zchk = Zm[train[0]][:20000]
        for side in (1, -1):
            g = models[("GB", side, 30)]
            assert np.allclose(mod.predict_z(Zchk, {k_: v for k_, v in g.items() if k_ != "_est"}), g["_est"].predict(Zchk), atol=1e-6)
        n_train_sessions = sum(len(days[m]) for m in train)
        tmeta = pd.concat([metas[m] for m in train], ignore_index=True)
        for cn, cfg in cfgs.items():
            mdl, h, k = cfg["model"], cfg["h"], cfg["k"]
            pLs, pSs = [], []
            for m in train:
                okL, okS = metas[m].okL.to_numpy(), metas[m].okS.to_numpy()
                pl = np.full(len(okL), -np.inf); ps = np.full(len(okL), -np.inf)
                pl[okL] = pred(mdl, 1, h, Zm[m][okL]); ps[okS] = pred(mdl, -1, h, Zm[m][okS])
                pLs.append(pl); pSs.append(ps)
            pL, pS = np.concatenate(pLs), np.concatenate(pSs)
            tau = calibrate_tau(tmeta, pL, pS, k, h, n_train_sessions)
            if fk == "final":
                final_tau[cn] = tau
                final_models[cn] = {"long": models[(mdl, 1, h)], "short": models[(mdl, -1, h)]}
                best, side = best_side(pL, pS)
                ok = best > tau
                insample[cn] = tmeta.loc[ok, ["symbol", "date", "tod", "close", "atr_d"]].assign(side=side[ok], pred=best[ok])
            else:
                mt = metas[fk]
                okL, okS = mt.okL.to_numpy(), mt.okS.to_numpy()
                pl = np.full(len(okL), -np.inf); ps = np.full(len(okL), -np.inf)
                pl[okL] = pred(mdl, 1, h, Zm[fk][okL]); ps[okS] = pred(mdl, -1, h, Zm[fk][okS])
                best, side = best_side(pl, ps)
                ok = best > tau
                cands[cn].append(mt.loc[ok, ["symbol", "date", "tod", "close", "atr_d"]].assign(side=side[ok], pred=best[ok], tau=tau, fold=fk))
            print(fk, cn, "tau", round(tau, 4), f"{time.time() - t0:.0f}s", flush=True)
        del Zm
    # OOF scoring through the real chassis
    grid = {}
    books = {}
    for cn, cfg in cfgs.items():
        c = pd.concat(cands[cn], ignore_index=True)
        c["u"] = 0.25 * c.atr_d
        c["h"] = cfg["h"]
        W = walker.get(c)
        bk = trade_book(c, W, cfg["k"], cfg["h"])
        books[cn] = bk
        st = stats(bk, oof_sessions, "r", spy)
        st.update(cfg, candidates_per_session=round(len(c) / len(oof_sessions), 2),
                  score_total_wo_best_day=st.get("total_r_wo_best_day"))
        grid[cn] = st
        print(cn, cfg["label"], st["trades_per_session"], st["avg_r"], st["total_r"], st.get("total_r_wo_best_day"), flush=True)
    elig = {c: g for c, g in grid.items() if g.get("trades_per_session", 0) >= 2.0}
    pool = elig if elig else grid
    order = list(cfgs)
    pick = max(pool, key=lambda c: (pool[c].get("total_r_wo_best_day", -1e9), -order.index(c)))
    cfg = cfgs[pick]
    bk = books[pick]
    # bias diagnostic: signal-close fill, no borrow fee
    diag = stats(bk.assign(r=bk.r_sigclose), oof_sessions, "r", spy)
    # random-entry control (same symbol-sessions and side, random eligible bar, same exit)
    allmeta = pd.concat([metas[m] for m in FOLDS], ignore_index=True)
    rt = rand_table(allmeta, allmeta.okL.to_numpy(), allmeta.okS.to_numpy(), rng)
    ss = bk[["symbol", "date", "side"]].drop_duplicates()
    rc = rt.merge(ss, on=["symbol", "date", "side"])
    rc["u"], rc["h"] = 0.25 * rc.atr_d, cfg["h"]
    W = walker.get(rc)
    rc = rc.merge(W[WKEY + ["r", "kind", "xmin"]], on=WKEY, how="left")
    rc = rc[rc.kind >= 0]
    rand = stats(rc, oof_sessions, "r", spy)
    # in-sample all-FIT book of the final model (reported only)
    ins = insample[pick].copy()
    ins["u"], ins["h"] = 0.25 * ins.atr_d, cfg["h"]
    W = walker.get(ins)
    ibk = trade_book(ins, W, cfg["k"], cfg["h"])
    ins_st = stats(ibk, fit_sessions, "r", spy)
    # freeze: model JSON beside the module + fitsel.json (before any check frame is built)
    md = final_models[pick]
    model = {"id": "ULT-11", "config": pick, **cfg, "tau": final_tau[pick], "feats": mod.FEATS,
             **scaler_from([mstats[m] for m in FIT_MONTHS]),
             "long": {k_: v for k_, v in md["long"].items() if k_ != "_est"},
             "short": {k_: v for k_, v in md["short"].items() if k_ != "_est"},
             "trained_on": FIT_MONTHS, "frozen_utc": datetime.now(timezone.utc).isoformat()}
    mp = ULT / "modules" / "ULT-11_model.json"
    jdump(model, mp)
    # all 12 final models for the plateau diagnostic (scored only after check_once.json exists)
    allm = {cn: {"config": cn, **cfgs[cn], "tau": final_tau[cn], **scaler_from([mstats[m] for m in FIT_MONTHS]),
                 "long": {k_: v for k_, v in final_models[cn]["long"].items() if k_ != "_est"},
                 "short": {k_: v for k_, v in final_models[cn]["short"].items() if k_ != "_est"}} for cn in cfgs}
    jdump(allm, Path(work) / "all_final_models.json")
    jdump({cn: {kk: vv for kk, vv in g.items()} for cn, g in grid.items()}, HERE / "fit_grid.json")
    fitsel = {"id": "ULT-11", "config": pick, **cfg,
              "rule": "round2 PLAN sec.5: highest OOF fit total R minus best fit day among configs >= 2 trades/session",
              "reached_2_per_session": bool(elig), "tau": final_tau[pick], "oof_fit": grid[pick], "insample_all_fit": ins_st,
              "random_control_oof": rand, "bias_diag_oof_sigclose_noborrow": diag,
              "fold_taus": {cn: sorted(set(round(float(x), 5) for x in pd.concat(cands[cn]).tau)) if len(pd.concat(cands[cn])) else []
                            for cn in [pick]},
              "sha256": {"bt.py": sha(__file__), "module": sha(MOD), "model_json": sha(mp)},
              "frozen_utc": datetime.now(timezone.utc).isoformat()}
    jdump(fitsel, HERE / "fitsel.json")
    print("PICK", pick, cfg, f"{time.time() - t0:.0f}s")


# ------------------------------------------------------------------------------------------------ CHECK stage
def check_month_job(args):
    month, work, model_paths = args
    mod = load_mod()
    f = guard_cols(month_frame(month, work))
    etb = set(pd.read_csv(UNIV).query("easy_to_borrow == True").symbol.astype(str))
    isetb = f.symbol.isin(etb).to_numpy()
    X = mod.raw_features(f)
    okL, okS = mod.side_ok(f, 1), mod.side_ok(f, -1) & isetb
    out = {}
    for nm, mp in model_paths.items():
        model = json.loads(Path(mp).read_text()) if not isinstance(mp, dict) else mp
        Z = mod.zscore(X, model)
        pl = np.full(len(f), -np.inf); ps = np.full(len(f), -np.inf)
        pl[okL] = mod.predict_z(Z[okL], model["long"]); ps[okS] = mod.predict_z(Z[okS], model["short"])
        best, side = best_side(pl, ps)
        ok = best > float(model["tau"])
        out[nm] = f.loc[ok, ["symbol", "date", "tod", "close", "atr_d"]].assign(side=side[ok], pred=best[ok]).reset_index(drop=True)
    meta = f[["symbol", "date", "tod", "close", "atr_d"]]
    rt = rand_table(meta, okL, okS, np.random.default_rng(SEED + int(month.replace("-", ""))))
    # live-path equivalence: module.predict on one symbol-day equals the batch prediction
    days = sorted(f.date.unique())
    return month, out, rt, days


def run_check(work, model_paths):
    import research.history2y.lib as lib  # noqa
    ms = check_months()
    res, rts, days = {k: [] for k in model_paths}, [], []
    with Pool(3) as p:
        for m, out, rt, dd in p.imap_unordered(check_month_job, [(m, str(work), model_paths) for m in ms]):
            for k, v in out.items():
                res[k].append(v)
            rts.append(rt); days += dd
            print(m, {k: len(v) for k, v in out.items()}, flush=True)
    no_locked(days)
    return {k: pd.concat(v, ignore_index=True) for k, v in res.items()}, pd.concat(rts, ignore_index=True), sorted(days)


def stage_check(work):
    fs = json.loads((HERE / "fitsel.json").read_text())
    mp = ULT / "modules" / "ULT-11_model.json"
    assert sha(mp) == fs["sha256"]["model_json"], "model changed after the freeze"
    assert not (HERE / "check_once.json").exists(), "check is scored ONCE"
    sector_map(work, "check")   # all (built from all non-locked daily rows, strictly prior sessions per date)
    res, rt, days = run_check(work, {"pick": str(mp)})
    c = res["pick"]
    c["u"], c["h"] = 0.25 * c.atr_d, int(fs["h"])
    walker = Walker()
    W = walker.get(c)
    bk = trade_book(c, W, int(fs["k"]), int(fs["h"]))
    spy = spy_types()
    st = stats(bk, days, "r", spy)
    diag = stats(bk.assign(r=bk.r_sigclose), days, "r", spy)
    ss = bk[["symbol", "date", "side"]].drop_duplicates()
    rc = rt.merge(ss, on=["symbol", "date", "side"])
    rc["u"], rc["h"] = 0.25 * rc.atr_d, int(fs["h"])
    W = walker.get(rc)
    rc = rc.merge(W[WKEY + ["r", "kind", "xmin"]], on=WKEY, how="left")
    rc = rc[rc.kind >= 0]
    rand = stats(rc, days, "r", spy)
    # same symbol-sessions, matched random vs signal per session (survivorship-neutral read)
    jdump({"id": "ULT-11", "config": fs["config"], "check": st, "random_control": rand, "signal_minus_random": round(st["avg_r"] - rand["avg_r"], 4),
           "bias_diag_sigclose_noborrow": diag, "candidates_per_session": round(len(c) / len(days), 2),
           "scored_utc": datetime.now(timezone.utc).isoformat()}, HERE / "check_once.json")
    bk[["symbol", "date", "tod", "side", "pred", "r", "kind", "xmin"]].to_csv(HERE / "check_trades.csv.gz", index=False)
    print(json.dumps(st, indent=1))


def stage_plateau(work):
    assert (HERE / "check_once.json").exists(), "plateau only after the single check score"
    allm = json.loads((Path(work) / "all_final_models.json").read_text())
    res, rt, days = run_check(work, allm)
    walker = Walker()
    out = {}
    for cn, c in res.items():
        cfg = allm[cn]
        c["u"], c["h"] = 0.25 * c.atr_d, int(cfg["h"])
        W = walker.get(c)
        bk = trade_book(c, W, int(cfg["k"]), int(cfg["h"]))
        st = stats(bk, days, "r")
        out[cn] = {"label": cfg["label"], **{k: st.get(k) for k in ("trades_per_session", "avg_r", "avg_r_wo_best_day", "total_r",
                                                                  "t_day_clustered", "best_day_share", "long_avg_r", "short_avg_r")}}
        print(cn, out[cn], flush=True)
    jdump(out, HERE / "check_plateau.json")


if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True)
    {"fit": stage_fit, "check": stage_check, "plateau": stage_plateau}[sys.argv[2]](W)
