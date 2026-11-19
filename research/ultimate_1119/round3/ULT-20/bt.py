"""ULT-20 EVR - event-conditioned learned ranker backtest (ultimate_1119 round3/PLAN.md sec. 3 "ULT-20", sec. 5-7).

Reuses the round-2 ULT-11 pipeline (round2/ULT-11/bt.py: sector map, chassis, tau calibration, ridge / GB export, stats,
random table) and the live module modules/ULT-20.py (build / side_rows / side_features / predict: the SAME code the live
module runs). Only additions here: sec_atrp in the month frame (for the E5 sector-lag event), the round-3 borrow tier
(1.2 bp of entry notional, 3 bp when the entry is < $20), an L2-logistic model, event-row random control.
Rows: (bar, name, side) with >= 1 event of that side, intake L2 (ADV20 >= $50M, cost_r <= 0.08); L1 rows (ADV20 >= $100M,
cost_r <= 0.05) are a subset flagged per row. Shorts: easy_to_borrow (universe.csv, today's flag), never LEV funds.
Target (training proxy, FIT only): after-cost R per 2u of decision close -> 5-min close at tod + 45 (frames + headtail),
LR8 both legs + borrow tier on shorts, winsorised +-4. Models: RG ridge a=1e3 (exact, all rows); LG L2-logistic C=0.01 on
1[target > 0] (score = logit); GB HistGBR(depth 2, 100 it, lr .05, leaf 2000, l2 1, seed 1119, no early stopping).
One pooled model for both sides. Walk-forward folds 2025-05..09 inside FIT (train on all earlier FIT months); "fit" = OOF.
Trading: best side per name-bar; score > tau_k; <= 3 per bar; session cap 2k; one lot per symbol; refire >= 30 min after
exit; max 2 per symbol-session; tau_k = in-sample threshold giving k entries/session on the training months.
Scoring: entry = OPEN of the 1-minute bar starting at the decision close; 2u catastrophic stop; time exit at the close of
minute entry + 44 (flat 15:50); LR8 (entry (1c+1bp) x tod mult; exit 1c+1bp; +2c on stops) + borrow tier. R per 2u.
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
no_locked, m2, chassis, calibrate_tau, scaler_from_unused = B11.no_locked, B11.m2, B11.chassis, B11.calibrate_tau, None
ridge_fit, gb_export, stats, spy_types, sha, jdump, guard_cols = (B11.ridge_fit, B11.gb_export, B11.stats, B11.spy_types,
                                                                  B11.sha, B11.jdump, B11.guard_cols)
sector_map, check_months, ETFS = B11.sector_map, B11.check_months, B11.ETFS
FIT_MONTHS = B11.FIT_MONTHS
FOLDS = B11.FOLDS
MOD = ULT / "modules" / "ULT-20.py"
MODEL_JSON = ULT / "modules" / "ULT-20_model.json"
SEED = 1119
H = 45
FORBIDDEN = ("win_", "r_long", "r_short", "heat", "Heat")


def borrow(side, e):
    return np.where(side < 0, np.where(e < 20, 3e-4, 1.2e-4) * e, 0.0)


def load_mod():
    spec = importlib.util.spec_from_file_location("ult20", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def configs():
    out, names = {}, iter("abcdefghijkl")
    for mdl in ("RG", "LG", "GB"):
        for k in (4, 10):
            for u in ("L1", "L2"):
                out["20" + next(names)] = dict(model=mdl, k=k, univ=u, h=H, label=f"{mdl}-k{k}-{u}")
    return out


# ------------------------------------------------------------------------------------------------ month frames
def month_frame(month, work):
    """ULT-11 month frame + sec_atrp (sector ETF 100 x atr_d / close at the same bar) for the E5 event."""
    import research.history2y.lib as lib
    lib.DATA = DATA
    f = lib.load_month(month, context=True)
    f["symbol"] = f["symbol"].astype(str)
    no_locked(f["date"].unique())
    f["date"] = f["date"].astype(str)
    half = "fit" if month in FIT_MONTHS else "check"
    sm = pd.read_parquet(Path(work) / f"secmap_{half}.parquet", filters=[("date", ">=", month + "-01"), ("date", "<=", month + "-31")])
    e = f[f.symbol.isin(ETFS)][["symbol", "date", "tod", "fromOpen", "atr_d", "close"]].copy()
    e["sec_atrp"] = 100 * e.atr_d / e.close
    e = e.rename(columns={"symbol": "sec", "fromOpen": "sec_fo"})[["sec", "date", "tod", "sec_fo", "sec_atrp"]]
    f = f.merge(sm, on=["symbol", "date"], how="left").merge(e, on=["sec", "date", "tod"], how="left")
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    return guard_cols(f)


def etb_set():
    u = pd.read_csv(UNIV)
    return set(u.loc[u.easy_to_borrow.astype(str).str.lower() == "true", "symbol"].astype(str))


def rand_pick(df, rng):
    """one random row per (symbol, date, side)"""
    df = df.assign(rk=rng.random(len(df)))
    return df.sort_values("rk").groupby(["symbol", "date", "side"]).head(1).drop(columns="rk")


def month_rows(f, mod, b, etb):
    """Event rows (L2 intake) for both sides + base rows for random control. Positions are into f."""
    sel = b["sel"]
    isetb = f.symbol.to_numpy()[sel]
    isetb = np.array([s in etb for s in isetb])
    out, base_rows = [], []
    for sgn in (1, -1):
        r2 = mod.side_rows(b, sgn, "L2")
        r1 = mod.side_rows(b, sgn, "L1")
        bo2 = mod.univ_ok(b, "L2") & (b["long_ok"] if sgn > 0 else b["short_ok"])
        bo1 = mod.univ_ok(b, "L1") & (b["long_ok"] if sgn > 0 else b["short_ok"])
        if sgn < 0:
            r2, r1, bo2, bo1 = r2 & isetb, r1 & isetb, bo2 & isetb, bo1 & isetb
        X = mod.side_features(b, sgn)
        pos = sel[r2]
        m = f.iloc[pos][["symbol", "date", "tod", "close", "atr_d"]].reset_index(drop=True)
        m["side"], m["inL1"], m["pos"] = sgn, r1[r2], pos
        out.append((m, X[r2].astype(np.float32)))
        bp = sel[bo2]
        bm = f.iloc[bp][["symbol", "date", "tod", "close", "atr_d"]].reset_index(drop=True)
        bm["side"], bm["inL1"] = sgn, bo1[bo2]
        base_rows.append(bm)
    meta = pd.concat([o[0] for o in out], ignore_index=True)
    X = np.vstack([o[1] for o in out])
    return meta, X, pd.concat(base_rows, ignore_index=True)


def month_job(args):
    month, work = args
    mod = load_mod()
    f = month_frame(month, work)
    assert not any(c.startswith(("win_", "r_long", "r_short")) or "heat" in c.lower() for c in f.columns)
    b = mod.build(f)
    meta, X, base = month_rows(f, mod, b, etb_set())
    # training target: TX-45 to the 5-min close at tod + 45 (frames + headtail rows after 15:00)
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
    mult = tod_cost_mult(meta.tod.to_numpy())
    cost = (0.01 + e * 1e-4) * mult + 0.01 + px * 1e-4 + borrow(s, e)
    with np.errstate(invalid="ignore", divide="ignore"):
        meta["y"] = np.clip((s * (px - e) - cost) / (2 * u), -4, 4).astype(np.float32)
    rng = np.random.default_rng(SEED + int(month.replace("-", "")))
    rb2 = rand_pick(base, rng)
    rb1 = rand_pick(base[base.inL1], rng)
    days = sorted(f.date.unique())
    return month, meta.drop(columns="pos"), X, {"L2": rb2, "L1": rb1}, days


# ------------------------------------------------------------------------------------------------ models
def fit_scaler(X):
    with np.errstate(invalid="ignore"):
        m = np.nanmean(X.astype(np.float64), 0)
        sd = np.nanstd(X.astype(np.float64), 0)
    m = np.nan_to_num(m)
    sd = np.where(np.isfinite(sd) & (sd > 1e-9), sd, 1.0)
    return {"mean": m.tolist(), "sd": sd.tolist()}


def train(mdl, Z, y):
    if mdl == "RG":
        acc = (len(y), Z.sum(0), y.sum(), Z.T @ Z, Z.T @ y)
        return ridge_fit(acc, 1e3), None
    if mdl == "LG":
        from sklearn.linear_model import LogisticRegression
        est = LogisticRegression(C=0.01, max_iter=1000)
        est.fit(Z, (y > 0).astype(int))
        return {"kind": "linear", "w": est.coef_[0].tolist(), "b": float(est.intercept_[0])}, est
    from sklearn.ensemble import HistGradientBoostingRegressor
    est = HistGradientBoostingRegressor(max_depth=2, max_iter=100, learning_rate=0.05, min_samples_leaf=2000,
                                        l2_regularization=1.0, early_stopping=False, random_state=SEED)
    est.fit(Z, y)
    return gb_export(est), est


def collapse(meta, pred):
    """best side per (symbol, date, tod): rows sorted by pred desc, first kept."""
    c = meta[["symbol", "date", "tod", "close", "atr_d", "side"]].assign(pred=pred)
    c = c[np.isfinite(c.pred)]
    c = c.sort_values("pred", ascending=False, kind="mergesort").drop_duplicates(["symbol", "date", "tod"])
    return c


def tau_for(c, k, n_sessions):
    """ULT-11 calibrate_tau on collapsed rows (one row per name-bar)."""
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
    day = np.array([str(x) for x in b.index.date])
    O, Hh, L, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
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
                if (s > 0 and L[kk] <= stop) or (s < 0 and Hh[kk] >= stop):
                    px = min(O[kk], stop) if s > 0 else max(O[kk], stop)
                    kd, xt = 1, m2(hhmm[kk]) + 1; break
            if px is None:
                px, kd, xt = C[sel[-1]], 0, m2(hhmm[sel[-1]]) + 1
            outs.append((e, px, kd, xt))
        (eA, pA, kA, xA), (eB, pB, kB, _) = outs
        mult = float(tod_cost_mult(np.array([r.tod]))[0])
        bf = float(borrow(np.array([s]), np.array([eA]))[0])
        rA = (s * (pA - eA) - ((0.01 + eA * 1e-4) * mult + 0.01 + pA * 1e-4 + 0.02 * (kA == 1) + bf)) / (2 * u)
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
    def __init__(self):
        self.done = None

    def get(self, T):
        T = T.assign(h=H, u=0.25 * T.atr_d)[WKEY + ["close", "u"]].drop_duplicates(WKEY)
        if self.done is not None:
            T = T.merge(self.done[WKEY], on=WKEY, how="left", indicator=True)
            T = T[T._merge == "left_only"].drop(columns="_merge")
        if len(T):
            no_locked(T.date.unique())
            W = walk(T)
            self.done = W if self.done is None else pd.concat([self.done, W], ignore_index=True)
        return self.done


def trade_book(cand, walked, k):
    c = cand.assign(h=H).merge(walked[WKEY + ["r", "kind", "xmin", "r_sigclose", "entry"]], on=WKEY, how="left")
    c = c[c.kind >= 0]
    c = c.sort_values(["date", "tod", "pred"], ascending=[True, True, False], kind="mergesort").reset_index(drop=True)
    kept = chassis(c, k, c.xmin.to_numpy())
    return c.iloc[kept].reset_index(drop=True)


def walked_rows(T, walker):
    W = walker.get(T)
    x = T.assign(h=H).merge(W[WKEY + ["r", "kind", "xmin"]], on=WKEY, how="left")
    return x[x.kind >= 0]


def full_stats(bk, sessions, spy):
    st = stats(bk, sessions, "r", spy)
    if len(bk):
        st["exit_mix_stop_share"] = round(float((bk.kind == 1).mean()), 3)
        st["avg_r_per_u"] = round(2 * st["avg_r"], 4)
        a = bk[(bk.date < "2025-06-01")]
        bb = bk[(bk.date >= "2025-06-01") & (bk.date <= "2025-09-30")]
        st["fit_subhalf_A_avg_r"] = round(float(a.r.mean()), 4) if len(a) else None
        st["fit_subhalf_A_trades"] = int(len(a))
        st["fit_subhalf_B_avg_r"] = round(float(bb.r.mean()), 4) if len(bb) else None
        st["fit_subhalf_B_trades"] = int(len(bb))
        st["bias_diag_sigclose_noborrow_avg_r"] = round(float(bk.r_sigclose.mean()), 4) if "r_sigclose" in bk else None
        ev = bk.groupby("date").size()
        st["trades_per_traded_session"] = round(float(ev.mean()), 2)
    return st


def random_control(bk, rt, walker, sessions, spy):
    ss = bk[["symbol", "date", "side"]].drop_duplicates()
    rc = rt.merge(ss, on=["symbol", "date", "side"])
    rc = walked_rows(rc[["symbol", "date", "tod", "close", "atr_d", "side"]], walker)
    return stats(rc, sessions, "r", spy)


# ------------------------------------------------------------------------------------------------ FIT stage
def stage_fit(work):
    t0 = time.time()
    mod = load_mod()
    src = MOD.read_text()
    assert not any(f'_col(d, "{c}' in src for c in FORBIDDEN), "forbidden column read by a feature"
    sector_map(work, "fit")
    metas, Xs, rts, days = {}, {}, {}, {}
    with Pool(3) as p:
        for m, meta, X, rt, dd in p.imap_unordered(month_job, [(m, str(work)) for m in FIT_MONTHS]):
            metas[m], Xs[m], rts[m], days[m] = meta, X, rt, dd
            print(m, len(meta), int(meta.inL1.sum()), f"{time.time() - t0:.0f}s", flush=True)
    for m in FIT_MONTHS:
        no_locked(days[m])
    cfgs = configs()
    folds = {fm: [m for m in FIT_MONTHS if m < fm] for fm in FOLDS}
    folds["final"] = list(FIT_MONTHS)
    oof_sessions = sorted(sum((days[m] for m in FOLDS), []))
    fit_sessions = sorted(sum((days[m] for m in FIT_MONTHS), []))
    cands = {c: [] for c in cfgs}
    final, insample, scalers, train_stats = {}, {}, {}, {}
    for univ in ("L1", "L2"):
        for fk, tr in folds.items():
            rows = {m: (metas[m].inL1.to_numpy() if univ == "L1" else np.ones(len(metas[m]), bool)) for m in metas}
            Xtr = np.vstack([Xs[m][rows[m]] for m in tr])
            ytr = np.concatenate([metas[m].y.to_numpy(np.float64)[rows[m]] for m in tr])
            mtr = pd.concat([metas[m][rows[m]] for m in tr], ignore_index=True)
            sc = fit_scaler(Xtr)
            Ztr = mod.zscore(Xtr.astype(np.float64), sc)
            okt = np.isfinite(ytr)
            n_tr_s = sum(len(days[m]) for m in tr)
            if fk != "final":
                Zf = mod.zscore(Xs[fk][rows[fk]].astype(np.float64), sc)
                mf = metas[fk][rows[fk]].reset_index(drop=True)
            for mdl in ("RG", "LG", "GB"):
                sm, est = train(mdl, Ztr[okt], ytr[okt])
                if mdl == "GB":
                    assert np.allclose(mod.predict_z(Ztr[:20000], sm), est.predict(Ztr[:20000]), atol=1e-6)
                if mdl == "LG":
                    assert np.allclose(mod.predict_z(Ztr[:20000], sm), est.decision_function(Ztr[:20000]), atol=1e-6)
                pin = mod.predict_z(Ztr, sm)
                cin = collapse(mtr, pin)
                if fk != "final":
                    cf = collapse(mf, mod.predict_z(Zf, sm))
                for k in (4, 10):
                    cn = [c for c, g in cfgs.items() if g["model"] == mdl and g["k"] == k and g["univ"] == univ][0]
                    tau = tau_for(cin, k, n_tr_s)
                    if fk == "final":
                        final[cn] = {"model": sm, "tau": tau, **sc}
                        insample[cn] = cin[cin.pred > tau]
                        train_stats[cn] = {"train_rows": int(len(ytr)), "train_pos_share": round(float((ytr[okt] > 0).mean()), 3),
                                           "train_mean_y": round(float(ytr[okt].mean()), 4)}
                    else:
                        cands[cn].append(cf[cf.pred > tau].assign(tau=tau, fold=fk))
                    print(univ, fk, cn, mdl, k, "tau", round(tau, 4), f"{time.time() - t0:.0f}s", flush=True)
            del Ztr, Xtr
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
        for s_, ev_ in (("long", 1), ("short", -1)):
            pass
        grid[cn] = st
        print(cn, cfg["label"], st.get("trades_per_session"), st.get("avg_r"), st.get("total_r"), st.get("total_r_wo_best_day"), flush=True)
    elig = {c: g for c, g in grid.items() if g.get("trades_per_session", 0) >= 2.0}
    pool = elig if elig else grid
    order = list(cfgs)
    pick = max(pool, key=lambda c: (pool[c].get("total_r_wo_best_day", -1e9), -order.index(c)))
    cfg = cfgs[pick]
    bk = books[pick]
    # random controls (same symbol-session-side): base-random (any eligible bar) and event-random (any event row)
    rt_base = pd.concat([rts[m][cfg["univ"]] for m in FOLDS], ignore_index=True)
    rand_base = random_control(bk, rt_base, walker, oof_sessions, spy)
    ev_rows = pd.concat([metas[m][metas[m].inL1] if cfg["univ"] == "L1" else metas[m] for m in FOLDS], ignore_index=True)
    rt_ev = rand_pick(ev_rows[["symbol", "date", "tod", "close", "atr_d", "side"]], np.random.default_rng(SEED))
    rand_ev = random_control(bk, rt_ev, walker, oof_sessions, spy)
    # in-sample all-FIT book of the final model (reported only)
    ins = insample[pick]
    W = walker.get(ins)
    ins_st = full_stats(trade_book(ins, W, cfg["k"]), fit_sessions, spy)
    # freeze
    fm = final[pick]
    model = {"id": "ULT-20", "config": pick, **cfg, "tau": fm["tau"], "feats": list(mod.FEATS), "mean": fm["mean"], "sd": fm["sd"],
             "model": fm["model"], "trained_on": FIT_MONTHS, "frozen_utc": datetime.now(timezone.utc).isoformat()}
    jdump(model, MODEL_JSON)
    allm = {cn: {"config": cn, **cfgs[cn], "tau": final[cn]["tau"], "mean": final[cn]["mean"], "sd": final[cn]["sd"],
                 "model": final[cn]["model"]} for cn in cfgs}
    jdump(allm, Path(work) / "all_final_models.json")
    jdump(grid, HERE / "fit_grid.json")
    fitsel = {"id": "ULT-20", "config": pick, **cfg,
              "rule": "round3 PLAN sec.5: highest OOF fit total R minus best fit day among configs >= 2 trades/session",
              "reached_2_per_session": bool(elig), "tau": fm["tau"], "oof_fit": grid[pick], "insample_all_fit": ins_st,
              "random_control_base_oof": rand_base, "random_control_event_oof": rand_ev,
              "signal_minus_random_base": round(grid[pick]["avg_r"] - rand_base["avg_r"], 4) if rand_base.get("trades") else None,
              "signal_minus_random_event": round(grid[pick]["avg_r"] - rand_ev["avg_r"], 4) if rand_ev.get("trades") else None,
              "train_stats_final": train_stats[pick],
              "model_summary": {"kind": fm["model"]["kind"], **({"w": dict(zip(mod.FEATS, np.round(fm["model"]["w"], 5).tolist()))}
                                                                 if fm["model"]["kind"] != "gb" else {})},
              "sha256": {"bt.py": sha(__file__), "module": sha(MOD), "model_json": sha(MODEL_JSON),
                         "symbols_json": sha(ULT / "modules" / "ULT-20_symbols.json")},
              "frozen_utc": datetime.now(timezone.utc).isoformat()}
    jdump(fitsel, HERE / "fitsel.json")
    print("PICK", pick, cfg, f"{time.time() - t0:.0f}s")


# ------------------------------------------------------------------------------------------------ CHECK stage
def check_month_job(args):
    month, work, models = args
    mod = load_mod()
    f = month_frame(month, work)
    b = mod.build(f)
    etb = etb_set()
    isetb_all = f.symbol.isin(etb).to_numpy()
    out = {}
    for nm, model in models.items():
        pl, ps = mod.predict(f, model, b)
        ps = np.where(isetb_all, ps, -np.inf)
        side = np.where(pl >= ps, 1, -1)
        best = np.maximum(pl, ps)
        ok = np.isfinite(best) & (best > float(model["tau"]))
        out[nm] = f.loc[ok, ["symbol", "date", "tod", "close", "atr_d"]].assign(side=side[ok], pred=best[ok]).reset_index(drop=True)
    meta, X, base = month_rows(f, mod, b, etb)
    rng = np.random.default_rng(SEED + int(month.replace("-", "")))
    rts = {"base_L2": rand_pick(base, rng), "base_L1": rand_pick(base[base.inL1], rng),
           "ev_L2": rand_pick(meta[["symbol", "date", "tod", "close", "atr_d", "side"]], rng),
           "ev_L1": rand_pick(meta.loc[meta.inL1, ["symbol", "date", "tod", "close", "atr_d", "side"]], rng)}
    return month, out, rts, sorted(f.date.unique())


def run_check(work, models):
    ms = check_months()
    res, rts, days = {k: [] for k in models}, {}, []
    with Pool(3) as p:
        for m, out, rt, dd in p.imap_unordered(check_month_job, [(m, str(work), models) for m in ms]):
            for k, v in out.items():
                res[k].append(v)
            for k, v in rt.items():
                rts.setdefault(k, []).append(v)
            days += dd
            print(m, {k: len(v) for k, v in out.items()}, flush=True)
    no_locked(days)
    return ({k: pd.concat(v, ignore_index=True) for k, v in res.items()}, {k: pd.concat(v, ignore_index=True) for k, v in rts.items()},
            sorted(days))


def stage_check(work):
    fs = json.loads((HERE / "fitsel.json").read_text())
    assert sha(MODEL_JSON) == fs["sha256"]["model_json"], "model changed after the freeze"
    assert sha(MOD) == fs["sha256"]["module"], "module changed after the freeze"
    assert not (HERE / "check_once.json").exists(), "check is scored ONCE"
    sector_map(work, "check")
    model = json.loads(MODEL_JSON.read_text())
    res, rts, days = run_check(work, {"pick": model})
    c = res["pick"]
    walker = Walker()
    W = walker.get(c)
    bk = trade_book(c, W, int(fs["k"]))
    spy = spy_types()
    st = full_stats(bk, days, spy)
    rb = random_control(bk, rts["base_" + fs["univ"]], walker, days, spy)
    re_ = random_control(bk, rts["ev_" + fs["univ"]], walker, days, spy)
    jdump({"id": "ULT-20", "config": fs["config"], "check": st, "random_control_base": rb, "random_control_event": re_,
           "signal_minus_random_base": round(st["avg_r"] - rb["avg_r"], 4) if rb.get("trades") else None,
           "signal_minus_random_event": round(st["avg_r"] - re_["avg_r"], 4) if re_.get("trades") else None,
           "candidates_per_session": round(len(c) / len(days), 2), "scored_utc": datetime.now(timezone.utc).isoformat()},
          HERE / "check_once.json")
    bk[["symbol", "date", "tod", "side", "pred", "r", "kind", "xmin"]].to_csv(HERE / "check_trades.csv.gz", index=False)
    print(json.dumps(st, indent=1))


def stage_plateau(work):
    assert (HERE / "check_once.json").exists(), "plateau only after the single check score"
    allm = json.loads((Path(work) / "all_final_models.json").read_text())
    res, rts, days = run_check(work, allm)
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
