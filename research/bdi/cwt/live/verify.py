"""Trade-for-trade parity of the Testing 2 CWT modules (research/bdi/cwt/live/<NAME>.py) with their scored versions.
Educational only - not financial advice.

For every package B setup in selection.py: rebuild the live-like 5-minute frame per symbol-day exactly as package B
saw it (lab frame rows 09:50-15:00 from research/history2y/lib.py, plus the 09:35-09:45 rows from
test_b/data/headtail.parquet; adv20 >= $95M; the locked block is never loaded), run the module's mask(df), keep the
first True bar per symbol-day inside the YAML window exactly as LabStrategy.generate does (tod >= max(950, lo) and
<= min(1500, hi)), and compare (date, symbol, entry bar) with the scored trades in test_b/data/trades.npz.
The expectancy over the matched trades is recomputed from the scored per-trade R (costs in).

    python research/bdi/cwt/live/verify.py [NAME ...]     # -> verify.json
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "research" / "history2y"))
sys.path.insert(0, str(HERE))
import lib  # noqa: E402
from selection import S  # noqa: E402

TB = HERE.parent / "test_b" / "data"
COLS = ["symbol", "date", "tod", "close", "high", "low", "vwapDistPct", "gap", "fromOpen", "atr_d", "dist_pdh_atr",
        "dist_pdl_atr", "volumeRatio", "vol_climax", "adv20"]


def load_mod(name):
    spec = importlib.util.spec_from_file_location(f"v_{name}", HERE / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def month_frame(month: str) -> pd.DataFrame:
    f = lib.load_month(month, COLS)
    f = f[(f["adv20"].to_numpy(float) >= 95e6) & (f["atr_d"].to_numpy(float) > 0)].reset_index(drop=True)
    f["symbol"] = f["symbol"].astype(str)
    a = pd.Timestamp(month + "-01")
    ht = pd.read_parquet(TB / "headtail.parquet", filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1))])
    ht["symbol"] = ht["symbol"].astype(str)
    ht["date"] = pd.to_datetime(ht["date"]).dt.date
    ht = ht[ht["tod"] < 950]                                    # the live frame's 09:35-09:45 rows
    ht = ht.merge(f[["symbol", "date"]].drop_duplicates(), on=["symbol", "date"], how="inner")
    h = pd.DataFrame({"symbol": ht["symbol"], "date": ht["date"], "tod": ht["tod"], "close": ht["c"], "high": ht["h"],
                      "low": ht["l"], "vwapDistPct": (ht["c"] / ht["vwap"] - 1) * 100})
    x = pd.concat([f.drop(columns="adv20"), h], ignore_index=True)
    return x.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)


def first_hits(df: pd.DataFrame, mask: np.ndarray, window) -> pd.DataFrame:
    lo, hi = window
    tod = df["tod"].to_numpy()
    m = np.asarray(mask, bool) & (tod >= max(950, lo)) & (tod <= min(1500, hi))
    h = df.loc[m, ["symbol", "date", "tod"]]
    return h.drop_duplicates(["symbol", "date"], keep="first")


def main(names=None):
    t0 = time.time()
    sel = [s for s in S if s["pkg"] == "B" and (not names or s["name"] in names)]
    mods = {s["name"]: load_mod(s["name"]) for s in sel}
    z = np.load(TB / "trades.npz", allow_pickle=True)
    dates = json.load(open(TB / "baseline.json"))["dates"]
    got = {s["name"]: [] for s in sel}
    for month in lib.months():
        df = month_frame(month)
        for s in sel:
            got[s["name"]].append(first_hits(df, mods[s["name"]].mask(df), s["window"]))
        print(month, len(df), round(time.time() - t0), flush=True)
    out = json.load(open(HERE / "verify.json")) if (HERE / "verify.json").exists() else {}
    for s in sel:
        g = pd.concat(got[s["name"]], ignore_index=True)
        mine = set(zip(g["date"].astype(str), g["symbol"], g["tod"].astype(int)))
        cid = s["cid"]
        ref = list(zip([dates[d] for d in z[f"{cid}|day"]], z[f"{cid}|sym"].astype(str), z[f"{cid}|tod"].astype(int)))
        r = z[f"{cid}|r"]
        refset = set(ref)
        matched = np.array([k in mine for k in ref])
        out[s["name"]] = {
            "source": f"package {s['pkg']} {s['cfg']} (id {cid})", "window": s["window"], "geom": s["geom"],
            "side": s["side"], "scored_n": len(ref), "module_n": len(mine), "matched": int(matched.sum()),
            "only_scored": len(refset - mine), "only_module": len(mine - refset),
            "parity": bool(mine == refset), "exp_scored": round(float(r.mean()), 4) if len(r) else None,
            "exp_matched": round(float(r[matched].mean()), 4) if matched.any() else None,
            "per_day": round(len(ref) / len(dates), 3),
        }
        print(s["name"], out[s["name"]], flush=True)
    out["_meta"] = {"what": "trade-for-trade parity of the live modules with the scored CWT configurations "
                            "(open two-year history; the locked block is never loaded). Educational only - not "
                            "financial advice.", "sessions": len(dates), "updated": time.strftime("%Y-%m-%d %H:%M")}
    json.dump(out, open(HERE / "verify.json", "w"), indent=1, sort_keys=True)


if __name__ == "__main__":
    main(sys.argv[1:])
