"""Power of OBS-UPDAY-NULL table 3 (Observer 2026-11-14, after Skeptic's ANCHOR950 power note): minimum detectable effect at
80% power, two-sided 5% (MDE = 2.80 x sd / sqrt(n)), for the rest-of-day return from t to the close, per move-so-far bucket.
Same data as upnull.py. Educational only - not financial advice."""
import pandas as pd, numpy as np
from pathlib import Path
C = Path(__file__).with_name("cache")
for sym in ["SPY", "QQQ"]:
    d = pd.read_parquet(C / f"{sym}_1m.parquet"); d = d[(d.t.dt.time >= pd.Timestamp("09:30").time()) & (d.t.dt.time < pd.Timestamp("16:00").time())].copy()
    d["day"] = d.t.dt.date; d["hm"] = d.t.dt.strftime("%H:%M"); g = d.groupby("day")
    day = pd.DataFrame({"c": g.c.last(), "n": g.size()}); day = day[day.n >= 300]; day["pc"] = day.c.shift(1); day = day.dropna()
    px = d.pivot_table(index="day", columns="hm", values="c", aggfunc="last")
    for t in ["10:00", "10:30", "11:00", "12:00", "13:00"]:
        m = (px[t].reindex(day.index) / day.pc - 1) * 100; rest = (day.c / px[t].reindex(day.index) - 1) * 1e4; out = []
        for lab, sel in [("all", m == m), ("<=-0.5%", m <= -0.5), ("-0.5..0", (m > -0.5) & (m <= 0)), ("0..+0.5", (m > 0) & (m <= 0.5)), (">+0.5%", m > 0.5)]:
            x = rest[sel].dropna(); out.append(f"{lab} n {len(x)} MDE {2.8 * x.std(ddof=1) / np.sqrt(len(x)):.0f}bps")
        print(f"{sym} t={t}: " + " | ".join(out))
print("3x ETFs: multiply by ~3. Educational only - not financial advice.")
