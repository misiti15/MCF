Educational only — not financial advice.

# SO-1A: how much of PDL-1a (R2A) depends on the half-off, and what the 2/day scale-out cap leaves

Owner item SO-1A (11-01: "needs more data + explanation; leave the cap on"). Research only: no config, ledger or backlog
change. Harness = regime-day (`build.py` here is regime-day/build.py for p05 only, plus a no-half-off sim and the bar at
which each trade reaches the half-off level; `score.py` scores). Costs in. TRAIN = 2024-10 + 2025-03..12, VALID =
2026-01..03 + 2026-07..09-15 (348 sessions). The locked block 2024-11..2025-02 and HOLD months 2026-04..06 / 2026-10
were never loaded (asserted in both scripts).

**Configurations: 4** (the 3 asked + SO1A-4, the cap as the live runner actually applies it). Lineage N 121,705 + 4 =
121,709; BAR90 bar t >= 4.355 (unchanged). None passes; none was meant to be a candidate.

## Results (18,912 trades, 54.3 per session; avg R per trade)

| id | half-off on | TRAIN | VALID | day t (T+V) | months + | win % | avg win / avg loss | avg R w/o best day (share) |
|---|---|---:|---:|---:|---:|---:|---:|---|
| SO1A-1 | every trade (as researched) | +0.0031 | +0.0071 | 1.14 | 76.5% | 84.9 | +0.090 / -0.472 | +0.0041 (17%) |
| SO1A-2 | none (plain bracket: 3x stop, +0.5 R1 target) | -0.0047 | +0.0054 | -0.02 | 47.1% | 73.2 | +0.157 / -0.429 | -0.0014 (total < 0) |
| SO1A-3 | first 2 per session by signal time | -0.0035 | +0.0056 | 0.08 | 47.1% | 73.6 | +0.154 / -0.428 | -0.0006 (best day 212% of total: `1 day`) |
| SO1A-4 | first 2 per session to reach +0.25 R1 (live cap rule) | -0.0024 | +0.0061 | 0.21 | 47.1% | 73.9 | +0.152 / -0.425 | +0.0002 (best day 86%: `1 day`) |

Best day for every row is 2025-04-09 (tariff-pause rally). Parity with regime-day R2A is exact (+0.0031 / +0.0071, t 1.14,
76.5%, w/o best day +0.0041). The sim's scale flag and the trigger-bar mirror agree on 100% of trades.

## What it means
1. **The half-off is essentially the whole edge.** Over TRAIN+VALID it adds +0.0050 R/trade, and the setup is +0.0049 with it
   and -0.0001 without it (about 100%). By split: TRAIN +0.0078 (more than all of +0.0031: without it TRAIN is negative);
   VALID +0.0017 (24% of +0.0071). Without it the months-positive rate drops from 76.5% to 47.1%.
2. **Why:** 64% of trades touch +0.25 R1 (1/12 of the 3x stop). Banking half there and moving the stop to break-even turns
   many would-be 3x-stop losses into break-even or small wins: win rate 73% -> 85%, avg loss -0.43 -> -0.47 (fewer but
   relatively bigger full losses), full-stop exits only 529 of 18,912. The trade-off is a smaller avg win (+0.157 -> +0.090).
3. **Under the cap R2A is about flat.** SO1A-4 (what live does) is -0.0024 / +0.0061, t 0.21, 47% months positive, and its
   positive total rests on one day. The two capped half-offs are worth more than the average one (+0.042 R each vs +0.006),
   because the first to trigger are early and clean, but 2 of ~29 is too few to move a 54-trade book.

## How many scale-outs R2A wants, and the competition for the 2 slots
- Scale-outs per session (trades reaching +0.25 R1): median 29, mean 34.8, 90th pct 64, max 122; more than 2 on 99.7% of
  sessions. Trades per session: median 47, 90th pct 100.
- The 2 slots are used up by about 10:00 ET (2nd trigger median 10:00, 10th-90th pct 09:55-10:20); every later R2A trade runs
  on the plain bracket.
- Competition in Testing 2: today R2A-long / -short are the only **enabled** Testing 2 setups with `live_scale_out: true`
  (7 others carry the flag but are disabled), and exactly one R2A leg fires per day. So R2A gets both slots; nothing else
  competes now. If a scale-out setup is enabled in Testing 2 later, it shares the same 2 per day (the cap counts the
  account's banked `-s` orders, first to trigger wins) and, since R2A triggers ~29 times a day from 09:55, R2A would take
  most slots first.

## For the decision (owner)
- Cap on (current): R2A's live record will measure roughly SO1A-4 (~0 R), not the researched +0.005. It is not a fair test of
  the researched setup.
- Exempt R2A: live would try ~29 (up to ~64) half-offs a day with the new cancel/bank/protect method; that is the volume
  the SO1 cap was set to avoid until the first live scale-outs are checked.
- Either way the researched edge itself is small (t 1.14 vs bar 4.355) and comes almost entirely from the half-off.

Files: `build.py` (cache built in scratch, deleted), `score.py`, `results.csv`, `results.json`, `score_out.txt`.
