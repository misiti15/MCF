# BDI 2026-10-30 (Friday): Move Hunt day 2, opening-level precursor test, account blocks

*Educational only — not financial advice. Live numbers are **paper** results from one session. The precursor test uses
the open two-year opening frame (research/bdi/timeofday/data/open, 09:35-10:30, built from the 1-minute SIP cache with
the locked block dropped at load; asserted absent in the script). **The locked block 2024-11-01..2025-02-28 was never
read.** **12 configurations were tried tonight (MH3), all reported below; none passes.** No config, setup, exit, ledger
or docs/live file was changed. Costs are in everywhere (P/L = journal `pnl_adj`; avg R = `pnl_adj / $ risk`).*

Built on, not redone: nightly1030 (close / coverage / handover gap, Primary WHY, late-short swarm 0/12, L3 borrow,
DM-NS3 / DM-MF), the four PDL / Reddit swarms (pdl1030*, rdt1030).

## Today's win
**The Move Hunt pinned down where the day's moves are, and ruled out the obvious way to catch them.** Day 2 confirms the
opening hole: **33 of the 50 biggest tradable moves started at the 09:35-09:45 decision bars (10-29: 30 of 50), and live
caught 0 of those 33.** The most visible opening precursor of the day (names popping up into the prior-day high and then
falling 1.1-1.3 ATR; the mirror at the prior-day low) was tested on two years in 12 pre-declared configurations and fails
everywhere (best t −4.3): the opening moves follow the day's direction, with no excess over a random 09:35 entry. That
saves building opening-level setups. Second measurable step: wrong-side R on the big movers fell from −16.1R to −4.1R.
Testing 1 and Testing 2 closed green (+$57.88 / +$55.10).

## 0a. Move Hunt (v1 definition unchanged; scripts research/bdi/moves/, output moves_1030_out.txt; moves.csv +100 rows)
Inputs: SIP 5-minute bars 10-01..10-30 for 1,535 symbols (`fetch5.py` with the start moved to 10-01 for disk), live
priors + SIP 1-minute bars (`research/ops/coverage1029/fetch.py`), the 5 journals. 1,175 liquid names, 77,448 decision rows.

| set | caught (right side) | R captured | wrong-side trades | main miss reasons |
|---|---|---|---|---|
| all (top 25 + 25) | **1 / 50 (2%)** (VSAT long, GY CWT12-coil) | +0.26 | 2, −0.26R | blackout 35 (22 on the event day: GPN +6.8 / −3.3 ATR, FISV, FIS, RMD, CDW, ZBRA, RBLX, AAPL) |
| tradable (blackout removed) | **3 / 50 (6%)**: long 3/25, short 0/25 | **+1.49** | 7, **−4.06R** | traded outside the move 20, no setup 18, skipped 6, wrong side only 3 |

**vs 10-29: 26% (13/50, +3.59R, wrong side −16.13R).** Caught: VSAT (GY CWT12-coil-k4 +0.26R), UPRO (T2 CWT13-z075
+1.61R), SPXL (T2 CWT13-z05 + Gen GEN-261026-06, −0.38R) — all three late-day index-bounce longs except VSAT.

What was known at the decision point, and why they were missed (only data available then):
- **The open (33 of 50).** The 25 biggest tradable shorts: 22 at 09:35-09:40. Ten of them were up from the open
  (+0.3..+1.6%), RSI5 77-100, within ~0.3 ATR of the prior-day high (WSM, MTN, GAP, QLYS, M, ULTA, KSS, NOC, BUG, DOV),
  then fell 1.1-1.3 ATR in 35-90 min on a trend-down day. No live setup runs before 09:50; the names were "traded
  outside the move" (later entries) or "no setup signalled". Long side at the open: TSLA / TSLL / TSLG / MAGS flushed
  into the prior-day low (RSI5 1-3) and bounced 1.2 ATR.
- **Groups.** Cyber-security (RBRK, NTSK, QLYS, BUG; second day after the TENB sympathy move) and retail (GAP, M, KSS,
  ULTA, WSM) fell as groups at 09:35-09:40. Bitcoin ETPs (IBIT, FBTC, BITO, BITX) rose together 10:15-11:18.
- **Volatility ETPs at the index turn** (VXX, UVXY, UVIX: long 13:00-14:34 +1.2 ATR, short 14:35-15:51 +1.6 ATR) — no
  setup signals them; the turn sat inside the 14:36-14:49 hand-over gap (nightly1030).
- **Skips:** AIOK short (+2.0 ATR) not shortable; WSM, ULTA, NOC spread > max; SNX long spread 32% of stop; SSO long
  cost filter / buying power (Gen).

Precursor test (one day of rows, hindsight labels; first 09:35-09:45 bar per symbol): PDH-pop short (k 0.30) 90
signals, 51% reached ≥ 0.5 ATR down within 90 min vs a 34% base; PDL-flush long (k 0.30) 75 signals, 5% vs 7% base.
Only the short side looked like a precursor — on a down day. Tested on two years below.

## 3. New tested idea: MH3 opening pop into the prior-day high (`research/bdi/1030/mh3_open_pdh.py`, `mh3_out.txt`)
Pre-declared in the script: first of 09:35 / 09:40 / 09:45 per symbol-day; short = |close − PDH| ≤ k ATR, fromOpen > 0,
RSI5 ≥ 70; long mirror at PDL with fromOpen < 0, RSI5 ≤ 30; k 0.15 / 0.30; exits t1s1 (lab) and stop 0.25 ATR held to
10:30; plus (declared before scoring) an SPY-direction gate (SPY fromOpen ≤ −0.10% for shorts / ≥ +0.10% for longs at
the same bar). adv20 ≥ $95M, blackout removed, production costs with the 09:35 entry multiplier (3.8x). Train ≤ 2025-09-30.

| config | n | avg R | t | w/o best day | train / valid | up / down | excess vs random 09:35 |
|---|---|---|---|---|---|---|---|
| short k15 t1s1 | 52,396 | −0.137 | −7.45 | −0.141 | −0.187 / −0.109 | −0.359 / +0.099 | −0.003 |
| short k30 t1s1 | 81,354 | −0.135 | −7.69 | −0.138 | −0.187 / −0.106 | −0.351 / +0.097 | −0.001 |
| short k30 t1s1 SPY-gated | 19,481 | −0.173 | −6.01 | −0.181 | −0.203 / −0.157 | −0.365 / +0.024 | −0.039 |
| short k15 h1030 | 52,396 | −0.141 | −6.84 | −0.145 | −0.172 / −0.123 | −0.323 / +0.090 | +0.010 |
| short k30 h1030 | 81,354 | −0.140 | −7.09 | −0.143 | −0.172 / −0.123 | −0.326 / +0.087 | +0.011 |
| short k30 h1030 SPY-gated | 19,481 | −0.181 | −5.30 | −0.194 | −0.188 / −0.178 | −0.315 / −0.008 | −0.031 |
| long k15 t1s1 | 50,434 | −0.124 | −6.73 | −0.126 | −0.113 / −0.129 | +0.067 / −0.320 | −0.004 |
| long k30 t1s1 | 77,858 | −0.119 | −6.73 | −0.122 | −0.113 / −0.123 | +0.079 / −0.315 | +0.000 |
| long k30 t1s1 SPY-gated | 18,794 | −0.134 | −4.44 | −0.143 | −0.100 / −0.148 | +0.033 / −0.352 | −0.014 |
| long k15 h1030 | 50,434 | −0.114 | −5.26 | −0.118 | −0.107 / −0.117 | +0.078 / −0.295 | +0.008 |
| long k30 h1030 | 77,858 | −0.114 | −5.22 | −0.118 | −0.109 / −0.116 | +0.094 / −0.297 | +0.008 |
| long k30 h1030 SPY-gated | 18,794 | −0.150 | −4.34 | −0.161 | −0.129 / −0.158 | +0.011 / −0.329 | −0.029 |

**Failed** (backlog `mh-1030-open-pdh-pop-fade`, status failed, 12 configs). N 12: full bar 2.23, BAR90 2.01; best t
−4.34; walk-forward positive months 0-19%. The level adds nothing over a random 09:35 entry; the result is the session's
direction (shorts win only on down days, longs only on up days), and the early SPY gate makes it worse (early index moves
mean-revert). No locked look spent, no Testing entry. Lesson for the Move Hunt: the opening movers are the day's beta;
a precursor has to say which way the *day* goes, or which *group* moves, not where a name sits vs a level.

## 0. Per-account session review (`accounts.py` → accounts_out.txt; peak / close from nightly1030 daily_peak.csv)

**Primary** — **−$91.43** after costs, 15 trades, 47% win vs 55% break-even, −0.168R; peak +$144 (14:21) → −$91
(give-back $236: the 5 late shorts RW3-FD ×3, RW5-FD, MF2-FD stopped in the +0.7% bounce off the 14:52 index low).
Best NS5-sma50-flush-oversold-long +1.9R (+$112), MF4-h40-FD +0.4R; worst RW3-FD −3.3R (−$125), RW5-FD −1.1R.
Sides: longs +0.265R / +$92, shorts −0.662R / −$184. Stack: ZETA 3 lots −$154 (first lot +0.4R, extra lots −1.2R; the
nightly found stacking not worse on Primary's record). Notable skips: L3-fromopen-FD 41 of 46 not shortable. Move Hunt:
Primary caught 0 of the 50 movers. Edits: (1) late-short skip — tested by nightly1030, failed 0/12, no change; (2) the
14:40 / 14:45 decision bars lost to the hand-over (OPS-HANDOVER, housekeeping) — this is the one Primary fix with no
setup risk; (3) none else: a variance day.

**Testing 1** — **+$57.88**, 43 trades, 58% win vs 55%, +0.060R; −$42 (12:00) → peak +$129 (14:21) → +$58 (give-back
$71, late shorts). Best RW7-gapdn-bounce-early-short-FD 27 trades +10.4R (+$99) — its record is still flat (329 trades,
−0.004R, −0.039R w/o best day, so no promotion case); worst CWT05-flush-m05-v3-long −2.8R. Shorts +0.090R, longs
−0.050R. Edit: none; RW7-FD stays on watch (record carried by today: watch the next 4 sessions).

**Testing 2** — **+$55.10**, 118 trades, 56% win vs 63%, −0.119R; −$112 (10:49) → peak +$216 (14:08) → +$55 (17 late
flattens gave back $224). Best CWT09-gapdn-bounce-g10-lowerhalf-short +4.0R, CWT09-vwaploss-g10 +2.6R; worst
NM-AR-AM-gapdown-capitulation-long −5.3R (5 trades, 0% win), CWT13-vwapstretch-z05-long 55 trades −7.8R. Longs −16.1R
on 100 lots. CWT13-z05-long: held to the close it would have made +15.6R today (stopped then reversed in the bounce), but
its 2-year verdict is retire (−0.080R, t −5.1) and its record is −0.066R (−0.151R w/o best day) — one-day exit evidence,
not an edit. Edit: CWT13-z05-long's former-Primary 10-session review is due ~11-09; NM-AR capitulation long on watch
(38 trades / 4 sessions −0.405R).

**Graveyard** — **−$703.08**, 361 trades, 56% win vs 64%, −0.143R; peak +$47 (10:01) → −$1,098 (11:10) → −$703.
Longs −56.3R / −$918 (CWT14-failbrk-orl-p05-lowvol-long −19.4R, orl-p05-long −20.4R as the index slid all morning);
shorts +$214 (CWT09-gapdn-bounce-g5-lowerhalf-short +8.2R, +$269). 75 same-symbol stacks (174 lots, −34.1R; extra lots
−14.9R). Edit: none (data collection, rule 20).

**Gen** — **−$2,744.98** (31 trades still unbooked, HK-RECON-GEN), 245 trades, 37% win vs 58%, −0.365R; peak +$323
(10:42) → −$3,579 (14:53) → −$2,745. Worst GEN-261019-04 −10.1R (−$769, leveraged ETFs with 6-7% stops),
GEN-261020-03 30 trades 0% win −34.8R; best GEN-261026-06 NewLOD LATE long +10.2R, GEN-261023-08 +7.1R (late index-bounce
longs). Edits: already queued (nightly-1029-burst20-one-bet, HK-RECON-GEN); nothing new.

## 1. Every trade, all accounts (`trades_bdi.py` → trades_bdi_out.txt, per_trade_1030.csv; patterns.csv +390 losers)
782 trades, all with SIP 1-minute paths; 390 losers. Exit what-ifs (sum R after costs; live / be05 / trail / hold / sar /
reenter): Primary −2.5 / −2.2 / −3.9 / −5.3 / +0.4 / −2.2; T1 +2.6 / +5.3 / +4.5 / −6.5 / +4.4 / +5.0; T2 −14.0 / −9.3 /
−0.8 / **+6.2** / −15.0 / −8.7; GY −51.5 / −38.3 / −48.5 / −129.8 / −48.2 / **−11.4**; Gen −89.5 / −68.7 / −60.6 / −61.6 /
−63.0 / −81.5. No alternative exit wins in every account (one day: per-trade se 0.03R).
- **Loss types:** wrong-side-after-big-swing is the biggest $ bucket (71 losers, −$2,543, Gen −$1,974); never-worked 103
  (−$1,975); stopped-then-reversed 73 (−$1,054, GY 41 — the orl longs stopped near the low).
- **Opposite side (hindsight check):** longs entered while SPY was ≤ −0.25% from the open: 402 lots, live −0.209R, the
  1R/1R opposite +0.187R; longs without that flag −0.439R live. The flag is known at entry, but on one trend-down day it
  is hindsight; the breadth / SPY gate tokens were tested before (nightly1030: neither separates Gen's winners). No rule.
- **Give-back:** Primary $236 and T2 $161 from the 14:08-14:21 peaks, both from late entries hit by the 14:52 bounce;
  the 15:45 flatten replay (nightly1030, +18.7R today) is the open item for that, not a new one.
- **Stacking:** extra same-symbol lots lost in GY (−14.9R) and Gen (−3.7R), not in T2 (+0.3R); Primary ZETA −1.2R on two
  extra lots. Consistent with earlier nights: no cap item.

## 2. Patterns → rules
1. "Opening movers follow the day" — now a tested negative (MH3); the Move Hunt's next precursor needs a day-direction or
   group signal. Queued as notes on `mh-1029-open-drive-window` and `mh-1029-earnings-sympathy` (group moves at the open,
   cyber-security second day).
2. Volatility ETPs and the afternoon index turn: the nightly's afternoon-reversal premise failed on 2 years; no new item.

## 5. Decisions
None. Nothing passed; no near-miss for Testing (best t −4.34 vs BAR90 2.01).

Reproduce: `fetch5.py` (start 10-01) → `research/ops/coverage1029/fetch.py <scratch>/cov 2026-10-30` →
`frames_today.py` → `moves.py <scratch> 2026-10-30`; `python research/bdi/1030/mh3_open_pdh.py`;
`trades_bdi.py <scratch> 2026-10-30` (needs `<scratch>/bars/<sym>.parquet`); `accounts.py <scratch>`;
`add_backlog.py`; `research/bdi/1028/merge_patterns.py research/bdi/1030/patterns_1030.csv`. Scratch deleted after the run.

Educational only — not financial advice.
