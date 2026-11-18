"""DIPTURN scorer (Scout's PLAN.md frozen 2026-11-14 23:30 ET + Amendment 1; Builder implementation, pre-score).
Day condition from SPY 1-min bars (locked block filtered out at read): open_0930 = first open; H20 / L20 = high / low of
09:30-09:49 (the 09:30..09:45 5-min bars); P = open of the 09:50 minute; pos = (P - L20) / (H20 - L20).
DT: L20 <= open - 0.25 x range AND pos >= 0.6. PF: H20 >= open + 0.25 x range AND pos <= 0.4.
Trades: full-day 2y lab lists (research/momside/data/trades_full.parquet, build_full.py), lab tod >= 955 only (dropped count
printed). C1 = long setups' trades on DT days; C2 = short setups' trades on PF days.
x = ex-market gross R (gross - TRAIN beta_setup x SPY over the leg's hold) minus the setup's own period mean (same side's trades
on all days). Estimate = pooled ratio sum(x on condition days) / n, SE day-clustered from per-day residuals (checklist 39).
Shared-day null: 500 draws of the same number of random days (one permutation for all setups). MDE80 = 2.8 SE; MDE at the bar
= (3.57 + 0.84) SE (guild standard 2026-11-15).
    python dipturn.py --selftest      python dipturn.py --score        Educational only - not financial advice."""
import os, subprocess, sys
from pathlib import Path
import numpy as np, pandas as pd
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
HERE = Path(__file__).resolve().parent; R = HERE.parent; ROOT = Path("/home/user/MCF")
SPLIT = "2025-09-30"; BAR90 = 3.57; NDRAW = 500
HALF_DAYS = {"2025-07-03", "2025-11-28", "2025-12-24"}     # Amendment 2: early-close sessions dropped (checklist 42)


def day_flags(s: pd.DataFrame) -> pd.DataFrame:
    """s: SPY 1-min bars (ET index) -> per date: open, H20, L20, P, pos, DT, PF, ret 09:50->close (bps)."""
    m = s.index.hour * 60 + s.index.minute; d = s.index.strftime("%Y-%m-%d")
    out = []
    for day, g in s.groupby(d):
        mm = g.index.hour * 60 + g.index.minute
        e = g[(mm >= 570) & (mm < 590)]; p = g[mm == 590]; cl = g[mm < 960]
        if len(e) < 10 or not len(p): continue
        if (e.index[0].hour, e.index[0].minute) != (9, 30): continue     # Skeptic: the open must be the 09:30 bar (else no flag)
        o = float(e.open.iloc[0]); H, L = float(e.high.max()), float(e.low.min()); rg = H - L; P = float(p.open.iloc[0])
        if rg <= 0: continue
        pos = (P - L) / rg
        out.append(dict(date=day, pos=pos, DT=bool(L <= o - 0.25 * rg and pos >= 0.6), PF=bool(H >= o + 0.25 * rg and pos <= 0.4),
                        r950=(float(cl.close.iloc[-1]) / P - 1) * 1e4))
    return pd.DataFrame(out).set_index("date")


def pooled(x, days, cond_days):
    """pooled ratio estimate over trades on cond_days, day-clustered SE (residual per day)."""
    m = np.isin(days, cond_days)
    if not m.any(): return np.nan, np.nan, 0, np.nan, np.nan
    S = pd.Series(x[m]).groupby(days[m]).agg(["sum", "size"])
    est = S["sum"].sum() / S["size"].sum(); e = S["sum"] - est * S["size"]; D = len(S)
    se = np.sqrt((e ** 2).sum() / S["size"].sum() ** 2 * D / max(D - 1, 1)) if D > 1 else np.nan
    return est, se, D, S["sum"].sum() - S["sum"].max(), S["size"].sum()


def run(B, F, rng):
    rows = []
    for cfg, side, flag in (("C1", 1, "DT"), ("C2", -1, "PF")):
        b = B[B.side == side]
        for per in ("TRAIN", "VALID"):
            g = b[b.per == per]
            x = (g.exm - g.groupby("setup").exm.transform("mean")).to_numpy(); xn = (g.r - g.groupby("setup").r.transform("mean")).to_numpy()
            xg = (g.gross - g.groupby("setup").gross.transform("mean")).to_numpy() if "gross" in g else x   # raw gross (index included)
            xa = x * 0.25 * g.dn.to_numpy()        # Skeptic: per-trade ATR = R x 0.25 x dn (t1s05 / t05s05: 1R = 0.125 ATR)
            days = g.date.to_numpy(); alld = np.array(sorted(set(days))); cd = np.array([d for d in alld if F[flag].get(d, False)])
            est, se, D, wob, n = pooled(x, days, cd); estn, sen, _, _, _ = pooled(xn, days, cd); esta, _, _, _, _ = pooled(xa, days, cd)
            estg, _, _, _, _ = pooled(xg, days, cd)
            null = np.array([pooled(x, days, rng.choice(alld, len(cd), replace=False))[0] for _ in range(NDRAW)]) if len(cd) else np.array([np.nan])
            ps = {}
            for su, gg in g.groupby("setup"):
                xi = (gg.exm - gg.exm.mean()).to_numpy(); mi = np.isin(gg.date.to_numpy(), cd)
                if mi.sum() >= 10: ps[su] = xi[mi].mean()
            ps = pd.Series(ps); tot = pd.Series({su: (gg.exm - gg.exm.mean())[np.isin(gg.date.to_numpy(), cd)].sum() for su, gg in g.groupby("setup")})
            pos_ = tot[tot > 0].sort_values(ascending=False)
            rows.append(dict(cfg=cfg, per=per, cond_days=D, days=len(alld), trades=int(n), exm_R=est, exm_ATR=esta, raw_gross_R=estg,
                             t=est / se if se else np.nan, se=se, MDE80=2.8 * se, MDE_bar=(BAR90 + 0.84) * se, null95=np.nanpercentile(null, 95),
                             net_R=estn, net_t=estn / sen if sen else np.nan, wo_best=wob, setups=len(ps), better=int((ps > 0).sum()),
                             worse=int((ps < 0).sum()), top5_share=pos_.head(5).sum() / tot.sum() if tot.sum() > 0 else np.nan,
                             spy_950_close_bps=F.loc[[d for d in cd if d in F.index], "r950"].mean() if len(cd) else np.nan))
    return pd.DataFrame(rows)


def selftest():
    rng = np.random.default_rng(7); days = [str(d.date()) for d in pd.bdate_range("2025-10-01", "2026-09-30")]
    F = pd.DataFrame(dict(DT=rng.random(len(days)) < 0.25, PF=rng.random(len(days)) < 0.25, r950=0.0), index=days)
    for planted in (0.10, 0.0):
        n = 40000; d = rng.choice(days, n); su = rng.choice(["L1", "L2", "S1"], n); side = np.where(su == "S1", -1, 1)
        eff = np.where((side > 0) & F.DT.reindex(d).to_numpy(), planted, 0.0)
        B = pd.DataFrame(dict(setup=su, side=side, date=d, exm=rng.normal(0, 1, n) + eff, r=rng.normal(0, 1, n), per="VALID", dn=1.0))
        B["gross"] = B.exm
        O = run(pd.concat([B, B.assign(per="TRAIN")]), F, rng); c1 = O[(O.cfg == "C1") & (O.per == "VALID")].iloc[0]
        print(f"selftest planted {planted}: est {c1.exm_R:+.3f} t {c1.t:+.2f} MDE80 {c1.MDE80:.3f} null95 {c1.null95:+.3f}")
        assert (c1.t > 4) if planted else abs(c1.t) < 3
    print("selftest ok. Educational only - not financial advice.")


def score():
    st = subprocess.run(["git", "-C", str(HERE), "status", "--porcelain", "PLAN.md", "dipturn.py"], capture_output=True, text=True).stdout
    assert not st.strip(), "PLAN.md and dipturn.py must be committed before the score"
    import pyarrow.dataset as pds
    NY = "America/New_York"; ix = "__index_level_0__"; TL0, TL1 = pd.Timestamp("2024-11-01", tz=NY), pd.Timestamp("2025-03-01", tz=NY)
    s = pds.dataset(str(ROOT / "data/cache_hist/1Min/SPY.parquet"), format="parquet").to_table(filter=(pds.field(ix) < TL0) | (pds.field(ix) >= TL1)).to_pandas()
    if ix in s.columns: s = s.set_index(ix)
    s.index = pd.DatetimeIndex(s.index).tz_convert(NY); s = s[~s.index.duplicated(keep="last")].sort_index()
    F = day_flags(s); F = F[~F.index.isin(HALF_DAYS)]
    B = pd.read_parquet(R / "momside/data/trades_full.parquet")
    assert not ((B.date >= "2024-11-01") & (B.date <= "2025-02-28")).any()
    n0 = len(B); drop950 = int((B.tod < 955).sum()); dl, ds = int(((B.tod < 955) & (B.side > 0)).sum()), int(((B.tod < 955) & (B.side < 0)).sum())
    nh = int(B.date.isin(HALF_DAYS).sum()); B = B[~B.date.isin(HALF_DAYS)]
    print(f"half-day sessions dropped: {nh} trades")
    B = B[B.tod >= 955].dropna(subset=["spy_move"]).reset_index(drop=True)
    B["per"] = np.where(B.date <= SPLIT, "TRAIN", np.where(B.date <= "2026-10-07", "VALID", "FWD"))
    beta = {su: (np.polyfit(g.spy_move, g.gross, 1)[0] if len(g) >= 30 else float(g.side.iloc[0])) for su, g in B[B.per == "TRAIN"].groupby("setup")}
    B["exm"] = B.gross - B.setup.map(beta).fillna(B.side.astype(float)) * B.spy_move
    sys.path.insert(0, str(ROOT)); from mcf.research.gates import GEOMK
    GK = {**GEOMK, "hold": (np.inf, 1.0), "holdtr": (np.inf, 1.0)}
    B["dn"] = B.geom.map(lambda gm: GK[gm][1]).astype(float)
    O = run(B[B.per != "FWD"], F, np.random.default_rng(20261116))
    pd.set_option("display.width", 300); pd.set_option("display.max_columns", 40)
    print(f"DIPTURN (PLAN + Amendment 1, one score): trades {n0}, dropped tod < 955: {drop950} (long {dl}, short {ds}); "
          f"DT days {int(F.DT.sum())} / PF {int(F.PF.sum())} of {len(F)}; family 2,611, BAR90 {BAR90}")
    print(O.round(4).to_string(index=False)); O.to_csv(HERE / "dipturn_results.csv", index=False)
    for c in ("C1", "C2"):
        v = O[(O.cfg == c) & (O.per == "VALID")].iloc[0]; tr = O[(O.cfg == c) & (O.per == "TRAIN")].iloc[0]
        gates = {"VALID est > 0, t >= 3.57": bool(v.exm_R > 0 and v.t >= BAR90), "TRAIN est > 0": bool(tr.exm_R > 0),
                 "VALID > null95": bool(v.exm_R > v.null95), ">= 60% setups better": bool(v.setups and v.better / v.setups >= 0.6),
                 "w/o best day > 0": bool(v.wo_best > 0)}
        print(c, gates, "->", "PASS (arena lead)" if all(gates.values()) else f"CLOSED: nothing above {v.MDE_bar:.3f}R per trade at the bar "
              f"(MDE80 {v.MDE80:.3f}R); smaller unknown")
    print("index check (Skeptic): raw_gross_R includes the index move, exm_R removes beta x SPY over each hold; if raw >> exm, "
          "the condition's 'edge' is index direction, not selection. configs shown: 2 x 2 periods")
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else score() if "--score" in sys.argv else print(__doc__)
