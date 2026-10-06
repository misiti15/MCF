"""Shared helper for the `regime_*` heat candidates. Educational only - not financial advice.

A regime heat score is a transparent weighted sum of MarcoFlow's heat components plus two raw terms,
computed per 5-minute bar, then gated by at most two regime terms:
    base  = sum_k w_k * component_k + w_fo * clip(fromOpen%, -3, 3) * 5 + w_gap * clip(gap%, -5, 5) * 3
    long  score =  base - k_cost * cost100        (enter long  when score >= T)
    short score = -base - k_cost * cost100        (enter short when score >= T; exported negated, so
                                                    the file's score <= SHORT_AT = -T)
    cost100 = 100 * 0.08 / atr_d  (round-trip cost in R x 100, from the PRIOR day's daily ATR in $;
                                    a tradability term: it favours names whose $ATR dwarfs the 8c cost)
Regime gates (NaN outside, so the bar never qualifies):
    1. time-of-day window on the bar-close HHMM (tod)
    2. optional sign gate on fromOpen (stock above/below today's open) or on the opening gap.
All inputs are causal and available live from 5-minute bars plus the prior daily ATR.
"""
import numpy as np

COMP = ["volumeHeat", "rsiHeat", "momentumHeat", "priceActionHeat", "trendHeat", "macdHeat", "vwapHeat"]


def regime_score(df, side, w, tod_from, tod_to, gate=None, k_cost=0.0, use_heat=False):
    """w: dict of weights over COMP and 'fo', 'gap' (long orientation). use_heat: base = original heat."""
    g = lambda c: np.nan_to_num(df[c].to_numpy(dtype=np.float64))
    if use_heat:
        base = g("heat")
    else:
        base = np.zeros(len(df))
        for c in COMP:
            if w.get(c):
                base += w[c] * g(c)
        if w.get("fo"):
            base += w["fo"] * np.clip(g("fromOpen"), -3, 3) * 5
        if w.get("gap"):
            base += w["gap"] * np.clip(g("gap"), -5, 5) * 3
    cost100 = 8.0 / df["atr_d"].to_numpy(dtype=np.float64)
    s = (base if side == "long" else -base) - k_cost * cost100
    tod = df["tod"].to_numpy()
    ok = (tod >= tod_from) & (tod <= tod_to) & np.isfinite(s)
    if gate == "fo+":
        ok &= g("fromOpen") > 0
    elif gate == "fo-":
        ok &= g("fromOpen") < 0
    elif gate == "gap+":
        ok &= g("gap") > 0
    elif gate == "gap-":
        ok &= g("gap") < 0
    s = np.where(ok, s, np.nan)
    return s if side == "long" else -s
