"""etfstop_1123 live replay (PLAN.md items 5-6): ETF-STOP50 and its variants on every live NM-ETF-family lot
(NM-ETF Primary / Live Lab / Testing 2, WB1 Explore 1, WB4 Testing E, ULT-22 Live Lab), run 1, LR8 cost-R, re-walked
on real SIP 1-minute bars (fetch_live_bars.py).
- burst lot: >= k lots of the same account+setup entered in the last w minutes, same 5-minute decision-bar peers
  included (rules_1122 live definition); F5: >= 5 such lots.
- a tightened lot whose minute low reaches entry - f x risk between its entry minute and its journal exit exits at
  min(bar open, level); R = gross - the lot's own journal cost (r - gross r).
- AV50 / AO50: SPY close of the minute before entry below SPY session VWAP / session open.
- Q50G2: once 2 burst lots have stopped (rule or own stop), the burst's open lots flatten at that minute's close.
- Primary: the -2R latch is re-applied on rule R (lots it now blocks are removed; lots the live latch blocked cannot
  be added back).
Usage: python live_replay.py WORKDIR.  Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

W, OUT = Path(sys.argv[1]), Path(__file__).parent
FAM = ["NM-ETF-late-dip-di-long", "NM-ETF-late-dip-di-long-WB1", "NM-ETF-late-dip-di-long-WB4", "ULT-22-wb4-wide-etf-long"]
t = pd.read_parquet(W / "live.parquet")
t = t[t.strategy.isin(FAM)].copy()
t["et"] = pd.to_datetime(t.entry_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
t["xt"] = pd.to_datetime(t.exit_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
t["risk"] = (t.entry - t.stop).abs()
t["gross"] = t.side * (t.exit - t.entry) / t.risk
t["cost"] = t.gross - t.r
t["bar"] = t.et.dt.floor("5min")
assert (t.side == 1).all()
B = pd.read_parquet(W / "livebars" / "livebars.parquet")
B["ts"] = pd.to_datetime(B.ts, utc=True).dt.tz_convert("America/New_York")
BAR = {k: g.sort_values("ts").reset_index(drop=True) for k, g in B.groupby(["symbol", "date"])}
SPY = {}
for d, g in B[B.symbol == "SPY"].groupby("date"):
    g = g.sort_values("ts")
    tp = (g.high + g.low + g.close) / 3
    vw = (tp * g.volume).cumsum() / g.volume.cumsum()
    SPY[d] = pd.DataFrame(dict(ts=g.ts.to_numpy(), c=g.close.to_numpy(), vw=vw.to_numpy(), o=g.open.iloc[0]))


def spy_state(d, et):
    s = SPY[d]
    s = s[s.ts < et.floor("min")]
    if not len(s):
        return None, None
    x = s.iloc[-1]
    return bool(x.c < x.vw), bool(x.c < x.o)


def path(x):
    b = BAR[(x.symbol, x.date)]
    return b[(b.ts >= x.et.floor("min")) & (b.ts < x.xt)]


def run(g, cfg):
    g = g.sort_values("et").reset_index(drop=True)
    n = len(g)
    k, w, f = cfg.get("k", 4), cfg.get("win", 10), cfg.get("tight")
    cnt = np.array([((g.et > x.et - pd.Timedelta(minutes=w)) & (g.bar <= x.bar)).sum() for x in g.itertuples()])
    isb = cnt >= k
    r = g.r.to_numpy().copy()
    xt = g.xt.copy()
    stopped = (g.exit_reason == "stop").to_numpy().copy()
    tight = np.zeros(n, bool)
    if f:
        for i, x in enumerate(g.itertuples()):
            if not isb[i]:
                continue
            ok = True
            bvw, bop = spy_state(x.date, x.et)
            if cfg.get("against") == "vwap":
                ok = bvw is True
            if cfg.get("against") == "open":
                ok = bop is True
            if cfg.get("from5"):
                ok = ok and cnt[i] >= 5
            if not ok:
                continue
            tight[i] = True
            lvl = x.entry - f * x.risk
            p = path(x)
            hit = p[p.low <= lvl]
            if len(hit):
                h = hit.iloc[0]
                px = min(h.open, lvl)
                r[i] = (px - x.entry) / x.risk - x.cost
                xt[i] = h.ts + pd.Timedelta(seconds=59)
                stopped[i] = True
    if cfg.get("gstop") and isb.any():
        start = g.et[isb].min()
        memb = np.array([abs((g.et[i] - start).total_seconds()) <= w * 60 for i in range(n)])
        st_times = sorted(xt[i] for i in range(n) if memb[i] and stopped[i])
        if len(st_times) >= cfg["gstop"]:
            tt = st_times[cfg["gstop"] - 1]
            for i in range(n):
                if memb[i] and xt[i] > tt and g.et[i] <= tt:
                    x = g.iloc[i]
                    b = BAR[(x.symbol, x.date)]
                    bb = b[b.ts <= tt.floor("min")]
                    if len(bb):
                        r[i] = (bb.close.iloc[-1] - x.entry) / x.risk - x.cost
                        xt[i] = tt
    take = np.ones(n, bool)
    if g.account.iloc[0] == "primary":
        for i in range(n):
            real = sum(r[j] for j in range(i) if take[j] and xt[j] <= g.et[i])
            if real <= -2 + 1e-12:
                take[i] = False
    return float(r[take].sum()), int(take.sum()), int(isb.sum()), int(tight.sum()), \
        int(((r < g.r.to_numpy() - 1e-9) & (g.r.to_numpy() > 0) & take).sum())


CFGS = {"base": {}, "Q50": dict(tight=0.5), "Q40": dict(tight=0.4), "Q60": dict(tight=0.6),
        "AV50": dict(tight=0.5, against="vwap"), "AO50": dict(tight=0.5, against="open"), "F5_50": dict(tight=0.5, from5=True),
        "Q50G2": dict(tight=0.5, gstop=2), "K5W10": dict(tight=0.5, k=5), "K6W10": dict(tight=0.5, k=6)}
rows = []
for (a, s, d), g in t.groupby(["account", "strategy", "date"]):
    for c, cfg in CFGS.items():
        R, n, nb, nt, wcut = run(g, cfg)
        rows.append(dict(account=a, setup=s, date=d, cfg=c, R=R, lots=n, burst_lots=nb, tight_lots=nt, winners_cut=wcut))
X = pd.DataFrame(rows)
X.round(3).to_csv(OUT / "S_live_replay.csv", index=False)
P = X.pivot_table(index=["account", "setup", "date"], columns="cfg", values="R")[list(CFGS)]
D = P.sub(P["base"], axis=0)
pd.set_option("display.width", 250)
out = []
out.append("per account/setup/day (R); burst lots per day from Q50 rows")
nb = X[X.cfg == "Q50"].set_index(["account", "setup", "date"])[["lots", "burst_lots", "tight_lots", "winners_cut"]]
out.append(P.round(2).join(nb).to_string())
by = P.groupby(level=["account", "setup"]).sum()
out.append("\ntotals per account/setup (R)")
out.append(by.round(2).to_string())
out.append("\nper day, NM-ETF family all accounts (R)")
out.append(P.groupby(level="date").sum().round(2).to_string())
summ = pd.DataFrame({"R_total": P.sum(), "dR_total": D.sum(), "setup_days_better": (D > 1e-9).sum(), "setup_days_worse": (D < -1e-9).sum(),
                     "worst_setup_day": P.min(), "dR_1120": D[D.index.get_level_values("date") == "2026-11-20"].sum(),
                     "dR_other_days": D[D.index.get_level_values("date") != "2026-11-20"].sum(),
                     "primary_dR": D[D.index.get_level_values("account") == "primary"].sum(),
                     "primary_dR_ex1120": D[(D.index.get_level_values("account") == "primary") & (D.index.get_level_values("date") != "2026-11-20")].sum()})
summ.round(2).to_csv(OUT / "S_live_summary.csv")
out.append("\nsummary")
out.append(summ.round(2).to_string())
txt = "\n".join(out)
print(txt)
(OUT / "S_live_out.txt").write_text(txt + "\n")
