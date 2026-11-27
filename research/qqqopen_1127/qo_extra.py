"""QQQOPEN-1127 post-hoc additions (NOT in PREREG; counted, exploratory -> LEAD at best):
  (a) IDX2 / IDX5 replicas (SPY dip by 09:45: 0.75 / 0.5, FADE-LONG TRAIL on SPXL) so all 5 live IDX setups are covered;
  (b) UP-PULLBACK-LONG: the mirror of the FADE-SHORT rows, which lost strongly (QQQ 0.5 TRAIL t -4.9): index running
      high >= X% above the open by 09:55, first bar closing in [09:50, 10:05] with close <= run_high - 0.20 x
      (run_high - open) -> LONG the 3x ETF at the next bar open; stop = min(ETF session low, ETF open) - 0.10 x
      (ETF high - ETF open). 2 signals x 4 X x 2 exits = 16.
Total 18 extra configs (study total 67 + 18 = 85). Same costs / stats as qo_score.py. Locked block never read.
    python research/qqqopen_1127/qo_extra.py <scratch_out_dir> <raw_2016_2022_dir>
Educational only - not financial advice.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import qo_score as S  # noqa: E402
import qo_sim as Q  # noqa: E402


def extra_day(ix, tx, sig, trd):
    rows = []
    if len(ix) < 40 or len(tx) < 40:
        return rows
    imin = Q.tmin(ix.index); tmn = Q.tmin(tx.index)
    if imin[0] != 570 or tmn[0] != 570:
        return rows
    exit_min = min(955, max(imin[-1], tmn[-1]) + 1 - 5)
    io, ih, il, ic = (ix[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    to_, th, tl, tc = (tx[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    O = io[0]; tO = to_[0]; ends = imin + 1
    run_lo = np.minimum.accumulate(il); run_hi = np.maximum.accumulate(ih)
    day = ix.index[0].date()
    specs = []
    if sig == "SPY":
        specs += [("IDX2rep", 0.75, 585, "FADE-LONG"), ("IDX5rep", 0.5, 585, "FADE-LONG")]
    specs += [("UPPB", X, 595, "UP-PULLBACK-LONG") for X in (0.5, 0.75, 1.0, 1.5)]
    for tag, X, dip_by, rule in specs:
        if rule == "FADE-LONG":
            cond = (run_lo <= O * (1 - X / 100)) & (ends <= dip_by)
        else:
            cond = (run_hi >= O * (1 + X / 100)) & (ends <= dip_by)
        if not cond.any():
            continue
        i0 = int(np.argmax(cond)); trig = None
        for i in range(i0, len(ix)):
            if ends[i] > 605:
                break
            if ends[i] < 590:
                continue
            ok = (ic[i] >= run_lo[i] + 0.20 * (O - run_lo[i])) if rule == "FADE-LONG" else \
                 (ic[i] <= run_hi[i] - 0.20 * (run_hi[i] - O))
            if ok:
                trig = i; break
        if trig is None:
            continue
        k = int(np.searchsorted(tmn, imin[trig], side="right")) - 1
        if k < 0 or k + 1 >= len(tx):
            continue
        lo = tl[: k + 1].min(); hi = th[: k + 1].max(); px = tc[k]
        if rule == "FADE-LONG":
            drop = tO - lo
            if not (drop > 0 and px > lo):
                continue
            stop = lo - 0.10 * drop
        else:
            stop = min(lo, tO) - 0.10 * max(hi - tO, 1e-9)
            if px <= stop:
                continue
        j = k + 1
        if tmn[j] >= exit_min:
            continue
        for ex in ("TRAIL",) if tag != "UPPB" else ("HOLD", "TRAIL"):
            r = Q.simulate(to_, th, tl, tc, tmn, j, to_[j], stop, 1, exit_min, ex == "TRAIL")
            if r is None:
                continue
            g, kind, kx, xp, risk = r
            rows.append(dict(date=str(day), split=Q.split_of(day), sig=sig, trd=trd, X=X, rule=f"{tag}:{rule}", exit=ex,
                             side=1, entry=to_[j], exit_px=xp, risk=risk, kind=kind, gross=g,
                             tod=int(tx.index[j].hour * 100 + tx.index[j].minute), emin=int(tmn[j]), xmin=int(tmn[kx]),
                             stop_pct=risk / to_[j] * 100))
    return rows


def main(out_dir, raw_dir):
    raw = Path(raw_dir)
    data = {s: Q.load(s, raw) for s in ("QQQ", "SPY", "TQQQ", "SPXL")}
    rows = []
    for sig, trd in Q.PAIRS.items():
        gT = {d: g for d, g in data[trd].groupby(data[trd].index.date)}
        for d, gi in data[sig].groupby(data[sig].index.date):
            if d in gT:
                rows += extra_day(gi, gT[d], sig, trd)
    t = pd.DataFrame(rows)
    dd = pd.to_datetime(t.date).dt.date
    assert not ((dd >= Q.LOCK[0]) & (dd <= Q.LOCK[1])).any()
    t = S.costs(t)
    t["year"] = t.date.str[:4]
    traded = {}
    for s in ("TQQQ", "SPXL"):
        df = data[s]
        traded[s] = {str(d): (g.open.to_numpy(float), g.high.to_numpy(float), g.low.to_numpy(float),
                              g.close.to_numpy(float), Q.tmin(g.index).astype(np.int64))
                     for d, g in df.groupby(df.index.date) if len(g) >= 40}
    rng = np.random.default_rng(1127)
    res = {}
    for k, g in t.groupby(S.KEY):
        name = "|".join(map(str, k))
        r = {s: S.st(g[g.split == s].r_livel, g[g.split == s].date) for s in S.SPLITS}
        r["ALL"] = S.st(g.r_livel, g.date); r["ALL_lr8"] = S.st(g.r_lr8, g.date); r["ALL_tight"] = S.st(g.r_tight, g.date)
        r["ALL_gross"] = S.st(g.gross, g.date)
        r["years"] = g.groupby("year").r_livel.agg(["size", "mean"]).round(3).reset_index().to_dict("records")
        if r["ALL"].get("mean", -1) > 0 and len(g) >= 20:
            r["control"] = S.control(g.copy(), traded[k[1]], 300, rng)
        res[name] = r
    json.dump(res, open(HERE / "extra.json", "w"), indent=1, default=str)
    for n, r in res.items():
        print(n, {s: (r[s].get("n"), r[s].get("mean")) for s in S.SPLITS}, "ALL", {x: r["ALL"].get(x) for x in ("n", "mean", "t", "best_share", "wo_best")},
              "lr8", r["ALL_lr8"].get("mean"), r.get("control"))
    print("extra configs", len(res))


if __name__ == "__main__":
    main(*sys.argv[1:3])
