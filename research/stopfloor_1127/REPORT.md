Educational only — not financial advice

# STOPFLOOR-1127: are very tight stops a cost-driven failure mode, and does a stop floor fix it? (research only; nothing changed)

## Plain-language summary
- **Verdict: FAIL. 0 of 18 pre-registered configs pass every bar.** The study does find a real pattern and two leads.
- **The pattern is real.** Tight stops lose more R, in live trading and in the backtest. The main cause is cost.
  - Live (non-Graveyard, 20,974 trades, 31 sessions, 10-14..11-25): stops under 50 bp lose −0.28 to −0.50 R/trade. Stops of 250 bp or more lose −0.14.
  - By stop width in spreads: under 6 spreads loses −0.31, 20+ spreads loses −0.135.
  - Realized cost is 0.38R/trade under 25 bp, 0.15R at 25–50 bp and 0.05R at 250+ bp.
- **Skipping tight-stop entries (remedy a)** helps the backtest on CHECK and T2 for every width rule tried. But no rule beats a random skip of the same share on both splits and on live.
  - The best backtest rule is skip when the stop is under $0.20 (Sc20). It passes every backtest bar: CHECK +1.37 R/day (t 3.0), T2 +1.09 (t 4.0), 100th percentile of random skips, every setup better. It **fails the live leg**: live, the trades it skips are only slightly worse than the ones kept (−0.209 vs −0.194), and it sits at the 68th percentile of random skips.
- **Widening the stop to a floor and resizing to keep $ risk (remedy b, new)** keeps every trade. It raises R on CHECK, T2 and FIT for 50/75/100 bp, and no setup gets worse. But on T2, widening a random set of lots by the same amounts helps as much or more (W75 T2 at the 10th percentile of the control). So the gain is "wider stops cost less", not "fix the tight ones".
- **Lead 1: spread-multiple floor, live only.** Skipping stops under 6 or 8 spreads beats 500 same-share random skips at the 100th percentile, live.
  - Skipped trades average −0.31 / −0.29 R vs −0.18 / −0.17 kept.
  - 12 of 14 / 13 of 16 setup families improve; 101 of 120 / 122 of 147 setups improve.
  - Best-day share is 18–19%.
  - It cannot be backtested: we have no spread history. So it can't pass these bars and is listed as a lead only.
- **Lead 2: the LIVE-L cost model under-charges tight-in-spread stops.**
  - Under 6 spreads, realized cost is 0.215R against LIVE-L's 0.126R (−0.088R).
  - At 6–8 spreads the gap is −0.043R.
  - At 20+ spreads LIVE-L over-charges by +0.040R.
  - A spread-aware cost term would make every research fill model fairer to wide-stop lots and harsher on tight ones.
- **Absolute level:** every arm stays negative per trade on CHECK and T2 after costs (the BASE book is −0.074 / −0.097 R per lot; the best arm is −0.053). A floor is a cost remedy, not an edge.

## Setup of the test
- Pre-registered: PREREG.md (sha256 0e2adc37…8149), committed in 73eac71635 before any score.
- **Configs: 18 counted** (10 bench + 8 live skip rules). Cumulative N ≈ 8,952 → **≈ 8,970**. The lineage bar t ≥ ~4.3 is shown for reference. The per-study bar is t ≥ 3.0 for 10 bench configs.
- **Lineage, read first:**
  - p3_1029 A1–A3: cost-filter gains were cost avoidance. A3 has been live as the Testing CF since 10-30.
  - cfprimary_1127 (tonight): CF on the Primary book fails vs random removal on CHECK. Its salvage lead was a filter on the tight-stop RW3/RW5 shorts.
  - New here: widen-and-resize, bp and spread floors, and a live per-setup breadth check.
- **Bench data:** Primary's 4 setups' bench10 candidate lots (rsw/cand.parquet from regsteer_1126; 52,544 lots, pre-book, i.e. the testing-arena view with no caps). Exits were re-walked on 1-min bars with the stopx BASE rule.
  - Parity: 100% of exit minutes reproduced. LIVE-L R matches cand r exactly on the shorts; LR8 matches on NM-ETF.
  - Sessions: CHECK 276, T2 415, FIT 170.
  - Locked block never read (asserted in every loader).
  - The 4 GEN setups in the file were excluded: their hold/trail exits are not in the walk.
- **Costs:** LIVE-L (cells_live.json) on all 4 setups; widened lots are charged at the widened risk. LR8 is shown as the second basis and has the same sign in every config. Controls: 200 random reps (skip: same share within setup × split; widen: the same widening multipliers permuted across lots within setup × split).
- **Live data:** the primshorts_1126 cleaned set, all accounts except Graveyard. R = decision-basis gross minus realized cost. 500 same-share random skips within setup.

## Failures first: every config against the bars (bench R/day = sum over lots; dR vs BASE, LIVE-L)
| Config | Share CHECK / T2 | dR/day CHECK (t) | dR/day T2 (t) | Control pct CHECK / T2 (p95 is the bar) | Best-day share C / T2 | Setups better C / T2 | Live leg | Fails |
|---|---|---|---|---|---|---|---|---|
| S50 skip < 50 bp | 6.7% / 18.4% | +0.91 (3.7) | +0.79 (4.7) | 99.5 / **91.5** | 6% / 8% | 2/2, 2/2 | pass (100th pct) | T2 control |
| S75 skip < 75 bp | 17.7 / 34.1 | +1.51 (3.5) | +1.48 (5.9) | **26.5** / 100 | 8 / 6 | 2/2, 3/3 | pass (99.8) | CHECK control |
| S100 skip < 100 bp | 27.7 / 44.4 | +2.68 (4.4) | +1.59 (5.1) | **93.0** / 96.0 | 6 / 6 | 3/3, 3/3 | pass (100) | CHECK control |
| Sc10 skip < $0.10 | 1.1 / 2.3 | +0.35 (**2.7**) | +0.15 (**2.3**) | 100 / 100 | 16 / 23 | <5% affected | **fail (93.0)** | t, live |
| **Sc20 skip < $0.20** | 6.8 / 19.3 | +1.37 (3.0) | +1.09 (4.0) | 100 / 100 | 22 / 9 | 3/3, 3/3 (+NM-ETF) | **fail (68.2)** | live only |
| W50 widen to 50 bp | 6.7 / 18.4 | +0.29 (3.9) | +0.01 (**0.1**) | 99.5 / **1.0** | 6 / — | 2/2, 2/2 | none | T2 |
| W75 widen to 75 bp | 17.7 / 34.1 | +0.55 (3.3) | +0.25 (**2.7**) | 99.5 / **10.0** | 12 / 11 | 2/2, 3/3 | none | T2 t, T2 control |
| W100 widen to 100 bp | 27.7 / 44.4 | +0.77 (**2.6**) | +0.61 (4.3) | 96.5 / **83.0** | 12 / 11 | 3/3, 3/3 | none | CHECK t, T2 control |
| Wc10 widen to $0.10 | 1.1 / 2.3 | −0.02 (−0.5) | +0.05 (1.8) | 10.5 / 98.5 | — / 34 | <5% | none | most |
| Wc20 widen to $0.20 | 6.8 / 19.3 | +0.25 (**2.1**) | +0.28 (3.1) | 99.5 / **82.0** | 26 / 13 | 2/3, 2/3 | none | CHECK t, T2 control |
| L-bp50 / 75 / 100 (live) | 9.6 / 25.2 / 39.3% of live | +585 / +1,185 / +1,801 R in 31 sessions | | 100 / 99.8 / 100 | 13 / 11 / 11% | 55/68, 91/112, 118/143 setups | — | no bench leg of its own (see S50–S100) |
| **L-k6 / k8 / k12 (live)** | 11.5 / 22.0 / 39.9% | +752 / +1,330 / +2,241 R | | **100 / 100 / 100** | 18 / 19 / 23% | 101/120, 122/147, 146/172 | — | no spread history to backtest |
| L-c10 / c20 (live) | 1.9 / 9.1% | +115 / +399 R | | 93.0 / 68.2 | 15 / 13% | 20/29, 67/88 | — | control |

- Avg dR without the best day is positive in every split for every config with a positive total.
- The live random means are large, e.g. L-k8: random +941R against +1,330R. Every live bin loses money (all accounts were negative per trade in this window), so any skip gains. Only the excess over random is selection.

## What works, and what can be salvaged
1. **The remedies are targeted, not broad.** In the bench no setup got worse in S50, Sc20, W75 or W100 on CHECK or T2.
   - Gains sit where the tight stops are: RW3/RW5 (median stop ~70–85 bp). S50 gains +0.03 to +0.08 R/lot there, and W75 gains +0.014 to +0.033. L3 and NM-ETF are barely touched.
   - Per family: gap-down shorts +0.010 to +0.069 R/lot; ETF long 0 to +0.005.
   - Live breadth for L-k8: 13 families better, 3 worse (LIQ −1.7, STQ −0.9, ULT −0.8 R). 122 setups better (+1,379R), 25 worse (−72R).
2. **But live and the bench disagree on which width measure selects.**
   - In the bench, cents select: the gross edge of stops under $0.20 is negative (−0.055 / −0.089 R on CHECK / T2), probably tick discreteness plus the target-through-by-1c rule.
   - Live, cents barely select: gross of stops under $0.10 is −0.036, better than the −0.087 of kept trades. bp and spread multiples do select.
   - The RW family is the exception live: under L-bp50 its tight-stop trades made money (+20R forgone). That matches cfprimary's live Primary line (RW3 +4.3R).
3. **Widening is a general cost lever.** LIVE-L cost per R falls as a/width for any lot, so a random widening gains too. The gross path effect is ~0 (dGross/day −0.09 to +0.17).
   - Salvage: it is the one remedy that keeps playing time.
   - A pre-registered test of uniform widening plus resize (every lot ×1.25 / ×1.5, R geometry kept) on the Primary book is the natural next test. It is not run here and not counted.
4. **Spread is the right unit for a floor (lead).** Stop width in spreads separates live outcomes better than bp or cents. LIVE-L, which has no spread term, under-charges exactly those lots (0.088R under 6 spreads).

## Caveats
- **Lot level, not book level.** Primary's 30-lot cap refills freed slots. cfprimary_1127 showed book gains shrink against random removals. Skip rules also cost playing time (7–44% of lots), which runs against the owner's playing-time rule. Widen rules do not.
- **Bench breadth is 4 setups.** The other setups' exits are not walkable here, so cross-setup breadth comes from live only, a single 31-session window.
- **Spread floors are untestable historically.** The live spread is the decision-time quote (spread_bps). The Testing CF already truncates the tightest stops in Testing 1/2, Explore 1 and Live Lab since 10-30, so those accounts' tight-stop bins are thinner.
- **Rule changes inside the live window 10-14..11-25 (research/ledger.jsonl):**
  - Setup moves: 10-15 RW3/RW5 → Primary; L3 in on 10-20, out on 10-22, back on 10-30.
  - Rules: 10-27 GX1; 10-28 sizing; 10-29 −2R latch.
  - **10-30 Testing cost filter CF** (max_stop_cost_r 0.15 in Testing 1/2, later Explore 1 / Live Lab; directly truncates tight stops).
  - 11-04 ROLL1 (Explore 1 / Live Lab); 11-11 TEAM-6; 11-12 LR8/LR3 and On Deck; 11-17 TSZ1 (testing half-size lots, R comparable); 11-19 Epoch 1 / U9-TGT.
  - **11-20 stop rounding** (bears on cents-level stops).
  - 11-23 burst brake / PSHADOW / Remedy-Q.
  - Bench windows use one fixed rule set.
- Today's 11-26/11-27 trades (incl. Primary AHCO with ~8–9c stops) are not in the live set: there are no exit bars yet.

## Backlog proposal
None of the configs passed, so this is a lead proposal for the synthesis step. It is not a pass.
- **id:** STOPFLOOR-K8-SHADOW
- **What:** journal, for every live entry in every account, the stop width in spreads at decision (already in signals.info spread_bps). Score a pre-registered shadow skip "stop < 8 spreads" (and k = 6) forward over 20 sessions against 500 same-share random skips. This is information only, with no live skip.
- **Alongside:** refit LIVE-L with a spread-multiple term (a "LIVE-S" cost model) and re-score the fill models.
- **Pass bar (forward):** 100th-percentile-class excess over random (≥ 95th), t ≥ 3.0 on day-clustered excess, best-day share < 25%, at least 2/3 of families better.
- **Separately:** a uniform widen-and-resize test on the Primary book (keeps playing time).

## Files
- Scripts: sf_walk.py (minute walk, BASE + 5 widen variants), sf_score.py (bins, configs, skip controls), sf_ctrl.py (widen controls, 7.9M walks), sf_live.py (live leg), sf_common.py.
- Outputs: score.json, ctrl_widen.json, live.json, summary.json (bar-by-bar pass/fail), *_out.txt.
