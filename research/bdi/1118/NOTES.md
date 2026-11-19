# BDI daily 2026-11-18 (Wednesday), REFOCUSED (CAPTURE / COVERAGE)

*Educational only — not financial advice. These are live **paper** results from one session plus two 2-year lab tests.
Nothing here is evidence that anything works live. **Configurations tried tonight: 2** (swing1118-L15 and EODREV1, one
each). The locked block 2024-11-01..2025-02-28 was not read.*

**Rule changes in window (ledger).** 11-18 is the second session under the 11-16 batch (WB window bands, SPYEXIT for
RW3 / RW5, TSZ1 testing half size, promotion hold from 11-17). Effective 11-18: GY-BENCH (18 Graveyard setups benched
11-18..11-24, 20 guests in), SRCV1 (2-year weight 0), ODPREP, live-quote recording. **From 11-19** the C3 set changes
Primary (NS5 moves to On Deck = Epoch 1, BASE1 twin, EXIT100, ROT caps, WB5): today is NS5's last Primary day, so
Primary figures before and after 11-19 are different books. Testing $ is under TSZ1 sizing.

Accounts: testing = On Deck; testing2 / explore1 / livelab / testingd / testinge / testingf = Testing A–F.
**Market:** SPY open→close **−0.43%** (gap +0.13%; C3 09:50 tag `flat-open / 0950 down`; day type DOWN by the ±0.25%
open→close rule). SPY low −0.87% at 11:20, bounce to +0.05% at 12:33, then −0.3/−0.5% for the afternoon. QQQ −0.21%
(low −1.15%). **IWM +0.74%** (high +1.56% at 12:33): a small-cap-up / large-cap-down split day.

## 0a Move Hunt (research/bdi/moves/moves_1118_out.txt; moves.csv +100 rows)
Inputs were rebuilt in scratch with coverage1029/fetch.py and a memory-light chunked copy of fetch5.py + frames_today.py.
The logic is unchanged; the container was short of memory. Live trades come from all 10 accounts: 1,131 trades on 506
symbols. There were 1,280 liquid names, and the top 25 per side is kept as on earlier days.

| Set | 11-18 | 11-17 |
|---|---|---|
| All movers | **4/50 = 8%, +0.84R** | 2/50 = 4%, +12.64R |
| Tradable (blackout removed) | **5/50 = 10%, +2.00R** | 3/50 = 6%, +10.17R |

- **Catches (all short):**
  - RY, Testing C GEN-261023-03: +1.64R.
  - CNC: Graveyard RW3S, On Deck and Testing A MF4: +0.71R.
  - CME, Testing C GEN-261023-03: −0.36R.
  - KO, Testing C GEN-261023-03: −1.15R.
  - CHYM, tradable set only: +1.16R.
  - Longs: 0/25. Wrong-direction trades on movers: 4, for −3.68R.
- **Miss reasons (all set):**

  | Reason | Misses |
  |---|---|
  | Traded outside the move | 16 |
  | No setup signalled | 12 |
  | Earnings blackout | 10 (5 on the event day, among them TJX, TGT and DIS; WSM reports 11-19) |
  | Skipped | 5 (CRWD spread 44 bps, ELV and MOH spread, GME and INVH cost filter) |
  | Wrong side only | 3 (CTRE, VFC, ISRG) |

- **Three opening group moves make up most of the list.** **76% of the movers decided by 09:45**, before the owner's
  09:50 entry rule.
  - **Managed care short 09:35 → 11:02:** UNH, HUM, ELV, MOH, CNC, CVS, plus DVA (7 of the top 25 shorts). Only CNC was
    caught. Primary traded none.
  - **Retail long on TJX / TGT earnings day (sympathy):** LULU, M, OLLI, VFC, with TJX / TGT / WSM themselves in blackout
    (7 of the top 25 longs). Most were "traded outside the move".
  - **Cyber / software long 09:35 → 11:05:** TENB, CHKP, CRWD, S, BUG, NTSK (PANW, dated 11-18, in blackout). TENB / S / NTSK were
    traded outside the move; CRWD was a spread skip.
  - These are the same patterns as backlog `mh-1029-earnings-sympathy` (rework, 8 configs),
    `mh-1102-group-laggard-hedged`, and the queued C3-MECH 09:35 harness (`mech-0935-harness`). No new idea is added
    tonight; today's list is three more examples for those studies.
- Primary caught **none** of the 50.

## 0b Swing autopsy — Primary (peak → −5.52R)
All 49 Primary trades are closed: **−5.52R** after costs, +$299 Alpaca (+$213 pnl_adj). R and $ disagree because lot size
is capped at ~$4k, so risk per lot ran $12–$195: tight-stop lots dominate R, not dollars (consultant note, owner_inbox).

**Path (1-minute mark-to-market of every lot, costs in; research/bdi/1118 scratch script):** −8.47R at 12:33 (the SPY
bounce top) → **peak +5.27R at 14:39** → −5.52R close. The dashboard showed the peak as about +2.2R at 14:20; its marks come
from polls, mine from 1-minute closes, so the levels differ but the shape is the same. Realised R at 14:20 was already
−3.81R (consultant).

| Leg 14:39 → close (−10.79R by mark) | Lots | R |
|---|---|---|
| Open at the peak, held into the 15:55 flatten | 27 (22 lost) | **−8.40** |
| Open at the peak, stopped / targeted before 15:55 (CME RW3 stop −1.22, JACK L3 stop −1.02) | 5 | −1.59 |
| Entered after the peak (JACK L3 15:01) | 1 | −0.81 |
| By setup: RW3 −4.80 · L3-fromopen −4.61 · RW5 −1.01 · ST7 −0.43 · NS5 −0.15 · NM-ETF +0.22 | | |
| By time: 14:39-15:00 −4.71 · 15:00-15:30 −4.58 · 15:30-close −1.50 | | |

- **What turned it: the crowded open short book drifting up into the close, not the index.** At the peak Primary held 32
  lots, 26 of them short. SPY moved only **+0.07%** from 14:39 to the close (QQQ +0.22%, mostly after 15:30; IWM +0.03%), yet
  22 of the 27 lots held to the flatten lost. The names were low-beta defensives and ETFs (PEP, UDR, CME, AEM, IXUS, VEU,
  SCHE, IWD, COPX) and L3's small caps (JACK, ECVT, PRMB). Each gave back 0.3–1.0R.
- **The day as a whole (realised):** RW3 −4.04R (14 trades; 4 stops −4.42R); L3-fromopen −2.46R, split into **AM +4.12R
  (10) vs 13:00+ −6.58R (9: JACK ×3, ECVT ×4, PRMB ×2, re-entries after stops)**; RW5 −0.31R; NS5 +1.77R; NM-ETF +0.08R;
  ST7 −0.56R. Long / short: +1.29 / −6.81R. Primary skipped **143 "not shortable/ETB"** signals and 6 latch signals.
- **Not repeated here:** same-symbol re-entry and stacking (crunch W7 SYM1 / STACK1); the L3 13:00 cutoff (open
  DECISION L3-AM); a book-wide 15:00 / 15:30 short exit for Primary (consultant CONS-PMX, Primary journal). Book-wide time
  stops (sw-w4-book-exits) and the late profit lock (sat1024, 0 of 6) already failed on 2 years.

**Lead added: swing1118-L15 "EOD-loser short cover"** (hypotheses.jsonl; pre-registered before the run; configs 1;
script research/bdi/1118/l15_bt.py → l15_bt_out.txt).
- **Mechanism:** intraday losers reverse in the last 30 minutes (end-of-day reversal: short covering, liquidity into the
  close). A short in a name already ≥ 2% down on the day has that risk and little left to gain.
- **Rule:** at the 15:30 5-min close, close every open short lot whose symbol is ≤ −2.0% from the open; all other lots
  keep their exit. Every lab short setup. Costs both sides on the alternative.
- **Pass bar:** VALID day-t ≥ 1.5, TRAIN delta > 0, VALID w/o best day > 0, ≥ 60% of families better.
- **2-year result (bt_lab1104, costs in): FAIL (near miss).**

  | Split | Loser lots | Delta | Per lot | Day-t |
  |---|---|---|---|---|
  | TRAIN | 10,937 | −200.0R | −0.018 | −0.75 |
  | VALID | 17,900 | **+534.7R** (w/o best day +388.9R) | +0.030 | **1.42** |
  | LATE (10-06..) | 1,414 | +80.9R | +0.057 | 1.69 |

  - VALID families: **8 better / 0 worse** (RW +257.9, NS +167.1, exhaustion +38.2, GEN +37.4, MF +11.2, CWT +9.2,
    NM +9.0, L +4.7). Setups: 18 better (+547.7R) / 7 worse (−15.9R; worst MF2-FD −6.0R).
  - Primary short family: RW3-FD +16.6 / +14.2 / −0.4R (TRAIN / VALID / LATE), RW5-FD +1.6 / +1.2 / +3.2R. L3-fromopen is
    almost never affected (3 lots): its shorts are in names that recovered, not losers.
  - Mirror (open shorts in names > −2%, same exit): no consistent effect (TRAIN +430.8R t 0.40, VALID −237.7R t −0.44).
    The loser condition is what carries the VALID / LATE effect.
- **What can be salvaged:** it fails on TRAIN (2025; best day 2025-04-21), passes the family spread and is positive in
  VALID and LATE. The live forward shadow costs nothing, so L15 runs as a journal-only shadow from 11-19
  (research/bdi/1118/fwd_l15.py). Its forward bar is ≥ 10 sessions with affected lots, pooled delta > 0 and > 0 on ≥ 60% of
  sessions; there is no trading change and no DECISION.
- **Today, in-sample (does not count):** all 10 accounts, 101 loser lots, delta **+14.12R**, 86 better. Primary only
  3 lots, +0.39R: Primary's giveback was in non-loser names, so L15 would not have saved today's Primary swing.

**Forward tally** (research/bdi/1112/fwd_swings.py on 11-18 → research/bdi/1118/fwd_swings_out.txt; forward.csv +4 rows):

| Lead | 11-18 | Running |
|---|---|---|
| L1 | no class A (NS5 longs class B: n 17, +0.406R) | n 91, −0.420R |
| L2 | no trigger | — |
| L3 | not qualifying (SPY +0.04%, IWM +1.03% at 10:00) | — |
| L6 | counter-index entries 341 at −0.008R vs others 790 at −0.166R (**+0.158**) | 8 sessions, n 3,876, −0.172R |

Lead count: **27 hypotheses + 2 swing-type rows** (L15 new). Backtest passes: only swing1111-L13 LATCH-CLOSE (1 forward
session, not re-tallied tonight). Best positive forward figure: gate1-checkpoint-gate, +13.81R over 3 sessions (last
tallied 11-10).

## 0 Per-account lines (11-18; day type DOWN by open→close, SPY −0.43%; IWM +0.74%)
- $ is the Alpaca day P/L (`pnl_adj` in brackets). R is journal R after costs. L / S is the R from long / short trades.
- The last three columns are **average R per session by SPY day type, 10-06..11-17**, for sessions on which the account
  traded (up > +0.25% open→close, down < −0.25%, quiet between; 10 up / 12 quiet / 9 down sessions in the window).
- Testing B–F have few sessions (1–4 per type). Testing D–F opened 11-12, so their columns are 1–3 sessions only. Do not
  read them as records.

| Account | $ (pnl_adj) | Trades | Avg R | Total R | L / S | Up avg/day | Quiet avg/day | Down avg/day |
|---|---|---|---|---|---|---|---|---|
| Primary | +$299 (+$213) | 49 | −0.113 | −5.52R | +1.29 / −6.81 | −8.92 (10) | −4.70 (12) | +8.87 (9) |
| On Deck | +$170 (+$147) | 62 | −0.122 | −7.59R | −1.39 / −6.19 | −22.40 (10) | −15.74 (9) | −13.79 (9) |
| Testing A | −$252 (−$303) | 266 | −0.214 | −56.85R | −37.40 / −19.45 | −23.15 (9) | −15.21 (9) | −49.46 (9) |
| Testing B | −$49 (−$60) | 47 | −0.141 | −6.64R | −0.85 / −5.79 | +2.58 (4) | +2.40 (1) | −5.11 (4) |
| Testing C | −$83 (−$101) | 78 | −0.159 | −12.43R | −1.39 / −11.04 | +1.93 (4) | −1.17 (1) | −3.87 (4) |
| Testing D | +$38 (+$9) | 153 | −0.004 | −0.58R | +1.07 / −1.65 | +7.28 (1) | — | −7.43 (3) |
| Testing E | −$72 (−$84) | 48 | −0.217 | −10.44R | −5.92 / −4.51 | −20.37 (1) | — | −10.83 (3) |
| Testing F | +$23 (+$3) | 114 | −0.022 | −2.48R | −0.50 / −1.98 | −17.52 (1) | — | +0.02 (3) |
| Gen | −$214 (−$282) | 135 | −0.061 | −8.25R | −24.11 / +15.86 | −33.74 (8) | −24.40 (7) | −32.52 (7) |
| Graveyard | −$74 (−$123) | 179 | −0.129 | −23.02R | +13.38 / −36.40 | −39.21 (7) | −25.12 (6) | −92.75 (7) |

- **This was a down day that did not pay the shorts.** Primary averages +8.87R on down days but lost here: −6.81R on
  shorts. SPY's −0.43% came with IWM +0.74%, so small and mid-cap gap-down names (L3's universe) recovered.
- **COVERAGE gap stands:** Primary loses on up (−8.92R / day) and quiet (−4.70R / day) sessions. No account with enough
  sessions is positive on both. Testing B (+2.58 / +2.40) and Testing C (+1.93 / −1.17) lean the right way on 1–4 sessions
  each, which is too few to read.
- Today's best live block: Testing D `CWT14-failbrk-orl-p10-long-WB5` +8.51R on 71 trades (the CWT14 family is closed to
  new variants by the C3 guardrails). Gen's MP short at +16.63R is an R-basis artefact ($0.80 at risk) and is ignored.

## 3 New tested idea (COVERAGE) — EODREV1, end-of-day reversal long: FAIL
Backlog `wi-eod-reversal` (idea since 10-07, untested), pre-registered in its notes before the run; configs 1; script
research/bdi/1118/eodrev_bt.py → eodrev_bt_out.txt. Chosen because it is the entry form of the L15 mechanism and the
crunch workstreams do not cover the last 30 minutes (W4 = per-setup conditions, W6 = outside-source filters, W7 = Primary
entry removal).
- **Rule:** names with ADV ≥ $95M and price ≥ $5 that are ≤ −2.0% from the open at the 15:30 close. Buy at the 15:30
  close; stop 1R = 0.25 × daily ATR (filled 2c through); else exit at the 15:55 close. 1c + 1 bp per side.
- **Bar:** the Testing bar (t ≥ 1.35), > 0 in TRAIN / VALID and SPY up and down sessions, and beat the all-name baseline by
  ≥ +0.05R.
- **Result: FAIL.** n 50,404 on 446 sessions, **−0.041R** after costs (day-t −5.24). TRAIN −0.083, VALID −0.011, LATE
  −0.024. By SPY day: up −0.048, quiet −0.016, down −0.052.
- **What it shows:** the reversal is real but small. The losers beat the all-name baseline (−0.073R, the cost of a 25-minute
  hold) by **+0.031R**, and by +0.059R on quiet days. The cost of two trades eats it. It is not a COVERAGE setup.
  As an *exit* (L15) the reversal needs no extra entry cost, which is why that form comes close. The backlog card is
  parked with this note.

Scratch (deleted after): `mh1118/`. Educational only — not financial advice.
