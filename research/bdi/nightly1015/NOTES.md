# Nightly winner/loser autopsy: 2026-10-15 (primary, Testing 1, Testing 2)

*Educational only — not financial advice. These are live **paper** results from one session (rule 7). They are a diagnosis, not evidence. No locked holdout was scored. One small history backtest was run (section "Backtest", **10 configurations**, pre-declared in `bt1015.py`); everything else is a descriptive split of today's trades (about 30 one-session splits, none of them gated).*

Inputs: `journal.db`, `status.json` (every commit since the 10-14 close, via `git log`), `reports/scorecard.json`, `setups/2026-10-15.json` and `intraday/2026-10-15.jsonl` from `origin/mcf-data`, `mcf-data-testing` and `mcf-data-testing2`; the 10-14 EOD `journal.db` of each branch (to find restated rows); `longhold/status.json` from `mcf-data-longhold` (S6, one line). SIP 1-minute bars for the 386 traded symbols plus SPY, QQQ and IWM, and for the 48 restated 10-12/10-14 lots (Alpaca market data only). No trading endpoint was called; broker orders and fills were **not** read. The broker side of every check is what `status.json` records from the broker (equity, positions).

Scripts in this folder (copied from nightly1014 and re-dated, plus new ones):
- `fetch.py`, `build.py` (`trades.csv`, 806 real trades; the restart split is replaced by `after_handover` = entered after the planned 15:02 job handover — none were), `summ.py` (`summ_out.txt`), `attr.py` (`attr_out.txt`, now also prints the SPY/QQQ/IWM open path), `qtycheck.py`, `statusscan.py`, `gapcurve.py`, `brokermtm.py`, `sc3.py` (`sc3_out.txt`).
- New: `restated.py` (`restated_lots.csv`: the rows the #58 paging fix booked, checked against the bars), `qty1012.py` (10-12 broker-vs-journal quantities on the restated journal), `gapstep.py` (per-symbol decomposition of a gap step between two snapshots), `autopsy.py` (`autopsy_out.txt`: MFE/MAE, give-back, time to MFE, clusters, latency), `bt1015.py` (backtest), `add_backlog.py`.

**Market: a gap-down reversal day.** SPY opened −0.44% below the 10-14 close (766.24 vs 769.62), QQQ −1.41%, IWM flat (+0.01%). All three then closed strongly up from the open: **SPY +0.72%, QQQ +1.32%, IWM +1.34%** (highs 15:22 / 15:46 / 15:42). Large and small caps rose together.

**The open path (for the index dip-bounce setups that start in Testing 1 on 10-16).**
- SPY: a small pop to **+0.16% at 09:42**, flat to 09:51, then a fast drop **09:52–09:54** (−0.21% by 09:54), a retest and the **low at 09:57: 764.43, −0.24% from the open** (−0.67% vs the prior close). Half the drop back by 09:59, **back above the open at 10:01**, +0.14% at 10:30, +0.45% at 11:00.
- QQQ: high +0.36% (09:45), drop from 09:52, low **09:57 at −0.43%** from the open (−1.84% vs prior close), above the open at 10:01, +0.16% at 10:30, +0.70% at 11:00.
- IWM: high +0.25% (09:41), low **09:54 at −0.21%**, above the open at 09:58 (led the turn by 3 minutes), +0.43% at 10:30, +0.98% at 11:00.
- So the owner's "bounce ~09:55" is right: the trough was 09:54 (IWM) / 09:57 (SPY, QQQ), a 0.4–0.8% swing down inside 6 minutes, and a V-shaped recovery that never retested.

## Failures first

### 1. All three accounts lost, and all three halted or nearly so; the short books were run over
| account | equity 09:29 (pre-open) | equity 15:55 (closed) | broker day P/L | journal day P/L | gap (broker − journal) | orders still `submitted` |
|---|---|---|---|---|---|---|
| Primary | 95,771.26 | 94,909.43 | **−861.83** | −861.83 | **0.00** | 0 (all days) |
| Testing 1 | 99,387.69 | 97,714.67 | **−1,673.02** | −1,673.02 | **0.00** | 0 (all days) |
| Testing 2 | 98,044.38 | 96,768.04 | **−1,276.34** | −1,097.71 | **−178.63** | 0 (all days) |
| S6 long-hold (separate, not ranked) | 96,997.94 (`last_equity`) | 96,030.72 (16:03 snapshot) | **−967.22 (−1.00%)** | — | — | — |

- Primary hit its daily loss limit (halt logged 14:30; its last entry was 11:20). Testing 1 hit its daily loss limit at **11:10** and skipped **876 later signals as "halted"**. Testing 2 did not halt (last entry 12:45, end of its windows).
- **Shorts against longs:** Primary shorts −$883.52 (47) vs longs +$21.69 (1); T1 shorts −$1,767.66 (207, 18% wins) vs longs +$94.64 (18, 67%); T2 shorts −$1,276.76 (175, 33%) vs longs +$179.05 (358, 70%). 10-13 and 10-14 were down/split days that favoured the shorts; today the index reversed up from 09:57 and stayed up.
- Overnight equity moves (not trading): Primary −0.44, T1 −5.92, T2 −6.50 between the 10-14 close and the 10-15 pre-open snapshot.
- S6: the official-close mark row for 10-15 is not in `longhold/marks.csv` yet (last row 10-14 = 96,997.94, which now equals the broker's `last_equity`: the H-5 fix holds). The day line above is the 16:03 intraday snapshot.

### 2. Clean close: yes, all three
`positions: []`, no open orders, `health.flatten_failed: []`, phase `closed` at 15:55, EOD report (csv/html/png) and `reports/scorecard.json` committed at 15:56–15:57 ET on all three branches (window 10-12..10-15). Primary and Testing 1 broker-vs-journal match to the cent. The planned 15:02 job handover (phase `handover`, "job 09:22 done" → "job 15:02/15:03 done") lost nothing: no gap in polls, no entries were due after 15:02.

### 3. #58 order-paging fix: the restatement worked
The first reconcile of today's job booked every old `submitted` order, **dated by its entry fill** (`date` and `exit_time` on the original day; `restated.py`). 0 orders are left `submitted` in any account, for any day.

| account | day | rows restated | P/L restated | day total before → after | broker day | gap after |
|---|---|---|---|---|---|---|
| Testing 1 | 10-12 | 15 (all "flatten") | −8.42 | +40.79 → **+32.37** (204 trades) | +18.96 | −13.41 |
| Testing 1 | 10-14 | 9 (the 10-14 H-1 lots) | **−6.06** | +71.27 → **+65.21** (326 trades) | +65.21 | **0.00** |
| Testing 2 | 10-12 | 24 (all "flatten") | −69.27 | −652.05 → **−721.32** (360 trades) | −663.27 | **+58.05** |
| Primary | — | 0 | — | — | — | — |

- **T1 10-14 now matches the broker exactly** (the −6.06 gap was the 9 unbooked lots; the 10-14 re-pricing estimate was −0.30 because it used the bar open, the booked fills are −6.06).
- All 48 restated lots were checked on the bars: quantities and P/L are consistent with the broker holding them to the 15:55 flatten (`qty1012.py`: on the restated journal, T2 10-12 has **0** persistent broker-vs-journal quantity mismatches over 151 snapshots; T1 10-12 one, GAP −22 shares 13:10–13:35, not a restated lot). 5 of them (T1 AMAT, DOC; T2 BEN, HSIC, EQX) touched their target on the bars before the flatten and were still held by the broker (the legs were not working for those ghosts on 10-12; at the target price they would have made +$23 more).
- **New residuals, not explained:** T2 10-12 journal is now **$58.05 below** the broker (before the restatement it was $11.22 above); T1 10-12 −13.41 and T1 10-13 −25.24 remain. Housekeeping H-2.

### 4. Testing 2: the −$374.72 of 10-14 is still there, and a −$178.63 gap appeared today
- 10-14: no 10-14 rows were restated in Testing 2 (it had no `submitted` orders that day), so the 10-14 journal is still −785.74 against a broker −1,160.46. Not explained; the restatement did not touch it.
- **Today −$178.63, same signature.** `gapcurve.py` and `brokermtm.py`: the gap is ~0 until 11:49, then **−78 between the 11:49:?? and 11:53 snapshots (15:50:32 → 15:54:16 UTC)** and **−86 between 14:10 and 14:12 (18:11:15 → 18:13:28 UTC)**, plus noise. `gapstep.py` for 11:49→11:53: broker equity −$121.09, while the journal changed −$42.66 and the broker's own held positions marked to SIP changed −$40.79; no symbol's position or journal disagrees by more than $0.30. So ~$80 left through orders that were in and out between two snapshots and appear in neither the positions nor the journal (as on 10-14). Primary and T1 show no such step. Broker quantity mismatches in T2 today (SYNA 9 vs 14, XRT 1 vs 10 for hours) are partial target fills that the journal books at the flatten as a blended "target" exit; they carry no P/L difference.
- Cumulative T2: broker −3,231.96 since 10-12 vs journal −2,708.04 (−523.92).
- **Needs the Testing 2 FILL activities for 15:50:32–15:54:16 UTC and 18:11:15–18:13:28 UTC on 10-15 (and 14:18:54–14:22:13 UTC on 10-14)**, read-only with the Testing 2 keys (`research/bdi/nightly1014/h2_fills.py`). Housekeeping H-2.

### 5. Market data and broker equity froze for 74 minutes (12:57–14:10 ET), in all three accounts
- Alpaca SIP 1-minute bars are **missing for all 389 symbols from 12:57 to 14:10** (SPY: 12:56 bar then 14:11). Live, `health.symbols_last_bar` was 0 at every poll in that window while `polls` kept counting, and the broker equity in `status.json` stayed fixed to the cent (Primary 95,145.99, T1 98,054.25, T2 97,183.16) — the paper broker's marks froze too. No entries and no exits were booked in the window; 19 bracket exits (T2 16, T1 3) were booked at 14:11 when data resumed.
- No harm visible today (no entries were due; brackets rest at the broker). But nothing flagged it: a 74-minute data outage looks like a quiet market in the status. Housekeeping H-3.

### 6. Primary: NS2 took 42 shorts in 35 minutes and lost −$788.87
- NS2-sma50break-overbought-short: 42 trades, 19% wins, −0.632R, **−$788.87**; 32 stops, 8 targets. Its previous high was 2 trades a day (10-14). **37 of the 42 were entered 10:45–11:20** as the rally lifted many names through their SMA50 into "overbought": 10 in the 11:05 poll, 9 in 11:00, 7 in 10:45 (31 of 42 in same-setup clusters of ≥ 5). 16 never worked (MFE < 0.2R, −$540.05); winners kept their peak (give-back 0.07R).
- RW6G1 (first trading day) 3 trades, all stops, −$98.28; all first signals (no refire), 2 never worked.
- The scorecard now flags **NS2 "below backtest – review": 52 trades, 27% wins, −0.500R, −$825.79 vs +0.021R expected.** This is the owner's call (rule 20 does not apply to Primary; demotion goes back to Testing 1).

### 7. Testing 1: −$1,673, every short family lost
- Worst: heat_fade_short-FD −$399.07 (44, 11% wins, MAE of losers 1.08R, 9 stops worse than −1.1R), NS2-FD −$343.26 (31), RW6-FD −$295.36 (23, 9% wins), RW2-FD −$212.23 (60), L3-fromopen-FD −$174.57 (12 of 12 lost), heat_fade_short (ex-primary) −$160.40 (17 of 17 lost, avg −1.32R).
- The 09:50 poll: 19 shorts (heat_fade_short and -FD, 9 each) into the 09:52–09:57 drop, **0 wins, −$136.11**: entered at 09:50 on the move down, stopped on the 10:01 reversal.
- 81 losers never worked (−$1,074.44); 39 losers had reached ≥ 0.5R first. Stops averaged −1.102R (−$69.87 beyond −1R).
- Stacking hurt: lot 1 −0.515R, lot 2 −1.001R (55), lot 3 −0.779R. Ex-primary setups 19 trades, −$148.56.
- Positive: LIQ-orl +$77.18 (12, 67%, 11 flattens), the long-beta setup that lost on 10-14 — it behaves as its config note says.

### 8. Testing 2: −$1,098 journal (−$1,276 broker), carried by CWT09 shorts
- CWT09-gapdn-bounce-g5-lowerhalf-short **−$683.07** (32, 9% wins): **21 entries in the 10:30 poll, 1 win, −$537.62** (gap-down names bouncing with the index), 23 never worked. CWT09-gapdn-vwaploss-g5-short −$168.99 (22, 14%). The 10:30 poll: 60 trades, 25% wins, −$740.39.
- The CWT14 PDL longs, the worst setups of 10-14, made money on the up day (pdl-p05-long +$94.38, 84% wins). CWT12-coil-k4 +$48.66.
- 26 broker rejects (take-profit/stop already through the base price), as on 10-13/10-14.

## Headline per account (real trades, run 1)
| account | trades | win% | avg R | P/L (journal) | broker | cost-adj | stop / target / flatten | intraday (marked, 5-min) |
|---|---|---|---|---|---|---|---|---|
| Primary (10 setups) | 48 | 21% | −0.563 | **−$861.83** | −$861.83 | −$926.53 | 36 / 10 / 2 | peak +$14 at 09:55; min −$874 at 15:45 |
| Testing 1 (40) | 225 | 22% | −0.641 | **−$1,673.02** | −$1,673.02 | −$1,774.36 | 170 / 40 / 15 | never green; min −$1,667 at 15:55 |
| Testing 2 (30) | 533 | 58% | −0.143 | **−$1,097.71** | **−$1,276.34** | −$1,192.63 | 216 / 308 / 9 | peak +$21 at 10:10; min −$1,103 at 15:55 |
| S6 long-hold (separate) | — | — | — | — | **−$967.22 (−1.00%)**, equity 96,030.72 (16:03) | — | — | — |

Entry latency, decision (poll start) → fill, median / p90: Primary 31 / 55 s, T1 94 / 147 s, T2 105 / 186 s (bar close → fill: 50 / 74, 119 / 173, 133 / 231 s). T1 and T2 are slower than on 10-14 (49 and 88 s): T1 evaluated 1,702 signals today. Losers did not pay more slippage than winners in any account (mean slip_bps: P −2.8 losers / +13.2 winners, T1 −2.5 / +10.4, T2 +5.7 / +8.7).

## Refire (#57) and same-setup re-entry (#54)
- **Primary:** no refire signal (RW6G1's 3 trades were first signals). **Testing 2:** none (no refire setups).
- **Testing 1: 796 refire signals**, 732 of them from **L3-gap-slope-fromopen-FD** (56 L3-rsi5hi-FD, 8 RW6-FD). 5 submitted, 791 skipped (458 halted, 330 not shortable, 2 spread, 1 lot cap). **The 5 refire trades all stopped: −1.096R, −$65.93** (RRGB, CRCL ×2, BULL, USAR — all L3-fromopen).
- **Same-setup re-entries (2nd+ lot of a setup on a symbol): 4, all L3-fromopen, all stopped, −$55.35.**
- Two partial sessions so far: 10-14 refire +$27.97 (8 trades), 10-15 −$65.93 (5). Nothing here is evidence (rules 7, 13). The 732 L3-fromopen refires show that on a rising tape its condition stays true bar after bar.

## NS3 and the snapshot
NS3 was demoted after hours on 10-14 (commit 589ee8f, 02:58 UTC 10-15), so **today was already its first Testing 1 session** (`former_primary: {demoted: 2026-10-14, first_testing_session: 2026-10-15}` in the T1 snapshot), not 10-16. Primary ran 10 setups with NS3 disabled. NS3 and NS3-FD produced **0 signals** in Testing 1 today. (Tonight's config commit 0caed26 promotes RW5-FD, RW3-FD, MF3-FD to Primary and adds 5 index open-dip bounce setups to Testing 1 from 10-16; today RW3-FD 1 trade +$5.20, MF3-FD 2 trades −$1.83, RW5-FD none.)

## Winner/loser autopsy (`autopsy_out.txt`)
| account | never-worked losers (MFE < 0.2R) | losers that reached ≥ 0.5R | winners MFE / MAE (median) | winners give-back (MFE − R) | time to MFE, winners | same-setup clusters ≥ 10 per poll |
|---|---|---|---|---|---|---|
| Primary | 18 of 38, −$619.61 | 9 | 1.09 / 0.50 R | 0.07 R | 69 min | 10 trades, −0.813R (singles −0.236R) |
| Testing 1 | 81 of 176, −$1,074.44 | 39 | 0.91 / 0.30 R | 0.11 R | 65 min | 48 trades, −0.727R (singles −0.640R) |
| Testing 2 | 121 of 224, −$1,559.54 | 43 | 0.50 / 0.22 R | 0.07 R | 12 min | 104 trades, −0.295R (singles −0.198R) |

- The loss was entry direction, not exits: winners kept their peak, and most losers either never worked or were stopped as the index climbed. Losers' median hold: P 22 min, T1 23 min, T2 26 min.
- Same-setup clusters lost most in Primary and T2; in T1 the 2–4 clusters did best (−0.226R). Mixed, one session.

## Intraday attribution (marked: realized plus open lots at the 1-minute close)
- **Primary:** green only 09:55–10:05 (+$14, NS2's first lot); the NS2 burst took it from −$18 at 10:45 to −$176 at 11:00 and **−$808 at 11:15**; low −$874 at 15:45 (NS2 −801.0, RW6G1 −98.3; NS5 +21.7, MF3 +8.8).
- **Testing 1:** never green. At the close: heat_fade_short-FD −399.6, NS2-FD −343.3, RW6-FD −295.4, RW2-FD −213.2 against LIQ-orl +82.4.
- **Testing 2:** peak +$21 at 10:10 (CWT14 PDL longs +64.6, PDH shorts −41.5), then the 10:30 CWT09 burst; at the close CWT09-g5-lowerhalf −679.6, CWT09-vwaploss −169.0, pdh-p10-short −109.8 against pdl-p05-long +91.0, coil-k4 +45.4.

## Scorecard summary, all three accounts (last summary 10-14)
Journal real trades (restated); the verdict uses the fixed bar in `mcf/report/scorecard.py`. Paper results, not evidence.

| account | sessions in scorecard | trades | P/L | by day | verdicts |
|---|---|---|---|---|---|
| Primary | 4 (10-12..10-15) | 99 | **−$775.76** | 10-12 +117.93, 10-13 −95.39, 10-14 +63.53, 10-15 −861.83 | 3 positive (MF4 +71.01, MF5 +35.00, MF3 +23.24), 7 too few, **1 below backtest – review: NS2 (52, −0.500R vs +0.021)** |
| Testing 1 | 4 (10-12..10-15) | 1,126 | **−$2,204.44** | 10-12 +32.37, 10-13 −629.03, 10-14 +65.21, 10-15 −1,673.02 | 10 positive (RW3-FD +117.08, RW5-FD +83.30, MF3-FD +73.43, MF4-FD +61.20), 14 negative (heat_fade_short-FD −492.38, NS2-FD −400.70, RW6-FD −301.08, RW2-FD −286.98), 12 too few, 1 below backtest (heat_fade_short ex-primary, 25, −0.916R vs −0.015) |
| Testing 2 | 4 (10-12..10-15) | 1,893 | **−$2,708.04** (broker −$3,231.96) | 10-12 −721.32, 10-13 −103.27, 10-14 −785.74, 10-15 −1,097.71 | 3 positive (coil-k4 +72.05, pdl-p10-lowvol +26.58, coil-k6 +7.91), 11 negative, **3 below backtest – review: CWT09-g5-lowerhalf-short (40, −0.661R vs +0.047), CWT09-vwaploss-g5-short (28, −0.690 vs −0.031), CWT13-z05-short (41, −0.345 vs −0.069)**, 11 too few |

- The 10-14 "below backtest" flags CWT14-pdl-p05-long and CWT12-coil-k6-long dropped off after today's up day; three short setups replaced them. Removal from Testing needs the owner prompt (rule 20); nothing is removed here.

## Backtest (two-year open history; 10 configurations; 0 pass)
Pre-declared in the docstring of `bt1015.py` before scoring. Frames via `research/history2y` (21 open months; the locked block 2024-11-01..2025-02-28 is refused by the loader, `MCF_HIST_ALLOW_LOCKED` never set), with the head/tail rows and outcomes of `research/bdi/refire1014/scan.py` (production R, time-of-day entry costs, structural exits simulated for CWT09). One signal per setup per symbol-day. Bar per configuration: exp > 0, better than baseline in both halves (≤ 2025-12 / 2026) and in up and down sessions, day-clustered t ≥ max(1.5, √(2 ln 10)) = **2.15**. Results: `bt1015_results.csv`. heat_fade_short(-FD) is a "heat" setup, not in the lab frames: not tested.

| setup | baseline n / exp R / t | H1 skip same-setup clusters ≥ 5: exp (Δ) | trades H1 removes: n / exp | H2 gap-down-reclaim veto: exp (Δ) | verdict |
|---|---|---|---|---|---|
| NS2 (Primary) | 3,124 / +0.004 / 0.07 | −0.066 (−0.070) | 1,247 / **+0.110** | −0.071 (−0.075) | both fail |
| NS2-FD | 8,151 / −0.055 / −1.82 | −0.082 (−0.027) | 2,259 / +0.016 | −0.077 (−0.022) | both fail |
| RW6-FD | 3,614 / −0.021 / −0.53 | −0.071 (−0.050) | 836 / **+0.145** | −0.076 (−0.054) | both fail |
| RW2-FD | 22,187 / −0.059 / −3.47 | −0.062 (−0.003) | 9,281 / −0.055 | −0.062 (−0.002) | both fail |
| CWT09-g5-lowerhalf | 5,222 / −0.189 / −1.51 | −0.315 (−0.127) | 2,725 / −0.072 | −0.194 (−0.005) | both fail |

- **H1 is refuted, and the opposite holds:** in the NS2 lineage the clustered first-signals are the *better* half (NS2 +0.110R, RW6-FD +0.145R removed). Today's NS2 burst was a bad day for a basket that is usually its best part. 40% (NS2) to 52% (CWT09) of first signals come in clusters of ≥ 5.
- **H2 fails:** on gap-down days whose index reclaims its open, these shorts historically did *better* than average (the veto lowers exp in all 5 setups, and up-session exp in all 5). A gap-down reclaim is not a reliable reversal-day marker for these setups; today is one outcome.
- Baselines: NS2 (Primary) is flat on history (+0.004R, t 0.07; up sessions −0.06, down +0.16), the -FD versions and CWT09-g5 are negative after costs. The CWT09-g5 scorecard expectation (+0.047R) does not match this history scan (−0.189R); the difference is the scan's structural exit model and should be checked before its rule-20 review.
- Both entries are recorded as `failed` with 5 configurations each (rule 3).

## Hypotheses added to `research/backlog.jsonl` (source "nightly-2026-10-15")
| id | category | status | from |
|---|---|---|---|
| `nightly-1015-short-breadth-cluster-skip` | filter | **failed** (5 configs) | Primary NS2 42 shorts, 31 in clusters ≥ 5, −$788.87; T2 CWT09-g5 21 shorts in one poll, −$537.62 |
| `nightly-1015-gapdn-reclaim-short-veto` | filter | **failed** (5 configs) | shorts lost −$3,927.94 across the 3 accounts (SPY gap −0.44%, reclaimed 10:01) |
| `nightly-1015-l3-fromopen-refire-cap` | risk (parent ledger 2026-10-14-refire-option-b) | idea | 732 L3-fromopen refire signals; 5 refires + 4 re-entries all stopped, −$121.28 |

`add_backlog.py` writes them; `python -m mcf.research.backlog report` regenerated `research/BACKLOG.md`. Nothing went into config/ or mcf/.

## Housekeeping for the lead (not backlog)
- **H-1 (done, verified).** The #58 paging fix restated 48 lots (T1 10-12 15 / −8.42, T1 10-14 9 / −6.06, T2 10-12 24 / −69.27); 0 orders `submitted`; T1 10-14 now equals the broker. Re-run nothing.
- **H-2 (T2 money gaps, unexplained).** 10-14 −374.72 (unchanged), 10-15 **−178.63** (steps at 15:50:32–15:54:16 and 18:11:15–18:13:28 UTC), 10-12 now **+58.05** (journal below broker after the restatement). Also T1 10-12 −13.41 and 10-13 −25.24. Pull the T2 (and T1) FILL activities for those windows (read-only, `h2_fills.py`) and match them to `mt2-`/`mct-` orders.
- **H-3 (new: silent data outage).** SIP bars absent 12:57–14:10 ET for every symbol; `health.symbols_last_bar` 0 for ~70 polls and broker equity frozen in all three accounts, with no alert. Add a status/health flag (e.g. `symbols_last_bar == 0` for ≥ 3 polls during market hours) and show it in the EOD report.
- **H-4.** T2 sibling partial target fills are held by the journal as open lots until the flatten and then booked as a blended "target" (SYNA, XRT today; quantity mismatch for 4–5 hours). P/L is right, but the open-lot count and lot cap see a lot that is mostly closed.
- **H-5 (S6).** The 10-15 official-close mark is not in `marks.csv` yet at the time of this note; check that the evening job writes it (16:03 snapshot −$967.22).

## Housekeeping follow-up (lead, 2026-10-15)
- **H-3 shipped.** The runner flags `health.data_stale` {since, last_bar, fresh, of, polls, stale_min} when fewer than 5% of the watched symbols have a bar in the last 5 minutes (from 09:35 to the flatten), prints `DATA STALE`, sends one email alert per outage (SMTP secrets, best effort) and skips the signal scan while stale (no entries on old bars; brackets and trade management unchanged). Recovered outages go to `health.data_outages`, the daily review lists them, and the dashboard's Data health tile shows STALE. On 10-15 it would have fired at ~13:02 ET and cleared at 14:11.
- **H-4 root cause.** Not a release bug: the SYNA (p05 lot, target 5 of 7 filled) and XRT (target 9 of 10) lots held real residual shares (broker 9 = 7 + 2, 1 = 1) with their target legs still working for the rest until the flatten. They stay open lots (lot-cap semantics unchanged; counting residuals differently would be a risk-rule change for the backlog). Shipped: `health.partial_lots` shows residual lots, and reconcile now closes a lot as soon as its own fills cover its quantity even when an OCO sibling leg still reports an open state.
- **H-2 cash steps vs H-3/H-4 (document only).** 18:11:15-18:13:28 UTC = 14:11-14:13 ET, the first two minutes after the outage (12:57-14:10 ET = 16:57-18:10 UTC), when 16 T2 bracket exits were booked and the broker's marks, frozen for 74 minutes, moved again. The step is likely the outage catching up (stop fills through the gap, and/or entries filled and exited inside one snapshot gap) rather than a new mechanism; it still needs the FILL activities to be confirmed. 15:50:32-15:54:16 UTC = 11:50-11:54 ET is outside the outage and does not line up with the partial fills (SYNA mismatch from before 11:00, XRT from 11:33, both with no P/L difference); it remains unexplained pending the FILL activities (`h2_fills.py`).
