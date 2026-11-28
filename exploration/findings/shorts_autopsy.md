# Track 2: Shorts autopsy (why shorts fail live, and whether any condition rescues them)

Educational only — not financial advice.

**Configs tried in this track: 9** (R1-R4 day/time skips, C5/C10/C20 crowding caps, D1 cross-clone dedupe, testing latch replay) plus 1 re-check of an already-settled exit (RW3/RW5 1.25x target, counted). Cumulative N ≈ 9,363 → **≈ 9,373** (other tracks tonight not included). All pre-registered in `exploration/sandbox/shorts_autopsy/PREREG.md` (commit 0118bab9fa; addendum A committed before its scores; addendum B was written before its score but committed together with the results). **Passes: 0 of 8 bench configs.** Locked holdout 2024-11-01..2025-02-28 never read (asserted in every bench script).

## Numbers first

| # | Finding | Key number |
|---|---|---|
| 1 | **The gap-down short family is not a slow bleed; it is one day.** Live (non-Graveyard, 10-23..11-27, LR8): 4,268 lots, −1,249R. 11-25 alone: 1,528 lots, **−1,216R (97%)**. The other 24 sessions: 2,740 lots, **−0.012 R/lot** (gross +0.024), weekly −0.8 / +27.8 / +16.0 / −84.4 / +118.3 / −1,325.6 (3 of 6 weeks green). | 97% of the family loss on 1 day |
| 2 | **Shorts are a leveraged bet on the market falling during the hold, and they lose about 0.17R per lot even after removing that bet.** Gross R per lot = −0.17 + (−0.80 × SPY % move during the hold). Market-neutral gross: shorts −0.174 / −0.160 (gap-down / other families, day t −2.4 / −3.6) vs longs −0.067. Short-book R per day correlates −0.80 with SPY's 11:00→close move. | short "selection" is worse than long by ~0.10R/lot live |
| 3 | **Primary's three shorts lose on SPY gap-UP days, not on gap-down days.** Primary account: shorts on SPY gap ≥ +0.5% days = 165 lots, **−78.7R in 6 sessions** (63% of the −124.6R Primary short total). The trio on gap-up days: L3 −17.0, RW3 −6.5, RW5 −21.4 R; on flat days RW3 +14.1, RW5 +21.1, L3 −0.4. | −7.5R per gap-up session |
| 4 | **On the 2-year bench no condition rescues shorts after costs.** Bench gross edge ≈ +0.03R/lot for the gap-down family; LIVE-L cost ≈ 0.10-0.13R; every split/setup negative (T2: RW3 −0.138, RW5 −0.182, L3 −0.053 R/lot). All 4 pre-registered skip rules and all 4 crowding/dedupe rules fail the matched-random control (percentiles 0-88, none ≥ 95 on both splits). | 0 of 8 pass |
| 5 | **Crowded and repeat short lots are the better lots on average, not the worse ones.** Bench: lots removed by a family cap of 20 average −0.004R vs −0.145R kept (T2); repeat lots in the same name −0.07 vs first lots −0.10 / −0.16 (CHECK / T2). The tail lives on crowded days, but so does the upside; caps only cut size. | crowding = size, not quality |
| 6 | **Borrow (ETB) is not the reason.** The 7,781 non-Graveyard shorts we could not borrow would have done gross −0.112R (what-if run), vs −0.228 for shortable shorts skipped for capacity; day-paired difference −0.03 (t −0.32). | no hidden "only the bad ones are borrowable" |

## 1. Live autopsy (non-Graveyard, 10-23..11-27, LR8 R after costs, identical signals counted once)

**Rule changes inside this window (ledger):** 10-28 Primary size ~$4k · 10-29 −2R latch (closed R) · 10-30 Testing cost filter · 11-11 TEAM-6 · 11-12 LR8 costs + restructure · 11-17 TSZ1 half lots in testing · 11-19 Epoch 1 / U9-TGT · 11-20 stop rounding / FOOTRACE-EXIT · 11-21 cost-basis fix · 11-23 ST7 out, BRAKE-BURST, PSHADOW · 11-27 GYH V1+V3, ROT-B3, GEN seed. The market itself was unusual: SPY fell from 773 (10-21) to 690 (11-20) and rallied to 728 (11-27), with three −3% days (11-05, 11-19, 11-20) and a gap-down-then-+2.4% squeeze on 11-25.

Gross below = fill-based (journal exit and entry fills, so slippage is inside); cost = LR8 fees/charges on top.

| Group | Lots | Sessions | Avg R | Gross | Total R | Day t | Avg R w/o best day | Avg R w/o worst day |
|---|---|---|---|---|---|---|---|---|
| Long | 8,695 | 25 | −0.162 | −0.118 | −1,408 | −2.74 | −0.177 | −0.113 |
| Short, gap-down family | 4,268 | 25 | −0.293 | −0.257 | −1,249 | −1.02 | −0.315 | **−0.008** |
| Short, other | 5,044 | 25 | −0.104 | −0.056 | −526 | −1.19 | −0.167 | −0.073 |

"Gap-down family" = strategy name contains gapdn / gap-slope (L3*, RW1/3/5/7, CWT09, NM-MF3/RWR1/PM-gapdn and their WB/RQa clones).

### By condition (shorts; full tables in `exploration/sandbox/shorts_autopsy/live_autopsy_out.txt`)
| Dimension | What the live data say |
|---|---|
| **Gap-down vs not** | Stock gapped ≤ −2.66%: −0.376 R/lot (2,262 lots); −2.66..−1%: −0.001 (1,299). Ex 11-25 the deep-gap buckets are ≈ 0 to +0.06. The gap itself is not the problem; 11-25 is. |
| **SPY gap** | Gap-down family on SPY gap ≤ −0.5% days: −0.476 (7 sessions; −0.015 ex 11-25); flat days **+0.051** (12 sessions, 7 green); SPY gap ≥ +0.5%: **−0.201** (6 sessions, 1 green, t −1.76). |
| **Market move during the hold (beta)** | SPY −0.3% or more during hold: shorts +0.510 R/lot; SPY +0.3% or more: −0.783. The slope is −0.80 R per 1% SPY; it explains most of the day-to-day swing. |
| **Squeeze days** (SPY down into 11:00, then +0.4%+ after) | 2 sessions, 2,107 short lots, **−1,418R** (80% of all short loss). Longs made +237R on the same 2 days. |
| **Time of day** | Gap-down family is flat at every hour ex 11-25. Non-gap-down shorts entered before 12:00 lose −0.17 to −0.19 R/lot ex 11-25 (2,820 lots); after 12:00 +0.03 / +0.06. On 11-25, 12:00-13:00 entries lost −656R (615 lots). |
| **Price band** | No band is positive; $20-50 worst (−0.239), $200+ least bad (−0.149). Costs fall with price (0.076R under $10 → 0.038R over $200). |
| **Stop width** | Stops < 30 bp: −0.919 (cost 0.275R); < 4 spreads −0.508, 4-6 spreads −0.322, 6-8 −0.277; ≥ 12 spreads −0.14. Same shape for longs. Already in hand via the SPREADFLOOR shadow (logs from 11-30). |
| **Borrow / ETB** | See finding 6 (`etb_skips_out.txt`). Non-borrowable names are mostly leveraged ETFs (UVIX, SNDQ, GDXU, SOXS, MSTU). |
| **Clones** | Since 11-19, 24 gap-down-family setups ran across 9 accounts; six L3 variants (rsi5hi ×3, lowdist ×2, fromopen ×3 incl. RQa-1230) lost about −1,040R between them. Primary lost only −42.3R that day because its −2R latch fired; the testing accounts have no latch. |

### Primary's three shorts (all accounts, deduped)
| Setup | Lots | Avg R | Gross | Avg R w/o best day | Best-day share | SPY move during hold ≤ −0.2% / > +0.2% |
|---|---|---|---|---|---|---|
| L3-gap-slope-fromopen-FD | 309 | +0.063 | +0.104 | −0.045 | 160% | +0.451 / −0.802 |
| RW3-gapdn-rsi5pop-flowsell-short-FD | 166 | −0.046 | +0.003 | −0.155 | — | +0.495 / −0.545 |
| RW5-heat30-...-gapdn-short-FD | 160 | −0.071 | −0.023 | −0.144 | — | +0.160 / −0.412 |

All three are `1 day` records or negative without the best day. Stops under 8 spreads lose on all three (−0.33 / −0.11 / −0.16).

## 2. Bench (bench10 engine unchanged, 8 short setups, LIVE-L costs, entry ≥ $5, ETB ≥ 0.9, candidate level)

Lots: CHECK 35,980 (276 sessions), T2 12,597 (427), FIT 22,768 (170). Full output in `bench_score_out.txt`.

| Setup | CHECK avg R (gross) | T2 avg R (gross) | FIT avg R |
|---|---|---|---|
| L3-gap-slope-fromopen-FD | −0.063 (+0.035) | −0.053 (+0.054) | +0.035 |
| L3-gap-slope-lowdist-FD | −0.170 (−0.066) | −0.168 (−0.058) | −0.152 |
| L3-gap-slope-rsi5hi-FD | −0.090 (+0.010) | −0.124 (−0.023) | −0.039 |
| RW3 | −0.100 (+0.029) | −0.138 (+0.007) | −0.165 |
| RW5 | −0.105 (+0.030) | −0.182 (−0.032) | −0.141 |
| CWT09 | +0.033 (n 405) | −0.243 (n 199) | −0.005 |
| RW6-ns2-up3 | −0.105 | −0.058 | +0.008 |
| NM-RWN4 | +0.006 (n 337) | −0.114 (n 120) | +0.057 |

**Descriptive cells:** no bucket of stock gap, SPY gap, time of day, price band or stop width is positive on both CHECK and T2 for the gap-down family. Two shapes repeat on the bench: (a) gap-down-then-rally days hurt (T2 −0.344 R/lot; hindsight only, not tradeable as defined); (b) **shorts entered when SPY is already ≥ +1% above its open are positive in all three splits** (gap-down family CHECK +0.146 / T2 +0.051 / FIT +0.073; other +0.202 / — / +0.149), but on only 13-30 days per split (day t 0.5-1.2) and live says the opposite (−0.468 over 3 sessions). This is a weak lead, not a finding.

### Pre-registered rules (pass bar: dR > 0, t ≥ 2, ≥ 95th percentile vs matched random, on both CHECK and T2)
| Config | CHECK dR/session (t; pct vs random) | T2 dR/session (t; pct) | FIT | Worst-5 C / T2 | Setups better/worse (C) | Verdict |
|---|---|---|---|---|---|---|
| R1 skip gap-down family on SPY gap ≥ +0.5% | +0.65 (1.67; 26th) | +0.09 (0.88; 12th) | −0.11 | unchanged | 6 / 0 | FAIL (a size cut on random days does as well) |
| R2 skip all shorts on SPY gap ≤ −0.5% | +0.34 (0.11; 27th) | +0.61 (0.96; 86th) | −0.62 | −1,984→−1,581 / −468→−288 | 6 / 2 (L3-fromopen −0.91) | FAIL (tail only; these days are the family's *best* on average) |
| R3 skip non-gap-down shorts before 12:00 | +0.37 (1.11; 14th) | +0.11 (1.08; 88th) | −0.66 | ≈ | 1 / 1 | FAIL |
| R4 R1 + R2 | +0.99 (0.31; 17th) | +0.69 (1.08; 45th) | −0.73 | as R2 | 6 / 2 | FAIL |
| C5 / C10 / C20 family open-lot cap | +8.1 / +7.1 / +5.4 (t 1.4-1.9; 1-10th) | +1.2 / +0.6 / +0.0 (0th) | ≤ +1.7 | −1,887→−95..−237 | 5 / 1 | FAIL (worse than the constant cut in every row) |
| D1 first lot per name per day across clones | +5.8 (1.55; 0th) | +1.2 (1.78; 0th) | −1.05 | −1,887→−370 | — | FAIL (repeats are better than first lots) |

Candidate-level caveat: no Primary cap/latch, so absolute R/session is the whole candidate pool, not a book. The rules are day/time skips, so the comparison against matched random removals is the meaningful part.

### Testing-account latch replay (live, descriptive, in-sample; `live_latch_testing_out.txt`)
Applying Primary's existing −2R closed-R latch to the 8 non-Primary, non-Graveyard accounts over 10-23..11-27: **+1,230R** (−3,036 → −1,806R; 3,575 of 17,064 lots dropped). Gap-down family +864R, but **−94R without 11-25** (insurance, not edge); longs +280R (+275 ex 11-25, day t 2.63); 61 setups better, 31 worse (worst −29.3R). Worst family day −1,173 → −215R. Green days unchanged (13→11 family, 5→5 longs).

### RW3/RW5 1.25x target re-check under LIVE-L (T1)
The settled pass (outsider_1120 Y1: +0.044 R/lot, t 2.58) **does not hold up under LIVE-L costs on this bench** (same lots, only the target moved; `rw_t125_out.txt`):
| Split | RW3 Δ R/lot (day t) | RW5 Δ (day t) | Both Δ (day t) | Weeks up |
|---|---|---|---|---|
| CHECK (7,309 lots) | +0.012 (1.77) | +0.002 (0.80) | **+0.007 (1.78)** | 37 / 58 |
| FIT (4,045 lots) | −0.015 (−1.30) | +0.001 (−0.67) | **−0.007 (−1.37)** | 12 / 36 |
T2 was not re-walked (needs the full T2 frame build). Read: at best +0.2 R/week for Primary; not a fix worth a rule change on this evidence. It stays a low-cost shadow candidate only because the earlier test passed.

## 3. Why shorts fail live: the autopsy in one paragraph
Three things stack. (1) **No gross edge after costs on the bench** (≈ +0.03R gross, ≈ 0.11R cost), the same wall as longs; nothing in gap, price, time, stop width or market state turns the family positive on held-out data. (2) **A large market bet** (−0.8R per 1% SPY over the hold) in a tape that fell 11% and then ripped: the short book is the account's index short, so it gets run over on squeeze days (11-25: −1,335R across accounts) and on SPY gap-up days (Primary: −78.7R in 6 sessions). (3) **Correlated clones without a latch** in the testing accounts turned one bad market day into 97% of the family's five-week loss. Removing 11-25, the gap-down family is break-even live (−0.012R/lot), which matches the bench (≈ −0.06 to −0.10) better than the headline does. "Shorts underperform" is mostly one day plus beta; the slow bleed is in the non-gap-down shorts (−0.084R/lot ex 11-25, morning entries worst).

## 4. Recommendations per Primary short and family (the owner decides; nothing here changes any rule)
| Setup / family | Verdict | Evidence | R/week effect (uncertainty) |
|---|---|---|---|
| **L3-gap-slope-fromopen-FD** | **Restrict** (existing L3-OUT or half-size card + LATCH-OPEN); no condition fix found | Bench −0.05..−0.06 R/lot both splits; live +0.063 but 160% best-day share; −0.47 R/lot on SPY gap-up days | Primary live −0.9 R/wk; bench book +0.77 R/day CHECK, +0.36 T2 if moved (primshorts), i.e. +1.8..+3.9 R/wk, mostly a size effect |
| **RW3** | **Keep for now, restrict by exposure if Primary must cut** (no fix found: the 1.25x target shrinks to +0.007 R/lot under LIVE-L) | Live flat-day +0.223, gap-day −0.16..−0.25; bench −0.10/−0.14 | Primary live −1.6 R/wk; 1.25x target ≈ +0.2 R/wk (±1); removal +0.95 R/day CHECK bench (rwout), mostly size |
| **RW5** | **Keep for now; first to cut if a second short must go** | Worst live (−2.3 R/wk), worst T2 (−0.182); flat days +0.347, gap-up −0.475 | Primary live −2.3 R/wk; removal +0.91 R/day CHECK / +0.80 T2 bench (rwout), mostly size |
| **Gap-down family in testing (L3/RW clones)** | **Restrict exposure** — fewer near-identical clones or a per-setup latch in testing; per-lot quality is unchanged | 11-25 = 97% of family loss; latch replay +864R (−94 ex 11-25); caps/dedupe fail on the bench (crowded lots are better) | Tail only: worst family day −1,173 → −215R (live replay) |
| **Non-gap-down shorts** (RW6, NS*, MF*, heat_fade, exhaustion, GEN shorts) | **Restrict/keep in testing; nothing for Primary** | Steady bleed −0.084 ex 11-25, market-neutral −0.174 (t −3.6), morning entries −0.17..−0.19; R3 (skip before 12:00) fails on bench | — |

## 5. Confidence
**Medium-high** on the diagnosis (one day + beta + clones; no rescuing condition): the bench has 71,345 lots over 873 sessions in three splits, eight configs all fail the matched-random control, and the live decomposition is arithmetic, not a fit. **Low** on any expected R/week number: live has 25 sessions in a corrective market, every short record is `1 day`, and the in-sample live replays (latch, gap-up skip) are not held out.

## PROPOSAL candidates (for the owner; none touches Primary rules)

**P1. GD-GAP family readout on the GAP-U shadow (tests restriction R1 forward).**
- What: in the regime-switch shadow already running, add a family-targeted readout: gap-down family shorts only, at SPY gap ≥ +0.25% and ≥ +0.5%, with a same-day random-switch control (consultants_1126 C method).
- Expected effect: in-sample Primary +7.5R per gap-up session (≈ +9 R/week); the bench says most of it is a size cut (12th-26th percentile vs random days), so the honest expectation is **+0.5 to +3 R/week** for Primary, with high uncertainty.
- Risk: none (readout); if adopted, fewer lots on up-gap days and fewer setups get playing time those days.
- Experiment: Primary and Testing lots (read-only); baseline = no switch; 20 sessions (GAP-U's 15-20-session bar, ~12-10 to 12-28); success = excess over same-day random switch ≥ 95th percentile and positive without the best day.
- **Can START Monday 11-30: yes** (readout on existing shadow data).

**P2. Testing-account tail guard: −2R per-setup latch (closed R) as a forward test in one testing account.**
- What: turn on the latch Primary already uses in one testing account that carries gap-down clones (Testing F = mcf-data-testingf, or Testing A = testing2), with skipped lots still recorded by the what-if run (run_id 2), so promotion data are not lost.
- Expected effect (live replay, in-sample): worst day cut by 60-90% (Testing F −261 → −63R; Testing A −135 → −56R; On Deck −391 → −49R); total ≈ **+5 to +70 R/week per account** (Testing F +36, Testing A +52; Testing E −4), nearly all from squeeze days; ex 11-25 about 0 for the gap-down family and positive for longs.
- Risk: what-if lots are bar-simulated without costs, so promotion stats for latched setups mix two bases; setups that lose early in the day get less live playing time (owner's playing-time rule) — needs the owner's call.
- Experiment: one testing account; baseline = the same account with the latched lots added back from its what-if run (LIVE-L cost applied to them); 20 sessions; success = worst-5 days improve ≥ 40% and total R not worse than baseline − 5R. Note the replay above is a lower bound (closed R only) and is in-sample.
- **Can START Monday 11-30: only with the owner's approval over the weekend** (testing config change, outside market hours; Primary untouched).

**P3. RW-TGT125 shadow (low priority: conflicting evidence).**
- What: nightly shadow replay of every Primary RW3 / RW5 lot with the target at 1.25R instead of 1.0R, from Alpaca 1-min bars (GET only); no orders, no config change.
- Expected effect: earlier test +0.044 R/lot (outsider_1120 Y1, t 2.58); tonight's LIVE-L re-check +0.007 (CHECK) / −0.007 (FIT). Honest expectation **0 to +0.5 R/week** for Primary if adopted; the shadow only settles the conflict.
- Risk: none while a shadow; if adopted, more lots end at the flatten (exposure to late reversals).
- Experiment: account = Primary lots (read-only); baseline = actual 1.0R exits; 20 sessions (to ~12-28); success = Δ ≥ +0.02 R/lot, day t ≥ 1.5, ≥ 3 of 4 weeks positive, best-day share < 50%.
- **Can START Monday 11-30: yes** (research script; no Primary change).

## Sources
- Scripts and outputs: `exploration/sandbox/shorts_autopsy/` (live_load.py, live_fetch.py, live_autopsy.py, live_autopsy2.py, etb_skips.py, live_latch_testing.py, gen_shorts.py, bench_score.py, bench_cap.py, bench_dedupe.py, rw_t125.py; *_out.txt, bench_rules.csv, bench_cap.csv; PREREG.md).
- Settled results used, not repeated: research/primshorts_1126 (LIVE-L, L3 options), research/rwout_1127 (removal = size cut), research/l3refire_1127 (repeats within L3), research/squeeze_1125 (B8/SV/SO), research/outsider_1120 (RW 1.25x target), research/consultants_1126 (GAP-U statistics), exploration/PRIOR_RESEARCH.md.
- Data: 10 journals via `git show origin/mcf-data*:journal.db` (run 1 trades, run 2 what-if skips), Alpaca daily and SPY/QQQ/IWM 1-min bars (GET only), bench10 caches (data/cache_hist, data/cache_fresh, research/history2y).

Educational only — not financial advice.
