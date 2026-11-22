"""Part D live replay (E4 approximation): the 19 pre-registered rules on the live NM-ETF-family journals (NM-ETF in
Primary / Live Lab / Testing 2, WB1 Explore 1, WB4 Testing E, ULT-22 Live Lab), run 1, LR8 cost-R.
No 1-minute bars after 2026-11-04 in this checkout: a lot's open mark is interpolated linearly in time between its
journal entry (entry price) and exit (exit price); a rule exit at time t books the interpolated mark less the lot's own
journal cost (r - gross r). Every 11-20 lot finally stopped, so 'no saving' (the journal R) is the lower bound.
Staggering (P1) keeps journal prices (unknown otherwise). Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

W, OUT = Path(sys.argv[1]), Path(__file__).parent
t = pd.read_parquet(W / "live.parquet")
t = t[t.strategy.isin(["NM-ETF-late-dip-di-long", "NM-ETF-late-dip-di-long-WB1", "NM-ETF-late-dip-di-long-WB4",
                       "ULT-22-wb4-wide-etf-long"])].copy()
t["et"] = pd.to_datetime(t.entry_time, utc=True, format="mixed")
t["xt"] = pd.to_datetime(t.exit_time, utc=True, format="mixed")
t["risk"] = (t.entry - t.stop).abs()
t["gross"] = t.side * (t.exit - t.entry) / t.risk
t["cost"] = t.gross - t.r
t["bar"] = t.et.dt.floor("5min")       # decision bar ~ the 5-minute bar of the order


def mark(x, when):
    f = np.clip((when - x.et).total_seconds() / max((x.xt - x.et).total_seconds(), 1), 0, 1)
    return x.side * ((x.entry + f * (x.exit - x.entry)) - x.entry) / x.risk


def run(g, cfg):
    g = g.sort_values("et").reset_index(drop=True)
    n = len(g)
    size = np.ones(n)
    take = np.ones(n, bool)
    r = g.r.to_numpy().copy()
    # burst lots: >= 4 lots in the last 10 minutes (same-bar peers counted)
    isb = np.array([((g.et > x.et - pd.Timedelta(minutes=10)) & (g.bar <= x.bar)).sum() + 0 >= 4 for x in g.itertuples()])
    # budget / latch (realized R before entry, closed lots only) -------------------------------
    for i, x in g.iterrows():
        prev = [j for j in range(i) if take[j]]
        real = sum(r[j] * size[j] for j in prev if g.xt[j] <= x.et)
        opn = sum(1 for j in prev if g.xt[j] > x.et)
        if x.account == "primary" and real <= -2:
            take[i] = False
        if cfg.get("budget") is not None and real - opn - 1 < -cfg["budget"]:
            take[i] = False
    if cfg.get("split"):
        for b, ix in g.groupby("bar").groups.items():
            if len(ix) >= 4:
                size[list(ix)] = 4 / len(ix)
    if cfg.get("halflate"):
        cnt = 0
        for i in range(n):
            cnt = cnt + 1 if isb[i] or cnt else 0
            if isb[i] and i >= 3:
                size[i] = 0.5
    if cfg.get("tight"):
        for i in range(n):
            if isb[i] and take[i]:
                if g.gross[i] <= -0.5:
                    r[i] = -0.5 - g.cost[i]
    if cfg.get("btime"):
        for i in range(n):
            if isb[i] and g.xt[i] > g.et[i] + pd.Timedelta(minutes=cfg["btime"]):
                r[i] = mark(g.iloc[i], g.et[i] + pd.Timedelta(minutes=cfg["btime"])) - g.cost[i]
    # group rules on a 30-second grid ----------------------------------------------------------
    if any(cfg.get(k) for k in ("gstop", "bbudget", "btstop", "sentinel")) and n:
        start = g.et[isb].min() if isb.any() else None
        memb = np.array([take[i] and start is not None and abs((g.et[i] - start).total_seconds()) <= 600 for i in range(n)])
        grid = pd.date_range(g.et.min(), g.xt.max(), freq="30s")
        closed = np.zeros(n, bool)
        for tt in grid:
            live = [i for i in range(n) if take[i] and g.et[i] <= tt and not closed[i] and g.xt[i] > tt]
            done = [i for i in range(n) if take[i] and (g.xt[i] <= tt or closed[i])]
            trig = []
            if start is not None and tt >= start:
                bl = [i for i in live if memb[i]]
                bR = sum(r[i] * size[i] for i in done if memb[i]) + sum(mark(g.iloc[i], tt) * size[i] for i in bl)
                stops = sum(1 for i in done if memb[i] and not closed[i] and g.exit_reason[i] == "stop")
                if cfg.get("gstop") and stops >= cfg["gstop"]:
                    trig += bl
                if cfg.get("bbudget") and bR <= -cfg["bbudget"]:
                    trig += bl
                if cfg.get("btstop") and abs((tt - (start + pd.Timedelta(minutes=cfg["btstop"]))).total_seconds()) < 15 and bR < 0:
                    trig += bl
            if cfg.get("sentinel"):
                k, X = cfg["sentinel"]
                if len(live) >= k and sum(mark(g.iloc[i], tt) * size[i] for i in live) <= -X:
                    trig += live
            for i in set(trig):
                r[i] = mark(g.iloc[i], tt) - g.cost[i]
                closed[i] = True
    return float((r * size)[take].sum()), int(take.sum())


CFGS = {"base": {}, "G2": dict(gstop=2), "G3": dict(gstop=3), "B2": dict(bbudget=2), "B3": dict(bbudget=3),
        "B4": dict(bbudget=4), "T15": dict(btstop=15), "T30": dict(btstop=30), "S4": dict(split=True),
        "SH": dict(halflate=True), "W3x1.5": dict(sentinel=(3, 1.5)), "W3x2.5": dict(sentinel=(3, 2.5)),
        "W4x1.5": dict(sentinel=(4, 1.5)), "W4x2.5": dict(sentinel=(4, 2.5)), "O4": dict(budget=4), "O6": dict(budget=6),
        "P1": {}, "P1W": dict(sentinel=(3, 1.5)), "Q50": dict(tight=True), "Q20": dict(btime=20)}
rows = []
for (a, s, d), g in t.groupby(["account", "strategy", "date"]):
    for c, cfg in CFGS.items():
        R, n = run(g, cfg)
        rows.append(dict(account=a, setup=s, date=d, cfg=c, R=R, lots=n))
X = pd.DataFrame(rows)
P = X.pivot_table(index=["account", "setup", "date"], columns="cfg", values="R")
D = P.sub(P["base"], axis=0)
X.round(3).to_csv(OUT / "D_live_replay.csv", index=False)
pd.set_option("display.width", 260)
print(P[P["base"] < -2].round(2).T.to_string())
summ = pd.DataFrame({"R_total": P.sum(), "dR_total": D.sum(), "days_better": (D > 1e-9).sum(), "days_worse": (D < -1e-9).sum(),
                     "worst_day": P.min(), "dR_1120": D[D.index.get_level_values("date") == "2026-11-20"].sum(),
                     "dR_other_days": D[D.index.get_level_values("date") != "2026-11-20"].sum()})
summ.round(2).to_csv(OUT / "D_live_summary.csv")
print(summ.round(2).to_string())
