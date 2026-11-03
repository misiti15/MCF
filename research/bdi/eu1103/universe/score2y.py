"""eu1103/universe: the 8 busiest live setups on the two-year open frames with NO ADV floor (adv20 >= $20M kept),
one row per trade with the symbol-day attributes needed for universe buckets (adv20, price, ATR%), plus a per
(date, symbol, side, geom) random-entry control (mean production R of every bar 09:50-15:00 of that symbol-day).
Masks = the live modules' own mask() / score() on the live-like frame (lab rows 09:50-15:00 + the 09:35-09:45 head
rows of research/bdi/cwt/test_b/data/headtail.parquet, as research/bdi/cwt/live/verify.py builds it).
Costs: gates.lab_trades / prod_r (production 1c + 1 bps per side, +2c stops, time-of-day entry multiplier).
Splits as night1102/simple: TRAIN 2024-10 + 2025-03..12, VALID 2026-01..03 + 2026-07..09-15 (old holdouts Apr-Jun 2026
and Sep 16-Oct 5 2026 not used). The rule-19 locked block 2024-11..2025-02 is never loaded (asserted).
    python score2y.py <scratch>  -> <scratch>/t2y/<month>.parquet, <scratch>/t2y/<month>_ctrl.parquet
Educational only - not financial advice."""
from __future__ import annotations

import importlib.util
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT), str(ROOT / "research/history2y"), str(ROOT / "research/bdi/cwt/live"),
                str(ROOT / "research/heat/candidates")]
import lib  # noqa: E402
from mcf.research import gates as G  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
S = Path(sys.argv[1]) / "t2y"
S.mkdir(parents=True, exist_ok=True)
TRAIN = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)]
VALID = ["2026-01", "2026-02", "2026-03", "2026-07", "2026-08", "2026-09"]
VALID_END = "2026-09-15"
for m in TRAIN + VALID:
    assert m not in lib.LOCKED_MONTHS and m in lib.months(), m

# name: (module path, kind, window, live min_adv)
SETUPS = {
    "CWT14-failbrk-orl-p05-long": ("research/bdi/cwt/live/CWT14-failbrk-orl-p05-long.py", "cwt", (950, 1500), 95e6),
    "CWT14-failbrk-pdl-p05-long": ("research/bdi/cwt/live/CWT14-failbrk-pdl-p05-long.py", "cwt", (950, 1500), 95e6),
    "CWT12-coil-k4-long": ("research/bdi/cwt/live/CWT12-coil-k4-long.py", "cwt", (950, 1130), 95e6),
    "CWT14-failbrk-pdh-p10-short": ("research/bdi/cwt/live/CWT14-failbrk-pdh-p10-short.py", "cwt", (950, 1200), 95e6),
    "heat_fade_short-FD": ("research/bdi/fullday/heat_fade_short-FD.py", "heat", (950, 1500), 125e6),
    "RW7-gapdn-bounce-early-short-FD": ("research/bdi/fullday/RW7-gapdn-bounce-early-short-FD.py", "lab", (950, 1500), 95e6),
    "RW2-exhaustion-noon-adv150-short-FD": ("research/bdi/fullday/RW2-exhaustion-noon-adv150-short-FD.py", "lab", (950, 1500), 150e6),
    "L3-gap-slope-fromopen-FD": ("research/bdi/fullday/L3-gap-slope-fromopen-FD.py", "lab", (950, 1500), 0.0),
}
TB = ROOT / "research/bdi/cwt/test_b/data"


def load(path):
    spec = importlib.util.spec_from_file_location("m_" + Path(path).stem.replace("-", "_"), ROOT / path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


MODS = {k: load(v[0]) for k, v in SETUPS.items()}


def head_rows(f, month):
    a = pd.Timestamp(month + "-01")
    ht = pd.read_parquet(TB / "headtail.parquet", filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1))])
    ht["symbol"] = ht["symbol"].astype(str)
    ht["date"] = pd.to_datetime(ht["date"]).dt.date
    ht = ht[ht["tod"] < 950].merge(f[["symbol", "date"]].drop_duplicates(), on=["symbol", "date"], how="inner")
    return pd.DataFrame({"symbol": ht["symbol"], "date": ht["date"], "tod": ht["tod"], "close": ht["c"], "high": ht["h"],
                         "low": ht["l"], "vwapDistPct": (ht["c"] / ht["vwap"] - 1) * 100, "ri": -1})


def run(month, split):
    f = lib.load_month(month)
    f = f[(np.nan_to_num(f["adv20"].to_numpy(float)) >= 20e6) & (f["atr_d"].to_numpy(float) > 0)]
    if split == "VALID":
        f = f[f["date"].astype(str) <= VALID_END]
    f = f.drop(columns=["ts"]).reset_index(drop=True)
    f["symbol"] = f["symbol"].astype(str)
    f["ri"] = np.arange(len(f))
    cw = ["symbol", "date", "tod", "close", "high", "low", "vwapDistPct", "gap", "fromOpen", "atr_d", "dist_pdh_atr",
          "dist_pdl_atr", "volumeRatio", "vol_climax", "ri"]
    x = pd.concat([f[cw], head_rows(f, month)], ignore_index=True)
    x = x.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    ri = x["ri"].to_numpy()
    tod = f["tod"].to_numpy(float)
    out = []
    for name, (path, kind, win, _) in SETUPS.items():
        mod = MODS[name]
        with np.errstate(invalid="ignore", divide="ignore"):
            if kind == "cwt":
                mx = np.asarray(mod.mask(x), bool)
                m = np.zeros(len(f), bool)
                m[ri[mx & (ri >= 0)]] = True
                side, geom = mod.SIDE, mod.GEOM
            elif kind == "heat":
                s = np.asarray(mod.score(f), float)
                m = np.nan_to_num(s, nan=np.inf) <= mod.SHORT_AT
                side, geom = "short", "t1s1"
            else:
                m = np.asarray(mod.mask(f), bool)
                side, geom = mod.SIDE, mod.GEOM
        if name.startswith("L3-"):
            m &= f["gap"].to_numpy(float) <= -2.6573517322540283
        m &= (tod >= win[0]) & (tod <= win[1])
        t = G.lab_trades(f, m, side, geom)
        k = f.set_index(["symbol", "date"])[["adv20", "atr_d"]]
        k = k[~k.index.duplicated()]
        t = t.join(k, on=["symbol", "date"])
        idx = G.first_per_symbol_day(f["symbol"].to_numpy(), f["date"].to_numpy(),
                                     m & np.isfinite(f[f"r_{side}_{geom}"].to_numpy(float)))
        t["px"] = f["close"].to_numpy(float)[idx]
        t["setup"], t["side"], t["geom"], t["split"] = name, side, geom, split
        out.append(t)
    # random control per symbol-day: mean production R over every bar 09:50-15:00
    ctrl = []
    for side in ("long", "short"):
        for geom in ("t1s1", "t05s1"):
            rr = f[f"r_{side}_{geom}"].to_numpy(float)
            ok = np.isfinite(rr)
            r = G.prod_r(rr[ok], f[f"win_{side}_{geom}"].to_numpy(float)[ok], f["close"].to_numpy(float)[ok],
                         f["atr_d"].to_numpy(float)[ok], geom, tod=tod[ok])
            c = pd.DataFrame({"symbol": f["symbol"].to_numpy()[ok], "date": f["date"].to_numpy()[ok], "r": r})
            c = c.groupby(["date", "symbol"]).r.mean().rename("rc").reset_index()
            ctrl.append(c.assign(side=side, geom=geom))
    return pd.concat(out, ignore_index=True), pd.concat(ctrl, ignore_index=True)


if __name__ == "__main__":
    t0 = time.time()
    for split, months in (("TRAIN", TRAIN), ("VALID", VALID)):
        for mo in months:
            p = S / f"{mo}.parquet"
            if p.exists():
                continue
            tr, c = run(mo, split)
            c.to_parquet(S / f"{mo}_ctrl.parquet", index=False)
            tr.to_parquet(p, index=False)
            print(mo, split, len(tr), tr.groupby("setup").size().to_dict(), f"{time.time() - t0:.0f}s", flush=True)
