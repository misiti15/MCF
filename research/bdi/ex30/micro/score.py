"""ex30/micro: 5 microstructure / bar-shape setups (primaries) + 10 neighbours on the two-year open history.
PLAN.md was written and committed before this ran. Harness = night1102/simple / ex30/xsec (gates.lab_trades:
production costs + time-of-day entry; day-matched random control). The harness re-implements every rule with pandas
group shifts, independent of the numpy modules; parity on 2026-09 compares the two bar by bar.
The rule-19 locked block (2024-11..2025-02) is never loaded (asserted).

    python score.py <scratch>   -> <scratch>/trades.parquet, <scratch>/ctrl.parquet, parity.csv here
Educational only - not financial advice.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "research/history2y"), str(HERE / "modules")]
import lib  # noqa: E402
from mcf.research import gates as G  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
S = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
TRAIN = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)]
VALID = ["2026-01", "2026-02", "2026-03", "2026-07", "2026-08", "2026-09"]
VALID_END = "2026-09-15"
for m in TRAIN + VALID:
    assert m not in lib.LOCKED_MONTHS and m in lib.months(), m
ADV = 95e6
COLS = ["symbol", "date", "tod", "close", "high", "low", "atr_d", "adv20", "vwapDistPct", "volumeRatio", "volumeSurge",
        "upper_wick", "lower_wick", "dist_hod_atr"] + \
       [f"{a}_{s}_t{g}" for a in ("r", "win") for s in ("long", "short") for g in ("1s1", "05s1")]


# ------------------------------------------------------------------------------------------------ harness rules (pandas)
def feats(df):
    g = df.groupby(["symbol", "date"], sort=False)
    F = pd.DataFrame(index=df.index)
    F["rng"] = (df.high - df.low) / df.atr_d
    for j in range(1, 11):
        F[f"rng{j}"] = g["high"].shift(j).sub(g["low"].shift(j)) / df.atr_d   # atr_d is constant inside a day
    F["h1"] = g["high"].shift(1)
    F["c1"] = g["close"].shift(1)
    for j in (1, 2, 3):
        F[f"vr{j}"] = g["volumeRatio"].shift(j)
    vw = df.close / (1 + df.vwapDistPct / 100)
    F["vwgap"] = (vw - df.close) / df.atr_d
    st = ((df.low <= vw) & (vw <= df.high) & (df.tod >= 950)).astype(float)
    live = (df.tod >= 950).astype(float)
    F["share"] = st.groupby([df.symbol, df.date]).cumsum() / live.groupby([df.symbol, df.date]).cumsum()
    # colour: compare (close-low)/range with 1-upper_wick (green) and lower_wick (red)
    pos = (df.close - df.low) / (df.high - df.low)
    body = 1 - df.upper_wick - df.lower_wick
    k = np.where((pos - (1 - df.upper_wick)).abs() <= (pos - df.lower_wick).abs(), 1.0, -1.0)
    k[~(body >= 0.05).to_numpy()] = 0.0
    F["k"] = k
    gk = F["k"].groupby([df.symbol, df.date])
    for j in range(1, 9):
        F[f"k{j}"] = gk.shift(j)
    hod = df.close + df.dist_hod_atr * df.atr_d
    at = hod.where(df.tod == 1030)
    F["H1"] = at.groupby([df.symbol, df.date]).transform("max").where(df.tod > 1030)
    return F


def mc1(df, F, k=7):
    nr = F["rng1"].notna()
    for j in range(2, k + 1):
        nr &= F["rng1"] <= F[f"rng{j}"]
    return nr & (df.close > F.h1) & (df.upper_wick <= 0.25) & (df.volumeRatio >= 1.5)


def mc2(df, F, surge=2.0):
    return (F.vr1 < 0.7) & (F.vr2 < 0.7) & (F.vr3 < 0.7) & (df.volumeRatio >= surge) & (df.upper_wick >= 0.5)


def mc3(df, F, share=0.60):
    return (F.share >= share) & (F.vwgap >= 0.30) & (df.lower_wick >= 0.5)


def mc4(df, F, n=6):
    run = pd.Series(True, index=df.index)
    for j in range(1, n + 1):
        run &= F[f"k{j}"] == -1
    return run & (F.k == 1) & (df.close > F.h1)


def mc5(df, F, vr=0.8):
    return (df.close > F.H1) & (F.c1 <= F.H1) & (df.volumeRatio < vr) & (df.volumeSurge < 1.0)


# name -> (side, geom, window, fn, primary kwargs, [neighbour kwargs])
SETUPS = {
    "MC1-nr7-expansion-volburst-long": ("long", "t1s1", (1045, 1500), mc1, {}, [dict(k=5), dict(k=10)]),
    "MC2-dryup-surge-wickreject-short": ("short", "t1s1", (1015, 1500), mc2, {}, [dict(surge=1.5), dict(surge=3.0)]),
    "MC3-vwap-glued-stretch-long": ("long", "t05s1", (1100, 1500), mc3, {}, [dict(share=0.50), dict(share=0.70)]),
    "MC4-redrun-outside-reversal-long": ("long", "t05s1", (1030, 1500), mc4, {}, [dict(n=5), dict(n=8)]),
    "MC5-firsthour-break-voldecay-short": ("short", "t1s1", (1035, 1400), mc5, {}, [dict(vr=0.6), dict(vr=1.0)]),
}


def configs(df):
    F = feats(df)
    tod, adv = df.tod.to_numpy(float), np.nan_to_num(df.adv20.to_numpy(float))
    for name, (side, geom, w, fn, kw, nbs) in SETUPS.items():
        base = (tod >= w[0]) & (tod <= w[1]) & (adv >= ADV)
        yield name, "primary", side, geom, w, fn(df, F, **kw).to_numpy(bool) & base
        for nb in nbs:
            yield name, "nb " + ",".join(f"{k}={v}" for k, v in nb.items()), side, geom, w, fn(df, F, **nb).to_numpy(bool) & base


def run_frame(df, split):
    tod, adv = df.tod.to_numpy(float), np.nan_to_num(df.adv20.to_numpy(float))
    trades, keys = [], set()
    for name, form, side, geom, w, m in configs(df):
        t = G.lab_trades(df, m, side, geom)
        t["setup"], t["form"], t["side"] = name, form, side
        trades.append(t)
        keys.add((side, geom, w))
    ctrl = []
    for side, geom, w in keys:
        base = (tod >= w[0]) & (tod <= w[1]) & (adv >= ADV)
        rr = df[f"r_{side}_{geom}"].to_numpy(float)
        ok = base & np.isfinite(rr) & (df.atr_d.to_numpy(float) > 0)
        r = G.prod_r(rr[ok], df[f"win_{side}_{geom}"].to_numpy(float)[ok], df.close.to_numpy(float)[ok],
                     df.atr_d.to_numpy(float)[ok], geom, tod=tod[ok])
        c = pd.DataFrame({"date": pd.to_datetime(df["date"].to_numpy()[ok]).date, "r": r}).groupby("date").r.mean()
        ctrl.append(c.rename("ctrl").reset_index().assign(side=side, geom=geom, win=str(w)))
    tr = pd.concat(trades, ignore_index=True)
    tr["split"] = split
    return tr, pd.concat(ctrl, ignore_index=True).assign(split=split)


def parity(df):
    """Harness masks == module masks on one month (bar by bar, inside window and ADV)."""
    mine = {n: m for n, f, *_, m in configs(df) if f == "primary"}
    out = {}
    for name, (side, geom, w, *_r) in SETUPS.items():
        spec = importlib.util.spec_from_file_location("m_" + name.replace("-", "_"), HERE / "modules" / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert mod.SIDE == side and mod.GEOM == geom and tuple(mod.WINDOW) == w, name
        ref = np.asarray(mod.mask(df), bool) & (np.nan_to_num(df.adv20.to_numpy(float)) >= ADV)
        a = mine[name]
        out[name] = dict(harness=int(a.sum()), module=int(ref.sum()), both=int((a & ref).sum()))
    return out


def main():
    t0 = time.time()
    (S / "cache").mkdir(parents=True, exist_ok=True)
    allt, allc = [], []
    for split, months in (("TRAIN", TRAIN), ("VALID", VALID)):
        for mo in months:
            ct = S / "cache" / f"{mo}.parquet"
            if ct.exists():
                allt.append(pd.read_parquet(ct)); allc.append(pd.read_parquet(S / "cache" / f"{mo}_ctrl.parquet"))
                continue
            df = lib.load_month(mo, columns=COLS)
            df = df[np.nan_to_num(df.adv20.to_numpy(float)) >= ADV]        # adv20 is per symbol-day: whole days drop
            if split == "VALID":
                df = df[df["date"].astype(str) <= VALID_END]
            df = df.reset_index(drop=True)
            df = df.astype({c: "float64" for c in COLS[2:]})   # same float64 arithmetic as the modules (parity)
            if mo == "2026-09":
                par = parity(df)
                print("parity 2026-09:", par, flush=True)
                pd.DataFrame(par).T.to_csv(HERE / "parity.csv")
            tr, c = run_frame(df, split)
            tr.to_parquet(ct, index=False); c.to_parquet(S / "cache" / f"{mo}_ctrl.parquet", index=False)
            allt.append(tr); allc.append(c)
            print(mo, split, len(tr), f"{time.time() - t0:.0f}s", flush=True)
            del df
    pd.concat(allt, ignore_index=True).to_parquet(S / "trades.parquet", index=False)
    pd.concat(allc, ignore_index=True).to_parquet(S / "ctrl.parquet", index=False)
    print("done", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
