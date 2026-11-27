"""STOPX-1127 Step 0: live stop-exit slippage vs the research assumptions (PREREG.md). Input: the primshorts_1126 cleaned
live set (live.parquet + exitbars.parquet; calib_live.prep() cleaning, unchanged). Stop exits only:
  slip/share = side x (engine fill - live fill), engine fill = stop, or the exit-minute open when already through it.
Reported in bps of price and R; vs 4 bp (inspector's LR8 quote), the LR8 research stop-exit charge (1c + 1 bp + 2c) and the
LIVE-L stop cell (exit part only is not separable there; whole-trade cell shown). Also: share of stop exits whose exit-minute
close is back on the right side of the stop. Usage: python sx_live.py LIVE_DIR OUT.json. Live data only (10-14..11-25), no
bench data, so the locked block is not involved. Educational only - not financial advice."""
import json
import os
import sys

import numpy as np
import pandas as pd

H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(H + "/../primshorts_1126"))
import calib_live as CL  # noqa: E402

CL.L = sys.argv[1]
OUT = sys.argv[2]


def summ(g):
    return {"n": int(len(g)), "slip_bps_mean": round(float(g.slip_bps.mean()), 2),
            "slip_bps_median": round(float(g.slip_bps.median()), 2), "slip_bps_p90": round(float(g.slip_bps.quantile(0.9)), 2),
            "slip_R_mean": round(float(g.slip_R.mean()), 4), "lr8_stop_charge_bps": round(float(g.lr8_bps.mean()), 2),
            "lr8_stop_charge_R": round(float(g.lr8_R.mean()), 4), "excess_vs_4bp_R": round(float(g.ex4_R.mean()), 4),
            "excess_vs_lr8_R": round(float(g.exl_R.mean()), 4),
            "close_back_share": round(float(g.close_back.mean()), 3) if g.close_back.notna().any() else None,
            "gapped_through_share": round(float(g.gapped.mean()), 3), "med_stop_bps": round(float(g.w_bps.median()), 1)}


if __name__ == "__main__":
    t = CL.prep()
    s = t[t.kind == "stop"].copy()
    sd = s.side
    eng = np.where(sd > 0, np.minimum(s.x_open, s.stop), np.maximum(s.x_open, s.stop))
    s["gapped"] = (eng != s.stop)
    s["slip_ps"] = sd * (eng - s.exit)
    p = s.ref_price
    s["slip_bps"] = s.slip_ps / p * 1e4
    s["slip_R"] = s.slip_ps / s.risk_ps
    lr8 = 0.01 + s.stop * 1e-4 + 0.02
    s["lr8_bps"] = lr8 / p * 1e4
    s["lr8_R"] = lr8 / s.risk_ps
    s["ex4_R"] = (s.slip_ps - 4e-4 * p) / s.risk_ps
    s["exl_R"] = (s.slip_ps - lr8) / s.risk_ps
    s["close_back"] = np.where(s.x_close.isna(), np.nan, np.where(sd > 0, s.x_close > s.stop, s.x_close < s.stop))
    fam = s.strategy.str.startswith(("L3-gap", "RW3", "RW5", "RW6", "RW7"))
    res = {"window": [str(s.date.min()), str(s.date.max())], "ALL": summ(s), "gapdown_family": summ(s[fam]),
           "rest": summ(s[~fam]), "by_side": {("long" if k > 0 else "short"): summ(g) for k, g in s.groupby("side")},
           "by_price": {k: summ(g) for k, g in s.groupby("pb")}, "by_stop_width": {k: summ(g) for k, g in s.groupby("wb")},
           "primary4": {k: summ(g) for k, g in s.groupby("strategy") if k in (
               "L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
               "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "NM-ETF-late-dip-di-long")},
           "accounts": int(s.account.nunique())}
    json.dump(res, open(OUT, "w"), indent=1)
    print(json.dumps({k: res[k] for k in ("window", "ALL", "gapdown_family", "rest", "by_side")}, indent=1))
    print(pd.DataFrame(res["by_price"]).T.to_string())
    print(pd.DataFrame(res["primary4"]).T.to_string())
