"""REGSTEER-1126 information (PREREG addendum A; not a config, not used for selection): bench W60 first-confirmed side vs the
day's close side (SPY last RTH close vs first RTH open) by month block and by confirmation time, with the base rate; share
of base-book entries at/after the day's first confirmation and with a confirmed side at the entry mark.
Usage: python rs_info.py STATES SCR OUT.json. Locked block never read (rs_states loaders assert). Educational only."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H.parents[1])); sys.path.insert(0, str(H))
import rs_states as S  # noqa: E402

ST, SCR, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
b = pd.concat([S.bars("SPY", S.FRESH), S.bars("SPY", S.HIST)])
d = b.index.date.astype(str)
day = pd.DataFrame({"o": b.open.groupby(d).first(), "c": b.close.groupby(d).last()})
day["close_side"] = np.sign(day.c - day.o).astype(int)
M = pd.read_parquet(ST / "marks.parquet")
S.no_locked(M.date.unique())
conf = M[M.level.abs() == 2].sort_values(["date", "T"]).groupby("date").first()
x = day.join(conf[["T", "level"]], how="left")
x["first_side"] = np.sign(x.level).fillna(0).astype(int)
c = x[x.first_side != 0].copy()
c["hit"] = c.first_side == c.close_side
up = float((day.close_side > 0).mean())
res = {"days": int(len(x)), "days_confirmed": int(len(c)), "hit_rate": round(float(c.hit.mean()), 3),
       "base_rate_majority_side": round(max(up, 1 - up), 3), "up_close_share": round(up, 3),
       "median_confirm_T": f"{int(c['T'].median()) // 60}:{int(c['T'].median()) % 60:02d}"}
c["blk"] = [f"{i[:4]}H{1 if i[5:7] <= '06' else 2}" for i in c.index]
c["mon"] = c.index.str[:7]
res["by_half_year"] = {k: f"{g.hit.mean():.2f} ({len(g)})" for k, g in c.groupby("blk")}
res["by_month"] = {k: f"{g.hit.mean():.2f} ({len(g)})" for k, g in c.groupby("mon")}
res["months_hit_ge_base"] = f"{sum(g.hit.mean() >= res['base_rate_majority_side'] for _, g in c.groupby('mon'))}/{c.mon.nunique()}"
tb = pd.cut(c["T"], [0, 600, 630, 690, 780, 999], labels=["10:00", "10:15-10:30", "10:45-11:30", "11:45-13:00", "13:15+"])
res["by_confirm_time"] = {str(k): f"{g.hit.mean():.2f} ({len(g)})" for k, g in c.groupby(tb, observed=True)}
B = pd.read_parquet(SCR / "base.parquet")
B["fT"] = B.date.map(conf["T"])
after = B.fT.notna() & (B.fT <= B.em - 1)
res["base_entries"] = int(len(B))
res["share_entries_after_first_confirmation"] = round(float(after.mean()), 3)
res["share_entries_confirmed_at_entry_mark"] = round(float((B.w60 != 0).mean()), 3)
res["share_entries_aligned_confirmed"] = round(float((B.side * B.w60 > 0).mean()), 3)
res["share_entries_against_confirmed"] = round(float((B.side * B.w60 < 0).mean()), 3)
json.dump(res, open(OUT, "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != "by_month"}, indent=1))
