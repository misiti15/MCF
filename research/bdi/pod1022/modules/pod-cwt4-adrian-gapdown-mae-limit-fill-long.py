"""pod-cwt4-adrian-gapdown-mae-limit-fill-long - Mid-size gap-down fill bought with a limit at the historical
worst-move-before-fill zone (LONG, index / sector ETFs).

Source: Chat With Traders ep 95, Adrian (@AdeyF69) ('Size-banded gap fill entered at historical MAE zone').
VARIANT of CWT test A6 (failed gap auction) and of the small index-ETF gap-fill sleeve (market entry at the open).
The change: no reversal trigger; the entry is a resting limit at the median MAE of past filled gaps.
URL: https://chatwithtraders.com/95

Rules (plain English). SYMBOLS: SPY, QQQ, IWM, DIA, XLK, XLF, XLE, XLV, XLI, XLY, XLP, XLU (+ XLB/XLRE/XLC if present).
  1. Today's gap-down is between 0.3% and 1.0% (fixed % band, the source's main band; the ATR-scaled band is not run).
  2. Over the prior 250 open sessions of the same ETF (daily bars, completed days only), take the gap-downs in the
     same band; a gap 'filled' when the day's high reached the prior close. The band's fill rate must be >= 65%
     (and >= 10 band days). MAE = (open - day low) / open on the filled days. Daily bars cannot tell whether the low
     came before the fill, so the day low is used (declared: an upper bound of the pre-fill MAE). Median MAE and
     80th-percentile MAE come from those filled days.
  3. Not a scheduled macro day (CPI / NFP / PPI / FOMC lists); prior-day range <= 1.5 x ATR(14) as of D-2.
  Entry: buy limit L = open x (1 - median MAE), valid to 12:00. The history frames start at the 09:50 bar, so the
  trade enters at the close of the first bar (09:50-12:00) by which the session low has reached L (declared: the
  scorer enters at a bar close, not at the limit price; touches in 09:30-09:35 also count).
  Stop (GEOM S): open x (1 - MAE80) - 0.05 x daily ATR; skipped if the session low already broke it.
  Target: the prior close (gap fill); else flat 15:55. One trade per symbol per day.
No tweak made. The parent comparison (market entry at 09:35) is not scored here (no 09:35 bar in the frames).
Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cwt4_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (950, 1200)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"]
BAND = (-1.0, -0.3)
LAYERS = ["gap -1.0..-0.3%", "250-session band fill rate >= 65%", "no macro day, prior range <= 1.5 ATR",
          "session low reached open x (1 - median MAE) by 12:00", "stop open x (1 - MAE80) - 0.05 ATR, target prior close"]
_ST = {}
_C = {}


def _gap_stats():
    if "g" in _C:
        return _C["g"]
    d = U.raw_daily()
    d = d[d["symbol"].isin(SYMBOLS)].copy()
    rows = []
    for sym, x in d.groupby("symbol", sort=False):
        x = x.sort_values("date").reset_index(drop=True)
        o, h, l, c = (x[k].to_numpy(float) for k in ("open", "high", "low", "close"))
        pc = np.r_[np.nan, c[:-1]]
        gap = (o / pc - 1) * 100
        inb = (gap >= BAND[0]) & (gap <= BAND[1])
        fill = h >= pc
        mae = (o - l) / o
        hl = h - l
        tr = np.maximum.reduce([hl, np.abs(h - pc), np.abs(l - pc)])
        atr = pd.Series(tr).rolling(14, min_periods=14).mean().to_numpy()
        for t in range(1, len(x)):
            a = max(0, t - 250)
            ib = inb[a:t]
            nb = int(ib.sum())
            rec = {"symbol": sym, "date": x["date"].iloc[t].strftime("%Y-%m-%d"), "nb": nb,
                   "fr": np.nan, "mae50": np.nan, "mae80": np.nan,
                   "rng1": hl[t - 1], "atr2": atr[t - 2] if t >= 2 else np.nan}
            if nb:
                fl = fill[a:t][ib]
                rec["fr"] = fl.mean()
                if fl.any():
                    mm = mae[a:t][ib][fl]
                    rec["mae50"] = float(np.median(mm))
                    rec["mae80"] = float(np.quantile(mm, 0.8))
            rows.append(rec)
    _C["g"] = pd.DataFrame(rows)
    return _C["g"]


def mask(df) -> np.ndarray:
    n = len(df)
    z = np.zeros(n, bool)
    if n == 0:
        return z
    k = U.key(df)
    b = U.base(df)
    s = U.map_day(df, k, _gap_stats(), ["nb", "fr", "mae50", "mae80", "rng1", "atr2"])
    ds = U.dstr(df)
    macro = np.isin(ds, sorted(U.macro_days()))
    gap = U.f(df, "gap")
    opn, pc, lod, c, atr = b["opn"], b["pc"], b["lod"], b["c"], b["atr"]
    with np.errstate(invalid="ignore", divide="ignore"):
        L = opn * (1 - s["mae50"])
        stop = opn * (1 - s["mae80"]) - 0.05 * atr
        m = (gap >= BAND[0]) & (gap <= BAND[1]) & (s["nb"] >= 10) & (s["fr"] >= 0.65) & ~macro
        m &= s["rng1"] <= 1.5 * s["atr2"]
        m &= (lod <= L) & (lod > stop) & (c > stop) & (c < pc) & (b["tod"] <= 1200)
    _ST[id(df)] = (stop, pc)
    return np.asarray(m, bool)


def stop_price(f, i):
    return U.stash_get(_ST, f, mask, i, 0)


def target_price(f, i, stop):
    return U.stash_get(_ST, f, mask, i, 1)
