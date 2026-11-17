"""Dip-day forward log (rule frozen 2026-11-16 - see RULE.md).

    python research/forward/dip_day/dipday.py --date YYYY-MM-DD [--score]

Marks the session's day type from SPY 1-minute bars (read-only market data via mcf.replay.store._fetch_bars; the
drop / rebound test is a port of research/drop_rebound_1116/study.py find_signal, from_runhigh) and pulls that day's
live trades (run_id = 1) of the IDX* / LD* / NM-ETF-late-dip* setups from all ten intraday journals (git show
origin/<state branch>:journal.db, read-only, temp copy removed). Upserts days.csv (one row per date) and forward.csv
(that date's trades), so re-running a date is idempotent. --score prints the pass-bar status.
Research only - nothing here places orders or changes any config. Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAYS, TRADES = HERE / "days.csv", HERE / "forward.csv"
TZ = "America/New_York"
FROZEN = "2026-11-16"
DROP, REB = 0.0065, 0.005
FIRST_HOUR_END = 59          # drop reached on a bar starting by 10:29
DEC_FROM, DEC_TO = 19, 149   # rebound judged on bar closes 09:50 .. 12:00
FAMILY = re.compile(r"^(IDX\d|LD\d|NM-ETF-late-dip)")
BRANCHES = {"primary": "mcf-data", "ondeck": "mcf-data-testing", "testing_a": "mcf-data-testing2",
            "graveyard": "mcf-data-graveyard", "gen": "mcf-data-gen", "testing_b": "mcf-data-explore1",
            "testing_c": "mcf-data-livelab", "testing_d": "mcf-data-testingd", "testing_e": "mcf-data-testinge",
            "testing_f": "mcf-data-testingf"}
DCOLS = ["date", "day_type", "drop", "max_drop_pct", "drop_time", "low", "low_time", "rebound_time", "status", "frozen"]
TCOLS = ["date", "day_type", "account", "strategy", "symbol", "side", "entry_time", "entry", "stop", "exit", "shares",
         "pnl_adj", "R", "exit_reason"]


def hm(i: int) -> str:
    m = 570 + i + 1
    return f"{m // 60:02d}:{m % 60:02d}"


def spy_grid(day: str) -> np.ndarray | None:
    sys.path.insert(0, str(ROOT))
    from mcf.replay.store import _fetch_bars       # read-only market data
    df = _fetch_bars(["SPY"], f"{day}T13:00:00Z", f"{day}T21:00:00Z", "1Min")
    if df is None or df.empty:
        return None
    df = df.set_index("ts")
    idx = df.index.tz_convert(TZ) if df.index.tz is not None else df.index
    m = (idx.hour * 60 + idx.minute - 570).to_numpy()
    keep = (m >= 0) & (m < 390)
    a = np.full((390, 4), np.nan)
    a[m[keep]] = df[["open", "high", "low", "close"]].to_numpy(dtype=float)[keep]
    last = int(m[keep].max()) if keep.any() else -1
    a = pd.DataFrame(a).ffill().bfill().to_numpy(copy=True)
    a[last + 1:] = np.nan
    return a if last >= 0 else None


def day_type(a: np.ndarray | None) -> dict:
    if a is None:
        return dict(day_type="", status="no bars (holiday or not yet open)")
    if np.isnan(a[DEC_TO, 3]):
        return dict(day_type="", status="pending: SPY bars to 12:00 not yet available")
    h, l, c = a[:, 1], a[:, 2], a[:, 3]
    dd = 1 - l / np.maximum.accumulate(h)
    hit = np.nonzero(dd[:FIRST_HOUR_END + 1] >= DROP)[0]
    out = dict(max_drop_pct=round(100 * float(dd[:FIRST_HOUR_END + 1].max()), 3), status="ok")
    if not len(hit):
        return dict(out, day_type="OTHER", drop=False)
    di = int(hit[0])
    peak = int(np.argmax(h[:di + 1]))
    out.update(drop=True, drop_time=hm(di))
    for i in range(di, DEC_TO + 1):
        L = l[peak:i + 1].min()
        if c[i] >= L * (1 + REB) and i >= DEC_FROM:
            j = peak + int(np.argmin(l[peak:i + 1]))
            return dict(out, day_type="DIP", low=round(float(L), 2), low_time=hm(j), rebound_time=hm(i))
    return dict(out, day_type="OTHER", status="ok (drop_no_rebound)")


def trades(day: str, dtype: str) -> list[dict]:
    out = []
    for acct, br in BRANCHES.items():
        fd, p = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            blob = subprocess.run(["git", "-C", str(ROOT), "show", f"origin/{br}:journal.db"], capture_output=True)
            if blob.returncode or not blob.stdout:
                continue
            Path(p).write_bytes(blob.stdout)
            c = sqlite3.connect(p)
            df = pd.read_sql("select strategy, symbol, side, entry_time, entry, stop, exit, shares, pnl_adj, exit_reason "
                             "from trades where run_id = 1 and date = ?", c, params=[day])
            c.close()
        finally:
            os.unlink(p)
        df = df[df.strategy.str.match(FAMILY)]
        for r in df.itertuples():
            risk = abs(r.entry - r.stop) * r.shares if r.shares else 0
            out.append(dict(date=day, day_type=dtype, account=acct, strategy=r.strategy, symbol=r.symbol, side=r.side,
                            entry_time=r.entry_time, entry=r.entry, stop=r.stop, exit=r.exit, shares=r.shares,
                            pnl_adj=r.pnl_adj, R=round(r.pnl_adj / risk, 4) if risk else "", exit_reason=r.exit_reason))
    return out


def upsert(path: Path, cols: list[str], day: str, rows: list[dict]) -> None:
    old = []
    if path.exists():
        with open(path, newline="") as f:
            old = [r for r in csv.DictReader(f) if r["date"] != day]
    allr = old + [{k: r.get(k, "") for k in cols} for r in rows]
    allr.sort(key=lambda r: (r["date"], r.get("account", ""), r.get("entry_time", "")))
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(allr)


def score() -> str:
    if not (DAYS.exists() and TRADES.exists()):
        return "dip-day: no log yet"
    d = pd.read_csv(DAYS)
    t = pd.read_csv(TRADES)
    t = t[pd.to_numeric(t.R, errors="coerce").notna()].assign(R=lambda x: x.R.astype(float))
    nd = int((d.day_type == "DIP").sum())
    a, b = t[t.day_type == "DIP"].R, t[t.day_type == "OTHER"].R
    msg = f"dip-day log: {len(d)} sessions, {nd} DIP (pass bar needs 10); trades DIP {len(a)} / OTHER {len(b)}"
    if len(a) >= 2 and len(b) >= 2:
        diff = a.mean() - b.mean()
        tt = diff / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
        msg += f"; avg R DIP {a.mean():+.2f} vs OTHER {b.mean():+.2f} (diff {diff:+.2f}, t {tt:.2f}) - not scored before 10 DIP days"
    return msg


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--score", action="store_true")
    a = ap.parse_args()
    if a.date:
        info = day_type(spy_grid(a.date))
        upsert(DAYS, DCOLS, a.date, [dict(date=a.date, frozen=FROZEN, **info)])
        tr = trades(a.date, info.get("day_type", "")) if info.get("day_type") else []
        upsert(TRADES, TCOLS, a.date, tr)
        print(f"{a.date}: {info.get('day_type') or '-'} ({info.get('status')}; max drop {info.get('max_drop_pct')}%, "
              f"low {info.get('low', '-')} {info.get('low_time', '')}, rebound {info.get('rebound_time', '-')}); "
              f"{len(tr)} family trades, sum R {sum(r['R'] for r in tr if r['R'] != ''):+.2f}")
    print(score())
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    main()
