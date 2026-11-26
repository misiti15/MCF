Educational only — not financial advice

# COMPASS-RD-1126 Part 1: what condition / compass pieces exist (2026-11-26, research only)

Owner 11-26: "put more emphasis on the market compass … steer, switch on and off … for certain setups". Research only:
no config, ledger, workflow or live change. Forward figures below are re-tallied tonight from the journals (run 1, LR8 R,
identical signals once) and `origin/mcf-data-compass` unless the row says otherwise. Guard: RESEARCH_RULES 26 lists
"day-type on/off switches" and "gates on proven setups" as ask-the-owner-first items, and STOP2(2) bars live per-setup
condition filters fitted on < 15 active days / 60 trades per half (0 of 31 passed, 8 made their setup worse). The
owner's 11-26 ask is the "yes" for this audit; any switch it proposes still needs the 2-year test + a forward bar.

## A. Live pieces (running every session; display or risk only, none steers setups by condition)
| piece | what it is | status | forward record |
|---|---|---|---|
| Market Compass (`mcf/report/compass_live.py`, `.github/workflows/compass.yml`) | 15-min marks 09:45-15:45: SPY/QQQ/IWM from open, VWAP side, 200-name breadth, W60 votes, 30-min C30, checkpoint state, GATE1 state; `compass/<date>.csv` on `mcf-data-compass` | live since 11-09, DISPLAY ONLY | 14 sessions 11-06..11-25 (11-16/17 only 1 recorded mark; recomputed). First confirmed W60 side = close side 12/14 (85.7%), median 10:00, 0.43 side flips/day; C30 12/14, median 11:15, 0.29 flips. Misses: 11-11 (10:00 DOWN, closed +0.40%), 11-25 (11:00 DOWN, V-day closed +1.93%). Backfilled 10-06..11-05: W60 16/23 (70%), C30 17/23 |
| compass_cond (`mcf/report/compass_cond.py`) | lookup: time x SPY-from-open bucket x vs prior close -> close-side / next-N-min rates; 2-year seed + 1 day/night | live (nightly), descriptive | 471 sessions, 1,090 cells. Not a test; no pass bar |
| BRAKE-BURST (config `burst_max_entries 30 / 10 min`) | runaway-entry brake per setup, every account | LIVE from 11-23 (ledger 2026-11-23-brake-burst) | risk control, not a condition switch |

## B. Journal-only forward shadows (no trading change) vs their pass bars
| shadow | rule (frozen) | forward n | record now | vs pass bar |
|---|---|---|---|---|
| comp15-w60-early (hypotheses.jsonl) | W60 as the early compass line | 14 / 20 sessions | precision 85.7% vs C30 85.7%; median first confirm 10:00 vs 11:15; flips +0.14/day vs C30 | all 3 criteria met so far (hypotheses.jsonl tally stale at 3 sessions / 11-10) |
| gate1-checkpoint-gate | listed 37 setups (27 Gen) after 11:00 only in TRAIN-favourable UP/DOWN/MIXED state | 15 / 20 sessions (11-05..11-25, 5 journals) | 733 dropped, avg -0.173R vs kept -0.066R; gated - ungated +127.0R, day t 2.44, best day 26%; excess t 0.89 | t >= 1.5 met; excess t >= 1.0 NOT yet (0.89); kept > dropped met. Tally in hypotheses.jsonl stale (3 sessions) |
| Compass Gate (`research/forward/compass_gate`, frozen 11-19) | block new entries whose market exposure is against the W60 side once confirmed | 4 / 15 forward sessions (11-20..25) | 2,454 blocked avg -0.275R vs kept -0.202R; saved +674R, session t -1.97; 11-20 = 59% (`1 day`). Primary 22 blocked -17.0R (NM-ETF -11.8R) | early; backfill (seen) failed checks 1/3/4 (164% one day; L3 counter-compass trades +32.5R) |
| REGSW GAP-U (`research/regime_switch`) | shorts off if SPY gap > +0.25%, longs off if < -0.25% | 10 / 20 sessions (11-11..11-25) | all accounts +339.0R (2,166 of 6,113 switched); 11-11 + 11-16 = 71%; Primary +37.1R (11-11 = 75%) | 2-year: VALID t 3.93 but failed crit 3/4; guild 1111 shared-day null: no longer beats random. Judged one-day |
| REGSW IDX3-P | per setup, off in its TRAIN-worst "all 3 indices agree" state (fits_P.csv) | 10 / 20 | +147.1R (551 switched); 11-25 = +134.0R (91%, `1 day`); Primary +17.9R (11-25 +31.6R, others -13.7R) | only label that beat chance TRAIN->VALID (0.47 vs 0.34); 2-year t 2.58 < 3.03. Carried by 11-25 |
| REGSW SPYO-P | per setup, off in its worst SPY-from-open state | 10 / 20 | +63.7R (374 switched); 11-25 +83.9R (>100%); Primary +0.9R | below random everywhere in the 2-year study |
| LEASH K11 / K12 (`research/l3leash`) | L3-fromopen half size SPY >= +0.40% (K11); -1R stop after UP-confirmed (K12) | 11 / 20 | Primary dK11 -17.9R, dK12 -28.0R | losing; on course to fail |
| BRAKE-1 shadow | family brake: half size after 3 family stops | since 11-02 | running +4.31R (never switched on) | no bar met; REGSW FSTOP-U = random level |
| ECG1 swing1109-L11 / MFX1 swing1110-L12 | W60 UP-confirmed blocks momentum shorts / midday-flip book exit | stale (1 / 0 forward sessions logged) | both FAILED their 2-year test (VALID t 0.67 / -0.17) | backtest failed; forward not maintained |

## C. Tested and failed / retired (2-year engine, costs in, locked block unread)
- GATE1 (research/bdi/gate1): 0 of 112 (bar 3.07); SPY-direction / REG1 gates gain only by trading less of a losing book (excess t <= 0.36).
- COMPASS-LEARN (research/compass_learn): 0 of 205 compass variants beat W60; extra inputs (Hunch lean, breadth-15, sector, gap) make it worse; "heading" next 30/60/120 min 51.8 / 51.1 / 50.0%. The compass reads *which side of the open the day closes on*, not where SPY goes next.
- REGSW phase 1 (research/regime_switch): 0 of 74 (+25 sensitivities, bar t 3.03). 62/74 "help" only because the 52 lab lists lose; per-setup labels flip (best-state match 31% vs chance 32%). Exception: SPY-from-open label stable on L3-fromopen (worst SPY < open) and RW3 / ST7 / NS5 (best SPY < open). CMP-U-OFF ("shorts off on UP-confirmed") cost L3-fromopen -35R FWD / -32.5R live. REGSW2 (guild 1111): 0 of 4.
- L3LEASH 1 + 2: 0 of 12 each — every leash that cuts red days gives up as much green-day R.
- BREADTH-1125 (research/breadth_1125): close-gate 0 of 12 (FIT lifts +9..+16 pp shrink to noise in CHECK/T2); PYR4 hedge book worse than Primary (paired t -1.81 / -0.41). `build_breadth.py` (5 point-in-time breadth series 2023-01..2026-11, corr 0.98 with lab breadth) is the reusable piece.
- Pyramid G TT1/TT0 tape-turn gate (research/pyramid_1124/G_REPORT.md): 10 configs; only B3+TT1 passes by the letter (23-day basket, treated TIER B); NM-ETF+TT1 TIER B (CHECK +0.087, T2 -0.031; live gated 20 tr +0.355 vs blocked 79 tr -0.289) - forward tag proposed, not running.
- breadth gates bdi-rg-g1..g6 (1,052 configs), cluster skips, ECG1, MFX1, swing L17 (NM-ETF deep-down class: opposite sign): all failed.
- Before-noon cutoff (owner_inbox 11-24): not supported; Primary's before-noon +35.4R is 101% one day (11-12). Remedy-Q Testing copies (no entries after 12:30) live in F/A/B since 11-23 (RQa-1230 L3 copy 97 tr -1.05R, 3 sessions).
- Hunch (mcf/hunch, research only): M1 next-bar direction never 65% (best 20-session window 52.3%); M3 next-bar volume 67.7% (not directional).

## D. Headline
- Real forward evidence (sessions, n): Compass side-of-close reading (14 sessions, 12/14 correct; 37 incl. backfill, 76%);
  gate1-checkpoint-gate (15 sessions, 733 dropped, day t 2.44, one criterion short); comp15-w60-early (14 sessions, on track).
- Everything that tried to switch a *whole side or the market* off (GAP-U, CMP-U, REG1, breadth, leash, cutoff) is either
  failed on 2 years or carried by 1-2 days forward. The pieces that keep surviving are **per-setup and SPY-from-open based**
  (REGX exception list, IDX3 label, gate1 setup-states) — see CONDITIONAL.md.
- Puzzle gap: no piece maps the stable per-setup condition to an action in the account where it matters (Primary), and
  three forward tallies (gate1, comp15, ECG1/MFX1) are stale in hypotheses.jsonl.
