# ULTIMATE CANDIDATE ULT-29 EARN-CONFL (research only, not enabled in any account)
# research/ultimate_1119/round4/PLAN.md sec. 3 "ULT-29"; backtest research/ultimate_1119/round4/ULT-29/RESULTS.md
# Next: only a TIER A / BEATS result goes to a testing arena, with the owner's yes AND an explicit owner exception to the
# earnings blackout (config earnings_blackout_days 4, owner 2026-10-07). Educational only - not financial advice.
"""ULT-29 EARN-CONFL - gated confluence on an earnings reaction-day with-gap base, LONG + SHORT.
PARTLY CHECK-INFORMED (round4/PLAN.md sec. 0.6). Needs an owner blackout exception (sec. 0.8).

Reaction day (RD): report date for a 'bmo' report, the next trading session for an 'amc' report; 'dmh' / 'unknown'
excluded; a repeat of a symbol within 10 sessions keeps the first (rd_events()). Point-in-time: report dates and
sessions are scheduled weeks ahead; surprise is NOT used by this setup.
Bases (decision 5-min bar close 10:00-13:00, point-in-time; intake price >= $10, |gap| < 20%, atr_d > 0,
ADV20 >= $30M, cost_r <= 0.08 with cost_r = LR8 stop-out round trip ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / u,
u = 0.25 x atr_d):
  EB-L long : RD name, gap >= +2%, universal long filter (skip while SPY is -0.30..-0.75% from its open AND SPY's
              30-min change < 0).
  EB-S short: RD name, gap <= -2%, easy to borrow (account side live / universe.csv in the backtest), RSI5 >= 25.
Triggers (decision bar; VWAP = close / (1 + vwapDistPct / 100); long, short mirrored):
  T1 VWAP-hold pullback : |low - VWAP| <= 0.15 x atr_d AND close > VWAP   (short: |high - VWAP| <= 0.15 atr_d, close < VWAP)
  T2 new session extreme: dist_hod_atr <= 0.02 AND previous bar's dist_hod_atr > 0.02   (short: dist_lod_atr)
  T3 RSI5 reset         : RSI5[prev] <= 40 AND RSI5 > 40 AND close > VWAP   (short: RSI5[prev] >= 60, RSI5 < 60, close < VWAP)
  T4 with-direction vol : volumeRatio >= 2 AND close > previous close   (short: close < previous close)
Gates (FIT only, round4/ULT-29/base_gate.json, trigger_gate.json): a base trades only if its random-entry avg R was
  >= 0 in both fit sub-halves under the frozen exit (BASE_OPEN); only triggers whose signal-minus-random (TX-45) was
  >= 0 in both sub-halves count (SURVIVE).
Signal: base AND >= CONF surviving triggers of the base's side each true on the decision bar or one of the previous
  W-1 bars (W bars counting the decision bar; same session, exact 5-min spacing).
Refire (THIN): max 2 per symbol-session, the 2nd >= REFIRE_BARS decision bars after the 1st (backtest chain: >= 30 min
  after the first lot's exit, one lot per symbol across sides).
Two setups, one file: a setup name ending "-S"/"-short" -> EB-S (short), anything else -> EB-L (long).
RD source live: the frame column `earn_rd` (bool) if present; otherwise ULT-29_rd.json ({"YYYY-MM-DD": [symbols]},
  built by rd_events() from a report-date + report-hour calendar, e.g. yfinance) gives today's RD names as SYMBOLS, and
  the YAML MUST carry `symbols: module` so only today's RD names are evaluated (the live frame has no symbol column).
  The module is loaded once per process: the runner must start fresh each session (or reload) for SYMBOLS to roll.
  No RD file for today -> SYMBOLS empty -> no signal (fail safe).
YAML per entry: symbols: module, min_adv 30e6, context: [spy_fo], window [1000, 1300], refire true, refire_cooldown 0.
Exit: EXIT "H" -> GEOM t1s1 (+1u / -1u around the decision close), EXIT "X" -> GEOM "S" (2u catastrophic stop, no
  target); YAML time_stop_min 45, time_stop_min_r 99; flat 15:50. Account side: day cap 30 entries (first by time).
Costs: on an RD bar before 10:30 the backtest charges x1.5 entry/exit costs; every short pays a 5 bp borrow estimate
  (8 bp if priced < $20) in the earnings window."""
import json
from datetime import datetime
from pathlib import Path

import numpy as np

_NAME = __name__.lower()
BASE = "EB-S" if _NAME.endswith(("-s", "_s", "-short", "_short")) else "EB-L"
SIDE = "short" if BASE == "EB-S" else "long"
_SGN = 1 if SIDE == "long" else -1
# ---- fit-frozen (round4/ULT-29/fitsel.json, base_gate.json, trigger_gate.json); set before any CHECK data.
W = 1
CONF = 2
EXIT = "X"
BASE_OPEN = {"EB-L": {"H": False, "X": False}, "EB-S": {"H": False, "X": False}}
SURVIVE = {"EB-L": (), "EB-S": ()}
# ----
GEOM = "t1s1" if EXIT == "H" else "S"
WINDOW = (1000, 1300)
LONG_TRIG = ("L1", "L2", "L3", "L4")
SHORT_TRIG = ("S1", "S2", "S3", "S4")
GAP_MIN = 2.0
MIN_ADV = 30e6
COST_MAX = 0.08
UNIV_BAND = (-0.75, -0.30)
THIN = True
REFIRE_BARS, MAX_PER_DAY = 6, 2
RD_FILE = Path(__file__).resolve().parent / "ULT-29_rd.json"
SYMBOL_HINT = None


def _today_rd():
    try:
        from zoneinfo import ZoneInfo
        d = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
        return frozenset(json.loads(RD_FILE.read_text()).get(d, []))
    except Exception:
        return frozenset()


SYMBOLS = _today_rd()
LAYERS = [
    "earnings reaction day (bmo: report day, amc: next session), "
    + ("gap >= +2%, SPY not -0.30..-0.75% and falling" if BASE == "EB-L" else "gap <= -2%, easy to borrow, RSI5 >= 25"),
    "ADV20 >= $30M, price >= $10, stop-out cost <= 0.08R",
    f"at least {CONF} of the gated triggers {', '.join(SURVIVE[BASE]) or '(none)'} within {W} bars",
    f"window: bar close {WINDOW[0]}-{WINDOW[1]} ET",
    "exit: +1R / -1R, 45-min time exit" if EXIT == "H" else "exit: 45-min time exit, 2u catastrophic stop",
]


# ---------------------------------------------------------------- reaction-day calendar (shared with bt.py)
def rd_events(earn, sessions):
    """Earnings table (symbol, date, session) + sorted trading-session list -> DataFrame(symbol, rd) of reaction days.
    bmo -> the report date (must be a session); amc -> the next session after the report date, and only if it lies
    within 5 calendar days (a gap in `sessions`, e.g. an excluded block, drops the event rather than jumping it).
    dmh / unknown excluded. A repeat of a symbol within 10 sessions keeps the first."""
    import pandas as pd
    s = pd.DatetimeIndex(pd.to_datetime(sorted(set(map(str, sessions)))))
    e = earn[earn["session"].isin(["bmo", "amc"])].copy()
    d = pd.to_datetime(e["date"]).dt.normalize()
    j = np.where(e["session"].to_numpy() == "bmo", s.searchsorted(d, "left"), s.searchsorted(d, "right"))
    ok = j < len(s)
    rd = pd.Series(pd.NaT, index=e.index, dtype="datetime64[ns]")
    rd[ok] = s[j[ok]]
    bmo = e["session"].to_numpy() == "bmo"
    ok &= np.where(bmo, rd.to_numpy() == d.to_numpy(), (rd - d).dt.days.fillna(99).to_numpy() <= 5)
    out = pd.DataFrame({"symbol": e["symbol"].astype(str).to_numpy()[ok], "j": j[ok],
                        "rd": rd.to_numpy()[ok]}).sort_values(["symbol", "j"]).drop_duplicates(["symbol", "j"])
    keep, last = [], {}
    for sym, jj in zip(out["symbol"], out["j"]):
        k = sym not in last or jj - last[sym] >= 10
        keep.append(k)
        if k:
            last[sym] = jj
    out = out[np.array(keep, bool)]
    return pd.DataFrame({"symbol": out["symbol"].to_numpy(), "rd": out["rd"].dt.strftime("%Y-%m-%d").to_numpy()})


def _tod_mult(tod):
    return np.where(tod < 935, 3.8, np.where(tod < 950, 2.1, np.where(tod < 1030, 1.4, 1.0)))


def _m2(t):
    t = np.asarray(t, float)
    return np.floor(t / 100) * 60 + t % 100


def _keys(df):
    import pandas as pd
    if "date" in df:
        day = df["date"].astype(str).to_numpy()
    else:
        day = pd.DatetimeIndex(df.index).strftime("%Y-%m-%d").to_numpy()
    if "symbol" in df:
        day = df["symbol"].astype(str).to_numpy() + "|" + day
    return day


def _col(df, k):
    return df[k].to_numpy(dtype=float) if k in df.columns else np.full(len(df), np.nan)


def _lag(v, key, mins, lag):
    """v at (same key, mins - lag), exact time match; NaN otherwise."""
    import pandas as pd
    v = np.asarray(v, float)
    kc = pd.factorize(key)[0].astype(np.int64)
    code = kc * 100000 + np.asarray(mins, np.int64)
    if len(code) and np.all(np.diff(code) > 0):
        want = code - np.asarray(lag, np.int64)
        j = np.clip(np.searchsorted(code, want), 0, len(code) - 1)
        return np.where(code[j] == want, v[j], np.nan)
    s = pd.Series(v, index=pd.MultiIndex.from_arrays([key, mins]))
    s = s[~s.index.duplicated()]
    return s.reindex(pd.MultiIndex.from_arrays([key, mins - lag])).to_numpy(dtype=float)


def _rd_flag(df):
    if "earn_rd" in df.columns:
        return df["earn_rd"].fillna(False).to_numpy().astype(bool)
    if "symbol" in df.columns:
        return np.array([s in SYMBOLS for s in df["symbol"].astype(str)], bool)
    if SYMBOL_HINT is not None:
        return np.full(len(df), SYMBOL_HINT in SYMBOLS)
    # live frame without a symbol column: the YAML `symbols: module` allow-list (today's RD names) restricts the scan
    return np.full(len(df), len(SYMBOLS) > 0)


def features(df) -> dict:
    """Point-in-time base parts and the eight triggers (on the bar) for every row (shared with bt.py). Uses only the
    row's own and earlier bars of the same symbol-session, its context column and prior-day values."""
    n = len(df)
    key = _keys(df).astype(object)
    tod = _col(df, "tod")
    mins = _m2(tod)
    c, h, lo, atr, gap = _col(df, "close"), _col(df, "high"), _col(df, "low"), _col(df, "atr_d"), _col(df, "gap")
    r5, vr = _col(df, "rsi5"), _col(df, "volumeRatio")
    hod, lod = _col(df, "dist_hod_atr"), _col(df, "dist_lod_atr")
    fo_s = _col(df, "spy_fo")
    adv = _col(df, "adv20")
    rd = _rd_flag(df)
    with np.errstate(invalid="ignore", divide="ignore"):
        vwap = c / (1 + _col(df, "vwapDistPct") / 100)
        one = 0.01 + c * 1e-4
        cost_r = (one * _tod_mult(tod) + one + 0.02) / (0.25 * atr)
        r5_p, c_p = _lag(r5, key, mins, 5), _lag(c, key, mins, 5)
        hod_p, lod_p = _lag(hod, key, mins, 5), _lag(lod, key, mins, 5)
        r30 = ((1 + fo_s / 100) / (1 + _lag(fo_s, key, mins, 30) / 100) - 1) * 100
        trig = {
            "L1": (np.abs(lo - vwap) <= 0.15 * atr) & (c > vwap),
            "L2": (hod <= 0.02) & (hod_p > 0.02),
            "L3": (r5_p <= 40) & (r5 > 40) & (c > vwap),
            "L4": (vr >= 2.0) & (c > c_p),
            "S1": (np.abs(h - vwap) <= 0.15 * atr) & (c < vwap),
            "S2": (lod <= 0.02) & (lod_p > 0.02),
            "S3": (r5_p >= 60) & (r5 < 60) & (c < vwap),
            "S4": (vr >= 2.0) & (c < c_p),
        }
        advok = np.nan_to_num(adv, nan=0.0) >= MIN_ADV if np.isfinite(adv).any() else np.ones(n, bool)
        intake = (rd & (c >= 10) & (np.abs(gap) < 20) & (atr > 0) & np.isfinite(fo_s) & advok
                  & (cost_r <= COST_MAX) & (tod >= WINDOW[0]) & (tod <= WINDOW[1]))
        univ_long = ~((fo_s >= UNIV_BAND[0]) & (fo_s <= UNIV_BAND[1]) & (r30 < 0)) & np.isfinite(r30)
        bases = {"EB-L": intake & (gap >= GAP_MIN) & univ_long,
                 "EB-S": intake & (gap <= -GAP_MIN) & (gap < 0.5) & (r5 >= 25)}
    trig = {k: np.nan_to_num(v.astype(float)) > 0 for k, v in trig.items()}
    bases = {k: np.nan_to_num(v.astype(float)) > 0 for k, v in bases.items()}
    return {"n": n, "key": key, "mins": mins, "tod": tod, "trig": trig, "bases": bases, "cost_r": cost_r,
            "spy_r30": r30, "vwap": vwap, "rd": rd}


def within(r, name, w) -> np.ndarray:
    """Trigger `name` true on the decision bar or one of the previous w-1 bars (w bars in all, exact 5-min spacing)."""
    b = r["trig"][name]
    out = b.copy()
    for k in range(1, w):
        out |= _lag(b.astype(float), r["key"], r["mins"], 5 * k) == 1.0
    return out


def count(r, base, w, survive=None) -> np.ndarray:
    names = SURVIVE[base] if survive is None else survive
    tot = np.zeros(r["n"], int)
    for k in names:
        tot += within(r, k, w).astype(int)
    return tot


def _thin(m, df):
    hit = np.flatnonzero(m)
    out = np.zeros(len(m), bool)
    key = _keys(df)
    last, n, cur = -10**9, 0, None
    for i in hit:
        if key[i] != cur:
            cur, last, n = key[i], -10**9, 0
        if n < MAX_PER_DAY and i - last >= REFIRE_BARS:
            out[i] = True; last = i; n += 1
    return out


def mask(df) -> np.ndarray:
    if "spy_fo" not in df.columns or not BASE_OPEN[BASE][EXIT] or len(SURVIVE[BASE]) < CONF:
        return np.zeros(len(df), bool)       # fail safe / base or triggers closed by the FIT gates
    r = features(df)
    m = r["bases"][BASE] & (count(r, BASE, W) >= CONF)
    return _thin(m, df) if THIN else m


def stop_price(f, i) -> float:
    """GEOM "S" (EXIT "X"): catastrophic stop 2u = 0.5 daily ATR beyond the decision close."""
    return float(f["close"].iloc[i]) - _SGN * 2 * 0.25 * float(f["atr_d"].iloc[i])
