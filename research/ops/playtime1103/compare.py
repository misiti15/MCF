"""Playtime 2026-11-03: per variant x account summary of the run.py replays (R after the production cost layer).

    MCF_REPLAY_STORE=<store> python compare.py <scratch>/j   -> variants.csv, variants_day.csv
Benched (V2) setup-sessions have no trades and are excluded from per-session stats by construction (they are not
zeros). Educational only - not financial advice."""
import os
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(os.environ.get("MCF_ROOT", "/home/user/MCF"))
STORE = Path(os.environ["MCF_REPLAY_STORE"])
OUT = Path(os.environ.get("OUT", Path(__file__).resolve().parent))
J = Path(sys.argv[1])
C = yaml.safe_load((ROOT / "config/default.yaml").read_text())["costs"]
BR = {"graveyard": "mcf-data-graveyard", "gen": "mcf-data-gen"}
CONF = {"graveyard": "FB", "gen": "B"}   # Gen on the lab universe (CPU: a full-universe Gen session took ~40 min)


def cost_r(df):
    e, x = df.entry.astype(float), df.exit.astype(float)
    risk = (e - df.stop.astype(float)).abs().replace(0, np.nan)
    per = lambda p: p * C["slippage_bps"] / 1e4 + C["slippage_per_share"]  # noqa: E731
    reason = df.exit_reason.astype(str).str.lower()
    ex = np.where(reason.str.contains("target"), 0.0,
                  per(x) + np.where(reason.str.contains("stop|trail"), C["stop_slippage_per_share"], 0.0))
    return ((per(e) + ex) / risk).fillna(0.0)


def summ(t, label, ac):
    t = t.copy()
    t["net"] = t.r_multiple.astype(float) - cost_r(t)
    t["hhmm"] = pd.to_datetime(t.entry_time.astype(str), utc=True, format="mixed").dt.tz_convert("America/New_York").dt.strftime("%H:%M")
    late = t[t.hhmm > "10:45"]
    byday = t.groupby("date").net.sum()
    best = byday.idxmax() if len(byday) else None
    wo = t[t.date != best]
    tot = t.net.sum()
    rej = None
    return dict(variant=label, account=ac, sessions=t.date.nunique(), trades=len(t), setups_traded=t.strategy.nunique(),
                setups_traded_after_1045=late.strategy.nunique(),
                setups_after_1045_per_session=round(late.groupby("date").strategy.nunique().mean(), 1) if len(late) else 0,
                trades_after_1045=len(late), total_R=round(tot, 1), avg_R=round(t.net.mean(), 3),
                best_day=best, best_day_share=round(byday.max() / tot, 2) if tot > 0 else None,
                avg_R_wo_best_day=round(wo.net.mean(), 3) if len(wo) else None), t


rows, days = [], []
for ac, br in BR.items():
    c = sqlite3.connect(J / br / "journal.db")
    lt = pd.read_sql("select strategy, symbol, date, entry_time, entry, stop, exit, exit_reason, r_multiple from trades "
                     "where run_id=1 and date between '2026-10-27' and '2026-11-03'", c)
    r, t = summ(lt, "live", ac)
    rows.append(r)
    if CONF[ac] == "B":   # the lab-universe replay can only trade lab names: live on the same names
        lab = set((ROOT / "research/lab_symbols.txt").read_text().split())
        r, t = summ(lt[lt.symbol.isin(lab)], "live_lab_names", ac)
        rows.append(r)
    for v in ("V0", "V1", "V2"):
        fs = sorted((STORE / "runs/playtime1103" / v / CONF[ac] / ac).glob("*/trades.csv.gz"))
        if not fs:
            continue
        rt = pd.concat([pd.read_csv(f).assign(date=f.parent.name) for f in fs])
        rs = pd.concat([pd.read_csv(f.parent / "signals.csv.gz") for f in fs])
        r, t = summ(rt, v, ac)
        r["conf"] = CONF[ac]
        st = rs.status.astype(str)
        rr = rs.reason.astype(str)
        r.update(bp_rejects=int(rr.str.contains("buying_power").sum()),
                 setup_cap_skips=int(rr.str.startswith("max positions for this setup").sum()))
        rows.append(r)
        days.append(t.groupby("date").agg(trades=("net", "size"), R=("net", "sum")).assign(variant=v, account=ac))
df = pd.DataFrame(rows)
df.to_csv(OUT / "variants.csv", index=False)
print(df.to_string(index=False))
if days:
    dd = pd.concat(days).reset_index()
    dd.to_csv(OUT / "variants_day.csv", index=False)
    print(dd.pivot_table(index=["account", "date"], columns="variant", values="R").round(1).to_string())
