"""shorts_autopsy bench: 8 short setups' bench10 candidate lots, LIVE-L costs, entry >= $5, ETB >= 0.9.
(1) descriptive breakdown by the live autopsy's dimensions per split; (2) the 4 pre-registered skip rules (PREREG.md) vs
matched random removals. Candidate level (no cap/latch). Locked block 2024-11-01..2025-02-28 never read (asserted).
cwd = repo checkout. Usage: python bench_score.py WORK > bench_score_out.txt. Educational only - not financial advice."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.dataset as pads
sys.path.insert(0, "."); sys.path.insert(0, "research/ultimate_1119/top10"); sys.path.insert(0, "research/primshorts_1126")
import bench10 as B  # noqa: E402
import calib_live as CL  # noqa: E402
W = Path(sys.argv[1]); TZ = "America/New_York"; LOCK = ("2024-11-01", "2025-02-28")
GD = ["L3-gap-slope-fromopen-FD", "L3-gap-slope-lowdist-FD", "L3-gap-slope-rsi5hi-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
      "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "CWT09-gapdn-vwaploss-g10-short"]
OTH = ["RW6-ns2-up3-short-FD", "NM-RWN4-ns2-spyup05-notfri-short"]
PRIM = GD[0], GD[3], GD[4]
def period(d):
    if ("2024-10-01" <= d <= "2024-10-31") or ("2025-03-01" <= d <= "2025-09-30"): return "FIT"
    if "2025-10-01" <= d <= "2026-11-04": return "CHECK"
    if "2023-01-03" <= d <= "2024-09-13": return "T2"
    return "none"
def nolock(ds):
    d = pd.Series(list(ds)).astype(str); assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any()
x = pd.concat([pd.read_parquet(W / f) for f in ("trades_t1.parquet", "trades_t2.parquet") if (W / f).exists()], ignore_index=True)
x["date"] = x.date.astype(str); x = B.add_r(x); x["per"] = x.date.map(period); x = x[x.per != "none"]; nolock(x.date.unique())
etb = pd.read_parquet("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/S/etb_rate.parquet").rate
x = x[(x.entry >= 5) & x.symbol.map(etb).fillna(0).ge(0.9)].copy()
cells = json.load(open("research/primshorts_1126/cells_live.json"))
kd = np.where(x.kind == 2, "target", np.where(x.kind == 1, "stop", "market"))
x["r"] = x.r_gross - CL.predict_R(cells, x.entry.to_numpy(), x.risk.to_numpy(), kd)
x["fam"] = np.where(x.setup.isin(GD), "gapdn", "other")
# SPY day table from 1-min caches (open 09:30 bar, regular close), plus SPY at each minute for open->entry
rows = {}
for src, lo, hi in ((Path("/home/user/MCF/data/cache_fresh/1Min/SPY.parquet"), "2022-12-01", "2024-09-13"),
                    (Path("/home/user/MCF/data/cache_hist/1Min/SPY.parquet"), "2024-09-16", "2026-11-04")):
    f = pads.field("__index_level_0__")
    b = pads.dataset(str(src)).to_table(filter=(f < pd.Timestamp(LOCK[0], tz=TZ)) | (f >= pd.Timestamp("2025-03-01", tz=TZ))).to_pandas()
    b = b.set_index("__index_level_0__") if "__index_level_0__" in b.columns else b
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    hm = b.index.hour * 100 + b.index.minute; b = b[(hm >= 930) & (hm < 1600)]
    b["date"] = b.index.date.astype(str); b["hm"] = b.index.hour * 100 + b.index.minute
    b = b[(b.date >= lo) & (b.date <= hi)]; nolock(b.date.unique())
    for d, g in b.groupby("date"):
        c11 = g[g.hm <= 1100].close
        rows[d] = dict(o=g.open.iloc[0], c=g.close.iloc[-1], c11=c11.iloc[-1] if len(c11) else np.nan, mins=g.set_index("hm").close)
dts = sorted(rows); sp = pd.DataFrame({d: {k: v for k, v in rows[d].items() if k != "mins"} for d in dts}).T.astype(float)
sp["pc"] = sp.c.shift(1); sp.loc[pd.to_datetime(pd.Series(sp.index, index=sp.index)).diff().dt.days.gt(5), "pc"] = np.nan
sp["gap"] = (sp.o / sp.pc - 1) * 100; sp["oc"] = (sp.c / sp.o - 1) * 100; sp["am"] = (sp.c11 / sp.o - 1) * 100; sp["pm"] = (sp.c / sp.c11 - 1) * 100
x["spy_gap"] = x.date.map(sp.gap); x["spy_oc"] = x.date.map(sp.oc); x["am"] = x.date.map(sp.am); x["pm"] = x.date.map(sp.pm)
def spy_at(r):
    m = rows.get(r.date); 
    if m is None: return np.nan
    s = m["mins"]; i = s.index.searchsorted(r.tod, side="right") - 1
    return (s.iloc[i] / m["o"] - 1) * 100 if i >= 0 else np.nan
x["spy_oe"] = [spy_at(r) for r in x[["date", "tod"]].itertuples()]
x["stop_bp"] = x.risk / x.entry * 1e4
print(f"lots {len(x)}; by split/setup:"); print(x.groupby(["setup", "per"]).size().unstack().to_string())
print("SPY gap missing share %.4f" % x.spy_gap.isna().mean())
NS = {p: int(sp.index.map(period).tolist().count(p)) for p in ("FIT", "CHECK", "T2")}
print("sessions", NS)
def st(g, per):
    ds = g.groupby("date").r.sum(); se = ds.std(ddof=1) / np.sqrt(len(ds)) if len(ds) > 1 else np.nan
    tot = g.r.sum(); best = ds.max() if len(ds) else 0
    return pd.Series(dict(n=len(g), days=len(ds), avgR=g.r.mean(), gross=g.r_gross.mean(), R_per_sess=tot / NS[per],
                          day_t=ds.mean() / se if se and se > 0 else np.nan, avg_wo_best=(tot - best) / max(1, len(g))))
pd.set_option("display.width", 250)
def tab(name, col, bins):
    print(f"\n## {name}")
    for per in ("CHECK", "T2", "FIT"):
        y = x[x.per == per]
        if not len(y): continue
        y = y.assign(b=pd.cut(y[col], bins)) if bins is not None else y.assign(b=y[col])
        o = y.groupby(["fam", "b"], observed=True).apply(st, per=per); print(f"[{per}]"); print(o.round(3).to_string())
print("\n## Totals by setup and split")
for per in ("CHECK", "T2", "FIT"):
    if not (x.per == per).any(): continue
    print(f"[{per}]"); print(x[x.per == per].groupby("setup").apply(st, per=per).round(3).to_string())
tab("Stock gap (%)", "gap", [-100, -5, -2.66, -1, 1, 100])
tab("SPY gap (%)", "spy_gap", [-10, -0.5, -0.15, 0.15, 0.5, 10])
tab("SPY open->entry (%)", "spy_oe", [-10, -1, -0.5, -0.2, 0.2, 0.5, 1, 10])
tab("Entry time", "tod", [900, 1030, 1200, 1400, 1600])
tab("Entry price ($)", "entry", [0, 10, 20, 50, 100, 200, 1e6])
tab("Stop width (bp)", "stop_bp", [0, 50, 75, 100, 150, 250, 1e5])
x["shape"] = np.where((x.am < -0.2) & (x.pm > 0.4), "dnAM-rallyPM", np.where((x.am > 0.2) & (x.pm < -0.4), "upAM-fadePM", "other"))
tab("SPY day shape (hindsight, descriptive)", "shape", None)
tab("SPY open->close (hindsight, descriptive)", "spy_oc", [-10, -0.75, -0.25, 0.25, 0.75, 10])
# ---------------- pre-registered rules
rng = np.random.default_rng(20261127)
RULES = {"R1 GD-SPYUP": lambda y: (y.fam == "gapdn") & (y.spy_gap >= 0.5),
         "R2 SPYDN": lambda y: y.spy_gap <= -0.5,
         "R3 AM-OTHER": lambda y: (y.fam == "other") & (y.tod < 1200),
         "R4 R1+R2": lambda y: ((y.fam == "gapdn") & (y.spy_gap >= 0.5)) | (y.spy_gap <= -0.5)}
DAYLEVEL = {"R1 GD-SPYUP": "gapdn", "R2 SPYDN": "all", "R4 R1+R2": "mixed"}
def goal(ds, n):
    full = ds.reindex(n, fill_value=0.0)
    return dict(worst5=full.nsmallest(5).sum(), red_per_mo=(full < 0).mean() * 21, avg_day=full.mean())
print("\n## Pre-registered rules (candidate level, all 8 setups pooled; LIVE-L)")
res = []
for name, f in RULES.items():
    for per in ("CHECK", "T2", "FIT"):
        y = x[x.per == per]; days = sorted(d for d in sp.index if period(d) == per)
        if not len(y): continue
        rm = f(y).fillna(False).to_numpy()
        rem = y[rm]; dsr = rem.groupby("date").r.sum().reindex(days, fill_value=0.0)
        gain = -dsr.sum() / len(days); se = dsr.std(ddof=1) / np.sqrt(len(days)); t = -dsr.mean() / se if se > 0 else np.nan
        # matched random control
        sims = []
        if name in DAYLEVEL:
            k = rem.date.nunique()
            if name == "R1 GD-SPYUP": pool = y[y.fam == "gapdn"]
            elif name == "R2 SPYDN": pool = y
            else: pool = None
            for _ in range(1000):
                dd = set(rng.choice(days, size=k, replace=False))
                if pool is not None:
                    sims.append(-pool[pool.date.isin(dd)].r.sum() / len(days))
                else:  # R4: R2-like on k2 days + R1-like on k1 days
                    k2 = y[y.spy_gap <= -0.5].date.nunique(); d2 = set(list(dd)[:k2]); d1 = set(list(dd)[k2:])
                    sims.append(-(y[y.date.isin(d2)].r.sum() + y[(y.fam == "gapdn") & y.date.isin(d1)].r.sum()) / len(days))
        else:
            pool = np.flatnonzero((y.fam == "other").to_numpy()); r = y.r.to_numpy()
            for _ in range(1000):
                sims.append(-r[rng.choice(pool, size=rm.sum(), replace=False)].sum() / len(days))
        pct = (np.array(sims) < gain).mean() * 100
        g0 = goal(y.groupby("date").r.sum(), days); g1 = goal(y[~rm].groupby("date").r.sum(), days)
        best_share = (-dsr).max() / (-dsr.sum()) if -dsr.sum() > 0 else np.nan
        ps = y.assign(rm=rm).groupby("setup").apply(lambda g: -g[g.rm].r.sum() / len(days))
        res.append(dict(rule=name, split=per, lots_removed=int(rm.sum()), share=rm.mean(), days_hit=rem.date.nunique(),
                        dR_sess=gain, t=t, pct_vs_random=pct, best_share=best_share, worst5_before=g0["worst5"], worst5_after=g1["worst5"],
                        red_mo_before=g0["red_per_mo"], red_mo_after=g1["red_per_mo"], setups_better=int((ps > 0).sum()), setups_worse=int((ps < 0).sum()),
                        per_setup=" ".join(f"{s.split('-')[0]}{'' if s not in GD[:3] else s.split('-')[3][:4]}:{v:+.2f}" for s, v in ps.items())))
R = pd.DataFrame(res); print(R.drop(columns="per_setup").round(3).to_string()); print(R[["rule", "split", "per_setup"]].to_string())
R.to_csv(Path(__file__).with_name("bench_rules.csv"), index=False)
x.drop(columns=[c for c in ("stop", "tgt") if c in x.columns]).to_parquet(W / "bench_feat.parquet")
