"""Mechanic NM-RWN5: replay data for every session of the setup's live window 2026-10-19..11-16 (live from 10-19 in
Testing 2, Explore 1 from 11-05, Testing D from 11-12; the parent trades Mondays only, but copies without the Monday part
trade any day, so all 21 sessions are scored). Read-only SIP GETs (mcf.replay.store._fetch_bars):
 1. daily bars for the universe file's adv >= $20M names -> adv20 / ATR(14) per session (as live priors);
 2. 1-minute bars (10-12..11-16) for names with adv20 >= $50M that traded >= 1% below their open on some replay session
    (every tested config needs fromOpen < -1%), plus SPY / QQQ.
Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from common import OUT, BOX
from mcf.replay.store import _fetch_bars
from mcf.report import engine as E
D0, D1 = "2026-10-19", "2026-11-16"
step = sys.argv[1] if len(sys.argv) > 1 else "all"
u = pd.read_csv(E.__file__.rsplit("/mcf/", 1)[0] + "/data/universe.csv")
U = sorted(set(u[u.adv >= 20e6].symbol.astype(str)) | {"SPY", "QQQ"})
if step in ("all", "daily"):
    dl = _fetch_bars(U, "2026-08-01T00:00:00Z", "2026-11-17T00:00:00Z", "1Day")
    dl.to_parquet(OUT + "rep_daily.parquet"); print("daily", len(dl), flush=True)
if step in ("all", "m1"):
    dl = pd.read_parquet(OUT + "rep_daily.parquet")
    dl["d"] = pd.DatetimeIndex(dl.ts).tz_convert(E.TZ).date.astype(str)
    dl = dl.sort_values(["symbol", "d"])
    dl["adv_p"] = (dl.close * dl.volume).groupby(dl.symbol).transform(lambda s: s.rolling(20).mean().shift(1))
    w = dl[(dl.d >= D0) & (dl.d <= D1) & (dl.adv_p >= BOX["adv"]) & ((dl.open - dl.low) / dl.open >= 0.01)]
    syms = sorted(set(w.symbol) | {"SPY", "QQQ"}); print("m1 symbols", len(syms), "symbol-days", len(w), flush=True)
    m1 = _fetch_bars(syms, "2026-10-12T13:00:00Z", f"{D1}T21:05:00Z", "1Min")
    m1 = m1[[c for c in ("symbol", "ts", "open", "high", "low", "close", "volume") if c in m1.columns or c == "ts"]] if "ts" in m1 else m1
    m1.to_parquet(OUT + "rep_1min_raw.parquet"); print("1min", len(m1), flush=True)
