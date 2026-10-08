"""Loss-type tags for all 60 live trades (multi-tag) + one primary type per trade. Diagnosis only.
usage: python research/oct7/autopsy/classify.py BARS_PARQUET   Educational only - not financial advice."""
import sys
import numpy as np
import pandas as pd

OUT = "research/oct7/autopsy/"
A = pd.read_csv(OUT + "trades_autopsy.csv")
raw = pd.read_parquet(sys.argv[1])
opens = {}
for (s, d), g in raw.reset_index().assign(d=lambda x: x.timestamp.dt.tz_convert("America/New_York").dt.date.astype(str)).groupby(["symbol", "d"]):
    g = g.sort_values("timestamp")
    g = g[g.timestamp.dt.tz_convert("America/New_York").dt.time >= pd.Timestamp("09:30").time()]
    opens[(s, d)] = float(g.open.iloc[0])
A["move_open_to_entry_pct"] = [(e / opens[(s, d)] - 1) * 100 for s, d, e in zip(A.symbol, A.date, A.entry)]
A["chase_pct"] = A.side * A.move_open_to_entry_pct          # >0: entered in the direction the stock had already moved
# news/earnings: earnings-related headlines in the 4-day window (mcf.data.earnings news fallback, checked 10-08)
# plus same-day material company news (HESM: Chevron stake sale + 2027 EBITDA guide-down; BKV: power contract)
NEWS = {("CEG", "2026-10-06"): "earnings-window headline", ("LW", "2026-10-06"): "earnings-window headline",
        ("PENG", "2026-10-07"): "earnings (Q4 print 10-06 after close)", ("NEOG", "2026-10-07"): "earnings (Q1 call 10-06)",
        ("ALAB", "2026-10-07"): "earnings-window headline 10-06",
        ("HESM", "2026-10-07"): "material news (Chevron stake sale, guide-down)", ("BKV", "2026-10-07"): "material news (power-equipment contract)"}
A["news"] = [NEWS.get((s, d), "") for s, d in zip(A.symbol, A.date)]
loss = A.r_live <= 0
tags = pd.DataFrame(index=A.index)
tags["never_worked"] = loss & (A.held_mfe_r < 0.15)
tags["gave_back_gains"] = loss & (A.held_mfe_r >= 0.5)
tags["stopped_then_reversed"] = loss & A.exit_reason.eq("stop") & (A.day_mfe_r >= 1.0) & (A.held_mfe_r < 1.0)
tags["late_hold"] = loss & A.exit_reason.eq("flatten")
tags["wrong_side_after_big_swing"] = loss & (A.chase_pct.abs() >= 3) & A.opp_would_win
tags["news_earnings"] = loss & A.news.ne("")
order = ["news_earnings", "stopped_then_reversed", "wrong_side_after_big_swing", "gave_back_gains", "late_hold", "never_worked"]
A["primary"] = np.where(~loss, "win", "small MFE then failed (0.15-0.5R)")
for c in reversed(order):
    A.loc[tags[c], "primary"] = c
A["tags"] = tags.apply(lambda r: ",".join(c for c in tags.columns if r[c]), axis=1)
A.to_csv(OUT + "trades_autopsy.csv", index=False)
print(pd.crosstab(A.primary, A.setup, margins=True).to_string())
print(tags.groupby(A.setup).sum().T.to_string())
print(A[loss][["date", "symbol", "setup", "r_live", "held_mfe_r", "day_mfe_r", "chase_pct", "opp_would_win", "news", "primary", "tags"]].round(2).to_string())
# money lost to the flatten bug (exits at 16:04-16:06 instead of 15:55)
f = A[A.exit_reason.eq("flatten")]
print("\nflatten-bug trades:", len(f), "live pnl", round(f.pnl.sum(), 2), "pnl at 15:55 close", round(f.pnl_at_1555.sum(), 2))
print(f[["date", "symbol", "setup", "exit_time", "r_live", "r_at_1555", "pnl", "pnl_at_1555"]].round(2).to_string())
print("\nby setup, live:", A.groupby("setup").agg(n=("pnl", "size"), pnl=("pnl", "sum"), r=("r_live", "mean"), win=("r_live", lambda x: (x > 0).mean())).round(2).to_string())
print("opposite 1R/1R would have hit target first:", A.opp_would_win.sum(), "of", len(A), "; among losers:", A[loss].opp_would_win.sum(), "of", loss.sum())
