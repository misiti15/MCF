"""AV50 burst tight stop (owner ETF-STOP50 yes 2026-11-24, variant AV50; research/etfstop_1123/REPORT.md, skeptic
research/etfstop_1123/SKEPTIC_1127.md). Opt-in per setup, default off:

    burst_tight_stop:
      enabled: true
      stop_frac: 0.5               # research cfg 'tight'
      burst_k: 4                   # research cfg 'k'
      burst_window_min: 10         # research cfg 'win'
      index_gate: spy_below_vwap   # research cfg against='vwap'
      spy_max_stale_min: 3         # = PaperRunner.SPY_STALE_MIN

For each signal of the setup at 5-minute decision time m (the entry is the close of minute m-1, decided at m):
  1. burst: A + B >= burst_k, where A = lots of this setup booked in this account (book) whose decision time is later
     than m - burst_window_min and earlier than m (by decision-bar time, never wall clock), and B = every signal of the
     setup at decision time m in this poll (this one and any later skipped by caps / the latch included);
  2. gate: SPY's last completed regular-hours 1-minute bar before m (the m-1 bar), close c, below SPY's session VWAP
     (mcf.features.vwap over 09:30 .. that bar). SPY missing or its last bar more than spy_max_stale_min minutes older
     than the m-1 bar: the gate is false (the lot keeps its normal stop);
  3. burst AND gate: shares are sized from the ORIGINAL stop (unchanged), the bracket stop is
     px - stop_frac x (px - stop). Target and every other exit unchanged.
  4. R stays in ORIGINAL risk units: the journal's stop (the R basis cost_r reads) is the original stop; the tight stop
     is only a tag (burst_tight, stop_tight, burst_count, spy_vs_vwap).
The runner (mcf/execution/runner.py) and the shadow book (mcf/execution/shadow.py, of_live lots) both decide through
this module. Educational only - not financial advice."""
from __future__ import annotations

import pandas as pd

from .features import vwap

KEY = "burst_tight_stop"
SPY = "SPY"
GATES = ("spy_below_vwap",)
DEFAULTS = {"stop_frac": 0.5, "burst_k": 4, "burst_window_min": 10, "index_gate": "spy_below_vwap",
            "spy_max_stale_min": 3}


def settings(params) -> dict | None:
    """The setup's burst_tight_stop settings (defaults filled in), or None when it is off / absent."""
    raw = (params or {}).get(KEY)
    if not isinstance(raw, dict) or not raw.get("enabled", False):
        return None
    s = {**DEFAULTS, **{k: v for k, v in raw.items() if k != "enabled"}}
    s["stop_frac"] = float(s["stop_frac"])
    s["burst_k"] = int(s["burst_k"])
    s["burst_window_min"] = float(s["burst_window_min"])
    s["spy_max_stale_min"] = float(s["spy_max_stale_min"])
    if s["index_gate"] not in GATES:
        raise ValueError(f"{KEY}.index_gate must be one of {GATES}, got {s['index_gate']!r}")
    if not 0.0 < s["stop_frac"] < 1.0:
        raise ValueError(f"{KEY}.stop_frac must be in (0, 1), got {s['stop_frac']}")
    return s


def of(strategy) -> dict | None:
    return settings(getattr(strategy, "params", None))


def enabled(strategies) -> bool:
    """Any setup with burst_tight_stop on (the runner then polls SPY every minute from 09:30)."""
    return any(of(s) is not None for s in strategies)


def decision_time(bar_ts) -> pd.Timestamp:
    """Decision time m of a 5-minute decision bar from its 1-minute decision bar's timestamp: the end of the bucket it
    decides (bar 14:04 -> 14:05; a bucket that missed its 4th minute is decided by a later bar of the same bucket or
    the first bar of the next: 14:06 -> 14:05)."""
    ts = pd.Timestamp(bar_ts)
    return (ts - pd.Timedelta(minutes=4)).floor("5min") + pd.Timedelta(minutes=5)


def hhmm_time(day, hhmm: str, tz) -> pd.Timestamp:
    """Timestamp of HHMM (the runner's 'moment' / client-id suffix) on `day` in `tz`."""
    return pd.Timestamp(f"{day} {hhmm[:2]}:{hhmm[2:4]}", tz=tz)


def booked_before(times, m: pd.Timestamp, window_min: float) -> int:
    """A: booked lots whose decision time t satisfies m - window < t < m."""
    lo = m - pd.Timedelta(minutes=window_min)
    return sum(1 for t in times if lo < t < m)


def spy_vs_vwap(spy: pd.DataFrame | None, m: pd.Timestamp, max_stale_min: float) -> tuple[float, float] | None:
    """(close, session VWAP) of SPY's last completed regular-hours 1-minute bar before m, or None when SPY is missing,
    has no bar since 09:30, or its last bar is more than max_stale_min minutes older than the m-1 bar."""
    if spy is None or len(spy) == 0:
        return None
    open_ = pd.Timestamp(f"{m.date()} 09:30", tz=m.tz)
    b = spy[(spy.index >= open_) & (spy.index < m)]
    if b.empty or b.index[-1] < m - pd.Timedelta(minutes=1) - pd.Timedelta(minutes=max_stale_min):
        return None
    vw = float(vwap(b).iloc[-1])
    c = float(b["close"].iloc[-1])
    if vw != vw or c != c:
        return None
    return c, vw


def gate_ok(s: dict, spy_state: tuple[float, float] | None) -> bool:
    """The index gate (only spy_below_vwap exists): SPY's m-1 close below its session VWAP; unknown -> False."""
    if spy_state is None:
        return False
    c, vw = spy_state
    return c < vw


def tight_stop(px: float, stop: float, frac: float) -> float:
    """px - frac x (px - stop): the stop at frac of the original distance (either side)."""
    return float(px) - float(frac) * (float(px) - float(stop))


def decide(s: dict, px: float, stop: float, m: pd.Timestamp, prior: int, n_now: int, spy) -> tuple[float | None, dict]:
    """(tight stop or None, journal tag). prior = A, n_now = B (>= 1: the lot itself)."""
    n = int(prior) + max(int(n_now), 1)
    burst = n >= s["burst_k"]
    st = spy_vs_vwap(spy, m, s["spy_max_stale_min"]) if burst else None
    tight = burst and gate_ok(s, st)
    tag = {"burst_tight": bool(tight), "burst_count": n, "burst_decision": f"{m:%H:%M}",
           "spy_vs_vwap": None if st is None else round(st[0] - st[1], 4)}
    if not tight:
        return None, tag
    ts = tight_stop(px, stop, s["stop_frac"])
    tag["stop_tight"] = round(ts, 4)
    return ts, tag
