# Research wave 6 — 2026-11-27 (evening, market closed) — synthesis

**Educational only — not financial advice.**

## In plain words

Two tasks ran tonight: one study and one build. Both were pre-registered or frozen before any scoring, with costs in
(LIVE-L first, LR8 alongside, plus a stress case), and the locked block 2024-11-01..2025-02-28 was never read.

- **IDXHEDGE failed (0 of 12).** Buying SPY or QQQ once at a "squeeze moment" against Primary's short book is now cheap
  (at most about 0.05 R/day, 1-20 R a year, against HEDGE-B's 60-120 R a year), so the "one-shot hedge" salvage idea
  fixed the cost problem. But it barely softens Primary's worst days (worst-5 only 0-3% better on CHECK and T2; the bar
  was 10%), because those days are single-stock squeezes that the index does not follow. Trigger B does find the bad
  days (81-92% of B10 hedge days fall in Primary's worst 20%), and when it fires it helps (B6-QQQ-k0.5 +34R over CHECK's
  worst 10 days), but other days then take their place in the worst five. An index leg cannot be the up-day remedy.
- **MEREBFWD is built and safe to run (journal only).** The month-end rebalancing rule (MEREB1: long SPY 14:00 to 15:55
  on the last session of the month when SPY lagged TLT month-to-date, stop 0.25 x ATR14) is frozen and logged as a
  forward shadow. Both skeptics re-ran it and neither could refute it: the port matches the scout line for line and
  reproduces its RECENT split exactly (n 7, +0.478R). It also fixes a scout bug (the 2025-11-28 half day was "traded" on
  after-hours prints for -1.18R; half-day month-ends now take no trade). Its in-sample seed day, 2026-10-30, lost
  -1.23R after LIVE-L costs (not scored). The first scored month-end is **Mon 2026-11-30**.

Verdict rule: a PASS/LEAD with 2 skeptic refutations becomes FAIL, 1 refutation becomes INCONCLUSIVE; for a BUILD, any
refutation means **not safe**. MEREBFWD went to 2 skeptics: 0 refutations, so it stands as BUILT (safe). IDXHEDGE was a
FAIL with no pass to overturn, so it was not sent to skeptics.

## Table

| Task | Verdict (after skeptics) | Configs | Key numbers (after LIVE-L costs unless stated) | What next |
|---|---|---|---|---|
| IDXHEDGE — one-shot SPY/QQQ long sleeve on Primary's bench book (triggers A, B6, B10 x SPY/QQQ x k 0.25/0.5; LO main, BASE alongside) | **FAIL** (0/12) | 12 | Cost bar passes everywhere: worst config -0.034 / -0.025 R/day CHECK / T2 (budget -0.20), stress at most -0.11 R/day. Worst-5 bar fails in all 12: best -25.7 -> -24.8 (CHECK), -14.5 -> -14.0 (T2). B6-QQQ-k0.5 +0.047 / -0.012 R/day, days <= -10R 39->34 / 22->17 (not consistent across configs). Trigger A loses on every split incl. FIT. Random-time control median about -0.01 R/day; only B10 k0.25 beats the 90th pct on both splits, by under 1R of worst-5. No sleeve reaches t 1 on CHECK and T2 together. | Not added as a remedy. Parked backlog entry records the 12 configs so the idea is not re-run blindly. |
| MEREBFWD — journal-only forward shadow of MEREB1 (L, S<0, SPY 14:00-15:55) | **BUILT — SAFE** (2 skeptics, 0 refutations) | 1 frozen | Port check: RECENT split n 7 +0.478R = scout exactly. With the half-day fix the other six average +0.75R (in-sample, not evidence). Seed 2026-10-30: S -4.32%, stopped 14:18, -1.23R (LR8 -1.11, stress -1.44). Pass bar fixed in advance: n >= 12 signal trades, t >= 2.0, best share < 50%, avg w/o best > 0, S12 > 0; S >= 0 month-ends logged as control. 5 unit tests pass. | Parent: add one line to the daily forward-logs trigger: `python research/forward/month_end/shadow.py --date $(TZ=America/New_York date +%F)` (not yet in the branch). A missed month-end can be backfilled with `--date`. |

### Skeptic caveats on MEREBFWD (none refutes the build; worth fixing or noting)

1. **One-big-day carry is not flagged.** In the scout's RECENT split, 2025-09-30 (+2.92R) is 87% of total R; avg R
   without it is only +0.07. In the corrected six it is 65% (+0.32 without it). Over the full history the best-day share
   is 191% and avg w/o best is -0.047. Any quote of "+0.48R" or "+0.75R" must carry the `1 day` tag. The forward pass bar
   already requires best share < 50%.
2. **Half-day cap also runs inside ATR14.** ATR windows that contain a half day now drop after-hours prints, which the
   scout kept. The ATR window of the first scored day (2026-11-30) contains the 2026-11-27 half day. Small, and the
   right data rule, but RULE.md does not name it as a difference from the scout; add one sentence (a wording fix, not a
   rule change). On cached data the 2025-12-31 ATR came out the same either way.
3. `R_s12` is set to -1.0 with no costs when the delayed 14:01 fill is already through the kept stop: slightly
   optimistic, stress number only.
4. "close_m=960 switches the half-day cap off" is loose wording: `_rth` still applies `cap_at_close`, so the +0.478 match
   holds by arithmetic with the scout's -1.18, not by a flag.
5. `is_month_end` relies on the offline holiday list, which starts in 2024 and must be extended past 2027; the script
   refuses dates beyond it. No half-day month-ends are coming through 2027.

**Configs tonight: 13** (12 + 1 frozen forward rule). **Cumulative N ≈ 9,350 → ≈ 9,363.** Family bar about t ≥ 4.28;
nothing tonight comes near it.

Every finalist is listed in `research/idxhedge_1127/REPORT.md` and `results.csv`; the MEREBFWD rule, script and journal
are in `research/forward/month_end/` (RULE.md, shadow.py, forward.csv) and `research/merebfwd_1127/REPORT.md`.

Follow-up from wave 5: the two IDXFWD defects (half-day exit in after-hours, avg-R-without-best-day count) were fixed in
a8b92f9c57; MEREBFWD uses the same calendar-close rule (`mcf.data.bars.close_min` / `cap_at_close`).

## Rule changes inside the windows used

IDXHEDGE replays Primary's bench book on history (T2 2023-01-03..2024-09-13, CHECK 2025-10-01..2026-11-04) under one
fixed rule set and LIVE-L costs, so no ledger effective date changes its figures; any live Primary figures for the
same windows must list the ledger's sizing / stop / move dates alongside. MEREBFWD trades SPY only and uses no live
setup, sizing or account rule. Two ledger entries take effect on its first scored day, **2026-11-30**:
`2026-11-30-etf-stop50-av50` (ETF-STOP50 / AV50, NM-ETF late-dip half-stop burst lots, Primary) and
`2026-11-30-friday-review-1127` (Friday review moves). They do not touch the shadow, but any live-account figure quoted
next to the 11-30 shadow row must name them.

## Backlog actions (this commit)

- **New, parked:** `idxhedge-1127-one-shot-index-hedge-sleeve` (12 configs, FAIL as a remedy; cost solved, tail
  not). Records the "one-shot hedge" lead from HEDGE-B and the SQZ-moment / index-hedge idea from waves 4-5 as tested.
- **Updated:** `scout-1127-mereb1-month-end-rebalance-close` notes: forward shadow built (MEREBFWD), skeptics 0/2,
  half-day bug fixed, seed -1.23R in-sample, first scored month-end 2026-11-30, one-big-day caveat. Status stays
  `parked` (forward lead; scored only by the shadow's frozen pass bar, not by `backlog run`).

Educational only — not financial advice.
