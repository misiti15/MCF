"""FREQ parity: the WB4 module's own mask() + LabStrategy refire_select on live-built frames (lab_frame + apply_daily) of the
replay sessions vs the engine's selection (sim2.select). Educational only - not financial advice."""
import importlib.util, numpy as np, pandas as pd
from datetime import timedelta
from sim2 import *
from mcf.replay.store import _fetch_bars
from mcf.report import engine as E
from mcf.strategies.setups import refire_select
sp = importlib.util.spec_from_file_location("m", "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/wt-wb-etffreq/research/workbench/NM-ETF-late-dip-di-long/modules/NM-ETF-late-dip-di-long-WB4.py")
M = importlib.util.module_from_spec(sp); sp.loader.exec_module(M)
RC = pd.read_parquet(SC + "cand_replay.parquet")
v = {**PARENT, "di": -5.0, "ret3": -0.75, "refire": True, "cool": 1, "lots": 3, "extra": (("ret12", ">=", -1.0),)}
eng = select(RC, v); eng_keys = set(zip(eng.symbol, eng.date, eng.tod.astype(int)))
syms = sorted(set(RC[RC.symbol.isin(M.SYMBOLS) & (RC.atr_d_pct >= 3.5) & (RC.adv20 >= 95e6)].symbol))
m1 = pd.read_parquet(SC + "replay_1min.parquet"); m1 = m1[m1.symbol.isin(syms)]
dl = _fetch_bars(syms, "2026-08-01T00:00:00Z", "2026-11-17T00:00:00Z", "1Day"); dl["d"] = pd.DatetimeIndex(dl.ts).tz_convert(E.TZ).date
raw = _fetch_bars(syms, "2026-10-08T13:00:00Z", "2026-11-16T21:05:00Z", "1Min"); raw["ts"] = pd.DatetimeIndex(raw.ts).tz_convert(E.TZ)
mod_keys = set()
for s, g in raw.groupby("symbol"):
    g = E._rth(g.set_index("ts")[["open", "high", "low", "close", "volume"]].astype(float).sort_index())
    dd = dl[dl.symbol == s].set_index("d")[["open", "high", "low", "close", "volume"]].astype(float)
    for day in sorted(set(RC.date)):
        d = pd.Timestamp(day).date(); gg = g[(g.index.date <= d) & (g.index.date >= (pd.Timestamp(day) - timedelta(days=10)).date())]
        if not (gg.index.date == d).any(): continue
        prior = dd[dd.index < d]
        if float((prior.close * prior.volume).tail(20).mean()) < 95e6: continue
        fr = E.apply_daily(E.lab_frame(gg), prior, day); fr = fr[fr.index.date == d].copy(); fr["symbol"] = s
        fr = fr.reset_index(drop=True)
        hit = np.flatnonzero(M.mask(fr) & (fr.close.to_numpy() >= 5))
        for i in refire_select(hit, 1):
            mod_keys.add((s, day, int(fr.tod.iloc[i])))
print("engine", len(eng_keys), "module", len(mod_keys), "both", len(eng_keys & mod_keys))
print("engine-only", sorted(eng_keys - mod_keys)); print("module-only", sorted(mod_keys - eng_keys))
