"""GEN exposure 2026-10-25: live breadth (over every polled symbol) vs the screen's breadth (over the lab universe).

    python research/ops/genexposure1025_breadth.py OUT.csv 2026-10-19 2026-10-20 ...

Per session: read-only SIP 1-minute bars (mcf.replay.store._fetch_bars) of every symbol in the Gen account's live
universe.csv of that day (origin/mcf-data-gen), then mcf.strategies.lab_context._breadth (the live code) over
(a) all of them = what the live runner computes from its poll, and (b) only the lab symbols (research/lab_symbols.txt)
= how the 2-year history / the screen defines breadth. One row per 5-minute bar: breadth / breadth_open both ways.
Also OUT_align.csv: per symbol-day, the 5-minute decision bars (bar closes 09:50..15:00) that have bars, and how many
of them the live gate can act on even with a poll every minute (LabStrategy.eligible needs the 1-minute bar count
% 5 == 0 and the runner acts only when the signal's bar - the first 1-minute bar at or after the bucket's 4th minute -
is the latest bar: so count(end) % 5 == 0). The screen's clock-based frames count every bucket.
Bars are not stored. Research only; nothing here trades. Educational only - not financial advice.
"""
from __future__ import annotations

import os
import sys

import pandas as pd

from mcf.replay import store
from mcf.strategies.lab_context import _breadth


def main(out: str, days: list[str]) -> None:
    lab = set(open(store.SYMBOLS_FILE).read().split())
    rows = []
    for d in days:
        u = (store.live_universe(pd.Timestamp(d).date(), "origin/mcf-data-gen")
             or store.live_universe(pd.Timestamp(d).date(), "origin/mcf-data"))   # 10-19: Gen's first day
        syms = sorted(u)
        df = store._fetch_bars(syms, f"{d}T13:30:00Z", f"{d}T20:00:00Z", "1Min")
        df = df.set_index("ts")
        df.index = df.index.tz_convert(store.TZ)
        df = df[(df.index.time >= pd.Timestamp("09:30").time()) & (df.index.time < pd.Timestamp("16:00").time())]
        peers = {s: g[["open", "high", "low", "close", "volume"]].astype(float) for s, g in df.groupby("symbol")}
        a = _breadth(peers)
        b = _breadth({s: v for s, v in peers.items() if s in lab})
        al = []
        for sym, g in peers.items():
            ts = g.index
            starts = pd.DatetimeIndex(ts.floor("5min").unique())
            close = starts + pd.Timedelta(minutes=5)
            hh = close.hour * 100 + close.minute
            starts = starts[(hh >= 950) & (hh <= 1500)]
            end = ts.searchsorted(starts + pd.Timedelta(minutes=4))
            ok = end < len(ts)
            al.append((sym, len(starts), int(((end[ok] + 1) % 5 == 0).sum()), len(ts)))
        A = pd.DataFrame(al, columns=["symbol", "buckets", "evaluable", "minutes"])
        A["date"] = d
        A["lab"] = A["symbol"].isin(lab)
        fa = out.replace(".csv", "_align.csv")
        A.to_csv(fa, mode="a", header=not os.path.exists(fa), index=False)
        t = a.join(b, rsuffix="_lab")
        t["date"] = d
        t["n_live"] = len(peers)
        t["n_lab"] = sum(1 for s in peers if s in lab)
        rows.append(t.reset_index())
        print(d, len(peers), "symbols with bars;", t["n_lab"].iloc[0], "lab", flush=True)
        del df, peers
    pd.concat(rows).to_csv(out, index=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
