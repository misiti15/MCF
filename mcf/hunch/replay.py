"""Hunch walk-forward replay, scoring and report (owner design 2026-11-04: one combined learner, ~20 tickers, pooled).

run():  steps through every guess slot (one 3-min bar close, all symbols at once) in time order over TRAIN, VALID
        and FORWARD (the locked block is never read: data.load_1min filters it out). At each step every learner first
        updates on the previous step's scored guesses, then guesses this step. The first WARMUP_SESS sessions are a
        warm-up (bin edges, scaler): guessed but never scored.
score:  hit rate per learner and baseline per period; a learner "beats" a baseline only if its day-clustered z of
        the paired hit difference reaches the multiple-testing bar max(1.5, sqrt(2 ln N)), N = learners x metrics
        run. McNemar z (guess-level, ignores clustering) is shown next to it for reference.
"consistent 65%+": rolling 20-session hit rate >= 65% in >= 90% of the windows on VALID.
Educational only - not financial advice.
"""
from __future__ import annotations

import copy
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from . import data as D
from . import learners as Lr
from . import metrics as M

WARMUP_SESS = 20
BASELINES = ["coin", "same_last", "base_rate", "always_yes", "mom20"]
TOD_NAMES = ["09:51-10:30", "10:33-12:00", "12:03-14:00", "14:03-15:00", "15:03-15:51"]
CONSIST_WIN, CONSIST_HIT, CONSIST_SHARE = 20, 0.65, 0.90
DISCLAIMER = "Educational only — not financial advice."


def bar_for(n: int) -> float:
    return max(1.5, math.sqrt(2 * math.log(max(n, 2))))


@dataclass
class Grid:
    """Guess slots as dense arrays: T steps x S symbols."""
    steps: pd.DataFrame          # date, b, sess (index into sessions), period, scored
    symbols: list
    X: np.ndarray                # (T, S, F) float32, NaN where missing
    y: np.ndarray                # (T, S) float, NaN where no answer
    mask: np.ndarray             # (T, S) bool: a valid guess slot
    base: np.ndarray             # (T, S, nb) baseline guesses (float 0/1; coin handled in scoring)
    extra: dict = field(default_factory=dict)


def make_grid(panel: pd.DataFrame, metric: str, features=None) -> Grid:
    features = list(features or D.FEATURES)
    p = panel.sort_values(["symbol", "date", "b"], kind="mergesort").reset_index(drop=True)
    y = M.label(p, metric)
    sl = M.same_last(p, metric)
    mo = M.mom20(p, metric)
    nxt_filled = p.groupby(["symbol", "date"], sort=False)["filled"].shift(-1).fillna(1).to_numpy()
    ok = ((p["b"] >= D.GUESS_FIRST) & (p["b"] <= D.GUESS_LAST) & (p["warmup"] == 0) & (p["filled"] == 0)
          ).to_numpy() & (nxt_filled == 0) & np.isfinite(y) & np.isfinite(p["atr"].to_numpy())
    slots = p.loc[(p["b"] >= D.GUESS_FIRST) & (p["b"] <= D.GUESS_LAST), ["date", "b"]].drop_duplicates()
    slots = slots.sort_values(["date", "b"]).reset_index(drop=True)
    sessions = sorted(slots["date"].unique())
    sidx = {d: i for i, d in enumerate(sessions)}
    slots["sess"] = slots["date"].map(sidx)
    slots["period"] = D.period_of(slots["date"])
    slots["scored"] = slots["sess"] >= WARMUP_SESS
    key = {(d, b): i for i, (d, b) in enumerate(zip(slots["date"], slots["b"]))}
    symbols = list(dict.fromkeys(p["symbol"]))
    T, S, F = len(slots), len(symbols), len(features)
    X = np.full((T, S, F), np.nan, dtype=np.float32)
    Y = np.full((T, S), np.nan)
    mask = np.zeros((T, S), bool)
    base = np.zeros((T, S, len(BASELINES)), dtype=np.float32)
    sym_i = {s: i for i, s in enumerate(symbols)}
    sel = np.flatnonzero(ok)
    ti = np.array([key[(d, b)] for d, b in zip(p["date"].to_numpy()[sel], p["b"].to_numpy()[sel])])
    si = p["symbol"].map(sym_i).to_numpy()[sel]
    X[ti, si] = p[features].to_numpy(dtype=np.float32)[sel]
    Y[ti, si] = y[sel]
    mask[ti, si] = True
    base[ti, si, 1] = np.nan_to_num(sl[sel], nan=0.0)
    base[ti, si, 4] = mo[sel]
    base[:, :, 3] = 1.0
    # SPY session open-to-close for the day-type breakdown (known only after the close: a report split, not a feature)
    spy = p[p["symbol"] == "SPY"].groupby("date").agg(o=("o", "first"), c=("c", "last"))
    o2c = (spy["c"] / spy["o"] - 1) * 100
    nc = p.groupby(["symbol", "date"], sort=False)["c"].shift(-1).to_numpy()
    ties = float((nc[sel] == p["c"].to_numpy()[sel]).mean()) if len(sel) else float("nan")
    return Grid(slots, symbols, X, Y, mask, base, {"spy_o2c": o2c, "features": features, "metric": metric,
                                                   "ties": ties})


TOPK = 8
MAIN = ["pooled:logreg", "pooled:gbt", f"pooled:top{TOPK}", "ticker:logreg"]


def _walk(grid: Grid, cols: list[int], full: bool, verbose: bool = False, diag: bool = True) -> dict:
    """One walk-forward pass. full=False runs only a pooled LogReg on feature columns `cols` (the top-k model)."""
    feats = [grid.extra["features"][j] for j in cols]
    X = grid.X if cols == list(range(grid.X.shape[2])) else grid.X[:, :, cols]
    T, S, F = X.shape
    st = grid.steps
    tod_col = feats.index("tod") if "tod" in feats else None
    if tod_col is None:  # time of day always goes in (as dummies) - append it if top-k left it out
        X = np.concatenate([X, grid.X[:, :, [grid.extra["features"].index("tod")]]], axis=2)
        feats = feats + ["tod"]
        tod_col, F = F, F + 1
    pooled = Lr.LogReg(F, tod_col, n_groups=S)
    names = ["pooled:logreg"]
    if full:
        warm = (st["sess"] < WARMUP_SESS).to_numpy()
        edges = Lr.bin_edges(X[warm][grid.mask[warm]].astype(float))
        C = Lr.bin_codes(X, edges)
        gbt = Lr.GBT(F)
        tick = Lr.PerTicker(S, F, tod_col)
        binned = Lr.Binned(F) if diag else None
        names += ["pooled:gbt", "ticker:logreg"] + ([f"ind:{f}" for f in feats] if diag else [])
    L = len(names)
    P = np.zeros((T, S, L), bool)
    base = grid.base.copy()
    yes_n = tot_n = 0.0
    sess_arr = st["sess"].to_numpy()
    periods = st["period"].to_numpy()
    snaps, gbt_snaps, w_hist = {}, {}, []
    last_sess = -1
    for k in range(T):
        if k > 0:
            m = grid.mask[k - 1]
            idx = np.flatnonzero(m)
            Xp, yp = X[k - 1][m].astype(float), grid.y[k - 1][m]
            if len(idx):
                pooled.update(Xp, yp, idx)
                yes_n += yp.sum()
                tot_n += len(yp)
            if full and diag:
                binned.update(C[k - 1][m], yp)
            if full:
                if len(idx):
                    tick.update(Xp, yp, idx)
        s = sess_arr[k]
        if s != last_sess:
            if last_sess >= 0 and periods[k] != periods[k - 1]:
                snaps[periods[k - 1]] = pooled.snapshot()
                if full:
                    gbt_snaps[periods[k - 1]] = copy.deepcopy(gbt)
            if full and s >= WARMUP_SESS and (s - WARMUP_SESS) % Lr.REFIT_SESS == 0:
                lo = np.searchsorted(sess_arr, max(0, s - Lr.WINDOW_SESS))
                mm = grid.mask[lo:k]
                gbt.fit(C[lo:k][mm], grid.y[lo:k][mm])
                if verbose:
                    print(f"  session {s} {st['date'].iloc[k]} gbt refit on {int(mm.sum())} guesses", flush=True)
            if periods[k] == "VALID":
                w_hist.append(pooled.w.copy())
            last_sess = s
        m = grid.mask[k]
        if not m.any():
            continue
        idx = np.flatnonzero(m)
        Xk = X[k][m].astype(float)
        pk = np.zeros((len(idx), L), bool)
        pk[:, 0] = pooled.predict(Xk, idx)
        if full:
            Ck = C[k][m]
            pk[:, 1] = gbt.predict(Ck)
            pk[:, 2] = tick.predict(Xk, idx)
            if diag:
                pk[:, 3:] = binned.predict(Ck)
        P[k][m] = pk
        base[k, m, 2] = 1.0 if (tot_n > 0 and yes_n / tot_n > 0.5) else 0.0
    snaps[periods[-1]] = pooled.snapshot()
    out = {"P": P, "names": names, "base": base, "snaps": snaps, "feats": feats, "tod_col": tod_col,
           "w_valid": np.array(w_hist) if w_hist else None}
    out["models"] = {"pooled": pooled, "yes_n": yes_n, "tot_n": tot_n, "symbols": list(grid.symbols), "feats": feats}
    if full:
        out.update(gbt_snaps=gbt_snaps, edges=edges, codes=C)
        out["models"]["ticker"] = tick
    return out


def save_state(res: dict, path: Path, metric: str, last_date) -> None:
    """The end-of-replay model state (pooled logreg + one logreg per ticker) for the live shadow to start from."""
    m = res["models"]
    p, t = m["pooled"], m["ticker"]
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, metric=metric, last_date=str(last_date), symbols=np.array(m["symbols"]),
                        feats=np.array(m["feats"]), yes_n=m["yes_n"], tot_n=m["tot_n"],
                        p_w=p.w, p_wg=p.wg, p_mu=p.sc.mu, p_m2=p.sc.m2, p_n=p.sc.n, p_rows=p.rows,
                        t_W=t.W, t_mu=t.mu, t_m2=t.m2, t_n=t.n, t_rows=t.rows)


def run(grid: Grid, verbose: bool = False, diag: bool | None = None) -> dict:
    """Main pass (pooled logreg, pooled GBT, per-ticker logreg, diagnostics), then the top-k pass whose k features are
    chosen by TRAIN permutation importance only (scored on the last 60 TRAIN sessions with end-of-TRAIN models).
    The top-k model's TRAIN hit rate is therefore not out of sample; its VALID / FORWARD hit rates are."""
    feats = grid.extra["features"]
    if diag is None:  # the single-indicator diagnostics only on the ~20-ticker run (memory at 100 / 200 tickers)
        diag = len(grid.symbols) <= 30
    main = _walk(grid, list(range(len(feats))), True, verbose, diag)
    tr = (grid.steps["period"] == "TRAIN") & grid.steps["scored"]
    tr_sess = grid.steps.loc[tr, "sess"].unique()
    sel = (grid.steps["sess"].isin(tr_sess[-60:]) & tr).to_numpy()
    imp_tr = importance(grid, main, "TRAIN", sel)
    top = list(imp_tr["feature"][:TOPK])
    if verbose:
        print("  top-k from TRAIN:", top, flush=True)
    tk = _walk(grid, [feats.index(f) for f in top], False)
    P = np.concatenate([main["P"][:, :, :2], tk["P"][:, :, :1], main["P"][:, :, 2:]], axis=2)
    names = main["names"][:2] + [f"pooled:top{TOPK}"] + main["names"][2:]
    return {**main, "P": P, "names": names, "topk": top, "imp_train": imp_tr}


def importance(grid: Grid, res: dict, snap_key: str, step_sel: np.ndarray, reps: int = 3, seed: int = 0,
               max_rows: int = 500_000) -> pd.DataFrame:
    """Permutation importance of the frozen pooled logreg and pooled GBT (as they stood at the end of `snap_key`)
    on the guesses of steps `step_sel`: each feature shuffled across those guesses in turn, `reps` times.
    Ranked by the mean of the two models' log-loss-increase ranks."""
    feats = res["feats"]
    S = len(grid.symbols)
    lr = Lr.LogReg.from_snapshot(res["snaps"][snap_key], len(feats), res["tod_col"], S)
    gb = res["gbt_snaps"][snap_key]
    m = grid.mask & step_sel[:, None]
    rng = np.random.default_rng(seed)
    keep = np.flatnonzero(m.ravel())
    if len(keep) > max_rows:  # a fixed random subsample keeps 100 / 200-ticker runs light
        keep = np.sort(rng.choice(keep, max_rows, replace=False))
    X = grid.X.reshape(-1, grid.X.shape[2])[keep].astype(float)
    C = res["codes"].reshape(-1, grid.X.shape[2])[keep]
    g = keep % grid.X.shape[1]
    y = grid.y.ravel()[keep]

    def ev(p):
        p = np.clip(p, 1e-6, 1 - 1e-6)
        return float(((p > 0.5) == (y > 0.5)).mean()), float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())

    h0l, l0l = ev(lr.proba(X, g))
    h0g, l0g = ev(gb.proba(C))
    rows = []
    for j, f in enumerate(feats):
        acc = []
        for _ in range(reps):
            perm = rng.permutation(len(X))
            Xs = X.copy()
            Xs[:, j] = X[perm, j]
            Cs = C.copy()
            Cs[:, j] = C[perm, j]
            hl, ll = ev(lr.proba(Xs, g))
            hg, lg = ev(gb.proba(Cs))
            acc.append(((l0l - ll) * -1000, (h0l - hl) * 100, (l0g - lg) * -1000, (h0g - hg) * 100))
        a = np.array(acc)
        rows.append({"feature": f, "lr_ll": a[:, 0].mean(), "lr_ll_sd": a[:, 0].std(), "lr_hit": a[:, 1].mean(),
                     "gbt_ll": a[:, 2].mean(), "gbt_ll_sd": a[:, 2].std(), "gbt_hit": a[:, 3].mean()})
    df = pd.DataFrame(rows)
    df["rank"] = (df["lr_ll"].rank(ascending=False) + df["gbt_ll"].rank(ascending=False)) / 2
    df = df.sort_values(["rank", "lr_ll"], ascending=[True, False]).reset_index(drop=True)
    df.attrs.update(lr_hit=h0l, gbt_hit=h0g, n=int(len(keep)))
    return df


# ------------------------------------------------------------------------------------------------ scoring


def _rows(grid: Grid, period: str | None = None):
    st = grid.steps
    sel = st["scored"].to_numpy()
    if period:
        sel = sel & (st["period"].to_numpy() == period)
    m = grid.mask & sel[:, None]
    return m


def hits_matrix(grid: Grid, res: dict) -> tuple[np.ndarray, np.ndarray, list]:
    """(T, S, L + nb) hit indicators (coin = 0.5), names."""
    y = grid.y > 0.5
    H = np.concatenate([(res["P"] == y[:, :, None]), (res["base"] > 0.5) == y[:, :, None]],
                       axis=2).astype(np.float32)
    H[:, :, len(res["names"])] = 0.5  # coin
    return H, y, res["names"] + BASELINES


def day_stats(h: np.ndarray, day: np.ndarray) -> tuple[float, float, int]:
    """Mean of h and its day-clustered SE (ratio estimator)."""
    n = len(h)
    if n == 0:
        return float("nan"), float("nan"), 0
    p = h.mean()
    u, inv = np.unique(day, return_inverse=True)
    r = np.bincount(inv, weights=h - p)
    D_ = len(u)
    se = math.sqrt((r ** 2).sum() * D_ / max(D_ - 1, 1)) / n
    return float(p), float(se), n


def paired(hl: np.ndarray, hb: np.ndarray, day: np.ndarray) -> dict:
    d = hl - hb
    mean, se, n = day_stats(d, day)
    z = mean / se if se and se > 0 else float("nan")
    b = float(((hl == 1) & (hb == 0)).sum())
    c = float(((hl == 0) & (hb == 1)).sum())
    if np.all(hb == 0.5):  # coin: binomial z
        zm = (hl.sum() - 0.5 * n) / math.sqrt(0.25 * n) if n else float("nan")
    else:
        zm = (b - c) / math.sqrt(b + c) if b + c > 0 else float("nan")
    return {"diff": mean, "z_day": z, "z_mcnemar": zm, "n": n}


def n_tests_per_metric(res: dict, n_sym: int) -> int:
    """Main learners + the two per-ticker comparisons (pooled and own model) per ticker + the diagnostics."""
    return len(MAIN) + 2 * n_sym + sum(n.startswith("ind:") for n in res["names"])


def score(grid: Grid, res: dict, n_metrics: int = 2) -> dict:
    n_tests = n_tests_per_metric(res, len(grid.symbols)) * n_metrics
    H, y, allnames = hits_matrix(grid, res)
    L = len(res["names"])
    st = grid.steps
    day_t = np.repeat(st["date"].to_numpy()[:, None], len(grid.symbols), axis=1)
    out = {"names": allnames, "learners": res["names"], "baselines": BASELINES, "bar": bar_for(n_tests),
           "n_tests": n_tests, "periods": {}}
    for per in ("TRAIN", "VALID", "FORWARD"):
        m = _rows(grid, per)
        if not m.any():
            continue
        Hm = H[m]
        days = day_t[m]
        rate = {}
        for j, nm in enumerate(allnames):
            p, se, n = day_stats(Hm[:, j], days)
            rate[nm] = {"hit": p, "se": se, "n": n}
        bb = max(BASELINES, key=lambda b: rate[b]["hit"])
        jb = allnames.index(bb)
        vs = {nm: paired(Hm[:, j], Hm[:, jb], days) for j, nm in enumerate(res["names"])}
        vs_coin = {nm: paired(Hm[:, j], np.full(len(Hm), 0.5), days) for j, nm in enumerate(res["names"])}
        out["periods"][per] = {"rate": rate, "best_baseline": bb, "vs_best": vs, "vs_coin": vs_coin,
                               "base_rate": float(y[m].mean()), "n": int(m.sum()),
                               "sessions": int(len(np.unique(days)))}
    # VALID breakdowns
    m = _rows(grid, "VALID")
    if m.any():
        tod = grid.X[:, :, grid.extra["features"].index("tod")]
        tb = np.searchsorted(np.array([60, 150, 270, 330]), tod, side="left")
        out["by_tod"] = {TOD_NAMES[i]: {nm: float(H[m & (tb == i)][:, j].mean()) for j, nm in enumerate(allnames)}
                         for i in range(5) if (m & (tb == i)).any()}
        out["by_symbol"] = per_ticker(grid, H, allnames, day_t)
        o2c = grid.extra["spy_o2c"]
        tr_days = st.loc[(st["period"] == "TRAIN") & st["scored"], "date"].unique()
        lo, hi = np.quantile(o2c.reindex(tr_days).dropna().to_numpy(), [1 / 3, 2 / 3])
        dtype = o2c.map(lambda v: "down" if v <= lo else ("up" if v >= hi else "flat"))
        dt = np.repeat(st["date"].map(dtype).to_numpy()[:, None], len(grid.symbols), axis=1)
        out["by_daytype"] = {k: {nm: float(H[m & (dt == k)][:, j].mean()) for j, nm in enumerate(allnames)} |
                             {"_n": int((m & (dt == k)).sum())} for k in ("up", "flat", "down") if (m & (dt == k)).any()}
        out["daytype_cuts"] = (float(lo), float(hi))
    # per-session hit rates (for the chart and the 65% check)
    sess_hit = {}
    sm = _rows(grid, None)
    dates = st["date"].to_numpy()
    for j, nm in enumerate(allnames):
        num = (H[:, :, j] * sm).sum(1)
        den = sm.sum(1)
        s = pd.DataFrame({"date": dates, "num": num, "den": den}).groupby("date")[["num", "den"]].sum()
        sess_hit[nm] = s
    out["_sess"] = sess_hit
    out["consistent"] = {nm: consistency(sess_hit[nm], st) for nm in res["names"]}
    return out


def per_ticker(grid: Grid, H: np.ndarray, allnames: list, day_t: np.ndarray) -> dict:
    """Each ticker's hit rates (TRAIN / VALID), its own best VALID baseline, the day-clustered z of the pooled and
    the per-ticker model against it, and the 65% consistency check per ticker."""
    st = grid.steps
    out = {}
    jl = {n: allnames.index(n) for n in ("pooled:logreg", "ticker:logreg")}
    for i, s in enumerate(grid.symbols):
        d = {}
        for per in ("TRAIN", "VALID"):
            m = _rows(grid, per)[:, i]
            if not m.any():
                continue
            Hm, days = H[:, i][m], day_t[:, i][m]
            rate = {nm: float(Hm[:, j].mean()) for j, nm in enumerate(allnames)}
            bb = max(BASELINES, key=lambda b: rate[b])
            jb = allnames.index(bb)
            d[per] = {"rate": rate, "n": int(m.sum()), "best_baseline": bb,
                      "z": {n: paired(Hm[:, j], Hm[:, jb], days)["z_day"] for n, j in jl.items()}}
        sm = _rows(grid, None)[:, i]
        cons = {}
        for n, j in jl.items():
            sh = pd.DataFrame({"date": st["date"].to_numpy(), "num": H[:, i, j] * sm, "den": sm.astype(float)})
            cons[n] = consistency(sh.groupby("date")[["num", "den"]].sum(), st)
        d["consistent"] = cons
        if "VALID" in d:
            out[s] = d
    return out


def consistency(s: pd.DataFrame, st: pd.DataFrame) -> dict:
    vd = set(st.loc[(st["period"] == "VALID"), "date"])
    v = s[s.index.isin(vd)]
    if len(v) < CONSIST_WIN:
        return {"windows": 0, "share": float("nan"), "max": float("nan"), "pass": False}
    num = v["num"].rolling(CONSIST_WIN).sum().dropna()
    den = v["den"].rolling(CONSIST_WIN).sum().dropna()
    r = num / den
    share = float((r >= CONSIST_HIT).mean())
    return {"windows": int(len(r)), "share": share, "max": float(r.max()), "min": float(r.min()),
            "pass": share >= CONSIST_SHARE}


# ------------------------------------------------------------------------------------------------ report


def _pct(x, d=2):
    return "—" if x is None or not np.isfinite(x) else f"{x * 100:.{d}f}%"


def _f(x, d=2):
    return "—" if x is None or not np.isfinite(x) else f"{x:.{d}f}"


def chart(sc: dict, grid: Grid, path: Path, metric: str, top: list):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    st = grid.steps
    fig, ax = plt.subplots(figsize=(11, 4.2), dpi=110)
    colors = ["#2a6fdb", "#d1495b", "#00a37a", "#8a8a8a"]
    for nm, col in zip(top, colors):
        s = sc["_sess"][nm]
        s = s[s.index.isin(set(st.loc[st["scored"], "date"]))]
        r = (s["num"].rolling(5).sum() / s["den"].rolling(5).sum())
        ax.plot(pd.to_datetime(r.index), r.to_numpy() * 100, lw=1.3 if nm != top[-1] else 1.0, color=col,
                ls="-" if nm != top[-1] else "--", label=nm)
    for per, c in (("VALID", "#f2e8c9"), ("FORWARD", "#dce9f5")):
        d = st.loc[st["period"] == per, "date"]
        if len(d):
            ax.axvspan(pd.to_datetime(d.min()), pd.to_datetime(d.max()), color=c, alpha=0.6, lw=0, label=per)
    ax.axhline(50, color="#444", lw=0.6)
    ax.axhline(65, color="#d1495b", lw=0.6, ls=":", label="65% goal")
    ax.set_ylabel("hit rate, rolling 5 sessions (%)")
    ax.set_title(f"Hunch {metric}: {M.DESCRIBE[metric]} — rolling 1-week hit rate. {DISCLAIMER}", fontsize=9)
    ax.legend(fontsize=7, ncol=6, loc="upper left")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def report(sc: dict, grid: Grid, res: dict, metric: str, outdir: Path, universe_note: str, runtime_s: float) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    feats = grid.extra["features"]
    V = sc["periods"].get("VALID", {})
    Tr = sc["periods"].get("TRAIN", {})
    Fw = sc["periods"].get("FORWARD", {})
    bar = sc["bar"]
    learners = res["names"]
    bb = V["best_baseline"]
    main_r = sorted(MAIN, key=lambda n: -V["rate"][n]["hit"])
    best = main_r[0]
    png = outdir / f"{metric}_rolling.png"
    chart(sc, grid, png, metric, ["pooled:logreg", "pooled:gbt", "ticker:logreg", bb])
    sel_v = (grid.steps["period"] == "VALID").to_numpy()
    imp = importance(grid, res, "TRAIN", sel_v)
    beats = [n for n in MAIN if V["vs_best"][n]["z_day"] >= bar]
    cons = [n for n in MAIN if sc["consistent"][n]["pass"]]
    tick = sc.get("by_symbol", {})
    tick_cons = [f"{s} ({n})" for s, d in tick.items() for n, c in d["consistent"].items() if c["pass"]]
    tick_beat = [f"{s} ({n})" for s, d in tick.items() for n, z in d["VALID"]["z"].items() if z >= bar]
    L = []
    w = L.append
    w(f"# Hunch {metric} — {M.DESCRIBE[metric]}\n")
    w(f"*{DISCLAIMER} Research tool only: Hunch places no orders and changes nothing in config/ or the trading path.*\n")
    w("## Verdict (failures first)\n")
    vb = V["vs_best"][best]
    cmax = max(sc["consistent"][n]["max"] for n in MAIN)
    w(f"- **Consistent 65%+: {'YES — ' + ', '.join(cons) if cons else 'NO'}** (pooled models); per ticker: "
      f"{', '.join(tick_cons) if tick_cons else '**none of the ' + str(len(tick)) + ' tickers**'}. Definition: rolling "
      f"{CONSIST_WIN}-session hit rate ≥ 65% in ≥ 90% of VALID windows. Highest VALID 20-session window of any main "
      f"pooled learner: {_pct(cmax, 1)}.")
    w(f"- **Hunch (best combined learner) on VALID: `{best}` {_pct(V['rate'][best]['hit'])}** "
      f"(±{_pct(V['rate'][best]['se'])} day-clustered SE, n = {V['rate'][best]['n']:,} guesses, {V['sessions']} "
      f"sessions) vs **best baseline `{bb}` {_pct(V['rate'][bb]['hit'])}**: {vb['diff'] * 100:+.2f} pp, "
      f"day-clustered z = {_f(vb['z_day'])} (McNemar z = {_f(vb['z_mcnemar'])}). Bar: z ≥ {bar:.2f} "
      f"(N = {sc['n_tests']} tests).")
    w(f"- Main learners beating the best baseline at the bar on VALID: "
      f"{', '.join(f'`{n}`' for n in beats) if beats else '**none**'}. Per-ticker (pooled or own model vs that "
      f"ticker's best baseline): {', '.join(tick_beat) if tick_beat else '**none**'}.")
    w(f"- Base rate ('yes' share): TRAIN {_pct(Tr.get('base_rate'))}, VALID {_pct(V['base_rate'])}. "
      f"{_pct(grid.extra['ties'], 1)} of guess slots have the next close exactly equal to this close (a tie counts as "
      "'not higher'), which is why the base-rate baseline ('no') sits above 50% on M1.")
    w(f"- Tests counted per metric: {len(MAIN)} main learners + 2 × {len(grid.symbols)} per-ticker comparisons + "
      f"{sum(n.startswith('ind:') for n in learners)} single-indicator diagnostics = {sc['n_tests'] // 2}; × 2 metrics "
      f"(M1, M3) = {sc['n_tests']}. One configuration per learner, hyper-parameters fixed in advance "
      f"(mcf/hunch/learners.py); nothing tuned on VALID. The top-{TOPK} model's features were picked on TRAIN: "
      f"{', '.join(res['topk'])}.\n")
    w("## Data and protocol\n")
    w(universe_note)
    w(f"- Periods: TRAIN {D.TRAIN[0]}..{D.TRAIN[1]} (locked block {D.LOCKED[0]}..{D.LOCKED[1]} never read — "
      f"filtered inside the parquet read), VALID {D.VALID[0]}..{D.VALID[1]}, FORWARD after that (reported "
      f"separately). Sessions scored: TRAIN {Tr.get('sessions')}, VALID {V.get('sessions')}, FORWARD "
      f"{Fw.get('sessions', 0)}; the first {WARMUP_SESS} sessions are warm-up (guessed, not scored); the first "
      f"session after the locked gap is an indicator warm-up (not guessed).")
    w("- Guesses: every 3-min bar closing 09:51..15:51 ET (121 a session per ticker); each uses data up to that bar's "
      "close only and is scored on the next bar. Walk-forward, online: the logistic learners update after every "
      "scored guess; the boosted trees refit every 20 sessions on the previous 120 sessions only.")
    w("- Learners: **pooled:logreg** = Hunch, all features, shared weights across tickers (+ ticker intercept); "
      "**pooled:gbt** = light boosted trees, all features, pooled; **pooled:top8** = pooled logreg on the TRAIN top-8 "
      "features; **ticker:logreg** = one Hunch instance per ticker (own weights, own data). Single-indicator learners "
      "are a diagnostic only.")
    w(f"- Run time {runtime_s:.0f} s. No rule / config change in research/ledger.jsonl bears on this study: it reads "
      "raw market bars, not setup results.\n")
    w("## Hunch: combined learners vs baselines\n")
    w(f"Day-clustered SE in brackets; z vs the best baseline (VALID: `{bb}`; TRAIN: `{Tr.get('best_baseline')}`), "
      f"day-clustered. ✔ = z ≥ {bar:.2f}.\n")
    w("| learner | TRAIN hit | VALID hit | FORWARD hit | VALID − best base (pp) | z vs best | McNemar z | z vs coin | "
      "20-sess ≥65% share | best 20-sess |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for n in main_r:
        vv, vc = V["vs_best"][n], V["vs_coin"][n]
        cs = sc["consistent"][n]
        fh = Fw["rate"][n]["hit"] if Fw else float("nan")
        note = " (in-sample feature pick)" if n.startswith("pooled:top") else ""
        w(f"| `{n}` | {_pct(Tr['rate'][n]['hit'])}{note} | {_pct(V['rate'][n]['hit'])} ({_pct(V['rate'][n]['se'])}) | "
          f"{_pct(fh)} | {vv['diff'] * 100:+.2f} | {_f(vv['z_day'])}{' ✔' if vv['z_day'] >= bar else ''} | "
          f"{_f(vv['z_mcnemar'])} | {_f(vc['z_day'])} | {_pct(cs['share'], 0)} | {_pct(cs['max'], 1)} |")
    for b in BASELINES:
        fh = Fw["rate"][b]["hit"] if Fw else float("nan")
        w(f"| baseline `{b}` | {_pct(Tr['rate'][b]['hit'])} | {_pct(V['rate'][b]['hit'])} | {_pct(fh)} | | | | | | |")
    w("\n## The 20+ Hunch instances: per ticker (VALID, TRAIN in brackets)\n")
    w(f"Each ticker's own best VALID baseline; z (day-clustered) of the pooled model and of that ticker's own model "
      f"against it. ✔ = z ≥ {bar:.2f}. 65% = share of VALID 20-session windows ≥ 65%.\n")
    w("| ticker | guesses | pooled:logreg | ticker:logreg | best baseline | z pooled | z own | 65% pooled | 65% own |")
    w("|---|---|---|---|---|---|---|---|---|")
    for s, d in sorted(tick.items(), key=lambda kv: -kv[1]["VALID"]["rate"]["pooled:logreg"]):
        v, t = d["VALID"], d.get("TRAIN", {"rate": {}})
        tr = lambda n: f" ({_pct(t['rate'].get(n), 1)})" if t["rate"] else ""  # noqa: E731
        zp, zo = v["z"]["pooled:logreg"], v["z"]["ticker:logreg"]
        w(f"| {s} | {v['n']:,} | {_pct(v['rate']['pooled:logreg'])}{tr('pooled:logreg')} | "
          f"{_pct(v['rate']['ticker:logreg'])}{tr('ticker:logreg')} | `{v['best_baseline']}` "
          f"{_pct(v['rate'][v['best_baseline']])} | {_f(zp)}{' ✔' if zp >= bar else ''} | {_f(zo)}"
          f"{' ✔' if zo >= bar else ''} | {_pct(d['consistent']['pooled:logreg']['share'], 0)} | "
          f"{_pct(d['consistent']['ticker:logreg']['share'], 0)} |")
    w("\n## Indicator trust table (primary: permutation importance of the combined model)\n")
    w(f"The end-of-TRAIN pooled logreg and pooled GBT, frozen, scored on every VALID guess (frozen hit: logreg "
      f"{_pct(imp.attrs['lr_hit'])}, GBT {_pct(imp.attrs['gbt_hit'])}, n = {imp.attrs['n']:,}); each indicator "
      "shuffled across the VALID guesses in turn (3 repeats; ± = sd over repeats). Higher log-loss increase = the "
      "model leans on it out of sample. Ranked by the mean of the two models' ranks. A negative value means "
      "shuffling the indicator *helped* on VALID: the model's use of it learned on TRAIN does not carry over. "
      "Mean weight = the pooled logreg's average standardized weight over VALID (sign = push toward 'yes').\n")
    wv = res["w_valid"].mean(0) if res["w_valid"] is not None else np.full(len(feats), np.nan)
    w("| rank | indicator | logreg log-loss ↑ ×1000 | logreg hit drop (pp) | GBT log-loss ↑ ×1000 | GBT hit drop (pp) | "
      "mean weight | TRAIN rank |")
    w("|---|---|---|---|---|---|---|---|")
    trr = {f: i + 1 for i, f in enumerate(res["imp_train"]["feature"])}
    for i, r in imp.iterrows():
        j = feats.index(r["feature"])
        w(f"| {i + 1} | {r['feature']} | {r['lr_ll']:+.3f} ± {r['lr_ll_sd']:.3f} | {r['lr_hit']:+.2f} | "
          f"{r['gbt_ll']:+.3f} ± {r['gbt_ll_sd']:.3f} | {r['gbt_hit']:+.2f} | {wv[j]:+.4f} | {trr[r['feature']]} |")
    inds = [n for n in learners if n.startswith("ind:")]
    if inds:
        w("\n**Diagnostic: single-indicator learners** (each indicator alone, binned; VALID hit [95% CI], vs best "
          "baseline). Not the approach — a cross-check of the table above.\n")
        w("| indicator | VALID hit [95% CI] | TRAIN hit | vs best base (pp) | z |")
        w("|---|---|---|---|---|")
        for n in sorted([n for n in learners if n.startswith("ind:")], key=lambda n: -V["rate"][n]["hit"]):
            r, vv = V["rate"][n], V["vs_best"][n]
            w(f"| {n[4:]} | {_pct(r['hit'])} [{_pct(r['hit'] - 1.96 * r['se'])}, {_pct(r['hit'] + 1.96 * r['se'])}] | "
              f"{_pct(Tr['rate'][n]['hit'])} | {vv['diff'] * 100:+.2f} | {_f(vv['z_day'])} |")
    cols = main_r + [bb]
    w("\n## VALID by time of day\n")
    w("| bar close | " + " | ".join(f"`{c}`" for c in cols) + " |")
    w("|---" * (len(cols) + 1) + "|")
    for t, d in sc.get("by_tod", {}).items():
        w(f"| {t} | " + " | ".join(_pct(d[c]) for c in cols) + " |")
    w("\n## VALID by SPY day type\n")
    lo, hi = sc.get("daytype_cuts", (np.nan, np.nan))
    w(f"SPY session open-to-close terciles, cut points from TRAIN ({lo:+.2f}% / {hi:+.2f}%). Known only after the "
      "close: a report split, never a feature.\n")
    w("| day type | guesses | " + " | ".join(f"`{c}`" for c in cols) + " |")
    w("|---" * (len(cols) + 2) + "|")
    for t, d in sc.get("by_daytype", {}).items():
        w(f"| {t} | {d['_n']:,} | " + " | ".join(_pct(d[c]) for c in cols) + " |")
    w(f"\n## Stability\n\n![rolling 1-week hit rate]({png.name})\n")
    w(f"Rolling 5-session hit rate of the combined learners and the best baseline (`{bb}`, dashed); VALID and "
      "FORWARD shaded.\n")
    w(f"*{DISCLAIMER}*")
    md = outdir / f"{metric}_report.md"
    md.write_text("\n".join(L) + "\n")
    summ = {"metric": metric, "best": best, "best_baseline": bb, "bar": bar, "n_tests": sc["n_tests"],
            "valid": {n: V["rate"][n]["hit"] for n in learners + BASELINES},
            "train": {n: Tr["rate"][n]["hit"] for n in learners + BASELINES},
            "z_vs_best_valid": {n: V["vs_best"][n]["z_day"] for n in learners},
            "consistent": {n: sc["consistent"][n] for n in MAIN}, "beats": beats, "ticker_beats": tick_beat,
            "topk": res["topk"], "trust_top": list(imp["feature"][:8]), "disclaimer": DISCLAIMER}
    (outdir / f"{metric}_summary.json").write_text(json.dumps(summ, indent=1, default=float))
    return md
