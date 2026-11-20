"""Setup-level giveback fixes (PLAN.md). Usage: python score.py fit | check. Educational only - not financial advice."""
import sys, glob, json, numpy as np, pandas as pd
from pathlib import Path
HERE = Path(__file__).parent; D = HERE / "data"
LIVE = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/gb_tmp/live_paths.parquet"
SETUPS = ["CWT14-failbrk-orl-p05-long", "CWT14-failbrk-orl-p05-lowvol-long", "CWT14-failbrk-pdl-p05-long", "CWT12-coil-k4-long",
          "CWT14-failbrk-pdl-p10-long", "heat_fade_short-FD", "RW7-gapdn-bounce-early-short-FD", "CWT14-failbrk-orl-p10-lowvol-long",
          "CWT14-failbrk-orl-p10-long", "CWT14-failbrk-pdl-p05-lowvol-long", "L3-gap-slope-fromopen-FD", "NM-ETF-late-dip-di-long",
          "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "ST7-rsi50dn-long-pm-t1s1-FD"]
LIVEONLY = {"heat_fade_short-FD", "NM-ETF-late-dip-di-long"}
CONFIGS = [("A", 3), ("A", 5), ("A", 10), ("B", 1330), ("B", 1400), ("B", 1430), ("C1", 0), ("C2", 0)]
NEIGH = {("A", 3): [("A", 5)], ("A", 5): [("A", 3), ("A", 10)], ("A", 10): [("A", 5)], ("B", 1330): [("B", 1400)],
         ("B", 1400): [("B", 1330), ("B", 1430)], ("B", 1430): [("B", 1400)], ("C1", 0): [("C2", 0)], ("C2", 0): [("C1", 0)]}
FIT_END_LAB = "2025-09-30"; FIT_END_LIVE = "2026-10-28"
fam = lambda s: s.split("-")[0].split("_")[0]


def load_lab():
    a = pd.concat(pd.read_parquet(p) for p in sorted(glob.glob("/home/user/MCF/research/history2y/data/bt_lab1104/sig_*.parquet")))
    a = a[a.setup.isin(SETUPS)].copy(); a["date"] = a.date.astype(str)
    assert not ((a.date >= "2024-11-01") & (a.date <= "2025-02-28")).any()
    a = a.drop_duplicates(["setup", "symbol", "date", "tod"]).sort_values(["setup", "date", "tod", "symbol"]).reset_index(drop=True)
    return pd.DataFrame(dict(setup=a.setup, symbol=a.symbol, date=a.date, tod=a.tod.astype(int), xtod=a.xtod.astype(int), r=a.r.astype(float),
                             half=np.where(a.date <= FIT_END_LAB, "fit", "check")))


def load_live():
    d = pd.read_parquet(LIVE, columns=["strategy", "symbol", "date", "m_in", "m_out", "R", "account", "id"])
    d = d[d.strategy.isin(SETUPS) & d.R.notna()].sort_values(["account", "id"]).drop_duplicates(["strategy", "symbol", "date", "m_in"])
    tod = (d.m_in // 60) * 100 + d.m_in % 60; xtod = (d.m_out // 60) * 100 + d.m_out % 60
    x = pd.DataFrame(dict(setup=d.strategy, symbol=d.symbol, date=d.date.astype(str), tod=tod.astype(int), xtod=xtod.astype(int), r=d.R.astype(float)))
    x["half"] = np.where(x.date <= FIT_END_LIVE, "fit", "check")
    return x.sort_values(["setup", "date", "tod", "symbol"]).reset_index(drop=True)


def features(x):
    x = x.copy()
    x["crowd"] = x.groupby(["setup", "date", "tod"]).r.transform("size")
    g = x.groupby(["setup", "symbol", "date"])
    x["nth"] = g.cumcount() + 1
    # C2: an earlier trade of this setup in the symbol today closed at a loss before this entry
    prior_loss = np.zeros(len(x), bool)
    for _, idx in g.indices.items():
        if len(idx) < 2: continue
        tods, xt, rr = x.tod.values[idx], x.xtod.values[idx], x.r.values[idx]
        for k in range(1, len(idx)):
            prior_loss[idx[k]] = bool(((xt[:k] <= tods[k]) & (rr[:k] < 0)).any())
    x["prior_loss"] = prior_loss
    return x


def drop_mask(x, cfg):
    k, v = cfg
    if k == "A": return x.crowd.values >= v
    if k == "B": return x.tod.values >= v
    if k == "C1": return x.nth.values >= 2
    return x.prior_loss.values


def tstat(per_day):
    v = np.asarray(per_day, float); n = len(v)
    return v.mean() / (v.std(ddof=1) / np.sqrt(n)) if n > 1 and v.std(ddof=1) > 0 else np.nan


def score(x, m, mu=None):
    """x: one setup, one half. m: drop mask. Paired stats vs parent and vs random removal."""
    mu = x.r.mean() if mu is None else mu
    days = x.date.values; ud = np.unique(days)
    dr = pd.Series(np.where(m, -x.r.values, 0.0)).groupby(days).sum().reindex(ud).values
    ex = pd.Series(np.where(m, mu - x.r.values, 0.0)).groupby(days).sum().reindex(ud).values
    top = x.r.values >= np.quantile(x.r.values, 0.9)
    kept = x[~m]
    def wo(z):
        if len(z) == 0: return np.nan
        g = z.groupby("date").r.agg(["sum", "size"]); b = g["sum"].idxmax()
        return (g["sum"].sum() - g.loc[b, "sum"]) / max(1, len(z) - g.loc[b, "size"])
    best_share = dr.max() / dr.sum() if dr.sum() > 0 else np.nan
    exwo = ex.sum() - ex.max()
    return dict(n=len(x), days=len(ud), dropped=int(m.sum()), keep=1 - m.mean(), top_keep=1 - (m & top).sum() / max(1, top.sum()),
                R_before=x.r.sum(), dR=dr.sum(), avg_before=x.r.mean(), avg_after=kept.r.mean() if len(kept) else np.nan,
                wo_before=wo(x), wo_after=wo(kept), t_raw=tstat(dr), excess=ex.sum(), t_ex=tstat(ex), excess_wo_best=exwo,
                best_day_share=best_share, dropped_avg=x.r.values[m].mean() if m.any() else np.nan)


def rand_pct(x, m, draws=2000, seed=7):
    rng = np.random.default_rng(seed)
    days = pd.factorize(x.date.values)[0]; r = x.r.values
    ndrop = np.bincount(days[m], minlength=days.max() + 1)
    start = np.r_[0, np.cumsum(np.bincount(days))[:-1]]
    o0 = np.argsort(days, kind="stable"); real = -r[m].sum(); out = np.empty(draws)
    for k in range(draws):
        key = rng.random(len(r)); o = np.lexsort((key, days)); pos = np.arange(len(r)) - start[days[o]]
        sel = o[pos < ndrop[days[o]]]; out[k] = -r[sel].sum()
    return float((out < real).mean())


def main(mode):
    lab, live = features(load_lab()), features(load_live())
    if mode == "fit":
        rows, diag = [], []
        for s in SETUPS:
            src = live if s in LIVEONLY else lab
            x = src[(src.setup == s) & (src.half == "fit")].reset_index(drop=True)
            for c in CONFIGS:
                m = drop_mask(x, c); rows.append(dict(setup=s, src="live" if s in LIVEONLY else "lab", cfg=f"{c[0]}{c[1] or ''}", **score(x, m)))
            for name, srcx in (("lab", lab), ("live", live)):
                z = srcx[(srcx.setup == s) & (srcx.half == "fit")]
                if len(z) == 0: continue
                for lab_, col, bins in (("crowd", "crowd", [0, 1, 2, 4, 9, 1e9]), ("tod", "tod", [0, 1030, 1200, 1330, 1400, 1430, 2400]), ("nth", "nth", [0, 1, 2, 99])):
                    for b, g in z.groupby(pd.cut(z[col], bins), observed=True):
                        diag.append(dict(setup=s, src=name, cut=lab_, bucket=str(b), n=len(g), avg=g.r.mean(), mfe_na=np.nan))
        F = pd.DataFrame(rows); F.to_csv(D / "fit_grid.csv", index=False); pd.DataFrame(diag).to_csv(D / "fit_diag.csv", index=False)
        el = F[(F.keep >= .70) & (F.top_keep >= .90) & (F.excess > 0) & (F.t_ex >= 2.0) & (F.excess_wo_best > 0)]
        adopt = el.sort_values("excess", ascending=False).drop_duplicates("setup")[["setup", "cfg", "excess", "t_ex"]]
        adopt.to_csv(D / "adopted.csv", index=False)
        print(F.to_string(max_rows=200)); print("\nADOPTED\n", adopt.to_string()); print("diag cells", len(diag))
    else:
        adopt = pd.read_csv(D / "adopted.csv"); cfgmap = {f"{c[0]}{c[1] or ''}": c for c in CONFIGS}
        out = []
        for a in adopt.itertuples():
            c = cfgmap[a.cfg]
            for name, srcx in (("lab", lab), ("live", live)):
                x = srcx[(srcx.setup == a.setup) & (srcx.half == "check")].reset_index(drop=True)
                if len(x) < 2: continue
                m = drop_mask(x, c); rec = dict(setup=a.setup, family=fam(a.setup), src=name, cfg=a.cfg, **score(x, m))
                rec["rand_pct"] = rand_pct(x, m) if m.any() else np.nan
                rec["neigh_excess"] = ";".join(f"{n[0]}{n[1] or ''}:{score(x, drop_mask(x, n))['excess']:+.1f}" for n in NEIGH[c])
                out.append(rec)
        C = pd.DataFrame(out); C.to_csv(D / "check.csv", index=False); print(C.T.to_string())


if __name__ == "__main__":
    main(sys.argv[1])
