# OPS-POLL: why Testing 2 and Generated poll 2-3x less often than the other accounts (2026-10-22)

*Educational only — not financial advice. Housekeeping (the live loop's speed); no setup, exit or risk rule changes.
Branch `claude/charming-mccarthy-i3rhhr`, **not merged**: it touches the live runner's signal path, so it merges after
the close / before 09:00 ET after the owner's review.*

## Answer first

- **Root cause: one line of bookkeeping, not the strategies.** Each lab setup with market context (`context:` —
  breadth, SPY/QQQ from open, QQQ vs VWAP) calls `lab_context.context_table()` once per symbol it checks. That function
  built its cache key by walking **every polled symbol's bars** (min/max timestamp, total bar count) **on every call**:
  ~70 ms per call with the ~4,000 live symbols. Gen has **40** context setups and Testing 2 **15**; Primary has 0,
  Testing 1 has 1, the Graveyard 0. At a 5-minute decision bar that is ~10,000+ calls → **10–25 minutes of key-building
  per poll** live. The context table itself was cached correctly; only the key was recomputed each time.
- **It compounds: a phase lock.** A poll that takes ~4.5 minutes ends just after the next 5-minute bar, so the next
  poll again starts at bar count ≡ 1 (mod 5) and the liquid names never sit on a decision bar when a poll looks.
  Generated polled every ~5.0 min from 11:00 to 15:00 and **saw 2 of the 63 decision bars (09:50–15:00) of names
  that trade every minute**. Testing 2 saw 39 of 63.
- **Fix (2 small, decision-neutral changes):** (1) compute that key once per poll — memoised on the poll's bars dict
  *and* the identity of every frame in it, so a new poll or any replaced frame gets a fresh key; (2) the lab setups of
  one symbol share one 5-minute resample of that poll's bars (it was redone by every setup; memoised on the same bars
  object only). Same inputs → same frames, same masks, same signals (tests below).
- **Measured offline (same session, same code path, lab universe ~1,060 symbols):** a 5-minute-bar poll
  **Gen 346 s → 100 s (3.5x)**, **Testing 2 307 s → 82 s (3.7x)** at 10:00; 11:00: Gen 337 s → 93 s,
  Testing 2 283 s → 90 s. Live the gain is larger (the key walk scales with ~4,000 live symbols, ~3.3x the replay's):
  expected **~230–300 polls/day for Testing 2 and Gen (was 157 / 126)**, no decision bar of a liquid name skipped.
- **Signals missed today** (from the poll logs, below): Testing 2 skipped **36%** of its symbol decision bars
  (24 of 63 bar times for every liquid name), Generated **47%** (61 of 63). Generated journaled 7 signals today against
  ~158/day its 40 setups fired in their screens — most of the gap is this. Value: on the 8-session Testing 2 replay
  (research/replay/VALIDATION.md) the signals the slow polls dropped were **slightly negative** (~−0.04 R/trade after
  paper fills), so recovering them is about measuring the setups honestly, not about money.

## 1. What the logs show

Poll-input logs `polls/2026-10-22/*.jsonl.gz` on each data branch (`mcf/execution/runner.py` poll_record /
read_poll_log). Gap = time between consecutive poll starts.

| account | polls | gap median | gap p90 | gap max | fetch median (`ms`) | context setups | lab setups |
|---|---|---|---|---|---|---|---|
| Primary | 379 | 0.98 min | 1.42 | 1.9 | 7.7 s | 0 | 11 |
| Testing 1 | 351 | 1.00 | 1.62 | 2.4 | 7.5 s | 1 | 26 (+7 other) |
| **Testing 2** | **157** | 1.34 | 4.89 | **17.5** | 8.4 s | **15** | 48 |
| **Generated** | **126** | 1.03 | 5.23 | **32.6** | 8.0 s | **40** | 40 |
| Graveyard | 329 | 1.03 | 1.70 | 2.3 | 6.9 s | 0 | 16 (+4 heat) |

By hour (Generated): 09:30–09:59 20 polls at ~1 min (no lab window open before 09:50 → nothing to evaluate);
10:00–10:59 **4 polls** (32.6 and 23.8 min gaps); 11:00–14:59 12 polls/hour at ~5.0 min; 15:00–15:55 ~1 min again
(windows close at 15:00). Testing 2: 10:00–11:59 gaps of 13–17.5 min, then 3.4–5 min until 15:00. The fetch is the
same ~7–8 s everywhere, so the time goes after the fetch.

Status health fields (`status.json` → health) only carry the fetch time (`last_poll_s`) and poll counter, and the
GitHub Actions job timing is not reachable from here (no Actions API in this session), so the split below is from an
offline run of the runner itself.

## 2. Where a poll's time goes (offline, the real runner)

`research/ops/pollspeed1022_profile.py`: builds the real `PaperRunner` for each account's current config on the
recorded session 2026-10-16 from the replay store (mcf/replay simulated clock / feed / quotes / broker — no network, no
orders; exact mode, the replay fast path off), restores, then calls `runner.step()` at 10:00, 10:01, 11:00, 13:30 and
times each phase with wall-clock wrappers (inclusive). `old` = the key walk and resample as before the fix. Universe:
the replay store's lab universe (1,077 symbols with priors, ~1,056 contexts); this box was shared with other jobs,
so absolute seconds are indicative, the ratios are what matter.

**Before → after, 5-minute-bar polls (seconds):**

| account | poll | before | after | of which before: context key walk | after: masks | after: frame build (heat_frame + extra_features) |
|---|---|---|---|---|---|---|
| Generated | 10:00 | 346.4 | **100.0** | 226.2 (65%) | 41.5 | 40.4 |
| Generated | 11:00 | 336.6 | **92.8** | 222.3 (66%) | 41.1 | 33.7 |
| Testing 2 | 10:00 | 306.9 | **82.2** | 169.0 (55%) | 27.8 | 37.1 |
| Testing 2 | 11:00 | 282.5 | **89.5** | 129.4 (46%) | 38.1 | 35.7 |

The remaining ~15 s "other" before the fix was mostly the per-setup 5-minute resample (fix 2: Gen 10:00 124 s with the
key fix alone → 100 s with both).

**After the fix, all accounts (same box, same session):**

| account | 10:00 (5-min bar) | 10:01 (not) | 11:00 | 13:30 |
|---|---|---|---|---|
| Primary | 44.7 s | 7.2 | 38.2 | 32.5 |
| Testing 1 | 56.3 s | 9.0 | 50.4 | 40.6 |
| Testing 2 | 82.2 | 13.2 | 89.5 | 62.8 |
| Generated | 100.0 | 17.4 | 92.8 | 62.8 |

Primary's offline 5-minute poll (~40 s on 1,056 names ≥ $95M ADV; live 1,175 such names) matches its live cadence
(~1 min with the 8 s fetch), so the offline seconds are a fair live proxy for the ≥ $95M population.

**Live scale.** The old key walk cost grows with *all* polled symbols (~4,000 live vs 1,200 here: ~3.3x per call) and
the number of calls grows with the eligible symbols (Gen has 13 setups at ≥ $20M ADV: 2,488 live names vs ~1,060
here; Testing 2 has 8 setups at $0–1M): that is the 10–30-minute live polls. After the fix the key is walked once per
poll; what is left is the frame build (~38 ms per symbol per 5-minute bar, shared by every lab setup) and each setup's
mask (~1–4 ms per symbol). Expected live 5-minute-bar polls: Gen ~2–3 min (≥ $20M names), Testing 2 ~2–3 min (all
names for its $0–1M setups) — like Testing 1 today (max gap 2.4 min, it also has $0 ADV setups) — and the polls in
between ~20–40 s.

## 3. Decision bars no poll evaluated today (2026-10-22)

`research/ops/pollspeed1022_missed.py`: a lab setup evaluates a symbol only when its bar count is a multiple of 5
(`LabStrategy.eligible`), and the runner acts only on the latest bar; a decision bar (count c, c % 5 = 0, c in 20..330
= bar closes 09:50..15:00 for a name trading every minute) is **missed** when no poll saw the symbol at exactly c bars.
Per-symbol counts come from each poll record (`exp` − k for the names under `miss[k]`, `exp` for the rest).
"Symbol decisions" ≈ 63 per symbol (fewer for names with missing minutes, so the total is an upper bound).

| account | polls | liquid-name decision bars missed (of 63) | symbol decisions missed | share |
|---|---|---|---|---|
| Primary | 379 | 0 | 1,775 | 0.7% |
| Testing 1 | 351 | 0 | 11,784 | 4.7% |
| **Testing 2** | 157 | **24** | **91,042** | **36%** |
| **Generated** | 126 | **61** | **119,089** | **47%** |
| Graveyard | 329 | 0 | 19,827 | 7.9% |

Testing 2 missed bar times: 09:55–10:10, 10:20–10:30, 10:40–10:45, 10:55–11:00, 11:10–11:15, 11:25–11:30, 12:25,
12:55, 13:05, 13:25, 13:35, 14:05, 14:15, 14:25, 14:55 (bar close times). Generated: every bar close 09:50–15:00
except 09:50 and 10:35.
(The small Primary / Testing 1 / Graveyard numbers are thinly traded names whose count passes a multiple of 5 during a
1–2-minute poll — the ordinary cost of polling once a minute.)

**Signals and value.** Today's journals: Testing 2 257 signals (138 trades), Generated 7 signals (4 trades). If
signals are spread evenly over decision bars, Testing 2 lost ~145 signals today (257 / 0.64 − 257). Generated's 40
setups averaged ~158 signals/day in their screens (sum of `gen.screen.per_day`; in-sample screen, not a tested edge):
7 is ~5% of that. Value: there are no replay results for 10-22 yet (the store ends 10-16 + the 10-19..21 fetch) and
none for Generated. The 8-session Testing 2 validation (10-12..10-21, research/replay/results/validation_paper.json,
gap.json) is the best estimate: the replay, which evaluates every decision bar, took 4,476 trades (−405.9 R, paper fills)
vs 2,740 live in-universe (−337.4 R); the ~1,700 extra trades were worth about **−68 R, ~−0.04 R/trade**. So the missed
signals were not a hidden profit; the cost is that Testing 2 and Generated measured a different (time-thinned) version
of their setups than their backtests and the replay — which is what these forward tests exist to measure.

## 4. The fix (commit on this branch)

1. `mcf/strategies/lab_context.py` — `context_table()` gets its key from `_peers_key(peers)`: the same key as before
   (symbol count, first bar, latest bar, total bars), walked once and memoised for the same dict object holding the
   same frame objects (a tuple of value ids is compared, ~0.1 ms for 4,000 names). The live runner builds a new bars
   dict every poll, so each poll gets a fresh key; a frame replaced in the same dict also invalidates it. The assembled
   table is cached under the same key (it was rebuilt per call from the cached columns).
2. `mcf/strategies/setups.py` — `LabStrategy.generate()` reuses the completed-5-minute resample of `ctx.bars` when it
   is the very same bars object (the runner scans every setup of a symbol with one bars object per poll); any other
   object (next poll, revised bars) is resampled afresh. The frame cache (`_LAB_FRAMES`) and its key are unchanged.

No trading rule, setup, window, exit, cap or order path changed; entries, prices and decisions are identical for the
bars a poll sees — the only behavioural change is that more decision bars get seen.

**Not done (options, need the owner):**
- *Catch-up* — evaluate a skipped 5-minute decision bar at the next poll with a late entry at the current price. It
  would change entries (late fills, different prices than the backtest measures), so it is a rule change, not
  housekeeping; with the fix it should rarely be needed. Can be built behind a flag if the post-fix poll logs still
  show skipped bars.
- *Further speed* (only if the logs say so): the GEN masks recompute arena indicators per setup and symbol (~40% of a
  Gen poll now); the frame build (~40%) could be made incremental per 5-minute bar (the replay's prefix property).
- Seen while reading: `_LAB_FRAMES` keys on (symbol, date, bar count, last bar time), so a bar revised by a late print
  between two polls with the same count keeps the earlier frame. Pre-existing, rare, unchanged here.

## 5. Tests

`tests/test_pollspeed.py` (6): the memoised key equals the old key; a new poll dict / a replaced frame gets a fresh key;
every context table identical with the old key on a synthetic day; a context lab setup polled through a synthetic day
gives **the same signals** with the memo and with the old key (equivalence); the key walk runs **once** for 400
add_context calls in one poll and the memo path is faster (timing); the resample memo is used only for the same bars
object, recomputes for revised bars, and gives identical signals with the memo forced off. Full suite: 406 passed (`python -m pytest -q`).

## 6. Expected after the fix, and how to check

- Polls/day: Testing 2 and Generated **~230–300** (was 157 / 126; Primary 379, Testing 1 351). The first post-fix
  session's poll log answers it: `python research/ops/pollspeed1022_missed.py <dir> <date>` should show 0 liquid-name
  decision bars missed for both, and symbol decisions missed in the Testing 1 range (≲ 5–8%).
- If a 5-minute-bar poll still runs over ~4 minutes, the phase lock returns: then do the further-speed items above
  before catch-up.

Raw numbers: `research/ops/pollspeed1022_results.json` (per-poll phases before/after, missed-bar counts).
