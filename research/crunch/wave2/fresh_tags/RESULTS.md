Educational only — not financial advice

# Wave 2 "fresh_tags" — WAVE1 §7 items 3, 4, 6 (results)

Research only: no config, runtime, ledger, assignments or setup change, and no decision; proposals carry reply codes
for the owner. Plan: `PLAN.md` (written 2026-11-19 21:54 UTC, before any scoring; sha256 b57de10a…acdf4eb, not
committed: only the Skeptic stage commits). Costs are in throughout. The locked block 2024-11-01..2025-02-28 was never
read, and `cache_fresh` (2023-24) was not used. Scripts are in `code/`. The 11-19 tag table is `tags_2026-11-19.csv.gz`.

**Configurations counted: 3** (all in item 4). Items 3 and 6 add none: item 3 uses the frozen rules and item 6 is a recheck.
Item-4 bar = max(1.5, √(2 ln 3)) = 1.50. Item 4 is a separate source with **SRCV1 weight 0**.

**Rule changes inside the windows (research/ledger.jsonl):**
- Item 3 (11-19 only): C3 Epoch 1 in force from 11-19.
  - NS5 moved Primary → On Deck, so Primary ran 5 setups.
  - C3-EXIT100 moved 20 setups to the Graveyard, MF2-FD and MF4-FD among them. This is why 43 of the 45 MFGAP hits sit in the Graveyard.
  - Also in force: GY-BENCH plus guests (11-18..11-24), C3-ROT/ROT2, U9-ETB bulk borrow list (40 L3 inverse shorts blocked as not-ETB), DQ-P4 fill marks, TSZ1 half-size testing lots (from 11-17; testing account R is not comparable with Primary's), and LR8 booked costs (from 11-12).
  - The 11-20 changes take effect after this window: FOOTRACE-EXIT, GY-FOOTRACE, the 9 ultimate_1119 testing admissions, the stop-rounding fix and the testing-admission rule.
- Item 6 (10-06..11-19):
  - 10-28: Primary ~$4k sizing.
  - 10-29: −2R latch.
  - 10-30: L3-rsi5hi promoted, L3-fromopen re-promoted.
  - 11-11: TEAM-6 lineup (L3-rsi5hi and NS1 leave Primary by 11-10/11-16).
  - 11-12: LR8. Neutralised here with `cost_r_lr8`.
  - 11-17: TSZ1 and the WB copies.
  - 11-19: C3.
- Item 4: one fixed rule set replayed, so no rule change falls inside its window.

---

## Item 3 — TAGS1 frozen rules on the first fresh session (2026-11-19). Report only, no verdict

- Data: all 10 journals at the 11-19 close. 1,066 live (run kind `paper`) and 1,128 shadow trades.
- Bars: Alpaca SIP 1-minute and daily bars, deleted after use. Tagged with `research/tags1/tags1.py build()` unchanged.
- R is the booked LR8 basis. Primary live is 32 lots, **−16.21R, −3.89 account R**.
- `score.py` was not run: it is sealed until 20 sessions (12-17). A single session says nothing either way.

| Rule (frozen) | Scope | Would-skip lots | R of those lots | Account R | Read of the day |
|---|---|---|---|---|---|
| FLAT25 | Primary live | **0** of 32 (shadow 0 of 82) | 0 | 0 | SPY was −0.91% to −2.45% from its open at every Primary entry (first entry 10:45 ET). FLAT25 had nothing to act on. |
| STACK1_L3X | Primary live | **1** (RW5 BTI 13:10 ET, RW3 BTI open) | −0.58 | −0.05 | Skipping would have saved +0.58R. 1 setup better / 0 worse. |
| MFGAP | all accounts, de-duplicated | **45** live (44 shadow) | **+13.61** (shadow +14.35) | +0.79 | **The rule would have cost 13.6R today.** The gap-up fades made +0.302R/lot (39 of 45 green, 26 targets). The other 51 MF shorts made −0.509R/lot (−26.0R). 0 setups better / 5 worse: MF4-FD +7.57 (25), MF3-FD +2.99 (5), MF2-FD +1.43 (13), MF2 +1.04, MF4 +0.58. 34 of 45 entries came at 13:xx ET in the Graveyard, on one down-tape afternoon, so this is one clustered day. |
| W4 watch tags | all | NS3-pday 8 (+6.34R), L3-PM 1 (+0.17), RW3-gap2 1 (+1.09), HFL-VWAP 0 | | | Tabulated only. |

- **Housekeeping finding (TAGS1-WHATIF):** `tags1.decisions()` labels every run whose kind is not `shadow` as "live". That includes the **what-if run** (`whatif`, 1,664 rows on 11-19 alone).
  - `score.py` keeps `source == "live"`, so as written the 12-17 score would mix about 1.5 what-if rows into every real trade.
  - The fix keeps only run kind `paper`/`live` as live. It changes no frozen threshold and no trade.
- Also: `research/tags1/tags/` does not exist, and nothing in `.github`/`scripts` calls the tagger. The "nightly" tagging may not be wired.
  - The 11-19 table here was built with the what-if rows excluded and can seed it.

## Item 4 — 2-year single-config scores (lab, weight 0)

- Source: the 2-year lab frames, sessions 2024-10-01..2026-10-05 outside the locked block. That is 424 sessions, all before the live record the rules were found on.
- Trades: the live mask, window, min_adv and prefilter, first bar per symbol-day, production-cost R (`gates.prod_r`; the lab cannot apply LR8).
- No ETB, refire or stacking is modelled.
- Deviation from the plan: the 2-year live-code replay (`research/replay2y`) has only 7 sessions and no trade files, so the lab was used.

| Config | Skipped / base | Skip avg vs keep avg | Skip gain | Random-removal pct | Day t | W/o best day (share) | Halves H1 / H2 | Setups better / worse | Pre-reg verdict |
|---|---|---|---|---|---|---|---|---|---|
| **FLAT25** on the Primary five | 7,016 / 17,861 (39%) | −0.037 vs **−0.053** | +258.2R | **4.8** | 1.54 | +203.5 (21%) | +235.8 / +22.5 | 4 (+264.1R) / 1 (NM −5.8R) | **Not supported.** The flat-tape trades are *better* than the ones kept. The "gain" is only the removal of trades from setups that lose in the lab; random removal does better 95% of the time. |
| **MFGAP** on MF1-5 FD | 2,708 / 39,471 (7%) | −0.068 vs −0.072 | +185.0R | **44.3** | 2.07 | +161.6 (13%) | +29.8 / +155.3 | 5 (+185.0R) / 0 | **Not supported.** Gap-up fades are no worse than the family's other trades (W6 live: −0.558 vs −0.137). Same removal effect as above. |
| **RW3/RW5 SPY-up-day profile** | 11,507 trades, 422 sessions | up −0.211 (5,663 tr, −1,193.7R) vs down **+0.078** (5,844 tr, +456.4R) | | | **Welch t 7.03** | | H1 −0.221/+0.067 (t 4.68); H2 −0.204/+0.084 (t 5.14) | RW3 −0.212/+0.058; RW5 −0.210/+0.101 | **Replicates strongly** (W7 live: −25.0R on 12 up / +19.4R on 7 down). It uses a hindsight day label, so it is a profile, not a rule. |

Per setup, FLAT25 (gain if skipped; avg R of the kept trades vs all trades):
- L3 +65.6 (−0.040 vs −0.042)
- RW3 +112.1 (−0.090 vs −0.069)
- RW5 +69.5 (−0.083 vs −0.059)
- ST7 +16.9 (+0.090 vs +0.032)
- NM-ETF −5.8 (+0.177 vs +0.162)

So for RW3/RW5, skipping flat-tape trades leaves a *worse* kept record. MFGAP per setup (gain): MF1 +21.8, MF2 +53.6, MF3 +58.9, MF4 +42.0, MF5 +8.7. Kept avg ≈ all avg for every one.

Context only, not a config: the same day split in the lab gives L3-fromopen up −0.105 / down +0.078. It carries the up-day squeeze too, unlike its live record. ST7 (long) is the reverse (+0.123 / −0.031). NM-ETF is positive on both.

## Item 6 — correlation recheck (per-session R, live run 1, 10-06..11-19, LR8)

| Pair | View | Trade R: both-traded days (n) | Trade R: union, 0-filled (n) | Account R: both (n) | Account R: union (n) |
|---|---|---|---|---|---|
| L3-fromopen ~ RW3 | Primary-only | 0.17 (14) | 0.14 (24) | 0.09 (14) | 0.06 (24) |
| L3-fromopen ~ RW3 | Pooled, de-duplicated | 0.10 (24) | 0.07 (29) | 0.09 (24) | 0.05 (29) |
| L3-rsi5hi ~ NS1 | Primary-only | n/a (3) | 0.23 (15) | n/a (3) | 0.15 (15) |
| L3-rsi5hi ~ NS1 | Pooled, de-duplicated | −0.29 (20) | −0.27 (30) | 0.05 (20) | 0.02 (30) |

Spearman agrees: −0.36..+0.30. Dropping the largest day (11-12) takes L3~RW3 pooled to 0.01.

- **W6's 0.74 / 0.76 is a labelling bug, not a data effect.**
  - In `w6_external/code/tests.py` (X7), `B.corr()` columns are alphabetical. They were relabelled with `six`, which is in `value_counts` order.
  - Re-running W6's exact method (no de-dup, booked R, 31 sessions 0-filled) gives L3-fromopen~RW3 **0.07** and L3-rsi5hi~NS1 **0.01**.
  - The cells printed as 0.74 and 0.76 are really **L3-fromopen ~ L3-rsi5hi (0.74)** and **RW3 ~ RW5 (0.76)**.
  - On my LR8 basis: pooled 0.74 and 0.76; Primary-only RW3~RW5 **0.77** (25 days).
  - W6's average pairwise ρ (0.091) and breadth 5.5 are unaffected, because the sum of a symmetric matrix does not depend on labels.
- WAVE1 §4.7 is resolved. L3-fromopen and RW3 are near-independent bets in both views. **RW3 and RW5 are one bet at the day level** (0.77 in Primary), and item 4 shows they share the same up-day squeeze.

## Proposals (reply codes; nothing changes without the owner)

| Code | Proposal | Evidence | Rec | Conflict with a standing rule |
|---|---|---|---|---|
| **TAGS1-WHATIF** | Housekeeping: `tags1.decisions()` treats only run kind `paper`/`live` as live and drops `whatif`. Make sure the nightly tagger actually runs, seeded with the 11-19 table here. | 1,664 what-if rows labelled live on 11-19; no tags dir and no caller | Yes | None. No frozen threshold changes and no trading effect. This keeps the TAGS1 "score once" rule honest. |
| **CORR1** | Correct W6 X7 / WAVE1 §2, §4.7 and W6-BREADTH: L3-fromopen~RW3 ≈ 0.07-0.17 and L3-rsi5hi~NS1 ≈ 0. The real high pairs are L3-fromopen~L3-rsi5hi 0.74 and RW3~RW5 0.76-0.77. Count RW3+RW5 as about one bet in breadth and red-day reviews. | Item 6 | Yes | None (reporting). |
| **TAGS1-HOLD** | Keep FLAT25 and MFGAP frozen as filed and scored once on 12-17. No early drop and no live use. Note in the Friday review that the 2-year lab (weight 0) does *not* support either one, and that MFGAP's first fresh day went the wrong way (−13.6R). | Item 3 + item 4 | Yes | None. Dropping either one early would break the TAGS1 pre-registration and the locked-score rule, so that is not proposed. |
| **UPDAY-PIT** | Backlog only: one pre-registered point-in-time version of the RW3/RW5 up-day profile (e.g. the 09:50 SPY day-type tag from C3-SCORE, or spy_fo at entry) on the 2-year lab with a fit/check split. Read it with the RW3/RW5-WB4 SPY-exit copies already running (C3-MECH). | Profile t 7.0, holds in both halves | Optional | Has to go through backlog gates (RESEARCH_RULES 15-17), W4-FRAME (shadow tag first) and STOP2 (no live per-setup filters from short samples). Any Primary use only in a Friday epoch window (C3-EPOCH). |

## Caveats
- Item 3 is one session, on a down-tape day.
- The item 4 lab charges production lab costs, not LR8. It does not model ETB (L3 inverse shorts are included) or stacking, and takes the first bar per symbol-day. Every short family loses in the lab, which is why random removal "gains".
- Account R across accounts mixes TSZ1 half-size testing lots (from 11-17).
- Temporary journals, bars and lab trades were deleted after the run.
