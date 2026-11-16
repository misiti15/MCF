"""Point-in-time market state per (date, tod = 5-minute bar close) for the gate experiments, anchored AFTER 09:50
(owner direction rule 2026-11-14): SPY since 09:50, SPY vs its 09:30-09:50 range, SPY vs session VWAP, breadth.
Only 1-minute bars that closed by `tod` are used. Locked block rows dropped. Educational only - not financial advice."""
import glob, numpy as np, pandas as pd
OUT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech2-cwt14/"
TEAMD = ["2026-11-05", "2026-11-06", "2026-11-09", "2026-11-10"]
def spy():
    a = pd.read_parquet("/home/user/MCF/data/cache_hist/1Min/SPY.parquet")[["open", "high", "low", "close", "volume"]]
    t = pd.concat([pd.read_parquet(f"/home/user/MCF/data/team/1Min/{d}.parquet") for d in TEAMD])
    t = t[t.symbol == "SPY"]; t["ts"] = pd.to_datetime(t.ts).dt.tz_convert("America/New_York")
    b = pd.concat([a, t.set_index("ts")[["open", "high", "low", "close", "volume"]]]).sort_index()
    b = b[~b.index.duplicated()]
    hm = b.index.hour * 100 + b.index.minute
    b = b[(hm >= 930) & (hm < 1600)].copy()
    b["date"] = b.index.strftime("%Y-%m-%d"); b = b[~((b.date >= "2024-11-01") & (b.date <= "2025-02-28"))]
    b["m"] = b.index.hour * 60 + b.index.minute
    rows = []
    for d, g in b.groupby("date"):
        o = g.open.iloc[0]
        tp = (g.high + g.low + g.close) / 3; vw = (tp * g.volume).cumsum() / g.volume.cumsum()
        early = g[g.m < 9 * 60 + 50]
        hi, lo = early.high.max(), early.low.min()
        c950 = early.close.iloc[-1] if len(early) else np.nan
        for tod in range(950, 1305, 5):
            if tod % 100 >= 60: continue
            mm = tod // 100 * 60 + tod % 100
            x = g[g.m < mm]
            if not len(x): continue
            c = x.close.iloc[-1]
            rows.append((d, tod, (c / o - 1) * 100, (c / c950 - 1) * 100, (c - lo) / (hi - lo) if hi > lo else np.nan,
                         int(np.sign(c - hi) if c > hi else (-1 if c < lo else 0)), (c / vw.loc[x.index[-1]] - 1) * 100))
    return pd.DataFrame(rows, columns=["date", "tod", "spy_fo1", "spy_d950", "spy_rpos", "spy_rng", "spy_vw"])
def breadth():
    c = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob("/home/user/MCF/research/history2y/data/context/*.parquet"))])
    c["date"] = c.date.astype(str)
    c = c[~((c.date >= "2024-11-01") & (c.date <= "2025-02-28"))]
    f = pd.read_parquet("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-cwt14/frames_extra.parquet",
                        columns=["symbol", "date", "tod", "vwapDistPct", "fromOpen", "adv20"])
    f = f[(f.date >= "2026-11-05") & (f.adv20 >= 50e6)]
    e = f.groupby(["date", "tod"]).agg(breadth=("vwapDistPct", lambda v: (v > 0).mean()), breadth_open=("fromOpen", lambda v: (v > 0).mean())).reset_index()
    return pd.concat([c[["date", "tod", "spy_fo", "breadth", "breadth_open"]], e], ignore_index=True)
if __name__ == "__main__":
    s = spy(); b = breadth()
    m = s.merge(b, on=["date", "tod"], how="left")
    b950 = m[m.tod == 950].set_index("date")[["breadth", "breadth_open"]].rename(columns=lambda x: x + "950")
    m = m.join(b950, on="date"); m["br_d950"] = m.breadth_open - m.breadth_open950
    m.to_parquet(OUT + "ctx.parquet"); print(m.shape); print(m[["spy_fo", "spy_fo1"]].corr())
    print(m.describe().T.round(3))
