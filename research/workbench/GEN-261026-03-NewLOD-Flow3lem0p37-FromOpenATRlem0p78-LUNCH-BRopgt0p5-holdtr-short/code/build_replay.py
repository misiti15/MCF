"""Mechanic GEN-261026-03: replay lab frames (sessions 2026-10-26..11-13) from the fetched SIP bars: lab_frame + apply_daily
as live, arena indicators, breadth_open / breadth from the 5-minute universe bars (lab_context rules), SPY/QQQ since 09:50,
adv20 from daily bars; candidate rows in the cand2y box. Educational only - not financial advice."""
import numpy as np, pandas as pd
from datetime import timedelta
from multiprocessing import Pool
from common import OUT, IND, BOX
from mcf.report import engine as E
from mcf.research.arena.indicators import compute
D0, D1 = "2026-10-26", "2026-11-13"

def breadth():
    m5 = pd.read_parquet(OUT + "rep_5min.parquet")
    m5["ts"] = pd.DatetimeIndex(m5.ts).tz_convert(E.TZ)
    hm = m5.ts.dt.hour * 100 + m5.ts.dt.minute
    d = m5[(hm >= 930) & (hm < 1600)].sort_values(["symbol", "ts"]).copy()
    d["day"] = d.ts.dt.strftime("%Y-%m-%d")
    key = [d.symbol, d.day]
    typ = (d.high + d.low + d.close) / 3
    cv = d.volume.groupby(key).cumsum(); vw = (typ * d.volume).groupby(key).cumsum() / cv.where(cv != 0)
    d["above"] = ((d.close - vw) > 0).astype(float)
    first = d.groupby(key).ts.transform("min")
    d["day_open"] = d.open.where(d.ts == first).groupby(key).transform("max")
    d = d[first.dt.hour * 100 + first.dt.minute == 930]   # day open = the 09:30 bar open
    d["above_open"] = (d.close > d.day_open).astype(float)
    end = d.ts + pd.Timedelta(minutes=5)
    d["tod"] = end.dt.hour * 100 + end.dt.minute
    b = d.groupby(["day", "tod"]).agg(breadth=("above", "mean"), breadth_open=("above_open", "mean"), nb=("above", "size")).reset_index()
    return b.rename(columns={"day": "date"})

def one(a):
    """lab_frame once over the symbol's 1-minute history 10-14..11-13 (multi-day lookbacks see >= 8 prior sessions, as the
    live 10-day fetch), then apply_daily per session from daily bars strictly before it."""
    sym, g, dd, days = a
    try:
        f = E.lab_frame(g)
    except Exception:
        return None
    out = []
    for day in days:
        d = pd.Timestamp(day).date()
        if not (f.index.date == d).any(): continue
        prior = dd[dd.index < d]
        if len(prior) < 15: continue
        f = E.apply_daily(f, prior, day)
    f = f.copy(); f["symbol"] = sym; f["date"] = f.index.strftime("%Y-%m-%d")
    # live sets atr_d = the daily ATR BEFORE extra_features (setups.py); re-derive the ATR-scaled extra features from it
    a = f["atr_d"].replace(0, np.nan); dk = f.index.date
    hod, lod = f["high"].groupby(dk).cummax(), f["low"].groupby(dk).cummin()
    f["dist_hod_atr"] = (hod - f["close"]) / a; f["dist_lod_atr"] = (f["close"] - lod) / a
    adv = {day: float((dd[dd.index < pd.Timestamp(day).date()].close * dd[dd.index < pd.Timestamp(day).date()].volume).tail(20).mean()) for day in days}
    f["adv20"] = f.date.map(adv)
    F = f.reset_index(drop=True)
    x = compute(F, names=IND, context=False)
    F = pd.concat([F[["symbol", "date", "tod", "close", "high", "low", "atr_d", "adv20", "gap"]], x], axis=1)
    return F[F.date >= D0]

if __name__ == "__main__":
    import os
    B = pd.read_parquet(OUT + 'rep_breadth.parquet') if os.path.exists(OUT + 'rep_breadth.parquet') else breadth(); B.to_parquet(OUT + "rep_breadth.parquet"); print("breadth", len(B), B.nb.median(), flush=True)
    m1 = pd.read_parquet(OUT + "rep_1min_raw.parquet")
    m1 = m1.set_index(pd.DatetimeIndex(m1.ts).tz_convert(E.TZ))
    dl = pd.read_parquet(OUT + "rep_daily.parquet"); dl["d"] = pd.DatetimeIndex(dl.ts).tz_convert(E.TZ).date
    days = sorted({x for x in m1.index.strftime("%Y-%m-%d") if D0 <= x <= D1})
    jobs = []
    for sym, g in m1.groupby("symbol"):
        g = E._rth(g[["open", "high", "low", "close", "volume"]].astype(float).sort_index())
        dd = dl[dl.symbol == sym].set_index("d")[["open", "high", "low", "close", "volume"]].astype(float).sort_index()
        jobs.append((sym, g, dd, days))
    with Pool(3) as p:
        res = p.map(one, jobs, chunksize=4)
    F = pd.concat([r for r in res if r is not None], ignore_index=True)
    F = F.merge(B[["date", "tod", "breadth", "breadth_open"]], on=["date", "tod"], how="left")
    ix = {}
    for e in ("SPY", "QQQ"):
        g = F[F.symbol == e][["date", "tod", "close"]]; b = g[g.tod == 950].set_index("date").close
        ix[e] = g.assign(v=(g.close / g.date.map(b) - 1) * 100).set_index(["date", "tod"]).v
    k = pd.MultiIndex.from_arrays([F.date, F.tod])
    F["spy950"] = ix["SPY"].reindex(k).to_numpy(); F["qqq950"] = ix["QQQ"].reindex(k).to_numpy()
    F["spy_fo"] = np.nan; F["blackout"] = False
    F.to_parquet(OUT + "rep_frames_all.parquet")
    keep = (F.tod >= BOX["lo"]) & (F.tod <= BOX["hi"]) & (F.adv20 >= BOX["adv"]) & (F.new_lod == 1) \
        & (F.flow3 <= BOX["flow3"]) & (F.fromOpen_atr <= BOX["fo"])
    F[keep].to_parquet(OUT + "cand_replay.parquet"); print("cand", keep.sum(), "days", days, flush=True)
