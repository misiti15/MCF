# Usage efficiency review — scheduled routines (2026-11-18)

_Educational only — not financial advice._

Research only. **No scheduled task was changed.** This is a proposal for the owner (DECISION **USAGE1**).
Owner context: C3-LEAN was declined (the Guild and the Reddit scout stay), but the owner wants the usage spent better.
The consultant's goals stay: daily consultant check-in, BDI refocus (capture + coverage, C3-MECH), shadow / replay
re-scores (REPS2), and the approved C3 items.

**Why it matters:** the usage limit was hit at ~13:15 ET on **11-11** and again on **11-12**. Both days the 13:21 BDI monitor
and the 13:51 Primary glitch check were missed (no Primary safety check for ~1 hour), and the top-20 / top-5 run, the
Reddit scout and other accounts' autopsies were skipped (owner inbox 11-11, 11-12). The safety checks are the cheapest
routines; the most expensive ones push them out.

## 1. Method and cost units

- Source: every scheduled task on the account (`list_triggers`, enabled and disabled, 30 entries), the owner inbox
  11-04..11-18, `research/ledger.jsonl`, `docs/live/decisions.json`, `research/consultant_p3/RESULTS.md` (Guild /
  Reddit / Top-5 yields).
- Token use per run is not logged anywhere, so cost is in **units**: **S = 1** (one quick read-only check, a small agent),
  **M = 3** (one agent with reading + writing, maybe one small backtest), **L = 8** (one agent with backtests/swarms or
  multi-account analysis). A Guild role run is costed **2** (one board read + one unit of work + push). These are
  estimates; section 5 shows how the saving moves if they are off.
- Window for "what it produced": 11-04..11-18 (2 weeks).

## 2. Inventory (enabled recurring tasks, weekly)

| # | Task (time ET) | Cadence | Runs/wk | Cost | Units/wk | What it produced 11-04..11-18 |
|---|---|---|---|---|---|---|
| 1 | Start guard 08:40 / 09:05 / 09:35 | 3× each weekday | 15 | S | 15 | Owner "guard start yes" 11-13; safety net for missed GitHub schedules. Mostly "session OK" |
| 2 | Session guard (:47, 08-14) | hourly weekdays | 35 | S | 35 | Same job check as #1 + Hunch/Compass watchdog; 08:47 overlaps the 08:40 start guard; :47 overlaps the :51 glitch check's job check |
| 3 | BDI intraday Primary monitor (:21, 10-15) | hourly weekdays | 30 | S | 30 | One inbox line/hour; 1 alert (11-18 15:21, −6.7R swing). Missed 13:21 on 11-11/11-12 (usage limit) |
| 4 | Primary glitch & catastrophe check (:51, 09-15) | hourly weekdays | 35 | S | 35 | Owner rule 11-11 (Primary ≈ live funds). OK lines; missed 13:51 on 11-11/11-12 |
| 5 | Forward logs: late turn + dip-day (16:33) | daily | 5 | S | 5 | Forward tallies, no pass yet |
| 6 | Nightly learning loop (16:47) | daily | 5 | L | 40 | Clean-close checks, coverage, inactive list, 6c shadow lines (LEASH, regime switch, compass cond, latch), promo/demo suggestions. Most of the inbox DECISIONs over the window |
| 7 | **Daily consultant check-in (17:04)** | daily (new 11-18) | 5 | M | 15 | Starts tonight (owner approved) |
| 8 | BDI daily (17:22) | daily | 5 | L | 40 | Move Hunt + capture rate, swing autopsy, ≥ 1 tested idea/day; refocused 11-18 (C3-MECH) |
| 9 | Testing arena rotation (17:23) | fires daily, acts every 4 sessions | 5 | S×4 + M | 8 | Spotlight/contender moves (5 ledger entries), assignments regenerated |
| 10 | BDI top-20 deep dive + top-5 tuning (18:07) | daily | 5 | L | 40 | Part A: CONDITIONS.md "thrives/struggles" table. Part B: **378 variants, 0 to Testing** (consultant P3); 20 notes dirs; skipped 11-11/11-12 for usage |
| 11 | Reddit setup scout (18:31) | daily | 5 | M | 15 | **26 ideas, 0 passed** (P3); ~150-400 posts scanned per run; 9 notes dirs; 0 DECISIONs |
| 12 | Nightly owner brief (19:17) | daily | 5 | M | 15 | The one owner message; carries every other routine |
| 13 | Blocked-signal audit (Mon/Thu 17:43) | 2×/wk | 2 | M | 6 | Coverage table, never-fired setups, HK fixes (e.g. HK-FLAT-1113) |
| 14 | End-of-week report (Fri 17:31) | weekly | 1 | M | 3 | Weekly post + images |
| 15 | BDI Saturday deep run (Sat 10:47) | weekly | 1 | L | 8 | Weekly scorecard, giveback review, plan |
| 16 | Biweekly parked-ideas review (1st/15th) | 2×/month | 0.5 | S | 0.5 | Re-queue list |
| 17–21 | **Research Guild** — Scout, Builder, Skeptic, Observer, Lead | each every 2 h, 24/7 | 5 × 84 = **420** | 2 | **840** | **78 ideas / 174 configs / 0 setups passed** (P3). But 3 owner-approved process items: COMPCAL display, PROMO2 (promotion hold), RULE21-DB (audit on decision bar) — all ledger 11-17; plus the Skeptic checklist, TIER-BIAS one-source note, locked-block disclosure fix. Runs nights and weekends with no new data |
| — | Arco platform rules watchdog (Mon/Thu) | 2×/wk | — | — | — | Different project; out of scope, not counted |

**One-shot tasks in flight (keep, not counted):** LEARN1 audit (11-18), REPS2 (11-18), RW7 Graveyard ask (11-18),
LATCH-CLOSE re-ask (11-20), SIZEUP1 re-evaluation (11-21).
**Disabled (no cost, housekeeping only):** Daily post images (replaced by the Friday report 11-09), Claude's pick shadow
(stopped 11-12), Restart-Guild one-shot (spent), consultant one-shot for today (replaced by the recurring check-in).
Proposal: the owner may let Claude delete these four; nothing depends on them.

**Total now: ~580 agent runs and ~1,150 units a week. The Guild is ~420 runs (72%) and ~840 units (73%).**

## 3. Redesign — keep the Guild and Reddit, aim them at gaps

The Guild and Reddit stay (owner). The change is *what* they work on and *how often*: both feed from one gap list
instead of open-ended idea hunting, which is what produced 0 setups from ~100 ideas.

### 3a. One gap list, refreshed nightly (no new agent)

`research/gaps/GAPS.md` (+ `gaps.json`), written by BDI daily as a by-product of the Move Hunt and the consultant's
day-type split. Each row = one **mechanism gap**: a category of big moves no live setup catches, or a day type where
Primary loses with no positive coverage. Columns: gap id, category (earnings reaction, opening drive 09:35-09:45,
gap-up day, sector move, inverse/vol ETF, up-day long, quiet-day long, ETB-only short), moves missed last 10 sessions,
R missed (tradable-only), day types, existing backlog ideas on it (by mechanism), status (open / in test / closed).
Ranked by tradable R missed. This is C3-MECH's "~60% of research on mechanism / day-type candidates" made concrete.

### 3b. Guild: 5 roles × 12 runs/day × 7 days → 3 roles, one round per weeknight + Saturday

| Now | Proposed |
|---|---|
| Scout, Builder, Skeptic, Observer, Lead; every 2 h, 24/7 (60 runs/day) | **Mechanism Scout**, **Builder**, **Skeptic**; one round per weeknight (~20:15 / 20:45 / 21:15 ET, after BDI daily and the brief) + one Saturday round after the BDI deep run |
| Open board, any idea | Each round takes the **top 1-2 open GAPS.md rows** only. Scout writes a mechanism card (day-type condition + falsifiable reason + pre-registered rule + pass bar); Builder runs ONE pre-registered backtest (2y, costs in, locked block never read, configs counted, ETB universe for shorts, vs random entries, w/o best day); Skeptic reviews before anything reaches the inbox |
| Lead steers | **Dropped**: the daily consultant + BDI refocus already steer (one steering voice, not two) |
| Observer watches live | **Dropped**: Move Hunt + the nightly loop already observe live; the Observer's live notes move to the Move Hunt section |
| Process / methodology finds (COMPCAL, PROMO2, RULE21-DB) | Kept as the Skeptic's second duty: one process/methodology check per week (Saturday), so the Guild's one proven contribution survives |

Runs: 3 × 5 + 3 = **18/wk (was 420, −96%)**; units ~45 (was 840). Each run has more depth than now (one full test per
night instead of a slice of one), and nothing runs at 03:00 on stale data.
Kill/keep rule (pre-registered): after 4 weeks, if the Guild has 0 ideas passing research on gap rows **and** no
approved process item, the owner gets a one-line ask (keep / weekly only / pause). If ≥ 1 passes research, keep.

### 3c. Reddit scout: daily → weekly (Saturday), filtered to missing mechanisms

- Runs once a week before the Saturday Guild round; scans the week (same subreddits; read-only).
- Keeps only ideas that map to an **open GAPS.md row** (long / up-day / quiet-day / earnings / opening-drive / ETB short),
  by mechanism, not wording. Everything else is skipped and only counted.
- No own backtest: a kept idea becomes a mechanism card for the Guild Builder (max 2 / week), so there is one test
  harness, one configs count and one Skeptic review.
- Runs: **1/wk (was 5)**; units 3 (was 15).

### 3d. Top-20 deep dive + top-5 tuning (daily L) → split

- **Part B (top-5 execution tuning, 378 variants / 0 to Testing; on the consultant's "Stop doing" list)** becomes the
  **C3-WB5 / Workbench queue job**: on the nights the approved Workbench queue has an item (C3-WB5's 5 tunes, one copy
  per night, ≤ 2 changed parts, tune type by parent record per C3-WB), run that one item; otherwise skip. No more
  open-ended one-knob grids on the 5 busiest setups. This *uses* the approved C3-WB rules rather than dropping Part B
  outright (C3-LEAN was declined).
- **Part A (conditions table)** → weekly, inside the Saturday BDI deep run (the charter already rotates "the full 20
  at least weekly"). It also feeds the day-type rows of GAPS.md.
- Runs: ~5 M while the WB queue lasts (~1-2 weeks), then ~0-2/wk; units 40 → ~15 then ~5.

### 3e. In-session checks: merge, keep the 30-minute rhythm

- **Merge the session guard (:47) into the :51 glitch check.** The glitch check already checks the Primary trade job;
  it adds "all 10 accounts' session jobs + Hunch/Compass watchdog" (script check, same agent). The 08:40 / 09:05 / 09:35
  start guards already cover the pre-open hours the 08:47 session guard covered. Saves 35 S runs/wk; the hourly
  job check stays (at :51 instead of :47).
- Keep the :21 BDI monitor and :51 glitch check (30-minute Primary rhythm, owner 11-11), and all three start guards
  (owner 11-13). These are the cheapest routines and the ones a usage-limit day loses first; protecting them is a
  goal of this plan, not a saving target.

### 3f. One shadow / replay scorer instead of scattered re-scores

The forward-logs task (16:33, S) becomes the **single scripted scorer**: late turn, dip-day, LEASH, regime switch,
compass conditional, latch shadow, REPS2 shadow score + replay-with-real-quotes re-score. Scripts only, one inbox block;
no analysis agent unless a pass bar is reached. The nightly loop drops its 6c shadow sub-steps (and the stale 6b
watch items: CWT14 PDL watch, PDL-1a R2A, RW3S observation; 6c2 BRAKE-1 if the owner agrees) and only reads the block.
Nightly loop L 40 → ~32 units; scorer stays S. This keeps the consultant's shadow/replay re-scores, cheaper and on
one clock.

### 3g. Unchanged (core to the consultant's goals)

Daily consultant check-in, BDI daily (refocused), nightly loop (trimmed), nightly brief, arena rotation, blocked-signal
audit (absorbs the C3-ROT "zero-signal / 60%+ blocked" triage every 2 sessions, so no new job), Friday report,
Saturday BDI deep run (+ Part A), parked-ideas review (→ monthly, folded with a monthly usage check of this table).

## 4. Lean cadence

| When | Routine | Cost |
|---|---|---|
| **Daily (weekdays)** 08:40 / 09:05 / 09:35 | Start guards | S |
| 09:51-15:51 hourly at :51 | Glitch check + job/Hunch/Compass watchdog (merged) | S |
| 10:21-15:21 hourly at :21 | BDI Primary monitor | S |
| 16:33 | Shadow / replay / forward scorer (scripts) | S |
| 16:47 | Nightly loop (trimmed) | L |
| 17:04 | Consultant check-in | M |
| 17:22 | BDI daily (Move Hunt → GAPS.md) | L |
| 17:23 | Arena rotation (acts every 4 sessions) | S / M |
| 18:07 | Workbench queue item (only when queued) | M or skip |
| 19:17 | Owner brief | M |
| ~20:15-21:15 | Guild round: Scout → Builder → Skeptic on top GAPS.md rows | 3 × 2 |
| **Weekly** Mon/Thu 17:43 | Blocked-signal audit (+ C3-ROT triage) | M |
| Fri 17:31 | End-of-week report (+ C3-EXIT100 / GY-LIFE Friday lists, epoch window) | M |
| Sat 10:47 | BDI deep run + top-20 Part A | L |
| Sat after | Reddit weekly (gap-filtered) → Guild Saturday round + weekly process check | M + 3 × 2 |
| **Monthly** 1st | Parked-ideas review + usage check of this table | S |

## 5. Expected savings

| Block | Runs/wk now → proposed | Units/wk now → proposed |
|---|---|---|
| Guild | 420 → 18 | 840 → 45 |
| Reddit | 5 → 1 | 15 → 3 |
| Top-20 / top-5 | 5 → ~5 then ~1 | 40 → ~15 then ~5 (+4 on Saturday) |
| Session guard → glitch check | 35 → 0 | 35 → 0 (+7 on the glitch check) |
| Nightly loop shadow trim | 5 → 5 | 40 → 32 |
| Parked review | 0.5 → 0.25 | 0.5 → 0.25 |
| Everything else | unchanged | unchanged |
| **Total** | **~580 → ~140 (−76%)** | **~1,150 → ~290 (−75%)** |

- **Without the Guild change** (if the owner keeps its schedule): units ~1,150 → ~1,080 (−6%), runs ~580 → ~540 (−7%).
- **Sensitivity:** if a Guild run costs 1 unit instead of 2, today's total is ~730 and the saving is ~65%; if 3, ~1,570
  and ~81%. Either way the Guild schedule is most of the bill, and the plan keeps the Guild.
- **What is not lost:** every safety check, the consultant check-in, BDI refocus, all shadow/replay re-scores, the C3
  queue. Expected R effect of the cut work: ~0 (the Guild, Reddit and Top-5 B had 0 setup passes from ~480
  ideas/variants). The gain is fewer usage-limit days, i.e. no missed 13:21 / 13:51 Primary checks, and more depth per
  Guild/Workbench run.
- **Rule changes in the window** (ledger): Testing half-size + promotion hold 11-17, rule 21 decision-bar audit 11-17,
  COMPCAL display 11-17, recorded quotes + SRCV1 11-18, C3 approvals 11-18. None changes this inventory's counts; the
  Guild's yields above span the whole window.

## 6. Implementation (only after the owner's USAGE1 yes; after hours; no setup/exit change)

1. Write `research/gaps/GAPS.md` generator into BDI daily's prompt (Move Hunt section).
2. Update the 5 Guild tasks: disable Lead + Observer (kept, not deleted), set Scout/Builder/Skeptic to weeknight
   20:15/20:45/21:15 + Saturday; new PROTOCOL section "gap rounds".
3. Reddit scout: weekly Saturday cron + gap filter + hand-off to Guild Builder.
4. Top-20/top-5: prompt → Workbench queue item; Part A sentence added to the Saturday deep run.
5. Glitch check prompt absorbs the session guard; session guard disabled (kept).
6. Forward-logs task becomes the scripted scorer; nightly loop 6b/6c trimmed.
7. Parked review → monthly; delete the 4 disabled tasks if the owner agrees.
Each change is a scheduled-task edit plus one ledger note (process change, no setup/exit change).

Reply codes: **USAGE1 yes** (all of 3a-3g), **USAGE1 guild** (Guild + Reddit + GAPS only), **USAGE1 safe** (3d-3f
only: no Guild/Reddit change), **USAGE1 no**.
