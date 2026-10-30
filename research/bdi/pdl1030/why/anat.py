"""pdl1030/why: descriptive slices (NOT scored configurations) over tr_*.parquet / sd_*.parquet (TRAIN+VALID only).
Educational only - not financial advice."""
import glob, numpy as np, pandas as pd
W = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pdl1030/why"
T = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(W + "/tr_*.parquet"))], ignore_index=True)
SD = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob(W + "/sd_*.parquet"))], ignore_index=True)
assert T.date.max() <= "2026-09-15" and not ((T.date >= "2024-11-01") & (T.date <= "2025-02-28")).any()
assert not T.date.str[:7].isin(["2026-04", "2026-05", "2026-06"]).any()
T["split"] = np.where(T.date <= "2025-12-31", "TRAIN", "VALID")
NS = SD.date.nunique()
out = []
def say(s): out.append(s)
def tday(g):
    d = g.groupby("date").r.sum(); n = len(g)
    # day-clustered t of mean R
    k = len(d)
    if k < 3: return np.nan
    m = g.r.mean(); e = (d - g.groupby("date").size() * m)
    se = np.sqrt((e ** 2).sum() * k / (k - 1)) / n
    return m / se
def tab(g, by, name):
    rows = []
    for k, x in g.groupby(by, observed=True):
        tr, va = x[x.split == "TRAIN"], x[x.split == "VALID"]
        rows.append(dict(bucket=k, n=len(x), per_sess=len(x) / NS, share=len(x) / len(g), avgR=x.r.mean(), t=tday(x),
                         sumR=x.r.sum(), train=tr.r.mean(), valid=va.r.mean(), win=(x.r > 0).mean(), stop=(x.code == 2).mean()))
    say(f"\n### {name} [descriptive slice, not a scored config]\n" + pd.DataFrame(rows).round(3).to_string(index=False))
# ---------- parity
say("## Parity vs swarm15 parents (TRAIN+VALID)")
ref = {"p05": (53326, -0.0677), "p05lv": (35238, -0.0950), "p10": (29836, -0.0880)}
for s, g in T.groupby("setup"):
    r = ref.get(s); say(f"{s}: n {len(g)}, avgR {g.r.mean():+.4f}, TRAIN {g[g.split=='TRAIN'].r.mean():+.4f}, VALID {g[g.split=='VALID'].r.mean():+.4f}"
                        + (f" | swarm15 n {r[0]} avgR {r[1]:+.4f} -> diff {g.r.mean()-r[1]:+.4f}" if r else " | (not in swarm15)")
                        + f"; trades/session {len(g)/NS:.1f}; day t {tday(g):+.2f}")
say(f"sessions {NS}")
# ---------- 1) frequency
SD["fb05w"] = SD.fb05 <= 1500; SD["fb10w"] = SD.fb10 <= 1500
say(f"\n## 1) Frequency (liquid = adv20 >= 95M; {len(SD)} symbol-days, {len(SD)/NS:.0f} names/session)")
say(f"break 0.05 ATR under PDL by 15:00: {SD.fb05w.mean():.1%}; 0.10 ATR: {SD.fb10w.mean():.1%}")
for s in ("p05", "p05lv", "p10", "p10lv"):
    say(f"{s}: symbol-days with a reclaim signal 09:50-15:00 {SD[f'sigwin_{s}'].mean():.1%} (= {SD[f'sigwin_{s}'].sum()/NS:.0f}/session); "
        f"of break days {SD[f'sigwin_{s}'][SD.fb05w if s.startswith('p05') else SD.fb10w].mean():.1%}; mean reclaim cycles/day on signal days {SD.loc[SD[f'sig_{s}'], f'nsig_{s}'].mean():.2f}")
say("open vs PDL (ATR) quantiles: " + repr(SD.open_pdl.quantile([.1, .25, .5, .75, .9]).round(2).to_dict()))
say("prior close vs PDL (ATR) quantiles: " + repr(SD.pc_pdl.quantile([.1, .25, .5, .75, .9]).round(2).to_dict()))
SD["ob"] = pd.cut(SD.open_pdl, [-99, 0, 0.25, 0.5, 1, 2, 99])
SD["gb"] = pd.cut(SD.gap, [-99, -2, -0.5, 0, 0.5, 2, 99])
SD["sg"] = np.sign(SD.spy_gap).map({-1: "SPY gap down", 0: "flat", 1: "SPY gap up"})
SD["sday"] = np.where(SD.spy_day > 0, "SPY up day (EOD, not known)", "SPY down day (EOD, not known)")
for col, nm in (("ob", "open vs PDL (ATR)"), ("gb", "stock gap %"), ("sg", "SPY gap"), ("sday", "SPY session")):
    g = SD.groupby(col, observed=True)
    say(f"\n### frequency by {nm} [descriptive]\n" + pd.DataFrame({"share_days": g.size() / len(SD), "break05": g.fb05w.mean(),
        "signal_p05": g.sigwin_p05.mean(), "signal_p10": g.sigwin_p10.mean()}).round(3).to_string())
fb = SD.loc[SD.fb05w, "fb05"]
say("first 0.05-ATR break time, share of break days: " + repr(pd.cut(fb, [0, 940, 1000, 1030, 1100, 1200, 1300, 1400, 1500]).value_counts(normalize=True, sort=False).round(3).to_dict()))
# ---------- 2) loss anatomy, parent p05 (also p10 headline)
for S in ("p05", "p10"):
    g = T[T.setup == S].copy()
    say(f"\n## 2) Loss anatomy: {S} (n {len(g)}, avgR {g.r.mean():+.4f}, {len(g)/NS:.1f}/session)")
    w, l = g[g.r > 0], g[g.r <= 0]
    say(f"win {len(w)/len(g):.1%}, avg win {w.r.mean():+.3f}, avg loss {l.r.mean():+.3f}; stops {(g.code==2).mean():.1%} avg {g[g.code==2].r.mean():+.3f}; "
        f"targets {(g.code==1).mean():.1%} avg {g[g.code==1].r.mean():+.3f}; flat 15:55 {(g.code==6).mean():.1%} avg {g[g.code==6].r.mean():+.3f}; moved stop {(g.code==3).mean():.1%} avg {g[g.code==3].r.mean():+.3f}")
    say(f"cost: median round-trip cost {g.cost_rt_R.median():.3f}R, mean {g.cost_rt_R.mean():.3f}R; gross avg R (r + cost approx) {(g.r + g.cost_rt_R).mean():+.3f}")
    hm = lambda t: (t // 100) * 60 + t % 100
    g["hold"] = hm(g.xtod) - hm(g.tod)
    st = g[g.code == 2]
    say(f"stops: median {st.hold.median():.0f} min to stop, <=30 min {(st.hold<=30).mean():.1%}; stopped trades' MFE before stop: median {st.mfe.median():.3f}R, >=0.25R {(st.mfe>=0.25).mean():.1%}, >=0.4R {(st.mfe>=0.4).mean():.1%}")
    say(f"targets: median {g[g.code==1].hold.median():.0f} min to target; all trades MFE >=0.5R {(g.mfe>=0.5).mean():.1%}, MAE <=-0.5R {(g.mae<=-0.5).mean():.1%}")
    say(f"day's low (as of entry) broken later in the session: {g.later_low.mean():.1%}; before exit {g.later_low_pre.mean():.1%}")
    g["tb"] = pd.cut(g.tod, [945, 1000, 1030, 1100, 1200, 1300, 1400, 1500])
    tab(g, "tb", "time of day (signal bar close)")
    g["spyfo"] = pd.cut(g.spy_fo, [-99, -0.5, -0.2, 0, 0.2, 0.5, 99]); tab(g, "spyfo", "SPY from open % at entry (known)")
    g["spyvd"] = np.where(g.spy_vd > 0, "SPY above VWAP", "SPY below VWAP"); tab(g, "spyvd", "SPY vs VWAP at entry (known)")
    g["qvd"] = np.where(g.qqq_vd > 0, "QQQ above VWAP", "QQQ below VWAP"); tab(g, "qvd", "QQQ vs VWAP at entry (known)")
    g["brb"] = pd.cut(g.breadth, [0, .3, .4, .5, .6, .7, 1]); tab(g, "brb", "breadth at entry (known)")
    g["sgap"] = pd.cut(g.spy_gap, [-99, -0.5, 0, 0.5, 99]); tab(g, "sgap", "SPY gap % (known at open)")
    g["sday"] = np.where(g.spy_day > 0, "SPY up session", "SPY down session"); tab(g, "sday", "SPY session close vs open (EOD; NOT known at entry)")
    g["spym"] = pd.cut(g.spy_x - g.spy_fo, [-99, -0.3, -0.1, 0, 0.1, 0.3, 99]); tab(g, "spym", "SPY move during the trade % (NOT known at entry)")
    g["db"] = pd.cut(g.depth, [0, .1, .2, .35, .5, .75, 1, 99]); tab(g, "db", "break depth below PDL, ATR (known)")
    g["ob"] = np.where(g.open_pdl < 0, "opened below PDL (gap-under)", "opened above PDL (intraday drift)"); tab(g, "ob", "gap-under vs intraday drift (known)")
    g["gb"] = pd.cut(g.gap, [-99, -3, -1, 0, 1, 3, 99]); tab(g, "gb", "stock gap % (known)")
    g["rb"] = pd.cut(g.reclaim, [-1, .02, .05, .1, .2, .4, 99]); tab(g, "rb", "reclaim bar close above PDL, ATR (known)")
    g["rs"] = pd.cut(g.fo - g.spy_fo, [-99, -2, -1, -0.5, 0, 0.5, 99]); tab(g, "rs", "stock fromOpen minus SPY fromOpen % (known)")
    g["rsc"] = pd.cut(g.chg - (g.spy_gap + g.spy_fo), [-99, -3, -2, -1, 0, 1, 99]); tab(g, "rsc", "stock vs SPY change from prior close % (approx; known)")
    g["vdb"] = pd.cut(g.vd, [-99, -1, -0.5, 0, 0.5, 99]); tab(g, "vdb", "stock vs its VWAP % (known)")
    g["ll"] = np.where(g.later_low, "day low broken again later", "day low holds"); tab(g, "ll", "later break of the day low (NOT known)")
    g["cb"] = pd.cut(g.cost_rt_R, [0, .03, .05, .08, .12, 99]); tab(g, "cb", "round-trip cost / R (known)")
    g["fbb"] = pd.cut(g.fb, [0, 945, 1000, 1030, 1100, 1300, 1500]); tab(g, "fbb", "time of the day's FIRST PDL break (known)")
    g["mfeb"] = pd.cut(g.mfe, [-1, 0.1, 0.25, 0.4, 0.5, 99], right=False); tab(g, "mfeb", "MFE R (NOT known)")
    # SPY-session x spy_fo at entry interaction
    g["ctx"] = g.spyvd + " & " + np.where(g.breadth > 0.5, "breadth>0.5", "breadth<=0.5"); tab(g, "ctx", "SPY VWAP x breadth (known)")
    # day concentration: R by session ranked by SPY session
    d = g.groupby("date").agg(R=("r", "sum"), n=("r", "size"), spy=("spy_day", "first"))
    d["q"] = pd.qcut(d.spy, 5, labels=["SPY q1 worst", "q2", "q3", "q4", "q5 best"])
    say("\n### per-session R by SPY session quintile (EOD, NOT known) [descriptive]\n" + d.groupby("q", observed=True).agg(sessions=("R", "size"), sumR=("R", "sum"), trades=("n", "sum"), avg_trades=("n", "mean")).assign(avgR=lambda z: z.sumR / z.trades).round(3).to_string())
    say(f"corr(session sum R, SPY session %) = {d.R.corr(d.spy):.2f}; corr(trades/session, SPY session) = {d.n.corr(d.spy):.2f}; corr(trades/session, session avg R) = {d.n.corr(d.R/d.n):.2f}")
    d["nq"] = pd.qcut(d.n, 4, labels=["fewest", "q2", "q3", "most"])
    say("signal-count quartile per session: " + d.groupby("nq", observed=True).apply(lambda z: f"{z.n.mean():.0f}/sess avgR {z.R.sum()/z.n.sum():+.3f}").to_dict().__repr__())
txt = "\n".join(out); print(txt); open(W + "/anat_out.txt", "w").write(txt + "\n\nEducational only - not financial advice.\n")
