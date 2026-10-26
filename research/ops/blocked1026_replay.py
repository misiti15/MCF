"""Blocked-signal audit 2026-10-26, part 2: what a full-coverage replay of the same sessions says.

    python research/ops/blocked1026_replay.py <scratch>
      <scratch>/rp_<acct>/<acct>/<day>/{signals,trades}.csv.gz   from
        python -m mcf.replay run --account <acct> --dates 2026-10-22,2026-10-23,2026-10-26 --as-live --universe live \
            --fills costs --jobs 3 --out <scratch>/rp_<acct>
      <scratch>/j/<branch>/journal.db

(a) never-fired setups: does the replay (a poll every minute, every 5-minute clock bucket evaluated - the GX1 gate,
    live from 2026-10-27; the frozen setups of each day) fire them? 0 in the replay too = rare on these days (or broken
    in replay as well, checked separately); >0 = live lost them to coverage (late start / poll gaps / old bar-count gate).
(b) the 2026-10-26 late start: replayed trades with entry before the account's first live poll (research cost model,
    the --fills costs replay). Replays are replays, not live results. Educational only - not financial advice."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
S = Path(sys.argv[1])
RES = json.loads((ROOT / "research/ops/blocked1026_results.json").read_text())
ACCTS = {"Primary": ("primary", "mcf-data"), "Testing 1": ("testing", "mcf-data-testing"),
         "Testing 2": ("testing2", "mcf-data-testing2"), "Graveyard": ("graveyard", "mcf-data-graveyard"),
         "Generated": ("gen", "mcf-data-gen")}
FIRST = {a: RES["coverage"][a]["2026-10-26"]["first"] for a in ACCTS}
out: dict = {}
for acct, (key, br) in ACCTS.items():
    base = S / f"rp_{key}" / key
    if not base.exists():
        continue
    sig = pd.concat([pd.read_csv(p) for p in sorted(base.glob("*/signals.csv.gz"))], ignore_index=True)
    tr = pd.concat([pd.read_csv(p) for p in sorted(base.glob("*/trades.csv.gz"))], ignore_index=True)
    rs = sig.groupby("strategy").size()
    nf = RES["never_fired"][acct]["never"]
    fired_in_replay = {n: int(rs.get(n, 0)) for n in nf}
    c = sqlite3.connect(S / "j" / br / "journal.db")
    live = pd.read_sql("select day, strategy from signals where run_id=1 and day in ('2026-10-22','2026-10-23','2026-10-26')", c)
    lv = live.groupby(["day"]).size().to_dict()
    rv = sig.groupby("day").size().to_dict() if "day" in sig else {}
    et = pd.to_datetime(tr.entry_time.astype(str).str[:19])
    d26 = tr[(tr.date == "2026-10-26") & (et.dt.strftime("%H:%M:%S") < FIRST[acct])]
    risk = (d26.entry - d26.stop).abs()
    out[acct] = dict(
        replay_signals_by_day=rv, live_signals_by_day=lv,
        never_fired_replay=fired_in_replay,
        never_fired_but_replay_fires={n: v for n, v in fired_in_replay.items() if v},
        late_start=dict(first_live_poll=FIRST[acct], trades=len(d26), R=round(float(d26.r_multiple.sum()), 2),
                        avg_R=round(float(d26.r_multiple.mean()), 3) if len(d26) else None,
                        pnl=round(float(d26.pnl_adj.sum()), 2),
                        by_setup=d26.groupby("strategy").r_multiple.agg(["size", "sum"]).round(2)
                        .sort_values("sum").to_dict("index")))
    print(f"\n=== {acct}: replay signals {rv} vs live {lv}")
    print("  never fired live; replay signals:", {k[:48]: v for k, v in fired_in_replay.items()})
    print("  10-26 before first live poll", FIRST[acct], ":", {k: v for k, v in out[acct]["late_start"].items() if k != "by_setup"})
(ROOT / "research/ops/blocked1026_replay.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
print("\nEducational only - not financial advice.")
