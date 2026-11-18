# Bespoke per-setup rules for Primary: design note (DRAFT, not implemented)

*Educational only — not financial advice.* Draft for the owner. No code or config changes come with this note.

Owner, 2026-11-17: "for any setup in the primary account … we should enable the ability to have bespoke rules and
conditions per setup … if something is being highly considered for primary account, we should allow it to run under the
best conditions possible, specifically made for that setup."

## 1. What already exists per setup (config `strategies.<id>` blocks)
| knob | what it does | where |
|---|---|---|
| `window`, `entry_from` / `entry_until` | entry time window | setups.py / lab modules |
| `prefilter`, module conditions (`gap`, `fromOpen`, …) | entry conditions (a copy = a new id) | lab modules |
| `refire`, `refire_cooldown` | re-entry chain on later bars | setups.py |
| `target_r`, `stop_atr`, `stop_atr_frac` | target and stop geometry (setups that expose them) | setups.py |
| `scale_out_r` + `live_scale_out` | partial at +x R, live only when opted in | setups.py / runner |
| `be_at_r`, `trail_r` / `trail_after_r` | breakeven move, trailing stop | runner exits |
| `time_stop_min` / `time_stop_min_r` | time stop if not working (WB4 uses 75 min) | runner exits |
| `spy_exit_pct`, `spy_exit_only_losing` | SPY-since-entry exit (SPYEXIT, 11-17) | runner / shadow / backtest |
| `max_lots_per_symbol` | per-setup lot cap ("2-lot option", 11-16) | risk.py `setup_lot_caps` |
| `max_stop_cost_r` | per-setup cost filter | risk.py `setup_cost_limits` |
| **`max_setup_daily_loss_r`** | **per-setup daily latch: a number, or null = off. Overrides the account's −2R** (GY-BENCH, 11-16) | risk.py `setup_loss_limits` / `loss_limit_for` |
| `twin_group`, `benched`, `guest` | twins, rotation, guests | risk.py / rotation |

So a fixed per-setup latch level **can already be set today** with one line in Primary's block. No code is needed for
that.

## 2. What is missing
1. **A time-windowed or state-dependent latch.** Today the limit is one number per setup. A bespoke rule like
   "−2 before 12:00, −3 after", or B6's "−3 when SPY at 10:00 is below its open", needs:
   `max_setup_daily_loss_r: {default: 2.0, after_1200: 3.0}` or
   `{default: 2.0, when: {spy_vs_open_at_1000_lt: 0.0}, then: 3.0}`.
   The runner would resolve the limit **at each entry decision** from point-in-time state only (the clock; SPY bars
   already known). The latch stays one-way: once tripped at the limit that applied then, the setup stays stopped
   unless the rule explicitly allows a later, wider limit. That choice must be written into the rule, and the backtest
   engine must use the same resolver (the shadow book and engine parity are already a requirement for SPYEXIT).
2. **The same override in the shadow book and the backtest engine**, so a bespoke rule is scored exactly as it trades.
3. **Visibility**: the dashboard and blueprint should show "bespoke: <rule> since <date> (ledger id)" next to the setup.
   blueprint.py already prints the account latch, and it should print the resolved per-setup one.
4. A **per-setup exit profile** (target_r / be_at_r / time stop) for `type: lab` setups without spawning a module copy.
   Today a Workbench copy is the way to do it, which is right for testing but heavy for a Primary rule.

## 3. Evidence bar for a bespoke Primary rule
A bespoke rule is a setup/exit change: research rules, the setup freeze and the ledger all apply. It ships only if:
1. **Pre-registered**: PLAN.md lists the rule family and every value tried before scoring, and the count goes into N.
2. **Validated**: it is better than the setup's current rule in the 2-year TRAIN and VALID splits and in the live-session
   replay. The full 2-year day-paired t is ≥ max(1.5, sqrt(2 ln N)) with N counted over the setup's lineage. It is also
   not worse in the setup's live journal record (paper fills; what-ifs labelled).
3. **Plateau**: neighbouring values (e.g. ±0.25R, ±15 min) are also better than the current rule, by at least half the
   gain. A lone spike is rejected. For a latch, the check is per *step*, since a level only sets the number of full
   stops (research/l3_bespoke_1117 Test A).
4. **One-big-day check**: the gain holds without the best session, and that session's share of the improvement is
   < 50%. A gain carried by 1-2 days is called out and does not ship.
5. **Costs in** (LR8), the locked block is never read, and it is reported with the configs tried and the rule-change
   context.
6. **Ledger**: an entry with effective date, patch, evidence path and the owner's approval. It is applied after hours
   (setup-freeze) and assignments are regenerated if the move rules apply. It is re-checked after ~10 Primary sessions,
   with an automatic revert to the account default if the live result runs below the old rule by more than the
   pre-set tolerance.

## 4. How this fits the owner's remedies rule (2026-11-05)
The remedies rule says a remedy for a failure mode must not be "tailored to one setup", and must not be so broad that
it hurts many setups. Bespoke Primary rules are a deliberate, bounded exception:
- **Account-wide remedies** (a new halt, a board-wide filter) still follow the remedies rule. They are targeted at the
  failure mode, with per-setup and per-family effects reported.
- **Primary setups** may also carry **evidence-backed bespoke rules**. These are tuning of one vetted car, not a remedy
  for the board. The tailoring risk (overfitting one setup) is controlled by the stricter bar in §3: pre-registration,
  lineage-counted t, plateau and the one-big-day check. That bar is higher than for a board remedy because the sample
  is one setup.
- A bespoke rule never changes another setup and never moves the account default. If several Primary setups end up
  with the same bespoke rule, that is a signal to consider it as an account-level remedy under the remedies rule.

## 5. First candidate (not proposed yet)
L3-gap-slope-fromopen-FD, per research/l3_bespoke_1117:
- Its fixed per-setup latch should stay at −2. −1.50..−2.00 is a plateau, the looser levels fail VALID, and the tighter
  levels would have cut 11-12.
- The one state rule with a consistent sign is **"−3 when SPY at 10:00 < its open, else −2"**. It reaches 2-year t 2.46
  against a bar of 2.74, and it is neutral live. It would need §2.1 (state-dependent latch) to run, and it should be
  re-scored once more Primary weak-start sessions exist.
