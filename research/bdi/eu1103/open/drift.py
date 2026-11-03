"""eu1103/open (1): what a 1-2 minute decision delay costs. From the 1-minute SIP cache (pyarrow filter drops the locked
block at read time): price at the decision bar close vs 1 and 2 minutes later, in R = 0.25 x daily ATR.
  (a) |move| at each mark over all trades' symbol-days (noise a delay adds), and
  (b) the SIGNED move in the trade's direction for the scored trades (Part 2 early + baseline, Part 3 O1/O3):
      negative = the live runner, acting ~60 s after the close (latency.py), pays it on entry.
    python drift.py <scratch>
Educational only - not financial advice."""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pds

ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT / "research/history2y")]
import lib  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
S = Path(sys.argv[1])
TZ = "America/New_York"
LK0, LK1 = pd.Timestamp("2024-11-01", tz=TZ), pd.Timestamp("2025-03-01", tz=TZ)
CACHE = ROOT / "data/cache_hist/1Min"

rs = pd.read_parquet(S / "rescore_trades.parquet")
rs["side"] = np.where(rs.setup.isin(["CWT14-failbrk-pdl-p05-long"]), 1, -1)
rs["group"] = rs.setup + "@" + rs.start.astype(str) + np.where(rs.tod < 950, " early", " >=0950")
rs = rs[(rs.start == 950) | (rs.tod < 950)]
rv = pd.read_parquet(S / "rev_trades.parquet")
rv = rv[rv.config.isin(["O1-dip-upmorning-k20-long", "O3-spike-dnmorning-k20-short"])]
rv = rv.assign(tod=955, side=np.where(rv.side == "long", 1, -1), group=rv.config)
T = pd.concat([rs[["date", "symbol", "tod", "side", "group"]], rv[["date", "symbol", "tod", "side", "group"]]],
              ignore_index=True)
T["date"] = pd.to_datetime(T["date"]).dt.date
dly = lib.daily()[["symbol", "date", "high", "low", "close"]]
out = []
for sym, g in T.groupby("symbol"):
    ix = "__index_level_0__"
    tb = pds.dataset(str(CACHE / f"{sym}.parquet"), format="parquet").to_table(
        filter=(pds.field(ix) < LK0) | (pds.field(ix) >= LK1), columns=[ix, "close"]).to_pandas()
    s = (tb.set_index(ix) if ix in tb.columns else tb)["close"]
    s = s[~s.index.duplicated()]
    for r in g.itertuples():
        hh, mm = divmod(int(r.tod), 100)
        t0 = pd.Timestamp(f"{r.date} {hh:02d}:{mm:02d}", tz=TZ) - pd.Timedelta(minutes=1)   # last 1-min bar of the 5-min bar
        try:
            p0, p1, p2 = s.loc[t0], s.loc[t0 + pd.Timedelta(minutes=1)], s.loc[t0 + pd.Timedelta(minutes=2)]
        except KeyError:
            continue
        out.append((r.date, sym, r.tod, r.side, r.group, p0, p1, p2))
x = pd.DataFrame(out, columns=["date", "symbol", "tod", "side", "group", "p0", "p1", "p2"])
# daily ATR(14) from the daily table (prior days), as the frames' atr_d
d = dly.sort_values(["symbol", "date"])
pc = d.groupby("symbol").close.shift(1)
tr = np.maximum(d.high - d.low, np.maximum((d.high - pc).abs(), (d.low - pc).abs()))
d["atr"] = tr.groupby(d.symbol).transform(lambda v: v.rolling(14, min_periods=10).mean().shift(1))
x = x.merge(d[["symbol", "date", "atr"]], on=["symbol", "date"], how="left")
R = 0.25 * x.atr
x["d1"] = x.side * (x.p1 - x.p0) / R      # + = price moved our way in the next minute (a delay HELPS)
x["d2"] = x.side * (x.p2 - x.p0) / R
x["a1"] = (x.p1 - x.p0).abs() / R
x["xcost"] = np.where(x.tod < 950, 0.7, 0.0) * (0.01 + x.p0 * 1e-4) / R   # 2.1x vs 1.4x entry multiplier, in R
print("Educational only - not financial advice.")
print("signed move in the trade's direction 1 and 2 minutes after the decision bar close (R); negative = a delay costs")
g = x.groupby("group").agg(n=("d1", "size"), d1_mean=("d1", "mean"), d1_t=("d1", lambda v: v.mean() / v.std() * np.sqrt(len(v))),
                           d2_mean=("d2", "mean"), abs1_med=("a1", "median"), abs1_mean=("a1", "mean"),
                           extra_cost_vs_0950=("xcost", "mean"))
print(g.round(4).to_string())
x.to_parquet(S / "drift.parquet", index=False)
