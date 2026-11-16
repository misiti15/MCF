"""Late-turn forward shadow (owner 2026-11-16 "late turn forward yes"). Rule frozen 2026-11-16 - see RULE.md.

    python research/forward/late_turn/shadow.py --date YYYY-MM-DD

Fetches that session's SPY and SPXL 1-minute bars read-only (mcf.replay.store._fetch_bars: market data only, no
trading endpoint), applies the frozen rule and upserts one row per date into forward.csv (idempotent: re-running a date
replaces its row, e.g. a row written before 12:50 ET is 'pending' and is completed by a later run).
The rule is a byte-for-byte port of research/morning_low_1116/study.py (window 10:55-11:20, D1, X = 10 bps, SPY +90,
SPXL trade); `--verify` re-scores the study's 35 historical trades from the cache and must match them.
Research only - nothing here places orders or changes any config. Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "forward.csv"
TZ = "America/New_York"
FROZEN = "2026-11-16"

# frozen constants (minute index 0 = the 09:30 bar; a bar's close is the price at its start + 1 min)
I950 = 19            # close of the 09:49 bar = price at 09:50
WS, WE = 85, 110     # window bars 10:55 .. 11:19 -> decision at the 11:19 bar close = 11:20
HOLD = 90            # exit at the close of bar WE - 1 + 90 = 12:50
DIP_BPS = 10.0       # new low at least 10 bps under the 09:50 price
LEV = 3.0            # SPXL
STOP_FLOOR, STOP_BUF = 0.0015, 0.0005
COST_C, COST_BPS, STOP_SLIP = 0.01, 1e-4, 0.02
COLS = ["date", "setup", "signal_time", "spy_950", "spy_win_low", "dip_bps", "entry", "stop", "exit_time", "exit",
        "stopped", "R_after_costs", "status", "frozen"]


def grid(df: pd.DataFrame | None, min_bars: int = 1) -> np.ndarray | None:
    """One session of 1-minute bars (index = bar start, tz-aware or ET) -> 390 x 5 (o,h,l,c,v), forward-filled as in
    the study. Bars after the last real bar are NaN (so an unfinished session is detectable)."""
    if df is None or len(df) < min_bars:
        return None
    idx = df.index.tz_convert(TZ) if df.index.tz is not None else df.index
    m = (idx.hour * 60 + idx.minute - 570).to_numpy()
    keep = (m >= 0) & (m < 390)
    a = np.full((390, 5), np.nan)
    a[m[keep]] = df[["open", "high", "low", "close", "volume"]].to_numpy(dtype=float)[keep]
    last = int(m[keep].max())
    v = np.nan_to_num(a[:, 4])
    a = pd.DataFrame(a).ffill().bfill().to_numpy(copy=True)
    a[:, 4] = v
    a[last + 1:, :4] = np.nan
    return a


def evaluate(spy: np.ndarray, spxl: np.ndarray | None) -> dict:
    """The frozen rule on one session's grids. Returns the forward.csv fields (without date / frozen)."""
    row = {k: "" for k in COLS if k not in ("date", "frozen")}
    if spy is None or np.isnan(spy[WE - 1, 3]):
        row.update(setup="", status="pending: SPY bars to 11:20 not yet available")
        return row
    p950 = spy[I950, 3]
    prior_lo = spy[20:WS, 2].min()
    wlo = spy[WS:WE, 2].min()
    dip = (p950 - wlo) / p950 * 1e4
    newlow = wlo < prior_lo
    reclaim = spy[WE - 1, 3] > spy[WS - 1, 3]
    row.update(spy_950=round(float(p950), 4), spy_win_low=round(float(wlo), 4), dip_bps=round(float(dip), 2))
    if not (newlow and dip >= DIP_BPS and reclaim):
        why = "no new 09:50+ low in 10:55-11:20" if not newlow else (
            f"dip {dip:.1f} bps < {DIP_BPS:.0f}" if dip < DIP_BPS else "no reclaim of the 10:55 price by 11:20")
        row.update(setup="no", status=f"no setup: {why}")
        return row
    row.update(setup="yes", signal_time="11:20")
    if spxl is None or np.isnan(spxl[WE - 1, 3]):
        row.update(status="pending: SPXL bars missing")
        return row
    ent = spxl[WE - 1, 3]
    udist = max(spy[WE - 1, 3] / wlo - 1, STOP_FLOOR) + STOP_BUF
    stop = ent * (1 - LEV * udist)
    ex_i = WE - 1 + HOLD
    row.update(entry=round(float(ent), 4), stop=round(float(stop), 4))
    exit_px, stopped, ex_t = None, False, None
    for i in range(WE, ex_i + 1):
        if np.isnan(spxl[i, 2]):
            break
        if spxl[i, 2] <= stop:
            exit_px, stopped, ex_t = min(stop, spxl[i, 0]), True, i
            break
    if exit_px is None:
        if np.isnan(spxl[ex_i, 3]):
            row.update(status="pending: exit at 12:50 not reached")
            return row
        exit_px, ex_t = spxl[ex_i, 3], ex_i + 1
    cost = 2 * COST_C + COST_BPS * (ent + exit_px) + (STOP_SLIP if stopped else 0.0)
    R = (exit_px - ent - cost) / (ent - stop)
    mm = 570 + ex_t
    row.update(exit_time=f"{mm // 60:02d}:{mm % 60:02d}", exit=round(float(exit_px), 4), stopped=bool(stopped),
               R_after_costs=round(float(R), 4), status="done")
    return row


def fetch(day: str) -> tuple[np.ndarray | None, np.ndarray | None]:
    sys.path.insert(0, str(HERE.parents[2]))
    from mcf.replay.store import _fetch_bars       # read-only market data
    df = _fetch_bars(["SPY", "SPXL"], f"{day}T13:00:00Z", f"{day}T21:00:00Z", "1Min")
    if df.empty:
        return None, None
    df = df.set_index("ts")
    return (grid(df[df.symbol == "SPY"]), grid(df[df.symbol == "SPXL"]))


def upsert(row: dict, path: Path = OUT) -> None:
    rows = []
    if path.exists():
        with open(path, newline="") as f:
            rows = [r for r in csv.DictReader(f) if r["date"] != row["date"]]
    rows.append({k: row.get(k, "") for k in COLS})
    rows.sort(key=lambda r: r["date"])
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)


def run(day: str, path: Path = OUT) -> dict:
    spy, spxl = fetch(day)
    row = {"date": day, "frozen": FROZEN, **{k: v for k, v in evaluate(spy, spxl).items() if k not in ("date", "frozen")}}
    if spy is None:
        row["status"] = "no bars (holiday or not yet open)"
    upsert(row, path)
    return row


def verify() -> None:
    """Re-score every cached session (read-only, locked block skipped) and compare with the study's trade list
    (research/morning_low_1116/trade_posthoc_1120_X10.csv): same signal days, same R."""
    root = Path(os.environ.get("MCF_ROOT", HERE.parents[2]))
    ref = pd.read_csv(HERE.parents[1] / "morning_low_1116" / "trade_posthoc_1120_X10.csv").set_index("day").R
    bars = {}
    for s in ("SPY", "SPXL"):
        b = pd.read_parquet(root / "data/cache_hist/1Min" / f"{s}.parquet")
        b.index = b.index.tz_convert(TZ)
        bars[s] = {str(d): x for d, x in b.groupby(b.index.date)}
    got = {}
    for d, x in bars["SPY"].items():
        if "2024-11-01" <= d <= "2025-02-28" or len(x[(x.index.hour * 60 + x.index.minute).isin(range(570, 960))]) < 380:
            continue
        out = evaluate(grid(x), grid(bars["SPXL"].get(d), 150))
        if out["setup"] == "yes":
            got[d] = float(out["R_after_costs"])
    ref = ref[ref.index <= max(bars["SPY"])]
    same = set(got) == set(ref.index)
    diff = max(abs(got[d] - ref[d]) for d in ref.index if d in got)
    print(f"signal days: shadow {len(got)}, study {len(ref)}, same set {same}, max |R diff| {diff:.2e}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", action="append", default=[])
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if a.verify:
        verify()
    for d in a.date:
        print(run(d))
