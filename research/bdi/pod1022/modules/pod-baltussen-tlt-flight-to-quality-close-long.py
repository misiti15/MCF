"""pod-baltussen-tlt-flight-to-quality-close-long - TLT rest-of-day momentum into the close on a risk-off equity day
(LONG TLT at 15:00, flat 15:55).

Source: Baltussen, Da, Lammers, Martens, 'Hedging demand and market intraday momentum' / 'Market Intraday Momentum
Everywhere' (60+ futures incl. bonds: the rest-of-day return predicts the last 30 minutes; linked to gamma / LETF
hedging).
URL: https://www3.nd.edu/~zda/intramom.pdf

VARIANT of pod-cwt3-colkitt-letf-rebalance-close-long (SPY/QQQ up >= 1% from the prior close at 15:00, long into the
close). Stated change: a different asset class and mechanism - it trades the Treasury ETF on Baltussen's cross-asset
finding, gated on a cross-asset risk-off condition (SPY down while TLT is up).

Rules (plain English, LONG). SYMBOLS TLT (the mask also sees SPY rows; trades only TLT). Decision at the 15:00 bar:
  1. TLT return from the prior close >= +0.40% and >= +0.5 x TLT atr_d / prior close.
  2. SPY return from the prior close <= -0.50% (equity risk-off).
  3. TLT close > TLT session VWAP and TLT dist_hod_atr <= 0.30 (the bond bid has not faded).
  4. SPY close below SPY session VWAP at 15:00.
  Entry: the 15:00 close. Stop (GEOM S): entry - 0.15 x atr_d. Target: none, flat 15:55.
Pre-declared configurations (5): this main (+0.40%); -t025 / -t060 (TLT threshold +0.25% / +0.60%, the ATR leg
unchanged); -gld (the same rule traded on GLD); -short (mirror: short TLT when TLT <= -0.40% and <= -0.5 ATR from the
prior close, SPY >= +1.0%, TLT < VWAP with dist_lod_atr <= 0.30, SPY > VWAP; stop entry + 0.15 ATR). No tweak made.
Costs per config/default.yaml (1c + 1 bps per side, applied by the scorer). Only bars up to 15:00 are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r38_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1500, 1500)
TRADE = "TLT"
SYMBOLS = [TRADE, "SPY"]
CONTEXT = []
THR = 0.40
LAYERS = ["15:00 bar", "TLT ret from PC >= +0.40% and >= 0.5 ATR", "SPY ret from PC <= -0.50%",
          "TLT > VWAP, dist_hod <= 0.30 ATR", "SPY < VWAP", "stop 0.15 ATR, flat 15:55"]
_ST = {}


def _compute(df):
    n = len(df)
    b = U.base(df)
    c, atr, tod, pc = b["c"], b["atr"], b["tod"], b["pc"]
    with np.errstate(invalid="ignore", divide="ignore"):
        ret = (c / pc - 1) * 100
        atrp = atr / pc * 100
        spy = U.rows_at(df, "SPY", ["close", "fromOpen", "gap", "vwapDistPct"])
        sopn = spy["close"] / (1 + spy["fromOpen"] / 100)
        sret = (spy["close"] / (sopn / (1 + spy["gap"] / 100)) - 1) * 100
        m = (df["symbol"].astype(str).to_numpy() == TRADE) & (tod == 1500) & (atr > 0)
        if SIDE == "long":
            m &= (ret >= THR) & (ret >= 0.5 * atrp)
            m &= sret <= -0.50
            m &= (U.f(df, "vwapDistPct") > 0) & (U.f(df, "dist_hod_atr") <= 0.30)
            m &= spy["vwapDistPct"] < 0
            stop = c - 0.15 * atr
        else:
            m &= (ret <= -THR) & (ret <= -0.5 * atrp)
            m &= sret >= 1.0
            m &= (U.f(df, "vwapDistPct") < 0) & (U.f(df, "dist_lod_atr") <= 0.30)
            m &= spy["vwapDistPct"] > 0
            stop = c + 0.15 * atr
    return np.asarray(m, bool), stop


def mask(df):
    m, s = _compute(df)
    _ST.clear()
    _ST[id(df)] = s
    return m


def stop_price(f, i):
    s = _ST.get(id(f))
    if s is None or len(s) != len(f):
        mask(f)
        s = _ST[id(f)]
    return float(s[i])
