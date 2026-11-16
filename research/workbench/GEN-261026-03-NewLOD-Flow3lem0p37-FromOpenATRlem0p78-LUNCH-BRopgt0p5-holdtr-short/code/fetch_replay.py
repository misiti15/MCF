"""Mechanic GEN-261026-03: replay data for sessions 2026-10-26..11-13 (the setup's live window: Gen 10-26..11-11, Testing D
11-12..). Read-only SIP GETs (mcf.replay.store._fetch_bars):
 1. daily bars for the universe file's adv >= $20M names -> adv20 / ATR(14) per session (as live priors);
 2. 5-minute bars for the same names -> breadth_open / breadth per 5-minute bucket (lab_context._breadth rules: close vs
    own day open / own session VWAP, label = bucket start; frame tod = bucket close);
 3. 1-minute bars (10-14..11-13) for names with adv20 >= $100M that dropped >= 0.4 daily ATR below their open on some replay
    session (a new low >= 0.45 ATR under the open is needed by every variant) -> lab frames as live
    (mcf.report.engine.lab_frame + apply_daily), arena indicators, candidate rows in the same box as cand2y.
Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from common import OUT, IND, BOX
from mcf.replay.store import _fetch_bars
from mcf.report import engine as E
from mcf.research.arena.indicators import compute
D0, D1 = "2026-10-26", "2026-11-13"
step = sys.argv[1] if len(sys.argv) > 1 else "all"
u = pd.read_csv(E.__file__.rsplit("/mcf/", 1)[0] + "/data/universe.csv")
U = sorted(set(u[u.adv >= 20e6].symbol.astype(str)) | {"SPY", "QQQ"})
if step in ("all", "daily"):
    dl = _fetch_bars(U, "2026-08-01T00:00:00Z", "2026-11-14T00:00:00Z", "1Day")
    dl.to_parquet(OUT + "rep_daily.parquet"); print("daily", len(dl), flush=True)
if step in ("all", "m5"):
    m5 = _fetch_bars(U, f"{D0}T13:00:00Z", f"{D1}T21:05:00Z", "5Min")
    m5.to_parquet(OUT + "rep_5min.parquet"); print("5min", len(m5), flush=True)
if step in ("all", "m1"):
    dl = pd.read_parquet(OUT + "rep_daily.parquet")
    dl["d"] = pd.DatetimeIndex(dl.ts).tz_convert(E.TZ).date.astype(str)
    dl = dl.sort_values(["symbol", "d"])
    g = dl.groupby("symbol")
    pc = g.close.shift(1)
    tr = pd.concat([dl.high - dl.low, (dl.high - pc).abs(), (dl.low - pc).abs()], axis=1).max(axis=1)
    dl["atr_p"] = tr.groupby(dl.symbol).transform(lambda s: s.rolling(14).mean().shift(1))
    dl["adv_p"] = (dl.close * dl.volume).groupby(dl.symbol).transform(lambda s: s.rolling(20).mean().shift(1))
    w = dl[(dl.d >= D0) & (dl.d <= D1) & (dl.adv_p >= BOX["adv"]) & ((dl.open - dl.low) >= 0.4 * dl.atr_p)]
    syms = sorted(set(w.symbol) | {"SPY", "QQQ"}); print("m1 symbols", len(syms), "symbol-days", len(w), flush=True)
    m1 = _fetch_bars(syms, "2026-10-14T13:00:00Z", f"{D1}T21:05:00Z", "1Min")
    m1.to_parquet(OUT + "rep_1min_raw.parquet"); print("1min", len(m1), flush=True)
