# ULTIMATE CANDIDATE ULT-32 FLOW-DIP (research only, not enabled in any account)
# research/ultimate_1119/round4/PLAN.md sec. 3 "ULT-32"; backtest research/ultimate_1119/round4/ULT-32/RESULTS.md
# Next: only a TIER A result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-32 FLOW-DIP - union of the two out-of-sample-stable "flow, not information" dips, LONG. CHECK-INFORMED.

Legs (all point-in-time at the decision 5-minute bar close; indicators ret3 / ret12 / di_diff7 / atr_d_pct via
mcf.research.arena.indicators.compute on the frame passed in, rsi = RSI(14), buyPressure = 19-bar frame columns):
  E  (NM-ETF WB4, exact)  universe W = WB4 ETF list (124), min_adv $95M, cost_r <= 0.10, bar close 14:00-15:00;
                          ret3 <= -0.75% AND di_diff7 >= -5 AND ret12 >= -1.0% AND atr_d_pct >= 3.5967583179473883.
                          GEOM t05s1.
  M  (ST7 collapse, large caps) non-fund stocks (STOCKS), ADV20 >= ADV_MD, price >= $20, cost_r <= 0.08,
                          bar close 10:15-15:00; RSI14 of the bar exactly 5 min earlier (same session) >= 50 AND RSI14
                          now <= RMAX; fromOpen <= -min(1.0%, 0.30 x atr_d%); buyPressure > 0. GEOM t1s1.
  D  (WB4-A dip, same large caps) bar close 14:00-15:00; ret3 <= -0.21 x atr_d% AND ret12 >= -0.28 x atr_d% AND
                          di_diff7 >= -5; cost_r <= 0.08. GEOM t05s1. Only when D_ON.
Intake (all legs): price >= $10; |gap| < 20%; atr_d > 0; cost_r = LR8 stop-out round trip
  ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / u, u = 0.25 x atr_d.
Universal long filter: skip while SPY is -0.30..-0.75% from its open AND SPY's 30-min change < 0 (YAML
  `context: [spy_fo]`; no SPY context -> no signal, fail safe).
LIVE: one YAML entry per leg, all pointing at this file; the leg is read from the setup name's suffix
  ("...-E" / "...-M" / "...-D"; LabStrategy loads the module as `lab_<name>`), else LEG_DEFAULT. Per entry:
  E: symbols: module (= W), min_adv 95e6, window [1400, 1500], geom t05s1.
  M: symbols: module (= STOCKS), min_adv ADV_MD, window [1015, 1500], geom t1s1.
  D: symbols: module (= STOCKS), min_adv ADV_MD, window [1400, 1500], geom t05s1.
  All: context [spy_fo], refire true, refire_cooldown 0, time_stop_min 45, time_stop_min_r 99.
Account-side (not in the module): earnings blackout +-4 trading days on M and D (the live universe
  `earnings_blackout_days: 4` already applies it to every name); one lot per symbol across legs; day cap 30.
Refire (THIN): max 2 per symbol-session, the 2nd >= REFIRE_BARS decision bars after the 1st (backtest chain is
  stricter: >= 30 min after the first lot's EXIT)."""
import json
from pathlib import Path

import numpy as np

SIDE = "long"
# ---- fit-frozen pick 32f (round4/ULT-32/fitsel.json, frozen 2026-11-19 before any CHECK data)
ADV_MD = 500e6
RMAX = 30.0
D_ON = True
# ----
LEG_DEFAULT = "EMD"
WIN = {"E": (1400, 1500), "M": (1015, 1500), "D": (1400, 1500)}
GEOMS = {"E": "t05s1", "M": "t1s1", "D": "t05s1"}
COST_R_MAX = {"E": 0.10, "M": 0.08, "D": 0.08}
E_RET3, E_RET12, E_DI, E_ATR = -0.75, -1.0, -5.0, 3.5967583179473883
D_RET3_K, D_RET12_K, D_DI = -0.21, -0.28, -5.0
RSI_PREV_MIN, FO_PCT, FO_K = 50.0, 1.0, 0.30
ADV_E, PX_MD = 95e6, 20.0
UNIV_BAND = (-0.75, -0.30)
REFIRE_BARS, MAX_PER_DAY = 6, 2
THIN = True
_U = json.loads((Path(__file__).resolve().parent / "ULT-32_symbols.json").read_text())
W = frozenset(_U["W"])
FUNDS = frozenset(_U["FUNDS"])
STOCKS = frozenset(_U["STOCKS"])


def _leg_from_name(name):
    for suf in ("-E", "-M", "-D"):
        if str(name).endswith(suf):
            return suf[1]
    return LEG_DEFAULT


LEG = _leg_from_name(__name__)
SYMBOLS = (W if LEG == "E" else STOCKS) if len(LEG) == 1 else (W | STOCKS)
GEOM = GEOMS[LEG] if len(LEG) == 1 else "t05s1"
LAYERS = [
    "leg E: WB4 ETF list, ADV20 >= $95M, 14:00-15:00: 15-min return <= -0.75%, 60-min return >= -1.0%, "
    "+DI(7) - -DI(7) >= -5, daily ATR >= 3.6% of price; exit +0.5R / -1R",
    f"leg M: stocks (no funds) ADV20 >= ${ADV_MD / 1e6:.0f}M, price >= $20, 10:15-15:00: RSI(14) >= 50 on the previous "
    f"5-min bar and <= {RMAX:g} now; down >= min(1.0%, 0.30 x daily ATR%) from the open; 19-bar buy pressure > 0; "
    "exit +1R / -1R",
    ("leg D: same stocks, 14:00-15:00: 15-min return <= -0.21 x daily ATR%, 60-min return >= -0.28 x daily ATR%, "
     "+DI(7) - -DI(7) >= -5; exit +0.5R / -1R" if D_ON else "leg D: off"),
    "intake: price >= $10, |gap| < 20%, cost_r <= 0.10 (E) / 0.08 (M, D)",
    "skip while SPY is -0.30..-0.75% from its open and falling over 30 min",
    "account: earnings blackout +-4 trading days (M, D); one lot per symbol; day cap 30; 45-min time exit",
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


def _lag(x, k, key, mins):
    """x k rows earlier in the same symbol-session, only when that row is exactly 5*k minutes earlier; else NaN."""
    n = len(x)
    out = np.full(n, np.nan)
    if n <= k:
        return out
    px = np.r_[np.full(k, np.nan), x[:-k]]
    pk = np.r_[np.full(k, None, dtype=object), key[:-k]]
    pm = np.r_[np.full(k, np.nan), mins[:-k]]
    ok = (pk == key) & (mins - pm == 5 * k)
    out[ok] = px[ok]
    return out


def spy_r30(df) -> np.ndarray:
    """SPY % change over the last 30 minutes from spy_fo (same session, bar closes >= 09:50); NaN without the t-30 row."""
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


def universe_flags(df, px, adv_md=None):
    """(is_W, is_MD) per row. Backtest: symbol + adv20 columns. Live: no symbol / adv20 -> the YAML entry decides
    (symbols: module + min_adv); price >= $20 is always applied to the M / D legs."""
    adv_md = ADV_MD if adv_md is None else adv_md
    n = len(df)
    if "symbol" in df:
        sym = df["symbol"].astype(str).to_numpy()
        inw = np.array([s in W for s in sym])
        stk = np.array([(s in STOCKS) and (s not in FUNDS) for s in sym])
    else:
        inw = np.full(n, "E" in LEG and len(LEG) == 1)
        stk = np.full(n, LEG in ("M", "D"))
    adv = df["adv20"].to_numpy(dtype=float) if "adv20" in df else np.full(n, np.inf)
    with np.errstate(invalid="ignore"):
        return inw & (adv >= ADV_E), stk & (adv >= adv_md) & (px >= PX_MD)


def features(df, adv_md=None) -> dict:
    """Point-in-time inputs at each decision bar close (shared with the backtest: bt.py imports this)."""
    from mcf.research.arena.indicators import compute
    x = compute(df, names=["atr_d_pct", "di_diff7", "ret3", "ret12"], context=False)
    c = lambda k: df[k].to_numpy(dtype=float)
    px, atr, tod, rsi = c("close"), c("atr_d"), c("tod"), c("rsi")
    key = _keys(df).astype(object)
    has_spy = "spy_fo" in df.columns
    fo = c("spy_fo") if has_spy else np.full(len(df), np.nan)
    r30 = spy_r30(df) if has_spy else np.full(len(df), np.nan)
    is_w, is_md = universe_flags(df, px, adv_md)
    with np.errstate(invalid="ignore", divide="ignore"):
        one = 0.01 + px * 1e-4
        cost_r = (one * _tod_mult(tod) + one + 0.02) / (0.25 * atr)
        atrp = atr / px * 100
        intake = (px >= 10) & (np.abs(c("gap")) < 20) & (atr > 0) & np.isfinite(fo)
        univ_ok = ~((fo >= UNIV_BAND[0]) & (fo <= UNIV_BAND[1]) & (r30 < 0))
    return {"tod": tod, "close": px, "rsi": rsi, "rsi_prev": _lag(rsi, 1, key, _minutes(tod)),
            "fromOpen": c("fromOpen"), "fo_thr": -np.minimum(FO_PCT, FO_K * atrp), "bp": c("buyPressure"),
            "ret3": x["ret3"].to_numpy(float), "ret12": x["ret12"].to_numpy(float), "di7": x["di_diff7"].to_numpy(float),
            "atrp_ind": x["atr_d_pct"].to_numpy(float), "atrp": atrp, "cost_r": cost_r, "intake": intake,
            "univ_ok": univ_ok, "is_w": is_w, "is_md": is_md, "spy_fo": fo, "spy_r30": r30}


def trig_E(r):
    a = r["atrp_ind"]
    with np.errstate(invalid="ignore"):
        return ((r["ret3"] <= E_RET3) & (r["di7"] >= E_DI) & (r["ret12"] >= E_RET12) & (a >= E_ATR)
                & (r["cost_r"] <= COST_R_MAX["E"]))


def trig_M(r, rmax=None):
    rmax = RMAX if rmax is None else rmax
    with np.errstate(invalid="ignore"):
        return ((r["rsi_prev"] >= RSI_PREV_MIN) & (r["rsi"] <= rmax) & (r["fromOpen"] <= r["fo_thr"]) & (r["bp"] > 0)
                & (r["cost_r"] <= COST_R_MAX["M"]))


def trig_D(r):
    a = r["atrp_ind"]
    with np.errstate(invalid="ignore"):
        return ((r["ret3"] <= D_RET3_K * a) & (r["ret12"] >= D_RET12_K * a) & (r["di7"] >= D_DI)
                & (r["cost_r"] <= COST_R_MAX["D"]))


def in_win(tod, leg):
    lo, hi = WIN[leg]
    return (tod >= lo) & (tod <= hi)


def leg_mask(r, leg, rmax=None, d_on=None):
    d_on = D_ON if d_on is None else d_on
    base = r["intake"] & r["univ_ok"] & in_win(r["tod"], leg)
    if leg == "E":
        return base & r["is_w"] & trig_E(r)
    if leg == "M":
        return base & r["is_md"] & trig_M(r, rmax)
    if leg == "D":
        return base & r["is_md"] & trig_D(r) if d_on else np.zeros(len(base), bool)
    raise KeyError(leg)


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
    if "spy_fo" not in df.columns:          # fail safe: no market context -> no signal (needs `context: [spy_fo]`)
        return np.zeros(len(df), bool)
    r = features(df)
    m = np.zeros(len(df), bool)
    for leg in LEG:
        m |= leg_mask(r, leg)
    return _thin(m, df) if THIN else m
