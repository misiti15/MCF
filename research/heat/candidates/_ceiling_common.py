"""Shared terms for the 'ceiling' candidates (GBM-distilled heat-style SHORT score). Educational only - not financial advice.

Distilled from a shallow HistGradientBoosting model fitted on TRAIN to the cross-sectionally demeaned short R.
All inputs are live-computable from 5-minute bars plus the prior daily ATR:
  cost   = round-trip cost in R = 0.08 / atr_d   (atr_d = prior 14-day daily ATR $, R = 0.25*atr_d, $0.01/share/side)
  early  = clip((120 - minutes since 09:30) / 60, 0, 2)  -> 2 at 09:30 ... 0 from 11:30 on
  atr5   = clip(atrPct, 0, 1.5)        (5-min ATR % of price)
  vw     = clip(vwapDistPct, -1.5, 2)  (% above session VWAP)
  macdH  = macdHeat (MarcoFlow component, -10..10)
  gp     = clip(gap, -3, 8); fo = clip(fromOpen, -3, 4); atrd = clip(100*atr_d/close, 0, 12)
Short score (points; higher = better short):
  core = 8 - 168*cost + 1.9*early - 6.6*atr5 + 0.9*vw + 0.2*macdH
  full = core-ish distillate with gap / fromOpen / daily-ATR% terms (weights below)
"""
import numpy as np


def short_points(df, variant="core", cost_gate=1.0):
    t = df["tod"].to_numpy()
    mins = (t // 100) * 60 + t % 100 - 570
    atr_d = df["atr_d"].to_numpy(dtype=float)
    cost = np.clip(0.08 / atr_d, 0, 0.1)
    early = np.clip((120 - mins) / 60, 0, 2)
    atr5 = np.clip(df["atrPct"].to_numpy(dtype=float), 0, 1.5)
    vw = np.clip(df["vwapDistPct"].to_numpy(dtype=float), -1.5, 2)
    mh = df["macdHeat"].to_numpy(dtype=float)
    if variant == "core":
        s = 8 - 168 * cost + 1.9 * early - 6.6 * atr5 + 0.9 * vw + 0.2 * mh
    elif variant == "full":
        gp = np.clip(df["gap"].to_numpy(dtype=float), -3, 8)
        fo = np.clip(df["fromOpen"].to_numpy(dtype=float), -3, 4)
        atrd = np.clip(atr_d / df["close"].to_numpy(dtype=float) * 100, 0, 12)
        s = (8 - 168 * cost + 1.9 * early - 6.6 * atr5 + 0.87 * vw + 0.2 * mh
             - 0.12 * gp - 0.19 * fo - 0.03 * atrd)
    elif variant == "control":  # NOT heat-style: cost + time of day only (shows where the 'edge' comes from)
        s = 8 - 168 * cost + 1.9 * early
    else:
        raise ValueError(variant)
    return np.where(cost > cost_gate, -100.0, s)
