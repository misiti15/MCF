"""ONE-TIME locked-block score (rule 19, look 1) of the 4 staged W1 candidates, authorised by the lead 2026-10-10.

Run with MCF_HIST_ALLOW_LOCKED=1 set for this script only:
    MCF_HIST_ALLOW_LOCKED=1 python research/swarm1010/w1_variants/score_locked.py
- Frames: research/history2y/data/locked (2024-11-01..2025-02-28) via lib.load_month.
- sma100_dist_pct: from data/cache_hist/1Min -> 5-min closes (same resample as the frames), SMA100 over the
  continuous series, kept only where today's bar count + 60 >= 100 (live parity: PRIOR5_BARS = 60 prior bars +
  today's bars; prior-day bars for 2024-11-01 come from the open October 2024 data). Same rule as build_extras.py.
- Modules run exactly as staged (modules/*.py, unchanged), YAML window 09:50-15:00, min_adv 95M (point-in-time
  adv20), first qualifying bar per symbol-day, production costs (gates.lab_trades / prod_r).
- Regimes: lib.regimes(include_locked=True) - tercile cut points from the open history only.
Bar (look 1): exp > 0 and day-clustered t >= 1.0. Writes locked.json. Educational only - not financial advice."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research" / "history2y")]
import lib  # noqa: E402
from mcf.data.bars import resample  # noqa: E402
from mcf.data.store import BarStore  # noqa: E402
from mcf.research import gates as G  # noqa: E402

MODS = ["W1-NS3-vwapreclaim-sma100-vol2-short", "W1-ST6-volspikeup-sma100above-short",
        "W1-ST1-ordn-sma100below-long", "W1-ST8-volspikedn-sma100below-long-t05s1"]
COLS = ["close", "vwapDistPct", "fromOpen", "volumeRatio", "atr_d", "gap", "macdPct", "flow3", "dist_lod_atr",
        "dist_hod_atr", "dist_pdh_atr", "dist_pdl_atr", "tod", "symbol", "date", "adv20",
        "r_short_t1s1", "win_short_t1s1", "r_long_t05s1", "win_long_t05s1"]
START, END = "2024-11-01", "2025-02-28"


def load_mod(name):
    sp = importlib.util.spec_from_file_location(name.replace("-", "_"), HERE / "modules" / f"{name}.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def sma100_table(symbols):
    store = BarStore(ROOT / "data" / "cache_hist")
    out = []
    for i, s in enumerate(symbols):
        df = store.load(s, end="2025-03-01")
        if df.empty:
            continue
        d5 = resample(df, "5min")
        c = d5["close"]
        dstr = pd.Index(d5.index.date.astype(str))
        g = pd.Series(np.r_[0, np.cumsum(dstr[1:] != dstr[:-1])])
        kbar = g.groupby(g).cumcount().to_numpy() + 1
        v = np.where(kbar + 60 >= 100, (c.to_numpy() / c.rolling(100).mean().to_numpy() - 1) * 100, np.nan)
        end = d5.index + pd.Timedelta(minutes=5)
        tod = (end.hour * 100 + end.minute).to_numpy()
        keep = (dstr >= START) & (dstr <= END) & (tod >= 950) & (tod <= 1500)
        out.append(pd.DataFrame({"symbol": s, "date": dstr[keep], "tod": tod[keep].astype(np.int32),
                                 "sma100_dist_pct": v[keep].astype(np.float32)}))
        if i % 200 == 0:
            print("sma100", i, s, flush=True)
    t = pd.concat(out, ignore_index=True)
    t["symbol"] = t["symbol"].astype("category")
    return t


def main():
    assert os.environ.get("MCF_HIST_ALLOW_LOCKED"), "set MCF_HIST_ALLOW_LOCKED=1 for this one-time score"
    mods = {n: load_mod(n) for n in MODS}
    trades = {n: [] for n in MODS}
    syms = BarStore(ROOT / "data" / "cache_hist").symbols()
    sma = sma100_table(syms)
    cover = {}
    for m in lib.LOCKED_MONTHS:
        df = lib.load_month(m, COLS)
        df = df[(df.tod >= 950) & (df.tod <= 1500)].reset_index(drop=True)
        key = pd.DataFrame({"symbol": df["symbol"].astype(str), "date": df["date"].astype(str),
                            "tod": df["tod"].astype(np.int32)})
        sm = sma[sma["date"].str.startswith(m)].copy()
        sm["symbol"] = sm["symbol"].astype(str)
        j = key.merge(sm, on=["symbol", "date", "tod"], how="left")
        assert len(j) == len(df)
        df["sma100_dist_pct"] = j["sma100_dist_pct"].to_numpy()
        cover[m] = {"rows": len(df), "sma100_nan_share": round(float(df["sma100_dist_pct"].isna().mean()), 4),
                    "sma100_nan_share_after_1250": round(float(df.loc[df.tod >= 1250, "sma100_dist_pct"].isna().mean()), 4)}
        ok = (df["adv20"].fillna(0).to_numpy() >= 95e6)
        for n, mod in mods.items():
            mk = np.asarray(mod.mask(df), bool) & ok
            trades[n].append(G.lab_trades(df, mk, mod.SIDE, mod.GEOM))
        print(m, cover[m], {n: sum(len(t) for t in trades[n]) for n in MODS}, flush=True)
    reg = lib.regimes(include_locked=True)
    lk = reg[(pd.Index(reg.index).astype(str) >= START) & (pd.Index(reg.index).astype(str) <= END)]
    n_sess = int(len(lk))
    out = {"sessions": n_sess, "regime_sessions": lk["regime"].value_counts().to_dict(),
           "cuts_open_history": reg.attrs.get("cuts"), "coverage": cover, "bar": "exp > 0 and day-clustered t >= 1.0 (look 1)"}
    for n in MODS:
        tr = pd.concat(trades[n], ignore_index=True)
        sm = G.summary(tr)
        rg = G.regime_split(tr, reg)
        passed = bool(sm.get("n", 0) and sm["exp_r"] > 0 and (sm.get("t") or 0) >= 1.0)
        out[n] = {"n": sm.get("n", 0), "per_day": round(sm.get("n", 0) / n_sess, 3), "win_rate": sm.get("win_rate"),
                  "exp_r": sm.get("exp_r"), "t": sm.get("t"), "ex_best_day": sm.get("ex_best_day"),
                  "days": sm.get("days"), "up": rg["up"], "flat": rg["flat"], "down": rg["down"],
                  "verdict": "passed_locked" if passed else "failed_locked"}
        print(n, json.dumps(out[n])[:400], flush=True)
    (HERE / "locked.json").write_text(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
