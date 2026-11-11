"""REPV step 4 input: per account, lost signals per session by reason over the CURRENT rule regime (sessions 11-05..11-10,
after UNI1 11-04 and ROLL1 11-05), converted to expected extra entries per session if that block were lifted:
risk-stage blocks (cap / halt / latch / twin / one-per-symbol / split gate / borrow) x the account's downstream pass rate
(taken / (taken + spread + cost filter + buying power)); cost-filter skips x (1 - buying-power share); buying-power rejects
x 1 (they had passed every check). What-if avg R (run_id=2, simulated with backtest costs, optimistic) is the P/L-noise
price per extra entry.

    python research/repv/unlocks.py      # writes research/repv/unlock_base.csv
Educational only - not financial advice."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from audit import ACCOUNTS, bucket, load  # noqa: E402

DAYS = ("2026-11-05", "2026-11-06", "2026-11-09", "2026-11-10")
RISK_STAGE = ("setup_cap", "account_halt", "latch", "twin", "one_per_symbol", "split_gate", "borrow", "slots")


def main():
    rows = []
    for acct, (branch, tag) in ACCOUNTS.items():
        sig, tr = load(branch)
        s = sig[(sig.run_id == 1) & sig.day.isin(DAYS)].copy()
        s["b"] = [bucket(a, r) for a, r in zip(s.status, s.reason)]
        w = tr[(tr.run_id == 2) & tr.date.isin(DAYS)]
        n = s.day.nunique()
        c = s.b.value_counts()
        down = c.get("taken", 0) + c.get("spread_crosscheck", 0) + c.get("cost_filter", 0) + c.get("buying_power", 0)
        pass_rate = c.get("taken", 0) / down if down else 0
        bp_share = c.get("buying_power", 0) / down if down else 0
        for b, k in c.items():
            if b == "taken":
                continue
            conv = pass_rate if b in RISK_STAGE else (1 - bp_share) if b == "cost_filter" else 1.0 if b == "buying_power" else None
            wb = w[w.bucket == b]
            rows.append({"account": acct, "tag": tag, "sessions": n, "bucket": b, "lost_per_session": round(k / n, 1),
                         "conversion": None if conv is None else round(conv, 2),
                         "extra_entries_per_session": None if conv is None else round(k / n * conv, 1),
                         "setups_hit": int(s[s.b == b].strategy.nunique()),
                         "whatif_avg_r": round(float(wb.r.mean()), 3) if len(wb) else None, "whatif_n": len(wb)})
        rows.append({"account": acct, "tag": tag, "sessions": n, "bucket": "taken",
                     "lost_per_session": round(c.get("taken", 0) / n, 1) if n else 0, "conversion": round(pass_rate, 2)})
    U = pd.DataFrame(rows)
    U.to_csv(HERE / "unlock_base.csv", index=False)
    pd.set_option("display.width", 220)
    print(U.sort_values(["account", "extra_entries_per_session"], ascending=[True, False]).to_string(index=False))


if __name__ == "__main__":
    main()
