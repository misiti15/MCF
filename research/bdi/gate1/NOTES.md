# GATE1 — switch setups on when the market shapes up their way (owner 2026-11-04)

*Educational only — not financial advice.* Backtests (2-year lab lists, uncapped, production costs) and live **paper**
results (journals run_id 1, 5 accounts, 22 sessions 10-06..11-04, 14,007 trades) are labelled separately. Research
only: nothing in config/ or the trading path changed. Pre-registered in `PLAN.md` (commit 6929609de, before any score;
two data amendments for missing 09:45 / 15:30 breadth rows, written before scoring). Locked block 2024-11-01..2025-02-28
never read. **Configurations: 62 gates (pre-registered bar t ≥ 2.87) + 7 combo checks + COMPASS addendum (36 measure
looks + 3 compass tables + 4 compass gates) = 112 looks → study bar 3.07. 0 pass.**

## Failures first
- **No gate passes.** Best on VALID by the pre-registered rule (raw t ≥ 2.87 AND excess t ≥ 1.0 AND TRAIN, LIVE > 0):
  none. Closest: setup-level learned gate from 11:00 (k = 1, off) — VALID +1,655R, t 2.26, excess t 1.22; LIVE all
  +63R (t 1.28), Primary+T1+T2 +25R (t 0.87). Kept avg R stays negative everywhere (VALID −0.061 vs −0.060 no gate).
- **The big-t gates are "trade less of a losing book", not timing.** SPY-direction strict gate @10:00 k2: VALID
  +24,503R t 7.99, LIVE +1,535R t 4.47 — but it keeps 22% of trades and **its kept trades are worse per trade**
  (VALID −0.069 vs −0.060; excess t −0.58). REG1 (10:00 fade): VALID t 4.79, LIVE t 2.60, excess t 0.18, kept avg
  −0.058 vs −0.060. Every 2-year book is negative in every state (side × state avg R −0.01..−0.11), so any block "helps".
- **"With the tape" does not separate R.** Avg R of trades entered after T, state with the side minus against it:
  TRAIN +0.015..+0.059 at 10:00–13:00, **VALID −0.063..−0.005 (wrong sign at every checkpoint 10:00–13:00)**, LIVE
  +0.24 at 10:00 then −0.10..+0.06 (`pred_r_with_against.csv`). Live overall after 10:00: with −0.100R (2,355),
  against −0.117R (2,783), MIXED −0.147R (7,652).
- **The winners are not in confirmed states.** Live setup-days ≥ +2R (3,456 trades, +1,102R): only **20%** of their R
  came from entries whose state agreed with the side; 46% in MIXED, 28% against, 7% before 10:00. A "turn on when the
  market stays your way" rule would have blocked ~74% of the winners' R.
- **11-04:** SPY UP at 10:00 (+0.55%, QQQ +1.34%, IWM −0.05%, breadth 0.51) → MIXED 10:30–11:30 (IWM −0.7..−0.8%,
  breadth 0.47–0.51) → UP again from 12:00. The day's winners (Graveyard LIQ-orl-sweep long +14.8R, CWT09 gap-down
  short +10.0R, CWT12 coil longs +14.3R, CWT14-orl-p10-lowvol +7.6R; Primary ST7-FD +3.1R) were entered 10:06–11:30,
  i.e. in MIXED. Longs entered 10:30–12:00 +23R; longs after 12:00 (state UP) −19R. **A checkpoint gate would not have
  switched the 11-04 winners on in time — it would have switched them on at 12:00, after their entries.**

## MARKET COMPASS (owner reframe 11-04 evening; addendum in PLAN.md, `compass.py`)
Three questions at each 30-min checkpoint, point-in-time only. Hit = the call's direction comes true; lift = hit minus
a same-mix naive call; 95% Wilson CIs in `compass_measures.csv`; ranking `compass_ranking.csv` (all checkpoints pooled).
1. **Moved so far:** SPY % from open (known exactly).
2. **Is it STAYING (SPY closes on the same side of its open)? — yes, this is readable.** Ranked on TRAIN, same order on
   VALID and LIVE: strong move |fo| ≥ 0.30% **89% / 89% / 97%** (TRAIN / VALID / LIVE, n 886 / 695 / 68); GATE1 state
   86 / 86 / 92%; persist3 83 / 84 / 80%; index agreement 81 / 82 / 88%; persist2 80 / 82 / 76%; fo sign 77 / 79 / 74%;
   VWAP side 71 / 72 / 75%; breadth side 70 / 65 / 64%; r30 sign 60 / 61 / 61%; gap ~50%; fades 23–39% (i.e. wrong).
   By checkpoint (fo sign): 68% at 10:00, 74% at 10:30–11:00, 78–83% by 12:00, 83–86% by 13:00–14:00.
3. **Where is it HEADING (from T on)? — close to a coin flip.** Best TRAIN lift for rest of day: strong_fo +5.5 pts,
   state +5.1 → VALID −0.7 / −1.1, LIVE −9 / −8. Next 60 min: state +4.3 → VALID −0.2. No measure has a VALID lift
   above +3 pts (gap sign +3.0 rest-of-day, +2.5 next 60 min; TRAIN −1.6 / −0.2). Momentum and fade both ≈ 50%.
- **Compass reading** = votes of fo sign, VWAP side, persist2, breadth side, index agreement (+ persist3 for
  "confirmed"; none possible at 10:00). Table (stays = SPY closes on the reading's side of the open; rest-of-day = SPY
  close vs price at T in the reading's direction, for "mixed" = up):

| T | reading | stays T / V / L | rest-of-day T / V / L | n T / V / L |
|---|---|---|---|---|
| 10:00 | leaning up | 68 / 67 / 67% | 58 / 58 / 33% | 107 / 95 / 9 |
| 10:00 | mixed | 55 / 29 / 100% | 55 / 33 / 50% | 33 / 21 / 2 |
| 10:00 | leaning down | 70 / 69 / 46% | 53 / 46 / 46% | 94 / 74 / 11 |
| 10:30 | UP-confirmed | 79 / 83 / 67% | 62 / 64 / 33% | 48 / 42 / 3 |
| 10:30 | leaning up | 68 / 60 / 80% | 56 / 48 / 60% | 62 / 48 / 5 |
| 10:30 | mixed | 54 / 52 / 60% | 57 / 48 / 80% | 35 / 21 / 5 |
| 10:30 | leaning down | 74 / 76 / 40% | 45 / 52 / 20% | 51 / 46 / 5 |
| 10:30 | DOWN-confirmed | 82 / 79 / 50% | 53 / 42 / 50% | 38 / 33 / 4 |
| 11:00 | UP-confirmed | 82 / 81 / 100% | 62 / 50 / 0% | 60 / 48 / 4 |
| 11:00 | leaning up | 64 / 60 / 62% | 50 / 40 / 50% | 52 / 45 / 8 |
| 11:00 | mixed | 68 / 53 / 100% | 68 / 53 / 100% | 22 / 30 / 1 |
| 11:00 | leaning down | 68 / 83 / 50% | 46 / 57 / 25% | 50 / 35 / 4 |
| 11:00 | DOWN-confirmed | 88 / 84 / 60% | 56 / 44 / 60% | 50 / 32 / 5 |
| 11:30 | UP-confirmed | 81 / 85 / 100% | 58 / 48 / 33% | 69 / 54 / 6 |
| 11:30 | DOWN-confirmed | 90 / 90 / 100% | 53 / 42 / 100% | 57 / 38 / 3 |
| 12:00 | UP-confirmed | 85 / 82 / 100% | 62 / 50 / 33% | 73 / 62 / 9 |
| 12:00 | leaning up | 72 / 69 / 50% | 49 / 41 / 25% | 43 / 29 / 4 |
| 12:00 | leaning down | 68 / 85 / 100% | 52 / 48 / 100% | 40 / 46 / 1 |
| 12:00 | DOWN-confirmed | 90 / 90 / 75% | 48 / 44 / 75% | 58 / 39 / 4 |
| 13:00 | UP-confirmed | 91 / 90 / 100% | 62 / 47 / 44% | 80 / 62 / 9 |
| 13:00 | DOWN-confirmed | 92 / 88 / 80% | 48 / 50 / 60% | 63 / 58 / 5 |
| 14:00 | UP-confirmed | 88 / 90 / 100% | 50 / 38 / 43% | 86 / 58 / 7 |
| 14:00 | DOWN-confirmed | 87 / 96 / 80% | 37 / 59 / 20% | 76 / 49 / 5 |

  (all rows incl. 11:30–14:00 leaning / mixed in `compass_table.csv`). Reading: a **confirmed** reading from 10:30 holds its
  side of the open 79–96% (VALID), vs ~50–70% for leaning / mixed; **the only heading edge that survives VALID is 10:30
  UP-confirmed (rest of day up 62 / 64%, n 48 / 42; live 1 of 3)**. After that, rest-of-day is 38–59% on VALID.
- **Compass used to switch setups** (family×side or setup on in its TRAIN-favorable readings, entries from 10:00):
  setup-level off: TRAIN +5,793R t 3.79 (excess t 2.80) → **VALID +1,745R t 1.86, excess t 0.61** → LIVE +85R t 1.25,
  excess t −0.82; family×side: VALID t 0.96, LIVE t 0.90. Kept avg R stays negative (VALID −0.064 vs −0.060). Not a pass.

## BEST RULE FOUND and how to use it (evidence level: **near-miss** for the gate, **weak** for the combos)
- **Read the compass at 10:30, 11:00, …: it tells you if the move will HOLD, not if it will extend.** Use it to decide
  which side's *fades vs continuations* to allow, not to chase direction.
- **Gate (near-miss, forward shadow):** setup-level learned state gate from 11:00, re-checked every 30 min, entries
  off when the state is outside the setup's TRAIN-favorable set (`shadow_rule_setup_states.csv`): VALID t 2.26 (bar 3.07),
  excess t 1.22, LIVE +63R (t 1.28).
- **Switch-on card (weak; from TRAIN+VALID, live only independent look):**
  - **UP-confirmed / UP state → L3 gap-down shorts ON** (L3-gap-slope-fromopen-FD; family L+S UP-confirmed TRAIN +0.089,
    VALID +0.009, LIVE +0.229; outside UP: −0.18 / −0.03 / −0.19). Off in mixed / down.
  - **DOWN-confirmed / leaning down → oversold-long families ON** (NM+L TRAIN +0.25 / +0.34, VALID +0.12 / +0.15;
    NS+L DOWN-confirmed +0.074 / +0.079; ST7-FD in DOWN VALID +0.18 t 2.09) — live small n and negative for NM / NS.
  - **Mixed:** no family positive in all three windows; Graveyard NS3-FD / RW4-FD shorts are 2-year mixed-state
    performers but negative live.

## What can be told at each checkpoint (pre-registered state) (`pred_direction.csv`; rest-of-day = SPY close vs price at T)
| T | TRAIN UP / DOWN agree (days) | VALID UP / DOWN | LIVE UP / DOWN | base rest-of-day up (T/V) |
|---|---|---|---|---|
| 10:00 | 62% (53) / 55% (49) | 58% (41) / 52% (42) | 33% (3) / 100% (1) | 53 / 54% |
| 10:30 | 60% / 56% | 58% / **40%** | 20% (5) / 60% (5) | 55 / 53% |
| 11:00 | 63% / 57% | 47% / 46% | 29% (7) / 50% (4) | 54 / 48% |
| 11:30 | 62% / 52% | 48% / 40% | 25% / 75% | 56 / 50% |
| 12:00 | 59% / 51% | 50% / 43% | 22% / 100% | 53 / 53% |
| 13:00 | 64% / 48% | 48% / 51% | 38% / 75% | 56 / 48% |
| 14:00 | 53% / 42% | 39% / 60% | 43% / 33% | 53 / 46% |
- The **rest of the day is a coin flip** from any state after 10:30 (VALID 40–51%); TRAIN's 60% UP edge is mostly the
  2025 up-drift (base 53–56%). Only the 10:00 UP state carries a few points in both halves (62 / 58% vs 53 / 54%).
- **Day type is mostly already decided by the move so far:** EOD type equals the state's type in 58–68% at 10:00,
  60–78% by 11:00, 80–87% by 14:00 (TRAIN/VALID) — that is the open-to-T move, not a forecast of later moves.
- MIXED is 47–56% of days at 10:00–11:00, ~40% after noon. Live window: 10:00 state was MIXED on 18 of 22 days.

## Gates vs no gate (totals R; avg R; avg w/o best day; green-day rate; max DD of daily R)
| gate | TRAIN | VALID | LIVE (all 5) | LIVE P+T1+T2 |
|---|---|---|---|---|
| no gate | −43,202; −0.078; −0.083; 14%; −42,744 | −32,713; −0.060; −0.062; 18%; −32,514 | −1,966; −0.140; −0.149; 9%; −1,960 | −1,017; −0.117; −0.130; 18% |
| best learned (setup @11:00 k1 off) | −40,200; −0.078; 93% kept; t 2.35 | −31,057; −0.061; t 2.26, ex 1.22 | −1,902; −0.141; t 1.28 | −992; t 0.87 |
| REG1 @10:00 off | −25,696; −0.086; 54% kept; t 4.14, ex −0.52 | −17,014; −0.058; t 4.79, ex 0.18 | −1,100; −0.137; t 2.60 | −600; t 1.48 |
| SPY-dir strict @10:00 k2 off | −7,316; −0.055; 24% kept; t 8.38, ex 0.36 | −8,209; −0.069; t 7.99, ex −0.58 | −431; −0.165; t 4.47 | −172; t 2.64 |
- By day type the strict gate cuts all three types (VALID up −1,558 / down −2,658 / quiet −3,993 vs −10,929 / −12,406 /
  −9,377): it is a volume cut, not a regime pick. Family×side learned gates: VALID t ≤ 1.70, LIVE ≈ 0. Side-level
  learned gates: no side has a positive state on TRAIN → ungated (12 configs = no change). Full table `gates.csv`.

## Graveyard: conditional performers?
- By the pre-registered test (one state TRAIN > +0.05, n ≥ 60, VALID > 0, other states ≤ 0 on TRAIN) 6 setups qualify,
  2 of them Graveyard: **NS3-failed-vwap-reclaim-short-FD** and **RW4-ns3-adv150-short-FD**, both in MIXED
  (TRAIN +0.087 / +0.092, VALID +0.023 / +0.024; other states −0.05..−0.08) — but **LIVE MIXED −0.20 / −0.28R**
  (78 / 72 trades) and day-clustered t ≤ 0.86 on both halves. 2-year conditional, live contrary: not a case to un-graveyard yet.
- 11-04's Graveyard winners have no 2-year conditional profile (CWT09-g5 short UP: TRAIN −0.31 / VALID +0.19; CWT12-k4
  long: every state ≤ 0; LIQ-orl-sweep not in the lab). Their 11-04 gains came in MIXED, the state no gate would pick.

## Three most promising combos (picked on TRAIN+VALID, so LIVE is their only independent look; `combos.csv`)
1. **L3-gap-slope-fromopen-FD (Primary short) only while the 30-min state is UP** (fade the up tape, consistent with REG1):
   in vs out TRAIN +0.084 vs −0.184 (12,557 / 8,343), VALID +0.004 vs −0.032, LIVE **+0.358 vs −0.192** (165 / 88).
   Weak: TRAIN in-state w/o best day −0.068 (`1 day`), VALID t 0.07.
2. **ST7-rsi50dn-long-pm-t1s1-FD (Primary long) only while DOWN**: TRAIN +0.030 vs −0.106, VALID +0.183 (t 2.09) vs
   +0.018, LIVE +0.138 (8) vs +0.103 (27). Small n.
3. **NM-AR-AM-gapdown-capitulation-long (Testing 2) in DOWN**: TRAIN +0.517 (491, t 1.26, 76% best day), VALID +0.259
   (220) — but VALID out-of-state also +0.170 and LIVE DOWN −1.04 (8 trades, 2 days). Selected on these frames (in-sample).

## Verdict and next step
- **Near-miss → forward shadow lead `gate1-checkpoint-gate`** (plus the compass reading and the switch-on card logged each session) (research/bdi/swings/hypotheses.jsonl): the
  setup-level learned gate from 11:00, 30-min re-check, off when the state is not in the setup's TRAIN-favorable set
  (`shadow_rule_setup_states.csv`, 37 setups: 27 Gen, 6 Graveyard, 2 T2, 2 Primary; other setups ungated). Fixed bar after
  20 forward sessions on the 5 journals: gated − ungated daily R t ≥ 1.5, excess t ≥ 1.0, kept avg R w/o best day > dropped.
- Honest reading: what can be known at a checkpoint is mostly how far the market has *already* gone; the rest of the day is
  close to a coin flip, and the live book's winners fire in MIXED tapes. The useful lever is per-setup (combo 1–2), not a
  market-wide on/off switch; REG1's forward shadow (REG2) already covers the side-level version.
- No DECISION card.

## Rule changes inside the live window (research/ledger.jsonl effective dates)
10-13 stacking; 10-21/10-22/10-26/10-27/10-28/10-30 promotions, demotions and rotations (L3-fromopen-FD, CWT14-pdl,
MF1/MF3/NS3/RW6G1/ST7/CWT13); 10-21 Graveyard opens; 10-23 per-setup latch semantics (off in Testing/Gen); 10-27 GX1
5-minute clock; 10-28 Primary ~$5k → ~$4k lots; 10-29 Primary −2R per-setup stop, Gen paused after 10-28; 10-30 CF cost
filter + BAR90 (Testing), L3-rsi5hi-FD promoted, L3-fromopen-FD re-promoted; 11-02 NS3-FD / RW4-FD to Graveyard, PDL-1a
R2A (T2); 11-03 MF3-FD / MF5-FD to Graveyard, SO1a cap exempt, RW3S (T2); 11-04 NS5-FD / ST4-FD / RW6G1-FD to Graveyard,
UNI1 (T2 top-500). Live R mixes all of these; Testing 1 data from 10-09, Testing 2 from 10-12, Gen from 10-19.

## Caveats
- Lab lists are uncapped signal chains (no slots / lot caps); live is censored by caps. Lab universe is today's list
  (survivorship). Breadth = lab universe (1,226 names), not the live top-500. Gen and NM setups were built on these frames.

## Files
`state.py` (checkpoint states) → `data.py` (trade table) → `pred.py`, `gate.py`, `cond.py`, `case.py`, `combos.py`, `compass.py`.
Tables: `pred_direction.csv`, `pred_r_by_state.csv`, `pred_r_with_against.csv`, `gates.csv`, `gates_summary.csv`,
`allowed_states.csv`, `shadow_rule_setup_states.csv`, `conditional_setups.csv`, `family_side_by_state.csv`,
`live_sessions.csv`, `live_win_setupdays_by_state.csv`, `live_lose_setupdays_by_state.csv`, `s1104_setups.csv`,
`s1104_by_halfhour.csv`, `combos.csv`, `compass_measures.csv`, `compass_ranking.csv`, `compass_table.csv`, `compass_usage.csv`. Scratch (journals, state / trade parquet) deleted after the run.
