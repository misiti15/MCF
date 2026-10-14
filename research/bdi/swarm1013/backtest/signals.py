"""swarm1013 backtest step 1: signals of the 11 live Primary lab setups on the open two-year frames.

Module mask & YAML window & adv20 >= min_adv; first qualifying bar per symbol-day per setup (RW6G1: every NS2-up3
base bar is kept here, its VWAP 2 SD guard is applied in bars.py on rebuilt 5-minute bars, then the first bar).
Open months only (lib.load_month refuses the locked block). Output: $SCR/signals.parquet.
Educational only - not financial advice.
"""
from __future__ import annotations

import importlib.util
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "research" / "history2y"))
sys.path.insert(0, str(ROOT))
import lib  # noqa: E402

SCR = Path(os.environ.get("SW_SCR", "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/sw1013bt"))
SETUPS = ["MF1", "MF2", "MF3", "MF4", "MF5", "NS1", "NS2", "NS3", "NS4", "NS5", "RW6G1"]
COLS = ["symbol", "date", "tod", "close", "high", "low", "atr_d", "adv20", "gap", "fromOpen", "vwapDistPct", "rsi", "rsi5",
        "sma50_dist_pct", "heat", "buyPressure", "momentum", "emaDiff", "volumeRatio", "flow3", "sma20_slope_pct",
        "sma20_dist_pct", "macdPct", "dist_pdh_atr", "dist_pdl_atr", "dist_hod_atr", "dist_lod_atr", "rsiSlope",
        "vwapReclaim", "pricePosition", "atrPct", "volumeSurge", "trendHeat", "rsiHeat", "momentumHeat", "vwapHeat",
        "macdHeat", "volumeHeat", "priceActionHeat", "flow9prev", "vol_climax", "bear_div", "bull_div", "upper_wick",
        "lower_wick", "dist_round_atr"]


def load_setups():
    cfg = yaml.safe_load((ROOT / "config/default.yaml").read_text())["strategies"]
    out = []
    for name, p in cfg.items():
        short = name.split("-")[0]
        if short not in SETUPS or not p.get("enabled") or p.get("type") != "lab":
            continue
        path = ROOT / p["module"]
        sys.path.insert(0, str(path.parent))
        spec = importlib.util.spec_from_file_location("m_" + re.sub(r"\W", "_", name), path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        out.append({"setup": short, "name": name, "mod": m, "side": m.SIDE, "geom": m.GEOM,
                    "min_adv": float(p.get("min_adv", 0)), "window": tuple(p.get("window") or (950, 1500))})
    assert sorted(s["setup"] for s in out) == sorted(SETUPS), [s["setup"] for s in out]
    return out


def main():
    SCR.mkdir(parents=True, exist_ok=True)
    sts = load_setups()
    rows = []
    for mo in lib.months():
        assert mo not in lib.LOCKED_MONTHS
        df = lib.load_month(mo)
        df["symbol"] = df["symbol"].astype(str)
        tod, adv = df["tod"].to_numpy(), df["adv20"].fillna(0).to_numpy()
        key = df["symbol"].to_numpy().astype(object) + "|" + df["date"].astype(str).to_numpy().astype(object)
        for s in sts:
            lo, hi = s["window"]
            base = (tod >= max(950, lo)) & (tod <= min(1500, hi)) & (adv >= s["min_adv"]) & (df["atr_d"].to_numpy() > 0)
            if s["setup"] == "RW6G1":
                # the NS2-up3 base of the module (its guard needs volume, applied later on rebuilt bars)
                with np.errstate(invalid="ignore"):
                    sma50 = df["sma50_dist_pct"].to_numpy(float)
                    p = np.r_[np.nan, sma50[:-1]]
                    p[np.r_[True, key[1:] != key[:-1]]] = np.nan
                    mk = (sma50 > 0) & (p <= 0) & (df["fromOpen"].to_numpy(float) > 3) & (df["rsi"].to_numpy(float) >= 60)
                mk = mk & base
                idx = np.flatnonzero(mk)
            else:
                with np.errstate(invalid="ignore"):
                    mk = np.asarray(s["mod"].mask(df), bool) & base
                idx = np.flatnonzero(mk)
                if len(idx):
                    _, first = np.unique(key[idx], return_index=True)
                    idx = np.sort(idx[first])
            sub = df.iloc[idx][["symbol", "date", "tod", "close", "high", "low", "atr_d", "adv20", "gap", "fromOpen",
                                "vwapDistPct", "rsi", f"r_{s['side']}_{s['geom']}", f"win_{s['side']}_{s['geom']}"]].copy()
            sub = sub.rename(columns={f"r_{s['side']}_{s['geom']}": "lab_r", f"win_{s['side']}_{s['geom']}": "lab_win"})
            sub["setup"], sub["side"], sub["geom"] = s["setup"], s["side"], s["geom"]
            rows.append(sub)
        print(mo, len(df), flush=True)
        del df
    x = pd.concat(rows, ignore_index=True)
    x["date"] = pd.to_datetime(x["date"])
    x.to_parquet(SCR / "signals.parquet", index=False)
    print(x.groupby("setup").size())


if __name__ == "__main__":
    main()
