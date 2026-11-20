"""BEG-03 backtest, the "normal way" (research/ultimate_1119/top10/bench10.py: LR8 costs, testing-arena book cap 100 /
<= 3 lots per symbol / price >= $5 / cost filter 0.15R, the same stats and SPY day types). Signals and exits on 1-minute
bars (stop entry, 1-minute rule).

  python run.py WORK build t1|t2        candidate symbol-days (gap >= 3%, RVOL20 >= 2, prior close 5-200, ADV20 >= $20M)
                                         from the BEG-02 day table (same RVOL20 definition) + their 09:30-12:59 bars
  python run.py WORK score VARIANT fit|check|t2|all [SEED [pre|after|univ]]   -> WORK/res_<tag>.json, WORK/bk_<tag>.parquet
The locked block 2024-11-01..2025-02-28 is never read (bench10.hist_bars filter + asserts). Educational only - not
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
import beg03 as G  # noqa: E402

S = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad")
DAYS = {"t1": S / "beg02w/days_t1.parquet", "t2": S / "beg02w/days_t2.parquet"}   # BEG-02 day table (run.py build1/2)
ETB = S / "ult/research/ultimate_1119/top10/etb_rate.parquet"
VARIANTS = {"base": {}}


def load_variants():
    p = HERE / "variants.json"
    if p.exists():
        VARIANTS.update(json.loads(p.read_text()))


def bars_job(args):
    test, sym, dates = args
    if test == "t1":
        b = B.hist_bars(sym)
    else:
        b = pd.read_parquet(B.FRESH / "1Min" / f"{sym}.parquet")
        b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
        b = b.sort_index()
    hh = b.index.hour * 100 + b.index.minute
    b = b[(hh >= 930) & (hh < 1300)]
    d = b.index.date.astype(str)
    b = b[np.isin(d, list(dates))]
    if not len(b):
        return None
    return pd.DataFrame({"symbol": sym, "date": b.index.date.astype(str),
                         "hhmm": (b.index.hour * 100 + b.index.minute).astype(np.int16),
                         "o": b.open.to_numpy(np.float32), "h": b.high.to_numpy(np.float32),
                         "l": b.low.to_numpy(np.float32), "c": b.close.to_numpy(np.float32),
                         "v": b.volume.to_numpy(np.float32)})


def build(W, test):
    D = pd.read_parquet(DAYS[test], columns=["symbol", "date", "prev_close", "atr", "adv20", "gap", "rvol20"])
    B.no_locked(D.date.unique())
    D = D[(D.gap >= 3.0) & (D.rvol20 >= 2.0) & D.prev_close.between(5, 200) & (D.adv20 >= 20e6)]
    D.to_parquet(W / f"cand_days_{test}.parquet")
    jobs = [(test, s, set(g.date)) for s, g in D.groupby("symbol")]
    with Pool(3) as p:
        out = [x for x in p.imap_unordered(bars_job, jobs, chunksize=4) if x is not None]
    C = pd.concat(out, ignore_index=True)
    B.no_locked(C.date.unique())
    if test == "t2":
        assert C.date.min() >= B.T2_LO and C.date.max() <= B.T2_HI
    C.to_parquet(W / f"cand_bars_{test}.parquet", compression="zstd")
    print(test, "candidate days", len(D), "with bars", C.groupby(["symbol", "date"]).ngroups, "rows", len(C))


def run_trades(W, test, params, seed=None, ctl="pre"):
    p = dict(G.P, **{k: v for k, v in params.items() if k in G.P})
    D = pd.read_parquet(W / f"cand_days_{test}.parquet")
    D = D[(D.gap >= p["gap_min"]) & (D.rvol20 >= p["rvol_min"]) & D.prev_close.between(p["min_price"], p["max_price"])
          & (D.adv20 >= p["min_adv"])].set_index(["symbol", "date"])
    C = pd.read_parquet(W / f"cand_bars_{test}.parquet")
    C = C.set_index(["symbol", "date"]).loc[lambda x: x.index.isin(D.index)].reset_index()
    rng = np.random.default_rng(seed) if seed is not None else None
    out = []
    for (sym, d), g in C.groupby(["symbol", "date"], sort=False):
        r = D.loc[(sym, d)]
        hh = g.hhmm.to_numpy(int)
        o, h, l, c, v = (g[k].to_numpy(float) for k in ("o", "h", "l", "c", "v"))
        win = np.flatnonzero((hh >= p["win_lo"]) & (hh <= p["win_hi"]))
        if ctl == "univ":       # control (added after the base, not fitted): every universe day, no trigger condition
            if not len(win):
                continue
            j = int(rng.choice(win))
            vw = G.vwap(h, l, c, v)
            r20 = hh <= p["r20_hi"]
            stop = max(l[r20].min(), vw[j - 1]) - p["stop_off"]
            dist = o[j] - stop
            if not (r20.any() and hh[0] == 930 and dist > 0 and p["min_stop_pct"] <= dist / o[j] * 100 <= p["max_stop_pct"]):
                continue
            e = dict(j=j, fill=float(o[j]), trig=float(o[j]), stop=float(stop), tgt=float(o[j] + p["tgt_r"] * dist))
        else:
            e = G.find_entry(o, h, l, c, v, hh, p)
            if e is None:
                continue
        if rng is not None and ctl in ("pre", "after"):
            # pre (PLAN.md): uniform over the whole window; after (added after the base, not fitted): uniform over the
            # window bars at or after the setup's own fill bar, so the control does not know a breakout comes later
            ww = win if ctl == "pre" else win[win >= e["j"]]
            j = int(rng.choice(ww))
            dist = e["trig"] - e["stop"]
            e = dict(j=j, fill=float(o[j]), trig=float(o[j]), stop=float(o[j] - dist), tgt=float(o[j] + p["tgt_r"] * dist))
        w = G.walk(o, h, l, c, hh, e["j"], e["fill"], e["stop"], e["tgt"], p)
        if w is None:
            continue
        px, kind, xt = w
        out.append((sym, d, int(hh[e["j"]]), 1, e["fill"], e["stop"], e["tgt"], e["fill"] - e["stop"], float(r.gap), px,
                    kind, xt, float(r.rvol20), (e["trig"] - e["stop"]) / e["trig"] * 100, float(r.prev_close),
                    float(r.atr)))
    T = pd.DataFrame(out, columns=["symbol", "date", "tod", "side", "entry", "stop", "tgt", "risk", "gap", "px", "kind",
                                   "xt", "rvol20", "stop_pct", "prev_close", "atr"])
    T["setup"] = "BEG-03"
    return T


def score_one(W, name, which, seed=None, ctl="pre"):
    load_variants()
    params = VARIANTS[name]
    etb = pd.read_parquet(ETB).rate
    spy1 = B.spy_t1()
    spy1 = spy1[spy1.index <= "2026-11-04"]
    res, booked = {}, {}
    tests = {"fit": ["t1"], "check": ["t1"], "t2": ["t2"], "all": ["t1", "t2"]}[which]
    for test in tests:
        T = run_trades(W, test, params, seed, ctl)
        if not len(T):
            continue
        T = B.add_r(T)
        bk = B.book(T, B.TESTING_RULES, etb)
        if test == "t1":
            h = B.half(pd.Series(spy1.index))
            n = {"fit": int((h == "fit").sum()), "check": int((h == "check").sum())}
            bk["half"] = B.half(bk.date)
            parts = ["fit", "check"] if which == "all" else [which]
            for part in parts:
                res["T1_" + part] = B.stats(bk[bk.half == part], n[part], spy1)
                res["T1_" + part]["raw_trades"] = int((B.half(T.date) == part).sum())
            booked["t1"] = bk[bk.half.isin(parts)]
        else:
            spy2 = pd.read_parquet(B.FRESH / "spy_days.parquet")
            spy2.index = spy2.index.astype(str)
            spy2 = spy2[(spy2.index >= B.T2_LO) & (spy2.index <= B.T2_HI)]["type"]
            res["T2"] = B.stats(bk, len(spy2), spy2)
            res["T2"]["raw_trades"] = int(len(T))
            booked["t2"] = bk
    tag = name + (f"_rnd{seed}" + ("" if ctl == "pre" else ctl) if seed is not None else "") + "_" + which
    (W / f"res_{tag}.json").write_text(json.dumps(res, indent=1, default=float))
    if booked:
        pd.concat([v.assign(test=k) for k, v in booked.items()]).to_parquet(W / f"bk_{tag}.parquet")
    return res


if __name__ == "__main__":
    W = Path(sys.argv[1])
    W.mkdir(parents=True, exist_ok=True)
    if sys.argv[2] == "build":
        build(W, sys.argv[3])
    elif sys.argv[2] == "score":
        seed = int(sys.argv[5]) if len(sys.argv) > 5 else None
        ctl = sys.argv[6] if len(sys.argv) > 6 else "pre"
        print(json.dumps(score_one(W, sys.argv[3], sys.argv[4], seed, ctl), indent=1, default=float))
