"""Month-end rebalancing forward shadow (MEREBFWD-1127). Rule frozen 2026-11-27 - see RULE.md.

    python research/forward/month_end/shadow.py --date YYYY-MM-DD [--date ...]   (acts only on a month's last session)
    python research/forward/month_end/shadow.py --score

Scout MEREB1 (research/bdi/scout_1127/mereb_bt.py), config L | th 0% | 14:00, ported line for line:
  S = SPY MTD - TLT MTD (daily closes, adjustment=all, prior month's last close -> the PRIOR session's close).
  On the last trading session of the month, if S < 0: long SPY at the open of the 14:00 bar, stop = entry -
  0.25 x ATR14 (RTH true range of the prior 14 sessions, from 1-minute bars), no target, flat at the open of the
  15:55 bar (half day: exchange close - 5 min; if that is not after 14:00 there is no trade).
Every month-end gets a row: signal yes (S < 0) or no; the no-signal rows carry the same trade as a control
(ctrl_* columns, never scored as the rule). Fetches GET-only market data (Alpaca /v2/stocks/bars; no trading endpoint),
applies LIVE-L costs (main), LR8 (alongside) and the S12 stress (+1 minute entry, stop level kept, +2 bp a side), and
upserts one row per date into forward.csv (idempotent). Research only - no orders, no config.
Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from mcf.data.bars import cap_at_close, close_min  # noqa: E402  calendar only (no order / trading code)
from mcf.execution.market_calendar import HOLIDAYS, next_trading_day  # noqa: E402  offline calendar

OUT = HERE / "forward.csv"
TZ = "America/New_York"
FROZEN = "2026-11-27"
FIRST_DAY = "2026-11-30"            # first month-end after the scout's data (ended 2026-11-04); earlier rows = seed
LOCK = ("2024-11-01", "2025-02-28")  # locked holdout: never read
SIG, BOND = "SPY", "TLT"
ENTRY_MIN, EXIT_MIN, HALF_BUF = 840, 955, 5     # 14:00 bar open; flat at the 15:55 bar open; half day close - 5
ATR_N, STOP_ATR, TH = 14, 0.25, 0.0
COLS = ["date", "S_pct", "spy_mtd_pct", "tlt_mtd_pct", "base_date", "prev_date", "signal", "atr14", "entry_time",
        "entry", "stop", "risk_pct", "exit_time", "exit", "kind", "R_gross", "R_livel", "R_lr8", "R_s12",
        "ctrl_R_livel", "ctrl_R_lr8", "status", "frozen"]
KIND = {0: "market", 1: "stop"}
PB = [0, 5, 10, 20, 50, 100, 1e9]
PBL = ["<5", "5-10", "10-20", "20-50", "50-100", "100+"]
TOD_COST = ((935, 3.8), (950, 2.1), (1030, 1.4))  # = mcf.research.gates.TOD_COST (LR8 entry multiplier)
CAL_END = max(HOLIDAYS)


def _nolock(day: str) -> None:
    assert not (LOCK[0] <= str(day) <= LOCK[1]), "locked block day"


def is_month_end(day: str) -> bool:
    """True if `day` is a trading session and the next trading session is in a later month (offline NYSE list)."""
    d = date.fromisoformat(day)
    if d.weekday() >= 5 or day in HOLIDAYS:
        return False
    if day[:4] > CAL_END[:4]:
        raise RuntimeError(f"market_calendar.HOLIDAYS ends {CAL_END}: extend it before running {day}")
    return next_trading_day(day).month != d.month


def signal(daily: pd.DataFrame, day: str) -> dict:
    """daily: index YYYY-MM-DD, columns SPY, TLT (adjusted closes, sessions before `day`). As mereb_bt.main."""
    dl = daily[[SIG, BOND]].dropna().sort_index()
    dl = dl[dl.index < day]
    for x in dl.index:
        _nolock(x)
    m = day[:7]
    pm = str(pd.Period(m, "M") - 1)
    prevm = dl[dl.index.str[:7] == pm]
    if prevm.empty:
        return dict(status="skipped: no prior-month close")
    base = prevm.index.max()
    prev = dl.index.max()
    if prev <= base:
        return dict(status="skipped: no session this month before the event day")
    sm = dl[SIG][prev] / dl[SIG][base] - 1
    tm = dl[BOND][prev] / dl[BOND][base] - 1
    return dict(S=sm - tm, spy=sm, tlt=tm, base=base, prev=prev)


def _rth(df: pd.DataFrame | None) -> pd.DataFrame | None:
    if df is None or df.empty:
        return None
    df = df[["open", "high", "low", "close"]].copy()
    df.index = pd.DatetimeIndex(df.index).tz_convert(TZ)
    df = df[~df.index.duplicated(keep="last")].sort_index().between_time("09:30", "15:59")
    df = cap_at_close(df)            # half days: drop the 13:00-16:00 after-hours prints
    return df if len(df) else None


def atr14(minute: pd.DataFrame, day: str) -> float:
    """Mean RTH true range of the 14 sessions before `day` (prior close = prior session's last RTH close)."""
    m = _rth(minute)
    if m is None:
        return float("nan")
    g = m.groupby(m.index.date.astype(str))
    H, L, C = g.high.max(), g.low.min(), g.close.last()
    H, L, C = H[H.index < day], L[L.index < day], C[C.index < day]
    pc = C.shift(1)
    tr = pd.concat([H - L, (H - pc).abs(), (L - pc).abs()], axis=1).max(axis=1).iloc[1:]
    return float(tr.iloc[-ATR_N:].mean()) if len(tr) >= ATR_N else float("nan")


def _cells():
    return json.load(open(ROOT / "research/primshorts_1126/cells_live.json"))


def costs(entry, exit_px, risk, kind, tod, cells=None):
    """Long-side costs in R as mereb_bt.costs: LIVE-L, LR8; plus 2 bp a side for the S12 stress."""
    cells = cells or _cells()
    pb = PBL[int(np.searchsorted(PB, entry, side="right")) - 1]
    a, b = cells.get(f"{pb}|{KIND[kind]}", cells[f"*|{KIND[kind]}"])[:2]
    c_livel = a / (risk / entry * 1e4) + b
    mult = 1.0
    for edge, mm in reversed(TOD_COST):
        if tod < edge:
            mult = mm
    ec = (0.01 + entry * 1e-4) * mult
    xc = 0.01 + exit_px * 1e-4 + (0.02 if kind == 1 else 0.0)
    return c_livel, (ec + xc) / risk, 2e-4 * (entry + exit_px) / risk


def trade(day_bars: pd.DataFrame | None, atr: float, close_m: int, start: int = ENTRY_MIN, stop=None):
    """mereb_bt.trade (side +1): entry at the open of the `start` bar, stop-first, flat at the open of the first bar
    >= exit_min. Returns (gross R, kind, entry, exit, stop, risk, entry_min, exit_min) or a status string."""
    x = _rth(day_bars)
    if x is None:
        return "no bars (holiday or not yet open)"
    if not np.isfinite(atr) or atr <= 0:
        return "skipped: ATR14 unavailable"
    exit_min = min(EXIT_MIN, close_m - HALF_BUF)
    if exit_min <= ENTRY_MIN:
        return "no trade: half day (exit before the 14:00 entry)"
    mn = np.array([t.hour * 60 + t.minute for t in x.index])
    j = int(np.searchsorted(mn, start))
    if j >= len(mn) or mn[j] != start:
        return f"skipped: no {start // 60:02d}:{start % 60:02d} bar"
    O, H, L, C = (x[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    fill = O[j]
    stop = fill - STOP_ATR * atr if stop is None else stop
    risk = fill - stop
    if risk <= 0:                    # S12 only: the delayed fill is already through the kept stop
        return (-1.0, 1, fill, fill, stop, None, mn[j], mn[j])
    for k in range(j, len(O)):
        if mn[k] >= exit_min:
            return ((O[k] - fill) / risk, 0, fill, O[k], stop, risk, mn[j], mn[k])
        if L[k] <= stop:
            px = O[k] if (k > j and O[k] < stop) else stop
            return ((px - fill) / risk, 1, fill, px, stop, risk, mn[j], mn[k])
    if mn[-1] + 1 < exit_min:
        return "pending: session not finished"
    return ((C[-1] - fill) / risk, 0, fill, C[-1], stop, risk, mn[j], mn[-1])


def evaluate(day: str, daily: pd.DataFrame, minute: pd.DataFrame, cells=None, close_m: int | None = None) -> dict:
    """The frozen rule on one month-end. daily: SPY/TLT adjusted closes; minute: SPY 1-minute bars (>= 15 sessions
    before `day` plus `day`)."""
    _nolock(day)
    row = {k: "" for k in COLS}
    row.update(date=day, frozen=FROZEN)
    close_m = close_min(day) if close_m is None else close_m
    s = signal(daily, day)
    if "status" in s:
        row.update(status=s["status"])
        return row
    row.update(S_pct=round(s["S"] * 100, 3), spy_mtd_pct=round(s["spy"] * 100, 3),
               tlt_mtd_pct=round(s["tlt"] * 100, 3), base_date=s["base"], prev_date=s["prev"],
               signal="yes" if s["S"] < -TH else "no")
    m = pd.DatetimeIndex(minute.index).tz_convert(TZ) if minute is not None and len(minute) else None
    a = atr14(minute, day) if m is not None else float("nan")
    today = minute[np.asarray(m.date.astype(str)) == day] if m is not None else None
    row["atr14"] = round(a, 4) if np.isfinite(a) else ""
    r = trade(today, a, close_m)
    if isinstance(r, str):
        row.update(status=r)
        return row
    cells = cells or _cells()
    g, kind, fill, xp, stop, risk, em, xm = r
    c_l, c_8, _ = costs(fill, xp, risk, kind, em // 60 * 100 + em % 60, cells)
    pre = "" if row["signal"] == "yes" else "ctrl_"
    if pre:
        row.update(ctrl_R_livel=round(g - c_l, 4), ctrl_R_lr8=round(g - c_8, 4),
                   status=f"no signal (S >= 0): control trade logged, not the rule")
        return row
    s1 = trade(today, a, close_m, start=ENTRY_MIN + 1, stop=stop)
    s12 = ""
    if not isinstance(s1, str):
        g1, k1, f1, x1, _, r1, e1, _ = s1
        if r1 is None:
            s12 = -1.0
        else:
            cl1, _, c2 = costs(f1, x1, r1, k1, e1 // 60 * 100 + e1 % 60, cells)
            s12 = round(g1 - cl1 - c2, 4)
    row.update(entry_time=f"{em // 60:02d}:{em % 60:02d}", entry=round(fill, 4), stop=round(stop, 4),
               risk_pct=round(risk / fill * 100, 3), exit_time=f"{xm // 60:02d}:{xm % 60:02d}", exit=round(xp, 4),
               kind=KIND[kind], R_gross=round(g, 4), R_livel=round(g - c_l, 4), R_lr8=round(g - c_8, 4), R_s12=s12,
               status="done" if day >= FIRST_DAY else "done (seed, in-sample: not scored)")
    return row


def _get_bars(syms, start, end, timeframe, adjustment):
    """Read-only Alpaca market data GET (no trading endpoint); same session / retry helpers as mcf.replay.store."""
    from mcf.replay.store import _get, _session
    url = "https://data.alpaca.markets/v2/stocks/bars"
    sess = _session()
    params = {"symbols": ",".join(syms), "timeframe": timeframe, "start": start, "end": end, "feed": "sip",
              "adjustment": adjustment, "limit": 10000}
    rows = []
    while True:
        j = _get(sess, url, params)
        for sym, bars in (j.get("bars") or {}).items():
            rows += [(sym, b["t"], b["o"], b["h"], b["l"], b["c"]) for b in bars]
        tok = j.get("next_page_token")
        if not tok:
            break
        params["page_token"] = tok
    df = pd.DataFrame(rows, columns=["symbol", "ts", "open", "high", "low", "close"])
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    return df


def fetch(day: str):
    d0 = str(date.fromisoformat(day) - timedelta(days=50))
    assert not (d0 <= LOCK[1] and day >= LOCK[0]), "fetch window touches the locked block"
    dd = _get_bars([SIG, BOND], f"{d0}T00:00:00Z", f"{day}T00:00:00Z", "1Day", "all")
    dd["date"] = dd.ts.dt.tz_convert(TZ).dt.date.astype(str)
    daily = dd.pivot(index="date", columns="symbol", values="close")
    m0 = str(date.fromisoformat(day) - timedelta(days=30))
    mm = _get_bars([SIG], f"{m0}T13:00:00Z", f"{day}T21:30:00Z", "1Min", "split").set_index("ts")
    return daily, mm[["open", "high", "low", "close"]]


def upsert(rows: list[dict], path: Path = OUT) -> None:
    days = {r["date"] for r in rows}
    old = []
    if path.exists():
        with open(path, newline="") as f:
            old = [r for r in csv.DictReader(f) if r["date"] not in days]
    allr = sorted(old + [{k: r.get(k, "") for k in COLS} for r in rows], key=lambda r: r["date"])
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(allr)


def run(day: str, path: Path = OUT, data=None) -> dict | None:
    """Acts only on the last trading session of a month; any other date is a no-op (returns None, writes nothing)."""
    _nolock(day)
    if not is_month_end(day):
        return None
    daily, minute = fetch(day) if data is None else data
    row = evaluate(day, daily, minute)
    upsert([row], path)
    return row


def _st(x):
    x = np.asarray(x, float)
    n = len(x)
    if n == 0:
        return dict(n=0)
    tot = float(x.sum())
    sd = x.std(ddof=1) if n > 1 else np.nan
    return dict(n=n, mean=round(float(x.mean()), 3), tot=round(tot, 2),
                t=round(float(x.mean() / (sd / np.sqrt(n))), 2) if n > 1 and sd > 0 else None,
                best_share=round(float(x.max()) / tot, 3) if tot > 0 else None,
                wo_best=round((tot - float(x.max())) / (n - 1), 3) if n > 1 else None)


def score(path: Path = OUT) -> dict:
    """Frozen pass bar (RULE.md): one trade per signal month-end (so per-trade t = per-day t)."""
    d = pd.read_csv(path, dtype=str).fillna("")
    d = d[d.date >= FIRST_DAY]
    tr = d[d.status == "done"].copy()
    num = lambda c, x: pd.to_numeric(x[c], errors="coerce").dropna()
    ctrl = d[d.ctrl_R_livel != ""]
    out = {"month_ends_logged": int(len(d)), "signal_trades": int(len(tr)),
           "livel": _st(num("R_livel", tr)), "lr8": _st(num("R_lr8", tr)), "s12": _st(num("R_s12", tr)),
           "control_no_signal_livel": _st(num("ctrl_R_livel", ctrl))}
    b, s = out["livel"], out["s12"]
    n = b.get("n", 0)
    if n >= 6 and (b["tot"] <= -4.0 or b["mean"] <= -0.40):
        v = "HARM STOP: close the question (logged; no re-tune on the same forward data)"
    elif n < 12:
        last = d.date.max() if len(d) else ""
        v = (f"INCONCLUSIVE (time cap): {n} of 12 signal trades" if last and last > "2030-12-31"
             else f"WAITING: {n} of 12 signal trades")
    else:
        ok = (b["mean"] > 0 and (b["t"] or 0) >= 2.0 and b["best_share"] is not None and b["best_share"] < 0.5
              and (b["wo_best"] or 0) > 0 and s.get("n", 0) and s["mean"] > 0)
        v = "PASS: write it up for the owner (decision)" if ok else "FAIL: close the question"
    out["verdict"] = v
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", action="append", default=[])
    ap.add_argument("--score", action="store_true")
    a = ap.parse_args()
    for d in a.date:
        r = run(d)
        print(d, "not a month-end session: nothing to do" if r is None else
              f"S {r['S_pct']}% signal {r['signal']} R_livel {r['R_livel'] or r['ctrl_R_livel']} | {r['status']}")
    if a.score:
        print(json.dumps(score(), indent=1))
