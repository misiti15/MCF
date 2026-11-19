"""ULT-31 EARN-AWARE RANK backtest (ultimate_1119 round4/PLAN.md sec. 2, 3 "ULT-31", 5, 6, 7).

Reuses the round-2 ULT-11 pipeline (round2/ULT-11/bt.py: sector map + month frame, chassis, tau calibration, ridge /
GB export, stats) and the round-3 ULT-20 flow (collapse to the better side, walk-forward folds, Walker), plus the live
module modules/ULT-31.py (earn_state / build / side_rows / side_features / predict: the SAME code the live module runs).
New here: the earnings state (round4/data/earnings_yf.parquet, never the _lockedblock sibling) through the module's
earn_state(); ridge with leave-one-month-out sign-stability selection (RS); the round-4 cost fixes (reaction-day x1.5
entry/exit cost before 10:30; borrow 5 bp of entry notional on shorts in RD-1..RD+1, 8 bp under $20, else 1.2 / 3 bp).
Rows: every (decision bar 10:00-15:00, name, side) in universe ALL (ADV20 >= $100M, cost_r <= 0.05) or EVT (RD / RD+1
names, ADV20 >= $30M, cost_r <= 0.08); universal filters; shorts easy_to_borrow (universe.csv, today's flag), never LEV.
Target (training proxy, FIT only): after-cost R per 2u of decision close -> 5-min close at tod + 45 (frames + headtail),
LR8 both legs + surcharge + borrow, winsorised +-4.
Models: RS ridge a=1e3 on z-scored features; inside each training fold the ridge is refit leaving out one training month
at a time; a feature is kept only if its coefficient sign equals the full-fold sign in >= 80% of those refits; the
ridge is refit on the kept set (dropped features weight 0). GB HistGBR(depth 2, 100 it, lr .05, min leaf 2000 ALL / 300
EVT, l2 1, seed 1119, no early stopping; ALL trains on a seeded subsample of <= 2M rows).
Walk-forward folds 2025-05..09 inside FIT (train on all earlier FIT months); "fit" = pooled OOF. Final model = all FIT.
Trading: best side per name-bar; score > tau_k; <= 3 per bar; session cap 2k; one lot per symbol; refire >= 30 min after
exit; max 2 per symbol-session. tau_k = in-sample threshold giving k entries/session on the training months (EVT: per
earnings-season session, season = >= 5 lab names on RD that day).
Scoring: entry = OPEN of the 1-minute bar starting at the decision close (within 4 min); 2u catastrophic stop; time exit
at the close of minute entry + 44 (flat 15:49); LR8 + surcharge + borrow. R per 2u.
FIT = 2024-10 + 2025-03..09; CHECK = 2025-10-01..latest. Locked 2024-11-01..2025-02-28 never read.
    python bt.py WORK fit | check | plateau
Educational only - not financial advice."""
from __future__ import annotations

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

_s = importlib.util.spec_from_file_location("ult11bt", ULT / "round2" / "ULT-11" / "bt.py")
B11 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(B11)
DATA, CACHE, HT, UNIV, LOCK = B11.DATA, B11.CACHE, B11.HT, B11.UNIV, B11.LOCK
no_locked, m2, chassis, ridge_fit, gb_export, stats, spy_types, sha, jdump, guard_cols = (
    B11.no_locked, B11.m2, B11.chassis, B11.ridge_fit, B11.gb_export, B11.stats, B11.spy_types, B11.sha, B11.jdump,
    B11.guard_cols)
sector_map, check_months = B11.sector_map, B11.check_months
FIT_MONTHS, FOLDS = B11.FIT_MONTHS, B11.FOLDS
MOD = ULT / "modules" / "ULT-31.py"
MODEL_JSON = ULT / "modules" / "ULT-31_model.json"
EARN = HERE.parent / "data" / "earnings_yf.parquet"
SEED = 1119
H = 45
N_CUM = 996
SURCH_T = 1030
FORBIDDEN = ("win_", "r_long", "r_short", "heat", "Heat")
GB_MAX_ROWS = 2_000_000


def load_mod(name="ult31"):
    spec = importlib.util.spec_from_file_location(name, MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def configs():
    out, names = {}, iter("abcdefgh")
    for u in ("ALL", "EVT"):
        for mdl in ("RS", "GB"):
            for k in (3, 8):
                out["31" + next(names)] = dict(univ=u, model=mdl, k=k, h=H, label=f"{u}-{mdl}-k{k}")
    return out


def locked(a):
    a = np.asarray(a, dtype=str)
    return (a >= LOCK[0]) & (a <= LOCK[1] + "~")


def borrow(side, e, ewin):
    bp = np.where(ewin > 0, np.where(e < 20, 8e-4, 5e-4), np.where(e < 20, 3e-4, 1.2e-4))
    return np.where(side < 0, bp * e, 0.0)


def cost_total(side, tod, e, px, kd, erd, ewin, xt, fixes=True):
    """$ cost per share: LR8 entry (x tod mult) + exit (1c + 1bp; +2c on stops) [+ x1.5 RD first-hour surcharge, borrow]."""
    tod = np.asarray(tod)
    se = np.where(fixes & (erd > 0) & (tod < SURCH_T), 1.5, 1.0)
    sx = np.where(fixes & (erd > 0) & (np.nan_to_num(np.asarray(xt, float), nan=9999) < SURCH_T), 1.5, 1.0)
    ec = (0.01 + e * 1e-4) * tod_cost_mult(tod) * se
    xc = (0.01 + px * 1e-4 + np.where(kd == 1, 0.02, 0.0)) * sx
    return ec + xc + (borrow(side, e, ewin) if fixes else 0.0)


# ------------------------------------------------------------------------------------------------ earnings state
def daily_closes(lo, hi):
    """daily closes lo..hi via pyarrow filters that exclude the locked block (never loaded)."""
    import datetime as dt
    f = pads.field("date")
    ds = pads.dataset(str(DATA / "daily.parquet"), format="parquet")
    L0, L1 = dt.date(2024, 11, 1), dt.date(2025, 2, 28)
    t = ds.to_table(columns=["symbol", "date", "close"],
                    filter=((f < L0) | (f > L1)) & (f >= dt.date.fromisoformat(lo)) & (f <= dt.date.fromisoformat(hi)))
    d = t.to_pandas()
    d["date"] = pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d")
    d["symbol"] = d["symbol"].astype(str)
    no_locked(d.date.unique())
    return d


def build_state(work, half):
    """fit: only report dates and closes <= 2025-09-30 are read (no check-period row before the freeze)."""
    p = Path(work) / f"earnstate_{half}.parquet"
    if p.exists():
        return pd.read_parquet(p)
    mod = load_mod()
    e = pd.read_parquet(EARN)
    d = pd.to_datetime(e["date"]).dt.strftime("%Y-%m-%d")
    lo, hi = ("2024-08-01", "2025-09-30") if half == "fit" else ("2025-08-01", "2026-12-31")
    e = e[(d >= lo) & (d <= hi)]
    no_locked(pd.to_datetime(e["date"]).dt.strftime("%Y-%m-%d").unique())
    sess = mod.sessions(lo, "2025-10-31" if half == "fit" else "2026-12-31")
    dl = daily_closes(lo, hi)
    st = mod.earn_state(e, sess, dl, drop=locked)
    st = st[st.date <= "2025-09-30"] if half == "fit" else st[st.date >= "2025-10-01"]
    st = st[st.date >= "2024-10-01"]
    no_locked(st.date.unique())
    st.to_parquet(p)
    return st


# ------------------------------------------------------------------------------------------------ month rows
def etb_set():
    u = pd.read_csv(UNIV)
    return set(u.loc[u.easy_to_borrow.astype(str).str.lower() == "true", "symbol"].astype(str))


def month_frame(month, work, half):
    f = guard_cols(B11.month_frame(month, work))
    assert not any(c.startswith(("win_", "r_long", "r_short")) or "heat" in c.lower() for c in f.columns)
    st = pd.read_parquet(Path(work) / f"earnstate_{half}.parquet",
                         filters=[("date", ">=", month + "-01"), ("date", "<=", month + "-31")])
    f = f.merge(st, on=["symbol", "date"], how="left")
    for k in ("e_rd", "e_rd1", "e_pre", "e_bmo", "e_win"):
        f[k] = f[k].fillna(0.0)
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    return f


def month_rows(f, mod, b, etb):
    """Union rows of ALL and EVT for both sides (positions into b['sel'])."""
    sel = b["sel"]
    isetb = np.array([s in etb for s in f.symbol.to_numpy()[sel]])
    metas, Xs = [], []
    for sgn in (1, -1):
        ra, re_ = mod.side_rows(b, sgn, "ALL"), mod.side_rows(b, sgn, "EVT")
        if sgn < 0:
            ra, re_ = ra & isetb, re_ & isetb
        r = ra | re_
        X = mod.side_features(b, sgn)[r].astype(np.float32)
        pos = sel[r]
        m = f.iloc[pos][["symbol", "date", "tod", "close", "atr_d", "e_rd", "e_win"]].reset_index(drop=True)
        m["side"], m["inALL"], m["inEVT"] = sgn, ra[r], re_[r]
        metas.append(m); Xs.append(X)
    return pd.concat(metas, ignore_index=True), np.vstack(Xs)


def target(meta, f, month):
    a = pd.Timestamp(month + "-01")
    ht = pd.read_parquet(HT, columns=["symbol", "date", "tod", "c"],
                         filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1)), ("tod", ">", 1500)])
    ht["symbol"] = ht["symbol"].astype(str)
    ht["date"] = pd.to_datetime(ht["date"]).dt.date.astype(str)
    no_locked(ht.date.unique())
    P = pd.concat([f[["symbol", "date", "tod", "close"]], ht.rename(columns={"c": "close"})])
    lk = pd.Series(P.close.to_numpy(float), index=pd.MultiIndex.from_arrays([(P.symbol + "|" + P.date).to_numpy(), m2(P.tod)]))
    lk = lk[~lk.index.duplicated()]
    px = lk.reindex(pd.MultiIndex.from_arrays([(meta.symbol + "|" + meta.date).to_numpy(), m2(meta.tod) + H])).to_numpy(float)
    e = meta.close.to_numpy(float)
    s = meta.side.to_numpy()
    u = 0.25 * meta.atr_d.to_numpy(float)
    cost = cost_total(s, meta.tod.to_numpy(), e, px, np.zeros(len(e)), meta.e_rd.to_numpy(), meta.e_win.to_numpy(),
                      np.full(len(e), 9999))
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.clip((s * (px - e) - cost) / (2 * u), -4, 4).astype(np.float32)


def month_job(args):
    month, work, half = args
    mod = load_mod()
    f = month_frame(month, work, half)
    b = mod.build(f)
    meta, X = month_rows(f, mod, b, etb_set())
    meta["y"] = target(meta, f, month)
    d50 = f[(f.tod == 1000) & (f.e_rd > 0)]
    nrd = d50.groupby("date").symbol.nunique().to_dict()
    days = sorted(f.date.unique())
    return month, meta, X, days, {d: int(nrd.get(d, 0)) for d in days}


# ------------------------------------------------------------------------------------------------ models
def fit_scaler(X):
    with np.errstate(invalid="ignore"):
        m = np.nanmean(X.astype(np.float64), 0)
        sd = np.nanstd(X.astype(np.float64), 0)
    m = np.nan_to_num(m)
    sd = np.where(np.isfinite(sd) & (sd > 1e-9), sd, 1.0)
    return {"mean": m.tolist(), "sd": sd.tolist()}


def acc_of(Z, y):
    return [len(y), Z.sum(0), y.sum(), Z.T @ Z, Z.T @ y]


def acc_sub(a, b):
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2], a[3] - b[3], a[4] - b[4]]


def ridge_keep(acc, keep, alpha=1e3):
    n, sx, sy, xx, xy = acc
    ix = np.flatnonzero(keep)
    w = np.zeros(len(sx))
    if len(ix):
        sub = ridge_fit((n, sx[ix], sy, xx[np.ix_(ix, ix)], xy[ix]), alpha)
        w[ix] = sub["w"]
        b = sub["b"]
    else:
        b = sy / n
    return {"kind": "ridge", "w": w.tolist(), "b": float(b)}


def train_rs(Z, y, month_id):
    """ridge + leave-one-month-out sign-stability selection (>= 80% sign agreement with the full-fold fit)."""
    accs = {m: acc_of(Z[month_id == m], y[month_id == m]) for m in np.unique(month_id)}
    tot = None
    for a in accs.values():
        tot = a if tot is None else [tot[i] + a[i] for i in range(5)]
    full = np.asarray(ridge_fit(tuple(tot), 1e3)["w"])
    agree = np.zeros(len(full))
    for m, a in accs.items():
        w = np.asarray(ridge_fit(tuple(acc_sub(tot, a)), 1e3)["w"])
        agree += (np.sign(w) == np.sign(full)) & (full != 0)
    frac = agree / len(accs)
    keep = frac >= 0.8
    out = ridge_keep(tot, keep)
    out["kept"] = keep.astype(int).tolist()
    out["sign_agree"] = np.round(frac, 3).tolist()
    return out


def train_gb(Z, y, leaf, rng):
    from sklearn.ensemble import HistGradientBoostingRegressor
    if len(y) > GB_MAX_ROWS:
        ix = np.sort(rng.choice(len(y), GB_MAX_ROWS, replace=False))
        Z, y = Z[ix], y[ix]
    est = HistGradientBoostingRegressor(max_depth=2, max_iter=100, learning_rate=0.05, min_samples_leaf=leaf,
                                        l2_regularization=1.0, early_stopping=False, random_state=SEED)
    est.fit(Z, y)
    return gb_export(est), est


def collapse(meta, pred, k):
    c = meta[["symbol", "date", "tod", "close", "atr_d", "side", "e_rd", "e_win"]].assign(pred=pred)
    c = c[np.isfinite(c.pred)]
    c = c.sort_values("pred", ascending=False, kind="mergesort")
    if k:
        c = c.groupby("date", sort=False).head(30 * k)
    return c.drop_duplicates(["symbol", "date", "tod"])


def tau_for(c, k, n_sessions):
    return B11.calibrate_tau(c.reset_index(drop=True), c.pred.to_numpy(), np.full(len(c), -np.inf), k, H, n_sessions)


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
    hm_all = m2(hhmm)
    day = np.array([str(x) for x in b.index.date])
    O, Hh, L, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    byday = {}
    if len(day):
        st = np.flatnonzero(np.r_[True, day[1:] != day[:-1]])
        en = np.r_[st[1:], len(day)]
        byday = {day[x]: np.arange(x, y) for x, y in zip(st, en)}
    res = []
    for r in T.itertuples():
        ix = byday.get(r.date)
        nan = (r.Index, np.nan, np.nan, -1, np.nan, np.nan, -1)
        if ix is None:
            res.append(nan); continue
        hm = hm_all[ix]
        t0 = m2(r.tod)
        j0 = np.searchsorted(hm, t0)
        if j0 >= len(ix) or hm[j0] - t0 > 4 or hm[j0] >= m2(1550):
            res.append(nan); continue
        tend = min(hm[j0] + 44, m2(1549))
        sel = ix[j0:][hm[j0:] <= tend]
        s, u = r.side, r.u
        outs = []
        for e in (O[sel[0]], r.close):       # A: next-minute open (chassis); B: signal close (bias diagnostic)
            stop = e - s * 2 * u
            px = None
            for kk in sel:
                if (s > 0 and L[kk] <= stop) or (s < 0 and Hh[kk] >= stop):
                    px = min(O[kk], stop) if s > 0 else max(O[kk], stop)
                    kd, xt = 1, hm_all[kk] + 1; break
            if px is None:
                px, kd, xt = C[sel[-1]], 0, hm_all[sel[-1]] + 1
            outs.append((e, px, kd, xt))
        (eA, pA, kA, xA), (_, pB, kB, _) = outs
        res.append((r.Index, eA, pA, kA, xA, pB, kB))
    return res


def walk(T, procs=3):
    T = T.reset_index(drop=True)
    jobs = [(s, g) for s, g in T.groupby("symbol") if (CACHE / f"{s}.parquet").exists()]
    with Pool(procs) as p:
        out = [x for r in p.imap_unordered(walk_job, jobs, chunksize=2) for x in r]
    a = pd.DataFrame(out, columns=["i", "entry", "px", "kind", "xmin", "pxB", "kindB"]).set_index("i")
    T = T.join(a)
    T["kind"] = T["kind"].fillna(-1).astype(int)
    s, tod, u = T.side.to_numpy(), T.tod.to_numpy(), T.u.to_numpy()
    xt_hhmm = (T.xmin.fillna(0) // 60 * 100 + T.xmin.fillna(0) % 60).to_numpy()
    e, px, kd = T.entry.to_numpy(), T.px.to_numpy(), T.kind.to_numpy()
    erd, ewin = T.e_rd.to_numpy(), T.e_win.to_numpy()
    T["r"] = (s * (px - e) - cost_total(s, tod, e, px, kd, erd, ewin, xt_hhmm)) / (2 * u)
    eB, pB, kB = T.close.to_numpy(), T.pxB.to_numpy(), T.kindB.to_numpy()
    T["r_sigclose"] = (s * (pB - eB) - cost_total(s, tod, eB, pB, kB, erd, ewin, xt_hhmm, fixes=False)) / (2 * u)
    return T.drop(columns=["px", "pxB", "kindB"])


WKEY = ["symbol", "date", "tod", "side"]


class Walker:
    def __init__(self):
        self.done = None

    def get(self, T):
        T = T.assign(u=0.25 * T.atr_d)[WKEY + ["close", "u", "e_rd", "e_win"]].drop_duplicates(WKEY)
        if self.done is not None:
            T = T.merge(self.done[WKEY], on=WKEY, how="left", indicator=True)
            T = T[T._merge == "left_only"].drop(columns="_merge")
        if len(T):
            no_locked(T.date.unique())
            W = walk(T)
            self.done = W if self.done is None else pd.concat([self.done, W], ignore_index=True)
        return self.done


def trade_book(cand, walked, k):
    c = cand.drop(columns=[x for x in ("e_rd", "e_win") if x in cand]).merge(
        walked[WKEY + ["r", "kind", "xmin", "r_sigclose", "entry", "e_rd", "e_win"]], on=WKEY, how="left")
    c = c[c.kind >= 0]
    c = c.sort_values(["date", "tod", "pred"], ascending=[True, True, False], kind="mergesort").reset_index(drop=True)
    kept = chassis(c, k, c.xmin.to_numpy())
    return c.iloc[kept].reset_index(drop=True)


def walked_rows(T, walker):
    W = walker.get(T)
    x = T[WKEY].merge(W[WKEY + ["r", "kind", "xmin", "e_rd", "e_win"]], on=WKEY, how="left")
    return x[x.kind >= 0]


SEASON = {}


def full_stats(bk, sessions, spy):
    st = stats(bk, sessions, "r", spy)
    if not len(bk):
        return st
    st["exit_mix_stop_share"] = round(float((bk.kind == 1).mean()), 3)
    st["avg_r_u025"] = round(2 * st["avg_r"], 4)
    a = bk[bk.date < "2025-06-01"]
    bb = bk[(bk.date >= "2025-06-01") & (bk.date <= "2025-09-30")]
    if len(a) or len(bb):
        st["fit_subhalf_A_avg_r"] = round(float(a.r.mean()), 4) if len(a) else None
        st["fit_subhalf_A_trades"] = int(len(a))
        st["fit_subhalf_B_avg_r"] = round(float(bb.r.mean()), 4) if len(bb) else None
        st["fit_subhalf_B_trades"] = int(len(bb))
    st["bias_diag_sigclose_noborrow_nosurcharge_avg_r"] = round(float(bk.r_sigclose.mean()), 4) if "r_sigclose" in bk else None
    st["trades_per_traded_session"] = round(float(bk.groupby("date").size().mean()), 2)
    ew = bk.e_win > 0
    ev = (bk.e_rd > 0)
    st["earn_window_split"] = {nm: {"n": int(len(x)), "avg_r": round(float(x.r.mean()), 4) if len(x) else None,
                                    "total_r": round(float(x.r.sum()), 2)}
                               for nm, x in (("rd_rows", bk[ev]), ("window_rd-1..rd+1", bk[ew]), ("no_window", bk[~ew]))}
    ss = bk.date.map(SEASON).fillna(False).astype(bool)
    st["season_split"] = {nm: {"n": int(len(x)), "avg_r": round(float(x.r.mean()), 4) if len(x) else None,
                               "total_r": round(float(x.r.sum()), 2)} for nm, x in (("season", bk[ss]), ("off", bk[~ss]))}
    return st


def random_control(bk, rows, walker, sessions, spy):
    """same symbol-session-side as the trades: one random eligible row of the universe (seed 1119)."""
    ss = bk[["symbol", "date", "side"]].drop_duplicates()
    rc = rows.merge(ss, on=["symbol", "date", "side"])
    rc = rc.assign(rk=np.random.default_rng(SEED).random(len(rc))).sort_values("rk")
    rc = rc.groupby(["symbol", "date", "side"]).head(1).drop(columns="rk")
    rc = walked_rows(rc[["symbol", "date", "tod", "close", "atr_d", "side", "e_rd", "e_win"]], walker)
    return stats(rc, sessions, "r", spy)


# ------------------------------------------------------------------------------------------------ FIT stage
def load_half(work, half, months):
    metas, Xs, days, nrd = {}, {}, {}, {}
    t0 = time.time()
    with Pool(3) as p:
        for m, meta, X, dd, nr in p.imap_unordered(month_job, [(m, str(work), half) for m in months]):
            metas[m], Xs[m], days[m] = meta, X, dd
            nrd.update(nr)
            print(m, len(meta), int(meta.inALL.sum()), int(meta.inEVT.sum()), f"{time.time() - t0:.0f}s", flush=True)
    for m in months:
        no_locked(days[m])
        no_locked(metas[m].date.unique())
    return metas, Xs, days, nrd


def stage_fit(work):
    t0 = time.time()
    mod = load_mod()
    src = MOD.read_text()
    for c in FORBIDDEN:
        assert f'_col(d, "{c}' not in src and f'_col(df, "{c}' not in src, "forbidden column read by a feature"
    sector_map(work, "fit")
    build_state(work, "fit")
    metas, Xs, days, nrd = load_half(work, "fit", FIT_MONTHS)
    SEASON.update({d: n >= 5 for d, n in nrd.items()})
    cfgs = configs()
    folds = {fm: [m for m in FIT_MONTHS if m < fm] for fm in FOLDS}
    folds["final"] = list(FIT_MONTHS)
    oof_sessions = sorted(sum((days[m] for m in FOLDS), []))
    fit_sessions = sorted(sum((days[m] for m in FIT_MONTHS), []))
    cands = {c: [] for c in cfgs}
    final, insample, train_info = {}, {}, {}
    rng = np.random.default_rng(SEED)
    for univ in ("ALL", "EVT"):
        col = "inALL" if univ == "ALL" else "inEVT"
        for fk, tr in folds.items():
            rows = {m: metas[m][col].to_numpy() for m in metas}
            Xtr = np.vstack([Xs[m][rows[m]] for m in tr])
            ytr = np.concatenate([metas[m].y.to_numpy(np.float64)[rows[m]] for m in tr])
            mid = np.concatenate([np.full(int(rows[m].sum()), i) for i, m in enumerate(tr)])
            mtr = pd.concat([metas[m][rows[m]] for m in tr], ignore_index=True)
            sc = fit_scaler(Xtr)
            Ztr = mod.zscore(Xtr.astype(np.float64), sc)
            del Xtr
            okt = np.isfinite(ytr)
            if univ == "ALL":
                n_tr_s = sum(len(days[m]) for m in tr)
            else:
                n_tr_s = sum(1 for m in tr for d in days[m] if SEASON.get(d))
            if fk != "final":
                Zf = mod.zscore(Xs[fk][rows[fk]].astype(np.float64), sc)
                mf = metas[fk][rows[fk]].reset_index(drop=True)
            for mdl in ("RS", "GB"):
                if mdl == "RS":
                    sm = train_rs(Ztr[okt], ytr[okt], mid[okt])
                    pin = mod.predict_z(Ztr, sm)
                    pf = mod.predict_z(Zf, sm) if fk != "final" else None
                else:
                    sm, est = train_gb(Ztr[okt], ytr[okt], 2000 if univ == "ALL" else 300, rng)
                    assert np.allclose(mod.predict_z(Ztr[:20000], sm), est.predict(Ztr[:20000]), atol=1e-6)
                    pin = est.predict(Ztr)
                    pf = est.predict(Zf) if fk != "final" else None
                for k in (3, 8):
                    cn = [c for c, g in cfgs.items() if g["model"] == mdl and g["k"] == k and g["univ"] == univ][0]
                    cin = collapse(mtr, pin, k)
                    tau = tau_for(cin, k, n_tr_s)
                    if fk == "final":
                        final[cn] = {"model": sm, "tau": tau, **sc}
                        insample[cn] = collapse(mtr, pin, 0).query("pred > @tau")
                        train_info[cn] = {"train_rows": int(okt.sum()), "train_sessions_for_tau": n_tr_s,
                                          "train_mean_y": round(float(ytr[okt].mean()), 4)}
                    else:
                        cf = collapse(mf, pf, 0)
                        cands[cn].append(cf[cf.pred > tau].assign(tau=tau, fold=fk))
                        if mdl == "RS":
                            train_info.setdefault(cn + "_folds", {})[fk] = {"kept": int(sum(sm["kept"])), "tau": round(tau, 4)}
                    print(univ, fk, cn, mdl, k, "tau", round(tau, 4), "n_tr_s", n_tr_s, f"{time.time() - t0:.0f}s", flush=True)
            del Ztr
    walker = Walker()
    spy = spy_types()
    grid, books = {}, {}
    for cn, cfg in cfgs.items():
        c = pd.concat(cands[cn], ignore_index=True)
        W = walker.get(c)
        bk = trade_book(c, W, cfg["k"])
        books[cn] = bk
        st = full_stats(bk, oof_sessions, spy)
        st.update(cfg, candidates_per_session=round(len(c) / len(oof_sessions), 2))
        grid[cn] = st
        print(cn, cfg["label"], st.get("trades_per_session"), st.get("avg_r"), st.get("total_r"), st.get("total_r_wo_best_day"), flush=True)
    elig = {c: g for c, g in grid.items() if g.get("trades_per_session", 0) >= 2.0}
    pool = elig if elig else grid
    order = list(cfgs)
    pick = max(pool, key=lambda c: (pool[c].get("total_r_wo_best_day", -1e9), -order.index(c)))
    pick_task_rule = max(pool, key=lambda c: (pool[c].get("total_r", -1e9), -order.index(c)))
    cfg = cfgs[pick]
    bk = books[pick]
    col = "inALL" if cfg["univ"] == "ALL" else "inEVT"
    urows = pd.concat([metas[m][metas[m][col]] for m in FOLDS], ignore_index=True)
    rand = random_control(bk, urows, walker, oof_sessions, spy)
    ins = insample[pick]
    W = walker.get(ins)
    ins_st = full_stats(trade_book(ins, W, cfg["k"]), fit_sessions, spy)
    fm = final[pick]
    model = {"id": "ULT-31", "config": pick, **cfg, "tau": fm["tau"], "feats": list(mod.FEATS), "mean": fm["mean"],
             "sd": fm["sd"], "model": fm["model"], "trained_on": FIT_MONTHS, "frozen_utc": datetime.now(timezone.utc).isoformat()}
    jdump(model, MODEL_JSON)
    allm = {cn: {"config": cn, **cfgs[cn], "tau": final[cn]["tau"], "mean": final[cn]["mean"], "sd": final[cn]["sd"],
                 "model": final[cn]["model"]} for cn in cfgs}
    jdump(allm, Path(work) / "all_final_models.json")
    jdump(grid, HERE / "fit_grid.json")
    summ = {"kind": fm["model"]["kind"]}
    if fm["model"]["kind"] == "ridge":
        summ["w"] = dict(zip(mod.FEATS, np.round(fm["model"]["w"], 5).tolist()))
        summ["sign_agree"] = dict(zip(mod.FEATS, fm["model"]["sign_agree"]))
    rs_final = {cn: {"kept": [f for f, k in zip(mod.FEATS, final[cn]["model"]["kept"]) if k],
                     "w": dict(zip(mod.FEATS, np.round(final[cn]["model"]["w"], 5).tolist()))}
                for cn in cfgs if cfgs[cn]["model"] == "RS"}
    fitsel = {"id": "ULT-31", "config": pick, **cfg,
              "rule": "round4 PLAN sec.5: highest OOF fit total R minus best fit day among configs >= 2 trades/session",
              "task_rule_pick_fit_total_r": pick_task_rule,
              "reached_2_per_session": bool(elig), "tau": fm["tau"], "oof_fit": grid[pick], "insample_all_fit": ins_st,
              "random_control_oof": rand,
              "signal_minus_random": round(grid[pick]["avg_r"] - rand["avg_r"], 4) if rand.get("trades") else None,
              "train_info": train_info, "model_summary": summ, "rs_final_models": rs_final,
              "season_sessions_fit": int(sum(SEASON.get(d, False) for d in fit_sessions)),
              "sha256": {"bt.py": sha(__file__), "module": sha(MOD), "model_json": sha(MODEL_JSON),
                         "symbols_json": sha(ULT / "modules" / "ULT-31_symbols.json"), "earnings": sha(EARN)},
              "frozen_utc": datetime.now(timezone.utc).isoformat()}
    jdump(fitsel, HERE / "fitsel.json")
    print("PICK", pick, cfg, "task-rule pick", pick_task_rule, f"{time.time() - t0:.0f}s")


# ------------------------------------------------------------------------------------------------ CHECK stage
def check_month_job(args):
    month, work, models = args
    mod = load_mod()
    f = month_frame(month, work, "check")
    b = mod.build(f)
    etb = etb_set()
    isetb_all = f.symbol.isin(etb).to_numpy()
    out = {}
    for nm, model in models.items():
        pl, ps = mod.predict(f, model, b)          # the live module's predict path
        ps = np.where(isetb_all, ps, -np.inf)
        side = np.where(pl >= ps, 1, -1)
        best = np.maximum(pl, ps)
        ok = np.isfinite(best) & (best > float(model["tau"]))
        out[nm] = f.loc[ok, ["symbol", "date", "tod", "close", "atr_d", "e_rd", "e_win"]].assign(
            side=side[ok], pred=best[ok]).reset_index(drop=True)
    meta, _ = month_rows(f, mod, b, etb)
    d50 = f[(f.tod == 1000) & (f.e_rd > 0)]
    nrd = d50.groupby("date").symbol.nunique().to_dict()
    days = sorted(f.date.unique())
    return month, out, meta.drop(columns=[]), days, {d: int(nrd.get(d, 0)) for d in days}


def run_check(work, models):
    ms = check_months()
    res, metas, days = {k: [] for k in models}, [], []
    with Pool(3) as p:
        for m, out, meta, dd, nr in p.imap_unordered(check_month_job, [(m, str(work), models) for m in ms]):
            for k, v in out.items():
                res[k].append(v)
            metas.append(meta); days += dd
            SEASON.update({d: n >= 5 for d, n in nr.items()})
            print(m, {k: len(v) for k, v in out.items()}, flush=True)
    no_locked(days)
    return {k: pd.concat(v, ignore_index=True) for k, v in res.items()}, pd.concat(metas, ignore_index=True), sorted(days)


def stage_check(work):
    fs = json.loads((HERE / "fitsel.json").read_text())
    assert sha(MODEL_JSON) == fs["sha256"]["model_json"], "model changed after the freeze"
    assert sha(MOD) == fs["sha256"]["module"], "module changed after the freeze"
    assert not (HERE / "check_once.json").exists(), "check is scored ONCE"
    sector_map(work, "check")
    build_state(work, "check")
    model = json.loads(MODEL_JSON.read_text())
    res, meta, days = run_check(work, {"pick": model})
    c = res["pick"]
    walker = Walker()
    W = walker.get(c)
    bk = trade_book(c, W, int(fs["k"]))
    spy = spy_types()
    st = full_stats(bk, days, spy)
    col = "inALL" if fs["univ"] == "ALL" else "inEVT"
    rb = random_control(bk, meta[meta[col]], walker, days, spy)
    t_bar = max(1.5, float(np.sqrt(2 * np.log(N_CUM))))
    jdump({"id": "ULT-31", "config": fs["config"], "check": st, "random_control": rb,
           "signal_minus_random": round(st["avg_r"] - rb["avg_r"], 4) if rb.get("trades") else None,
           "candidates_per_session": round(len(c) / len(days), 2), "t_bar": round(t_bar, 3),
           "season_sessions_check": int(sum(SEASON.get(d, False) for d in days)),
           "scored_utc": datetime.now(timezone.utc).isoformat()}, HERE / "check_once.json")
    bk[["symbol", "date", "tod", "side", "pred", "r", "kind", "xmin", "e_rd", "e_win"]].to_csv(HERE / "check_trades.csv.gz", index=False)
    print(json.dumps(st, indent=1))


def stage_plateau(work):
    assert (HERE / "check_once.json").exists(), "plateau only after the single check score"
    allm = json.loads((Path(work) / "all_final_models.json").read_text())
    res, meta, days = run_check(work, allm)
    walker = Walker()
    out = {}
    for cn, c in res.items():
        cfg = allm[cn]
        W = walker.get(c)
        bk = trade_book(c, W, int(cfg["k"]))
        st = stats(bk, days, "r")
        out[cn] = {"label": cfg["label"], **{k: st.get(k) for k in ("trades_per_session", "avg_r", "avg_r_wo_best_day", "total_r",
                                                                  "t_day_clustered", "best_day_share", "long_trades", "long_avg_r",
                                                                  "short_trades", "short_avg_r")}}
        print(cn, out[cn], flush=True)
    jdump(out, HERE / "check_plateau.json")


if __name__ == "__main__":
    Wd = Path(sys.argv[1]); Wd.mkdir(parents=True, exist_ok=True)
    {"fit": stage_fit, "check": stage_check, "plateau": stage_plateau}[sys.argv[2]](Wd)
