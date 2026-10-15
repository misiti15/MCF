"""Append OPP 2026-10-14/15 entries to research/backlog.jsonl (idempotent by id). Educational only - not financial advice."""
import json
from pathlib import Path

ROOT = Path("/home/user/MCF")
B = ROOT / "research" / "backlog.jsonl"
SRC = "OPP 2026-10-15 (research/bdi/opp1014/NOTES.md)"
E = " Educational only - not financial advice."
COMMON = "opp1014.py, pre-declared in PLAN.md; open two-year history (locked block never loaded), production + tod costs, x3 extended tier; study N 65 (bar 2.89), "
new = [
    {"id": "opp1014-rw2-opposite-long", "title": "RW2 never-worked as an opportunity: go long at the RW2-FD short signal, or reverse long at its t1s1 stop (all stops / never-worked stops)",
     "category": "setup", "parent": "bdi1014-rw2-extension-floor", "tags": ["owner-opportunity", "rw2", "opposite-side", "sar", "never_worked", "opp"],
     "hypothesis": "RW2-FD short losers recur as never_worked (4 sessions); if the exhaustion short fails, the move continues up, so the long side (at the signal or at the stop) should pay.",
     "status": "failed", "configs_tried": 11,
     "notes": COMMON + "lineage N 934,993 (bar 5.24). 22,187 RW2-FD signals (base short t1s1 -0.062R, sim = frame), 40% stopped, 47% of stops never worked (MFE < 0.25R). 0 of 11 exp > 0: A1 long at signal -0.051..-0.074R (t -3.7..-6.5; excess vs same-minute control +0.02R, t 2.1-3.1); A2 long at stop -0.074..-0.120R (n 8,761); A3 never-worked stops -0.070..-0.127R (n 4,142). Long legs ~0 in up sessions, -0.14..-0.47R in down. Both sides of the RW2 signal lose after costs: the signal has no direction." + E},
    {"id": "opp1014-rw2-continuation-short", "title": "RW2 failed-extension continuation: after the RW2 short's stop, short the first VWAP loss or lower low (t1s1 / t2s1 / eod-s1; all or never-worked stops)",
     "category": "setup", "parent": "bdi1014-rw2-extension-floor", "tags": ["owner-opportunity", "rw2", "continuation", "never_worked", "opp"],
     "hypothesis": "When the post-stop extension itself fails (first VWAP loss or lower low), the exhaustion short's thesis comes back with a better entry.",
     "status": "failed", "configs_tried": 12,
     "notes": COMMON + "lineage N 934,993 (bar 5.24). 0 of 12 exp > 0. Best LL (all) t1s1 -0.064R (n 7,574, t -3.09, excess +0.006); VL (all) t1s1 -0.118R (n 2,505). Down sessions +0.09..+0.24R, up sessions -0.17..-0.43R: regime-driven, no edge over the same-minute control (|excess t| < 1.9)." + E},
    {"id": "opp1014-st2-skipped-sameday-rebound", "title": "ST2 skipped stocks as an opportunity: same-day rebound long on adv >= $95M names down >= 3/4/5/6% from the open (H5 = 5-min high reclaim, VW = VWAP reclaim, MR = H5 + 0.5 ATR below VWAP), 10:30-15:00, t05s1 / t1s1",
     "category": "setup", "parent": "bdi1014-st2-wrong-side", "tags": ["owner-opportunity", "st2", "rebound", "wrong_side_after_big_swing", "opp"],
     "hypothesis": "Stocks already >= 3% below the open (ST2's wrong-side losers) mean-revert once a reversal trigger prints.",
     "status": "failed", "configs_tried": 24,
     "notes": COMMON + "lineage N 120,542 (bar 4.84). 0 of 24 exp > 0. Best VW down>=3% t1s1 -0.024R (n 22,818, t -1.05) and t05s1 -0.029R (t -2.15). VW beats the same-minute random control by +0.04..+0.066R (t 2.2-4.4) and the down-X base rate (-0.04..-0.05R) by ~+0.02R, but stays negative after costs. Up sessions +0.04..+0.18R, down -0.03..-0.19R; WF 0.06-0.47. Rework idea: VW with an index-up gate (counts as a new lineage step)." + E},
    {"id": "opp1014-st2-skipped-nextday-rebound", "title": "ST2 skipped stocks, next day: after a day closing >= 3/4/5/6% below its open, buy the next open or 09:50 and exit same day (EOD or t1s1); gap-fade reference (gap <= -2%)",
     "category": "setup", "parent": "bdi1014-st2-wrong-side", "tags": ["owner-opportunity", "st2", "rebound", "next-day", "gap-fade", "opp"],
     "hypothesis": "Large intraday losers rebound the next session (short-term reversal), especially after a gap down.",
     "status": "failed", "configs_tried": 18,
     "notes": COMMON + "lineage N 120,542 (bar 4.84). 8 of 16 B2 configs exp > 0 (all EOD exits), none meets the Testing bar. Best 09:50 EOD down>=6%: +0.462R (R = 0.25 ATR, n 6,123, t 1.44, win 54%); excess vs same-day universe +0.20R (t 2.59); train +1.01 / valid +0.03; up +1.51 / down -0.45; WF 0.53. April 2025 (tariff crash/rebound) carries it: down>=5% 09:50 EOD is +3.82R over 968 trades that month and +0.066R over the other 8,578. t1s1 exits all negative (-0.05..-0.18R). Gap-fade reference: EOD -0.028R, t1s1 -0.215R. Next-day gap-down subset is stronger (down>=5% open EOD +0.64 vs gap-up +0.15) - same April caveat. Rework idea: market-regime gate known at the open (e.g. SPY prior-day <= -2%), ex-April-2025 check first." + E},
]
es = [json.loads(l) for l in B.read_text().splitlines() if l.strip()]
have = {e["id"] for e in es}
for n in new:
    n = {"added": "2026-10-15", "source": SRC, "module": None, "variant": None, **n}
    if n["id"] in have:
        es = [n if e["id"] == n["id"] else e for e in es]
    else:
        es.append(n)
B.write_text("".join(json.dumps(e) + "\n" for e in es))
print(len(es), "entries")
