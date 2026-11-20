"""BEG-10 backtest, the "normal way" (research/ultimate_1119/top10/bench10.py: LR8 costs + borrow, testing-arena book
cap 100 / <= 3 lots per symbol / price >= $5 / ETB >= 90% / cost filter 0.15R, the same stats and SPY day types).
Signals and exits on 1-minute bars; entry by OCO stop orders (fill = max(open, trigger)).

Day context (prev close, ATR, ADV20) is reused read-only from the BEG-02 day tables (beg02w/days_*.parquet);
prev_high / prev_low = the prior RTH session's high / low from the same 1-minute bars (a prior session more than
5 calendar days back, e.g. across the locked block, gives no NR flag -> the day is skipped).
  python run.py WORK build t1|t2      NR-day bars (prev close >= 10, ADV >= 30M, prev range <= 0.6 x ATR)
  python run.py WORK score VARIANT fit|check|t2|all [seed]
Locked block 2024-11-01..2025-02-28 is never read (bench10.hist_bars filter + asserts). Educational only - not
financial advice."""
from __future__ import annotations

import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research/ultimate_1119/top10"))
import bench10 as B  # noqa: E402
import beg10 as G  # noqa: E402

S = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad")
DAYS = S / "beg02w"
ETB = S / "ult/research/ultimate_1119/top10/etb_rate.parquet"
CTX: dict = {}


def base_days(test):
    D = pd.read_parquet(DAYS / f"days_{test}.parquet", columns=["symbol", "date", "prev_close", "atr", "adv20", "gap"])
    B.no_locked(D.date.unique())
    return D[(D.prev_close >= 10) & (D.adv20 >= 30e6) & (D.atr > 0)]


def job(args):
    sym, test = args
    d = CTX["D"]
    d = d[d.symbol == sym].set_index("date")
    if test == "t1":
        b = B.hist_bars(sym)
    else:
        b = pd.read_parquet(B.FRESH / "1Min" / f"{sym}.parquet")
        b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
        b = b.sort_index()
    hh = b.index.hour * 100 + b.index.minute
    b = b[(hh >= 930) & (hh < 1600)]
    if not len(b):
        return None, None
    B.no_locked(np.unique(b.index.date.astype(str)))
    ds = b.index.date.astype(str)
    g = b.groupby(ds)
    dd = pd.DataFrame({"hi": g.high.max(), "lo": g.low.min()}).sort_index()
    dt = pd.to_datetime(dd.index)
    ok = (dt - pd.Series(dt).shift(1).to_numpy()).days <= 5
    dd["ph"] = np.where(ok, dd.hi.shift(1), np.nan)
    dd["pl"] = np.where(ok, dd.lo.shift(1), np.nan)
    j = d.join(dd[["ph", "pl"]], how="inner").dropna(subset=["ph", "pl"])
    j["prange_atr"] = (j.ph - j.pl) / j.atr
    rows = j.reset_index()[["date", "ph", "pl", "prange_atr"]].assign(symbol=sym)
    nr = j[j.prange_atr <= 0.6]
    if not len(nr):
        return rows, None
    bb = b[np.isin(ds, nr.index.to_numpy())]
    hm = (bb.index.hour * 100 + bb.index.minute).to_numpy()
    bb = bb[hm <= 1555]
    hm = hm[hm <= 1555]
    cand = pd.DataFrame({"symbol": sym, "date": bb.index.date.astype(str), "hhmm": hm.astype(np.int16),
                         "o": bb.open.to_numpy(np.float32), "h": bb.high.to_numpy(np.float32),
                         "l": bb.low.to_numpy(np.float32), "c": bb.close.to_numpy(np.float32)})
    return rows, cand


def init(test):
    CTX["D"] = base_days(test)


def build(W, test):
    D = base_days(test)
    syms = sorted(D.symbol.unique())
    rows, cands = [], []
    with Pool(3, initializer=init, initargs=(test,)) as p:
        for i, (r, c) in enumerate(p.imap_unordered(job, [(s, test) for s in syms], chunksize=4)):
            if r is not None:
                rows.append(r)
            if c is not None:
                cands.append(c)
            if i % 200 == 0:
                print(test, i, len(cands), flush=True)
    R = pd.concat(rows, ignore_index=True)
    R.to_parquet(Path(W) / f"prange_{test}.parquet")
    C = pd.concat(cands, ignore_index=True)
    B.no_locked(C.date.unique())
    C.to_parquet(Path(W) / f"cand_{test}.parquet", compression="zstd")
    print(test, "days with prev range", len(R), "NR share", round(float((R.prange_atr <= 0.6).mean()), 3),
          "NR candidate days", C.groupby(["symbol", "date"]).ngroups, "rows", len(C))


VARIANTS = {"base": {}}


def load_variants():
    p = HERE / "variants.json"
    if p.exists():
        VARIANTS.update(json.loads(p.read_text()))


def run_trades(W, test, params, etb, seed=None, parts=None):
    """seed=None: the setup's trades. seed=int: the random control on every ARMED symbol-day (OCO placed, filled or
    not): side drawn at random (long, or short if ETB), entry at the open of a bar drawn uniformly from 10:00..12:29,
    the same $ stop distance and the same R-multiple target as the setup; same exits."""
    D = base_days(test)
    p = dict(G.P, **{k: (tuple(v) if k == "sides" else v) for k, v in params.items() if k in G.P})
    R = pd.read_parquet(Path(W) / f"prange_{test}.parquet")
    D = D.merge(R, on=["symbol", "date"])
    D = D[(D.prev_close >= p["min_price"]) & (D.adv20 >= p["min_adv"]) & (D.prange_atr <= p["nr_atr"])]
    D = D.set_index(["symbol", "date"])
    import pyarrow.parquet as pq
    C = pq.read_table(Path(W) / f"cand_{test}.parquet", read_dictionary=["symbol", "date"]).to_pandas()
    if parts is not None:                     # only the requested T1 half is walked
        dc = C.date.cat.categories.to_numpy().astype(str)
        C = C[np.isin(B.half(dc), parts)[C.date.cat.codes.to_numpy()]]
    sc, dcode = C.symbol.cat.codes.to_numpy(), C.date.cat.codes.to_numpy()
    scat, dcat = C.symbol.cat.categories, C.date.cat.categories
    cut = np.flatnonzero((np.diff(sc) != 0) | (np.diff(dcode) != 0)) + 1
    starts, ends = np.r_[0, cut], np.r_[cut, len(C)]
    HH, O_, H_, L_, C_ = (C[k].to_numpy() for k in ("hhmm", "o", "h", "l", "c"))
    Dd = {k: v for k, v in zip(D.index, D[["atr", "gap", "prange_atr"]].itertuples(index=False))}
    rng = np.random.default_rng(seed) if seed is not None else None
    out = []
    for a, z in zip(starts, ends):
        sym, d = str(scat[sc[a]]), str(dcat[dcode[a]])
        r = Dd.get((sym, d))
        if r is None:
            continue
        hh = HH[a:z].astype(int)
        o, h, l, c = (x[a:z].astype(float) for x in (O_, H_, L_, C_))
        is_etb = bool(etb.get(sym, 0) >= 0.9)
        atr = float(r.atr)
        if rng is None:
            e = G.find_entry(o, h, l, hh, atr, p, etb=is_etb)
            if e is None:
                continue
            side, stop, tgt, j, fill, trig = e["side"], e["stop"], e["tgt"], e["j"], e["fill"], e["trig"]
        else:
            pl = G.plan(h, l, hh, atr, p)
            if pl is None:
                continue
            legs = {s: v for s, v in pl["legs"].items() if s == 1 or is_etb}
            if not legs:
                continue
            side = int(rng.choice(sorted(legs)))
            trig, stop0, _ = legs[side]
            win = np.flatnonzero((hh >= p["win_lo"]) & (hh <= p["win_hi"]))
            if not len(win):
                continue
            j = int(rng.choice(win))
            dist = abs(trig - stop0)
            fill = o[j]
            stop, tgt = fill - side * dist, fill + side * p["tgt_r"] * dist
            e = dict(hi=pl["hi"], lo=pl["lo"])
        w = G.walk(o, h, l, c, hh, j, fill, side, stop, tgt, p)
        if w is None:
            continue
        px, kind, xt = w
        out.append((sym, d, int(hh[j]), side, fill, stop, tgt, abs(fill - stop), float(r.gap), px, kind, xt,
                    float(r.prange_atr), (e["hi"] - e["lo"]) / atr, abs(fill - stop) / atr,
                    side * (fill - trig) / abs(fill - stop) if rng is None else 0.0))
    T = pd.DataFrame(out, columns=["symbol", "date", "tod", "side", "entry", "stop", "tgt", "risk", "gap", "px", "kind",
                                   "xt", "prange_atr", "or_atr", "risk_atr", "slip_r"])
    T["setup"] = "BEG-10"
    return T


def score_one(W, name, which, seed=None):
    load_variants()
    params = VARIANTS[name]
    etb = pd.read_parquet(ETB).rate
    spy1 = B.spy_t1()
    res, booked = {}, {}
    tests = {"fit": ["t1"], "check": ["t1"], "t2": ["t2"], "all": ["t1", "t2"], "t1": ["t1"]}[which]
    for test in tests:
        T = run_trades(W, test, params, etb, seed, parts=None if test == 't2' else ([which] if which in ('fit', 'check') else ['fit', 'check']))
        if not len(T):
            continue
        T = B.add_r(T)
        bk = B.book(T, B.TESTING_RULES, etb)
        if test == "t1":
            days = pd.Series(spy1.index)
            days = days[days <= "2026-11-04"]
            h = B.half(days)
            n = {"fit": int((h == "fit").sum()), "check": int((h == "check").sum())}
            bk["half"] = B.half(bk.date)
            parts = ["fit", "check"] if which in ("all", "t1") else [which]
            for part in parts:
                res["T1_" + part] = B.stats(bk[bk.half == part], n[part], spy1)
                res["T1_" + part]["raw_trades"] = int((B.half(T.date) == part).sum())
                for s, nm in ((1, "long"), (-1, "short")):
                    x = bk[(bk.half == part) & (bk.side == s)]
                    res["T1_" + part][f"avg_r_{nm}"] = round(float(x.r.mean()), 4) if len(x) else None
                    res["T1_" + part][f"n_{nm}"] = int(len(x))
            if len(parts) == 2:
                res["T1_combined"] = B.stats(bk[bk.half.isin(parts)], n["fit"] + n["check"], spy1)
            booked["t1"] = bk[bk.half.isin(parts)]
        else:
            spy2 = pd.read_parquet(B.FRESH / "spy_days.parquet")
            spy2.index = spy2.index.astype(str)
            spy2 = spy2[(spy2.index >= B.T2_LO) & (spy2.index <= B.T2_HI)]["type"]
            res["T2"] = B.stats(bk, len(spy2), spy2)
            res["T2"]["raw_trades"] = int(len(T))
            for s, nm in ((1, "long"), (-1, "short")):
                x = bk[bk.side == s]
                res["T2"][f"avg_r_{nm}"] = round(float(x.r.mean()), 4) if len(x) else None
                res["T2"][f"n_{nm}"] = int(len(x))
            booked["t2"] = bk
    tag = name + (f"_rnd{seed}" if seed is not None else "") + "_" + which
    (Path(W) / f"res_{tag}.json").write_text(json.dumps(res, indent=1, default=float))
    if booked and seed is None:
        pd.concat([v.assign(test=k) for k, v in booked.items()]).to_parquet(Path(W) / f"bk_{tag}.parquet")
    return res


if __name__ == "__main__":
    W = Path(sys.argv[1])
    W.mkdir(parents=True, exist_ok=True)
    if sys.argv[2] == "build":
        build(W, sys.argv[3])
    else:
        seed = int(sys.argv[5]) if len(sys.argv) > 5 else None
        print(json.dumps(score_one(W, sys.argv[3], sys.argv[4], seed), indent=1, default=float))
