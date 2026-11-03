"""eu1103/open: rebuild the lab-frame rows for bar closes 09:35-09:50 (the lab frames start at 09:50) with the SAME
pipeline (heat_frame + extra_features + _outcomes_asym on continuous 5-minute RTH bars, mcf.research.setup_lab.build
logic, only the final tod filter differs). The 1-minute cache is read with a pyarrow filter that drops the rule-19
locked block 2024-11-01..2025-02-28 at read time (never loaded). Only TRAIN / VALID dates are written.
    python build_early.py <out dir>      -> <out>/early_<k>.parquet
Educational only - not financial advice."""
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pds

ROOT = Path("/home/user/MCF")
sys.path.insert(0, str(ROOT))
from mcf.data.bars import resample  # noqa: E402
from mcf.research.heat import heat_frame  # noqa: E402
from mcf.research.setup_lab import _outcomes_asym, extra_features  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
CACHE = ROOT / "data/cache_hist/1Min"
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
TZ = "America/New_York"
LK0, LK1 = pd.Timestamp("2024-11-01", tz=TZ), pd.Timestamp("2025-03-01", tz=TZ)
KEEP = ["close", "high", "low", "rsi", "rsi5", "heat", "buyPressure", "gap", "fromOpen", "sma20_slope_pct",
        "sma20_dist_pct", "bear_div", "dist_pdh_atr", "dist_pdl_atr", "vwapDistPct", "volumeRatio", "vol_climax",
        "atr_d", "tod", "rsiHeat", "priceActionHeat", "momentumHeat", "vwapHeat"]
GEOMS = {"t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0)}


def ok_date(d: pd.Series) -> np.ndarray:
    s = d.astype(str)
    train = ((s >= "2024-10-01") & (s <= "2024-10-31")) | ((s >= "2025-03-01") & (s <= "2025-12-31"))
    valid = ((s >= "2026-01-01") & (s <= "2026-03-31")) | ((s >= "2026-07-01") & (s <= "2026-09-15"))
    return (train | valid).to_numpy()


def one(sym):
    ix = "__index_level_0__"
    dset = pds.dataset(str(CACHE / f"{sym}.parquet"), format="parquet")
    flt = (pds.field(ix) < LK0) | (pds.field(ix) >= LK1)
    df = dset.to_table(filter=flt).to_pandas()
    if ix in df.columns:
        df = df.set_index(ix)
    if df.empty:
        return None
    assert not ((df.index >= LK0) & (df.index < LK1)).any()
    df = df[["open", "high", "low", "close", "volume"]].astype(float).sort_index()
    df = df[~df.index.duplicated(keep="last")]
    d1 = df.groupby(df.index.date)
    dv = (df["close"] * df["volume"]).groupby(df.index.date).sum()
    adv20 = dv.shift(1).rolling(20, min_periods=5).mean()
    d5 = resample(df, "5min")
    if len(d5) < 300:
        return None
    f = heat_frame(d5)
    f = f.join(extra_features(d5, f))
    for g, (up, dn) in GEOMS.items():
        o = _outcomes_asym(f, 0.25, 0.01, up, dn)
        for k, arr in o.items():
            f[f"{k}_{g}"] = arr
    f = f[(f.tod >= 935) & (f.tod <= 950) & f.atr_d.notna() & f.rsi.notna()]
    f = f[KEEP + [c for c in f.columns if c.startswith(("r_", "win_"))]].copy()
    f["date"] = f.index.date
    f = f[ok_date(pd.Series(f["date"]))]
    f["symbol"] = sym
    f["adv20"] = pd.Series(f["date"]).map(adv20).to_numpy()
    num = [c for c in f.columns if c not in ("symbol", "date", "tod")]
    return f.astype({c: "float32" for c in num}).astype({"tod": "int16"}).reset_index(drop=True)


if __name__ == "__main__":
    syms = sorted(p.stem for p in CACHE.glob("*.parquet"))
    t0, buf, k = time.time(), [], 0
    for i, s in enumerate(syms):
        p = OUT / f"early_{i // 100:02d}.parquet"
        if p.exists():
            continue
        try:
            x = one(s)
        except Exception as e:
            print("fail", s, e, flush=True)
            x = None
        if x is not None:
            buf.append(x)
        if (i + 1) % 100 == 0 or i == len(syms) - 1:
            pd.concat(buf, ignore_index=True).to_parquet(p, index=False, compression="zstd")
            buf = []
            print(i + 1, f"{time.time() - t0:.0f}s", flush=True)
