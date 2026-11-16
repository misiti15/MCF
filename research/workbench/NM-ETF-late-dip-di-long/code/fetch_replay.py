"""Mechanic NM-ETF: read-only SIP GET of 1-minute + daily bars for the module's ETFs (+SPY/QQQ), sessions 2026-10-19..11-13
(the setup's live window), lab frames built as live (mcf.report.engine.lab_frame + apply_daily), arena indicators, adv20 from
daily bars. Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from datetime import timedelta
from common import OUT, SYMS, IND
from mcf.replay.store import _fetch_bars
from mcf.report import engine as E
from mcf.research.arena.indicators import compute
syms = sorted(set(SYMS) | {"SPY", "QQQ"})
m1 = _fetch_bars(syms, "2026-10-08T13:00:00Z", "2026-11-13T21:05:00Z", "1Min")
dl = _fetch_bars(syms, "2026-08-01T00:00:00Z", "2026-11-14T00:00:00Z", "1Day")
m1.to_parquet(OUT + "replay_raw1m.parquet"); dl.to_parquet(OUT + "replay_daily.parquet")
print("fetched", len(m1), len(dl), flush=True)
m1["ts"] = pd.DatetimeIndex(m1.ts).tz_convert(E.TZ)
dl["d"] = pd.DatetimeIndex(dl.ts).tz_convert(E.TZ).date
days = sorted({d for d in m1.ts.dt.date.astype(str) if d >= "2026-10-19"})
F, M = [], []
for sym, g in m1.groupby("symbol"):
    g = E._rth(g.set_index("ts")[["open", "high", "low", "close", "volume"]].astype(float).sort_index())
    dd = dl[dl.symbol == sym].set_index("d")[["open", "high", "low", "close", "volume"]].astype(float)
    for day in days:
        d = pd.Timestamp(day).date()
        gg = g[(g.index.date <= d) & (g.index.date >= (pd.Timestamp(day) - timedelta(days=10)).date())]
        if not (gg.index.date == d).any(): continue
        prior = dd[dd.index < d]
        try:
            fr = E.apply_daily(E.lab_frame(gg), prior, day)
        except Exception as e:
            print("fail", sym, day, e); continue
        fr = fr[fr.index.date == d].copy(); fr["symbol"] = sym; fr["date"] = day
        fr["adv20"] = float((prior.close * prior.volume).tail(20).mean())
        F.append(fr)
        x = gg[gg.index.date == d].copy(); x["symbol"] = sym; x["date"] = day; M.append(x)
F = pd.concat(F); F = F.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
x = compute(F, names=IND, context=False)
F = pd.concat([F[["symbol", "date", "tod", "close", "high", "low", "atr_d", "adv20"]], x], axis=1)
ix = {}
for e in ("SPY", "QQQ"):
    g = F[F.symbol == e][["date", "tod", "close"]]; b = g[g.tod == 950].set_index("date").close
    ix[e] = g.assign(v=(g.close / g.date.map(b) - 1) * 100).set_index(["date", "tod"]).v
k = pd.MultiIndex.from_arrays([F.date, F.tod])
F["spy950"] = ix["SPY"].reindex(k).to_numpy(); F["qqq950"] = ix["QQQ"].reindex(k).to_numpy()
F.to_parquet(OUT + "replay_frames_all.parquet")
F[(F.tod >= 1300) & (F.tod <= 1500) & (F.adv20 >= 95e6) & (F.ret3 <= -0.40) & F.symbol.isin(SYMS)].to_parquet(OUT + "cand_replay.parquet")
pd.concat(M).to_parquet(OUT + "replay_1min.parquet")
print("days", days)
