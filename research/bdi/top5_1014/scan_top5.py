"""top5_1014 step 3-4: one-knob variants of the 5 most-traded live setups on the open two-year history.
Pre-declaration: PLAN.md (written before this was run). Educational only - not financial advice.

    python research/bdi/top5_1014/scan_top5.py     # -> $SCR/trades.parquet (scratch, deleted after the report)

The rule-19 locked block 2024-11-01..2025-02-28 is never loaded: lib.months() lists open months only and
lib.load_month refuses locked months; MCF_HIST_ALLOW_LOCKED is never set.
"""
from __future__ import annotations

import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numba
import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT / "research" / "bdi" / "refire1014"), str(ROOT / "research" / "history2y"),
                str(ROOT / "research" / "heat" / "candidates"), str(ROOT / "research" / "bdi" / "cwt" / "live"), str(ROOT)]
import lib  # noqa: E402
import scan  # noqa: E402
import cwt_live_lib as CL  # noqa: E402
from _regime_common import regime_score  # noqa: E402
from mcf.research import gates  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/top5_1014")
W9 = {'rsiHeat': 1, 'priceActionHeat': 1, 'momentumHeat': -1, 'vwapHeat': -1}   # heat_fade_short-FD weights

# ------------------------------------------------------------------------------------------------ the grid (PLAN.md)
# each: (setup, var id, knob, dict of overrides). "P" = the parent (reference run, not counted).
CWT = {"CWT14-failbrk-orl-p05-long": dict(level="OR", p=0.05, k=3, vr=np.inf),
       "CWT14-failbrk-orl-p05-lowvol-long": dict(level="OR", p=0.05, k=3, vr=1.0),
       "CWT14-failbrk-pdl-p05-long": dict(level="PD", p=0.05, k=3, vr=np.inf)}
GRID = []
for s in CWT:
    GRID += [(s, "P", "parent", {}),
             (s, "V01", "p", {"p": 0.04}), (s, "V02", "p", {"p": 0.06}),
             (s, "V03", "reclaim", {"k": 2}), (s, "V04", "reclaim", {"k": 4}),
             (s, "V05", "window", {"win": (1030, 1500)}), (s, "V06", "window", {"win": (950, 1300)}),
             (s, "V07", "geom", {"geom": "t1s1"}), (s, "V08", "geom", {"geom": "t1s05"}),
             (s, "V09", "vwap", {"f": "vwap_above"}), (s, "V10", "vwap", {"f": "vwap_below"}),
             (s, "V11", "rsi", {"f": "rsi_lt40"}), (s, "V12", "rsi", {"f": "rsi_ge40"}),
             (s, "V13", "fromopen", {"f": "fo_gt_m1"}), (s, "V14", "gap", {"f": "gap_pos"})]
    if "lowvol" in s:
        GRID += [(s, "V15", "volratio", {"vr": 0.8}), (s, "V16", "volratio", {"vr": 1.2})]
H = "heat_fade_short-FD"
GRID += [(H, "P", "parent", {}),
         (H, "H01", "threshold", {"thr": -10.2}), (H, "H02", "threshold", {"thr": -12.4}), (H, "H03", "threshold", {"thr": -13.6}),
         (H, "H04", "window", {"win": (1030, 1500)}), (H, "H05", "window", {"win": (1130, 1500)}), (H, "H06", "window", {"win": (950, 1400)}),
         (H, "H07", "geom", {"geom": "t05s1"}), (H, "H08", "geom", {"geom": "t1s05"}),
         (H, "H09", "vwap", {"f": "vwap_above"}), (H, "H10", "vwap", {"f": "vwap_below"}),
         (H, "H11", "rsi", {"f": "rsi_ge50"}), (H, "H12", "rsi5", {"f": "rsi5_ge70"}), (H, "H13", "fromopen", {"f": "fo_le_m05"}),
         (H, "H14", "min_adv", {"adv": 100e6}), (H, "H15", "min_adv", {"adv": 150e6})]
R7 = "RW7-gapdn-bounce-early-short-FD"
GRID += [(R7, "P", "parent", {}),
         (R7, "R01", "heat", {"heat": -16}), (R7, "R02", "heat", {"heat": -24}),
         (R7, "R03", "buypressure", {"bp": -0.12}), (R7, "R04", "buypressure", {"bp": -0.18}),
         (R7, "R05", "rsi_band", {"rsi": (53, 67)}), (R7, "R06", "rsi_band", {"rsi": (57, 63)}),
         (R7, "R07", "gap", {"gap": -1.0}),
         (R7, "R08", "window", {"win": (1030, 1500)}), (R7, "R09", "window", {"win": (1130, 1500)}), (R7, "R10", "window", {"win": (950, 1400)}),
         (R7, "R11", "geom", {"geom": "t05s1"}), (R7, "R12", "geom", {"geom": "t1s05"}),
         (R7, "R13", "vwap", {"f": "vwap_above"}), (R7, "R14", "vwap", {"f": "vwap_below"}),
         (R7, "R15", "min_adv", {"adv": 114e6}), (R7, "R16", "min_adv", {"adv": 76e6})]
EXTRA = []   # plateau checks added only if PLAN section 4 calls for them (appended + counted in NOTES)


def setup_defaults(s):
    if s in CWT:
        return dict(side="long", geom="t05s1", win=(950, 1500), adv=95e6, **CWT[s])
    if s == H:
        return dict(side="short", geom="t1s1", win=(950, 1500), adv=125e6, thr=-11.3)
    return dict(side="short", geom="t1s1", win=(950, 1500), adv=95e6, heat=-20, bp=-0.15, rsi=(55, 65), gap=0.0)


# ------------------------------------------------------------------------------------------------ CWT14 kernel
@numba.njit(cache=True)
def _b3(new, lo_ok, L, h, l, c, vr, atr, p, kmax, vrmax):
    """cwt_live_lib.b3 (long side) with the reclaim window (kmax) and the poke-bar volume cap (vrmax) as knobs."""
    n = len(c)
    flag = np.zeros(n, np.bool_)
    inexc = False
    stale = False
    st = 0
    v0 = np.nan
    for i in range(n):
        if new[i]:
            inexc = False
            stale = False
        if not lo_ok[i] or np.isnan(L[i]):
            continue
        beyond = l[i] <= L[i] - p * atr[i]
        inside = c[i] > L[i]
        if (not inexc) and (not stale) and beyond:
            inexc = True
            st = i
            v0 = vr[i]
        if inexc:
            if inside:
                if i - st <= kmax and (vrmax == np.inf or v0 < vrmax):
                    flag[i] = True
                inexc = False
            elif i - st > kmax:
                inexc = False
                stale = True
        elif stale and inside:
            stale = False
    return flag


def cwt_levels(fh):
    x = CL.arrays(fh)
    at10 = np.where(x.tod == 1000, x.lod, np.nan)
    Lor = pd.Series(at10).groupby(x.seg).ffill().to_numpy(float)
    return x, {"OR": (Lor, x.tod >= 1005), "PD": (x.pdl, np.ones(x.n, bool))}


# ------------------------------------------------------------------------------------------------ trades
def filt(df, f):
    g = lambda k: df[k].to_numpy(float)  # noqa: E731
    return {None: np.ones(len(df), bool), "vwap_above": g("vwapDistPct") > 0, "vwap_below": g("vwapDistPct") < 0,
            "rsi_lt40": g("rsi") < 40, "rsi_ge40": g("rsi") >= 40, "rsi_ge50": g("rsi") >= 50,
            "rsi5_ge70": g("rsi5") >= 70, "fo_gt_m1": g("fromOpen") > -1.0, "fo_le_m05": g("fromOpen") <= -0.5,
            "gap_pos": g("gap") > 0}[f]


def trades(df, mask, cfg):
    tod = df["tod"].to_numpy()
    lo, hi = cfg["win"]
    with np.errstate(invalid="ignore"):
        base = (tod >= max(950, lo)) & (tod <= min(1500, hi)) & (df["adv20"].fillna(0).to_numpy() >= cfg["adv"]) \
            & (df["atr_d"].to_numpy(float) > 0)
    t = gates.lab_trades(df, np.asarray(mask, bool) & base, cfg["side"], cfg["geom"], tod_costs=True)
    return t


def controls(f, month):
    out = {}
    for adv in sorted({95e6, 125e6, 100e6, 150e6, 114e6, 76e6}):
        u = f[f["adv20"] >= adv]
        c = u[["date", "tod"]].copy()
        for s in ("long", "short"):
            for g in ("t05s1", "t1s1", "t1s05"):
                r = u[f"r_{s}_{g}"].to_numpy(float)
                ok = np.isfinite(r) & (u["atr_d"].to_numpy(float) > 0)
                v = np.full(len(u), np.nan)
                v[ok] = gates.prod_r(r[ok], u[f"win_{s}_{g}"].to_numpy(float)[ok], u["close"].to_numpy(float)[ok],
                                     u["atr_d"].to_numpy(float)[ok], g, tod=u["tod"].to_numpy(float)[ok])
                c[f"{s}_{g}"] = v
        out[adv] = c.groupby(["date", "tod"]).mean()
    return out


def month_job(month):
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS
    f = lib.load_month(month)
    f["symbol"] = f["symbol"].astype(str)
    fh = scan.with_head(f, scan.head_rows(f, month, liq=False))
    x, lev = cwt_levels(fh)
    vr = np.nan_to_num(x.vr, nan=np.inf)   # NaN volumeRatio never counts as low volume (as `v0 < 1` in b3)
    b3cache = {}
    ctrl = controls(f, month)
    rows = []
    for s, vid, knob, ov in GRID + EXTRA:
        cfg = {**setup_defaults(s), **ov}
        if s in CWT:
            key = (cfg["level"], cfg["p"], cfg["k"], cfg["vr"])
            if key not in b3cache:
                L, ok = lev[cfg["level"]]
                b3cache[key] = _b3(x.new, ok, L, x.h, x.l, x.c, vr, x.atr, cfg["p"], cfg["k"], cfg["vr"])
            df, m = fh, b3cache[key] & filt(fh, cfg.get("f"))
        elif s == H:
            sc = regime_score(f, "short", W9, 950, 1500, gate="fo-", k_cost=8.0, use_heat=False)
            with np.errstate(invalid="ignore"):
                df, m = f, (sc <= cfg["thr"]) & filt(f, cfg.get("f"))
        else:
            g = lambda k: f[k].to_numpy(float)  # noqa: E731
            with np.errstate(invalid="ignore"):
                m = (g("heat") <= cfg["heat"]) & (g("buyPressure") < cfg["bp"]) & (g("rsi") >= cfg["rsi"][0]) \
                    & (g("rsi") <= cfg["rsi"][1]) & (g("gap") < cfg["gap"]) & filt(f, cfg.get("f"))
            df = f
        t = trades(df, m, cfg)
        c = ctrl[cfg["adv"]][f"{cfg['side']}_{cfg['geom']}"]
        t["ctrl"] = [c.get((d, int(tt)), np.nan) for d, tt in zip(t["date"], t["tod"])]
        t["setup"], t["var"], t["knob"] = s, vid, knob
        rows.append(t)
    out = pd.concat(rows, ignore_index=True)
    print(month, len(out), round(time.time() - t0), flush=True)
    return out


def check_parity():
    """The numba kernel equals cwt_live_lib.b3 on one open month (first 300k rows)."""
    f = lib.load_month("2025-06")
    f["symbol"] = f["symbol"].astype(str)
    fh = scan.with_head(f, scan.head_rows(f, "2025-06", liq=False)).iloc[:300_000].reset_index(drop=True)
    x, lev = cwt_levels(fh)
    vr = np.nan_to_num(x.vr, nan=np.inf)
    for level, lowvol in (("OR", False), ("OR", True), ("PD", False)):
        a = CL.b3(fh, level=level, p=0.05, lowvol=lowvol, side="long")
        L, ok = lev[level]
        b = _b3(x.new, ok, L, x.h, x.l, x.c, vr, x.atr, 0.05, 3, 1.0 if lowvol else np.inf)
        assert (a == b).all(), (level, lowvol, int((a != b).sum()))
        print("parity ok", level, lowvol, int(a.sum()))


def main():
    SCR.mkdir(parents=True, exist_ok=True)
    check_parity()
    months = lib.months()
    assert not set(months) & set(lib.LOCKED_MONTHS)
    with Pool(int(os.environ.get("T5_PROCS", 3))) as p:
        T = pd.concat(p.map(month_job, months), ignore_index=True)
    T.to_parquet(SCR / "trades.parquet", index=False)
    print(T.groupby(["setup", "var"]).size().to_string())


if __name__ == "__main__":
    main()
