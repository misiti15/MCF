"""ex30/time: time / calendar setups (5 primaries + 10 neighbours = 15 configs) on the two-year open history.
PLAN.md was written and committed (80baddd2c) before this ran. Harness = ex30/peer + night1102/simple (gates.lab_trades:
production costs + time-of-day entry; day-matched random control). Features are computed here independently of the
modules (numpy segment lags vs the modules' pandas groupby) and compared bar by bar on 2026-09 (parity.csv).
spy_prng (live: SPY daily prior range / ATR) = SPY frame first-bar dist_pdh_atr + dist_pdl_atr, as pdl1030/pdl1a.
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
sys.path[:0] = [str(ROOT), str(ROOT / "research/history2y")]
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
COLS = ["symbol", "date", "tod", "close", "high", "atr_d", "adv20", "fromOpen", "vwapDistPct", "gap", "dist_hod_atr",
        "dist_lod_atr", "dist_pdh_atr", "dist_pdl_atr"] + \
       [f"{a}_{s}_t{g}" for a in ("r", "win") for s in ("long", "short") for g in ("1s1", "05s1")]


def col(df, k):
    return df[k].to_numpy(float)


def seg_lag(x, seg, n=1):
    p = np.r_[np.full(n, np.nan), x[:-n]]
    ps = np.r_[np.full(n, -1), seg[:-n]]
    p[ps != seg] = np.nan
    return p


def add_prng(df):
    sp = df[df["symbol"] == "SPY"].sort_values(["date", "tod"])
    fb = sp.groupby(sp["date"].astype(str)).first()
    prng = (fb["dist_pdh_atr"] + fb["dist_pdl_atr"]).astype(float)
    df["spy_prng"] = prng.reindex(df["date"].astype(str)).to_numpy(float)
    return df


def feats(df, new):
    seg = np.cumsum(new)
    c, atr, fo, tod = col(df, "close"), col(df, "atr_d"), col(df, "fromOpen"), col(df, "tod")
    dh, dl = col(df, "dist_hod_atr"), col(df, "dist_lod_atr")
    dt = pd.to_datetime(df["date"].astype(str))
    F = dict(c=c, tod=tod, atr=atr, vwd=col(df, "vwapDistPct"), spy=col(df, "spy_fo"), prng=col(df, "spy_prng"),
             gap=col(df, "gap"), dh=dh, dl=dl, dom=dt.dt.day.to_numpy(), dow=dt.dt.weekday.to_numpy())
    with np.errstate(invalid="ignore", divide="ignore"):
        F["hod"], F["lod"] = c + dh * atr, c - dl * atr
        F["pc"], F["ph"] = seg_lag(c, seg), seg_lag(col(df, "high"), seg)
        F["hod6"], F["lod2"] = seg_lag(F["hod"], seg, 6), seg_lag(F["lod"], seg, 2)
        F["mv"] = (c - c / (1 + fo / 100)) / atr
        F["rg"] = dh + dl
        F["ps"] = dl / F["rg"]
        F["va"] = F["vwd"] / 100 * c / atr
    return F


def tm1(F, mv=0.75, dh=0.40):
    return (np.abs(F["spy"]) <= 0.25) & (F["mv"] >= mv) & (F["dh"] >= dh) & \
        (F["hod"] - F["hod6"] <= 0.01 * F["atr"]) & (F["c"] < F["pc"])


def tm2(F, pr=1.0, sp=0.20):
    p = np.ones(len(F["c"]), bool) if pr is None else (F["prng"] <= pr)
    return (np.abs(F["spy"]) <= sp) & p & (F["rg"] >= 0.75) & (F["ps"] <= 0.15) & (F["c"] > F["pc"])


def tm3(F, gp=1.0, mv=-0.75):
    return (F["gap"] >= gp) & (F["mv"] <= mv) & (F["dl"] <= 0.15) & (F["vwd"] < 0)


def tm4(F, mv=-0.75, mon=False):
    m = (F["mv"] <= mv) & (F["lod"] < F["lod2"]) & (F["c"] > F["ph"]) & (F["vwd"] < 0)
    return m & (F["dow"] == 0) if mon else m


def tm5(F, cal="tom", lo=28, hi=3):
    tom = (F["dom"] >= lo) | (F["dom"] <= hi)
    cm = tom if cal == "tom" else ~tom
    return cm & (F["mv"] >= 0.50) & (F["va"] > 0) & (F["va"] <= 0.15) & (F["c"] > F["pc"])


SETUPS = {
    "TM1-lunch-stalled-high-fade-quiet-short": ("short", "t05s1", (1130, 1330), tm1, [dict(mv=1.0), dict(dh=0.25)]),
    "TM2-quiet-tape-range-floor-fade-long": ("long", "t05s1", (1200, 1500), tm2, [dict(pr=None), dict(sp=0.30)]),
    "TM3-gapup-drift-powerhour-short": ("short", "t05s1", (1430, 1500), tm3, [dict(gp=2.0), dict(mv=-0.50)]),
    "TM4-ten-oclock-reversal-long": ("long", "t1s1", (1000, 1015), tm4, [dict(mv=-1.0), dict(mon=True)]),
    "TM5-turn-of-month-vwap-pullback-long": ("long", "t05s1", (1030, 1400), tm5,
                                             [dict(cal="not_tom"), dict(lo=27, hi=4)]),
}


def newflag(df):
    s, d = df["symbol"].to_numpy(), df["date"].to_numpy()
    return np.r_[True, (s[1:] != s[:-1]) | (d[1:] != d[:-1])]


def configs(df, new):
    F = feats(df, new)
    tod, adv = col(df, "tod"), np.nan_to_num(col(df, "adv20"))
    with np.errstate(invalid="ignore"):
        for name, (side, geom, w, fn, nbs) in SETUPS.items():
            base = (tod >= w[0]) & (tod <= w[1]) & (adv >= ADV)
            yield name, "primary", side, geom, w, fn(F) & base
            for nb in nbs:
                yield name, "nb " + ",".join(f"{k}={v}" for k, v in nb.items()), side, geom, w, fn(F, **nb) & base


def run_frame(df, split):
    if split == "VALID":
        df = df[df["date"].astype(str) <= VALID_END].reset_index(drop=True)
    new = newflag(df)
    tod, adv = col(df, "tod"), np.nan_to_num(col(df, "adv20"))
    trades, keys = [], set()
    for name, form, side, geom, w, m in configs(df, new):
        t = G.lab_trades(df, m, side, geom)
        t["setup"], t["form"], t["side"] = name, form, side
        trades.append(t)
        keys.add((side, geom, w))
    ctrl = []
    for side, geom, w in keys:
        base = (tod >= w[0]) & (tod <= w[1]) & (adv >= ADV)
        rr = df[f"r_{side}_{geom}"].to_numpy(float)
        ok = base & np.isfinite(rr) & (col(df, "atr_d") > 0)
        r = G.prod_r(rr[ok], col(df, f"win_{side}_{geom}")[ok], col(df, "close")[ok], col(df, "atr_d")[ok], geom, tod=tod[ok])
        c = pd.DataFrame({"date": pd.to_datetime(df["date"].to_numpy()[ok]).date, "r": r}).groupby("date").r.mean()
        ctrl.append(c.rename("ctrl").reset_index().assign(side=side, geom=geom, win=str(w)))
    tr = pd.concat(trades, ignore_index=True)
    tr["split"] = split
    return tr, pd.concat(ctrl, ignore_index=True).assign(split=split)


def load_mod(name):
    spec = importlib.util.spec_from_file_location("m_" + name.replace("-", "_"), HERE / "modules" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parity(df):
    """Harness masks == module masks on one month (bar by bar, inside window and ADV)."""
    mine = {n: m for n, f, *_, m in configs(df, newflag(df)) if f == "primary"}
    out = {}
    for name, (side, geom, w, *_r) in SETUPS.items():
        mod = load_mod(name)
        assert mod.SIDE == side and mod.GEOM == geom and tuple(mod.WINDOW) == w, name
        ref = np.asarray(mod.mask(df), bool) & (np.nan_to_num(col(df, "adv20")) >= ADV)
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
            df = add_prng(lib.load_month(mo, columns=COLS, context=True))
            assert df["spy_prng"].notna().mean() > 0.95, mo
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
