# ULTIMATE CANDIDATE ULT-35 EARN-FAIL (research only, not enabled in any account)
# research/ultimate_1119/round4/PLAN.md sec. 3 "ULT-35"; backtest research/ultimate_1119/round4/ULT-35/RESULTS.md
# Next: only a TIER A / BEATS result goes further, with the owner's yes AND an owner exception to the 4-day earnings
# blackout (config earnings_blackout_days: 4). Educational only - not financial advice.
"""ULT-35 EARN-FAIL - failed earnings gap: trade the reclaim AGAINST the gap, LONG + SHORT. PARTLY CHECK-INFORMED.

Thesis: when a reaction-day gap fails (price back through VWAP and the open), the market has rejected the news reading
and trapped gap traders unwind. Mutually exclusive with ULT-28 on any bar (ULT-28 needs the gap holding: close on the
gap side of VWAP and fromOpen with the gap; this needs both on the other side).
Rule (point-in-time at the decision 5-minute bar close; frame columns gap, vwapDistPct, fromOpen, rsi5; context spy_fo):
  event    reaction day RD of a scheduled earnings report (bmo -> report date; amc -> next session; dmh / unknown
           excluded; repeats of a symbol within 10 sessions keep the first).
  intake   price >= $10; G <= |gap| < 20%; atr_d > 0; cost_r <= 0.08 (LR8 stop-out round trip
           ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / u, u = 0.25 x atr_d); ADV20 >= $30M (live: YAML min_adv 30e6).
  side     gap <= -G -> LONG (gap-down reclaim); gap >= +G -> SHORT (gap-up failure). s = -sign(gap).
  FAIL     core(bar) = s x vwapDistPct > 0 AND s x foa >= D, foa = (close - open) / atr_d with
           open = close / (1 + fromOpen/100); entry on the FIRST such bar = core now and core false on the previous bar
           (exactly 5 min earlier, same session; no previous bar -> no signal).
  short    RSI5 >= 25 (easy-to-borrow and the earnings borrow estimate are account / backtest side). The chassis'
           universal "no short if gap >= +0.5%" filter would remove EVERY short of this design (a gap-up failure is a
           gap-up by definition); the candidate's own short rule (PLAN sec. 3 ULT-35) overrides it, and the side split
           is reported.
  universal  long: skip while SPY is -0.30..-0.75% from its open AND SPY's 30-min change < 0 (no SPY context -> no
           long signal).
  window   bar close 10:15-13:30 (YAML window must match).
  refire   (THIN) max 2 per symbol-session, the 2nd >= REFIRE_BARS decision bars after the 1st (backtest chain: >= 30 min
           after the first lot's exit, one lot per symbol). YAML refire true, refire_cooldown 0.
Exit: EXIT "T" -> GEOM t1s1 (+1u / -1u) with YAML time_stop_min 45, time_stop_min_r 99; EXIT "X" -> GEOM "S" with a
      2u catastrophic stop (stop_price), no target, time_stop_min 45. Flat 15:50.
Live event source: the allow-list SYMBOLS (YAML `symbols: module`) = today's reaction-day names, built at import from
the calendar file CAL (env MCF_EARN_CAL; parquet with the earnings_yf.parquet columns symbol, date, session,
surprise_pct). Missing / unreadable calendar -> empty list -> no trades (fail safe). The side comes from the gap sign,
so both entries share the list. In the backtest the frame carries an e_rd (bool) column, which takes precedence.
Two sides, one file: a setup name ending in "-S" / "-short" is the short side (account-side: shorts easy-to-borrow
only; earnings-window shorts carry a 5 bp borrow estimate, 8 bp under $20, in the backtest). Account-side: day cap 30
entries over both sides (first by time, ADV20 desc)."""
import os
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

_NAME = __name__.lower()
SIDE = "short" if _NAME.endswith(("-s", "_s", "-short", "_short")) else "long"
_SGN = 1 if SIDE == "long" else -1
# ---- fit pick (round4/ULT-35/fitsel.json); filled in after the FIT grid
G = 3.0                   # |gap| floor, %
D = 0.0                   # fromOpen threshold against the gap, in daily ATRs
EXIT = "T"                # "T" t1s1 cap45 | "X" TX-45 with a 2u catastrophic stop
# ----
GEOM = "t1s1" if EXIT == "T" else "S"
WINDOW = (1015, 1330)
MIN_ADV, COST_R_MAX, PX_MIN, GAP_MAX = 30e6, 0.08, 10.0, 20.0
RSI5_SHORT_MIN = 25.0
UNIV_BAND = (-0.75, -0.30)
THIN = True
REFIRE_BARS, MAX_PER_DAY = 15, 2
REPEAT_SESSIONS = 10
NYSE_HOLIDAYS = frozenset("""
2024-01-01 2024-01-15 2024-02-19 2024-03-29 2024-05-27 2024-06-19 2024-07-04 2024-09-02 2024-11-28 2024-12-25
2025-01-01 2025-01-09 2025-01-20 2025-02-17 2025-04-18 2025-05-26 2025-06-19 2025-07-04 2025-09-01 2025-11-27
2025-12-25 2026-01-01 2026-01-19 2026-02-16 2026-04-03 2026-05-25 2026-06-19 2026-07-03 2026-09-07 2026-11-26
2026-12-25 2027-01-01 2027-01-18 2027-02-15 2027-03-26 2027-05-31 2027-06-18 2027-07-05 2027-09-06 2027-11-25
2027-12-24""".split())
CAL = Path(os.environ.get("MCF_EARN_CAL", str(Path(__file__).resolve().parents[3] / "state" / "earnings"
                                               / "earnings_cal.parquet")))
LAYERS = [
    "earnings reaction day (bmo report day / the session after an amc report)",
    "intake: price >= $10, ADV20 >= $30M, cost <= 0.08 of a 0.25-ATR unit",
    f"gap {'<=' if _SGN > 0 else '>='} {-_SGN * G:+g}% (and |gap| < 20%): the gap is AGAINST this side",
    (f"first bar back above VWAP and >= {D:g} daily ATR above the open (gap-down reclaim)" if _SGN > 0 else
     f"first bar back below VWAP and >= {D:g} daily ATR below the open (gap-up failure)"),
] + (["RSI(5) >= 25, easy to borrow"] if _SGN < 0 else
     ["skip while SPY is -0.30..-0.75% from its open and falling over 30 min"]) + [
    f"window: bar close {WINDOW[0]}-{WINDOW[1]} ET",
    "exit: +1R / -1R (R = 0.25 x daily ATR), 45-min time exit" if EXIT == "T" else
    "exit: 45-min time exit, catastrophic stop 0.5 x daily ATR",
]


# ---------------------------------------------------------------- calendar / event table (shared with bt.py)
def sessions(start: str, end: str) -> list[str]:
    """NYSE sessions start..end (weekdays minus NYSE_HOLIDAYS) - no market data needed, so look-ups never touch data."""
    d0, d1 = date.fromisoformat(start), date.fromisoformat(end)
    out, d = [], d0
    while d <= d1:
        if d.weekday() < 5 and d.isoformat() not in NYSE_HOLIDAYS:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def reaction_days(earn, sess: list[str]):
    """Event table: symbol, rd (reaction-day session), rd_i (index into sess), session, report_date, surprise_pct
    (clipped +-100; NaN = missing). bmo -> first session >= report date; amc -> first session > report date;
    dmh / unknown excluded; repeats of a symbol within REPEAT_SESSIONS sessions keep the first."""
    import pandas as pd
    e = earn[earn["session"].isin(["bmo", "amc"])].copy()
    e["report_date"] = pd.to_datetime(e["date"]).dt.strftime("%Y-%m-%d")
    arr = np.array(sess)
    side = np.where(e["session"].to_numpy() == "amc", "right", "left")
    i_l = np.searchsorted(arr, e["report_date"].to_numpy(), side="left")
    i_r = np.searchsorted(arr, e["report_date"].to_numpy(), side="right")
    e["rd_i"] = np.where(side == "right", i_r, i_l)
    e = e[(e["rd_i"] < len(arr)) & (e["report_date"] >= arr[0])]
    e["rd"] = arr[e["rd_i"].to_numpy()]
    e["surprise_pct"] = e["surprise_pct"].astype(float).clip(-100, 100)
    e = e.sort_values(["symbol", "rd_i"], kind="mergesort")
    keep, last = [], {}
    for idx, sym, ri in zip(e.index, e["symbol"].astype(str), e["rd_i"]):
        if sym in last and ri - last[sym] < REPEAT_SESSIONS:
            continue
        last[sym] = ri
        keep.append(idx)
    return e.loc[keep, ["symbol", "rd", "rd_i", "session", "report_date", "surprise_pct"]].reset_index(drop=True)


def today_symbols(day: str | None = None) -> frozenset:
    """Live allow-list: today's reaction-day names (both sides; the side comes from the gap sign)."""
    try:
        import pandas as pd
        day = day or datetime.now().strftime("%Y-%m-%d")
        if not CAL.exists():
            return frozenset()
        earn = pd.read_parquet(CAL, columns=["symbol", "date", "session", "surprise_pct"])
        d0 = (date.fromisoformat(day) - timedelta(days=40)).isoformat()
        earn = earn[pd.to_datetime(earn["date"]).dt.strftime("%Y-%m-%d").between(d0, day)]
        ev = reaction_days(earn, sessions(d0, day))
        return frozenset(ev.loc[ev["rd"] == day, "symbol"].astype(str))
    except Exception:       # fail safe: no calendar -> no trades
        return frozenset()


SYMBOLS = today_symbols()        # YAML `symbols: module` on both entries


# ---------------------------------------------------------------- features / signal
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


def _prev(x, key, mins):
    """x of the previous row of the same symbol-session, only when exactly 5 minutes earlier; else NaN."""
    out = np.full(len(x), np.nan)
    if len(x) > 1:
        ok = (key[1:] == key[:-1]) & (mins[1:] - mins[:-1] == 5)
        out[1:][ok] = x[:-1][ok]
    return out


def spy_r30(df, key) -> np.ndarray:
    import pandas as pd
    fo = df["spy_fo"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    m = _minutes(tod)
    s = pd.Series(np.where(tod >= 950, fo, np.nan), index=pd.MultiIndex.from_arrays([key, m]))
    s = s[~s.index.duplicated()]
    lag = s.reindex(pd.MultiIndex.from_arrays([key, m - 30])).to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return ((1 + fo / 100) / (1 + lag / 100) - 1) * 100


def features(df) -> dict:
    """Point-in-time inputs at each decision bar close (shared with the backtest: bt.py imports this)."""
    n = len(df)
    c = lambda k: df[k].to_numpy(dtype=float)   # noqa: E731
    px, atr, tod = c("close"), c("atr_d"), c("tod")
    key = _keys(df)
    mins = _minutes(tod)
    adv = c("adv20") if "adv20" in df.columns else np.full(n, np.inf)
    has_spy = "spy_fo" in df.columns
    fo = c("spy_fo") if has_spy else np.full(n, np.nan)
    r30 = spy_r30(df, key) if has_spy else np.full(n, np.nan)
    e_rd = df["e_rd"].to_numpy(dtype=bool) if "e_rd" in df.columns else np.ones(n, bool)      # live: allow-list
    with np.errstate(invalid="ignore", divide="ignore"):
        one = 0.01 + px * 1e-4
        cost_r = (one * _tod_mult(tod) + one + 0.02) / (0.25 * atr)
        gap = c("gap")
        sfo = c("fromOpen")
        foa = (px - px / (1 + sfo / 100)) / atr
        vd = c("vwapDistPct")
        intake = ((px >= PX_MIN) & (np.abs(gap) < GAP_MAX) & (atr > 0) & (cost_r <= COST_R_MAX) & (adv >= MIN_ADV)
                  & e_rd)
        univ_long_ok = has_spy & ~((fo >= UNIV_BAND[0]) & (fo <= UNIV_BAND[1]) & (r30 < 0)) if has_spy \
            else np.zeros(n, bool)
    return {"tod": tod, "close": px, "gap": gap, "vd": vd, "foa": foa, "rsi5": c("rsi5"),
            "vd_prev": _prev(vd, key, mins), "foa_prev": _prev(foa, key, mins), "cost_r": cost_r,
            "intake": intake, "univ_long_ok": np.asarray(univ_long_ok, bool), "spy_fo": fo, "spy_r30": r30}


def core(vd, foa, sgn, d) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return (sgn * vd > 0) & (sgn * foa >= d)


def fail_cross(r, sgn, d=None) -> np.ndarray:
    """First bar of the failure: core now, core false on the previous bar (which must exist)."""
    d = D if d is None else d
    prev_ok = ~np.isnan(r["vd_prev"]) & ~np.isnan(r["foa_prev"])
    return core(r["vd"], r["foa"], sgn, d) & prev_ok & ~core(r["vd_prev"], r["foa_prev"], sgn, d)


def signal(r, sgn, g=None, d=None) -> np.ndarray:
    """Intake + side rule (no window, no thinning). sgn = trade side; the gap is against it."""
    g = G if g is None else g
    with np.errstate(invalid="ignore"):
        m = r["intake"] & (-sgn * r["gap"] >= g) & fail_cross(r, sgn, d)
        if sgn > 0:
            m &= r["univ_long_ok"]
        else:
            m &= r["rsi5"] >= RSI5_SHORT_MIN
    return m


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
    r = features(df)
    tod = r["tod"]
    m = signal(r, _SGN) & (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return _thin(m, df) if THIN else m


def stop_price(f, i) -> float:
    """GEOM "S" (EXIT X): catastrophic stop 2u = 0.5 x atr_d beyond the decision close."""
    return float(f["close"].iloc[i]) - _SGN * 2 * 0.25 * float(f["atr_d"].iloc[i])
