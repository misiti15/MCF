"""Mechanic NM-RWN5: replay lab frames (all sessions 2026-10-19..11-16) from the fetched SIP bars: lab_frame + apply_daily
as live (mcf.report.engine), adv20 from daily bars, spy_fo = SPY's fromOpen at the same 5-minute bar (the live `spy_fo`
context column), spy950 / fo950 (% since the 09:50 bar close), prev_vwap, dow; candidate rows in the cand2y BOX.
Educational only - not financial advice."""
import numpy as np, pandas as pd
from multiprocessing import Pool
from common import OUT, BOX, COLS
from mcf.report import engine as E
D0, D1 = "2026-10-19", "2026-11-16"

def one(a):
    sym, g, dd, days = a
    try:
        f = E.lab_frame(g)
    except Exception:
        return None
    for day in days:
        d = pd.Timestamp(day).date()
        if not (f.index.date == d).any(): continue
        prior = dd[dd.index < d]
        if len(prior) < 15: continue
        f = E.apply_daily(f, prior, day)
    f = f.copy(); f["symbol"] = sym; f["date"] = f.index.strftime("%Y-%m-%d")
    adv = {}
    for day in days:
        p = dd[dd.index < pd.Timestamp(day).date()].tail(20)
        adv[day] = float((p.close * p.volume).mean()) if len(p) else np.nan
    f["adv20"] = f.date.map(adv)
    F = f.reset_index(drop=True)
    F = F[F.date >= D0]
    key = F.symbol + "|" + F.date
    F["prev_vwap"] = F.groupby(key, sort=False).vwapDistPct.shift(1)
    c950 = F[F.tod == 950].set_index("date").close
    F["fo950"] = (F.close / F.date.map(c950) - 1) * 100
    if sym in ("SPY", "QQQ"):
        return F
    keep = (F.tod >= BOX["lo"]) & (F.tod <= BOX["hi"]) & (F.fromOpen < BOX["fo"])
    return F[keep]

if __name__ == "__main__":
    m1 = pd.read_parquet(OUT + "rep_1min_raw.parquet")
    m1 = m1.set_index(pd.DatetimeIndex(m1.ts).tz_convert(E.TZ))
    dl = pd.read_parquet(OUT + "rep_daily.parquet"); dl["d"] = pd.DatetimeIndex(dl.ts).tz_convert(E.TZ).date
    days = sorted({x for x in m1.index.strftime("%Y-%m-%d") if D0 <= x <= D1})
    def jobs():
        for sym, g in m1.groupby("symbol"):
            g = E._rth(g[["open", "high", "low", "close", "volume"]].astype(float).sort_index())
            dd = dl[dl.symbol == sym].set_index("d")[["open", "high", "low", "close", "volume"]].astype(float).sort_index()
            yield (sym, g, dd, days)
    with Pool(3) as p:
        res = list(p.imap(one, jobs(), chunksize=8))
    F = pd.concat([r for r in res if r is not None], ignore_index=True)
    spy = F[F.symbol == "SPY"].set_index(["date", "tod"])
    k = pd.MultiIndex.from_arrays([F.date, F.tod])
    F["spy_fo"] = spy.fromOpen.reindex(k).to_numpy()
    F["spy950"] = spy.fo950.reindex(k).to_numpy()
    F["dow"] = pd.to_datetime(F.date).dt.dayofweek
    F = F[~F.symbol.isin(["SPY", "QQQ"])]
    keep = (F.tod >= BOX["lo"]) & (F.tod <= BOX["hi"]) & (F.adv20 >= BOX["adv"]) & (F.vwapDistPct > 0) \
        & (F.prev_vwap <= 0) & (F.fromOpen < BOX["fo"])
    F = F.loc[keep, [c for c in COLS if c in F.columns]]
    F.to_parquet(OUT + "cand_replay.parquet"); print("cand", len(F), "days", days, flush=True)
