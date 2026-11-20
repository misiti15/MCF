"""BEG-02 backtest, the "normal way" (research/ultimate_1119/top10/bench10.py: LR8 costs + borrow, testing-arena book
cap 100 / <= 3 lots per symbol / price >= $5 / ETB >= 90% / cost filter 0.15R, the same stats and SPY day types).
Signals and exits are on 1-minute bars (the setup is defined on 1-minute bars), entry at the next bar open (spec).

  python run.py WORK build1   T1: per-symbol day table (rvol20 inputs, 09:50 move, trend side) + candidate-day bars
  python run.py WORK build2   T2 2023-01-03..2024-09-13 (data/cache_fresh, 469 symbols), same outputs
  python run.py WORK score VARIANT [fit|check|t2|all]   signals + walk + book + stats -> WORK/res_<variant>.json
Locked block 2024-11-01..2025-02-28 is never read (pyarrow filter + asserts, as bench10). Educational only - not
financial advice."""
from __future__ import annotations

import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research/ultimate_1119/top10"))
import bench10 as B  # noqa: E402
import beg02 as G  # noqa: E402

FRAMES = Path("/home/user/MCF/research/history2y/data/frames")
ETB = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ult/research/ultimate_1119/top10/etb_rate.parquet")
CTX: dict = {}


# ------------------------------------------------------------------------------------------------ build
def day_rows(sym, b, daily):
    """b: RTH 1-minute bars of one symbol; daily: DataFrame date -> prev_close, atr, adv20 (point-in-time).
    -> (day table rows, candidate bars)"""
    hh = b.index.hour * 100 + b.index.minute
    b = b[(hh >= 930) & (hh < 1600)]
    if not len(b):
        return [], None
    day = b.index.date.astype(str)
    hhmm = (b.index.hour * 100 + b.index.minute).to_numpy()
    O, H, L, C, V = (b[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))
    rows, keep = [], []
    starts = np.flatnonzero(np.r_[True, day[1:] != day[:-1]])
    ends = np.r_[starts[1:], len(day)]
    for a, e in zip(starts, ends):
        d = day[a]
        if d not in daily.index:
            continue
        pc, atr, adv = daily.loc[d, ["prev_close", "atr", "adv20"]]
        hm = hhmm[a:e]
        v0949 = float(V[a:e][hm <= 949].sum())
        vw = G.vwap(H[a:e], L[a:e], C[a:e], V[a:e])
        side, mv = G.setup_side(hm, C[a:e], vw, pc)
        rows.append((sym, d, pc, atr, adv, v0949, mv, side, (O[a] / pc - 1) * 100 if pc > 0 else np.nan))
        if side != 0 and pc >= 10 and adv >= 20e6 and atr > 0:
            keep.append(np.arange(a, e))
    cand = None
    if keep:
        ix = np.concatenate(keep)
        cand = pd.DataFrame({"symbol": sym, "date": day[ix], "hhmm": hhmm[ix].astype(np.int16),
                             "o": O[ix].astype(np.float32), "h": H[ix].astype(np.float32),
                             "l": L[ix].astype(np.float32), "c": C[ix].astype(np.float32),
                             "v": V[ix].astype(np.float32)})
    return rows, cand


def t1_ctx():
    out = []
    for p in sorted(FRAMES.glob("month=*")):
        m = p.name.split("=")[1]
        if m in B.LOCKED_MONTHS:
            continue
        t = pads.dataset(str(p), format="parquet").to_table(
            columns=["symbol", "date", "tod", "gap", "atr_d", "adv20"], filter=pads.field("tod") == 950).to_pandas()
        out.append(t)
    f = pd.concat(out, ignore_index=True)
    f["date"] = pd.to_datetime(f["date"]).dt.date.astype(str)
    f["symbol"] = f["symbol"].astype(str)
    B.no_locked(f.date.unique())
    return f.drop(columns="tod")


def t1_job(args):
    sym, W = args
    if "f" not in CTX:
        CTX["f"] = pd.read_parquet(Path(W) / "ctx1.parquet")
    f = CTX["f"]
    f = f[f.symbol == sym].set_index("date")
    if not len(f):
        return [], None
    b = B.hist_bars(sym)
    b = b[b.index.date.astype(str) >= "2024-09-16"]
    op = b.groupby(b.index.date.astype(str))["open"].first()   # 09:30 open (RTH bars from 09:30)
    hh = b.index.hour * 100 + b.index.minute
    op = b[(hh >= 930)].groupby(b[(hh >= 930)].index.date.astype(str))["open"].first()
    d = pd.DataFrame({"prev_close": op.reindex(f.index) / (1 + f["gap"] / 100), "atr": f["atr_d"], "adv20": f["adv20"]})
    return day_rows(sym, b, d)


def t2_job(sym):
    b = pd.read_parquet(B.FRESH / "1Min" / f"{sym}.parquet")
    b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
    b = b.sort_index()
    hh = b.index.hour * 100 + b.index.minute
    b = b[(hh >= 930) & (hh < 1600)]
    ds = pd.Series(b.index.date.astype(str))
    assert ds.max() <= B.T2_HI and not ((ds >= B.LOCK[0]) & (ds <= B.LOCK[1])).any()
    g = b.groupby(b.index.date.astype(str))
    dd = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last(),
                       "dv": (b.close * b.volume).groupby(b.index.date.astype(str)).sum()})
    from mcf import features as F
    daily = pd.DataFrame({"prev_close": dd.close.shift(1), "atr": F.atr(dd).shift(1),
                          "adv20": dd.dv.shift(1).rolling(20, min_periods=5).mean()})
    daily = daily[(daily.index >= B.T2_LO) & (daily.index <= B.T2_HI)].dropna(subset=["prev_close", "atr"])
    return day_rows(sym, b, daily)


def build(W, test):
    W = Path(W)
    if test == "t1":
        if not (W / "ctx1.parquet").exists():
            t1_ctx().to_parquet(W / "ctx1.parquet")
        syms = sorted(p.stem for p in B.CACHE.glob("*.parquet"))
        jobs, fn = [(s, str(W)) for s in syms], t1_job
    else:
        syms = sorted(p.stem for p in (B.FRESH / "1Min").glob("*.parquet"))
        jobs, fn = syms, t2_job
    rows, cands = [], []
    with Pool(3) as p:
        for i, (r, c) in enumerate(p.imap_unordered(fn, jobs, chunksize=4)):
            rows.extend(r)
            if c is not None:
                cands.append(c)
            if i % 200 == 0:
                print(test, i, len(rows), flush=True)
    D = pd.DataFrame(rows, columns=["symbol", "date", "prev_close", "atr", "adv20", "v0949", "move950", "side", "gap"])
    D = D.sort_values(["symbol", "date"]).reset_index(drop=True)
    B.no_locked(D.date.unique())
    # rvol20 = 09:30-09:49 volume / mean of the prior 14 sessions (min 5), as engine.SymbolHistory/rank_contexts;
    # the rolling window never spans the locked gap (segments split at gaps > 10 calendar days)
    dt = pd.to_datetime(D.date)
    seg = ((D.symbol != D.symbol.shift()) | ((dt - dt.shift()).dt.days > 10)).cumsum()
    D["avg0949"] = D.groupby(seg).v0949.transform(lambda s: s.shift(1).rolling(14, min_periods=5).mean())
    D["rvol20"] = D.v0949 / D.avg0949.where(D.avg0949 > 0)
    u0 = (D.prev_close >= 5) & (D.adv20 >= 20e6) & D.rvol20.notna()
    D["rank_rvol20"] = np.nan
    D.loc[u0, "rank_rvol20"] = D[u0].groupby("date").rvol20.rank(ascending=False, method="first")
    D.to_parquet(W / f"days_{test}.parquet")
    C = pd.concat(cands, ignore_index=True)
    B.no_locked(C.date.unique())
    C.to_parquet(W / f"cand_{test}.parquet", compression="zstd")
    print(test, "days", len(D), "candidate days", C.groupby(["symbol", "date"]).ngroups, "rows", len(C))


# ------------------------------------------------------------------------------------------------ score
VARIANTS = {
    "base": {},
}


def load_variants():
    p = HERE / "variants.json"
    if p.exists():
        VARIANTS.update(json.loads(p.read_text()))


def run_trades(W, test, params, rank_max=50, seed=None):
    """seed=None: the setup's own trades. seed=int: random-entry control on the same symbol-days, sides, $ risk and
    target multiple as the setup's trades (entry bar uniform in the entry window), same exits."""
    D = pd.read_parquet(Path(W) / f"days_{test}.parquet")
    D = D[(D.side != 0) & (D.prev_close >= params.get("min_price", 10)) & (D.adv20 >= 20e6) & (D.atr > 0)
          & (D.rank_rvol20 <= rank_max)]
    if "min_abs_move" in params:
        D = D[D.move950.abs() >= params["min_abs_move"]]
    if "side_only" in params:
        D = D[D.side == params["side_only"]]
    D = D.set_index(["symbol", "date"])
    C = pd.read_parquet(Path(W) / f"cand_{test}.parquet")
    C = C.set_index(["symbol", "date"]).loc[lambda x: x.index.isin(D.index)].reset_index()
    p = dict(G.P, **{k: v for k, v in params.items() if k in G.P})
    rng = np.random.default_rng(seed) if seed is not None else None
    out = []
    for (sym, d), g in C.groupby(["symbol", "date"], sort=False):
        r = D.loc[(sym, d)]
        hh = g.hhmm.to_numpy(int)
        o, h, l, c, v = (g[k].to_numpy(float) for k in ("o", "h", "l", "c", "v"))
        sig = G.find_signal(o, h, l, c, v, hh, float(r.prev_close), float(r.atr), p)
        if sig is None:
            continue
        if rng is not None:
            win = np.flatnonzero((hh >= p["win_lo"]) & (hh <= p["win_hi"]))
            if not len(win):
                continue
            k = int(rng.choice(win))
            dist = abs(sig["ref"] - sig["stop"])
            sig = dict(k=k, side=sig["side"], ref=c[k], stop=c[k] - sig["side"] * dist,
                       tgt=c[k] + sig["side"] * sig["tgt_r"] * dist, tgt_r=sig["tgt_r"])
        w = G.walk(o, h, l, c, hh, sig, p)
        if w is None:
            continue
        j, fill, px, kind, xt = w
        out.append((sym, d, int(hh[j]), sig["side"], fill, sig["stop"], sig["tgt"], abs(fill - sig["stop"]),
                    float(r.gap), px, kind, xt, int(hh[sig["k"]]), sig["tgt_r"], float(r.move950),
                    float(r.rank_rvol20), abs(sig["ref"] - sig["stop"]) / float(r.atr)))
    T = pd.DataFrame(out, columns=["symbol", "date", "tod", "side", "entry", "stop", "tgt", "risk", "gap", "px", "kind",
                                   "xt", "sig_tod", "tgt_r", "move950", "rank", "stop_atr"])
    T["setup"] = "BEG-02"
    return T


def score_one(W, name, which, seed=None):
    load_variants()
    params = VARIANTS[name]
    etb = pd.read_parquet(ETB).rate
    spy1 = B.spy_t1()
    res = {}
    tests = {"fit": ["t1"], "check": ["t1"], "t2": ["t2"], "all": ["t1", "t2"], "t1": ["t1"]}[which]
    booked = {}
    for test in tests:
        T = run_trades(W, test, params, params.get("rank_max", 50), seed)
        if not len(T):
            continue
        T = B.add_r(T)
        bk = B.book(T, B.TESTING_RULES, etb)
        if test == "t1":
            last = "2026-11-04"
            days = pd.Series(spy1.index)
            days = days[days <= last]
            h = B.half(days)
            n = {"fit": int((h == "fit").sum()), "check": int((h == "check").sum())}
            bk["half"] = B.half(bk.date)
            parts = ["fit", "check"] if which in ("all", "t1") else [which]
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
    tag = name + (f"_rnd{seed}" if seed is not None else "") + "_" + which
    (Path(W) / f"res_{tag}.json").write_text(json.dumps(res, indent=1, default=float))
    if booked:
        pd.concat([v.assign(test=k) for k, v in booked.items()]).to_parquet(Path(W) / f"bk_{tag}.parquet")
    return res


if __name__ == "__main__":
    W = Path(sys.argv[1])
    W.mkdir(parents=True, exist_ok=True)
    st = sys.argv[2]
    if st == "build1":
        build(W, "t1")
    elif st == "build2":
        build(W, "t2")
    elif st == "score":
        seed = int(sys.argv[5]) if len(sys.argv) > 5 else None
        print(json.dumps(score_one(W, sys.argv[3], sys.argv[4], seed), indent=1, default=float))
