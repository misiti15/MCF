"""ULT-21 ETF-RANK backtest (ultimate_1119 round3/PLAN.md sec. 1-2, 3 "ULT-21", 4-7).

Features / eligibility: modules/ULT-21.py raw_features / eligible / predict_z (the SAME code the live module runs) on the
lab frames (research/history2y/data/frames + context), EQB symbols only (modules/ULT-21_universe.json).
Training target (FIT only): after-cost R of TX-45 = decision close -> close of the 1-minute bar ending at tod + 45
(1-minute cache), LR8 market both legs (long only: no borrow), per 2u (u = 0.25 dATR), winsorised +-4.
Models: RG = ridge alpha 1e4 (exact, centred, on z-scored features); GB = HistGradientBoostingRegressor(max_depth 2,
max_iter 100, lr 0.05, min_samples_leaf 2000, l2 1.0, no early stopping, seed 1119), exported to numpy trees (the live
evaluator, checked against sklearn). Walk-forward inside FIT: folds 2025-05..09, train on all earlier FIT months;
"fit" = pooled OOF over the fold months; final model on all FIT frozen in modules/ULT-21_model.json + fitsel.json.
Trading (chassis): pred > tau; <= 3 entries per bar (highest pred first); session cap 2k; one lot per symbol AND one open
lot per exposure group; refire >= 30 min after the exit; max 2 per symbol-session. tau = training in-sample constant
that gives k entries/session through this chassis with approximate exits at entry + 45 min.
Scoring: entry = OPEN of the 1-minute bar starting at the decision close (<= 4 min gap, before 15:50), LR8 entry cost.
  T5 = t05s1 bracket around the decision close (+0.5u limit / -1u stop), 45-min cap, R per u.
  TX = 45-min time exit with a 2u catastrophic stop from the entry, R per 2u.
  Stop first, gap-through at the worse of open/stop, +2c on stops, target at the limit without exit cost, flat 15:50.
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
LOCK = ("2024-11-01", "2025-02-28")
FIT_MONTHS = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 10)]
FOLDS = [f"2025-{m:02d}" for m in range(5, 10)]
MOD = ULT / "modules" / "ULT-21.py"
MODEL_JSON = ULT / "modules" / "ULT-21_model.json"
SEED = 1119
H = 45
N_CUM = 880
TZ = "America/New_York"


def no_locked(dates):
    s = pd.Series([str(x)[:10] for x in dates])
    assert not ((s >= LOCK[0]) & (s <= LOCK[1])).any(), "locked block row found"


def load_mod():
    spec = importlib.util.spec_from_file_location("ult21", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def m2(t):
    t = np.asarray(t, int)
    return (t // 100) * 60 + t % 100


def hhmm(mins):
    mins = np.asarray(mins, int)
    return (mins // 60) * 100 + mins % 60


def check_months():
    import research.history2y.lib as lib
    lib.DATA = DATA
    return [m for m in lib.months() if m >= "2025-10" and m not in lib.LOCKED_MONTHS]


def load_1min(sym, a, b):
    """1-minute bars of sym for dates [a, b] (strings), the locked block filtered out by pyarrow."""
    d = pads.dataset(str(CACHE / f"{sym}.parquet"), format="parquet")
    fld = pads.field("__index_level_0__")
    L0, L1 = pd.Timestamp(LOCK[0], tz=TZ), pd.Timestamp("2025-03-01", tz=TZ)
    t = d.to_table(filter=((fld < L0) | (fld >= L1)) & (fld >= pd.Timestamp(a, tz=TZ))
                   & (fld < pd.Timestamp(b, tz=TZ) + pd.Timedelta(days=1))).to_pandas()
    if "__index_level_0__" in t.columns:
        t = t.set_index("__index_level_0__")
    t.index = pd.DatetimeIndex(t.index).tz_convert(TZ)
    t = t.sort_index()
    no_locked(np.unique(t.index.date))
    return t


def guard_cols(df):
    """Forbidden outcome / heat columns are dropped before any feature is computed (look-ahead guard)."""
    bad = [c for c in df.columns if c.startswith(("win_", "r_long", "r_short")) or "heat" in c.lower()]
    df = df.drop(columns=bad)
    assert not any(c.startswith(("win_", "r_")) or "heat" in c.lower() for c in df.columns)
    return df


# ------------------------------------------------------------------------------------------------ month features
def month_job(args):
    month, want_y = args
    import research.history2y.lib as lib
    lib.DATA = DATA
    mod = load_mod()
    f = lib.load_month(month, context=True)
    f["symbol"] = f["symbol"].astype(str)
    no_locked(f["date"].unique())
    f["date"] = f["date"].astype(str)
    days = sorted(str(x) for x in set(lib.load_context(month)["date"]))
    f = guard_cols(f[f.symbol.isin(sorted(mod.SYMBOLS))]).sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    X = mod.raw_features(f)
    ok = mod.eligible(f)
    sel = np.flatnonzero(ok)
    meta = f.loc[sel, ["symbol", "date", "tod", "close", "atr_d", "adv20"]].reset_index(drop=True)
    meta["grp"] = meta.symbol.map(mod.GROUP)
    if want_y:
        y = np.full(len(meta), np.nan)
        a = month + "-01"
        b = str((pd.Timestamp(a) + pd.offsets.MonthEnd(0)).date())
        for sym, g in meta.groupby("symbol"):
            p = CACHE / f"{sym}.parquet"
            if not p.exists():
                continue
            t = load_1min(sym, a, b)
            mins = t.index.hour * 60 + t.index.minute
            lk = pd.Series(t.close.to_numpy(float), index=pd.MultiIndex.from_arrays([t.index.date.astype(str), mins]))
            lk = lk[~lk.index.duplicated()]
            ex_min = np.minimum(m2(g.tod.to_numpy()) + H - 1, 15 * 60 + 49)
            px = lk.reindex(pd.MultiIndex.from_arrays([g.date.to_numpy(), ex_min])).to_numpy(float)
            e = g.close.to_numpy(float)
            u = 0.25 * g.atr_d.to_numpy(float)
            cost = (0.01 + e * 1e-4) * tod_cost_mult(g.tod.to_numpy()) + 0.01 + px * 1e-4
            y[g.index.to_numpy()] = np.clip((px - e - cost) / (2 * u), -4, 4)
        meta["y"] = y.astype(np.float32)
    return month, meta, X[sel].astype(np.float32), days


def build(months, want_y, procs=3):
    metas, Xs, days = {}, {}, {}
    with Pool(procs) as p:
        for m, meta, X, dd in p.imap_unordered(month_job, [(m, want_y) for m in months]):
            no_locked(meta.date.unique()); no_locked(dd)
            metas[m], Xs[m], days[m] = meta, X, dd
            print(m, len(meta), flush=True)
    return metas, Xs, days


# ------------------------------------------------------------------------------------------------ models
def month_stats(X):
    M = np.isfinite(X)
    X0 = np.where(M, X, 0.0).astype(np.float64)
    return M.sum(0).astype(float), X0.sum(0), (X0 * X0).sum(0)


def scaler_from(stats_list):
    n = sum(s[0] for s in stats_list); s1 = sum(s[1] for s in stats_list); s2 = sum(s[2] for s in stats_list)
    m = s1 / np.maximum(n, 1)
    sd = np.sqrt(np.maximum(s2 / np.maximum(n, 1) - m * m, 1e-12))
    return {"mean": m.tolist(), "sd": sd.tolist()}


def ridge_fit(Z, y, alpha):
    mx, my = Z.mean(0), y.mean()
    Zc = Z - mx
    w = np.linalg.solve(Zc.T @ Zc + alpha * np.eye(Z.shape[1]), Zc.T @ (y - my))
    return {"kind": "ridge", "w": w.tolist(), "b": float(my - mx @ w)}


def gb_fit(Z, y):
    from sklearn.ensemble import HistGradientBoostingRegressor
    est = HistGradientBoostingRegressor(max_depth=2, max_iter=100, learning_rate=0.05, min_samples_leaf=2000,
                                        l2_regularization=1.0, early_stopping=False, random_state=SEED)
    est.fit(Z, y)
    trees = []
    for it in est._predictors:
        nd = it[0].nodes
        trees.append({"f": nd["feature_idx"].astype(int).tolist(), "thr": nd["num_threshold"].astype(float).tolist(),
                      "l": nd["left"].astype(int).tolist(), "r": nd["right"].astype(int).tolist(),
                      "leaf": nd["is_leaf"].astype(bool).tolist(), "v": nd["value"].astype(float).tolist(),
                      "depth": int(nd["depth"].max())})
    return {"kind": "gb", "baseline": float(np.ravel(est._baseline_prediction)[0]), "trees": trees}, est


def configs():
    out, names = {}, iter("abcdefgh")
    for mdl in ("RG", "GB"):
        for k in (2, 4):
            for ex in ("T5", "TX"):
                out["21" + next(names)] = dict(model=mdl, k=k, exit=ex, label=f"{mdl}-k{k}-{ex}")
    return out


# ------------------------------------------------------------------------------------------------ chassis
def chassis(c, k, exit_min, cap_bar=3):
    """c sorted by date, tod, pred desc. One lot per symbol (max 2/symbol-session, refire >= 30 min after the exit),
    one open lot per exposure group, <= cap_bar entries per bar, session cap 2k. Returns kept positions."""
    keep = []
    dt, sy, gr, tt = c.date.to_numpy(), c.symbol.to_numpy(), c.grp.to_numpy(), m2(c.tod.to_numpy())
    cur, state, gbusy, nday, bar_t, nbar = None, {}, {}, 0, -1, 0
    for i in range(len(c)):
        if dt[i] != cur:
            cur, state, gbusy, nday, bar_t, nbar = dt[i], {}, {}, 0, -1, 0
        if nday >= 2 * k:
            continue
        if tt[i] != bar_t:
            bar_t, nbar = tt[i], 0
        if nbar >= cap_bar:
            continue
        n, free = state.get(sy[i], (0, -1))
        if n >= 2 or tt[i] < free or tt[i] < gbusy.get(gr[i], -1):
            continue
        keep.append(i)
        state[sy[i]] = (n + 1, exit_min[i] + 30)
        gbusy[gr[i]] = exit_min[i]
        nday += 1; nbar += 1
    return np.asarray(keep, int)


def calibrate_tau(meta, pred, k, n_sessions):
    c = pd.DataFrame({"date": meta.date.to_numpy(), "symbol": meta.symbol.to_numpy(), "grp": meta.grp.to_numpy(),
                      "tod": meta.tod.to_numpy(), "pred": pred})
    c = c.sort_values("pred", ascending=False).groupby("date").head(40 * k)
    c = c.sort_values(["date", "tod", "pred"], ascending=[True, True, False], kind="mergesort").reset_index(drop=True)
    ex = m2(c.tod.to_numpy()) + H
    pv = c.pred.to_numpy()
    lo, hi = float(np.min(pv)), float(np.max(pv))
    for _ in range(30):
        mid = (lo + hi) / 2
        s = pv > mid
        n = len(chassis(c[s], k, ex[s])) / n_sessions
        if n > k:
            lo = mid
        else:
            hi = mid
    return hi


# ------------------------------------------------------------------------------------------------ 1-minute walk
def walk_job(args):
    sym, T = args
    ds_ = sorted(T.date.unique())
    b = load_1min(sym, ds_[0], ds_[-1])
    hm_all = (b.index.hour * 100 + b.index.minute).to_numpy()
    day = b.index.date.astype(str)
    O, Hh, Lo, Cc = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    byday = {}
    if len(day):
        st = np.flatnonzero(np.r_[True, day[1:] != day[:-1]])
        en = np.r_[st[1:], len(day)]
        byday = {day[a]: np.arange(a, e) for a, e in zip(st, en)}
    res = []
    for r in T.itertuples():
        ix = byday.get(r.date)
        nan = (r.Index,) + (np.nan,) * 9
        if ix is None:
            res.append(nan); continue
        hm = hm_all[ix]
        j0 = np.searchsorted(hm, r.tod)
        if j0 >= len(ix) or m2(hm[j0]) - m2(r.tod) > 4 or hm[j0] >= 1550:
            res.append(nan); continue
        e = O[ix[j0]]
        dc = r.close
        u = r.u
        tend = min(int(hhmm(m2(hm[j0]) + H - 1)), 1549)
        path = ix[j0:][hm_all[ix[j0:]] <= tend]
        mult = float(tod_cost_mult(np.array([r.tod]))[0])
        # T5: bracket around the decision close
        stop, tgt = dc - u, dc + 0.5 * u
        px5, k5, x5 = None, 0, None
        for q in path:
            if Lo[q] <= stop:
                px5, k5, x5 = min(O[q], stop), 1, hm_all[q]; break
            if Hh[q] >= tgt:
                px5, k5, x5 = tgt, 2, hm_all[q]; break
            px5, x5 = Cc[q], hm_all[q]
        # TX: 2u catastrophic stop from the entry, time exit
        out = []
        for e_ in (e, dc):
            cst = e_ - 2 * u
            pxt, kt, xt = None, 0, None
            for q in path:
                if Lo[q] <= cst:
                    pxt, kt, xt = min(O[q], cst), 1, hm_all[q]; break
                pxt, xt = Cc[q], hm_all[q]
            out.append((pxt, kt, xt))
        (pxt, kt, xt), (pxb, kb, _) = out

        def rr(e_, px, kd, unit):
            ec = (0.01 + e_ * 1e-4) * mult
            xc = (0.0 if kd == 2 else 0.01 + px * 1e-4) + (0.02 if kd == 1 else 0.0)
            return (px - e_ - ec - xc) / unit
        r5, r5b = rr(e, px5, k5, u), rr(dc, px5, k5, u)
        rt, rtb = rr(e, pxt, kt, 2 * u), rr(dc, pxb, kb, 2 * u)
        res.append((r.Index, r5, k5, m2(x5) + 1, r5b, rt, kt, m2(xt) + 1, rtb, e))
    return res


WCOLS = ["r_T5", "kind_T5", "xmin_T5", "rsc_T5", "r_TX", "kind_TX", "xmin_TX", "rsc_TX", "entry"]
WKEY = ["symbol", "date", "tod"]


class Walker:
    def __init__(self):
        self.done = None

    def get(self, T):
        T = T[WKEY + ["close", "atr_d"]].drop_duplicates(WKEY)
        if self.done is not None:
            T = T.merge(self.done[WKEY], on=WKEY, how="left", indicator=True)
            T = T[T._merge == "left_only"].drop(columns="_merge")
        if len(T):
            no_locked(T.date.unique())
            T = T.reset_index(drop=True)
            T["u"] = 0.25 * T.atr_d
            jobs = [(s, g) for s, g in T.groupby("symbol") if (CACHE / f"{s}.parquet").exists()]
            with Pool(3) as p:
                out = [x for r in p.imap_unordered(walk_job, jobs, chunksize=2) for x in r]
            a = pd.DataFrame(out, columns=["i"] + WCOLS).set_index("i")
            W = T.join(a)[WKEY + WCOLS]
            self.done = W if self.done is None else pd.concat([self.done, W], ignore_index=True)
        return self.done


def trade_book(cand, walked, k, ex):
    c = cand.merge(walked, on=WKEY, how="left")
    c = c[c[f"r_{ex}"].notna()].copy()
    c["r"], c["kind"], c["xmin"], c["r_sigclose"] = c[f"r_{ex}"], c[f"kind_{ex}"], c[f"xmin_{ex}"], c[f"rsc_{ex}"]
    c = c.sort_values(["date", "tod", "pred"], ascending=[True, True, False], kind="mergesort").reset_index(drop=True)
    kept = chassis(c, k, c.xmin.to_numpy())
    return c.iloc[kept].reset_index(drop=True)


# ------------------------------------------------------------------------------------------------ statistics
_SPY = {}


def spy_types():
    if "s" not in _SPY:
        sys.path.insert(0, str(ULT / "benchmark"))
        from stats import spy_days
        _SPY["s"] = spy_days()["type"]
    return _SPY["s"]


def stats(t, sessions, col="r"):
    t = t[t[col].notna()]
    n_s = len(sessions)
    if not len(t):
        return {"trades": 0, "sessions": n_s, "trades_per_session": 0.0}
    day = t.groupby("date")[col].sum()
    tot = float(t[col].sum())
    avg = tot / len(t)
    best = day.idxmax()
    dev = (t[col] - avg).groupby(t.date).sum()
    se = float(np.sqrt((dev ** 2).sum())) / len(t)
    tps = len(t) / day.size
    o = {"trades": int(len(t)), "sessions": n_s, "sessions_traded": int(day.size), "trades_per_session": round(len(t) / n_s, 3),
         "win": round(float((t[col] > 0).mean()), 3), "avg_r": round(avg, 4),
         "avg_r_wo_best_day": round(float(t.loc[t.date != best, col].mean()), 4) if (t.date != best).any() else None,
         "best_day": str(best), "best_day_r": round(float(day.max()), 2),
         "best_day_share": round(float(day.max()) / tot, 3) if tot > 0 else None, "total_r": round(tot, 2),
         "total_r_wo_best_day": round(tot - float(day.max()), 2), "total_r_per_session": round(tot / n_s, 4),
         "worst_day": round(float(day.min()), 2), "worst_day_per_trade_session": round(float(day.min()) / tps, 3),
         "t_day_clustered": round(avg / se, 3) if se > 0 else None}
    ex = t[(t.date < "2025-04-03") | (t.date > "2025-04-09")]
    o["avg_r_ex_0403_0409"] = round(float(ex[col].mean()), 4) if len(ex) else None
    o["n_ex_0403_0409"] = int(len(ex))
    ty = t.date.map(spy_types())
    for nm in ("up", "flat", "down"):
        x = t.loc[ty == nm, col]
        o[f"avg_r_spy_{nm}"] = round(float(x.mean()), 4) if len(x) else None
        o[f"n_spy_{nm}"] = int(len(x))
    if "xmin" in t:
        o["median_hold_min"] = float(np.median(t.xmin - m2(t.tod)))
    if "kind" in t:
        o["exit_mix"] = {str(k): int(v) for k, v in t.kind.map({0: "time", 1: "stop", 2: "target"}).value_counts().items()}
    if "symbol" in t:
        inv = set(json.loads((ULT / "modules" / "ULT-21_universe.json").read_text())["inverse"])
        x = t[t.symbol.isin(inv)]
        o["inverse_trades"], o["inverse_avg_r"] = int(len(x)), (round(float(x[col].mean()), 4) if len(x) else None)
        o["top_symbols"] = {s: int(v) for s, v in t.symbol.value_counts().head(8).items()}
    ss = sorted(sessions)
    mid = ss[len(ss) // 2]
    o["first_half_avg_r"] = round(float(t.loc[t.date < mid, col].mean()), 4) if (t.date < mid).any() else None
    o["second_half_avg_r"] = round(float(t.loc[t.date >= mid, col].mean()), 4) if (t.date >= mid).any() else None
    a, b = t[t.date < "2025-06-01"], t[(t.date >= "2025-06-01") & (t.date <= "2025-09-30")]
    if len(a) and len(b) and t.date.max() <= "2025-09-30":
        o["fitA_avg_r"], o["fitA_n"] = round(float(a[col].mean()), 4), int(len(a))
        o["fitB_avg_r"], o["fitB_n"] = round(float(b[col].mean()), 4), int(len(b))
    return o


def rand_control(book, meta, walker, ex, seed):
    """Same symbol-sessions as the trades; one random eligible decision bar each; same exit."""
    rng = np.random.default_rng(seed)
    m = meta[["symbol", "date", "tod", "close", "atr_d"]].merge(book[["symbol", "date"]].drop_duplicates(), on=["symbol", "date"])
    m["rk"] = rng.random(len(m))
    rc = m.sort_values("rk").groupby(["symbol", "date"]).head(1).drop(columns="rk")
    W = walker.get(rc)
    rc = rc.merge(W, on=WKEY, how="left")
    rc["r"], rc["kind"], rc["xmin"] = rc[f"r_{ex}"], rc[f"kind_{ex}"], rc[f"xmin_{ex}"]
    return rc[rc.r.notna()]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def jdump(o, p):
    Path(p).write_text(json.dumps(o, indent=1, default=lambda x: x.item() if hasattr(x, "item") else str(x)))


def predict(mod, Z, mdl):
    return mod.predict_z(Z, mdl)


# ------------------------------------------------------------------------------------------------ FIT stage
def stage_fit(work):
    t0 = time.time()
    mod = load_mod()
    src = MOD.read_text()
    assert not any(f'"{c}' in src for c in ("win_", "r_long", "r_short")) and "heat" not in src.lower(), "forbidden column"
    metas, Xs, days = build(FIT_MONTHS, True)
    for m in FIT_MONTHS:
        no_locked(days[m])
    mstats = {m: month_stats(Xs[m]) for m in FIT_MONTHS}
    cfgs = configs()
    folds = {fm: [m for m in FIT_MONTHS if m < fm] for fm in FOLDS}
    folds["final"] = list(FIT_MONTHS)
    walker = Walker()
    oof_sessions = sorted(sum((days[m] for m in FOLDS), []))
    fit_sessions = sorted(sum((days[m] for m in FIT_MONTHS), []))
    cands = {c: [] for c in cfgs}
    final_models, final_tau, insample, scalers = {}, {}, {}, {}
    for fk, train in folds.items():
        sc = scaler_from([mstats[m] for m in train])
        Zm = {m: mod.zscore(Xs[m].astype(np.float64), sc) for m in (train + ([fk] if fk != "final" else []))}
        okm = {m: np.isfinite(metas[m].y.to_numpy()) for m in train}
        Ztr = np.vstack([Zm[m][okm[m]] for m in train])
        ytr = np.concatenate([metas[m].y.to_numpy(np.float64)[okm[m]] for m in train])
        models = {"RG": ridge_fit(Ztr, ytr, 1e4)}
        g, est = gb_fit(Ztr, ytr)
        chk = Ztr[:20000]
        assert np.allclose(mod.predict_z(chk, g), est.predict(chk), atol=1e-6), "numpy tree evaluator != sklearn"
        models["GB"] = g
        print(fk, "trained on", len(ytr), f"{time.time() - t0:.0f}s", flush=True)
        n_train_sessions = sum(len(days[m]) for m in train)
        tmeta = pd.concat([metas[m] for m in train], ignore_index=True)
        Zall = np.vstack([Zm[m] for m in train])
        for cn, cfg in cfgs.items():
            mdl, k = cfg["model"], cfg["k"]
            ptr = predict(mod, Zall, models[mdl])
            tau = calibrate_tau(tmeta, ptr, k, n_train_sessions)
            if fk == "final":
                final_tau[cn], final_models[cn], scalers[cn] = tau, models[mdl], sc
                ok = ptr > tau
                insample[cn] = tmeta.loc[ok, ["symbol", "grp", "date", "tod", "close", "atr_d"]].assign(pred=ptr[ok])
            else:
                mt = metas[fk]
                p = predict(mod, Zm[fk], models[mdl])
                ok = p > tau
                cands[cn].append(mt.loc[ok, ["symbol", "grp", "date", "tod", "close", "atr_d"]].assign(pred=p[ok], tau=tau, fold=fk))
            print(fk, cn, cfg["label"], "tau", round(tau, 4), flush=True)
        if fk == "final":
            imp = {"RG_w": dict(zip(mod.FEATS, np.round(models["RG"]["w"], 4)))}
        del Zm, Ztr, Zall
    grid, books = {}, {}
    for cn, cfg in cfgs.items():
        c = pd.concat(cands[cn], ignore_index=True)
        W = walker.get(c)
        bk = trade_book(c, W, cfg["k"], cfg["exit"])
        books[cn] = bk
        st = stats(bk, oof_sessions)
        st.update(cfg, candidates_per_session=round(len(c) / len(oof_sessions), 2))
        grid[cn] = st
        print(cn, cfg["label"], st["trades_per_session"], st["avg_r"], st["total_r"], st.get("total_r_wo_best_day"), flush=True)
    elig = {c: g for c, g in grid.items() if g.get("trades_per_session", 0) >= 2.0}
    pool = elig if elig else grid
    order = list(cfgs)
    pick = max(pool, key=lambda c: (pool[c].get("total_r_wo_best_day", -1e9), -order.index(c)))
    cfg = cfgs[pick]
    bk = books[pick]
    diag = stats(bk.assign(r=bk.r_sigclose), oof_sessions)
    allmeta = pd.concat([metas[m] for m in FOLDS], ignore_index=True)
    rc = rand_control(bk, allmeta, walker, cfg["exit"], SEED)
    rand = stats(rc, oof_sessions)
    ins = insample[pick]
    W = walker.get(ins)
    ins_st = stats(trade_book(ins, W, cfg["k"], cfg["exit"]), fit_sessions)
    # base rate: every eligible OOF bar (no ranker), TX-45 proxy target (pre-chassis, decision-close entry)
    base_y = float(np.nanmean(allmeta.y))
    model = {"id": "ULT-21", "config": pick, **cfg, "tau": final_tau[pick], "h": H, "feats": mod.FEATS,
             **scalers[pick], "model": final_models[pick], "trained_on": FIT_MONTHS,
             "frozen_utc": datetime.now(timezone.utc).isoformat()}
    jdump(model, MODEL_JSON)
    allm = {cn: {"config": cn, **cfgs[cn], "tau": final_tau[cn], **scalers[cn], "model": final_models[cn]} for cn in cfgs}
    jdump(allm, Path(work) / "all_final_models.json")
    jdump(grid, HERE / "fit_grid.json")
    fitsel = {"id": "ULT-21", "note": "Educational only - not financial advice. Frozen BEFORE any check frame is built.",
              "config": pick, **cfg,
              "rule": "round3 PLAN sec.5: highest OOF fit total R minus best fit day among configs >= 2 trades/session",
              "eligible_2_per_session": sorted(elig), "tau": final_tau[pick], "oof_fit": grid[pick],
              "insample_all_fit": ins_st, "random_control_oof": rand,
              "signal_minus_random_oof": round(grid[pick]["avg_r"] - rand.get("avg_r", np.nan), 4),
              "bias_diag_oof_sigclose": diag, "base_rate_oof_tx45_proxy": round(base_y, 4),
              "final_ridge_weights": imp, "configs_counted_this_candidate": 8 + 1, "n_cumulative": N_CUM,
              "sha256": {"bt.py": sha(__file__), "module": sha(MOD), "model_json": sha(MODEL_JSON),
                         "universe": sha(ULT / "modules" / "ULT-21_universe.json")},
              "frozen_utc": datetime.now(timezone.utc).isoformat()}
    jdump(fitsel, HERE / "fitsel.json")
    print("PICK", pick, cfg, f"{time.time() - t0:.0f}s")


# ------------------------------------------------------------------------------------------------ CHECK stage
def check_cands(work, models):
    mod = load_mod()
    metas, Xs, days = build(check_months(), False)
    alld = sorted(sum(days.values(), []))
    no_locked(alld)
    meta = pd.concat([metas[m] for m in sorted(metas)], ignore_index=True)
    X = np.vstack([Xs[m] for m in sorted(metas)]).astype(np.float64)
    out = {}
    for nm, model in models.items():
        p = mod.predict_z(mod.zscore(X, model), model["model"])
        ok = p > float(model["tau"])
        out[nm] = meta.loc[ok, ["symbol", "grp", "date", "tod", "close", "atr_d"]].assign(pred=p[ok]).reset_index(drop=True)
    return out, meta, alld


def stage_check(work):
    fs = json.loads((HERE / "fitsel.json").read_text())
    assert sha(MODEL_JSON) == fs["sha256"]["model_json"], "model changed after the freeze"
    assert sha(MOD) == fs["sha256"]["module"], "module changed after the freeze"
    assert not (HERE / "check_once.json").exists(), "check is scored ONCE"
    model = json.loads(MODEL_JSON.read_text())
    res, meta, days = check_cands(work, {"pick": model})
    c = res["pick"]
    walker = Walker()
    W = walker.get(c)
    bk = trade_book(c, W, int(fs["k"]), fs["exit"])
    st = stats(bk, days)
    diag = stats(bk.assign(r=bk.r_sigclose), days)
    rc = rand_control(bk, meta, walker, fs["exit"], SEED + 1)
    rand = stats(rc, days)
    z = max(1.5, float(np.sqrt(2 * np.log(N_CUM))))
    fit = fs["oof_fit"]
    tierA = bool(st["avg_r"] > 0 and (st["avg_r_wo_best_day"] or -1) > 0 and fit["avg_r"] > 0 and st["trades_per_session"] >= 2.0)
    beats = bool(tierA and st["avg_r"] > 0.0836 and st["avg_r_wo_best_day"] > 0.0734 and st["total_r_per_session"] > 0
                 and st["worst_day_per_trade_session"] >= -2.152 and (st["t_day_clustered"] or 0) >= z)
    tierB = bool(fit["avg_r"] > 0 and st["avg_r"] > -0.02)
    jdump({"id": "ULT-21", "config": fs["config"], "label": fs["label"], "check": st, "random_control": rand,
           "signal_minus_random": round(st["avg_r"] - rand.get("avg_r", np.nan), 4), "bias_diag_sigclose": diag,
           "candidates_per_session": round(len(c) / len(days), 2), "t_bar": round(z, 3),
           "tier": "BEATS" if beats else ("A" if tierA else ("B" if tierB else "FAIL")),
           "scored_utc": datetime.now(timezone.utc).isoformat()}, HERE / "check_once.json")
    bk[["symbol", "date", "tod", "pred", "r", "kind", "xmin"]].to_csv(HERE / "check_trades.csv.gz", index=False)
    print(json.dumps(st, indent=1))


def stage_plateau(work):
    assert (HERE / "check_once.json").exists(), "plateau only after the single check score"
    allm = json.loads((Path(work) / "all_final_models.json").read_text())
    res, meta, days = check_cands(work, allm)
    walker = Walker()
    out = {}
    for cn, c in res.items():
        cfg = allm[cn]
        W = walker.get(c)
        st = stats(trade_book(c, W, int(cfg["k"]), cfg["exit"]), days)
        out[cn] = {"label": cfg["label"], **{k: st.get(k) for k in ("trades_per_session", "avg_r", "avg_r_wo_best_day", "total_r",
                                                                  "t_day_clustered", "best_day_share", "worst_day_per_trade_session",
                                                                  "first_half_avg_r", "second_half_avg_r")}}
        print(cn, out[cn], flush=True)
    jdump(out, HERE / "check_plateau.json")


if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True)
    {"fit": stage_fit, "check": stage_check, "plateau": stage_plateau}[sys.argv[2]](W)
