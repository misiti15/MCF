"""Dip-day statistics per owner variant (DEV + HOLDOUT, locked block excluded): drop from the open to the morning low,
when the low happens, and how much of the drop is recovered. Index bars only. Educational only - not financial advice."""
import json

import numpy as np
import pandas as pd
from common import OUT, VARIANTS, load, sample

from mcf.strategies.base import t
from mcf.strategies.index_dip import find_trigger

rows, summ = [], {}
for v, P in VARIANTS.items():
    days = load(P["signal_symbol"])
    for d, x in days.items():
        if len(x) < 380:
            continue
        o = x.open.iloc[0]
        end = np.array((x.index + pd.Timedelta(minutes=1)).time)
        rl = np.minimum.accumulate(x.low.to_numpy())
        q = (rl <= o * (1 - P["dip_pct"] / 100)) & (end <= t(P["dip_by"]))
        if not q.any():
            continue
        am = x[end <= t("11:00")]
        lo_i = int(np.argmin(am.low.to_numpy()))
        lo = am.low.iloc[lo_i]
        lo1005 = x[end <= t("10:05")].low.min()
        drop = o - lo
        c = lambda hm: x[end <= t(hm)].close.iloc[-1]
        r = {"variant": v, "date": d, "sample": sample(d), "drop_to_low_1005_pct": (lo1005 / o - 1) * 100,
             "drop_to_am_low_pct": (lo / o - 1) * 100, "am_low_time": f"{am.index[lo_i]:%H:%M}",
             "day_low_pct": (x.low.min() / o - 1) * 100, "day_low_time": f"{x.index[int(np.argmin(x.low.to_numpy()))]:%H:%M}",
             "new_low_after_1005": bool(x[end > t("10:05")].low.min() < lo1005),
             "rec_1030": (c("10:30") - lo) / drop, "rec_1200": (c("12:00") - lo) / drop, "rec_close": (c("16:00") - lo) / drop,
             "oc_pct": (x.close.iloc[-1] / o - 1) * 100}
        for k, f in (("rec10_fires", 0.10), ("rec20_fires", 0.20)):
            r[k] = find_trigger(x, P["dip_pct"], P["dip_by"], "09:50", "10:05", "recovery", f) is not None
        rows.append(r)
R = pd.DataFrame(rows)
R.to_csv(OUT / "dipdays.csv", index=False)
for v, g in R.groupby("variant"):
    mins = pd.to_datetime(g.am_low_time, format="%H:%M")
    tb = lambda a, b: round(float(((g.am_low_time >= a) & (g.am_low_time < b)).mean() * 100))
    summ[v] = {"n_days": len(g), "n_dev": int((g["sample"] == "DEV").sum()),
               "drop_to_am_low_mean_pct": round(g.drop_to_am_low_pct.mean(), 2),
               "drop_to_am_low_median_pct": round(g.drop_to_am_low_pct.median(), 2),
               "drop_to_1005_low_mean_pct": round(g.drop_to_low_1005_pct.mean(), 2),
               "am_low_time_median": (mins.sort_values().iloc[len(mins) // 2]).strftime("%H:%M"),
               "am_low_share_pct": {"<09:50": tb("09:30", "09:50"), "09:50-10:05": tb("09:50", "10:05"),
                                    "10:05-11:00": tb("10:05", "11:01")},
               "new_low_after_1005_pct": round(g.new_low_after_1005.mean() * 100),
               "recovered_by_1030_median": round(g.rec_1030.median(), 2),
               "recovered_by_1200_median": round(g.rec_1200.median(), 2),
               "recovered_by_close_median": round(g.rec_close.median(), 2),
               "close_above_open_pct": round((g.oc_pct > 0).mean() * 100),
               "rec10_fires_pct": round(g.rec10_fires.mean() * 100), "rec20_fires_pct": round(g.rec20_fires.mean() * 100)}
(OUT / "dipstats.json").write_text(json.dumps(summ, indent=1))
print(json.dumps(summ, indent=1))
