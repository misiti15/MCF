"""OFF what-ifs for the candidate condition switches, bench (FIT/CHECK/T2) + live. Educational only - not financial advice."""
import numpy as np, pandas as pd
D = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/crd/"
b = pd.read_parquet(D + "bench/bench_tagged.parquet")
l = pd.read_parquet(D + "live_feat.parquet").rename(columns={"strategy": "setup"}); l["split"] = "LIVE"
e = l.expo.values; th = lambda v, k: np.where(v > k, 1, np.where(v < -k, -1, 0))
l["spyo_al"] = e * th(l.spy_fo, .001); l["idx3_al"] = e * l.idx3; l["gap_al"] = e * l.gapst; l["cmp_al"] = e * l.cmp
# live cp30: SPY >= 0.30% at the latest 30-min checkpoint from 10:30 (from the 1-min bars)
bars = pd.read_parquet(D + "idx_bars.parquet"); bars = bars[bars.symbol == "SPY"]; bars["date"] = bars.ts.dt.date.astype(str); bars["m"] = bars.ts.dt.hour * 60 + bars.ts.dt.minute
cpv = {}
for dd, g in bars.groupby("date"):
    o = g.open.iloc[0]; cpv[dd] = {T: (g.close.values[g.m.values <= T - 1][-1] / o - 1) for T in range(630, 931, 30)}
st = []
for dd, em in zip(l.date, l.em):
    ok = [T for T in range(630, 931, 30) if T <= em]; f = cpv.get(dd, {}).get(ok[-1], 0) if ok else 0
    st.append(1 if f >= .003 else (-1 if f <= -.003 else 0))
l["cp30_al"] = e * np.array(st)
RULES = [("RW3-gapdn-rsi5pop-flowsell-short-FD", "spyo_al", -1), ("RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "spyo_al", -1),
         ("L3-gap-slope-fromopen-FD", "spyo_al", 1), ("L3-gap-slope-fromopen-FD", "idx3_al", 1),
         ("NM-ETF-late-dip-di-long", "cp30_al", -1), ("NM-ETF-late-dip-di-long", "spyo_al", -1),
         ("MF3-open-flowsell-rsi5hi-FD", "gap_al", -1), ("CWT09-gapdn-bounce-g5-lowerhalf-short", "spyo_al", -1),
         ("RW7-gapdn-bounce-early-short-FD", "spyo_al", -1), ("CWT14-failbrk-pdh-p10-short", "idx3_al", -1)]
out = []
for s, f, v in RULES:
    for sp in ["FIT", "CHECK", "T2", "LIVE"]:
        g = (b if sp != "LIVE" else l); g = g[(g.setup == s) & (g.split == sp)]
        if not len(g): continue
        sw = g[g[f] == v]; kp = g[g[f] != v]
        days = sorted(g.date.unique()); d = (-sw.groupby("date").r.sum()).reindex(days).fillna(0)
        ex = (sw.r - g.r.mean()).groupby(sw.date).mean() if len(sw) else pd.Series(dtype=float)
        out.append(dict(rule=f"{s[:24]} off {f}={v:+d}", split=sp, n=len(g), sw=len(sw), sw_pct=round(len(sw) / len(g) * 100),
                        sw_avg=round(sw.r.mean(), 3), kept_avg=round(kp.r.mean(), 3), base_avg=round(g.r.mean(), 3),
                        dR=round(d.sum(), 1), dR_day_t=round(d.mean() / d.std(ddof=1) * np.sqrt(len(d)), 2),
                        excess_t=round(-ex.mean() / ex.std(ddof=1) * np.sqrt(len(ex)), 2) if len(ex) > 2 else np.nan,
                        best_share=round(d.max() / d.sum(), 2) if d.sum() > 0 else np.nan))
O = pd.DataFrame(out); O.to_csv(D + "bench_off.csv", index=False)
pd.set_option("display.width", 250); print(O.to_string(index=False))
