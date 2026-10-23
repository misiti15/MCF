"""pod-cwt3-breitstein-oversold-largecap-open-print-long - Buy the open in a large cap that has fallen 5 days straight
and gaps far more than the index (LONG).

Source: Chat With Traders EP236, Lance Breitstein (The Ultimate Day Trader Pt. 3; fade the opening sell imbalance in a
relatively oversold large cap) [~00:27:00].
URL: https://chatwithtraders.com/236

VARIANT, parent cwt-a-a5-open-print-fv-fade (CWT19: both sides, every name, |open - beta fair open| >= 0.3-0.75 ATR,
failed). Stated changes: long only; a multi-day oversold precondition (5 straight down days, 5-day return <= -15%);
large caps only; gap relative to SPY's; no waiting for a reclaim.

Rules (plain English, LONG). Daily values only from completed days (research/history2y daily table):
  Universe: top-300 names by 20-day dollar volume as of D-1 (rank over the daily table), prior close >= $20.
  (a) D-5..D-1 all down closes (each close below the one before) and the 5-day return close D-1 / close D-6 - 1
      <= -15% (the source's range is -10/-15/-20%; the middle value is used, no tweak). The six closes must span
      <= 10 calendar days.
  (b) today's gap <= -3% and <= 2 x SPY's gap (the stock gaps much more than the market);
  (c) SPY gap > -1.0%;
  (d) no earnings on D0 or D-1 (the scorer universe already applies the live 4-day earnings blackout).
  Entry deviation (scorer limit): the source buys the 09:30 opening print; the pod1022 scorer can only enter at a bar
  close from 09:50, so this module enters at the 09:50 bar close (the first scorable bar) with the source's levels.
  There is therefore no opening-auction slippage term; the standard costs x1.4 (pre-10:30) apply.
  Stop (GEOM S): opening print - 0.5 x ATR14(daily) (the source's 1.0 x ATR x 0.5). A day already below that stop
  at 09:50 is skipped. Target: the prior-day close (gap fill); a day already at or above it is skipped.
  Exit deviation: the source's 10:30 time exit cannot be modelled (no time exit in the scorer); unfilled trades are
  held to 15:55. Costs in (scorer).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (950, 950)
CONTEXT = []
LAYERS = ["top-300 by adv20 (D-1), price >= $20", "5 straight down closes, 5-day return <= -15%",
          "gap <= -3% and <= 2x SPY gap", "SPY gap > -1%", "entry 09:50 close (open-print proxy)",
          "stop open - 0.5 ATR, target prior close, else 15:55"]

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
    if "d" in _CACHE:
        return _CACHE["d"]
    d = _lib().daily()[["symbol", "date", "open", "close", "adv20"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    g = d.groupby("symbol", sort=False)
    c = d["close"]
    cs = [g["close"].shift(k) for k in range(1, 6)]
    down5 = (c < cs[0]) & (cs[0] < cs[1]) & (cs[1] < cs[2]) & (cs[2] < cs[3]) & (cs[3] < cs[4])
    d["down5"] = down5.astype(float)
    d["ret5"] = (c / cs[4] - 1) * 100
    dt = pd.to_datetime(d["date"])
    sp = (dt - dt.groupby(d["symbol"]).shift(5)).dt.days
    d.loc[~(sp <= 10), ["down5", "ret5"]] = np.nan
    d["rank"] = d.groupby("date")["adv20"].rank(ascending=False, method="first")
    d["next_date"] = g["date"].shift(-1)
    d = d[(pd.to_datetime(d["next_date"]) - dt).dt.days <= 5]
    out = d[["symbol", "next_date", "close", "down5", "ret5", "rank"]].rename(columns={"next_date": "date", "close": "pc"})
    _CACHE["d"] = out
    return out


def compute(df):
    n = len(df)
    if n == 0:
        return np.zeros(0, bool), np.zeros(0), np.zeros(0)
    key = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "date": df["date"].to_numpy()})
    dg = key.merge(_daily(), on=["symbol", "date"], how="left")
    f = lambda k: df[k].to_numpy(float)
    c, gap, fo, atr = f("close"), f("gap"), f("fromOpen"), f("atr_d")
    spy = df.loc[df["symbol"].astype(str) == "SPY", ["date", "gap"]].drop_duplicates("date")
    if spy.empty:
        d = _lib().daily()
        d = d[d["symbol"].astype(str) == "SPY"].sort_values("date")
        spy = pd.DataFrame({"date": d["date"], "gap": (d["open"] / d["close"].shift(1) - 1) * 100})
    sg = pd.DataFrame({"date": df["date"].to_numpy()}).merge(spy.rename(columns={"gap": "sg"}), on="date",
                                                             how="left")["sg"].to_numpy(float)
    pc = dg["pc"].to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        o = c / (1 + fo / 100)
        stop = o - 0.5 * atr
        m = (dg["rank"].to_numpy(float) <= 300) & (pc >= 20)
        m &= (dg["down5"].to_numpy(float) == 1) & (dg["ret5"].to_numpy(float) <= -15)
        m &= (gap <= -3) & (gap <= 2 * sg) & (sg > -1.0)
        m &= (stop < c) & (pc > c)
    return np.asarray(m, bool), stop, pc


def mask(df) -> np.ndarray:
    m, stop, tgt = compute(df)
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
