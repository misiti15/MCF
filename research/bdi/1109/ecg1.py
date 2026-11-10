"""ECG1 (research/bdi/1109/ECG1_PLAN.md, pre-registered before this read): block new momentum shorts (MF / flowsell / L3)
at/after 10:00 while the W60 15-min compass reads UP-confirmed. ONE config. 2-year lab lists bt_lab1104, costs in, locked
block excluded (asserted). Also scores the live 11-09 in-sample what-if from the 7 journals + compass/2026-11-09.csv.
Usage: python ecg1.py <scratch-with-journals>     Educational only - not financial advice."""
import glob, importlib.util, io, math, sqlite3, subprocess, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); HERE = Path(__file__).resolve().parent; J = Path(sys.argv[1])
FAM = r"^(?:NM-)?MF\d|flowsell|^L3-"
# ------------------------------------------------------------ W60 on 2 years (state15.hist + comp15 W60 logic)
spec = importlib.util.spec_from_file_location("state15", ROOT / "research/bdi/hc1/state15.py")
argv0 = sys.argv; sys.argv = ["x", str(J)]; s15 = importlib.util.module_from_spec(spec); spec.loader.exec_module(s15); sys.argv = argv0
st = s15.hist().dropna(subset=["fo"]).sort_values(["date", "T"]).reset_index(drop=True)
sg = lambda x: np.nan_to_num(np.sign(np.asarray(x, float))).astype(int)
st["s"] = sg(st.fo)
base = st.s + sg(st.vw) + np.where(st.breadth_open > 0.5, 1, np.where(st.breadth_open < 0.5, -1, 0)) + \
    np.where((st.s == sg(st.qqq_fo)) & (st.s == sg(st.iwm_fo)), st.s, 0)
piv = st.pivot(index="date", columns="T", values="s")
pW = np.zeros(len(st), int); nm = np.zeros(len(st), int)
for T in sorted(st["T"].unique()):
    marks = [t for t in piv.columns if t <= T and t > T - 60]
    sub = piv[marks]; same = sub.eq(sub[T], axis=0).all(axis=1) & (sub[T] != 0)
    i = (st["T"] == T).values
    pW[i] = np.where(same.reindex(st.date[i]).values, piv[T].reindex(st.date[i]).values, 0); nm[i] = len(marks)
v = base.values + pW
st["W60"] = np.where((v >= 4) & (pW == 1) & (nm >= 2), 2, np.where(v >= 2, 1, np.where((v <= -4) & (pW == -1) & (nm >= 2), -2, np.where(v <= -2, -1, 0))))
W = st[st["T"] >= 600].pivot(index="date", columns="T", values="W60")
# ------------------------------------------------------------ lab trades
T = pd.concat(pd.read_parquet(f) for f in sorted(glob.glob(str(ROOT / "research/history2y/data/bt_lab1104/*.parquet"))))
T = T[(T.side == -1) & T.setup.str.contains(FAM, regex=True)].copy()
T = T[~((T.date >= "2024-11-01") & (T.date <= "2025-02-28"))]
assert not ((T.date >= "2024-11-01") & (T.date <= "2025-02-28")).any()
T["m"] = (T.tod // 100) * 60 + T.tod % 100
marks = np.array(sorted(W.columns))
def gate(d, m):
    if m < 600 or d not in W.index: return False
    k = marks[marks <= m]
    return bool(len(k) and W.at[d, k[-1]] == 2)
T["blk"] = [gate(d, m) for d, m in zip(T.date, T.m)]
T["split"] = np.where(T.date <= "2025-12-31", "TRAIN", np.where(T.date <= "2026-10-05", "VALID", "LATE"))
dts = st.groupby("date").agg(o=("open", "first"), c=("close", "first"))
fo10 = st[st["T"] == 600].set_index("date").fo
oc = (dts.c / dts.o - 1) * 100
T["dtype"] = T.date.map(lambda d: "up" if oc.get(d, 0) > 0.25 else ("down" if oc.get(d, 0) < -0.25 else "quiet"))
T["s10"] = T.date.map(lambda d: "above" if fo10.get(d, 0) >= 0 else "below")
out = []
def p(*a): out.append(" ".join(str(x) for x in a)); print(out[-1])
p(f"family shorts {len(T):,} trades, {T.setup.nunique()} setups, {T.date.nunique()} days; blocked share {T.blk.mean():.1%}; "
  f"W60 UP-confirmed share of 10:00+ marks {(W.values == 2).mean():.1%}")
res = {}
for sp in ("TRAIN", "VALID", "LATE"):
    g = T[T.split == sp]; d = g[g.blk]; k = g[~g.blk]
    daily = (-g.r.where(g.blk, 0)).groupby(g.date).sum()
    t = daily.mean() / (daily.std(ddof=1) / math.sqrt(len(daily))) if len(daily) > 2 and daily.std() > 0 else np.nan
    pos = daily[daily != 0]; best = pos.max() if len(pos) else 0
    res[sp] = dict(delta=-d.r.sum(), t=t)
    p(f"{sp}: n {len(g):,} | blocked {len(d):,} avg {d.r.mean():+.4f}R | kept avg {k.r.mean():+.4f}R (base {g.r.mean():+.4f}) | "
      f"delta {-d.r.sum():+.1f}R, day-t {t:.2f} ({len(daily)} days, gate active {int((daily != 0).sum())}); best day {best:+.1f}R "
      f"({best / max(-d.r.sum(), 1e-9):.0%} of delta), delta w/o best {(-d.r.sum() - best):+.1f}R")
    for col in ("dtype", "s10"):
        p(f"   by {col}: " + "; ".join(f"{kk} blocked n {len(x[x.blk])} delta {-x[x.blk].r.sum():+.1f}R (kept avg {x[~x.blk].r.mean():+.3f})" for kk, x in g.groupby(col)))
per = []
for sp in ("TRAIN", "VALID", "LATE"):
    for s, x in T[T.split == sp].groupby("setup"):
        per.append(dict(split=sp, setup=s, n=len(x), blocked=int(x.blk.sum()), setup_R=round(x.r.sum(), 1), delta_R=round(-x[x.blk].r.sum(), 1)))
Pp = pd.DataFrame(per); Pp.to_csv(HERE / "ecg1_setups.csv", index=False)
v = Pp[Pp.split == "VALID"]; worse = v[v.delta_R < -0.05 * v.setup_R.abs()]
p(f"VALID per setup: better {(v.delta_R > 0).sum()}, worse {(v.delta_R < 0).sum()} | " + "; ".join(f"{r.setup} {r.delta_R:+.1f}" for r in v.itertuples()))
p(f"LATE per setup: " + "; ".join(f"{r.setup} {r.delta_R:+.1f}" for r in Pp[Pp.split == 'LATE'].itertuples()))
BAR = max(1.5, math.sqrt(2 * math.log(34))); B90 = max(1.35, 0.9 * BAR)
ok = (res["VALID"]["t"] >= BAR, res["TRAIN"]["delta"] > 0, res["LATE"]["delta"] >= 0, len(worse) == 0)
p(f"BAR (N 34) {BAR:.2f}, BAR90 {B90:.2f}: VALID t {res['VALID']['t']:.2f} >= bar {ok[0]} (BAR90 {res['VALID']['t'] >= B90}); TRAIN delta > 0 {ok[1]}; "
  f"LATE delta >= 0 {ok[2]} ({res['LATE']['delta']:+.1f}R); setups worse > 5%: {len(worse)} {list(worse.setup)} -> {'PASS' if all(ok) else 'FAIL'}")
# ------------------------------------------------------------ live 11-09 (in-sample) what-if, 7 accounts
D = "2026-11-09"
cp = pd.read_csv(io.StringIO(subprocess.run(["git", "-C", str(ROOT), "show", f"origin/mcf-data-compass:compass/{D}.csv"], capture_output=True, text=True).stdout))
cp["m"] = cp["T"].str[:2].astype(int) * 60 + cp["T"].str[3:].astype(int)
L = []
for a in ("p", "t1", "t2", "gy", "gen", "ex1", "ll"):
    t = pd.read_sql("select symbol, strategy, side, entry_time, entry, stop, shares, pnl_adj from trades where date=? and run_id=1", sqlite3.connect(J / a / "journal.db"), params=(D,))
    t["acct"] = a; L.append(t)
L = pd.concat(L); L = L[(L.side == -1) & L.strategy.str.contains(FAM, regex=True)].copy()
L["R"] = L.pnl_adj / ((L.entry - L.stop).abs() * L.shares)
et = pd.to_datetime(L.entry_time, utc=True, format="mixed").dt.tz_convert("America/New_York"); L["m"] = et.dt.hour * 60 + et.dt.minute
def lg(m):
    x = cp[(cp.m <= m) & (cp.m >= 600)]
    return bool(len(x) and x.w60.iloc[-1] == "UP-confirmed")
L["blk"] = L.m.map(lg)
p(f"\nLIVE {D} (in-sample): family shorts {len(L)}, shadow-blocked {int(L.blk.sum())} live {L[L.blk].R.sum():+.2f}R -> gate gain {-L[L.blk].R.sum():+.2f}R; kept {int((~L.blk).sum())} {L[~L.blk].R.sum():+.2f}R")
p("   by account: " + "; ".join(f"{a} {len(x)} {-x.R.sum():+.2f}R" for a, x in L[L.blk].groupby("acct")))
p("   by setup: " + "; ".join(f"{s} {len(x)} {-x.R.sum():+.2f}R" for s, x in L[L.blk].groupby("strategy")))
L.to_csv(HERE / "ecg1_live_1109.csv", index=False)
(HERE / "ecg1_out.txt").write_text("\n".join(out) + "\n\nEducational only - not financial advice.\n")
