"""ULT-19 LR-LITE - backtest (ultimate_1119 round2/PLAN.md sec. 1-2, 3 "ULT-19", 5, 6).

Features: computed by the LIVE module itself (modules/ULT-19.py raw/design/scale/score) on the lab frames
(research/history2y/data/frames, 5-min decision bars 09:50-15:00 bar close) + context (spy_fo).
Training target (FIT only, training proxy): after-cost R of a 45-min time exit (entry = decision close, exit = the 5-min
close at tod + 45 from frames + headtail tail rows; LR8 market both legs, + 1.2 bp borrow for shorts), in 0.25-dATR
units, winsorised +-4.
Model: ridge alpha 1e5 on the side-signed design (long rows + short rows stacked, each side only where its universal
filters pass, shorts only ETB); stability filter: coefficient -> 0 where the sign differs between two sub-halves of the
training set (final model: A = 2024-10 + 2025-03..05, B = 2025-06..09; walk-forward folds: the fold's training
sessions split chronologically in two halves by session count, since the early folds have no B data).
Trading rule (causal): per name take the side with the higher score; enter if score > tau and that side passes its
filters; at most 3 entries per 5-min bar (highest score first); session cap 2k; one lot per symbol, next entry >= 15
bars later (45-min hold + 30-min cooldown), max 2 per symbol-session. tau = the constant that gives on average k
entries/session when this rule is run on the training period's in-sample scores (bisection).
Walk-forward inside FIT: folds 2025-05..09, each trained on all FIT months before it; pooled OOF = "fit" figures.
Chassis scoring: entry = OPEN of the 1-minute bar starting at the decision-bar close (LR8 entry cost on it); TX-45:
catastrophic stop at decision close -+ 2 x 0.25 dATR (as the live stop_price), stop first, gap-through at the worse of
open/stop, time exit at the close of minute entry+44 or the 15:49 minute; R per unit of risk (2 x 0.25 dATR) as
bench.cost_r; R in 0.25-dATR units = 2 x. Costs LR8 + 2c on stops + 1.2 bp borrow on shorts.
Locked block 2024-11-01..2025-02-28 never read (month list, pyarrow filters, asserts).
    python bt.py WORK fit | check | plateau
Educational only - not financial advice."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
UL = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(UL / "benchmark"))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "never reads the locked block"
from mcf.research.gates import tod_cost_mult  # noqa: E402

DATA = Path("/home/user/MCF/research/history2y/data")
CACHE = Path("/home/user/MCF/data/cache_hist/1Min")
HT = Path("/home/user/MCF/research/bdi/cwt/test_b/data/headtail.parquet")
LOCK = ("2024-11-01", "2025-02-28")
LOCKED_MONTHS = {"2024-11", "2024-12", "2025-01", "2025-02"}
FIT_MONTHS = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 10)]
FOLDS = ["2025-05", "2025-06", "2025-07", "2025-08", "2025-09"]
SUB_A = {"2024-10", "2025-03", "2025-04", "2025-05"}
MOD = UL / "modules" / "ULT-19.py"
MODEL_JSON = UL / "modules" / "ULT-19_model.json"
ALPHA = 1e5
H = 45
BORROW = 1.2e-4
UNIV = {"UA": (50e6, 0.10), "UB": (200e6, 0.06)}
KS = [5, 10, 20]
GRID = [(f"19{c}", k, u) for c, (k, u) in zip("abcdef", [(k, u) for k in KS for u in ("UA", "UB")])]
FORBIDDEN = ("win_", "r_long", "r_short", "heat", "Heat")
FRAME_COLS = ["symbol", "date", "tod", "close", "fromOpen", "vwapDistPct", "gap", "atr_d", "rsi", "rsi5", "adv20"]
assert not any(c.startswith(("win_", "r_")) or "eat" in c for c in FRAME_COLS), "forbidden column"


def no_locked(dates):
    s = pd.Series([str(x) for x in dates])
    assert not ((s >= LOCK[0]) & (s <= LOCK[1])).any(), "locked block row found"


def load_mod():
    spec = importlib.util.spec_from_file_location("ult19_bt", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def check_months():
    ms = sorted(p.name.split("=", 1)[1] for p in (DATA / "frames").glob("month=*"))
    return [m for m in ms if m >= "2025-10" and m not in LOCKED_MONTHS]


def hhmm_plus(tod, mins):
    m = (np.asarray(tod, int) // 100) * 60 + np.asarray(tod, int) % 100 + mins
    return (m // 60) * 100 + m % 60


ETB = None


def etb_set():
    u = pd.read_csv(ROOT / "data" / "universe.csv")
    return set(u.loc[u.easy_to_borrow.astype(str).str.lower() == "true", "symbol"].astype(str))


# ---------------------------------------------------------------- stage 1: features (one month per worker)
def month_features(args):
    month, with_y = args
    assert month not in LOCKED_MONTHS
    mod = load_mod()
    p = DATA / "frames" / f"month={month}"
    f = pads.dataset(str(p), format="parquet").to_table(columns=FRAME_COLS).to_pandas()
    f["date"] = pd.to_datetime(f["date"]).dt.date.astype(str)
    no_locked(f["date"].unique())
    c = pd.read_parquet(DATA / "context" / f"month={month}.parquet", columns=["date", "tod", "spy_fo"])
    c["date"] = pd.to_datetime(c["date"]).dt.date.astype(str)
    f = f.merge(c, on=["date", "tod"], how="left")
    f["symbol"] = f["symbol"].astype(str)
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    r = mod.raw(f)
    lo_adv, hi_cost = min(v[0] for v in UNIV.values()), max(v[1] for v in UNIV.values())
    keep = mod.intake(r, hi_cost) & (f["adv20"].fillna(0).to_numpy() >= lo_adv) & (r["tod"] >= 950) & (r["tod"] <= 1500)
    etb = etb_set()
    out = pd.DataFrame({"symbol": f["symbol"].to_numpy()[keep], "date": f["date"].to_numpy()[keep]})
    for k in ("tod", "close", "atr_d", "gap", "fo_datr", "vd_datr", "atr_pct", "cost_r", "spy_fo", "spy_r30", "rsi5", "rsi14"):
        out[k] = r[k][keep].astype(np.float64 if k in ("close", "atr_d") else np.float32)
    out["adv20"] = f["adv20"].to_numpy()[keep].astype(np.float32)
    out["okL"] = mod.side_ok(r, 1)[keep]
    out["okS"] = mod.side_ok(r, -1)[keep] & out["symbol"].isin(etb).to_numpy()
    out["tod"] = out["tod"].astype(np.int16)
    if with_y:
        a = pd.Timestamp(month + "-01")
        ht = pd.read_parquet(HT, columns=["symbol", "date", "tod", "c"],
                             filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1))])
        ht = ht[ht.tod > 1500].rename(columns={"c": "close"})
        ht["symbol"] = ht["symbol"].astype(str)
        ht["date"] = pd.to_datetime(ht["date"]).dt.date.astype(str)
        no_locked(ht["date"].unique())
        P = pd.concat([f[["symbol", "date", "tod", "close"]], ht[["symbol", "date", "tod", "close"]]], ignore_index=True)
        P = P.drop_duplicates(["symbol", "date", "tod"]).rename(columns={"tod": "tx", "close": "px"})
        q = out[["symbol", "date"]].copy()
        q["tx"] = hhmm_plus(out["tod"].to_numpy(), H)
        px = q.merge(P, on=["symbol", "date", "tx"], how="left")["px"].to_numpy(float)
        e, u, tod = out["close"].to_numpy(float), 0.25 * out["atr_d"].to_numpy(float), out["tod"].to_numpy()
        ec = (0.01 + e * 1e-4) * tod_cost_mult(tod)
        xc = 0.01 + px * 1e-4
        out["yL"] = np.clip((px - e - ec - xc) / u, -4, 4).astype(np.float32)
        out["yS"] = np.clip((e - px - ec - xc - BORROW * e) / u, -4, 4).astype(np.float32)
    out["month"] = month
    return out


def build(months, with_y):
    with Pool(3) as p:
        parts = p.map(month_features, [(m, with_y) for m in months])
    F = pd.concat(parts, ignore_index=True)
    F["symbol"] = F["symbol"].astype("category")
    no_locked(F["date"].unique())
    return F


# ---------------------------------------------------------------- stage 2: ridge with the stability filter
def rawdict(F):
    return {k: F[k].to_numpy(float) for k in ("tod", "close", "atr_d", "gap", "fo_datr", "vd_datr", "atr_pct", "cost_r",
                                              "spy_fo", "spy_r30", "rsi5", "rsi14")} | {"rsi14": F["rsi14"].to_numpy(float)}


def in_univ(F, u):
    adv, cmax = UNIV[u]
    return (F["adv20"].to_numpy() >= adv) & (F["cost_r"].to_numpy() <= cmax)


def fit_ridge(mod, F, train, u, halves):
    """train: bool mask over F; halves: (maskA, maskB) inside train. Returns model dict."""
    base = train & in_univ(F, u)
    T = F[base]
    r = rawdict(T)
    XL, XS = mod.design(r, 1), mod.design(r, -1)
    okL, okS = T["okL"].to_numpy(), T["okS"].to_numpy()
    Xall = np.vstack([XL[okL], XS[okS]])
    mean = np.nanmean(Xall, axis=0)
    sd = np.nanstd(Xall, axis=0)
    sd[~np.isfinite(sd) | (sd <= 0)] = 1.0
    ZL, ZS = mod.scale(XL, mean, sd), mod.scale(XS, mean, sd)
    yL, yS = T["yL"].to_numpy(float), T["yS"].to_numpy(float)
    vL, vS = okL & np.isfinite(yL), okS & np.isfinite(yS)

    def solve(sel):
        a, b = sel[base] if sel is not None else np.ones(len(T), bool), None
        mL, mS = vL & a, vS & a
        Z = np.vstack([ZL[mL], ZS[mS]])
        y = np.r_[yL[mL], yS[mS]]
        A = Z.T @ Z + ALPHA * np.eye(Z.shape[1])
        return np.linalg.solve(A, Z.T @ y), len(y)

    w, n = solve(None)
    wA, nA = solve(halves[0])
    wB, nB = solve(halves[1])
    flip = np.sign(wA) != np.sign(wB)
    wf = np.where(flip, 0.0, w)
    return {"universe": u, "min_adv": UNIV[u][0], "cost_r_max": UNIV[u][1], "features": mod.FEATURES,
            "mean": mean.tolist(), "sd": sd.tolist(), "w_unfiltered": w.tolist(), "w_A": wA.tolist(), "w_B": wB.tolist(),
            "zeroed": [mod.FEATURES[i] for i in np.flatnonzero(flip)], "w": wf.tolist(), "n_train": int(n),
            "n_A": int(nA), "n_B": int(nB), "alpha": ALPHA}


def chrono_halves(F, train):
    d = np.array(sorted(F.loc[train, "date"].unique()))
    cut = d[len(d) // 2]
    dates = F["date"].to_numpy()
    return train & (dates < cut), train & (dates >= cut)


# ---------------------------------------------------------------- stage 3: causal trading rule
def candidates(mod, F, sel, model):
    """Rows of F[sel] in the model's universe with the better side, its score and eligibility."""
    m = sel & in_univ(F, model["universe"])
    T = F[m]
    r = rawdict(T)
    pL, pS = mod.score(r, 1, model), mod.score(r, -1, model)
    side = np.where(pL >= pS, 1, -1)
    pred = np.where(side > 0, pL, pS)
    ok = np.where(side > 0, T["okL"].to_numpy(), T["okS"].to_numpy())
    C = pd.DataFrame({"symbol": T["symbol"].astype(str).to_numpy(), "date": T["date"].to_numpy(),
                      "tod": T["tod"].to_numpy().astype(int), "side": side, "pred": pred, "close": T["close"].to_numpy(),
                      "atr_d": T["atr_d"].to_numpy(), "gap": T["gap"].to_numpy(float), "adv20": T["adv20"].to_numpy()})
    C = C[ok].sort_values(["date", "tod", "pred"], ascending=[True, True, False], kind="mergesort").reset_index(drop=True)
    return C


def simulate(C, tau, k):
    """Causal rule on candidate rows (sorted date, tod, pred desc). Returns the chosen row indices."""
    c = C[C.pred.to_numpy() > tau]
    if not len(c):
        return np.zeros(0, int)
    idx = c.index.to_numpy()
    dd, tt, ss = c.date.to_numpy(), c.tod.to_numpy(), c.symbol.to_numpy()
    bar = ((tt // 100) * 60 + tt % 100 - 570) // 5
    cap = 2 * k
    out = []
    cur_d, cur_t, nbar, nday, last, cnt = None, None, 0, 0, {}, {}
    for j in range(len(c)):
        if dd[j] != cur_d:
            cur_d, cur_t, nbar, nday, last, cnt = dd[j], None, 0, 0, {}, {}
        if tt[j] != cur_t:
            cur_t, nbar = tt[j], 0
        if nday >= cap or nbar >= 3:
            continue
        s = ss[j]
        if cnt.get(s, 0) >= 2 or bar[j] - last.get(s, -999) < 15:
            continue
        out.append(idx[j]); nbar += 1; nday += 1; last[s] = bar[j]; cnt[s] = cnt.get(s, 0) + 1
    return np.asarray(out, int)


def calibrate_tau(C, k, n_sessions):
    lo, hi = float(np.quantile(C.pred, 0.5)), float(C.pred.max())
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        n = len(simulate(C, mid, k)) / n_sessions
        if n > k:
            lo = mid
        else:
            hi = mid
    return hi


# ---------------------------------------------------------------- stage 4: 1-minute chassis walk
def walk1_job(args):
    sym, T, seed = args
    d = pads.dataset(str(CACHE / f"{sym}.parquet"), format="parquet")
    fld = pads.field("__index_level_0__")
    tz = "America/New_York"
    dmin = pd.Timestamp(min(T.date), tz=tz)
    dmax = pd.Timestamp(max(T.date), tz=tz) + pd.Timedelta(days=1)
    L0, L1 = pd.Timestamp("2024-11-01", tz=tz), pd.Timestamp("2025-03-01", tz=tz)
    b = d.to_table(filter=((fld < L0) | (fld >= L1)) & (fld >= dmin) & (fld < dmax)).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(tz)
    b = b.sort_index()
    no_locked(np.unique(b.index.date))
    hhmm = (b.index.hour * 100 + b.index.minute).to_numpy()
    day = b.index.date.astype(str)
    O, Hh, Lo, Cc = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    byday = {}
    if len(day):
        st = np.flatnonzero(np.r_[True, day[1:] != day[:-1]])
        en = np.r_[st[1:], len(day)]
        byday = {day[a]: np.arange(a, e) for a, e in zip(st, en)}
    rng = np.random.default_rng(seed)
    res = []

    def one(ix, tod, s, u, dclose):
        hm = hhmm[ix]
        j0 = np.searchsorted(hm, tod)
        if j0 >= len(ix) or hm[j0] - tod > 4 or hm[j0] >= 1550:
            return None
        e = O[ix[j0]]
        if dclose is None:          # random control: decision close = close of the last minute before tod
            if j0 == 0 or hm[j0 - 1] < hhmm_plus(tod, -5):
                return None
            dclose = Cc[ix[j0 - 1]]
        tend = min(int(hhmm_plus(hm[j0], H - 1)), 1549)
        stop = dclose - s * 2 * u
        px, kd, xt = None, 0, None
        for q in ix[j0:]:
            if hhmm[q] > tend:
                break
            if (s == 1 and Lo[q] <= stop) or (s == -1 and Hh[q] >= stop):
                px = min(O[q], stop) if s == 1 else max(O[q], stop)
                kd, xt = 1, hhmm[q]; break
            px, xt = Cc[q], hhmm[q]
        if px is None:
            return None
        return e, dclose, px, kd, int(hhmm_plus(xt, 1))

    for r in T.itertuples():
        ix = byday.get(r.date)
        u = 0.25 * r.atr_d
        a = None if ix is None else one(ix, r.tod, r.side, u, r.close)
        rr = None
        if ix is not None:
            for _ in range(5):
                rt = int(hhmm_plus(950, 5 * int(rng.integers(0, 63))))
                rr = one(ix, rt, r.side, u, None)
                if rr is not None:
                    break
            rr = None if rr is None else (rt,) + rr
        res.append((r.Index,) + (a if a else (np.nan,) * 5) + (rr if rr else (np.nan,) * 6))
    return res


def cost_R(side, tod, e, px, kd, u, borrow=True):
    ec = (0.01 + e * 1e-4) * tod_cost_mult(tod)
    xc = 0.01 + px * 1e-4 + np.where(kd == 1, 0.02, 0.0)
    bf = np.where((side < 0) & borrow, BORROW * e, 0.0)
    return (side * (px - e) - ec - xc - bf) / (2 * u)


def walk(T, work, tag):
    T = T.reset_index(drop=True)
    no_locked(T["date"].unique())
    jobs = [(s, g, 1119 + i) for i, (s, g) in enumerate(T.groupby("symbol")) if (CACHE / f"{s}.parquet").exists()]
    with Pool(3) as p:
        out = [x for r in p.imap_unordered(walk1_job, jobs, chunksize=4) for x in r]
    cols = ["i", "e", "dclose", "px", "kd", "xt", "rtod", "re", "rdclose", "rpx", "rkd", "rxt"]
    a = pd.DataFrame(out, columns=cols).set_index("i")
    T = T.join(a)
    u = 0.25 * T.atr_d.to_numpy()
    s, tod = T.side.to_numpy(), T.tod.to_numpy()
    T["r"] = cost_R(s, tod, T.e.to_numpy(), T.px.to_numpy(), T.kd.to_numpy(), u)
    T["r_sigclose_noborrow"] = cost_R(s, tod, T.close.to_numpy(), T.px.to_numpy(), T.kd.to_numpy(), u, borrow=False)
    T["r_rand"] = cost_R(s, T.rtod.to_numpy(), T.re.to_numpy(), T.rpx.to_numpy(), T.rkd.to_numpy(), u)
    T["hold"] = np.where(T.xt.notna(), (T.xt // 100 * 60 + T.xt % 100) - (tod // 100 * 60 + tod % 100), np.nan)
    T.to_parquet(Path(work) / f"trades_{tag}.parquet")
    return T


# ---------------------------------------------------------------- stage 5: statistics
SPY = None


def spy_types():
    global SPY
    if SPY is None:
        from stats import spy_days
        SPY = spy_days()
    return SPY


def stats(t, n_sessions, col="r"):
    t = t[t[col].notna()]
    if not len(t):
        return {"trades": 0, "sessions": int(n_sessions), "trades_per_session": 0.0}
    day = t.groupby("date")[col].sum()
    tot = float(t[col].sum())
    avg = float(t[col].mean())
    best = day.idxmax()
    dev = (t[col] - avg).groupby(t["date"]).sum()
    se = float(np.sqrt((dev ** 2).sum())) / len(t)
    tps = len(t) / day.size
    ty = t.date.map(spy_types()["type"])
    o = {"trades": int(len(t)), "sessions": int(n_sessions), "sessions_traded": int(day.size),
         "trades_per_session": round(len(t) / n_sessions, 2), "win": round(float((t[col] > 0).mean()), 3),
         "avg_r": round(avg, 4), "avg_r_dATR025": round(2 * avg, 4),
         "avg_r_wo_best_day": round(float(t.loc[t.date != best, col].mean()), 4), "best_day": str(best),
         "best_day_share": round(float(day.max() / tot), 3) if tot > 0 else None, "total_r": round(tot, 2),
         "total_r_wo_best_day": round(tot - float(day.max()), 2),
         "total_r_per_session": round(tot / n_sessions, 3), "worst_day": round(float(day.min()), 2),
         "worst_day_per_trade_session": round(float(day.min()) / tps, 3), "t_day_clustered": round(avg / se, 2) if se > 0 else None}
    for k in ("up", "flat", "down"):
        x = t.loc[ty == k, col]
        o[f"avg_r_spy_{k}"] = round(float(x.mean()), 4) if len(x) else None
        o[f"n_spy_{k}"] = int(len(x))
    ex = t[~t.date.between("2025-04-03", "2025-04-09")]
    o["avg_r_ex_0403_0409"] = round(float(ex[col].mean()), 4) if len(ex) else None
    o["n_ex_0403_0409"] = int(len(ex))
    for sd, nm in ((1, "long"), (-1, "short")):
        x = t.loc[t.side == sd, col]
        o[f"avg_r_{nm}"] = round(float(x.mean()), 4) if len(x) else None
        o[f"n_{nm}"] = int(len(x))
    o["median_hold_min"] = float(np.nanmedian(t["hold"])) if "hold" in t else None
    return o


def full_stats(t, n_sessions):
    o = stats(t, n_sessions)
    rnd = t[t.r_rand.notna() & t.r.notna()]
    o["random_avg_r"] = round(float(rnd.r_rand.mean()), 4) if len(rnd) else None
    o["signal_minus_random"] = round(float((rnd.r - rnd.r_rand).mean()), 4) if len(rnd) else None
    o["bias_diag_sigclose_noborrow_avg_r"] = round(float(t.r_sigclose_noborrow.mean()), 4)
    d = sorted(t.date.unique())
    if len(d) > 1:
        mid = d[len(d) // 2]
        o["first_half_avg_r"] = round(float(t.loc[t.date < mid, "r"].mean()), 4)
        o["second_half_avg_r"] = round(float(t.loc[t.date >= mid, "r"].mean()), 4)
    return o


def sessions(lo, hi, months=None):
    s = spy_types()
    d = pd.Series(s.index)
    m = (d >= lo) & (d <= hi)
    if months is not None:
        m &= d.str[:7].isin(months)
    no_locked(d[m])
    return int(m.sum())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------- drivers
def run_fit(work):
    mod = load_mod()
    t0 = time.time()
    F = build(FIT_MONTHS, True)
    print("fit features", len(F), round(time.time() - t0), "s", flush=True)
    months = F["month"].to_numpy()
    allfit = np.ones(len(F), bool)
    ns_fit = sessions("2024-10-01", "2025-09-30", FIT_MONTHS)
    models, trades = {}, []
    for u in UNIV:
        # final all-FIT model with A/B halves
        A = np.isin(months, list(SUB_A))
        fm = fit_ridge(mod, F, allfit, u, (A, ~A))
        models[(u, "final")] = fm
        C = candidates(mod, F, allfit, fm)
        for k in KS:
            tau = calibrate_tau(C, k, ns_fit)
            fm.setdefault("tau", {})[k] = tau
            ch = C.loc[simulate(C, tau, k)].assign(cfg=f"{u}k{k}", part="insample")
            trades.append(ch)
        print(u, "final zeroed", fm["zeroed"], "tau", fm["tau"], flush=True)
        for fo in FOLDS:
            tr = months < fo
            fmod = fit_ridge(mod, F, tr, u, chrono_halves(F, tr))
            ns_tr = sessions("2024-10-01", "2025-09-30", sorted(set(months[tr])))
            Ctr = candidates(mod, F, tr, fmod)
            Cte = candidates(mod, F, months == fo, fmod)
            fmod["tau"] = {}
            for k in KS:
                tau = calibrate_tau(Ctr, k, ns_tr)
                fmod["tau"][k] = tau
                trades.append(Cte.loc[simulate(Cte, tau, k)].assign(cfg=f"{u}k{k}", part="oof"))
            models[(u, fo)] = fmod
            print(u, fo, "zeroed", fmod["zeroed"], "w", np.round(fmod["w"], 4).tolist(), flush=True)
    del F
    T = pd.concat(trades, ignore_index=True)
    key = ["symbol", "date", "tod", "side"]
    U = T.drop_duplicates(key)[key + ["close", "atr_d", "gap"]]
    W = walk(U, work, "fit")
    T = T.merge(W[key + ["e", "px", "kd", "r", "r_sigclose_noborrow", "r_rand", "hold"]], on=key, how="left")
    ns_oof = sessions("2025-05-01", "2025-09-30", FOLDS)
    grid = {}
    for name, k, u in GRID:
        g = T[T.cfg == f"{u}k{k}"]
        grid[name] = {"k": k, "universe": u, "oof": full_stats(g[g.part == "oof"], ns_oof),
                      "insample_allfit": full_stats(g[g.part == "insample"], ns_fit)}
        o = grid[name]["oof"]
        print(name, u, k, {x: o.get(x) for x in ("trades_per_session", "avg_r", "avg_r_wo_best_day", "total_r",
                                                 "total_r_wo_best_day", "t_day_clustered", "signal_minus_random")}, flush=True)
    elig = [n for n in grid if grid[n]["oof"]["trades_per_session"] >= 2.0]
    pool = elig or list(grid)
    pick = max(pool, key=lambda n: (grid[n]["oof"]["total_r_wo_best_day"], -GRID_ORDER[n]))
    mfin = models[(grid[pick]["universe"], "final")]
    frozen = {k_: v for k_, v in mfin.items() if k_ != "tau"} | {"tau": mfin["tau"][grid[pick]["k"]], "k": grid[pick]["k"],
                                                                  "config": pick}
    MODEL_JSON.write_text(json.dumps(frozen, indent=1))
    fold_models = {f"{u}|{fo}": {k_: v for k_, v in m_.items() if k_ not in ("features",)} for (u, fo), m_ in models.items()}
    (HERE / "fit_grid.json").write_text(json.dumps({"note": "Educational only - not financial advice. ULT-19 FIT grid; "
                                                    "'oof' = pooled walk-forward out-of-fold 2025-05..09 (selection + TIER A fit test).",
                                                    "sessions_fit": ns_fit, "sessions_oof": ns_oof, "grid": grid,
                                                    "models": fold_models}, indent=1, default=float))
    fitsel = {"note": "Educational only - not financial advice. Frozen BEFORE any check feature/trade is built.",
              "frozen_at_utc": pd.Timestamp.utcnow().isoformat(), "pick": pick, "k": grid[pick]["k"],
              "universe": grid[pick]["universe"], "selection_rule": "max OOF fit total R minus best fit day among "
              "configs with >= 2.0 OOF trades/session (PLAN sec. 5)", "eligible": elig,
              "pick_by_total_r": max(pool, key=lambda n: grid[n]["oof"]["total_r"]),
              "fit_oof": grid[pick]["oof"], "model": frozen,
              "sha256": {"bt.py": sha(__file__), "module": sha(MOD), "model_json": sha(MODEL_JSON)}}
    (HERE / "fitsel.json").write_text(json.dumps(fitsel, indent=1, default=float))
    print("PICK", pick, "frozen", flush=True)
    for p in Path(work).glob("trades_fit.parquet"):
        p.unlink()


GRID_ORDER = {n: i for i, (n, _, _) in enumerate(GRID)}


def run_check(work, plateau=False):
    sel = json.loads((HERE / "fitsel.json").read_text())
    assert sha(MODEL_JSON) == sel["sha256"]["model_json"], "model changed after the freeze"
    mod = load_mod()
    F = build(check_months(), False)
    ns = sessions("2025-10-01", "2099-12-31")
    allc = np.ones(len(F), bool)
    if not plateau:
        m = sel["model"]
        C = candidates(mod, F, allc, m)
        T = C.loc[simulate(C, m["tau"], m["k"])].reset_index(drop=True)
        W = walk(T, work, "check")
        o = full_stats(W, ns)
        o["daily_r"] = {d: round(float(v), 3) for d, v in W.groupby("date").r.sum().items()}
        (HERE / "check_once.json").write_text(json.dumps({"note": "Educational only - not financial advice. ULT-19 fit "
                                                          "pick scored ONCE on CHECK.", "pick": sel["pick"],
                                                          "scored_at_utc": pd.Timestamp.utcnow().isoformat(), "check": o},
                                                         indent=1, default=float))
        print(json.dumps({k: v for k, v in o.items() if k != "daily_r"}, indent=1, default=float))
        return
    # plateau: every grid config with its own frozen all-FIT model (diagnostic only, never re-selects)
    fg = json.loads((HERE / "fit_grid.json").read_text())
    res = {}
    for name, k, u in GRID:
        m = fg["models"][f"{u}|final"]
        m = m | {"universe": u}
        C = candidates(mod, F, allc, m)
        T = C.loc[simulate(C, m["tau"][str(k)], k)].reset_index(drop=True)
        W = walk(T, work, f"plat_{name}")
        res[name] = full_stats(W, ns)
        print(name, {x: res[name].get(x) for x in ("trades_per_session", "avg_r", "avg_r_wo_best_day", "t_day_clustered")}, flush=True)
        (Path(work) / f"trades_plat_{name}.parquet").unlink()
    (HERE / "check_plateau.json").write_text(json.dumps({"note": "Educational only - not financial advice. Plateau "
                                                         "diagnostic AFTER the single check score; never used to select.",
                                                         "grid": res}, indent=1, default=float))


if __name__ == "__main__":
    work = Path(sys.argv[1]); work.mkdir(parents=True, exist_ok=True)
    stage = sys.argv[2]
    if stage == "fit":
        run_fit(work)
    elif stage == "check":
        run_check(work)
    elif stage == "plateau":
        run_check(work, plateau=True)
