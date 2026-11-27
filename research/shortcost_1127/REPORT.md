Educational only — not financial advice

# SHORTCOST-1127: where trading is cheapest after LIVE-L, and whether a cost-zone universe filter is a remedy (research only; nothing changed)

**Plain-language summary.**
- **Verdict: LEAD, not a pass. 0 of 4 history configs met every bar.** Costs are in throughout: LIVE-L is the headline and LR8 is shown alongside.
- **The task's example bar ("shorts only where LIVE-L cost < 0.05R") cannot be used.** LIVE-L never prices a trade that cheaply: 0.3% of live shorts and about 0% of history lots fall below it. The pre-registered bars were therefore 0.10R and 0.12R.
- **Cost explains less than setup quality.** LIVE-L cost per trade is fairly flat at 0.06–0.19R. The exception is stops tighter than 50 bp, which cost 0.17–0.19R. Net R by price, spread, time and ETB band is negative almost everywhere, and gross R, not cost, sets the ranking.
- **Cheapest zones: stop width of 200 bp or more in $10–100 names, about 0.06–0.075R.** The most expensive and worst zone is shorts with stops under 50 bp: −0.34R per trade net, t −4.7.
- **Best single rule: R2, skip shorts whose pre-trade LIVE-L cost is 0.10R or more.**
  - It beats a size-matched random removal on both history splits:
    - CHECK +258R, day-clustered t 3.09, best-day share 13%.
    - T2 +137R, t 2.98, best-day share 10%.
  - It fails two bars:
    - Per setup: only 2 of the 5 setups it touches (L3, RW5) beat random on both splits.
    - Live: the trades it keeps are no better than all trades (LIVE-L −0.2005 vs −0.1967 R/trade). On fills (realised basis) they are flat.
  - It is also broad. It removes 80–93% of RW3, RW5, G05 and G07 lots, which comes close to switching those setups off.
- **R3 (skip any side at 0.12R or more) is the most consistent but fails CHECK.**
  - T2: +134R, t 2.35.
  - Live LIVE-L: +244R, t 2.56. Live on fills: +225R, t 2.39.
  - Per setup: 6 of 7 setups improve on both splits; the worst is −0.004 R/trade.
  - CHECK: +157R but t 1.33, below the 2.0 bar.
- **No rule makes the history book positive.** Best case is R2: CHECK −1.41 R/session (base −4.12), T2 −1.05 (base −3.54).
- **Salvage: L3-gap-slope-fromopen-FD in cheap zones.**
  - Under R2 it removes 32–39% of L3 lots. L3 moves from −0.099 to −0.062 R/trade on CHECK and from −0.127 to −0.050 on T2, which is +170R and +121R vs random.
  - Live L3 moves from +0.079 to +0.161 R/trade (436 → 263 trades).
  - It is still negative on history, so it does not flip. It also counts only as a per-setup observation, because the owner's remedy rule says a remedy must not be tailored to one setup.

Pre-registration: PREREG.md, sha256 6961bda9…adca80, committed 110de0275b before any outcome was scored.
- **Configs: 6.** R1–R5 were pre-registered. P6 (ETB-always shorts) was added after the fact; it is counted and cannot pass.
- Cumulative N goes from about 8,952 to **about 8,958**. A lineage claim needs t ≥ about 4.3; nothing here reaches it.
- The locked block 2024-11-01..2025-02-28 is never read (asserted in sc_common.no_locked and bench10.no_locked on every load).
- Splits: CHECK 2025-10-01..2026-11-04 (276 sessions), T2 2023-01-03..2024-09-13 (427 sessions), FIT 2024-10 + 2025-03..09 (170 sessions; reported, not judged).

## 1. Data
- **Live data.**
  - Source: the primshorts_1126 pipeline (load_live.py and exit-minute bars), cleaned with calib_live.prep.
  - Size: 34,868 → **32,131 trades**, 2026-10-14..11-25, 10 journals (20,975 non-Graveyard).
  - Input hashes: live.parquet e892774b…94cd, exitbars.parquet b4ee3fbc…bcd19.
  - Per trade I compute:
    - engine gross R, from the decision-bar close to the engine exit;
    - **LIVE-L net** = gross minus the LIVE-L cost of the realised exit kind;
    - **realised net** = gross minus the realised cost (fills, fees, 1.2 bp borrow);
    - LR8 net, for reference.
  - **In-sample caveat:** the LIVE-L cells were fitted on these same trades. The realised basis is the independent live view.
- **ETB.** Every executed short was ETB at the time, because the broker rejects HTB names ("not shortable/ETB": 1,383 skips in Testing A alone), so no executed trade is HTB. The proxy used instead is the share of the 26 universe snapshots in which a name was ETB: always (1.0) or marginal (below 1.0).
- **History data.**
  - Source: bench10 candidate lots regenerated tonight by arenastars_1127/as_gen.py and copied read-only (trades_t1 3811e58b…, trades_t2 f1ca82a8…).
  - Setups: L3-gap-slope-fromopen-FD, RW3, RW5 and NM-ETF in the Primary book (cap 30, −2R latch); G05, G07 (shorts) and G37 (long) in the testing book (cap 100, cost filter 0.15).
  - Common rules: price ≥ $5 and shorts ETB ≥ 0.9.
  - The rule is applied before the book, so freed slots can refill.
  - The RND-* random-entry pools serve as a universe control.
  - Difference from arenastars: LIVE-L is used on both sides here, including NM-ETF and G37 (disclosed).

## 2. Live cost map (exploratory, all accounts; full tables in live_out.txt and live_map.json)
LIVE-L net and realised net are R per trade. Cost is in R.

| Cut | Short: n / LIVE-L cost / realised cost / LIVE-L net / realised net | Long: same order |
|---|---|---|
| $5–10 | 629 / 0.132 / 0.133 / **−0.089** / −0.090 | 809 / 0.128 / 0.133 / −0.193 / −0.198 |
| $10–20 | 1,305 / 0.101 / 0.110 / −0.117 / −0.126 | 1,530 / 0.104 / 0.097 / −0.167 / −0.159 |
| $20–50 | 3,237 / 0.102 / 0.109 / −0.201 / −0.209 | 4,030 / 0.105 / 0.100 / −0.164 / −0.159 |
| $50–100 | 3,848 / 0.108 / 0.115 / −0.185 / −0.192 | 4,123 / 0.112 / 0.105 / −0.190 / −0.183 |
| $100+ | 6,374 / 0.119 / 0.127 / −0.166 / −0.174 | 6,246 / 0.124 / 0.117 / −0.211 / −0.203 |
| stop < 50 bp | 1,468 / **0.186 / 0.191 / −0.341** (t −4.7) | 1,985 / 0.168 / 0.141 / −0.228 |
| stop 200 bp+ | 3,923 / **0.078 / 0.062** / −0.137 / −0.121 | 3,347 / 0.076 / 0.063 / −0.150 / −0.136 |
| spread < 10 bp | 8,231 / 0.121 / 0.107 / −0.187 / −0.172 | 9,915 / 0.122 / 0.095 / −0.184 / −0.158 |
| spread 20–35 bp | 2,277 / 0.092 / **0.139** / −0.156 / −0.202 | 1,855 / 0.094 / 0.130 / −0.201 / −0.237 |
| before 10:30 | 3,345 / 0.124 / **0.150** / −0.200 / −0.226 | 5,456 / 0.123 / 0.103 / −0.222 / −0.202 |
| 14:00 and later | 2,016 / 0.101 / 0.101 / **+0.019** / +0.018 (best-day share 329%, `1 day`) | 1,483 / 0.103 / 0.087 / −0.207 / −0.191 |
| ETB-always | 13,792 / 0.112 / 0.120 / −0.160 / −0.169 | — |
| ETB-marginal | 1,601 / 0.115 / 0.108 / **−0.265** / −0.259 (gross −0.151: a selection effect, not cost) | — |

What the map shows:
1. **Cheapest zones** (cells with n ≥ 200): stops of 200 bp or more in $20–50 / $10–20 / $50–100 names cost 0.060–0.075R. Every one of those cells is still net-negative on the shorts side, from −0.15 to −0.37R.
2. **Positive zones.** The only positive zones are $100+ shorts at 14:00 or later:
   - 100–200 bp stops: +0.137, best-day share 77%;
   - 200 bp+ stops: +0.052, best-day share 156%.
   - $10–20 shorts with 100–200 bp stops at 10:30–12:00: +0.047, share 86%.
   All of these are concentrated (`1 day`).
3. **LIVE-L blind spots** (input for a future LIVE-L v2):
   - It has no spread term. Realised cost rises with spread (0.107 → 0.139R on shorts), while LIVE-L predicts lower cost, because wide-spread names carry wider stops.
   - It under-charges opening shorts: realised 0.150 vs 0.124R before 10:30.
   - LR8 under-charges $100+ names (0.047 vs 0.127R realised) and over-charges $5–20 names (0.18 vs 0.13). This confirms primshorts_1126.
4. **Families** (by LIVE-L cost, cheapest first): ULT long 0.065, L3 short 0.091, NM, exhaustion_short, ST, NS, RW 0.110, GEN-short 0.112, CWT 0.124, MF short **0.145** (MF realised 0.177, the costliest). Net R is driven by family gross R: L3 family short −0.456 (all accounts, all L3 variants), RW −0.111, GEN-short −0.055, NM short +0.011.

## 3. History replay (LIVE-L, 7 setups; gain = rule book minus the mean of 20 size-matched random removals)
| Rule | Split | Base R | Rule R | Random R | Gain vs random | Day t | Best-day share of gain | Book avg R/trade (base → rule) | Bars 1 / 2 / 3 |
|---|---|---|---|---|---|---|---|---|---|
| R1 shorts c_ex ≥ 0.12 | CHECK | −1,137 | −659 | −790 | +132 | **1.36** | 23% | −0.071 → −0.062 | Y / **N** / Y |
| | T2 | −1,509 | −648 | −757 | +109 | 2.09 | 15% | −0.151 → −0.126 | Y / Y / Y |
| R2 shorts c_ex ≥ 0.10 | CHECK | −1,137 | −390 | −649 | **+258** | **3.09** | 13% | −0.071 → −0.057 | Y / Y / Y |
| | T2 | −1,509 | −450 | −587 | **+137** | **2.98** | 10% | −0.151 → −0.118 | Y / Y / Y |
| R3 any side c_ex ≥ 0.12 | CHECK | −1,137 | −472 | −628 | +157 | **1.33** | 37% | −0.071 → −0.050 | Y / **N** / Y |
| | T2 | −1,509 | −378 | −512 | +134 | 2.35 | 10% | −0.151 → −0.104 | Y / Y / Y |
| R4 shorts $100+ and stop < 100 bp | CHECK | −1,137 | −863 | −953 | +90 | **1.17** | 33% | −0.071 → −0.071 | Y / **N** / Y |
| | T2 | −1,509 | −944 | −1,059 | +114 | 2.22 | 12% | −0.151 → −0.144 | Y / Y / Y |

Rule-book avg R without its best day (CHECK / T2): R1 −0.084 / −0.136, R2 −0.090 / −0.131, R3 −0.072 / −0.110, R4 −0.089 / −0.152. The book is negative throughout, so there is no positive best-day share to report.

**LR8 view (rule book vs base):**
| Rule | CHECK | T2 |
|---|---|---|
| R1 | −168 vs −401 | −436 vs −1,089 |
| R2 | −112 vs −401 | −271 vs −1,089 |
| R3 | −81 vs −401 | −295 vs −1,089 |
| R4 | −428 vs −401 (worse) | −768 vs −1,089 |

**FIT** (not judged): the gain vs random is near zero or negative for R1, R2 and R4 (−9 / +24 / −14), and +399R for R3 (t 1.08). FIT does not support the CHECK and T2 gains.

**Cost or selection?** (decomp.csv: candidate lots, kept vs removed, 7 real setups)
- On CHECK the removed lots have the same or better gross R than the kept ones. For example, under R2 kept lots have gross +0.048 and LIVE-L cost 0.086, while removed lots have gross +0.040 and cost 0.130. So on CHECK the gain is the modelled cost alone.
- On T2 the removed lots also have worse gross R (−0.010 vs +0.045).
- The RND pools gain too (R2: CHECK +34 / +37R, T2 +25 / +19R). That fits cost being a real per-trade drag. It is not evidence that the setups select better trades.

**Per-setup effect** (avg R per trade, base → rule, with gain vs random in R in brackets; "—" = not touched):
| Setup | R1 CHECK | R1 T2 | R2 CHECK | R2 T2 | R3 CHECK | R3 T2 | R4 CHECK | R4 T2 |
|---|---|---|---|---|---|---|---|---|
| L3-fromopen | −0.099→−0.079 (+80) | −0.127→−0.107 (+61) | −0.099→**−0.062 (+170)** | −0.127→**−0.050 (+121)** | −0.099→−0.079 (+77) | −0.127→−0.107 (+57) | −0.099→−0.076 (+95) | −0.127→−0.139 (+9) |
| RW3 | −0.090→−0.075 (+33) | −0.142→−0.113 (+10) | −0.090→−0.044 (+41) | −0.142→−0.157 (−3) | −0.090→−0.075 (+34) | −0.142→−0.113 (+13) | −0.090→−0.089 (+17) | −0.142→−0.130 (+14) |
| RW5 | −0.093→−0.083 (+23) | −0.178→−0.139 (+21) | −0.093→−0.048 (+36) | −0.178→−0.147 (+6) | −0.093→−0.083 (+22) | −0.178→−0.139 (+15) | −0.093→−0.107 (−13) | −0.178→−0.189 (−10) |
| NM-ETF | — | — | — | — | −0.028→−0.027 (+0) | −0.108→−0.099 (+2) | — | — |
| G05 | +0.017→+0.016 (−5) | −0.072→−0.076 (−4) | +0.017→+0.042 (+18) | −0.072→−0.089 (−8) | +0.017→+0.016 (−5) | −0.072→−0.076 (−4) | +0.017→+0.013 (−12) | −0.072→−0.078 (+5) |
| G07 | −0.028→−0.021 (+1) | −0.198→−0.129 (+21) | −0.028→−0.046 (−7) | −0.198→−0.057 (+21) | −0.028→−0.021 (+1) | −0.198→−0.129 (+21) | −0.028→−0.034 (+2) | −0.198→−0.156 (+97) |
| G37 | — | — | — | — | −0.083→−0.015 (+28) | −0.152→−0.072 (+29) | — | — |

How many setups improve vs random on both splits:
| Rule | Improve / touched | Worst change in avg R per trade vs base |
|---|---|---|
| R1 | 4/5 | −0.004 |
| R2 | **2/5** | −0.018 |
| R3 | 6/7 | −0.004 |
| R4 | **3/5** | −0.014 |

Share of candidate lots each rule removes (CHECK / T2):
| Rule | L3 | RW3 | RW5 | G05 | G07 | G37 |
|---|---|---|---|---|---|---|
| R1 | 9% / 18% | 56% / 78% | 62% / 82% | — | 59% / 76% | — |
| R2 | 32% / 39% | 80% / 91% | 84% / 93% | 66% / 74% | 84% / 92% | — |
| R3 | as R1 | as R1 | as R1 | — | as R1 | 57% / 79% |
| R4 | 4% / 5% | 34% / 51% | 37% / 51% | — | — | — |

At these levels the RW-family filters are close to switching those setups off. That is the "too broad" side of the owner's remedy rule.

**Verdict per pre-registered bar:**
| Rule | Fails | Notes |
|---|---|---|
| R1 | bar 2 on CHECK | |
| R2 | bar 4 (per setup) and bar 5 (live contradiction) | Bars 1–3 hold on both splits, so → **LEAD** |
| R3 | bar 2 on CHECK | Everything else holds |
| R4 | bar 2 on CHECK and bar 4 | |
| R5 | live only | LIVE-L gain −52R, t −0.88; realised +56R, t 0.74, best-day share 92%: no lead |
| P6, post-hoc: shorts only in ETB-always names | history | Worse than random: CHECK −80R, t −1.45; T2 −54R, t −2.34. The live ETB-marginal gap does not replicate on history (labels are 2026 snapshots applied to history: anachronistic) |

## 4. Live replay (non-Graveyard current setups, assignments.json 11-27; no slot refill; LIVE-L in-sample)
| Rule | Share skipped | Kept vs all avg R (LIVE-L) | Gain vs random LIVE-L (t, best-day share) | Gain vs random on fills (t) | Setups touched / improve / worse | Flips to positive (of which ≥ 20 kept trades) |
|---|---|---|---|---|---|---|
| R1 | 16% | −0.192 vs −0.197 | +162R (1.90, 18%) | +175R (1.94) | 68 / 39 / 26 | 7 (5) |
| R2 | 30% | −0.2005 vs −0.1967 | +89R (1.11, 33%) | +121R (1.47) | 81 / 50 / 24 | 9 (1) |
| R3 | 33% | −0.180 vs −0.197 | +244R (**2.56**, 16%) | +225R (**2.39**) | 109 / 60 / 44 | 13 (7) |
| R4 | 8% | −0.193 vs −0.197 | +137R (2.25, 23%) | +161R (2.58) | 62 / 38 / 23 | 8 (6) |
| R5 | 15% | −0.197 vs −0.197 | −52R (−0.88) | +56R (0.74, 92%) | 80 / 38 / 39 | 7 (2) |

**Flips with at least 20 kept trades** (LIVE-L avg R per trade, all → kept; `1 day` = avg R without the best day ≤ 0):
| Setup | Account | Rule | Trades (all → kept) | Avg R (all → kept) | Avg R w/o best day | Best-day share | Note |
|---|---|---|---|---|---|---|---|
| NS4-pm-vwap-reclaim-oversold-short-FD | Testing F | R4 | 57 → 37 | −0.049 → **+0.202** | +0.100 | 56% | the only flip whose avg w/o best day stays > 0 with ≥ 20 trades |
| NS4-pm-vwap-reclaim-oversold-short | Testing D | R1/R3 | 55 → 20 | −0.118 → +0.165 | −0.026 | | `1 day` |
| NS4-pm-vwap-reclaim-oversold-short-FD | Testing F | R1/R3 | 57 → 23 | → +0.159 | −0.006 | | `1 day` |
| GEN-261026-05-Ret15mATR…OPEN-hold-short | Testing E | R1/R3 | 95 → 32 | −0.545 → +0.181 | −0.655 | | `1 day` |
| MF3-open-flowsell-rsi5hi | Testing C | R4 | 93 → 49 | → +0.100 | −0.026 | | `1 day` |
| MF4-h40-open-flowsell | Testing A | R1/R3/R4 | 87 → 71–79 | → +0.001 | | | flat |
| NM-MF3-qqqdn-gapdn-FD | Testing A | R2 | 84 → 40 | −0.010 → +0.142 | +0.040 | 76% | `1 day` |
| NM-MF3-qqqdn-gapdn-FD | Testing A | R4 | 84 → 68 | → +0.039 | | | `1 day` |
| orb20_a | On Deck | R3 | 38 → 30 | → +0.050 | | | `1 day` |
| CWT12-flag-s1-long | Testing C | R3 | 32 → 17 | → +0.227 | +0.268 | | fewer than 20 kept trades |
| GEN-261029-01-ORBfailUp… | Setup Generator | R3 | 119 → 61 | → +0.036 | | | `1 day` |

All other flips have fewer than 10 kept trades (listed in live_setups.csv).

**Primary setups (live, LIVE-L avg R per trade, all → kept):**
| Setup | All | R1 / R3 | R2 | R4 |
|---|---|---|---|---|
| L3-fromopen | +0.079 | +0.132 | +0.161 | +0.091 |
| RW3 | +0.047 | +0.152 | +0.274 (65 trades) | +0.123 |
| RW5 | +0.043 | +0.066 | +0.315 (36 trades) | +0.051 |
| NM-ETF | −0.126 | unchanged (−0.136 under R3) | unchanged | unchanged |

These live records were already `1 day` per primshorts_1126.

**Rule changes inside the live window** (research/ledger.jsonl; they bear on cost and on which trades were taken):
- 10-14 to 10-23: many promotions, demotions and Graveyard moves, including L3-fromopen into Primary on 10-21, out on 10-22 and back on 10-30.
- 10-23: setup stop-latch.
- 10-28: Primary position size 4k/5k.
- **10-30: Testing cost filter cf 0.15** (Testing trades after 10-30 were already pre-filtered on LR8 stop cost).
- 11-12: LR2/LR3/LR8 cost-R basis, plus GEN and Graveyard sizing caps.
- 11-17: TSZ1 testing sizing.
- 11-19: C3 epoch, DQ-P3 LR8 basis, **U9 ETB borrow list**.
- 11-21: QA cost-basis fix.
- 11-23: burst brake.

The live window mixes these regimes. The spread caps ("spread N bps > max", "spread is X% of stop") truncate the live spread bands.

## 5. Read (optimistic, honest)
- Cost-zone filtering is directionally right almost everywhere:
  - every rule raises book R vs base on CHECK and T2, on both LIVE-L and LR8 (except R4 on LR8 CHECK);
  - most rules beat a random cut on T2;
  - R3 and R4 beat it live on realised fills (t 2.4–2.6).
- What stops a pass:
  1. CHECK significance for R1, R3 and R4 (t 1.2–1.4).
  2. On CHECK the gain is modelled cost only: gross R is unchanged.
  3. The RW and GEN families lose most of their lots, so the filter acts like an off-switch, not a targeted remedy.
- The useful, targeted part is **stop width**: shorts with stops under 50 bp cost about 0.19R and net −0.34R live (t −4.7). A width floor or a LIVE-L stop-cost cap (R3 at 0.12 is the practical form) is the remedy candidate worth a forward test.
- The cost model itself needs a spread term and an opening-short term (LIVE-L v2) before further cost-zone work.

## 6. Backlog proposal (LEAD, not a pass; for the synthesis step to decide)
`{"id": "LIVEL-CAP12", "kind": "filter", "status": "lead", "rule": "skip any signal whose pre-trade LIVE-L cost estimate c_ex (primshorts_1126 cells, fixed exit-kind weights 0.357/0.283/0.360) is >= 0.12R; replaces nothing yet (runs beside the LR8 cost filter cf 0.15)", "evidence": "research/shortcost_1127: T2 +134R vs size-matched random (t 2.35), live realised +225R (t 2.39), 6/7 setups improve, worst -0.004R/trade; CHECK +157R t 1.33 (fails); history book still negative", "next": "re-test with LIVE-L v2 (spread + opening terms) fitted on live through 11-25 and scored on live 11-26 onward + CHECK; per-setup report; consider a stop-width floor (< 50 bp shorts) as the narrower form", "configs_lineage": 6}`

Scripts (this folder):
| File | Contents |
|---|---|
| sc_common.py | c_ex, the rules, t statistics |
| sc_live.py | live map and live replay → live_map.json, live_rules.json, live_rules_real.json, live_setups.csv, live_out.txt |
| sc_hist.py | history books |
| sc_score.py | scoring against the bars → hist_score.json, hist_setups.csv, hist_skipshare.json, score_out.txt |
| sc_decomp.py | cost vs selection split → decomp.csv |
| sc_posthoc.py | P6 → posthoc.json |

Large inputs stay in scratch and are not committed.
