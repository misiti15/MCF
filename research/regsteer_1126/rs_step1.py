"""REGSTEER-1126 Step 1: bench-live rank agreement of setup x state cells (S1 SPY-gap tercile x S2 W60 confirmed side).
Gate = Spearman of setup-demeaned cell means (raw reported), 90% CI by day-block bootstrap (1,000 draws, seed 1126).
Cells need >= 30 bench and >= 8 live trades. Usage: python rs_step1.py SCR OUT.json. Educational only."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

SCR, OUT = Path(sys.argv[1]), Path(sys.argv[2])
LOCK = ("2024-11-01", "2025-02-28")
SETUPS = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
          "NM-ETF-late-dip-di-long", "GEN-261022-05-MACDhge0p079-UpWickge0p71-ORHdistlem0p38-PM-BRoplt0p35-holdtr-short",
          "GEN-261026-07-Flow3ge0p56-BBpctge0p98-ADX7le34-PM-BRvwlt0p3-holdtr-short",
          "GEN-261020-09-EMAdChgge0p093-Z12lem0p82-VWAPcrossesle0-MID-QQQltm0p3-holdtr-long",
          "GEN-261023-07-RSIslopege9p1-BarRngATRge0p087-VWAPcrossesge8-LUNCH-BRvwgt0p7-hold-long"]
NB, NL, NBOOT = 30, 8, 1000


def prep(c, cuts):
    c = c[c.setup.isin(SETUPS) & c.gap.notna() & (c.w60 != -9)].copy()
    c["s1"] = np.where(c.gap <= cuts[0], -1, np.where(c.gap > cuts[1], 1, 0))
    c["cell"] = c.s1.astype(str) + "|" + c.w60.astype(str)
    c["a1"], c["a2"] = c.side * c.s1, c.side * c.w60          # aligned states (+1 with the exposure)
    return c


def cellstats(c):
    g = c.groupby(["setup", "cell"]).r.agg(["mean", "size"])
    mu = c.groupby("setup").r.mean()
    g["dm"] = g["mean"] - mu.reindex(g.index.get_level_values(0)).to_numpy()
    return g


def gamma(c):
    """pooled aligned effect per (a1, a2): mean of (r - setup mean), trade-weighted."""
    d = c.r - c.setup.map(c.groupby("setup").r.mean())
    return d.groupby([c.a1, c.a2]).mean()


def rho(b, l):
    j = b.join(l, lsuffix="_b", rsuffix="_l", how="inner")
    j = j[(j.size_b >= NB) & (j.size_l >= NL)]
    if len(j) < 5:
        return np.nan, np.nan, len(j)
    return spearmanr(j.dm_b, j.dm_l)[0], spearmanr(j.mean_b, j.mean_l)[0], len(j)


def boot_days(c, rng):
    d = c.date.unique()
    pick = rng.choice(d, len(d), replace=True)
    cnt = pd.Series(pick).value_counts()
    idx = c.index[c.date.isin(cnt.index)]
    rep = c.loc[idx, "date"].map(cnt).to_numpy()
    return c.loc[np.repeat(idx.to_numpy(), rep)]


if __name__ == "__main__":
    C = pd.read_parquet(SCR / "cand.parquet")
    d_ = C.date.astype(str); assert not ((d_ >= LOCK[0]) & (d_ <= LOCK[1])).any()
    L = pd.read_parquet(SCR / "live_states.parquet").rename(columns={"strategy": "setup"})
    gd = C.groupby("date").gap.first()
    cuts = tuple(gd[C.groupby("date").per.first().isin(["T2", "FIT"])].quantile([1 / 3, 2 / 3]).to_numpy())
    Cb, Lb = prep(C, cuts), prep(L, cuts)
    res = {"gap_tercile_cuts": cuts, "n_live_trades": int(len(Lb)), "live_sessions": int(Lb.date.nunique())}
    sl = cellstats(Lb)
    for nm, sub in [("all", Cb)] + [(p, Cb[Cb.per == p]) for p in ("T2", "FIT", "CHECK")]:
        r_dm, r_raw, n = rho(cellstats(sub), sl)
        res[f"rho_{nm}"] = dict(demeaned=r_dm, raw=r_raw, cells=n)
    # setups-only views (Primary 4 / contenders) for information
    for nm, ss in (("primary4", SETUPS[:4]), ("contenders", SETUPS[4:])):
        r_dm, r_raw, n = rho(cellstats(Cb[Cb.setup.isin(ss)]), cellstats(Lb[Lb.setup.isin(ss)]))
        res[f"rho_{nm}"] = dict(demeaned=r_dm, raw=r_raw, cells=n)
    rng = np.random.default_rng(1126)
    bs = []
    for _ in range(NBOOT):
        bs.append(rho(cellstats(boot_days(Cb, rng)), cellstats(boot_days(Lb, rng)))[:2])
    bs = np.array(bs, float)
    res["ci90_demeaned"] = list(np.nanpercentile(bs[:, 0], [5, 95]))
    res["ci90_raw"] = list(np.nanpercentile(bs[:, 1], [5, 95]))
    gb, gl = gamma(Cb), gamma(Lb)
    j = pd.concat([gb.rename("bench"), gl.rename("live")], axis=1).dropna()
    res["gamma_cells"] = {f"{a}|{b}": [round(v, 4) for v in r] for (a, b), r in j.iterrows()}
    res["gamma_sign_agree"] = f"{int((np.sign(j.bench) == np.sign(j.live)).sum())}/{len(j)}"
    res["gamma_spearman"] = spearmanr(j.bench, j.live)[0] if len(j) >= 4 else None
    # the cell table (bench all / live) for the record
    cb, cl = cellstats(Cb), sl
    tab = cb.join(cl, lsuffix="_b", rsuffix="_l", how="outer").round(4)
    tab.reset_index().to_csv(OUT.with_suffix(".cells.csv"), index=False)
    r = res["rho_all"]["demeaned"]; lo = res["ci90_demeaned"][0]
    res["gate"] = "per-setup steering allowed" if (r > 0.2 and lo > 0) else "STOP at side-level (pooled configs only)"
    res["build_bar_rho"] = bool(r >= 0.3 and lo > 0)
    json.dump(res, open(OUT, "w"), indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))
