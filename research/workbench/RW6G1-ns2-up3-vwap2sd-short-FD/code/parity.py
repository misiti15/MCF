"""Module parity: WB modules' mask (live code) vs the bench mask on the replay frames (volume from the 1-min SIP bars)."""
import sys, importlib.util, numpy as np, pandas as pd
sys.path.insert(0, "code"); import sim3, band
W = sys.argv[1]
RF = pd.read_parquet("replay_frames.parquet"); RF["date"] = RF.date.astype(str); RF["tod"] = RF.tod.astype(int)
R1 = pd.read_parquet("replay_1min.parquet")
V = []
for (s, d), g in R1.groupby(["symbol", "date"]):
    x = g.sort_index().volume.resample("5min", label="left", closed="left").sum()
    e = x.index + pd.Timedelta(minutes=5); V.append(pd.DataFrame({"symbol": s, "date": d, "tod": e.hour * 100 + e.minute, "volume": x.values}))
RF = RF.merge(pd.concat(V), on=["symbol", "date", "tod"], how="left").sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
exec(open("code/load.py").read().split("C = pd.read_parquet")[0].split("RF = pd.read_parquet")[0])
key = (RF.symbol + "|" + RF.date).values
p = np.r_[np.nan, RF.sma50_dist_pct.values[:-1]]; p[np.r_[True, key[1:] != key[:-1]]] = np.nan; RF["p_sma50"] = p
RF["dist_hod_atr"] = (RF.groupby(["symbol", "date"]).high.cummax() - RF.close) / RF.atr_d
BT = [band.table(g.sort_index(), s, d) for (s, d), g in R1.groupby(["symbol", "date"])]
RF = RF.merge(pd.concat(BT), on=["symbol", "date", "tod"], how="left").merge(SPY, on=["date", "tod"], how="left")
cfgs = {"PARENT": (f"/home/user/MCF/research/bdi/fullday/RW6G1-ns2-up3-vwap2sd-short-FD.py", sim3.BASE),
        "WB1": (f"{W}/modules/RW6G1-ns2-up3-vwap2sd-short-FD-WB1.py", dict(sim3.BASE, w=(1100, 1500))),
        "WB2": (f"{W}/modules/RW6G1-ns2-up3-vwap2sd-short-FD-WB2.py", dict(sim3.BASE, z5min=0.5)),
        "WB3": (f"{W}/modules/RW6G1-ns2-up3-vwap2sd-short-FD-WB3.py", dict(sim3.BASE, w=(1100, 1500), z5min=0.5, gapmax=2.0))}
for k, (path, v) in cfgs.items():
    sp = importlib.util.spec_from_file_location(k, path); M = importlib.util.module_from_spec(sp); sp.loader.exec_module(M)
    hits = set()
    for (s, d), g in RF.groupby(["symbol", "date"]):
        m = M.mask(g.reset_index(drop=True))
        ok = m & (g.tod.values >= v["w"][0]) & (g.tod.values <= v["w"][1]) & (g.close.values >= 5)
        hits |= set(zip(g.symbol.values[ok], g.date.values[ok], g.tod.values[ok]))
    vv = dict(v, refire=True, cd=0) ; b = sim3.signals(RF, dict(vv, adv=None))
    bs = set(zip(b.symbol, b.date, b.tod))
    print(f"{k}: module {len(hits)} bars, bench {len(bs)}, both {len(hits & bs)}; module-only {sorted(hits - bs)[:5]} bench-only {sorted(bs - hits)[:5]}")
