"""Late decision bars (bar close 15:05..15:30) for the entry-cutoff study (NOTES.md 0.1). One process.

Same code path as mcf/research/setup_lab.build (heat_frame + extra_features + _outcomes_asym, R = 0.25 x daily ATR,
exits by the 15:55 bar close) and research/history2y/build_frames.daily_table (point-in-time adv20); only the
decision-bar filter differs (<= 15:30 instead of <= 15:00). Locked-block rows (2024-11-01..2025-02-28) are dropped at
load, before any computation. Also writes the RW6G1 VWAP +2 SD band guard for the late bars (module's own code).

    python research/bdi/cutoff/build_late.py                 # all symbols -> data/late/part-*.parquet
    python research/bdi/cutoff/build_late.py --check 10      # identity check vs the stored frames (rows <= 15:00)
Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research/history2y")]
from build_frames import daily_table  # noqa: E402
from mcf.data.bars import resample  # noqa: E402
from mcf.data.store import BarStore  # noqa: E402
from mcf.research.heat import heat_frame  # noqa: E402
from mcf.research.setup_lab import GEOMS, _outcomes_asym, extra_features  # noqa: E402

CACHE = ROOT / "data" / "cache_hist"
LOCKED = ("2024-11-01", "2025-02-28")
FIRST = "2024-10-01"
OUT = HERE / "data" / "late"
HI = 1530

_spec = importlib.util.spec_from_file_location("rw6g1fd", ROOT / "research/bdi/fullday/RW6G1-ns2-up3-vwap2sd-short-FD.py")
RW6G1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(RW6G1)


def frame(sym: str, store: BarStore, lo: int = 950, hi: int = HI):
    """Lab rows with bar close lo..hi for one symbol (setup_lab.build body with the tod filter widened), + guard."""
    m1 = store.load(sym)
    if m1.empty:
        return None, None
    d = m1.index.strftime("%Y-%m-%d")
    m1 = m1[(d < LOCKED[0]) | (d > LOCKED[1])]           # rule 19: locked rows never enter a computation
    d5 = resample(m1, "5min")
    if len(d5) < 300:
        return None, None
    f = heat_frame(d5)
    f = f.join(extra_features(d5, f))
    for g, (up, dn) in GEOMS.items():
        o = _outcomes_asym(f, 0.25, 0.01, up, dn)
        for k, arr in o.items():
            f[f"{k}_{g}"] = arr
    f["symbol"] = sym
    f = f[(f.tod >= lo) & (f.tod <= hi) & f.atr_d.notna() & f.rsi.notna()]
    num = f.select_dtypes("number").columns
    f = f.astype({k: "float32" for k in num if k != "tod"})
    f["date"] = f.index.date
    x = f.reset_index(names="ts")
    dd = daily_table(m1, sym)
    x = x.merge(dd[["date", "adv20"]], on="date", how="left")
    x["adv20"] = x["adv20"].astype("float32")
    x = x[x["date"].astype(str) >= FIRST]
    # RW6G1 band guard on full-day 5-minute bars (as research/bdi/timeofday/build_open.py)
    b5 = d5.copy()
    b5["symbol"], b5["date"] = sym, b5.index.date
    blk = RW6G1.vwap_band_block(b5)
    end = b5.index + pd.Timedelta(minutes=5)
    tod = np.asarray(end.hour * 100 + end.minute)
    sel = blk & (tod >= 1505) & (tod <= hi)
    block = pd.DataFrame({"symbol": sym, "date": b5["date"].to_numpy()[sel].astype(str), "tod": tod[sel]})
    return x.reset_index(drop=True), block


def build(chunk: int = 40):
    OUT.mkdir(parents=True, exist_ok=True)
    (HERE / "data" / "block").mkdir(parents=True, exist_ok=True)
    store = BarStore(CACHE)
    syms = store.symbols()
    t0, rows = time.time(), 0
    for k in range(0, len(syms), chunk):
        p = OUT / f"part-{k // chunk:03d}.parquet"
        if p.exists():
            continue
        xs, bs = [], []
        for s in syms[k:k + chunk]:
            x, b = frame(s, store)
            if x is None:
                continue
            xs.append(x[x["tod"] >= 1505])
            bs.append(b)
        if xs:
            x = pd.concat(xs, ignore_index=True)
            x["date"] = x["date"].astype(str)
            pd.concat(bs, ignore_index=True).to_parquet(HERE / "data" / "block" / p.name, index=False)
            x.to_parquet(p, index=False, compression="zstd")
            rows += len(x)
        print(f"chunk {k // chunk}: {rows} late rows ({time.time() - t0:.0f}s)", flush=True)
    print("done", flush=True)


def check(n: int, seed: int = 20261011):
    """Rows <= 15:00 from this builder vs the stored history2y frames (months outside the warm-up)."""
    import pyarrow.dataset as pads

    store = BarStore(CACHE)
    rng = np.random.default_rng(seed)
    syms = list(rng.choice(store.symbols(), n, replace=False)) + ["AAPL", "TSLA"]
    months = ["2024-10", "2025-06", "2025-12", "2026-05", "2026-09"]
    out = []
    for s in syms:
        x, _ = frame(s, store, hi=1500)
        if x is None:
            out.append({"symbol": s, "skipped": True})
            continue
        x["date"] = x["date"].astype(str)
        for mo in months:
            p = ROOT / "research/history2y/data/frames" / f"month={mo}"
            ref = pads.dataset(str(p), format="parquet").to_table(filter=pads.field("symbol") == s).to_pandas()
            ref["date"] = pd.to_datetime(ref["date"]).dt.date.astype(str)
            mine = x[x["date"].str.startswith(mo)]
            ref = ref.sort_values(["date", "tod"]).reset_index(drop=True)
            mine = mine.sort_values(["date", "tod"]).reset_index(drop=True)
            r = {"symbol": s, "month": mo, "rows_ref": len(ref), "rows_new": len(mine)}
            if len(ref) == len(mine) and len(ref):
                bad = []
                for c in ref.columns:
                    if c in ("symbol", "date", "ts"):
                        same = (ref[c].astype(str).to_numpy() == mine[c].astype(str).to_numpy()).all()
                    else:
                        a, b = ref[c].to_numpy(float), mine[c].to_numpy(float)
                        same = np.allclose(a, b, rtol=0, atol=0, equal_nan=True)
                    if not same:
                        bad.append(c)
                r["mismatch_cols"] = bad
            out.append(r)
            print(r, flush=True)
    (HERE / "identity_check.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", type=int, default=0)
    ap.add_argument("--chunk", type=int, default=40)
    a = ap.parse_args()
    check(a.check) if a.check else build(a.chunk)
