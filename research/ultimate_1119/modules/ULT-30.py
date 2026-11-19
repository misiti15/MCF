# ULTIMATE CANDIDATE ULT-30 EARN-DAY2 (research only, not enabled in any account)
# research/ultimate_1119/round4/PLAN.md sec. 3 "ULT-30"; backtest research/ultimate_1119/round4/ULT-30/RESULTS.md
# Next: only a TIER A / BEATS result goes further, with the owner's yes AND an owner exception to the 4-day earnings
# blackout (config earnings_blackout_days: 4). Educational only - not financial advice.
"""ULT-30 EARN-DAY2 - day-after-earnings continuation, LONG + SHORT. PARTLY CHECK-INFORMED.

Thesis: PEAD is strongest in the first days. On RD+1 (the session after the earnings reaction day RD) the full reaction
is known before the open; trade in the reaction direction while the day-2 tape holds VWAP and the open.
Rule (point-in-time at the decision 5-minute bar close; frame columns gap, vwapDistPct, fromOpen, rsi5; context spy_fo):
  event    session RD+1 of a scheduled earnings report (RD: bmo -> report date; amc -> next session; dmh / unknown
           excluded; repeats of a symbol within 10 sessions keep the first).
  REACT    close(RD) / close(RD-1) - 1 minus SPY's close(RD) / close(RD-1) - 1, in %, from daily bars dated <= RD
           (both known before the RD+1 open). |REACT| >= T. Side s = sign(REACT).
  intake   price >= $10; |gap| < 20%; atr_d > 0; cost_r <= 0.08 (LR8 stop-out round trip
           ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / u, u = 0.25 x atr_d); ADV20 >= $30M (live: YAML min_adv 30e6).
  rule     s x gap >= -0.5% (no reversal gap); s x vwapDistPct > 0; s x fromOpen >= 0; RSI5 <= 85 (long) / >= 25 (short).
  universal  long: skip while SPY is -0.30..-0.75% from its open AND SPY's 30-min change < 0 (no SPY context -> no
           long signal). short: no short if gap >= +0.5% (implied by s x gap >= -0.5 up to the boundary; enforced) or
           RSI5 < 25.
  SIDES    "both" or "long" (long-only: the short entry never fires).
  window   bar close 09:50-12:30 (YAML window must match).
  refire   (THIN) max 2 per symbol-session, the 2nd >= REFIRE_BARS decision bars after the 1st (backtest chain: >= 30 min
           after the first lot's exit, one lot per symbol). YAML refire true, refire_cooldown 0.
Exit: EXIT "T" -> GEOM t1s1 (+1u / -1u) with YAML time_stop_min 45, time_stop_min_r 99; EXIT "X" -> GEOM "S" with a
      2u catastrophic stop (stop_price), no target, time_stop_min 45. Flat 15:50.
Live event source: the allow-list SYMBOLS (YAML `symbols: module`) = today's RD+1 names whose REACT passes T with the
sign of this side, built at import by the same day2_events() the backtest uses, from
  - the calendar file CAL (env MCF_EARN_CAL; parquet with the earnings_yf columns symbol, date, session), and
  - a daily-close file DAILY (env MCF_DAILY_CLOSES; parquet symbol, date, close; must include SPY and the last two
    sessions before today - the runner's pre-open prior build already fetches 30 daily bars per name).
Missing / unreadable files or missing closes -> empty list -> no trades (fail safe). Fresh import per session.
In the backtest the frame carries e_d2 (bool) and e_react (REACT %) columns, which take precedence.
Two sides, one file: a setup name ending in "-S" / "-short" is the short side (account-side: shorts easy-to-borrow
only; earnings-window shorts carry a 5 bp borrow estimate, 8 bp under $20, in the backtest). Day cap 30 entries over
both sides (first by time, ADV20 desc)."""
import os
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

_NAME = __name__.lower()
SIDE = "short" if _NAME.endswith(("-s", "_s", "-short", "_short")) else "long"
_SGN = 1 if SIDE == "long" else -1
# ---- fit-frozen pick 30b (round4/ULT-30/fitsel.json, frozen 2026-11-19T09:01Z before any CHECK data); CHECK FAIL
T = 4.0                   # |REACT| floor, % (relative to SPY)
SIDES = "both"            # "both" | "long"
EXIT = "X"                # "T" t1s1 cap45 | "X" TX-45 with a 2u catastrophic stop
# ----
GEOM = "t1s1" if EXIT == "T" else "S"
WINDOW = (950, 1230)
MIN_ADV, COST_R_MAX, PX_MIN, GAP_MAX = 30e6, 0.08, 10.0, 20.0
REV_GAP = -0.5            # s x gap >= -0.5%
RSI5_LONG_MAX, RSI5_SHORT_MIN = 85.0, 25.0
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
_STATE = Path(__file__).resolve().parents[3] / "state" / "earnings"
CAL = Path(os.environ.get("MCF_EARN_CAL", str(_STATE / "earnings_cal.parquet")))
DAILY = Path(os.environ.get("MCF_DAILY_CLOSES", str(_STATE / "daily_closes.parquet")))
LAYERS = [
    "day after an earnings reaction day (RD+1)",
    f"reaction day close-to-close move vs SPY {'>=' if _SGN > 0 else '<='} {_SGN * T:+g}%",
    "intake: price >= $10, ADV20 >= $30M, cost <= 0.08 of a 0.25-ATR unit, |gap| < 20%",
    "no gap against the reaction (> 0.5%)",
    "close on the reaction side of VWAP and not below/above today's open",
    "RSI(5) <= 85" if _SGN > 0 else "RSI(5) >= 25, easy to borrow",
] + (["skip while SPY is -0.30..-0.75% from its open and falling over 30 min"] if _SGN > 0 else []) + [
    f"window: bar close {WINDOW[0]}-{WINDOW[1]} ET",
    "exit: +1R / -1R (R = 0.25 x daily ATR), 45-min time exit" if EXIT == "T" else
    "exit: 45-min time exit, catastrophic stop 0.5 x daily ATR",
]


# ---------------------------------------------------------------- calendar / event table (shared with bt.py)
def sessions(start: str, end: str) -> list[str]:
    """NYSE sessions start..end (weekdays minus NYSE_HOLIDAYS) - no market data needed."""
    d0, d1 = date.fromisoformat(start), date.fromisoformat(end)
    out, d = [], d0
    while d <= d1:
        if d.weekday() < 5 and d.isoformat() not in NYSE_HOLIDAYS:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def reaction_days(earn, sess: list[str]):
    """Event table (same spec as ULT-28): symbol, rd, rd_i (index into sess), session, report_date, surprise_pct."""
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
    e["surprise_pct"] = e["surprise_pct"].astype(float).clip(-100, 100) if "surprise_pct" in e else np.nan
    e = e.sort_values(["symbol", "rd_i"], kind="mergesort")
    keep, last = [], {}
    for idx, sym, ri in zip(e.index, e["symbol"].astype(str), e["rd_i"]):
        if sym in last and ri - last[sym] < REPEAT_SESSIONS:
            continue
        last[sym] = ri
        keep.append(idx)
    return e.loc[keep, ["symbol", "rd", "rd_i", "session", "report_date", "surprise_pct"]].reset_index(drop=True)


def day2_events(earn, sess: list[str], daily):
    """RD+1 table: symbol, d2 (RD+1 session), rd, rdm1, react (%: symbol close-to-close RD-1 -> RD minus SPY's).
    daily: DataFrame symbol, date (YYYY-MM-DD), close; only rows dated <= RD are ever used. Events whose RD-1 / RD /
    RD+1 fall outside sess, or whose closes (symbol or SPY) are missing, are dropped (never filled)."""
    import pandas as pd
    ev = reaction_days(earn, sess)
    ev = ev[(ev["rd_i"] >= 1) & (ev["rd_i"] + 1 < len(sess))].copy()
    arr = np.array(sess)
    ev["rdm1"] = arr[ev["rd_i"].to_numpy() - 1]
    ev["d2"] = arr[ev["rd_i"].to_numpy() + 1]
    dl = daily[["symbol", "date", "close"]].copy()
    dl["date"] = pd.to_datetime(dl["date"]).dt.strftime("%Y-%m-%d")
    cl = dict(zip(dl["symbol"].astype(str) + "|" + dl["date"], dl["close"].astype(float)))
    g = lambda s, d: np.array([cl.get(a + "|" + b, np.nan) for a, b in zip(s, d)], float)   # noqa: E731
    sym = ev["symbol"].astype(str).to_numpy()
    spy = np.full(len(ev), "SPY")
    with np.errstate(invalid="ignore", divide="ignore"):
        r_sym = g(sym, ev["rd"]) / g(sym, ev["rdm1"]) - 1
        r_spy = g(spy, ev["rd"]) / g(spy, ev["rdm1"]) - 1
    ev["react"] = (r_sym - r_spy) * 100
    ev = ev[np.isfinite(ev["react"].to_numpy())]
    return ev[["symbol", "d2", "rd", "rdm1", "react", "session", "surprise_pct"]].reset_index(drop=True)


def today_symbols(day: str | None = None, side: str = SIDE, t: float | None = None, sides: str | None = None) -> frozenset:
    """Live allow-list: today's RD+1 names with |REACT| >= T and sign(REACT) = this side."""
    t = T if t is None else t
    sides = SIDES if sides is None else sides
    try:
        import pandas as pd
        if side == "short" and sides == "long":
            return frozenset()
        day = day or datetime.now().strftime("%Y-%m-%d")
        if not CAL.exists() or not DAILY.exists():
            return frozenset()
        d0 = (date.fromisoformat(day) - timedelta(days=40)).isoformat()
        earn = pd.read_parquet(CAL, columns=["symbol", "date", "session"])
        earn = earn[pd.to_datetime(earn["date"]).dt.strftime("%Y-%m-%d").between(d0, day)]
        daily = pd.read_parquet(DAILY, columns=["symbol", "date", "close"])
        daily = daily[pd.to_datetime(daily["date"]).dt.strftime("%Y-%m-%d") < day]       # strictly before today
        ev = day2_events(earn, sessions(d0, day), daily)
        ev = ev[ev["d2"] == day]
        sg = 1 if side == "long" else -1
        ev = ev[sg * ev["react"] >= t]
        return frozenset(ev["symbol"].astype(str))
    except Exception:       # fail safe: no calendar / closes -> no trades
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
    adv = c("adv20") if "adv20" in df.columns else np.full(n, np.inf)
    has_spy = "spy_fo" in df.columns
    fo = c("spy_fo") if has_spy else np.full(n, np.nan)
    r30 = spy_r30(df, key) if has_spy else np.full(n, np.nan)
    e_d2 = df["e_d2"].to_numpy(dtype=bool) if "e_d2" in df.columns else np.ones(n, bool)      # live: allow-list
    # live: the allow-list already holds |REACT| >= T with this side's sign -> react = +/- inf on the module side
    e_react = c("e_react") if "e_react" in df.columns else np.full(n, _SGN * np.inf)
    with np.errstate(invalid="ignore", divide="ignore"):
        one = 0.01 + px * 1e-4
        cost_r = (one * _tod_mult(tod) + one + 0.02) / (0.25 * atr)
        gap = c("gap")
        intake = ((px >= PX_MIN) & (np.abs(gap) < GAP_MAX) & (atr > 0) & (cost_r <= COST_R_MAX) & (adv >= MIN_ADV)
                  & e_d2)
        univ_long_ok = has_spy & ~((fo >= UNIV_BAND[0]) & (fo <= UNIV_BAND[1]) & (r30 < 0)) if has_spy \
            else np.zeros(n, bool)
    return {"tod": tod, "close": px, "gap": gap, "vd": c("vwapDistPct"), "fo": c("fromOpen"), "rsi5": c("rsi5"),
            "cost_r": cost_r, "intake": intake, "univ_long_ok": np.asarray(univ_long_ok, bool), "spy_fo": fo,
            "spy_r30": r30, "react": e_react}


def rule(r, sgn) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        m = (sgn * r["gap"] >= REV_GAP) & (sgn * r["vd"] > 0) & (sgn * r["fo"] >= 0)
        if sgn > 0:
            return m & (r["rsi5"] <= RSI5_LONG_MAX) & r["univ_long_ok"]
        return m & (r["rsi5"] >= RSI5_SHORT_MIN) & (r["gap"] < 0.5)


def signal(r, sgn, t=None, sides=None) -> np.ndarray:
    """Intake + event side/size + day-2 rule (no window, no thinning)."""
    t = T if t is None else t
    sides = SIDES if sides is None else sides
    if sgn < 0 and sides == "long":
        return np.zeros(len(r["tod"]), bool)
    with np.errstate(invalid="ignore"):
        return r["intake"] & (sgn * r["react"] >= t) & rule(r, sgn)


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
