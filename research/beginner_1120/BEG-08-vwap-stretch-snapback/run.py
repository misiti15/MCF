"""BEG-08 backtest, the "normal way" (research/ultimate_1119/top10/bench10.py: LR8 costs + 1.2 bp borrow on shorts,
testing-arena book cap 100 / <= 3 lots per symbol / price >= $5 / ETB >= 0.9 for shorts / cost filter 0.15R, the same
stats and SPY day types). Signals and exits on 1-minute bars read straight from the bar caches.

  python run.py WORK score VARIANT fit|check|all|t2 [SEED same|univ]   -> WORK/res_<tag>.json, WORK/bk_<tag>.parquet
Candidate days: the BEG-02 day table (scratchpad beg02w/days_t*.parquet). The locked block 2024-11-01..2025-02-28 is
never read (bench10.hist_bars filter + asserts). Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
import zlib
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
import beg08 as G  # noqa: E402

S = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad")
DAYS = {"t1": S / "beg02w/days_t1.parquet", "t2": S / "beg02w/days_t2.parquet"}
ETB = S / "ult/research/ultimate_1119/top10/etb_rate.parquet"
VARIANTS = {"base": {}}
COLS = ["symbol", "date", "tod", "side", "entry", "stop", "tgt", "risk", "gap", "px", "kind", "xt", "rank_rvol20",
        "sig_tod", "stop_atr", "tgt_r_plan", "atr", "rsi5", "stretch_atr", "run_len", "setup_tod"]


def load_variants():
    p = HERE / "variants.json"
    if p.exists():
        VARIANTS.update(json.loads(p.read_text()))


def cand_days(test, p):
    D = pd.read_parquet(DAYS[test], columns=["symbol", "date", "prev_close", "atr", "adv20", "gap", "rank_rvol20"])
    B.no_locked(D.date.unique())
    D = D[(D.prev_close >= p["min_price"]) & (D.adv20 >= p["min_adv"]) & (D.rank_rvol20 > p["rank_min"]) & (D.atr > 0)]
    if test == "t1":
        D = D[D.date <= "2026-11-04"]
    else:
        D = D[(D.date >= B.T2_LO) & (D.date <= B.T2_HI)]
    return D


def load_bars(test, sym):
    if test == "t1":
        b = B.hist_bars(sym)
    else:
        f = B.FRESH / "1Min" / f"{sym}.parquet"
        if not f.exists():
            return None
        b = pd.read_parquet(f)
        b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
        b = b.sort_index()
    hh = b.index.hour * 100 + b.index.minute
    return b[(hh >= 930) & (hh < 1600)]


def sym_job(args):
    test, sym, rows, p, seed, ctl, same, med_stop = args
    b = load_bars(test, sym)
    if b is None or not len(b):
        return []
    day = b.index.date.astype(str)
    hhall = (b.index.hour * 100 + b.index.minute).to_numpy(int)
    O, H, L, C, V = (b[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))
    RSI = G.rsi5_on_1min(b.index, C, p["rsi_n"])
    rng = np.random.default_rng(None if seed is None else (seed * 7919 + zlib.crc32(sym.encode()) % 100003))
    can_short = sym not in G.NO_SHORT
    out = []
    for r in rows:
        ix = np.flatnonzero(day == r["date"])
        if not len(ix):
            continue
        hh = hhall[ix]
        if hh[0] != 930:
            continue
        o, h, l, c, v, rsi = O[ix], H[ix], L[ix], C[ix], V[ix], RSI[ix]
        atr = r["atr"]
        vw = G.vwap(h, l, c, v)
        if ctl is None:
            trades = G.day_trades(o, h, l, c, v, hh, rsi, atr, can_short, p)
        else:
            win = np.flatnonzero((hh >= p["win_lo"]) & (hh <= p["win_hi"]))
            win = win[win + 1 < len(o)]
            if not len(win):
                continue
            trades = []
            if ctl == "same":
                for side, dist in same.get((sym, r["date"]), []):
                    trades.append((int(rng.choice(win)), side, dist))
            else:
                k = int(rng.choice(win))
                side = -1 if c[k] > vw[k] else 1
                if side < 0 and not can_short:
                    continue
                trades.append((k, side, med_stop * atr))
            tt = []
            for k, side, dist in trades:
                ck = float(c[k])
                stop = ck - side * dist
                tgt = float(vw[k]) if side * (vw[k] - ck) > 0 else None
                j = k + 1
                fill = float(o[j])
                if side * (fill - stop) <= 0 or (tgt is not None and side * (tgt - fill) <= 0):
                    continue
                px, kind, xt, kx = G.walk(o, h, l, c, hh, j, side, stop, tgt, p)
                tt.append(dict(k=k, j=j, fill=fill, side=side, stop=stop, tgt=tgt, ref=ck, s0=k - 1, px=px,
                               kind=kind, xt=xt))
            trades = tt
        for e in trades:
            dist = abs(e["ref"] - e["stop"])
            k, s0 = e["k"], e["s0"]
            out.append((sym, r["date"], int(hh[e["j"]]), e["side"], e["fill"], e["stop"],
                        np.nan if e["tgt"] is None else e["tgt"], abs(e["fill"] - e["stop"]), r["gap"], e["px"],
                        e["kind"], e["xt"], r["rank_rvol20"], int(hh[k]), dist / atr,
                        np.nan if e["tgt"] is None else abs(e["tgt"] - e["ref"]) / max(dist, 1e-9), atr,
                        float(rsi[k - 1]), float((c[k - 1] - vw[k - 1]) / atr), int(k - s0), int(hh[s0])))
    return out


def run_trades(test, params, seed=None, ctl=None, same=None, med_stop=None, part=None):
    p = dict(G.P, **{k: v for k, v in params.items() if k in G.P})
    D = cand_days(test, p)
    if part is not None:                 # fit-only runs never touch CHECK days (and vice versa)
        D = D[B.half(D.date) == part]
    if ctl == "same":
        D = D[[(s, d) in same for s, d in zip(D.symbol, D.date)]]
    jobs = [(test, s, g.to_dict("records"), p, seed, ctl, same or {}, med_stop) for s, g in D.groupby("symbol")]
    with Pool(4) as pool:
        out = [x for res in pool.imap_unordered(sym_job, jobs, chunksize=4) for x in res]
    T = pd.DataFrame(out, columns=COLS)
    B.no_locked(T.date.unique())
    T["setup"] = "BEG-08"
    return T


def score_one(W, name, which, seed=None, ctl=None):
    load_variants()
    params = VARIANTS[name]
    etb = pd.read_parquet(ETB).rate
    spy1 = B.spy_t1()
    spy1 = spy1[spy1.index <= "2026-11-04"]
    same, med = None, {}
    if ctl is not None:
        bk0 = pd.read_parquet(W / f"bk_{name}_{which}.parquet")
        if ctl == "same":
            same = {}
            for s, d, sd, e, st in zip(bk0.symbol, bk0.date, bk0.side, bk0.entry, bk0.stop):
                same.setdefault((s, d), []).append((int(sd), abs(e - st)))
        med = {t: float(g.stop_atr.median()) for t, g in bk0.groupby("test")}
    res, booked = {}, {}
    tests = {"fit": ["t1"], "check": ["t1"], "t2": ["t2"], "all": ["t1", "t2"]}[which]
    for test in tests:
        T = run_trades(test, params, seed, ctl, same, med.get(test), which if which in ("fit", "check") else None)
        if test == "t1":
            T = T[B.half(T.date) != "none"] if len(T) else T
            if which in ("fit", "check"):
                T = T[B.half(T.date) == which]
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
            if which == "all":
                res["T1_combined"] = B.stats(bk, n["fit"] + n["check"], spy1)
            booked["t1"] = bk[bk.half.isin(parts)]
        else:
            spy2 = pd.read_parquet(B.FRESH / "spy_days.parquet")
            spy2.index = spy2.index.astype(str)
            spy2 = spy2[(spy2.index >= B.T2_LO) & (spy2.index <= B.T2_HI)]["type"]
            res["T2"] = B.stats(bk, len(spy2), spy2)
            res["T2"]["raw_trades"] = int(len(T))
            booked["t2"] = bk
    tag = name + (f"_rnd{seed}{ctl}" if seed is not None else "") + "_" + which
    (W / f"res_{tag}.json").write_text(json.dumps(res, indent=1, default=float))
    if booked:
        pd.concat([v.assign(test=k) for k, v in booked.items()]).to_parquet(W / f"bk_{tag}.parquet")
    return res


if __name__ == "__main__":
    W = Path(sys.argv[1])
    W.mkdir(parents=True, exist_ok=True)
    if sys.argv[2] == "score":
        seed = int(sys.argv[5]) if len(sys.argv) > 5 else None
        ctl = sys.argv[6] if len(sys.argv) > 6 else None
        print(json.dumps(score_one(W, sys.argv[3], sys.argv[4], seed, ctl), indent=1, default=float))
