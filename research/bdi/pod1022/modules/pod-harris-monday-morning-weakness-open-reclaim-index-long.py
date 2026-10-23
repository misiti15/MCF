"""pod-harris-monday-morning-weakness-open-reclaim-index-long - Monday-morning weekend-effect dip, index ETF reclaim of
the open.

Source: Harris (1986) 'A transaction data study of weekly and intradaily patterns in stock returns' (JFE) - Monday
losses concentrated right after the open, other mornings rise; Better System Trader ep 137 Dimitri Speck on intraday
seasonality.
URL: https://ideas.repec.org/a/eee/jfinec/v16y1986i1p99-117.html

VARIANT of pod-crabel-stretch-open-reclaim-long and pod-cal-turnaround-tuesday-index-reclaim-long. Stated change:
calendar gate = first session of the week (Monday or post-holiday Tuesday) with NO prior down-day requirement,
index / sector ETFs only, and the dip must happen in the first 45 minutes (the Harris window).

Rules (long, SYMBOLS = SPY QQQ IWM DIA + sector ETFs: XLF XLK XLE XLV XLI XLY XLP XLU SMH XBI KRE):
  1) First trading session of the week (previous session in an earlier ISO week).
  2) The ETF's fromOpen (close vs today's open) was <= -0.35% on some bar closing 09:35-10:15 (09:35-09:45 closes from
     the head/tail table, 09:50-10:15 from the frame), and SPY's low of day so far was set by 10:15 (SPY's running
     LOD at the entry bar equals its running LOD at the 10:15 bar).
  3) Entry bar closing 10:15-11:30: fromOpen crosses from < 0 (previous bar) to > 0 (reclaims today's open), with
     breadth_open >= 0.50.
  4) gap >= -1.0% (not a crash Monday).
Entry: that bar's close. Stop: low of day - 0.05 x atr_d (GEOM S). Hold to 15:55, no target (the optional 1R trail is
not used; the scorer's 'hold' control applies). Costs per config/default.yaml. No tweak made.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r35_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1015, 1130)
SYMBOLS = list(U.ETF15)
CONTEXT = ["breadth_open"]


def _spy_lod_ok(df):
    """Per row: SPY running LOD at this (date, tod) == SPY running LOD at 10:15 (from SPY's own frame rows)."""
    sp = df[df["symbol"].astype(str) == "SPY"]
    if len(sp) == 0:
        return np.zeros(len(df), bool)
    c = sp["close"].to_numpy(float)
    lod = c - sp["dist_lod_atr"].to_numpy(float) * sp["atr_d"].to_numpy(float)
    t = pd.DataFrame({"date": pd.Series(sp["date"].to_numpy()).astype(str).to_numpy(),
                      "tod": sp["tod"].to_numpy(np.int64), "lod": lod})
    l15 = t[t["tod"] == 1015][["date", "lod"]].rename(columns={"lod": "l15"})
    t = t.merge(l15, on="date", how="left")
    t["ok"] = (t["tod"] >= 1015) & (t["lod"] >= t["l15"] - 1e-6 * t["l15"])
    k = pd.DataFrame({"date": pd.Series(df["date"].to_numpy()).astype(str).to_numpy(),
                      "tod": df["tod"].to_numpy(np.int64)})
    m = k.merge(t[["date", "tod", "ok"]], on=["date", "tod"], how="left")
    assert len(m) == len(df)
    return m["ok"].fillna(False).to_numpy(bool)


def mask(df) -> np.ndarray:
    if "breadth_open" not in df or len(df) == 0:
        return np.zeros(len(df), dtype=bool)
    k = U.key(df)
    b = U.base(df)
    tod = b["tod"]
    fo = U.f(df, "fromOpen")
    s = U.map_spy(df, ["first_week"])
    hmin = U.map_head(df, k, SYMBOLS)
    with np.errstate(invalid="ignore", divide="ignore"):
        fo_head = (hmin / b["opn"] - 1) * 100
        fo_early = np.where((tod <= 1015) & np.isfinite(fo), fo, np.inf)
        fo_min = U.run_min(fo_early, k)               # min fromOpen over 09:50..min(tod, 10:15) bars
        fo_min = np.fmin(fo_min, fo_head)
        m = np.isin(df["symbol"].astype(str).to_numpy(), SYMBOLS)
        m &= s["first_week"] == 1
        m &= fo_min <= -0.35
        m &= _spy_lod_ok(df)
        m &= (U.lag(fo, k) < 0) & (fo > 0)
        m &= U.f(df, "breadth_open") >= 0.50
        m &= U.f(df, "gap") >= -1.0
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return np.asarray(m, dtype=bool)


def stop_price(f, i):
    c = float(f["close"].iat[i])
    atr = float(f["atr_d"].iat[i])
    return c - float(f["dist_lod_atr"].iat[i]) * atr - 0.05 * atr
