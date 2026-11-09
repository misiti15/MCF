Educational only — not financial advice.

# Exposure Lab (owner 2026-11-09) — shadow, research only, no orders

Owner 2026-11-09: give every setup in Primary's PV decision, and the rest of the top 20, as much exposure as possible on
11-09 and 11-10. Check whether they work best side by side or get in each other's way. After the 11-10 close, reconfirm
one of PV0 / PV1 / PV2. Primary's setup list is unchanged until then.

**PV names** (research/preval_1107/NOTES.md): PV0 = Primary as is (10 setups); PV1 = Option 1 (opt1b: MF2-FD, MF4-FD and
MF4 base out, 7 setups); PV2 = Option 2 (opt2b: RW3-FD, RW5-FD, L3-fromopen-FD, ST7-FD, NS5, NM-ETF late dip; 6 setups).

## The set (26 setups, 8 GEN)
- **PV setups (11):** RW3-gapdn-rsi5pop-flowsell-short-FD, RW5-heat30-flowsell-rsi5pop-gapdn-short-FD,
  L3-gap-slope-fromopen-FD, ST7-rsi50dn-long-pm-t1s1-FD, NS5-sma50-flush-oversold-long, MF2-open-rsimidhi-flowsell-FD,
  MF4-h40-open-flowsell-FD, MF4-h40-open-flowsell, NS1-rsidip-rsi5pop-long, L3-gap-slope-rsi5hi-FD (Primary) and
  NM-ETF-late-dip-di-long (Live Lab).
- **Top 20 by total R:** last 15 sessions (10-19..11-06), 7 journals, run_id=1, R = pnl_adj / (|entry - stop| x
  shares). Five are already PV setups. The other 15:
  - Testing 1: RW7-FD, L3-lowdist-FD.
  - Testing 2: RW1-FD, NM-MF3.
  - Graveyard: CWT09 bounce g5, CWT09 vwaploss g5.
  - Live Lab: CWT09 vwaploss g10.
  - **8 GEN (flagged; Gen account):** GEN-261020-10, -261021-02, -261028-06, -261022-07, -261026-02, -261026-03,
    -261027-08, -261019-03.
- Top 5: L3-fromopen-FD +54.7R (216 trades), RW3-FD +36.7R (87), RW5-FD +34.0R (98), RW7-FD +21.8R (280), CWT09 bounce
  g5 +20.6R (100).
- **Rule changes inside the 15-session window** (research/ledger.jsonl): 10-29 Primary -2R per-setup latch; 10-30
  Testing cost filter; 11-02 PDL-1a / DM-NS3; 11-03 DM-MF moves / SO-1A / RW3S; 11-04 DM-N3 + UNI1 (Testing 2 top-500
  pool); 11-05 ROLL1 (Explore 1 / Live Lab). The R totals therefore mix rule regimes.

## Part 1 — live exposure for 11-09 / 11-10 (PR #160, merged 08:07 ET 11-09)

**Checks (journals run_id=1, sessions 11-02..11-06):**
- Nothing is benched: no session-rotation bench exists in config, and the 11-06 low-rep review moved 0 setups.
- Room per account:
  - **Gen is the only overloaded account:** 1,065 halt skips, 401 buying-power rejects and 342 per-setup-cap skips.
  - Testing 1 / Testing 2: 0 capacity blocks.

**Owner update (live exposure over shadow, moves OK): TEMPORARY moves (ledger `2026-11-09-expo1109-gen-temp-moves`).**
The 5 set GENs that Gen held back move out for 11-09 + 11-10 and go back to Gen after the 11-10 close:

| setup | Gen blocks, 11-02..11-06 | moves to |
|---|---|---|
| GEN-261021-02 (long) | 161 per-setup-cap skips | Testing 1 |
| GEN-261019-03 (long) | 17 halt skips | Testing 1 |
| GEN-261026-02 (long) | 1 halt skip (its only signal) | Testing 1 |
| GEN-261022-07 (short) | 8 halt skips | Testing 2 |
| GEN-261026-03 (short) | 8 halt skips | Testing 2 |

- Longs go to Testing 1, where the split-tape short gate does not apply to them. Shorts go to Testing 2, which has no
  split-tape gate.
- Every other non-Primary set setup had no capacity block of its own and stays home.
- Primary's list, sizing, stops, latches and exits are unchanged.
- These 2 sessions run under Testing rules (cost filter, scale-out cap, Testing 2's top-500 pool), so they are not
  like-for-like with the Gen record.
- The daily-post leaderboard skips GEN rows outside the Gen scorecard. The 5 count in the Testing totals but are on no
  leaderboard for these 2 days.

## Part 2 — the lab (`mcf/report/exposure_lab.py`)

    python -m mcf.report.exposure_lab --date 2026-11-09 --jobs 4

Engine: the Team's as-live engine (`mcf.report.team` -> `mcf.replay.harness.run_session`, fills=costs,
limit_fill=through, live journaled spreads). Every run uses Primary's rules (`config/default.yaml`) on Primary's universe
for the session. Each setup brings its own block from its home account; sizing keys are dropped. Fills are simulated
from 1-minute bars, not broker fills.

| run | what |
|---|---|
| `alone:<setup>` x 26 | the setup on its own, with a whole Primary account (77 slots, buying power x3.2, -2R latch, -20R halt) to itself |
| `together` | all 26 in one Primary-rules book (one position per symbol, shared slots / buying power / halt; Primary's setup order, then list order) |
| `book:PV0/PV1/PV2` | the three candidate Primary books |

**Output:** `research/exposure_lab/<date>.json`:
- `crowding`: per setup, trades and R alone vs together, the difference, and the reasons it was skipped in the
  together book (held_by_other / daily_loss / slots ...).
- `pairwise` (from the alone runs):
  - same-symbol trades whose holding times overlap, and how many of those are opposite side;
  - correlation of 5-minute changes in marked R (open + closed).
- `books`: each PV book's R, green day, wins, long / short R and worst intraday drawdown (peak-to-trough of the
  5-minute marked R path), with per-setup R and skips.
- `trades`: every simulated trade of every run.

**Partials and runtime:**
- Per-run partials are cached in `data/exposure_lab/<date>/` (git-ignored), so a stopped run resumes where it left off.
- One full-universe run takes about 5-7 min, so the 30 runs take roughly 45-60 min with `--jobs 4`.

**How to read it:**
- A setup that makes less together than alone is being crowded (another setup takes its symbol first, or the shared
  halt / latch stops it).
- Pairs with many opposite-side overlaps actually clash.
- Pairs with high 5-minute correlation stack risk in the same direction.
- This is one session per run. Decide on 11-09 and 11-10 together, and remember 2 sessions is a small sample.

## Schedule
- After the close on 11-09 and 11-10, run by the 16:47 nightly loop (line in research/owner_inbox/2026-11-09.md).
- After the 11-10 run: reconfirm PV0 / PV1 / PV2 from these two sessions, the preval_1107 replay and the journals.

## Smoke check (2026-11-06, `--only pv,together`, cached Team data)
- The PV books reproduce the preval_1107 replay exactly:

  | book | R | trades | worst intraday drawdown |
  |---|---|---|---|
  | PV0 | -24.43 | 57 | -47.26R |
  | PV1 | +12.33 | 59 | -5.64R |
  | PV2 | +10.11 | 54 | -5.79R |

- Together (all 26): +21.77R in 218 trades, worst intraday drawdown -49.84R.
- The alone runs were not part of the smoke. `2026-11-06.json` is that partial output.

## 2026-11-09 — full run (30 runs, 3,654 symbols with bars, `--jobs 4`, exit 0, no code changes)
Shadow, Primary rules for every run, fills simulated from 1-minute bars after costs. One session (SPY +1.75% from open
by 15:21, a strong up day against the shorts).

**PV books:**

| book | R | trades | green | long / short R | worst intraday drawdown |
|---|---|---|---|---|---|
| PV0 (as is) | -17.85 | 33 | no | +1.55 / -19.41 | -19.49R |
| PV1 (opt1b) | +0.19 | 16 | yes | +1.55 / -1.36 | -4.74R |
| PV2 (opt2b) | +1.16 | 17 | yes | +1.99 / -0.83 | -4.97R |

- PV0's loss is almost all MF4-h40-open-flowsell-FD: -16.71R in 16 trades (1 win). The live Primary journal closed
  about -19.2R with MF4-FD at about -17.1R, so the shadow matches live closely.
- PV0 minus MF4-FD and MF2-FD is roughly PV1; PV1 vs PV2 differ by L3-rsi5hi/NS1 vs NM-ETF late dip and ~1R.
- Together (all 26): -15.74R in 89 trades (sum of alone runs -33.4R), worst intraday drawdown -24.29R.
  Together beats the alone sum only because MF4 base is blocked by its own FD twin (see below).

**Crowding (alone -> together; R / trades):**
- L3-gap-slope-fromopen-FD +0.68/10 -> -1.22/8 (5 held_by_other, 23 daily_loss skips; 117 borrow skips in both).
- L3-gap-slope-lowdist-FD +4.41/5 -> +2.62/3 (2 held_by_other).
- NM-ETF-late-dip-di-long +0.99/2 -> 0/0 (2 daily_loss skips: the shared book was already latched/halted).
- L3-gap-slope-rsi5hi-FD +1.37/3 -> +0.45/1.
- Gainers from crowding are the losers being blocked: MF4 base -16.71 -> 0 (17 held_by_other), RW7-FD -2.53 -> +0.74,
  CWT09 vwaploss g5 -2.65 -> -1.12, RW5-FD -1.22 -> -0.11.

**Pairwise conflicts (alone runs):**
- MF4-h40-open-flowsell x MF4-h40-open-flowsell-FD: 16 same-symbol overlaps, corr 1.00 — the same trades twice.
- The three L3 gap-slope variants stack: fromopen x rsi5hi 9 overlaps (corr 0.64), fromopen x lowdist 9 (0.63),
  lowdist x rsi5hi 3 (0.71).
- Only true opposite-side clash: GEN-261021-02 (long) x RW7-FD (short), 2 overlaps, corr -0.31. Small.
- Short-gap-down family (RW1/RW3/RW5/RW7/MF2) overlaps are 1-2 each, corr 0.1-0.6.

**Rule changes in effect:** 11-09 `2026-11-09-expo1109-gen-temp-moves` (5 GENs live in Testing 1/2 for 11-09/11-10);
the lab runs every setup under Primary rules regardless. One session only — decide with 11-10.
