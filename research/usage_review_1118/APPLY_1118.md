Educational only — not financial advice.

# USAGE1 — owner yes 2026-11-18, and a better use for the Guild

Owner: "Yes or find a better use for the guild that offers better use to mcf in general."

This file is the implementation plan. **No scheduled task was changed here**: the parent session makes the trigger
edits (each is a process change: no setup or exit change; ledger 2026-11-19-usage1-plan). The cadence is PLAN.md
sections 3-4 (lean cadence, ~580 → ~140 agent runs a week, every safety check kept). The Guild part below replaces
PLAN.md 3b with a design aimed at the north star (find more of the big moves beforehand, long and short).

## 1. Lean cadence (as PLAN.md section 4)
Kept unchanged: start guards (08:40 / 09:05 / 09:35), :21 BDI Primary monitor, :51 glitch check (absorbs the :47 session
guard), 16:33 single scripted scorer (late turn, dip-day, LEASH, regime switch, compass conditional, latch shadow,
REPS2 shadow + real-quote replay, **TAGS1 tagger**, **REPS2 fast-lane re-pick → lane.json**), 16:47 nightly loop
(trimmed: its 6c shadow sub-steps move to the scorer), 17:04 consultant check-in, 17:22 BDI daily (writes the gap list),
17:23 arena rotation, 18:07 Workbench queue item only when queued (WB2 hold: no new tunes unless the owner asks),
19:17 owner brief, Mon/Thu blocked-signal audit (+ C3-ROT triage + **refresh docs/live/arena_resources.json for ROT2**),
Fri report (+ C3-EXIT100 / GY-LIFE lists), Sat BDI deep run (+ top-20 Part A), monthly parked review + usage check.
Reddit: weekly (Saturday), gap-filtered, hand-off to the Guild Builder.

## 2. The Guild, redesigned: targeted gap teams (instead of 5 roles every 2 hours, 24/7)
**Why:** 420 runs a week produced 78 ideas, 174 configs and 0 setups; its real contributions were process checks
(COMPCAL, PROMO2, RULE21-DB). The work that moves the north star is closing named gaps in what MCF catches.

**The gap list (input, no new agent):** BDI daily writes `research/gaps/GAPS.md` + `gaps.json` from the Move Hunt:
one row per mechanism gap — category (opening drive 09:35-09:45, gap-up day, sector / group move, earnings reaction
outside the blackout, inverse / vol ETF, up-day long, quiet-day long, ETB-only short), moves missed in the last 10
sessions, tradable R missed, day types, existing backlog ideas on it, status. Ranked by tradable R missed. The 11-18
Guild note already names the top one: ~4.5 missed non-ETF moves a day with >= 1 ATR left after 09:50 — the gap is
**which name and which side** (SIDEHUNT).

**Teams (one per open top gap, at most 2 at a time):** each team is 3 runs on one gap, one night:
1. **Mechanism Scout** — writes one mechanism card for the gap: day-type condition, falsifiable reason, a
   pre-registered rule (<= 2 parts), the pass bar (max(1.5, sqrt(2 ln N)), lineage-counted), the engine it will use
   (ENG1-A: an existing engine, no one-off simulator).
2. **Builder** — runs that ONE pre-registered test on the 2-year data (costs in, LR8 basis, locked block never read,
   ETB universe for shorts, vs random entries, w/o best day, per-family better/worse counts), plus the live-period
   check on the recorded sessions.
3. **Skeptic** — tries to break it (look-ahead, rule conflicts with Primary, overlap with existing setups, one-big-day)
   before anything reaches the owner inbox. Second duty, Saturday: one process / methodology check a week (keeps the
   Guild's proven contribution).
A card that passes goes to the backlog → testing arena on the Testing bar (rule 22), never straight to Primary.

**Cadence:** one team round per weeknight (~20:15 / 20:45 / 21:15 ET, after the brief) + one Saturday round after the
BDI deep run: 18 runs a week (was 420). Lead and Observer roles are disabled (kept, not deleted): the consultant
check-in and BDI steer; the Move Hunt observes.

**Score it (pre-registered kill/keep):** after 4 weeks (2026-12-16), if no gap card has passed research AND no process
item was approved, the owner gets a one-line ask (keep / weekly / pause). Each team's result is logged against its gap
row so the capture rate on that category can be compared before and after.

## 3. Steps for the parent session (after hours)
1. BDI daily prompt: write research/gaps/GAPS.md + gaps.json (Move Hunt section).
2. Guild tasks: Scout / Builder / Skeptic → weeknights 20:15 / 20:45 / 21:15 + Saturday; Lead + Observer disabled.
3. Reddit scout → Saturday weekly, gap filter, hand-off to the Builder.
4. Top-20 / top-5 → Workbench-queue item only (WB2 hold: nothing queued unless the owner asks); Part A → Saturday.
5. Glitch check absorbs the session guard; session guard disabled (kept).
6. 16:33 forward-logs task → the single scripted scorer, with `python research/tags1/tags1.py --date <today> --jdir <journals>`
   and `python research/reps2/fastlane.py` (re-picks lane.json) added; nightly loop drops its 6c shadow sub-steps.
7. Parked review → monthly; the four disabled tasks may be deleted only on the owner's word.
