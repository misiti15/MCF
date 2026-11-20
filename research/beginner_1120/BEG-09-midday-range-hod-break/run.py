"""BEG-09 backtest, the "normal way" (research/ultimate_1119/top10/bench10.py: LR8 costs + borrow, testing-arena book
cap 100 / <= 3 lots per symbol / price >= $5 / ETB >= 90% / cost filter 0.15R, the same stats and SPY day types).
Signals and exits on 1-minute bars; entry by stop order (fill = max(open, trigger)).

Day context (prev close, ATR, ADV20, rank_rvol20) is reused read-only from the BEG-02 day tables (beg02w/days_*.parquet).
  python run.py WORK build t1|t2      candidate-day bars (rank <= 50, prev close >= 10, ADV >= 20M, |11:29 move| >= 2%)
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
import beg09 as G  # noqa: E402

S = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad")
DAYS = S / "beg02w"
ETB = S / "ult/research/ultimate_1119/top10/etb_rate.parquet"
CTX: dict = {}


def cand_days(test):
    D = pd.read_parquet(DAYS / f"days_{test}.parquet",
                        columns=["symbol", "date", "prev_close", "atr", "adv20", "gap", "rank_rvol20"])
    B.no_locked(D.date.unique())
    return D[(D.rank_rvol20 <= 50) & (D.prev_close >= 10) & (D.adv20 >= 20e6) & (D.atr > 0)]


def job(args):
    sym, test = args
    D = CTX["D"]
    d = D[D.symbol == sym].set_index("date")
    if test == "t1":
        b = B.hist_bars(sym)
    else:
        b = pd.read_parquet(B.FRESH / "1Min" / f"{sym}.parquet")
        b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
        b = b.sort_index()
    hh = b.index.hour * 100 + b.index.minute
    b = b[(hh >= 930) & (hh < 1600)]
    ds = b.index.date.astype(str)
    b = b[np.isin(ds, d.index.to_numpy())]
    if not len(b):
        return None
    B.no_locked(np.unique(b.index.date.astype(str)))
    out = []
    for dt, g in b.groupby(b.index.date.astype(str)):
        hm = (g.index.hour * 100 + g.index.minute).to_numpy()
        k = np.flatnonzero(hm == 1129)
        if not len(k):
            continue
        mv = (g.close.iloc[k[0]] / d.loc[dt, "prev_close"] - 1) * 100
        if abs(mv) < 2.0:
            continue
        out.append(pd.DataFrame({"symbol": sym, "date": dt, "hhmm": hm.astype(np.int16),
                                 "o": g.open.to_numpy(np.float32), "h": g.high.to_numpy(np.float32),
                                 "l": g.low.to_numpy(np.float32), "c": g.close.to_numpy(np.float32),
                                 "v": g.volume.to_numpy(np.float32)}))
    return pd.concat(out) if out else None


def init(test):
    CTX["D"] = cand_days(test)


def build(W, test):
    D = cand_days(test)
    syms = sorted(D.symbol.unique())
    cands = []
    with Pool(3, initializer=init, initargs=(test,)) as p:
        for i, c in enumerate(p.imap_unordered(job, [(s, test) for s in syms], chunksize=4)):
            if c is not None:
                cands.append(c)
            if i % 200 == 0:
                print(test, i, len(cands), flush=True)
    C = pd.concat(cands, ignore_index=True)
    B.no_locked(C.date.unique())
    C.to_parquet(Path(W) / f"cand_{test}.parquet", compression="zstd")
    print(test, "candidate days", C.groupby(["symbol", "date"]).ngroups, "rows", len(C))


VARIANTS = {"base": {}}


def load_variants():
    p = HERE / "variants.json"
    if p.exists():
        VARIANTS.update(json.loads(p.read_text()))


def run_trades(W, test, params, seed=None, armed=False):
    """seed=None: the setup's trades. seed=int: random control. armed=False: the pre-registered control (same filled
    symbol-days, entry bar uniform 12:00..14:59; look-ahead biased). armed=True: the fair control on every ARMED
    symbol-day (filled or not), entry bar uniform from the arming bar + 1 through 14:59."""
    D = cand_days(test)
    p = dict(G.P, **{k: v for k, v in params.items() if k in G.P})
    D = D[(D.rank_rvol20 <= p["rank_max"]) & (D.prev_close >= p["min_price"]) & (D.adv20 >= p["min_adv"])]
    D = D.set_index(["symbol", "date"])
    C = pd.read_parquet(Path(W) / f"cand_{test}.parquet")
    C = C.set_index(["symbol", "date"]).loc[lambda x: x.index.isin(D.index)].reset_index()
    rng = np.random.default_rng(seed) if seed is not None else None
    out = []
    for (sym, d), g in C.groupby(["symbol", "date"], sort=False):
        r = D.loc[(sym, d)]
        hh = g.hhmm.to_numpy(int)
        o, h, l, c, v = (g[k].to_numpy(float) for k in ("o", "h", "l", "c", "v"))
        if armed:
            e = G.plan(o, h, l, c, v, hh, float(r.prev_close), float(r.atr), p)
            if e is None:
                continue
            e["j"], e["fill"] = -1, np.nan
        else:
            e = G.find_entry(o, h, l, c, v, hh, float(r.prev_close), float(r.atr), p)
        if e is None:
            continue
        side, stop, tgt, j, fill = e["side"], e["stop"], e["tgt"], e["j"], e["fill"]
        if rng is not None:
            lo = hh[e["k_arm"]] + 1 if armed else 1200
            win = np.flatnonzero((hh >= lo) & (hh <= p["order_until"]))
            if armed:
                win = win[win > e["k_arm"]]
            if not len(win):
                continue
            j = int(rng.choice(win))
            dist = abs(e["trig"] - e["stop"])
            fill = o[j]
            stop, tgt = fill - side * dist, fill + side * p["tgt_r"] * dist
        w = G.walk(o, h, l, c, hh, j, fill, side, stop, tgt, p)
        if w is None:
            continue
        px, kind, xt = w
        mv = (c[hh == p["move_hhmm"]][0] / float(r.prev_close) - 1) * 100
        out.append((sym, d, int(hh[j]), side, fill, stop, tgt, abs(fill - stop), float(r.gap), px, kind, xt,
                    int(hh[e["k_arm"]]), mv, float(r.rank_rvol20), abs(fill - stop) / float(r.atr),
                    side * (e["trig"] - (e["hi"] if side == 1 else e["lo"])) / float(r.atr)))
    T = pd.DataFrame(out, columns=["symbol", "date", "tod", "side", "entry", "stop", "tgt", "risk", "gap", "px", "kind",
                                   "xt", "arm_tod", "move1129", "rank", "risk_atr", "hod_dist_atr"])
    T["setup"] = "BEG-09"
    return T


def score_one(W, name, which, seed=None, armed=False):
    load_variants()
    params = VARIANTS[name]
    etb = pd.read_parquet(ETB).rate
    spy1 = B.spy_t1()
    res, booked = {}, {}
    tests = {"fit": ["t1"], "check": ["t1"], "t2": ["t2"], "all": ["t1", "t2"], "t1": ["t1"]}[which]
    for test in tests:
        T = run_trades(W, test, params, seed, armed)
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
            if len(parts) == 2:
                res["T1_combined"] = B.stats(bk[bk.half.isin(parts)], n["fit"] + n["check"], spy1)
            booked["t1"] = bk[bk.half.isin(parts)]
        else:
            spy2 = pd.read_parquet(B.FRESH / "spy_days.parquet")
            spy2.index = spy2.index.astype(str)
            spy2 = spy2[(spy2.index >= B.T2_LO) & (spy2.index <= B.T2_HI)]["type"]
            res["T2"] = B.stats(bk, len(spy2), spy2)
            res["T2"]["raw_trades"] = int(len(T))
            booked["t2"] = bk
    tag = name + (f"_{'arm' if armed else 'rnd'}{seed}" if seed is not None else "") + "_" + which
    (Path(W) / f"res_{tag}.json").write_text(json.dumps(res, indent=1, default=float))
    if booked:
        pd.concat([v.assign(test=k) for k, v in booked.items()]).to_parquet(Path(W) / f"bk_{tag}.parquet")
    return res


if __name__ == "__main__":
    W = Path(sys.argv[1])
    W.mkdir(parents=True, exist_ok=True)
    if sys.argv[2] == "build":
        build(W, sys.argv[3])
    else:
        seed = int(sys.argv[5]) if len(sys.argv) > 5 else None
        print(json.dumps(score_one(W, sys.argv[3], sys.argv[4], seed, len(sys.argv) > 6 and sys.argv[6] == "armed"), indent=1, default=float))
