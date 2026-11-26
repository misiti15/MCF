"""REGSTEER-1126: bench candidate lots with costs and point-in-time states, the Primary base book, and live trades with states.
  bench: rs_bench.py WORK (trades_t1/t2) -> bench10 add_r -> price >= $5, ETB shorts -> r = LIVE-L (shorts) / LR8 research
         (longs, primshorts convention) -> S1 gap tercile input, S2 W60 side at the latest mark <= entry minute - 1.
  base book (Primary 4): primshorts_1126 booksim.sim_day with Primary rules, LATCH-OPEN off; open marks not modelled (the
         -20R halt sees realised R only). Taken lots -> base.parquet.
  live: rs_live_load.py output + SPY gap (compass cond_obs, locked rows dropped at read) + live W60 (compute() on Alpaca bars,
        compass_rd_1126 backfill copy).
Usage: python rs_cand.py WORK STATES SCR. Locked block 2024-11-01..2025-02-28 never read (asserted). Educational only."""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

H = Path(__file__).resolve().parent
ROOT = H.parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/ultimate_1119/top10"))
sys.path.insert(0, str(ROOT / "research/primshorts_1126"))
import bench10 as B  # noqa: E402
import calib_live as CLV  # noqa: E402
from booksim import sim_day  # noqa: E402
sys.path.insert(0, str(H))

W, ST, SCR = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
LOCK = ("2024-11-01", "2025-02-28")
PRIMARY4 = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
            "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "NM-ETF-late-dip-di-long"]


def no_locked(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def period(d):
    if ("2024-10-01" <= d <= "2024-10-31") or ("2025-03-01" <= d <= "2025-09-30"):
        return "FIT"
    if "2025-10-01" <= d <= "2026-11-04":
        return "CHECK"
    if "2023-01-03" <= d <= "2024-09-13":
        return "T2"
    return "none"


def side_at(marks, dates, em):
    """W60 confirmed side (+1 / -1 / 0) at the latest mark T <= em - 1 of that date (marks: date, T(min), level)."""
    m = marks.sort_values(["date", "T"])
    out = np.zeros(len(dates), int)
    idx = {d: (g["T"].to_numpy(), g.level.to_numpy()) for d, g in m.groupby("date")}
    for i, (d, e) in enumerate(zip(dates, em)):
        if d not in idx:
            out[i] = -9; continue
        T, L = idx[d]
        k = np.searchsorted(T, e - 1, side="right") - 1
        out[i] = 0 if k < 0 else (1 if L[k] == 2 else (-1 if L[k] == -2 else 0))
    return out


if __name__ == "__main__":
    x = pd.concat([pd.read_parquet(W / f) for f in ("trades_t1.parquet", "trades_t2.parquet")], ignore_index=True)
    x["date"] = x.date.astype(str)
    x = B.add_r(x)
    x["per"] = x.date.map(period)
    x = x[x.per != "none"].copy()
    no_locked(x.date.unique())
    etb = pd.read_parquet(SCR / "etb_rate.parquet").rate
    x = x[x.entry >= 5.0]
    x = x[(x.side > 0) | x.symbol.map(etb).fillna(0).ge(0.9)].copy()
    cells = json.load(open(ROOT / "research/primshorts_1126/cells_live.json"))
    kd = np.where(x.kind == 2, "target", np.where(x.kind == 1, "stop", "market"))
    x["r_live"] = np.where(x.side < 0, x.r_gross - CLV.predict_R(cells, x.entry.to_numpy(), x.risk.to_numpy(), kd), x.r)
    gap = pd.read_parquet(ST / "gap.parquet").set_index("date").gap
    marks = pd.read_parquet(ST / "marks.parquet")
    no_locked(marks.date.unique()); no_locked(gap.index)
    x["gap"] = x.date.map(gap)
    x["w60"] = side_at(marks, x.date.to_numpy(), x.em.to_numpy())
    c = x[["setup", "symbol", "date", "per", "tod", "em", "xm", "side", "entry", "risk", "r_live", "gap", "w60"]]
    c = c.rename(columns={"r_live": "r"}).reset_index(drop=True)
    c.to_parquet(SCR / "cand.parquet")
    print(c.groupby(["setup", "per"]).size().unstack().fillna(0).astype(int).to_string())
    print("w60 missing", int((c.w60 == -9).sum()), "gap missing", int(c.gap.isna().sum()))

    # Primary base book (Primary rules, LATCH-OPEN off)
    p = c[c.setup.isin(PRIMARY4)].copy()
    p["si"] = p.setup.map({s: i for i, s in enumerate(PRIMARY4)})
    p = p.sort_values(["date", "em", "si", "symbol"], kind="mergesort").reset_index(drop=True)
    taken = np.zeros(len(p), bool)
    w = np.ones(4); lo = np.zeros(4, bool)
    for d, g in p.groupby("date"):
        ix = g.index.to_numpy()
        _, tk, _, _ = sim_day(g.si.to_numpy(), pd.factorize(g.symbol)[0], g.side.to_numpy(float), g.entry.to_numpy(float),
                              g.risk.to_numpy(float), np.zeros(len(g)), g.em.to_numpy(int), g.xm.to_numpy(int),
                              g.r.to_numpy(float), lambda o, m: np.full(len(o), np.nan), 4, w, lo)
        taken[ix] = tk
    base = p[taken].reset_index(drop=True)
    base.to_parquet(SCR / "base.parquet")
    days = pd.Series(sorted(p.date.unique()))
    print("base lots", len(base), "of", len(p), "| sessions with candidates", len(days))
    print(base.groupby("per").apply(lambda g: g.groupby("date").r.sum().mean()).round(3).to_dict())

    # live trades with states
    L = pd.read_parquet(SCR / "live.parquet")
    go = pd.read_parquet(SCR / "gap_obs.parquet").set_index("date").gap
    no_locked(go.index)
    L["gap"] = L.date.map(go)
    lm = pd.read_parquet(SCR / "live_compass_marks.parquet")
    lm = lm.assign(level=lm.w60.map({"UP-confirmed": 2, "leaning up": 1, "mixed": 0, "leaning down": -1,
                                      "DOWN-confirmed": -2}), T=lm["m"].astype(int))
    L["w60"] = side_at(lm[["date", "T", "level"]], L.date.to_numpy(), L.em.to_numpy())
    L.to_parquet(SCR / "live_states.parquet")
    print("live", len(L), "gap missing", int(L.gap.isna().sum()), "w60 missing", int((L.w60 == -9).sum()))
