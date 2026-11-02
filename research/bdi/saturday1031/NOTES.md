# BDI Saturday deep run 2026-10-31 (week 10-26..10-30)

*Educational only — not financial advice. Live numbers are **paper** trades (rule 7), costs in (journal `pnl_adj`,
R = pnl_adj / $ risk). History numbers are **backtests** on the open two-year history with production costs. The locked
block 2024-11-01..2025-02-28 was never read (`MCF_HIST_ALLOW_LOCKED` never set; every loader asserts it; the 1-min walk
drops it on read). The old holdouts (Apr-Jun 2026, >= 2026-09-16) were dropped before every sweep. No holdout was
scored. No config, setup, exit or assignment was changed. `PLAN.md` was written before anything was scored.*

**Configurations tried: 27** (A flatten 5, B burst risk share 6, C F4 rework 8, D new open longs 8). **0 pass.**
**No new owner decision**; the three open ones (DM-NS3, DM-MF, BRAKE-1) carry over.

## Failures first
1. **Neither give-back candidate holds on two years, so there is no give-back proposal this week.**
   - The 15:45 flatten (live replay +66.9R since 10-06, t 2.02) is **−0.0011R per trade on two years** (t −0.72;
     15:40 / 15:50 also ≤ 0; longs −0.005R). The live gain is two days (58%) of a short sample.
   - Burst risk sharing cuts live give-back in every account but fails on two years: there, burst lots are **better**
     than the rest (−0.002 vs −0.028R), so sizing them down lowers R per unit of risk and keeps only 70-83% of the
     top-decile winners' R.
2. **The rdt1030 near-misses are not near-misses.** F4-RW4-L: 0 of 8 rework rows pass; every row is a "long on QQQ-up
   days" trade (down days −0.29..−0.39R, the random same-bar control makes +0.02..+0.05R too). F2-RW3-L is 89% one
   day (2025-04-07; +0.005R without it), so it is not reworked (one-big-day rule).
3. **The 09:35-09:50 long precursors do not pick direction.** Both new ideas sit on the random 09:40 baseline
   (excess −0.05..+0.02R); up days +0.04..+0.21R, down days −0.18..−0.43R.
4. **Discover workflow finished** (section 1), but more than twice as slow as last week (62 vs 27 min).
5. **Gen's −$2,744.98 on 10-30 is missing 31 unbooked trades** (HK-RECON-GEN); week numbers for Gen are incomplete.

## Today's win
A measured step on the 09:35-09:50 problem: a random 09:40 long with the lab 0.25 ATR bracket loses −0.135R (costs and
noise); with a **0.5 ATR stop and a 10:30 exit it loses −0.065R** — half the drag. Any opening setup should be built on
the wider geometry. And two live-only beliefs (15:45 flatten, burst cap) were checked against two years before they
became rules.

## 1. Discover workflow (weekly)
- **Finished: run 41212073345** (schedule, 2026-10-31 14:51-15:54 UTC, **success in ~62 min** vs 27 min last week): Mine
  34 min, refresh bars 24 min, backlog re-test 4 min, publish; mcf-data commit 5917f2c8 "discovery + backlog 2026-10-31".
- **Bar cache refreshed to 2026-10-30** (lab-cache sample 2026-06-15..10-30). **Backlog re-tested: 66 lab entries**
  (`mcf-data/backlog/backlog_results.jsonl`, history +66 rows). 42 of 66 positive in-sample on the cache window (last week
  43), 22 positive forward (21). Top: RW3 base `bdi-rw-gapdn-rsi5pop-flowsell` +0.219R (n 368, t 4.18; forward 56 trades
  +0.239R), L3 rsi5hi +0.198R (546, t 3.22; forward 48, −0.227R), NS1 +0.175R (t 2.92; forward −0.088R), RW5 base +0.197R
  (t 2.64; forward 43, +0.320R). One 4.5-month regime, not the two-year gates (RW3 / RW5 bases are negative on two years).
- Discovery: 2,290 rule / direction combinations, 58 sessions, **45 "replicated"** (32 last week). The top rows are again
  the odd "RSI14 < 35 + new high of day" short family (a feature artefact, sat1024) and "gap down > 2%" short (+0.088R test,
  the L3 / RW gap-down family already live). One long: gap up > 2% + up > 2% from open, 09:50-11:00 (+0.112R test,
  n 398) — the opening drive again; D2 above shows the 09:40 version has no edge on two years. Nothing new added.

## 2. Rule-18 rework round + new ideas (PLAN.md; all rows, failures included)

### A. Earlier flatten (`flat2y.py` → `flat2y_out.txt`, `flat2y.csv`) — backlog `nightly-1027-flatten-1545` → failed
60,907 lab trades (21 setups, base windows), 348 sessions; each walked on the 1-min cache. Harness check: simulated
15:55 result vs the lab r: corr 0.999, mean −0.0256 vs −0.0219R; geometry per setup matched to ≤ 0.02R.

| config | trades affected | Δ per trade | Δ per affected | t_day | TRAIN / VALID | up / down | top-decile R kept | pass |
|---|---|---|---|---|---|---|---|---|
| 15:40 all | 13,651 | −0.0002 | −0.0009 | −0.11 | +0.0008 / −0.0009 | +0.0057 / −0.0070 | 98% | no |
| 15:45 all | 13,257 | −0.0011 | −0.0052 | −0.72 | −0.0023 / −0.0004 | +0.0015 / −0.0046 | 99% | no |
| 15:50 all | 12,733 | −0.0007 | −0.0032 | −0.56 | −0.0008 / −0.0006 | +0.0026 / −0.0040 | 99% | no |
| 15:45 longs | 2,849 | −0.0050 | −0.0224 | −1.08 | −0.0146 / −0.0001 | −0.0007 / −0.0094 | 99% | no |
| 15:45 shorts | 10,408 | −0.0001 | −0.0005 | −0.06 | +0.0005 / −0.0005 | +0.0017 / −0.0022 | 99% | no |

Bar t ≥ 1.79 (N 5). The last 10-15 minutes are a coin flip on two years (positive only in up sessions). Caveat: the lab
lists hold base windows, not the -FD lots; the late-entry -FD lots are the ones open at 15:45 live.

### B. Burst risk sharing (`burst.py` → `burst_out.txt`, `burst2y.csv`, `burst_live.csv`) — `nightly-1029-burst20-one-bet` → failed
Two years: 24% of lab trades are in bursts of ≥ 10, 15% in ≥ 20.

| K / C | burst avg R vs rest | TRAIN burst / rest | VALID burst / rest | R per risk VALID (base −0.0014) | day std (base 51R) | worst 5 days (base −1,084R) | best 5 days (base +781R) | top-decile R kept |
|---|---|---|---|---|---|---|---|---|
| 10 / 3 | −0.002 / −0.028 | −0.033 / −0.064 | +0.025 / −0.008 | −0.0069 | 32.7 | −552 | +310 | 70% |
| 10 / 5 | same | | | −0.0061 | 33.7 | −564 | +326 | 73% |
| 10 / 10 | same | | | −0.0043 | 37.1 | −613 | +409 | 81% |
| 20 / 3 | +0.000 / −0.026 | −0.032 / −0.061 | +0.036 / −0.007 | −0.0059 | 36.2 | −605 | +388 | 79% |
| 20 / 5 | same | | | −0.0055 | 36.7 | −617 | +399 | 80% |
| 20 / 10 | same | | | −0.0046 | 38.3 | −673 | +434 | 83% |

t(rest − burst) −0.58 / −0.47 (bar 1.89): the wrong sign. Live paper (10-06..10-30, K 10 / C 3) is the opposite: daily
give-back mean P $198 → $186, T1 $386 → $359, T2 $436 → $328, GY $864 → $696, Gen $763 → $558, P/L better in all five
(Gen −$5,550 → −$3,850). The live sample is 8-19 sessions of one regime; the two years win. Gen's generated setups are
not in the lab lists, so a Gen-only two-year test is the open follow-up (not built).

### C. F4-RW4-L rework (`f4rw/`: unchanged rdt1030 harness copy, `build.py check` max |diff| 0.0; `score_out.txt`, `results.csv`)
N 2,145 → BAR90 t ≥ 3.52. Long only, 348 sessions (harness split: TRAIN ≤ 2025-12-31).

| id | rule | n/sess | TRAIN / VALID | t | WF | up / down-day R | control R | w/o best day (share) |
|---|---|---|---|---|---|---|---|---|
| S31-Q10-L | QQQ ≥ +0.10% | 17.9 | +0.000 / +0.090 | 0.85 | 40% | +0.148 / −0.341 | +0.029 | +0.006 (87%) |
| S31-Q30-L | QQQ ≥ +0.30% | 13.5 | +0.018 / +0.129 | 1.11 | 40% | +0.166 / −0.371 | +0.054 | +0.022 (69%) |
| S31-BE-L | + BE at +1R | 15.9 | +0.009 / +0.111 | 1.06 | 50% | +0.152 / −0.328 | +0.036 | +0.017 (71%) |
| S31-2R-L | + fixed 2R | 15.9 | +0.011 / +0.124 | 1.12 | 50% | +0.163 / −0.332 | +0.045 | +0.020 (69%) |
| S31-RET-L | + retrace entry | 6.4 | −0.067 / +0.092 | 0.17 | 40% | +0.121 / −0.378 | +0.021 | −0.022 |
| S31-TS-L | + tight stop | 16.3 | +0.005 / +0.129 | 1.06 | 50% | +0.175 / −0.385 | +0.039 | +0.020 (70%) |
| S31-D30-L | push ≥ 0.30 ATR | 5.0 | −0.011 / +0.190 | 1.35 | 70% | +0.191 / −0.293 | +0.049 | +0.048 (51%) |
| S31-G10-L | FVG ≥ 0.10 ATR | 13.0 | +0.011 / +0.099 | 1.07 | 40% | +0.135 / −0.312 | +0.030 | +0.020 (63%) |

~80% of trades ride to the 15:55 flatten; the result is the QQQ-up-day drift. Two rework rounds (6 + 8) failed: the F4
lineage is dropped (`sat1031-f4-orl-sweep-qqq-rework`).

### D. New 09:35-09:50 longs (`open_long.py` → `open_long_out.txt`, `open_long.csv`)
Prior from the move library (10-29 + 10-30, 69 early long movers): median gap −1.7%, RSI5 16, below VWAP, at the PDL,
volumeRatio 2.2. N 20 (Move Hunt lineage) → BAR90 2.20. Baseline = first 09:40 long of every eligible symbol-day.

| config | n/sess | exp R | t | TRAIN / VALID | up / down | WF | baseline | excess |
|---|---|---|---|---|---|---|---|---|
| D1 capitulation reversal v1.5 t1s1 | 10.7 | −0.116 | −2.00 | −0.127 / −0.110 | +0.211 / −0.432 | 29% | −0.135 | +0.019 |
| D1 v3 t1s1 | 2.3 | −0.138 | −1.89 | −0.159 / −0.127 | +0.159 / −0.401 | 35% | −0.135 | −0.003 |
| D2 gap-and-go v1.5 t1s1 | 9.1 | −0.152 | −3.69 | −0.215 / −0.125 | +0.036 / −0.404 | 24% | −0.135 | −0.018 |
| D2 v3 t1s1 | 2.7 | −0.120 | −2.55 | −0.177 / −0.094 | +0.036 / −0.375 | 12% | −0.135 | +0.015 |
| D1 v1.5 h1030w | 10.7 | −0.065 | −1.60 | −0.080 / −0.057 | +0.111 / −0.255 | 29% | −0.065 | +0.000 |
| D1 v3 h1030w | 2.3 | −0.115 | −2.43 | −0.174 / −0.085 | +0.009 / −0.234 | 35% | −0.065 | −0.050 |
| D2 v1.5 h1030w | 9.1 | −0.073 | −2.43 | −0.096 / −0.064 | +0.056 / −0.203 | 24% | −0.065 | −0.008 |
| D2 v3 h1030w | 2.7 | −0.063 | −1.62 | −0.097 / −0.048 | +0.082 / −0.182 | 41% | −0.065 | +0.002 |

Learned: at 09:40 the stock's own state (flush, gap, volume) tells us a big move is likely, not which way; the day's
direction decides. The open needs a market-direction precursor (index / sector / breadth at 09:35-09:45) or a
two-sided entry, on the wide geometry.

## 3. Week scorecard 10-26..10-30 (paper, costs in; `week.py` → `week_out.txt`, `week_scorecard.csv`)
| account | R | trades | avg R | win % vs break-even | P/L after costs (before) | green days | last week R / $ |
|---|---|---|---|---|---|---|---|
| Primary | **−5.2R** | 125 | −0.042 | 58% vs 60% | −$135.23 (−$78.53) | **3 of 5** | +38.8R / +$540 |
| Testing 1 | −82.9R | 704 | −0.118 | 51% vs 58% | −$297.22 (−$147.00) | 3 of 5 | −84.1R / −$275 |
| Testing 2 | −115.9R | 911 | −0.127 | 57% vs 65% | −$926.32 (−$780.54) | 2 of 5 | −0.4R / +$345 |
| Graveyard | −203.6R | 1,645 | −0.124 | 56% vs 64% | −$3,437.38 (−$2,883.92) | 0 of 5 | −133.5R / −$2,737 (3 days) |
| Gen | −218.2R | 665 | −0.328 | 37% vs 57% | −$6,238.10 (−$5,731.32) | 1 of 5 | +5.7R / +$688 |
| **total** | **−625.9R** | 4,050 | | | **−$11,034** | | |

- **Primary:** 10-26 +$34, 10-27 +$88, 10-28 +$246, 10-29 −$411, 10-30 −$91. Without its best day (10-27, +6.4R) the
  week is −11.6R. Best: Early Sellers into a Pop, mid-RSI (all day) `MF2-open-rsimidhi-flowsell-FD` 11 trades +4.5R,
  SMA50 Flush Oversold Bounce `NS5-sma50-flush-oversold-long` 4 trades +3.4R (+$257). Worst: Stretched Below VWAP Bounce
  `CWT13-vwapstretch-z05-long` 11 trades −4.4R, `MF4-h40-open-flowsell-FD` 14 trades −2.8R. Since start 6 of 19 sessions
  green, −$1,248.65; live-funds hold stays.
- **Testing 1:** best Gap-Down Recovery Fade (all day) `L3-gap-slope-fromopen-FD` 90 trades +22.5R (+0.250, +$557) —
  it was promoted to Primary on 10-30. Worst `CWT14-failbrk-pdl-p05-long` 257 trades −34.0R, `MF3-open-flowsell-rsi5hi-FD`
  40 −18.4R, `RW4-ns3-adv150-short-FD` 21 −13.2R (the last two are in DM-MF / DM-NS3).
- **Testing 2:** best `L3-gap-slope-rsi5hi-FD` 38 trades +10.2R (now Primary), `CWT09-gapdn-vwaploss-g10-short` 8 +4.5R.
  Worst `CWT12-coil-k4-long` 203 −35.6R (moved to the Graveyard 10-29), `CWT14-failbrk-pdl-p05-lowvol-long` 173 −25.8R,
  `MF5-flowsell-vwapup-rsi5hi-FD` 24 −14.1R (DM-MF). Longs −77.7R of the −115.9R.
- **Graveyard:** worst `CWT14-failbrk-pdh-p10-short` 106 −37.4R, `RW2-exhaustion-noon-adv150-short-FD` 86 −34.9R (−$1,049),
  `heat_fade_short-FD` 97 −27.6R. Best `CWT13-vwapstretch-z05-short` 43 +4.1R.
- **Gen:** 10-29 −$3,872 and 10-30 −$2,745 are the week. Worst `GEN-261020-07-…-AM-BRvwgt0p7-hold-long` 48 trades −43.1R
  (−$1,685; the 47-lot 10:45 burst), `GEN-261020-03-…-MID-…-t05s05-long` 30 −34.8R. Best `GEN-261026-06-NewLOD-…-LATE-…-long`
  13 +10.2R, `GEN-261026-02-VolRatio…-LATE-…-long` 10 +8.0R.
- Week vs last week: Primary −44R worse (last week was one +$1,369 day); T1 flat; T2 −115R worse (longs on two down
  mornings, 10-27 / 10-28); Gen −224R (two burst days).

## 4. Weekly give-back review (`giveback_week.py` → `giveback_week_out.txt`; nightly peak attribution)
Marked peak → close ($, costs in):

| account | 10-26 | 10-27 | 10-28 | 10-29 | 10-30 | week give-back |
|---|---|---|---|---|---|---|
| Primary | +61 (11:30) → +34 | +97 (15:36) → +88 | +260 (15:18) → +246 | +20 (13:21) → −411 | **+144 (14:21) → −91** | $719 |
| Testing 1 | +553 (15:54) → +504 | 0 → −407 | +83 (10:52) → −702 | **+475 (13:53) → +250** | +129 (14:21) → +58 | $1,537 |
| Testing 2 | +12 → −40 | +17 → −261 | 0 → −926 | +285 (15:26) → +246 | **+216 (14:08) → +55** | $1,456 |
| Graveyard | +36 → −405 | +100 → −950 | 0 → −1,079 | +124 → −301 | +47 → −703 | $3,745 |
| Gen | +229 (13:58) → −64 | +863 (15:46) → +565 | +261 (12:55) → −122 | **+278 (11:34) → −3,928** | **+323 (10:42) → −2,745** | $8,250 |

What gave it back (week sums, $): Primary: open winners turning −$603 (10-29 RW5-FD short −$247 stopped in the bounce,
10-30 RW3-FD −$95), new entries after the peak only −$58, twins −$207. Testing 1: entries after the peak −$971
(10-28 RW4-FD −$179), open winners −$508, late flatten −$319. Testing 2: after the peak −$1,157 (10-28 NS3V1 −$532), late
flatten −$421. Graveyard: after the peak −$2,649 (RW2-FD, heat_fade_short-FD, CWT14 ORL longs). Gen: after the peak −$4,186
and open winners −$3,974 (10-29: GEN-261020-07 burst −$2,186 open at the peak).
"Up a lot, then a loss" (peak ≥ +$100, close < 0): Primary 10-30; Gen 10-26, 10-28, 10-29, 10-30; Graveyard 10-27, 10-29.

Did the live caps help (blocked signals priced by the journal what-if run, net of costs; `week_out.txt`)?
- **Twin-exposure cap: yes, every account** — blocked twins would have made −57.2R: Primary −2.6R, T1 −18.3R
  (MF3 base vs MF3-FD), T2 −27.0R (NS3-FD vs NS3V1), Graveyard −9.3R.
- **Per-setup −2R loss limit:** Graveyard (latched) blocked 759 signals worth **−188.6R** (helped a lot; 10-30 alone
  −98.0R); Primary ST-P blocked 4 signals worth −2.7R (10-29); off in T1 / T2 / Gen (ST-A), nothing to measure.

Give-back proposals: **none this week.** Both tested candidates fail on two years (section 2A, 2B). The give-back is
structural: Primary's comes from open trades turning on index reversals (not new entries), the testing books' from new
entries after the peak on down mornings, Gen's from same-bar bursts. Rules that cut it on two years only do it by cutting
trades or winners (sat1024: 23 configs; today 11 more). Not proposing an over-correction.

## 5. New setup ideas
Tested and failed today: D1 / D2 (above). Queued (ideas, 0 configs):
- **Index-first open (09:35-09:50, two-sided):** decide the side from SPY / QQQ / breadth at 09:35-09:45 (the open follows
  the day), then take the stock with the biggest volume-confirmed move on that side, wide geometry. Needs the open frame
  plus the context table.
- **Gen-only burst risk share** two-year test on the generator's own rule lists.

## 6. Plan for next week (11-02..11-06)
1. Owner decisions open: DM-NS3, DM-MF, BRAKE-1.
2. Mon: HK-RECON-GEN (31 unbooked Gen trades) and OPS-HANDOVER (standby Python setup ~10 min) before the open.
3. BDI weekdays: index-first open study (pre-declared, wide geometry); Gen burst test; Move Hunt capture rate daily.
4. Watch the L3 pair in Primary (borrow skips) and NS4-FD / GEN-261026-03 monitor marks; CF review 11-12.
5. Message-board proposals (MB-PROP) still wait on the owner.

## Backlog (`backlog_updates.py`, BACKLOG.md re-rendered)
New (all failed): `sat1031-f4-orl-sweep-qqq-rework` (8), `sat1031-open-capitulation-reversal-long` (4),
`sat1031-open-gap-and-go-long` (4), `sat1031-burst-risk-share` (6). Updated: `nightly-1027-flatten-1545` → failed (+5),
`nightly-1029-burst20-one-bet` → failed, `reddit-1030-orbfvg-f4` (+8, lineage dropped), `reddit-1030-orbfvg-f2` (note).

## Files
`PLAN.md`, `week.py` → `week_out.txt` / `week_scorecard.csv` / `week_by_setup_*.csv`, `giveback_week.py` →
`giveback_week_out.txt` / `.csv`, `flat2y.py` → `flat2y_out.txt` / `.csv`, `burst.py` → `burst_out.txt` / `burst2y.csv` /
`burst_live.csv`, `f4rw/` (build, score, rework.json, results.csv, score_out.txt), `open_long.py` → `open_long_out.txt` /
`.csv`, `backlog_updates.py`. Scratch (journals, F4 trade lists, 1-min walk, ~25 MB) deleted.

Educational only — not financial advice.
