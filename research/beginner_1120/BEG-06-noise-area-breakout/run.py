"""BEG-06 backtest, the "normal way": bench10's costs (add_r: LR8 + borrow), testing-arena book (TESTING_RULES) and
stats() imported unchanged from research/ultimate_1119/top10/bench10.py; signals and exits on 1-minute bars.

  python run.py score VARIANT PART          PART in fit | check | t2
  python run.py rand VARIANT PART           200 random-side seeds (same entries, stop distance, exit time)
Outputs go to WORK (scratchpad); only small json lands in this folder. The locked block 2024-11-01..2025-02-28 is never
read (bench10.hist_bars pyarrow filter + no_locked asserts; frames' locked months skipped). The m_t profile follows the
live priors build (last 14 prior sessions within 24 calendar days, >= 5 needed), so sessions whose look-back would sit in
the locked block (early March 2025) have no profile and no trade. Educational only - not financial advice."""
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
import beg06 as G  # noqa: E402

FRAMES = Path("/home/user/MCF/research/history2y/data/frames")
ETB = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ult/research/ultimate_1119/top10/etb_rate.parquet")
WORK = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/beg06w")
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


def move_profiles(b):
    """{date: avg |close/open-1| by minute of session (390)} from PRIOR sessions only (live priors rule)."""
    hh = b.index.hour * 100 + b.index.minute
    mos = (b.index.hour * 60 + b.index.minute - 570).to_numpy()
    ds = b.index.date.astype(str)
    op = b.groupby(ds)["open"].transform("first").to_numpy()
    mv = pd.DataFrame({"date": ds, "mos": mos, "m": np.abs(b.close.to_numpy() / op - 1)})
    piv = mv.pivot_table(index="date", columns="mos", values="m", aggfunc="last").reindex(columns=range(390))
    dates = pd.to_datetime(piv.index)
    arr = piv.to_numpy()
    out = {}
    for i, d in enumerate(dates):
        lo = d - pd.Timedelta(days=24)
        idx = [q for q in range(max(0, i - 40), i) if dates[q] >= lo][-14:]
        if len(idx) < 5:
            out[piv.index[i]] = None
            continue
        m = pd.Series(np.nanmean(arr[idx], axis=0)).ffill().bfill().to_numpy()
        out[piv.index[i]] = m
    return out


def _rth(b):
    hh = b.index.hour * 100 + b.index.minute
    return b[(hh >= 930) & (hh < 1600)]


def sessions(test):
    """-> {(sym, date): (o,h,l,c,v,hhmm, prev_close, atr, move)}."""
    S = {}
    if test == "t1":
        f = t1_daily()
        for sym in G.SYMBOLS:
            b = _rth(B.hist_bars(sym))
            mp = move_profiles(b)
            fs = f[f.symbol == sym].set_index("date")
            for d, g in b.groupby(b.index.date.astype(str)):
                if d not in fs.index or d > T1_LAST:
                    continue
                pc = float(g.open.iloc[0] / (1 + fs.loc[d, "gap"] / 100))
                S[(sym, d)] = (*(g[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume")),
                               (g.index.hour * 100 + g.index.minute).to_numpy(), pc, float(fs.loc[d, "atr_d"]),
                               mp.get(d))
    else:
        from mcf import features as F
        for sym in G.SYMBOLS:
            b = pd.read_parquet(B.FRESH / "1Min" / f"{sym}.parquet")
            b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
            b = _rth(b.sort_index())
            ds = pd.Index(b.index.date.astype(str))
            assert ds.max() <= B.T2_HI and not ((ds >= B.LOCK[0]) & (ds <= B.LOCK[1])).any()
            mp = move_profiles(b)
            g0 = b.groupby(ds)
            dd = pd.DataFrame({"open": g0.open.first(), "high": g0.high.max(), "low": g0.low.min(),
                               "close": g0.close.last()})
            daily = pd.DataFrame({"pc": dd.close.shift(1), "atr": F.atr(dd).shift(1)})
            for d, g in b.groupby(ds):
                if d < B.T2_LO or d > B.T2_HI or not np.isfinite(daily.loc[d, "atr"]):
                    continue
                S[(sym, d)] = (*(g[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume")),
                               (g.index.hour * 100 + g.index.minute).to_numpy(), float(daily.loc[d, "pc"]),
                               float(daily.loc[d, "atr"]), mp.get(d))
    return S


_HALF: dict = {}


def _half(d):
    if d not in _HALF:
        _HALF[d] = B.half([d])[0]
    return _HALF[d]


def trades(S, params, part, seed=None):
    p = dict(G.P, **{k: v for k, v in params.items() if k in G.P})
    rng = np.random.default_rng(seed) if seed is not None else None
    out = []
    for (sym, d), (o, h, l, c, v, hh, pc, atr, mv) in S.items():
        if part in ("fit", "check") and _half(d) != part:
            continue
        gap = (o[0] / pc - 1) * 100
        for t in G.session_trades(o, h, l, c, v, hh, pc, atr, mv, p):
            side, j, x = t["side"], t["j"], t["x"]
            fill, stop, px, kind, xt = t["fill"], t["stop"], t["px"], t["kind"], t["xt"]
            if rng is not None:        # random side, same entry / stop distance / exit time
                side = int(rng.choice([-1, 1]))
                dist = abs(t["fill"] - t["stop"])
                stop = fill - side * dist
                px, kind, xt = o[x] if t["kind"] != G.KIND_STOP else o[min(x + 1, len(o) - 1)], 0, t["xt"]
                xend = x if t["kind"] != G.KIND_STOP else min(x + 1, len(o) - 1)
                for k in range(j, xend):
                    if (side == 1 and l[k] <= stop) or (side == -1 and h[k] >= stop):
                        px = min(o[k], stop) if side == 1 else max(o[k], stop)
                        kind, xt = 1, int(hh[k]) + 1
                        break
            out.append((sym, d, int(hh[j]), side, fill, stop, np.nan, abs(fill - stop), gap, px, kind, xt,
                        t["check"], t["m"] * 100, atr, (t["upper"] / t["lower"] - 1) * 100,
                        (fill / t["vw"] - 1) * 100))
    T = pd.DataFrame(out, columns=["symbol", "date", "tod", "side", "entry", "stop", "tgt", "risk", "gap", "px",
                                   "kind", "xt", "check", "m_pct", "atr", "band_w_pct", "vw_dist_pct"])
    T["setup"] = "BEG-06"
    return T


_NS: dict = {}


def n_sessions(part):
    if part not in _NS:
        if part == "t2":
            spy2 = pd.read_parquet(B.FRESH / "spy_days.parquet")
            spy2.index = spy2.index.astype(str)
            spy2 = spy2[(spy2.index >= B.T2_LO) & (spy2.index <= B.T2_HI)]["type"]
            _NS[part] = (len(spy2), spy2)
        else:
            spy1 = B.spy_t1()
            spy1 = spy1[spy1.index <= T1_LAST]
            _NS[part] = (int((B.half(spy1.index) == part).sum()), spy1)
    return _NS[part]


_S: dict = {}


def score(name, part, seed=None, save=True):
    test = "t2" if part == "t2" else "t1"
    if test not in _S:
        _S[test] = sessions(test)
    params = load_variants()[name]
    T = trades(_S[test], params, part, seed)
    if "etb" not in _S:
        _S["etb"] = pd.read_parquet(ETB).rate
    raw = B.add_r(T)
    bk = B.book(raw, B.TESTING_RULES, _S["etb"])
    n, spy = n_sessions(part)
    st = B.stats(bk, n, spy)
    st["raw_signals"] = int(len(T))
    st["removed_by_cost_filter"] = int((raw.stop_cost_r > 0.15).sum())
    st["raw_avg_r_no_filter"] = round(float(raw.r.mean()), 4) if len(raw) else None
    if len(bk):
        st["exit_mix"] = {str(k): [int(len(g)), round(float(g.r.mean()), 3)] for k, g in bk.groupby("kind")}
        st["by_side"] = {str(k): [int(len(g)), round(float(g.r.mean()), 3)] for k, g in bk.groupby("side")}
        st["by_symbol"] = {str(k): [int(len(g)), round(float(g.r.mean()), 3)] for k, g in bk.groupby("symbol")}
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
    vals = np.array([score(name, part, seed=s, save=False)[0].get("avg_r", np.nan) for s in range(n)], float)
    o = {"setup_avg_r": st0.get("avg_r"), "rand_mean_avg_r": round(float(np.nanmean(vals)), 4),
         "rand_p05": round(float(np.nanpercentile(vals, 5)), 4), "rand_p95": round(float(np.nanpercentile(vals, 95)), 4),
         "setup_percentile": round(float((vals < st0.get("avg_r", np.nan)).mean() * 100), 1), "seeds": n}
    res = json.loads((HERE / "results.json").read_text()) if (HERE / "results.json").exists() else {}
    res[f"{name}_{part}_random_side"] = o
    (HERE / "results.json").write_text(json.dumps(res, indent=1, default=float))
    return o


def comb(name):
    bk = pd.concat([pd.read_parquet(WORK / f"bk_{name}_{p}.parquet") for p in ("fit", "check")], ignore_index=True)
    spy = B.spy_t1()
    spy = spy[spy.index <= T1_LAST]
    n = int(pd.Series(B.half(spy.index)).isin(["fit", "check"]).sum())
    st = B.stats(bk, n, spy)
    res = json.loads((HERE / "results.json").read_text())
    res[f"{name}_t1comb"] = st
    (HERE / "results.json").write_text(json.dumps(res, indent=1, default=float))
    return st


if __name__ == "__main__":
    cmd, name = sys.argv[1], sys.argv[2]
    keys = ("trades", "sessions_traded", "trades_per_session", "win", "avg_r", "avg_r_gross", "avg_r_wo_best_day",
            "best_day", "best_day_share", "total_r_per_session", "worst_day", "t_day_clustered", "raw_signals",
            "removed_by_cost_filter", "exit_mix", "by_side", "by_symbol", "avg_r_spy_up", "avg_r_spy_flat",
            "avg_r_spy_down", "median_hold_min")
    if cmd == "score":
        st, _ = score(name, sys.argv[3])
        print(json.dumps({k: st.get(k) for k in keys}, default=float))
    elif cmd == "rand":
        print(json.dumps(rand(name, sys.argv[3])))
    elif cmd == "comb":
        st = comb(name)
        print(json.dumps({k: st.get(k) for k in keys}, default=float))
