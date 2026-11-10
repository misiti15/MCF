Educational only — not financial advice.

# L3LEASH-2 — the L3LEASH leashes re-scored on a lab universe that live could actually short (owner 2026-11-10)

Owner, 11-10 (~13:30 ET): "L3LEASH-2 yes, LEASH shadow yes". Setup: Gap-Down Recovery Fade (all day)
`L3-gap-slope-fromopen-FD` (short). Follows research/l3leash/NOTES.md (0 of 12 leashes passed, and the lab base lost
money in every split while live Testing 1 made +55R). **Research only. No config, setup, exit, ledger or workflow change.**

## Plain-English summary
- **Verdict: still 0 of 12 leashes pass. Recommendation: keep the setup as is (no leash). Track K11 and K12 forward
  (LEASH shadow, below). Re-score after 20 forward sessions.**
- **How live decides shortability:** at each signal, live asks Alpaca whether the name is `shortable and
  easy_to_borrow` (`AlpacaBroker.can_short`, cached for the session). If not, the signal is skipped as "not
  shortable/ETB" (runner.py). Alpaca keeps no history of these flags, but every morning's `universe.csv` records them,
  and those files are committed. Their git history on mcf-data / -testing / -testing2 gives **22 daily snapshots,
  10-07..11-09, 5,623 symbols**.
- **The flags match live exactly.** On the same day, the snapshot flag reproduces live's skip/pass decision on **99.8%**
  of L3-fromopen signal symbol-days (626) and on 99.1% of all short-signal symbol-days (10,378).
- **The proxy (E90):** keep a lab trade when its symbol was shortable+ETB on ≥ 90% of the snapshot days. It agrees
  with live on **96.3%** of L3 symbol-days. It still agrees **96.0%** out of time: built from 10-07..10-23 only and
  scored on live 10-26..11-10.
  - The flags are very stable over this month: of 1,209 lab symbols, 1,088 were ETB in both halves and 35 were not ETB
    in both halves.
  - **Limit:** the proxy applies an Oct-Nov 2026 borrow list to 2024-25 trades. It can be right within weeks, but it
    cannot be checked across years.
  - Simple price / liquidity cut-offs do not work as a proxy. All lab names are liquid (ADV ≥ $20M), and the
    hard-to-borrow ones among them are still high-ADV names (AUC: price 0.83, ADV 0.60). No price/ADV threshold
    reproduces the split.
- **Restricted base vs live:** the restriction removes 25% of the setup's lab trades. The removed (non-ETB) trades are
  the worst ones (TRAIN −0.234R/trade, FWD −0.402R/trade).
  - **FWD** turns from −39.2R to **+16.5R** (403 trades, +0.041R/trade, win 55%). Live's direction is now right.
  - **On the same days as live Testing 1** (10-13..10-29):
    - lab E90 **+29.0R** (246 trades)
    - lab unrestricted −23.6R
    - live **+55.1R** (206 trades)
  - Part of the effect comes through the latch: without the non-ETB losers, the lab no longer hits −2R early on
    10-20, and that day becomes +29.2R (live: +33.6R).
  - **TRAIN / VALID still lose:** −310R (−0.132R/trade) and −191R (−0.079R/trade).
  - So the ETB proxy explains the gap in FWD, where the borrow list is current. It does not rescue 2025 to 2026-09.
    Either the borrow list then was different (the proxy's limit), or the setup really was weak then.
  - FWD's +16.5R is carried by **one day** (10-20, +29.2R, 177% of total; avg R without it −0.036). **`1 day` tag.**
- **Leashes on the restricted base:** every leash that "helps" in TRAIN/VALID does it by trading a losing base less.
  All of them lose in FWD except K12. K12 (−1R per-setup daily stop once the compass read UP-confirmed) is again the
  closest call:
  - VALID +24.1R, removing 9% of red-day losses for 8% of green-day R.
  - FWD +9.8R, removing 19% of red-day losses and giving up −2% of green-day R (i.e. a small gain).
  - It fails on: the red-day cut is under 20% in both VALID and FWD; TRAIN is −9.9R; and 2 sisters are worse by more
    than 5% in VALID.
  - Live: Primary −1.4R, Testing 1 −12.9R.
- **K11** (half size when SPY ≥ +0.40% from the open) is +26.8R in VALID but **−24.5R in FWD**, giving up 43% of
  green-day R. It also costs live R: Primary −2.5R, Testing 1 −21.9R.
- **Sisters (Remedies rule):** in VALID most leashes "help" most sisters, again because their lab bases lose. In FWD,
  where the sisters earn, K11 makes 3 better and 4 worse (−19R; L3-lowdist −22R). K12 makes 3 better and 4 worse
  (−28R; RW5-FD −33R).
- **Configurations:** 12 leashes + 2 proxy sensitivities (E100, FWD own-day flag) = **14 new; lineage total 26**.
  Paired VALID t bar at N 24 = 2.52; best is K01 at 1.92.

## 1. ETB proxy and validation (`etb_validation.csv`)
| scope | proxy | symbol-days | agree | live ETB share | proxy ETB share | ETB called not | not called ETB |
|---|---|---|---|---|---|---|---|
| L3-fromopen signals | same-day snapshot flag | 626 | 99.8% | 37.5% | 37.4% | 1 | 0 |
| L3-fromopen signals | **E90** | 629 | **96.3%** | 37.4% | 34.0% | 22 | 1 |
| L3-fromopen signals | E100 | 629 | 94.1% | 37.4% | 31.5% | 37 | 0 |
| L3-fromopen signals | E90 from 10-07..10-23, scored 10-26..11-10 | 275 | 96.0% | 25.5% | 22.9% | 9 | 2 |
| all short signals | same-day snapshot flag | 10,378 | 99.1% | 77.3% | 76.5% | 88 | 7 |
| all short signals | E90 | 10,384 | 97.3% | 77.3% | 75.0% | 257 | 23 |
| all short signals | E90 out of time | 3,987 | 96.2% | 69.6% | 67.4% | 120 | 33 |

- Live's L3 signals are mostly on names outside the lab: 63% of L3 symbol-days were not ETB live, and 33% of live L3
  trades are on symbols outside the lab's 1,226 names.
- Within the lab, E90 keeps 74.7% of L3-fromopen trades, 74.0% of L3-rsi5hi, 85% of L3-lowdist / MF2-FD / MF4-FD, and
  91-94% of MF4 / RW3-FD / RW5-FD.
- 0.1-0.3% of trades are on symbols never seen in a snapshot. Those are dropped.

## 2. Restricted base vs live (B0: −2R latch, ≤ 3 lots/symbol, ≤ 30 open, production costs; `bases.csv`)
| universe | split | trades | total R | avg R | win | day-t | avg R w/o best day |
|---|---|---|---|---|---|---|---|
| ALL (L3LEASH) | TRAIN | 2,902 | −355.3 | −0.122 | 49.7% | −2.50 | −0.141 |
| ALL | VALID | 3,021 | −166.5 | −0.055 | 50.3% | −1.38 | −0.070 |
| ALL | FWD | 408 | −39.2 | −0.096 | 48.3% | −1.10 | −0.159 |
| **E90** | TRAIN | 2,351 | −310.4 | −0.132 | 47.1% | −3.04 | −0.152 |
| **E90** | VALID | 2,408 | −191.3 | −0.079 | 48.7% | −1.90 | −0.099 |
| **E90** | FWD | 403 | **+16.5** | +0.041 | 55.3% | +0.42 | −0.036 (`1 day`: 10-20 = 177%) |
| E100 | TRAIN / VALID / FWD | 2,307 / 2,351 / 390 | −294.2 / −186.6 / +18.5 | −0.128 / −0.079 / +0.047 | | | |
| FWD own-day flag | FWD | 408 | +4.9 | +0.012 | 53.9% | +0.12 | −0.068 |
| NOT-E90 (removed) | TRAIN / VALID / FWD | 1,093 / 1,501 / 104 | −256.1 / −107.6 / −41.8 | −0.234 / −0.072 / −0.402 | | | |
| LIVE Primary 10-21..11-09 | | 34 | −7.2 | −0.211 | 50.0% | −0.94 | −0.340 |
| LIVE Testing 1 10-13..10-29 | | 206 | +55.1 | +0.267 | 66.0% | +1.51 | +0.171 (`1 day`: 61%) |

Same days as live, lab vs live (L3-fromopen, days ≤ 11-04):

| account | days | live | lab E90 | lab ALL |
|---|---|---|---|---|
| Testing 1 | 11 | +55.1R (206) | +29.0R (246) | −23.6R (216) |
| Primary | 5 of 7 | −7.1R (23) | +4.3R (93) | +1.3R (97) |

Testing 1's live symbol-days overlap with lab E90 symbol-days: 60%. Primary's overlap is 15%.

**Reading:**
- The restricted base now looks like live in FWD (positive, win 55%). On the live days, the restriction flips the lab
  from −24R to +29R.
- In TRAIN / VALID the restricted base is still negative. The −0.08..−0.13R/trade loss is spread across all of
  2025-2026.
- The FWD positive rests mostly on 10-20.
- The sister restricted bases follow the same pattern:

  | setup | E90 TRAIN | E90 VALID | E90 FWD | ALL FWD |
  |---|---|---|---|---|
  | RW3-FD | −267R | −52R | +27R | +32R |
  | RW5-FD | −165R | −105R | +30R | +28R |
  | L3-rsi5hi-FD | −181R | −67R | −18R | −7R |

  Restriction barely moves RW3/RW5, because 93% of their trades are already on ETB names.

## 3. K01–K12 on the E90 base (`verdict.csv`, `configs.csv`)
| cfg | leash | TRAIN dR | VALID dR | FWD dR | VALID red cut / green given | FWD red cut / green given | VALID paired t | sisters VALID better/worse (>5%) | sisters FWD better/worse (dR) | live Primary dR | live Testing 1 dR | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| K01 | BLOCK on UP-conf | +72.5 | +95.7 | −34.6 | 31% / 20% | 24% / 73% | 1.92 | 6/1 (1) | 2/5 (−18) | −2.6 | −34.2 | fail |
| K02 | SCALE 0.5 pre-conf / 0 UP | +77.2 | +56.1 | −46.5 | 36% / 40% | 9% / 81% | 0.86 | 6/1 (1) | 3/4 (−8) | −2.9 | −42.7 | fail |
| K03 | SCALE 0.5 pre-conf / 0.5 UP | +74.2 | +27.7 | −41.5 | 24% / 30% | −26% / 47% | 0.57 | 6/1 (1) | 4/3 (−3) | −2.8 | −26.3 | fail |
| K04 | RAMP 0.5x < 10:30 | +8.7 | −33.2 | −15.3 | 4% / 16% | −29% / 3% | −0.59 | 4/3 (2) | 4/3 (−7) | −1.6 | +0.6 | fail |
| K05 | RAMP 0.5x < 10:45 | +17.8 | −21.8 | −13.2 | 9% / 20% | −17% / 8% | −0.43 | 6/1 (1) | 4/3 (+9) | −1.7 | −2.9 | fail |
| K06 | RAMP 0.5x < 11:15 | +1.9 | +0.9 | −33.5 | 16% / 25% | −39% / 25% | 0.02 | 4/3 (2) | 3/4 (−34) | −2.3 | −5.1 | fail |
| K07 | RAMP<10:30 + BLOCK | +67.6 | +25.8 | −51.1 | 30% / 38% | −5% / 78% | 0.37 | 5/2 (2) | 4/3 (−11) | −3.0 | −33.6 | fail |
| K08 | SPY ≥ +0.20% skip | +131.0 | +72.7 | −48.4 | 42% / 44% | 28% / 97% | 1.09 | 7/0 (0) | 3/4 (−19) | −2.4 | −50.5 | fail |
| K09 | SPY ≥ +0.40% skip | +64.7 | +34.8 | −44.6 | 21% / 22% | 11% / 79% | 0.80 | 7/0 (0) | 4/3 (−5) | −2.6 | −43.9 | fail |
| K10 | SPY ≥ +0.20% half | +65.1 | +35.6 | −36.7 | 18% / 18% | −10% / 51% | 1.11 | 7/0 (0) | 3/4 (−21) | −2.4 | −25.5 | fail |
| K11 | SPY ≥ +0.40% half | +42.8 | +26.8 | −24.5 | 13% / 12% | 5% / 43% | 1.05 | 7/0 (0) | 3/4 (−19) | −2.5 | −21.9 | fail |
| K12 | −1R latch after UP-conf | −9.9 | +24.1 | +9.8 | 9% / 8% | 19% / −2% | 0.87 | 4/3 (2) | 3/4 (−28) | −1.4 | −12.9 | fail |

- Pass bar (unchanged from L3LEASH):
  - In VALID and in FWD: red-day cut ≥ 20%, green-day give-up ≤ 10%, dR ≥ 0.
  - TRAIN dR ≥ 0.
  - No sister worse by more than 5% of its base |R| in VALID.
- Paired VALID t vs N-24 bar 2.52: none clear it.
- Live rows are the live trades themselves (already ETB-only), so they are the same as in L3LEASH.

**Per-sister dR on the E90 base for the two shadow candidates (TRAIN / VALID / FWD):**
- **K11:**
  - L3-lowdist +16.7 / +17.9 / **−22.4**
  - L3-rsi5hi +15.9 / +6.8 / +5.0
  - MF2-FD −8.2 / +13.6 / −8.2
  - MF4 +3.4 / +4.5 / +4.7
  - MF4-FD +4.9 / +12.3 / +5.4
  - RW3-FD +10.6 / +8.3 / −0.7
  - RW5-FD +13.3 / +24.5 / −3.0
- **K12:**
  - L3-lowdist +21.4 / +18.3 / +2.1
  - L3-rsi5hi +9.5 / **−28.4** / +20.9
  - MF2-FD +17.1 / +47.6 / +11.8
  - MF4 +16.1 / −4.9 / −8.5
  - MF4-FD +22.6 / −1.1 / −13.9
  - RW3-FD −12.7 / +39.2 / −7.5
  - RW5-FD +18.3 / +42.5 / **−32.9**

All configs: `study_out.txt` ("Sisters (E90)").

Diagnostic, E90 base day R by SPY day type:

| split | SPY up | flat | SPY down |
|---|---|---|---|
| TRAIN | −255R (78 days, 69% red) | −53R (56 days) | −3R (52 days) |
| VALID | −200R (58 days, 69% red) | −24R (54 days) | +32R (50 days) |
| FWD | **+32R** (6 days) | −12R (8 days) | −4R (3 days) |

So in FWD the up-day pattern reversed, and in TRAIN/VALID it held.

## 4. LEASH shadow (forward, paper-only) — `research/l3leash/shadow.py`
- **Nightly command (after 16:05 ET):** `python research/l3leash/shadow.py --date YYYY-MM-DD`.
  - It fetches origin/mcf-data, mcf-data-testing and mcf-data-compass itself; pass `--no-fetch` to skip that.
- **What it reads:**
  - the day's live `L3-gap-slope-fromopen-FD` trades from Primary (journal run 1, plus the run-2 what-ifs that the −2R
    latch blocked) and Testing 1 (journal run 1);
  - the production compass rows (`compass/<day>.csv`); for older days, the research/l3leash/live_compass.py parquet or
    a recompute with mcf.report.compass_live;
  - SPY 1-min bars from the read-only market-data GET.
- **What it writes:** one row per date per account in `research/l3leash/shadow_scoreboard.csv`. A re-run replaces the
  row. Each row has:
  - base (actual R) and base_sim (−2R latch re-sim);
  - K11 and K12 with dK11 / dK12 vs base_sim;
  - entries halved / cut;
  - first UP-confirmed mark and max SPY-from-open at entry;
  - running totals per account and kind;
  - kind = "forward" (≥ 11-10) or "backfill (in-sample)". 11-10 is flagged `seen_at_design=1`.
- **Backfill (in-sample) 10-13..11-09:**

  | account | trades | base actual | base sim | K11 | K12 |
  |---|---|---|---|---|---|
  | Primary | 45 | −7.54R | −7.18R | −9.69R (**−2.51**) | −8.61R (**−1.42**) |
  | Testing 1 | 222 | +49.69R | +55.09R | +33.15R (**−21.94**) | +42.18R (**−12.91**) |

  - This matches the study's live rows exactly.
  - K11 cost on Testing 1 comes mostly from 10-20 (−15.8R) and 10-26 (−5.7R). K12 cost comes from 10-20 (−8.2R) and
    10-26 (−4.9R).
- **11-10 is left for the nightly loop.** This work finished before the close, and the script refuses the current date
  before 16:05 ET.
  - Testing 1 no longer runs the setup: it was re-promoted to Primary on 10-30, and promotion is a move. Its forward
    rows will read 0 trades.
- **Re-score after 20 forward sessions after 11-10.** Bar, declared now:
  - K11 or K12 is worth a proposal only if, over those sessions on Primary, its cumulative dR ≥ 0;
  - and it cuts ≥ 20% of the R lost on red base days while giving up ≤ 10% of green-day R;
  - and the one-big-day check is shown.
  - It informs the owner; it does not auto-change anything.

## Method
- **Universe and caps:** lab trades, compass, SPY, sims, splits, caps, −2R latch and costs are exactly as
  research/l3leash/study.py. Only the universe changes: all 8 setups are restricted the same way.
- **Live window:** live is cut at 11-09. 11-10 is partial and goes to the shadow.
- **Locked block:** 2024-11-01..2025-02-28 is filtered at load and asserted.
- **Flags:** from `universe.csv` (built ~08:45-09:30 ET each morning). Live's check happens at signal time (cached per
  session), which explains the residual 0.2% disagreement.

## One-big-day check
- **E90 FWD base:** +16.5R. The best day (10-20, +29.2R on 52 trades) is 177% of the total, so the `1 day` tag
  applies. Without it the base is −12.7R (avg −0.036R).
- **Live Testing 1:** +55.1R, best day 61% (`1 day`; 10-20 again).
- **Primary:** negative over 10-21..11-09.
- 10-20 also dominates the K11 / K12 shadow backfill cost.

## Rule-change context (research/ledger.jsonl) inside the windows
- 10-14 lab refire option B (cooldown per setup).
- 10-20 per-setup −2R daily loss limit (net).
- 10-20/21 L3-fromopen-FD Testing 1 → Primary, then 10-22 demoted back to Testing 1.
- 10-23 setup stop latches. Testing 1/2 + Gen setup stop off.
- 10-28 Primary ~$5k then ~$4k position size (per-setup cap 30).
- 10-29 Primary −2R latch (ST-P).
- 10-30 L3-fromopen-FD re-promoted Testing 1 → Primary.
- 11-05 ROLL1.
- 11-09/11-10 EXPO1109 temporary GEN moves.

The lab is rule-fixed: the latch and caps apply on all days. Live and the shadow backfill mix pre- and post-latch
sessions (10-21/10-22 Primary had no latch; Testing 1 had its setup stop off from 10-23). base_sim applies −2R to all
of them.

## Caveats
- **The proxy carries an Oct-Nov 2026 borrow list back to 2024-25.** Names that were hard to borrow then but are ETB now
  (and the reverse) are misclassified. This most likely explains why TRAIN/VALID stay negative while FWD flips.
- **The lab universe is only 1,226 liquid names.** A third of live L3 trades are outside it.
- **Samples are small:** FWD has 17-21 days, and live is 7 + 11 days.
- **Survivorship:** today's symbol list.

## Files
- `study2.py`: this study. Run: `python research/l3leash2/study2.py <scratch>`, with `<scratch>/j/{primary,testing,testing2}.db`
  from `git show origin/mcf-data[-testing|-testing2]:journal.db` and `<scratch>/live_compass.parquet` + `live_spy.parquet`
  from `python research/l3leash/live_compass.py <scratch>`.
- `study_out.txt`, `etb_validation.csv`, `bases.csv`, `configs.csv`, `verdict.csv`.
- `research/l3leash/shadow.py`, `research/l3leash/shadow_scoreboard.csv`, `tests/test_l3leash_shadow.py`.

Educational only — not financial advice.
