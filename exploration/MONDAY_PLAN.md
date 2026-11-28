# Monday 11-30 plan (ready to start on the owner's approval Sunday or Monday before 09:30 ET)

Educational only — not financial advice. Nothing here is applied by the exploration session. Approvals use the one-line reply in [DECISIONS.md](DECISIONS.md). Data basis, rule changes in the window and the configuration count are stated there.

## What "green every day" honestly means for Monday

**The numbers:**
- Primary over 25 sessions: −147.0R, 8 green days of 25, 1 green week of 6.
- The 4 setups trading Monday made −30.1R of that, red on 14 of 25 days.
- At today's edge (−0.05 to −0.16R per lot after costs), the chance of a red day is about 55-65%, whatever filter is added.
- To be red on at most 1 day in 20 the book would need about +0.67R per lot. That is roughly 6x anything seen live, and no track tonight found a positive edge after costs.

**So:**
- **Monday can be made safer, not reliably green.** The realistic target for the first week is Stage 1: no day worse than −20R, and every day yields at least one measured verdict ("a winning day in some way", per the charter).
- With L3 out and LATCH-OPEN on, a green week is still only about a 30-40% chance. The roster without L3 averaged about −1.1R a day with a day sd of about 9R, so a 5-day week has about −5R expected and an sd of about 20R. The cycle-3 replay of exactly this book ([latchopen_monday](findings/latchopen_monday.md)) gives −0.31 R/day live (25 sessions, `1 day`) and about −1.25 R/day on the bench (CHECK −1.28, T2 −1.22).
- Green **weeks** need a positive-edge sleeve. That is what TAGS2, PAIRED-CARD and LONG-SURVIVORS are searching for, as forward tests that cannot fool us.

## The plan by account

### Primary: unchanged unless you approve an override
| Item | Default (no reply) | If you reply `monday` | Approval |
|---|---|---|---|
| Lineup | L3, RW3, RW5, NM-ETF | **RW3, RW5, NM-ETF**. L3 moves to On Deck (D2) | `L3-OUT out monday`: overrides PRIME-RULES probation and the Friday rule |
| −2R latch | Closed R only | **Closed + open R** (D1); no new entries once a setup is down 2R including open lots | `LATCH-OPEN monday`: overrides the Friday rule |
| B8 | Off | Journal tag only (D3) | `B8 shadow monday` |
| AV50 for NM-ETF | **Starts Monday** (already approved, ledger 2026-11-30-etf-stop50-av50) | same | none |
| −20R halt, sizing, exits | Unchanged | Unchanged | — |

**How an override would be applied (Sat/Sun, outside market hours):**
1. On a branch cut from witis4, run `python exploration/sandbox/decisions/apply_draft.py --repo <checkout> --code COMBO --when monday --date <reply date> --where <chat|inbox>`. COMBO = LATCH-OPEN + L3-OUT + B8. For a partial yes use `--code LATCH-OPEN | L3-OUT | B8-SHADOW` one at a time; add `--code ARENA-LATCH-F` if D5 is approved. Use the script, not `git apply`: the `config.diff` files are a readable view only ([DRYRUN.md](sandbox/decisions/DRYRUN.md)).
2. Run `python -m mcf.report.assignments` for L3-OUT, and commit the regenerated `docs/live/assignments.json` in the **same commit** as the config move. Then run `python -m mcf.research.ledger check`. The dry run could not run this check.
3. Run the full `pytest -q` and expect 1,076 passed. If `test_poll_log` fails, re-run it alone: it is a known timing flake under load.
4. Open a PR on the default branch and merge it before Monday's 09:30 open (setup-freeze allows weekends).

Dry-run status: every draft, the combo and the all-five stack passed the full suite on a throwaway copy at f5a2626587. The test edits that come with it ("off unless approved", the 4 → 3 Primary count, the Testing F 2R exception) are part of the script.

**Monday before the open:**
- status.json `health.risk_state.safety` shows `latch_counts_open.enabled: true` (if approved).
- assignments.json shows L3 under On Deck with Sunday's timestamp.

### Testing accounts and arena
| Account | Monday | Approval |
|---|---|---|
| On Deck | Receives L3 (if D2). Gets the ODB3/ODP2 admissions you say yes to. T1X2: one DAY market sell of the 12 phantom SOXX shares after the open | `T1X2 yes`, `ODP2/ODB3 as recommended` |
| Testing F | **ARENA-LATCH-F**: closed −2R per-setup latch, frozen block 11-30..12-11 (D5). This is in-session throttling in a testing account, so `yes` is a time-boxed exception to the playing-time rule | `ARENA-LATCH-F yes` by Sunday |
| Testing A-E, On Deck | Unchanged. **FROZEN-BLOCKS** first block 11-30..12-11: no rule changes inside it; the playing-time session rotation stays exempt (D6) | `FROZEN-BLOCKS yes` |
| Explore 1, Live Lab, Gen | Unchanged (not in the frozen blocks; the low-rep rotation every ~2 sessions continues) | — |
| Graveyard | Unchanged (GY-SHADOW / TWIN is a 12-04 discussion, D9) | — |

### Shadows and reports (no trading effect; one "go" each)
| Item | Starts | Where it reads from | Approval |
|---|---|---|---|
| TAGS2: 7 frozen would-skip rules (basket, gap-up gap-down shorts, profit lock, side/stop budgets, long strength) | Rules frozen before the open; first rows Monday night | All journals, after the close | `TAGS2 go` |
| PAIRED-CARD scoreboard (LATCH-OPEN skipped lots, RW 1.25x target as a descriptive read only after its cycle-2 fail, L3 first-lot-only, SPREADFLOOR) | Monday night; one report 12-11 | Journals + 1-minute bar packs | `REPORTS go` |
| LONG-SURVIVORS (GEN-261020-09, CWT14-orl-p10-long-WB5) | Monday night; score 12-28 | Their own live lots | `REPORTS go` |
| Weekly Stage-1 scorecard | First full read Fri 12-04 | Journals | `REPORTS go` |
| Already running, no action | SPREADFLOOR shadow (logs from 11-30), TAGS1 (score 12-17), GAP-U / IDX3-P / SPYO-P regime shadows (about 12-10; report on the new roster), MEREBFWD (first scored day **11-30**, month-end), Epoch 1 vs BASE1 twin, BRAKE-1, compass gate, inverse-short guard (about 12-04), L3 leash K11/K12 (loses its Primary basis if L3 moves) | | none |

**Failed in cycle 2, so not part of Monday:** the RW 1.25x target (LIVE-L re-check: CHECK +0.007, T2 +0.003 R/lot; dropped, D13) and the SPY gap-up short switch (0 of 5 configs beat random day-skips). Neither adds a rule, shadow or card.

## Expected effect (honest ranges)

| Change | Red days | Worst day | Weekly R (Primary) |
|---|---|---|---|
| LATCH-OPEN (on roster A, cycle 3 replay) | About unchanged (bench +3 red days per window; live 14/25 → 14/25) | Days ≤ −20R: CHECK 9 → 2 (about 8 → 1.8 a year), T2 1 → 0, live 2 → 0; worst-5 CHECK −148 → −97. An 11-25-type day: −40 → about −8R (4-setup book) | **+1 to +4** (CHECK +4.0, T2 +1.0, live +3.6 but +1.1 without 11-10), from trading 13-23% fewer lots |
| L3-OUT | About unchanged (14/25 either way on the live roster) | −42 → −26R live; day sd 15.8 → 9.1 | 0 to +4 (bench CHECK +4.8, T2 +2.0) |
| Both (roster A + LATCH-OPEN vs today's 4-setup closed-latch book) | About 55-65% red days | Bench days ≤ −20R about 8.4 → **0.7 a year** pooled (CHECK alone 17 → 1.8 a year) | Bench +2.9 (T2) to +8.8 (CHECK); live +3.3 (noise, t < 1). The book itself is still about **−6 R/wk** on the bench and −1.6 R/wk live; a green week is still only about a 30-40% chance |
| Shadows, TAGS2, reports, frozen blocks | None now | None now | 0 now; they are how a positive edge could be found and proven in 2-6 weeks |

The **arena** on a squeeze day remains the biggest absolute risk in paper R: −1,160R on 11-25, mostly no-stop L3 copies. ARENA-LATCH-F tests the guard in one account first, out of respect for the playing-time rule.

**Control for the LATCH-OPEN read (cycle 3):** on roster A it beats a plain size cut of the same lots (R at the 100th / 65th percentile on CHECK / T2) but not a random cut of the same lots on the same days (16th / 0th percentile). So the forward bar is "beats a constant cut on fire days", with the random same-day cut reported beside it, not "skipped lots ≤ 0R".

## What will be measured by Monday night (posted in the nightly brief)

1. **Primary:**
   - Day R (LR8), lots, red/green.
   - Worst setup-day; whether the day breached the Stage-1 −20R bar.
   - Weekly running total.
2. **LATCH-OPEN** (if on):
   - Fires (setup, time, closed + open R at the fire).
   - Lots skipped and their what-if R after LIVE-L costs.
   - Fallbacks to closed R.
3. **L3-OUT** (if done):
   - L3's On Deck lots and R.
   - What L3 would have added to Primary, from the On Deck record scaled to Primary size; descriptive only.
4. **B8** (if on): the number of entries it would have blocked, and their R.
5. **AV50 day 1:** NM-ETF burst lots on the half stop, and R vs the old stop (from bars).
6. **Testing F** (if on): latch fires, skipped-lot what-if R, and the same-day random-cut control for the day.
7. **TAGS2 day-1 rows:** tag counts per rule per account. No scoring until 12-29.
8. **Already-running tests:**
   - SPREADFLOOR first tags.
   - MEREBFWD first scored day.
   - GAP-U switch state for the day.
9. **Rule-change line** for the brief: "11-30: AV50 (NM-ETF exits), 11-27 Friday-review arena moves" plus whatever the owner approved (LATCH-OPEN / L3-OUT / B8 / Testing F latch), so day-1 results are never read as setup quality.

## Decision checkpoints after Monday
- **Fri 12-04 epoch:**
  - Anything not applied Monday (LATCH-OPEN / L3-OUT / B8 at `friday`).
  - HS-SCALE shock-only.
  - PRIM-EXPOSURE (RW5) on week-1 data.
  - GY-SHADOW + TWIN go/no-go for 12-07.
  - First Stage-1 scorecard.
- **12-11:** PAIRED-CARD report; the first frozen block ends (ARENA-LATCH-F read).
- **12-17:** TAGS1 score. **12-28/29:** LONG-SURVIVORS and TAGS2 scores.

Educational only — not financial advice.
