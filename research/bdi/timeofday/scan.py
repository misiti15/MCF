"""Scan the open two-year lab frames (research/history2y, locked block refused by the loader) for every setup of
NOTES.md 0.2: current-window trades, full-day trades (tod layer removed) and per-bucket trades, production costs.
Also the random-bar baseline per bucket and side (t1s1, adv20 >= 95M).

Outputs (git-ignored): data/trades.parquet, data/baseline.parquet
    python research/bdi/timeofday/scan.py
Educational only - not financial advice.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research/history2y"), str(HERE)]
from lib import load_month, months  # noqa: E402
from mcf.research import gates as G  # noqa: E402
from tod_free import FULL, prepare  # noqa: E402

DATA = HERE / "data"
BUCKETS = {"B1": (950, 1030), "B2": (1035, 1130), "B3": (1135, 1300), "B4": (1305, 1400), "B5": (1405, 1500)}


def load_block() -> pd.DataFrame:
    b = pd.concat([pd.read_parquet(p) for p in sorted((DATA / "block").glob("*.parquet"))], ignore_index=True)
    b["date"] = b["date"].astype(str)
    return b


def masks(s: dict, df: pd.DataFrame, which: str) -> list[tuple[np.ndarray, str]]:
    m = s[which]
    with np.errstate(invalid="ignore"):
        if s["kind"] == "lab":
            return [(np.asarray(m.mask(df), bool), s["side"])]
        sc = np.asarray(m.score(df), float)
        legs = []
        if s["sides"] in ("both", "long") and getattr(m, "LONG_AT", None) is not None:
            legs.append((sc >= m.LONG_AT, "long"))
        if s["sides"] in ("both", "short") and getattr(m, "SHORT_AT", None) is not None:
            legs.append((sc <= m.SHORT_AT, "short"))
        return legs


_STS = None
_BLOCK = None


def _init():
    global _STS, _BLOCK
    _STS = prepare()
    _BLOCK = load_block()
    for s in _STS:
        if s["needs_block"]:
            for w in ("orig", "free"):
                s[w].vwap_band_block = lambda df, k=2.0: df["_block"].to_numpy(bool)


def one_month(mo: str) -> str:
    out = DATA / "scan" / f"{mo}.parquet"
    if out.exists():
        return mo + " (cached)"
    sts, block = _STS, _BLOCK
    rows, base = [], []
    df = load_month(mo)
    ds = df["date"].astype(str)
    bm = block[block["date"].str.startswith(mo)]
    key = df["symbol"].astype(str) + "|" + ds + "|" + df["tod"].astype(str)
    bkey = set(bm["symbol"] + "|" + bm["date"] + "|" + bm["tod"].astype(str))
    df["_block"] = key.isin(bkey).to_numpy()
    tod, adv = df["tod"].to_numpy(), df["adv20"].fillna(0).to_numpy()
    for s in sts:
        lo, hi = s["window"]
        ok_adv = adv >= s["min_adv"]
        cur = (tod >= lo) & (tod <= hi) & ok_adv
        full = (tod >= FULL[0]) & (tod <= FULL[1]) & ok_adv
        for (mo_, side), (mf, _) in zip(masks(s, df, "orig"), masks(s, df, "free")):
            sets = [("current", mo_ & cur), ("full", mf & full)]
            sets += [(b, mf & full & (tod >= a) & (tod <= z)) for b, (a, z) in BUCKETS.items()]
            for lab, mk in sets:
                tr = G.lab_trades(df, mk, side, s["geom"])
                tr["setup"], tr["set"], tr["side"] = s["setup"], lab, side
                rows.append(tr)
    okb = adv >= 95e6
    for side in ("long", "short"):
        r = G.prod_r(df[f"r_{side}_t1s1"].to_numpy(float), df[f"win_{side}_t1s1"].to_numpy(float),
                     df["close"].to_numpy(float), df["atr_d"].to_numpy(float), "t1s1")
        ok = okb & np.isfinite(r) & (df["atr_d"].to_numpy(float) > 0)
        for b, (a, z) in BUCKETS.items():
            sel = ok & (tod >= a) & (tod <= z)
            g = pd.DataFrame({"date": df["date"].to_numpy()[sel], "r": r[sel]}).groupby("date")["r"].agg(["sum", "size"])
            g = g.reset_index()
            g["bucket"], g["side"] = b, side
            base.append(g)
    x = pd.concat(rows, ignore_index=True)
    x["symbol"] = x["symbol"].astype(str)
    x["date"] = x["date"].astype(str)
    bb = pd.concat(base, ignore_index=True)
    bb["date"] = bb["date"].astype(str)
    bb.to_parquet(DATA / "scan" / f"base-{mo}.parquet", index=False)
    x.to_parquet(out, index=False)
    return mo


def main():
    from multiprocessing import Pool
    (DATA / "scan").mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with Pool(4, initializer=_init) as pool:
        for mo in pool.imap_unordered(one_month, months()):
            print(f"{mo} ({time.time() - t0:.0f}s)", flush=True)
    x = pd.concat([pd.read_parquet(p) for p in sorted((DATA / "scan").glob("20*.parquet"))], ignore_index=True)
    x.to_parquet(DATA / "trades.parquet", index=False)
    b = pd.concat([pd.read_parquet(p) for p in sorted((DATA / "scan").glob("base-*.parquet"))], ignore_index=True)
    b.to_parquet(DATA / "baseline.parquet", index=False)


if __name__ == "__main__":
    main()
