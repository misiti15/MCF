"""Write backlog_updates.jsonl (status updates for the lead; research/backlog.jsonl is not modified) from results.csv.
Educational only - not financial advice."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path("/home/user/MCF"); OUT = Path(__file__).resolve().parent
R = pd.read_csv(OUT / "results.csv")
BL = {e["id"]: e for e in (json.loads(x) for x in (ROOT / "research/backlog.jsonl").read_text().splitlines() if x.strip())}


def line(c):
    t, v = R[(R.config == c) & (R.split == "train")].iloc[0], R[(R.config == c) & (R.split == "valid")].iloc[0]
    return (f"{c}: skips {v.skip_share:.0%}; train delta {t.delta:+.4f}R/trade (t {t.t_delta:.2f}), valid {v.delta:+.4f} (t {v.t_delta:.2f}), "
            f"valid excess vs random skip {v.excess:+.4f} (t {v.t_excess:.2f}), valid up/flat/down {v.delta_up:+.4f}/{v.delta_flat:+.4f}/{v.delta_down:+.4f}")


cands = R[R.verdict == "CANDIDATE"].config.unique()
assert not len(cands), "a candidate exists: write a finalist entry instead"
common = ("History test research/bdi/bdi1019 (PLAN.md pre-declared; 23 configs, bar 2.50; 45 Primary/Testing-1 setups, 366,240 "
          "history entries, train <= 2025-12 n 171,078 / 234 days parent -0.065R, valid 2026-01..10-07 n 195,162 / 192 days parent "
          "-0.026R; costs in; skipped trade = 0 R; locked block not read; no holdout scored). 0 of 23 pass. ")
A = [c for c in R.config.unique() if c[0] in "ACD"]
B = [c for c in R.config.unique() if c[0] == "B"]
best = R[R.split == "valid"].sort_values("t_delta", ascending=False)
out = []
for eid, cfgs, extra in (
        ("nightly-1019-index-chase-veto", A,
         "Chase veto (QQQ/SPY x 30/60 min x 0/0.2/0.4%), near-extreme variant (0.10/0.15/0.25%) and late chase after 11:00. "
         "Best: " + line("D-chase-QQQ-60m-0.2-after1100") + "; also " + line("A-chase-SPY-60m-0.2") + ". "
         "The improvement is mostly less exposure to a negative book: vetoed trades are no worse than a random skip of the same "
         "share (excess t <= 1.14 in every config), and the veto helps in up sessions and hurts in down sessions (regime bet). "
         "No per-setup row passes the per-setup bar 3.73 (23 x 45). "),
        ("gb-1019-post-peak-index-guard", B,
         "Tested as a history proxy WITHOUT the account-peak condition (book peaks are not reproducible on history): after 10:30 skip "
         "entries against QQQ/SPY's move from the open (0/0.25/0.5%). Best: " + line("B-against-QQQ-fo-1030-0.00") +
         "; " + line("B-against-QQQ-fo-1030-0.25") + ". Train-only effect; valid t <= 1.42, not better than random skip, "
         "negative in valid down sessions. ")):
    e = dict(BL[eid])
    e["status"] = "failed"
    e["configs_tried"] = int((e.get("configs_tried") or 0) + len(cfgs))
    e["tested"] = "2026-10-19"
    e["evidence"] = "research/bdi/bdi1019/NOTES.md, results.csv, by_setup.csv"
    e["notes"] = common + extra + "Rework ideas (rule 18): long-only setups / side-specific veto; regime-conditional version. Educational only - not financial advice."
    out.append(e)
(OUT / "backlog_updates.jsonl").write_text("".join(json.dumps(e) + "\n" for e in out))
print("\n".join(json.dumps(e)[:600] for e in out))
