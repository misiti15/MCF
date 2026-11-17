# Replay calibration — targets (written 2026-11-17, BEFORE any scoring)

*Educational only — not financial advice. Pre-registration for the owner's "replay calibration yes" (2026-11-16): "It
needs to be 98% or higher in terms of accuracy compared to live testing ... how can we be sure this has the same testing
effect as live testing and not the rose-colored glasses effect?" Terms as in docs/GLOSSARY.md ("Session replay").
This file is committed before the calibrated replay is run on any held-out session; it is not edited after scoring
(a later change gets a dated addendum below the line, never an edit above it).*

## Data split (fixed now)

| set | sessions | accounts | use |
|---|---|---|---|
| TRAIN | 2026-10-22 .. 2026-10-30 (7 sessions; live poll logs exist from 10-22) — plus 10-06 .. 10-30 journals for the spread table only | Primary, Testing 1 (`testing`), Testing 2 (`testing2`) | every fitted number (spread table, fill-within-minute weight, any switch on/off) |
| HELD-OUT | 2026-11-02 .. 2026-11-16 (11 sessions) | same three accounts | scored ONCE with the frozen calibrated replay; no change after it is read |

Not scored here (no train sessions): Testing D/E/F (from 11-12), Explore 1 / Live Lab (from 11-05), Gen (93 setups;
too slow for the time box). Their replay sessions keep the "uncalibrated" weight until scored the same way.

## Unit and matching

- **Live trade** = a filled live entry (journal `trades`, run 1, joined to its entry signal by order id); **replay
  trade** = a filled replay entry.
- **Match** = same setup + symbol + side + **decision bar** (`info.bar_time`, exact minute; ±1 minute reported as a
  secondary number only), one-to-one, live → replay.
- R per trade = after costs with the **LR8 live cost model applied to each side's own fills** (live: actual fills;
  replay: simulated fills), so a cost-model change (LR8 from 11-12) cannot show up as a replay gap.

## Targets (all must hold on HELD-OUT, per account and pooled)

| # | metric | target |
|---|---|---|
| T1 | trade match = matched / live trades | **≥ 98%** |
| T2 | extra = unmatched replay trades / live trades | **≤ 2%** |
| T3 | R bias = mean(replay R − live R) over matched pairs, 95% CI clustered by session | **|mean| ≤ 0.01R** AND **not optimistic**: one-sided, mean − 1.645·SE ≤ 0 |
| T4 | daily R: account-day total R, replay vs live | Pearson **≥ 0.95** and sign agreement **≥ 90%** of account-days |
| T5 | skip-reason match: live signals (all statuses) matched in replay with the same status and reason category | **≥ 95%** |
| T6 | worst day: per account, the live worst day is the replay's worst day, and replay R on it is within max(10%, 2R) of live | holds for every account |

Per setup (≥ 10 live trades in held-out) the same numbers are reported, every setup listed, no setup dropped.

## Anti-rose-colored-glasses rules

1. **Haircut:** every replay R used anywhere = replay R − (measured optimism, the > 0 part of the held-out bias) − 0.02R.
2. **Fresh out-of-sample every night:** every new live session is re-scored as held-out (nightly drift report); an
   alert goes to the owner inbox if the rolling held-out match / extra / bias falls outside the targets.
3. **Partial weight only, earned on held-out data** (config/effective_sessions.json): 0.35 per replay session at
   ≥ 98% held-out match, ≤ 2% extra and no optimism; 0.2 at 95–98%; 0 below 95%. Until held-out targets are met the
   replay stays at the lower tier.
4. **Primary still needs real live confirmation** (On Deck ≥ 5 live sessions; Primary needs the full live record).
5. No tuning on held-out: the calibrated replay is frozen (code commit + fitted parameters file) before the held-out run.
   The number of configurations tried on TRAIN is reported.
6. If replay and live disagree beyond noise, live wins.

## Gaps closed before scoring (what "calibrated replay" means)

1. Full live universe per day (session packs, `--universe live`).
2. Live poll schedule per account and day from the poll logs (actual poll times and fetch latency; outages / late polls =
   no decisions; bars that arrived late at a poll are hidden from that poll).
3. Spread quotes: per-symbol spread table fitted on TRAIN-period journals only.
4. Order latency: decision at poll time + fetch latency; market entries fill inside the minute bar at a weight fitted on
   TRAIN (live fill vs bar open/close).
5. Shortability / ETB from that day's universe.csv (not today's flags).
6. Caps / lots / twin cascade, halts, latches: the real runner code, account state starting flat (intraday accounts
   flatten 15:55).
7. LR8 costs on actual fills (scoring, both sides).
