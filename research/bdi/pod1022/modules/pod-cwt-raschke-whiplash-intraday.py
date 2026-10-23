"""pod-cwt-raschke-whiplash-intraday - Gap below the prior-day low that recovers above VWAP (Whiplash / day-2 failure
long). Config W (Raschke Whiplash; the primary). Config D2 (SMB Second-Day failure mirror) is
pod-cwt-raschke-whiplash-intraday-D2.py, which reuses this file with CFG = "D2".

Source: Linda Raschke (CWT ep 048 guest), 'Street Smarts' gap-reversal patterns (Traders.com); SMB Second-Day Play
failure rule run on the opposite side (SMB Trade of the Week / Steven Spencer). MERGED from
pod-cwt-raschke-whiplash-intraday and pod-smb-day2-failure-mirror-long.
URL: https://technical.traders.com/tradersonline/display.asp?art=2794

VARIANT, opposite side of CWT09 bad-news gap-down bounce short, L3 gap-down recovery fade, NS3/RW4 big-loser VWAP
reclaim fade; differs from pod-raschke-adx-gapper (no trend gate, deeper gap, VWAP / range trigger, not a PDL reclaim)
and from SMB Second-Day failure (written short-only).

Rules (plain English, LONG):
  1. Config W: today's open is below the prior-day low by >= 0.5 x daily ATR (open = close / (1 + fromOpen/100), PDL
     from dist_pdl_atr).
     Config D2 (completed days only, research/history2y daily table): the prior day's change was <= -5% or <= -2 x ATR%
     (daily ATR / prior close), the prior day closed in the bottom 25% of its range, and today opened below the PDL.
  2. Trigger, 10:00-12:30:
     W (from 10:30): two consecutive 5-minute closes above the session VWAP and in the upper half of the day's range so
     far (running high / low of day); entry on the second.
     D2: the first close above VWAP of the day (vwapReclaim == +1 and no earlier frame close above VWAP), with
     flow3 >= 0.3 and volumeRatio >= 1.3.
  3. spy_fo > -0.3% at the trigger.
  Entry at the trigger close. Stop (GEOM S): max(low of day, entry - 0.6 x daily ATR) (pre-declared 0.6 of the
  source's 0.5-0.6 range). Target: W = the PDL; D2 = the prior close capped at 2R (2R if the prior close is not above
  the entry); if the PDL is not above the entry (W) the trade holds to 15:55. Flat 15:55. Costs in (scorer).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1230)
CFG = "W"
CONTEXT = ["spy_fo"]
STOP_ATR = 0.6
LAYERS = ["W: open < PDL - 0.5 ATR | D2: prior day <= -5% or -2 ATR%, closed in bottom 25%, open < PDL",
          "W: 2 consecutive closes above VWAP and in the upper half of the day range (10:30-12:30) | "
          "D2: first close above VWAP, flow3 >= 0.3, volumeRatio >= 1.3 (10:00-12:30)",
          "spy_fo > -0.3%", "stop max(LOD, entry - 0.6 ATR), target PDL (W) / prior close capped 2R (D2), flat 15:55"]

_ROOT = Path(__file__).resolve().parents[4]
_STASH = {}
_CACHE = {}


def _lib():
    p = str(_ROOT / "research" / "history2y")
    if p not in sys.path:
        sys.path.insert(0, p)
    import lib  # noqa: E402
    return lib


def _daily():
    if "daily" in _CACHE:
        return _CACHE["daily"]
    d = _lib().daily()[["symbol", "date", "high", "low", "close"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    gs = d.groupby("symbol", sort=False)
    c1 = gs["close"].shift(1)
    dt = pd.to_datetime(d["date"])
    d["chg"] = (d["close"] / c1 - 1) * 100
    d.loc[~((dt - dt.groupby(d["symbol"]).shift(1)).dt.days <= 5), "chg"] = np.nan
    rng = d["high"] - d["low"]
    d["cloc"] = np.where(rng > 0, (d["close"] - d["low"]) / rng, np.nan)
    d["next_date"] = gs["date"].shift(-1)
    d = d[(pd.to_datetime(d["next_date"]) - dt).dt.days <= 5]
    out = d[["symbol", "next_date", "close", "chg", "cloc"]].rename(columns={"next_date": "date", "close": "pc_d"})
    _CACHE["daily"] = out
    return out


def _seg_first(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    return k, np.r_[True, k[1:] != k[:-1]] if len(k) else np.zeros(0, bool)


def _prev(x, first):
    p = np.r_[np.nan, x[:-1]]
    p[first] = np.nan
    return p


def compute(df, cfg):
    n = len(df)
    if n == 0 or "spy_fo" not in df:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, h, l, atr = f("close"), f("high"), f("low"), f("atr_d")
    tod = df["tod"].to_numpy(np.int64)
    key, first = _seg_first(df)
    with np.errstate(invalid="ignore", divide="ignore"):
        vw = c / (1 + f("vwapDistPct") / 100)
        opn = c / (1 + f("fromOpen") / 100)
        pdl = c - f("dist_pdl_atr") * atr
        hod = np.maximum(c + f("dist_hod_atr") * atr, pd.Series(h).groupby(key).cummax().to_numpy())
        lod = np.minimum(c - f("dist_lod_atr") * atr, pd.Series(l).groupby(key).cummin().to_numpy())
        spy = f("spy_fo")
        if cfg == "W":
            above = (c > vw) & (c >= 0.5 * (hod + lod))
            m = (pdl - opn >= 0.5 * atr) & above & (_prev(above.astype(float), first) == 1)
            m &= (tod >= 1030) & (tod <= 1230)
        else:
            key_df = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "date": df["date"].to_numpy()})
            dg = key_df.merge(_daily(), on=["symbol", "date"], how="left")
            pc = dg["pc_d"].to_numpy(float)
            chg = dg["chg"].to_numpy(float)
            gate = ((chg <= -5) | (chg <= -2 * atr / pc * 100)) & (dg["cloc"].to_numpy(float) <= 0.25) & (opn < pdl)
            ab = (c > vw).astype(np.int64)
            seen = pd.Series(ab).groupby(key).cumsum().to_numpy()        # closes above VWAP so far, this bar incl.
            m = gate & (ab == 1) & (seen == 1) & (f("vwapReclaim") == 1) & (f("flow3") >= 0.3) & (f("volumeRatio") >= 1.3)
            m &= (tod >= 1000) & (tod <= 1230)
        m &= spy > -0.3
        stop = np.maximum(lod, c - STOP_ATR * atr)
        R = c - stop
        if cfg == "W":
            tgt = np.where(pdl > c, pdl, c + 50 * atr)
        else:
            tgt = np.where(pc > c, np.minimum(pc, c + 2 * R), c + 2 * R)
    m = np.asarray(m & np.isfinite(stop) & (R > 0), bool)
    return m, stop, tgt


def mask(df) -> np.ndarray:
    m, stop, tgt = compute(df, CFG)
    _STASH.clear()
    _STASH[id(df)] = (stop, tgt)
    return m


def _get(f):
    s = _STASH.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _STASH[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])
