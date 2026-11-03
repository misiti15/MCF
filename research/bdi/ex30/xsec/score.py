"""ex30/xsec: cross-sectional rank-proxy setups (5 primaries + 10 neighbours) and information-only true universe ranks
(grid T, 24 configs) on the two-year open history. PLAN.md was written and committed before this ran.
Harness = night1102/simple (gates.lab_trades: production costs + time-of-day entry; day-matched random control).
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
COLS = ["symbol", "date", "tod", "close", "atr_d", "adv20", "fromOpen", "vwapDistPct"] + \
       [f"{a}_{s}_t{g}" for a in ("r", "win") for s in ("long", "short") for g in ("1s1", "05s1")]


def col(df, k):
    return df[k].to_numpy(float)


def lag(x, new, n=1):
    """x shifted n bars inside each symbol-day (NaN across a boundary)."""
    x = np.asarray(x, float)
    p = np.r_[np.full(n, np.nan), x[:-n]]
    seg = np.cumsum(new)
    ps = np.r_[np.full(n, -1), seg[:-n]]
    p[ps != seg] = np.nan
    return p


# ------------------------------------------------------------------------------------------------ rank-proxy setups
def feats(df, new):
    c, atr, fo = col(df, "close"), col(df, "atr_d"), col(df, "fromOpen")
    with np.errstate(invalid="ignore", divide="ignore"):
        return dict(c=c, move=(c - c / (1 + fo / 100)) / atr, excess=(fo - col(df, "spy_fo")) / (atr / c * 100),
                    vwd=col(df, "vwapDistPct"), b=col(df, "breadth"), bo=col(df, "breadth_open"), spy=col(df, "spy_fo"))


def xs1(F, new, bo=0.65, mv=0.75):
    return (F["bo"] >= bo) & (F["spy"] > 0) & (F["move"] <= -mv) & (F["vwd"] < 0)


def xs2(F, new, bo=0.35, mv=0.75):
    return (F["bo"] <= bo) & (F["spy"] < 0) & (F["move"] >= mv) & (F["vwd"] > 0)


def quiet(F):
    return (np.abs(F["spy"]) <= 0.25) & (F["b"] >= 0.35) & (F["b"] <= 0.65)


def xs3(F, new, ex=1.0):
    return quiet(F) & (F["excess"] >= ex) & (F["c"] < lag(F["c"], new))


def xs4(F, new, ex=1.0):
    return quiet(F) & (F["excess"] <= -ex) & (F["c"] > lag(F["c"], new))


def xs5(F, new, db=0.15):
    v = F["vwd"]
    return (F["b"] - lag(F["b"], new, 3) <= -db) & (v - lag(v, new, 3) > 0) & (lag(v, new) <= 0) & (v > 0)


# name -> (side, geom, window, fn, primary kwargs, [neighbour kwargs], module)
SETUPS = {
    "XS1-laggard-greentape-short": ("short", "t1s1", (1000, 1400), xs1, {}, [dict(bo=0.60), dict(mv=1.0)]),
    "XS2-leader-redtape-long": ("long", "t1s1", (1000, 1400), xs2, {}, [dict(bo=0.40), dict(mv=1.0)]),
    "XS3-quiet-topoutlier-fade-short": ("short", "t1s1", (1030, 1430), xs3, {}, [dict(ex=0.75), dict(ex=1.5)]),
    "XS4-quiet-bottomoutlier-fade-long": ("long", "t1s1", (1030, 1430), xs4, {}, [dict(ex=0.75), dict(ex=1.5)]),
    "XS5-rankclimb-fallingtape-long": ("long", "t05s1", (1000, 1500), xs5, {}, [dict(db=0.10), dict(db=0.20)]),
}


def configs(df, new):
    F = feats(df, new)
    tod, adv = col(df, "tod"), np.nan_to_num(col(df, "adv20"))
    with np.errstate(invalid="ignore"):
        for name, (side, geom, w, fn, kw, nbs) in SETUPS.items():
            base = (tod >= w[0]) & (tod <= w[1]) & (adv >= ADV)
            yield name, "primary", side, geom, w, fn(F, new, **kw) & base
            for nb in nbs:
                yield name, "nb " + ",".join(f"{k}={v}" for k, v in nb.items()), side, geom, w, fn(F, new, **nb) & base
        # grid T: true universe top / bottom 10 at one decision bar (information only: not live-runnable)
        vwatr = (F["c"] - F["c"] / (1 + F["vwd"] / 100)) / col(df, "atr_d")
        for t in (1000, 1100, 1300):
            at = (tod == t) & (adv >= ADV)
            for fname, x in (("move", F["move"]), ("vwapATR", vwatr)):
                ok = at & np.isfinite(x)
                s = pd.Series(np.where(ok, x, np.nan))
                d = pd.Series(df["date"].to_numpy())
                hi = s.groupby(d).rank(ascending=False, method="first").to_numpy() <= 10
                lo = s.groupby(d).rank(ascending=True, method="first").to_numpy() <= 10
                for ext, m in (("top", hi & ok), ("bottom", lo & ok)):
                    for style in ("momentum", "fade"):
                        side = ("long" if ext == "top" else "short") if style == "momentum" else ("short" if ext == "top" else "long")
                        yield f"T-{fname}-{t}-{ext}10-{style}-{side}", "gridT", side, "t1s1", (t, t), m


def run_frame(df, split):
    if split == "VALID":
        df = df[df["date"].astype(str) <= VALID_END].reset_index(drop=True)
    new = np.r_[True, (df["symbol"].to_numpy()[1:] != df["symbol"].to_numpy()[:-1]) | (df["date"].to_numpy()[1:] != df["date"].to_numpy()[:-1])]
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


def parity(df):
    """Harness masks == module masks on one month (bar by bar, inside window and ADV)."""
    new = np.r_[True, (df["symbol"].to_numpy()[1:] != df["symbol"].to_numpy()[:-1]) | (df["date"].to_numpy()[1:] != df["date"].to_numpy()[:-1])]
    mine = {n: m for n, f, *_, m in configs(df, new) if f == "primary"}
    out = {}
    for name, (side, geom, w, *_r) in SETUPS.items():
        spec = importlib.util.spec_from_file_location("m_" + name.replace("-", "_"), HERE / "modules" / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
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
            df = lib.load_month(mo, columns=COLS, context=True)
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
