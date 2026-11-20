"""BEG-05 backtest, the "normal way": bench10's costs (add_r: LR8 + borrow), testing-arena book (TESTING_RULES) and
stats() imported unchanged from research/ultimate_1119/top10/bench10.py; signals and exits on 1-minute bars.

  python run.py score VARIANT PART [SEED]     PART in fit | check | t2 ; SEED = random-side control seed
  python run.py rand VARIANT PART             200 random-side seeds -> mean / setup percentile
Outputs go to WORK (scratchpad); only small json lands in this folder. Locked block 2024-11-01..2025-02-28 is never read
(bench10.hist_bars pyarrow filter + no_locked asserts; frames' locked months skipped). Educational only - not financial
advice."""
from __future__ import annotations

import json
import sys
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
import beg05 as G  # noqa: E402

FRAMES = Path("/home/user/MCF/research/history2y/data/frames")
ETB = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ult/research/ultimate_1119/top10/etb_rate.parquet")
WORK = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/beg05w")
T1_LAST = "2026-11-04"


def load_variants():
    v = {"base": {}}
    p = HERE / "variants.json"
    if p.exists():
        v.update(json.loads(p.read_text()))
    return v


def t1_daily():
    out = []
    for p in sorted(FRAMES.glob("month=*")):
        if p.name.split("=")[1] in B.LOCKED_MONTHS:
            continue
        out.append(pads.dataset(str(p), format="parquet").to_table(
            columns=["symbol", "date", "tod", "gap", "atr_d"],
            filter=(pads.field("tod") == 950) & pads.field("symbol").isin(list(G.SYMBOLS))).to_pandas())
    f = pd.concat(out, ignore_index=True)
    f["date"] = pd.to_datetime(f["date"]).dt.date.astype(str)
    f["symbol"] = f["symbol"].astype(str)
    B.no_locked(f.date.unique())
    return f


def sessions(test):
    """-> {(sym, date): (o,h,l,c,v,hhmm, prev_close, atr)} for the test's sessions."""
    S = {}
    if test == "t1":
        f = t1_daily()
        for sym in G.SYMBOLS:
            b = B.hist_bars(sym)
            hh = b.index.hour * 100 + b.index.minute
            b = b[(hh >= 930) & (hh < 1600)]
            fs = f[f.symbol == sym].set_index("date")
            for d, g in b.groupby(b.index.date.astype(str)):
                if d not in fs.index or d > T1_LAST:
                    continue
                pc = float(g.open.iloc[0] / (1 + fs.loc[d, "gap"] / 100))
                S[(sym, d)] = (*(g[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume")),
                               (g.index.hour * 100 + g.index.minute).to_numpy(), pc, float(fs.loc[d, "atr_d"]))
    else:
        from mcf import features as F
        for sym in G.SYMBOLS:
            b = pd.read_parquet(B.FRESH / "1Min" / f"{sym}.parquet")
            b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
            b = b.sort_index()
            hh = b.index.hour * 100 + b.index.minute
            b = b[(hh >= 930) & (hh < 1600)]
            ds = pd.Index(b.index.date.astype(str))
            assert ds.max() <= B.T2_HI and not ((ds >= B.LOCK[0]) & (ds <= B.LOCK[1])).any()
            g0 = b.groupby(ds)
            dd = pd.DataFrame({"open": g0.open.first(), "high": g0.high.max(), "low": g0.low.min(),
                               "close": g0.close.last()})
            daily = pd.DataFrame({"pc": dd.close.shift(1), "atr": F.atr(dd).shift(1)})
            for d, g in b.groupby(ds):
                if d < B.T2_LO or d > B.T2_HI or not np.isfinite(daily.loc[d, "atr"]):
                    continue
                S[(sym, d)] = (*(g[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume")),
                               (g.index.hour * 100 + g.index.minute).to_numpy(), float(daily.loc[d, "pc"]),
                               float(daily.loc[d, "atr"]))
    return S


def trades(S, params, part, seed=None):
    p = dict(G.P, **{k: v for k, v in params.items() if k in G.P})
    rng = np.random.default_rng(seed) if seed is not None else None
    out = []
    for (sym, d), (o, h, l, c, v, hh, pc, atr) in S.items():
        if part in ("fit", "check") and _half(d) != part:
            continue
        sig = G.find_signal(o, h, l, c, v, hh, pc, atr, p)
        if sig is None:
            continue
        if rng is not None:
            sig = dict(sig, side=int(rng.choice([-1, 1])))
        w = G.walk(o, h, l, c, hh, sig, p)
        if w is None:
            continue
        j, fill, stop, px, kind, xt = w
        gap = (o[0] / pc - 1) * 100
        r2 = (c[sig["k"]] / c[np.flatnonzero(hh == p["r1_hhmm"])[0]] - 1) * 100
        out.append((sym, d, int(hh[j]), sig["side"], fill, stop, np.nan, abs(fill - stop), gap, px, kind, xt,
                    sig["r1"], r2, atr, sig["dist"] / atr))
    T = pd.DataFrame(out, columns=["symbol", "date", "tod", "side", "entry", "stop", "tgt", "risk", "gap", "px",
                                   "kind", "xt", "r1", "r2", "atr", "stop_atr"])
    T["setup"] = "BEG-05"
    return T


_HALF: dict = {}


def _half(d):
    if d not in _HALF:
        _HALF[d] = B.half([d])[0]
    return _HALF[d]


_NS: dict = {}


def n_sessions(part):
    if part not in _NS:
        _NS[part] = _n_sessions(part)
    return _NS[part]


def _n_sessions(part):
    if part == "t2":
        spy2 = pd.read_parquet(B.FRESH / "spy_days.parquet")
        spy2.index = spy2.index.astype(str)
        spy2 = spy2[(spy2.index >= B.T2_LO) & (spy2.index <= B.T2_HI)]["type"]
        return len(spy2), spy2
    spy1 = B.spy_t1()
    spy1 = spy1[spy1.index <= T1_LAST]
    return int((B.half(spy1.index) == part).sum()), spy1


_S: dict = {}


def score(name, part, seed=None, save=True):
    test = "t2" if part == "t2" else "t1"
    if test not in _S:
        _S[test] = sessions(test)
    params = load_variants()[name]
    T = trades(_S[test], params, part, seed)
    if "etb" not in _S:
        _S["etb"] = pd.read_parquet(ETB).rate
    etb = _S["etb"]
    raw = B.add_r(T)
    bk = B.book(raw, B.TESTING_RULES, etb)
    n, spy = n_sessions(part)
    st = B.stats(bk, n, spy)
    st["raw_signals"] = int(len(T))
    st["removed_by_cost_filter"] = int(len(raw) - len(raw[raw.stop_cost_r <= 0.15]))
    st["raw_avg_r_no_filter"] = round(float(raw.r.mean()), 4) if len(raw) else None
    st["stop_rate"] = round(float((bk.kind == 1).mean()), 3) if len(bk) else None
    if save:
        WORK.mkdir(parents=True, exist_ok=True)
        tag = f"{name}_{part}" + (f"_rnd{seed}" if seed is not None else "")
        raw.to_parquet(WORK / f"raw_{tag}.parquet")
        bk.to_parquet(WORK / f"bk_{tag}.parquet")
        res = json.loads((HERE / "results.json").read_text()) if (HERE / "results.json").exists() else {}
        res[tag] = st
        (HERE / "results.json").write_text(json.dumps(res, indent=1, default=float))
    return st, bk


def rand(name, part, n=200):
    st0, _ = score(name, part, save=False)
    vals = []
    for s in range(n):
        st, _ = score(name, part, seed=s, save=False)
        vals.append(st.get("avg_r", np.nan))
    vals = np.array(vals, float)
    o = {"setup_avg_r": st0.get("avg_r"), "rand_mean_avg_r": round(float(np.nanmean(vals)), 4),
         "rand_p05": round(float(np.nanpercentile(vals, 5)), 4), "rand_p95": round(float(np.nanpercentile(vals, 95)), 4),
         "setup_percentile": round(float((vals < st0.get("avg_r", np.nan)).mean() * 100), 1), "seeds": n}
    res = json.loads((HERE / "results.json").read_text()) if (HERE / "results.json").exists() else {}
    res[f"{name}_{part}_random_side"] = o
    (HERE / "results.json").write_text(json.dumps(res, indent=1, default=float))
    return o


if __name__ == "__main__":
    cmd, name, part = sys.argv[1], sys.argv[2], sys.argv[3]
    if cmd == "score":
        st, _ = score(name, part, int(sys.argv[4]) if len(sys.argv) > 4 else None)
        print(json.dumps(st, indent=1, default=float))
    elif cmd == "rand":
        print(json.dumps(rand(name, part), indent=1))
