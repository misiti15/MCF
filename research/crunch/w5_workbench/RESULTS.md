# W5-workbench — why Workbench tunes fail out of sample, what it takes to see a real one, and a better protocol (WB2)

*Educational only — not financial advice.* Crunch 2026-11-18, after the close. Research and proposals only: no config,
setup, exit, latch or runtime change; nothing merged that affects trading. Promotion hold on. L3-gap-slope-fromopen-FD
was not tuned. Locked block 2024-11-01..2025-02-28 not read (no 2-year data used). The plan was committed before any
scoring: [PLAN.md](PLAN.md) (commit 6a464780b). WB2 spec: [PROTOCOL.md](PROTOCOL.md). Code: `code/`. Numbers: `data/`.

**Configurations tried: 15** (Part D: 3 exit classes x 5 setups), plus **1 post-plan check** (C3-WB5's refire-off on
L3-rsi5hi, re-scored as a paired effect; reported, no verdict). Bar t ≥ max(1.5, √(2 ln 15)) = **2.33**. Parts A-B
re-use outputs that U7, L3 bespoke and W4 already counted and add no configurations.

**Data.** Live journals (run 1) of all ten `mcf-data*` branches, 10-06..11-18. R after costs = pnl_adj / (|entry − stop|
× shares). Identical signals in two accounts are counted once (27,052 trades, 219 setups). Part D walks 1-minute SIP bars
from the public release packs `bars-2026-10/11`, streamed one session at a time and deleted after use. 11-18 has no pack
yet, so its trades keep their live R (Δ = 0). Bars cover 1,445 of 1,549 demo trades.

## Failures first

- **WB2 demo: 0 of 3 exit classes pass, and all three are harmful.** On five gap-down short fades (RW7, RW5, RW3,
  RW1, L3-rsi5hi; 1,549 trades, 28 sessions), each earlier-exit class lowers R. X1 = target at 0.75x: −0.030R per
  trade, t −2.58, sign-flip p 0.009 on the negative side; 5 of 5 setups worse (−49.6R). X2 = break-even after +0.5R:
  −0.027R per trade; 4 worse (−45.0R), 1 better (+2.2R). X3 = 60-minute stop when MFE < 0.25R: −0.025R per trade;
  5 of 5 worse (−41.4R). WB2 rejects all three.
- **The old protocol would have shipped the harmful one.** It picks each setup's best class on the earlier half and
  checks it on the later half. Here it picks X2 (break-even) for RW7, RW1 and RW5, because X2 scored +4.3R, +4.0R and
  +0.3R on the fit halves. On the check halves those picks lose −22.0R, −1.8R and −7.2R. That is the same in-sample
  trap that U7 (fit +63.6R → check −45.3R) and C3-WB5 item 4 (1R target: fit +0.553 → check +0.011) fell into.
- **C3-WB5's one deployed pass is not evidence yet.** L3-rsi5hi-WB5 turns refire off, and it went live in Testing C
  on 11-19. Re-scored as a paired effect on the parent's full record (158 trades, 23 sessions), it is **+0.003R per
  trade, t 0.11**: the 25 refires average −0.018R and the first entries average +0.124R. The halves flip sign (fit
  −0.029, check +0.033). The pass rests on 15 refire trades in the check half. No proposal to undo it: it is a testing
  copy. It just should not count toward promotion before a paired read-out.

## Part A — why ~100+ tunes passed in-sample and failed on unseen sessions

**A1. The size of a tune's fit gain predicts nothing, and gates predict the wrong sign** (U7, 250 eligible candidates;
`data/A_diagnosis_out.txt`).

| | n | Spearman (fit gain, check gain) | mean check gain | share of check gains > 0 |
|---|---|---|---|---|
| all | 250 | **−0.26** | −1.23R | 35% |
| gates | 229 | **−0.37** | −0.25R | 38% |
| exits | 21 | +0.21 | −11.9R | 5% |
| the 17 chosen (best fit per setup) | 17 | — | fit +63.6R → check **−45.3R** | — |
| top decile by fit gain | 26 | — | fit +4.88 → check **−3.35** each | — |

**Why gates go negative.** A gate's gain is minus the R of the trades it drops. On a short record those trades' R is
mostly the parent's own level in that half plus noise. Parent level does not persist. The 20 U7 parents' fit-half avg R
vs check-half avg R has Spearman **−0.47**. Across all 71 live setups with ≥ 40 trades, the first half of a setup's own
sessions vs the second half has Spearman **−0.22**, and the sign agrees only 62% of the time (A4). So a gate that "fixed"
a bad fit half is mostly removing trades from a period that then mean-reverts. U7 check gain vs minus the parent's
check avg has Spearman +0.40: gate "gains" track the parent's level, not the gate. W4 found the same (fit/check sign
agreement 56%, top-quartile effects shrink to 0.23x).

**A2. Pooling across setups helps, but only when the class is fixed in advance.** Grouping U7's 229 gates into 16
classes (e.g. "drop the bottom third of rvol") gives a class-level fit vs check Spearman of +0.13 (16 classes). That is
better than −0.37 per candidate but still weak. Only 7 of 16 classes keep their sign. Taking the best pooled-fit class
and applying it to all 15 setups would have lost −15.4R on check, against −45.3R for per-setup picks. Pooling cut the
damage by two thirds; it did not find an edge. Lesson: pooling cuts selection noise, but a class picked by searching on
the data still carries the winner's curse. WB2 therefore pre-registers a small number of classes from a mechanism, and
the evidence for each comes from all sessions, not from a single fit pick.

**A3. Segments disagree with each other even for a 400+-session engine.** For L3-fromopen's 21 variants (Δ vs parent),
the Spearman between 2-year TRAIN and VALID is **−0.32** and between TRAIN and FWD **−0.46**. Replay vs VALID is +0.32.
The "regime shift between halves" is real at every horizon. With 21 one-knob variants of one setup, no segment ranks the
next.

**A4. Noise model of live R** (`data/A4_icc.csv`).

| quantity | value |
|---|---|
| per-trade SD of R (setups with ≥ 30 trades) | **0.84R** (IQR 0.73-0.97) |
| trades per traded day | median 9.8 (IQR 5.6-20.1) |
| same-day correlation of trades within a setup (ICC) | median **0.22** (IQR 0.12-0.31) |
| design effect (cluster SE² / iid SE²) | median **3.7**; 1.6 at 2-5 trades/day, 5.0 at > 10 |
| correlation of a setup's daily R with other same-side setups that day | median **0.37** (a common day / regime factor) |
| same per-trade paired Δ of an exit tune (Part D) | SD **0.31R**, ICC **0.04** |

Two things follow. (1) Day clustering divides the effective sample by ~4: 430 trades over 13 days (RW7's U7 check)
behave like ~120 independent trades. (2) Pairing removes almost everything. An exit tune walked on the parent's own
trades has an SD of Δ of 0.31R instead of 0.84R, and almost no day clustering (ICC 0.04 vs 0.22). The common day factor
cancels because both arms see the same day.

**A5. The multiple-testing bar is not what broke U7.** With K = 20 the best null t averages 1.86, and the 2.45 bar holds
the family-wise false-pass rate near 13%. With K = 265 it averages 2.84 against a 3.34 bar. U7, U8 and W4 all reported
0 passes, so the bars did their job. What failed was the **selection step before the bar**. Picking one of 15 candidates
on 3-13 fit sessions picks noise, and the check half (2-13 sessions) is too short to tell (Part B). In-sample "passes"
(P4 60/60, and the owner's 11-16 "meets or exceeds, no significance hurdle" rule) had no bar at all.

**Tune types.** On proven parents, exit tunes mostly cut winners. U7 exits: 1 of 21 positive on check. Part D: earlier
exits −0.025 to −0.030R per trade. L3 bespoke: none valid. Gates on losing parents mostly remove trades that random
removal would also remove (W4: excess +31.8R over 31 setups vs +135R from random removal).

## Part B — power: how much data a +0.05R / +0.10R tune needs

80% power, one-sided bar, day clustering via the design effect 1 + (m−1)·ICC (`data/B_power.csv`). Trades (sessions):

| design | bar | +0.05R, 3 trades/day | +0.10R, 3/day | +0.05R, 10/day | +0.10R, 10/day |
|---|---|---|---|---|---|
| **unpaired** copy vs parent (two separate live records: today's arena WB copies) | 1.645 | 5,000 (1,667) | 1,250 (417) | 10,400 (1,040) | 2,600 (260) |
| | 2.45 | 8,760 (2,920) | 2,190 (730) | 18,200 (1,822) | 4,550 (456) |
| **paired gate** (drop 1/3 of the parent's own trades) | 1.645 | 833 (278) | 208 (70) | 1,733 (174) | 433 (44) |
| | 2.45 | 1,460 (487) | 365 (122) | 3,040 (304) | 759 (76) |
| **paired exit tune** (same trades, counterfactual or shadow on the same signals) | 1.645 | 255 (85) | 64 (22) | 321 (33) | 80 (9) |
| | 2.45 | 447 (149) | 112 (38) | 563 (57) | 141 (15) |

What a typical U7 check half could resolve (1 SE of the avg difference): 30 trades / 6 days → unpaired **0.30R**,
paired gate 0.12R, paired exit 0.06R. 60 / 9 → 0.23 / 0.09 / 0.04R.

**Reading it.**
- **An unpaired record cannot verdict a +0.05R tune within any horizon MCF has.** The "copy in Testing X vs parent in
  Testing Y" design needs about 1,000-3,000 sessions, i.e. years. The 11-17 WB copies (15 of them) will never be
  verdicted by their own records.
- **C3-WB's final pass (40 paired shadow trades over 5 sessions) is underpowered for small effects.** At 40 paired
  exit trades the SE is ~0.05R, so +0.05R gives t ≈ 1. It is fine as a harm check, and it detects +0.10R only at around
  65-110 paired trades.
- **Pooling multiplies the sample.** Five setups of one mechanism give ~1,500 paired trades in 28 sessions. That
  resolves ±0.03R (Part D: SE 0.008-0.018R).

**Monte Carlo on the real paired noise** (`data/B_powersim.csv`, 300 reps). The demo's X1-X3 deltas, demeaned so the
true effect is 0, are given a planted effect on one class, and sessions are resampled. Both protocols here are already
paired, so the gap below comes from pooling plus using all sessions, not from pairing.

| sessions | planted effect | old protocol: per-setup fit→check, any true pass | old: false pass (a null class) | WB2 detects | WB2 false pass |
|---|---|---|---|---|---|
| 28 | 0 | 2% | **15%** | 1% | **3%** |
| 28 | +0.03R | 45% | 8% | **84%** | 3% |
| 28 | +0.05R | 98% | 4% | 100% | 4% |
| 56 | +0.03R | 81% | 2% | 100% | 3% |

Caveat: the planted effect is the same in every setup. If the true effect differs between setups, pooling gains less.
The random-effects τ and the shrinkage step are there for that case.

## Part C — the proposal: WB2 (full spec in [PROTOCOL.md](PROTOCOL.md))

1. **Hypotheses are tune classes, not per-setup picks.** At most three pre-registered classes per mechanism family
   (≥ 3 setups that share the mechanism tag, C3-MECH). Each class has one fixed parameter taken from the mechanism or
   from earlier work. Nothing is searched on the data being scored.
2. **Paired on the same signals.** Exits, refire and gates are scored as the per-trade Δ on the parent's own live trades
   (1-minute counterfactual walk, conservative fills, costs in). Live confirmation runs as a **shadow overlay on the
   parent's signals** (same polls, run 3), never as an unpaired copy record.
3. **Use all sessions, check stability instead of making one split.** Day-clustered pooled t (random effects, DL) plus a
   day-level sign-flip test and leave-one-week-out folds (≥ 75% same sign). A single fit/check split throws away half the
   data and is dominated by the regime swing between halves.
4. **Shrink per setup.** Empirical-Bayes Δ_i = μ + B(θ_i − μ). A class is adopted only for setups whose shrunk Δ > 0,
   and only if the class passes as a whole.
5. **Bar** t ≥ max(1.5, √(2 ln N)), with N = classes x setups across the lineage; permutation p < 0.01; avg R w/o best
   day not worse.
6. **Sequential live confirmation.** mSPRT (always-valid) on the daily paired Δ of the shadow overlay. Stop for harm as
   soon as e ≥ 20 on the negative side. Confirm on the positive side or at the power-based horizon in the Part B table
   (exits ~120-150 paired trades for +0.10R; gates ~400+).
7. **2-year replay as a prior only once calibrated.** Weight 0 while the rule-21 audit fails (U11: 87.1% match, 44% for
   L3-fromopen). After that, use it as the prior mean of μ with a discount set by its out-of-sample rank correlation.
8. **Harmful classes are results too.** A class that is significantly negative for a family goes into the backlog as a
   "don't" note for that mechanism, and that saves future search.

## Part D — demonstration: WB2 on 5 gap-down short fades (3 classes, 15 configs)

Pooled per class (`data/D_pooled.csv`):

| class | pooled Δ/trade (RE) | day-clustered Δ ± SE | t | sign-flip p | weeks positive (leave-one-out) | shrunk Δ > 0 | avg R w/o best day: parent → variant | mSPRT (e ≥ 20) | verdict |
|---|---|---|---|---|---|---|---|---|---|
| X1 target 0.75x | −0.030 | −0.032 ± 0.012 | **−2.58** | 0.009 (negative side) | 0 of 6 | 0 of 5 | +0.027 → −0.001 | no crossing (max e 3.6) | FAIL — harmful |
| X2 BE after +0.5R | −0.027 | −0.028 ± 0.015 | −1.78 | 0.039 (negative side) | 0 of 6 | 0 of 5 | +0.027 → −0.001 | no crossing (2.3) | FAIL |
| X3 60-min stop if MFE < 0.25R | −0.025 | −0.027 ± 0.018 | −1.36 | 0.089 (negative side) | 0 of 6 | 0 of 5 | +0.027 → +0.001 | no crossing (1.4) | FAIL |

Per setup (`data/D_per_setup.csv`; avg R w/o best day with the best day's share; n/a = total ≤ 0):

| class | setup | trades / sessions | parent avg / w/o best (share) | variant avg / w/o best (share) | trades changed | Δ/trade ± SE (t) | Δ total R | shrunk Δ |
|---|---|---|---|---|---|---|---|---|
| X1 | L3-rsi5hi | 158 / 23 | +0.101 / +0.024 (82%) | +0.057 / −0.000 (100%) | 61% | −0.044 ± 0.030 (t −1.46) | −7.0 | −0.030 |
| X1 | RW1 | 219 / 27 | −0.028 / −0.056 (n/a) | −0.049 / −0.079 (n/a) | 37% | −0.022 ± 0.021 (t −1.01) | −4.7 | −0.030 |
| X1 | RW3 | 199 / 27 | +0.167 / +0.052 (73%) | +0.099 / +0.002 (98%) | 47% | −0.068 ± 0.029 (t −2.36) | −13.6 | −0.030 |
| X1 | RW5 | 206 / 27 | +0.144 / +0.057 (66%) | +0.115 / +0.040 (70%) | 48% | −0.029 ± 0.020 (t −1.46) | −6.0 | −0.030 |
| X1 | RW7 | 767 / 26 | +0.016 / −0.005 (130%) | −0.008 / −0.028 (n/a) | 38% | −0.024 ± 0.012 (t −2.06) | −18.3 | −0.030 |
| X2 | L3-rsi5hi | 158 / 23 | +0.101 / +0.024 (82%) | +0.068 / −0.020 (122%) | 6% | −0.033 ± 0.019 (t −1.70) | −5.2 | −0.029 |
| X2 | RW1 | 219 / 27 | −0.028 / −0.056 (n/a) | −0.018 / −0.049 (n/a) | 16% | +0.010 ± 0.023 (t +0.44) | +2.2 | −0.018 |
| X2 | RW3 | 199 / 27 | +0.167 / +0.052 (73%) | +0.090 / −0.020 (119%) | 15% | −0.077 ± 0.031 (t −2.52) | −15.3 | −0.035 |
| X2 | RW5 | 206 / 27 | +0.144 / +0.057 (66%) | +0.111 / +0.017 (87%) | 17% | −0.033 ± 0.027 (t −1.23) | −6.8 | −0.028 |
| X2 | RW7 | 767 / 26 | +0.016 / −0.005 (130%) | −0.007 / −0.029 (n/a) | 17% | −0.023 ± 0.016 (t −1.43) | −17.6 | −0.025 |
| X3 | L3-rsi5hi | 158 / 23 | +0.101 / +0.024 (82%) | +0.092 / +0.029 (76%) | 16% | −0.009 ± 0.023 (t −0.41) | −1.5 | −0.025 |
| X3 | RW1 | 219 / 27 | −0.028 / −0.056 (n/a) | −0.052 / −0.080 (n/a) | 26% | −0.025 ± 0.019 (t −1.27) | −5.4 | −0.025 |
| X3 | RW3 | 199 / 27 | +0.167 / +0.052 (73%) | +0.116 / +0.003 (98%) | 24% | −0.051 ± 0.030 (t −1.68) | −10.2 | −0.025 |
| X3 | RW5 | 206 / 27 | +0.144 / +0.057 (66%) | +0.116 / +0.028 (79%) | 27% | −0.028 ± 0.027 (t −1.02) | −5.8 | −0.025 |
| X3 | RW7 | 767 / 26 | +0.016 / −0.005 (130%) | −0.008 / −0.029 (n/a) | 30% | −0.024 ± 0.024 (t −1.03) | −18.6 | −0.025 |

Improve / worsen per class (Remedies rule): X1 0 improve / 5 worse (−49.6R); X2 1 improve (RW1 +2.2R) / 4 worse
(−45.0R); X3 0 / 5 worse (−41.4R). The random-effects τ is ~0 for X1 and X3: the harm is the same size in every setup,
which is the case where pooling earns the most.

Old protocol on the same data (`data/D_oldprotocol.csv`): fit picks X2 for RW7, RW1 and RW5 and nothing for RW3 and
L3-rsi5hi. On the check halves the picks lose **−31.0R**. WB2 rejects X2 for the whole family.

What can be salvaged (optimism, honestly): (1) **Holding to the parent target is right for this family.** Each
earlier-exit idea costs ~0.025-0.030R per trade, about 40-50R over this window across the five setups, and that kind of
search can now stop for gap-down fades. (2) WB2 resolves effects of ±0.03R per family in ~28 sessions, and the U7-style
pipeline cannot. (3) The next useful WB2 classes for this family go the other way: **later or larger exits** (target
1.25x, a give-back trail only after +1R). These cannot be walked "earlier only" from live exits, so they need the
calibrated replay or a shadow overlay. They are proposed as the next WB2 run, not scored here.

## Rule changes inside the window (research/ledger.jsonl), so results are not read as setup effects

10-20 twin-symbol block · 10-22/23 testing per-setup latch off · 10-28 Primary sizing · 10-29 Primary −2R per-setup
latch, BAR90 · 10-30 L3 re-promoted · 11-11 TEAM-6 · 11-12 LR1-LR8 (after-cost R, live cost model; records before and
after use different cost bases) · 11-13 RW6/ST4 to the arena · 11-16 ROT1 rotation, RW7 On Deck → Testing F · 11-17 TSZ1
half-size testing lots (R comparable), 15 WB copies, the SPYEXIT engine and the RW3-WB4 / RW5-WB4 SPY-exit copies,
promotion hold · 11-18 GY-BENCH, SRCV1, recorded quotes, ODPREP · 11-19 C3 batch (C3-WB, C3-WB5 refire copy, EXIT100,
BAR2, ROT, NS5) takes effect after this window. RW3 and RW5 are Primary members, and part of their record ran under the
−2R latch (from 10-29). The latch removes post-latch trades, so a counterfactual on a trade that exists is unaffected.
The demo's paired Δ uses each trade as it was taken.

## Caveats

- The exit walk only allows **earlier** exits than live. Inside a bar it takes the stop first. A target must trade
  through by 3 bp. Break-even and time-stop exits pay an extra exit cost on top of the live costs. All of this is
  conservative for the variants. 11-18 and 104 other trades have no bars and keep Δ = 0.
- RW3 and RW5 often trade the same symbol-day, so their deltas are correlated. The pooled SE uses the larger of the
  random-effects SE and the day-clustered SE over all five setups, and the sign-flip works on pooled daily sums.
- The Monte Carlo plants a homogeneous effect, and session resampling ignores autocorrelation across days.
- The power table uses the median SD and ICC. Hold setups (SD ~0.93) need ~25% more trades than target setups (~0.76).
- Outside methods drawn on (standard references, no data fetched): DerSimonian & Laird (1986) random effects; Efron
  (2010) empirical Bayes; Johari, Pekelis & Walsh (2017) always-valid mSPRT; Deng et al. (2013) CUPED, paired variance
  reduction; Bailey, Borwein, López de Prado & Zhu (2015) probability of backtest overfitting (CSCV); White (2000)
  Reality Check / Hansen (2005) SPA for best-of-K selection.
- Scratch data (journals, bar paths) were deleted after the run.

## Decision codes (owner; nothing changes without a yes)

- **WB2-PROTOCOL** (recommended): adopt PROTOCOL.md as the Workbench evaluation standard. It amends C3-WB rules 3-4:
  classes per mechanism family, paired, all sessions, pooled + shrunk, permutation and leave-one-week-out checks.
  Research-process only; no trading change.
- **WB2-OVERLAY** (recommended, runtime: after hours, adversarial review if it touches Primary's path): run exit and
  refire WB variants as journal-only **shadow overlays on the parent's own signals** (run 3) instead of separate copies.
  Pairing is exact, the overlay takes no arena slots (more reps for low-rep setups), and verdicts come in ~30-150
  sessions instead of never.
- **WB2-SHADOW-N** (recommended): replace "40+ paired trades / 5+ sessions" with the power-based horizon plus mSPRT
  early stop for harm. Exits: ≥ 120 paired trades and ≥ 15 sessions for +0.10R. Gates: ≥ 400 paired trades. Report
  the SE with every read-out.
- **WB2-GDX-NOTE** (recommended, backlog note only): "earlier-exit tunes (target < parent, break-even at +0.5R,
  no-progress time stop) hurt gap-down short fades: −0.025 to −0.030R per trade, 14 of 15 setup x class pairs worse".
  The RW3-WB4 / RW5-WB4 SPY-since-entry exits are also an earlier-exit class. Read them out with the paired overlay
  before any verdict.
- **WB5-REFIRE-FLAG** (information): L3-rsi5hi-WB5 (refire off) is +0.003R per trade, t 0.11 on the full paired record.
  Keep it running as decided. Do not count it toward On Deck / Primary without a paired read-out.
- **WB2-NEXT** (optional): the next WB2 run on this family uses later-exit classes (target 1.25x; trail after +1R),
  scored on the calibrated replay or the overlay. Pre-registered, 2 classes x 5 setups.
