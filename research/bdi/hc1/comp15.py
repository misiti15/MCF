"""COMP15 (PLAN.md): compass every 15 min from 09:45 on rolling 30/45/60-min / whole-day windows vs the 30-min GATE1
compass. Usage: python comp15.py <scratch>. Writes comp15_*.csv here and <scratch>/compass15.parquet (for HC1).
Educational only - not financial advice."""
import math, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
S = Path(sys.argv[1])
per = lambda d: "TRAIN" if d <= "2026-02-28" else ("VALID" if d <= "2026-10-07" else ("FWD" if d <= "2026-11-04" else "LIVE"))
st = pd.concat([pd.read_parquet(S / "state15.parquet"), pd.read_parquet(S / "state15_live.parquet")])
st = st[st.date >= "2024-10-01"].dropna(subset=["close"]).sort_values(["date", "T"]).reset_index(drop=True)
st["w"] = st.date.map(per)
sg = lambda x: np.nan_to_num(np.sign(np.asarray(x, float))).astype(int)
st["s"] = sg(st.fo)
base = st.s + sg(st.vw) + np.where(st.breadth_open > 0.5, 1, np.where(st.breadth_open < 0.5, -1, 0)) + \
    np.where((st.s == sg(st.qqq_fo)) & (st.s == sg(st.iwm_fo)), st.s, 0)
lab = lambda T: f"{T // 60}:{T % 60:02d}"


def reading(v, p, nm):
    return np.where((v >= 4) & (p == 1) & (nm >= 2), 2, np.where(v >= 2, 1, np.where((v <= -4) & (p == -1) & (nm >= 2), -2,
                    np.where(v <= -2, -1, 0))))


# rolling-window compasses on the 15-min clock
piv = st.pivot(index="date", columns="T", values="s")
CL = {}
for W in [30, 45, 60, "day"]:
    pW = np.zeros(len(st), int); nm = np.zeros(len(st), int)
    for T in sorted(st["T"].unique()):
        marks = [t for t in piv.columns if t <= T and (W == "day" or t > T - W)]
        sub = piv[marks]
        same = sub.eq(sub[T], axis=0).all(axis=1) & (sub[T] != 0)
        i = (st["T"] == T).values
        pW[i] = np.where(same.reindex(st.date[i]).values, piv[T].reindex(st.date[i]).values, 0)
        nm[i] = len(marks)
    CL[f"W{W}"] = reading(base.values + pW, pW, nm)
# 30-min GATE1 compass (persist2 / persist3 on 09:45, 10:00, 10:30, ...), held between its checkpoints
c30 = st[st["T"].isin([585] + list(range(600, 931, 30)))].copy()
g = c30.groupby("date").s
p1, p2 = g.shift(1), g.shift(2)
pers2 = np.where(c30.s == p1, c30.s, 0); pers3 = np.where((c30.s == p1) & (p1 == p2), c30.s, 0)
v30 = base[c30.index].values + pers2
c30["c30"] = np.where((v30 >= 4) & (pers3 == 1), 2, np.where(v30 >= 2, 1, np.where((v30 <= -4) & (pers3 == -1), -2, np.where(v30 <= -2, -1, 0))))
c30.loc[c30["T"] == 585, "c30"] = np.nan                    # 09:45 is a persistence input only in GATE1
st = st.merge(c30[["date", "T", "c30"]], on=["date", "T"], how="left")
st["C30"] = st.groupby("date").c30.ffill()                 # held on the 15-min clock
for k, v in CL.items():
    st[k] = v
CLOCKS = ["C30", "W30", "W45", "W60", "Wday"]
st["y_stay"] = sg(st.close - st.open); st["y_rod"] = sg(st.close - st.px)
st["y_30"] = np.where(st.px30.notna(), sg(st.px30 - st.px), 0); st["y_60"] = np.where(st.px60.notna(), sg(st.px60 - st.px), 0)
st.to_parquet(S / "compass15.parquet")

Q = ["y_stay", "y_rod", "y_30", "y_60"]


def dct(x):
    x = pd.Series(x).dropna()
    return round(x.mean() / (x.std(ddof=1) / math.sqrt(len(x))), 2) if len(x) > 2 and x.std() > 0 else np.nan


rows = []
ev = st[st["T"] >= 600]                                    # matched clock 10:00..15:30 (09:45 reported apart)
for w in ["TRAIN", "VALID", "FWD", "LIVE"]:
    e = ev[ev.w == w]
    for lvl in ["confirmed", "directional"]:
        for q in Q:
            ref = None
            for c in CLOCKS:
                r = e[c].values
                sel = (np.abs(r) == 2) if lvl == "confirmed" else (r != 0)
                sel &= (e[q].values != 0) & ~np.isnan(r)
                hit = (np.sign(r[sel]) == e[q].values[sel]).astype(float)
                dh = pd.Series(hit).groupby(e.date.values[sel]).mean()
                if c == "C30":
                    ref = dh
                d = (dh - ref).dropna() if c != "C30" else pd.Series(dtype=float)
                rows.append(dict(w=w, level=lvl, q=q, clock=c, n=int(sel.sum()), days=dh.size, cover=round(sel.mean(), 3),
                                 hit=round(hit.mean(), 4) if len(hit) else np.nan,
                                 d_vs_C30_dayavg=round(d.mean(), 4) if len(d) else np.nan, t=dct(d)))
H = pd.DataFrame(rows); H.to_csv(HERE / "comp15_hits.csv", index=False)
# half-hour checkpoints only (C30 native vs 15-min windows at the same T)
hh = ev[ev["T"].isin(range(630, 931, 30))]
r2 = []
for w in ["TRAIN", "VALID", "FWD"]:
    e = hh[hh.w == w]
    for c in CLOCKS:
        for lvl in ["confirmed", "directional"]:
            r = e[c].values; sel = ((np.abs(r) == 2) if lvl == "confirmed" else (r != 0))
            r2.append(dict(w=w, clock=c, level=lvl, n=int(sel.sum()), **{q: round((np.sign(r[sel & (e[q].values != 0)]) == e[q].values[sel & (e[q].values != 0)]).mean(), 4) for q in Q}))
pd.DataFrame(r2).to_csv(HERE / "comp15_halfhour.csv", index=False)

# 09:45 low-confidence reading (rolling windows only; C30 has none)
e45 = st[st["T"] == 585]
r45 = []
for w in ["TRAIN", "VALID", "FWD"]:
    e = e45[e45.w == w]
    for lvl in [1, -1]:
        sel = np.sign(e.W30.values) == lvl
        r45.append(dict(w=w, reading="leaning up" if lvl == 1 else "leaning down", n=int(sel.sum()),
                        **{q: round((e[q].values[sel] == lvl).mean(), 3) for q in Q}))
pd.DataFrame(r45).to_csv(HERE / "comp15_0945.csv", index=False)

# earliness and flips per day
er = []
for c in CLOCKS:
    for d, x in st.groupby("date"):
        r = x[c].values; Tt = x["T"].values; side = x.y_stay.iloc[0]
        conf = np.flatnonzero(np.abs(np.nan_to_num(r)) == 2)
        nz = [np.sign(v) for v in r if not np.isnan(v) and v != 0]
        cf = [np.sign(v) for v in r if not np.isnan(v) and abs(v) == 2]
        er.append(dict(date=d, w=x.w.iloc[0], clock=c, first=Tt[conf[0]] if len(conf) else np.nan,
                       first_ok=float(np.sign(r[conf[0]]) == side) if len(conf) else np.nan,
                       flips=sum(a != b for a, b in zip(nz, nz[1:])), cflips=sum(a != b for a, b in zip(cf, cf[1:])),
                       changes=sum(a != b for a, b in zip(r[~np.isnan(r)], r[~np.isnan(r)][1:]))))
E = pd.DataFrame(er)
ES = E.groupby(["w", "clock"]).agg(days=("date", "size"), med_first=("first", "median"), conf_any=("first", lambda x: x.notna().mean()),
                                    by1015=("first", lambda x: (x <= 615).mean()), by1030=("first", lambda x: (x <= 630).mean()),
                                    by1100=("first", lambda x: (x <= 660).mean()), first_prec=("first_ok", "mean"),
                                    flips=("flips", "mean"), cflips=("cflips", "mean"), changes=("changes", "mean")).reset_index()
ES["med_first"] = ES.med_first.map(lambda v: lab(int(v)) if v == v else "-")
# day-paired earliness and flips vs C30
for c in CLOCKS[1:]:
    for w in ["TRAIN", "VALID", "FWD"]:
        a = E[(E.clock == c) & (E.w == w)].set_index("date"); b = E[(E.clock == "C30") & (E.w == w)].set_index("date")
        both = a["first"].notna() & b["first"].notna()
        i = (ES.clock == c) & (ES.w == w)
        ES.loc[i, "earlier_min_med"] = (b["first"] - a["first"])[both].median()
        ES.loc[i, "dflips_t"] = dct(a.flips - b.flips)
ES.round(3).to_csv(HERE / "comp15_early_flips.csv", index=False)
CN = {2: "UP-conf", 1: "lean up", 0: "mixed", -1: "lean dn", -2: "DN-conf"}
lv = st[st.w == "LIVE"][["T", "fo", "breadth_open"] + CLOCKS].copy()
lv["T"] = lv["T"].map(lab)
for c in CLOCKS:
    lv[c] = lv[c].map(lambda v: CN.get(int(v), "-") if v == v else "-")
lv.round(4).to_csv(HERE / "comp15_live_1105.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
print(H[H.w.isin(["TRAIN", "VALID", "FWD"])].to_string(index=False)); print(pd.DataFrame(r2).to_string(index=False))
print(pd.DataFrame(r45).to_string(index=False)); print(ES.round(3).to_string(index=False)); print(lv.to_string(index=False))
