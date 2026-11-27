"""Path speed of live trades on 1-minute bars (cache_hist, lab symbols, through 2026-11-04): signed MTM / MFE / MAE in R
at fixed horizons after entry, independent of the exit rule (each trade's own R = |entry - stop|)."""
import pandas as pd, numpy as np, os
from multiprocessing import Pool
X = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/X/"
C = "/home/user/MCF/data/cache_hist/1Min/"
H = [5, 10, 15, 30, 60, 120]
d = pd.read_parquet(X + "live_dedup.parquet")
d = d[d.date <= "2026-11-04"]
d = d[d.symbol.map(lambda s: os.path.exists(C + s + ".parquet"))].copy()
d["et"] = d.entry_time.dt.tz_convert("America/New_York")

def one(args):
    sym, g = args
    b = pd.read_parquet(C + sym + ".parquet", filters=[("__index_level_0__", ">=", pd.Timestamp("2026-10-06", tz="America/New_York"))]) if False else pd.read_parquet(C + sym + ".parquet")
    b = b[b.index >= pd.Timestamp("2026-10-06", tz="America/New_York")]
    out = []
    for i, r in g.iterrows():
        e0 = r.et.floor("min") + pd.Timedelta(minutes=1)   # first full minute after the fill
        day_end = r.et.normalize() + pd.Timedelta(hours=15, minutes=55)
        p = b[(b.index >= e0) & (b.index < day_end)]
        if len(p) < 3:
            continue
        R = abs(r.entry - r.stop); s = r.side
        fav_hi = (p.high - r.entry) * s / R if s == 1 else (r.entry - p.low) / R
        adv = (p.low - r.entry) / R if s == 1 else (r.entry - p.high) / R
        mtm = (p.close - r.entry) * s / R
        mins = np.arange(1, len(p) + 1)
        row = {"i": i}
        for h in H:
            m = mins <= h
            row[f"mtm{h}"] = mtm.values[m][-1] if len(p) >= h else np.nan
            row[f"mfe{h}"] = fav_hi.values[m].max() if len(p) >= h else np.nan
            row[f"mae{h}"] = adv.values[m].min() if len(p) >= h else np.nan
            row[f"absmv{h}"] = abs(p.close.values[m][-1] - r.entry) / r.entry * 1e4 if len(p) >= h else np.nan
        # first-passage to +1R / -1R and to +0.5R over the rest of the session (exit rule ignored)
        for lvl in (0.5, 1.0):
            up = np.where(fav_hi.values >= lvl)[0]; dn = np.where(adv.values <= -1.0)[0]
            row[f"t_up{lvl}"] = up[0] + 1 if len(up) else np.nan
            row[f"first_up{lvl}"] = (len(up) > 0) and (not len(dn) or up[0] < dn[0])
        row["t_dn1"] = (np.where(adv.values <= -1.0)[0][0] + 1) if (adv.values <= -1.0).any() else np.nan
        row["stop_pct_bps"] = R / r.entry * 1e4
        out.append(row)
    return out

if __name__ == "__main__":
    with Pool(4) as pool:
        res = pool.map(one, list(d.groupby("symbol")), chunksize=8)
    q = pd.DataFrame([x for r in res for x in r]).set_index("i")
    q = d[["side_s", "strategy", "account", "date", "r", "tgt_r", "hold"]].join(q, how="inner")
    q.to_parquet(X + "live_path.parquet"); print(len(q), "of", len(d))
