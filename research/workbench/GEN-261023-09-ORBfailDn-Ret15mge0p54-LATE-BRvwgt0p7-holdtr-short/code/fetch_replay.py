"""Mechanic GEN-261023-09: replay data for sessions 2026-10-23..11-16 (the setup's live window: Setup Generator 10-23..11-13,
Testing E from 11-16). Read-only SIP GETs (mcf.replay.store._fetch_bars):
 1. daily bars for the universe file's adv >= $20M names -> adv20 / ATR(14) per session (as live priors);
 2. 5-minute bars for the same names -> breadth (share above own session VWAP) / breadth_open per 5-minute bucket
    (lab_context rules; frame tod = bucket close);
 3. 1-minute bars (10-09..11-16) for names with a prior 20-day avg dollar volume >= $75M on some replay session (the box)
    -> lab frames as live (mcf.report.engine.lab_frame + apply_daily), arena indicators, candidate rows in the cand2y box.
Educational only - not financial advice."""
import sys, pandas as pd
from common import OUT, BOX
from mcf.replay.store import _fetch_bars
from mcf.report import engine as E
D0, D1 = "2026-10-23", "2026-11-16"
step = sys.argv[1] if len(sys.argv) > 1 else "all"
u = pd.read_csv(E.__file__.rsplit("/mcf/", 1)[0] + "/data/universe.csv")
U = sorted(set(u[u.adv >= 20e6].symbol.astype(str)) | {"SPY", "QQQ"})
if step in ("all", "daily"):
    dl = _fetch_bars(U, "2026-08-01T00:00:00Z", "2026-11-17T00:00:00Z", "1Day")
    dl.to_parquet(OUT + "rep_daily.parquet"); print("daily", len(dl), flush=True)
if step in ("all", "m5"):
    m5 = _fetch_bars(U, f"{D0}T13:00:00Z", f"{D1}T21:05:00Z", "5Min")
    m5.to_parquet(OUT + "rep_5min.parquet"); print("5min", len(m5), flush=True)
if step in ("all", "m1"):
    dl = pd.read_parquet(OUT + "rep_daily.parquet")
    dl["d"] = pd.DatetimeIndex(dl.ts).tz_convert(E.TZ).date.astype(str)
    dl = dl.sort_values(["symbol", "d"])
    dl["adv_p"] = (dl.close * dl.volume).groupby(dl.symbol).transform(lambda s: s.rolling(20).mean().shift(1))
    w = dl[(dl.d >= D0) & (dl.d <= D1) & (dl.adv_p >= BOX["adv"])]
    syms = sorted(set(w.symbol) | {"SPY", "QQQ"}); print("m1 symbols", len(syms), flush=True)
    parts = []
    for i in range(0, len(syms), 100):
        parts.append(_fetch_bars(syms[i:i + 100], "2026-10-09T13:00:00Z", f"{D1}T21:05:00Z", "1Min")); print(i, flush=True)
    m1 = pd.concat(parts, ignore_index=True)
    m1.to_parquet(OUT + "rep_1min_raw.parquet"); print("1min", len(m1), flush=True)
