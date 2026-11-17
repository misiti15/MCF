"""FREQ replay data: read-only SIP GET of 1-minute + daily bars for every symbol of every set (+SPY/QQQ), sessions
2026-10-19..11-16 (all live sessions of the setup: Testing 2 10-19..11-04, Live Lab 11-05..11-10, Primary 11-11..11-16);
lab frames built as live (mcf.report.engine.lab_frame + apply_daily), arena indicators (context=False), adv20 from daily bars.
Same code as the first Workbench pass (../code/fetch_replay.py), wider symbol list, one more session. Educational only."""
import json, numpy as np, pandas as pd
from datetime import timedelta
from multiprocessing import Pool
from mcf.replay.store import _fetch_bars
from mcf.report import engine as E
from mcf.research.arena.indicators import compute
S = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/etffreq/"
IND = ["ret3", "di_diff7", "atr_d_pct", "adx7", "vwap_atr", "day_pos", "fromOpen_atr", "rvol_day", "ret12", "ret6",
       "ret_since950_atr", "rsi7", "z12"]
sets = json.load(open(S + "sets.json"))
syms = sorted({s for k, v in sets.items() if k != "VIX" for s in v} | {"SPY", "QQQ"})

def per_sym(a):
    sym, g, dd, days = a
    g = E._rth(g.set_index("ts")[["open", "high", "low", "close", "volume"]].astype(float).sort_index())
    F, Mn = [], []
    for day in days:
        d = pd.Timestamp(day).date()
        gg = g[(g.index.date <= d) & (g.index.date >= (pd.Timestamp(day) - timedelta(days=10)).date())]
        if not (gg.index.date == d).any(): continue
        prior = dd[dd.index < d]
        try:
            fr = E.apply_daily(E.lab_frame(gg), prior, day)
        except Exception as e:
            continue
        fr = fr[fr.index.date == d].copy(); fr["symbol"] = sym; fr["date"] = day
        fr["adv20"] = float((prior.close * prior.volume).tail(20).mean())
        F.append(fr)
        x = gg[gg.index.date == d].copy(); x["symbol"] = sym; x["date"] = day; Mn.append(x)
    return (pd.concat(F) if F else None), (pd.concat(Mn) if Mn else None)

if __name__ == "__main__":
    m1 = _fetch_bars(syms, "2026-10-08T13:00:00Z", "2026-11-16T21:05:00Z", "1Min")
    dl = _fetch_bars(syms, "2026-08-01T00:00:00Z", "2026-11-17T00:00:00Z", "1Day")
    print("fetched", len(m1), len(dl), flush=True)
    m1["ts"] = pd.DatetimeIndex(m1.ts).tz_convert(E.TZ)
    dl["d"] = pd.DatetimeIndex(dl.ts).tz_convert(E.TZ).date
    days = sorted({d for d in m1.ts.dt.date.astype(str) if d >= "2026-10-19"})
    args = [(s, g, dl[dl.symbol == s].set_index("d")[["open", "high", "low", "close", "volume"]].astype(float), days)
            for s, g in m1.groupby("symbol")]
    with Pool(3) as p:
        res = p.map(per_sym, args)
    F = pd.concat([r[0] for r in res if r[0] is not None]).sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    x = compute(F, names=IND, context=False)
    F = pd.concat([F[["symbol", "date", "tod", "close", "high", "low", "atr_d", "adv20"]], x], axis=1)
    ix = {}
    for e in ("SPY", "QQQ"):
        g = F[F.symbol == e][["date", "tod", "close"]]; b = g[g.tod == 950].set_index("date").close
        ix[e] = g.assign(v=(g.close / g.date.map(b) - 1) * 100).set_index(["date", "tod"]).v
    k = pd.MultiIndex.from_arrays([F.date, F.tod])
    F["spy950"] = ix["SPY"].reindex(k).to_numpy(); F["qqq950"] = ix["QQQ"].reindex(k).to_numpy()
    F[(F.tod >= 1300) & (F.tod <= 1500) & (F.adv20 >= 30e6) & (F.ret3 <= -0.30)].to_parquet(S + "cand_replay.parquet")
    M = pd.concat([r[1] for r in res if r[1] is not None])
    M.to_parquet(S + "replay_1min.parquet")
    print("days", len(days), days[0], days[-1], "cands", flush=True)
