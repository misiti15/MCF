import sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF/research/bdi/cwt/live"); sys.path.insert(0, "/home/user/MCF")
import cwt_live_lib as L
OUT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-cwt14/"
df = pd.read_parquet(OUT + "frames_extra.parquet")
df = df[df.adv20.fillna(0) >= 50e6].sort_values(["symbol","date","tod"]).reset_index(drop=True)
x = L.arrays(df)
at10 = np.where(x.tod == 1000, x.lod, np.nan); orl = pd.Series(at10).groupby(x.seg).ffill().to_numpy(float)
PS = [0.10, 0.15, 0.08]
masks = {p: L.b3(df, level='OR', p=p, lowvol=False, side='long') for p in PS}
any_ = np.zeros(len(df), bool)
for p in PS: any_ |= masks[p]
idx = np.flatnonzero(any_ & (df.tod.to_numpy() >= 950) & (df.tod.to_numpy() <= 1500))
r = df.iloc[idx].copy()
for p in PS: r[f"m{int(p*100):02d}"] = masks[p][idx]
r["orl"] = orl[idx]; r["lod"] = x.lod[idx]; r["vwap"] = x.vwap[idx]; r["open_d"] = x.open_d[idx]; r["pc"] = x.pc[idx]
r["month"] = "2026-11x"
s = pd.read_parquet(OUT + "sig_frames.parquet"); s["date"] = s.date.astype(str)
cols = [c for c in s.columns if c in r.columns]
r = r[cols]
# parity 11-02..11-04
a = s[(s.date >= "2026-11-02") & s.m10 & (s.adv20 >= 95e6)][["symbol","date","tod"]]
b = r[(r.date <= "2026-11-04") & r.m10 & (r.adv20 >= 95e6)][["symbol","date","tod"]]
m = a.merge(b, how="outer", indicator=True); print("parity 11-02..04:", m._merge.value_counts().to_dict())
r[r.date >= "2026-11-05"].to_parquet(OUT + "sig_extra.parquet"); print(len(r[r.date >= "2026-11-05"]))
