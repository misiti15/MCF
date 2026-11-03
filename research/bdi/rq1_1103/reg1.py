"""REG1: pre-declared switch A (night1102/regime PLAN.md) on the Primary book - live and replayed sessions.
  A  fade@10:00: trades entered before 10:00 ET are untouched; after 10:00 a short is kept only if SPY's 09:59 bar close
     (= SPY at 10:00) is at/above SPY's 09:30 open, a long only if it is below. Everything else is 'dropped'.
Books scored (each: all / kept / dropped R and avg R, vs-random (kept R - total R x kept share) with day-clustered t,
kept avg R without its best session and that session's share of kept R):
  live20      live Primary paper trades 10-06..11-02, R = pnl_adj / (|entry-stop| x shares) (regime's definition)
  live_cost   the same trades, R = journal r_multiple - production cost layer (the replay's definition), audit sessions
  replay      the rq1 FB replay of Primary on the same audit sessions (same R definition as live_cost)
  indep       Primary's current setups replayed on sessions before 10-06 (indep.py; not in the live sample)
    python reg1.py <scratch dir>     (needs spy_1min.parquet, j/mcf-data.db, store/runs/rq1_1103/FB/primary, indep/)
Educational only - not financial advice."""
import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCR = Path(sys.argv[1])
sp = importlib.util.spec_from_file_location("c1029", ROOT / "research/bdi/replay_audit1029/compare.py")
C = importlib.util.module_from_spec(sp)
sp.loader.exec_module(C)
COSTS = yaml.safe_load((ROOT / "config/default.yaml").read_text())["costs"]
NY = "America/New_York"

spy = pd.read_parquet(SCR / "spy_1min.parquet")
spy["date"] = spy.index.date
st = {}
for d, g in spy.groupby("date"):
    o = g["open"].iloc[0]
    c10 = g[g.index.hour * 100 + g.index.minute <= 959]["close"].iloc[-1]
    st[d] = "up" if c10 >= o else "down"
STATE = pd.Series(st)


def prep(t: pd.DataFrame, rcol: str) -> pd.DataFrame:
    t = t.copy()
    t["date"] = pd.to_datetime(t["date"]).dt.date
    et = pd.to_datetime(t["entry_time"], utc=True, format="mixed").dt.tz_convert(NY)
    t["etod"] = et.dt.hour * 100 + et.dt.minute
    t["side"] = t["side"].astype(int)
    t["R"] = t[rcol]
    s = t["date"].map(STATE)
    t["keep"] = (t.etod < 1000) | ((t.side < 0) & (s == "up")) | ((t.side > 0) & (s == "down"))
    return t.dropna(subset=["R"])


def cost_R(t):
    return t.r_multiple.astype(float) - C.cost_r(t, COSTS)


def score(t: pd.DataFrame) -> dict:
    days = sorted(t.date.unique())
    k, dr = t[t.keep], t[~t.keep]
    share = t.keep.mean()
    dk = k.groupby("date").R.sum().reindex(days, fill_value=0)
    dt = t.groupby("date").R.sum().reindex(days, fill_value=0)
    diff = dk - dt * share
    se = diff.std(ddof=1) / np.sqrt(len(diff)) if len(diff) > 1 else np.nan
    best = dk.idxmax() if len(dk) else None
    kb = k[k.date != best]
    return {"sessions": len(days), "n_all": len(t), "R_all": round(t.R.sum(), 1), "avg_all": round(t.R.mean(), 3),
            "n_kept": len(k), "R_kept": round(k.R.sum(), 1), "avg_kept": round(k.R.mean(), 3) if len(k) else None,
            "n_dropped": len(dr), "R_dropped": round(dr.R.sum(), 1),
            "avg_dropped": round(dr.R.mean(), 3) if len(dr) else None,
            "kept_pct": round(100 * share, 1), "vs_random": round(k.R.sum() - t.R.sum() * share, 1),
            "vs_random_t": round(diff.mean() / se, 2) if se and se > 0 else None,
            "best_kept_session": str(best), "best_share_of_kept_R": round(dk.max() / k.R.sum(), 2) if k.R.sum() > 0 else None,
            "avg_kept_wo_best": round(kb.R.mean(), 3) if len(kb) else None,
            "vs_random_wo_best": round(diff.drop(best).sum(), 1) if best is not None else None,
            "days_vs_random_pos": int((diff > 0).sum()), "days_state_up": int(sum(STATE[d] == "up" for d in days))}


def daily(t):
    g = t.groupby("date")
    return pd.DataFrame({"state10": [STATE[d] for d in g.groups], "n": g.size(), "R_all": g.R.sum().round(2),
                         "R_kept": t[t.keep].groupby("date").R.sum().reindex(g.groups.keys(), fill_value=0).round(2),
                         "n_kept": t[t.keep].groupby("date").size().reindex(g.groups.keys(), fill_value=0)})


con = sqlite3.connect(SCR / "j" / "mcf-data.db")
L = pd.read_sql("select * from trades where run_id=1", con)
L = L[pd.to_datetime(L.date) >= "2026-10-06"]
L["risk"] = (L.entry - L.stop).abs() * L.shares
L["R_adj"] = np.where(L.risk > 0, L.pnl_adj / L.risk, np.nan)
L["R_cost"] = cost_R(L)
live20 = prep(L, "R_adj")

rep_dir = SCR / "store/runs/rq1_1103/FB/primary"
rp = []
for d in sorted(p.name for p in rep_dir.iterdir() if (p / "trades.csv.gz").exists()):
    x = pd.read_csv(rep_dir / d / "trades.csv.gz")
    if len(x):
        x["date"] = d
        rp.append(x)
RP = pd.concat(rp, ignore_index=True)
RP["R_cost"] = cost_R(RP)
rdays = sorted(set(RP.date.astype(str)))
replay = prep(RP, "R_cost")
live_cost = prep(L[L.date.astype(str).isin(rdays)], "R_cost")

ind = []
for p in sorted((SCR / "indep").glob("*/trades.csv.gz")):
    x = pd.read_csv(p)
    if len(x):
        x["date"] = p.parent.name
        ind.append(x)
IP = pd.concat(ind, ignore_index=True) if ind else None
out = {"_note": "Educational only - not financial advice.", "state_by_day": {str(k): v for k, v in STATE.items()}}
books = {"live20": live20, "live_cost_audit_sessions": live_cost, "replay_audit_sessions": replay}
if IP is not None:
    IP["R_cost"] = cost_R(IP)
    books["indep_pre1006"] = prep(IP, "R_cost")
pd.set_option("display.width", 250)
for k, t in books.items():
    out[k] = score(t)
    out[k + "_by_day"] = {str(d): r for d, r in daily(t).to_dict("index").items()}
    print(f"== {k}\n", json.dumps(out[k]))
    print(daily(t).to_string())
# rule-change sub-windows of the live book (ledger: Primary -2R latch from 10-29, size ~$4k 10-28)
for lab, m in (("live 10-06..10-28", live20.date < pd.Timestamp("2026-10-29").date()),
               ("live 10-29..11-02", live20.date >= pd.Timestamp("2026-10-29").date())):
    out[lab] = score(live20[m])
    print(lab, json.dumps(out[lab]))
if "indep_pre1006" in books:
    t = books["indep_pre1006"]
    for side, m in (("indep longs", t.side > 0), ("indep shorts", t.side < 0)):
        out[side] = score(t[m])
        print(side, json.dumps(out[side]))
(HERE / "reg1_results.json").write_text(json.dumps(out, indent=1, default=str))
