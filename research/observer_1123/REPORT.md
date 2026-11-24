# Big-move-day observer, 2026-11-23

Educational only — not financial advice. Paper accounts; R after costs (LR8 basis) unless said otherwise.

**Sources.** `log.jsonl` here: 5-min market + account snapshots 09:34-12:18 ET (observer stopped ~12:21; no snapshot 09:55-10:22).
The afternoon comes from the account journals (`mcf-data*` EOD 11-23, `cost_r_lr8`) and Alpaca 5-min / daily SIP bars
(GET only; reachable) -> `index_5min_vs_open.csv`. Primary is not re-analysed here; see `research/hardstop_1123/REPORT.md` Part 2.

**Rule changes in this window:** 11-20 stop rounding fix; 11-23 burst brake (BRAKE-BURST) live, ST7 out of Primary,
PSHADOW start, CWT05 + GEN-261027-06 to the Graveyard. 11-23 results are the first session under the burst brake.

## The market path: the whole move was in the gap

| | gap (open vs prev close) | open -> close | day low vs open | close vs prev |
|---|---|---|---|---|
| SPY | +5.01% | −0.27% | −1.2% 09:35 (high +0.4% 10:35) | +4.73% |
| QQQ | +7.81% | −0.78% | −1.7% 09:35 | +6.97% |
| NVDA | +33.1% | −1.11% | −5.4% 09:35 | +31.6% |
| SMH | +17.3% | −1.95% | — | +15.0% |
| IWM | +3.67% | −0.10% | — | +3.56% |
| VIXY | −14.2% | +0.72% | — | −13.6% |

After an opening dip (09:35) the indexes recovered to the open by 10:15-10:35 and then went sideways in a ~1% band all
day, closing slightly below the open. It was a huge **gap-and-hold** day, not a trend day: nothing intraday paid for
being long "with the move".

## Accounts (final, journals)

| account | trades | R | long R (n) | short R (n) | before 11:00 / after |
|---|---|---|---|---|---|
| Testing A | 120 | **+26.4** | +9.4 (16) | +17.0 (104) | +21.2 / +5.2 |
| Testing E | 432 | **+23.1** | −10.5 (335) | +33.6 (97) | +26.3 / −3.2 |
| Graveyard | 267 | **+18.4** | −23.1 (168) | +41.4 (99) | +31.4 / −13.0 |
| Setup Generator | 22 | +10.4 | −0.7 (5) | +11.1 (17) | 0 / +10.4 |
| Testing D | 136 | +7.1 | −0.9 (26) | +8.0 (110) | +4.6 / +2.5 |
| Testing C | 53 | +4.9 | +3.5 (15) | +1.4 (38) | −2.6 / +7.5 |
| Testing F | 75 | +2.1 | +7.0 (19) | −4.9 (56) | +0.2 / +2.0 |
| **Primary** | 24 | **+0.49** (+$185.38) | +3.0 (6) | −2.5 (18) | +2.3 / −1.8 |
| On Deck | 50 | −3.0 | +0.9 (4) | −3.9 (46) | −1.3 / −1.7 |
| Testing B | 53 | −6.4 | −8.2 (36) | +1.8 (17) | +1.9 / −8.3 |
| **All** | 1,232 | **+83.5** | −19.6 (630) | **+103.1 (602)** | |

No account halted; no data-stale polls. Latches: Primary L3-fromopen and RW5 (see below); Graveyard 6 setups
(GEN-261021-06, GEN-261022-01, GEN-261027-05, NS5-sma50-flush, RW3S, ST1-ordn).
In the morning (observer) the lab accounts sat on 30-130 open lots each from 10:22; Graveyard's open count jumped
89 -> 155 between 11:28 and 11:48 (a 31-entry burst at ~11:45).

**Primary** (verified: 24 trades, +0.49R, +$185.38; intraday curve peak +5.3R 12:48, low −4.06R 14:25):
RW3 +3.61 (6, 5 wins), NM-ETF +3.00 (6/6: inverse-ETF dip buys at 14:05-15:00), RW5 −3.35 (7, latched), L3-fromopen −2.77
(5, latched). All 18 shorts were in names that gapped **down** against a +5% index (defensives: CL, CHD, UNH, KMB, VTR,
PLMR) — Primary was short the day's rotation laggards, which rebounded at midday (the BDI Move Hunt long movers). Reused
from hardstop_1123 Part 2: shorts entered after 11:00 −4.84R (mostly 11:30-13:10), 10 of 18 shorts flattened 15:55 for
−2.57R, not a pile-on.

## Who fought the move, who rode it (all accounts, identical signals once)

- **Shorts made the day: +103.1R on 602.** The winners were shorts in names that gapped **up** hard, i.e. fading the gap:
  gap > 10% +115.1R (276, +0.42R avg), 5-10% +7.8R, 2-5% +7.8R. Shorts in flat / gapped-down names lost
  (gap ≤ 0: 100 trades −12.7R; 0-2%: 44 −14.8R). Best: GEN-261022-08 short (Graveyard) +36.0R, GEN-261026-05 (Testing E)
  +19.6R, NS3V1-am-widestop (Testing A) +17.4R, NM-RWN5-WB3 (Testing E) +11.3R, GEN-261023-06 (Gen) +11.1R.
- **Gap-up longs fought the tape: 535 longs in gapped-up names −64.3R**, graded by gap size (2-5% −0.05R avg, 5-10% −0.17R,
  > 10% −0.22R). The brief's −44.5R / 364 lots is the three named gap-continuation setups (verified: ULT-05-withgap-cont-long
  310 −20.51R, all time stops; GEN-261021-06 ORBfailUp-Gapge1p2 51 −22.03R, latched; BEG-GNG 3 −1.93R).
- **Longs in gapped-down names rode the rotation: 66 trades +40.6R** (NM-AR gap-down capitulation +8.0R,
  GEN-261020-01 +11.9R). Note IGR1 (the same idea as a rule) failed 0/8 on two years last night — on its own it is a beta bet.
- **Exits:** 15:55 flatten +72.9R (470 lots; shorts +64.3R) — the gap fades were held to the close and paid; long time
  stops −20.2R (320).
- **Worst minutes:** entries at 11:20 (48 lots −17.1R), 10:05 (34, −12.0R), 10:40 (54, −11.8R); exits at 10:20 −11.6R,
  10:30 −11.1R, 11:15 −10.9R. Best entry bursts 10:25 (69, +23.1R) and 10:30 (49, +32.5R).

## Skips and brakes (reused from `research/ops/blocked_audit.md`)

- Burst brake (first day) skipped 293 entries, −46.4R gross / **−56.6R net saved** (Graveyard 78 GEN-261021-06, Testing E 147
  ULT-05 long, Testing D 65 GEN-261029-06, Testing A 3). It caps the rate, not the day: ULT-05 still took 310 lots.
- ETB / not shortable was the biggest skip in most accounts (On Deck 179, Testing F 104, Primary 49). Spread skips peaked in
  Testing E (196) and Graveyard (62) on the open; cost-filter skips 11-35 per account.
- **PSHADOW 0 shadow trades is genuine:** all 28 shadow signals were on inverse / levered ETFs with no borrow; the same shadow
  run entered 36 shorts on ordinary names, so the ETB list reaches the shadow path. No fix needed.

## Lessons

1. **What was knowable at 09:50:** SPY gap +5.0%, QQQ +7.8%, VIXY −14%, and by 09:50 SPY −0.7% / QQQ −1.4% / SMH −2.8% / NVDA
   −1.4% *below their opens*, i.e. the gap was not extending. (Breadth was not in the observer log.)
2. **How rare:** SPY gap ≥ +2% on 22 of 2,739 sessions since 2016 (all since 2020; 6 since 2024), ≥ +3% on 10, ≥ +4% on 2
   (2020-03-24 +5.3%, 2026-11-23). ≥ +1.5%: 44; ≥ +1%: 124. In the live record (since 10-06) only 11-04 (+1.15%) and 11-23 qualify.
   On SPY ≥ +2% gap days the open -> close median is +0.10% (50% close above the open): no direction to lean on, so a
   "big-gap day" rule must target the failure mode, not bet the index.
3. **The targeted failure mode is gap-continuation longs whose gap is index beta.** That is exactly the open backlog idea
   `nightly-1123-index-gap-residual-gap` (residual gap = stock gap − beta × index gap, index-gap days only, all gap-up long
   setups pooled, per-setup improve / worse counts). Tonight's graded numbers were added to its notes; no new entry
   (the gap-down long side is IGR1, already parked). The short side needs no remedy: gap-fade shorts carried the day.
4. Too few such days live (2) to judge any setup on them; any study uses the 2-year 1-min lab with costs in.

Files: `log.jsonl` (observer), `index_5min_vs_open.csv`, `profitable_setups_1123.{png,csv}` (separate table refresh).
