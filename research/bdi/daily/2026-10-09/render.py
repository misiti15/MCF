"""Markdown tables for AUTOPSY.md from trades.csv. Educational only - not financial advice."""
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
A = pd.read_csv(HERE / "trades.csv")
AB = {"heat_fade_short": "hfs", "heat_fade_long": "hfl", "exhaustion_short": "exh", "orb20_a": "orb"}


def ab(s):
    if s in AB:
        return AB[s]
    return s.split("-")[0] if s[:2] in ("MF", "NS", "RW", "ST", "L3") else s


def rules(t):
    s = t.setup
    f = lambda k: t.get(f"f_{k}", np.nan)  # noqa: E731
    if s.startswith("heat"):
        return f"score {f('score'):.1f}, gap {f('gap'):+.2f}%, fromOpen {f('fromOpen'):+.2f}%, rsi {f('rsi'):.0f}"
    if s.startswith("exh") or s.startswith("RW2"):
        return f"rsi5 {f('rsi5'):.0f}, sma20 {f('sma20_dist_pct'):+.2f}%, bear_div {f('bear_div'):.0f}, fromOpen {f('fromOpen'):+.1f}%"
    if s.startswith("orb"):
        return f"OR break, fromOpen {f('fromOpen'):+.1f}%, rsi {f('rsi'):.0f}"
    return (f"heat {f('heat'):.0f}, bp {f('buyPressure'):+.2f}, vwap {f('vwapDistPct'):+.2f}%, rsi5 {f('rsi5'):.0f}, "
            f"rsi {f('rsi'):.0f}, fo {f('fromOpen'):+.1f}%, gap {f('gap'):+.1f}%")


for acct, g in A.groupby("account"):
    print(f"\n### {acct} ({len(g)} trades)\n")
    print("| id | sym | setup | side | in-out (ET) | exit | r live | rule values at signal (recomputed) | brd / SPY fo at entry | "
          "held MFE / MAE (R) | t->MFE held / day (min) | day MFE | BE0.5 | trail | tp0.5 | tp1 | hold 15:55 | SAR | re-entry | "
          "opposite 1R/1R | loss type |")
    print("|" + "---|" * 21)
    for _, t in g.sort_values("entry_time").iterrows():
        print(f"| {t.id} | {t.symbol} | {ab(t.setup)} | {'L' if t.side == 1 else 'S'} | {t.entry_time[:5]}-{t.exit_time[:5]} | "
              f"{t.exit_reason} | {t.r_live:+.2f} | {rules(t)} | {t.ctx_brd_fo:.2f} / {t.spy_fromopen_pct:+.2f}% | "
              f"{t.held_mfe_r:.2f} / {t.held_mae_r:.2f} | {t.held_t_mfe_min:.0f} / {t.day_t_mfe_min:.0f} | {t.day_mfe_r:.2f} | "
              f"{t['wi_be0.5']:+.2f} | {t['wi_trail0.5']:+.2f} | {t['wi_tp0.5']:+.2f} | {t.wi_tp1:+.2f} | {t.wi_hold_1555:+.2f} | "
              f"{t.wi_stop_and_reverse:+.2f} | {t.wi_reentry:+.2f} | {t.opp_1r1r:+.2f} ({t.opp_why}) | {t.loss_type} |")
