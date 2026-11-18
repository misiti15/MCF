Educational only — not financial advice

# Graveyard deep dive — 2026-11-18 (after the close; research only, no config change)

**Data:** live journals (run_id 1) of all ten accounts, 10-06..11-18, R after costs = pnl_adj / (|entry − stop| × shares);
identical signals across accounts (setup, symbol, date, entry minute) counted once. Day types are hindsight SPY
open-to-close labels (> +0.25% up, < −0.25% down, else quiet; research/usage/u5_daytype), 10-06..11-17 (11-18 unlabelled).
"Primary winners" = the 8 Primary setups with positive total R in the window (L3-gap-slope-fromopen-FD, MF4-h40,
NM-ETF-late-dip, NS4, NS5, RW3-FD, RW5-FD, ST7). Locked block not read. Code: `code/` (gy.py → raw stats, triage.py →
TRIAGE.csv, pot.py → pot cost). Input from research/usage/u8_graveyard_prep (10 revival tunes, 0 passed, 1,100 configs).
This review tried no new configuration (0 configs); it ranks and classifies only.

**Rule changes inside the window (ledger):** Graveyard opens 10-21 with the −2R per-setup latch; 10-27 slot cut; 10-28
sizing; 10-29 Primary −2R latch; 11-12 LR3/LR8 cost batch and REPV-11/12 (300 smaller Graveyard slots); 11-13 RW6 → Testing C,
ST4 → Testing B; 11-16 RW3S in, ROT1; 11-17 KILL-FLAT open, TSZ1 testing half size, promotion hold; 11-18 GY-BENCH
(17 residents rest 11-18..11-24), 20 guests in, recorded quotes / SRCV1. Whole records mix these regimes; Graveyard-only
columns start 10-21 or at each move date.

## Scope

`config/account_graveyard.yaml` has 54 blocks: 34 residents + 20 GY-BENCH guests (guests return home 11-25 and are judged
there; 2 guest trades on 11-18, −2.1R). Of the 34 residents, 2 are `enabled: false` since 11-13 (RW6, ST4 — in the arena),
17 are benched 11-18..11-24, 15 ran today.

## Triage (34 residents)

| Triage | n | Setups (display name) |
|---|---|---|
| TUNE-CANDIDATE | 3 | Early Sellers into a Pop (MF3-FD), Early Sellers Above VWAP (MF1-FD) — wait for C3-WB5 #3; Big Loser VWAP Reclaim Fade (NS3-FD) — waits for C3-WB5 #2 |
| KEEP-TESTING | 9 | Big Gainer Fade, VWAP Band Guard (RW6G1-FD), Midday Gap-Up Dip Buy (heat_fade_long), Gap-Down Bounce Rejection Short (CWT09-bounce), Sellers into Strength (MF5-FD), Gap-Down Heavy-Selling Short (RW3S-FD), Big Gainer Average Reclaim Fade (NS2, NS2-FD), Big Loser Flush Buy (NS5-FD), Opening-Range Breakdown Buy (ST1-FD) |
| ARCHIVE (proposed, GY-ARCHIVE-20) | 20 | 9 CWT14 + 2 CWT12, Morning Bounce Fade (heat_fade_short, -FD), Midday Gap-Up Dip Buy (all day) (heat_fade_long-FD), Big-Stock Blow-off Short (RW2-FD), Opening-Range Low Sweep Reversal (LIQ), Down-Stock Trend-Turn Buy (ST2-FD), Stretched Above VWAP Fade (CWT13), Gap-Down VWAP Loss Short (CWT09-vwaploss), Big-Stock VWAP Reclaim Fade (RW4-FD) |
| N/A (in arena) | 2 | RW6-FD (Testing C), ST4-FD (Testing B) |

Per-setup numbers (record, w/o best day + share, Graveyard-only, last-5 / last-10, day type, rho, overlap, mechanism,
untried tunes, reason) are in TRIAGE.csv.

### Highlights

- **No resident is positive w/o its best day over its whole record** (U8 finding holds with 11-18 added). Best whole
  records: RW6G1 +0.020 (−0.055 w/o best; best day 297% of the total — a `1 day` record), NS2-FD −0.028 (−0.233 w/o best).
- **Graveyard-only positives:** heat_fade_long 137 trades +0.093 (+0.012 w/o best), last-10 +25.3R; NS2-FD 216 trades
  +0.116 (−0.114 w/o best — one-day), last-10 +34.2R; RW6G1 37 trades +0.171 (+0.120 w/o best). These three are the
  pot's live cases.
- **Trend:** last-10 total R is positive for 4 residents (NS2-FD +34.2, heat_fade_long +25.3, RW6G1 +8.0,
  ST1-FD +3.7) and negative for every archive name (−3.5 to −93.7R).
- **Day-type fit (hindsight):** the fades lose on SPY-up days — heat_fade_short-FD −0.61 (n 192) vs +0.16 down (n 298);
  heat_fade_short −0.57 vs +0.04; MF1/MF3/MF5 −0.43 to −0.59 on up days; CWT09-bounce −0.61 up / +0.35 down. The
  failed-break longs (CWT14 ORL/PDL, CWT12) lose most on down days (−0.20 to −0.76). Hindsight labels are not tradable;
  U5 found no real-time day-type cue with an edge, so this is input for C3-MECH, not a tune.
- **Correlation with Primary winners:** the shorts that sit near Primary's book — NS2-FD 0.43, heat_fade_short-FD 0.44,
  MF3 0.42, MF1 0.37, MF5 0.35 — would add little diversification if revived; same-symbol overlap is highest for
  NS5-FD (34%, Primary NS5's twin), MF5 (21%), MF3 (20%), RW3S (14%). The CWT14 ORL longs are the most negatively
  correlated (−0.42 to −0.59) but lose on their own.
- **Mechanisms:** archive names are mostly level-trap reversals (CWT14), compression breakouts (CWT12) and late-day
  stretch fades; the KEEP/TUNE list is mostly overextension / order-flow shorts and the gap-up dip buy.

## Pot cost (Graveyard account)

- 21 sessions (10-21..11-18): 9,330 resident trades, **−1,095.3R**; 2 green sessions of 21. Worst 11-17 −177.4R.
- 10 sessions before GY-BENCH (11-04..11-17): **579 trades/session, −62.5R/session** (−$243/session at REPV-11 lot sizes).
  - The 20 archive names: 477 trades, **−66.5R**, −$444 per session; 82% of trades; ~1,760 of ~2,100 signals per session.
  - The other 12 residents + 2 now in the arena: 102 trades, **+4.0R** per session (+40.1R over 10 sessions; best day
    11-12 = 186% of the total, avg R w/o best day −0.042 — a one-day record).
- Slots: 300 slots / 75 per setup; archive names hit the per-setup cap on busy days (CWT14 ORL p05 ~50 trades/session).
  Usage: Graveyard journal 29.7 MB (largest of the ten), ~2,400-2,800 signal rows and 750-1,170 order rows per session.
- 17 of the 20 archive names are already resting under GY-BENCH until 11-24; archiving changes 3 running setups now
  (CWT13, CWT09-vwaploss, RW4-FD) and keeps the 17 off from 11-25.
- Inflow: C3-EXIT100 flags 31 arena setups (−1,251R) for the Graveyard; without an exit the pot would roughly double.

## Decisions written

- **GY-LIFE (Yes)** — the standing lifecycle rule in RULE.md (entry = C3-EXIT100, Friday review, archive rule, revival
  test, graduation, pot budget).
- **GY-ARCHIVE-20 (Yes)** — archive the 20 names above (`enabled: false` + `archived` marker, record kept, re-testable,
  never deleted). Applied in an after-close window once approved, with a ledger entry and assignments.json regenerated.

## Caveats

- 11-18 has no day-type label; Graveyard-only records are 3-21 sessions. One or two days move any number here.
- Archive criteria were written after seeing U8 and these stats (not pre-registered); they mirror C3-EXIT100's thresholds
  so that one bar covers the arena exit and the Graveyard exit.
- Correlations use days where both the setup and Primary traded (≥ 8 days).
