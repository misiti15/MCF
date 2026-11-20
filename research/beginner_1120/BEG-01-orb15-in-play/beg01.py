"""BEG-01 backtest on the normal-way components (research/ultimate_1119/top10/bench10.py: add_r costs, book, stats).
Stop-entry setup, so signals come from the module's helpers on a per symbol-day table built from 1-minute bars, and
the walk follows mcf.backtest.engine stop-entry semantics + the bench rules (target traded through by >= 1c).
  python beg01.py WORK days1         T1 day table (data/cache_hist, locked block filtered out at read)
  python beg01.py WORK days2         T2 day table (data/cache_fresh, 2023-01-03..2024-09-13)
  python beg01.py WORK walk VARS T   walk variants (comma list from VARIANTS) on test T (t1 | t2)
  python beg01.py WORK score VARS T  book + stats (only the halves asked: fit | check | t2)
Educational only - not financial advice."""
from __future__ import annotations

import importlib.util
import json
import zlib
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "ultimate_1119" / "top10"))
import bench10 as B  # noqa: E402

_s = importlib.util.spec_from_file_location("beg01mod", HERE / "BEG-01.py")
M = importlib.util.module_from_spec(_s)
_s.loader.exec_module(M)

ETB = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ult/research/ultimate_1119/top10/"
           "etb_rate.parquet")
VARIANTS = {"base": {}, "stop25": {"stop_atr": 0.25, "rand": True}, "stopOR": {"stop_atr": 1e9, "rand": True},
            "until1015": {"order_until": 1015, "rand": True}}   # tweaks appended after the FIT diagnosis (PLAN.md), before they are scored
NRAND = 5


def rth(b):
    hm = b.index.hour * 100 + b.index.minute
    return b[(hm >= 930) & (hm < 1600)]


def day_stats(b):
    b = rth(b)
    hm = b.index.hour * 100 + b.index.minute
    day = b.index.date.astype(str)
    df = pd.DataFrame({"date": day, "hm": hm, "o": b.open.values, "h": b.high.values, "l": b.low.values,
                       "c": b.close.values, "v": b.volume.values})
    df["dv"] = df.c * df.v
    g = df.groupby("date")
    out = pd.DataFrame({"first_hm": g.hm.first(), "o930": g.o.first(), "dh": g.h.max(), "dl": g.l.min(), "dc": g.c.last(),
                        "dvol": g.dv.sum()})
    orr = df[df.hm <= M.OR_END].groupby("date")
    out["or_hi"], out["or_lo"], out["c944"] = orr.h.max(), orr.l.min(), orr.c.last()
    w = df[df.hm <= M.DECISION].groupby("date")
    out["vol20"], out["px949"], out["last_hm949"] = w.v.sum(), w.c.last(), w.hm.last()
    out = out.reset_index()
    # RVOL20: 14 prior sessions, none older than 30 calendar days, >= 5 needed
    dts = pd.to_datetime(out.date).values
    v = out.vol20.to_numpy(float)
    rv = np.full(len(out), np.nan)
    for i in range(len(out)):
        lo = np.searchsorted(dts, dts[i] - np.timedelta64(30, "D"))
        j0 = max(lo, i - 14)
        if i - j0 >= 5:
            m = v[j0:i].mean()
            rv[i] = v[i] / m if m > 0 else np.nan
    out["rvol"] = rv
    return out


def hist_bars(sym):
    return B.hist_bars(sym)


def fresh_bars(sym):
    b = pd.read_parquet(B.FRESH / "1Min" / f"{sym}.parquet")
    b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
    b = b.sort_index()
    ds = pd.Series(b.index.date.astype(str))
    assert not ((ds >= B.LOCK[0]) & (ds <= B.LOCK[1])).any()
    return b


def days1_job(sym):
    try:
        d = day_stats(hist_bars(sym))
    except Exception as e:  # noqa: BLE001
        return sym, None, str(e)
    d.insert(0, "symbol", sym)
    return sym, d, None


def days2_job(sym):
    b = fresh_bars(sym)
    d = day_stats(b)
    # ATR14 (mean TR, min 10, through the prior close) and ADV20 (prior 20, min 5): heat.py / build_frames formulas
    pc = d.dc.shift(1)
    tr = pd.concat([d.dh - d.dl, (d.dh - pc).abs(), (d.dl - pc).abs()], axis=1).max(axis=1)
    d["atr"] = tr.rolling(14, min_periods=10).mean().shift(1)
    d["adv20"] = d.dvol.shift(1).rolling(20, min_periods=5).mean()
    d["gap"] = (d.o930 / pc - 1) * 100
    d.insert(0, "symbol", sym)
    d = d[(d.date >= B.T2_LO) & (d.date <= B.T2_HI)]
    return sym, d, None


def days1(W):
    import research.history2y.lib as lib
    lib.DATA = B.DATA
    syms = sorted(p.stem for p in B.CACHE.glob("*.parquet"))
    out = []
    with Pool(3) as p:
        for s, d, e in p.imap_unordered(days1_job, syms, chunksize=4):
            if d is not None:
                out.append(d)
    D = pd.concat(out, ignore_index=True)
    D = D[D.date >= "2024-10-01"]
    B.no_locked(D.date.unique())
    fr = []
    for m in lib.months():
        f = lib.load_month(m, columns=["symbol", "date", "tod", "atr_d", "adv20", "gap"])
        f = f[f.tod == 950]
        fr.append(pd.DataFrame({"symbol": f.symbol.astype(str), "date": f.date.astype(str), "atr": f.atr_d,
                                "adv20": f.adv20, "gap": f.gap}))
    F = pd.concat(fr, ignore_index=True)
    B.no_locked(F.date.unique())
    D = D.merge(F, on=["symbol", "date"], how="inner")
    D.to_parquet(Path(W) / "days_t1.parquet")
    print(len(D), "T1 symbol-days", D.symbol.nunique(), "symbols")


def days2(W):
    syms = sorted(p.stem for p in (B.FRESH / "1Min").glob("*.parquet"))
    with Pool(3) as p:
        out = [d for _, d, _ in p.imap_unordered(days2_job, syms, chunksize=4) if d is not None and len(d)]
    D = pd.concat(out, ignore_index=True)
    D.to_parquet(Path(W) / "days_t2.parquet")
    print(len(D), "T2 symbol-days", D.symbol.nunique(), "symbols")


def candidates(D, p):
    D = D[(D.first_hm == 930) & (D.last_hm949 == M.DECISION)].copy()
    u0 = (D.px949 >= M.PX_U0) & (D.adv20 >= M.ADV_U0) & D.rvol.notna()
    D["rank"] = np.nan
    D.loc[u0, "rank"] = D[u0].groupby("date").rvol.rank(ascending=False, method="first")
    ok = M.eligible_stats(D.px949, D.adv20, D.rvol, D["rank"].fillna(1e9), D.atr, p)
    C = D[ok].copy()
    side, trig, stop, tgt = M.plan_from_stats(C.o930, C.c944, C.or_hi, C.or_lo, C.atr, p)
    C["side"], C["trig"], C["stop"], C["tgt"] = side, trig, stop, tgt
    C = C[(C.side != 0) & ~((C.side < 0) & C.symbol.isin(M.NO_SHORT))]
    return C.reset_index(drop=True)


def walk_day(O, H, L, C, hm, side, trig, stop, tgt, be_r, start, until, market_hm=None, risk_usd=None):
    """engine.simulate stop-entry semantics + bench target rule. Returns dict."""
    n = len(hm)
    j = None
    if market_hm is not None:
        ks = np.flatnonzero(hm >= market_hm)
        if not len(ks) or hm[ks[0]] >= until:
            return None
        j = int(ks[0])
        fill = O[j]
        stop = fill - side * risk_usd
        tgt = fill + side * 2.0 * risk_usd if tgt is not None else None
    else:
        for k in range(n):
            if hm[k] < start:
                continue
            if hm[k] >= until:
                break
            if side == 1 and H[k] >= trig:
                j, fill = k, max(O[k], trig)
                break
            if side == -1 and L[k] <= trig:
                j, fill = k, min(O[k], trig)
                break
        if j is None:
            return {"kind": -1}
    if tgt is not None and side * (tgt - fill) <= 0:
        return {"kind": -2, "fill": fill, "ehm": int(hm[j])}
    risk = side * (fill - stop)
    if risk <= 0:
        return {"kind": -3}
    st, mfe, mae, be_on = stop, 0.0, 0.0, False
    px = kd = xt = None
    for k in range(j, n):
        if hm[k] >= M.EXIT_BY:
            px, kd, xt = O[k], 0, M.EXIT_BY
            break
        adv = L[k] if side == 1 else H[k]
        mae = min(mae, side * (adv - fill) / risk)
        if (side == 1 and L[k] <= st) or (side == -1 and H[k] >= st):
            gt = (O[k] < st) if side == 1 else (O[k] > st)
            px = (O[k] if (gt and k > j) else st)
            kd, xt = 1, int(hm[k]) + 1
            break
        fav = H[k] if side == 1 else L[k]
        mfe = max(mfe, side * (fav - fill) / risk)
        if tgt is not None and ((side == 1 and H[k] >= tgt + 0.01) or (side == -1 and L[k] <= tgt - 0.01)):
            px, kd, xt = tgt, 2, int(hm[k]) + 1
            break
        if be_r is not None and mfe >= be_r:
            st = max(st, fill) if side == 1 else min(st, fill)
            be_on = True
    if px is None:
        px, kd, xt = C[n - 1], 0, int(hm[n - 1]) + 1
    # diagnostics: after a stop, did price later reach the target (before 15:55)?
    later_tgt = False
    if kd == 1 and tgt is not None:
        rest = np.flatnonzero((np.arange(n) > k) & (hm < M.EXIT_BY))
        if len(rest):
            later_tgt = bool((H[rest].max() >= tgt + 0.01) if side == 1 else (L[rest].min() <= tgt - 0.01))
    return {"kind": kd, "fill": fill, "px": px, "ehm": int(hm[j]), "xt": xt, "risk": risk, "stop_used": stop,
            "mfe": mfe, "mae": mae, "be": be_on, "later_tgt": later_tgt, "chase": bool(side * (fill - trig) > 0)
            if market_hm is None else False}


def walk_job(args):
    sym, T, src = args
    b = rth(hist_bars(sym) if src == "t1" else fresh_bars(sym))
    hm_all = b.index.hour * 100 + b.index.minute
    day = b.index.date.astype(str)
    idx = {d: np.flatnonzero(day == d) for d in np.unique(day)}
    O, H, L, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    rows = []
    for r in T.itertuples():
        ix = idx.get(r.date)
        if ix is None:
            continue
        a = (O[ix], H[ix], L[ix], C[ix], hm_all[ix])
        res = walk_day(*a, r.side, r.trig, r.stop, r.tgt, r.be_r, r.start, r.until)
        rows.append({"var": r.var, "symbol": sym, "date": r.date, "side": r.side, "trig": r.trig, "rand": -1, **res})
        if r.var == "base" or r.rand:
            rng = np.random.default_rng(zlib.crc32(f"{sym}|{r.date}|{r.var}".encode()))
            mins = np.arange(r.start, r.until)
            mins = mins[(mins % 100) < 60]
            for s in range(NRAND):
                mh = int(rng.choice(mins))
                rr = walk_day(*a, r.side, r.trig, r.stop, r.tgt, r.be_r, r.start, r.until, market_hm=mh,
                              risk_usd=abs(r.trig - r.stop))
                if rr is not None:
                    rows.append({"var": r.var, "symbol": sym, "date": r.date, "side": r.side, "trig": r.trig, "rand": s, **rr})
    return rows


def walk(W, vars_, src):
    D = pd.read_parquet(Path(W) / f"days_{src}.parquet")
    allc = []
    for v in vars_:
        p = VARIANTS[v]
        c = candidates(D, p)
        c["var"], c["be_r"] = v, p.get("be_r", M.BE_R)
        c["start"], c["until"] = p.get("order_from", M.ORDER_FROM), p.get("order_until", M.ORDER_UNTIL)
        c["rand"] = p.get("rand", False)
        allc.append(c)
    C = pd.concat(allc, ignore_index=True)
    if src == "t1":
        hh = B.half(C.date)
        C = C[hh != "none"]
    keepc = C.drop(columns=["rand"]).copy()
    jobs = [(s, g, src) for s, g in C.groupby("symbol")]
    with Pool(3) as p:
        out = [x for r in p.imap_unordered(walk_job, jobs, chunksize=2) for x in r]
    R = pd.DataFrame(out)
    R = R.merge(keepc[["var", "symbol", "date", "gap", "atr", "rvol", "rank", "px949", "or_hi", "or_lo", "stop", "tgt"]],
                on=["var", "symbol", "date"], how="left")
    R.to_parquet(Path(W) / f"walk_{src}_{'_'.join(vars_)}.parquet")
    print(src, vars_, len(C), "candidates;", R[R.rand < 0].kind.value_counts().to_dict())


def to_trades(R):
    t = R[R.kind >= 0].copy()
    t = pd.DataFrame({"var": t["var"], "symbol": t.symbol, "date": t.date, "side": t.side, "entry": t.fill,
                      "stop": t.stop_used, "tgt": t.tgt, "risk": t.risk, "gap": t.gap.fillna(0), "px": t.px,
                      "kind": t.kind, "tod": t.ehm + 1, "xt": t.xt, "rand": t.rand, "mfe": t.mfe, "mae": t.mae,
                      "be": t.be, "later_tgt": t.later_tgt, "chase": t.chase, "rvol": t.rvol, "rank": t["rank"],
                      "atr": t.atr, "ehm": t.ehm})
    return B.add_r(t)


def load_ctx():
    etb = pd.read_parquet(ETB).rate
    spy1 = B.spy_t1()
    spy2 = pd.read_parquet(B.FRESH / "spy_days.parquet")
    spy2.index = spy2.index.astype(str)
    spy2 = spy2[(spy2.index >= B.T2_LO) & (spy2.index <= B.T2_HI)]["type"]
    t1d = pd.Series(spy1.index)
    t1d = t1d[t1d <= "2026-11-04"]
    h = B.half(t1d)
    nses = {"fit": int((h == "fit").sum()), "check": int((h == "check").sum()), "t2": int(len(spy2))}
    return etb, spy1, spy2, nses


def score(W, vars_, src, halves, save_tag=None):
    etb, spy1, spy2, nses = load_ctx()
    R = pd.read_parquet(Path(W) / f"walk_{src}_{'_'.join(vars_)}.parquet")
    T = to_trades(R)
    out = {}
    for v in vars_:
        for h in halves:
            res = {}
            for kind, sub in (("setup", T[(T["var"] == v) & (T.rand < 0)]), ("random", T[(T["var"] == v) & (T.rand >= 0)])):
                if src == "t1":
                    sub = sub[B.half(sub.date) == h]
                ns, spy = (nses[h], spy1) if src == "t1" else (nses["t2"], spy2)
                if kind == "setup":
                    bk = B.book(sub, B.TESTING_RULES, etb)
                    res["book"] = B.stats(bk, ns, spy)
                    nocf = dict(B.TESTING_RULES, cf=None)
                    res["book_no_cost_filter"] = B.stats(B.book(sub, nocf, etb), ns, spy)
                    res["raw_fills"] = int(len(sub))
                    if save_tag:
                        bk.assign(var=v, half=h).to_parquet(Path(W) / f"booked_{save_tag}_{v}_{h}.parquet")
                else:
                    seeds = []
                    for s in range(NRAND):
                        bk = B.book(sub[sub.rand == s], B.TESTING_RULES, etb)
                        seeds.append((len(bk), float(bk.r.mean()) if len(bk) else np.nan))
                    res["random"] = {"trades_mean": float(np.mean([a for a, _ in seeds])),
                                     "avg_r_mean": round(float(np.nanmean([b for _, b in seeds])), 4),
                                     "avg_r_by_seed": [round(b, 4) for _, b in seeds]}
            n_c = R[(R["var"] == v) & (R.rand < 0)]
            if src == "t1":
                n_c = n_c[B.half(n_c.date) == h]
            res["candidates"] = int(len(n_c))
            res["outcomes"] = {str(k): int(x) for k, x in n_c.kind.value_counts().items()}
            out[f"{v}|{h}"] = res
            b = res["book"]
            print(f"{v:10s} {h:6s} n={b.get('trades')} avgR={b.get('avg_r')} wo={b.get('avg_r_wo_best_day')} "
                  f"share={b.get('best_day_share')} R/s={b.get('total_r_per_session')} t={b.get('t_day_clustered')} "
                  f"win={b.get('win')} | noCF n={res['book_no_cost_filter'].get('trades')} "
                  f"avgR={res['book_no_cost_filter'].get('avg_r')} | rand={res['random']['avg_r_mean']} "
                  f"(n~{res['random']['trades_mean']:.0f}) cand={res['candidates']} {res['outcomes']}")
    return out


if __name__ == "__main__":
    W = Path(sys.argv[1])
    W.mkdir(parents=True, exist_ok=True)
    st = sys.argv[2]
    if st == "days1":
        days1(W)
    elif st == "days2":
        days2(W)
    elif st == "walk":
        walk(W, sys.argv[3].split(","), sys.argv[4])
    elif st == "score":
        vs, src = sys.argv[3].split(","), sys.argv[4]
        halves = sys.argv[5].split(",")
        o = score(W, vs, src, halves, save_tag=src)
        tag = sys.argv[6] if len(sys.argv) > 6 else "_".join(vs)
        (W / f"score_{src}_{tag}_{'_'.join(halves)}.json").write_text(json.dumps(o, indent=1, default=float))
