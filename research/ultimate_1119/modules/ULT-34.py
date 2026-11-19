# ULTIMATE CANDIDATE ULT-34 NO-NEWS REVERSAL (research only, not enabled in any account)
# research/ultimate_1119/round4/PLAN.md sec. 3 "ULT-34"; backtest research/ultimate_1119/round4/ULT-34/RESULTS.md
# Next: only a TIER A / BEATS result goes further, and only with the owner's yes. Respects the 4-day earnings blackout
# by construction (no report in d-5..d+1). Educational only - not financial advice.
"""ULT-34 NO-NEWS REVERSAL - day-2 fade of an extreme prior-day move with no earnings, LONG + SHORT. NOT check-informed.

Thesis: a large one-day move with no scheduled news is more likely a liquidity shock, and those revert (Chan 2003,
JFE). The side comes from the name's own move (not SPY), so it covers both tapes.
Event at session d (point-in-time: daily bars dated < d only):
  r1       close(d-1) / close(d-2) - 1, in %, with d-2, d-1 consecutive NYSE sessions both present in the daily data
           (no fill across a gap / the locked block).
  size     |r1| >= K x atr_d%, atr_d% = 100 x ATR14(daily bars dated < d) / close(d-1) (= the lab frame's atr_d and the
           live ctx.atr: mcf.features.atr, simple 14-day mean true range).
  no news  no scheduled earnings report for the symbol whose reaction-session position lies in d-5..d+1 (any report
           session; amc maps to the next session). Symbols NOT covered by the earnings calendar are excluded unless
           they are (non-leveraged) ETFs, which have no earnings (fail safe). Leveraged / inverse / volatility funds
           (LEV, ULT-31_symbols.json) are excluded from events altogether.
  side     s = -sign(r1) (fade the prior-day move).
Intake (decision 5-minute bar close): price >= $10; |gap| < 20%; atr_d > 0; cost_r <= 0.08 (LR8 stop-out round trip
  ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / u, u = 0.25 x atr_d); ADV20 >= $50M (live: YAML min_adv 50e6).
Rule: s x gap <= +0.5 x |r1| (today has not already fully reverted at the open); s x vwapDistPct > 0;
  confirm F: "V" = VWAP side only, "VO" = VWAP side AND s x fromOpen >= 0.
Universal: long - skip while SPY is -0.30..-0.75% from its open AND SPY's 30-min change < 0 (no SPY context -> no
  long); short - gap < +0.5% and RSI5 >= 25; shorts easy-to-borrow only (account side), borrow 1.2 bp (3 bp < $20).
Window: bar close 10:00-13:00 (YAML window must match). Refire (THIN): max 2 per symbol-session, 2nd >= REFIRE_BARS
  decision bars after the 1st (backtest chain: >= 30 min after the first lot's exit, one lot per symbol).
Exit: EXIT "T" -> GEOM t1s1 (+1u / -1u), time_stop_min 45, time_stop_min_r 99; EXIT "X" -> GEOM "S" with a 2u
  catastrophic stop (stop_price), no target, time_stop_min 45. Flat 15:50.
Live event source: the allow-list SYMBOLS (YAML `symbols: module`) = today's event names with this side, built at
import by the same nonews_events() the backtest uses, from
  - the calendar CAL (env MCF_EARN_CAL; parquet symbol, date, session), and
  - a daily-bar file DAILY (env MCF_DAILY_BARS; parquet symbol, date, high, low, close; >= 16 sessions before today;
    only rows dated strictly before today are read).
  The live frame carries no symbol, so the per-name |r1| for the gap rule is looked up by the prior-day high / low
  fingerprint (prev_high = close + dist_pdh_atr x atr_d, prev_low = close - dist_pdl_atr x atr_d, both exact in the
  live frame); no unique match -> no signal. Missing files / closes -> empty list -> no trades (fail safe).
In the backtest the frame carries e_ok (event bool for this side), e_r1 (r1 %) and e_k (|r1| / atr_d%), which take
precedence. Two sides, one file: a setup name ending in "-S" / "-short" is the short side."""
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

_NAME = __name__.lower()
SIDE = "short" if _NAME.endswith(("-s", "_s", "-short", "_short")) else "long"
_SGN = 1 if SIDE == "long" else -1
# ---- fit-frozen pick 34d (round4/ULT-34/fitsel.json, frozen before any CHECK data)
K = 2.0                   # |r1| floor in daily-ATR% multiples
F = "VO"                  # "V" VWAP side | "VO" VWAP side and not through today's open
EXIT = "X"                # "T" t1s1 cap45 | "X" TX-45 with a 2u catastrophic stop
# ----
GEOM = "t1s1" if EXIT == "T" else "S"
WINDOW = (1000, 1300)
MIN_ADV, COST_R_MAX, PX_MIN, GAP_MAX = 50e6, 0.08, 10.0, 20.0
GAP_FRAC = 0.5            # s x gap <= GAP_FRAC x |r1|
RSI5_SHORT_MIN = 25.0
UNIV_BAND = (-0.75, -0.30)
EARN_LO, EARN_HI = -5, 1  # no report reaction position in d-5..d+1
THIN = True
REFIRE_BARS, MAX_PER_DAY = 15, 2
NYSE_HOLIDAYS = frozenset("""
2024-01-01 2024-01-15 2024-02-19 2024-03-29 2024-05-27 2024-06-19 2024-07-04 2024-09-02 2024-11-28 2024-12-25
2025-01-01 2025-01-09 2025-01-20 2025-02-17 2025-04-18 2025-05-26 2025-06-19 2025-07-04 2025-09-01 2025-11-27
2025-12-25 2026-01-01 2026-01-19 2026-02-16 2026-04-03 2026-05-25 2026-06-19 2026-07-03 2026-09-07 2026-11-26
2026-12-25 2027-01-01 2027-01-18 2027-02-15 2027-03-26 2027-05-31 2027-06-18 2027-07-05 2027-09-06 2027-11-25
2027-12-24""".split())
_U = json.loads((Path(__file__).resolve().parent / "ULT-31_symbols.json").read_text())
ETF = frozenset(_U["ETF"])
LEV = frozenset(_U["LEV"])
_STATE = Path(__file__).resolve().parents[3] / "state" / "earnings"
CAL = Path(os.environ.get("MCF_EARN_CAL", str(_STATE / "earnings_cal.parquet")))
DAILY = Path(os.environ.get("MCF_DAILY_BARS", str(_STATE / "daily_bars.parquet")))
LAYERS = [
    f"prior-day close-to-close move {'<=' if _SGN > 0 else '>='} {-_SGN * K:+g} x daily ATR% (fade it)",
    "no scheduled earnings in the 5 sessions before through the session after; no leveraged/inverse funds",
    "intake: price >= $10, ADV20 >= $50M, cost <= 0.08 of a 0.25-ATR unit, |gap| < 20%",
    "today's gap has not already retraced more than half the prior-day move",
    "close on the fade side of VWAP" + (" and not back through today's open" if F == "VO" else ""),
] + (["skip while SPY is -0.30..-0.75% from its open and falling over 30 min"] if _SGN > 0 else
     ["gap < +0.5%, RSI(5) >= 25, easy to borrow"]) + [
    f"window: bar close {WINDOW[0]}-{WINDOW[1]} ET",
    "exit: +1R / -1R (R = 0.25 x daily ATR), 45-min time exit" if EXIT == "T" else
    "exit: 45-min time exit, catastrophic stop 0.5 x daily ATR",
]


# ---------------------------------------------------------------- calendar / event table (shared with bt.py)
def sessions(start: str, end: str) -> list[str]:
    d0, d1 = date.fromisoformat(start), date.fromisoformat(end)
    out, d = [], d0
    while d <= d1:
        if d.weekday() < 5 and d.isoformat() not in NYSE_HOLIDAYS:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def report_positions(earn, sess: list[str]):
    """symbol, rd_i: reaction-session position of every scheduled report (amc -> next session; else the report date)."""
    import pandas as pd
    rd = pd.to_datetime(earn["date"]).dt.strftime("%Y-%m-%d").to_numpy()
    arr = np.array(sess)
    amc = earn["session"].astype(str).to_numpy() == "amc"
    ri = np.where(amc, np.searchsorted(arr, rd, "right"), np.searchsorted(arr, rd, "left"))
    return pd.DataFrame({"symbol": earn["symbol"].astype(str).to_numpy(), "rd_i": ri})


def nonews_events(daily, earn, sess: list[str], with_atr: bool = False):
    """Rows (symbol, d) with r1 (%), prev_close, news (bool: report in d-5..d+1), covered (calendar or ETF), lev.
    daily: symbol, date, close (+ high, low when with_atr: atr14 from bars dated < d). Only d-1 / d-2 (and older for the
    ATR) are read for session d; r1 needs d-2, d-1 consecutive sessions present (never filled)."""
    import pandas as pd
    sidx = {x: i for i, x in enumerate(sess)}
    dl = daily.copy()
    dl["date"] = pd.to_datetime(dl["date"]).dt.strftime("%Y-%m-%d")
    dl["symbol"] = dl["symbol"].astype(str)
    dl = dl[dl["date"].isin(sidx)].copy()
    dl["i"] = dl["date"].map(sidx)
    dl = dl.sort_values(["symbol", "i"], kind="mergesort")
    g = dl.groupby("symbol", sort=False)
    prv, pi = g["close"].shift(), g["i"].shift()
    dl["r1"] = np.where(dl["i"] - pi == 1, (dl["close"] / prv - 1) * 100, np.nan)
    if with_atr:
        # = mcf.features.atr per symbol (simple 14-day mean true range through this row's date)
        tr = np.maximum.reduce([(dl["high"] - dl["low"]).to_numpy(float), (dl["high"] - prv).abs().to_numpy(float),
                                (dl["low"] - prv).abs().to_numpy(float)])
        tr = np.where(prv.isna().to_numpy(), (dl["high"] - dl["low"]).to_numpy(float), tr)
        dl["atr"] = pd.Series(tr, index=dl.index).groupby(dl["symbol"], sort=False).transform(
            lambda x: x.rolling(14, min_periods=14).mean())
    dl = dl[dl["r1"].notna() & (dl["i"] + 1 < len(sess))]
    arr = np.array(sess)
    out = pd.DataFrame({"symbol": dl["symbol"].to_numpy(), "d": arr[(dl["i"] + 1).to_numpy()],
                        "d_i": (dl["i"] + 1).to_numpy(), "r1": dl["r1"].to_numpy(),
                        "prev_close": dl["close"].to_numpy()})
    if with_atr:
        out["atr"] = dl["atr"].to_numpy()
        out["prev_high"], out["prev_low"] = dl["high"].to_numpy(), dl["low"].to_numpy()
    rp = report_positions(earn, sess)
    bad = set()
    for s, ri in zip(rp["symbol"], rp["rd_i"]):
        for dd in range(ri - EARN_HI, ri - EARN_LO + 1):     # RD in [d-5, d+1]  <=>  d in [RD-1, RD+5]
            bad.add((s, dd))
    covered = set(rp["symbol"]) | set(ETF)
    out["news"] = [(s, i) in bad for s, i in zip(out["symbol"], out["d_i"])]
    out["covered"] = out["symbol"].isin(covered).to_numpy()
    out["lev"] = out["symbol"].isin(LEV).to_numpy()
    return out


def today_events(day: str | None = None, side: str = SIDE, k: float | None = None):
    """Live: today's qualifying names for this side -> DataFrame symbol, r1, prev_high, prev_low (empty on any error)."""
    import pandas as pd
    k = K if k is None else k
    empty = pd.DataFrame(columns=["symbol", "r1", "prev_high", "prev_low"])
    try:
        day = day or datetime.now().strftime("%Y-%m-%d")
        if not CAL.exists() or not DAILY.exists():
            return empty
        d0 = (date.fromisoformat(day) - timedelta(days=60)).isoformat()
        d1 = (date.fromisoformat(day) + timedelta(days=10)).isoformat()
        earn = pd.read_parquet(CAL, columns=["symbol", "date", "session"])
        ed = pd.to_datetime(earn["date"]).dt.strftime("%Y-%m-%d")
        earn = earn[ed.between(d0, d1)]
        daily = pd.read_parquet(DAILY, columns=["symbol", "date", "high", "low", "close"])
        daily = daily[pd.to_datetime(daily["date"]).dt.strftime("%Y-%m-%d") < day]       # strictly before today
        ev = nonews_events(daily, earn, sessions(d0, d1), with_atr=True)
        ev = ev[(ev["d"] == day) & ~ev["news"] & ev["covered"] & ~ev["lev"]]
        atrp = 100 * ev["atr"] / ev["prev_close"]
        sg = 1 if side == "long" else -1
        ev = ev[(np.abs(ev["r1"]) >= k * atrp) & (-np.sign(ev["r1"]) == sg) & (atrp > 0)]
        return ev[["symbol", "r1", "prev_high", "prev_low"]].reset_index(drop=True)
    except Exception:       # fail safe
        return empty


_EV = today_events()
SYMBOLS = frozenset(_EV["symbol"].astype(str))        # YAML `symbols: module` on both entries


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


def _live_r1(df, ev=None) -> np.ndarray:
    """Live (no e_* columns): per-row r1 from the allow-list, matched on the prior-day high / low fingerprint."""
    ev = _EV if ev is None else ev
    n = len(df)
    out = np.full(n, np.nan)
    if not len(ev) or not {"dist_pdh_atr", "dist_pdl_atr"} <= set(df.columns):
        return out
    c = df["close"].to_numpy(float)
    a = df["atr_d"].to_numpy(float)
    ph = c + df["dist_pdh_atr"].to_numpy(float) * a
    pl = c - df["dist_pdl_atr"].to_numpy(float) * a
    eh, el, er = (ev[k].to_numpy(float) for k in ("prev_high", "prev_low", "r1"))
    for i in range(n):
        tol = max(0.011, 2e-4 * c[i]) if np.isfinite(c[i]) else 0
        hit = np.flatnonzero((np.abs(eh - ph[i]) <= tol) & (np.abs(el - pl[i]) <= tol))
        if len(hit) == 1:
            out[i] = er[hit[0]]
    return out


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
    if "e_r1" in df.columns:          # backtest
        e_ok = df["e_ok"].to_numpy(dtype=bool)
        r1, ek = c("e_r1"), c("e_k")
    else:                             # live: the allow-list already holds K, no-news, side
        r1 = _live_r1(df)
        e_ok = np.isfinite(r1)
        ek = np.where(e_ok, np.inf, np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        one = 0.01 + px * 1e-4
        cost_r = (one * _tod_mult(tod) + one + 0.02) / (0.25 * atr)
        gap = c("gap")
        intake = ((px >= PX_MIN) & (np.abs(gap) < GAP_MAX) & (atr > 0) & (cost_r <= COST_R_MAX) & (adv >= MIN_ADV)
                  & e_ok)
        univ_long_ok = (~((fo >= UNIV_BAND[0]) & (fo <= UNIV_BAND[1]) & (r30 < 0))) if has_spy else np.zeros(n, bool)
    return {"tod": tod, "close": px, "gap": gap, "vd": c("vwapDistPct"), "fo": c("fromOpen"), "rsi5": c("rsi5"),
            "cost_r": cost_r, "intake": intake, "univ_long_ok": np.asarray(univ_long_ok, bool), "spy_fo": fo,
            "spy_r30": r30, "r1": r1, "k": ek}


def rule(r, sgn, f=None) -> np.ndarray:
    f = F if f is None else f
    with np.errstate(invalid="ignore"):
        m = (sgn * r["gap"] <= GAP_FRAC * np.abs(r["r1"])) & (sgn * r["vd"] > 0)
        if f == "VO":
            m &= sgn * r["fo"] >= 0
        if sgn > 0:
            return m & r["univ_long_ok"]
        return m & (r["rsi5"] >= RSI5_SHORT_MIN) & (r["gap"] < 0.5)


def signal(r, sgn, k=None, f=None) -> np.ndarray:
    """Intake + event (side = -sign(r1), |r1| >= k x atr_d%) + rule (no window, no thinning)."""
    k = K if k is None else k
    with np.errstate(invalid="ignore"):
        return r["intake"] & (-np.sign(r["r1"]) == sgn) & (r["k"] >= k) & rule(r, sgn, f)


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
