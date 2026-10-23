"""pod-cwt3-colkitt-letf-rebalance-close-long - Front-run leveraged-ETF end-of-day rebalancing: index long into the
close on big up days.

Source: Chat With Traders EP313, Doug Colkitt (front-running mechanical ETP end-of-day rebalancing) [~00:16:21].
URL: https://chatwithtraders.com/313

VARIANT: neighbour pod-raschke-trend-day-last-hour-long triggers on trend-day structure; this one triggers only on the
size of the return from the PRIOR CLOSE (the 2x / 3x ETF rebalancing need is about L(L-1) x AUM x r, measured from the
prior close, not the open) and enters later.

Rules (plain English, LONG). SYMBOLS = SPY, QQQ. Decision at the 15:00 5m bar close (the 14:55-15:00 bar):
  (a) return from the prior close (close / prior close - 1) >= +1.0%;
  (b) price > session VWAP;
  (c) price within 0.5 x ATR14(5m) x 4 (= 2 x ATR14(5m)) of the session high (no collapsed rally);
  (d) not a half-day session (half days have no 15:00 bar in the frames, so they never qualify).
  Entry: the 15:00 bar close. Stop (GEOM S): a fixed 0.5 x ATR14(daily) x 0.25 (= 0.125 x daily ATR) below the entry.
  Exit: 15:55 bar close (the scorer's flat time; the rebalance prints at the close). No target.
Pre-declared tests from the source (configurations tried are reported, not picked): thresholds +0.75 / +1.0 / +1.5%
(companions -t075 / -t150), and the mirror short at <= -1.0% (companion -short). The 15:30 entry cannot be scored
(the scorer clips entries to <= 15:00). Main = +1.0% long.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import numpy as np

SIDE = "long"
GEOM = "S"
WINDOW = (1500, 1500)
SYMBOLS = ["SPY", "QQQ"]
CONTEXT = []
THR = 1.0
LAYERS = ["15:00 bar", "return from prior close >= +1.0%", "close > VWAP", "within 2 x ATR5 of the HOD",
          "stop 0.125 daily ATR, exit 15:55"]

_ST = {}


def _compute(df):
    n = len(df)
    g = lambda x: df[x].to_numpy(float) if x in df else np.full(n, np.nan)
    c, atr, tod = g("close"), g("atr_d"), df["tod"].to_numpy(np.int64)
    with np.errstate(invalid="ignore", divide="ignore"):
        opn = c / (1 + g("fromOpen") / 100)
        pc = opn / (1 + g("gap") / 100)
        ret = (c / pc - 1) * 100
        a5 = g("atrPct") / 100 * c
        hod = c + g("dist_hod_atr") * atr
        lod = c - g("dist_lod_atr") * atr
        vd = g("vwapDistPct")
        m = tod == 1500
        if SIDE == "long":
            m &= (ret >= THR) & (vd > 0) & (hod - c <= 2.0 * a5)
            stop = c - 0.125 * atr
        else:
            m &= (ret <= -THR) & (vd < 0) & (c - lod <= 2.0 * a5)
            stop = c + 0.125 * atr
        m &= np.isfinite(stop) & (atr > 0)
    return m, stop, np.full(n, np.nan)


def mask(df) -> np.ndarray:
    m, stop, tgt = _compute(df)
    _ST.clear()
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)


def _get(f):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])
