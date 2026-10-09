"""Summaries for AUTOPSY.md from trades.csv (diagnosis only). Educational only - not financial advice."""
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
A = pd.read_csv(HERE / "trades.csv")
A = A[~A.artifact]
pd.set_option("display.width", 250)
A["win"] = A.r_live > 0
A["et"] = A.entry_time.str[:5]
A["early"] = A.et < "10:31"
for a, g in A.groupby("account"):
    print("=====", a, len(g), "trades, P/L", round(g.pnl.sum(), 2), "adj", round(g.pnl_adj.sum(), 2), "WR", round(g.win.mean(), 3),
          "avgR", round(g.r_live.mean(), 3))
    print(g.groupby("setup").agg(n=("pnl", "size"), wins=("win", "sum"), avgR=("r_live", "mean"), pnl=("pnl", "sum"),
                                 first=("et", "min"), last=("et", "max")).round(2).to_string())
    print("entry 09:50-10:30 vs later:")
    print(g.groupby("early").agg(n=("pnl", "size"), wins=("win", "sum"), avgR=("r_live", "mean"), pnl=("pnl", "sum")).round(2))
    print(g.groupby(["early", "setup"]).agg(n=("pnl", "size"), pnl=("pnl", "sum"), avgR=("r_live", "mean")).round(2).to_string())
    wi = ["wi_base_sim", "wi_be0.5", "wi_trail0.5", "wi_tp0.5", "wi_tp1", "wi_hold_1555", "r_hold_nostop_1555",
          "wi_stop_and_reverse", "wi_reentry", "opp_1r1r", "opp_hold_1555"]
    t = g.groupby("setup")[wi].sum()
    t.loc["ALL"] = g[wi].sum()
    t.insert(0, "n", g.groupby("setup").size().reindex(t.index).fillna(len(g)).astype(int))
    print(t.round(2).to_string())
    print("loss types")
    print(pd.crosstab(g.loss_type, g.setup, margins=True).to_string())
    L = g[~g.win]
    print("opp target first on losers", int((L.opp_why == "target").sum()), "/", len(L), "; on winners",
          int((g[g.win].opp_why == "target").sum()), "/", int(g.win.sum()))
    for f in ["flag_spy30_against", "flag_trend_against", "flag_fromopen_against", "flag_flow3_against"]:
        x = g[g[f] == True]  # noqa: E712
        y = g[g[f] == False]  # noqa: E712
        print(f, "WR with", round(x.win.mean(), 2), len(x), "without", round(y.win.mean(), 2), len(y))
    for f in ["ctx_g1_allows", "ctx_g3_allows"]:
        x = g[g[f] == True]  # noqa: E712
        y = g[g[f] == False]  # noqa: E712
        print(f, "allowed: n", len(x), "WR", round(x.win.mean(), 2), "avgR", round(x.r_live.mean(), 3), "pnl", round(x.pnl.sum(), 2),
              "| blocked: n", len(y), "WR", round(y.win.mean(), 2), "avgR", round(y.r_live.mean(), 3), "pnl", round(y.pnl.sum(), 2))
    print("median t->MFE held", g.held_t_mfe_min.median(), "day", g.day_t_mfe_min.median())
    print("by side:", g.groupby("side").agg(n=("pnl", "size"), pnl=("pnl", "sum"), avgR=("r_live", "mean")).round(2).to_dict())
    print("news on losers:")
    print(g[g.news.notna() & ~g.win][["id", "symbol", "setup", "et", "news"]].to_string())
