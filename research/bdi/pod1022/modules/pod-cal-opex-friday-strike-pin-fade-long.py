"""pod-cal-opex-friday-strike-pin-fade-long - Monthly options-expiration Friday: fade afternoon moves away from the
nearest round strike, back toward it (LONG side; the SHORT side is pod-cal-opex-friday-strike-pin-fade-short.py).

Source: pinning literature - Ni, Pearson and Poteshman (2005), 'Stock price clustering on option expiration dates',
Journal of Financial Economics 78(1); discussed widely in systematic-trading interviews. Not verified against a
specific podcast episode (web blocked this run).
URL: https://doi.org/10.1016/j.jfineco.2004.08.005
Variant check: the round-number setups already in the backlog (CWT44, 'Overbought/oversold at ... round numbers',
pod-wt-flat-top-roundnum-long) use neither the expiration-day gate nor a magnet target at the strike.

Rules (plain English):
  Date gate: the third Friday of the month (monthly opex); if that Friday is an NYSE holiday, the Thursday before it.
  Universe: adv20 >= $200M (heavily optioned names) plus SPY / QQQ / IWM.
  1. Bar close 12:00-15:00.
  2. |spy_fo| <= 0.6 (not a trend day).
  3. dist_round_atr between 0.12 and 0.35, on the frame's strike grid ($5 at >= $100, $1 at >= $20, else $0.5).
  4a. SHORT module: close ABOVE the nearest round level and rsi5 >= 70.
  4b. LONG module: close BELOW the nearest round level and rsi5 <= 30.
  Entry: bar close. GEOM S: stop = entry -/+ 0.25 x atr_d (away from the strike); target = the round level (limit);
  otherwise flat 15:55. Costs per config/default.yaml (applied by the scorer). No tweak made.
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1200, 1500)
MIN_ADV = 0
CONTEXT = ["spy_fo"]
INDEX = ["SPY", "QQQ", "IWM"]
LAYERS = ["monthly opex Friday (Thursday if the Friday is a holiday)", "adv20 >= $200M or SPY/QQQ/IWM",
          "|spy_fo| <= 0.6", "dist_round_atr in [0.12, 0.35]", "below the strike and rsi5 <= 30 (long) / above and >= 70 (short)",
          "12:00-15:00", "stop 0.25 ATR away from the strike, target = the strike, flat 15:55"]

HOLIDAYS = {"2024-03-29", "2025-04-18", "2026-04-03", "2026-06-19"}   # NYSE Friday holidays 2024-2026 that fall on a third Friday or Good Friday
_STASH = {}


def _opex_dates():
    out = set()
    for ms in pd.date_range("2024-01-01", "2027-01-01", freq="MS"):
        fr = [d for d in pd.date_range(ms, ms + pd.offsets.MonthEnd(0)) if d.weekday() == 4][2]
        if fr.strftime("%Y-%m-%d") in HOLIDAYS:
            fr = fr - pd.Timedelta(days=1)
        out.add(fr.date())
    return out


GATE = _opex_dates()


def _compute(df):
    n = len(df)
    z = np.zeros(n, bool)
    if not n or "spy_fo" not in df:
        return z, np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, atr, tod = f("close"), f("atr_d"), f("tod")
    step = np.where(c >= 100, 5.0, np.where(c >= 20, 1.0, 0.5))
    rnd = np.round(c / step) * step
    dt = pd.to_datetime(df["date"]).dt.date.to_numpy()
    sym = df["symbol"].astype(str)
    with np.errstate(invalid="ignore"):
        m = np.isin(dt, list(GATE))
        m &= (f("adv20") >= 200e6) | sym.isin(INDEX).to_numpy()
        m &= np.abs(f("spy_fo")) <= 0.6
        dr = f("dist_round_atr")
        m &= (dr >= 0.12) & (dr <= 0.35)
        if SIDE == "long":
            m &= (c < rnd) & (f("rsi5") <= 30)
            stop = c - 0.25 * atr
        else:
            m &= (c > rnd) & (f("rsi5") >= 70)
            stop = c + 0.25 * atr
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return np.asarray(m, bool), stop, rnd


def mask(df) -> np.ndarray:
    m, stop, tgt = _compute(df)
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
