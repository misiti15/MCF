# ULTIMATE CANDIDATE ULT-28 EARN-GO (research only, not enabled in any account)
# research/ultimate_1119/round4/PLAN.md sec. 3 "ULT-28"; backtest research/ultimate_1119/round4/ULT-28/RESULTS.md
# Next: only a TIER A / BEATS result goes further, with the owner's yes AND an owner exception to the 4-day earnings
# blackout (config earnings_blackout_days: 4). Educational only - not financial advice.
"""ULT-28 EARN-GO - earnings reaction-day continuation with the gap, LONG + SHORT. PARTLY CHECK-INFORMED.

Thesis: the reaction day (bmo report day, or the session after an amc report) is the one day a single-name move is
known to carry information; information drifts (PEAD), so trade WITH the gap while it is holding, from 09:50.
Rule (point-in-time at the decision 5-minute bar close; frame columns gap, vwapDistPct, fromOpen, rsi5, dist_hod_atr,
dist_lod_atr; context spy_fo):
  event    reaction day RD of a scheduled earnings report (bmo -> report date; amc -> next session; dmh / unknown
           excluded; repeats of a symbol within 10 sessions keep the first). Surprise % is public before the RD open.
  intake   price >= $10; G <= |gap| < 20%; atr_d > 0; cost_r <= 0.08 (LR8 stop-out round trip
           ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / u, u = 0.25 x atr_d); ADV20 >= $30M (live: YAML min_adv 30e6).
  side     s = sign(gap): gap >= +G -> long entry, gap <= -G -> short entry.
  HOLD     s x vwapDistPct > 0 (close on the gap side of VWAP); s x fromOpen >= 0; RSI5 <= 85 (long) / >= 25 (short).
  PUSH     HOLD and a new session extreme on this bar: dist_hod_atr <= 0.02 (long) / dist_lod_atr <= 0.02 (short),
           the previous bar (exactly 5 min earlier, same session) not at the extreme (so never on the 09:50 bar).
  S        "agree": sign(surprise_pct) = s (missing -> excluded); "any": ignored.
  universal  long: skip while SPY is -0.30..-0.75% from its open AND SPY's 30-min change < 0 (no SPY context -> no
           long signal). short: RSI5 >= 25 (in HOLD); gap <= -G implies gap < +0.5%.
  window   bar close 09:50-12:30 (YAML window must match).
  refire   (THIN) max 2 per symbol-session, the 2nd >= REFIRE_BARS decision bars after the 1st (backtest chain: >= 30 min
           after the first lot's exit, one lot per symbol). YAML refire true, refire_cooldown 0.
Exit: EXIT "T" -> GEOM t1s1 (+1u / -1u) with YAML time_stop_min 45, time_stop_min_r 99; EXIT "X" -> GEOM "S" with a
      2u catastrophic stop (stop_price), no target, time_stop_min 45. Flat 15:50.
Live event source: the allow-list SYMBOLS (YAML `symbols: module`) = today's reaction-day names for this side (and,
with S "agree", the matching surprise sign), built at import from the calendar file CAL (env MCF_EARN_CAL; parquet
with the earnings_yf.parquet columns symbol, date, session, surprise_pct). Missing / unreadable calendar -> empty list
-> no trades (fail safe). The runner must re-import the module each session (it does: a fresh process per session).
In the backtest the frame carries e_rd (bool) and e_surp (surprise %) columns, which take precedence.
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
# ---- fit-frozen pick 28a (round4/ULT-28/fitsel.json, frozen 2026-11-19T08:52Z before any CHECK data); CHECK FAIL
G = 3.0                   # |gap| floor, %
ENTRY = "HOLD"            # "HOLD" | "PUSH"
S = "agree"               # "agree" | "any"
EXIT = "T"                # "T" t1s1 cap45 | "X" TX-45 with a 2u catastrophic stop
# ----
GEOM = "t1s1" if EXIT == "T" else "S"
WINDOW = (950, 1230)
MIN_ADV, COST_R_MAX, PX_MIN, GAP_MAX = 30e6, 0.08, 10.0, 20.0
RSI5_LONG_MAX, RSI5_SHORT_MIN = 85.0, 25.0
EXT_ATR = 0.02
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
    f"gap {'>=' if _SGN > 0 else '<='} {_SGN * G:+g}% (and |gap| < 20%)",
    "close on the gap side of VWAP and not below/above the open (gap holding)",
    "RSI(5) <= 85" if _SGN > 0 else "RSI(5) >= 25, easy to borrow",
] + (["new session high on this bar" if _SGN > 0 else "new session low on this bar"] if ENTRY == "PUSH" else []) + (
    ["EPS surprise agrees with the gap"] if S == "agree" else []) + (
    ["skip while SPY is -0.30..-0.75% from its open and falling over 30 min"] if _SGN > 0 else []) + [
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


def today_symbols(day: str | None = None, side: str = SIDE, s_mode: str = S) -> frozenset:
    """Live allow-list: today's reaction-day names (with S "agree": surprise sign matching this side)."""
    try:
        import pandas as pd
        day = day or datetime.now().strftime("%Y-%m-%d")
        if not CAL.exists():
            return frozenset()
        earn = pd.read_parquet(CAL, columns=["symbol", "date", "session", "surprise_pct"])
        d0 = (date.fromisoformat(day) - timedelta(days=40)).isoformat()
        earn = earn[pd.to_datetime(earn["date"]).dt.strftime("%Y-%m-%d").between(d0, day)]
        ev = reaction_days(earn, sessions(d0, day))
        ev = ev[ev["rd"] == day]
        if s_mode == "agree":
            sg = 1 if side == "long" else -1
            ev = ev[np.sign(ev["surprise_pct"]) == sg]
        return frozenset(ev["symbol"].astype(str))
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
    dh, dl = c("dist_hod_atr"), c("dist_lod_atr")
    e_rd = df["e_rd"].to_numpy(dtype=bool) if "e_rd" in df.columns else np.ones(n, bool)      # live: allow-list
    e_surp = c("e_surp") if "e_surp" in df.columns else None                                  # live: allow-list
    with np.errstate(invalid="ignore", divide="ignore"):
        one = 0.01 + px * 1e-4
        cost_r = (one * _tod_mult(tod) + one + 0.02) / (0.25 * atr)
        gap = c("gap")
        intake = ((px >= PX_MIN) & (np.abs(gap) < GAP_MAX) & (atr > 0) & (cost_r <= COST_R_MAX) & (adv >= MIN_ADV)
                  & e_rd)
        univ_long_ok = has_spy & ~((fo >= UNIV_BAND[0]) & (fo <= UNIV_BAND[1]) & (r30 < 0)) if has_spy \
            else np.zeros(n, bool)
    return {"tod": tod, "close": px, "gap": gap, "vd": c("vwapDistPct"), "fo": c("fromOpen"), "rsi5": c("rsi5"),
            "dh": dh, "dl": dl, "dh_prev": _prev(dh, key, mins), "dl_prev": _prev(dl, key, mins), "cost_r": cost_r,
            "intake": intake, "univ_long_ok": np.asarray(univ_long_ok, bool), "spy_fo": fo, "spy_r30": r30,
            "e_surp": e_surp}


def hold(r, sgn) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        if sgn > 0:
            return (r["vd"] > 0) & (r["fo"] >= 0) & (r["rsi5"] <= RSI5_LONG_MAX) & r["univ_long_ok"]
        return (r["vd"] < 0) & (r["fo"] <= 0) & (r["rsi5"] >= RSI5_SHORT_MIN)


def push(r, sgn) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        if sgn > 0:
            return (r["dh"] <= EXT_ATR) & (r["dh_prev"] > EXT_ATR)          # NaN prev (09:50) -> False
        return (r["dl"] <= EXT_ATR) & (r["dl_prev"] > EXT_ATR)


def agree(r, sgn) -> np.ndarray:
    if r["e_surp"] is None:
        return np.ones(len(r["tod"]), bool)      # live: the allow-list already applies the surprise sign
    with np.errstate(invalid="ignore"):
        return np.sign(r["e_surp"]) == sgn      # NaN -> False (missing excluded)


def signal(r, sgn, g=None, entry=None, s_mode=None) -> np.ndarray:
    """Intake + side rule (no window, no thinning)."""
    g = G if g is None else g
    entry = ENTRY if entry is None else entry
    s_mode = S if s_mode is None else s_mode
    with np.errstate(invalid="ignore"):
        m = r["intake"] & (sgn * r["gap"] >= g) & hold(r, sgn)
    if entry == "PUSH":
        m &= push(r, sgn)
    if s_mode == "agree":
        m &= agree(r, sgn)
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
