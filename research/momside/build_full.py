"""MOMSIDE Amendment 2 input (Lead lead-20261114-1300-1): the FULL-DAY 2-year lab lists (research/history2y/data/bt_lab1104,
all entry times, locked block never read) with gross (bt_all's cost formula inverted, as compassbf/retag.py; exit-cost term
at the entry price, error < 0.001R) and spy_move (SPY % move entry bar close -> exit bar close, 1-min SIP cache, block
filtered out), code copied from compassbf/retag.py minus its tod >= 12:00 filter and compass tags. Prints counts and missing
rates only (no outcome statistic is read before the score). Output: data/trades_full.parquet (git-ignored).
    python build_full.py          Educational only - not financial advice."""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.dataset as pds
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
import lib
from mcf.research.gates import GEOMK, tod_cost_mult
HERE = Path(__file__).resolve().parent
NY = "America/New_York"; TL0, TL1 = pd.Timestamp("2024-11-01", tz=NY), pd.Timestamp("2025-03-01", tz=NY)
SL, BP, SX = 0.01, 1e-4, 0.02
T = pd.concat(pd.read_parquet(p) for p in sorted((ROOT / "research/history2y/data/bt_lab1104").glob("sig_*.parquet")))
T["date"] = pd.to_datetime(T.date).dt.date.astype(str); T["tod"] = T.tod.astype(int); T["xtod"] = T.xtod.astype(int)
T = T.reset_index(drop=True)
assert not ((T.date >= "2024-11-01") & (T.date <= "2025-02-28")).any()
parts = []
for m in sorted(pd.to_datetime(T.date).dt.strftime("%Y-%m").unique()):
    f = lib.load_month(m, columns=["symbol", "date", "tod", "close", "atr_d", "gap"])
    f["date"] = f.date.astype(str); f["tod"] = f.tod.astype(int); f["symbol"] = f.symbol.astype(str)
    sub = T[pd.to_datetime(T.date).dt.strftime("%Y-%m") == m].reset_index()
    sub["symbol"] = sub.symbol.astype(str)
    parts.append(sub.merge(f.drop_duplicates(["symbol", "date", "tod"]), on=["symbol", "date", "tod"], how="left"))
J = pd.concat(parts).set_index("index").sort_index()
assert len(J) == len(T)
e = J.close.to_numpy(float); R = .25 * J.atr_d.to_numpy(float); dn = J.geom.map(lambda g: GEOMK[g][1]).to_numpy(float)
tier = np.where((J.gap.abs().to_numpy(float) >= 20) | (e < 5), 3.0, 1.0); kd = J.kind.to_numpy()
cost = (SL + e * BP) * tod_cost_mult(J.tod.to_numpy()) + np.where(kd == 2, 0.0, SL + e * BP) + np.where(kd == 1, SX, 0.0)
T["gross"] = (T.r.to_numpy() * dn + tier * cost / R) / dn
p = ROOT / "data/cache_hist/1Min/SPY.parquet"; ix = "__index_level_0__"
s = pds.dataset(str(p), format="parquet").to_table(filter=(pds.field(ix) < TL0) | (pds.field(ix) >= TL1)).to_pandas()
if ix in s.columns: s = s.set_index(ix)
s.index = pd.DatetimeIndex(s.index).tz_convert(NY); s = s[~s.index.duplicated(keep="last")]
key = pd.Series(s.close.values, index=list(zip(s.index.strftime("%Y-%m-%d"), s.index.hour * 100 + s.index.minute)))
def last_min(t):
    m = t // 100 * 60 + t % 100 - 1
    return m // 60 * 100 + m % 60
a = key.reindex(list(zip(T.date, T.tod.map(last_min)))).to_numpy(); b = key.reindex(list(zip(T.date, T.xtod.map(last_min)))).to_numpy()
T["spy_move"] = (b / a - 1) * 100
(HERE / "data").mkdir(exist_ok=True)
T[["setup", "side", "geom", "symbol", "date", "tod", "xtod", "kind", "r", "gross", "spy_move"]].to_parquet(HERE / "data/trades_full.parquet", index=False)
print(f"trades_full: {len(T)} trades, {T.setup.nunique()} setups, {T.date.nunique()} days, entries before 12:00 "
      f"{(T.tod < 1200).mean():.1%}; gross missing {np.isnan(T.gross).mean():.2%}; spy_move missing {np.isnan(T.spy_move).mean():.2%}. "
      "No outcome statistic printed. Educational only - not financial advice.")
