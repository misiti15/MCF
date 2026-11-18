# Usage plan items 4-11 — lead consultant summary (2026-11-18)

_Educational only — not financial advice._

Research only, run during market hours: no config, code or runtime change, no merge, nothing deployed. The promotion
hold is on, so anything that passes is written up as a proposal with a reply code. Costs are in (LR8). The locked block
(2024-11-01..2025-02-28) was not read. Every item pre-registered its PLAN.md before scoring. Gap-Down Recovery Fade
(L3-gap-slope-fromopen-FD) was not touched. Item 10 (adversarial review) and item 12 (LEARN1) run separately tonight.

**Rule changes inside the windows (10-06..11-17, 2-year data excepted):** sizing 10-28, Primary -2R latch 10-29,
TEAM-6 11-11, the LR3/LR8 cost batch 11-12, TSZ1 testing sizing 11-16, Testing half-size + promotion hold 11-17,
recorded quotes + SRCV1 from 11-18. Live-journal results before and after these dates mix rule regimes; each item's
RESULTS.md lists the ones that touch it.

## Scoreboard

| Item | Tried | Configs | Passed | Key number | Files |
|---|---|---|---|---|---|
| U4 longs | 5 mechanism long specs x 2 exits | 10 | 0 | 2-year: all 10 negative (-0.046 to -0.134R, t -0.87 to -3.18). Best live (U4-VWR) +0.106R, t 1.0, 52% best day, -0.116R over 2 years | research/usage/u4_longs/ |
| U5 day type | 4 setups with built-in day-type cues | 20 | 0 | Fit -0.20 to -0.27R after costs, gross also negative; S3 check +0.732R (37 trades) but fit -0.215R, 77% best day | research/usage/u5_daytype/ |
| U6 mechanism | M1-M5 (opening drive, gap-and-go, sector lag, lev ETF, afternoon trend) | 19 | 0 | Fit total -1,092R; gross about 0, costs 0.08-0.16R/trade; capture 15.0% → 18.3% but -4.2R on those sessions | research/usage/u6_mechanism/ |
| U7 Workbench | 20 top On Deck/Testing setups, 1 tune each | 265 | 0 | Tunes chosen on earlier sessions: later sessions -45.6R total (5 better +12.4R, 10 worse -58.0R); no better than the menu median | research/usage/u7_workbench/ |
| U8 Graveyard | 10 revival tunes over 34 residents | 1,100 | 0 | Bar t 3.74; no gate beat 95% of random subsets (best 92%); RW6G1 transfer-watch only; CANDIDATES.md ready | research/usage/u8_graveyard_prep/ |
| U9 execution leaks | ETB skips, broker rejects, quote check, B2 re-anchor | 4 | **2** | Quote check: 115 fills at/through target or stop cost -65.3R; B2 re-anchor fails (-0.48R/trade, t -3.96) | research/usage/u9_execleaks/ |
| U11 engines | Inventory of simulators, retirement plan | 0 | n/a | 6 engines; replay matches live 87.1% (target 98%), 44% for L3-fromopen; 15 gates, none green | research/usage/u11_engine/ |

Total configurations across items 4-11: 1,418.

## Per item

**U4 longs — FAIL (U4-NOCOPY).** The long edge depends on day type: 4 of 5 specs are positive on SPY up days in both
datasets and negative on quiet and down days. Existing live longs: 14,503 trades, -1,952R; the solid long setups
(NM-ETF-late-dip, ST7) are already in Primary. Codes: U4-NOCOPY, U4-KEEP-LONGS, optional U4-GEN2701-REPS (more low-rep
rotation for GEN-261027-01, not a copy).

**U5 day type — FAIL.** All four fit averages negative after and before costs; the no-cue versions are negative too, so
the cue adds no edge. Median stop 0.14 ATR means costs take 0.10-0.18R per trade. S3 (quiet-day VWAP-stretch long) goes
to a pre-registered forward watch only; random entries on the same days made +0.333R against its +0.732R.

**U6 mechanism — FAIL.** No setup beats its random control by more than ~0.03R. In check, M2/M3/M4 are positive but
each is negative without its best day (best-day share 121-430%). M3 long and M2 short go to the backlog as notes.

**U7 Workbench — FAIL (U7-NONE; U7-RERUN at 15 active days / 30 trades).** RW7's 120-minute time stop alone cost
-30.2R in later sessions. L3-lowdist's current exits are already best; its entries beat random by the widest margin
(+0.376R vs +0.002R). Entries beat random in 12 of 20 setups.

**U8 Graveyard — FAIL, no decision.** No resident is positive without its best day over its whole record. On CHECK the
tunes raised total R for 7 of 10 and lowered it for 3 (+44.7R summed, mostly by dropping trades); avg R improved for
5 of 10, avg R w/o best day for 3 of 10. Day-type gates flipped sign. CWT12/14 residents (-1,211.5R) got no tunes.

**U9 execution leaks — 2 proposals pass.**
- *U9-TGT (quote pre-check).* Skip an entry when the fill-side quote is already at/through the target, or the
  exit-side quote at/through the stop. Target part: 96 fills, +8.47R over 23 days; check half +5.32R, t 2.32 vs bar
  1.67; best-day share 61% in check (38% over all days); 15 setups improve (+8.98R), 4 worse (-0.50R). Stop part:
  19 fills, +56.9R, check t 8.24, best-day share 46%, 11 improve / 0 worse (large in R because the fill-to-stop distance
  is tiny; small in dollars). About -3.7 fills per session, all with no upside. 226 broker take-profit rejects become
  clean skips. Runtime change: research/usage/u9_execleaks/fix.patch part (b), `live.skip_passed_at_quote`.
- *U9-ETB (bulk borrow list + once-per-day ETB journaling).* Expected 0R and 0 reps: the borrow test runs before
  every cap, so a skip takes no slot; the 09:08 flags matched every skip, 0 intraday flips. Removes ~300-650 journal
  rows and up to ~640 per-symbol broker GETs per session. Housekeeping-grade; fix.patch part (a).
- *B2 (re-price rejected brackets) — FAIL:* -0.48R/trade on check, t -3.96.
- fix.patch applied: full suite 771 passed. Not committed to code, not merged.

**U11 engines — inventory, decision ENG1.** E1 Backtester, E1p/E1h (imported by the live runner, so moved not
deleted), E2 lab frames, E3/E3c session replay, E4 one-off simulators (28 studies in 6 sessions), E5 Shadow. 2-year
screen +0.157R optimistic, 2-year backtest +0.06 to +0.09R; no source ranks setups (Spearman about 0). First fair
re-test with recorded quotes around 12-02. ENG1-A now (labelling, no new one-off simulators), ENG1-B after close
(move helpers, nightly drift scoring, shared exit walker), ENG1-C when the gates are green.

## Open decisions added (owner_inbox 2026-11-18, docs/live/decisions.json)

1. **U9-TGT (Yes)** — apply fix.patch part (b) after the close. Reply U9-TGT-YES.
2. **U9-ETB (Yes)** — apply fix.patch part (a) after the close. Reply U9-ETB-YES.
3. **ENG1 (Yes, A now; B after close)** — engine retirement plan. Reply "ENG1 A", "ENG1 A+B" or "ENG1 no".

Neither U9 change touches a setup, an exit or the lineup, so neither needs a promotion or an assignments.json change.

## Caveats

- Live-session bars cover about 31 sessions; check halves are 12-16 sessions. One or two days move any result.
- U9's numbers come from journal what-ifs (quotes recorded only from 11-18); U9-TGT's stop part is large in R only
  because those fills had almost no distance to the stop.
- 2-year data is replay-only and runs optimistic (U11); it was used for fit, not as a verdict.
- Bars were t >= max(1.5, sqrt(2 ln N)) per item; 1,418 configs in total across items.
