# UPDAY diagnosis — Gap-Down Recovery Fade (all day) `L3-gap-slope-fromopen-FD` on up-market days
Educational only — not financial advice. Mechanic 2026-11-17 (after hours). Full bucket tables: `diag_buckets.txt`.

**Day type** (both tests, reporting only): SPY 09:50 close → 16:00 close; up > +0.25%, down < −0.25%, quiet between.
Gates may only use what is known at the signal bar: SPY % since the 09:50 close (`spy950`), SPY % over the last 30 minutes
(`spy30`), the stock's move since 09:50 minus SPY's (`rs950`), time of day. Breadth exists in the 2-year frames but not for the
replay sessions after 11-04, so it could not be tested on identical terms (not used).

## 1. Where the parent loses — it is an up-day problem
| test | up days (avg R / trades / total R) | down days | quiet days |
|---|---|---|---|
| Session replay (23 sessions: 8 up / 6 down / 9 quiet) | −0.150 / 100 / −15.0R | −0.008 / 71 / −0.6R | +0.202 / 179 / +36.1R |
| 2-year backtest (417 sessions: 147 up / 113 down / 157 quiet) | −0.147 / 2,051 / −300.8R | +0.149 / 1,369 / +204.1R | −0.093 / 1,465 / −135.8R |
In the 2-year test up days cost −301R, more than the parent's whole −233R. WB4 (13:00 end, gap ≤ −3.2%, 75-min hold) already
softens them: replay up +0.152, 2-year −0.103.

## 2. Why a simple "pause when SPY is up" does not fix it
- The up-day losers are mostly entered BEFORE the market's rise is visible. Parent replay, up days, by SPY since 09:50 at entry:
  ≤ +0.15%: about −0.7R per trade (15 trades); +0.15..+0.30%: −0.525 (21); +0.30..+0.50%: −0.145 (44); > +0.50%: +0.635 (20).
  2-year up days are negative in every bucket (−0.07 to −0.51; −1.04 on 6 trades).
- Trades taken while SPY is already up are not the bad ones: SPY > +0.25% at entry → replay +0.405 vs −0.113 otherwise
  (2-year −0.033 vs −0.055). A skip gate therefore removes winners (G1 skip > +0.25%: replay +0.059 → −0.049).
- Up days hurt by time of day (parent 2-year, up days): before 10:30 −0.160, 11-12 −0.215, 12-13 −0.171, after 13:00 −0.045.
  Replay up days: before 10:30 −0.736, after 13:00 −0.378.
- Relative strength since 09:50 and gap size do not separate up-day losers consistently (replay and 2-year disagree by bucket).

## 3. What the failure looks like inside the trade
The short is opened on a stock that has bounced > 3.5% off its open; on an up day the market keeps lifting it and the lot
drifts to the stop. The signal the setup is missing is not visible at entry — it shows AFTER entry, as SPY rising. So the
targeted remedy is an exit that reacts to SPY rising after entry (fixes the failure where it occurs, does not touch trades on
days when SPY does not rise), plus not opening new late lots once the market is already up (afternoon up-state entries have
little time left to work and keep the book full).

## 4. Parts tried, by family (42 configs; full table in RESULTS.md)
| family | parts | result |
|---|---|---|
| Up-day skip gates | G1-G4 (SPY > +0.25 / +0.40% since 09:50, SPY 30-min > +0.20%, both) | cut replay winners or worse 2-year; G3 helps replay only |
| Size-down on up states | S1, S2 (half size) | R-weighted avg R falls in replay; 2-year unchanged |
| Up-state exits | X1-X4 (hold 60, target 0.75R, stop 0.8R, half off at +0.5R) | all lower the replay |
| Stricter entry on up states | Q1-Q3 (gap ≤ −5%, fromOpen > 5, RS since 09:50 < 4%) | all lower the replay |
| Time of day on up states | T1 (no U entries after 12:00), T2 (none before 10:30 while SPY rising) | pass on meets; up days better in replay only |
| In-trade SPY exit | Y1-Y3, R2a-R2c, Z1-Z2 (exit once SPY +0.20..+0.50% since entry; U-only; under-water only) | **lifts up days in both tests, 2-year down days ~unchanged** |
| Combos | R2d-R2f, Z3, Z4, Z8 | **R2d (SPY +0.30% exit + no U entries after 12:00) best balance → WB5** |
| On WB4 | W1-W6, Z5-Z7, V1-V4 | SPY exit costs WB4 replay winners (W1-W3, Z5-Z6); only V2 (no U entries before 11:00) and Z7 meet WB4; V2 lifts up days in both tests |
