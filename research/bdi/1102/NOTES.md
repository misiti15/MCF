# BDI 2026-11-02 (Monday): Move Hunt day 3, opening group-move test, account blocks

*Educational only — not financial advice. Live numbers are **paper** results from one session. The two-year test uses the
open opening frame (research/bdi/timeofday/data/open, 09:35-10:30, locked block dropped at build time and asserted absent)
and the history2y daily table with the locked block **dropped before** the peer table is built. **The locked block
2024-11-01..2025-02-28 was never read.** **16 configurations were tried tonight (MH4), all reported below; none passes.**
No config, setup, exit, ledger or docs/live file was changed. Costs are in everywhere (P/L = journal `pnl_adj`; avg R =
`pnl_adj / $ risk`).*

Built on, not redone: nightly1102 (close / coverage / hand-over, Primary WHY = 6 SOXS shorts, the 4-config inverse-ETF
swarm, L3-only follow-up queued, DM-N3, HK-LATCH, HK-RECON-GEN). The past week's families (pdl1030*, rdt1030,
saturday1031) and the inverse-ETF skip were not re-tested.

**Rule changes inside the windows quoted here** (research/ledger.jsonl): today — PDL-1a R2A legs in Testing 2 from
11-02, NS3-FD / RW4-FD moved to the Graveyard from 11-02, BRAKE-1 shadow line from 11-02. Primary records since 10-23 also
span the ~$4,000 position size (10-28), the −2R per-setup stop (10-29) and the L3 pair promotion (10-30); Testing records
span the setup-stop removal (10-23), the lab 5-minute clock (10-27), BAR90 (10-29) and the cost filter (10-30).

## Today's win
**The Move Hunt found what the open movers share — their group — and measured it: a name that lags a moving peer group
catches up.** On two years, laggards of a residual-correlation peer group that has moved ≥ 0.4 ATR (ex-market) by
09:40-09:50 beat a day-matched random entry by **+0.075R (longs, t 2.43; positive in both train +0.135R and valid
+0.062R)** and +0.080R (shorts, t 2.71, valid only), at ~10 signals a day per side. It is not a setup yet (the day's
direction and the opening cost leave the absolute P/L at −0.03..−0.05R), but it is the first opening precursor in three
Move Hunt days that carries information *beyond the day's direction* (MH3 on 10-30 had none: excess −0.04..+0.01R).
Second: **capture rate rose to 22% (11 of 50 tradable movers) from 6% on 10-30**, and 7 of the 36 opening movers were
caught (10-30: 0 of 33).

## 0a. Move Hunt (v1 definition unchanged; research/bdi/moves/, output moves_1102_out.txt; moves.csv +100 rows)
Inputs: SIP 5-minute bars 10-08..11-02 for 1,568 symbols (`fetch5.py` with the start moved to 10-08 for disk), live
priors + SIP 1-minute bars (`research/ops/coverage1029/fetch.py`), the 5 journals. 1,205 liquid names, 79,483 decision rows.

| set | caught (right side) | R captured | wrong-side trades | main miss reasons |
|---|---|---|---|---|
| all (top 25 + 25) | **2 / 50 (4%)** (TWST, CASY shorts, Gen) | +1.19 | 2, −2.41R | blackout 39 (11 on the event day: EW +2.5 / −3.7 ATR, IDXX, BAM, TOST, RIVN, AXSM, NTRA, FOXA) |
| tradable (blackout removed) | **11 / 50 (22%)**: long 4/25, short 7/25 | **−0.65** | 23, **−16.01R** | no setup 16, traded outside the move 9, wrong side only 8, skipped 6 |

**vs 10-30: 6% (3/50, +1.49R, wrong side −4.06R); 10-29: 26% (13/50, +3.59R, −16.13R).** More catches, but the R was
negative: Gen's opening shorts caught CASY (+1.24R) and UNH (+1.11R) yet stopped on GIS (−2.25R), CPB, HRL (−1.1R each)
before the food group fell; GY CWT12-coil-k4 caught AS / TCOM longs (+0.31 / +0.33R), T2 CWT12-flag RBA (+0.30R), Gen
GEN-261019-01 RBRK (+0.43R). Primary caught none of the 50.

What was known at the decision point, and why they were missed (only data available then):
- **The open again (36 of 50 at 09:35-09:45; 10-29 30, 10-30 33).** No live setup runs before 09:50 except Gen's OPEN
  rules and a few CWT entries.
- **Groups.** Packaged food fell as a group 09:45-09:55 (CPB −1.06, GIS −1.00, HRL −0.96, CAG −0.86 ATR; KMB in blackout,
  DPZ −0.86) and alternative asset managers rose 09:35-09:40 (BN +1.85, KKR +0.99; BAM / APO / ARES reporting, in
  blackout) — earnings sympathy for the third Move Hunt day. Tesla complex long 09:55 (TSLA, TSLL, TSLG; TSLQ short).
- **Wrong side (−16.0R).** The opening failed-breakdown longs bought names that were starting the day's big down moves:
  XBI (5 lots, −4.6R: GY CWT14-failbrk-orl-p05 ×2, T2 CWT14-failbrk-pdl-p05-R2A / -p10 / -p10-lowvol), TSLQ, ROIV, CPB;
  IBKR long ×3 (Gen ORBfailUp, GY heat_fade_long, T2 CWT13-z05-long, −3.15R).
- **Skips:** ELV / NTSK shorts spread > max; ARKG not shortable; IBKR / DE / HPQ shorts blocked by the GY −2R setup
  limit.

Precursor check (one day, hindsight labels, decision rows 09:40-09:50): group-lead longs (peer median ≥ 0.4 ATR, agree
≥ 70%) 11 signals, 36% reached ≥ 0.5 ATR in 90 min vs a 20% base; lead shorts 25 signals, 16% vs 7%; laggards 33% / 0%
(6 signals each). 9 of the 50 tradable movers had a same-direction group signal (HEI, TDG, TCOM, SGI long; TWST, ELV,
NTSK, ARKG, UNH short). Tested on two years below.

## 3. New tested idea: MH4 opening group move (`research/bdi/1102/mh4_group.py`, `mh4_out.txt`, `mh4_results.csv`)
Pre-declared in the script: peers = top-10 residual-return correlation names (daily returns minus beta × SPY, trailing
120 non-locked sessions before each month, corr ≥ 0.30); z = move from the open in ATR units minus the cross-sectional
median at that bar; P = median peer z (≥ 6 peers), agree ≥ 0.7; first of 09:40 / 09:45 / 09:50 per symbol-day with |P| ≥ g;
**lag** = own z < P/2 (catch-up), **lead** = own z ≥ P; g 0.40 / 0.60; exits t1s1 and stop 0.25 ATR held to 10:30.
adv20 ≥ $95M, blackout removed, production costs with the tod entry multiplier. Train ≤ 2025-09-30. Pass needs BAR90,
walk-forward ≥ 54%, both regimes > 0 **and** a day-matched excess t ≥ 1.5.

| config | n | /day | avg R | t | w/o best day | train / valid | up / down | **day-matched excess** (t) | excess train / valid |
|---|---|---|---|---|---|---|---|---|---|
| lag long g40 t1s1 | 3,210 | 10.3 | −0.052 | −1.46 | −0.063 | −0.125 / −0.036 | +0.076 / −0.156 | **+0.075 (2.43)** | +0.135 / +0.062 |
| lag long g40 h1030 | 3,210 | 10.3 | −0.031 | −0.66 | −0.051 | −0.160 / −0.003 | +0.116 / −0.192 | +0.086 (2.38) | +0.161 / +0.070 |
| lag long g60 t1s1 | 580 | 5.0 | −0.023 | −0.35 | −0.052 | −0.393 / +0.039 | +0.089 / −0.193 | +0.080 (1.44) | −0.043 / +0.101 |
| lag long g60 h1030 | 580 | 5.0 | +0.056 | 0.64 | +0.019 | −0.508 / +0.152 | +0.206 / −0.172 | +0.135 (1.97) | −0.046 / +0.165 |
| lead long g40 t1s1 | 4,979 | 15.8 | −0.114 | −2.98 | −0.125 | −0.256 / −0.087 | +0.022 / −0.239 | −0.003 (−0.09) | −0.029 / +0.002 |
| lead long g40 h1030 | 4,979 | 15.8 | −0.118 | −2.30 | −0.137 | −0.319 / −0.079 | +0.016 / −0.288 | −0.017 (−0.41) | −0.048 / −0.011 |
| lead long g60 t1s1 | 1,008 | 7.8 | −0.017 | −0.25 | −0.039 | −0.218 / +0.017 | +0.180 / −0.261 | +0.098 (1.64) | +0.133 / +0.092 |
| lead long g60 h1030 | 1,008 | 7.8 | −0.042 | −0.40 | −0.121 | −0.372 / +0.013 | +0.174 / −0.366 | +0.053 (0.57) | +0.069 / +0.051 |
| lag short g40 t1s1 | 2,815 | 9.1 | −0.045 | −1.38 | −0.053 | −0.130 / −0.018 | −0.214 / +0.082 | **+0.080 (2.71)** | −0.010 / +0.109 |
| lag short g40 h1030 | 2,815 | 9.1 | −0.062 | −1.35 | −0.077 | −0.112 / −0.046 | −0.209 / +0.051 | +0.073 (2.11) | +0.004 / +0.095 |
| lag short g60 t1s1 | 463 | 4.3 | −0.011 | −0.15 | −0.028 | −0.134 / +0.029 | −0.156 / +0.098 | +0.157 (2.51) | +0.030 / +0.198 |
| lag short g60 h1030 | 463 | 4.3 | −0.036 | −0.43 | −0.064 | −0.283 / +0.045 | −0.168 / +0.086 | +0.138 (1.87) | −0.123 / +0.224 |
| lead short g40 t1s1 | 5,169 | 17.2 | −0.056 | −1.38 | −0.067 | −0.166 / −0.026 | −0.202 / +0.007 | +0.069 (1.77) | −0.047 / +0.100 |
| lead short g40 h1030 | 5,169 | 17.2 | −0.030 | −0.48 | −0.053 | −0.188 / +0.013 | −0.177 / +0.007 | +0.103 (1.85) | −0.072 / +0.149 |
| lead short g60 t1s1 | 1,057 | 9.3 | −0.049 | −0.56 | −0.083 | −0.172 / −0.009 | −0.125 / −0.116 | +0.125 (1.42) | −0.059 / +0.187 |
| lead short g60 h1030 | 1,057 | 9.3 | +0.004 | 0.03 | −0.076 | −0.189 / +0.041 | −0.093 / −0.094 | +0.167 (1.26) | −0.063 / +0.244 |

**Failed** (backlog `mh-1102-open-group-move`, status failed, 16 configs). N 16: full bar 2.35, BAR90 2.12; best absolute
t 0.64 (lag long g60 h1030, train −0.51R), walk-forward positive months 16-56%; longs win only on up days, shorts only on
down days. **What it found:** the day-matched excess is positive in 14 of 16 configs; for laggards it clears 2.1-2.7 t
at g 0.40 on both sides, and for long laggards it holds in both halves. Leaders (lead g40) add nothing on the long side.
So the group tells *which* names will move, the day tells *which way the book ends*. A market-neutral rework (laggard +
beta-sized SPY hedge) is queued with a pre-declared 4-8 config test: `mh-1102-group-laggard-hedged`. No locked look
spent, no Testing entry (absolute P/L fails; nothing to suggest).

## 0. Per-account session review (`accounts.py` → accounts_out.txt; peak / close from nightly1102 daily_peak.csv)

**Primary** — **−$627.19** after costs (−$614.39 before), 12 trades, 25% win vs 48% break-even, −0.515R; peak +$67
(12:07) → −$627 (give-back $695: the four SOXS L3 lots open at the peak −$240 and the five entries after it −$407 —
SOXS L3-fromopen lot 4, rsi5hi ×2, ST7-FD ASST long −$127). Best MF2-open-rsimidhi-flowsell-FD CBRS +2.2R (+$100),
RW3-FD RNG +0.6R; worst L3-fromopen-FD −4.1R (−$424), L3-rsi5hi-FD −2.0R (−$217). Shorts −0.461R / −$500 (11), long −1.1R.
Notable skips: 251 not shortable (L3's single-stock inverse ETFs, saved per the nightly), 30 setup-loss-limit blocks
(−16.8R saved). Loss types: all 7 big losers were wrong-side-after-big-swing (−$769). What-ifs (sum R): live −6.2, hold
−4.2, stop-and-reverse −2.6, opposite +6.4 — the SOXS lots were the wrong side of semis, not a bad exit. Move Hunt:
Primary caught 0 of 50. Edits: (1) **count lots by underlying** — the SOXS shorts were one long-semis bet the per-symbol
cap and the −2R latch saw only partly (backlog `bdi-1102-underlying-exposure-cap`, test pre-declared on the 2-year book);
(2) L3 inverse / leveraged skip — already queued by the nightly (`nightly-1102-l3-inverse-etf-skip`), not repeated;
(3) HK-LATCH (housekeeping, nightly). Nothing else: the L3 review stays 11-12 (record carried by one day, see nightly 1a).

**Testing 1** — **−$184.55** (−$178.95 before), 37 trades, 30% win vs 55%, −0.455R; peak +$12 (09:58) → −$185 (give-back
$197; 29 after-peak entries −$117, open winners at the peak −$77 — NS3 CRDO short −$41, SOXL long NS5-FD −$42). Best
RW7-gapdn-bounce-early-short-FD +1.7R (+$35), RW6G1-FD +0.8R; worst NS5-FD −2.1R (−$59), ST4-FD −2.1R (−$33). Longs −0.970R
(11), shorts −0.237R (26). Skips: 53 not shortable, cost filter 24 (saved −6.2R before costs, nightly). Edits: (1) DM-N3
(NS5-FD / ST4-FD / RW6G1-FD to the Graveyard) — today's two worst are both in it, the decision is already open; (2) RW7-FD
331 trades +0.001R, −0.033R w/o best day: still flat, no promotion case.

**Testing 2** — **−$389.38** (−$382.24 before), 129 trades, 47% win vs 66%, −0.256R; peak +$95 (12:38) → −$389 (give-back
$484: 62 after-peak entries −$348, mostly afternoon longs into the slide; AMDL / SOXL / MXL / TTMI longs). Longs −0.314R
on 110 lots (−$520), shorts +0.077R on 19 (+$130). Best NS3V1-am-widestop-short +1.3R (+$57), NM-AR-AM capitulation long
+1.6R; worst CWT14-failbrk-pdl-p05-R2A-long 19 trades −3.0R (−$170, day 1 of R2A), NM-HL-T75-pm-long 24 trades −9.9R
(−$158; record 43 trades / 7 sessions −0.099R, −0.201R w/o best day). Only account where **hold to the close** beat live
(+4.8R vs −33.1R; one day). Edits: (1) NM-HL-T75-pm-long on watch (needs 20 sessions before a review; it is the T2 long
cluster that loaded up after 12:38); (2) R2A watch per nightly (exemption 11-03); (3) the opening CWT14 failed-breakdown
longs were the wrong side of XBI / TSLQ — no new rule from one day (pdl family exhausted this week).

**Graveyard** — **−$1,626.84** (−$1,509.80 before), 395 trades, 49% win vs 62%, −0.212R; peak +$67 (10:09) → −$1,627
(299 after-peak entries −$1,191). Longs −$1,709 (258), shorts +$82 (137). Best RW2-exhaustion-noon-adv150-short-FD +9.8R
(+$265), heat_fade_short-FD +7.2R (+$264); worst heat_fade_long −18.6R (−$699), heat_fade_long-FD −12.0R. 67 same-symbol
stacks (160 lots −35.9R; extra lots −16.6R; CRDO 3 lots −$181). 338 setup-loss-limit blocks. Edit: none (data collection,
rule 20).

**Gen** — **−$1,723.62** (−$1,563.94 before; 39 entries still unbooked, HK-RECON-GEN), 226 trades, 32% win vs 53%,
−0.365R; peak +$153 (10:59) → −$1,724 (147 after-peak entries −$1,689). Longs −$1,836 (138), shorts +$112 (88). Best
GEN-261022-07 short +15.1R (+$454), GEN-261021-02 long +8.9R; worst GEN-261021-06 ORBfailUp MID long 46 trades −47.3R
(−$1,085; record 112 trades / 5 sessions −0.390R, −0.653R w/o best day). Gen made 7 of the 11 Move Hunt catches (its
OPEN rules run before 09:50) but lost them on the food group. Edit: none new (burst item already queued; GEN-261021-06 is
the Generator's own retirement call).

## 1. Every trade, all accounts (`trades_bdi.py` → trades_bdi_out.txt, per_trade_1102.csv; patterns.csv +455 losers)
799 trades, all with SIP 1-minute paths; 455 losers. Exit what-ifs (sum R after costs; live / be05 / trail / hold / sar /
reenter / opp): Primary −6.2 / −5.7 / −5.5 / −4.2 / −2.6 / −5.6 / +6.4; T1 −16.8 / −12.1 / −11.4 / −4.2 / −14.0 / −11.7 /
+10.5; T2 −33.1 / −19.3 / −11.7 / **+4.8** / −18.2 / −24.3 / +15.3; GY −83.7 / −59.1 / −29.0 / −25.8 / −65.1 / −55.8 /
+42.2; Gen −82.6 / −50.4 / −38.8 / −7.5 / −29.0 / −68.7 / +43.4. Per trade: live −0.278R, hold −0.046R, trail −0.121R,
opposite +0.147R (se ~0.03-0.05) — a trend-down day where every alternative beat the bracket; one day decides nothing
(hold lost −129.8R in GY on 10-30).
- **Loss types:** wrong-side-after-big-swing is again the biggest $ bucket (118 losers, −$4,062; Primary all 7, −$769);
  small-MFE-then-failed 106 (−$1,812); never-worked 79 (−$1,478); stopped-then-reversed 73 (−$1,105, GY 54).
- **Opposite side (hindsight check):** the opposite 1R/1R won on longs whether or not SPY was already down at entry
  (+0.214R without the flag, +0.236R with it) — the flag known at entry does not pick them; shorts entered while SPY was
  ≥ +0.25% up did *well* (+0.314R live, n 86). No rule.
- **Give-back:** every account peaked before noon except T2 (12:38); after-peak entries made the give-back in all five
  (P −$407, T1 −$117, T2 −$348, GY −$1,191, Gen −$1,689). The late-short skip (nightly1030) and the post-peak brake
  (sat1024) already failed on two years; nothing new to test from one more down-afternoon.
- **Correlated stacking across sister setups / symbols:** Primary SOXS 6 lots by 2 sister L3 setups (−6.1R); across
  accounts the same long-semis bet sat in SOXS shorts (P), SOXL longs (T1 NS5-FD, T2 NM-HL) and AMDL longs (T2 R2A, NM-HL)
  → `bdi-1102-underlying-exposure-cap`. Same-symbol stacks: extra lots lost in GY (−16.6R), T2 (−1.4R), Gen (−2.4R).

## 2. Patterns → rules
1. **Opening movers come in groups; laggards of a moving group catch up** — tested tonight (MH4): real cross-sectional
   information (day-matched excess t 2.4-2.7), not an absolute setup. Next test pre-declared (hedged laggard book).
2. **Leveraged / inverse ETFs hide stacking** (SOXS short = SOXL long) — risk item with a 2-year test, queued.
3. Opening failed-breakdown longs on the day's big shorts (XBI, TSLQ, ROIV, CPB) — same as 10-30's orl longs; the pdl /
   orl families were swept this week (pdl1030*), so no new item.

## 5. Decisions
None. Nothing passed; no Testing near-miss (best absolute t 0.64 vs BAR90 2.12). DM-N3 (nightly) stays the only open
decision tonight.

Configurations tried tonight: **16** (MH4), 0 pass. About 15 descriptive splits (account, side, loss type, give-back,
stacking, flags, what-ifs) were looked at as well.

Reproduce: `research/bdi/moves/fetch5.py` (start 10-08) → `research/ops/coverage1029/fetch.py <scratch>/cov 2026-11-02`
→ `frames_today.py <scratch> 2026-11-02` → `moves.py <scratch> 2026-11-02`; `python research/bdi/1102/mh4_group.py
<scratch>`; `research/bdi/nightly1102/fetch.py <scratch>` → `trades_bdi.py <scratch> 2026-11-02`; `accounts.py <scratch>`;
`add_backlog.py`; `research/bdi/1028/merge_patterns.py research/bdi/1102/patterns_1102.csv`. Scratch deleted after the run.

Educational only — not financial advice.
