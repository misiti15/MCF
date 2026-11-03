"""ex30/levels: 5 price-level / magnet setups (primaries) + 10 neighbours on the two-year open history.
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
COLS = ["symbol", "date", "tod", "close", "high", "low", "atr_d", "adv20", "vwapDistPct", "volumeRatio",
        "upper_wick", "dist_hod_atr", "fromOpen", "gap"] + \
       [f"{a}_{s}_t{g}" for a in ("r", "win") for s in ("long", "short") for g in ("1s1", "05s1")]


# ------------------------------------------------------------------------------------------------ harness rules (pandas)
def grid(px):
    return pd.Series(np.select([px >= 200, px >= 50, px >= 10], [10.0, 5.0, 1.0], 0.5), index=px.index)


def feats(df):
    g = df.groupby(["symbol", "date"], sort=False)
    F = pd.DataFrame(index=df.index)
    F["o"] = df.close / (1 + df.fromOpen / 100)
    F["pc"] = F.o / (1 + df.gap / 100)
    F["vw"] = df.close / (1 + df.vwapDistPct / 100)
    F["hod"] = (df.close + df.dist_hod_atr * df.atr_d).round(2)
    F["hodp"] = F.hod.groupby([df.symbol, df.date]).shift(1)
    F["c1"] = g["close"].shift(1)
    lows = pd.concat([g["low"].shift(j) for j in range(1, 7)], axis=1)
    F["lo6"] = lows.min(axis=1).where(lows.iloc[:, -1].notna())
    return F


def lv1(df, F, wick=0.40):
    st = grid(F.hodp)
    R = (np.floor(F.hodp / st) + 1) * st
    return (df.high >= R) & (df.close <= R - 0.05 * df.atr_d) & (df.upper_wick >= wick)


def lv2(df, F, pull=0.40):
    st = grid(df.close)
    R = np.floor(df.close / st) * st
    return (F.c1 < R) & (df.close >= R) & (F.hodp >= R - 0.05 * df.atr_d) & (F.hodp <= R + 0.10 * df.atr_d) & \
        (F.lo6 <= R - pull * df.atr_d)


def lv3(df, F, gmin=1.5):
    half = F.pc + 0.5 * (F.o - F.pc)
    return (df.gap >= gmin) & (df.gap <= 8.0) & (df.close <= half) & (F.c1 > half) & (df.close < F.vw) & \
        (df.close - F.pc >= 0.30 * df.atr_d)


def lv4(df, F, gmax=-1.0):
    return (df.gap <= gmax) & (F.hodp >= F.pc) & (df.low <= F.pc + 0.10 * df.atr_d) & (df.close >= F.pc + 0.02 * df.atr_d)


def lv5(df, F, stretch=1.0):
    return (df.gap.abs() <= 0.4) & (df.close >= F.pc + stretch * df.atr_d) & (df.dist_hod_atr <= 0.05) & (df.volumeRatio < 1.0)


# name -> (side, geom, window, fn, primary kwargs, [neighbour kwargs])
SETUPS = {
    "LV1-round-firsttouch-reject-short": ("short", "t05s1", (1000, 1500), lv1, {}, [dict(wick=0.30), dict(wick=0.50)]),
    "LV2-round-secondtouch-break-long": ("long", "t1s1", (1030, 1500), lv2, {}, [dict(pull=0.30), dict(pull=0.50)]),
    "LV3-gapup-halffill-short": ("short", "t1s1", (1000, 1400), lv3, {}, [dict(gmin=1.0), dict(gmin=2.5)]),
    "LV4-gapdn-filled-retest-long": ("long", "t05s1", (1015, 1500), lv4, {}, [dict(gmax=-0.5), dict(gmax=-2.0)]),
    "LV5-flatopen-pclose-stretch-short": ("short", "t1s1", (1130, 1500), lv5, {}, [dict(stretch=0.75), dict(stretch=1.25)]),
}


def configs(df):
    F = feats(df)
    tod, adv = df.tod.to_numpy(float), np.nan_to_num(df.adv20.to_numpy(float))
    for name, (side, geom, w, fn, kw, nbs) in SETUPS.items():
        base = (tod >= w[0]) & (tod <= w[1]) & (adv >= ADV)
        yield name, "primary", side, geom, w, fn(df, F, **kw).fillna(False).to_numpy(bool) & base
        for nb in nbs:
            yield name, "nb " + ",".join(f"{k}={v}" for k, v in nb.items()), side, geom, w, fn(df, F, **nb).fillna(False).to_numpy(bool) & base


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
