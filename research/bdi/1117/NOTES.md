# BDI daily 2026-11-17 (Tuesday), LEAN

*Educational only — not financial advice. These are live **paper** results from one session. They describe the day and
are not evidence that anything works. **Configurations tried tonight: 1** (the L14 backtest).
The locked block 2024-11-01..2025-02-28 was not read.*

**Rule changes in window (ledger).** 11-17 is the first session under the 11-16 batch:
- window bands (WB) on L3-fromopen, RW3-FD, RW5, ST7, NM-ETF late-dip, MF2, RW1, RW7 and others;
- the SPYEXIT engine for RW3 / RW5;
- TSZ1 testing sizing (Testing $ is not comparable with earlier days);
- kill-flat-open and shadow mode.

On 11-16, RW7 moved On Deck → Testing F and RW3S moved Testing E → Graveyard. The promotion hold started 11-17. Today's
figures should not be pooled with earlier days without allowing for these changes.

Accounts: testing = On Deck; testing2 / explore1 / livelab / testingd / testinge / testingf = Testing A–F.
SPY open→close was **−0.81%** (a down day). SPY was −1.12% at 10:45, hit its low of −1.28% at 11:45, bounced to
−0.54% at 12:20 and closed near its lows. QQQ −0.91%, IWM −1.11%.

## 0a Move Hunt (research/bdi/moves/moves_1117_out.txt; moves.csv +100 rows)
Inputs were rebuilt in scratch with coverage1029/fetch.py, fetch5.py and frames_today.py. Live trades come from all
10 accounts: 1,552 trades on 676 symbols. There were 1,274 liquid names. The top 25 per side is kept for comparability
with earlier days. Moves are measured in daily ATR within 90 minutes of a 5-minute decision point.
- **Capture rate 2/50 = 4% in the right direction, +12.64R captured.** On 11-12 it was 5/50 = 10%, +9.31R; that day used
  the same 10-account basis.
  - Longs 0/25. Shorts 2/25: NKE (Gen GEN-261022-09 short, **+10.20R**) and CRM (Testing C GEN-261023-03 short, +2.44R).
  - Wrong-direction trades on movers: 15, for −17.26R. These include 6 NKE longs/shorts the wrong way (−6.79R; Primary's
    ST7 / NS5 NKE longs are among them), plus SCHW and BNY.
  - Tradable set (blackout names removed): 3/50, +10.17R. The extra catch is WCN long, −2.47R.
- **Miss reasons (all set, 48 misses):**

  | Reason | Misses |
  |---|---|
  | No setup signalled | 23 |
  | Traded outside the move | 13 |
  | Earnings blackout | 6 (CTVA-type event names: VIK, DIS, TSN) |
  | Skipped | 3 (BNY and VKTX "halted" — Graveyard hit its halt; STT spread 34 bps) |
  | Wrong side only | 3 (DOG, PSQ, SCHW) |

- **Two clusters account for most "no setup" misses:**
  - **Long inverse / volatility ETPs on the index drop:** UVIX, UVXY, VXX, VIXY, SPXU, SPXS, SDS, SDOW, DOG, PSQ (10 of
    the top 25 longs). No live setup buys inverse ETPs into an index break; DOG and PSQ were only touched by short trades.
  - **Short regional / large banks 09:55→10:55:** KBWB, KEY, HBAN, ZION, CFG, BNY, STT, SCHW (8 of the top 25 shorts).
    These were mostly "no setup" or "traded outside the move". Primary's RW3 shorted KBE / KRE only at 12:05, after the
    bank move had finished, and was stopped.

## 0b Swing autopsy — Primary (−1R → −6.73R closed at 12:16 → −2.46R / −$465 at the close)
All 22 Primary trades are closed. The parts of the swing below sum to the leg exactly. The method is a lean
trade-cluster split, not the minute-level beta decomposition of research/bdi/1110/swings.py.

| Leg 09:50→12:16 (−6.73R) | R | Part |
|---|---|---|
| BEZ: 4 × L3-gap-slope-fromopen-FD shorts 10:00-10:30, all stopped by 10:43 | −4.33 | top name / bad entries |
| NKE: ST7 long 10:45, NS5 long 11:20 (SPY −1.0% from open) | −2.24 | setup–day mismatch |
| KBE + KRE: RW3-FD shorts at 12:05, the first leg of SPY's +0.5% bounce | −2.51 | market direction |
| BLMN: 3 × L3 shorts, all hit target | +2.36 | offset |

| Leg 12:16→close (+4.27R) | R |
|---|---|
| RW5-FD shorts IYR / XHB / DE / AA / RNR, entered 12:15-12:21, all hit target | +4.29 |
| NM-ETF late-dip longs (LABD, SOXL, TECL, TQQQ) | +0.74 |
| VST NS5 long flattened | −0.81 |
| EWT RW3 short flattened | +0.05 |

- **BEZ** gapped down and then squeezed from its 7.42 open to 9.00 at 10:50 (+21%) while SPY fell. L3's rule shorts
  gap-down names that are already up > 3.46% from the open, so BEZ fit the rule every 10 minutes. Both the L3 and RW3
  −2R latches fired.
  - Primary had **77 "not shortable/ETB" skips** and 21 "setup daily loss limit" (latch) skips.
- **What turned it:** RW5's five sector / ETF shorts sold SPY's 12:20 bounce high (−0.54%), and the index then
  slid back to −1.29% by 15:15. All five hit target. The ETF late-dip longs added a little into the close.
- **Market vs setup:** this was a down day. The longs lost (−2.31R long vs −0.15R short), and three names / clusters (BEZ,
  NKE, KBE/KRE) made −9.08R of the losses. Re-entry and spike (FADEMOVE) filters and the latch level were not
  re-tested: research/latch_review_1117 already covers them, with the latch kept and both filters hurting.

**Lead added: swing1117-L14 "down-day bounce, matured"** (hypotheses.jsonl; pre-registered before the run; configs 1;
script research/bdi/1117/l14_bt.py).
- **Rule:**
  - Qualifying day: SPY's lowest 5-min close from the open over 09:35-12:00 is ≤ −0.75%.
  - B = first bar ≤ 13:30 that is back up by ≥ +0.30 percentage points.
  - A = RW3 / RW5 / MF2 / MF4 -FD shorts entered B+10..45 min; C = same-day family shorts entered B−60..B+10.
- **Pass bar:** n_A ≥ 40 on ≥ 8 days, A ≥ +0.10R, A − C ≥ +0.20R, paired t ≥ 1.5, positive in both train and valid.
- **2-year result (bt_lab1104, costs in): FAIL.**
  - 43 qualifying days.
  - A: n 761, −0.408R. C: n 735, −0.244R. A − C −0.164R.
  - Paired day diff +0.069R (t 0.69); train +0.162, valid −0.028.
  - By setup in A: MF2 −0.64, MF4 −0.33, RW3 −0.22, RW5 −0.32.
- **What can be salvaged:** on deep down mornings the whole short family loses after the low, in both windows and worst
  on days that close up. That points at a *family-off after a deep morning low* idea rather than a timing one. It is not
  tested tonight. L14 is closed and gets no forward shadow.
- **Today, in-sample:** B = 12:05; A (RW5) +4.29R vs C (RW3 KBE/KRE) −2.51R.

**Forward tally** (research/bdi/1112/fwd_swings.py on 11-17 → research/bdi/1117/fwd_swings_out.txt; forward.csv +4 rows;
11-13 / 11-16 not logged):

| Lead | 11-17 | Running |
|---|---|---|
| L1 | no class A | n 91, −0.420R |
| L2 | no trigger | — |
| L3 | not qualifying (SPY +0.13%, IWM +0.15% at 10:00) | — |
| L6 | counter-index entries 532 at −0.344 vs others 1,020 at −0.270 (−0.074) | 7 sessions, n 3,535, −0.188R, t −1.26 |

Lead count: 26 hypotheses + 2 swing-type rows. Only one lead has passed its backtest: swing1111-L13 LATCH-CLOSE. Its
forward record is 1 session, so it is too early to read. The best positive forward figure is gate1-checkpoint-gate:
+13.81R over 3 sessions, but it was last tallied 11-10.

## 0 Per-account lines (11-17; day type DOWN, SPY −0.81%)
- $ is the Alpaca day P/L (after costs as booked; `pnl_adj` in brackets).
- R = journal R after costs.
- L/S = R from long / short trades on this down day.

| Account | $ (pnl_adj) | Trades | Avg R | Total R | L / S |
|---|---|---|---|---|---|
| Primary | −$465 (−$520) | 22 | −0.112 | −2.46R | −2.31 / −0.15 |
| On Deck | −$523 (−$569) | 120 | −0.332 | −39.80R | −2.09 / −37.71 |
| Testing A | −$422 (−$495) | 308 | −0.169 | −51.94R | −41.45 / −10.49 |
| Testing B | +$10 (−$11) | 91 | −0.040 | −3.65R | −17.62 / +13.96 |
| Testing C | −$7 (−$19) | 62 | −0.088 | −5.47R | −15.26 / +9.78 |
| Testing D | −$132 (−$158) | 110 | −0.301 | −33.11R | −36.41 / +3.30 |
| Testing E | −$11 (−$26) | 78 | −0.064 | −5.01R | −3.01 / −2.01 |
| Testing F | −$12 (−$64) | 187 | −0.056 | −10.51R | −37.63 / +27.12 |
| Gen | −$357 (−$408) | 200 | −0.643 | −128.69R | −6.98 / −121.70 |
| Graveyard (halted) | −$683 (−$738) | 374 | −0.474 | −177.41R | −231.00 / +53.58 |

On a down day, every account but On Deck and Gen made its R on the short side or lost it on longs. On Deck's and Gen's
shorts lost heavily: −37.7R and −121.7R. Testing $ is under TSZ1 sizing from today.

Scratch (deleted after): `mh1117/`. Educational only — not financial advice.
