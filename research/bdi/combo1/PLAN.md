Educational only — not financial advice

# COMBO1 — pre-registered plan (written 2026-11-03 before any COMBO1 number in this folder was computed)

Owner 2026-11-03 ("COMBO1 yes", top of `research/queue.jsonl`): combine the week's small positives into one testable
setup family instead of testing each alone. Research only: no `config/`, setup, exit, ledger or trading-path change.

**Lineage.** BDI 11-03 already ran a first COMBO1 pass (`research/bdi/1103/combo1.py`, 9 configs: scan *names that lag
their peers* + fade bar, t1s1 / h1030H; 0 pass; backlog `combo1-1103-open-scan-laggard-fade`, parked). Those 9 count
toward this project's try-count. The configs below are new: they use the real 09:35 scan (opening 5-minute $ volume /
adv20, the eu1103/preopen measure; the 1103 pass used 09:35 volumeRatio as a proxy), and they take the side the
evidence points to (eu1103/edge: big single-name moves keep going; the fade bar is the *entry timing*, not the side).

## Inputs (locked block 2024-11-01..2025-02-28 never read)
- `research/bdi/timeofday/data/open/*.parquet`: lab-pipeline 5-minute rows, bar closes 09:35..10:30, lab t1s1 outcome
  (R = 0.25 x daily ATR, +1R target / -1R stop, out by 15:55). Locked block absent (asserted).
- `o5_hist.parquet`: 09:30-09:35 $ volume per symbol-day, built by `research/bdi/eu1103/preopen/build_o5.py` from the
  1-minute SIP cache with the locked block filtered out at read (asserted). Rebuilt into scratch, not committed (size).
- `research/history2y/data/daily.parquet` (SPY day type, peer / beta tables), locked dates dropped at load.
- Earnings blackout (+-4 trading days) removed (`mcf.research.generator.data._blackout`). SPY/QQQ/IWM/DIA not traded.
- Splits: TRAIN 2024-10 + 2025-03..2025-09; VALID 2025-10-01..2026-10-07.

## Building blocks (exact)
- **U — top-500 universe** (eu1103/universe): on each date, names with adv20 >= $95M and atr_d > 0 on the 09:35 row,
  ranked by adv20 x ATR% (ATR% = atr_d / 09:35 close x 100); keep the top 500.
- **S — 09:35 mover scan** (eu1103/preopen): the top 150 names of U by o5 $ volume / adv20.
- **z — ex-market move**: z = fromOpen / ATR% at the bar, minus that bar's cross-sectional median (ATR units).
- **Peer group** (MH4, bdi/1102): top-10 residual-correlation peers (daily returns ex-SPY beta, trailing 120 non-locked
  sessions before the month, corr >= 0.30, >= 6 peers). P = median peer z at the bar, agree = share of peers with the
  sign of P.
- **Fade bar (timing)**: the signal bar closes against the trade side (close < previous 5-min close for a long, > for a
  short) — the short-term reversal timing that is the book's only positive line (eu1103 Q1, +0.046R).

## The 3 combinations x 2 exits = 6 configurations
- **C1 SCAN-PB** (scan mover, pullback entry, continuation side): name in S; bar close 09:45..10:15; |z| >= 0.50;
  side = sign(z); fade bar against the side; first signal per symbol-day.
- **C2 SCAN-PB-GRP** (C1 + its group agrees): C1 and side x P >= 0.25 and agree >= 0.6.
- **C3 LAG-OF-SCAN** (peer laggard whose group is led by scanned movers): name in U, >= 2 of its peers in S, side =
  sign(P), side x P >= 0.40, agree >= 0.7, side x own z < side x P / 2; bar close 09:40..09:50; fade bar against the
  side; first per symbol-day.
- **Exits**: `t1s1` (lab bracket above) and `h1030H` (stop 1R = 0.25 ATR on later 5-min highs/lows, else out at the
  10:30 close, minus beta x SPY's move entry->10:30 in R; hedge leg costs 1c + 1 bps per side on beta x notional).

## Costs (realistic, entries cross the spread)
Per trade friction in R = max(0.10, production cost + spread crossing), where production cost = (1c + 1 bps) x
time-of-day multiplier on entry, 1c + 1 bps on exit (free on a t1s1 target fill), +2c on stops; spread crossing =
4.4 bps x price x time-of-day multiplier on entry (live entries fill +4.4 bps worse than the mid, eu1103/edge). The
mean friction per config is reported.

## Reported for every config (finalists and failures)
trades, trades/session (over all sessions in the split), avg R, day-clustered t, avg R ex-market (BETA1 OLS on SPY's
move over the trade window; for t1s1 the window is entry -> 15:55 SPY close, an approximation since exit times are not
in the frame), avg R without the best day and that day's share of total R (`1 day` flag at >= 50%), TRAIN / VALID avg
R, R split by SPY day type (open-to-close up > +0.25%, down < -0.25%, else quiet), walk-forward share of positive
months, day-matched excess (vs the mean of all eligible U names, same date + bar + side + exit).

## Gates (fixed now)
- **Try-count**: N = 9 (1103 pass) + 6 = 15 -> full bar sqrt(2 ln 15) = 2.33, **BAR90 t >= 2.09**.
- **BAR90 (rule 22)**: t >= 2.09, TRAIN > 0 and VALID > 0, positive on SPY up AND down days, walk-forward positive months
  >= 54%, day-matched excess > 0 (beats random); best-day share reported.
- **Live Lab light lane gate (night1102/livelab, LL1)**: TRAIN >= -0.02R and VALID >= -0.02R with the costs above,
  1.5-25 trades/session, not a duplicate of a live setup.
- Outcome: any lane pass -> Live Lab / Testing candidate DECISION in `research/owner_inbox/2026-11-03.md` (never
  Primary). Else one FYI line, and the best near-miss (highest VALID avg R among the 6) is parked with a frozen
  forward-shadow rule in `research/bdi/swings/hypotheses.jsonl` (forward pass: >= 20 sessions, >= 40 trades, avg R > 0,
  t >= 1.0, avg R w/o best day > 0). No locked-block look is spent in this project.
