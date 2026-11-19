Educational only — not financial advice.

# ROOTCAUSE-1119 / stacking — is stacking the reason Primary lost -14.4R on 2026-11-19?

Research only: no config, setup, exit or order change. Data: live paper journals (run 1) of Primary (mcf-data), Testing 1/2 and the
other accounts (mcf-data-<key>), plus Primary's what-if run (signals not taken) and its poll logs (SPY path, open-position marks).
R = pnl_adj / (|entry-stop| x shares), LR8 costs in. The locked block (2024-11-01..2025-02-28) was not read. Scripts:
`/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/stkcode/` (a1-a5.py, rem.py).

**Cluster** = entries by one setup, same side, same account, chained within 30 min. **Burst** = the same, chained within 2 min.

## Verdict (plain English)
- **Stacking is not the root cause. It amplifies the setup's call, whichever way it goes.** On the winning setups, stacking is
  where the profit is made. Capping it would take away most of their R. The owner's view holds on the record.
- **What went wrong today was the call, not the count.** Both losing clusters were long-market bets made into a falling tape:
  - ST7 bought 7 tech/semis/crypto names in one minute.
  - L3 shorted SPXS and SQQQ. Shorting an inverse ETF is a long-index bet: it is the opposite of what this short fade is meant to do.
  - SPY then fell about 0.8% in 4 minutes (730.5 at 11:49 to 724.7 at 11:53). It hit 14 long-beta lots at once: 7 ST7, 6 L3 and IWN.
- **The one targeted failure mode found here:** short setups shorting inverse index ETFs (SOXS, SQQQ, SPXS, SDS, PSQ...).
  - Live record, all accounts: 127 trades, **-60.7R, avg -0.48R, win 29%**. Red on 16 of 22 days.
  - Excluding today: 98 trades, still -43.5R.

## 1. Clustered vs isolated trades (live, Primary all setups + ST7-FD / L3-fromopen-FD in Testing 1/2)
Nearly every trade of the active setups is part of a cluster (L3: 391 of 403). So the useful split is by cluster size.

| scope | singles: n / total R / avg | size 2-3 | size 4-9 | size 10+ | ICC of R inside clusters |
|---|---|---|---|---|---|
| L3-gap-slope-fromopen-FD | 12 / -2.8 / -0.23 | 36 / +0.2 / +0.01 | 66 / -9.3 / -0.14 | **289 / +93.3 / +0.32** (10 clusters) | 0.35 (391 trades ~ 90 independent) |
| ST7-rsi50dn-long-pm-t1s1-FD | 22 / -0.4 / -0.02 | 10 / +4.2 / +0.42 | **26 / -7.2 / -0.28** | none | 0.22 |
| RW3-FD + RW5-FD | 53 / +9.3 / +0.18 | 68 / -7.9 / -0.12 | 85 / +13.8 / +0.16 | 133 / +25.2 / +0.19 | 0.55 |
| all other Primary setups | 127 / -23.1 / -0.18 | 164 / -7.0 / -0.04 | 205 / -31.1 / -0.15 | **326 / -92.3 / -0.28** | 0.20 |

**Where the big wins come from.** All 10 of the best clusters had 9 to 80 lots:
- L3: 10-20 +33.6R (80 lots), 11-12 +30.2R (49), 10-29 +19.4R, 11-16 +16.4R, 10-26 +12.7R.
- RW3-FD: 10-22 +21.3R (21 of 21 won). RW5-FD: 10-22 +21.1R (24 of 24 won).
- MF2-FD: 10-22 +29.8R.

**Where the big losses come from.** Also big clusters, mostly on setups that have no edge:
- NS2 10-15: -27.3R. MF2-FD 11-06: -21.6R. MF4-FD 11-09: -17.1R.
- L3 (Testing 1) 10-15: -13.5R.
- ST7 today: -7.5R.

**Day level (setup-day R):**

| setup | days with a cluster of 5+ lots | days without |
|---|---|---|
| L3-fromopen-FD | 16 days, **+92.8R** (mean +5.8) | 9 days, -11.5R (mean -1.3) |
| RW3-FD | 7 days, +22.5R | 17 days, +1.5R |
| RW5-FD | 8 days, +10.2R | 17 days, +6.1R |
| ST7-FD | 3 days, -5.3R | 16 days, +1.9R |

**One-big-day check.** These records are carried by one stacked day each:

| setup / account | total | avg R w/o best day | best day, share of total R |
|---|---|---|---|
| L3 Primary | +31.65R | +0.005 | 11-12, **98%** (`1 day`) |
| L3 Testing 1 | +49.69R | +0.113 | 10-20, 68% (`1 day`) |
| RW3-FD Primary | +23.96R | -0.002 | 10-22, 101% (`1 day`) |
| RW5-FD Primary | +16.30R | -0.023 | 10-22, 121% (`1 day`) |
| ST7-FD Primary | -6.63R | -0.296 | n/a (total is negative) |
| ST7-FD Testing 1 | +3.18R | -0.072 | 10-12, 127% (`1 day`) |

So the edge of the winning setups lives in their mass-signal days. Without those days it is about zero.

**Clusters are mostly market-direction bets.**
- The correlation between a cluster's mean R and the SPY move in the trade's direction over its holding window rises with cluster size:
  - singles: +0.22
  - clusters of 2-4: +0.27
  - clusters of 5+: **+0.47**
- Clusters of 5+, split by what SPY did:
  - SPY moved with the trade: 38 clusters, +151.2R.
  - SPY moved against it: 43 clusters, -154.4R.
- So stacking sizes up whatever the setup's day-direction call is. It neither creates nor destroys edge.

## 2. Do the caps stop winning setups from capitalizing? (Primary what-if run)
- The per-setup cap (30 open lots) bound on one day only: L3 on 11-12. It skipped 648 signals, 135 of them distinct symbols.
  - First signal per symbol: **+101.2R gross**, avg +0.75, win 97%.
  - Live L3 averages 0.032R of cost per trade, so these are worth roughly +97R net.
  - This is a single day (100% share) and the fill model is optimistic. It is evidence for the owner's view, not proof.
- Other skips of L3 signals:
  - Lot cap: 65 signals, +4.1R gross.
  - Per-setup -2R latch: 69 signals, -8.5R gross, so the latch saved about 8R.
  - Not shortable/ETB: 1,986 signals. These are not tradable, so they say nothing about stacking.
- The L3LEASH lab (research/l3leash, 2 years) adds a caution:
  - L3's mass-signal days on SPY-up closes cost -242R (TRAIN) and -177R (VALID).
  - So raising the cap makes both tails bigger.
  - The owner's shadow test of a higher cap is the right instrument, not a live change.

## 3. Remedies tested (counterfactual: trades removed or resized on the live record, all accounts, run 1)

Removing a trade frees capacity, so these results are lower bounds.

| # | remedy (targeted at) | setup-accounts improved | setup-accounts worse | net |
|---|---|---|---|---|
| R-A | **No short of an inverse index ETF by any short setup** (a short that is really a long-index bet) | **39 (+73.3R)** | 14 (-12.6R) | **+60.7R** (126 trades) |
| R-A excl. 11-19 | same, without today | 35 (+54.7R) | 11 (-11.3R) | **+43.5R** (97 trades) |
| (info) | long setups buying inverse ETFs, removed | 22 (+37.3R) | 27 (-32.5R) | +4.8R (no signal: leave alone) |
| R-B1 | Burst of 4+ same-setup entries within 2 min, sized x 1/sqrt(n) | 113 | 52 (-244R) | +979R, but **fails** |
| R-B2 / R-B3 | 1/n sizing; 6+ threshold | same pattern | same pattern | **fail** |
| R-C1 | At most 3 open lots per account with the same index exposure (SPX/NDX/R2K/TECH ETFs, incl. inverse/levered) | 65 (+127R) | 29 (-56R) | +71R, **not targeted** |
| R-C2 | same with 5 lots | 42 (+79.5R) | 22 (-40.4R) | +39R, **not targeted** |

**Why the R-B burst sizing fails.** The net gain only comes from shrinking setups that lose anyway. It cuts every winner:
- L3: Testing 1 -21.3R, Primary -17.4R
- RW3-FD Primary: -15.7R
- RW5-FD Primary: -13.3R
- graveyard RW6: -29.5R
- graveyard NS2-FD: -25.5R

This is the "cap the stacking" remedy, and the evidence rejects it.

**Why R-C is not targeted.** It costs several winners:
- MF2-FD Primary: -8.3R
- RW5-FD Primary: -5.3R
- graveyard RW6: -8.0R

It is too broad by the Remedies rule.

**R-A detail:**
- Biggest gains:
  - L3-fromopen-FD Primary +10.6R
  - L3-fromopen-FD-WB4 Testing 2 +4.0R
  - L3-lowdist-FD Testing 1 +4.1R
  - exhaustion_short Testing 1 +4.2R
  - L3-rsi5hi-FD Primary +3.1R
  - RW3-FD Primary +2.1R
- Worst losses: graveyard heat_fade_short-FD -2.7R, livelab NM-RWR3 -2.1R. Nothing loses more than 2.7R.
- By symbol:

| symbol | trades | R |
|---|---|---|
| SOXS | 59 | -24.6 |
| SQQQ | 49 | -23.7 |
| SPXS | 9 | -7.3 |
| SDS | 3 | -3.3 |
| PSQ | 4 | -4.3 |
| TZA | 2 | +3.6 |

- **Status: live record only.** Not checked on the 2-year lab yet. It needs a lab check on the 2-year cache (inverse ETFs are in the universe) and a shadow run before it goes to the backlog. It is not a live change.

**Untested:**
- A factor-concentration check on same-minute bursts. ST7 today was 7 lots of one tech/crypto factor in one minute.
- ST7's record is too small to test it (58 trades, -3.4R live).
- ST7's issue is the setup itself: no live edge, and one burst carries the result. Stacking is not the issue there.

## 4. Today's numbers in this frame
- **ST7-FD**, entered 10:45-10:46:
  - The 7 names were already green at 11:19 (+0.13..+0.67R open, poll marks).
  - All were stopped in the 11:50 flush: -7.53R. IWN was entered at 11:55 and lost another -1.05R.
  - Taking one lot instead of seven would have cost about -1R. But the same rule would have cut 11-04 (+3.1R, 9 lots), and every winning L3/RW day.
- **L3-fromopen-FD**:
  - 6 shorts of SPXS/SQQQ (long-index). All stopped within one minute: -6.49R.
  - R-A would have removed all 6. It is not tailored to today: the same mode cost -12.3R on 11-02 (SOXS) and -6.7R on 10-19.

## Rule-change context (research/ledger.jsonl, effective dates inside the live window)
- 10-13: per-lot stacking, up to 3 lots per symbol, all accounts.
- 10-20: twin block, and a -2R per-setup stop in Testing.
- 10-20: L3 moved Testing 1 -> Primary. 10-22: back to Testing 1. 10-30: re-promoted to Primary.
- 10-23: the latch (LL-LATCH). ST-A switches the per-setup stop off in Testing 1/2.
- 10-27: ST7 promoted to Primary.
- 10-28: Primary sizing ~$4k per position; slots 160 -> 77; per-setup cap 100 -> 30.
- 10-29: Primary -2R per-setup latch (ST-P).
- 10-30: Testing cost filter (CF).
- 11-04: Testing 2 trades only the top-500 pool (UNI1).
- 11-05: low-rep homes go live (Explore 1 / Live Lab).
- Any cluster comparison across 10-28/10-29 mixes cap and latch regimes. L3's 11-12 is the only day the 30-lot cap bound.

## Configurations counted
- 1 cluster definition (30-min chain) and 1 burst definition (2-min chain), used for description.
- 8 remedy configurations: R-A, R-A excl-today, the info variant, R-B x3, R-C x2.
- All are reported above. No finalist is scored on a holdout.
