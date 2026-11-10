# BDI Saturday deep run 2026-11-07 (week 11-02..11-06)

*Educational only — not financial advice. Live numbers are **paper** trades (rule 7), costs in (journal `pnl_adj`,
R = pnl_adj / $ risk). History numbers are **backtests** on the open two-year history with production costs. The locked
block 2024-11-01..2025-02-28 was never read (`MCF_HIST_ALLOW_LOCKED` never set; every script asserts it). No holdout was
scored. No config, setup, exit or assignment was changed. `PLAN.md` was committed (2a760d0ea) before anything was scored.
Not duplicated: ROTA1 (FAILED, N 975, branch claude/rota1-1107) and the Primary re-evaluation (wt-preval).*

**Configurations tried tonight: 21** (A burst / give-back 7, B MF after-flush 6, C FB1 flush-chase 4, E range-tape extremes 4;
D GATE1 not reworked, as pre-declared). **0 pass. No give-back proposal passes, so none is made. No new owner decision.**

## Failures first
1. **No give-back remedy holds on two years.** The best one, A7 (QDAY flush gate + an open −3R latch on top of the live
   realised −2R latch), is +224.9R live (t 2.34; 48 setups better +288R / 14 worse −63R; Primary +23.8R, 7 better / 1 worse
   −0.6R) and cuts the Primary-setup give-back on VALID (mean 18.1 → 16.0R/day, p90 43.2 → 35.3R) — but VALID excess t is
   −0.74 (it wins by trading less of a losing book; the gain is CWT +4,709R) and it harms GEN (−172R, 11 / 19). Fails.
2. **The MF2 / MF4 setup-level "don't sell after the flush" rework fails.** Both parents are negative on two years
   (MF2-FD −0.088R t −2.08; MF4-FD −0.085R t −4.84). No QQQ threshold rescues them (−0.080..−0.096R; regime-up −0.20..−0.24R).
   Live the filter would have saved +10..+22R (MF2) / +11..+13R (MF4), the live record only. Consistent with DM-MF2 / DM-MF4.
3. **The FB1 flush-chase guard does not work even in non-down tapes.** Guarded shorts are slightly *better* than their setup
   mean (+0.005..+0.014R); removing them helps on SPY-up days and hurts on down / quiet days; 13-16 families harmed.
4. **QDAY range-tape extremes fail (new idea, E).** Long entries at the low / short entries at the high while SPY is flat
   lose −0.08..−0.10R; up-regime longs +0.05R, down-regime −0.22R. A flat tape at entry does not make the extremes revert.
5. **Give-back this week was mostly correlated stops of open shorts, not entries after the peak** (Primary: open winners
   −$1,675, entries after the peak −$1,232, twins −$123). This is the burst problem again; no rule fixes it on two years.

## Today's win
The week's QDAY read is clear and useful: on **quiet SPY days** T1 (+10.0R), T2 (+3.1R) and Graveyard (−7.4R ≈ flat) did
fine; the week's losses came from **down** (T2 −118R, GY −144R) and **up** (Gen −174R) days. And two cheap safety nets
proved their worth on live: the Graveyard −2R latch blocked −444R, Gen's account halt −79R net.

## 1. Discover workflow (weekly)
- **Finished: run 42383860037** (schedule, 2026-11-07 14:55-15:31 UTC, **success in ~36 min**, vs 62 last week): Mine 30.5 min,
  refresh bars 1.6 min (vs 24; incremental), backlog re-test 2.8 min, publish; mcf-data commit 3d9bb8964 "discovery + backlog 2026-11-07".
- **Bar cache refreshed to 2026-11-06** (lab-cache sample 2026-06-15..11-06). **Backlog re-tested: 66 lab entries**
  (`mcf-data/backlog/backlog_results.jsonl`, history +66 rows). 42 of 66 positive in-sample (last week 42), 21 positive
  forward (22). Top: RW3 base `bdi-rw-gapdn-rsi5pop-flowsell` +0.230R (n 405, t 4.79; forward 93 +0.278R), NS1 +0.165R
  (t 2.97; forward −0.044R), L3 rsi5hi +0.184R (t 2.96; forward 71 −0.199R), RW5 base +0.206R (t 2.94; forward 62 +0.317R),
  ST7-FD +0.167R (t 2.82; forward 78 +0.146R). One 4.7-month regime, not the two-year gates.
- Discovery: 2,294 combinations, 58 sessions, **39 replicated** (45 last week). Top rows again gap-down > 2% shorts (the
  live L3 / RW family) and the "RSI14 < 35 + new high of day" short artefact. One new long lead: gap-up > 2% name at a new
  low of day 11:00-13:30 (test n 559, +0.064R) → backlog `sat1107-gapup-midday-lod-long` (idea).

## 2. Rule-18 rework round (PLAN.md; all rows, failures included)
### A. Burst / give-back near-misses (`sim_a.py`, `score_a.py` → `a_out.txt`, `a_decision.csv`, `a_giveback.csv`; BURST lineage 36, bar 2.68)
| config | TRAIN Δ (excess t) | VALID Δ (t / excess t) | VALID up / down / quiet | live all Δ (t) | live up / down / quiet | live setups +/− (R) | Primary Δ (11-05 / 11-06) | fam harmed |
|---|---|---|---|---|---|---|---|---|
| A1 flush 2 / −0.30% | +2,568 (0.39) | +944 (2.15 / −0.58) | +595 / −150 / +499 | +185.7 (2.47) | +58 / +63 / +65 | 35 (+253) / 9 (−67) | +57.8 (+18.9 / +27.6) | GEN |
| A2 flush 2 / −0.50% | +1,360 (0.32) | +283 (0.93 / −0.96) | +154 / −68 / +197 | +113.0 (2.20) | +31 / +49 / +33 | 24 / 7 | +32.5 (+18.9 / +11.6) | GEN, MF, exh |
| A3 flush 3 / −0.40% | +2,300 (0.64) | +630 (1.81 / −0.39) | +280 / −33 / +384 | +144.1 (2.19) | +37 / +56 / +51 | 24 / 7 | +32.9 (+16.7 / +10.8) | GEN, MF |
| A4 QDAY flush 2 / −0.40% | +1,985 (1.00) | +163 (0.89 / −1.13) | +223 / −175 / +115 | +89.6 (1.72) | +38 / −4 / +56 | 22 / 5 | +19.2 (0 / +11.6) | GEN, MF |
| A5 QDAY flush 2 / −0.30% | +2,301 (1.02) | +344 (1.23 / −0.95) | +422 / −277 / +199 | +117.5 (1.79) | +58 / −3 / +62 | 26 / 7 | +37.9 (0 / +27.6) | GEN, MF |
| A6 realised −2 + open −3 latch | +8,066 (1.31) | +4,922 (6.08 / −0.43) | +707 / +2,183 / +2,031 | +141.2 (1.93) | +10 / +98 / +34 | 35 / 12 | +5.6 (0 / −0.6) | — |
| A7 A4 + A6 | +8,358 (1.39) | +4,933 (6.05 / −0.74) | +795 / +2,037 / +2,101 | +224.9 (2.34) | +42 / +94 / +88 | 48 (+288) / 14 (−63) | +23.8 (0 / +11.0) | GEN |
Give-back (peak − close of the realised-R curve; `a_giveback.csv`): VALID Primary-setup book 30.6R/day base → A1 29.3; the
latch rows start from the live latch (18.1R) → A6 16.2, A7 16.0 (p90 43.2 → 35.3); live Primary 8.1 → A1 6.4, A7 6.0 (from 7.0).
Swing days (peak ≥ 3R, close ≤ 0) barely move (47 → 47-49 VALID). Remedies reading: the flush gates are targeted (block
1-3.4% of trades) and help every Primary setup they touch live (MF2-FD +29.2R, MF4-FD +15.8R, heat_fade_short +7.9R for A1),
but on two years they remove trades that were *better* than their setup average (excess < 0) and the MF family itself loses.
### B. MF after-flush (`b_mf.py` → `b_out.txt`; lineage 6, BAR90 1.70) — see Failures 2. All 6 rows fail every gate.
### C. FB1 flush-chase rework (`c_e.py` → `ce_out.txt`, `c_results.csv`; lineage 8, bar 2.04)
| config | blocked (share) | blocked excess | train Δ (t) | valid Δ (t) | SPY up / down / quiet | fam helped / harmed | pass |
|---|---|---|---|---|---|---|---|
| C1 ≤0.15 ATR & SPY ≥ −0.25% | 44,875 (9.6%) | +0.009 | +66 (0.19) | −488 (−1.12) | +2,382 / −2,132 / −672 | 10 / 14 | no |
| C2 ≤0.10 | 29,280 (6.2%) | +0.007 | +12 (0.05) | −214 (−0.72) | +1,415 / −1,239 / −379 | 9 / 14 | no |
| C3 ≤0.25 | 85,142 (18.1%) | +0.005 | +41 (0.07) | −485 (−0.59) | +5,323 / −4,457 / −1,310 | 11 / 13 | no |
| C4 C1 + QQQ at its low | 14,985 (3.2%) | +0.014 | −237 (−1.04) | +32 (0.13) | +759 / −965 / +1 | 5 / 16 | no |
### D. GATE1 checkpoint gate — not reworked (pre-declared: lineage 112, bar 3.07 vs best VALID t 2.26; forward shadow logs).
### E. New: range-tape extremes (`c_e.py`, `e_results.csv`; lineage 4, Testing bar 1.50)
| config | n (per session) | avg R | t | regime up / flat / down | SPY up / down / quiet | WF | baseline | pass |
|---|---|---|---|---|---|---|---|---|
| E1a long ≤0.15 ATR of low | 47,416 (106) | −0.097 | −9.27 | +0.051 / −0.070 / −0.215 | +0.042 / −0.286 / −0.085 | 0% | −0.096 | no |
| E1b long ≤0.25 | 84,106 (189) | −0.098 | −9.79 | +0.050 / −0.077 / −0.220 | +0.036 / −0.273 / −0.089 | 0% | −0.096 | no |
| E2a short ≤0.15 ATR of high | 37,106 (83) | −0.091 | −6.31 | −0.291 / −0.064 / +0.099 | −0.308 / +0.099 / −0.045 | 17% | −0.076 | no |
| E2b short ≤0.25 | 52,857 (119) | −0.084 | −6.48 | −0.280 / −0.062 / +0.097 | −0.291 / +0.097 / −0.045 | 6% | −0.076 | no |

## 3. New setup ideas (Move Hunt, long side)
Tested: E (above, fails). Queued (0 configs): `sat1107-gapup-midday-lod-long` (discovery replicated long),
`sat1107-index-first-open-two-sided` (carried from sat1031). Learned again: stock-level state (flush, extreme, gap) says a
move is likely, not which way; the side has to come from the index / tape, or the setup has to be two-sided.

## 4. Week scorecard 11-02..11-06 (paper, costs in; `week.py` → `week_out.txt`, `week_scorecard.csv`, `week_by_setup.csv`)
SPY: 11-02 down (−0.78%), 11-03 quiet, 11-04 up (+0.73%), 11-05 down (−4.56%), 11-06 quiet.
| account | R | trades | avg R | win vs BE | Alpaca $ | green days (R) | w/o best day | R up / down / quiet days | prev week R |
|---|---|---|---|---|---|---|---|---|---|
| Primary | **−25.2** | 222 | −0.114 | 47% vs 53% | **−$2,038.76 without MTUM / −$13,680.99 with** | 2 / 5 | −36.6 | −10.7 / −1.6 / −12.8 | −5.2 |
| Testing 1 | −5.1 | 289 | −0.018 | 52% vs 53% | −$176.39 | 3 / 5 | −11.5 | −4.3 / −10.8 / **+10.0** | −82.9 |
| Testing 2 | −147.6 | 794 | −0.186 | 51% vs 64% | −$1,771.40 | 1 / 5 | −152.7 | −32.2 / −118.5 / +3.1 | −115.9 |
| Graveyard | −211.5 | 2,291 | −0.092 | 56% vs 61% | −$1,472.00 | 1 / 5 | −233.2 | −59.9 / −144.2 / −7.4 | −203.6 |
| Gen | −311.3 | 1,467 | −0.212 | 42% vs 53% | −$4,046.17 | 0 / 5 | −298.4 | −174.0 / −98.3 / −39.0 | −205.3 |
| Explore 1 (2 sessions) | −12.9 | 60 | −0.215 | 42% vs 53% | +$106.04 | 1 / 2 | −15.3 | — / −15.3 / +2.4 | — |
| Live Lab (2 sessions) | −2.6 | 38 | −0.069 | 50% vs 55% | +$94.70 | 0 / 2 | −1.4 | — / −1.4 / −1.2 | — |
Primary Alpaca by day: −615.37 / +142.76 / −145.76 / −363.32 (11-05 trading only; −11,824.02 with the MTUM booking) /
−1,238.60 with MTUM (−1,057.07 without). R and $ diverge on 11-05 (+4.5R, −$419 journal): lot sizes differ across setups.
- **Primary** best: Gap-Down RSI-Pop Flow-Sell Short (all day) `RW3-gapdn-rsi5pop-flowsell-short-FD` 31 tr +16.1R (record 83 tr
  +0.469R, w/o best day +0.252R), `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD` 26 tr +13.1R (record +0.371, w/o best +0.238),
  `ST7-rsi50dn-long-pm-t1s1-FD` 12 tr +4.1R (record 21 tr +0.133, **w/o best −0.029, `1 day` 112%**). Worst: `MF2-open-rsimidhi-flowsell-FD`
  62 tr −27.4R (record +0.065, **w/o best −0.290, `1 day` 443%**), `MF4-h40-open-flowsell-FD` 51 tr −20.2R (record −0.258),
  `L3-gap-slope-rsi5hi-FD` 13 tr −7.8R. Shorts −25.5R, longs +0.3R.
- **Testing 1** best `RW7-gapdn-bounce-early-short-FD` 107 tr +28.2R (record 436 tr +0.061, w/o best +0.032, `1 day` 53%); worst
  `CWT05-flush-m05-v3-long` −10.3R, `intraday_momentum` −9.6R, `NS1-rsidip-rsi5pop-long-FD` −5.2R. Longs −29.0R, shorts +23.9R.
- **Testing 2** best `RW1-gapdn-bounce-flowsell-short-FD` 26 tr +8.4R (w/o best +0.211); worst `RW3S-gapdn-flowsell-short-FD` 140 tr
  −40.6R (verdict fails), `CWT14-failbrk-pdl-p10-long` −38.6R, `CWT13-vwapstretch-z05-long` −32.1R. Longs −118.3R.
- **Graveyard** best `CWT09-gapdn-vwaploss-g5-short` +37.5R (`1 day` 131%), `heat_fade_short-FD` +36.2R; worst CWT14 ORL longs −57.6 / −46.3 / −35.4R.
- **Gen** best `GEN-261022-07-…-short` +20.1R (`1 day` 144%); worst `GEN-261019-05-…-long` 52 tr −52.1R, `GEN-261021-06-…-long` −50.7R. 11-04 alone −174R.
- **Explore 1 / Live Lab** (low-rep homes, ROLL1 from 11-05, no verdicts): NM-RWN3 +6.1R (6 tr), NM-RWR3 +3.4R (3 tr); CWT13-z075-long −10.7R (23 tr, all 11-05).
- **Rule changes in the window** (`research/ledger.jsonl` effective dates): 11-02 PDL-1a R2A legs into T2, DM-NS3 Graveyard moves;
  11-03 DM-MF moves (MF3-FD / MF5-FD → GY), SO-1A, RW3S added to T2; 11-04 DM-N3 moves, **UNI1** (T2 top-500 pool); 11-05 **ROLL1**
  (Explore 1 / Live Lab). Standing: Primary ~$4k lot (10-28), Primary −2R latch (10-29), Testing CF (10-30), −20R account halt.
  T2's −147.6R straddles UNI1 (11-04): 11-02..11-03 −28.0R vs 11-04..11-06 −119.6R (11-05 −85.4R on a −4.6% SPY day).

## 5. Weekly give-back review (`giveback_week.py` → `giveback_week_out.txt` / `.csv`; nightly peak attribution)
Marked peak → close ($, costs in):
| account | 11-02 | 11-03 | 11-04 | 11-05 | 11-06 | week give-back |
|---|---|---|---|---|---|---|
| Primary | +67 (12:07) → −627 | +207 (15:39) → +136 | **+463 (12:17) → −209** | **+153 (11:06) → −419** | **+435 (10:36) → −1,091** | $3,534 |
| Testing 1 | +12 → −185 | +70 → +13 | +7 → −37 | +285 (13:08) → +48 | +61 → +13 | $583 |
| Testing 2 | +95 → −389 | +41 → +41 | +12 → −518 | +13 → −996 | +165 (11:14) → +47 | $2,141 |
| Graveyard | +67 → −1,627 | +44 → −308 | +49 → −772 | +323 → +323 | +2,153 (11:34) → +397 | $4,622 |
| Gen | **+153 → −1,724** | +10 → −586 | 0 → −2,455 | **+378 → −1,100** | **+510 → −273** | $7,186 |
| Explore 1 | — | — | — | +88 → +50 | +228 (10:36) → +48 | $217 |
| Live Lab | — | — | — | +152 → +152 | +64 → −61 | $125 |
What gave it back (week sums, $): **Primary** open winners stopped −$1,675 (11-05 MF4-FD −$805, 11-06 MF2-FD −$435), entries
after the peak −$1,232 (11-05 MF4-FD −$612, 11-06 MF2-FD −$371, 11-02/11-04 L3-rsi5hi-FD −$217/−$199), open losers −$627, twins
−$123, late flatten +$195. **T2** entries after the peak −$1,704 (11-05 RW3S −$542), late flatten −$598, twins −$394. **Graveyard**
open winners −$2,097 (11-06 longs through the 12:00 QQQ slide), after-peak −$1,617, twins −$1,230. **Gen** after-peak −$5,155.
Timing: Primary peaked 10:36-12:17 on its three swing days, each followed by an index reversal against a one-direction short
stack. "Up a lot, then a loss" (peak ≥ +$100, close < 0): Primary 11-04, 11-05, 11-06; Gen 11-02, 11-05, 11-06.

Did the live caps help (blocked signals priced by the journal what-if run, net of costs; `week_out.txt`, `week_caps.csv`)?
- **Twin-exposure cap: yes, every account where it fired** — blocked twins −25.2R: Primary −9.7R (MF4 base), T1 −4.0R, T2 −2.7R, GY −8.8R.
- **Per-setup −2R latch: yes.** Primary blocked 130 signals worth −12.2R (11-02 −17.6R, mostly L3-fromopen-FD; it cost +6.2R on
  11-03 and +3.3R on 11-05); Graveyard 2,945 signals worth **−444.4R** (11-05 −320.7R). Off in T1 / T2 / Gen.
  It did not stop the bursts (MF2 latched 10:46 / MF4 10:52 on 11-06, after their last entries).
- **−20R account halt (Primary 11-06 10:55): slightly costly that day** — 91 blocked signals would have made +3.9R after costs
  (MF2 −2.9R, the rest positive). Gen's halt blocked −78.9R net (11-04 −123.2R, 11-05 +44.3R).

**Give-back proposals: none this week.** Both best candidates (A7 and A1) cut give-back live and on VALID without touching
exits or winners, but neither clears the two-year excess test (Remedies rule: they help every Primary setup they touch live,
but on two years the MF family and GEN get worse). Kept as forward shadows (`burst2-flush-gate-short`, `burst1-openloss-latch3`).
The setup-level fix is the move itself: DM-MF2 / DM-MF4 (Primary re-evaluation, not this run).

## 6. Plan for next week (11-09..11-13)
1. Owner: DM-MF2 / DM-MF4 at the Primary re-evaluation (two-year evidence tonight backs the move: both negative, no filter saves them).
2. QDAY through 11-17: daily R split by SPY up / down / quiet; build the index-first two-sided open (side from SPY / QQQ / breadth 09:35-09:45).
3. Test `sat1107-gapup-midday-lod-long` on two years (wide geometry, same-time random-long control).
4. Watch the A7 / A1 shadows forward (journal only); re-score after 10 more sessions instead of re-tuning now.
5. Housekeeping: HK-GEN-BP (Gen buying-power rejects), MTUM ticket with Alpaca.

## Backlog (`backlog_updates.py`; BACKLOG.md re-rendered)
New: `sat1107-burst-flush-latch-rework` (7, parked), `sat1107-range-extreme` (4, parked), `sat1107-gapup-midday-lod-long` (idea),
`sat1107-index-first-open-two-sided` (idea). Updated: `burst2-mf-after-flush-rework` → parked (6), `fb1-1105-sell-bounce-not-flush`
(4 → 8), `gate1-checkpoint-gate` (note).

## Files
`PLAN.md`, `week.py` → `week_out.txt` / `week_scorecard.csv` / `week_by_setup.csv` / `week_caps.csv`, `giveback_week.py` →
`giveback_week_out.txt` / `.csv`, `sim_a.py` + `score_a.py` → `a_*.csv` / `a_out.txt`, `b_mf.py` → `b_out.txt` / `b_results.csv`,
`c_e.py` → `ce_out.txt` / `c_results.csv` / `e_results.csv`, `backlog_updates.py`. Inputs: BURST2 trade tables and the 11-06
journals in the scratchpad (not committed).

Educational only — not financial advice.
