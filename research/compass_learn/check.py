"""COMPASS-LEARN: check the vectorised backfill (engine.py) against mcf.report.compass_live.compute on sampled history
days + the live days, and against the recorded live CSVs (mcf-data-compass). Usage: python check.py <scratch>.
Writes backfill_check.csv. Educational only - not financial advice."""
import subprocess
import sys
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
from mcf.hunch import data as HD  # noqa: E402
from mcf.report import compass_live as CL  # noqa: E402
import engine as E  # noqa: E402

S = Path(sys.argv[1])
P = pd.read_parquet(S / "panel.parquet")
pan = E.Panel(P)
rng = np.random.default_rng(1110)
hist_days = sorted(rng.choice([d for d in pan.dates if d < "2026-11-05"], 12, replace=False).tolist())
live_days = ["2026-11-05", "2026-11-06", "2026-11-09"]
syms = list(dict.fromkeys(["SPY", "QQQ", "IWM"] + CL.universe()))
bars = {d: {} for d in hist_days + live_days}
for s in syms:
    h = HD.load_1min(s, Path("/home/user/MCF/data/cache_hist/1Min"))
    h.index = pd.to_datetime(h.index).tz_convert("America/New_York")
    dd = pd.Series(h.index.date).astype(str).values
    for d in hist_days:
        x = h[dd == d]
        if len(x):
            bars[d][s] = x[["open", "high", "low", "close", "volume"]].astype(float)
lv = pd.read_parquet(S / "live" / "live_bars.parquet")
lv["ts"] = pd.to_datetime(lv.ts)
for d in live_days:
    x = lv[lv.ts.dt.strftime("%Y-%m-%d") == d]
    for s, g in x.groupby("symbol"):
        bars[d][s] = g.set_index("ts")[["open", "high", "low", "close", "volume"]].astype(float).sort_index()

conf = lambda n: 1 if n == "UP-confirmed" else (-1 if n == "DOWN-confirmed" else 0)
lvl = {v: k for k, v in CL.NAMES.items()}
w60, _, _ = E.vote(pan, 15, 60, 0.0)
c30L = E.hold(E.c30_level(pan), E.CPS)
ck, _, _ = E.b_chk(pan)
rows = []
for d in hist_days + live_days:
    out = CL.compute(bars[d], d, pd.Timestamp(f"{d} 16:30", tz="America/New_York"))
    i = int(np.flatnonzero(pan.dates == d)[0])
    for r in out:
        T = int(r["T"][:2]) * 60 + int(r["T"][3:]); j = E.mi(T)
        rows.append(dict(date=d, T=r["T"], src="compute", w60_live=conf(r["w60"]), w60_bf=int(w60[i, j]),
                         c30_live=lvl.get(r["c30"], 0), c30_bf=int(c30L[i, j]),
                         chk_live={"UP": 1, "DOWN": -1}.get(r["checkpoint"], 0), chk_bf=int(ck[i, j]),
                         bo_live=r["breadth_open"], bo_bf=pan.m["br"][i, j]))
# recorded live CSVs
for d in ("2026-11-06", "2026-11-09"):
    txt = subprocess.run(["git", "-C", str(ROOT), "show", f"origin/mcf-data-compass:compass/{d}.csv"],
                         capture_output=True, text=True).stdout
    if not txt:
        continue
    i = int(np.flatnonzero(pan.dates == d)[0])
    for r in pd.read_csv(StringIO(txt)).to_dict("records"):
        T = int(r["T"][:2]) * 60 + int(r["T"][3:]); j = E.mi(T)
        rows.append(dict(date=d, T=r["T"], src="recorded", w60_live=conf(r["w60"]), w60_bf=int(w60[i, j]),
                         c30_live=lvl.get(r["c30"], 0) if isinstance(r["c30"], str) else 0, c30_bf=int(c30L[i, j]),
                         chk_live={"UP": 1, "DOWN": -1}.get(r["checkpoint"], 0), chk_bf=int(ck[i, j]),
                         bo_live=r["breadth_open"], bo_bf=pan.m["br"][i, j]))
C = pd.DataFrame(rows)
C.to_csv(HERE / "backfill_check.csv", index=False)
for src, g in C.groupby("src"):
    print(src, len(g), "W60 match", (g.w60_live == g.w60_bf).mean().round(4), "C30", (g.c30_live == g.c30_bf).mean().round(4),
          "CHK", (g.chk_live == g.chk_bf).mean().round(4), "breadth |diff| max",
          (g.bo_live - g.bo_bf).abs()[g["T"] != "09:45"].max())
print(C[(C.w60_live != C.w60_bf) | (C.c30_live != C.c30_bf) | (C.chk_live != C.chk_bf)].to_string())
