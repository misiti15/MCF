"""W4 step 1 (NOTES.md 1.1): the trade lists of book P (primary, 16 setups) and book T (Testing, 32 -FD setups), with
entry price, daily ATR and 5-minute ATR% joined from the open lab frames (research/history2y/lib.py refuses the locked
block; MCF_HIST_ALLOW_LOCKED is never set). The 3 L3-*-FD lists are generated here from the FD module masks.

Output (git-ignored): data/trades.parquet
    python research/swarm1010/w4_exits_sizing/build_trades.py
Educational only - not financial advice.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research/history2y")]
from lib import load_month, months  # noqa: E402
from mcf.research import gates as G  # noqa: E402

assert "MCF_HIST_ALLOW_LOCKED" not in __import__("os").environ
OUT = HERE / "data"
L3 = ["L3-gap-slope-rsi5hi-FD", "L3-gap-slope-lowdist-FD", "L3-gap-slope-fromopen-FD"]
L3_PRE = -2.6573517322540283


def load_mod(p: Path):
    spec = importlib.util.spec_from_file_location(p.stem.replace("-", "_"), p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    ver = json.load(open(ROOT / "research/bdi/fullday/verify.json"))["setups"]
    geom = {s["setup"]: s["geom"] for s in ver}
    cfg = yaml.safe_load((ROOT / "config/default.yaml").read_text())["strategies"]
    primary = [k for k, v in cfg.items() if v.get("enabled") and v.get("type") in ("lab", "heat")]
    testing_fd = [s["setup"] for s in ver]
    t = pd.read_parquet(ROOT / "research/bdi/timeofday/data/trades.parquet")
    parts = []
    p = t[(t["set"] == "current") & t["setup"].isin(primary)].copy()
    p["book"] = "P"
    p["geom"] = p["setup"].map(lambda s: geom[s + "-FD"])
    parts.append(p)
    f = t[(t["set"] == "full") & (t["setup"] + "-FD").isin(testing_fd)].copy()
    f["setup"] = f["setup"] + "-FD"
    f["book"] = "T"
    f["geom"] = f["setup"].map(geom)
    parts.append(f)
    print("primary lab/heat:", len(primary), "| testing from timeofday:", f["setup"].nunique(), flush=True)

    mods = {n: load_mod(ROOT / f"research/bdi/fullday/{n}.py") for n in L3}
    cols = ["symbol", "date", "tod", "close", "atr_d", "atrPct", "gap", "sma20_slope_pct", "rsi5", "fromOpen",
            "dist_lod_atr", "r_short_t1s1", "win_short_t1s1", "r_short_t05s1", "win_short_t05s1"]
    trades = pd.concat(parts, ignore_index=True)
    trades["date"] = trades["date"].astype(str)
    feat, l3 = [], []
    for mo in months():
        df = load_month(mo, cols)
        df["date"] = df["date"].astype(str)
        tod = df["tod"].to_numpy()
        for n, m in mods.items():
            g = m.GEOM
            msk = np.asarray(m.mask(df), bool) & (tod >= 950) & (tod <= 1500) & (df["gap"].to_numpy(float) <= L3_PRE)
            lt = G.lab_trades(df.assign(date=pd.to_datetime(df["date"])), msk, "short", g)
            lt["date"] = lt["date"].astype(str)
            lt["setup"], lt["side"], lt["geom"], lt["book"], lt["set"] = n, "short", g, "T", "full"
            l3.append(lt)
        need = pd.concat([trades.loc[trades["date"].str.startswith(mo), ["symbol", "date", "tod"]],
                          l3[-3][["symbol", "date", "tod"]], l3[-2][["symbol", "date", "tod"]],
                          l3[-1][["symbol", "date", "tod"]]]).drop_duplicates()
        feat.append(need.merge(df[["symbol", "date", "tod", "close", "atr_d", "atrPct"]], how="left"))
        print(mo, len(df), flush=True)
        del df
    l3 = pd.concat(l3, ignore_index=True)
    print("L3 counts:", l3.groupby("setup").size().to_dict(), flush=True)
    trades = pd.concat([trades, l3[trades.columns.intersection(l3.columns)]], ignore_index=True)
    feat = pd.concat(feat, ignore_index=True).drop_duplicates(["symbol", "date", "tod"])
    trades = trades.merge(feat, on=["symbol", "date", "tod"], how="left")
    print("missing features:", int(trades["close"].isna().sum()), flush=True)
    order = {n: i for i, n in enumerate(primary)}
    order.update({n: 100 + i for i, n in enumerate(testing_fd)})
    trades["order"] = trades["setup"].map(order)
    trades.rename(columns={"r": "r_lab5"}).to_parquet(OUT / "trades_lab.parquet", index=False)
    print(trades.groupby(["book", "setup"]).size().to_string(), flush=True)


if __name__ == "__main__":
    main()
