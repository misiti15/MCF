"""TT1/TT0 SPY tape-turn gate per (date, T) where T = minute (HHMM) at which the decision is made; uses SPY 1-min bars
labelled < T only. Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
INBOX = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox"
sys.path.insert(0, INBOX); sys.path.insert(0, INBOX + "/research/ultimate_1119/top10")
import bench10 as B
TZ = "America/New_York"

def gate_table(b):
    hm = b.index.hour * 100 + b.index.minute
    b = b[(hm >= 930) & (hm < 1600)].copy()
    b["d"] = b.index.date.astype(str)
    out = []
    for d, g in b.groupby("d"):
        mins = (g.index.hour * 60 + g.index.minute).to_numpy()
        c = g.close.to_numpy(float); v = g.volume.to_numpy(float)
        vw = np.cumsum(c * v) / np.maximum(np.cumsum(v), 1)
        dist = (c / vw - 1) * 100
        below = (dist <= -0.05) & (mins >= 9 * 60 + 35)
        cumbelow = np.cumsum(below) > 0
        for tm in range(9 * 60 + 50, 15 * 60 + 56):
            i = np.searchsorted(mins, tm) - 1
            j = np.searchsorted(mins, tm - 30) - 1
            if i < 0 or j < 0:
                continue
            a = dist[i] > 0; was = bool(cumbelow[i]); up = c[i] / c[j] - 1 > 0
            out.append((d, (tm // 60) * 100 + tm % 60, a, was, up, dist[i], (c[i] / c[j] - 1) * 100))
    s = pd.DataFrame(out, columns=["date", "T", "reclaim", "was_below", "up30", "spy_vw", "spy30"])
    s["TT1"] = s.reclaim & s.was_below & s.up30
    s["TT0"] = s.reclaim & s.up30
    return s

if __name__ == "__main__":
    s1 = gate_table(B.hist_bars("SPY")); B.no_locked(s1.date.unique())
    b2 = pd.read_parquet(B.FRESH / "1Min" / "SPY.parquet"); b2.index = pd.DatetimeIndex(b2.index).tz_convert(TZ); b2 = b2.sort_index()
    s2 = gate_table(b2); s2 = s2[(s2.date >= B.T2_LO) & (s2.date <= B.T2_HI)]
    bl = pd.read_parquet("../L3/live_SPY.parquet"); bl.index = pd.DatetimeIndex(bl.index).tz_convert(TZ)
    s3 = gate_table(bl); s3 = s3[s3.date > "2026-11-04"]
    s = pd.concat([s1.assign(src="T1"), s2.assign(src="T2"), s3.assign(src="live")])
    B.no_locked(s.date.unique())
    s.to_parquet("gate.parquet")
    # overlap check T1 vs live SPY for 10-06..11-04
    s4 = gate_table(bl); m = s1.merge(s4, on=["date", "T"], suffixes=("", "_l"))
    print("T1 vs live SPY agreement TT1:", (m.TT1 == m.TT1_l).mean(), len(m))
    for src, x in s.groupby("src"):
        d = x[x["T"] % 5 == 0]
        print(src, x.date.nunique(), "share bars TT1", round(d.TT1.mean(), 3), "TT0", round(d.TT0.mean(), 3),
              "days with any TT1 by 15:00", round(d[d["T"] <= 1500].groupby("date").TT1.any().mean(), 3))
