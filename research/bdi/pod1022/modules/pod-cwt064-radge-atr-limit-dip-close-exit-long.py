"""pod-cwt064-radge-atr-limit-dip-close-exit-long - Uptrend stock limit-dip below prior close, same-day close exit.

Source: Chat With Traders ep 064, Nick Radge 'The casino edge, mean reversion strategies' (limit-below-close entries in
uptrending stocks).
URL: https://chatwithtraders.com/episodes-by-topic-quant-algo

VARIANT of backlog 'CWT21 oversold dip buy with a limit entry 2-5% below the close' (daily, multi-day hold). Stated
change: intraday-only (flat 15:55), ATR-scaled limit, and an index-not-falling gate.

Rules (long, universe adv20 >= $50M, prior close >= $10):
  1) Daily uptrend: prior close above its 100-day average close and prior 3-day return (C[D-1] / C[D-4] - 1) < 0.
  2) Limit fill proxy: the FIRST bar closing 09:50-12:00 whose low reaches PDC - 0.6 x atr_d, with gap > -1% (the dip
     happens intraday, not on the open). If the running low of day had already reached the limit before that bar
     (i.e. during 09:30-09:45, not visible bar by bar), the day is skipped.
  3) spy_fo >= -0.3 on the fill bar (stock-specific dip).
  4) No earnings-type day: gap > -1% (above) and volumeRatio <= 3 on the fill bar (the scorer universe also removes
     the 4-day earnings blackout).
Entry: the scorer enters at the fill bar's CLOSE (the harness cannot fill at a limit price inside a bar; this is the
source's 'or that bar's close if it gapped through' case applied to every fill - a stated deviation). The bar's close
must still be below the exit limit (else the exit limit would already have filled). Disaster stop: entry - 1.0 x atr_d
(GEOM S, R = atr_d). Exit: limit at PDC - 0.1 x atr_d, else flat 15:55. Costs per config/default.yaml. No tweak made.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r35_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (950, 1200)
MIN_ADV = 50e6
CONTEXT = ["spy_fo"]


def mask(df) -> np.ndarray:
    if "spy_fo" not in df or len(df) == 0:
        return np.zeros(len(df), dtype=bool)
    k = U.key(df)
    d = U.map_daily(df, k, ["dc_1", "sma100_1", "c_4"])
    b = U.base(df)
    lim = b["pc"] - 0.6 * b["atr"]
    tod = b["tod"]
    st = U.start(k)
    with np.errstate(invalid="ignore"):
        touch = b["l"] <= lim
        # running LOD before this bar (previous bar's LOD; on the first frame bar: LOD excluding this bar unknown,
        # so require the 09:50 bar's own low to be the day's low when it touches)
        lod_prev = U.lag(b["lod"], k)
        pre = np.where(st, (b["lod"] <= lim) & (b["l"] > b["lod"] + 1e-9), lod_prev <= lim)
        earlier = np.asarray(pd_cummax(pre & np.isfinite(b["lod"]), k), bool)
        first = U.first_true(touch | earlier, k) & touch & ~earlier
        m = first
        m &= (d["dc_1"] > d["sma100_1"]) & (d["dc_1"] / d["c_4"] - 1 < 0) & (d["dc_1"] >= 10)
        m &= U.f(df, "gap") > -1.0
        m &= U.f(df, "spy_fo") >= -0.3
        m &= U.f(df, "volumeRatio") <= 3
        m &= b["c"] < b["pc"] - 0.1 * b["atr"]
        m &= U.f(df, "adv20") >= MIN_ADV
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return np.asarray(m, dtype=bool)


def pd_cummax(x, k):
    import pandas as pd
    return pd.Series(np.asarray(x, np.int64)).groupby(k).cummax().to_numpy() > 0


def stop_price(f, i):
    return float(f["close"].iat[i]) - 1.0 * float(f["atr_d"].iat[i])


def target_price(f, i, stop):
    c = float(f["close"].iat[i])
    pc = c / (1 + float(f["fromOpen"].iat[i]) / 100) / (1 + float(f["gap"].iat[i]) / 100)
    return pc - 0.1 * float(f["atr_d"].iat[i])
