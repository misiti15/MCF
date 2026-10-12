"""One-off leaderboard snapshot for the live page (docs/live/leaderboard.json), used until each account's nightly
scorecard carries its own leaderboard. Usage: python scripts/leaderboard_snapshot.py <account>=<journal.db> ...
Educational only - not financial advice.
"""
import json
import os
import sys
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "docs" / "live" / "leaderboard.json"


def main(pairs: list[str]) -> None:
    from mcf.config import load_config
    from mcf.journal import Journal
    from mcf.report import scorecard

    out = {"generated": pd.Timestamp.now(tz="America/New_York").strftime("%Y-%m-%d %H:%M ET"), "accounts": {},
           "disclaimer": "Educational only - not financial advice."}
    for pair in pairs:
        acct, db = pair.split("=", 1)
        os.environ["MCF_ACCOUNT"] = acct
        cfg = load_config()
        j = Journal(db)
        rid = j.get_or_create_run("paper", "MCF Update (live paper)")
        out["accounts"][acct] = scorecard.leaderboard(j.trades(run_id=rid), cfg, acct)
    OUT.write_text(json.dumps(out, indent=1))
    print(OUT, {k: len(v) for k, v in out["accounts"].items()})


if __name__ == "__main__":
    main(sys.argv[1:])
