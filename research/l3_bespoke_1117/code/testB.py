"""Test B: time / day-type split (descriptive) + 8 latch-rule configs (engine + live)."""
import numpy as np, pandas as pd
import load4 as L, sim4
from live import T, replay, stats as lstats
SD = L.SD
s10 = SD.spy10.to_dict()
def mk(am, pm):
    return lambda d, em: (am if em < 720 else pm)
def spyrule(cond, lim_true, lim_else=-2.0):
    def f(d, em):
        if em < 600 or d not in s10:
            return lim_else
        return lim_true if cond(s10[d]) else lim_else
    return f
CFG = {"PARENT -2": -2.0,
       "B1 AM -2 / PM none": mk(-2.0, None), "B2 AM -2 / PM -3": mk(-2.0, -3.0), "B3 AM -2 / PM -4": mk(-2.0, -4.0),
       "B4 AM none / PM -2": mk(None, -2.0), "B5 AM -3 / PM -2": mk(-3.0, -2.0),
       "B6 -3 if SPY10<open": spyrule(lambda x: x < 0, -3.0), "B7 -1 if SPY10>=+0.25%": spyrule(lambda x: x >= 0.25, -1.0),
       "B8 none if SPY10<open": spyrule(lambda x: x < 0, None)}
bk = pd.read_pickle("A_books.pkl")
rows = []
for test in ("replay", "2y"):
    raw = bk[(test, "raw")]; days = L.DAYS[test]; base = None
    for name, lim in CFG.items():
        b = sim4.book(raw, sim4.P, lim)
        if base is None: base = b
        segs = [("ALL", b, base, days)]
        if test == "2y":
            for sp in ("TRAIN", "VALID", "FWD"):
                dd = [d for d in days if L.split(d) == sp]
                segs.append((sp, b[b.date.map(L.split) == sp], base[base.date.map(L.split) == sp], dd))
        for seg, bb, bs, dd in segs:
            t, dr = sim4.paired_t(bs, bb, dd)
            rows.append(dict(test=test, seg=seg, cfg=name, **sim4.stats(bb, dd), t_vs_parent=t, dR_vs_parent=dr))
# live
base = None
for name, lim in CFG.items():
    m = replay(T, lim); x = T[m]
    for acct_sel in (["Primary"], ["Primary", "On Deck"]):
        xx = x[x.acct.isin(acct_sel)]
        rows.append(dict(test="live " + "+".join(acct_sel), seg="ALL", cfg=name, **{k: v for k, v in lstats(xx).items()}))
df = pd.DataFrame(rows); df.to_csv("B_latch_rules.csv", index=False, float_format="%.4f")
pd.set_option("display.width", 250)
print(df[["test", "seg", "cfg", "trades", "avg", "total", "total_wo_best", "avg_wo_best", "best_share", "worst_day", "t_vs_parent", "dR_vs_parent"]].round(3).to_string())

# descriptive: half-hour, AM/PM, day type, SPY10 start
def lab(x, em):
    hh = (em // 30) * 30
    return x.assign(hh=[f"{h // 60:02d}:{h % 60:02d}" for h in hh], half=np.where(em < 720, "AM 09:50-11:59", "PM 12:00-15:00"))
D = []
for test in ("replay", "2y"):
    b = bk[(test, "none")]          # cap, no latch: every signal the book can hold
    b = lab(b, b.em.values).assign(dtype=b.date.map(SD.dtype_oc), start=b.date.map(SD.start10))
    if test == "2y": b["split"] = b.date.map(L.split)
    for by in ("hh", "half", "dtype", "start"):
        segs = [("ALL", b)] + ([(sp, b[b.split == sp]) for sp in ("TRAIN", "VALID", "FWD")] if test == "2y" else [])
        for seg, x in segs:
            for k, g in x.groupby(by):
                w = g.r[g.r > 0]; l = g.r[g.r <= 0]
                D.append(dict(test=test, seg=seg, by=by, bucket=k, trades=len(g), avg=g.r.mean(), total=g.r.sum(), win=(g.r > 0).mean(),
                              wl=w.mean() / -l.mean() if len(l) else np.nan))
lv = T[T.src == "live"]; lv = lab(lv, lv.em.values).assign(dtype=lv.date.map(SD.dtype_oc), start=lv.date.map(SD.start10))
for acct_sel in (["Primary"], ["Primary", "On Deck"]):
    x0 = lv[lv.acct.isin(acct_sel)]
    for by in ("hh", "half", "dtype", "start"):
        for k, g in x0.groupby(by):
            w = g.rc[g.rc > 0]; l = g.rc[g.rc <= 0]
            D.append(dict(test="live " + "+".join(acct_sel), seg="ALL", by=by, bucket=k, trades=len(g), avg=g.rc.mean(), total=g.rc.sum(),
                          win=(g.rc > 0).mean(), wl=w.mean() / -l.mean() if len(l) else np.nan, days=g.date.nunique()))
D = pd.DataFrame(D); D.to_csv("B_time_daytype.csv", index=False, float_format="%.4f")
print(D[(D.seg == "ALL") | (D.by == "half") | (D.by == "start")].round(3).to_string())
