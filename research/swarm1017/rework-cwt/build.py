"""Build the rework-cwt event table per OPEN month (PLAN.md). Educational only - not financial advice.

    python build.py <scratch_dir> [month ...]      -> <scratch>/ev_<month>.parquet, <scratch>/atr_<month>.npy

Per month: lab frame rows (adv20 >= $1M, atr_d > 0; lib.load_month refuses the locked block, MCF_HIST_ALLOW_LOCKED is
never set) + the 09:35-09:45 / 15:05-15:55 rows of research/bdi/cwt/test_b/data/headtail.parquet (live-like frame as
research/bdi/cwt/live/verify.py; tail rows only feed the exit simulator). Kernels from kern.py on
cwt_live_lib.arrays(). Output: one row per 09:50-15:00 frame row carrying any family event, with decision-time
features, context (SPY fromOpen, SPY gap, breadth), outcomes (2 sides x 7 exits, production costs; S for A7 shorts)
and the same-minute random baselines ($95M population and all rows).
"""
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research" / "history2y"), str(ROOT / "research" / "bdi" / "cwt" / "live"), str(HERE)]
import lib  # noqa: E402
import cwt_live_lib as L  # noqa: E402
from mcf.research.gates import prod_r  # noqa: E402
from kern import b1k, b4ak, b4bk, b5k  # noqa: E402
from sim import sim  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
HT = ROOT / "research" / "bdi" / "cwt" / "test_b" / "data" / "headtail.parquet"
EARN = ROOT / "research" / "bdi" / "earnings" / "data" / "earnings_yf.parquet"
HOLIDAYS = ["2024-09-02", "2024-11-28", "2024-12-25", "2025-01-01", "2025-01-09", "2025-01-20", "2025-02-17",
            "2025-04-18", "2025-05-26", "2025-06-19", "2025-07-04", "2025-09-01", "2025-11-27", "2025-12-25",
            "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25", "2026-06-19", "2026-07-03",
            "2026-09-07", "2026-11-26", "2026-12-25"]
FEAT = ["close", "high", "low", "vwapDistPct", "gap", "fromOpen", "atr_d", "dist_pdh_atr", "dist_pdl_atr",
        "volumeRatio", "vol_climax", "adv20", "atrPct", "sma20_slope_pct", "rsi", "sma50_dist_pct"]
FG = ("t1s1", "t05s1", "t1s05")
SIMX = {"t05s05": (0.5, 0.5, 0, 0, 0.5, 0, 0, 0, 0), "so1": (1.0, 1.0, 0, 0.5, 0.5, 0, 0, 0, 0),
        "so05": (0.5, 1.0, 0, 0.25, 0.5, 0, 0, 0, 0), "tr1": (1.0, 1.0, 0, 0, 0.5, 0.5, 0.5, 0, 0)}
PARITY = {"t1s1": (1.0, 1.0, 0, 0, 0.5, 0, 0, 0, 0), "t05s1": (0.5, 1.0, 0, 0, 0.5, 0, 0, 0, 0),
          "t1s05": (1.0, 0.5, 0, 0, 0.5, 0, 0, 0, 0)}
EXITS = list(FG) + list(SIMX)
B1V = [(a, dt, tg) for a in (1.0, 1.5, 2.0, 2.5, 3.0) for dt in (0.3, 0.4, 0.5) for tg in (1, 2)]
NCO = (2, 3, 4, 6, 8)
B5V = [(m, v) for m in (0.5, 0.75, 1.0, 1.25) for v in (2, 3, 5, 8)]


def earn_black(sym_dates: pd.DataFrame) -> np.ndarray:
    er = pd.read_parquet(EARN, columns=["symbol", "date"])
    er["date"] = pd.to_datetime(er["date"]).dt.date
    g = er.groupby("symbol")["date"].apply(lambda s: np.array(sorted(set(s)), dtype="datetime64[D]")).to_dict()
    sd = sym_dates.reset_index(drop=True)
    u = sd.drop_duplicates()
    res = {}
    for s, d in zip(u["symbol"], u["date"]):
        rep = g.get(s)
        if rep is None:
            res[(s, d)] = False
            continue
        n = np.abs(np.busday_count(np.datetime64(d, "D"), rep, holidays=HOLIDAYS))
        res[(s, d)] = bool((n <= 4).any())
    return np.array([res[k] for k in zip(sd["symbol"], sd["date"])], bool)


def month_frame(m):
    cols = ["symbol", "date", "tod"] + FEAT + [f"{k}_{s}_{g}" for s in ("long", "short") for g in FG for k in ("r", "win")]
    f = lib.load_month(m, cols)
    spy = f.loc[f.symbol == "SPY", ["date", "tod", "fromOpen", "gap"]].rename(columns={"fromOpen": "spy_fo", "gap": "spy_gap"})
    f = f[(f["adv20"].to_numpy(float) >= 1e6) & (f["atr_d"].to_numpy(float) > 0)].reset_index(drop=True)
    f["symbol"] = f["symbol"].astype(str)
    f["_fi"] = np.arange(len(f))
    a = pd.Timestamp(m + "-01")
    ht = pd.read_parquet(HT, filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1))])
    ht["symbol"] = ht["symbol"].astype(str)
    ht["date"] = pd.to_datetime(ht["date"]).dt.date
    ht = ht[(ht.tod < 950) | (ht.tod > 1500)]
    ht = ht.merge(f[["symbol", "date"]].drop_duplicates(), on=["symbol", "date"], how="inner")
    h = pd.DataFrame({"symbol": ht["symbol"], "date": ht["date"], "tod": ht["tod"].astype(f["tod"].dtype),
                      "close": ht["c"].astype(float), "high": ht["h"].astype(float), "low": ht["l"].astype(float),
                      "vwapDistPct": (ht["c"].astype(float) / ht["vwap"].astype(float) - 1) * 100, "_fi": -1})
    P = pd.concat([f[["symbol", "date", "tod", "close", "high", "low", "vwapDistPct", "gap", "fromOpen", "atr_d",
                      "dist_pdh_atr", "dist_pdl_atr", "volumeRatio", "vol_climax", "_fi"]], h], ignore_index=True)
    P = P.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    return f, P, spy


def kernels(P):
    """All family event arrays on P (index = P rows)."""
    x = L.arrays(P)
    E = {}
    bits = np.zeros(x.n, np.int64)
    for bi, (a, dt, tg) in enumerate(B1V):
        bits |= b1k(x.new, x.c, x.h, x.l, x.vwap, x.open_d, x.atr, a, dt, tg).astype(np.int64) << bi
    E["b1bits"] = bits
    with np.errstate(invalid="ignore", divide="ignore"):
        rng = (x.hod - x.lod) / x.atr
        exs = ((x.hod - x.c) / x.atr <= 0.05) & (rng >= 0.4)
        exl = ((x.c - x.lod) / x.atr <= 0.05) & (rng >= 0.4)
        zs = np.where(exs, (x.c - x.vwap) / x.atr, np.nan)
        zl = np.where(exl, (x.vwap - x.c) / x.atr, np.nan)
        E["b2zs"] = np.where(x.h < L.prev(x, x.h), L.prev(x, zs), np.nan)
        E["b2zl"] = np.where(x.l > L.prev(x, x.l), L.prev(x, zl), np.nan)
    for k in NCO:
        E[f"b4a{k}"] = b4ak(x.new, x.c, x.h, x.l, x.hod, x.atr, k)
    E["b4bpush"], E["b4bd"] = b4bk(x.new, x.c, x.h, x.l, x.vwap, x.open_d, x.atr)
    c6 = L.prev(x, x.c, 6)
    lodp = np.nan_to_num(L.prev(x, x.lod, 1), nan=-1e18)
    vc = np.nan_to_num(x.vc, nan=0.0)
    vc3 = np.fmax(np.fmax(vc, np.nan_to_num(L.prev(x, vc, 1))), np.nan_to_num(L.prev(x, vc, 2)))
    bits = np.zeros(x.n, np.int64)
    for bi, (m, v) in enumerate(B5V):
        bits |= b5k(x.new, x.c, x.h, c6, lodp, vc3, x.atr, m, float(v)).astype(np.int64) << bi
    E["b5bits"] = bits
    # A7 (gap applied later): trig masks + structural stop (09:30-10:30 high)
    tod = x.tod
    with np.errstate(invalid="ignore"):
        above = (x.h > x.vwap) & (tod <= 1030)
        cond = pd.Series(above).groupby(x.seg).cummax().to_numpy(bool)
        E["a7t1"] = cond & (tod >= 1030) & (x.c < x.vwap)
        or30h = pd.Series(np.where(tod <= 1000, x.h, np.nan)).groupby(x.seg).transform("max").to_numpy(float)
        reach = (x.h >= x.vwap) | ((tod >= 1005) & (x.h >= or30h))
        lowerhalf = (x.c - x.l) < 0.5 * (x.h - x.l)
        E["a7t2"] = (cond | (x.h > x.vwap)) & reach & lowerhalf
        E["a7stop"] = pd.Series(np.where(tod <= 1030, x.h, np.nan)).groupby(x.seg).transform("max").to_numpy(float)
    return x, E


def month_job(args):
    m, OUT = args
    t0 = time.time()
    f, P, spy = month_frame(m)
    x, E = kernels(P)
    new = x.new
    seg = x.seg
    last = np.r_[np.flatnonzero(new)[1:] - 1, len(P) - 1]
    dend = last[seg].astype(np.int64)
    fi = P["_fi"].to_numpy()
    f2P = np.full(len(f), -1, np.int64)
    f2P[fi[fi >= 0]] = np.flatnonzero(fi >= 0)
    hh, ll, cc = P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float)
    ptod = P["tod"].to_numpy(np.int64)
    # outcomes for every frame row
    O = {}
    Rv = 0.25 * f["atr_d"].to_numpy(float)
    for s in ("long", "short"):
        for g in FG:
            O[f"{s}_{g}"] = prod_r(f[f"r_{s}_{g}"].to_numpy(float), f[f"win_{s}_{g}"].to_numpy(float),
                                   f["close"].to_numpy(float), f["atr_d"].to_numpy(float), g,
                                   tod=f["tod"].to_numpy(float)).astype(np.float32)
        sd = 1 if s == "long" else -1
        for xx, prm in SIMX.items():
            O[f"{s}_{xx}"] = sim(hh, ll, cc, ptod, dend, f2P, Rv, sd, *map(float, prm[:7]), int(prm[7]), float(prm[8]))
    par = {}
    if m in ("2025-06", "2026-03"):
        for s in ("long", "short"):
            sd = 1 if s == "long" else -1
            for g, prm in PARITY.items():
                rs = sim(hh, ll, cc, ptod, dend, f2P, Rv, sd, *map(float, prm[:7]), int(prm[7]), float(prm[8]))
                ref = O[f"{s}_{g}"]
                ok = np.isfinite(ref) & np.isfinite(rs)
                par[f"{s}_{g}"] = [int(ok.sum()), float(np.mean(np.abs(rs[ok] - ref[ok]) < 0.02)),
                                   float(rs[ok].mean()), float(ref[ok].mean())]
    # map events to frame rows
    ev = {k: v[f2P] for k, v in E.items()}
    tod = f["tod"].to_numpy(np.int64)
    inwin = (tod >= 950) & (tod <= 1500)
    p95 = f["adv20"].to_numpy(float) >= 95e6
    with np.errstate(invalid="ignore"):
        anyev = (ev["b1bits"] != 0) | np.isfinite(ev["b2zs"]) & (ev["b2zs"] >= 0.25) | np.isfinite(ev["b2zl"]) & (ev["b2zl"] >= 0.25)
        for k in NCO:
            anyev |= ev[f"b4a{k}"] > 0
        anyev |= np.isfinite(ev["b4bpush"]) & (ev["b4bpush"] >= 0.5) & (ev["b4bd"] >= 0.2) & (ev["b4bd"] <= 0.6)
        anyev |= ev["b5bits"] != 0
        anyev = anyev & p95
        a7 = (ev["a7t1"] | ev["a7t2"]) & (f["gap"].to_numpy(float) <= -3) & (tod >= 1030)
        anyev = (anyev | a7) & inwin
    # A7 structural exit (short, stop = 09:30-10:30 high, no target, flat 15:55)
    ia = np.flatnonzero(a7 & inwin)
    rS = np.full(len(f), np.nan, np.float32)
    if len(ia):
        stop = ev["a7stop"][ia]
        ent = f["close"].to_numpy(float)[ia]
        okk = stop > ent
        sub = ia[okk]
        RS = (stop - ent)[okk]
        rS[sub] = sim(hh, ll, cc, ptod, dend, f2P[sub], RS, -1, 0.0, 1.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0, 0.0)
    # same-minute baselines
    key = pd.MultiIndex.from_arrays([f["date"], f["tod"]])
    ob = pd.DataFrame({k: v for k, v in O.items()})
    ob["date"], ob["tod"] = f["date"].to_numpy(), tod
    b95 = ob[p95].groupby(["date", "tod"]).mean().add_prefix("b95_")
    ball = ob.groupby(["date", "tod"]).mean().add_prefix("ball_")
    ctx = pd.DataFrame({"date": f["date"].to_numpy()[p95], "tod": tod[p95], "up": f["fromOpen"].to_numpy(float)[p95] > 0}) \
        .groupby(["date", "tod"])["up"].mean().rename("breadth")
    C = b95.join(ball).join(ctx)
    ix = np.flatnonzero(anyev)
    out = f.loc[ix, ["symbol", "date", "tod"] + [c for c in FEAT if c not in ("high", "low")]].reset_index(drop=True)
    out["p95"] = p95[ix]
    for k, v in ev.items():
        if k != "a7stop":
            out[k] = v[ix]
    for k, v in O.items():
        out[f"o_{k}"] = v[ix]
    out["o_short_S"] = rS[ix]
    out = out.merge(C.reset_index(), on=["date", "tod"], how="left")
    out = out.merge(spy, on=["date", "tod"], how="left")
    out["black"] = earn_black(out[["symbol", "date"]])
    num = [c for c in out.columns if out[c].dtype.kind == "f"]
    out = out.astype({c: "float32" for c in num})
    out.to_parquet(Path(OUT) / f"ev_{m}.parquet", index=False)
    rs = np.random.default_rng(int(m.replace("-", ""))).choice(np.flatnonzero(p95 & inwin), size=min(20000, int((p95 & inwin).sum())), replace=False)
    np.save(Path(OUT) / f"atr_{m}.npy", f["atrPct"].to_numpy(float)[rs])
    print(m, len(f), len(P), "events", len(out), "a7", len(ia), round(time.time() - t0, 1), par, flush=True)
    return m, len(out), par


if __name__ == "__main__":
    OUT = sys.argv[1]
    ms = sys.argv[2:] or lib.months()
    assert not set(ms) & set(lib.LOCKED_MONTHS)
    with Pool(int(os.environ.get("NPROC", "3"))) as p:
        res = p.map(month_job, [(m, OUT) for m in ms], chunksize=1)
    import json
    json.dump({m: {"events": n, "sim_parity": par} for m, n, par in res}, open(Path(OUT) / "build_meta.json", "w"), indent=1)
