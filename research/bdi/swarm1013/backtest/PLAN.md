# swarm1013 rule candidates on the two-year history: pre-declaration

*Educational only - not financial advice. Written 2026-10-14 before any configuration of this study was scored.
Results go in NOTES.md. This file may only gain dated amendments, written before the affected configurations are
scored.*

Input: `research/bdi/swarm1013/{worst_1_5,worst_6_10,top_3}.md`, the rule candidates from reviewing Primary's
2026-10-13 paper trades (n = 18 trades, one session: hypotheses only). Lead's brief: families E1-E6 below, applied to
the live Primary lab setups MF1-MF5, NS1-NS5 and RW6G1 (`config/default.yaml`).

Seen before writing this plan: the three swarm files, `docs/RESEARCH_RULES.md`, `mcf/research/gates.py`, the
dips1013 engine/prep (code only), `research/history2y/{lib,rescore}.py` and the row counts per setup in
`research/history2y/data/lab_trades.parquet` (published RESCORE material). No result of this study had been computed.

## 0. Data and conventions
**Data (open two-year history only).**
- Signals: each live module's `mask()` on the history frames (`lib.load_month`, open months only), the YAML window,
  point-in-time adv20 >= min_adv ($95M), first qualifying bar per symbol-day per setup (the lab convention; live
  allows same-setup re-entries on new signals, which this study does not model).
  - RW6G1 needs volume (VWAP + 2 SD guard): its NS2/fromOpen>3 base comes from the frame, the guard is computed with
    the module's own `vwap_band_block` on 5-minute bars rebuilt from the 1-minute cache from 09:35.
- Paths: 5-minute OHLCV bars rebuilt from the SIP 1-minute cache (`data/cache_hist/1Min`), bar close 09:35..16:00,
  as dips1013/prep.py. Locked-block rows (2024-11-01..2025-02-28) are dropped right after every read;
  `MCF_HIST_ALLOW_LOCKED` is never set. The locked block is the lead's, not scored here.
- ETFs: `research/bdi/indexlink/data/etf1m.npz` (QQQ, SMH, sector ETFs; 426 open sessions). Session VWAP of an ETF =
  cumulative 5-minute typical price x volume (heat_frame formula). Sector ETF per symbol =
  `research/bdi/indexlink/linkage.csv` `sector_etf` (highest-correlation sector ETF over the open history: a mild
  look-ahead in the mapping only); QQQ when missing.
- Daily closes: `lib.daily()` (locked block excluded).
- Survivorship caveat (rule 19): today's universe applied to the past.

**Fills and costs (gates production costs, always in).**
- R = 0.25 x daily ATR (lab R) for every rule; all results are in lab R. Geometry (up, dn) from each module's GEOM
  (`gates.GEOMK`): MF1 t1s05, MF2 t1s05, MF3 t1s1, MF4 t05s1, MF5 t1s1, NS1 t05s1, NS2 t1s1, NS3 t1s1, NS4 t1s05,
  NS5 t1s1, RW6G1 t1s1.
- **B0 lab baseline (reference):** entry at the signal bar close, brackets from it, entry cost (1c + 1 bps) x
  `gates.tod_cost_mult`.
- **B1 live-model baseline (the baseline for E1-E6):** the signal bar close is the reference price `ref`; the fill is
  the next 5-minute bar's open +/- the half spread h = (1c + 1 bps x px) x tod_cost_mult (paid in the price, not charged
  again); stop and target are anchored at `ref` (as live: ref -/+ dn R, ref +/- up R).
- Exit simulation on 5-minute bars from the fill bar (k+1) to the 15:55 bar: stop first inside a bar; a bar opening
  through the stop fills at its open; target as a limit at the target; timed exit at the 15:55 close.
- Exit costs: target (limit) free; stop / trailing stop / breakeven stop = 1c + 1 bps + 2c; market exits (timed,
  index exit, time stop) = 1c + 1 bps at the bar close. Everything x3 on the extended tier (|gap| >= 20% or
  price < $5).
- Partial exits: each half is costed as its own exit (the extra fill is charged).

**Splits and statistics.**
- train = open sessions <= 2025-12-31; valid = 2026-01-02..2026-10-07; open = both.
- Every config is compared with B1 on the **same trades** (the baseline trades of its scope). Paired delta per baseline
  trade: d = r_rule - r_B1; a skipped trade has r_rule = 0 (so d = -r_B1).
- Day-clustered t (`gates.summary` formula) for exp R and for the delta; up/flat/down regime split (`lib.regimes()`,
  a same-day label used only for reporting and the up/down gate); ex-best-day; walk-forward share of positive test
  months (`gates.walk_forward` on the delta series, locked months excluded).

## 1. Grid (every cell is counted)
Scopes: `ALL` (11 setups pooled) and each setup = 12 scopes, unless stated.

**E1 fill-anchored brackets (5 variants x 12 scopes = 60).**
- `A`: stop and target re-anchored at the fill.
- `K25` / `K50`: skip when progress = side x (fill - ref) / R >= 0.25 / 0.5 (brackets at ref, as B1).
- `AK25` / `AK50`: fill-anchored and the same skip.

**E2 partial / trail (4 x 12 = 48).** R = lab R.
- `P-T05`: 50% at the setup's target (= 1R for t1 geometries; 0.5R for t05s1 MF4/NS1), remainder trails 0.5R
  behind the best price since entry (initial stop until then); the remainder ends at the trail, the original stop, or
  15:55.
- `P-BAR`: 50% at the target, remainder's stop = the prior completed 5-minute bar's high (short) / low (long), only
  ever tightened.
- `NT075` / `NT100`: no target; once MFE >= 0.75R / 1.0R, trail 0.5R behind the best price; initial stop until then.
- Trail levels update at bar closes and apply from the next bar (no intrabar look-ahead).

**E3 index-reclaim exit (6 variants x 14 scopes = 84).** Scopes: ALL, SHORTS (9), LONGS (2), each of 11 setups.
- Short: exit at the close of the first 5-minute bar after the fill bar's start (bars k+1..) on which the index closes
  above its session VWAP; long mirror: closes below. Brackets stay; stop/target inside a bar take precedence over the
  close-based exit.
- Index: `QQQ`, `SMH`, `SECT` (sector ETF). Entry condition: `any`, or `aln` = only arm the exit if the index was on
  the trade's side of its VWAP at the signal bar (short: index close <= VWAP).

**E4 time stop / breakeven (7 x 12 = 84).**
- `T20` / `T30` / `T45`: at the close of the bar 20/30/45 minutes after the fill (bar k+4 / k+6 / k+9) exit at market
  if MFE so far < 0.5R.
- `BE03`: once MFE >= 0.3R (bar close), stop moves to the fill price (from the next bar).
- `T20+BE`, `T30+BE`, `T45+BE`: both.

**E5 correlated-lot cap (portfolio replay of the Primary book; 5 variants x (book + 11 setup breakdowns) = 60).**
- Book = every B1 trade of the 11 setups, ordered by signal bar then config order; a position is open from its fill
  bar until its B1 exit bar. A new trade is skipped if >= `c` open same-side positions (not skipped themselves) have a
  20-session 5-minute-return correlation >= `rho` with it (prior 20 open sessions with data, intraday 5-minute log
  returns; >= 10 sessions required, else no skip).
- Variants: (rho, c) in {(0.35, 2) [the candidate], (0.50, 2), (0.35, 1), (0.50, 1)}, and `SECT2`: >= 2 open
  same-side positions with the same sector ETF.
- The book is not slot-limited (160 slots, max_lots_per_symbol 3 not binding at this size; stated).

**E6 setup filters (skip rules; 42).**
- `MF5-a` on MF5 only (4): fromOpen > 0 & vwapDistPct >= 0.10; fromOpen > 0 only; vwapDistPct >= 0.10 only;
  fromOpen > 0 & vwapDistPct >= 0.20.
- `FS30` flow-sell divergence (2 thresholds x 6 scopes = 12): skip a short when the stock's 30-minute return
  (signal close / close 6 bars earlier, or the 09:30 open if earlier) > +0.25% / +0.50%. Scopes: MF pooled, MF1..MF5.
- `NS2-3D` (2 x 3 = 6): skip when the 3-session return (prior close / close 3 sessions before, NaN across the dropped
  block = no skip) < -10% / -15%. Scopes: NS2, RW6G1, NS2+RW6G1 pooled.
- `SIR` stop-inside-range (2 x 10 = 20): skip a short when the ref-anchored stop < max high of the last 15 / 30
  minutes (5-minute bars k-2..k / k-5..k). Scopes: SHORTS pooled and each of the 9 short setups.

**References (counted): B0 and B1 x 12 scopes = 24.**

**Study N = 60 + 48 + 84 + 84 + 60 + 42 + 24 = 402. t_required = max(1.5, sqrt(2 ln 402)) = 3.46.**
Prior lineages: book-wide exit overlays (EXIT_STUDY t6-exit-overlay, sw-w4-book-exits, t1-orb-exits) failed; the
E2/E4 families are their continuation and this N is counted on top (stated, not merged, because those counts are not
all recorded in one place).

## 2. Gates (fixed in advance), per config cell
- G1 n_open (baseline trades in scope) >= 150.
- G2 paired delta > 0 on train and on valid.
- G3 delta day-clustered t on open >= 3.46.
- G4 delta > 0 in up sessions and in down sessions.
- G5 delta ex-best-day > 0, and walk-forward positive-month share of the delta >= 0.6.
- G6 plateau: every pre-declared neighbour has open delta > 0. Neighbours: E1 K25<->K50, AK25<->AK50, A<->AK25;
  E2 NT075<->NT100, P-T05<->P-BAR; E3 the other two indexes with the same entry condition; E4 the adjacent time stop
  (T20<->T30<->T45) and the same time stop with/without BE (BE03<->T30+BE); E5 adjacent rho and c; E6 the other
  threshold(s) of the same filter.
- G7 the rule's own trade set: open exp > 0 after costs, and > 0 in up and in down sessions.

**Routing.**
- *Primary candidate:* G1-G7 all pass -> goes to the lead for the one-time locked-block score (rule 19, look 1:
  t >= 1.0), then backlog gates and ledger; never straight to Primary.
- *Testing 1:* G1, G2, G4, G6 pass and delta t_open >= 2.0, but G3 or G7 fails.
- *Backlog (record only):* everything else, with its numbers.

**Finalists (reported in full, failures included):** per family, the 3 cells with the highest train delta t among
n_open >= 150 and train delta > 0, plus every cell that passes G1-G4. Chosen on train; valid and open reported.

## Amendments
(none)
