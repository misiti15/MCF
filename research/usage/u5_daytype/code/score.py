"""U5 scoring: pre-registered pass rule (PLAN.md). Educational only - not financial advice."""
import glob, json, math, sys
import numpy as np, pandas as pd

S = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/up_u5"
OUT = sys.argv[1]
TBAR = max(1.5, math.sqrt(2 * math.log(12)))
NAMES = {"S1": "DT-QD-FBD-long", "S2": "DT-QD-FBO-short", "S3": "DT-QD-VWAPSTRETCH-long", "S4": "DT-UP-VWAPPB-long"}


def load(tag):
    info = pd.DataFrame([json.load(open(f)) for f in sorted(glob.glob(f"{S}/out_{tag}/*.json"))]).set_index("date")
    T = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{S}/out_{tag}/*_t.csv")) if open(f).read(10).strip()], ignore_index=True)
    R = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{S}/out_{tag}/*_r.csv"))], ignore_index=True)
    return info, T, R


def cap(t, n=15):
    keep = []
    for (_, _, _), g in t.sort_values(["date", "setup", "var", "em", "symbol"]).groupby(["date", "setup", "var"], sort=False):
        open_ = []
        for i, em, xm in zip(g.index, g.em.values, g.xm.values):
            open_ = [x for x in open_ if x > em]
            if len(open_) < n:
                keep.append(i); open_.append(xm)
    return t.loc[keep]


def stats(t, days):
    if not len(t):
        return dict(trades=0)
    d = t.groupby("date").r.sum().reindex(days, fill_value=0.0)
    tot = t.r.sum(); b = d.idxmax(); nb = (t.date == b).sum()
    dev = (t.r - t.r.mean()).groupby(t.date).sum()
    tcl = t.r.sum() / math.sqrt((dev ** 2).sum()) if (dev ** 2).sum() > 0 else 0.0
    return dict(trades=len(t), days_traded=int(t.date.nunique()), win=round((t.r > 0).mean(), 3), avg=round(t.r.mean(), 4),
                total=round(tot, 1), t_day=round(tcl, 2), avg_wo_best=round((tot - d[b]) / (len(t) - nb), 4) if len(t) > nb else np.nan,
                best_day=round(d.max(), 1), best_share=round(d.max() / tot, 2) if tot > 0 else np.nan, worst_day=round(d.min(), 1),
                green_days=int((d > 0).sum()), stop_pct=round((t.kind == 0).mean(), 2), tgt_pct=round((t.kind == 1).mean(), 2),
                med_r_atr=round(t.r_atr.median(), 3))


fi, fT, fR = load("fit"); ci, cT, cR = load("chk")
q40 = float(fi.or30s.quantile(0.40))
res = []
for tag, info, T, Rd in (("fit", fi, fT, fR), ("check", ci, cT, cR)):
    qdays = set(info.index[info.or30s <= q40])
    days = list(info.index)
    T = T[~(T.setup.isin(["S1", "S2", "S3"]) & (T["var"] == "cue") & ~T.date.isin(qdays))]
    Rd = Rd[~(Rd.setup.isin(["S1", "S2", "S3"]) & ~Rd.date.isin(qdays))]
    T = cap(T)
    T.to_csv(f"{S}/trades_{tag}.csv", index=False)
    for s in NAMES:
        for var in ("cue", "nocue"):
            x = T[(T.setup == s) & (T["var"] == var)]
            res.append(dict(sample=tag, setup=s, name=NAMES[s], version="day-type cue" if var == "cue" else "no cue (all days)",
                            **stats(x, days)))
        rr = Rd[Rd.setup == s]
        res.append(dict(sample=tag, setup=s, name=NAMES[s], version="random entries",
                        **(stats(rr.assign(kind=-1, r_atr=np.nan), days) if len(rr) else dict(trades=0))))
    print(tag, "sessions", len(days), "quiet-cue days (OR30 <= q40)", len(qdays), "up-cue days", int(info.up_any.sum()))
res = pd.DataFrame(res)
res.to_csv(f"{OUT}/u5_results.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print("q40 =", round(q40, 4), " TBAR =", round(TBAR, 2))
print(res.drop(columns=["name"]).to_string(index=False))

# verdicts
v = []
for s in NAMES:
    f = res[(res["sample"] == "fit") & (res.setup == s) & (res.version == "day-type cue")].iloc[0]
    c = res[(res["sample"] == "check") & (res.setup == s) & (res.version == "day-type cue")].iloc[0]
    rc = res[(res["sample"] == "check") & (res.setup == s) & (res.version == "random entries")].iloc[0]
    fitok = f.trades >= 100 and f.avg > 0 and f.t_day >= TBAR
    chkok = (c.trades >= 25 and c.avg > 0 and c.avg_wo_best > 0 and (c.best_share < 0.5) and c.avg > rc.avg)
    v.append(dict(setup=s, name=NAMES[s], fit_ok=fitok, check_ok=chkok,
                  verdict="PASS" if fitok and chkok else ("WATCH" if fitok else "FAIL")))
v = pd.DataFrame(v); v.to_csv(f"{OUT}/u5_verdicts.csv", index=False); print(v.to_string(index=False))
