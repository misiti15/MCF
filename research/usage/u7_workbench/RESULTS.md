Educational only — not financial advice

# U7 Workbench at scale — results (2026-11-18, research only, market hours: nothing changed, nothing deployed)

**Headline: 0 of 20 tunes pass; no Testing-copy proposal.** One pre-registered tune per setup (C3-WB menus, one
change each) was chosen on the earlier half of each setup's live sessions and judged on the later half. The 17 tunes
that could be chosen made the check sessions 45.6R worse in total. 5 setups improved (+12.4R), 10 got worse (-58.0R),
2 were unchanged and 3 had no tune that beat the parent on fit. No tune reached the significance bar (best t = 1.56
against 2.45). Picking each setup's tune on its fit sessions did no better than picking the median candidate from the
same menu (-45.6R against -49.7R). Across all 250 eligible candidates, the gain on fit and the gain on check moved in
opposite directions (Spearman -0.26).

**Configurations tried: 265** fit candidates (4 proven parents × 4-6 exit/frequency candidates, 16 others × 15 one-gate
candidates), plus 17 check verdicts. Bar for a verdict: t ≥ max(1.5, sqrt(2 ln 20)) = 2.45. With N = 265 the bar would
be 3.34. Pre-registration: PLAN.md (committed before any scoring). Data: Live journals (run_id 1), 10-08..11-17,
R after costs = pnl_adj / risk, plus 1-minute SIP bars of each traded symbol-day for features, exit walks and random
entries. Shadow covers one session (11-17), which already sits inside every check half, so no separate paired-shadow
verdict was possible.

## Per setup (check = later sessions only; parent = live record as traded; var = tuned copy)

| # | Setup | Live n / days, avg, w/o best day (share) | Menu → tune chosen on fit | Check: parent n, avg → var n, avg | var w/o best day (share) | Δ check R, t | Real vs random entries (check) | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | GEN-261027-01 (long) | 16 / 6, +0.187, +0.139 (39%) | X: target 0.75× parent's | 6, +0.225 → 6, +0.215 | +0.148 (66%) | -0.06, -0.12 | +0.242 vs -0.077 | FAIL (worse; 3 days) |
| 2 | GEN-261026-03 (short) | 21 / 5, +0.379, +0.129 (77%) | X: none beat parent on fit | 9, +0.206 | — | — | +0.303 vs +0.665 | FAIL (no tune) |
| 3 | L3-gap-slope-lowdist-FD | 108 / 18, +0.245, +0.109 (69%) | X: none beat parent on fit | 60, +0.389 | — | — | +0.376 vs +0.002 | FAIL (no tune): parent's exits already best |
| 4 | RW7-gapdn-bounce-early-short-FD | 715 / 25, +0.026, +0.005 (83%) | X: time stop 120 min | 430, +0.070 → 430, +0.000 | -0.035 | -30.22, -1.59 | +0.101 vs +0.139 | FAIL (worse) |
| 5 | GEN-261026-07 | 132 / 6, +0.036, -0.007 | G: entry ≥ 13:37 | 67, +0.111 → 50, +0.108 | +0.056 (59%) | -2.06, -0.79 | +0.151 vs -0.015 | FAIL |
| 6 | RW1-gapdn-bounce-flowsell-short-FD | 195 / 26, +0.009, -0.020 | G: stop cost ≥ 0.051R | 121, -0.028 → 55, -0.027 | -0.101 | +1.89, +0.30 | +0.030 vs +0.130 | FAIL |
| 7 | GEN-261029-07 | 51 / 5, +0.021, -0.051 | G: stop cost ≤ 0.080R | 29, +0.166 → 29, +0.166 (gate removed nothing) | +0.389 (52%) | 0.00 | +0.205 vs +0.222 | FAIL (2 days) |
| 8 | GEN-261019-10 | 100 / 12, +0.051, -0.062 | G: entry ≤ 13:56 | 64, +0.268 → 38, +0.179 | +0.075 (68%) | -10.35, -1.60 | +0.241 vs -0.117 | FAIL (worse) |
| 9 | CWT05-flush-m05-v5-long | 21 / 12, +0.023, -0.062 | G: move from open ≤ -0.50 ATR | 12, +0.287 → 7, +0.237 | +0.046 (86%) | -1.78, -1.12 | +0.442 vs -0.492 | FAIL |
| 10 | NM-HL-T75-pm-long | 61 / 13, -0.013, -0.071 | G: gap (long) ≤ +1.3% | 18, +0.194 → 13, +0.376 | +0.242 (61%) | +1.41, +1.17 | +0.181 vs -0.104 | FAIL (1-day share 61%, t, reps) |
| 11 | GEN-261029-06 | 144 / 7, +0.005, -0.091 | G: move from open (short) ≥ -0.05 ATR | 96, +0.061 → 58, +0.129 | +0.026 (92%) | +1.66, +0.24 | +0.099 vs +0.051 | FAIL (1-day 92%) |
| 12 | NS1-rsidip-rsi5pop-long | 27 / 13, -0.029, -0.092 | G: VWAP distance ≥ +0.025 ATR | 15, -0.077 → 13, -0.156 | -0.200 | -0.88, -1.57 | -0.174 vs +0.063 | FAIL (worse) |
| 13 | NS4-pm-vwap-reclaim-oversold-short | 51 / 15, -0.034, -0.098 | G: VWAP distance ≤ -0.010 ATR | 31, -0.072 → 20, -0.337 | -0.475 | -4.50, -0.84 | -0.080 vs +0.369 | FAIL (worse) |
| 14 | GEN-261028-07 | 18 / 5, +0.125, -0.101 | G: move from open ≤ +0.60 ATR | 7, +0.287 → 7, +0.287 (gate removed nothing) | +0.210 (58%) | 0.00 | +0.380 vs +0.364 | FAIL (2 days) |
| 15 | ST8-volspikedn-long-pm-t1s1-FD | 30 / 14, -0.038, -0.114 | G: gap (long) ≤ +4.5% | 18, -0.205 → 15, -0.301 | -0.441 | -0.82, -1.18 | -0.189 vs +0.041 | FAIL (worse) |
| 16 | ST3-rsi5up-short-pm-t1s1-FD | 16 / 8, -0.054, -0.120 | G: none beat parent on fit | 12, -0.072 | — | — | -0.036 vs -0.219 | FAIL (no tune) |
| 17 | ST6-volspikeup-short-mid-t1s1-FD | 42 / 10, -0.098, -0.128 | G: move from open (short) ≥ +0.68 ATR | 35, -0.195 → 8, -0.077 | -0.132 | +6.20, +1.56 | -0.143 vs -0.274 | FAIL (still < 0; 8 trades) |
| 18 | GEN-261019-08 | 16 / 6, +0.008, -0.128 | G: stop cost ≤ 0.19R | 6, +0.437 → 5, +0.765 | +0.178 (81%) | +1.21, +1.00 | +0.416 vs +0.151 | FAIL (1-day 81%; 5 trades) |
| 19 | NS4-pm-vwap-reclaim-oversold-short-FD | 51 / 16, -0.028, -0.132 | G: relative volume ≥ 0.73 | 32, -0.250 → 16, -0.758 | -0.845 | -4.14, -0.91 | -0.180 vs +0.090 | FAIL (worse) |
| 20 | MF3-open-flowsell-rsi5hi | 69 / 14, -0.074, -0.136 | G: move from open (short) ≥ -0.35 ATR | 44, -0.110 → 38, -0.210 | -0.363 | -3.14, -1.67 | -0.107 vs -0.343 | FAIL (worse) |

Full numbers: u7_results.csv (verdict checks c1..c6 per setup), u7_parents.csv (live record, fit / check, random
entries), u7_candidates.csv (all 265 candidates with fit totals and, for diagnosis only, their check effect).
"Real vs random entries" runs real and random entries through the same simplified engine (stop / parent target /
flat 15:55, LR8 costs) on the check trades, with 5 random entry minutes per trade inside the setup's entry-time span.

## What the run shows (and what can be salvaged)

1. **One tune chosen on 3-13 fit sessions does not carry forward.** That held for exits on proven parents and for
   gates on the rest. It matches P4 (60/60 in-sample passes) and P5 (Spearman 0.03): at this record length the
   Workbench cannot tell a real improvement from noise. The biggest loss is RW7's 120-minute time stop (+2.7R on fit,
   -30.2R on check). RW7's later-session R comes from late-day flushes, and a time stop cuts exactly those.
2. **For 2 of the 4 proven parents the current exits are already the best option.** For L3-gap-slope-lowdist-FD and
   GEN-261026-03, no target or time-stop change and no refire-off beat the parent on fit. L3-lowdist also has the
   clearest entry edge of the 20 (check: +0.376R real vs +0.002R random, 60 trades, +0.183 w/o best day). Leave it as
   is. It stays first in line under C3-BAR2 on its non-overlap record.
3. **Entries beat random entries in 12 of 20 setups** (check, same engine). The clearest cases, besides L3-lowdist,
   are GEN-261019-10 (+0.241 vs -0.117, 64 trades), CWT05-flush-m05-v5 (+0.442 vs -0.492, 12 trades), GEN-261027-01
   (+0.242 vs -0.077), NM-HL-T75 (+0.181 vs -0.104) and GEN-261026-07 (+0.151 vs -0.015). These setups have real
   entry content. Their weak w/o-best-day records come from exits or day mix, not from the signal. They need reps,
   not a gate.
4. **These entries do worse than random:** NS4 (window and -FD), NS1, ST8 and RW1 (check). They are candidates for
   EXIT100 once they reach 100 trades / 15 active days, not for more Workbench time.
5. **Leads worth a watch (none proposed):** NM-HL-T75 with gap ≤ +1.3% (check +0.194 → +0.376, 13 trades,
   1-day share 61%); ST6 with "already extended ≥ 0.68 ATR" (+6.2R, t 1.56, 8 trades, still negative). Both fail the
   pre-registered rule. Re-test them only as one-gate copies once the parents reach 15 active days (C3-ROT).

## Improve / worsen across the 20 setups (check total R, tuned vs parent)

Improve 5 (RW1 +1.89, NM-HL-T75 +1.41, GEN-261029-06 +1.66, ST6 +6.20, GEN-261019-08 +1.21; total +12.37) ·
worse 10 (RW7 -30.22, GEN-261019-10 -10.35, NS4 -4.50, NS4-FD -4.14, MF3 -3.14, GEN-261026-07 -2.06, CWT05-m05-v5
-1.78, NS1 -0.88, ST8 -0.82, GEN-261027-01 -0.06; total -57.95) · unchanged 2 · no tune 3. Net -45.6R
(-15.3R without RW7).

## Decision code (for the owner; nothing changes without a yes)

- **U7-NONE**: no Workbench Testing copy from item 7. The 11-16 WB copies of L3-lowdist (WB4), RW7 (WB3), RW1 (WB3),
  GEN-261026-03 (WB1) and GEN-261027-01 (WB5) keep running and are judged on their own live records. This run
  validates none of them.
- **U7-RERUN** (recommended, routine): repeat this exact pipeline (same menus, same split rule, code in code/) when a
  setup reaches 15 active days and 30 trades. Today only 5 of the 20 have 15+ traded sessions.

## Rule changes inside the window (research/ledger.jsonl), so results are not read as setup effects

10-20 per-setup -2R loss stop in Testing 1/2 (latched 10-23; off in Testing 1/2 and Gen from 10-23, ST-A) · 10-28/29
Primary sizing and the Primary -2R latch · 10-30 testing cost filter (skip stop-exit cost > 0.15R; this caps the stop
cost gate) · 11-12 LR1 flatten time, LR8 cost model for pnl_adj from 11-12 (fit and check halves partly use different
cost models), On Deck build / GEN graduation / testing-area moves · 11-16 ROT1 rotation, RW7 On Deck → Testing F ·
11-17 TSZ1 half-size testing lots (R comparable, $ not) and the WB copies going live. Several setups changed account
inside their window. R is per-trade risk-normalised, so the moves do not change R.

## Caveats

Check halves are short: 2-13 sessions; 10 of the 17 tunes had < 15 check trades or < 4 check days. Exit tunes can only
exit earlier than live. They walk 1-minute bars up to the live exit, and the live exit cost stays in (conservative).
Gate features are measured on the last completed 1-minute bar before entry. The stop-cost feature is the LR8 formula
(max($0.02, 4 bp) + $0.01) / risk, because the journal field is missing on about half the trades (set before
scoring). ITA on 10-27 needed its split-adjusted bars rescaled to live prices (3:1). That was found and fixed during
the run and changed no verdict. SEC/TAF fees are left out of the random-entry engine (tiny). No 2-year re-score was
run: with no pass, there is nothing to carry into the Workbench 2-year test. Scratch data were deleted.
