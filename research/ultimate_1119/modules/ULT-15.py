# ULTIMATE CANDIDATE ULT-15 CONFLUENCE (research only, not enabled in any account)
# research/ultimate_1119/round2/PLAN.md sec. 3 "ULT-15"; backtest research/ultimate_1119/round2/ULT-15/RESULTS.md
# Next: only a TIER A result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-15 CONFLUENCE - 2+ round-1 triggers on a base whose own random-entry expectancy is >= 0, LONG and SHORT.

Rule (all point-in-time, at the decision 5-minute bar close; frame columns rsi = RSI(14), rsi5 = RSI(5),
buyPressure = 19-bar, dist_hod_atr / dist_lod_atr = (HOD - close) / (close - LOD) in daily ATRs, sma20_dist_pct,
upper_wick = upper-wick share of the decision bar):
  intake U2   price >= $10; |gap| < 20%; atr_d > 0; cost_r <= COST_R_MAX (LR8 stop-out round trip
              ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / u, u = 0.25 x atr_d); ADV20 floor via the YAML min_adv
              (L1: $200M long / $100M short with cost_r <= 0.05; L2: $50M with cost_r <= 0.08)
  base BL     (long) atr_d% >= 3.0; bar close 10:30-15:00; spy_fo >= 0 AND spy_r30 >= 0 (SPY up from its open and
              not falling over the last 30 min); universal long filter (skip SPY -0.30..-0.75% from open with
              spy_r30 < 0) kept - it never binds under spy_fo >= 0.
  base BS     (short) easy to borrow (account-side live: shorts.require_easy_to_borrow; backtest universe.csv flag);
              gap <= -1.0%; bar close 11:00-15:00; spy_fo <= 0 AND spy_r30 <= 0; universal short filters
              (gap >= +0.5% never with gap <= -1%; RSI5 >= 25).
  triggers    long  TL1 RSI14 crossed below 50 (this bar < 50, the bar before >= 50) within the last 3 bars AND
                        RSI14 <= 30;
                    TL2 RSI5 crossed up through 30 on this or the previous bar AND buyPressure > 0;
                    TL3 from_open_atr <= -1.0 OR dist_hod_atr >= 1.5   (from_open_atr = (close - 09:30 open) / atr_d)
              short TS1 60 <= RSI5 < 90 AND dist_lod_atr >= 0.5 AND |sma20_dist_pct| >= 1.5;
                    TS2 RSI5 of the previous bar >= 80 AND RSI5 now < previous (RSI5 slope < 0, as ULT-08) AND
                        upper_wick > 0;
                    TS3 from_open_atr >= +1.0
              A trigger COUNTS if it is true on the decision bar or one of the 2 bars before it (same session,
              exactly 5 / 10 min earlier). Signal = base AND (number of counted triggers) >= CONF.
              Honest note: the long triggers all measure "oversold", so they are correlated, not independent.
  spy_r30     = SPY % change over exactly the last 6 five-minute bars, from spy_fo; unknown -> no signal (fail safe).
  side gate   a side whose base failed the FIT random-entry gate (round2/ULT-15/base_gate.json) is OFF (SIDES_ON).
  refire      (THIN) max 2 per symbol-session, the 2nd >= REFIRE_BARS decision bars after the 1st (backtest chain:
              >= 30 min after the first lot's exit, one lot per symbol across both sides). YAML: refire true,
              refire_cooldown 0.
Two sides, one file (as ULT-05/14): LabStrategy has one side per setup, so the account carries TWO `type: lab` entries
pointing at this file; a setup name ending in "-S" / "-short" is the short side, anything else the long side.
Exit: GEOM "S": stop_price = decision close -/+ 2u (catastrophic), no target; YAML time_stop_min EXIT_MIN,
time_stop_min_r 99 (TX30 / TX45). R per 2u. Account-side: day cap 30 entries over both sides; flat 15:50 implied."""
import numpy as np

_NAME = __name__.lower()
SIDE = "short" if _NAME.endswith(("-s", "_s", "-short", "_short")) else "long"
_SGN = 1 if SIDE == "long" else -1
GEOM = "S"
# ---- fit-frozen (round2/ULT-15/fitsel.json, base_gate.json); set after the FIT grid, before any CHECK data.
# The FIT base gate FAILED for both sides at both liquidity levels (random avg R < 0 in both sub-halves), so no config
# may trade (pre-registered rule) and SIDES_ON is empty: this module never fires as frozen. CONF / EXIT_MIN / LIQ hold
# the DIAGNOSTIC ungated pick 15c (C2of3-TX45-L1) for the record; RESULTS.md: FAIL.
CONF = 2                  # triggers required (2-of-3 or 3-of-3)
EXIT_MIN = 45             # TX30 / TX45 (YAML time_stop_min)
LIQ = "L1"                # L1 / L2
SIDES_ON = ()             # sides whose base passed the FIT random-entry gate at LIQ (none did)
# ----
LIQ_LEVELS = {"L1": {"long": (200_000_000, 0.05), "short": (100_000_000, 0.05)},
              "L2": {"long": (50_000_000, 0.08), "short": (50_000_000, 0.08)}}
MIN_ADV, COST_R_MAX = LIQ_LEVELS[LIQ][SIDE]
WINDOWS = {"long": (1030, 1500), "short": (1100, 1500)}
WINDOW = WINDOWS[SIDE]
ATR_PCT_MIN = 3.0
GAP_SHORT_MAX = -1.0
UNIV_BAND = (-0.75, -0.30)
RSI5_SHORT_MIN = 25.0
TRIG_BARS = 3
THIN = True
REFIRE_BARS = 15 if EXIT_MIN == 45 else 12
MAX_PER_DAY = 2
LAYERS = ([
    f"intake: price >= $10, |gap| < 20%, cost_r <= {COST_R_MAX:g}, ADV20 >= ${MIN_ADV / 1e6:.0f}M (YAML min_adv)",
] + (["base: daily ATR >= 3.0% of price", "base: SPY up from its open and not falling over 30 min",
      f"{CONF} of 3: RSI14 cross < 50 to <= 30 | RSI5 up-cross 30 with buy pressure | >= 1 ATR below open or "
      ">= 1.5 ATR off the high (each within 3 bars)"] if _SGN > 0 else
     ["base: easy to borrow, gap <= -1.0%, RSI(5) >= 25", "base: SPY down from its open and not rising over 30 min",
      f"{CONF} of 3: RSI5 60-90 >= 0.5 ATR off the low, away from SMA20 | RSI5 >= 80 turning down with an upper wick | "
      ">= 1 ATR above the open (each within 3 bars)"]) + [
    f"window: bar close {WINDOW[0]}-{WINDOW[1]} ET",
    f"exit: {EXIT_MIN}-min time exit, 2R catastrophic stop",
])


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
    t = np.asarray(tod, dtype=float)
    return (t // 100) * 60 + t % 100


def _lag(x, k, key, mins):
    """x k rows earlier in the same symbol-session, only when that row is exactly 5*k minutes earlier; else NaN."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    out = np.full(n, np.nan)
    if n <= k:
        return out
    px = np.r_[np.full(k, np.nan), x[:-k]]
    pk = np.r_[np.full(k, -1), key[:-k]]
    pm = np.r_[np.full(k, np.nan), mins[:-k]]
    ok = (pk == key) & (mins - pm == 5 * k)
    out[ok] = px[ok]
    return out


def _within(b, key, mins, bars=TRIG_BARS):
    """b true on this bar or one of the bars-1 bars before it (same session, exact 5-min spacing)."""
    out = np.asarray(b, bool).copy()
    for k in range(1, bars):
        out |= _lag(b.astype(float), k, key, mins) == 1.0
    return out


def features(df) -> dict:
    """Point-in-time inputs and the six triggers at each decision bar close (shared with the backtest bt.py)."""
    import pandas as pd
    n = len(df)
    c = lambda k: df[k].to_numpy(dtype=float)   # noqa: E731
    px, atr, tod = c("close"), c("atr_d"), c("tod")
    key = pd.factorize(_keys(df))[0]
    mins = _minutes(tod)
    fo = c("spy_fo") if "spy_fo" in df.columns else np.full(n, np.nan)
    rsi, r5, bp = c("rsi"), c("rsi5"), c("buyPressure")
    with np.errstate(invalid="ignore", divide="ignore"):
        one = 0.01 + px * 1e-4
        cost_r = (one * _tod_mult(tod) + one + 0.02) / (0.25 * atr)
        p30 = _lag(fo, 6, key, mins)
        r30 = ((1 + fo / 100) / (1 + p30 / 100) - 1) * 100
        atrp = atr / px * 100
        foa = (px - px / (1 + c("fromOpen") / 100)) / atr
        rsi_p, r5_p = _lag(rsi, 1, key, mins), _lag(r5, 1, key, mins)
        # long triggers
        cr50 = (rsi < 50) & (rsi_p >= 50)
        tl1 = _within(cr50, key, mins) & (rsi <= 30)
        up30 = (r5 >= 30) & (r5_p < 30)
        tl2 = _within(up30, key, mins, 2) & (bp > 0)
        tl3 = (foa <= -1.0) | (c("dist_hod_atr") >= 1.5)
        # short triggers
        ts1 = (r5 >= 60) & (r5 < 90) & (c("dist_lod_atr") >= 0.5) & (np.abs(c("sma20_dist_pct")) >= 1.5)
        ts2 = (r5_p >= 80) & (r5 < r5_p) & (c("upper_wick") > 0)
        ts3 = foa >= 1.0
        intake = (px >= 10) & (np.abs(c("gap")) < 20) & (atr > 0)
    w = {k: _within(v, key, mins) for k, v in (("TL1", tl1), ("TL2", tl2), ("TL3", tl3),
                                               ("TS1", ts1), ("TS2", ts2), ("TS3", ts3))}
    nl = w["TL1"].astype(int) + w["TL2"].astype(int) + w["TL3"].astype(int)
    ns = w["TS1"].astype(int) + w["TS2"].astype(int) + w["TS3"].astype(int)
    return {"tod": tod, "close": px, "cost_r": cost_r, "intake": intake, "spy_fo": fo, "spy_r30": r30,
            "atrp": atrp, "gap": c("gap"), "rsi5": r5, "foa": foa, "n_long": nl, "n_short": ns, **w}


def base(r, sgn, cost_max) -> np.ndarray:
    """Base BL / BS (incl. intake, universal filters and the side window); no ADV (YAML min_adv / backtest)."""
    tod, fo, r30 = r["tod"], r["spy_fo"], r["spy_r30"]
    with np.errstate(invalid="ignore"):
        ok = r["intake"] & (r["cost_r"] <= cost_max) & np.isfinite(fo) & np.isfinite(r30)
        if sgn > 0:
            univ = ~((fo >= UNIV_BAND[0]) & (fo <= UNIV_BAND[1]) & (r30 < 0))
            return (ok & univ & (r["atrp"] >= ATR_PCT_MIN) & (fo >= 0) & (r30 >= 0)
                    & (tod >= WINDOWS["long"][0]) & (tod <= WINDOWS["long"][1]))
        return (ok & (r["gap"] <= GAP_SHORT_MAX) & (r["gap"] < 0.5) & (r["rsi5"] >= RSI5_SHORT_MIN)
                & (fo <= 0) & (r30 <= 0) & (tod >= WINDOWS["short"][0]) & (tod <= WINDOWS["short"][1]))


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
    if "spy_fo" not in df.columns or SIDE not in SIDES_ON:   # fail safe / side gated off by the FIT base gate
        return np.zeros(len(df), bool)
    r = features(df)
    m = base(r, _SGN, COST_R_MAX) & ((r["n_long"] if _SGN > 0 else r["n_short"]) >= CONF)
    return _thin(m, df) if THIN else m


def stop_price(f, i) -> float:
    """GEOM "S": catastrophic stop 2u = 0.5 daily ATR beyond the decision close."""
    return float(f["close"].iloc[i]) - _SGN * 2 * 0.25 * float(f["atr_d"].iloc[i])
