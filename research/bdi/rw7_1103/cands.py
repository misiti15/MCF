"""rw7_1103 pass 1: candidate decision bars (superset of every grid config) + a 3% random control sample, from the open
two-year lab frames. Locked block never loaded (lib refuses it; asserted). Writes <out>/cand.parquet, <out>/ctrl.parquet.
Usage: python cands.py <out>   Educational only - not financial advice."""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(os.environ.get("MCF_DATA_ROOT", "/home/user/MCF"))   # checkout holding the (untracked) history data
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
COLS = ["symbol", "date", "tod", "close", "rsi", "heat", "buyPressure", "gap", "atr_d", "adv20", "fromOpen",
        "r_short_t1s1", "win_short_t1s1"]
rng = np.random.default_rng(20261103)
C, K = [], []
for m in lib.months():
    f = lib.load_month(m, columns=COLS, context=True)
    d = pd.to_datetime(f.date)
    assert not ((d >= "2024-11-01") & (d <= "2025-02-28")).any()
    f["symbol"] = f.symbol.astype(str)
    base = (f.adv20 >= 95e6) & (f.atr_d > 0) & f.tod.between(950, 1500) & np.isfinite(f.r_short_t1s1)
    # per-date top-500 rank by adv20 x ATR% (first bar of the symbol-day)
    fb = f[base].groupby(["date", "symbol"], sort=False).first().reset_index()
    fb["score"] = fb.adv20 * fb.atr_d / fb.close
    fb["rank"] = fb.groupby("date").score.rank(ascending=False, method="first")
    f = f.merge(fb[["date", "symbol", "rank"]], on=["date", "symbol"], how="left")
    base = (f.adv20 >= 95e6) & (f.atr_d > 0) & f.tod.between(950, 1500) & np.isfinite(f.r_short_t1s1)
    sup = base & (f.heat <= -16) & (f.buyPressure < -0.12) & f.rsi.between(50, 70) & (f.gap < 0)
    C.append(f[sup].copy())
    k = f[base & (rng.random(len(f)) < 0.03)].copy(); K.append(k)
    print(m, int(sup.sum()), len(k), flush=True)
pd.concat(C).reset_index(drop=True).to_parquet(OUT / "cand.parquet")
pd.concat(K).reset_index(drop=True).to_parquet(OUT / "ctrl.parquet")
