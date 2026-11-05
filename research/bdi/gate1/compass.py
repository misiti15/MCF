"""GATE1 COMPASS (owner reframe 11-04): rank point-in-time measures for 'staying' and 'heading', build a 5-level compass,
and score compass-based setup switching. Usage: python compass.py <scratch>. Educational only - not financial advice."""
import math, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
S = Path(sys.argv[1])
CPS = [600, 630, 660, 690, 720, 750, 780, 840]
lab = lambda T: f"{T//60}:{T%60:02d}"
wn = lambda d: "TRAIN" if d < "2026-01-01" else ("VALID" if d <= "2026-10-05" else "LIVE")
st = pd.read_parquet(S / "state.parquet"); st["date"] = st.date.astype(str)
st = st[st.date >= "2024-10-01"].dropna(subset=["close"]).sort_values(["date", "T"]).reset_index(drop=True)
st["w"] = st.date.map(wn)
sg = lambda x: np.nan_to_num(np.sign(np.asarray(x, float))).astype(int)
g = st.groupby("date")
st["p1"] = g.fo.shift(1); st["p2"] = g.fo.shift(2)
st["px60"] = g.px.shift(-2)                                   # checkpoints 30 min apart from 10:00
st.loc[st["T"] == 585, "px60"] = np.nan
pers2 = np.where(sg(st.fo) == sg(st.p1), sg(st.fo), 0)
pers3 = np.where((sg(st.fo) == sg(st.p1)) & (sg(st.p1) == sg(st.p2)), sg(st.fo), 0)
agree = np.where((sg(st.fo) == sg(st.qqq_fo)) & (sg(st.fo) == sg(st.iwm_fo)), sg(st.fo), 0)
bside = np.where(st.breadth_open > 0.5, 1, np.where(st.breadth_open < 0.5, -1, 0))
M = {"fo_sign": sg(st.fo), "vwap_side": sg(st.vw), "r30_sign": sg(st.r30), "persist2": pers2, "persist3": pers3,
     "breadth_side": bside, "index_agree": agree, "state": st.st.values, "strong_fo": np.where(st.fo.abs() >= 0.003, sg(st.fo), 0),
     "gap_sign": sg(st.gap.fillna(0)), "fade_r30": -sg(st.r30), "fade_fo": -sg(st.fo)}
v = sg(st.fo) + sg(st.vw) + pers2 + bside + agree
comp = np.where((v >= 4) & (pers3 == 1), 2, np.where(v >= 2, 1, np.where((v <= -4) & (pers3 == -1), -2, np.where(v <= -2, -1, 0))))
st["compass"] = comp
CN = {2: "UP-confirmed", 1: "leaning up", 0: "mixed", -1: "leaning down", -2: "DOWN-confirmed"}
OUT = {"staying": sg(st.close - st.open), "heading_rod": sg(st.close - st.px), "heading_60m": sg(st.px60 - st.px)}


def wilson(k, n):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n; z = 1.96; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 3), round(c + h, 3))


rows = []
sub = st["T"].isin(CPS).values
for q, y in OUT.items():
    yv = pd.Series(y).where(st.px60.notna() | (q != "heading_60m"))
    for mname, call in M.items():
        for w in ["TRAIN", "VALID", "LIVE"]:
            for T in ["all"] + CPS:
                i = sub & (st.w == w).values & (yv.notna()).values & (call != 0)
                if T != "all":
                    i &= (st["T"] == T).values
                n = int(i.sum())
                if n == 0:
                    continue
                hit = (call[i] == yv.values[i]).mean()
                base_all = sub & (st.w == w).values & yv.notna().values & ((st["T"] == T).values if T != "all" else True)
                pu = (yv.values[base_all] > 0).mean(); share_up = (call[i] > 0).mean()
                base = share_up * pu + (1 - share_up) * (1 - pu)
                lo, hi = wilson(int(round(hit * n)), n)
                rows.append(dict(question=q, measure=mname, w=w, T=T if T == "all" else lab(T), n=n,
                                 coverage=round(n / base_all.sum(), 2), hit=round(hit, 3), lo=lo, hi=hi, base=round(base, 3), lift=round(hit - base, 3)))
H = pd.DataFrame(rows); H.to_csv(HERE / "compass_measures.csv", index=False)
rk = H[H["T"] == "all"].pivot_table(index=["question", "measure"], columns="w", values=["hit", "lift", "n"])
rk.columns = [f"{a}_{b}" for a, b in rk.columns]
rk = rk.reset_index().sort_values(["question", "lift_TRAIN"], ascending=[True, False])
rk.to_csv(HERE / "compass_ranking.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
print(rk[["question", "measure", "n_TRAIN", "hit_TRAIN", "lift_TRAIN", "hit_VALID", "lift_VALID", "n_LIVE", "hit_LIVE", "lift_LIVE"]].round(3).to_string(index=False))

# compass table: checkpoint x reading -> hit rates (reading's direction; mixed: share up)
ct = []
for w in ["TRAIN", "VALID", "LIVE"]:
    for T in CPS:
        for c in [2, 1, 0, -1, -2]:
            i = (st.w == w) & (st["T"] == T) & (st.compass == c)
            if not i.sum():
                continue
            x = st[i]; d = np.sign(c) if c else 1
            r = dict(w=w, T=lab(T), reading=CN[c], n=int(i.sum()))
            for q, y in OUT.items():
                yy = pd.Series(y, index=st.index)[i]; ok = yy.notna() & ((q != "heading_60m") | x.px60.notna())
                k = int((yy[ok] == d).sum()); m = int(ok.sum())
                r[q] = round(k / m, 3) if m else np.nan
                r[q + "_ci"] = wilson(k, m)
            ct.append(r)
CT = pd.DataFrame(ct); CT.to_csv(HERE / "compass_table.csv", index=False)
print(CT.to_string(index=False))

# compass-based switching (family x side or setup), entries >= 10:00, latest checkpoint
T_ = pd.read_parquet(S / "trades.parquet"); T_ = T_[T_.w.isin(["TRAIN", "VALID", "LIVE"])].reset_index(drop=True)
cm = st[st["T"] >= 600][["date", "T", "compass"]].rename(columns={"T": "cp"})
T_ = T_.merge(cm, on=["date", "cp"], how="left")
T_["bk"] = np.where(T_.w == "LIVE", np.where(T_.acct.isin(["primary", "testing", "testing2"]), "LIVE_PT", "LIVE_ALL"), T_.w)
elig = (T_.m >= 600) & T_.compass.notna()
use = []
for unit, mn in [("fs", 200), ("setup", 60)]:
    tr = T_[elig & (T_.w == "TRAIN")]
    gg = tr.groupby([unit, "compass"]).agg(n=("r", "size"), d=("date", "nunique"), a=("r", "mean")).reset_index()
    va = T_[elig & (T_.w == "VALID")].groupby([unit, "compass"]).r.agg(["size", "mean"]).reset_index().rename(columns={"size": "vn", "mean": "va"})
    lv = T_[elig & (T_.w == "LIVE")].groupby([unit, "compass"]).r.agg(["size", "mean"]).reset_index().rename(columns={"size": "ln", "mean": "la"})
    gg = gg.merge(va, on=[unit, "compass"], how="left").merge(lv, on=[unit, "compass"], how="left")
    gg["ok"] = (gg.a > 0) & (gg.n >= mn) & (gg.d >= 15)
    al = gg[gg.ok].groupby(unit).compass.apply(set).to_dict(); al = {k: s for k, s in al.items() if len(s) < 5}
    gg["unit"] = unit; use.append(gg.rename(columns={unit: "u"}))
    key = list(zip(T_[unit].astype(str), T_.compass))
    ok = np.array([(u not in al) or (c in al[u]) for u, c in key])
    for res in [0.0, 0.5]:
        wgt = np.where(elig & ~ok, res, 1.0)
        for bk in ["TRAIN", "VALID", "LIVE_PT"] + ["LIVE5"]:
            i = (T_.bk == bk).values if bk != "LIVE5" else (T_.w == "LIVE").values
            df = T_[i]; w = wgt[i]; r = df.r.values
            day = pd.Series(w * r).groupby(df.date.values).sum(); base = pd.Series(r).groupby(df.date.values).sum(); dd = day - base
            mu = df.groupby("setup").r.transform("mean").values
            ex = pd.Series((1 - w) * (mu - r)).groupby(df.date.values).sum()
            tt = lambda x: round(x.mean() / (x.std(ddof=1) / math.sqrt(len(x))), 2) if x.std() > 0 else np.nan
            kept = w.sum(); best = day.idxmax(); kb = w[df.date.values == best].sum()
            print(f"compass-gate {unit} {'off' if res == 0 else 'half'} {bk}: totR {day.sum():.1f} avgR {day.sum()/kept:.4f} kept {kept/len(df):.3f} "
                  f"w/o best {(day.sum()-day.max())/(kept-kb):.4f} green {(day>0).mean():.2f} delta {dd.sum():.1f} t {tt(dd)} ex {ex.sum():.1f} ex_t {tt(ex)}")
    print(unit, "gated units:", len(al))
U = pd.concat(use); U["reading"] = U.compass.map(CN); U.round(3).to_csv(HERE / "compass_usage.csv", index=False)
F = U[(U.unit == "fs")].pivot_table(index="u", columns="reading", values=["a", "va", "la"]).round(3)
print(F.to_string())
B = U[(U.a > 0) & (U.va > 0) & (U.n >= 200) & (U.vn >= 200)].sort_values("va", ascending=False)
print(B.head(20).round(3).to_string())
