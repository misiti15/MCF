"""D2PM scorer, to the frozen PLAN.md (3 looks). Reads data/cache_pm (premarket) + data/cache_hist/1Min (RTH) + earnings_yf.
usage (MCF checkout): python d2pm.py <earnings_yf.parquet|-> [--universe research/lab_symbols.txt] [--selftest]
Reporting cuts (Skeptic 2026-11-10, no new looks): premarket $vol and trade-count terciles, SPY up/down/quiet day, fixed lab list.. Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from pathlib import Path
ET = "America/New_York"; PM, RTH = Path("data/cache_pm"), Path("data/cache_hist/1Min")
D0, D1 = "2026-10-07", "2026-11-09"
def auc(score, y):
    s = pd.Series(score).rank().to_numpy(); y = np.asarray(y, bool); n1, n0 = y.sum(), (~y).sum()
    return (s[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0) if n1 and n0 else np.nan
def terc(s):
    """per-day tercile label; days with < 3 names get NaN (small event subgroups)."""
    return pd.qcut(s.rank(method="first"), 3, labels=["T1", "T2", "T3"]) if s.notna().sum() >= 3 else pd.Series(np.nan, index=s.index)
def welch_day(x, by):
    """day-demeaned mean of x and its day-clustered t (days as the unit)."""
    d = pd.Series(x).groupby(np.asarray(by)).mean(); return d.mean(), d.mean() / (d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 2 else np.nan, len(d)
def name_days(sym, spy):
    """one row per session: premarket features at 09:29:59 and RTH labels (09:35 decision, 09:51 entry)."""
    pp, rp = PM / f"{sym}.parquet", RTH / f"{sym}.parquet"
    if not (pp.exists() and rp.exists()): return []
    pm, r = pd.read_parquet(pp), pd.read_parquet(rp)
    r = r.between_time("09:30", "15:59"); rd = r.groupby(r.index.date)
    day = rd.agg(h=("high", "max"), l=("low", "min"), c=("close", "last"))
    day["tr"] = np.maximum(day.h, day.c.shift(1)) - np.minimum(day.l, day.c.shift(1)); day["atr"] = day.tr.shift(1).rolling(10, min_periods=5).mean()
    day["pc"] = day.c.shift(1); pmd = pm.groupby(pm.index.date); out = []
    dv = pmd.apply(lambda g: (g.close * g.volume).sum()); norm = dv.shift(1).rolling(10, min_periods=5).median()
    for d, g in rd:
        if not (D0 <= str(d) <= D1) or d not in dv.index or not np.isfinite(day.at[d, "atr"]) or not np.isfinite(norm.get(d, np.nan)): continue
        p = pmd.get_group(d); last = p.close.iloc[-1]; vw = (p.close * p.volume).sum() / max(p.volume.sum(), 1)
        p9 = p.between_time("04:00", "09:00"); p900 = p9.close.iloc[-1] if len(p9) else np.nan
        try:
            c935 = g.at_time("09:35").close.iloc[0]; o951 = g.at_time("09:51").open.iloc[0]
            c1130 = g.at_time("11:29").close.iloc[0]; c1555 = g.at_time("15:54").close.iloc[0]
        except IndexError: continue
        w = g.between_time("09:36", "11:05"); atr = day.at[d, "atr"]
        s = spy.get(d)
        if s is None: continue
        out.append(dict(sym=sym, date=str(d), pm_dvol=dv[d], pm_trades=p["trades"].sum() if "trades" in p else np.nan, pm_rvol=dv[d] / norm[d] if norm[d] > 0 else np.nan, gap=last / day.at[d, "pc"] - 1,
                        pm_vwap_drift=last / vw - 1, pm_late=last / p900 - 1 if p900 == p900 else np.nan,
                        up_atr=(w.high.max() - c935) / atr, dn_atr=(c935 - w.low.min()) / atr,
                        r1130=c1130 / o951 - 1 - s["r1130"], r1555=c1555 / o951 - 1 - s["r1555"], spy1130=s["r1130"], dtype=s["dtype"]))
    return out
def spy_rets():
    g = pd.read_parquet(RTH / "SPY.parquet").between_time("09:30", "15:59"); o = {}
    for d, x in g.groupby(g.index.date):
        try:
            o951 = x.at_time("09:51").open.iloc[0]; oc = x.close.iloc[-1] / x.open.iloc[0] - 1
            o[d] = dict(r1130=x.at_time("11:29").close.iloc[0] / o951 - 1, r1555=x.at_time("15:54").close.iloc[0] / o951 - 1,
                        dtype="up" if oc > 0.003 else ("down" if oc < -0.003 else "quiet"))
        except IndexError: pass
    return o
def events(path):
    if path == "-": return set()
    e = pd.read_parquet(path); e = e[e.session.isin(["bmo", "amc", "BMO", "AMC"])].copy()   # dmh dropped (Skeptic)
    d = pd.to_datetime(e.date).dt.tz_localize(None).dt.normalize(); amc = e.session.str.lower() == "amc"
    react = np.where(amc, d + pd.offsets.BDay(1), d + pd.offsets.BDay(0))
    return set(zip(e.symbol, pd.to_datetime(react).strftime("%Y-%m-%d")))
def score(X):
    """X: one row per name-day. Beta-1 ex-market (beta60 not available on the 1-month RTH cache; stated in the output)."""
    X = X.dropna(subset=["pm_rvol", "gap", "pm_vwap_drift", "r1130", "r1555"]).copy()
    X["mover"] = (X.groupby("date").up_atr.rank(ascending=False) <= 50) | (X.groupby("date").dn_atr.rank(ascending=False) <= 50)
    print(f"name-days {len(X)}, names {X.sym.nunique()}, sessions {X.date.nunique()} ({X.date.min()}..{X.date.max()}); movers {int(X.mover.sum())}; ex-market = minus SPY (beta 1)")
    for grp, Y in (("all", X), ("event", X[X.event]), ("non-event", X[~X.event])):
        if len(Y) < 50: continue
        print(f"\n[{grp}] n {len(Y)}  L1 AUC pm_rvol -> mover {auc(Y.pm_rvol, Y.mover):.3f}   (gap |.| AUC {auc(Y.gap.abs(), Y.mover):.3f} for reference)")
        q = Y.pm_rvol >= Y.groupby("date").pm_rvol.transform(lambda s: s.quantile(0.8))
        for sub, Z in (("all", Y), ("top pm_rvol quintile", Y[q])):
            for h in ("r1130", "r1555"):
                line = f"   {sub:22s} {h}: "
                for lab, col in (("GAP baseline", "gap"), ("L2 pm_vwap_drift", "pm_vwap_drift"), ("L3 pm_late", "pm_late")):
                    z = Z.dropna(subset=[col]); rr = z[h] - z.groupby("date")[h].transform("mean")   # day-demeaned RETURN, then signed
                    m, t, nd = welch_day(np.sign(z[col]) * rr, z.date); line += f"{lab} {m * 1e4:+.1f}bp t {t:+.2f} | "
                print(line + f"days {nd}")
        for lab, col in (("L2", "pm_vwap_drift"), ("L3", "pm_late")):         # within gap-sign strata: does it add to the gap?
            z = Y.dropna(subset=[col]); agree = np.sign(z[col]) == np.sign(z.gap); v = np.sign(z.gap) * z.r1130
            a, b = v[agree].groupby(z.date[agree]).mean(), v[~agree].groupby(z.date[~agree]).mean(); j = a.index.intersection(b.index)
            dd = (a[j] - b[j]); print(f"   {lab} agrees with gap minus disagrees (gap-side r1130): {dd.mean() * 1e4:+.1f}bp t {dd.mean() / (dd.std() / np.sqrt(len(dd))):+.2f} days {len(dd)}")
        # Skeptic's reporting cuts (no new looks): premarket volume / trade-count tercile, SPY day type (hindsight label, descriptive)
        for cut, key in (("pm $vol tercile", Y.groupby("date").pm_dvol.transform(terc)),
                         ("pm trades tercile", Y.groupby("date").pm_trades.transform(terc) if Y.pm_trades.notna().any() else None),
                         ("SPY day", Y.dtype)):
            if key is None: continue
            line = f"   {cut:18s} r1130: "
            for k in sorted(pd.Series(key).dropna().unique()):
                z = Y[key == k]
                if len(z) < 30: continue
                rr = z.r1130 - z.groupby("date").r1130.transform("mean")
                parts = []
                for lab, col in (("gap", "gap"), ("L2", "pm_vwap_drift"), ("L3", "pm_late")):
                    m, t, nd = welch_day(np.sign(z[col]) * rr, z.date); parts.append(f"{lab} {m * 1e4:+.1f}bp t {t:+.2f}")
                line += f"[{k} n {len(z)} d {z.date.nunique()}: " + ", ".join(parts) + "] "
            print(line)
        best = (np.sign(Y.pm_vwap_drift) * Y.r1130).groupby(Y.date).sum(); print(f"   best-day share of L2 r1130 total: {best.max() / best.sum():.0%}" if best.sum() > 0 else "   L2 r1130 total not positive")
def selftest():
    rng = np.random.default_rng(7); n = 4000; d = np.repeat([f"2026-10-{i:02d}" for i in range(7, 27)], n // 20)
    X = pd.DataFrame(dict(sym=np.tile(np.arange(n // 20), 20).astype(str), date=d, pm_rvol=rng.lognormal(0, 1, n), gap=rng.normal(0, .02, n),
                          pm_vwap_drift=rng.normal(0, .005, n), pm_late=rng.normal(0, .003, n)))
    X["up_atr"] = rng.gamma(2, .3, n) * (1 + X.pm_rvol / 5); X["dn_atr"] = rng.gamma(2, .3, n) * (1 + X.pm_rvol / 5)
    X["r1130"] = 0.5 * X.pm_vwap_drift + rng.normal(0, .01, n); X["r1555"] = X.r1130 + rng.normal(0, .01, n); X["spy1130"] = 0; X["event"] = False
    X["pm_dvol"] = X.pm_rvol * 1e6; X["pm_trades"] = X.pm_rvol * 100; X["dtype"] = np.where(X.date < "2026-10-14", "up", np.where(X.date < "2026-10-20", "down", "quiet"))
    assert auc(X.pm_rvol, (X.up_atr > X.up_atr.quantile(.9))) > 0.55; assert abs(auc(rng.normal(size=500), rng.random(500) > .5) - .5) < .08
    z = X; rr = z.r1130 - z.groupby("date").r1130.transform("mean"); m, t, _ = welch_day(np.sign(z.pm_vwap_drift) * rr, z.date); assert t > 5, t
    m0, t0, _ = welch_day(np.sign(z.pm_late) * rr, z.date); assert abs(t0) < 3, t0
    score(X); print("selftest ok: AUC, planted L2 drift found (finite t), null L3 not found, null AUC ~0.5")
if __name__ == "__main__":
    if "--selftest" in sys.argv: selftest(); sys.exit()
    spy = spy_rets(); ev = events(sys.argv[1]); rows = []
    syms = sorted(p.stem for p in PM.glob("*.parquet") if p.stem != "SPY")
    if "--universe" in sys.argv:                                   # Skeptic cut 3: the fixed lab list instead of names traded live
        u = set(Path(sys.argv[sys.argv.index("--universe") + 1]).read_text().split()); syms = [x for x in syms if x in u]
        print(f"universe filter: {len(syms)} names from {sys.argv[sys.argv.index('--universe') + 1]}")
    for i, s in enumerate(syms):
        rows += name_days(s, spy)
    X = pd.DataFrame(rows); X["event"] = [(a, b) in ev for a, b in zip(X.sym, X.date)]
    score(X); print("Educational only - not financial advice.")
