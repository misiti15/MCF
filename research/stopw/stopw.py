"""STOPW (guild Scout plan research/stopw/PLAN.md, frozen 2026-11-09 17:40 ET before any score): minimum stop width in bps at
the same $ risk. Every 2-year lab trade (BEREPLAY sample: bt_lab1104 lists + optional GEN hold lists) is walked on 1-minute
bars with the current stop (BASE) and with D' = max(D, X bp x entry): W60 / W80 / W100 (target price unchanged) and W80S
(target scaled by D'/D). Results in units of each trade's own risk; costs as bt_all. Family N 77 -> BAR90 2.65 on delta t.
    python stopw.py <hold_lists_dir|-> [procs] > stopw_out.txt          python stopw.py --selftest
Locked block 2024-11-01..2025-02-28 dropped at every read (asserted). Educational only - not financial advice."""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path("/home/user/MCF"); HERE = Path(__file__).resolve().parent
N_FAMILY = 77
SL, BP, SX = 0.01, 1e-4, 0.02
VARS = [("W60", 60, False), ("W80", 80, False), ("W100", 100, False), ("W80S", 80, True)]


def first(mask):
    return int(np.argmax(mask)) if mask.any() else 10 ** 9


def walk(o, h, l, c, e, s, D, U, trail=False):
    """= research/bereplay walk() for modes fixed / trail -> (exit price, kind 0 flat / 1 stop / 2 target). Stop-first."""
    n = len(c)
    if n == 0: return e, 0
    fav = (h - e) if s > 0 else (e - l)
    if trail:
        cb = np.maximum.accumulate(c) if s > 0 else np.minimum.accumulate(c)
        prev = np.r_[e, cb[:-1]]
        on = s * (prev - e) >= D
        lev = np.where(on, prev - s * D, e - s * D)
        lev = np.maximum(lev, e - D) if s > 0 else np.minimum(lev, e + D)
    else:
        lev = np.full(n, e - s * D)
    hit = (l <= lev) if s > 0 else (h >= lev)
    i_s = first(hit); i_t = first(fav >= U) if np.isfinite(U) else 10 ** 9
    if i_s <= i_t and i_s < n:
        return (o[i_s] if s * (o[i_s] - lev[i_s]) <= 0 else lev[i_s]), 1
    if i_t < n: return e + s * U, 2
    return c[-1], 0


def r_of(o, h, l, c, e, s, D, U, trail, tier, ecost):
    """net result in units of the stop distance D (= the trade's $ risk at equal-risk sizing)."""
    px, kd = walk(o, h, l, c, e, s, D, U, trail)
    xcost = (0.0 if kd == 2 else SL + px * BP) + (SX if kd == 1 else 0.0)
    return (s * (px - e) - tier * (ecost + xcost)) / D, kd


def widen(D, U, e, X, scale):
    """D' = max(D, X bp x e); U unchanged or scaled by D'/D."""
    D2 = max(D, X / 1e4 * e)
    return D2, (U * D2 / D if (scale and np.isfinite(U)) else U)


def selftest():
    e = 50.0; D = 0.2; U = 0.2                    # 40bp stop, 1R target (t1s1)
    D2, U2 = widen(D, U, e, 80, False); assert abs(D2 - 0.4) < 1e-9 and U2 == U
    D3, U3 = widen(D, U, e, 80, True); assert abs(U3 - 0.4) < 1e-9
    assert widen(0.6, 0.6, e, 80, False)[0] == 0.6                  # 120bp stop untouched
    # path: dips to 49.75 (stops the 40bp stop at 49.80) then rallies to 50.25 (target 50.20)
    o = np.array([50.0, 49.9, 49.8, 50.1, 50.2]); h = np.array([50.0, 49.95, 49.9, 50.2, 50.3])
    l = np.array([49.95, 49.8, 49.75, 50.0, 50.1]); c = np.array([49.95, 49.85, 49.85, 50.15, 50.25])
    ec = SL + e * BP
    rb, kb = r_of(o, h, l, c, e, 1, D, U, False, 1.0, ec); assert kb == 1 and rb < -1        # BASE: stopped, -1R minus costs
    rw, kw = r_of(o, h, l, c, e, 1, D2, U2, False, 1.0, ec); assert kw == 2 and rw > 0        # W80: survives, hits target
    assert abs(rw - (0.2 - (ec + 0)) / 0.4) < 1e-9                                             # +0.5R' minus entry cost
    # costs in R halve when D doubles on a flat trade
    of = np.full(5, 50.0); r1, _ = r_of(of, of, of, of, e, 1, 0.2, U, False, 1.0, ec); r2, _ = r_of(of, of, of, of, e, 1, 0.4, U, False, 1.0, ec)
    assert abs(r2 - r1 / 2) < 1e-9
    print("selftest ok: widen (floor, scale, untouched wide stop), equal-risk R (stop vs survive), cost halving")


def main():
    import pyarrow.dataset as pds
    from multiprocessing import Pool
    assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
    sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y")); sys.path.insert(0, str(HERE.parent / "bereplay"))
    import lib
    from mcf.research import gates as G
    import bereplay as BR                                  # sample loader + geometry map (no run on import)
    assert (BR.SL, BR.BP, BR.SX) == (SL, BP, SX)
    T90 = round(max(1.35, 0.9 * G.t_required(N_FAMILY)), 2)
    hold_dir = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "-" else None
    procs = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    t = BR.load_lists(hold_dir)
    global JOB_CTX
    JOB_CTX = dict(GK=BR.GK, TL0=BR.TL0, TL1=BR.TL1, G=G, pds=pds)
    jobs = [(s, g) for s, g in t.groupby("symbol")]
    rows = []
    with Pool(procs) as pool:
        for k, res in enumerate(pool.imap_unordered(sym_job, jobs, chunksize=4)):
            if res: rows += res
            if k % 200 == 0: print(f"symbols {k}/{len(jobs)}", flush=True)
    cols = ["setup", "side", "geom", "symbol", "date", "tod", "stop_bp", "BASE"] + [v for v, _, _ in VARS] + [f"cost_{v}" for v in ["BASE"] + [v for v, _, _ in VARS]]
    X = pd.DataFrame(rows, columns=cols)
    X["family"] = np.where(X.setup.str.startswith("GEN"), "GEN", X.setup.str.split("-").str[0])
    X.to_parquet(HERE / "stopw_trades.parquet", index=False)
    D_ = lib.daily(); S = D_[D_.symbol == "SPY"].set_index("date"); oc = S.close / S.open - 1
    dtype = pd.Series(np.where(oc > .0025, "up", np.where(oc < -.0025, "down", "quiet")), index=S.index)
    X["top"] = X.BASE >= X.groupby("family").BASE.transform(lambda v: v.quantile(.9))
    print(f"\nreplayed {len(X)} trades, {X.setup.nunique()} setups, {X.family.nunique()} families, {X.date.nunique()} days; "
          f"median stop {X.stop_bp.median():.0f}bp; share < 60/80/100bp: {(X.stop_bp < 60).mean():.0%} / {(X.stop_bp < 80).mean():.0%} / {(X.stop_bp < 100).mean():.0%}")
    print(f"family N {N_FAMILY}: BAR90 {T90}")
    out = []
    for v, Xbp, _ in VARS:
        x = X.copy(); x["r"] = x[v] - x.BASE
        s_ = G.summary(x); tr_, va_ = G.summary(x[x.date <= BR.SPLIT]), G.summary(x[x.date > BR.SPLIT])
        ty = x.groupby(x.date.map(dtype)).r.sum()
        fam = x.groupby(["family", "side"]).agg(n=("r", "size"), changed=("stop_bp", lambda b: float((b < Xbp).mean())),
                                                 delta=("r", "mean"), base=("BASE", "mean"),
                                                 cost_base=("cost_BASE", "median"), cost_var=(f"cost_{v}", "median"))
        better, worse = int((fam.delta > 1e-9).sum()), int((fam.delta < -1e-9).sum()); worst = float(fam.delta.min())
        tp = x[x.top]; keep = float((tp[v] > 0).mean()) if len(tp) else np.nan
        row = dict(config=v, n=s_["n"], days=s_["days"], changed=round(float((x.stop_bp < Xbp).mean()), 3),
                   base_avg=round(x.BASE.mean(), 4), var_avg=round(x[v].mean(), 4), delta=s_["exp_r"], delta_t=s_.get("t"),
                   delta_total=round(x.r.sum(), 1), wo_best=s_.get("ex_best_day"), train=tr_.get("exp_r"), train_t=tr_.get("t"),
                   valid=va_.get("exp_r"), valid_t=va_.get("t"), up=round(ty.get("up", 0), 1), down=round(ty.get("down", 0), 1),
                   quiet=round(ty.get("quiet", 0), 1), fam_better=better, fam_worse=worse, worst_fam_delta=round(worst, 4),
                   top_kept=round(keep, 3), top_sum_base=round(tp.BASE.sum(), 1), top_sum_var=round(tp[v].sum(), 1),
                   cost_med_base=round(x.cost_BASE.median(), 3), cost_med_var=round(x[f"cost_{v}"].median(), 3))
        row["pass"] = bool((row["delta_t"] or 0) >= T90 and (row["train"] or -1) > 0 and (row["valid"] or -1) > 0 and row["up"] > 0
                           and row["down"] > 0 and (row["wo_best"] or -1) > 0 and better > worse and worst >= -0.03 and keep >= .90)
        out.append(row)
        fam = fam.round(4).sort_values("delta")
        print(f"\n{v} per family x side (delta = variant - BASE, R per trade in own-risk units):\n{fam.to_string()}")
        fam.reset_index().to_csv(HERE / f"stopw_family_{v}.csv", index=False)
    R = pd.DataFrame(out); pd.set_option("display.width", 420); pd.set_option("display.max_columns", 40)
    print("\n" + R.to_string(index=False))
    print("\nequal $ risk: R' = P/L / D', D' = max(D, X bp x entry); target price unchanged (W80S: scaled by D'/D); costs as bt_all;"
          "\ntop_kept = share of each family's BASE top-decile trades still > 0 under the variant; changed = share with D < X.")
    print(f"configs {len(VARS)} (family N {N_FAMILY}), BAR90 {T90}: pass {int(R['pass'].sum())}")
    R.to_csv(HERE / "stopw_results.csv", index=False)
    print("Educational only - not financial advice.")


JOB_CTX = {}


def sym_job(args):
    """per symbol: BASE and the 4 variants for every trade (same 1-minute slicing and costs as research/bereplay)."""
    sym, tr = args
    if not JOB_CTX:                                         # spawned worker: rebuild the context
        sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y")); sys.path.insert(0, str(HERE.parent / "bereplay"))
        import pyarrow.dataset as pds
        from mcf.research import gates as G
        import bereplay as BR
        JOB_CTX.update(GK=BR.GK, TL0=BR.TL0, TL1=BR.TL1, G=G, pds=pds)
    GK, TL0, TL1, G, pds = (JOB_CTX[k] for k in ("GK", "TL0", "TL1", "G", "pds"))
    p = ROOT / "data/cache_hist/1Min" / f"{sym}.parquet"
    if not p.exists(): return None
    ix = "__index_level_0__"
    df = pds.dataset(str(p), format="parquet").to_table(filter=(pds.field(ix) < TL0) | (pds.field(ix) >= TL1)).to_pandas()
    if ix in df.columns: df = df.set_index(ix)
    assert not ((df.index >= TL0) & (df.index < TL1)).any()
    df = df[~df.index.duplicated(keep="last")].sort_index()
    mm = (df.index.hour * 60 + df.index.minute).to_numpy(); keep = (mm >= 570) & (mm < 955)
    df = df[keep]; mm = mm[keep]; dd = df.index.date
    O, H, L, C = (df[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    st = np.r_[0, np.flatnonzero(dd[1:] != dd[:-1]) + 1]; en = np.r_[st[1:], len(dd)]
    span = {dd[a]: (a, b) for a, b in zip(st, en)}
    out = []
    for r in tr.itertuples(index=False):
        if r.date not in span: continue
        a, b = span[r.date]; t0 = r.tod // 100 * 60 + r.tod % 100
        j = a + int(np.searchsorted(mm[a:b], t0))
        o, h, l, c = O[j:b], H[j:b], L[j:b], C[j:b]
        e = float(r.close); R = .25 * float(r.atr_d); up, dn = GK[r.geom]; D = dn * R; U = up * R
        if not (np.isfinite(e) and e > 0 and D > 0): continue
        tier = 3.0 if (abs(r.gap) >= 20 or e < 5) else 1.0
        ecost = (SL + e * BP) * float(G.tod_cost_mult(np.array([r.tod]))[0])
        trail = r.geom == "holdtr"
        rb, _ = r_of(o, h, l, c, e, r.side, D, U, trail, tier, ecost)
        res, costs = [], [tier * (ecost + SL + e * BP) / D]
        for v, Xbp, scale in VARS:
            D2, U2 = widen(D, U, e, Xbp, scale)
            rv, _ = r_of(o, h, l, c, e, r.side, D2, U2, trail, tier, ecost); res.append(rv)
            costs.append(tier * (ecost + SL + e * BP) / D2)
        out.append((r.setup, r.side, r.geom, sym, r.date, r.tod, D / e * 1e4, rb, *res, *costs))
    return out


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
