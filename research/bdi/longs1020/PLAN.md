# longs1020 — dip-timed longs (BDI, owner request 2026-10-20) — PLAN (written before anything is scored)

*Educational only — not financial advice. History backtests only (not paper, not live).*

Owner: "More attention to longs ... better timed on dips for longs on a bad market day or in general." Chart read
2026-10-20: SPY low −0.21% at 09:45 then +0.84% by 10:30; the live IDX1/2/3/5 dip-bounce setups (dip ≥ 0.5–1.0%)
did not fire because the dip was shallow.

## Data, split, costs (fixed)
- Open history only. Locked block 2024-11-01..2025-02-28 is never read: lab frames via `research/history2y/lib`
  (refuses it); 1-minute bars via pyarrow row filters that drop the block **before** the rows are materialised.
- TRAIN = open sessions ≤ 2025-12-31 (2024-09-16..10-31 for 1-min / 2024-10 for frames, and 2025-03..2025-12).
  VALID = 2026-01-01 onward (frames end 2026-10-07, 1-min bars 2026-10-16). Same split as swarm1017.
- Costs always in: production R (`gates.prod_r`, 1c + 1 bps per side, entry side × time-of-day multiplier,
  +2c on stop fills), ×3 on the extended tier (|gap| ≥ 20% or price < $5), as `arena.data.outcomes`.
- R = 0.25 × daily ATR (`atr_d` of the traded symbol, from the frames). Long only.
- Exits (4): `t1s1`, `t05s1` (lab outcomes, entry at the decision bar close, flat 15:55), `holdtr` (stop 1R; once
  +1R the stop trails 1R behind the best high; flat 15:55) and `time60` (stop 1R, exit at the close 60 minutes after
  entry). holdtr/time60 use a 1-minute path simulator: entry at the next 1-minute open after the decision bar, stop
  checked first inside each bar, a gap through the stop fills at the open. Parity of the simulator vs lab t1s1 is
  reported.
- Statistics: one trade per (setup, symbol, day) — the first qualifying bar; day-clustered t (`gates.summary`);
  regime = `gates.session_regimes` (up / flat / down by the universe median open-to-close, open-history terciles);
  also an ex-ante "bad tape" split: SPY below its open by ≥ 0.3% at the decision bar.

## Part 0 — descriptive: SPY / QQQ morning dip-then-bounce (not a search; no configurations counted)
Per session (1-minute bars): open, low of 09:30–11:00 and its time, dip % (open → low), dip in daily-ATR units and in
opening-range (09:30–09:45) units, bounce = highest high after the low until 12:00 minus the low (× dip), close vs open.
Tables: share of sessions whose 09:30–11:00 low prints 09:35–10:15; by dip bucket (0–0.1, 0.1–0.25, 0.25–0.5, 0.5–1,
> 1%): sessions, share with bounce ≥ 1× dip by 12:00 (back to the open), median bounce/dip, share closing above the open.
Predictors at the 10:00 decision (sessions where SPY's 5-minute-close running low is ≤ −0.10% by 10:00):
Y = 1 if the low so far is not broken before 12:00 AND SPY at 12:00 > SPY at 10:00; also ret(10:00→12:00).
Features (all known at 10:00): dip %, dip/ATR, recovery fraction off the low, gap %, close vs VWAP, close vs opening
range, prior-day SPY return, prior 5-day SPY return, IWM−SPY and QQQ−SPY from-open spread, breadth (share above VWAP)
and its change from its 09:50–10:00 low, 09:30–10:00 SPY volume vs its 20-day average. Report train AUC and
train/valid tercile means; a feature is "stable" if its sign agrees on train and valid.

## Part A — index-level dip-bounce longs (96 configurations + 8 A2 + 8 parents)
- Signal → instrument (2): SPY → SPXL, QQQ → TQQQ.
- 5-minute bars of the signal from its 1-minute bars; fo(t) = close(t)/open(09:30) − 1 (%; the live `spy_fo`),
  runmin(t) = min fo over bars closing 09:35..t.
- Dip (3): `abs015` runmin ≤ −0.15%; `abs030` runmin ≤ −0.30%; `rel020` runmin ≤ −0.20 × signal ATR% (atr_d/close).
- Trigger (4), decision bar close 09:50..10:30, first qualifying bar after the dip:
  `rec20` fo(t) ≥ runmin + 0.20·|runmin|; `vwap` signal 5-min close crosses above its session VWAP;
  `hl` low(t) > low(t−1) and close(t) > high(t−1) on the signal; `brd` breadth(t) ≥ min breadth(09:50..t) + 0.10 and
  fo(t) > fo(t−1).
- Exits (4). Total 2 × 3 × 4 × 4 = **96**.
- Parents (8, counted): IDX5 replica (SPY 1-min running low ≤ −0.5% by 09:45, 1-min 20% recovery 09:50–10:05 → SPXL)
  and IDX1 replica (QQQ ≤ −1.0% by 09:55 → TQQQ), 4 exits each.
- A2 (8, counted): the single Part-0 feature with the largest |train AUC − 0.5| becomes a filter (train median split,
  the bounce-favouring side) on the top 8 Part-A configurations by train t.
- Controls (not counted as candidates, reported): C_all = the instrument bought at a random bar 09:50–10:30 on every
  session (mean over all window bars); C_same = a random window bar after the dip on the same dip sessions.

## Part B — stock-level dip-timed longs (lab frames, adv20 ≥ $95M; 88 configurations)
Context columns `spy_fo`, `breadth` (live via LabStrategy `context:`); spymin = running min of spy_fo since 09:35
(early bars from SPY 1-minute bars, as the live frame has them).
- B1 index-dip + stock VWAP reclaim (0950–1100): spymin ≤ −d, spy_fo ≥ spymin + 0.10, stock vwapDistPct crosses > 0;
  d ∈ {0.15, 0.30} × RS ∈ {none, fromOpen > spy_fo} × 4 exits = 16.
- B2 bad-tape holder (stock above its open and VWAP while SPY is down): spy_fo ≤ −d, fromOpen > 0, vwapDistPct > 0,
  dist_pdl_atr > 0, close > prior bar high; d ∈ {0.30, 0.60} × window {0950–1100, 1100–1400} × 4 exits = 16.
- B3 oversold + breadth turn (0950–1130): rsi ≤ x, breadth ≥ min breadth today + b, spy_fo ≥ spymin + 0.15;
  x ∈ {30, 40} × b ∈ {0.05, 0.10} × 4 exits = 16.
- B4 relative strength on the dip + higher-low (spymin ≤ −d, fromOpen − spy_fo ≥ 0.5, low > prior low, close > prior
  high); d ∈ {0.15, 0.30} × window {0950–1030, 0950–1100} × 4 exits = 16.
- B5 live long setups with a dip-timing filter: parents NS1, NS5, ST2, ST4 (masks as swarm1017 rework-ns / rework-st,
  their own windows) × filter {IDXTURN: spymin ≤ −0.15 & spy_fo ≥ spymin + 0.10; BRDUP: breadth ≥ breadth two bars
  earlier + 0.05} × exit {parent geom, holdtr} = 16; parents themselves 4 × 2 exits = 8 (counted).
- Baseline: same-minute random long (mean over the universe at that date and bar), same exit; B5 also its parent.

## Count and bar
N = 96 + 8 + 8 + 64 + 16 + 8 = **200** pre-declared configurations (+ controls, reported). Study bar
max(1.5, sqrt(2 ln 200)) = **3.26**; lineage bars (idxdip/arena/dips lineages, > 100k) are reported too (~4.8–5.0).

## Candidate rule (Testing bar, pre-declared)
exp > 0 on TRAIN and VALID; beats its baseline(s) on both (Part A: C_all and C_same and the parent with the same
exit; Part B: the same-minute random long; B5 also the parent); VALID day-clustered t ≥ 1.5; n_train ≥ 30 (A) /
150 (B); exp without the best day > 0. Up to 4, ranked by VALID t, one per family. Down-session result reported for
each (owner wants longs that hold on bad days). Multiple-testing bar stated separately. If none: best near-misses.
No locked holdout is scored here (the lead does that once per version).
