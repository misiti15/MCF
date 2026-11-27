"""NEVERAGAIN live: journals (git show, read-only) -> lots; Alpaca GET SIP 1-min closes for Primary symbol-days + SPY/IWM.
Usage (cwd inbox): python live_fetch.py OUTDIR [DB_PRIMARY]. Educational only - not financial advice."""
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, ".")
from mcf.config import load_config  # noqa: E402
from mcf.costs import cost_r_lr8  # noqa: E402
from mcf.data.bars import normalize, rth  # noqa: E402
from mcf.data.priors import _bars, _client  # noqa: E402
from mcf.research.shadow_calib import BRANCHES  # noqa: E402

OUT = Path(sys.argv[1]); TZ = "America/New_York"
DBP = sys.argv[2] if len(sys.argv) > 2 else None
cfg = load_config(); parts = []
for acct, br in BRANCHES.items():
    p = OUT / "j.db"
    if acct == "primary" and DBP:
        raw = open(DBP, "rb").read()
    else:
        raw = subprocess.run(["git", "show", f"origin/{br}:journal.db"], capture_output=True).stdout
    if not raw:
        continue
    p.write_bytes(raw)
    con = sqlite3.connect(p)
    x = pd.read_sql("SELECT strategy, symbol, side, date, entry_time, exit_time, entry, stop, target, exit, exit_reason, "
                    "meta, shares, pnl, pnl_adj, r_multiple FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con)
    x["account"] = acct; parts.append(x); con.close(); os.remove(p)
t = pd.concat(parts, ignore_index=True)
t["date"] = t["date"].astype(str).str[:10]
t = t[t.date >= "2026-10-06"]
t["r"] = cost_r_lr8(t, cfg).astype(float)
t = t[t["r"].notna()]
t["k"] = t.account + "|" + t.strategy + "|" + t.symbol + "|" + t.date + "|" + t.entry_time.astype(str).str[:19]
t = t.drop_duplicates("k")
t["side_n"] = np.where(t.side.astype(str).str.lower().isin(["1", "long", "buy"]), 1, -1)
t["risk"] = (t.entry - t.stop).abs()
t = t[t.risk > 0].copy()
t["cost"] = t.side_n * (t.exit - t.entry) / t.risk - t.r
for c, s in (("em", "entry_time"), ("xm", "exit_time")):
    tt = pd.to_datetime(t[s], utc=True, format="mixed").dt.tz_convert(TZ)
    t[c] = (tt.dt.hour * 60 + tt.dt.minute).to_numpy()
t["e_ns"] = pd.to_datetime(t.entry_time, utc=True, format="mixed").astype("int64")
t["xm"] = np.maximum(t.xm, t.em).clip(upper=959)
t = t[(t.em >= 570) & (t.em < 960)]
keep = ["account", "strategy", "symbol", "date", "side_n", "entry", "stop", "exit", "exit_reason", "risk", "cost", "r",
        "r_multiple", "em", "xm", "e_ns", "pnl_adj"]
t[keep].to_parquet(OUT / "lots_all.parquet", index=False)
print("lots", len(t), t.groupby("account").size().to_dict())
if "--nobars" in sys.argv:
    sys.exit()
# bars: Primary symbol-days + gap-down shorts of other accounts (for the G3 descriptive) + SPY/IWM every day
P = t[(t.account == "primary") | t.strategy.str.contains("gap")]
have = {}
gp = OUT / "grid.npz"
if gp.exists() and "--refetch" not in sys.argv:
    z = np.load(gp, allow_pickle=True); have = dict(zip(z["keys"], z["arr"]))
    for a in sys.argv:
        if a.startswith("--refresh="):
            have = {k: v for k, v in have.items() if not k.endswith(a.split("=")[1])}
dc = _client(); new = {}
for d, g in P.groupby("date"):
    syms = sorted(set(g.symbol) | {"SPY", "IWM"})
    syms = [s for s in syms if f"{s}|{d}" not in have]
    if not syms:
        continue
    a = datetime.fromisoformat(d) + timedelta(hours=13); b = a + timedelta(hours=9)
    raw = _bars(dc, syms, a, b, 1, "sip")
    if raw.empty:
        print(d, "empty"); continue
    for s, x in raw.groupby(level=0):
        x = rth(normalize(x.droplevel(0)))
        x.index = pd.DatetimeIndex(x.index).tz_convert(TZ)
        x = x[x.index.date.astype(str) == d]
        if not len(x):
            continue
        k = (x.index.hour * 60 + x.index.minute).to_numpy() - 570
        ok = (k >= 0) & (k < 390)
        a1 = np.full(391, np.nan, np.float32)
        a1[0] = x.open.to_numpy()[ok][0]
        a1[1 + k[ok]] = x.close.to_numpy()[ok]
        a1[1:] = pd.Series(a1[1:]).ffill().bfill().to_numpy(np.float32)
        new[f"{s}|{d}"] = a1
    print(d, len(syms), flush=True)
have.update(new)
np.savez_compressed(gp, keys=np.array(list(have)), arr=np.stack(list(have.values())))
print("grids", len(have))
