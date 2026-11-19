# ULTIMATE CANDIDATE ULT-33 EARN-GEO (research only, not enabled in any account)
# research/ultimate_1119/round4/PLAN.md sec. 3 "ULT-33"; backtest research/ultimate_1119/round4/ULT-33/RESULTS.md
# Next: only a TIER A / BEATS result goes further, with the owner's yes AND an owner exception to the 4-day earnings
# blackout (config earnings_blackout_days: 4). Educational only - not financial advice.
"""ULT-33 EARN-GEO - cost geometry on earnings reaction-day moves: wider R, 2:1 target, limit entry. LONG + SHORT.
PARTLY CHECK-INFORMED.

Thesis: on ordinary bars the edge is a fixed few bp, so widening R only dilutes it (ULT-16, ULT-25). On an earnings
reaction day the move is 2-4 daily ATRs, so the opportunity should scale with R while the costs do not. A high-liquidity
tier (ADV20 >= $100M) keeps costs low.
Event set (fixed, = ULT-28's HOLD event at G 3%, S any, plus the liquidity tier):
  event    reaction day RD of a scheduled earnings report (bmo -> report date; amc -> next session; dmh / unknown
           excluded; repeats within 10 sessions keep the first) - ULT-28's reaction_days() / today_symbols().
  intake   price >= $10; 3% <= |gap| < 20%; atr_d > 0; ADV20 >= $100M (live: YAML min_adv 100e6);
           cost_r(M) <= 0.08 with cost_r(M) = LR8 stop-out round trip ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / (M x atr_d).
  side     s = sign(gap).
  HOLD     s x vwapDistPct > 0; s x fromOpen >= 0; RSI5 <= 85 (long) / >= 25 (short); long: SPY universal filter
           (skip while SPY is -0.30..-0.75% from its open AND SPY's 30-min change < 0; no SPY context -> no long).
  window   bar close 09:50-12:30.
  refire   (THIN) max 2 per symbol-session, the 2nd >= REFIRE_BARS bars after the 1st (backtest: >= 30 min after exit).
Exit (GEOM "S" with stop_price / target_price, YAML time_stop_min 45, time_stop_min_r 99; flat 15:50):
  Ru = M x atr_d; stop = close - s x 1 Ru; target = close + s x K Ru (K 1 = t1s1, K 2 = t2s1).
Entry: ENTRY "MKT" = market at the next minute (the live LabStrategy default).
       ENTRY "LMT" = limit at VWAP + s x 0.05 x atr_d, valid 15 min (backtest only). The live LabStrategy / Signal has
       market and stop entries only, so a LMT pick needs runner support first; run as is, this module trades MKT.
Live event source: the allow-list SYMBOLS (YAML `symbols: module`) = today's reaction-day names (any surprise), built at
import from the calendar parquet (env MCF_EARN_CAL) by ULT-28's code. Missing calendar -> empty list -> no trades.
In the backtest the frame carries an e_rd column, which takes precedence.
Two sides, one file: a setup name ending in "-S" / "-short" is the short side (shorts easy-to-borrow only; reaction-day
shorts carry a 5 bp borrow estimate, 8 bp under $20, in the backtest). Day cap 30 over both sides."""
import importlib.util
from pathlib import Path

import numpy as np

_NAME = __name__.lower()
SIDE = "short" if _NAME.endswith(("-s", "_s", "-short", "_short")) else "long"
_SGN = 1 if SIDE == "long" else -1
# ---- fit-frozen pick 33l m1-t2s1-LMT (round4/ULT-33/fitsel.json); set after the FIT grid, before any CHECK data.
# FAIL on fit (avg R -0.029, all 12 configs negative); faithful build for the record only, NOT for deployment.
M = 1.0                   # Ru = M x atr_d
K = 2.0                   # target in Ru (1 = t1s1, 2 = t2s1); stop is always 1 Ru
ENTRY = "LMT"             # "MKT" | "LMT" (LMT = backtest only; live LabStrategy trades MKT = 33k)
# ----
GEOM = "S"
G = 3.0
WINDOW = (950, 1230)
MIN_ADV, COST_R_MAX, PX_MIN, GAP_MAX = 100e6, 0.08, 10.0, 20.0
LMT_OFF_ATR, LMT_VALID_MIN = 0.05, 15
THIN = True
REFIRE_BARS, MAX_PER_DAY = 15, 2

_spec = importlib.util.spec_from_file_location("ult33_base28", Path(__file__).resolve().parent / "ULT-28.py")
B28 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B28)
sessions, reaction_days = B28.sessions, B28.reaction_days

LAYERS = [
    "earnings reaction day (bmo report day / the session after an amc report)",
    "intake: price >= $10, ADV20 >= $100M, cost <= 0.08 of the risk unit",
    f"gap {'>=' if _SGN > 0 else '<='} {_SGN * G:+g}% (and |gap| < 20%)",
    "close on the gap side of VWAP and not below/above the open (gap holding)",
    "RSI(5) <= 85" if _SGN > 0 else "RSI(5) >= 25, easy to borrow",
] + (["skip while SPY is -0.30..-0.75% from its open and falling over 30 min"] if _SGN > 0 else []) + [
    f"window: bar close {WINDOW[0]}-{WINDOW[1]} ET",
    f"exit: +{K:g}R / -1R (R = {M:g} x daily ATR), 45-min time exit",
]

SYMBOLS = B28.today_symbols(side=SIDE, s_mode="any")      # YAML `symbols: module` on both entries


def features(df, m=None) -> dict:
    """Point-in-time inputs at each decision bar close (bt.py imports this). cost_r is per m x atr_d."""
    m = M if m is None else m
    n = len(df)
    c = lambda k: df[k].to_numpy(dtype=float)   # noqa: E731
    px, atr, tod = c("close"), c("atr_d"), c("tod")
    key = B28._keys(df)
    adv = c("adv20") if "adv20" in df.columns else np.full(n, np.inf)
    has_spy = "spy_fo" in df.columns
    fo = c("spy_fo") if has_spy else np.full(n, np.nan)
    r30 = B28.spy_r30(df, key) if has_spy else np.full(n, np.nan)
    e_rd = df["e_rd"].to_numpy(dtype=bool) if "e_rd" in df.columns else np.ones(n, bool)
    with np.errstate(invalid="ignore", divide="ignore"):
        one = 0.01 + px * 1e-4
        cost_r = (one * B28._tod_mult(tod) + one + 0.02) / (m * atr)
        gap = c("gap")
        intake = ((px >= PX_MIN) & (np.abs(gap) < GAP_MAX) & (atr > 0) & (cost_r <= COST_R_MAX) & (adv >= MIN_ADV)
                  & e_rd)
        univ_long_ok = (~((fo >= -0.75) & (fo <= -0.30) & (r30 < 0))) if has_spy else np.zeros(n, bool)
    return {"tod": tod, "close": px, "gap": gap, "vd": c("vwapDistPct"), "fo": c("fromOpen"), "rsi5": c("rsi5"),
            "cost_r": cost_r, "intake": intake, "univ_long_ok": np.asarray(univ_long_ok, bool), "atr": atr}


def signal(r, sgn) -> np.ndarray:
    """Intake + side rule + HOLD (no window, no thinning)."""
    with np.errstate(invalid="ignore"):
        return r["intake"] & (sgn * r["gap"] >= G) & B28.hold(r, sgn)


def limit_price(close, vwap_dist_pct, atr, sgn):
    """LMT: VWAP (from the decision bar's close and vwapDistPct) + s x 0.05 x atr_d."""
    vwap = close / (1 + vwap_dist_pct / 100.0)
    return vwap + sgn * LMT_OFF_ATR * atr


def _thin(mk, df):
    hit = np.flatnonzero(mk)
    if not len(hit):
        return mk
    key = B28._keys(df)
    out = np.zeros(len(mk), bool)
    last, n, cur = -10**9, 0, None
    for i in hit:
        if key[i] != cur:
            cur, last, n = key[i], -10**9, 0
        if n < MAX_PER_DAY and i - last >= REFIRE_BARS:
            out[i] = True; last = i; n += 1
    return out


def mask(df) -> np.ndarray:
    r = features(df)
    tod = r["tod"]
    mk = signal(r, _SGN) & (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return _thin(mk, df) if THIN else mk


def stop_price(f, i) -> float:
    return float(f["close"].iloc[i]) - _SGN * M * float(f["atr_d"].iloc[i])


def target_price(f, i, stop) -> float:
    return float(f["close"].iloc[i]) + _SGN * K * M * float(f["atr_d"].iloc[i])
