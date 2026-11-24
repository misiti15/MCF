# BDI daily 2026-11-24 (Tuesday): CAPTURE / COVERAGE

*Educational only — not financial advice. Live figures are **paper** results; the lab covers 2 years. **Configurations
tried tonight: 3** (GAPDEF-1124 A / B / C, the same 3 on live and lab). The locked block 2024-11-01..2025-02-28 was not
read. Lean run: scratch under scratchpad/bdi1124 (deleted after).*

**Rule changes in the window (ledger).** Nothing effective 11-24. Earlier in the windows used below: 11-19 C3 Epoch 1;
11-20 stop rounding fix; 11-23 ST7 out of Primary (lineup RW3-FD, RW5-FD, L3-fromopen, NM-ETF), BRAKE-BURST, PSHADOW,
FOOTRACE-EXIT. The 10-23..11-24 live window of the gap study also spans 10-28 Primary sizing, the 10-29 -2R latch,
11-12 LR8 costs, ROT1 (11-16), TSZ1 (11-17) and the account moves of RW7 (11-13/16), RW3S (11-12/13) and RW1 (11-12).

**Market: a rotation day.** NVDA −8% / QQQ −2.5% vs the prior close; SPY +0.51% open→close (an **up** day by the ±0.25%
rule), QQQ −0.39%, IWM +0.94%, XLV +2.8% from the open. Money moved into health care, staples, utilities, REITs and
small caps from 09:35.

## 0a Move Hunt (research/bdi/moves/moves_1124_out.txt; moves.csv +100 rows)
Inputs rebuilt with research/ops/coverage1029/fetch.py, moves/fetch5.py and frames_today.py; moves.py unchanged, all 10
accounts (1,273 trades on 609 symbols), 1,289 liquid names, top 25 per side.

| Set | 11-24 | 11-23 (last run) |
|---|---|---|
| All movers | **2/50 = 4%, +0.62R** | 5/50 = 10%, +0.40R |
| Tradable (blackout removed) | **3/50 = 6%, +1.10R** | 5/50 = 10%, +0.40R |

- **Catches (all shorts):** EBAY (Testing A GEN-261026-01, +1.71R), KYMR (Testing C GEN-261022-04, −1.09R); tradable
  adds SUNB (Testing C GEN-261023-03, +0.48R). **Long side 0 of 25.**
- **What was known at the decision point:** 21 of 25 long movers were decided at 09:35–09:40 — the rotation bid, from
  the open: BMRN, BSX, ABT, MCK, AHR, MANH, DUK, SRE, VICI, NNN, OHI, EFX, WTW, DOCU (MDT / SJM blackout). They were
  sector moves (health care, utilities, REITs), not stock news. The short side's biggest moves were the afternoon
  slide in the agri processors (BG −2.85 ATR from 13:35, DAR, ADM); DAR / ADM short signals were **skipped by the
  setup daily loss limit**, and 4 ADM longs went the wrong way (−4.75R).
- **Miss reasons (all set):** no setup signalled 17, blackout 11, traded outside the move 10, wrong side only 5,
  skipped 5. Wrong-direction trades 14, −10.20R.
- **Read:** the morning rotation into defensives is the second session running (11-23 CL / CHD / CLH) where the
  biggest long moves were sector bids decided at 09:35–09:40 that no long setup takes, while the gap-down short family
  shorted the same groups (step 0b).

## 0b Swing autopsy: Primary (research/bdi/1124/swings.py → swings_out.txt, timeline_p.csv; method unchanged)
- **Close:** **−11.71R after costs**, −$600.04, 25 trades (7 wins after costs). Realised path peak −1.25R (10:25).
- **Mark (1-min, no costs while open):** peak **+1.07R at 10:28**, trough **−10.78R at 14:20**. PTLO (L3-fromopen ×3,
  −3.87R, all stopped 10:11–10:40) is not on this curve (below the $60M-ADV bar set), so the true trough is ≈ −14.6R.

| Leg | R | Market | Setup-day mismatch | Bad entries | Stock-specific |
|---|---|---|---|---|---|
| **10:28 → 14:20** (the day's swing) | **−11.85** | −1.84 | **−3.74** | −0.63 | **−5.64** |
| 10:28 → 12:44 | −9.09 | −4.35 | −2.00 | −0.21 | −2.53 |
| 14:20 → 15:02 (the turn) | +7.03 | **+6.38** | +0.04 | −0.03 | +0.64 |
| 15:37 → close | −4.69 | −4.52 | +0.65 | 0.00 | −0.82 |

- **Top 5 names in 10:28 → 14:20 (−6.12R), all Gap-Down Pop Fade, Heavy Selling (`RW3-gapdn-rsi5pop-flowsell-short-FD`):**
  INDA −1.60R, BMO −1.20R, AVT −1.12R, GMED −1.12R, LUNR −1.08R. By setup in the leg: RW3 −9.81, RW5 −2.12, NM-ETF +0.08.
- **What it was:** 19 of 21 entries in the leg were shorts (avg final −0.415R) in names that were barely red at the
  open (JNJ 0.0%, INDA −0.2%, BMO −0.7%) or in groups the rotation was buying. The stock-specific and mismatch parts
  (−9.38R of −11.85R) are the "gap that was not a gap" failure, not the index.
- **What turned it:** the index. SPY faded +0.59% → +0.10% from 14:20 to 15:02 with the book at net beta −15R per +1%
  SPY (13 shorts open): +6.38R of the +7.03R leg is market. It gave −4.52R of that back into the close.
- **Lead:** none new. The swing type recurs from 11-23 (swing1123-L18, defensive counter-gap rebound; closed); a
  `recurrence_1124` note is added to L18, and the testable version is tonight's family remedy (step 3–4, GAPDEF-1124).
- **Forward tallies:**
  - **swing1118-L15** EOD-loser short cover (1124/fwd_l15_out.txt): today **+33.61R on 182 lots, 9 of 10 accounts
    better** (Primary +2.47R on 8 lots; Gen −0.13R). Out-of-sample 4 of 10: 2 of 4 sessions > 0, pooled **−46.64R**.
  - **fwd_swings** (1124/fwd_swings_out.txt, research/bdi/1112/fwd_swings.py): L1 no class-A lots; L2 no trigger;
    **L3 qualifying** (SPY +0.64%, IWM +1.06% at 10:00): shorts after the 10:45 cut −0.585R (n 114) vs before −0.096R
    (n 49), so after − before −0.489 — against L3 (running 12 sessions −0.339, t −2.66). L6 counter-index entries
    n 411 +0.167R vs others −0.307R (+0.474), opposite to L6's sign again (running −0.231, t −1.58).
  - **swing1111-L13 LATCH-CLOSE:** not re-tallied tonight (usage); stays +302.7R over 7 sessions to 11-20, `1 day` (69%).
- **Lead count:** 32 rows in hypotheses.jsonl (16 swing L-leads), 0 added. Best forward lead is still L13.

## 0 Per-account lines (11-24; research/bdi/1124/acct.py → acct_out.txt)
$ = Alpaca day P/L (nightly). R = journal R after costs. Peak = realised running peak (exit order). Day-type columns =
avg R per traded session 10-06..11-23 by SPY open→close (up / quiet / down; sessions in brackets). Today is an **up** day.

| Account | $ | Trades | Avg R | Total R (L / S) | Peak (time) | Best setup | Worst setup | Up / Quiet / Down per day |
|---|---|---|---|---|---|---|---|---|
| Primary | −$600 | 25 | −0.468 | −11.71 (+0.40 / −12.11) | −1.25 (10:25) | NM-ETF-late-dip-di-long +0.40 (2) | RW3-gapdn-rsi5pop-flowsell-short-FD −7.05 (12) | −8.92 (10) / −4.70 (12) / +4.74 (13) |
| On Deck | +$4 | 98 | −0.053 | −5.24 (−4.38 / −0.86) | −1.05 (10:24) | L3-gap-slope-rsi5hi-FD +5.97 (46) | RW1-gapdn-bounce-flowsell-short-FD −7.53 (39) | −22.40 / −15.74 / −10.58 |
| Testing A | +$9 | 99 | −0.019 | −1.90 (+6.20 / −8.10) | +3.93 (12:45) | NM-AR-AM-gapdown-capitulation-long +10.76 (18) | RW3-gapdn-…-FD-RQa-1230 −5.54 (10) | −23.15 / −15.21 / −31.77 |
| Testing B | +$102 | 48 | +0.071 | +3.42 (+0.15 / +3.27) | +3.90 (15:55) | L3-gap-slope-rsi5hi-FD-WB4 +7.23 (26) | CWT04-backside-lh-a15-short −2.43 (2) | +2.58 / +2.40 / +3.19 |
| Testing C | +$56 | 57 | +0.002 | +0.09 (+1.10 / −1.01) | +1.95 (10:06) | L3-gap-slope-rsi5hi-FD-WB5 +4.05 (26) | GEN-261022-04 short −4.56 (4) | +1.93 / −1.17 / −19.38 |
| Testing D | −$170 | 106 | −0.222 | −23.55 (−14.05 / −9.49) | −1.00 (11:13) | GEN-261027-01 long-WB5 +1.72 (4) | GEN-261027-10 long −15.09 (47) | +7.28 / — / −3.37 |
| Testing E | −$336 | 160 | −0.223 | −35.68 (−5.19 / −30.48) | +2.88 (11:12) | GEN-261027-01 long +1.85 (4) | RW7-gapdn-bounce-early-short-FD-WB3 −21.33 (50) | −20.37 / — / −1.64 |
| Testing F | −$280 | 142 | −0.269 | −38.19 (+1.31 / −39.50) | +5.09 (10:28) | MF1-945-flowsell-vwapup +5.65 (1) | RW7-gapdn-bounce-early-short-FD −33.55 (98) | −17.52 / — / +1.25 |
| Gen | +$17 | 145 | −0.086 | −12.50 (−19.14 / +6.64) | −1.11 (10:01) | GEN-261020-09 long +25.55 (41) | GEN-261021-02 long −44.69 (44) | −33.74 / −24.40 / −28.85 |
| Graveyard | −$392 | 393 | −0.179 | −70.25 (−48.63 / −21.62) | +9.57 (11:16) | GEN-261023-09 short +8.22 (24) | RW3S-gapdn-flowsell-short-FD −44.70 (88) | −39.21 / −25.12 / −84.03 |

- The worst setup in 6 of 10 accounts is a gap-down short family member (RW3, RW1, RW3-RQa, RW7-WB3, RW7, RW3S): the
  family is today's loss. The L3-rsi5hi copies were the best setup in On Deck, B and C (+17.25R together).
- **COVERAGE gap unchanged:** Primary averages −8.92R per up day (10) and added another (−11.71R).
- **Today's win:** Testing A's Gap-Down Capitulation Long (`NM-AR-AM-gapdown-capitulation-long`) +10.76R on 18 — it
  bought the side of the rotation that the short family sold. Gen GEN-261020-09 +25.55R (41) is a one-day figure.

## 1 Patterns (research/bdi/patterns.csv +399 loser rows; research/bdi/1124/patterns.py → patterns_out.txt)
Accounts Primary, On Deck, Testing A–F (735 trades). Classifier unchanged.
- **Never worked** −97.1R (113) is today's type again (Testing F −27.3, E −25.0: RW7 / RW7-WB3 shorts); small MFE then
  failed −54.6R (57); late hold −41.5R (123); gave back −27.1R (49); wrong side after a big swing −25.7R (45).
- Primary: never worked −8.2R, small-MFE −4.6R (7 of 11 stops had MFE ≤ 0.05R, nightly) — entries with no follow-through.
- Stacking: lot 2+ 37 trades −0.140R vs lot 1 −0.154R — not the problem today.
- Inverse ETPs: short-exposure ETP longs (IWM / QQQ / GDX inverse) won in every account (+0.2..+0.9R each).

## 2 Recurring patterns → rules
- Gap-down short family on names that did not really gap (11-23, 11-24): tested tonight as GAPDEF-1124 (below).

## 3–4 Tested idea: GAPDEF-1124 family gap-definition remedy — FAIL (configs 3; research/bdi/gapdef_1124/NOTES.md)
- **Live (10 journals 10-23..11-24, 2,927 family trades, LR8):** A (first-minute-VWAP gap ≤ −1%) +42.11R but 11-24 is
  148% of it (w/o best day −20.17R, day t 0.45); setups 12 better (+65.19R) / 8 worse (−23.09R; RW7 −8.39R). B (≤ −0.5 ATR)
  −2.21R. C (before-noon cutoff arm) +48.02R, 11-24 = 305%.
- **Lab (2 years, bench10, 82,809 trades):** A removed vs kept avg R fit −0.092 vs −0.090 (no edge), check −0.034 vs
  −0.016; B wrong sign. The thin-print part alone looks useful in the lab (−0.070 vs −0.043) but cut L3 winners live.
- Next step: thin-print guard alone, 1 config, per setup (backlog note). No Testing-copy suggestion.

## 5 Decision
None. Nothing passed.

Educational only — not financial advice.
