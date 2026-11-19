Educational only — not financial advice.

# ROOTCAUSE-1119 / system_rules: did a system rule cause the 2026-11-19 Primary loss, or cost us the recovery?

Research only. Nothing in config, setups, exits or orders was changed. Sources:
- Primary journal: origin/mcf-data journal.db, as of 13:49 ET. Run 1 = live, run 2 = what-if, run 3 = shadow.
- Primary poll logs for 11-19 (MTM / realized-R path).
- Live journals of all 9 accounts: `rootcause_1119/stk/*.db`.
- SPY betas from the 2-year cache: `cond_work/beta.csv`.
- L3/ST7 2-year lab fires: `sl_work/lab_fires.parquet`.
- 1-minute bars for the 44 skipped or blocked symbols: 2 Alpaca GET requests (bars to 13:51 ET).

Method notes:
- R = pnl_adj / (|entry-stop| x shares). Costs in: 1 bp + $0.01/share per side, +$0.02 on stop exits.
- The locked block 2024-11-01..2025-02-28 was not read.
- Scripts: `rootcause_1119/sys_scripts/` (fetch.py, sim.py, guard.py, dupstop.py). Outputs: `rootcause_1119/sys_work/`.
- Calibration: my bar simulator re-ran L3's 6 actual trades at **-6.55R vs the journal's -6.49R**.
- **Configurations tried: 8.** Short-beta guard at 3 thresholds; 0.15R cost filter in Primary; no same-stop stacking; latch what-if (lot cap on and off); ETB what-if.

**Rule-change context for the live window** (research/ledger.jsonl):
- 10-28: Primary slot ~$4k (77 slots).
- 10-29: per-setup -2R latch, Primary only.
- 10-30: 0.15R cost filter, Testing 1/2 only (Primary off). Same day: L3-fromopen-FD re-promoted to Primary and L3-rsi5hi-FD promoted.
- 11-05: low-rep accounts went live.
- So L3's whole Primary record sits under the latch and the $4k slot. ST7's Primary record (from 10-25) spans the latch start.

## Verdict
**No. A system rule is not the root cause, and no rule cost us a recovery.** The loss was set by the time the entries were made. Of today's -16.8R realized so far (-14.4R at the time of the brief, then RW5 -2.4R), the rules prevented roughly 40R more:

| rule | what it did today | R impact today |
|---|---|---|
| ETB skip (`require_easy_to_borrow`) | Blocked 41 short signals: 40 L3 (nearly all inverse/vol ETFs: SOXS, SPXU, TECS, QID, FNGD, UVXY, VXX, TSLQ...) and 1 RW3 (TRI) | **Saved ~+33R** (simulated: L3 -33.9R, 9 of 40 won; TRI +0.7 open) |
| -2R per-setup latch | Could not act before the losses. Afterwards it blocked 24 L3 and 1 RW5 signals | **Saved ~+10R** (blocked L3 = -10.0R with the 3-lot cap, 17 closed -8.3R, rest marked 13:51; VSXY +0.6 open) |
| -20R account halt | Not reached (realized low about -16.8R) | 0. Without the ETB skips, the day would have been about -50R and the halt would have fired only after the loss |
| 3 lots / symbol + refire (cooldown 1) | L3 took 3 lots on SPXS and 3 on SQQQ with nearly identical stops | -4.4R vs 1 lot. Historically same-stop stacking is L3's **best** class (see 4) |
| 0.15R cost filter (Primary off) | 4 of 19 entries were above 0.15R (SPXS lot 2, IBRX, OGE, ADC) | Would have saved +4.6R today, but costs the current Primary setups historically (see 3) |
| setup_order, spread, crosscheck | No same-symbol conflicts; 3 spread skips | ~0 |
| Sizing (min(0.25% risk, ~$4k slot)) | The slot cap always binds. $ risk per trade $15-$173, so the same R costs very different $ | 0 in R. In $, MUU (4.9% stop) alone was -$183 of -$909 |

**Why the latch could never have helped today:**
- L3's 6 stops filled in **14 seconds**, 11:51:53 to 11:52:07.
- The account's open MTM was **+9.3R at 11:42 and +4.5R at 11:50**, then -6.5R at 11:52.
- So neither a realized-R latch nor a mark-to-market latch had anything to see before the move.
- ST7's IWN lot (11:55) came after one ST7 loss (-1.16R). The -2R line was crossed at 12:00.
- Any latch built on R is after the fact when 14 lots share one exposure and one 4-minute SPY drop (-0.8%) takes them all.

**On the owner's premise:** neither of today's setups has a strong live record in Primary.
- **ST7-FD**, Primary since 10-25: 42 trades, -6.6R, avg -0.158R, win 43%. Without its best day: -0.296R. It never stacks on a symbol. Its 7 lots today were 7 different names in one minute.
- **L3-fromopen-FD**, Primary since 10-30: 158 trades, +38.7R, avg +0.245R, win 70%. But 11-12 is 80% of its total R (**1 day**). Without it: +0.073R; 6 of 12 days green.
- So "capitalise on every opportunity" was not stopped by any rule today. The opportunities taken were losing calls: long-market dip buys and inverse-ETF shorts, made while the tape kept falling.

## 1. The only system-level gap found: rules are blind to symbol class (a short of an inverse/vol ETF is a long-market bet)
- Live record: L3 is meant to fade a gap-down recovery. On SPXS/SQQQ that means *buying* the S&P/Nasdaq dip.
- ETB is the only rule that ever stops this, and it does so by accident and inconsistently:
  - Today it blocked 39 inverse/vol shorts (-33.9R simulated).
  - It let the two most liquid ones, SPXS and SQQQ, through (-6.5R).
- **Size of this gap today: at most the 6.49R of L3's SPXS/SQQQ lots. 0R of ST7's -8.7R.**

**Remedy R1, short-beta guard** (targeted): short setups skip symbols whose 2-year daily SPY beta is <= -1 (inverse and long-vol products).
- Defined from data, not a hand list. Applies to every short setup.
- Thresholds tried: 0 / -0.5 / -1.
  - At 0 it catches defensive stocks (MO, CME, DUK) and is noisy.
  - -1 is the clean cut.

| test (live, all 9 accounts, run 1) | trades removed | setup-accounts improve | worse | net |
|---|---|---|---|---|
| beta <= -1, all dates | 151 (avg -0.43R, win 31%) | **42 (+79.4R)** | 17 (-14.6R) | **+64.8R** |
| beta <= -1, excluding 11-19 | 122 | 38 (+62.0R) | 15 (-14.4R) | +47.6R |
| beta <= -0.5 | 154 | 41 (+77.9R) | 18 (-15.0R) | +62.9R |
| beta <= 0 | 332 | 68 (+126.7R) | 26 (-21.8R) | +105.0R (noisy class) |

Per setup:
- **Primary, beta <= -1:** 5 improve and 1 gets worse.
  - Improve: L3-fromopen-FD +10.6R (10 trades; +4.1R without today), L3-rsi5hi-FD +3.1, RW3-FD +2.1, MF2-FD +1.2, exhaustion_short +1.1.
  - Worse: RW5-FD -0.9R (1 trade).
- **Largest worsening anywhere:** heat_fade_short-FD in the Graveyard -2.7R, NM-RWR3 in Live Lab -2.1R, L3-fromopen-FD in Testing 1 -0.5R.

Counter-evidence, reported honestly:
- Primary's what-if journal (run 2) has 126 ETB-skipped shorts on beta <= -1 symbols through 11-18 that would have made **+12.6R** (+0.10R avg; L3 67 of them, +17.7R).
- Combining taken trades and what-if trades through 11-18 gives about -35R on 248 trades (-0.14R avg). Still negative, but weaker than the taken record alone.
- 2-year lab, L3 fires: beta <= -1 symbols avg **-0.071R** (n=3,635; total negative) vs +0.013R on the rest. ST7 rarely touches them (12 fires, -0.08R).
- Beta covers only the 1,225 symbols in the cache. Several single-stock inverse ETFs skipped today (NVDQ, PLTZ, MUZ...) are not in it.

**Status: live-record and lab check only.** This overlaps the stacking agent's R-A (hand list, +60.7R) and should be merged with it.
- Next step: backlog entry plus a shadow run, outside market hours.
- It is not a live change.
- Expected to be **underestimated** if the what-if R is accurate; overestimated if live fills are worse than what-if fills.

## 2. The latch: protective, not a recovery blocker
History (Primary what-if run 2, 10-29..11-18):
- 224 latch-blocked signals would have made **-8.0R**, so the latch saved +8R.
- Per setup, 5 helped and 2 got worse:
  - Helped: MF2-FD +12.4, L3-fromopen-FD +8.5, RW5-FD +4.9, NS5 +3.3, MF4-FD +1.6.
  - Worse: L3-rsi5hi-FD -12.7 (11-05: +12.8 blocked), RW3-FD -10.0.

Today, the blocked L3 signals in time order:
- SPXS/SQQQ at 11:55 stopped at 12:00 (-2.2R).
- 12:05/12:15 hit target on the 12:22 bounce (+3.9R).
- Every signal from 12:25 on lost or is red at 13:51.
- Net about -10R. The only "recovery" window was +1.7R on the first 6 blocked signals.

Remedy idea (MTM-aware or earlier latch): **untested, and not worth testing for this failure mode.** The loss came in 14 seconds from an account showing +4.5R open.

## 3. The 0.15R cost filter in Primary (tested, rejected as a remedy here)
- It would have skipped 4 of today's 19 entries (+4.6R).
- On Primary's full live record: 482 of 1,384 trades are flagged (-35.0R, avg -0.073R vs -0.059R unflagged).
- Per setup: 15 improve (+66.3R) and 10 get worse (-31.3R).
- The worse side is today's Primary core: RW3-FD -9.7, MF2-FD -5.6, L3-fromopen-FD -4.8, RW5-FD -2.8.
- Most of the gain comes from setups that have already left Primary. **Not targeted. Keep it Testing-only.**

## 4. 3 lots per symbol with same-stop refires (tested, rejected as a remedy)
Classes (all accounts):
- "Same-stop stack" = a later lot whose stop is within 0.25R of an open lot's stop, same setup/symbol/day.
- Results: +0.046R avg (302 trades); different-stop stack +0.067R (113); first lots -0.123R.
- For L3-fromopen-FD:
  - Same-stop stacks +0.311R avg (138 trades), its **best** class.
  - First lots +0.205R; refires after going flat -0.258R.

Remedy "no same-stop stacking":
- 31 setup-accounts affected: 18 improve (+40.9R), 13 worse (-54.9R), **net -14.0R**.
- L3 in Testing 1 -36.0R, L3 in Primary -6.9R.
- **Rejected.** It agrees with the owner: the lot cap and refire are not the problem; the call is.

## 5. ETB skips today: all 41, simulated to 13:51
- 40 L3 short signals (10:30-13:15): 31 stopped and 8 hit target (UVIX, UVXY, VXX, MSTZ, SMST: the vol/crypto-inverse ones that fired before 10:50). 1 is open at a loss.
- Total **-33.9R**.
- Nearly every one is a long-market bet that was stopped in the 11:51-12:05 drop.
- RW3 TRI: +0.74R open.
- The "13 skipped short signals" in the brief probably counts another window or account. Primary journaled 41.

## Bottom line for the swarm
- Today's -16.8R came from the entries: long-market dip buys (ST7) and inverse-ETF shorts (L3) on a trend-down day.
- System rules took nothing away from those entries. ETB and the latch kept the day about 40R smaller.
- The one system-level fix worth carrying is a symbol-class rule (R1/R-A: no short of an inverse/vol product). It sits at the boundary between system and setup universe, and it addresses at most 6.5R of today.
- ST7's 8.7R is a setup/conditions question: it is negative in Primary live (avg -0.158R).
