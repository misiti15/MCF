"""late_entry1027 / sizing_proof: two-year, live-shaped per-setup trade lists for every covered setup of Primary,
Testing 1 and Testing 2 (docs/live/assignments.json, 2026-10-27), costs in, with the 5-minute exit bar of every trade.

Same code as research/bdi/gates1021/scripts/scan.py (live_setups -> unique_setups, mask, window capped at 09:50..15:00,
min_adv on point-in-time adv20, refire chain, prod_r_tier = production costs with time-of-day entry costs and 3x on
the extended tier, exit_bars = stop-first 5-minute bracket walk). The gates1021 cache keeps exit bars only for two
setups, so this builder adds exit_tod / exit_kind for every trade. No control / peer columns (not needed here).
The rule-19 locked block (2024-11-01..2025-02-28) is never loaded (history2y lib refuses it; no_locked asserts).

    G21SCR=$SCRATCH/szp/g python research/ops/late_entry1027/build_cache.py 3    # -> $G21SCR/sig/<month>.parquet
Educational only - not financial advice.
"""
from __future__ import annotations

import json
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research" / "bdi" / "gates1021" / "scripts"))
import scan  # noqa: E402
from common import SCR, chain, lib, load_mod, no_locked  # noqa: E402

ACCTS = ("primary", "testing", "testing2")


def targets() -> list[dict]:
    asg = json.loads((ROOT / "docs/live/assignments.json").read_text())["accounts"]
    want = {s for a in ACCTS for s in asg[a]}
    us = scan.unique_setups()
    out = []
    for r in us.to_dict("records"):
        hit = sorted(set(r["names"].split(",")) & want)
        if hit:
            r["ids"] = hit
            out.append(r)
    return out


def month_job(args):
    month, sts = args
    t0 = time.time()
    f = lib.load_month(month, context=True)          # context columns (spy_fo, qqq_fo, breadth ...) as live
    f["symbol"] = f["symbol"].astype(str)
    no_locked(f["date"].unique())
    spy_prev = pd.read_parquet(SCR / "spy_prev.parquet").set_index("date")["spy_prev"]
    f = f.merge(scan.context_extra(month, spy_prev), on=["date", "tod"], how="left")
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    tod = f["tod"].to_numpy()
    adv = f["adv20"].fillna(0).to_numpy()
    atr_ok = f["atr_d"].to_numpy(float) > 0
    rows = []
    for s in sts:
        try:
            m = load_mod(s["setup"], s["module"])
            lo, hi = s["window"]
            with np.errstate(invalid="ignore", divide="ignore"):
                mk = np.asarray(m.mask(f), bool)
        except Exception as e:  # noqa: BLE001
            rows.append(pd.DataFrame({"key": [s["setup"]], "error": [repr(e)[:200]]}))
            continue
        side, geom = s["side"], s["geom"]
        ok = mk & (tod >= max(950, lo)) & (tod <= min(1500, hi)) & (adv >= s["min_adv"]) & atr_ok \
            & np.isfinite(f[f"r_{side}_{geom}"].to_numpy(float))
        hit = np.flatnonzero(ok)
        if not len(hit):
            continue
        pos = chain(f["symbol"].to_numpy()[hit], f["date"].to_numpy()[hit], tod[hit], s["refire"], s["cooldown"])
        idx = hit[pos]
        et, kd = scan.exit_bars(f, idx, side, geom)
        out = pd.DataFrame({"key": s["setup"], "symbol": f["symbol"].to_numpy()[idx], "date": f["date"].to_numpy()[idx],
                            "tod": tod[idx], "r": scan.prod_r_tier(f, idx, side, geom),
                            "win": f[f"win_{side}_{geom}"].to_numpy(float)[idx], "exit_tod": et, "exit_kind": kd})
        rows.append(out)
    res = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    res.to_parquet(SCR / "sig" / f"{month}.parquet")
    return month, len(res), round(time.time() - t0, 1)


def main():
    (SCR / "sig").mkdir(parents=True, exist_ok=True)
    sts = targets()
    d = lib.daily()                                   # prior-day SPY return, as scan.main (NaN after a data gap)
    spy = d[d["symbol"] == "SPY"].sort_values("date")
    dd = pd.to_datetime(spy["date"])
    prev = spy["close"].pct_change() * 100
    prev[(dd.diff().dt.days > 5).to_numpy()] = np.nan
    pd.DataFrame({"date": spy["date"].to_numpy(), "spy_prev": prev.to_numpy()}).to_parquet(SCR / "spy_prev.parquet")
    pd.DataFrame([{k: (",".join(v) if isinstance(v, list) else v) for k, v in r.items()} for r in sts]).to_csv(
        SCR / "setups.csv", index=False)
    print(len(sts), "unique setups,", sum(len(r["ids"]) for r in sts), "ids", flush=True)
    with Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 2) as p:
        for r in p.imap_unordered(month_job, [(m, sts) for m in lib.months()]):
            print(r, flush=True)


if __name__ == "__main__":
    main()
