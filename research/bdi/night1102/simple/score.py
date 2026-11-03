"""night1102/simple: simpler forms (all condition subsets) of the busiest live setups, scored on the two-year open
history (TRAIN / VALID) and re-scored on the live period (2026-10-06..11-02 frames rebuilt from 1-minute bars).
PLAN.md was written before this ran. Costs: gates.lab_trades (production + time-of-day entry). Random control:
day-matched (trade R minus the mean R of every eligible bar of the same side / geometry / window / ADV that date).
The rule-19 locked block (2024-11..2025-02) is never loaded (lib.months() = open months only; asserted).

    python score.py <scratch>     -> <scratch>/trades_<split>.parquet, research/bdi/night1102/simple/results.csv
Educational only - not financial advice.
"""
from __future__ import annotations

import importlib.util
import itertools
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "research/history2y"), str(ROOT / "research/bdi/cwt/live")]
import lib  # noqa: E402
from mcf.research import gates as G  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
S = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
TRAIN = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)]
VALID = ["2026-01", "2026-02", "2026-03", "2026-07", "2026-08", "2026-09"]
VALID_END = "2026-09-15"
for m in TRAIN + VALID:
    assert m not in lib.LOCKED_MONTHS and m in lib.months(), m
COLS = ["symbol", "date", "tod", "close", "high", "low", "atr_d", "adv20", "heat", "buyPressure", "rsi", "rsi5", "gap",
        "sma20_dist_pct", "sma20_slope_pct", "bear_div", "fromOpen", "vwapDistPct", "dist_hod_atr", "dist_lod_atr",
        "dist_pdl_atr", "dist_pdh_atr", "volumeRatio", "emaDiff", "macdPct", "sma50_dist_pct", "flow3"] + [f"{a}_{s}_{g}" for a in ("r", "win") for s in ("long", "short") for g in ("t1s1", "t05s1")]


# ------------------------------------------------------------------------------------------------ helpers
def newday(df):
    sy, dt = df["symbol"].to_numpy(), df["date"].to_numpy()
    return np.r_[True, (sy[1:] != sy[:-1]) | (dt[1:] != dt[:-1])]


def prevv(v, new):
    p = np.r_[np.nan, np.asarray(v, float)[:-1]]
    p[new] = np.nan
    return p


def col(df, k):
    return df[k].to_numpy(float)


# ------------------------------------------------------------------------------------------------ kernels
# each kernel: side, geom, window, min_adv, conds(df, new) -> {label: bool array}; the parent = AND of all conds
def conds_rw(heat, bp, rsi_lbl):
    def f(df, new):
        rsi, rsi5 = col(df, "rsi"), col(df, "rsi5")
        r = {"rsi55-65": (rsi >= 55) & (rsi <= 65)} if rsi_lbl == "rsi55-65" else {"rsi5>80": rsi5 > 80}
        return {f"heat<={heat}": col(df, "heat") <= heat, f"bp<{bp}": col(df, "buyPressure") < bp, **r,
                "gap<0": col(df, "gap") < 0}
    return f


def conds_exh(df, new):
    return {"rsi5>90": col(df, "rsi5") > 90, "sma20dist>1": col(df, "sma20_dist_pct") > 1.0, "bear_div": col(df, "bear_div") > 0}


def conds_st2(df, new):
    s = col(df, "sma20_slope_pct")
    c = col(df, "close")
    z = (c - c / (1 + col(df, "vwapDistPct") / 100)) / col(df, "atr_d")
    return {"slope20 crosses up": (s > 0) & (prevv(s, new) <= 0), "down>3% from open": col(df, "fromOpen") < -3.0,
            "bp>0": col(df, "buyPressure") > 0, "|vwap z|<0.5": np.abs(z) < 0.5}


def conds_cwt13(df, new):
    c, l, atr = col(df, "close"), col(df, "low"), col(df, "atr_d")
    lod = c - col(df, "dist_lod_atr") * atr
    hod = c + col(df, "dist_hod_atr") * atr
    vw = c / (1 + col(df, "vwapDistPct") / 100)
    near = (c - lod) / atr <= 0.05
    stretch = (vw - c) >= 0.5 * atr
    used = (hod - lod) / atr >= 0.4
    return {"prev at LOD": prevv(near.astype(float), new) == 1, "prev >=0.5ATR below VWAP": prevv(stretch.astype(float), new) == 1,
            "prev range>=0.4ATR": prevv(used.astype(float), new) == 1, "higher low": l > prevv(l, new)}


def b3_long(df, new, p, maxbars, lowvol):
    """cwt_live_lib.b3(level='PD', side='long') with the poke depth p and the reclaim limit as parameters
    (maxbars=None: no limit). Only symbol-days whose low reaches the prior-day low are looped."""
    c, l = col(df, "close"), col(df, "low")
    atr = col(df, "atr_d")
    seg = np.cumsum(new) - 1
    first = np.flatnonzero(new)
    L = (c - col(df, "dist_pdl_atr") * atr)[first][seg]
    A = atr[first][seg]
    vr = np.where(col(df, "tod") < 950, np.nan, col(df, "volumeRatio"))
    touch = pd.Series(l <= L - p * A).groupby(seg).transform("any").to_numpy()
    flag = np.zeros(len(c), bool)
    inexc = stale = False
    st, v0 = 0, np.nan
    for i in np.flatnonzero(touch):
        if new[i]:
            inexc = stale = False
        if math.isnan(L[i]):
            continue
        beyond = l[i] <= L[i] - p * A[i]
        inside = c[i] > L[i]
        if not inexc and not stale and beyond:
            inexc, st, v0 = True, i, vr[i]
        if inexc:
            if inside:
                if (maxbars is None or i - st <= maxbars) and (not lowvol or v0 < 1):
                    flag[i] = True
                inexc = False
            elif maxbars is not None and i - st > maxbars:
                inexc, stale = False, True
        elif stale and inside:
            stale = False
    return flag


KERNELS = {
    "RW7-gapdn-bounce-early-short-FD": dict(side="short", geom="t1s1", win=(950, 1500), adv=95e6, conds=conds_rw(-20, -0.15, "rsi55-65"),
                                            module="research/bdi/fullday/RW7-gapdn-bounce-early-short-FD.py"),
    "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": dict(side="short", geom="t1s1", win=(950, 1500), adv=95e6, conds=conds_rw(-30, -0.15, "rsi5>80"),
                                                       module="research/bdi/fullday/RW5-heat30-flowsell-rsi5pop-gapdn-short-FD.py"),
    "RW3-gapdn-rsi5pop-flowsell-short-FD": dict(side="short", geom="t1s1", win=(950, 1500), adv=95e6, conds=conds_rw(-20, -0.35, "rsi5>80"),
                                                module="research/bdi/fullday/RW3-gapdn-rsi5pop-flowsell-short-FD.py"),
    "exhaustion_short-FD": dict(side="short", geom="t1s1", win=(950, 1500), adv=95e6, conds=conds_exh,
                                module="research/bdi/fullday/exhaustion_short-FD.py"),
    "ST2-slope20up-long-am-t05s1-FD": dict(side="long", geom="t05s1", win=(950, 1500), adv=95e6, conds=conds_st2,
                                           module="research/bdi/fullday/ST2-slope20up-long-am-t05s1-FD.py"),
    "CWT13-vwapstretch-z05-long": dict(side="long", geom="t05s1", win=(1100, 1500), adv=95e6, conds=conds_cwt13,
                                       module="research/bdi/cwt/live/CWT13-vwapstretch-z05-long.py"),
    "CWT14-failbrk-pdl-p10-long": dict(side="long", geom="t05s1", win=(950, 1500), adv=95e6, conds=None,
                                       module="research/bdi/cwt/live/CWT14-failbrk-pdl-p10-long.py"),
}
CWT14_FORMS = [("parent p0.10 reclaim<=3", 0.10, 3, False), ("drop depth: p0 reclaim<=3", 0.0, 3, False),
               ("drop reclaim limit: p0.10", 0.10, None, False), ("drop both: any touch then reclaim", 0.0, None, False),
               ("add lowvol (live p10-lowvol twin)", 0.10, 3, True)]


def configs_for(df, new):
    """-> list of (kernel, form label, k conditions, mask without window/ADV) ; parent first."""
    out = []
    for k, K in KERNELS.items():
        if K["conds"] is None:
            for lab, p, mb, lv in CWT14_FORMS:
                nc = 1 + (p > 0) + (mb is not None) + lv
                out.append((k, lab, nc, b3_long(df, new, p, mb, lv)))
            c, pdl = col(df, "close"), col(df, "close") - col(df, "dist_pdl_atr") * col(df, "atr_d")
            seg = np.cumsum(new) - 1
            L = pdl[np.flatnonzero(new)][seg]
            out.append((k, "core: close crosses above PDL", 1, (c > L) & (prevv(c, new) <= L)))
            continue
        cd = K["conds"](df, new)
        names = list(cd)
        with np.errstate(invalid="ignore"):
            for r in range(len(names), 0, -1):
                for sub in itertools.combinations(names, r):
                    m = np.ones(len(df), bool)
                    for nm in sub:
                        m &= np.asarray(cd[nm], bool)
                    lab = "parent" if r == len(names) else ("drop " + " & ".join(x for x in names if x not in sub)
                                                            if r == len(names) - 1 else "core: " + " & ".join(sub))
                    out.append((k, lab, r, m))
        if k == "exhaustion_short-FD":
            out.append((k, "parent + ADV>=150M (RW2-noon-adv150-FD twin)", 4, out[-7][3] & (col(df, "adv20") >= 150e6)))
    return out


def run_frame(df, split):
    df = df.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    if split == "VALID":
        df = df[df["date"].astype(str) <= VALID_END].reset_index(drop=True)
    new = newday(df)
    tod, adv = col(df, "tod"), np.nan_to_num(col(df, "adv20"))
    trades, ctrl = [], []
    for k, lab, nc, m in configs_for(df, new):
        K = KERNELS[k]
        base = (tod >= K["win"][0]) & (tod <= K["win"][1]) & (adv >= (150e6 if "150M" in lab else K["adv"]))
        t = G.lab_trades(df, m & base, K["side"], K["geom"])
        t["kernel"], t["form"], t["k"] = k, lab, nc
        trades.append(t)
    for key in {(K["side"], K["geom"], K["win"], K["adv"]) for K in KERNELS.values()} | {("short", "t1s1", (950, 1500), 150e6)}:
        side, geom, w, a = key
        base = (tod >= w[0]) & (tod <= w[1]) & (adv >= a)
        rr = df[f"r_{side}_{geom}"].to_numpy(float)
        ok = base & np.isfinite(rr) & (col(df, "atr_d") > 0)
        r = G.prod_r(rr[ok], col(df, f"win_{side}_{geom}")[ok], col(df, "close")[ok], col(df, "atr_d")[ok], geom, tod=tod[ok])
        c = pd.DataFrame({"date": pd.to_datetime(df["date"].to_numpy()[ok]).date, "r": r}).groupby("date").r.mean()
        ctrl.append(c.rename("ctrl").reset_index().assign(side=side, geom=geom, win=str(w), adv=a))
    tr = pd.concat(trades, ignore_index=True)
    tr["split"] = split
    return tr, pd.concat(ctrl, ignore_index=True).assign(split=split)


def parity(df):
    """My parent masks == the live module masks on one month (bar by bar, inside window and ADV)."""
    df = df.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    new = newday(df)
    mine = {(k, lab): m for k, lab, nc, m in configs_for(df, new) if lab.startswith("parent")}
    out = {}
    for k, K in KERNELS.items():
        spec = importlib.util.spec_from_file_location("m_" + k.replace("-", "_"), ROOT / K["module"])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        need = {"volume", "vol_climax", "volumeRatio"}
        d2 = df if not need - set(df.columns) else df.assign(**{c: df.get(c, 0.0) for c in need - set(df.columns)})
        with np.errstate(invalid="ignore"):
            ref = np.asarray(mod.mask(d2), bool)
        lab = "parent p0.10 reclaim<=3" if K["conds"] is None else "parent"
        tod = col(df, "tod")
        w = (tod >= K["win"][0]) & (tod <= K["win"][1]) & (np.nan_to_num(col(df, "adv20")) >= K["adv"])
        a, b = mine[(k, lab)] & w, ref & w
        out[k] = dict(mine=int(a.sum()), module=int(b.sum()), both=int((a & b).sum()))
    return out


def main():
    t0 = time.time()
    allt, allc = [], []
    for split, months in (("TRAIN", TRAIN), ("VALID", VALID)):
        for mo in months:
            df = lib.load_month(mo, columns=COLS + ["vol_climax"])
            if mo == "2026-09":
                par = parity(df)
                print("parity 2026-09:", par, flush=True)
                pd.Series({k: str(v) for k, v in par.items()}).to_csv(HERE / "parity.csv")
            tr, c = run_frame(df, split)
            allt.append(tr)
            allc.append(c)
            print(mo, split, len(tr), f"{time.time() - t0:.0f}s", flush=True)
            del df
    lf = pd.read_parquet(S / "live_frames.parquet")
    lf["date"] = pd.to_datetime(lf["date"]).dt.date
    tr, c = run_frame(lf, "LIVE")
    allt.append(tr)
    allc.append(c)
    T = pd.concat(allt, ignore_index=True)
    C = pd.concat(allc, ignore_index=True)
    T.to_parquet(S / "trades.parquet", index=False)
    C.to_parquet(S / "ctrl.parquet", index=False)
    print("done", len(T), f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
