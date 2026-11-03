Educational only — not financial advice

# Live Lab daily pipeline — at most 5 new candidates a day, 20 seats, automatic exits (design, 2026-11-03)

Owner 2026-11-03: "a happy medium: quality setups for testing, but not so many that we run out of accounts/exposure —
something like the top 5 setups from Live Lab research per day, continuous research every day, a thorough system to
develop and test them without overwhelming the system."

This is a design only. No config, setup or exit change is made, and nothing is merged. It builds on:
- the lane rules in `research/bdi/night1102/livelab/NOTES.md` (gate, fail-fast, 20-session verdict);
- the account wiring on `claude/accounts-3new` (`config/account_livelab.yaml`, unmerged);
- the capacity study `research/ops/capacity1103/NOTES.md`.

**Rule-change context.** The base rates below come from the 10-06..11-02 live window. Several rule changes fall inside
it: the Graveyard opens 10-21, ST-A 10-22, GX1 5-minute clock 10-27, Primary size 10-28, Primary -2R stop and
generator pause 10-29, Testing CF 10-30, and R2A and the Graveyard moves 11-02 (see the night1102 NOTES for the list).
Number of configurations tried: 0 (design).

## 0. Facts this design is built on (measured elsewhere, re-used here)

- **The lane is supply-limited, not seat-limited.**
  - Of 374 backlog entries, only **3 pass the light gate cleanly** (night1102 `backlog_lane.csv`), and 6 more need a
    trade-count check.
  - The 30 ex30 exploratory setups pass **0 of 18,618 configurations** (ex30 CATALOG). They go to Explore 1 and 2, not
    the Live Lab.
- **The base rates are poor.**
  - Of 36 setups with ≥ 8 sessions and ≥ 40 trades, 22% were positive on their later trades.
  - The generator-style lane (Gen) averaged −0.284R over 990 trades.
  - Only one kill rule separated losers: after 45 trades, avg R ≤ −0.30 killed 9 of 50 setups, and none of the 9 was
    positive later.
- **Live noise.** A true +0.20R takes about 17 sessions to reach a day-clustered t of 1.5, and +0.30R takes about 8.
  So 20 sessions is the verdict window, and 5-10 sessions can only confirm a failure.
- **Capacity.** One account is one GitHub job, whatever its seat count. What seats do cost is the account's own poll
  coverage (CPU). Testing 1 runs 25 setups at 97-100% of polls. Testing 2 (45), the Graveyard (33) and Gen (93) run at
  66-94%. **A 20-seat cap keeps the Live Lab in the 97-100% band.**

## 1. Where candidates come from (daily, existing routines; nothing new to research)

| source (routine, ET) | what it hands the lane | expected gate-passers |
|---|---|---|
| BDI daily (17:22): Move Hunt precursors, QDAY quiet-day / both-ways ideas, the "≥ 1 new tested idea a day" | new setups / reworks with 2-year costs-in numbers | about 0.5-1 a day (most fail the gate) |
| Reddit scout (18:31) | top 1-3 ideas tested on the 2-year backtest | about 0-2 a week |
| Top-20 deep dive + top-5 tuning (18:07) | only variants whose parent is **not** live (Graveyard / retired). Variants of live setups stay in the normal backlog → Testing path, never in the lane (a twin would compete with its parent) | about 0-1 a week |
| ex30 / explore families | gen2 / family variants that pass the gate. The 30 delivered ex30 setups (gate = no) go to **Explore 1/2**, not here | 0 today |
| Backlog (`research/backlog.jsonl`, idea / rework / near-miss with a costs-in number) | re-checked once a week (Saturday deep run) | 3 now, plus up to 6 after a trade-count check |
| Setup Generator, only if the owner resumes it into the lane | at most 1 a day by quota | 0 (paused) |

**Realistic supply: 3-9 at the start, then about 1-3 gate-passers a week.**

## 2. The light gate (unchanged from night1102/livelab/PLAN.md and NOTES.md)

A candidate is admissible only if all of these hold:
- costs-in expectancy ≥ −0.02R on the open two-year TRAIN **and** VALID frames (production costs and the
  time-of-day entry multiplier; the locked block 2024-11-01..2025-02-28 is refused in code);
- 1.5-25 trades a session;
- the live module matches its scored version trade for trade (mask parity);
- it is not a duplicate of any setup live in any account, by mechanism, not by name;
- R by SPY up / down / quiet day is reported with it.

There is no t bar and no holdout at entry.

## 3. The daily ranked queue — at most 5 "on deck"

Every evening, all admissible candidates are scored with a fixed formula, declared here before any candidate is
scored:

```
score = VALID avg R × n/(n+150)                       (shrunk; n = VALID trades)
      + 0.04 if quiet-day R ≥ 0                         (QDAY focus, through 2026-11-17)
      + 0.04 if up-day R ≥ 0 and down-day R ≥ 0         (works both ways)
      + 0.03 if it would have caught ≥ 1 of the last 5 sessions' big moves that no live setup caught (Move Hunt)
      + 0.02 if long                                     (the book's weak side)
      − 0.03 if trades/session outside 3-15              (slow verdict, or a seat hog)
      − 0.05 per Live Lab seat its family already holds beyond 2
tie-break: earliest added
```

**Hard limits:**
- at most **5 on deck** a day (the top 5 by score);
- at most **2 from one source** among those 5;
- at most **3 seats per family** in the lab;
- at least **6 of the 20 seats long** whenever long candidates exist.

**Admissions:**
- Each day admits `min(5, free seats)` from the on-deck list, best first.
- A candidate that is on deck but not admitted stays queued for up to **10 sessions**, then returns to the backlog as
  `lane-expired` (it can re-enter if it is re-scored).
- When there are more candidates than seats, the lab simply stays full. It never goes over 20.

## 4. Seats, exits, verdict (frozen per setup at entry, in its `lane:` block)

- **Seat cap: 20** (200 slots, `max_positions_per_strategy` 10, about $1,000 lots).
  - A new setup only enters when a seat frees.
  - If the Live Lab's poll coverage falls below 90% on 2 sessions in a row, admissions pause and the cap drops to 16
    until coverage is back.
- **Fail-fast (automatic, applied the next session):**
  - after ≥ 5 sessions and ≥ 45 live trades, avg R ≤ −0.30;
  - or at any time, cumulative live R ≤ −15R.
  - The setup is switched off as a move out of the lab, and its backlog entry becomes `lane-failed` with its numbers.
    It is not deleted. Retiring a module still asks the owner (rule 20 precedent).
- **Verdict at 20 sessions and ≥ 40 trades.** Under 40 trades, the window extends once to 30 sessions, then the setup
  is judged or dropped as `too rare`. A **pass** needs all of these:
  - live avg R > 0 with day-clustered t ≥ 1.0;
  - avg R without the best day > 0, with the best-day share < 50% (one-big-day check);
  - ≥ 3 up and ≥ 3 down sessions seen, with avg R ≥ −0.05 on each;
  - shadow-track avg R > 0 (portfolio-blocked signals only; execution blocks are excluded).
- **A pass becomes a graduation DECISION** to the owner (promotion = move, so it leaves the lab in the same change).
  Live R and shadow R are reported separately. A fail becomes `lane-failed`.

## 5. Graduation and exposure balance (Testing 1 = Testing 2; Explore keeps its reps)

**Graduates go to Testing 1 or Testing 2 on equal footing.** The destination is whichever account has fewer enabled
setups, alternating on ties. That is placement by load, not by tier.
- Each Testing account gets a **soft cap of 35 setups**, or lower if its coverage drops below 90%.
- Testing 2 has 45 today (coverage 77-94%), so it takes **no graduate until it is below the cap**.
- If both accounts are full, the graduate waits on a **bench**: it keeps trading in its lab seat for up to 10 more
  sessions while the nightly loop's demotion suggestions free a Testing seat. The owner can also pick a swap.

**Explore 1 and 2 are a separate lane.**
- They take the ex30 setups (gate = no), with the same fail-fast and 20-session verdict.
- Each has its own seat cap of 15 (30 setups over 2 accounts).
- They do not draw from the Live Lab queue, and the Live Lab does not take Explore setups. One setup runs in one
  account (promotion = move).
- An Explore pass graduates to Testing 1/2 by the same rule. An Explore setup that fails but has a promising variant
  goes back to research. A re-worked variant enters through the queue like any other candidate.

**What this keeps for the existing accounts.**
- The lab is its own account, so lab setups never compete with Testing setups for symbols (place in line).
- Testing gets at most about 3 new setups a month (see below), offset by demotions.
- No account goes past its seat cap, so per-setup reps (median 4-5 trades a session) hold steady.

## 6. Steady-state numbers

**Assumptions** (from the night1102 base rates; to be re-measured after 20 lab sessions):
- 30% of entrants fail fast, at a mean of about 8 sessions;
- 55% reach the 20-session verdict;
- 15% extend to 30 sessions;
- this gives a **mean tenure of about 18 sessions**;
- the verdict pass rate is 15-25% (a 22% later-positive base rate; about a 16% false-pass chance on a true 0R before
  the other checks).

| quantity | seat-limited (supply ≥ 6/week) | supply-limited (likely now: about 2 gate-passers/week) |
|---|---|---|
| seats used | 20 | about 7 (2/week ÷ 5 sessions × 18 sessions) |
| entries / week | about 5.6 (20 seats ÷ 18 sessions × 5) | about 2 |
| exits / week | about 5.6 (about 1.7 fail-fast, 3.9 verdicts) | about 2 |
| verdicts / month | about 17 | about 6 |
| expected graduates / month | **about 3 (range 2-5)** | **about 1 (range 0-2)** |
| fill time from empty | 4 sessions at 5/day (if 20 candidates exist) | does not fill |
| GitHub jobs added | 1 trade job (+1 watchdog / EOD per fire); seats add 0 | same |

**Day 1 of the lane** (supply today): the 3 clean backlog setups, plus up to 2 after their trade-count check. That is
3-5 seats in the first week.

## 7. The routine (two scheduled tasks plus existing ones) and the config / code pieces

**Evening — "Live Lab queue (daily)", 18:56 ET weekdays** (after BDI 17:22 and top-20 18:07; Reddit's 18:31 results
count once they are committed, otherwise the next day):
1. `python -m mcf.research.lane evaluate --date <today>`: apply the frozen fail-fast and verdict rules to every lab
   setup from today's journal. This writes `docs/live/livelab.json` (sessions, n, avg R, day-clustered t, avg R
   without the best day plus its share, up / down / quiet R, shadow R, state).
2. `python -m mcf.research.lane gate --new`: run the light gate on the day's new candidates (each source writes them to
   `research/livelab/candidates.jsonl` with their numbers).
3. `python -m mcf.research.lane rank`: apply the score and hard limits, and write `research/livelab/queue.json` (on
   deck ≤ 5, admits = min(5, free seats), expiries).
4. Inbox:
   - one FYI line: "LL: N running / F failed-fast today / admits A, B tomorrow / queue Q";
   - a **DECISION only for a verdict pass** (graduation, with reply code `LL<k> T1` / `LL<k> T2` / `LL<k> wait`);
   - a veto code for admissions (`LL veto <k>`).
   - The routine ends with one line, "Live Lab queue done — in tonight's 19:17 brief."

**Morning — "Live Lab apply (daily)", 07:37 ET weekdays** (must merge before the 08:35 trade start; outside
09:30-16:00, so the setup-freeze check passes):
1. Read vetoes from `docs/live/decisions.json` and the chat answers.
2. Write one PR containing:
   - the admissions: each a `strategies:` entry plus a `lane:` block in `config/account_livelab.yaml`, with
     `setup_order` updated;
   - the fail-fast and verdict exits: switched off in the same overlay;
   - `docs/live/assignments.json` regenerated (`python -m mcf.report.assignments`);
   - one ledger entry per move, then `python -m mcf.research.ledger check`;
   - the full pytest suite.
3. Merge once the tests and setup-freeze pass.
4. If anything fails, **nothing is admitted that day** (the lab keeps yesterday's seats).

**The owner approves the lane rules once.** That is one ledger entry, `2026-11-xx-livelab-lane`, holding this
document's gate, score, limits, exits and verdict, frozen. After that, admissions and fail-fast exits within the rules
are automatic FYIs that the owner can veto. Graduations always need the owner's yes. For the first 2 weeks the owner may
prefer to approve each day's admits (`LL yes`); that costs one reply a night.

**Config / code pieces (not built; extends the night1102 "exact pieces"):**
1. `config/account_livelab.yaml` (on `claude/accounts-3new`): per setup a `lane:` block
   `{entered, source, score, gate: {train_exp, valid_exp, tpd, up/down/quiet}, window: {sessions: 20, min_trades: 40,
   extend_to: 30}, fail_fast: {min_sessions: 5, after_trades: 45, avg_r_le: -0.30, cum_r_le: -15}}`, plus a top-level
   `lane: {seat_cap: 20, coverage_floor: 0.90, admits_per_day: 5, per_source: 2, per_family: 3, min_long: 6,
   queue_ttl_sessions: 10}`.
2. `research/livelab/candidates.jsonl` (append-only: id, source, date, module, gate numbers) and
   `research/livelab/queue.json` (the day's on-deck, admits, expiries, vetoes).
3. `mcf/research/lane.py` (new): `gate()`, which refuses the locked block and checks parity and duplicates;
   `score()` / `rank()`, the formula and limits above; `evaluate()`, the frozen exits; and `plan()`, which writes the
   overlay diff for the morning PR.
4. `mcf/research/backlog.py`: the statuses `lane-queued | lane-running | lane-failed | lane-passed | lane-expired`, so
   the backlog shows where each candidate is.
5. `mcf/report/livelab.py` → `docs/live/livelab.json`, plus a dashboard tab (columns include "Avg R w/o best day" and
   the `1 day` tag).
6. Runner pieces from night1102: the `live.cross_setup_symbol_lock` flag (off in the lab), and the what-if
   `shadow_class` tag plus `no_sim` stub rows.
7. `tests/test_livelab.py`:
   - the gate refuses the locked block;
   - the queue never exceeds 5 on deck, 2 per source, 3 per family or 20 seats;
   - fail-fast fires at 45 trades and −0.30R;
   - a pass needs the one-big-day and up / down checks;
   - assignments are regenerated with every admit or exit.
8. Capacity guard: the morning routine skips admissions if `research/ops/capacity1103/measure.py` shows yesterday's
   exact GitHub peak above 14 or the lab's coverage below 90%.

**Rollout order** (with capacity1103):
1. Live Lab account first, with the 3 clean candidates.
2. 2 sessions of measurement.
3. Switch the queue on.
4. Explore 1, then Explore 2, each after 2 clean sessions.

Educational only — not financial advice.
