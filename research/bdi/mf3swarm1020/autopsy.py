"""Step 1b: live autopsy of MF3-open-flowsell-rsi5hi (950-1100) and -FD (950-1500), all sessions, Primary + Testing 1.
Paper results (rule 7), in-sample, small n: diagnosis only. radj = journal pnl_adj / $ risk (costs in).
Writes autopsy_out.txt. Educational only - not financial advice."""
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
T = pd.read_csv(HERE / "live_trades.csv")
T["var"] = np.where(T.strategy.str.endswith("-FD"), "FD", "W")
T["win"] = T.radj > 0
T["never"] = T.mfe_r < 0.2                     # never worked: best excursion < +0.2R
T["giveback"] = (T.mfe_r >= 0.5) & (T.radj < 0)  # was +0.5R, closed red
T["side_vs_idx"] = np.where(T.qqq_fo < 0, "QQQ<0 at entry (with index)", "QQQ>=0 at entry (against index)")
T["daytype"] = pd.cut(T.qqq_day, [-9, -0.3, 0.3, 9], labels=["QQQ day down", "QQQ day flat", "QQQ day up"])
out = []


def tab(by, df=T, name=None):
    g = df.groupby(by, observed=True)
    r = g.agg(n=("radj", "size"), days=("date", "nunique"), avgR=("radj", "mean"), sumR=("radj", "sum"), win=("win", "mean"),
              never=("never", "mean"), mfe=("mfe_r", "median"), mae=("mae_r", "median"), pnl=("pnl_adj", "sum"))
    out.append(f"\n### by {name or by}\n" + r.round(3).to_string())


out.append(f"trades {len(T)} | sessions {T.date.nunique()} ({T.date.min()}..{T.date.max()}) | avg R {T.radj.mean():+.3f} "
           f"(SE {T.radj.std() / np.sqrt(len(T)):.3f}) | win {T.win.mean():.1%} | never-worked {T.never.mean():.1%} | "
           f"give-back (>=+0.5R then red) {T.giveback.mean():.1%}")
tab("var", name="variant")
tab(["var", "acct"], name="variant x account")
tab("date")
T["tb"] = pd.cut(T.tod, [949, 1015, 1100, 1300, 1500], labels=["0950-1015", "1015-1100", "1100-1300", "1300-1500"])
tab("tb", name="entry time bucket (decision bar close)")
tab("side_vs_idx", name="QQQ from-open at entry")
T["spyb"] = pd.cut(T.spy_fo, [-9, -0.25, 0, 0.25, 9])
tab("spyb", name="SPY from-open at entry")
tab("daytype", name="QQQ session open-to-close")
T["rsi5b"] = pd.cut(T.rsi5, [70, 80, 90, 101])
tab("rsi5b", name="RSI5 at entry")
T["bpb"] = pd.cut(T.buyPressure, [-1.01, -0.5, -0.35, -0.25])
tab("bpb", name="flowsell (buyPressure) at entry")
T["gapb"] = pd.cut(T.gap, [-99, -1, 0, 1, 99])
tab("gapb", name="gap %")
T["fob"] = pd.cut(T.fromOpen, [-99, -1, 0, 1, 99])
tab("fob", name="stock from-open %")
T["advb"] = pd.qcut(T.adv20, 3)
tab("advb", name="adv20 tercile ($)")
T["stb"] = pd.qcut(T.stop_atrd, 3, duplicates="drop")
tab("stb", name="stop distance / daily ATR (R = 0.25 ATR by construction; deviation = fill vs ref)")
T["heatb"] = pd.cut(T.heat, [-101, -50, -40, -30])
tab("heatb", name="heat")
T["vwb"] = pd.cut(T.vwapDistPct, [-99, 0, 99])
tab("vwb", name="VWAP side")
tab("exit_reason")
first = T.sort_values("nt").groupby(["acct", "strategy", "symbol", "date"]).cumcount()
T["nth"] = np.where(first == 0, "1st entry sym-day", "re-entry")
tab("nth", name="1st vs re-entry (same setup/account/symbol/day)")
out.append("\nMFE quantiles: " + T.mfe_r.quantile([.25, .5, .75]).round(2).to_string().replace("\n", " | "))
out.append("losers that reached >= +0.5R: %d of %d" % (((T.radj < 0) & (T.mfe_r >= 0.5)).sum(), (T.radj < 0).sum()))
s = "\n".join(out)
(HERE / "autopsy_out.txt").write_text("Educational only - not financial advice. PAPER, in-sample, small n.\n" + s + "\n")
print(s)
