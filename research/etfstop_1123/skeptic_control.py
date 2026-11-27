"""SKEPTIC_1127 size-matched controls for AV50 (copy of partS.py: same engine, signals, costs, book; only the
control switches `rt` / `rh` / `const` / `avsize` added). Original partS docstring follows.
etfstop_1123 (PLAN.md): ETF-STOP50 plateau / variants on the rules_1122 part-D harness (partD.py, extended:
burst k / window, stop fraction, point-in-time SPY state, F5, Q50+G2, per-lot MAE/MFE). 21 configurations + base.
Original header: Part D: NM-ETF-late-dip-di-long protection study.
E4-normal-way: bench10 NM-ETF signals re-walked minute by minute by one per-day simulator that reproduces bench10
walk_trades + add_r (LR8 costs) + book (Primary: cap 30, <= 3 lots per symbol, -2R latch on realized cost-R), with the
protection rules layered on. FIT 2024-10 + 2025-03..09, T2 2023-01..2024-09, CHECK 2025-10-01..2026-11-04.
The locked block 2024-11-01..2025-02-28 is never read (pyarrow filter + assert).
Usage: python skeptic_control.py CHECKOUT TOP10W OUTDIR [NSEEDS].  Educational only - not financial advice."""
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


# ------------------------------------------------------------------ SPY point-in-time state
SPYS = {}   # date -> dict minute -> (close, vwap, open) of that completed minute
for src, dd in ((HIST, [d for d in sorted(S.date.unique()) if d >= "2024-09-16"]),
                (FRESH, [d for d in sorted(S.date.unique()) if d < "2024-09-16"])):
    f = pads.field("__index_level_0__")
    lo, hi = pd.Timestamp(dd[0], tz=TZ), pd.Timestamp(dd[-1], tz=TZ) + pd.Timedelta(days=1)
    flt = (f >= lo) & (f < hi)
    if src is HIST:
        flt = flt & ((f < pd.Timestamp(LOCK[0], tz=TZ)) | (f >= pd.Timestamp("2025-03-01", tz=TZ)))
    b = pads.dataset(str(src / "SPY.parquet"), format="parquet").to_table(filter=flt).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b = b.sort_index()
    day = b.index.date.astype(str)
    no_locked(np.unique(day))
    for d in dd:
        x = b[day == d]
        if not len(x):
            continue
        tp = (x.high + x.low + x.close) / 3
        vw = (tp * x.volume).cumsum() / x.volume.cumsum().replace(0, np.nan)
        mins = x.index.hour * 60 + x.index.minute
        o0 = float(x.open.iloc[0])
        SPYS[d] = dict(zip(mins, zip(x.close.to_numpy(float), vw.to_numpy(float), [o0] * len(x))))
        SPYS[d]["oc"] = float(x.close.iloc[-1]) / o0 - 1


def spy_state(d, m):
    """SPY state from the last completed minute before entry minute m (no look-ahead)."""
    st = SPYS.get(d)
    if not st:
        return None, None
    for mm in range(m - 1, m - 16, -1):
        if mm in st:
            c, vw, o = st[mm]
            return bool(c < vw), bool(c < o)
    return None, None


# ------------------------------------------------------------------ simulator
class Lot:
    __slots__ = ("i", "sym", "entry", "stop", "tgt", "risk", "size", "em", "tier", "ecost", "bars", "k", "open",
                 "px", "kind", "xm", "r", "burst", "is_burst", "rank", "gap", "tod", "tstop", "risk0", "midx", "bvw", "bop", "tight")


def cost_r(lot):
    xcost = (0.0 if lot.kind == 2 else 0.01 + lot.px * 1e-4) + (0.02 if lot.kind == 1 else 0.0)
    gross = lot.px - lot.entry
    return (gross - lot.tier * (lot.ecost + xcost)) / lot.risk * lot.size


def mark(lot, c):
    return (c - lot.entry) / lot.risk * lot.size


def sim_day(sig, cfg):
    """sig: signals of one day (DataFrame). Returns list of closed lots (dict) and burst info."""
    cfg = cfg or {}
    K, WIN = cfg.get("k", 4), cfg.get("win", 10)
    frac = cfg.get("tight")
    frac = 0.5 if frac is True else frac
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
        prior = sum(1 for t in booked_times if t > m - WIN)
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
            lot.is_burst = prior + ncand >= K
            lot.risk0, lot.midx, lot.tight = lot.risk, 0, False
            lot.bvw, lot.bop = spy_state(r.date, m)
            if cfg.get("split") and ncand >= 4:
                lot.size = 4.0 / ncand
            # burst membership
            act = bursts[-1] if bursts and m - bursts[-1]["start"] <= WIN else None
            if lot.is_burst and act is None:
                act = dict(start=m, members=[x for x in lots if x.em > m - WIN], flat=False)
                for x in act["members"]:
                    x.burst = len(bursts)
                bursts.append(act)
            if act is not None:
                lot.burst = bursts.index(act)
                act["members"].append(lot)
                lot.midx = len(act["members"])
                if cfg.get("halflate") and len(act["members"]) >= 4:
                    lot.size = 0.5
            per = PER_OF[r.date]
            if cfg.get("const") is not None:                 # constant size cut, every lot
                lot.size = cfg["const"][per]
            if cfg.get("avsize") and lot.is_burst and lot.bvw is True:   # AV50 lots, half size instead of half stop
                lot.size = 0.5
            if cfg.get("rt") is not None or cfg.get("rh") is not None:     # random selection (pool, p per period, seed)
                pool, p, seed = cfg.get("rt") or cfg.get("rh")
                inpool = lot.is_burst if pool == "burst" else True
                if inpool and U[seed, r.Index] < p[per]:
                    if cfg.get("rt") is not None:
                        lot.stop = lot.entry - 0.5 * lot.risk
                        lot.tight = True
                    else:
                        lot.size = 0.5
                        lot.tight = True
            if frac and lot.is_burst:
                ok = True
                if cfg.get("against") == "vwap":
                    ok = lot.bvw is True
                elif cfg.get("against") == "open":
                    ok = lot.bop is True
                if cfg.get("from5"):
                    ok = ok and lot.midx >= 5
                if ok:
                    lot.stop = lot.entry - frac * lot.risk   # R in original risk units
                    lot.tight = True
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
    out = []
    for l in lots:
        mins, O, H, L, C = l.bars
        sel = (mins >= l.em) & (mins <= l.xm)
        mae = (l.entry - L[sel].min()) / l.risk0 if sel.any() else np.nan
        mfe = (H[sel].max() - l.entry) / l.risk0 if sel.any() else np.nan
        out.append(dict(i=l.i, sym=l.sym, em=l.em, xm=l.xm, kind=l.kind, r=l.r, size=l.size, is_burst=bool(l.is_burst),
                        inburst=l.burst is not None, midx=l.midx, tight=bool(l.tight), bvw=l.bvw, bop=l.bop,
                        mae=mae, mfe=mfe))
    return out, dict(bursts=len(bursts), sentinel=sentinel_hits)



PER_OF = {d: period(d) for d in S.date.unique()}
NSEEDS = int(sys.argv[4]) if len(sys.argv) > 4 else 200
U = np.random.default_rng(1127).random((NSEEDS, int(S.index.max()) + 1))
days = sorted(S.date.unique())
G = {d: g for d, g in S.groupby("date")}
PERS = ("FIT", "T2", "CHECK")


def run(name, cfg):
    rows = []
    for d in days:
        out, _ = sim_day(G[d], cfg)
        for o in out:
            o.update(cfg=name, date=d)
            rows.append(o)
        if not out:
            rows.append(dict(cfg=name, date=d, r=0.0, i=-1, sym="", em=0, xm=0, kind=-1, size=0.0, is_burst=False,
                             inburst=False, tight=False))
    x = pd.DataFrame(rows)
    x["per"] = x.date.map(period)
    return x


B = run("base", {})
A = run("AV50", dict(tight=0.5, against="vwap"))
Q = run("Q50", dict(tight=0.5))
# size matching (per period): AV50 halves the stop-risk of its tight lots -> exposure cut = 0.5 * tight / lots
ntA = A[A.i >= 0].groupby("per").tight.sum()
nA = A[A.i >= 0].groupby("per").size()
nbQ = Q[Q.i >= 0].groupby("per").is_burst.sum()          # burst lots (pool for the burst-only random control)
p_all = {p: float(ntA[p] / nA[p]) for p in PERS}
p_burst = {p: float(ntA[p] / nbQ[p]) for p in PERS}
const = {p: 1.0 - 0.5 * p_all[p] for p in PERS}
print("AV50 tight lots", ntA.to_dict(), "lots", nA.to_dict(), "burst lots", nbQ.to_dict())
print("p_all", p_all, "p_burst", p_burst, "const size", const)
parts = [B, A, Q, run("CONST", dict(const=const)), run("AVSIZE", dict(avsize=True))]
for s in range(NSEEDS):
    parts.append(run("RTB%03d" % s, dict(rt=("burst", p_burst, s))))   # half stop, random burst lots
    parts.append(run("RTA%03d" % s, dict(rt=("all", p_all, s))))       # half stop, random lots of any kind
    parts.append(run("RHA%03d" % s, dict(rh=("all", p_all, s))))       # half SIZE, random lots of any kind
    if s % 20 == 0:
        print("seed", s, flush=True)
L = pd.concat(parts, ignore_index=True)
no_locked(L.date.unique())
L[["cfg", "date", "per", "i", "r", "size", "is_burst", "tight", "bvw"]].to_parquet(OUT / "K_lots.parquet", index=False)
print("lots written", len(L))
