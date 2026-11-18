"""W8-DQ audit (crunch 2026-11-18): R / P/L accounting checks over every live journal. Read-only.

    python research/crunch/w8_dataquality/audit.py <dir with <branch>.db and <branch>.status.json>
(extract with: git show origin/<branch>:journal.db > <dir>/<branch>.db; same for status.json)
Live run = runs.kind 'paper' (run_id 1); what-if = run 2; shadow = run 3 (excluded). R = pnl_adj / (|entry-stop| x shares).
Educational only - not financial advice."""
import glob
import json
import os
import sqlite3
import sys

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from mcf import costs  # noqa: E402
from mcf.config import load_config  # noqa: E402
from mcf.report.c3score import whatif_corrected  # noqa: E402

src = sys.argv[1]
cfg = load_config()
model = costs.live_model(cfg)
EFF = model["effective_from"]
for f in sorted(glob.glob(os.path.join(src, "*.db"))):
    acct = os.path.basename(f)[:-3]
    con = sqlite3.connect(f)
    d = pd.read_sql("SELECT t.*, o.entry_ref FROM trades t LEFT JOIN orders o ON o.broker_order_id = t.broker_order_id "
                    "WHERE t.run_id = 1", con)
    w = pd.read_sql("SELECT * FROM trades WHERE run_id = 2", con)
    st = json.load(open(f[:-3] + ".status.json"))
    risk = (d.entry - d.stop).abs() * d.shares
    R = d.pnl_adj / risk
    chk = {
        "trades": len(d),
        "r_multiple != pnl/risk": int(((d.pnl / risk - d.r_multiple).abs() > 1e-6).sum()),
        "pnl != side*(exit-entry)*shares": int(((d.side * (d.exit - d.entry) * d.shares - d.pnl).abs() > 0.05).sum()),
        "dup broker ids": int(d.broker_order_id.duplicated().sum()),
        "post-LR8 rows not tagged lr8": int(((d.date >= EFF) & ~d.meta.fillna("").str.contains("costs=lr8")).sum()),
        "pnl_adj re-cost mismatch": int(sum(abs(costs.pnl_adj(r.pnl, int(r.side), r.entry, r.shares, costs.parts_from_row(r),
                                                              None if pd.isna(r.target) else r.target, r.date, cfg)[0]
                                                - r.pnl_adj) > 0.01 for r in d.itertuples())),
    }
    r8 = costs.cost_r_lr8(d, cfg)
    h = pd.DataFrame(st.get("history") or []).set_index("date") if st.get("history") else pd.DataFrame()
    jp = d.groupby("date").pnl.sum()
    gap = (h["alpaca_day_pl"] - jp).dropna() if len(h) else pd.Series(dtype=float)
    first = ~w.sort_values("signal_time").duplicated(["date", "symbol", "strategy", "side"])
    wc = whatif_corrected(w, key=("symbol", "date", "strategy"))
    print(f"\n== {acct}")
    print("  integrity:", chk)
    print(f"  sum R after costs (booked) {R.sum():.1f} | uniform LR8 {r8.sum():.1f} | $-weighted R "
          f"{d.pnl_adj.sum() / risk.mean():.1f} | median risk/trade ${risk.median():.0f}")
    print(f"  Alpaca - journal $: total {gap.sum():.0f}, days |gap|>$20: "
          f"{ {k: round(v) for k, v in gap[gap.abs() > 20].items()} }")
    print(f"  what-if: rows {len(w)}, repeat share {1 - first.mean():.2f}, raw R {w.r_multiple.sum():.1f}, "
          f"corrected R {wc['r']} on {wc['n']} (unfillable dropped {wc['dropped_unfillable']})")
    slip_r = d.side * (d.entry - d.entry_ref) / (d.entry - d.stop).abs()
    print(f"  entry fill vs signal ref, in R: mean {slip_r.mean():+.3f}, p90 {slip_r.quantile(.9):+.3f}")
