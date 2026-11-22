"""Part D: NM-ETF-late-dip-di-long protection study (pre-registered in D_PREREG.md; 19 configurations).
E4-normal-way: bench10 NM-ETF signals re-walked minute by minute by one per-day simulator that reproduces bench10
walk_trades + add_r (LR8 costs) + book (Primary: cap 30, <= 3 lots per symbol, -2R latch on realized cost-R), with the
protection rules layered on. FIT 2024-10 + 2025-03..09, T2 2023-01..2024-09, CHECK 2025-10-01..2026-11-04.
The locked block 2024-11-01..2025-02-28 is never read (pyarrow filter + assert).
Usage: python partD.py CHECKOUT TOP10W OUTDIR.  Educational only - not financial advice."""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

CK, T10, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
sys.path.insert(0, str(CK))
from mcf.research.gates import tod_cost_mult  # noqa: E402

SETUP = "NM-ETF-late-dip-di-long"
TZ = "America/New_York"
LOCK = ("2024-11-01", "2025-02-28")
HIST, FRESH = Path("/home/user/MCF/data/cache_hist/1Min"), Path("/home/user/MCF/data/cache_fresh/1Min")
BORROW = 1.2e-4


def period(d):
    if ("2024-10-01" <= d <= "2024-10-31") or ("2025-03-01" <= d <= "2025-09-30"):
        return "FIT"
    if d >= "2025-10-01":
        return "CHECK"
    if d <= "2024-09-13":
        return "T2"
    return "none"


def no_locked(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


# ------------------------------------------------------------------ signals and bars
s1 = pd.read_parquet(T10 / "trades_t1.parquet")
s2 = pd.read_parquet(T10 / "trades_t2.parquet")
S = pd.concat([s1[s1.setup == SETUP], s2[s2.setup == SETUP]], ignore_index=True)
S = S[S.kind.notna() & (S.kind >= 0)].copy()
S["date"] = S.date.astype(str)
S["per"] = S.date.map(period)
S = S[S.per != "none"].reset_index(drop=True)
no_locked(S.date.unique())
S = S[S.entry >= 5.0]          # book(): price >= $5 (long-only setup: no ETB filter)
S["em"] = (S.tod // 100) * 60 + S.tod % 100

BARS = {}   # (sym, date) -> (minute-of-day array, O, H, L, C)
for sym, g in S.groupby("symbol"):
    days = sorted(g.date.unique())
    t1d = [d for d in days if d >= "2024-09-16"]
    t2d = [d for d in days if d < "2024-09-16"]
    for src, dd in ((HIST, t1d), (FRESH, t2d)):
        if not dd or not (src / f"{sym}.parquet").exists():
            continue
        f = pads.field("__index_level_0__")
        lo, hi = pd.Timestamp(dd[0], tz=TZ), pd.Timestamp(dd[-1], tz=TZ) + pd.Timedelta(days=1)
        flt = (f >= lo) & (f < hi)
        if src is HIST:
            flt = flt & ((f < pd.Timestamp(LOCK[0], tz=TZ)) | (f >= pd.Timestamp("2025-03-01", tz=TZ)))
        b = pads.dataset(str(src / f"{sym}.parquet"), format="parquet").to_table(filter=flt).to_pandas()
        if "__index_level_0__" in b.columns:
            b = b.set_index("__index_level_0__")
        b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
        b = b.sort_index()
        day = b.index.date.astype(str)
        no_locked(np.unique(day))
        mins = (b.index.hour * 60 + b.index.minute).to_numpy()
        O, H, L, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
        for d in dd:
            ix = np.flatnonzero(day == d)
            if len(ix):
                BARS[(sym, d)] = (mins[ix], O[ix], H[ix], L[ix], C[ix])


# ------------------------------------------------------------------ simulator
class Lot:
    __slots__ = ("i", "sym", "entry", "stop", "tgt", "risk", "size", "em", "tier", "ecost", "bars", "k", "open",
                 "px", "kind", "xm", "r", "burst", "is_burst", "rank", "gap", "tod", "tstop")


def cost_r(lot):
    xcost = (0.0 if lot.kind == 2 else 0.01 + lot.px * 1e-4) + (0.02 if lot.kind == 1 else 0.0)
    gross = lot.px - lot.entry
    return (gross - lot.tier * (lot.ecost + xcost)) / lot.risk * lot.size


def mark(lot, c):
    return (c - lot.entry) / lot.risk * lot.size


def sim_day(sig, cfg):
    """sig: signals of one day (DataFrame). Returns list of closed lots (dict) and burst info."""
    cfg = cfg or {}
    sig = sig.sort_values(["em", "symbol"], kind="mergesort")
    # staggered schedule
    plan = []
    for em, g in sig.groupby("em", sort=True):
        for j, r in enumerate(g.itertuples()):
            plan.append((em + (j if cfg.get("stagger") else 0), j, r))
    plan.sort(key=lambda x: (x[0], x[1]))
    if not plan:
        return [], {}
    m0 = plan[0][0]
    lots, open_, realized = [], [], 0.0
    booked_times = []           # entry minutes of booked lots (for the burst definition)
    bursts = []                 # dicts: start, members(list of lots), flat(bool)
    pi = 0
    sentinel_hits = 0
    for m in range(m0, 15 * 60 + 56):
        # (a) existing open lots: bar m -> own stop / target / 15:55 flat
        def step(lot):
            mins, O, H, L, C = lot.bars
            while lot.k < len(mins) and mins[lot.k] < m:
                lot.k += 1
            if lot.k >= len(mins):                       # data ends: last close (bench: C[sel[-1]])
                lot.px, lot.kind, lot.xm, lot.open = C[-1], 0, m, False
                return
            k = lot.k
            if m >= 15 * 60 + 55:                        # bench: open of the first bar at/after 15:55
                lot.px, lot.kind, lot.xm, lot.open = O[k], 0, m, False
                return
            if mins[k] != m:
                return
            if L[k] <= lot.stop:
                lot.px, lot.kind, lot.xm, lot.open = min(O[k], lot.stop), 1, m, False
                return
            if H[k] >= lot.tgt + 0.01:
                lot.px, lot.kind, lot.xm, lot.open = lot.tgt, 2, m, False
                return
            if lot.tstop is not None and m >= lot.tstop:
                lot.px, lot.kind, lot.xm, lot.open = C[k], 0, m, False

        for lot in open_:
            step(lot)
        for lot in [x for x in open_ if not x.open]:
            lot.r = cost_r(lot)
            realized += lot.r
        open_ = [x for x in open_ if x.open]
        # (c) entries at minute m
        cands = []
        while pi < len(plan) and plan[pi][0] <= m:
            if plan[pi][0] == m:
                cands.append(plan[pi])
            pi += 1
        prior = sum(1 for t in booked_times if t > m - 10)
        ncand = len(cands)                      # signals of this decision minute (known at decision time)
        for (_, j, r) in cands:                 # sequential, as bench10 book(): a same-minute exit counts for the next
            if realized <= -2.0 + 1e-12:
                continue
            if len(open_) >= 30:
                continue
            if sum(1 for o in open_ if o.sym == r.symbol) >= 3:
                continue
            if cfg.get("budget") is not None:
                if realized - len(open_) * 1.0 - 1.0 < -cfg["budget"] - 1e-12:
                    continue
            bars = BARS.get((r.symbol, r.date))
            if bars is None:
                continue
            lot = Lot()
            lot.i, lot.sym, lot.stop, lot.tgt, lot.em = r.Index, r.symbol, r.stop, r.tgt, m
            lot.gap, lot.tod, lot.size, lot.tstop = r.gap, r.tod, 1.0, None
            if cfg.get("stagger") and m != r.em:
                mins, O, H, L, C = bars
                kk = np.flatnonzero(mins == m - 1)
                if not len(kk):
                    continue
                e = C[kk[0]]
                if e <= r.stop or e >= r.tgt:
                    continue
                lot.entry = e
            else:
                lot.entry = r.entry
            lot.risk = lot.entry - lot.stop
            if not lot.risk > 0:
                continue
            lot.tier = 3.0 if (abs(r.gap) >= 20 or lot.entry < 5) else 1.0
            lot.ecost = (0.01 + lot.entry * 1e-4) * float(tod_cost_mult(np.array([r.tod]))[0])
            lot.bars, lot.k, lot.open, lot.burst = bars, 0, True, None
            lot.is_burst = prior + ncand >= 4
            if cfg.get("split") and ncand >= 4:
                lot.size = 4.0 / ncand
            # burst membership
            act = bursts[-1] if bursts and m - bursts[-1]["start"] <= 10 else None
            if lot.is_burst and act is None:
                act = dict(start=m, members=[x for x in lots if x.em > m - 10], flat=False)
                for x in act["members"]:
                    x.burst = len(bursts)
                bursts.append(act)
            if act is not None:
                lot.burst = bursts.index(act)
                act["members"].append(lot)
                if cfg.get("halflate") and len(act["members"]) >= 4:
                    lot.size = 0.5
            if cfg.get("tight") and lot.is_burst:
                lot.stop = lot.entry - (0.5 if cfg["tight"] is True else cfg["tight"]) * lot.risk   # R in original risk units
            if cfg.get("btime") and lot.is_burst:
                lot.tstop = m + cfg["btime"]
            booked_times.append(m)
            lots.append(lot)
            open_.append(lot)
            step(lot)                            # bench convention: the entry minute's bar is walked too
            if not lot.open:
                lot.r = cost_r(lot)
                realized += lot.r
                open_.remove(lot)
        # (b) rule checks at the close of minute m
        def close_at(lot):
            mins, O, H, L, C = lot.bars
            kk = lot.k if lot.k < len(mins) and mins[lot.k] == m else None
            return None if kk is None else C[kk]

        def flatten(group):
            nonlocal realized
            for lot in group:
                if lot.open:
                    c = close_at(lot)
                    if c is None:
                        continue
                    lot.px, lot.kind, lot.xm, lot.open = c, 0, m, False
                    lot.r = cost_r(lot)
                    realized += lot.r

        for bi, b in enumerate(bursts):
            if b["flat"]:
                continue
            mem = b["members"]
            if not any(x.open for x in mem):
                continue
            stops = sum(1 for x in mem if not x.open and x.kind == 1)
            marks = [mark(x, close_at(x)) for x in mem if x.open and close_at(x) is not None]
            bR = sum(x.r for x in mem if not x.open) + sum(marks)
            trig = False
            if cfg.get("gstop") and stops >= cfg["gstop"]:
                trig = True
            if cfg.get("bbudget") and bR <= -cfg["bbudget"]:
                trig = True
            if cfg.get("btstop") and m == b["start"] + cfg["btstop"] and bR < 0:
                trig = True
            if trig:
                flatten(mem)
                b["flat"] = True
        open_ = [x for x in open_ if x.open]
        if cfg.get("sentinel"):
            k, X = cfg["sentinel"]
            if len(open_) >= k:
                mk = [mark(x, close_at(x)) for x in open_ if close_at(x) is not None]
                if sum(mk) <= -X:
                    flatten(open_)
                    sentinel_hits += 1
                    open_ = [x for x in open_ if x.open]
        if not open_ and pi >= len(plan):
            break
    # anything still open (no bars): close at last close
    for lot in open_:
        lot.px, lot.kind, lot.xm, lot.open = lot.bars[4][-1], 0, 15 * 60 + 55, False
        lot.r = cost_r(lot)
    out = [dict(i=l.i, sym=l.sym, em=l.em, xm=l.xm, kind=l.kind, r=l.r, size=l.size, is_burst=bool(l.is_burst),
                inburst=l.burst is not None) for l in lots]
    return out, dict(bursts=len(bursts), sentinel=sentinel_hits)


CFGS = {
    "base": {},
    "G2": dict(gstop=2), "G3": dict(gstop=3),
    "B2": dict(bbudget=2), "B3": dict(bbudget=3), "B4": dict(bbudget=4),
    "T15": dict(btstop=15), "T30": dict(btstop=30),
    "S4": dict(split=True), "SH": dict(halflate=True),
    "W3x1.5": dict(sentinel=(3, 1.5)), "W3x2.5": dict(sentinel=(3, 2.5)),
    "W4x1.5": dict(sentinel=(4, 1.5)), "W4x2.5": dict(sentinel=(4, 2.5)),
    "O4": dict(budget=4), "O6": dict(budget=6),
    "P1": dict(stagger=True), "P1W": dict(stagger=True, sentinel=(3, 1.5)),
    "Q50": dict(tight=True), "Q20": dict(btime=20),
    # plateau check of the only pre-registered finalist (added after scoring, counted: N = 21; D_PREREG.md addendum)
    "Q40": dict(tight=0.4), "Q65": dict(tight=0.65),
}

rows = []
days = sorted(S.date.unique())
G = {d: g for d, g in S.groupby("date")}
for name, cfg in [(k, v) for k, v in CFGS.items() if len(sys.argv) < 5 or k in sys.argv[4].split(",")]:
    for d in days:
        out, info = sim_day(G[d], cfg)
        for o in out:
            o.update(cfg=name, date=d)
            rows.append(o)
        if not out:
            rows.append(dict(cfg=name, date=d, r=0.0, i=-1, sym="", em=0, xm=0, kind=-1, size=0.0, is_burst=False, inburst=False))
L = pd.DataFrame(rows)
L["per"] = L.date.map(period)
L.to_parquet(OUT / "D_lots.parquet", index=False)
print("lots written", len(L))
