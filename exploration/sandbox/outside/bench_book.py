"""Simplified P4 book on the 2-year minute bench candidates (cand.parquet from the regsteer_1126 bench build, LIVE-L R).
Rules: <= 30 lots per setup per day, <= 3 per symbol per setup per day, -2R closed latch per setup, -20R closed halt.
Optional: profit lock X (closed book R >= X -> no new entries). Locked block asserted absent.
Educational only - not financial advice."""
import numpy as np
import pandas as pd

LOCK = ("2024-11-01", "2025-02-28")
P4 = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
      "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "NM-ETF-late-dip-di-long"]


def load(path, setups=P4):
    c = pd.read_parquet(path)
    c["date"] = c.date.astype(str)
    assert not ((c.date >= LOCK[0]) & (c.date <= LOCK[1])).any(), "locked block row found"
    c = c[c.setup.isin(setups)].copy()
    c["si"] = c.setup.map({s: i for i, s in enumerate(setups)})
    return c.sort_values(["date", "em", "si", "symbol"], kind="mergesort").reset_index(drop=True)


def book_day(g, X=np.inf, latch=-2.0, halt=-20.0, cap=30, symcap=3):
    """g: one day's candidates sorted by em. Returns keep mask and lock flag."""
    em, xm, r, si, sym = g.em.to_numpy(), g.xm.to_numpy(), g.r.to_numpy(), g.si.to_numpy(), g.symbol.to_numpy()
    keep = np.zeros(len(g), bool); cnt = {}; scnt = {}
    locked = False
    for i in range(len(g)):
        prev = keep[:i] & (xm[:i] <= em[i])
        closed_s = {s: r[:i][prev & (si[:i] == s)].sum() for s in set(si[:i][prev])} if prev.any() else {}
        closed = sum(closed_s.values())
        if closed <= halt:
            break
        if closed >= X - 1e-12:
            locked = True
            break
        s = si[i]
        if closed_s.get(s, 0.0) <= latch + 1e-12 or cnt.get(s, 0) >= cap or scnt.get((s, sym[i]), 0) >= symcap:
            continue
        keep[i] = True; cnt[s] = cnt.get(s, 0) + 1; scnt[(s, sym[i])] = scnt.get((s, sym[i]), 0) + 1
    return keep, locked
