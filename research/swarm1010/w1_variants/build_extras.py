"""W1 step 0: indicator-variant columns aligned row-for-row with research/bdi/stack1009/data/base.npz (open two-year
history, adv20 >= 95M, bar closes 09:50-15:00; built by research/history2y/lib.py, rule-19 locked block refused).

Part A (frames, via lib.load_month - locked months refused): heat, rest3 = priceActionHeat - momentumHeat - vwapHeat
  (the heat_fade score minus its RSI component, so the RSI length can be varied), checked row-aligned on close.
Part B (data/cache_hist/1Min, rows of the locked block 2024-11-01..2025-02-28 DROPPED AT LOAD, before any computation):
  5-min bars (mcf.data.bars.resample) -> rsi5/9/14/21 (MarcoFlow simple RSI, as heat_frame), EMA pair differences
  (8/21, 13/21, 9/20, 8/20, 13/20; 9/21 = emaDiff for the check), SMA100 distance (live parity: valid only once
  60 prior + today's bars >= 100, i.e. today's bar count >= 40), VWAP SD z = (close - VWAP) / volume-weighted SD of
  the typical price (today's bars; as research/bdi/trendguard / RW6G1), and lab outcomes for two extra exits
  (target 1.5R / stop 1R = t15s1, target 1R / stop 0.75R = t1s075) with the lab's rules (R = 0.25 x daily ATR,
  stop first on a shared bar, timed exit at the 15:55 bar close) and production costs (gates.prod_r formula).
  Check columns: rsi14 vs base rsi, ema 9/21 vs emaDiff, t1s1 prod R vs base p_*_t1s1 (reported in build_check.json).

Output (git-ignored): data/ext/<name>.npy (float16 for indicators/outcomes, float32 for heat/rest3).
    python research/swarm1010/w1_variants/build_extras.py
Educational only - not financial advice.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numba
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research" / "history2y"), str(HERE)]
import lib  # noqa: E402
from mcf.data.bars import resample  # noqa: E402
from mcf.data.store import BarStore  # noqa: E402
from mcf.research.heat import _rsi_simple  # noqa: E402
from npzmap import npz_memmap  # noqa: E402

SDIR = ROOT / "research" / "bdi" / "stack1009" / "data"
OUT = HERE / "data" / "ext"
LOCKED = ("2024-11-01", "2025-02-28")
F16 = ["rsi9", "rsi21", "rsi5x", "rsi14x", "ed8_21", "ed13_21", "ed9_20", "ed8_20", "ed13_20", "ed9_21x", "sma100",
       "zsd", "p_long_t15s1", "p_short_t15s1", "p_long_t1s075", "p_short_t1s075", "p_long_t1s1x", "p_short_t1s1x"]
F32 = ["heat", "rest3"]


@numba.njit(cache=True)
def outcomes(c, h, l, tod, dnew, rows5, R, up, dn, side):
    """Lab outcome (gross R, won flag) for entries at 5-min bars rows5 (indices into c/h/l), production-cost R."""
    n = len(rows5)
    out = np.full(n, np.nan)
    m = len(c)
    for j in range(n):
        i = rows5[j]
        r = R[j]
        if not (r > 0) or i < 0:
            continue
        e = c[i]
        tg = e + side * up * r
        st = e - side * dn * r
        k = i + 1
        last = i
        res = 0  # 0 timed, 1 won, 2 lost
        while k < m and not dnew[k]:
            if tod[k] > 1555:
                break
            if (side > 0 and l[k] <= st) or (side < 0 and h[k] >= st):
                res = 2
                break
            if (side > 0 and h[k] >= tg) or (side < 0 and l[k] <= tg):
                res = 1
                break
            last = k
            k += 1
        if res == 1:
            g = up
        elif res == 2:
            g = -dn
        else:
            g = side * (c[last] - e) / r
        cost = 0.01 + e * 1e-4
        if res != 1:
            cost += 0.01 + e * 1e-4
        if res != 1 and g <= -dn + 1e-6:
            cost += 0.02
        out[j] = g - cost / r
    return out


def part_a(arrs, n):
    pos = 0
    for m in lib.months():
        df = lib.load_month(m, ["close", "tod", "adv20", "heat", "priceActionHeat", "momentumHeat", "vwapHeat",
                                "symbol", "date"])
        df = df[(df.tod >= 950) & (df.tod <= 1500)]
        df = df[df["adv20"].to_numpy(float) >= 95e6].reset_index(drop=True)
        k = len(df)
        arrs["heat"][pos:pos + k] = df["heat"].to_numpy(np.float32)
        arrs["rest3"][pos:pos + k] = (df["priceActionHeat"].to_numpy(np.float64) - df["momentumHeat"].to_numpy(np.float64)
                                      - df["vwapHeat"].to_numpy(np.float64)).astype(np.float32)
        arrs["_close"][pos:pos + k] = df["close"].to_numpy(np.float32)
        pos += k
        print("A", m, k, flush=True)
    assert pos == n, (pos, n)


def part_b(arrs, B, n):
    dates = pd.read_csv(SDIR / "dates.csv").iloc[:, 0].astype(str).tolist()
    dmap = {d: i for i, d in enumerate(dates)}
    symbols = pd.read_csv(SDIR / "symbols.csv").iloc[:, 0].astype(str).tolist()
    sym = np.asarray(B["sym"])
    order = np.argsort(sym, kind="stable")
    bounds = np.searchsorted(sym[order], np.arange(len(symbols) + 1))
    day, tod_b, atr = B["day"], B["tod"], B["atr_d"]
    store = BarStore(ROOT / "data" / "cache_hist")
    missing = 0
    t0 = time.time()
    for si, s in enumerate(symbols):
        rows = order[bounds[si]:bounds[si + 1]]
        if not len(rows):
            continue
        df = store.load(s)
        ds = pd.Series(df.index.date.astype(str), index=df.index)
        df = df[(ds < LOCKED[0]) | (ds > LOCKED[1])]          # locked block dropped before any computation
        d5 = resample(df, "5min")
        c, h, l, v = (d5[k].to_numpy(float) for k in ("close", "high", "low", "volume"))
        end = d5.index + pd.Timedelta(minutes=5)
        tod = (end.hour * 100 + end.minute).to_numpy()
        dstr = pd.Index(d5.index.date.astype(str))
        dnew = np.r_[True, dstr[1:] != dstr[:-1]]
        di = np.array([dmap.get(x, -1) for x in dstr], np.int64)
        cs = pd.Series(c)
        ind = {}
        for nn in (5, 9, 14, 21):
            ind[{5: "rsi5x", 9: "rsi9", 14: "rsi14x", 21: "rsi21"}[nn]] = _rsi_simple(cs, nn).to_numpy()
        ema = {k: cs.ewm(span=k, adjust=False).mean().to_numpy() for k in (8, 9, 13, 20, 21)}
        for f, sl in ((8, 21), (13, 21), (9, 20), (8, 20), (13, 20), (9, 21)):
            ind[f"ed{f}_{sl}" + ("x" if (f, sl) == (9, 21) else "")] = (ema[f] - ema[sl]) / ema[sl] * 100
        sma100 = cs.rolling(100).mean().to_numpy()
        g = pd.Series(np.cumsum(dnew))
        kbar = g.groupby(g).cumcount().to_numpy() + 1
        ind["sma100"] = np.where(kbar + 60 >= 100, (c / sma100 - 1) * 100, np.nan)
        tp = (h + l + c) / 3
        cv = pd.Series(v).groupby(g).cumsum().to_numpy().astype(float)
        cv[cv == 0] = np.nan
        vw = pd.Series(tp * v).groupby(g).cumsum().to_numpy() / cv
        var = pd.Series(tp * tp * v).groupby(g).cumsum().to_numpy() / cv - vw * vw
        sd = np.sqrt(np.clip(var, 0, None))
        with np.errstate(divide="ignore", invalid="ignore"):
            ind["zsd"] = np.where(sd > 0, (c - vw) / sd, np.nan)
        key5 = pd.Index(np.where(di >= 0, di * 10000 + tod, -1 - np.arange(len(di))))  # dates outside base: unique dummies
        keyb = day[rows].astype(np.int64) * 10000 + tod_b[rows].astype(np.int64)
        pos = key5.get_indexer(keyb)
        missing += int((pos < 0).sum())
        ok = pos >= 0
        for k, a in ind.items():
            vals = np.full(len(rows), np.nan)
            vals[ok] = a[pos[ok]]
            arrs[k][rows] = vals.astype(np.float16)
        R = 0.25 * atr[rows].astype(np.float64)
        for (up, dn, nm) in ((1.5, 1.0, "t15s1"), (1.0, 0.75, "t1s075"), (1.0, 1.0, "t1s1x")):
            for side, sn in ((1, "long"), (-1, "short")):
                r = outcomes(c, h, l, tod, dnew, np.where(ok, pos, -1).astype(np.int64), R, up, dn, side)
                arrs[f"p_{sn}_{nm}"][rows] = r.astype(np.float16)
        if si % 100 == 0:
            print("B", si, s, len(rows), f"missing {missing}", f"{time.time() - t0:.0f}s", flush=True)
    return missing


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    B = npz_memmap(SDIR / "base.npz")
    n = len(B["close"])
    arrs = {k: (np.full(n, np.nan, np.float16) if k.endswith("x") else   # check columns stay in RAM
                np.lib.format.open_memmap(OUT / f"{k}.npy", mode="w+", dtype=np.float16, shape=(n,))) for k in F16}
    skip_a = "--skip-a" in sys.argv     # heat / rest3 already built and checked (row alignment asserted)
    arrs.update({k: np.lib.format.open_memmap(OUT / f"{k}.npy", mode="r+" if skip_a else "w+", dtype=np.float32,
                                              shape=(n,)) for k in F32})
    for k in F16:
        arrs[k][:] = np.nan
    if not skip_a:
        arrs["_close"] = np.zeros(n, np.float32)
        part_a(arrs, n)
        assert np.array_equal(arrs["_close"], np.asarray(B["close"])), "part A row misalignment"
        del arrs["_close"]
    missing = part_b(arrs, B, n)
    chk = {"rows": n, "missing_rows_partB": missing}

    def cmp(a, b, name, tol):
        a = np.asarray(arrs[a], np.float64)
        b = np.asarray(B[b], np.float64)
        ok = np.isfinite(a) & np.isfinite(b)
        d = np.abs(a[ok] - b[ok])
        chk[name] = {"n": int(ok.sum()), "nan_new": int((~np.isfinite(a) & np.isfinite(b)).sum()),
                     "share_within_tol": float((d <= tol).mean()), "p999_absdiff": float(np.quantile(d, 0.999)),
                     "max_absdiff": float(d.max())}
    cmp("rsi14x", "rsi", "rsi14_vs_base", 0.1)
    cmp("rsi5x", "rsi5", "rsi5_vs_base", 0.1)
    cmp("ed9_21x", "emaDiff", "ema9_21_vs_base", 0.005)
    cmp("p_long_t1s1x", "p_long_t1s1", "t1s1_long_vs_base", 0.01)
    cmp("p_short_t1s1x", "p_short_t1s1", "t1s1_short_vs_base", 0.01)
    for k, a in arrs.items():
        if k in F32 and skip_a:
            continue
        if hasattr(a, "flush"):
            a.flush()
    (HERE / "build_check.json").write_text(json.dumps(chk, indent=1))
    print(json.dumps(chk, indent=1))


if __name__ == "__main__":
    main()
