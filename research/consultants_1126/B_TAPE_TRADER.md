Educational only — not financial advice

# Consultant B (tape trader): steering Primary's short book with the tape, and longs that hedge it (2026-11-26)

Research memo only: no config, no ledger, no backlog edit. Live figures are **paper**, LR8 R after costs, identical signals across accounts counted once (`footrace.live_trades` logic + entry times from the 10 journals), 39 sessions 10-01..11-25 with SPY marks from `mcf-data-compass` (`cond_obs.csv`, 10-min; `compass/<date>.csv`, VWAP/breadth from 11-06 only). Day labels "up/down/quiet" use the close and are **hindsight**; every steering cut below uses only the SPY mark at entry.
**Looks taken here: ~14 descriptive cuts on live trades + 1 trigger-frequency count on the 2-year SPY marks (no outcomes read). All in-sample, hypothesis-generating only.** Locked block 2024-11-01..2025-02-28 filtered out, never read.
**Rule changes inside the window (ledger):** 10-28 Primary sizing, 10-29 −2R latch, 11-11 TEAM-6, 11-12 LR8 + restructure, 11-17 TSZ1 half lots, 11-19 C3 Epoch 1, 11-20 stop rounding, 11-23 ST7 out + burst brake. R is LR8-recomputed throughout, so costs are on one basis, but lineups and lot sizes change across the window.

## Bottom line first
- Primary is not a strategy book, it is a **short index position with stock-picking noise on top**. 11-25: 30 shorts / 0 longs at 11:39, −19.6R per +1% SPY; 72% of the −48.5R swing was beta. Across all accounts, daily short R vs daily long R correlate **−0.63** (36 days). The testing longs are the same tape bet with the opposite sign: all longs −0.183R/trade (n 16,117); all shorts −0.155R (n 14,805). Netting two losing tape bets lowers variance, it does not make money.
- The "+256R of longs" on 11-25 is a one-day record. GEN-261027-10: +0.145R (174 tr) but **−0.427R on its other 76**; GEN-261023-07 +0.571R (121) but **−0.297R on its other 73**; GEN-261022-01 −0.391R w/o 11-25 (265). Both lunch GENs are just "breadth_open > 0.65 / breadth > 0.7" longs — i.e. already compass-gated, and still negative off the V-day.
- MCF's own research says the compass reads **where the day stands** (|SPY fo| ≥ 0.30% at a checkpoint holds its side to the close 89/89/97%), not **where it goes** (next 30-120 min ≈ 50%). So steering must (a) stop trading against a state that is already decided, and (b) **hedge beta** when the book is one-sided — not forecast the afternoon. The breadth close-gate (0/12) and the L19 / VRL / leaders flips already prove forecasting fails here. I agree.

## 1. What makes fades bleed and dip-buys pay — observable signals and when they are knowable
| Signal (point-in-time) | Short fades bleed when… | Longs pay when… | Knowable |
|---|---|---|---|
| SPY gap vs prior close | Index gap ≤ −0.75% (beta gappers flood the gap-down list; gap-fill risk) | Same day, once the gap starts filling | 09:30 |
| Stock **residual** gap (gap − β60 × SPY gap) | Raw gap is mostly index (no catalyst, fills with SPY) | — | 09:30 |
| Opening drive (09:30-10:00) | Early low that is bought straight back (11-25: −0.90% at 09:44, flat by 10:00) — it is information, not a trigger | — | 10:00 |
| First-hour range vs 20-day avg; which side breaks | Narrow IR, then range expansion up after 11:30 | IR high taken with breadth | 10:30 (break: any time) |
| SPY vs open and VWAP, 30-min checkpoint state | SPY in ±0.30% of open after 11:30 (chop/transition) or back above VWAP after a ≥0.4% dip | SPY not ≤ −0.30% after 11:30 | 10:30, every 10-30 min |
| Breadth (share above VWAP / above open), sector ETFs up | breadth_vwap jumps from ≤ 0.40 to ≥ 0.70 in 30 min, sector_up ≥ 8/11 (11-25: 0.34 → 0.72 → 0.93, 11:45-12:15) | Same, and breadth_open ≥ 0.65 | 15-min marks |
| QQQ / IWM agreement | IWM green while SPY red (11-18, 11-24): shorts are being squeezed in small caps first | IWM leads the turn | any mark |
| VXX / UVXY intraday | Vol ETPs roll over from the morning high while SPY is still red (11-25: the 12 inverse/vol ETPs were decided ~11:50) | Same | any mark (not recorded yet) |
| Time of day | 11:30-13:00 lunch turns: trio entries 11:30-13:00 −0.462R (n 1,421; **+0.059 w/o 11-25**) | Afternoon trend after a decided state | clock |
| Calendar | Pre-holiday / holiday-week short covering (11-25 = day before Thanksgiving) | same | pre-open (anecdotal, untested) |

## 2. MCF's live record against day types (labelled samples; trio = L3 + RW3 + RW5, all accounts unless stated)
- **RW3 / RW5 are down-tape shorts.** Primary, hindsight day type: RW3 down +0.513R (94 tr, 11 d) / up −0.328R (76, 9); RW5 down +0.347R (77, 11) / up −0.355R (81, 10). Point-in-time, entries ≥ 11:30: RW3 with SPY ≤ −0.30% **+0.238R (n 126)**, in ±0.30% chop −0.229R (104); RW5 +0.240R (74) vs +0.127R (70).
- **L3 is not a down-day setup; it is a relative-weakness setup that dies on index gap-fill days.** L3 (all accounts) flat-gap days +0.209R (205), SPY-gap ≤ −0.75% days excl. 11-25 **+0.286R (294, 5 days)**, but 11-25 alone = 1,367 trio lots (vs 5-252 on the other big gap-down days) and −1,099R: the raw-gap filter flooded with beta gappers.
- **Shorting relative weakness early on an up tape works**: trio entries < 11:30 with SPY ≥ +0.30% **+0.325R (n 328, 13 d; +0.241 w/o best day)**. So "no shorts on up days" would cut winners — consistent with GATE1 and the gap-up studies.
- **Trio after 11:30 with SPY ≥ +0.30%:** −0.565R (1,596) but **+0.050R w/o 11-25**. The live record has exactly one big V-day; it cannot prove an "UP afternoon → stop shorting" rule. Do not build on that cut.
- **Shorts in midday chop bleed:** all short setups, entries ≥ 11:30 with |SPY fo| < 0.30%: −0.196R/trade w/o 11-25 (n 1,768), day-mean −0.311R t −3.65 (24 d); **31 of 41 short setups worse** than in trended states (median −0.29R). Trio only: −0.265R/day, t −2.08 (19 d).
- **Dip-buys into a down afternoon bleed:** all long setups, entries ≥ 11:30 with SPY ≤ −0.30%: −0.355R (n 2,305), day-mean −0.226R t −2.43, 10 of 14 days red, **26 of 34 long setups worse** (median −0.195R) vs −0.071R/day elsewhere. NM-ETF in Primary: down days −0.304R (30 tr, 6 d), and it buys inverse ETPs too (on 11-25 those lost).

## 3-4. Steering rules (exact thresholds; mechanism / what kills it / how it differs / test)
Marks = last closed 10-min (or 5-min) SPY bar; fo = % from the 09:30 open; breadth as `compass_live` records it.

**S1 Down-tape long brake (top pick; a targeted remedy).** From 11:30, no new **long-beta** entry in any long setup while SPY fo ≤ −0.30%. Inverse / long-vol ETPs count as short-beta (not braked; they are the inverse-guard's job). Mechanism: once a checkpoint is ≥ 0.30% red after 11:30 it stays red ~89%; dip-buys there are catching a trend. Kills it: V-days (it would have blocked 11-25's 11:35-11:55 long movers) — that cost is exactly what S3 pays back. Differs from GATE1 (pooled both sides, all trades; with-minus-against had the wrong sign on VALID) and TT1 (a turn-on gate needing a reclaim): S1 is long-side only, one condition, after 11:30 only. Live evidence above (t −2.43, 14 days).

**S2 Midday-chop pause for the fade family.** From 11:30, no new L3 / RW3 / RW5 entry while |SPY fo| < 0.30% (RW3/RW5 keep firing when SPY ≤ −0.30%; L3 keeps its morning). Mechanism: no tape behind the fade, and chop near the open is where the turn happens. Kills it: GATE1's warning — "trade less of a losing book" looks good on RAW; it must also be ≥ 0 on the zero-expectancy (Z) book. Live: day t −3.65 (all shorts), 31/41 setups worse.

**S3 Gap-fill hedge trigger (the 11-25 rule).** Fires once, 11:30-13:30, when **all** hold on a closed 5-min bar: SPY traded ≤ −0.40% from its open at some point after 10:30; SPY closes ≥ session VWAP + 0.10%; breadth_vwap ≥ 0.70; ≥ 8 of 11 sector SPDRs above their open; Primary net beta ≤ −8R per +1% SPY. Action: (a) open H1 sized to bring net beta to −4R/1%; (b) no new fade-family shorts for the rest of the day; open shorts untouched (exit studies say holding beats cutting). 11-25: fires ~12:00 (VWAP +0.22%, breadth_vwap 0.715, sector_up 8/11, beta ~−19R) — in-sample, one day. 11-18 (breadth_vwap 0.805 at 12:30 but sector_up 7/11) and 11-23 (10:30, before the floor) do not fire. Differs from R2 squeeze exit (fired at 10:04 on the first V, closed every short, no breadth/book/time conditions) and from nightly-1015 gap-down reclaim veto (pure veto, 0/5, lowered exp in all 5): S3 **adds a hedge** and only freezes new shorts. Kills it: false V's (the dip resumes) — the hedge stop caps that at −1R of hedge size. Rare: ~32 proxy fires in 471 sessions (VWAP proxied by the open; ~7 when also gapped ≤ −0.5%), so it is insurance, judged on book tails, not t.

**S4 Hedge, don't block (variant of NETBETA-B8, the only remedy that passed).** When B8 binds (|net beta| > 8R/1%), buy the index (H1 mechanics, no trigger) for the excess instead of refusing the next short. Mechanism: B8's RAW gain came from trading a losing book less (Z −154R/yr, all 3 shorts worse); a hedge keeps the shorts' stock-specific edge and sells only the beta. Kills it: if the trio's residual (beta-stripped) edge is ≤ 0 the hedge just adds costs. Test vs B8 on Z.

**S5 L3 residual-gap filter.** L3's `gap_le −2.657%` measured on residual gap = gap − β60 × SPY gap (extends backlog `nightly-1123-index-gap-residual-gap`, written for gap-up longs, to the gap-down shorts). Kills it: on normal days it changes nothing; it only matters on |SPY gap| ≥ 0.75% days (~6 live). Report lots removed per day.

## New hedge longs (entries ≥ 09:50, flat 15:55)
**H1 Index gap-fill reclaim long (SPY; IWM as config 2).** Trigger: first closed 5-min bar 11:30-13:30 with SPY ≥ VWAP +0.10% after SPY was ≤ −0.40% from its open after 10:30, breadth_vwap ≥ 0.70 (S3 without the book clause; config 1b adds SPY gap ≤ −0.50%). Entry: next bar open. Stop: session low since 10:30 − 0.05%, capped at 0.60% below entry. Target: prior close (gap fill) if gapped down, else none; trail 1R once +1.5R; flat 15:55. 1 trade/day. Size: 1R in research; in Primary sized by S3. Why it hedges: it exists only on the afternoons the short book is squeezed. VRL's own control (every liquid name at the reclaim, +0.088R, t 1.30) says the edge after a V is the index, not the names — so trade the index, cheaply (1-2 bps cost, no borrow, no spread filter). Kills it: failed reclaims on trend-down days (11-18 type).

**H2 Trapped-short gap reclaim long (stock).** Universe: the L3 candidates (gap ≤ −2.66%, ADV20 ≥ $95M, ETB not needed). Trigger 10:30-14:30: stock traded ≥ 0.50 daily ATR below its open, then a 5-min close **above its own open** with SPY ≥ its VWAP at that bar. Entry next bar open; stop = session low (cap 0.50 daily ATR; skip if < 0.15 ATR); target = prior close; else flat 15:55; first signal per symbol-day, max 10 names/day. Mechanism: the gap-down fade failed in that name; faders (MCF included: AADX, LBRT, AXON, INIO, RUN on 11-25) cover into the prior close. Prior art to beat, honestly: R05 gap-fill long (128 configs, +0.010R, up +0.387 / flat −0.136 — a tape bet) and L19 (stopped names, −0.120R). H2 differs by the stock's own open reclaim **plus** the SPY-above-VWAP condition and the L3-only universe; if it does not beat R05's base and a same-minute random L3-universe long, park it. Not proposed: a breadth-thrust long (GC thrust failed 0/3 as a close-gate) and 09:35 open-drive longs (Team E, 0/12).

## How to test (house rules)
- **Pre-register one PREREG.md, hashed before any score**, 10 configs: S1, S2, S3+H1, S4, S5, H1 (1, 1b, IWM), H2 (2: target prior close / hold). Cumulative N ≈ 2,269 → ≈ 2,279; bar per BAR90 at that N. No tuning of 0.30 / 0.40 / 0.70 / 8R.
- Engine: neveragain minute engine + bench10 lots, Primary P4 lineup and book rules, LR8 + borrow + tod cost multipliers; FIT 170 / CHECK 276 / T2 (2023-24, breadth from `build_breadth.py`, sector ETFs from cache); locked block filtered at the read and asserted. H1/H2 scored standalone (after costs, w/o best day, best-day share, day t) **and** as book add-ons.
- Pass bars: S1/S2/S5 — CHECK and T2 dR > 0 on RAW **and** on the Z book, per-setup improve/worse counts with R (remedy rule), best day < 50%. S3/S4/H1 — insurance bar from squeeze_1125: worst-5 and days ≤ −10R better on CHECK and T2, avg day not worse, Z cost reported. H2 — standalone ≥ +0.03R after costs on CHECK and T2 and beats both controls.
- Anything that passes: journal-only shadow tags in Primary + Testing 1/2 for 20 sessions (no trade changes, no playing time cost), then ledger entry + `python -m mcf.research.ledger check`, skeptic review, change outside 09:30-16:00 ET.
- Record VXX/UVXY fo and IWM-minus-SPY in `compass_live` as LEARN inputs now (recorded only, not votes) so the next round can test the vol-rollover signal on real marks.

## What earlier MCF work already rejected, and where I differ
- R2 squeeze exit fired at 10:04 on the first V → S3 has an 11:30 floor, a post-10:30 dip, breadth + sector + book clauses.
- Breadth close-gate 0/12 ("midday breadth does not forecast the afternoon") → S3/H1 use breadth as confirmation of a reclaim that already happened, and act by hedging beta, not by forecasting; judged as insurance.
- TT1 / NM-ETF+TT1 "mostly a tape bet" (2023-24 −0.031) → agreed; S1 is a brake, not a turn-on, and H1 trades the tape openly in the index instead of dressing it up as stock selection.
- Regime / direction gates 0/74, 0/112, GATE1 0/112 → S1/S2 are one-sided, after-11:30, ≤ 1 config each, and must pass Z.
- L19, VRL, leaders-on-reclaim: the names add nothing over the index after a V → H1 is the index; H2 must beat R05 + random.
- Gap-up-day protection 0/67 → not attempted; early relative-weakness shorts on up tapes are the trio's best cell.
- Do not promote the 11-25 V-buyers (GEN-261027-10, GEN-261023-07) to Primary on that day: −0.43 / −0.30R off it.

Educational only — not financial advice
