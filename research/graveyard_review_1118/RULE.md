Educational only — not financial advice

# GY-LIFE — proposed standing Graveyard lifecycle rule (2026-11-18, for the owner)

Status: **proposal** (decision GY-LIFE). Nothing here changes config until the owner says yes. Rule 20 stands: nothing is
ever deleted; moving a setup into or out of the Graveyard, archiving and retiring are the owner's decisions; routines only
propose. Costs are always in (LR8); records are live journals only (rule 21: replays never count).

## 1. Entry (arena → Graveyard)

- **Trigger = C3-EXIT100 (approved 11-18):** a Testing / Gen / On Deck setup with 100+ live trades, 15+ active days,
  avg R ≤ -0.05 after costs and avg R w/o best day ≤ 0 is proposed at the Friday review. W7-DRAIN names are covered.
- It moves with its full block, names and `former_primary` marker and is switched off where it came from (promotion = move);
  `docs/live/assignments.json` regenerated and a ledger entry in the same commit.
- Low-activity trims never go to the Graveyard (they rotate through the low-rep homes, owner 11-03/11-04).

## 2. Status inside the Graveyard

Every resident carries exactly one of three states, set at the review and shown in `TRIAGE.csv`-style tables:

| State | Meaning |
|---|---|
| KEEP-TESTING | still collecting reps, or its Graveyard record is positive / improving |
| TUNE-CANDIDATE | meets the archive numbers but a pre-registered test of its family (C3-WB / C3-WB5) is pending; the parent keeps running untouched until that test reads |
| ARCHIVE (proposed) | meets every archive condition below; goes to the owner as a GY-ARCHIVE-N list |

## 3. Review cadence

- **Weekly, Friday after the close** (same window as C3-EPOCH): recompute the table, propose state changes in one owner-inbox
  line with a reply code (GY-ARCHIVE-N for archives, GY-OUT-N for graduations). No in-session changes (setup freeze).
- Active days count only sessions the setup was eligible to trade (benched sessions excluded, C3-ROT).
- Every row shows avg R, avg R w/o best day and the best day's share (`1 day` tag at ≥ 50%), last-5 / last-10 active
  sessions, day-type split, correlation with Primary winners, and the rule changes inside the window (ledger dates).

## 4. Archive rule (all must hold)

1. **Reps:** ≥ 100 Graveyard trades and ≥ 10 Graveyard active sessions.
2. **Graveyard record:** avg R ≤ -0.05 and avg R w/o best day ≤ 0.
3. **Whole live record** (all accounts, identical signals counted once): ≥ 150 trades and avg R w/o best day ≤ -0.05.
4. **No recovery:** total R over its last 10 active sessions ≤ 0.
5. **No pending test:** no pre-registered test of the setup or of its family is waiting to read. When one family test
   covers several copies, the copy named as the test's revival target stays TUNE-CANDIDATE; the others may be archived.

Archive = `enabled: false` plus an `archived: {from, code, reason}` marker in `config/account_graveyard.yaml`; the block,
display name, `former_primary` marker and journal rows stay; the leaderboard shows the setup with an "archived" tag and its
frozen record. It is **not** deleted and **not** retired (retiring stays the owner's separate decision under rule 20).
A TUNE-CANDIDATE whose family test fails is re-checked against 1-4 at the next Friday review.

## 5. Revival test (archive → back)

An archived setup comes back only by one of:

1. **Family / mechanism test passes** — a pre-registered single change (C3-WB: ≤ 2 parts, chosen on earlier sessions,
   out-of-sample + paired-shadow pass, costs in, try-count-scaled t bar). The tuned version re-enters the Graveyard as a new
   version (rule 22 versioning) for a 10-session probation; the untuned parent stays archived.
2. **New mechanism evidence** — e.g. a real-time day-type gate from C3-MECH research passes for that mechanism
   (heat_fade_short / -FD are the obvious first users: hindsight up-day -0.57 / -0.61R vs down-day +0.04 / +0.16R).
3. **Owner request.**

No revival on its own frozen record, and never by re-reading the locked block.

## 6. Graduation (Graveyard → arena)

Proposed (GY-OUT-N) when: ≥ 15 Graveyard active days, ≥ 30 Graveyard trades, whole-record avg R w/o best day > 0 and best
day < 50% of total (U8 transfer condition for RW6G1). It moves to Testing 1/2 or a low-rep home (promotion = move), never
to the same account as its twin.

## 7. Pot budget

- Target ≤ ~15 KEEP-TESTING + TUNE-CANDIDATE residents running at once, plus guests (GY-BENCH). Slots 300 / 75 per setup
  stay as they are (REPV-11/12).
- GY-BENCH (rest 5 sessions at > 150 Graveyard trades) stays for KEEP-TESTING / TUNE-CANDIDATE residents; archived
  setups no longer need it.
- C3-ROT cap (2 CWT14 per session) applies here as well while any CWT14 is active.

## Why

The Graveyard has never had an exit: 21 sessions, 2 green, -1,095R on 9,330 resident trades. 20 of 32 running residents
meet every archive condition and produced 82% of its trades and -66.5R per session over the 10 sessions before GY-BENCH.
Archiving them frees the pot for the C3-EXIT100 inflow (31 setups qualify now) without starving the few residents that
still have a case. See NOTES.md for the numbers.
