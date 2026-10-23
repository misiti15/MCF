"""pod-opex-friday-round-strike-pin-fade-short - Monthly OpEx pin: midday fade back to a round strike already traded
today (SHORT side; the other side is pod-opex-friday-round-strike-pin-fade-long.py).

Source: SpotGamma / Brent Kochuba podcast appearances on OpEx pinning and dealer gamma (pinning to high open-interest
strikes on expiration Friday). Written from memory, URL not re-checked.
URL: https://spotgamma.com/

VARIANT of the backlog idea 'Overbought/oversold at PDH/PDL/HOD/round numbers' and the opposite of
pod-wt-flat-top-roundnum-long (a breakout). Stated change: only monthly-OpEx Fridays, the level is a round strike the
stock already traded through today, the trade is a fade TOWARD the strike, and the window is midday.
Also differs from pod-cal-opex-friday-strike-pin-fade-* (pod1022, Ni/Pearson/Poteshman): this one needs the strike to
lie inside today's range so far, a wider 0.30-0.80 ATR stretch, a first-reversal-bar trigger, a fixed heavy-options
universe and a 0.40 ATR stop. The duplicate check is run against those files.
Rules (plain English):
  Universe: SPY, QQQ, IWM, AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA, AMD, AVGO, NFLX.
  Strike grid: $5 for price >= $100, $1 for $20-100 (no trade below $20). Bar close 12:30-14:45.
  1. The date is the 3rd Friday of the month (Thursday before it when that Friday is an NYSE holiday).
  2. |spy_fo| <= 0.50%.
  3. K = the nearest grid strike. Today's range so far (LOD..HOD) contains K, and |close - K| is 0.30-0.80 x atr_d.
  4. Long when close < K: rsi5 <= 30 and close > previous close. Short when close > K: rsi5 >= 70 and close <
     previous close.
  Entry: close. Stop (GEOM S): entry -/+ 0.40 x atr_d. Target: K (limit). Flat 15:55.
Small sample (about 22 OpEx days x 13 symbols): read n and best_day_share. No tweak made.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "short"
GEOM = "S"
WINDOW = (1230, 1445)
SYMBOLS = ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "AMD", "AVGO", "NFLX"]
MIN_ADV = 0
CONTEXT = ["spy_fo"]
LAYERS = ["monthly OpEx Friday", "|spy_fo| <= 0.5", "nearest $5/$1 strike inside today's range",
          "|close - K| 0.30-0.80 ATR", "rsi5 <= 30 + up close below K (long) / >= 70 + down close above K (short)",
          "stop 0.40 ATR, target K, flat 15:55"]
HOLIDAYS = {"2024-03-29", "2025-04-18", "2026-04-03", "2026-06-19"}


def _opex_dates():
    out = set()
    for ms in pd.date_range("2024-01-01", "2027-01-01", freq="MS"):
        fr = [d for d in pd.date_range(ms, ms + pd.offsets.MonthEnd(0)) if d.weekday() == 4][2]
        if fr.strftime("%Y-%m-%d") in HOLIDAYS:
            fr = fr - pd.Timedelta(days=1)
        out.add(fr.date())
    return out

import numpy as np
import pandas as pd

_ST = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _start(k):
    return np.r_[True, k[1:] != k[:-1]] if len(k) else np.zeros(0, bool)


def _lag(x, k, n=1):
    """x from n bars earlier in the same symbol-day k (NaN when that bar is in another group)."""
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def _base(df):
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c = _f(df, "close")
    atr = _f(df, "atr_d")
    b = dict(k=k, tod=tod, c=c, h=_f(df, "high"), l=_f(df, "low"), atr=atr)
    b["hod"] = c + _f(df, "dist_hod_atr") * atr          # running high of day (includes 09:30-09:45)
    b["lod"] = c - _f(df, "dist_lod_atr") * atr          # running low of day
    b["pdl"] = c - _f(df, "dist_pdl_atr") * atr          # prior completed day's low
    b["vwap"] = c / (1 + _f(df, "vwapDistPct") / 100)
    b["atr5"] = _f(df, "atrPct") * c / 100                # 5-minute ATR(14), $
    return b


def _stash_get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    if s is None or s[j] is None:
        return float("nan")
    return float(s[j][i])


def stop_price(f, i):
    return _stash_get(f, i, 0)


def target_price(f, i, stop):
    return _stash_get(f, i, 1)


GATE = _opex_dates()


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df) or "spy_fo" not in df:
        return z
    b = _base(df)
    k, tod, c, atr = b["k"], b["tod"], b["c"], b["atr"]
    dt = pd.to_datetime(df["date"]).dt.date.to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        step = np.where(c >= 100, 5.0, np.where(c >= 20, 1.0, np.nan))
        K = np.round(c / step) * step
        m = np.isin(dt, list(GATE))                                                   # (1)
        m &= np.abs(_f(df, "spy_fo")) <= 0.50                                          # (2)
        m &= (b["lod"] <= K) & (b["hod"] >= K)                                         # (3)
        d = np.abs(c - K) / atr
        m &= (d >= 0.30) & (d <= 0.80)
        r5, pc = _f(df, "rsi5"), _lag(c, k)
        if SIDE == "long":
            m &= (c < K) & (r5 <= 30) & (c > pc)                                       # (4)
            stop = c - 0.40 * atr
        else:
            m &= (c > K) & (r5 >= 70) & (c < pc)
            stop = c + 0.40 * atr
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (stop, K)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(K), dtype=bool)
