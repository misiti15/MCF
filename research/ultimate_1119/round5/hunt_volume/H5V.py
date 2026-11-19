# ULTIMATE ROUND-5 VOLUME-TRACK HUNT H5V (research only, not enabled in any account)
# research/ultimate_1119/round5/hunt_volume/PLAN.md; results in RESULTS.md next to this file.
# Educational only - not financial advice.
"""H5V - narrow, liquid, event-style legs (one-bar extremes / exhaustion) to add volume to the BOOK-EM narrow-edge book.

All features are point-in-time at the decision 5-minute bar close (09:50-15:00 lab rows): rsi = RSI(14) frame column,
rsi_prev = RSI(14) of the bar exactly 5 min earlier in the same session, fromOpen / buyPressure / vol_climax /
lower_wick frame columns, ret1 / ret3 / ret12 / di_diff7 / atr_d_pct via mcf.research.arena.indicators.compute,
spy_fo = SPY's own fromOpen (YAML `context: [spy_fo]`). No breadth, no cross-sectional ranks, no earnings outcomes.
Intake (all legs): price >= $10, |gap| < 20%, atr_d > 0, spy_fo present (fail safe), cost_r = LR8 stop-out round trip
((1c + 1bp) x tod mult + 1c + 1bp + 2c) / u, u = 0.25 x atr_d.  Long legs: the universal SPY long filter (skip while SPY
is -0.30..-0.75% from its open AND its 30-min change < 0).
Legs (leg letter = setup-name suffix "-F", "-S", ...; LabStrategy loads the module as `lab_<name>`):
  F long  ETF RSI collapse     EQB ETFs, adv20 >= $95M, 10:15-15:00, RSI14 prev >= 50 and now <= F_RMAX,
                               fromOpen <= -min(1.0%, 0.30 x atr_d%), (F_BP) buyPressure > 0, cost_r <= 0.10.
  S short heavyweight spike fade  non-fund stocks, adv20 >= S_ADV, price >= $20, 10:15-15:00, RSI14 prev <= 50 and now
                               >= S_RMIN, fromOpen >= +min(1.0%, 0.30 x atr_d%), buyPressure < 0, cost_r <= 0.08.
  C short heavyweight collapse continuation  non-fund stocks, adv20 >= C_ADV, price >= $20, 10:15-15:00, RSI14 prev
                               >= 50 and now <= 30, fromOpen <= -min(1.0%, 0.30 x atr_d%), buyPressure <= 0,
                               cost_r <= 0.08, and (C_SPY) SPY below its open.
  X short WB4-mirror ETF late pop fade  W list, adv20 >= $95M, 14:00-15:00, ret3 >= X_RET3, di_diff7 <= +5,
                               ret12 <= +1.0%, atr_d_pct >= 3.5967583179473883, cost_r <= 0.10.
  K long  one-bar shock snap   K_UNIV (EQB adv20 >= $300M | LEV adv20 >= $95M), 10:15-15:00, ret1 <= -K_K x atr_d%,
                               vol_climax >= 2, cost_r <= 0.10.
  V long  capitulation bar     non-fund stocks adv20 >= $500M, price >= $20, 10:15-15:00, ret1 <= -0.10 x atr_d%,
                               vol_climax >= V_VC, lower_wick >= 0.3, cost_r <= 0.08.
  Q long  sector-ETF relative extreme  SECT (context ETFs minus SPY), adv20 >= $95M, 11:00-15:00,
                               fromOpen - spy_fo <= -Q_K x atr_d%, RSI14 <= 35, cost_r <= 0.10.
Exits: GEOM per leg (t1s1 = +1R/-1R, t05s1 = +0.5R/-1R; R = 0.25 x daily ATR); 45-min time exit; flat by 15:50.
Account-side (not in the module): earnings blackout +-4 trading days on the stock legs (S, C, V); shorts only on
easy-to-borrow names; one lot per symbol; max 2 per symbol-session (2nd >= 30 min after the 1st exit); day cap 30.
Refire (THIN): max 2 per symbol-session, the 2nd >= REFIRE_BARS decision bars after the 1st."""
import json
from pathlib import Path

import numpy as np

# ---- FIT picks (round5/hunt_volume/fitsel.json, frozen 2026-11-19 before any CHECK data was built)
P = {
    "F": {"rmax": 35.0, "bp": False, "geom": "t1s1"},
    "S": {"adv": 1e9, "rmin": 70.0, "geom": "t05s1"},
    "C": {"adv": 500e6, "spy": True, "geom": "t1s1"},
    "X": {"ret3": 0.75, "geom": "t05s1"},
    "K": {"univ": "EQB", "k": 0.2, "geom": "t1s1"},
    "V": {"vc": 3.0, "geom": "t05s1"},
    "Q": {"k": 0.5, "geom": "t1s1"},
}
# ----
SIDES = {"F": "long", "S": "short", "C": "short", "X": "short", "K": "long", "V": "long", "Q": "long"}
WIN = {"F": (1015, 1500), "S": (1015, 1500), "C": (1015, 1500), "X": (1400, 1500), "K": (1015, 1500),
       "V": (1015, 1500), "Q": (1100, 1500)}
COST_R_MAX = {"F": 0.10, "S": 0.08, "C": 0.08, "X": 0.10, "K": 0.10, "V": 0.08, "Q": 0.10}
PX_STOCK, FO_PCT, FO_K = 20.0, 1.0, 0.30
X_DI, X_RET12, X_ATR = 5.0, 1.0, 3.5967583179473883
K_VC, V_RET1_K, V_LW, Q_RSI = 2.0, 0.10, 0.3, 35.0
ADV_ETF, ADV_K_EQB, ADV_V = 95e6, 300e6, 500e6
UNIV_BAND = (-0.75, -0.30)
REFIRE_BARS, MAX_PER_DAY = 6, 2
THIN = True
_U = json.loads((Path(__file__).resolve().parent / "H5V_symbols.json").read_text())
W, EQB, LEV, SECT = (frozenset(_U[k]) for k in ("W", "EQB", "LEV", "SECT"))
FUNDS = frozenset(_U["FUNDS"])
STOCKS = frozenset(_U["STOCKS"]) - FUNDS
LEGS = "FSCXKVQ"


def _leg_from_name(name):
    for lg in LEGS:
        if str(name).endswith("-" + lg):
            return lg
    return "F"


def leg_symbols(leg, p=None):
    p = P[leg] if p is None else p
    if leg == "F":
        return EQB
    if leg in ("S", "C", "V"):
        return STOCKS
    if leg == "X":
        return W
    if leg == "K":
        return EQB if p["univ"] == "EQB" else LEV
    return SECT


LEG = _leg_from_name(__name__)
SIDE = SIDES[LEG]
GEOM = P[LEG]["geom"]
SYMBOLS = leg_symbols(LEG)
LAYERS = [
    f"leg {LEG} ({SIDE}); see the module docstring for the rule; parameters {P[LEG]}",
    "intake: price >= $10, |gap| < 20%, cost_r cap per leg; long legs skip while SPY is -0.30..-0.75% from its open "
    "and falling over 30 min",
    "account: earnings blackout +-4 trading days (stock legs); shorts easy-to-borrow only; one lot per symbol; day cap 30;"
    " 45-min time exit",
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


def _lag1(x, key, mins):
    """x one row earlier in the same symbol-session, only when that row is exactly 5 minutes earlier; else NaN."""
    n = len(x)
    out = np.full(n, np.nan)
    if n <= 1:
        return out
    px = np.r_[np.nan, x[:-1]]
    pk = np.r_[np.array([None], dtype=object), key[:-1]]
    pm = np.r_[np.nan, mins[:-1]]
    ok = (pk == key) & (mins - pm == 5)
    out[ok] = px[ok]
    return out


def spy_r30(df) -> np.ndarray:
    """SPY % change over the last 30 minutes from spy_fo (same session, bar closes >= 09:50); NaN without t-30."""
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


def groups(df):
    """Per-row universe membership. Backtest: symbol column. Live: no symbol -> the YAML entry decides
    (symbols: module + min_adv), so the leg's own group is True."""
    n = len(df)
    if "symbol" in df:
        sym = df["symbol"].astype(str).to_numpy()
        return {g: np.array([s in S for s in sym]) for g, S in
                (("EQB", EQB), ("LEV", LEV), ("W", W), ("SECT", SECT), ("STOCKS", STOCKS))}
    own = {"F": "EQB", "S": "STOCKS", "C": "STOCKS", "V": "STOCKS", "X": "W", "Q": "SECT",
           "K": P["K"]["univ"]}[LEG]
    return {g: np.full(n, g == own) for g in ("EQB", "LEV", "W", "SECT", "STOCKS")}


def features(df) -> dict:
    """Point-in-time inputs at each decision bar close (shared with the backtest: hunt.py imports this)."""
    from mcf.research.arena.indicators import compute
    x = compute(df, names=["atr_d_pct", "di_diff7", "ret1", "ret3", "ret12"], context=False)
    c = lambda k: df[k].to_numpy(dtype=float)
    px, atr, tod, rsi = c("close"), c("atr_d"), c("tod"), c("rsi")
    key = _keys(df).astype(object)
    has_spy = "spy_fo" in df.columns
    fo = c("spy_fo") if has_spy else np.full(len(df), np.nan)
    r30 = spy_r30(df) if has_spy else np.full(len(df), np.nan)
    n = len(df)
    adv = c("adv20") if "adv20" in df else np.full(n, np.inf)
    with np.errstate(invalid="ignore", divide="ignore"):
        one = 0.01 + px * 1e-4
        cost_r = (one * _tod_mult(tod) + one + 0.02) / (0.25 * atr)
        atrp = atr / px * 100
        intake = (px >= 10) & (np.abs(c("gap")) < 20) & (atr > 0) & np.isfinite(fo)
        univ_ok = ~((fo >= UNIV_BAND[0]) & (fo <= UNIV_BAND[1]) & (r30 < 0))
    return {"tod": tod, "close": px, "adv": np.nan_to_num(adv, nan=0.0), "rsi": rsi,
            "rsi_prev": _lag1(rsi, key, _minutes(tod)), "fromOpen": c("fromOpen"),
            "fo_thr": np.minimum(FO_PCT, FO_K * atrp), "bp": c("buyPressure"), "vc": c("vol_climax"),
            "lw": c("lower_wick"), "ret1": x["ret1"].to_numpy(float), "ret3": x["ret3"].to_numpy(float),
            "ret12": x["ret12"].to_numpy(float), "di7": x["di_diff7"].to_numpy(float),
            "atrp_ind": x["atr_d_pct"].to_numpy(float), "atrp": atrp, "cost_r": cost_r, "intake": intake,
            "univ_ok": univ_ok, "spy_fo": fo, "spy_r30": r30, "g": groups(df)}


def leg_mask(r, leg, p=None):
    """Rows where leg `leg` with parameters p (default: the module's frozen P[leg]) fires."""
    p = P[leg] if p is None else p
    tod, g, adv, px = r["tod"], r["g"], r["adv"], r["close"]
    lo, hi = WIN[leg]
    base = r["intake"] & (tod >= lo) & (tod <= hi) & (r["cost_r"] <= COST_R_MAX[leg])
    if SIDES[leg] == "long":
        base &= r["univ_ok"]
    rsi, rp, fo, thr, bp = r["rsi"], r["rsi_prev"], r["fromOpen"], r["fo_thr"], r["bp"]
    with np.errstate(invalid="ignore"):
        if leg == "F":
            m = g["EQB"] & (adv >= ADV_ETF) & (rp >= 50) & (rsi <= p["rmax"]) & (fo <= -thr)
            if p["bp"]:
                m &= bp > 0
        elif leg == "S":
            m = g["STOCKS"] & (adv >= p["adv"]) & (px >= PX_STOCK) & (rp <= 50) & (rsi >= p["rmin"]) & (fo >= thr) & (bp < 0)
        elif leg == "C":
            m = g["STOCKS"] & (adv >= p["adv"]) & (px >= PX_STOCK) & (rp >= 50) & (rsi <= 30) & (fo <= -thr) & (bp <= 0)
            if p["spy"]:
                m &= r["spy_fo"] < 0
        elif leg == "X":
            m = (g["W"] & (adv >= ADV_ETF) & (r["ret3"] >= p["ret3"]) & (r["di7"] <= X_DI) & (r["ret12"] <= X_RET12)
                 & (r["atrp_ind"] >= X_ATR))
        elif leg == "K":
            u = (g["EQB"] & (adv >= ADV_K_EQB)) if p["univ"] == "EQB" else (g["LEV"] & (adv >= ADV_ETF))
            m = u & (r["ret1"] <= -p["k"] * r["atrp"]) & (r["vc"] >= K_VC)
        elif leg == "V":
            m = (g["STOCKS"] & (adv >= ADV_V) & (px >= PX_STOCK) & (r["ret1"] <= -V_RET1_K * r["atrp"])
                 & (r["vc"] >= p["vc"]) & (r["lw"] >= V_LW))
        elif leg == "Q":
            m = g["SECT"] & (adv >= ADV_ETF) & (fo - r["spy_fo"] <= -p["k"] * r["atrp"]) & (rsi <= Q_RSI)
        else:
            raise KeyError(leg)
    return base & m


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
    m = leg_mask(features(df), LEG)
    return _thin(m, df) if THIN else m
