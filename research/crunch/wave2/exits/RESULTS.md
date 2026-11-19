Educational only — not financial advice

# Wave 2 item 5 — WB2-NEXT: later / larger exits on the gap-down short fades, plus the SPY-since-entry read-out

Crunch 2026-11-19, after the close. This is research and proposals only. No config, setup, exit or runtime change was made, nothing is merged, and no final decision is taken without the owner.
- The plan was written before any variant was scored: [PLAN.md](PLAN.md), sha256 `2d176f12…a1885`, 22:11 UTC. The Skeptic stage commits it.
- Code is in `code/` and numbers are in `data/`.
- The locked block 2024-11-01..2025-02-28 was not read. No 2-year data was used.
- Costs are in: the LR8 live model through `mcf.costs.lot_costs` on every arm, with records before 11-12 re-costed to the same basis (DQ-P3).

**Configurations: 9 pre-registered** (Y1-Y3 x RW3, RW5, L3-rsi5hi). The bar is t ≥ max(1.5, √(2 ln 9)) = **2.10**.
- **2 already-counted configs were re-scored** (the RW3-WB4 / RW5-WB4 SPY exits, first counted by UPDAY).
- **6 more were seen, descriptive only.** The replay ran over all five W5 family setups, so Y1-Y3 on RW1 and RW7 were also computed. That puts the honest look count at 15. At N = 15 the bar is 2.33, and the Y1 verdict below holds at both bars.

**Eligibility changed under the pre-registered rule.** On the LR8 basis, L3-rsi5hi's avg R without its best day is −0.003 (best day 102% of the total). It therefore fails "w/o best day > 0", and the verdicts use **RW3 + RW5**. L3-rsi5hi is shown as a sensitivity check.

**Deviation from the plan (one, conservative).** The plan priced replayed stops and flattens at max(1c, 1 bp) + 1c. They were priced instead with the LR8 model itself: stops at max(2c, 4 bp) and flattens at max(1c, 1 bp), on both arms. This makes the parent replay match live more closely: its mean gap fell from −0.02R to about +0.01R.

**Data.**
- Trades: run-1 live trades from all ten accounts, 10-12..11-17, 27 sessions. Signals that appear in two accounts are counted once.
- RW3 + RW5: 383 trades (312 Primary, 71 Testing 1).
- Bars: 1-minute SIP release packs. All 1,445 family trades had bars.
- 11-18 and 11-19 have no pack yet, so 37 RW3/RW5 trades from those days are not scored.

## Failures and nulls first

| class (RW3 + RW5, 383 paired trades) | Δ R/trade (RE) ± SE | t | sign-flip p | weeks same sign | verdict |
|---|---|---|---|---|---|
| **Y2: trail after +1R** (target cancelled at +1R, stop = best − 0.5R) | +0.005 ± 0.012 | 0.42 | 0.47 | 2 of 6 | **FAIL, null.** Halves +0.022 / −0.019. RW3 −1.2R, RW5 +1.5R. |
| **Y3: target set from the fill** (same reward:risk from the fill price) | +0.026 ± 0.016 | 1.58 | 0.09 | 6 of 6 | **FAIL** (t, perm). Halves +0.056 / −0.010. RW3 +2.8R, RW5 +5.6R. |
| **SPY-since-entry exit** (RW3 at 0.30%, RW5 at 0.40%, on the parents' own live trades) | +0.015 ± 0.018 | 0.83 | 0.38 | 5 of 6 | **FAIL, null.** RW3 −0.03R (16 better / 17 worse). RW5 +3.4R (17 / 11), but its best day is 53% of the gain (`1 day`). |

- **Trail after +1R does nothing on this family.** In the replay only 55 of 383 trades ever arm the trail. Those that do give back about as much as they gain.
  - On L3-rsi5hi the target sits about 0.5R away, so it fills before +1R and Y2 never applies (−1.8R in total, from 1 trade).
  - RW7 (descriptive): −7.3R (21 better / 38 worse).
- **Setting the target from the fill agrees with the root-cause result** (execution.md, bracket anchoring: +10.3R, of which 11-19 alone was +12R).
  - On this family it is mildly positive but not significant, and its later half is negative.
  - It is not a remedy for 11-19's misses.
- **Live WB4 copies, 3 sessions, descriptive only.** Entry gates and fills differ, so this is not a paired test.
  - RW3-WB4 made +2.45R on 17 trades (7 SPY exits), while RW3 in Primary made −4.47R on 25.
  - RW5-WB4 made +3.07R on 13 trades (3 SPY exits), while RW5 made +1.77R on 20.
  - On signals matched to the parent (same symbol, signal within 5 min), the copies trail the parents: RW3 13 trades, −1.04R vs +0.22R; RW5 12 trades, +2.34R vs +4.70R.
  - Neither the 27-session counterfactual nor 3 live sessions show an edge, so the copies should keep running unscored. Per WB2-SHADOW-N, 120 or more paired trades are needed for a verdict.

## The one class that passes: Y1, target at 1.25x the parent's distance (from the signal price, stop unchanged)

| | RW3 + RW5 (verdict) | calibrated trades only | + L3-rsi5hi (3 setups) |
|---|---|---|---|
| Δ R/trade, random effects ± SE | **+0.044 ± 0.017** | +0.056 ± 0.018 | +0.053 ± 0.013 |
| t (bar 2.10; 2.33 at N = 15) | **2.58** | 3.16 | 4.01 |
| sign-flip p | 0.002 | 0.002 | 0.0006 |
| leave-one-week-out folds positive | 6 of 6 | 6 of 6 | 6 of 6 |
| halves (early / late) | +0.055 / +0.036 | | |
| family avg R w/o best day, parent → Y1 | +0.051 → **+0.087** | +0.113 → +0.161 | +0.064 → +0.110 |
| best day's share of the gain | 31% | 30% | 20% |
| total Δ | +17.4R | +18.3R | +27.9R |
| verdict | **PASS** | PASS | PASS |

Per setup (Remedies rule: every affected setup, improvements and worsenings with sizes; n trades / 27 sessions):

| setup | n | parent avg / w/o best (share) | Y1 avg / w/o best (share) | Δ/trade ± SE (t) | better / worse | Δ total | shrunk Δ |
|---|---|---|---|---|---|---|---|
| RW3-gapdn-rsi5pop-flowsell-short-FD | 185 | +0.176 / +0.057 (72%) | +0.239 / +0.110 (60%) | +0.063 ± 0.021 (2.98) | 69 / 13 | +11.7R | +0.050 |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | 198 | +0.136 / +0.045 (72%) | +0.165 / +0.065 (66%) | +0.029 ± 0.017 (1.67) | 68 / 16 | +5.7R | +0.038 |
| L3-gap-slope-rsi5hi-FD (not eligible) | 152 | +0.094 / +0.010 (92%) | +0.163 / +0.069 (68%) | +0.069 ± 0.018 (3.95) | 105 / 5 | +10.5R | — |
| RW7 (descriptive) | 715 | +0.007 | +0.023 | +0.016 ± 0.008 (2.11) | 178 / 45 | +11.4R | — |
| RW1 (descriptive) | 195 | −0.011 | +0.006 | +0.017 ± 0.012 (1.36) | 46 / 16 | +3.3R | — |

All five family setups improve and none gets worse. That fits the Remedies rule: the change is targeted at one failure mode, the target being too close, which shows up across the whole family.

**Mechanism.**
- In the replay, 124 of the 166 RW3/RW5 trades that reached the parent target went on to reach 1.25x (+0.245R each, +30.4R in total).
- The other 42 were flattened at 15:55 instead of banking the target (−0.310R each, −13.0R).
- None turned from a target into a stop.
- This mirrors W5: earlier exits cost this family 0.025-0.030R per trade, and a larger target gains about 0.04-0.06R. The fade usually runs further than one signal-R.

**Calibration.** The parent arm of the replay lands within 0.10R of live, with the same exit type, on 85% of RW3 trades, 82% of RW5 and 93% of L3-rsi5hi. Its mean is +0.005 to +0.019R above live. Both arms come from the same engine, so this bias cancels in Δ. On calibrated trades only, Δ is larger.

## What this does and does not say about 11-19

- 10 of 14 lots reached +0.8R or more before reversing, and no ST7 or L3 lot reached its target.
- None of these classes would have saved 11-19:
  - A larger target is further away.
  - Setting the target from the fill was +12R on that one day but is not significant over 27 sessions.
  - The trail needs +1R, and only ST7's 5 lots peaking at 0.99-1.32R would have come close.
- ST7-FD and L3-fromopen sit outside this family and were not tuned (L3-fromopen is protected).
- The 11-19 loss is a universe and trigger defect (FINDINGS R1/R2), not an exit problem.
- 11-18 and 11-19 have no bars, so Y1's effect on them is unmeasured.

## Caveats

- **Source.** The replay uses 1-minute bars. A stop is taken before a target inside the same bar, and a target needs a 3 bp touch-through. This is conservative for both arms.
- **Unmodelled live effects.** Partial fills, the new U9-TGT quote check (11-19) and the 11-20 rounding of take-profit prices toward entry are not modelled. The rounding change moves a 1.25x limit by under 1 cent.
- **Latch interaction.** Primary has a −2R per-setup latch (since 10-29). Y1 banks winners later, so the realized R that the latch reads lags. Y1 could therefore latch a setup slightly earlier on some days. This is not modelled, and the paired Δ is per trade as taken.
- **Regime.** Six weeks of mostly choppy-to-down tape. The gain depends on gap-down fades drifting into the close, because 42 trades end at the 15:55 flatten. On a strong up-close day Y1 gives back more. Weeks: +0.027, +0.071, +0.057, +0.073, +0.010, +0.068.
- **Small effect.** At +0.044R per trade, a live paired shadow needs about 255-320 trades to confirm +0.05R (W5 Part B), which is roughly 6-8 weeks of RW3 + RW5.
- **Earlier work.** RW3 V13 (target 1.0 → 0.8R) failed (research/workbench/RW3…/RESULTS.md), which is consistent. Y1 is the first larger-target test on this family. The GUARDRAILS check found no prior failure of the same class.

## Rule changes inside the window (research/ledger.jsonl)

**Inside the scored window, 10-12..11-17:**
- 10-20 twin-symbol block.
- 10-22/23 per-setup latch off in testing.
- 10-28 Primary sizing ×2.
- 10-29 Primary −2R per-setup latch.
- 10-30 L3-rsi5hi to Primary.
- 11-11 TEAM-6.
- 11-12 LR1-LR8 cost model. Re-costed here to one basis.
- 11-16 ROT1.
- 11-17 TSZ1 half-size testing lots (R comparable), 15 WB copies, the SPYEXIT engine with the RW3-WB4 / RW5-WB4 copies, and the promotion hold.

**After the window, and in the live WB4 read-out:**
- 11-18 GY-BENCH, SRCV1, recorded quotes.
- 11-19 C3 batch (C3-EPOCH / BASE1, EXIT100, BAR2, C3-WB, ROT / ROT2), U9-ETB, U9-TGT, DQ-P3 / DQ-P4.
- 11-20 FOOTRACE-EXIT, GY-FOOTRACE, stop / take-profit rounding direction, and the ultimate_1119 testing admissions.

## Proposals (owner decides; nothing is applied)

- **WB2-Y1-SHADOW (recommended).** Run "target 1.25x" as a journal-only paired shadow overlay on RW3's and RW5's own live signals: same polls, no orders, no slot.
  - Read-out uses WB2 W6: mSPRT harm stop, then confirmation at ≥ 120 paired trades / ≥ 15 sessions with t ≥ 1.645.
  - L3-rsi5hi and RW7 are optionally included as information only.
  - Needs: the owner's yes to WB2-OVERLAY (Wave 1, still pending), built after hours.
  - Conflicts with standing rules:
    1. RW3 and RW5 are Primary members. Any real change to their exits is a Primary change. Under C3-EPOCH it is allowed only in the Friday-after-close epoch window, it needs the adversarial review (GUARDRAILS 11-19), and it needs a ledger entry. Not before confirmation.
    2. The setup-freeze rule: no exit change during 09:30-16:00 ET.
    3. C3-WB requires a paired shadow A/B final pass before adoption. This proposal is that pass, so there is no conflict.
    4. Run as a Workbench copy instead, it would be a brand-new setup (11-18 rule), it would be unpaired, and it could not be verdicted (W5 Part B). Hence the overlay.
- **WB2-GDX-NOTE-2 (recommended, backlog note only).** For gap-down short fades:
  - Trail after +1R: null (+0.005R, t 0.42).
  - Target set from the fill: +0.026R, t 1.58, later half negative. Do not re-try without new evidence.
  - Larger target: positive. This adds to W5's "earlier exits hurt" note.
- **WB4-SPY-READ (information).** The SPY-since-entry exit is null on the parents' 27-session record (RW3 −0.03R, RW5 +3.4R with a `1 day` tag). Keep both copies running as decided. They should not count toward On Deck / Primary without a paired read-out of ≥ 120 trades.
- **WB2-NEXT-2 (optional, next run).** Test a target of 1.5x as one pre-registered class on the same family. The 2-year replay can be added as a separate source with weight 0, excluding the locked block.
