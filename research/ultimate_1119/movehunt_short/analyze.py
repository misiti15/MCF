"""movehunt_short analysis: pre-declared grid on the fit-half signal table (build.py). Educational only - not financial advice.
Universe U1 (primary): px >= 5, ADV20 >= $20M, 1R >= 0.40% of price. Primary geometry g1 (t1 s1 cap45, LR8 costs).
Sub-halves for sign persistence: A = 2024-10 + 2025-03..05, B = 2025-06..09. SPY up/down day split is an END-OF-DAY
label used only as a diagnostic (never as a filter).
"""
import glob, sys, numpy as np, pandas as pd

TMP = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mhs_tmp"
OUT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ult/research/ultimate_1119/movehunt_short/"
ETB = set(pd.read_csv("/home/user/MCF/data/universe.csv").query("easy_to_borrow == True").symbol)

def _ld(f):
    d = pd.read_parquet(f)
    d["g1c"] = d.g1.clip(-1.5, 2.0).astype("float32")   # diagnostic: caps tiny-risk fills (R denominator = fill-to-stop)
    return d
x = pd.concat([_ld(f) for f in glob.glob(f"{TMP}/*.parquet")], ignore_index=True)
x["date"] = x.date.astype("category"); x["sym"] = x.sym.astype("category")
_ds = pd.Series(x.date.unique().astype(str))
assert not ((_ds >= "2024-11-01") & (_ds <= "2025-02-28")).any() and (_ds < "2025-10-01").all()
spyday = x[x.tod == 1515].groupby("date", observed=True).spyfo.first()   # spy from open at the last signal (15:15) ~ day direction (diagnostic only)
x["spyup"] = x.date.map(spyday > 0).astype(bool)
x["half"] = np.where((x.date.astype(str) < "2025-06-01"), "A", "B")
x["etb"] = x.sym.isin(ETB)
x["fnh"] = ((x.min_hod >= 3) & (x.min_hod <= 30) & (x.dh_atr >= 0.25)).astype(int)
U1 = x[(x.adv_m >= 20) & (x.r0pct >= 0.40)].copy()
print("rows", len(x), "U1", len(U1), "days", x.date.nunique(), "syms", x.sym.nunique(), flush=True)
NCFG = 0


def stats(d, g="g1"):
    if len(d) == 0:
        return dict(n=0)
    day = d.groupby("date", observed=True)[g].agg(["sum", "count"])
    tot = day["sum"].sum()
    best = day["sum"].max()
    nd = len(day)
    m = d[g].mean()
    # day-clustered t
    se = day["sum"].std(ddof=1) * np.sqrt(nd) / len(d) if nd > 1 else np.nan
    wo = (tot - best) / (len(d) - day.loc[day["sum"].idxmax(), "count"]) if len(d) > day["count"].max() else np.nan
    hA, hB = d[d.half == "A"][g].mean(), d[d.half == "B"][g].mean()
    return dict(n=len(d), days=nd, per_day=round(len(d) / x.date.nunique(), 2), hit=round(d.w1.mean(), 3), swing=round(d.sw.mean(), 3),
                avgR=round(m, 4), totR=round(tot, 1), t=round(m / se, 2) if se and se > 0 else np.nan, avgR_wo_best=round(wo, 4),
                best_share=round(best / tot, 2) if tot > 0 else np.nan, A=round(hA, 4), B=round(hB, 4),
                up=round(d[d.spyup][g].mean(), 4), down=round(d[~d.spyup][g].mean(), 4), etb=round(d[d.etb][g].mean(), 4),
                g1c=round(d.g1c.mean(), 4), g2=round(d.g2.mean(), 4), g3=round(d.g3.mean(), 4), g4=round(d.g4.mean(), 4))


rows = []
base = stats(U1); base.update(kind="baseline", name="U1 all bars 09:50-15:15"); rows.append(base); NCFG += 1
b0 = stats(x); b0.update(kind="baseline", name="U0 (px>=5, adv>=10M) all bars"); rows.append(b0); NCFG += 1

MARG = {
    "tod": ("tod", [950, 1030, 1130, 1300, 1400, 1516]),
    "gap%": ("gap", [-99, -3, -1, 1, 3, 99]),
    "runup_open_atr": ("ro_atr", [-99, 0, 0.5, 1, 2, 99]),
    "runup_lod_atr": ("rl_atr", [0, 1, 2, 3, 99]),
    "rsi5": ("rsi5", [0, 70, 80, 90, 101]),
    "vwap_z": ("vwz", [-99, 1, 2, 3, 99]),
    "failed_new_high": ("fnh", [0, 0.5, 2]),
    "blowoff_lower_high": ("blow", [0, 0.5, 2]),
    "ret5_atr(rolling over<0)": ("ret5", [-99, 0, 99]),
    "rvol15": ("rv15", [0, 1, 2, 999]),
    "spy_since_0950%": ("spy950", [-99, -0.2, 0.2, 99]),
    "spy_30min%": ("spy30", [-99, -0.1, 0.1, 99]),
    "price": ("px", [5, 10, 20, 1e9]),
    "atr%": ("atrpct", [0, 3, 5, 999]),
    "adv_$M": ("adv_m", [20, 100, 500, 1e12]),
}
for nm, (col, edges) in MARG.items():
    cut = pd.cut(U1[col], edges, right=False)
    for iv, d in U1.groupby(cut, observed=True):
        s = stats(d); s.update(kind="marginal", name=f"{nm} {iv}"); rows.append(s); NCFG += 1


def first(d):
    return d.sort_values(["date", "sym", "tod"]).drop_duplicates(["date", "sym"])  # first signal per symbol-day


U = U1
C = {
    "K1 ext: runup_open>=1.5ATR & rsi5>=80": (U.ro_atr >= 1.5) & (U.rsi5 >= 80),
    "K2 vwap: vwz>=2.5 & rsi5>=80": (U.vwz >= 2.5) & (U.rsi5 >= 80),
    "K3 failed new high & runup_lod>=2ATR": (U.fnh == 1) & (U.rl_atr >= 2),
    "K4 blow-off lower high & runup_lod>=1.5ATR": (U.blow == 1) & (U.rl_atr >= 1.5),
    "K5 gapdn rsi5pop: gap<=-2 & runup_open>=1 & rsi5>=75": (U.gap <= -2) & (U.ro_atr >= 1) & (U.rsi5 >= 75),
    "K6 K5 & spy950<=+0.15": (U.gap <= -2) & (U.ro_atr >= 1) & (U.rsi5 >= 75) & (U.spy950 <= 0.15),
    "K7 K1 & spy950<=+0.15": (U.ro_atr >= 1.5) & (U.rsi5 >= 80) & (U.spy950 <= 0.15),
    "K8 K2 & ret5<0": (U.vwz >= 2.5) & (U.rsi5 >= 80) & (U.ret5 < 0),
    "K9 no-gap ext: |gap|<1 & runup_open>=2 & vwz>=2": (U.gap.abs() < 1) & (U.ro_atr >= 2) & (U.vwz >= 2),
    "K10 L3-like: gap<=-2.5 & runup_open>=1.5 & 10:15-13:00": (U.gap <= -2.5) & (U.ro_atr >= 1.5) & (U.tod >= 1015) & (U.tod <= 1300),
    "K11 K10 & spy950<=+0.15": (U.gap <= -2.5) & (U.ro_atr >= 1.5) & (U.tod >= 1015) & (U.tod <= 1300) & (U.spy950 <= 0.15),
    "K12 late ext: tod>=14:00 & runup_open>=1.5 & vwz>=2": (U.tod >= 1400) & (U.ro_atr >= 1.5) & (U.vwz >= 2),
    "K13 K1 & ret5<0 & spy30<=+0.1": (U.ro_atr >= 1.5) & (U.rsi5 >= 80) & (U.ret5 < 0) & (U.spy30 <= 0.1),
    "K14 control: random bar while spy950<=-0.2": (U.spy950 <= -0.2),
    # added after the first partial look (gap>=3 marginal was the least-bad bucket): counted like the rest
    "K15 gapup ext: gap>=3 & runup_open>=1 & rsi5>=80": (U.gap >= 3) & (U.ro_atr >= 1) & (U.rsi5 >= 80),
    "K16 gapup failed new high: gap>=3 & fnh": (U.gap >= 3) & (U.fnh == 1),
    "K17 gapup vwap stretch rolling: gap>=3 & vwz>=2 & ret5<0": (U.gap >= 3) & (U.vwz >= 2) & (U.ret5 < 0),
}
todb = pd.cut(U1.tod, MARG["tod"][1], right=False)
base_tod = U1.groupby(todb, observed=True).g1.mean()
for nm, m in C.items():
    d = first(U[m])
    for g in ("g1", "g2", "g3", "g4"):
        s = stats(d, g); s.update(kind="combo", name=nm + f" [{g}]")
        if g == "g1":
            w = pd.cut(d.tod, MARG["tod"][1], right=False).value_counts(normalize=True)
            s["tod_matched_base"] = round(float((w * base_tod.reindex(w.index)).sum()), 4)
        rows.append(s); NCFG += 1
r = pd.DataFrame(rows)
cols = ["kind", "name", "n", "days", "per_day", "hit", "swing", "avgR", "totR", "t", "avgR_wo_best", "best_share", "A", "B", "up", "down", "etb", "g1c", "g2", "g3", "g4", "tod_matched_base"]
r = r[[c for c in cols if c in r.columns]]
r.to_csv(OUT + "cells.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 300)
print(r.to_string(index=False))
print("configurations counted:", NCFG)
