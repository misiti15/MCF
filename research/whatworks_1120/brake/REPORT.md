Educational only — not financial advice

**Owner summary**
- **Primary:** none of the loss brakes I tested gives Primary a reliable gain. Its current -2R per-setup latch and -20R cost-in halt already cover the period since 11-12, and in that period no tighter loss brake would have fired. Keep them unchanged.
- **11-17 Gen -134.6R:** no loss brake could have caught it. The setup opened 143 trades in about 6 minutes (10:55–11:01 ET), before any of them had closed. Only a brake that counts entries catches this.
- **Recommendation 1:** a runaway-entry brake in every account: at most 30 new entries per setup in any 10 minutes, then a pause until the window clears. It would never have fired in Primary in 32 sessions, it saves about 103R of the 11-17 case, and it fired on 12 days across all accounts.
- **Recommendation 2:** turn the watchdog "act" mode on in all accounts before any real money. I'd do it now. Gen and the Graveyard carried leftover positions overnight from 11-13 to 11-16, which is exactly the case its "after flatten" check closes.
- **Not recommended:** per-setup loss latches or tighter halts in Testing or Gen. After a setup is down -X R, the rest of its trades that day are no worse than its other trades, so the latch only repeats what the Friday exit rules already do.

## Method
- **Data:** every closed live trade (run 1) from the 10 account journals on the origin/mcf-data* branches, 2026-10-06..11-19. That is 28,118 trades, with real entry and exit timestamps.
  - Trades are not de-duplicated across accounts, because a brake acts per account.
  - R is after costs on the single LR8 basis (`mcf.costs.cost_r_lr8`, per DQ-P3).
  - These totals are lower than `live_trades.pkl`, which carries the booked basis. Primary is -133.4R LR8 vs -87.5R booked; all accounts are -4,242R vs -3,505R.
  - The locked block (2024-11-01..2025-02-28) was not read. MarcoFlow was not called, and no orders were placed.
- **Replay:** trades are processed in entry-time order.
  - A loss brake looks only at cost-in R that was **realized before the entry's timestamp**, from trades it did not itself block. It latches for the rest of the day.
  - Open lots at the trigger run to their real exit, because the journals hold no mark path. Blocked trades are removed whole.
  - Burst brakes count the setup's entries in the previous M minutes. The "losing" variants also require the setup's realized R that day to be below 0.
- **Metrics for each brake and scope:**
  - Blocked trades, R saved (blocked losers), R forgone (blocked winners), net, and days triggered, better and worse.
  - One-big-day check: net without the best day, and the best day's share of the net.
  - Per-setup better/worse count, with total and worst harm.
  - Two selectivity tests. **Edge vs random** asks whether the brake beats blocking the same number of random trades in that scope. **Edge vs same-setup rest** is stricter: it asks whether the blocked trades are worse than that setup's own other trades.
  - The selectivity tests matter because the overall book is negative (-0.15R per trade), so blocking almost anything "saves" R.
- **Sanity check:** `open_cap_30` blocks 0 Primary trades, which matches Primary's live per-setup cap of 30.
- **Limits:**
  - Trades the live brakes already blocked are not in the record, so looser brakes cannot be tested in Primary or the Graveyard. Those live brakes are Primary's -2R latch from 10-29 (254 signals blocked) and its halt (95), plus the Graveyard's -2R latch and 120R halt.
  - Without marks, the replay does not include open-lot losses.

**Rule changes inside the window (from the ledger):**
- 10-15: Primary's -20R halt fired (raw R).
- 10-22: ST-A switched the latch off in Testing 1/2 and Gen. The Graveyard kept its -2R raw latch from 10-21.
- 10-29: ST-P put the -2R latch in Primary.
- 11-12:
  - LR3: Primary's latch and halt count cost-in R.
  - LR8: new cost model.
  - Account halts went 120→300R in Testing and Gen.
  - Gen's per-setup cap went 48→150.
  - LR7: watchdog act in Primary.
- 11-17: TSZ1 (Testing half-size lots, cap 100).
- 11-18: GY-BENCH.
- 11-19: C3-EXIT100.

## Results — Primary (1,397 trades, -133.4R LR8)
| brake | blocked | saved | forgone | net R | days +/- | net w/o best day | setups +/- | worst harm | edge vs same-setup |
|---|---|---|---|---|---|---|---|---|---|
| setup stop -2R cost-in | 166 | 76.0 | 54.2 | +21.8 | 9/6 | +2.1 | 9/7 | -4.6 | -21.2 |
| setup stop -3R | 118 | 55.8 | 39.4 | +16.3 | 7/5 | +4.6 | 7/3 | -5.7 | -18.6 |
| setup stop -4R | 59 | 27.7 | 21.8 | +5.9 | 4/4 | -5.8 | 4/2 | -5.7 | -15.3 |
| setup stop -5R | 43 | 24.0 | 16.9 | +7.2 | 3/2 | -4.5 | 3/2 | -5.7 | -7.7 |
| account halt -15R | 83 | 38.6 | 35.4 | +3.3 | 4/3 | +0.3 | 7/7 | -3.1 | -8.8 |
| account halt -10R | 171 | 59.9 | 76.7 | -16.8 | 5/7 | -19.7 | 9/11 | -18.9 | -48.6 |
| cross-account family -4R (2+ accounts) | 125 | 49.5 | 34.1 | +15.5 | 8/4 | +3.8 | 7/3 | -2.6 | -0.6 |
| system halt -100R | 387 | 196.9 | 170.2 | +26.7 | 12/6 | -3.7 | 10/6 | -22.4 | -7.3 |
| burst 10 in 5 min (cooldown) | 24 | 13.7 | 10.6 | +3.0 | 4/2 | -1.7 | 4/2 | -6.2 (L3-fromopen) | +0.5 |
| burst 20 in 30 min (cooldown) | 45 | 27.3 | 15.9 | +11.4 | 3/2 | +0.3 | 3/2 | -9.7 | +4.1 |
| **burst 30 in 10 min (cooldown)** | **0** | 0 | 0 | **0** | 0 | 0 | 0/0 | 0 | — |
| open-lot cap 15 per setup | 110 | 50.3 | 43.2 | +7.2 | 10/3 | -7.6 | 7/3 | -22.7 | +0.3 |
| entry cap 20 per setup per day | 131 | 51.8 | 45.6 | +6.2 | 8/4 | -8.9 | 6/3 | -25.0 | -6.6 |

**By rule period:**
- Nearly every Primary gain comes from 10-06..10-28, before the latch existed. The setup stop -2R adds +22.8R there.
- 10-29..11-11 (latch on, raw R): -1.0R to -5.7R.
- 11-12..11-19 (latch and halt on cost-in R): 0 trades blocked.
- The burst brake (20 in 30 min) was +11.6R, then +9.5R, then -9.7R in the latest period.
- An entry cap of 20 was -25.0R since 11-12; the L3-fromopen winner is hit.
- The best day is usually 10-15 (NS2, -29.2R in 42 trades).

## Results — all accounts (28,118 trades, -4,242R)
| brake | blocked | net R | days +/- | net w/o best day | best-day share | setups +/- | R harmed | edge vs random | edge vs same-setup |
|---|---|---|---|---|---|---|---|---|---|
| setup stop -2R | 4,467 | +683 | 24/8 | +527 | 0.23 | 105/56 | -260 | +9 | -225 |
| setup stop -4R | 2,158 | +416 | 23/8 | +277 | 0.33 | 66/29 | -123 | +90 | -73 |
| setup stop -8R | 897 | +193 | 13/8 | +137 | 0.29 | 35/13 | -44 | +58 | -12 |
| account halt -20R | 8,538 | +1,211 | 24/5 | +1,034 | 0.15 | 155/83 | -366 | -77 | -42 |
| account halt -40R | 4,744 | +649 | 17/7 | +495 | 0.24 | 113/64 | -283 | -67 | -92 |
| cross-account family -4R | 6,591 | +1,031 | 22/5 | +672 | 0.35 (11-17) | 112/62 | -227 | +36 | +149 |
| system halt -100R | 6,580 | +940 | 16/4 | +709 | 0.25 | 176/110 | -477 | -53 | +256 |
| burst 10 in 5 min (cooldown) | 2,660 | +629 | 25/5 | +443 | 0.30 | 71/37 | -215 | +228 | +148 |
| burst 10 in 10 min (cooldown, losing only) | 1,131 | +227 | 21/7 | +146 | 0.35 | 50/23 | -113 | +56 | -17 |
| burst 20 in 15 min (cooldown) | 2,129 | +439 | 24/5 | +258 | 0.41 | 60/25 | -165 | +118 | +30 |
| **burst 30 in 10 min (cooldown)** | **632** | **+199** | 12/5 | +86 | 0.57 (11-17) | 26/10 | -72 | — | +26 |
| burst 40 in 10 min (cooldown) | 306 | +111 | 7/5 | +9 | 0.92 | 9/7 | -38 | — | +13 |
| open-lot cap 30 per setup | 1,539 | +211 | 15/9 | +92 | 0.57 | 32/21 | -176 | -21 | -25 |
| entry cap 30 per setup per day | 5,276 | +735 | 23/7 | +579 | 0.21 | 62/28 | -201 | -61 | -41 |

**Burst 30 in 10 min by scope:**

| scope | net R | blocked | setups +/- |
|---|---|---|---|
| Primary | 0 | 0 | — |
| Gen | +141.1 | 370 | 10/3 |
| Graveyard | +34.5 | 125 | 6/4 |
| Testing A–F | +22.9 | 137 | 10/3 |

Biggest harms from burst 30 in 10 min fall on two bursty Gen winners:

| setup | harm | its total R |
|---|---|---|
| GEN-261021-02 | -31.5R | +37.2R |
| GEN-261020-09 | -25.8R | +49.4R |

**What the selectivity tests show:**
- **Loss brakes** (setup stops and halts) are negative against the same-setup baseline at every level. They save R only because they land on setups that are bad all day anyway.
- **Burst brakes** do target a failure mode. Entries of one setup within 5 minutes share 39% of their R variance (10% when shuffled), so a burst is mostly one correlated bet. The blocked burst trades average -0.21 to -0.24R, against -0.14R for the trades kept.

## 11-17 Gen case
GEN-261022-09-Ret15mATRlem0p16-…-hold-short: 144 trades, -134.6R. 143 of them entered between 10:55 and 11:01 ET, and nothing had closed at the 6th entry.

| brake | trades blocked of 144 | R saved | what's left |
|---|---|---|---|
| any setup stop (-2R to -8R) or account halt (-10R to -40R) | 1–7 | ≤ 0.9 | -134R |
| burst 10 in 5 min | 133 | 124.7 | -9.9R |
| burst 30 in 10 min | 114 | 103.4 | -31.2R |
| burst 40 in 10 min | 104 | 101.7 | — |
| open-lot cap 30 | 112 | 105.7 | — |
| cross-account family -4R or system halt -100R | 144 | 134.6 | — |

The last row is not a real catch: those brakes had already fired earlier in the day from other setups' losses.

## Recommendation
1. **Runaway-entry brake, all accounts:** at most 30 new entries per setup in any 10 minutes, then a pause until the window clears.
   - It targets the one failure mode no current brake sees: a correlated wave of entries placed before any exit. It is not tailored to one setup.
   - **Primary:** it never fired in 32 sessions.
   - **Testing:** it removes 2.2% of trades. Those are mostly duplicate exposure inside one burst, so testing loses few independent reps.
   - **The 11-17 caveat:** its average gain is carried by 11-17 (best-day share 0.57). Treat it as insurance, not an R improvement.
   - **The tighter 10-in-5 version:** it is more selective (+148R vs the same-setup baseline), but it touches 109 setups and hurts L3-gap-slope-fromopen-FD in Primary (-6.2R). That breaks the "protect what works" principle, so don't use it.
   - Under owner rules this is a setup/exit-adjacent risk change: it needs a backlog entry and a ledger entry, and ships outside market hours.
2. **Watchdog act in all accounts:** yes, and do it before real money. It only flattens on a dead run, stale data, a failed flatten, or exposure left after the flatten, and it never touches setups. The evidence is the KILL-FLAT ledger entry: Graveyard (10 symbols) and Gen (4 symbols) carried lots from 11-13 to 11-16 with health.position_mismatch.
   - One gap: the watchdog's dry-mode logs are not on the data branches, so I could not count how often it would have acted. Checking a few days of watchdog.yml run logs before the switch would confirm there are no false triggers.

**Do not adopt:**
- Tighter Primary latch or halt, or a cross-account or system-wide loss halt. They are broad (touching 150–290 setups), fail the same-setup test, and are dominated by 10-15 or 11-17.
- Loss latches in Testing or Gen. This supports ST-A and the owner's "give rules a chance": consistency over churn.
- Separately, a consistency fix could make non-Primary halts count cost-in R at their existing catastrophe levels (LR3 extension). That is not a new brake and was not tested for value here.

## Configurations counted
48 brake configurations, each scored on 6 scopes (Primary, Gen, Graveyard, Testing A–F, low-rep, all), for 288 rows:
- setup stop: 6
- account halt: 6
- cross-account family: 3
- system halt: 2
- burst cooldown: 10
- burst cooldown, losing only: 6
- burst latch: 2
- entry cap: 4
- open-lot cap: 4
- combo: 1
- runaway stop after K trades: 4

Every one is in the CSV, and no holdout was used. I wrote no report files and committed nothing.

Files are in /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ww_out/brake:
- `brake_eval.csv` — all 288 rows, including the selectivity columns
- `brake_eval_selectivity.csv`
- `brake_eval_blocks.npz`
- `brake_eval.py` — the replay
- `load_trades.py` — the journal loader
- `brake_detail.py` — the period, 11-17 and selectivity breakdowns

The working copy of the trades is /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ww_scratch/brake/trades.parquet (5 MB).
