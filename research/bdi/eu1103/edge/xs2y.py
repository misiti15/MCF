"""eu1103/edge: the two pre-declared 2-year tests (PLAN.md). Pass 1 builds one row per eligible name-day-t with |z| >= 0.5
(plus per-day baseline sums for every eligible name); pass 2 selects and scores. Usage:
  python xs2y.py build <scratch>    -> <scratch>/xs_rows.parquet, <scratch>/xs_base.parquet
  python xs2y.py score <scratch>    -> results_2y.csv, results_2y.json (this folder)
The locked block 2024-11-01..2025-02-28 is dropped by the parquet read filter and asserted absent.
Educational only - not financial advice."""
import json, math, sys
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.parquet as pq

ROOT = Path("/home/user/MCF"); OUT = Path(__file__).parent
H = ROOT / "data" / "cache_hist" / "1Min"
TZ = "America/New_York"
L0, L1 = pd.Timestamp("2024-11-01", tz=TZ), pd.Timestamp("2025-03-01", tz=TZ)
END = pd.Timestamp("2026-10-06", tz=TZ)
TS = {940: 10, 945: 15, 950: 20}          # decision bar close -> entry bar index (bar i starts 09:30 + i min)
EX = {1030: 60, 1555: 385}                # exit at the open of this bar
NB = 390


def load(sym):
    t = pq.read_table(H / f"{sym}.parquet", filters=[[("__index_level_0__", "<", L0)], [("__index_level_0__", ">=", L1)]]).to_pandas()
    t = t[t.index < END]
    assert not ((t.index >= L0) & (t.index < L1)).any()
    mi = (t.index.hour - 9) * 60 + t.index.minute - 30
    t = t[(mi >= 0) & (mi < NB)]
    d = t.index.normalize().tz_localize(None); mi = (t.index.hour - 9) * 60 + t.index.minute - 30
    days = pd.DatetimeIndex(sorted(set(d)))
    pos = days.get_indexer(d)
    M = {k: np.full((len(days), NB), np.nan) for k in ("open", "high", "low", "close", "volume")}
    for k in M:
        M[k][pos, mi] = t[k].to_numpy()
    return days, M


def ffill(a):
    m = np.isnan(a); idx = np.where(~m, np.arange(a.shape[1]), 0); np.maximum.accumulate(idx, axis=1, out=idx)
    return a[np.arange(a.shape[0])[:, None], idx]


def build(S):
    syms = [s.strip() for s in open(ROOT / "research" / "lab_symbols.txt") if s.strip()][:int(__import__("os").environ.get("LIMIT", "99999"))]
    sd, SM = load("SPY"); sc = ffill(SM["close"]); so = SM["open"][:, 0]
    spy = pd.DataFrame({"so": so}, index=sd)
    spy5 = np.diff(sc[:, 30:386:5], axis=1) / sc[:, 30:381:5]       # 10:00..15:55 5-min returns
    rows, base = [], []
    for n, sym in enumerate(syms):
        if sym in ("SPY",) or not (H / f"{sym}.parquet").exists():
            continue
        try:
            days, M = load(sym)
        except Exception as e:
            print("skip", sym, e); continue
        if len(days) < 30:
            continue
        j = sd.get_indexer(days); okd = j >= 0
        days = days[okd]; M = {k: v[okd] for k, v in M.items()}; j = j[okd]
        C = ffill(M["close"]); O = M["open"]; Hh, Ll, V = M["high"], M["low"], np.nan_to_num(M["volume"])
        dopen = O[:, 0]; dclose = C[:, -1]; dh = np.nanmax(Hh, 1); dl = np.nanmin(Ll, 1)
        pc = np.r_[np.nan, dclose[:-1]]
        tr = np.nanmax(np.c_[dh - dl, np.abs(dh - pc), np.abs(dl - pc)], 1)
        atr = pd.Series(tr).rolling(14, min_periods=10).mean().shift(1).to_numpy()
        adv = pd.Series(dclose * V.sum(1)).rolling(20, min_periods=10).mean().shift(1).to_numpy()
        s5 = np.diff(C[:, 30:386:5], axis=1) / C[:, 30:381:5]; m5 = spy5[j]
        ok5 = np.isfinite(s5) & np.isfinite(m5)
        cov = np.where(ok5, s5 * m5, 0).sum(1); var = np.where(ok5, m5 * m5, 0).sum(1)
        b = (pd.Series(cov).rolling(20, min_periods=10).sum().shift(1) / pd.Series(var).rolling(20, min_periods=10).sum().shift(1)).to_numpy()
        beta = np.clip(0.7 * b + 0.3, 0, 3)
        elig = (pc >= 5) & (adv >= 20e6) & (atr / pc >= 0.01) & np.isfinite(beta) & np.isfinite(dopen)
        for t, ei in TS.items():
            cv = np.cumsum(V[:, :ei], 1)[:, -1]
            rv = cv / pd.Series(cv).rolling(14, min_periods=10).mean().shift(1).to_numpy()
            pt = C[:, ei - 1]; st = sc[j, ei - 1]
            idio = (pt / dopen - 1) - beta * (st / so[j] - 1)
            z = idio / (atr / pc)
            ent = O[:, ei]; spe = SM["open"][j, ei]
            cost_in = (0.01 + 1e-4 * ent) * (2.1 if t < 950 else 1.4)
            Ru = 0.5 * atr
            for side in (1, -1):
                stop = ent - side * Ru
                for ex, xi in EX.items():
                    seg_l, seg_h, seg_o = Ll[:, ei:xi], Hh[:, ei:xi], O[:, ei:xi]
                    hit = (seg_l <= stop[:, None]) if side > 0 else (seg_h >= stop[:, None])
                    hit = np.nan_to_num(hit.astype(float)).astype(bool)
                    any_ = hit.any(1); k = hit.argmax(1)
                    o_k = seg_o[np.arange(len(k)), k]
                    sfill = np.where(side > 0, np.fmin(o_k, stop), np.fmax(o_k, stop))
                    xo = O[:, xi]; xs = SM["open"][j, xi]
                    if ex == 1555:
                        xo = np.where(np.isnan(xo), C[:, xi], xo)
                    exitp = np.where(any_, sfill, xo)
                    # SPY price when the stock leg closes (stop bar open, else the exit bar open)
                    so_k = SM["open"][j[:, None], np.arange(ei, xi)[None, :]][np.arange(len(k)), k]
                    sx = np.where(any_, so_k, xs)
                    cost = cost_in + 0.01 + 1e-4 * exitp + np.where(any_, 0.02, 0)
                    R = (side * (exitp - ent) - cost) / Ru
                    hedge = (-side * beta * ent * (sx / spe - 1) - beta * ent * 2 * (1e-4 + 0.01 / spe)) / Ru
                    good = elig & np.isfinite(R) & np.isfinite(z) & np.isfinite(rv) & np.isfinite(hedge)
                    key = f"{t}_{ex}_{side}"
                    for bk, bm in (("lo", rv < 1.5), ("hi", rv >= 3)):
                        m = good & bm
                        base.append(pd.DataFrame({"date": days[m], "key": key, "bucket": bk, "R": R[m], "Rh": R[m] + hedge[m]}))
                    sel = good & (np.abs(z) >= 0.5)
                    rows.append(pd.DataFrame({"date": days[sel], "symbol": sym, "t": t, "ex": ex, "side": side, "z": z[sel].astype("float32"),
                                              "rvol": rv[sel].astype("float32"), "R": R[sel].astype("float32"),
                                              "hedge": hedge[sel].astype("float32"), "stopped": any_[sel]}))
        if n % 100 == 0:
            print(n, sym, len(rows), flush=True)
    X = pd.concat(rows, ignore_index=True)
    X["date"] = X.date.dt.date
    X.to_parquet(S / "xs_rows.parquet")
    Bs = pd.concat(base, ignore_index=True).groupby(["date", "key", "bucket"]).agg(sumR=("R", "sum"), sumRh=("Rh", "sum"), n=("R", "size")).reset_index()
    Bs["date"] = Bs.date.dt.date
    Bs.to_parquet(S / "xs_base.parquet")
    print("rows", len(X), "base", len(Bs))


def tclust(df, col):
    g = df.groupby("date")[col].agg(["sum", "size"]); mu = df[col].mean()
    se = math.sqrt(((g["sum"] - g["size"] * mu) ** 2).sum()) / len(df)
    return mu / se if se > 0 else float("nan")


def score(S):
    sys.path.insert(0, str(ROOT / "research" / "history2y")); import lib
    X = pd.read_parquet(S / "xs_rows.parquet"); Bs = pd.read_parquet(S / "xs_base.parquet")
    reg = lib.regimes().reset_index(); reg["date"] = pd.to_datetime(reg["date"]).dt.date
    rcol = "regime"
    rmap = dict(zip(reg.date, reg[rcol]))
    out, keep = [], {}
    tests = {"A_quiet_fade": ("lo", -1), "B_inplay_ride": ("hi", 1)}
    for name, (bk, dirn) in tests.items():
        Xb = X[(X.rvol < 1.5) if bk == "lo" else (X.rvol >= 3)]
        for t in TS:
            for ex in EX:
                # side for the selected name: fade = -sign(z), ride = +sign(z); rows exist for both sides
                c = Xb[(Xb.t == t) & (Xb.ex == ex)]
                c = c[c.side == (dirn * np.sign(c.z)).astype(int)]
                c = c.assign(az=c.z.abs()).sort_values(["date", "az"], ascending=[True, False]).groupby("date").head(10)
                for hedged in (False, True):
                    d = c.assign(r=c.R + (c.hedge if hedged else 0))
                    # baseline: other eligible names, same day / t / exit / side / bucket
                    bb = Bs[Bs.bucket == bk].set_index(["date", "key"])
                    keyv = [f"{t}_{ex}_{s}" for s in d.side]
                    idx = list(zip(d.date, keyv))
                    bsum = bb.reindex(idx)
                    col = "sumRh" if hedged else "sumR"
                    base_mu = ((bsum[col].to_numpy() - d.r.to_numpy()) / (bsum["n"].to_numpy() - 1))
                    d = d.assign(base=base_mu, diff=d.r.to_numpy() - base_mu, regime=d.date.map(rmap),
                                 split=np.where(pd.to_datetime(d.date) >= "2026-01-01", "VALID", "TRAIN"),
                                 month=pd.to_datetime(d.date).dt.strftime("%Y-%m"))
                    cfg = f"{name}|t{t}|x{ex}|{'hedged' if hedged else 'raw'}"
                    keep[cfg] = d
                    for sp, g in d.groupby("split"):
                        dd = g.groupby("date").r.sum(); b = dd.idxmax()
                        mo = g.groupby("month").r.mean()
                        rr = {"config": cfg, "split": sp, "n": len(g), "sessions": g.date.nunique(),
                              "avgR": g.r.mean(), "t": tclust(g, "r"), "win": (g.r > 0).mean(),
                              "avgR_wo_best": (dd.sum() - dd.max()) / max(1, len(g) - (g.date == b).sum()),
                              "best_share": dd.max() / dd.sum() if dd.sum() > 0 else np.nan,
                              "vs_base": g["diff"].mean(), "t_vs_base": tclust(g.dropna(subset=["diff"]), "diff"),
                              "wf_pos_months": (mo > 0).mean(), "stopped": g.stopped.mean(),
                              "green_days": (dd > 0).mean()}
                        for rg in ("up", "flat", "down"):
                            q = g[g.regime == rg]; rr[f"{rg}_R"] = q.r.mean() if len(q) else np.nan; rr[f"{rg}_n"] = len(q)
                        out.append(rr)
    R = pd.DataFrame(out); R.round(4).to_csv(OUT / "results_2y.csv", index=False)
    print(R.round(3).to_string())
    json.dump({"configs": int(R.config.nunique()), "regime_col": rcol}, open(OUT / "results_2y.json", "w"))
    pd.concat([v.assign(config=k) for k, v in keep.items()]).to_parquet(S / "xs_selected.parquet")


if __name__ == "__main__":
    {"build": build, "score": score}[sys.argv[1]](Path(sys.argv[2]))
