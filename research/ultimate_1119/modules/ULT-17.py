# ULTIMATE CANDIDATE ULT-17 SECTOR-LAG (research only, not enabled in any account)
# research/ultimate_1119/round2/PLAN.md sec. 3 "ULT-17"; backtest research/ultimate_1119/round2/ULT-17/RESULTS.md
# Next: only a TIER A / BEATS result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-17 SECTOR-LAG - sector-ETF lead-lag catch-up, LONG and SHORT, decision bars 10:15-15:00.

A name whose sector ETF made a sharp 15-minute move that the name has not yet followed is traded in the sector's
direction, on a time exit.

Rule (all point-in-time, at the decision 5-minute bar close; the SAME features() / trigger() code is used by bt.py):
  sector    sec_fo   = sector ETF % change from its first 5-min open to the close of the same bar (as spy_fo for SPY)
            sec_atrp = sector ETF prior-day daily ATR as % of its price at the bar (100 x atr_d / close)
            sec_beta = OLS beta of the name's daily returns on the sector's, clipped [0.3, 3]
            (sector = argmax Pearson correlation of daily close-to-close returns over the prior <= 60 open sessions,
            min 20, among 22 ETFs SPY QQQ IWM XLK XLF XLE XLV XLI XLY XLP XLU XLB XLRE XLC SMH XBI KRE GDX XOP ITB IBIT
            ARKK; strictly prior sessions)
  sret3     sector 15-min return % = (1 + sec_fo/100) / (1 + sec_fo[t-15min]/100) - 1   (x 100)
  nret3     name 15-min return % of 5-min closes (same session, exact t-15min bar)
  trigger   |sret3| >= S x sec_atrp AND sgn(sret3) = side AND
            lag = sgn(sret3) x (beta x sret3 - nret3) / atr_d% (name) >= LMIN
  intake U2 price >= $10; |gap| < 20%; atr_d > 0; cost_r <= 0.08 (LR8 stop round trip ((1c + 1bp) x tod mult + 1c +
            1bp + 2c) / u, u = 0.25 x atr_d); ADV20 >= $50M via the YAML min_adv; non-ETF names only (YAML
            `symbols: module` = SYMBOLS, the frozen lab stock list from ULT-12_symbols.json "S")
  universal long: not (SPY from open in [-0.75%, -0.30%] and SPY 30-min change < 0)
  universal short: gap < +0.5% and RSI(5) >= 25; easy-to-borrow (account side live; universe.csv flag in the backtest)
  window    bar close 10:15-15:00 (inclusive)
  refire    (THIN) max 2 per symbol-session, the 2nd >= (H + 30) / 5 decision bars after the 1st (the backtest chain:
            >= 30 min after the first lot's exit, one lot per symbol across both sides). YAML: refire true,
            refire_cooldown 0.
  sector missing (no sec_* columns / NaN) or no SPY context -> no signal (fail safe).
Two sides, one file: LabStrategy has one side per setup, so the account carries TWO `type: lab` entries pointing at this
file; a setup name ending in "-S" / "-short" is the short side, anything else the long side.
Exit: GEOM "S": stop_price = catastrophic stop 2u (0.5 daily ATR) beyond the decision close, no target; YAML
time_stop_min H, time_stop_min_r 99; flat 15:50 implied (last entry 15:00 + 45 min). Account side: day cap 30 entries
over both sides (first by time, ADV20 desc), one lot per symbol.
LIVE GAP (documented in RESULTS.md): the live lab frame carries no sec_fo / sec_atrp / sec_beta columns; a runner
extension (per-name sector map, refreshed daily from prior sessions, plus the sector ETF's fromOpen per bar, built like
lab_context.spy_fo) is needed before any live use. Without it the module fires nothing (fail safe).
Context: `context: [spy_fo]`."""
import json
from pathlib import Path

import numpy as np

_NAME = __name__.lower()
SIDE = "short" if _NAME.endswith(("-s", "_s", "-short", "_short")) else "long"
_SGN = 1 if SIDE == "long" else -1
GEOM = "S"
SECTOR_ETFS = ("SPY", "QQQ", "IWM", "XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC", "SMH",
               "XBI", "KRE", "GDX", "XOP", "ITB", "IBIT", "ARKK")
# ---- fit-frozen pick 17g (round2/ULT-17/fitsel.json); set after the FIT grid, before any CHECK data
S = 0.25
LMIN = 0.20
H = 30
# ----
WINDOW = (1015, 1500)
MIN_ADV = 50_000_000
COST_R_MAX = 0.08
GAP_SHORT_MAX = 0.5
RSI5_SHORT_MIN = 25.0
MAX_PER_DAY = 2
THIN = True
_U = json.loads((Path(__file__).resolve().parent / "ULT-12_symbols.json").read_text())
SYMBOLS = frozenset(_U["S"]) - frozenset(SECTOR_ETFS)
LAYERS = [
    "intake U2: price >= $10, |gap| < 20%, cost_r <= 0.08, ADV20 >= $50M (YAML min_adv), stocks only",
    f"sector ETF 15-min move >= {S:g} x its daily ATR% ({'up' if _SGN > 0 else 'down'})",
    f"name lags its sector (beta x sector move - name move) by >= {LMIN:g} x its daily ATR%",
    ("not into a falling SPY (-0.30..-0.75% from open and 30-min < 0)" if _SGN > 0
     else "gap < +0.5%, RSI(5) >= 25, easy to borrow"),
    f"window: bar close {WINDOW[0]}-{WINDOW[1]} ET; exit: {H}-min time exit, 2u catastrophic stop",
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


def _lag(v, df, lag_min):
    """Value of v at the same symbol-session bar lag_min minutes earlier (NaN without that exact bar)."""
    import pandas as pd
    key = _keys(df)
    m = _minutes(df["tod"].to_numpy(dtype=float))
    s = pd.Series(np.asarray(v, float), index=pd.MultiIndex.from_arrays([key, m]))
    s = s[~s.index.duplicated()]
    return s.reindex(pd.MultiIndex.from_arrays([key, m - lag_min])).to_numpy(dtype=float)


def _col(df, k):
    return df[k].to_numpy(dtype=float) if k in df.columns else np.full(len(df), np.nan)


def _pct_change_fo(fo, fo_lag):
    with np.errstate(invalid="ignore"):
        return ((1 + fo / 100) / (1 + fo_lag / 100) - 1) * 100


def features(df) -> dict:
    """Point-in-time inputs at each decision bar close (shared with the backtest: bt.py imports this)."""
    px, atr, tod = _col(df, "close"), _col(df, "atr_d"), _col(df, "tod")
    gap, rsi5 = _col(df, "gap"), _col(df, "rsi5")
    sfo, satrp, beta = _col(df, "sec_fo"), _col(df, "sec_atrp"), _col(df, "sec_beta")
    spy = _col(df, "spy_fo")
    sret3 = _pct_change_fo(sfo, _lag(sfo, df, 15))
    with np.errstate(invalid="ignore", divide="ignore"):
        nret3 = (px / _lag(px, df, 15) - 1) * 100
        natrp = 100 * atr / px
        sgn = np.sign(sret3)
        lag = sgn * (np.clip(beta, 0.3, 3.0) * sret3 - nret3) / natrp
        spy_r30 = _pct_change_fo(spy, _lag(np.where(tod >= 950, spy, np.nan), df, 30))
        one = 0.01 + px * 1e-4
        cost_r = (one * _tod_mult(tod) + one + 0.02) / (0.25 * atr)
        intake = ((px >= 10) & (np.abs(gap) < 20) & (atr > 0) & (cost_r <= COST_R_MAX) & np.isfinite(spy)
                  & np.isfinite(sret3) & np.isfinite(satrp) & np.isfinite(beta) & np.isfinite(lag))
        long_ok = ~((spy >= -0.75) & (spy <= -0.30) & (spy_r30 < 0))
        short_ok = (gap < GAP_SHORT_MAX) & (rsi5 >= RSI5_SHORT_MIN)
        smove = np.abs(sret3) / satrp
    return {"tod": tod, "close": px, "sret3": sret3, "nret3": nret3, "satrp": satrp, "beta": beta, "natrp": natrp,
            "lag": lag, "smove": smove, "sgn": sgn, "spy_fo": spy, "spy_r30": spy_r30, "gap": gap, "rsi5": rsi5,
            "cost_r": cost_r, "intake": intake, "long_ok": long_ok, "short_ok": short_ok}


def trigger(r, sgn, s, lmin) -> np.ndarray:
    """Un-thinned, un-windowed trigger for one side (sgn +1 long / -1 short) at thresholds (s, lmin)."""
    with np.errstate(invalid="ignore"):
        side_ok = r["long_ok"] if sgn > 0 else r["short_ok"]
        return r["intake"] & (r["sgn"] == sgn) & (r["smove"] >= s) & (r["lag"] >= lmin) & side_ok


def _thin(m, df):
    hit = np.flatnonzero(m)
    out = np.zeros(len(m), bool)
    if not len(hit):
        return out
    key = _keys(df)
    gap_bars = int(np.ceil((H + 30) / 5))
    last, n, cur = -10**9, 0, None
    for i in hit:
        if key[i] != cur:
            cur, last, n = key[i], -10**9, 0
        if n < MAX_PER_DAY and i - last >= gap_bars:
            out[i] = True; last = i; n += 1
    return out


def mask(df) -> np.ndarray:
    if "spy_fo" not in df.columns or "sec_fo" not in df.columns:   # fail safe (needs context + sector columns)
        return np.zeros(len(df), bool)
    r = features(df)
    tod = r["tod"]
    m = trigger(r, _SGN, S, LMIN) & (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return _thin(m, df) if THIN else m


def stop_price(f, i) -> float:
    """GEOM "S": catastrophic stop 2u = 0.5 daily ATR beyond the decision close."""
    return float(f["close"].iloc[i]) - _SGN * 2 * 0.25 * float(f["atr_d"].iloc[i])
