"""l3_1022 Part 1: live PAPER record of L3-gap-slope-fromopen-FD through 2026-10-22 (journals run 1 of every account,
read from origin/mcf-data* via git show; regime1022 live.journals / live.record reused unchanged), by account, day,
regime (regime1022 labels; 10-22 from a read-only SIP SPY fetch), lots per symbol-day and entry hour.
Writes live_trades.csv, live_summary.json, live_out.md. Educational only - not financial advice."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import l3c
from live import journals, record   # regime1022/scripts/live.py
from regime import day_table

OUT = l3c.HERE


def main():
    T = journals()
    t = T[T["strategy"] == l3c.SETUP].copy()
    dt = day_table()
    t["regime"] = t["date"].map(dt["regime"]).fillna("unknown")
    et = pd.to_datetime(t["entry_time"], utc=True).dt.tz_convert("America/New_York")
    t["hhmm"] = et.dt.hour * 100 + et.dt.minute
    t["hour"] = pd.cut(t["hhmm"], [0, 1030, 1130, 1300, 1430, 2400],
                       labels=["09:50-10:30", "10:30-11:30", "11:30-13:00", "13:00-14:30", "14:30-15:00"], right=False)
    t = t.sort_values(["acct", "date", "entry_time"])
    t["lot_no"] = t.groupby(["acct", "date", "symbol"]).cumcount() + 1
    t.to_csv(OUT / "live_trades.csv", index=False)
    md, js = ["# Live paper record - L3-gap-slope-fromopen-FD (through 2026-10-22)\n"], {}
    for name, sub in (("primary", t[t["acct"] == "p"]), ("testing1", t[t["acct"] == "t1"]), ("all", t)):
        r = record(sub)
        js[name] = r
        md.append(f"\n## {name}: {r}\n")
        by = sub.groupby(["date", "acct"]).agg(n=("radj", "size"), R=("radj", "sum"), avgR=("radj", "mean"),
                                               pnl=("pnl_adj", "sum"), regime=("regime", "first"),
                                               syms=("symbol", "nunique"), maxlots=("lot_no", "max"))
        md.append(by.round(3).to_string() + "\n")
        js[name + "_by_regime"] = {k: record(g) for k, g in sub.groupby("regime")}
        md.append("\nby regime:\n" + pd.DataFrame(js[name + "_by_regime"]).T[
            ["trades", "sessions", "win_pct", "breakeven_win_pct", "avg_r", "sum_r", "pnl_adj"]].to_string() + "\n")
        js[name + "_by_lot"] = {str(k): record(g) for k, g in sub.groupby(np.minimum(sub["lot_no"], 3))}
        md.append("\nby lot number (1, 2, 3+ within symbol-day):\n" + pd.DataFrame(js[name + "_by_lot"]).T[
            ["trades", "win_pct", "avg_r", "sum_r", "pnl_adj"]].to_string() + "\n")
        js[name + "_by_hour"] = {str(k): record(g) for k, g in sub.groupby("hour", observed=True)}
        md.append("\nby entry time:\n" + pd.DataFrame(js[name + "_by_hour"]).T[
            ["trades", "win_pct", "avg_r", "sum_r", "pnl_adj"]].to_string() + "\n")
        stk = sub.groupby(["date", "symbol"]).agg(lots=("radj", "size"), R=("radj", "sum"), pnl=("pnl_adj", "sum"))
        top = stk[stk["lots"] >= 2].sort_values("R")
        md.append(f"\nsymbol-days with >= 2 lots: {len(top)} of {len(stk)}, R {top['R'].sum():+.2f}, "
                  f"${top['pnl'].sum():+.2f}\n" + top.round(2).to_string() + "\n")
        js[name + "_stacked"] = {"symbol_days": int(len(stk)), "stacked_days": int(len(top)),
                                 "stacked_R": float(top["R"].sum()), "stacked_pnl": float(top["pnl"].sum())}
    lab = dt.loc[[d for d in dt.index if str(d) >= "2026-10-06"], ["o2c", "range", "med20", "regime"]]
    md.append("\n## Session labels (regime1022 rules)\n" + lab.round(2).to_string() + "\n")
    js["labels"] = {str(k): v for k, v in lab["regime"].items()}
    (OUT / "live_summary.json").write_text(json.dumps(js, indent=1, default=str))
    (OUT / "live_out.md").write_text("".join(md))
    print("".join(md))


if __name__ == "__main__":
    main()
