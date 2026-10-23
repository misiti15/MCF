"""pod-cwt-mcdermitt-rs-hold-at-index-newlow-long-holdtr - GEOM holdtr CHECK of Stock holding above its low while SPY prints a new session low:
long the relative-strength holder (LONG). Same mask as pod-cwt-mcdermitt-rs-hold-at-index-newlow-long.py; exit
GEOM holdtr (stop 1R = 0.25 x atr_d, 1R trail once +1R, flat 15:55) instead of the structural stop / 1.5R target.

Source: Chat With Traders ep. 267, Dan McDermitt, 'Relative strength at support while the index makes new lows'
(local: research/bdi/cwt/catalog.jsonl, family CWT16).
URL: https://chatwithtraders.com/267
VARIANT of CWT16 / Reddit R16-rel-strength and 'Relative strength vs SPY with market/VWAP filters' (generic RS-vs-SPY
continuation). Stated changes: the trigger fires ONLY on the bar where SPY makes a new session low, and the stop sits
under the stock's own LOD (structural).

Rules (plain English, LONG):
  1. Bar close 10:00-14:00.
  2. spy_fo <= -0.40 AND spy_fo equals its running minimum for the date (a new SPY session low on this bar; the
     running minimum is taken over the per-date SPY context from the 09:50 bar on - bars up to this one only).
  3. The stock's fromOpen >= 0 (green on the day).
  4. dist_lod_atr >= 0.40 (well off its low).
  5. vwapDistPct > 0.
  6. adv20 >= $50M.
  Entry: bar close. GEOM S: stop = (close - dist_lod_atr x atr_d) - 0.05 x atr_d (just under the stock's LOD);
  target = entry + 1.5 x risk; otherwise flat 15:55. Costs per config/default.yaml (applied by the scorer).
  No tweak made.
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "holdtr"
WINDOW = (1000, 1400)
MIN_ADV = 50e6
TARGET_MULT = 1.5
CONTEXT = ["spy_fo"]
LAYERS = ["SPY new session low on this bar with spy_fo <= -0.40", "stock fromOpen >= 0", "dist_lod_atr >= 0.40",
          "vwapDistPct > 0", "adv20 >= $50M", "10:00-14:00", "stop LOD - 0.05 ATR, target 1.5R, flat 15:55"]
_STASH = {}


def _spy_newlow(df):
    """True where spy_fo is at its running minimum for the date (ties count), from per-(date, tod) context."""
    u = pd.DataFrame({"date": df["date"].astype(str).to_numpy(), "tod": df["tod"].to_numpy(np.int64),
                      "spy": df["spy_fo"].to_numpy(float)}).drop_duplicates(["date", "tod"]).sort_values(["date", "tod"])
    u["mn"] = u.groupby("date")["spy"].cummin()
    u["nl"] = (u["spy"] <= u["mn"] + 1e-12).astype(float)
    k = pd.DataFrame({"date": df["date"].astype(str).to_numpy(), "tod": df["tod"].to_numpy(np.int64)})
    return k.merge(u[["date", "tod", "nl"]], on=["date", "tod"], how="left")["nl"].to_numpy(float) == 1


def _compute(df):
    n = len(df)
    if not n or "spy_fo" not in df:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, atr, tod, dl = f("close"), f("atr_d"), f("tod"), f("dist_lod_atr")
    with np.errstate(invalid="ignore"):
        m = (f("spy_fo") <= -0.40) & _spy_newlow(df)
        m &= f("fromOpen") >= 0
        m &= dl >= 0.40
        m &= f("vwapDistPct") > 0
        m &= f("adv20") >= MIN_ADV
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = (c - dl * atr) - 0.05 * atr
        tgt = c + TARGET_MULT * (c - stop)
        m &= np.isfinite(stop) & (stop < c)
    return np.asarray(m, bool), stop, tgt


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
