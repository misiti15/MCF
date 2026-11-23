"""etfstop_1123 scoring (PLAN.md metrics) from work/S_lots.parquet. Educational only - not financial advice.
Usage: python score.py WORKDIR"""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

W, OUT = Path(sys.argv[1]), Path(__file__).parent
TZ, LOCK = "America/New_York", ("2024-11-01", "2025-02-28")
L = pd.read_parquet(W / "S_lots.parquet")
L["r"] = L.r.fillna(0.0)
L["year"] = L.date.str[:4]
SPYOC = pd.read_parquet(W / "spy_oc.parquet").set_index("date").spy_oc
CFGS = [c for c in L.cfg.unique() if c != "base"]
N = len(CFGS)
BAR = max(1.5, math.sqrt(2 * math.log(N)))
NLIN = 21 + 2 + 21 + (N - 2)
BARL = max(1.5, math.sqrt(2 * math.log(NLIN)))
P = []


def pr(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    P.append(s)


# sessions per period / year (SPY calendar, locked block filtered out)
def sessions():
    ds = []
    for src, lo, hi in (("/home/user/MCF/data/cache_fresh/1Min", "2023-01-01", "2024-09-14"),
                        ("/home/user/MCF/data/cache_hist/1Min", "2024-09-16", "2026-11-05")):
        f = pads.field("__index_level_0__")
        flt = (f >= pd.Timestamp(lo, tz=TZ)) & (f < pd.Timestamp(hi, tz=TZ))
        flt = flt & ((f < pd.Timestamp(LOCK[0], tz=TZ)) | (f >= pd.Timestamp("2025-03-01", tz=TZ)))
        t = pads.dataset(src + "/SPY.parquet", format="parquet").to_table(filter=flt, columns=["__index_level_0__"])
        idx = pd.DatetimeIndex(t.column(0).to_pandas()).tz_convert(TZ)
        ds += list(np.unique(idx.date.astype(str)))
    s = pd.Series(sorted(set(ds)))
    assert not ((s >= LOCK[0]) & (s <= LOCK[1])).any()
    return s


def period(d):
    if ("2024-10-01" <= d <= "2024-10-31") or ("2025-03-01" <= d <= "2025-09-30"):
        return "FIT"
    if d >= "2025-10-01":
        return "CHECK"
    if d <= "2024-09-13":
        return "T2"
    return "none"


SESS = sessions()
SESS = SESS[SESS.map(period) != "none"]
NSESS = SESS.groupby(SESS.map(period)).size().to_dict()
NSESS["ALL"] = len(SESS)
NYEAR = SESS.groupby(SESS.str[:4]).size().to_dict()
YEARS = len(SESS) / 252.0
pr("sessions", NSESS, NYEAR, "years %.2f" % YEARS)

day = L.groupby(["cfg", "per", "date"]).r.sum().unstack("cfg").fillna(0.0)
dd_all = day.droplevel("per")


def tstat(x):
    n = len(x)
    s = x.std(ddof=1)
    return x.mean() / (s / math.sqrt(n)) if n > 2 and s > 0 else float("nan")


def w5(x):
    return x.nsmallest(5).sum()


def wobd(x):
    return x.drop(x.idxmax()).sum() if len(x) > 1 else 0.0


# ---------------------------------------------------------------- A. summary per config x period
rows = []
for c in CFGS:
    for per in ("FIT", "T2", "CHECK", "FIT+T2", "ALL"):
        if per == "ALL":
            d = day
        elif per == "FIT+T2":
            d = day[day.index.get_level_values("per").isin(["FIT", "T2"])]
        else:
            d = day.xs(per, level="per", drop_level=False)
        b, x = d["base"], d[c]
        dd = x - b
        lots = L[(L.cfg == c) & (L.i >= 0) & ((L.per == per) | (per == "ALL") | ((per == "FIT+T2") & L.per.isin(["FIT", "T2"])))]
        rows.append(dict(cfg=c, per=per, R_base=b.sum(), R=x.sum(), dR=dd.sum(), lots=len(lots), tight_lots=int(lots.tight.sum()),
                         worst_base=b.min(), worst=x.min(), worst_cut=x.min() - b.min(),
                         w5_base=w5(b), w5=w5(x), w5_cut=w5(x) - w5(b),
                         d_le4_base=int((b <= -4).sum()), d_le4=int((x <= -4).sum()),
                         days_better=int((dd > 1e-9).sum()), days_worse=int((dd < -1e-9).sum()),
                         wobd_base=wobd(b), wobd=wobd(x), t_dR=tstat(dd)))
A = pd.DataFrame(rows)
A.round(3).to_csv(OUT / "S_results.csv", index=False)
pd.set_option("display.width", 250)
pr("bars: study N=%d -> %.2f ; lineage N=%d -> %.2f" % (N, BAR, NLIN, BARL))
for per in ("FIT", "T2", "CHECK", "ALL"):
    pr("===== A.", per)
    pr(A[A.per == per].drop(columns=["per"]).round(2).to_string(index=False))

# ---------------------------------------------------------------- B. harm detail (lot-matched)
base = L[(L.cfg == "base") & (L.i >= 0)].set_index(["date", "i"])
top_thr = base.r.quantile(0.9)
best10 = dd_all["base"].nlargest(10).index
harm_rows = []
for c in CFGS:
    x = L[(L.cfg == c) & (L.i >= 0)].set_index(["date", "i"])
    j = base[["r", "kind", "is_burst", "mae", "mfe", "per", "year"]].join(x[["r", "kind", "tight"]].rename(columns={"tight": "tight_c"}), rsuffix="_c", how="outer")
    j["in_b"], j["in_c"] = j.r.notna(), j.r_c.notna()
    both = j[j.in_b & j.in_c]
    t = both[both.tight_c == True]  # noqa: E712
    win_stop = t[(t.r > 0) & (t.kind_c == 1)]
    lose_less = t[(t.r < 0) & (t.r_c > t.r + 1e-9)]
    lose_more = t[(t.r <= 0) & (t.r_c < t.r - 1e-9)]
    small_win_cut = t[(t.r > 0) & (t.kind_c != 1) & (t.r_c < t.r - 1e-9)]
    unchanged = t[(t.r_c - t.r).abs() <= 1e-9]
    other = both[(both.tight_c != True) & ((both.r_c - both.r).abs() > 1e-9)]  # noqa: E712
    only_b, only_c = j[j.in_b & ~j.in_c], j[~j.in_b & j.in_c]
    top = base[base.r >= top_thr]
    topj = top[["r"]].join(x[["r"]], rsuffix="_c")
    kept = (topj.r_c.fillna(0) >= 0.9 * topj.r)
    tb = base[(base.r >= top_thr) & base.is_burst]
    tbj = tb[["r"]].join(x[["r"]], rsuffix="_c")
    harm_rows.append(dict(cfg=c, tight_lots=len(t), tight_base_winners=int((t.r > 0).sum()), tight_base_losers=int((t.r <= 0).sum()),
                          winners_stopped_early=len(win_stop), winners_stopped_lostR=(win_stop.r_c - win_stop.r).sum(),
                          winners_stopped_baseR=win_stop.r.sum(),
                          losers_lose_less=len(lose_less), losers_savedR=(lose_less.r_c - lose_less.r).sum(),
                          small_losers_lose_more=len(lose_more), lose_moreR=(lose_more.r_c - lose_more.r).sum(),
                          unchanged=len(unchanged), other_changed_lots=len(other), otherR=(other.r_c - other.r).sum(),
                          lots_dropped=len(only_b), droppedR=-only_b.r.sum(), lots_added=len(only_c), addedR=only_c.r_c.sum(),
                          top_decile_n=len(topj), top_decile_kept=int(kept.sum()), top_decile_kept_pct=kept.mean() * 100,
                          top_decile_R_base=topj.r.sum(), top_decile_R_cfg=topj.r_c.fillna(0).sum(),
                          top_burst_n=len(tbj), top_burst_kept=int((tbj.r_c.fillna(0) >= 0.9 * tbj.r).sum()),
                          best10_dR=(dd_all.loc[best10, c] - dd_all.loc[best10, "base"]).sum(),
                          best10_days_worse=int(((dd_all.loc[best10, c] - dd_all.loc[best10, "base"]) < -1e-9).sum())))
    if c == "Q50":
        Q50J = j
        win_stop.reset_index().round(3).to_csv(OUT / "S_q50_winners_stopped.csv", index=False)
H = pd.DataFrame(harm_rows)
H.round(3).to_csv(OUT / "S_harm.csv", index=False)
pr("===== B. harm detail (all periods, lot-matched vs base); top-decile threshold r >= %.3f" % top_thr)
pr(H.round(2).T.to_string())
pr("best 10 base days:", list(best10), "base R", dd_all.loc[best10, "base"].round(2).tolist())

# ---------------------------------------------------------------- C. MAE / MFE of base burst lots
bb = base[base.is_burst].copy()
bins = [-9, 0.25, 0.5, 0.75, 1.0 - 1e-9, 99]
labs = ["<0.25", "0.25-0.5", "0.5-0.75", "0.75-<1", ">=1 (stop)"]
bb["mae_b"] = pd.cut(bb.mae, bins, labels=labs)
bb["res"] = np.where(bb.r > 0, "winner", "loser")
M = bb.groupby(["mae_b", "res"], observed=False).agg(n=("r", "size"), R=("r", "sum"), mfe_med=("mfe", "median")).unstack("res")
M.round(3).to_csv(OUT / "S_mae_burst.csv")
pr("===== C. base burst lots by MAE (R units of the normal stop): n=%d, winners=%d (R %.2f), losers=%d (R %.2f)" % (
    len(bb), (bb.r > 0).sum(), bb[bb.r > 0].r.sum(), (bb.r <= 0).sum(), bb[bb.r <= 0].r.sum()))
pr(M.round(2).to_string())
pr("winners with MAE >= 0.5:", int(((bb.r > 0) & (bb.mae >= 0.5)).sum()), "R", round(bb[(bb.r > 0) & (bb.mae >= 0.5)].r.sum(), 2))
pr("by period:", bb.groupby("per").apply(lambda g: "n=%d win=%d win_mae>=.5=%d winR=%.1f lossR=%.1f" % (
    len(g), (g.r > 0).sum(), ((g.r > 0) & (g.mae >= .5)).sum(), g[g.r > 0].r.sum(), g[g.r <= 0].r.sum())).to_string())

# ---------------------------------------------------------------- D. stability: per year / regime / pit state
reg = pd.Series({d: ("up" if v > 0.003 else "down" if v < -0.003 else "quiet") for d, v in SPYOC.items()})
st_rows = []
for c in CFGS:
    dd = dd_all[c] - dd_all["base"]
    for y in sorted(set(dd.index.str[:4])):
        m = dd.index.str[:4] == y
        st_rows.append(dict(cfg=c, cut="year", key=y, sessions=NYEAR.get(y, 0), dR=dd[m].sum(), days_changed=int((dd[m].abs() > 1e-9).sum()),
                            worst_base=dd_all.loc[m, "base"].min(), worst=dd_all.loc[m, c].min(),
                            w5_cut=w5(dd_all.loc[m, c]) - w5(dd_all.loc[m, "base"])))
    for k in ("up", "down", "quiet"):
        m = dd.index.map(lambda d: reg.get(d) == k).to_numpy(bool)
        st_rows.append(dict(cfg=c, cut="regime_hindsight", key=k, sessions=int(m.sum()), dR=dd[m].sum(), days_changed=int((dd[m].abs() > 1e-9).sum()),
                            worst_base=dd_all.loc[m, "base"].min(), worst=dd_all.loc[m, c].min(),
                            w5_cut=w5(dd_all.loc[m, c]) - w5(dd_all.loc[m, "base"])))
    x = L[(L.cfg == c) & (L.i >= 0)].set_index(["date", "i"])
    j = base[["r", "bvw", "bop", "is_burst"]].join(x[["r"]], rsuffix="_c", how="inner")
    j = j[j.is_burst]
    for k, g in j.groupby(j.bvw.map({True: "SPY<VWAP", False: "SPY>=VWAP"})):
        st_rows.append(dict(cfg=c, cut="pit_burst_lots", key=k, sessions=len(g), dR=(g.r_c - g.r).sum(), days_changed=int(((g.r_c - g.r).abs() > 1e-9).sum())))
    for k, g in j.groupby(j.bop.map({True: "SPY<open", False: "SPY>=open"})):
        st_rows.append(dict(cfg=c, cut="pit_burst_lots", key=k, sessions=len(g), dR=(g.r_c - g.r).sum(), days_changed=int(((g.r_c - g.r).abs() > 1e-9).sum())))
ST = pd.DataFrame(st_rows)
ST.round(3).to_csv(OUT / "S_stability.csv", index=False)
pr("===== D. stability (Q50 and variants); pit_burst_lots: 'sessions' = burst lots, 'days_changed' = lots changed")
pr(ST[ST.cfg.isin(["Q50", "AV50", "AO50", "F5_50", "Q50G2"])].round(2).to_string(index=False))
pr("regime day counts (signal days, HINDSIGHT SPY o-c):", reg.value_counts().to_dict())

# ---------------------------------------------------------------- E. plateaus
def plat(cs):
    out = []
    for c in cs:
        a = A[A.cfg == c].set_index("per")
        h = H[H.cfg == c].iloc[0]
        out.append(dict(cfg=c, dR_FIT=a.loc["FIT", "dR"], dR_T2=a.loc["T2", "dR"], dR_CHECK=a.loc["CHECK", "dR"], dR_ALL=a.loc["ALL", "dR"],
                        worst_cut_FIT=a.loc["FIT", "worst_cut"], worst_cut_T2=a.loc["T2", "worst_cut"], worst_cut_CHECK=a.loc["CHECK", "worst_cut"],
                        worst_ALL=a.loc["ALL", "worst"], w5_cut_ALL=a.loc["ALL", "w5_cut"], t_ALL=a.loc["ALL", "t_dR"],
                        tight_lots=a.loc["ALL", "tight_lots"], top_kept_pct=h.top_decile_kept_pct, win_stopped=h.winners_stopped_early,
                        R_per_year=a.loc["ALL", "dR"] / YEARS))
    return pd.DataFrame(out)


PF = plat(["Q30", "Q40", "Q50", "Q60", "Q70", "Q80"])
PK = plat(["K3W5", "K3W10", "K3W15", "K4W5", "Q50", "K4W15", "K5W5", "K5W10", "K5W15", "K6W5", "K6W10", "K6W15"])
PV = plat(["Q50", "AV50", "AO50", "F5_50", "Q50G2"])
pd.concat([PF.assign(grid="fraction"), PK.assign(grid="burst_k_w"), PV.assign(grid="variant")]).round(3).to_csv(OUT / "S_plateau.csv", index=False)
pr("===== E. plateau over stop fraction (k=4, w=10); base worst ALL %.2f, base w5 ALL %.2f" % (dd_all["base"].min(), w5(dd_all["base"])))
pr(PF.round(2).to_string(index=False))
pr("===== E. plateau over burst definition (f=0.5)")
pr(PK.round(2).to_string(index=False))
pr("===== variants")
pr(PV.round(2).to_string(index=False))

# ---------------------------------------------------------------- F. walk-forward (choose f on FIT only)
fit = day.xs("FIT", level="per")
cand = {1.0: fit["base"]}
for f in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
    cand[f] = fit["Q%d" % round(f * 100)]
J = {f: v.sum() + w5(v) for f, v in cand.items()}
JR = {f: v.sum() for f, v in cand.items()}
fJ, fR = max(J, key=J.get), max(JR, key=JR.get)
pr("===== F. walk-forward: J(FIT) = R + worst-5 sum:", {k: round(v, 2) for k, v in J.items()}, "-> chosen f =", fJ,
   "; max-R choice f =", fR)
for f in sorted({fJ, fR}):
    c = "base" if f == 1.0 else "Q%d" % round(f * 100)
    for per in ("T2", "CHECK"):
        d = day.xs(per, level="per")
        pr("  f=%s %s: R %.2f (base %.2f) dR %.2f worst %.2f (base %.2f) w5 %.2f (base %.2f)" % (
            f, per, d[c].sum(), d["base"].sum(), d[c].sum() - d["base"].sum(), d[c].min(), d["base"].min(), w5(d[c]), w5(d["base"])))

# ---------------------------------------------------------------- G. bootstrap + cost per year
rng = np.random.default_rng(1123)
B = []
n = len(dd_all)
idx = rng.integers(0, n, size=(5000, n))
for c in ["Q50", "AV50", "AO50", "F5_50", "Q50G2", "Q40", "Q60"]:
    b, x = dd_all["base"].to_numpy(), dd_all[c].to_numpy()
    bs, xs = b[idx], x[idx]
    dR = (xs - bs).sum(1)
    wc = xs.min(1) - bs.min(1)
    w5c = np.sort(xs, 1)[:, :5].sum(1) - np.sort(bs, 1)[:, :5].sum(1)
    B.append(dict(cfg=c, dR_med=np.median(dR), dR_p5=np.percentile(dR, 5), dR_p95=np.percentile(dR, 95), P_dR_neg=(dR < 0).mean(),
                  worst_cut_med=np.median(wc), worst_cut_p5=np.percentile(wc, 5), worst_cut_p95=np.percentile(wc, 95), P_worst_better=(wc > 1e-9).mean(),
                  P_worst_worse=(wc < -1e-9).mean(),
                  w5_cut_med=np.median(w5c), w5_cut_p5=np.percentile(w5c, 5), w5_cut_p95=np.percentile(w5c, 95), P_w5_better=(w5c > 1e-9).mean(),
                  dR_per_year=dd_all[c].sum() / YEARS - dd_all["base"].sum() / YEARS,
                  usd_per_year=(dd_all[c].sum() - dd_all["base"].sum()) / YEARS * 105,
                  days_changed_per_year=int(((dd_all[c] - dd_all["base"]).abs() > 1e-9).sum()) / YEARS))
BS = pd.DataFrame(B)
BS.round(3).to_csv(OUT / "S_bootstrap.csv", index=False)
pr("===== G. day bootstrap (5000, seed 1123, %d signal days, %.2f years of sessions); $ at $105 risk/lot" % (n, YEARS))
pr(BS.round(2).T.to_string())

# worst 10 base days under each key config
wd = dd_all.loc[dd_all["base"].nsmallest(10).index, ["base", "Q30", "Q40", "Q50", "Q60", "Q70", "Q80", "AV50", "AO50", "F5_50", "Q50G2"]]
wd.round(2).to_csv(OUT / "S_worst_days.csv")
pr("===== worst 10 base days")
pr(wd.round(2).to_string())
bd = dd_all.loc[best10, ["base", "Q40", "Q50", "Q60", "AV50", "AO50", "F5_50", "Q50G2"]]
bd.round(2).to_csv(OUT / "S_best_days.csv")
pr("===== best 10 base days")
pr(bd.round(2).to_string())
(OUT / "S_out.txt").write_text("\n".join(P) + "\n")
