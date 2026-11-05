# GATE1 — checkpoint market-state gate: pre-registration (written 2026-11-05 before any GATE1 number was computed)

*Educational only — not financial advice.* Research only; nothing in config/ or the trading path changes.

Owner question (2026-11-04): switch setups ON when the market is shaping up their way, keep them restricted when the
day looks bad, re-checked every 30 minutes; and what can be told after the first 30 min / 1 h / 2 h / 3 h.

## Data and windows
- Market state from SIP 1-minute SPY / QQQ / IWM (`data/cache_hist/1Min`), breadth from the lab context tables
  (`research/history2y/data/context`, lab universe 1,226 names — not the live top-500; same measure on 2 years and live).
- Trades: 2-year lab lists `research/history2y/data/bt_lab1104` (95 setups, uncapped, production R after costs, entry =
  `tod`); live paper journals run_id 1 of all five accounts (`git show origin/mcf-data*:journal.db`), R = pnl_adj / risk.
- TRAIN = 2024-10 + 2025-03-01..2025-12-31; VALID = 2026-01-01..2026-10-05; LIVE = 2026-10-06..2026-11-04.
  Locked block 2024-11-01..2025-02-28 never read (dates dropped on load of the 1-minute index bars as well).

## Point-in-time features at checkpoint T (only bars that closed by T)
Checkpoints every 30 min 10:00..15:30 (plus 09:45 used only for confirmation at 10:00).
fo = SPY last close / 09:30 open − 1; vw = SPY close vs session VWAP (1-min typical price × volume); r30 = SPY 30-min
return; QQQ/IWM fo; breadth_open / breadth = share of lab universe above own open / own VWAP at the 5-min bar ending T;
rng = (SPY high − low so far)/open vs median of the same figure at T over the prior 20 sessions; gap = SPY open / prior close − 1.

## States (fixed)
- **UP** at T: fo ≥ +0.15% AND vw > 0 AND breadth_open ≥ 0.50 AND (QQQ fo > 0 OR IWM fo > 0).
- **DOWN** at T: fo ≤ −0.15% AND vw < 0 AND breadth_open ≤ 0.50 AND (QQQ fo < 0 OR IWM fo < 0).
- **MIXED** otherwise (descriptive sub-tag QUIET = MIXED with rng < 0.75).
- **Confirmed (k)**: k = 1 the state at T; k = 2 the state at T and at the previous checkpoint agree (else MIXED).
- A trade entered at minute m ≥ start uses the confirmed state of the latest checkpoint T ≤ m (re-checked every 30 min,
  switching on/off). Trades before the start checkpoint are never touched.

## Predictive tables (descriptive)
Per checkpoint 10:00, 10:30, 11:00, 11:30, 12:00, 12:30, 13:00, 14:00 and state: days; share of days where SPY close vs
price at T has the state's sign (UP/DOWN) and base rate; EOD day type (SPY open→close ≥ +0.25% up, ≤ −0.25% down, else
quiet); avg R of trades entered after T by side and by family×side, split by state, TRAIN / VALID / LIVE.

## Gates scored (N = 62 configurations; bar t ≥ max(1.5, sqrt(2 ln 62)) = 2.87)
- **G-learn** (36): unit ∈ {side, family×side, setup} × start ∈ {10:00, 10:30, 11:00} × k ∈ {1, 2} × restricted ∈ {off, half}.
  Family = leading letters of the setup name (CWT, L, MF, NS, RW, ST, NM, GEN, …). Allowed states of a unit = states with
  TRAIN avg R > 0, n ≥ min (side 500, family 200, setup 60 trades) and ≥ 15 days. A unit with no allowed state, or all
  three allowed, is ungated. Live setups without lab coverage: family/side gates by name; setup gate leaves them ungated.
- **G-dir** (24): SPY-direction gate, strict (longs only in UP, shorts only in DOWN) or lenient (longs off in DOWN,
  shorts off in UP) × start 3 × k 2 × off/half.
- **REG1** (2): at 10:00 shorts only if SPY ≥ open, longs only if SPY < open, rest of day, no re-check; off / half.
- Baseline: no gate.

## Metrics and pass rule
Total R, avg R, avg R w/o best day + best-day share, trades kept, green-day rate (daily R > 0), max drawdown of daily R,
R by EOD day type; TRAIN → VALID → LIVE; plus the **excess delta** (dropped trades scored against the unit's own mean in
that window), to separate state timing from "trading less of a losing book".
**Pass** = VALID day-clustered t of (gated − no-gate) daily R ≥ 2.87 AND TRAIN delta > 0 AND LIVE delta > 0 AND VALID
excess-delta t ≥ 1.0. Pass and holds live → DECISION (shadow first). Close (VALID t ≥ 1.5 with the other legs) → forward
shadow lead `gate1-checkpoint-gate` with this bar. Graveyard: a setup is a "conditional performer" if one state has TRAIN
avg R > +0.05 (n ≥ 60) and VALID avg R > 0 in the same state while its other states are ≤ 0 on TRAIN.

Amendment (before any score): the context table has no 5-minute breadth row before 09:50, so the 09:45 state (used only
for k = 2 confirmation at 10:00) uses the SPY / QQQ / IWM conditions without breadth. Sessions before 2024-10-01 (no
frames) have no breadth and are outside every window anyway. The context table ends at the 15:00 bar, so 15:30 uses the 15:00 breadth (older, still point-in-time).

## Addendum COMPASS (owner reframe 2026-11-04 evening; written after the GATE1 gate results above were read, before any compass number)
Three questions at each checkpoint, point-in-time only: (1) moved so far (SPY fo, reported); (2) STAYING = P(SPY closes on
the same side of its open as at T); (3) HEADING = sign of SPY close vs price at T (rest of day) and sign of SPY 60 min after T.
Measures (each a +1 / −1 / abstain call): fo sign; vw sign; r30 sign; persist2 (fo same sign at T and previous checkpoint);
persist3 (and the one before); breadth_open side of 0.5; index agreement (SPY, QQQ, IWM fo same sign); pre-registered state;
strong move (|fo| ≥ 0.30%); gap sign; fade-r30 (−r30 sign); fade-fo (−fo sign). 12 measures × 3 outcomes = 36 looks.
Hit rate with Wilson 95% CI and lift vs the base hit of a same-mix call; ranked on TRAIN, checked on VALID and LIVE.
**Compass reading** (fixed now): votes v = sign(fo) + sign(vw) + persist2 + breadth side + index agreement (each −1/0/+1).
UP-confirmed: v ≥ 4 and persist3 = +1; leaning up: v ≥ 2 (not confirmed); DOWN-confirmed / leaning down mirrored; else mixed.
Usage rule: family × side allowed in compass readings with TRAIN avg R > 0 (n ≥ 200, ≥ 15 days), ungated if none / all;
entries from 10:00, latest checkpoint, off / half; also setup-level (n ≥ 60). 4 gate configs; compass hit tables 3 looks.
Total study looks now 62 + 7 + 36 + 3 + 4 = 112 → bar max(1.5, sqrt(2 ln 112)) = 3.07.
