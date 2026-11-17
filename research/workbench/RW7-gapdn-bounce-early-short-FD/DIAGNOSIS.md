# Workbench DIAGNOSIS — Gap-Down Early Bounce Short (all day) `RW7-gapdn-bounce-early-short-FD`
Educational only — not financial advice. Mechanic 2026-11-16 (built ~15:40-16:30 ET; research files only, no config change, no deploy).

Setup: leaderboard rank 28; live 567 trades / 23 sessions (Testing 1 / On Deck, 10-12..11-13), avg −0.021R after costs
(−12.1R; −0.051R w/o best day 11-05 +14.3R); demoted to Testing F 11-13 after the close (from session 11-16; Graveyard review
Wed 11-18). Record is swingy: last 5 sessions +6.7 / −28.7 / −2.1 / +12.3 / −20.4R.
Rule changes inside the live window (research/ledger.jsonl), so the live record mixes rule sets: 10-14 split-tape short gate
in Testing 1 (195 RW7 signals skipped; off from 11-12, ODX-1), 10-20 per-setup −2R latch in Testing (105 skips) → off 10-23
(ST-A), 10-30 cost filter stop cost ≤ 0.15R (Testing CF), 11-12 LR1 / LR5 / LR8 costs, 11-13 move On Deck → Testing F
(from 11-16). The bench replay applies TODAY's Testing F rules to every session, so none of these mixes into the comparison.

## 1. Teardown — every part (engine view, `RW7-gapdn-bounce-early-short-FD_engine.png`, blueprint `RW7-gapdn-bounce-early-short-FD.md`)
| Part | Setting | Inspected how | Finding |
|---|---|---|---|
| P1 account universe | ADV ≥ $5M core, ATR ≥ 1% | not a setup knob | — |
| P2 setup ADV floor | ≥ $95M | V01 ADV ≥ $150M (2y only; replay names passed $95M live) | 2y −0.019 → −0.019 (no change); FWD better, not kept |
| P3 price floor | ≥ $5 | V02 ≥ $10 | ~0 effect (2 trades) |
| P4 earnings blackout | 4 days | not replayable (universe) | — |
| P5 short borrow | shortable + ETB | 104/1306 live signals blocked (8%); bench uses ETB ≥ 90% of snapshots | — |
| P6 / P7 window | 09:50-15:00 | V03 start 10:15, V04 start 11:00, V05 end 14:00, V06 end 13:00 | **end 13:00 passes both tests** (live: entries after 13:00 = 173 trades −28.4R, −0.164R); start later fails 2y |
| P8 refire | off | V07 refire cd 6 | 2y −0.022 (worse) |
| P9 heat ≤ −20 | | V08 ≤ −25 | 2y −0.032 FAIL (as RW5/MF2: deeper heat = trend day) |
| P10 buyPressure < −0.15 | | V09 < −0.20 | replay +0.014 FAIL |
| P11 RSI(14) 55-65 | | V10 55-60, V11 55-62.5, V12 57-65, V13 + RSI(5) ≤ 90 | band cuts fail or ~0 (live 55-57.5 best, 2y 57.5-60 worst: no stable sub-band); RSI(5) ≤ 90 small pass |
| P12 gap < 0 | | V14 < −0.5%, V15 < −1.5% | **−0.5% passes** (live: gap −1.5..0 = 325 trades −27.7R); −1.5% fails 2y |
| P14 cap 30 lots / setup | 45 skips live | bench applies it | — |
| P15 lots / symbol 3 | | V16 → 1 (tool) | no effect (refire off: one lot per symbol-day already) |
| P16 per-setup latch | off | V17 −2R (tool) | replay +0.010 FAIL (cuts recovery days) |
| P17 account stop | −300R | backstop | — |
| P18 cost filter 0.15R | on (account) | V18 0.10, V19 off | **the filter is worth keeping** (off: 2y −0.036, worst day −62.7R); 0.10 fails replay |
| P19 quote / spread | live only | not replayable | — |
| P20 entry at market | signal-bar close | bench fills at the bar close; live slip makes replay ~+0.04R/trade richer than live on the same trades (393 matched, corr 0.93) — same for parent and copies | — |
| P21 1R 0.25 ATR | | V20 0.30 ATR | passes (meets) small; not stacked (C3/C6 weaker) |
| P22 / P23 size, max position | | sizing, not R | — |
| P24 stop 1R | | V21 1.25R, V23 BE after +0.5R | 1.25R: 2y worst day −66.6R FAIL; BE fails both |
| P25 target 1R | | V22 0.8R | meets only (replay +0.022 / 2y −0.023) |
| P27 time exit 15:55 | | V24 max hold 120, V25 flat 15:00 | max hold fails replay; flat 15:00 passes but has no per-setup live knob |
| NEW market gates (after 09:50, owner rule) | — | V26 SPY > +0.20% since 09:50 (RW3/RW5 sibling part), S1/S2/D5 0.30/0.10/0.00, V27 SPY above 09:30-09:50 high, D8 SPY last 30 min > +0.10%, E3 0.20 | **the sibling gate transfers** (0.10 best alone); the 30-min gate is the part that fixes the 2-year worst days |
| NEW stock layers | — | V28 slope ≤ 0.20 / C12 ≤ 0.05 (MF2 sibling), V29 VWAP floor −1%, V30-V32 fromOpen caps | small passes / one-test only; not kept |

## 2. Evidence — 5 worst + 5 best live trades (PNGs in this folder; IGM 11-16 is a Testing F trade from today's session)
| Trade | R | What happened | Part responsible | What WB3 does to THIS trade |
|---|---|---|---|---|
| worst1 TTD 10-14 12:25 | −1.40 stop | $11.80 name, 1R = $0.11; stopped in 17 min, MFE 0.00R | P18 cost (stop cost 0.42R; before the 10-30 filter) | dropped (cost clause / account filter) |
| worst2 PFGC 10-28 10:45 | −1.36 stop | gap −0.8% already filled (fromOpen +1.1%), above VWAP, SPY +0.11% since 09:50 | P12 shallow gap + market up after 09:50 | dropped (SPY since 09:50 +0.11% > 0.10) |
| worst3 PDBC 10-26 11:20 | −1.36 stop | commodity ETF, 1R $0.05 (cost 0.66R), SPY +0.53% since 09:50 | P18 + market up | dropped (SPY gate, cost) |
| worst4 WDAY 10-27 10:55 | −1.32 stop | SPY +0.26% since 09:50 and +0.32% in the last 30 min — shorting into a rally | market up after 09:50 | dropped (both SPY gates) |
| worst5 LHX 11-05 13:55 | −1.32 stop | afternoon, shallow gap −0.67% | P6 late entry | dropped (after 13:00) |
| best1 NVDA 11-05 11:35 | +4.21 target* | SPY −1.6% since 09:50 but bounced +0.59% in 30 min; stock −5% from open | — | **dropped** (30-min gate) — gives back |
| best2 APH 11-05 11:35 | +2.40 target | same bar / same day as NVDA | — | **dropped** (30-min gate) |
| best3 IGM 11-16 | Testing F, today | (not in the replay window) | — | n/a |
| best4 SPCX 11-05 11:35 | +2.13 target | same 11:35 bar on 11-05 | — | **dropped** (30-min gate) |
| best5 PURR 10-16 14:30 | +1.51 target | late, $9 name (cost 0.22R) | — | dropped (after 13:00, cost) |
(*R > 1 on a 1R target = the price gapped through the target on a fast 1-min bar.)

## 3. Across ALL live trades (component_analysis.txt)
- Exits: stop 148 (−1.09R avg, −161.5R), target 173 (+0.93R), flatten 246 (−0.046R). 82 of 148 stops never got +0.2R (entries
  go straight against); 94 flattened trades had +0.5R at some point. Stop/target/BE/max-hold tweaks were tested — none helps
  (§1): the bracket is not the leak.
- Time: 10:15-11:00 −22.7R (84), 11:00-12:00 +36.0R (176), 13:00-14:00 −26.1R (102); everything after 13:00 −28.4R (173).
- Gap: gap ≤ −3% +17.3R (89, +0.19R); gap −1.5..0% −27.7R (325).
- Market after 09:50: SPY 0..+0.2% since 09:50 −20.7R (74), but SPY > +0.2% +16.7R (137) — live disagrees with the 2-year
  test on the gate (below).
- 2-year (bench, 16,747 trades): the leak is DAY TYPE — SPY up days −0.235R (5,417 trades, −1,247R), flat +0.002, down +0.160.
  No stock-level sensor separates as strongly (gap, RSI, heat, VWAP, slope buckets all within ±0.05R).
- Most-often-responsible part: market state after 09:50 (2y) and late / shallow-gap entries (live and 2y).

## 4. Candidate tweaks picked (one part each, then combined)
1. NEW gate — skip when SPY is up > +0.10% since the 09:50 close (sibling part, tighter) → WB2.
2. P6 — window end 15:00 → 13:00 → WB1.
3. Combo WB3 — WB2 + NEW gate SPY last-30-min ≤ +0.20% (reference never before 09:50) + P12 gap < −0.5% + P6 end 13:00.

Where the live evidence pushes back (reported, not hidden): in the 23 live sessions the since-09:50 part removed 176 trades
at +4.7R net and the 30-min part 46 at +5.5R (incl. the 3 best 11-05 11:35 trades); the gap and end-13:00 parts removed
−12.7R and −28.4R. The 177 live trades WB3 keeps were +17.0R (+0.096R) vs the parent's −12.1R. The pass decision uses the
identical bench tests only (owner 2026-11-16), where both gates pay (RESULTS.md, ablation F1-F3).
