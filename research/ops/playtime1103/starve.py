"""Playtime 2026-11-03 (owner GY-BP refined): which setups are STARVED by their account's capacity, 10-27..11-03.

Starved = a signal the account turned away for capacity: broker buying-power reject, max concurrent positions (slots),
max positions for this setup (per-setup cap). Not counted: borrow/ETB, spread/realism, cost filter, twin / opposite side /
lot cap (place in line), setup daily loss latch (a rule), quiet-by-design. Scale-out cap (T1/T2, 2/day) never blocks an
entry and is only printed to the runner log, so it cannot starve a setup's signals.

    python research/ops/playtime1103/starve.py <scratch>   # <scratch>/j/<branch>/journal.db = git show origin/<branch>:journal.db

What-if R = journal run_id 2 row of the same setup + symbol + day + skip reason, net of the production cost model
($0.01/sh + 1 bp per side, +$0.02/sh on stop exits, no exit cost on target fills), as inactive1103/audit.py.
Writes starve.csv (per account x setup) and starve_time.csv (per account x session). Educational only - not financial advice."""
import os
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(os.environ.get("MCF_ROOT", "/home/user/MCF"))
sys.path.insert(0, str(ROOT))
from mcf.report.playing_time import classify  # noqa: E402

S = Path(sys.argv[1])
OUT = Path(os.environ.get("OUT", Path(__file__).resolve().parent))
D0, D1 = "2026-10-27", "2026-11-03"
ACCTS = {"Primary": "mcf-data", "Testing 1": "mcf-data-testing", "Testing 2": "mcf-data-testing2",
         "Graveyard": "mcf-data-graveyard", "Generated": "mcf-data-gen"}


def cap_kind(status, reason):
    r = str(reason or "").lower()
    if status == "rejected" and "buying_power" in r:
        return "buying_power"
    b = classify(status, reason)
    return {"slots_full": "slots", "setup_cap": "setup_cap"}.get(b)


def net_r(w):
    R = (w.entry - w.stop).abs()
    cps = (0.01 + w.entry * 1e-4) + np.where(w.exit_reason == "target", 0.0, 0.01 + w.exit * 1e-4) \
        + np.where(w.exit_reason == "stop", 0.02, 0.0)
    return w.r_multiple - np.where(R > 0, cps / R, 0.0)


rows, trows = [], []
for acct, br in ACCTS.items():
    c = sqlite3.connect(S / "j" / br / "journal.db")
    sig = pd.read_sql("select day, ts, symbol, strategy, status, reason from signals where run_id=1 and day between ? and ?",
                      c, params=(D0, D1))
    sig["kind"] = [cap_kind(a, b) for a, b in zip(sig.status, sig.reason)]
    sig["taken"] = sig.status.isin(["submitted", "dry_run"])
    sig["hhmm"] = sig.ts.str[11:16]
    wi = pd.read_sql("select strategy, date, symbol, signal_time, entry, stop, exit, exit_reason, r_multiple, meta "
                     "from trades where run_id=2 and date between ? and ?", c, params=(D0, D1))
    wi["kind"] = [("buying_power" if "buying_power" in str(m) else
                   "setup_cap" if "max positions for this setup" in str(m) else
                   "slots" if "max concurrent" in str(m) else None) for m in wi.meta]
    wi = wi[wi.kind.notna()].copy()
    wi["net"] = net_r(wi) if len(wi) else []
    cap = sig[sig.kind.notna()]
    for d, g in sig.groupby("day"):
        cg = g[g.kind.notna()]
        trows.append(dict(account=acct, day=d, signals=len(g), taken=int(g.taken.sum()),
                          bp_rejects=int((cg.kind == "buying_power").sum()),
                          bp_first=cg[cg.kind == "buying_power"].hhmm.min() if (cg.kind == "buying_power").any() else "",
                          setup_cap_skips=int((cg.kind == "setup_cap").sum()),
                          setup_cap_first=cg[cg.kind == "setup_cap"].hhmm.min() if (cg.kind == "setup_cap").any() else "",
                          slot_skips=int((cg.kind == "slots").sum())))
    for (name, kind), g in cap.groupby(["strategy", "kind"]):
        w = wi[(wi.strategy == name) & (wi.kind == kind)]
        allsig = sig[sig.strategy == name]
        rows.append(dict(account=acct, setup=name, kind=kind, blocked=len(g), sessions=g.day.nunique(),
                         first_block=g.hhmm.min(), median_block=sorted(g.hhmm)[len(g) // 2],
                         taken_window=int(allsig.taken.sum()), signals_window=len(allsig),
                         taken_sessions=allsig[allsig.taken].day.nunique(),
                         whatif_n=len(w), whatif_net_R=round(float(w.net.sum()), 2) if len(w) else 0.0,
                         whatif_avg_R=round(float(w.net.mean()), 3) if len(w) else None))
df = pd.DataFrame(rows).sort_values(["account", "blocked"], ascending=[True, False])
df.to_csv(OUT / "starve.csv", index=False)
pd.DataFrame(trows).to_csv(OUT / "starve_time.csv", index=False)
print(df.to_string(index=False))
print(pd.DataFrame(trows).to_string(index=False))
