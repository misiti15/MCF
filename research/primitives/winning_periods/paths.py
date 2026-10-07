"""Step 1: per-trade 1-minute mark-to-market paths, time-to-MFE, and the portfolio's intraday P/L path per day.
Input: trades_live_setups.csv (production Backtester, config/default.yaml, sessions 2026-07-15..09-15).
Output: trades_enriched.csv, minute_paths.npz (per trade: unrealised $ per minute 09:30..16:00), day_paths.csv.
Educational only - not financial advice."""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from mcf.backtest.engine import Costs, is_extended  # noqa: F401
from mcf.config import load_config
from mcf.data.store import BarStore

OUT = "research/primitives/winning_periods/"
cfg = load_config()
store = BarStore(cfg["data"]["cache_dir"])
import glob
tr = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(OUT + "trades_live_setups_*.csv"))], ignore_index=True)
tr.to_csv(OUT + "trades_live_setups.csv", index=False)
for c in ("signal_time", "entry_time", "exit_time"):
    tr[c] = pd.to_datetime(tr[c], utc=True).dt.tz_convert("America/New_York")
tr["date"] = pd.to_datetime(tr["date"]).dt.date
NMIN = 391  # minute index 0 = 09:30 ... 390 = 16:00
cost = Costs.from_cfg(cfg["costs"])
cost_x = Costs.from_cfg({**cfg["costs"], "slippage_per_share": cfg["costs"]["extended_slippage_per_share"]})
# extended tier: entry slippage tells us (fill - raw open) ~ 3c; recover from entry vs bar open below


def mi(ts):
    return (ts.hour * 60 + ts.minute) - (9 * 60 + 30)


mark = np.full((len(tr), NMIN), np.nan)       # unrealised $ while open (exit-cost adjusted), realised after exit
favm = np.full((len(tr), NMIN), np.nan)
ttm, mfe_chk, ext_flag = np.full(len(tr), np.nan), np.full(len(tr), np.nan), np.zeros(len(tr), bool)
for sym, g in tr.groupby("symbol"):
    bars = store.load(sym, start="2026-07-15", end="2026-09-16")
    if bars.empty:
        continue
    bdate = bars.index.date
    for i, row in g.iterrows():
        b = bars[bdate == row.date]
        if b.empty:
            continue
        side, sh, ent = row.side, row.shares, row.entry
        m0, m1 = mi(row.entry_time), mi(row.exit_time)
        bm = np.array([mi(t) for t in b.index])
        c = b["close"].to_numpy()
        h, l = b["high"].to_numpy(), b["low"].to_numpy()
        # did the engine use extended costs? entry vs raw open of the entry bar
        eb = b[bm == m0]
        if len(eb):
            ext_flag[i] = side * (ent - eb["open"].iloc[0]) > 0.025 + 1e-4 * ent
        cs = cost_x if ext_flag[i] else cost
        # minute k close -> marked P/L if closed at market at k (exit cost in)
        risk = abs(ent - row.stop)
        best, best_k = -np.inf, m0
        for k in range(NMIN):
            if k < m0:
                continue
            if k >= m1:
                mark[i, k] = row.pnl
                continue
            sel = np.flatnonzero(bm == k)
            if len(sel):
                px = c[sel[0]]
                fav = (h if side == 1 else l)[sel[0]]
                f = side * (fav - ent) / risk
                favm[i, k] = f
                if f > best:
                    best, best_k = f, k
                mark[i, k] = side * (cs.exit(px, side, "time") - ent) * sh
            else:
                mark[i, k] = mark[i, k - 1] if k > m0 and np.isfinite(mark[i, k - 1]) else 0.0
        ttm[i] = best_k - m0
        mfe_chk[i] = best
tr["time_to_mfe_min"] = ttm
tr["hold_min"] = [(mi(b) - mi(a)) for a, b in zip(tr.entry_time, tr.exit_time)]
tr["extended"] = ext_flag
tr["entry_hhmm"] = tr.entry_time.dt.strftime("%H:%M")
tr["exit_hhmm"] = tr.exit_time.dt.strftime("%H:%M")
tr.to_csv(OUT + "trades_enriched.csv", index=False)
np.save(OUT + "minute_marks.npy", mark.astype(np.float32))
np.save(OUT + "minute_fav_r.npy", favm.astype(np.float32))

rows = []
for d, g in tr.groupby("date"):
    p = np.nansum(mark[g.index], axis=0)
    for k in range(0, NMIN):
        rows.append((d, k, float(p[k])))
dp = pd.DataFrame(rows, columns=["date", "minute", "pnl"])
dp.to_csv(OUT + "day_paths.csv", index=False)
print("done", len(tr), "trades", dp.date.nunique(), "days")
