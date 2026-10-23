"""pod-bst-alvarez-pd-lowibs-etf-vwap-hold-long - Prior-day low-IBS ETF, intraday VWAP-hold confirmation (Alvarez
mean-reversion class).

Source: Better System Trader ep 130 / 133 'Building Mean Reversion trading strategies' (Cesar Alvarez) - IBS /
close-location dip entries and market classification.
URL: https://podwise.ai/podcasts/2840?page=10

NEW feature family: the PRIOR-DAY internal bar strength IBS = (PDC - PDL) / (PDH - PDL), not intraday rsi5 and not a
3-down-days count.

Rules (long, SYMBOLS = the 15-ETF list SPY QQQ IWM DIA XLF XLK XLE XLV XLI XLY XLP XLU SMH XBI KRE):
  1) Prior-day IBS <= 0.15 (completed day D-1, daily table).
  2) Prior close above its 50-day average close (SMA50 of daily closes ending D-1; uptrend class).
  3) Today's gap between -1.0% and +0.3%.
  4) Entry bar closing 10:30-13:00: close > VWAP, fromOpen > 0, and the low of day has not been undercut after 10:30
     (running LOD at this bar == running LOD at the 10:30 bar = the 09:30-10:30 low).
Entry at that bar's close. Stop: low of day - 0.1 x atr_d (GEOM S). Target: prior-day high (limit), else flat 15:55
(a bar at or above the PDH is skipped by the scorer as a wrong-side target). Costs per config/default.yaml. No tweak.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r35_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1300)
SYMBOLS = list(U.ETF15)


def mask(df) -> np.ndarray:
    if len(df) == 0:
        return np.zeros(0, dtype=bool)
    k = U.key(df)
    d = U.map_daily(df, k, ["ibs_1", "dc_1", "sma50_1"])
    b = U.base(df)
    tod = b["tod"]
    lod1030 = U.at_tod(b["lod"], k, tod, 1030)
    gap = U.f(df, "gap")
    with np.errstate(invalid="ignore"):
        m = np.isin(df["symbol"].astype(str).to_numpy(), SYMBOLS)
        m &= d["ibs_1"] <= 0.15
        m &= d["dc_1"] > d["sma50_1"]
        m &= (gap >= -1.0) & (gap <= 0.3)
        m &= (U.f(df, "vwapDistPct") > 0) & (U.f(df, "fromOpen") > 0)
        m &= b["lod"] >= lod1030 - 1e-6 * b["c"]
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return np.asarray(m, dtype=bool)


def stop_price(f, i):
    c = float(f["close"].iat[i])
    atr = float(f["atr_d"].iat[i])
    return c - float(f["dist_lod_atr"].iat[i]) * atr - 0.1 * atr


def target_price(f, i, stop):
    c = float(f["close"].iat[i])
    return c + float(f["dist_pdh_atr"].iat[i]) * float(f["atr_d"].iat[i])
