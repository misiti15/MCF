# BDI 2026-10-13: passive-limit entry for the 09:45 dip edge (A) and a split-tape gate for shorts (B): pre-declaration

*Educational only - not financial advice. Written 2026-10-13 after the close, before any configuration of this study
was scored. Results go in NOTES.md. This file may only gain dated amendments, written before the affected
configurations are scored.*

Inputs seen before writing: `research/bdi/nightly1013/NOTES.md` (Testing 1 shorts -$760 in the 11:30-13:00 QQQ
rebound on a split tape, QQQ +0.56% / IWM -0.46%), `research/bdi/dips1013/NOTES.md` + `summary.json` (stocks down
>= 0.75% at the 09:45 close beat a same-minute random long by +0.055R, t 5.4, but the x2.1 09:45 entry cost eats
it), `research/bdi/indexlink/NOTES.md` (ix-gate: 912 SPY/QQQ "market agrees" conditions, 0 pass; QQQ-vs-VWAP agrees
pooled -0.023R vs blocked). No number of this study had been computed.

Data rules (both parts): open two-year history only. The rule-19 locked block 2024-11-01..2025-02-28 is never
loaded (`lib.load_month` refuses it; 1-minute cache rows inside it are dropped right after each read);
`MCF_HIST_ALLOW_LOCKED` is never set. Splits: train = sessions <= 2025-12-31, valid = 2026-01-02..2026-10-07,
open = both (426 sessions). Statistics: day-clustered t (`gates.summary` formula), up / down sessions
(`lib.regimes()`), walk-forward share (`gates.walk_forward`), ex-best-day, busiest-session share. Survivorship caveat
as rule 19.

## Part A - passive limit entry for the 09:45 dip (lineage `dips1013-B` continued, id `bdi1013-limit945`)
**Signals (6), all from the dips1013 E945 lines that cleared the excess bar** (dip measured at the 09:45 5-minute
bar close = close of the 09:44 minute; O = first 09:30 minute open; PC = O / (1 + gap/100)):
- S1 `O-p0.75-none`: close <= O x (1 - 0.75%).
- S2 `O-p0.75-capd`: S1 and capd (09:40-09:45 5-min volume <= 50% of the max 5-min volume of 09:30..09:45).
- S3 `O-p0.75-qqqmid`: S1 and QQQ 09:45 close > midpoint of QQQ open and QQQ session low.
- S4 `B-p0.75-capd`: 0.75% below both O and PC, and capd.
- S5 `B-p1.0-capd`: 1.0% below both, and capd.
- S6 `PC-p0.75-flat-qqqmid`: 0.75% below PC, |gap| < 0.5%, and qqqmid.
Population: point-in-time adv20 >= $95M and atr_d > 0 (frames at 09:50), one signal per symbol-day.

**Exits (3)**: t1s05, t1s1, t05s1 (R = 0.25 x daily ATR, levels relative to the actual fill price). Simulated on
1-minute bars: stop first inside a minute, a minute that opens through the stop fills at its open, target fills at the
target, timed exit at the 15:55 bar close (close of the 15:54 minute). In the fill minute itself only the stop is
checked (conservative: no same-minute target).

**Entries (49)**:
- `MKT`: market at the 09:45 close (baseline; entry cost x2.1 as dips1013).
- Limit buy at L = C945 x (1 - x bps), x in {0, 5, 10, 20}, or L = C945 - a x atr_d, a in {0.05, 0.10} (6 offsets;
  x = 0 is the "at the bid" proxy - the history has no quotes, so the last trade is used, which is optimistic vs a
  real bid by half a spread; noted), valid v in {1, 3, 5, 10} minutes from 09:45:00 (minutes 09:45..09:45+v-1).
  **Fill only if a 1-minute low trades through: low <= L - $0.01**; the fill price is L, the fill minute is the first
  such minute.
- Two unfilled policies: `LIM` (skip the trade) and `CHASE` (market at the close of the last valid minute, entry cost x
  the time-of-day multiplier of that minute's end).
- 6 x 4 x 2 + 1 = 49.

**Costs**: filled limit entry pays no spread / slippage charge and no tod multiplier, only a fee proxy of 0.5 bps
(Alpaca has no commission; SEC/TAF are sell-side and already inside the exit charge). Market entries pay (1c + 1 bps)
x `gates.tod_cost_mult`. Exits as dips1013: target free, stop 1c + 1 bps + 2c, timed 1c + 1 bps. x3 on the extended
tier (|gap| >= 20% or price < $5). Sensitivity for finalists only (not counted): filled limits charged the full
1c + 1 bps (x1.0).

**Grid: 6 signals x 3 exits x 49 entries = 882.** Controls (counted): random-limit control = every eligible symbol-day
with the same limit rule (24 limit variants x 3 exits = 72) and the market random control (3) = 75.
**Part A N = 957.** Lineage bar: dips1013 Part B lineage 102,021 + 957 = 102,978 -> t >= sqrt(2 ln N) = 4.80.

Reported for every configuration: n signals, n filled, fill rate, exp / t (train, valid, open), excess vs the
same-session market control (mean of all eligible symbols' MKT trade with the same exit) and vs the same-session
random-limit control (mean of all eligible symbols' filled trades under the same limit rule), up / down exp, and the
**adverse-selection lines**: MKT-entry R of the filled signals vs MKT-entry R of the unfilled signals ("what the
unfilled ones would have made"), and the price-improvement gain (limit R - MKT R on the same filled trades).

**Finalists**: for each signal x exit (18), the LIM or CHASE configuration with the highest train exp among those with
train n >= 100, plus the MKT baseline of each signal x exit (18) for comparison = 36 rows, every one reported.

**Bars** (fixed now):
- Research gate (Primary): open n >= 150, exp > 0, t >= 4.80, up and down exp > 0, WF >= 0.6, ex-best-day > 0,
  busiest session <= 10%. And it must be runnable.
- Testing-1 bar (experimental tag): open exp > 0 with t >= 2.0; train and valid exp > 0; up and down exp > 0;
  excess vs the market control > 0 with t >= 2; WF >= 0.6; ex-best-day > 0; busiest <= 10%; plateau = both neighbour
  offsets (same validity) and both neighbour validities (same offset) have exp > 0.
- Runnability caveat known now: LabStrategy windows start at 09:50 and the runner places market brackets only, so a
  09:45 resting-limit entry needs an mcf/ execution hook. A pass would therefore be routed as a backlog hook request,
  not a config change.

## Part B - split-tape / index-divergence gate for SHORT setups (lineage `ix-gate` continued, id `bdi1013-splitgate`)
**Lists (35)**: the live short trade lists already built (and re-costed with the time-of-day entry cost) in
`research/bdi/indexlink/data/gate_trades.parquet`:
- Primary `-cur` (live windows): MF1, MF2, MF3, MF4, MF5, NS2, NS3, NS4, RW6G1 (9).
- Testing 1 `-FD`: MF1-5, NS2-4, RW6G1 (9), RW1-RW7 (7), ST3, ST5, ST6 (3), L3-gap-slope rsi5hi / lowdist / fromopen
  (short side only) (3), exhaustion_short-FD and -cur, heat_fade_short-FD and -cur (4).
- Plus 2 pooled books: Primary (the 9 lists) and Testing 1 (the 26 lists).
Window/config check: default.yaml windows for MF/NS/RW6G1 are unchanged since the lists were built (2026-10-11).

**Context at the entry bar** (bar close tod; values from the indexlink 1-minute ETF array at the close of the bar's
last minute): QQQ / IWM / SPY fromOpen (vs the 09:30 open) and distance to session VWAP (cumulative 1-minute typical
price x volume), QQQ 30-minute change.

**Gates (10)** - a short is **skipped** (blocked) when:
- G1 `split`: QQQ fo > 0 and QQQ above VWAP and IWM fo < 0 (the owner-described tape).
- G2 `split-dz`: G1 with 0.10% dead zones (QQQ fo > +0.10%, QQQ VWAP dist > +0.10%, IWM fo < -0.10%).
- G3 `qqq-up`: QQQ fo > 0 and QQQ above VWAP (large-cap rising intraday, IWM ignored).
- G4 `qqq-fo`: QQQ fo > 0.
- G5 `spy-up`: SPY fo > 0 and SPY above VWAP.
- G6/G7/G8 `div-x`: QQQ fo - IWM fo >= x, x in {0.25, 0.50, 0.75}%.
- G9 `split+div`: G1 and QQQ fo - IWM fo >= 0.50%.
- G10 `split-rebound`: QQQ 30-minute change > 0 and QQQ above VWAP and IWM fo < 0 (the 11:46-12:30 rebound shape).
**Grid: 10 gates x 37 (35 lists + 2 pools) = 370.** Lineage N = ix-gate 912 + regime1009 1,052 + 370 = 2,334 ->
t >= 3.94.

Per list x gate: base n / exp / t; kept n / exp / t; change; blocked n / exp; kept-minus-blocked difference with a
day-clustered (cluster-robust) t; train / valid change; up / down kept exp; WF share; ex-best-day; busiest session.

**Bars** (fixed now):
- Primary (proposed change): the gated list passes n >= 150, exp > 0, t >= 3.94, up and down > 0, WF >= 0.6,
  ex-best-day > 0, busiest <= 10%, AND the gate raises exp vs the base in train AND valid.
- Portfolio-wide gate: raises exp in >= 75% of the 35 lists in train AND in valid, and the pooled (Primary or Testing
  1 pool) kept-minus-blocked t <= -3.94 (blocked trades worse than kept), with its neighbours (G1/G2, G6/G7/G8) the
  same sign.
- Testing-1 bar (experimental gate for the Testing 1 short book): on the Testing 1 pool, kept-minus-blocked > 0 with
  day-clustered t >= 2.0, the pooled change > 0 in train AND valid, and the neighbour gates the same sign.
- Otherwise: backlog with the numbers.

A descriptive (not counted, not gated) replay of 2026-10-13: which of today's Testing 1 / Primary shorts each gate
would have skipped, from today's QQQ / IWM / SPY 1-minute bars.

## Counts
Study N = 957 (A) + 370 (B) = 1,327. Nothing is scored on the locked block.
