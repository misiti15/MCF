"""Deep dive on the owner's 10 named 10-07 trades + the owner's alternative entry times (diagnosis only).
usage: python research/oct7/autopsy/deep10.py BARS_PARQUET
Educational only - not financial advice.
"""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from mcf.data.bars import resample
from mcf.research.heat import heat_frame
from mcf.research.setup_lab import extra_features

ET = "America/New_York"
raw = pd.read_parquet(sys.argv[1])
B = {}
for s, g in raw.groupby(level=0):
    g = g.droplevel(0)
    g.index = g.index.tz_convert(ET)
    B[s] = g.between_time("09:30", "15:59")[["open", "high", "low", "close", "volume"]]


def day(s, d):
    g = B[s]
    return g[g.index.date == pd.Timestamp(d).date()]


def walk(sym, d, t_entry_close, side, R, tgt_r=1.0):
    """Entry at the OPEN of the bar after the HH:MM bar (market entry after that bar closes)."""
    b = day(sym, d)
    after = b[b.index > pd.Timestamp(f"{d} {t_entry_close}", tz=ET)]
    after = after[after.index <= pd.Timestamp(f"{d} 15:54", tz=ET)]
    e = float(after["open"].iloc[0])
    fav = (after["high"] if side == 1 else after["low"])
    adv = (after["low"] if side == 1 else after["high"])
    f, a = side * (fav - e) / R, side * (adv - e) / R
    res, when = "time", None
    for ts in after.index:
        if a[ts] <= -1:
            res, when = "stop -1R", ts
            break
        if f[ts] >= tgt_r:
            res, when = f"target +{tgt_r}R", ts
            break
    return dict(entry=round(e, 3), R=round(R, 3), R_pct=round(R / e * 100, 2), mfe_r=round(f.max(), 2),
                t_mfe=str(f.idxmax().time())[:5], mae_r=round(a.min(), 2), t_mae=str(a.idxmin().time())[:5],
                first=res, at=str(when.time())[:5] if when is not None else "",
                close_1555_r=round(side * (after["close"].iloc[-1] - e) / R, 2))


def frame(sym, d, atr):
    prev, cur = day(sym, "2026-10-06"), day(sym, d)
    hist = pd.concat([resample(prev, "5min").iloc[-40:], resample(cur, "5min")])
    f = heat_frame(hist)
    f["atr_d"] = atr
    f = f.join(extra_features(hist, f))
    f["gap"] = (float(cur["open"].iloc[0]) / float(prev["close"].iloc[-1]) - 1) * 100
    f = f.iloc[-len(resample(cur, "5min")):]
    w = {'rsiHeat': 1, 'priceActionHeat': 1, 'momentumHeat': -1, 'vwapHeat': -1}
    base = sum(w[k] * f[k] for k in w)
    f["hfs_score"] = -base - 8 * 8.0 / atr                    # short when >= 11.3, 09:50-10:30, fromOpen < 0
    f["hfl_score"] = base - np.clip(f["fromOpen"], -3, 3) * 5 - 4 * 8.0 / atr   # long when >= 57.5, 11:05-13:30, gap > 0
    f["exh"] = (f["rsi5"] > 90) & (f["sma20_dist_pct"] > 1) & (f["bear_div"] > 0)
    return f


D = "2026-10-07"
out = []
print("== owner's alternative entries ==")
alts = [("HESM", "09:45", -1, 2.051949, "owner 09:46 short (live orb R)"), ("HESM", "10:25", -1, 2.051949, "owner 10:26 short (live orb R)"),
        ("HESM", "10:32", -1, 2.051949, "LIVE orb20 short (reference)"),
        ("RIOT", "10:54", -1, 0.335898, "owner 10:55 short (live lab R)"), ("RIOT", "12:36", -1, 0.335898, "owner 12:37 short (live lab R)"),
        ("RIOT", "13:19", -1, 0.335898, "LIVE exhaustion short (reference)"),
        ("CHTR", "09:49", -1, 1.505007, "LIVE heat_fade_short (09:50 entry)"), ("CHTR", "09:50", -1, 1.505007, "CHTR +1 min"),
        ("CHTR", "09:51", -1, 1.505007, "CHTR +2 min"), ("CHTR", "09:52", -1, 1.505007, "CHTR +3 min"),
        ("CHTR", "09:54", -1, 1.505007, "CHTR next 5-min bar close (09:55)"),
        ("CHTR", "11:04", 1, 1.255007, "LIVE heat_fade_long 11:05"), ("CHTR", "11:06", 1, 1.255007, "CHTR long +2 min"),
        ("PENG", "09:50", -1, 3.81, "PENG opposite: short at the long's entry (orb R)"),
        ("BKV", "10:16", -1, 0.6325, "BKV opposite: short at the long's entry (orb R)"),
        ("ILMN", "10:24", 1, 4.191754 / 1, "ILMN opposite: long at the short's entry"),
        ("ALAB", "10:24", 1, 5.306939, "ALAB opposite: long at the short's entry")]
for sym, tt, side, R, lab in alts:
    r = walk(sym, D, tt, side, R)
    r.update(label=lab, sym=sym, bar=tt, side=side)
    out.append(r)
A = pd.DataFrame(out)
print(A[["label", "sym", "bar", "side", "entry", "R_pct", "mfe_r", "t_mfe", "mae_r", "t_mae", "first", "at", "close_1555_r"]].to_string())

print("\n== rule values around the owner's times (5-min bar closes) ==")
atr = {"HESM": 4 * 2.051949 / 2, "RIOT": 4 * 0.335898, "CHTR": 4 * 1.505007, "WHR": 4 * 0.340205,
       "ALAB": 4 * 5.306939, "ILMN": 4 * 4.191754, "PENG": 4 * 3.81 / 2, "BKV": 4 * 0.6325 / 2, "NEOG": 4 * 0.4925 / 2}
cols = ["tod", "close", "fromOpen", "gap", "vwapDistPct", "rsi", "rsi5", "pricePosition", "momentum", "sma20_dist_pct",
        "bear_div", "hfs_score", "hfl_score", "exh"]
for sym, tods in {"HESM": [940, 945, 950, 1025, 1030, 1035], "RIOT": [1050, 1055, 1100, 1235, 1240, 1320],
                  "CHTR": [945, 950, 955, 1000, 1105], "WHR": [1310, 1500, 1515, 1520, 1525, 1530],
                  "ALAB": [1015, 1020, 1025, 1030], "ILMN": [1020, 1025, 1030]}.items():
    f = frame(sym, D, atr[sym])
    print(sym, "(ATR assumed", round(atr[sym], 3), "- heat/lab ATR from journal R; HESM ATR unknown, assumed 2xR)")
    print(f[f["tod"].isin(tods)][cols].round(2).to_string())

print("\n== minute paths (close every 15 min) ==")
for sym in ["HESM", "PENG", "BKV", "ILMN", "CHTR", "ALAB", "RIOT", "NEOG", "WHR"]:
    b = day(sym, D)
    s = b["close"].resample("15min").last()
    print(sym, "open", b["open"].iloc[0], "hi", b["high"].max(), "@", str(b["high"].idxmax().time())[:5],
          "lo", b["low"].min(), "@", str(b["low"].idxmin().time())[:5], "close", b["close"].iloc[-1])
    print("   ", " ".join(f"{i.strftime('%H:%M')}={v:.2f}" for i, v in s.items()))
A.to_csv("research/oct7/autopsy/owner_alternatives.csv", index=False)
