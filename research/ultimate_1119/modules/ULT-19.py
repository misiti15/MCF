# ULTIMATE CANDIDATE ULT-19 LR-LITE (research only, not enabled in any account)
# research/ultimate_1119/round2/PLAN.md sec. 3 "ULT-19"; backtest research/ultimate_1119/round2/ULT-19/RESULTS.md
# Next: only a TIER A result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-19 LR-LITE - shrunk linear score on persistent factors, LONG and SHORT, 09:50-15:00.

Score (one model, side as a signed design, s = +1 long / -1 short), all point-in-time at the 5-min decision bar close:
  features  5 time-block dummies (bar close 0950-1029, 1030-1129, 1130-1259, 1300-1359, 1400-1500);
            s x gap %; s x fromOpen in daily-ATR units; s x vwapDist in daily-ATR units; atr_d % of price; cost_r;
            s x spy_fo; s x spy_r30 (SPY change over the last 30 min from spy_fo; NaN before 10:20 -> 0);
            s x (RSI5 - 50); s x (RSI14 - 50)
  scaling   signed features / training sd (natural zero kept); unsigned (atr_d %, cost_r) (x - mean) / sd; dummies raw;
            clip +-5; NaN -> 0
  model     ridge alpha 1e5 on FIT (target: after-cost R of a 45-min time exit, 0.25-dATR units, winsorised +-4);
            a coefficient whose sign differs between fit sub-halves A and B is set to 0 (stability filter)
  rule      pred(own side) > TAU and pred(own side) >= pred(other side) (the better side per name)
Intake (U2): price >= $10; |gap| < 20%; atr_d > 0; cost_r <= COST_R_MAX (LR8 stop-out round trip / (0.25 x atr_d));
            ADV20 >= MIN_ADV via the YAML min_adv.
Universal filters: no short if gap >= +0.5% or RSI5 < 25; no long while SPY is -0.30..-0.75% from its open and
            spy_r30 < 0. Shorts only in easy-to-borrow names (account universe; not visible to the module).
Refire (THIN): first hit, a later hit >= 15 bars (45-min hold + 30-min cooldown) after the previous one, max 2 per
            symbol-session. YAML: refire true, refire_cooldown 0.
Two sides, one file: the side comes from the setup name (ending in "-S"/"-short" = short side), e.g. ULT-19-L / ULT-19-S.
Exit: GEOM "S": stop_price = 2 x 0.25 daily ATR catastrophic stop beyond the decision close, no target;
      YAML time_stop_min 45 (45-min time exit). Flat 15:50 implied (last entry 15:00 + 45 min).
Account-side (not in the module): at most 3 new entries per 5-min bar (highest score first in research), session cap
2k entries over both sides. The fitted coefficients, scaler, TAU and universe are frozen in ULT-19_model.json."""
import json
from pathlib import Path

import numpy as np

_NAME = __name__.lower()
SIDE = "short" if _NAME.endswith(("-s", "_s", "-short", "_short")) else "long"
_SGN = 1 if SIDE == "long" else -1
GEOM = "S"
WINDOW = (950, 1500)
HOLD_MIN = 45
REFIRE_BARS, MAX_PER_DAY = 15, 2
THIN = True
FEATURES = ["tb0950", "tb1030", "tb1130", "tb1300", "tb1400", "gap", "fo_datr", "vd_datr", "atr_pct", "cost_r",
            "spy_fo", "spy_r30", "rsi5c", "rsi14c"]
SIGNED = np.array([0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1], bool)
DUMMY = np.array([1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0], bool)
TB_EDGES = (950, 1030, 1130, 1300, 1400, 1501)

MODEL_FILE = Path(__file__).resolve().parent / "ULT-19_model.json"
MODEL = json.loads(MODEL_FILE.read_text()) if MODEL_FILE.exists() else None
MIN_ADV = float(MODEL["min_adv"]) if MODEL else 50e6
COST_R_MAX = float(MODEL["cost_r_max"]) if MODEL else 0.10
TAU = float(MODEL["tau"]) if MODEL else float("inf")
LAYERS = [
    f"intake: price >= $10, |gap| < 20%, cost_r <= {COST_R_MAX:g}, ADV20 >= ${MIN_ADV / 1e6:g}M (YAML min_adv)",
    "universal filters (short: gap < +0.5%, RSI5 >= 25; long: not SPY -0.30..-0.75% from open with spy_r30 < 0)",
    f"LR-LITE score ({'long' if _SGN > 0 else 'short'} side) > {TAU:.4g} and >= the other side's score",
    f"window: bar close {WINDOW[0]}-{WINDOW[1]} ET", f"exit: {HOLD_MIN}-min time exit, 2R catastrophic stop",
]


def _tod_mult(tod):
    return np.where(tod < 935, 3.8, np.where(tod < 950, 2.1, np.where(tod < 1030, 1.4, 1.0)))


def _keys(df):
    import pandas as pd
    if "date" in df:
        day = df["date"].astype(str).to_numpy()
    else:
        day = pd.DatetimeIndex(df.index).strftime("%Y-%m-%d").to_numpy()
    if "symbol" in df:
        day = df["symbol"].astype(str).to_numpy() + "|" + day
    return day


def _minutes(tod):
    tod = np.asarray(tod, float)
    return (tod // 100) * 60 + tod % 100


def spy_r30(df) -> np.ndarray:
    """SPY % change over the last 30 minutes from spy_fo: (1 + fo_t) / (1 + fo_{t-30}) - 1, using only rows of the
    same session with bar close >= 09:50 (as in the research frames); NaN before 10:20 or without the t-30 row."""
    import pandas as pd
    fo = df["spy_fo"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    key = _keys(df)
    m = _minutes(tod)
    s = pd.Series(np.where(tod >= 950, fo, np.nan), index=pd.MultiIndex.from_arrays([key, m]))
    s = s[~s.index.duplicated()]
    lag = s.reindex(pd.MultiIndex.from_arrays([key, m - 30])).to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return ((1 + fo / 100) / (1 + lag / 100) - 1) * 100


def raw(df) -> dict:
    """Raw (unsigned, unscaled) inputs and intake pieces, shared with the backtest (bt.py imports this)."""
    def c(k):
        return df[k].to_numpy(dtype=float)
    px, atr, tod = c("close"), c("atr_d"), c("tod")
    with np.errstate(invalid="ignore", divide="ignore"):
        u = 0.25 * atr
        one = 0.01 + px * 1e-4
        cost_r = (one * _tod_mult(tod) + one + 0.02) / u
        fo, vd = c("fromOpen"), c("vwapDistPct")
        o = px / (1 + fo / 100)
        vw = px / (1 + vd / 100)
        out = {"tod": tod, "close": px, "atr_d": atr, "gap": c("gap"), "fo_datr": (px - o) / atr,
               "vd_datr": (px - vw) / atr, "atr_pct": atr / px * 100, "cost_r": cost_r, "spy_fo": c("spy_fo"),
               "spy_r30": spy_r30(df), "rsi5": c("rsi5"), "rsi14": c("rsi")}
    return out


def intake(r, cost_r_max) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return ((r["close"] >= 10) & (np.abs(r["gap"]) < 20) & (r["atr_d"] > 0) & (r["cost_r"] <= cost_r_max)
                & np.isfinite(r["cost_r"]) & np.isfinite(r["spy_fo"]))   # no market context -> no signal


def side_ok(r, sgn) -> np.ndarray:
    """Universal filters for one side (sgn +1 long / -1 short)."""
    with np.errstate(invalid="ignore"):
        if sgn < 0:
            return ~((r["gap"] >= 0.5) | (r["rsi5"] < 25) | ~np.isfinite(r["rsi5"]))
        fo, r30 = r["spy_fo"], r["spy_r30"]
        return ~((fo <= -0.30) & (fo >= -0.75) & (r30 < 0))


def design(r, sgn) -> np.ndarray:
    """Unscaled design matrix (n x 14) for side sgn."""
    tod = r["tod"]
    cols = [((tod >= a) & (tod < b)).astype(float) for a, b in zip(TB_EDGES[:-1], TB_EDGES[1:])]
    cols += [sgn * r["gap"], sgn * r["fo_datr"], sgn * r["vd_datr"], r["atr_pct"], r["cost_r"], sgn * r["spy_fo"],
             sgn * r["spy_r30"], sgn * (r["rsi5"] - 50), sgn * (r["rsi14"] - 50)]
    return np.column_stack(cols)


def scale(X, mean, sd) -> np.ndarray:
    """signed: x / sd; unsigned non-dummy: (x - mean) / sd; dummies raw; clip +-5; NaN -> 0."""
    mean, sd = np.asarray(mean, float), np.asarray(sd, float)
    mu = np.where(SIGNED | DUMMY, 0.0, mean)
    s = np.where(DUMMY, 1.0, sd)
    with np.errstate(invalid="ignore"):
        Z = np.clip((X - mu) / s, -5, 5)
    return np.nan_to_num(Z, nan=0.0)


def score(r, sgn, model) -> np.ndarray:
    return scale(design(r, sgn), model["mean"], model["sd"]) @ np.asarray(model["w"], float)


def _thin(m, df):
    hit = np.flatnonzero(m)
    if not len(hit):
        return m
    key = _keys(df)
    out = np.zeros(len(m), bool)
    last, n, cur = -10**9, 0, None
    for i in hit:
        if key[i] != cur:
            cur, last, n = key[i], -10**9, 0
        if n < MAX_PER_DAY and i - last >= REFIRE_BARS:
            out[i] = True; last = i; n += 1
    return out


def mask(df) -> np.ndarray:
    if MODEL is None or "spy_fo" not in df.columns:   # fail safe: no frozen model / no market context -> no signal
        return np.zeros(len(df), bool)
    r = raw(df)
    own, oth = score(r, _SGN, MODEL), score(r, -_SGN, MODEL)
    tod = r["tod"]
    with np.errstate(invalid="ignore"):
        m = (intake(r, COST_R_MAX) & side_ok(r, _SGN) & (own > TAU) & (own >= oth)
             & (tod >= WINDOW[0]) & (tod <= WINDOW[1]))
    return _thin(m, df) if THIN else m


def stop_price(f, i) -> float:
    """GEOM "S": catastrophic stop 2R = 0.5 daily ATR beyond the decision close."""
    return float(f["close"].iloc[i]) - _SGN * 2 * 0.25 * float(f["atr_d"].iloc[i])
