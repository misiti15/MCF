import sys; import pandas as pd, numpy as np
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 100)
S = sys.argv[1]
T = pd.read_csv(f"{S}/trades_all.csv", parse_dates=["entry_time", "exit_time", "signal_time"])
T["entry_time"] = pd.to_datetime(T.entry_time, utc=True); T["exit_time"] = pd.to_datetime(T.exit_time, utc=True)
T["dollar_R"] = T.risk * T.shares
cols = ["acct", "symbol", "strategy", "side", "entry_hhmm", "entry", "stop", "target", "exit", "exit_reason", "r_multiple", "shares", "pnl", "dollar_R", "hold_min", "mfe", "mae"]
for a in ("p", "t1", "t2"):
    d = T[T.acct == a]
    print("=====", a)
    print("stop wrong side:", d.stop_wrong_side.sum(), " target wrong side:", d.tgt_wrong_side.sum(), " shares<=0:", (d.shares <= 0).sum())
    print("hold<0.5min:", (d.hold_min < 0.5).sum(), " hold<2min:", (d.hold_min < 2).sum())
    print("pnl sign != r sign:", ((np.sign(d.pnl) != np.sign(d.r_multiple)) & (d.pnl.abs() > 0.05)).sum())
    print("target exit with r<0:", ((d.exit_reason == "target") & (d.r_multiple < 0)).sum(), " stop exit with r>0:", ((d.exit_reason == "stop") & (d.r_multiple > 0)).sum())
    print("stop worse than -1.25R:"); print(d[d.r_multiple < -1.25][cols].round(3).to_string())
    print("exit et max:", d.exit_time.dt.tz_convert("America/New_York").max(), " entry before 09:50:", (d.entry_hhmm < "09:50").sum())
    print("dollar_R:", d.dollar_R.describe().round(1).to_dict())
    print("structural trades:"); print(d[d.target.isna()][cols].round(3).to_string())
    print("top 1R outliers:"); print(d.nlargest(5, "dollar_R")[cols].round(3).to_string())
    # concurrent same-symbol
    dup = []
    for s, g in d.groupby("symbol"):
        g = g.sort_values("entry_time")
        for i in range(len(g)):
            for j in range(i + 1, len(g)):
                if g.entry_time.iloc[j] < g.exit_time.iloc[i]:
                    dup.append((s, g.strategy.iloc[i], g.strategy.iloc[j], str(g.entry_time.iloc[j])))
    print("overlapping same-symbol positions:", len(dup), dup[:5])
    rep = d.groupby("symbol").size()
    print("symbols traded >1 time:", (rep > 1).sum(), " max per symbol:", rep.max(), rep.nlargest(5).to_dict())
    # sequential same symbol re-entries within 5 min after stop
    print("immediate re-entry after exit (<5min) same symbol:")
    rr = []
    for s, g in d.groupby("symbol"):
        g = g.sort_values("entry_time")
        for i in range(1, len(g)):
            gap = (g.entry_time.iloc[i] - g.exit_time.iloc[i - 1]).total_seconds() / 60
            if 0 <= gap < 5: rr.append((s, g.strategy.iloc[i - 1], g.exit_reason.iloc[i - 1], g.strategy.iloc[i], round(gap, 1), round(g.pnl.iloc[i], 2)))
    print(len(rr), rr[:10])
