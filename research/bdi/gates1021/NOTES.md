> **CORRECTION 2026-10-22 (research/bdi/regime1022):** the "prior-session SPY" input used here was the day's own close-to-close move (lookahead), not the prior day. Re-scored with the real prior day, all six U7 finalists fail (t 0.04-2.17 vs bar 3.63) and the "stable up-prior-day" finding disappears. Decision G1 is withdrawn (R1). The findings below that rely on U7 or prior-day SPY are void.

# gates1021: why NS3-FD and L3-FD lost on 2026-10-21, and a direction check-gate layer (owner request 2026-10-21)

*Educational only - not financial advice. Unless a line says "paper" or "live", the numbers are backtests on the
open two-year history. Live-day numbers come from the Primary paper journal (origin/mcf-data, run_id 1, as of
14:36 ET). Costs are always in: production cost, time-of-day entry cost and x3 on the extended tier. The locked
block 2024-11-01..2025-02-28 was never read, and no holdout was scored. `PLAN.md` was written before any scoring
and has not been changed since.*

**Configurations: 718 in total.**
- Part A: 32 (2 setups x 16).
- Part B: 14 gates x 49 covered setups = 686.
- Study bar: max(1.5, sqrt(2 ln 718)) = **3.63** on the day-clustered t.
- NS3 lineage (swarm1017 rework-ns, 165,764 configurations): bar 4.90.

TRAIN = sessions up to 2025-12-31. VALID = 2026-01-01..2026-10-07.

## Failures first
- **Part A: 0 of 30 tweaks pass.** A pass needs three things together: at least 80% of the parent's trades kept,
  better avg R on both train and valid, and a pooled t of at least 3.63. All 32 rows are in `results_A.csv`.
  - NS3-FD, best tweak: *skip when the stock's 5 most-correlated peers are up at least 1% (median)*.
    - Keeps 95% / 94% of trades.
    - avg R +0.009 / -0.020, against the parent's -0.005 / -0.021.
    - t 3.01, below the bar. It also needs live code.
  - L3-FD, best tweak: *no entries before 10:30*.
    - Keeps 93% / 93%.
    - avg R -0.022 / -0.023, against -0.032 / -0.029.
    - t 2.64.
- **Tweaks that would have saved money today are worse on two years.** They lower avg R, or block 35-80% of the
  trades and fail participation:
  - one lot per symbol;
  - first signal only (refire off);
  - a cap on the setup's open lots;
  - the -2R daily stop;
  - QQQ-up skips.
- **NS3-FD, skip when QQQ is at least +0.25%:** better on train (+0.045 vs -0.005), worse on valid (-0.043 vs -0.021).
  It does not hold up.
- **Both parents lose money on two years, even as they run live.** Live means refire cd1 plus the lot cap of 3.
  - NS3-FD: -0.015R per trade (n 16,955, t -0.63).
  - L3-gap-slope-fromopen-FD: -0.031R (n 25,124, t -0.62).
  - L3 looked about +0.02R in refire1014, which had no extended-tier cost. Its many sub-$5 and big-gap names cost 3x.
- **Every gated variant below still has negative avg R on valid after costs.** The gates only remove each setup's
  worst market state. They improve a losing setup; they do not make it a winner.
- **The finalist gates are about 75-100% market beta.** The same gate applied to random same-minute shorts gains
  about as much (`robust.csv`, beta_share). They are honest *direction* gates, not setup-specific edges.
- **The finalist gate would not have fired today.**
  - The gate is: SPY's prior session at least +0.5% and SPY at least +0.25% from the open.
  - SPY on 10-20 closed only +0.34% over 10-19 (10-19 was +0.42% over 10-16).
  - So it would have blocked nothing on 10-21.
- **Coverage gaps.** 40 of the 93 live setup slots are not covered, because their outcome is not in the frames:
  - 23 CWT / opening-range setups that need the 09:35-09:45 rows;
  - 7 classic setups (IDX, orb20_a, intraday_momentum);
  - 3 with structural S exits;
  - 3 holdtr LD setups;
  - 2 RW6G1 (1-minute VWAP-band guard);
  - 2 ETF allow-list setups.
  - Details in `setups_used.csv`.
- **The Part A sim models this setup alone.** It does not model other setups' lots, portfolio caps, ETB/spread skips
  or fill slippage.

## A. What happened today (paper, Primary; `today_trades.csv`, `today_paths.csv`, `today.json`)
**NS3-failed-vwap-reclaim-short-FD:** 25 lots on 17 names.
- 6 closed, all stopped:
  - ROIV 10:06 → 10:07
  - CLSK 10:35 → 13:35
  - HUT 10:50 → 13:53
  - RIOT 11:16 → 13:53
  - FPS 11:40 → 13:30
  - RIOT 11:51 → 13:52
  - Total -6.2R, -$256 adjusted (journal pnl_adj; the owner's -$244 is unadjusted).
- 19 lots open, about -$225 unrealized at 14:36 (status.json, split evenly across each position's lots).

**L3-gap-slope-fromopen-FD:** 5 lots, all stopped, -5.4R, -$177 adjusted.
- FTNT 10:40, 11:20, 11:30
- TKNO 11:46, 12:06

- **Re-entry after a stop: none.** No same-symbol entry came after that symbol was stopped. Every "repeat" was a
  **stacked lot** while the earlier lot was still open: RIOT x2, FTNT x3, TKNO x2, CIFR x3, SKHY x3, NBIS x2,
  AKAM x2, AAOI x2, CBRS x2, JD x2. The stacked lots then stopped together.
  - NS3: 10 of 25 lots were 2nd or 3rd lots.
  - L3: 3 of 5.
- **Correlated cluster.** The crypto-miner and AI-infrastructure names squeezed together from 13:00 to 14:00, which
  hit all four miner stops within 23 minutes (13:30-13:53). From-open moves at 13:00 → 14:00:
  - CIFR -3.9 → -1.0
  - RIOT -1.6 → +0.8
  - HUT -3.8 → -1.1
  - CLSK -2.3 → +0.1
  - IREN +0.7 → +2.5
  - MARA +0.5 → +2.2
  - WULF +1.4 → +2.9
- **Peers were not up at entry.** The stocks' peer medians were -2% to -4% when the shorts were taken, so a "peers
  up together" gate would not have fired. The move came *after* entry.
- **L3 faded strong gap-down recoveries that kept going.** FTNT was +4.1% from the open at the first lot and +5.35%
  by 13:30. TKNO went from +6.6% to +9.2%.
- **Market at entry.**
  - The early NS3 entries (10:05-11:16) came while SPY was -0.27..+0.03% from the open and QQQ -0.09..+0.34%: a flat
    or slightly down tape at the time.
  - The later entries (11:40-14:35) came with SPY +0.19..+0.41% and QQQ +0.5..+0.73%, with breadth 0.58-0.71.
  - The stopped lots were entered at SPY -0.17..+0.19%. The tape turned up *after* entry: SPY went from -0.23% at
    10:30 to +0.36% at 13:30.
  - Both 10-20 and 10-21 were up days: SPY open-to-close +0.41% and +0.40% so far.
- **Time of day.** Entries ran from 10:05 to 14:35, and all the damage came from entries made between 10:05 and 12:06.

**Would a per-setup -2R daily stop have helped today? No.**
- NS3-FD reached -2R realized only at 13:30 (FPS). Its big losses were lots already open, which stopped between
  13:30 and 13:53. The stop would have blocked only the 4 late lots (CBRS x2, JD x2), which are about +$13 now.
- L3-FD reached -2R at 13:03, after its last entry (12:06), so the stop changes nothing.
- A realized-loss stop is too slow for correlated lots that all stop within the same half hour.
- On two years it also hurts. As live (Part A g8):
  - NS3-FD -0.049R vs -0.015R;
  - L3 -0.104R vs -0.031R;
  - with only 65% / 26% of trades kept.
- What would have helped today is capping the setup's open lots (e.g. at most 5 at once: -$87 instead of -$482).
  On two years that cap lowers NS3's avg R (-0.044 vs -0.015) and blocks 68-79% of the trades. Today's fix is not
  a fix over two years.

### Do these setups do better on down days? (descriptive, A0 trades; `states_A.csv`, train / valid avg R)
| state | NS3-FD | L3-fromopen-FD |
|---|---|---|
| hindsight day: down / flat / up | **+0.152 / +0.053**; -0.108 / -0.047; **-0.241 / -0.112** | -0.048 / +0.136; +0.003 / +0.003; -0.033 / -0.111 |
| at entry: SPY from open <= -0.5% | +0.115 / **-0.196** (flips) | -0.201 / +0.030 (flips) |
| at entry: SPY from open >= +0.5% | -0.166 / -0.003 | +0.058 / +0.012 |
| at entry: QQQ from open >= +0.5% | -0.132 / +0.011 | +0.021 / +0.023 |
| prior session SPY <= -0.5% | +0.190 / +0.016 | -0.095 / +0.112 |
| prior session SPY >= +0.5% | -0.128 / -0.033 | **-0.239 (t -3.9) / -0.186 (t -3.2)** |

- **With hindsight, yes: both are short-side regime bets.** NS3-FD earns on days that end down and loses on days
  that end up.
- **The state at entry does not tell you which kind of day it is.** SPY or QQQ from the open flips sign between
  train and valid. This matches direction1020: the rest of the day is close to unknowable at 10:00-11:00.
- **The only at-entry signal stable on both splits is an up prior session.**
  - For L3, the prior day alone is strong. Prior-day-only was not a pre-declared gate, so it is **untested** and
    goes to the backlog as an idea.
- **Stacking on two years** (`stacking_A.csv`):
  - NS3's 2nd and 3rd lots are not worse than its 1st lots (lot 1 -0.028 / -0.036, lot 2 +0.050 / -0.004).
  - L3's re-entries after a stop are about 0R, the same as everything else.
  - Losses are concentrated by day. L3's 105 days at or below -5R carry -3,609R, against -767R in total.

## B1. Short list: setup → unfavourable state (stable on train and valid; `shortlist_B1.csv`)
**15 of 49 setups have a real, stable split.** That means at least one state with gate-delta t ≥ 2.0 on train and
≥ 1.0 on valid, positive on both, and at least 3% of trades. That is 32 setup-state pairs in all.

- **All are shorts except NS1-FD (long).**
- **For shorts, the favourable state is "not a continuing up-tape."** The recurring unfavourable states:
  - **U7**: prior SPY session at least +0.5% *and* SPY at least +0.25% from the open now. This is in 13 of the 15.
  - **U4 / U2**: QQQ or SPY at least +0.25% from the open while breadth is rising.
  - **U5 / U6**: breadth at least 0.65, or rising by at least 10 points.
- No market-down state is unfavourable for any short.

| setup (account) | unfavourable state(s) → favourable = everything else |
|---|---|
| NS3-failed-vwap-reclaim-short-FD (P) | U7 |
| MF4-h40-open-flowsell (P) | U7 |
| MF4-h40-open-flowsell-FD (P) | U7, U4, U5, U6 |
| MF1-945-flowsell-vwapup (P) | U5, U6 |
| RW3-gapdn-rsi5pop-flowsell-short-FD (P) | U7, U2, U4, U6 |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD (P) | U7 |
| MF3-open-flowsell-rsi5hi-FD (T1) | U7, U1, U2, U4 |
| MF5-flowsell-vwapup-rsi5hi (T1, T2) and -FD (T2) | U7, U4 |
| RW4-ns3-adv150-short-FD (T1, T2) | U7 |
| RW7-gapdn-bounce-early-short-FD (T1) | U7, U2, U4 |
| exhaustion_short-FD (T1, T2) | U7, D3 (QQQ ≤ -0.5%) |
| NS1-rsidip-rsi5pop-long-FD (T1, long) | D7 (prior SPY ≤ -0.5% and SPY ≤ -0.25% now) |
| RW1-gapdn-bounce-flowsell-short-FD (T2) | U7, U2, U4 |
| L3-gap-slope-rsi5hi-FD (T2) | U7 |

- **L3-gap-slope-fromopen-FD is not on the list.** Its U7 split (no lot cap) does not reach t 2.0 on train,
  despite the prior-day pattern above.

## B2. Finalists: one check-gate each, ready as testing-account candidates
**Gate: U7.** Skip a new short while SPY's prior session closed at least +0.5% *and* SPY is at least +0.25% from
today's open.
- It needs **one small piece of live code**: a `spy_prev` context column (SPY's prior-session close-to-close
  return). LabStrategy's context today has spy_fo, qqq_fo and breadth only.
- Without it, the modules fail safe: the gate never blocks, and the setup trades exactly like its parent.

| new setup | module | parent (acct) | kept % train / valid | winners blocked % | train avg R parent → gated (t) | valid avg R parent → gated (t) | gate Δ t pooled | choppy days: blocked %, Δ R | quarters + | beta share |
|---|---|---|---|---|---|---|---|---|---|---|
| MF4-h40-open-flowsell-FD-g1 | `modules/MF4-h40-open-flowsell-FD-g1.py` | MF4-h40-open-flowsell-FD (P) | 87.3 / 86.5 | 11.1 / 12.2 | -0.119 → -0.108 (-3.44) | -0.051 → -0.039 (-1.79) | 4.80 | 2.6%, -0.000 | 8/9 | 0.75 |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD-g1 | `modules/RW5-...-FD-g1.py` | RW5-...-FD (P) | 86.3 / 84.3 | 8.9 / 12.2 | -0.054 → -0.011 (-0.32) | -0.066 → -0.032 (-0.86) | 4.78 | 2.2%, +0.004 | 9/9 | 0.76 |
| MF3-open-flowsell-rsi5hi-FD-g1 | `modules/MF3-open-flowsell-rsi5hi-FD-g1.py` | MF3-...-FD (T1) | 84.6 / 83.5 | 12.7 / 15.0 | -0.099 → -0.071 (-2.76) | -0.051 → -0.038 (-1.38) | 4.62 | 3.2%, -0.002 | 9/9 | 0.97 |
| RW7-gapdn-bounce-early-short-FD-g1 | `modules/RW7-gapdn-bounce-early-short-FD-g1.py` | RW7-...-FD (T1) | 89.0 / 87.7 | 7.9 / 11.0 | -0.083 → -0.053 (-2.02) | -0.040 → -0.025 (-0.78) | 4.12 | 2.0%, +0.000 | 9/9 | 1.02 |
| RW3-gapdn-rsi5pop-flowsell-short-FD-g1 | `modules/RW3-gapdn-rsi5pop-flowsell-short-FD-g1.py` | RW3-...-FD (P) | 88.6 / 88.2 | 9.3 / 9.6 | -0.095 → -0.073 (-2.39) | -0.045 → -0.022 (-0.61) | 4.09 | 1.5%, +0.001 | 9/9 | 0.96 |
| RW1-gapdn-bounce-flowsell-short-FD-g1 | `modules/RW1-gapdn-bounce-flowsell-short-FD-g1.py` | RW1-...-FD (T2) | 89.1 / 88.7 | 7.7 / 9.7 | -0.073 → -0.045 (-1.57) | -0.026 → -0.009 (-0.25) | 3.95 | 1.4%, -0.001 | 9/9 | 1.00 |
| *near-miss, not a candidate:* NS3-failed-vwap-reclaim-short-FD-g1 | `modules/NS3-failed-vwap-reclaim-short-FD-g1.py` | NS3-...-FD (P) | 86.3 / 83.8 | 10.7 / 15.4 | -0.004 → **+0.024** (0.51) | -0.016 → -0.006 (-0.22) | 2.98 (< 3.63) | 2.9%, +0.001 | 8/9 | 1.63 |

- **Choppy days are barely touched.** The gate blocks only 1.4-3.2% of the trades taken on choppy days
  (|SPY o→c| < 0.3%), and its effect there is about 0. It does not keep these setups out of flat markets.
- **The improvement comes from up sessions.** Up-session Δ is +0.06..+0.11R per trade; flat and down are about 0.
- **No single day drives it.** The best day carries 6-14% of the improvement.
- **Parity** (`verify_modules.json`; 2025-06, 2026-02, 2026-07):
  - Every module reproduces every scan signal.
  - The non-refire modules add under 1% extra signals. These are later bars that become the day's first signal once
    the gate blocks an earlier one; they are not in the scoring.
  - NS3-FD-g1 matches exactly (3,068 / 3,068).
- **Near-misses (pass participation and beat the parent on both splits, t below 3.63):**
  - MF1 (U6 breadth surge), 3.04
  - MF4 Primary windowed (U7), 2.48
  - NS3-FD (U7), 2.98
  - MF5 / MF5-FD (U7), 3.50
  - RW4-FD (U7), 2.44
  - exhaustion_short-FD (D3), 2.33
  - NS1-FD long (D7), 3.04
  - L3-rsi5hi-FD (U7), 2.77
  - All are in `finalists_B2.csv`. They are rework items, not candidates.
- **The six finalists are one finding, not six.** They share the same gate and the same market-beta mechanism.
  Their multiple-testing count is already in N.

**YAML to add only if the owner chooses to.** Not applied here: config/ was not touched. Each finalist needs the
`spy_prev` live code first.
```yaml
# e.g. config/account_testing.yaml (strategies:) - copy the parent's block, change the module and add context
  RW5-heat30-flowsell-rsi5pop-gapdn-short-FD-g1:
    enabled: true
    type: lab
    module: research/bdi/gates1021/modules/RW5-heat30-flowsell-rsi5pop-gapdn-short-FD-g1.py
    min_adv: 95000000
    window: [950, 1500]
    context: [spy_fo]          # + spy_prev once the live code exists
    scale_out_r: null
    tags: [gates1021, direction-gate, finalist]
```

## Method notes
- **Signals.** Live-shaped: mask + YAML window ∩ 09:50-15:00, adv20 ≥ min_adv, then the account's refire chain
  (`mcf.strategies.setups.refire_select`).
- **Outcome.** The frame lab outcome converted to production R.
- **Exit times** (Part A lot rules) come from the 5-minute path. They agree with the frame outcome on 100% of
  decided trades.
- **State at entry.** spy_fo, qqq_fo and breadth come from the lab context table. d2 = breadth minus breadth two bars
  earlier, from the 10:00 bar on. Prior-day SPY return is close-to-close, set to NaN across the data gap.
- **Gate Δ** = (gated total R − parent total R) / parent trades, day-clustered.
- **Control** = the mean production R of every adv20 ≥ $95M frame row at the same date and minute, same side and
  geometry.
- **Peers** = the top 5 by train daily-return correlation (non-ETF).
- **Today's bars** are SIP 1-minute bars for 10-20 / 10-21, fetched read-only (`scripts/fetch_today.py`; keys from
  the environment, never written). Scratch data (about 200 MB) lives in the session scratchpad, not in git.

**Files:** all under `research/bdi/gates1021/`.
- `PLAN.md`
- `scripts/`: common, setups, scan, load, part_a, part_b, robust, today, fetch_today, gen_modules, verify_modules,
  gen_backlog
- Outputs: `results_A.csv`, `states_A.csv`, `stacking_A.csv`, `results_B.csv`, `shortlist_B1.csv`,
  `finalists_B2.csv`, `robust.csv`, `counts.json`, `setups_used.csv`, `setups_scored.csv`, `today_*.csv`,
  `today.json`, `verify_modules.json`, `modules.json`, `modules/*.py`
- `backlog_proposals.jsonl` (17 entries: 6 finalists, 9 rework near-misses, 1 failed Part A record, 1 idea). Not
  appended to research/backlog.jsonl.

Educational only - not financial advice.
