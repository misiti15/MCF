Educational only — not financial advice.

# HEDGE-B pre-registration (written 2026-11-26 18:24 UTC, before any hedge configuration below was built or scored)

Source: consultant memo A (research/consultants_1126/A_REGIME_PM.md §2 "hedge, don't block (B8 → H8)" and §3 HEDGE-B).
Owner request 2026-11-26: "every effort to diversify Primary toward fewer red days". RESEARCH_RULES rule 26 guards
"hedge promotions"; **the owner's 11-26 request explicitly lifts that guard for this test** (flagged here, as memo A
flagged it). Research only: no config, ledger, decisions.json or live change. Engine label (rule 31): E4 one-off
simulator = the squeeze_1125 / neveragain minute book engine (research/squeeze_1125/sim.py), re-used, with the hedge
overlay added as a post-step on its per-minute book state.

## Configurations (N = 2) and references
- **H8**: B = 8. **H4**: B = 4 (near-full). Counted: **cumulative N ≈ 2,271 → 2,273** (primshorts_1126 reported
  ≈ 2,271; nothing equity-side reported since: consultant memos C/A 0 configs; crypto_setups1 counts in its own family,
  N_cum 1,491). Family bar stated descriptively: sqrt(2 ln 2273) ≈ 3.93.
- References, not counted: **REF** (the lot book, no hedge) and **B8 block** (squeeze_1125 R1 net-beta entry block,
  B = 8). Placebo (below) not counted.

## Hedge rule (fixed now)
- Net book beta E(m) = Σ b_i over the open lots at the end of minute m, b_i = side × β_i × 0.01 × entry / risk
  (R per +1% SPY; β_i exactly as squeeze_1125: 60-session point-in-time daily beta to SPY, ≥ 20 obs else 1.0,
  shrunk 0.67·β̂ + 0.33, clipped [−3, 3]). E_IWM(m) = the same with each lot's beta to IWM (same formula vs IWM).
- Target h*(m) = −sign(E) × max(|E| − B, 0), in R per +1% SPY, decided on state at the end of minute m and **filled at
  the close of bar m+1** (next-bar fill). Rebalance only when |h* − h| ≥ 2.0 (hysteresis band, memo A), except:
  the hedge is flattened (next bar) whenever the book has no open lots, and **always flattened at the 15:55 bar close**.
- Leg split (memo A "SPY/IWM in proportion to E/E_IWM"): IWM share f = |E_IWM| / (|E| + |E_IWM|) at each rebalance
  (0 if both 0); SPY leg value = 100 × (1 − f) × h* R-dollars; IWM leg value = 100 × f × h* / β_IWM→SPY R-dollars
  (β_IWM→SPY = IWM's raw 60-session point-in-time beta to SPY, ≥ 20 obs, else 1.2), so the legs together carry h* R per
  +1% SPY. Shares are fixed between rebalances; leg P&L = shares × price change (1-min closes).
- Hedge costs per traded notional: 0.5 bp half-spread + 0.5 bp slippage per side (1.0 bp), plus fees: SEC 20.60 $/M on
  sell notional charged on every date (conservative), CAT 0.00005 $/share/side and TAF 0.000195 $/share sold (≈ 0 at
  ETF prices, included). Borrow for short SPY/IWM intraday = 0.
- The hedge is an **overlay**: it does not count toward per-setup latches or the −20R halt, so the lot set is identical
  to REF and only beta is removed. Hedge P&L (gross, cost, net) is reported as its own line. Buying power is not
  modelled (lots are in R); the report states peak hedge notional and peak gross (lots + hedge) at 1R ≈ $67 against
  ~$336k (4×).

## Lot books (contexts) and cost model
- Primary book rules as squeeze_1125: P4 lineup (L3-gap-slope-fromopen-FD, RW3, RW5, NM-ETF-late-dip-di-long), ≥ $5,
  shorts ETB ≥ 0.9, 30 lots per setup, ≤ 3 per symbol per setup, 77 slots, burst brake 30/10 min, −2R latch,
  −20R closed+open halt. Lots = bench10 regenerated for the 4 setups (squeeze_1125/gen.py unchanged).
- Costs on stocks: **LIVE-L** (primshorts_1126 cells_live.json) for the shorts; NM-ETF keeps LR8 research (as primshorts).
- 4 contexts: {P4, L3-OUT (L3-fromopen removed)} × {BASE latch, LATCH-OPEN (LO)}. **The pass bar is judged on P4+LO**
  (memo A's spec); the other three contexts are reported with the same bar applied.
- Books: **RAW**; **Z** = every lot shifted so each setup's mean is 0 (shift = the setup's average R over lots taken in
  that context's RAW REF run, pooled FIT+CHECK+T2; open marks shifted pro rata over the lot's duration, as squeeze);
  **P** = the same shifted so each setup averages **+0.10R**. Z and P are re-simulated (latch/halt see shifted R).

## Splits
FIT 2024-10 + 2025-03..09 (confirmation only, nothing tuned); CHECK 2025-10-01..2026-11-04; T2 2023-01-03..2024-09-13.
The locked block 2024-11-01..2025-02-28 is filtered at load (pyarrow filters) and **asserted absent** in every script.
Live window 2026-10-23..2026-11-25: Primary journal lots (run 1, LR8 cost-R as footrace.live_trades; journal via
`git show origin/mcf-data:journal.db`, copied to the scratchpad and deleted after), Alpaca SIP 1-min bars (open marks,
SPY, IWM), Alpaca daily bars (betas). Live REF applies the −2R latch (and LO where named) and −20R halt as what-if.

## Placebo
H8 with each day's SPY/IWM 1-min paths replaced by those of a random other bench day (sizing still from the real E),
20 draws, seed 1126.

## Metrics (per context × book × config × period)
Avg daily R, red-day % and red days per month (× 21), worst-5 (mean and sum), days ≤ −10R, rolling 20-session floor
(minimum 20-session sum), total R and dR/yr vs REF, hedge gross / cost / net R per year, turnover (rebalances and
traded notional per session), effect by day type (SPY open-to-close: up > +0.5%, down < −0.5%, else quiet), best-day
share, per-setup hedge P&L (each minute's hedge P&L and cost allocated by the setup's signed share E_s / E).

## Pass bar (memo A §3, copied; every item must hold on CHECK and on T2 separately; judged on P4+LO vs REF)
1. Z book: worst-5 days ≥ 30% shallower than REF, and days ≤ −10R down ≥ 40%.
2. Z book: dR/yr ≥ −15R.
3. P book (+0.10R per lot): dR/yr ≥ −15R, and red days up by no more than 2 pp.
4. Z book: worst-5 improvement above the placebo's 90th percentile (20 draws); and hedge-leg gross P&L within ±1
   day-clustered SE of zero (i.e. net hedge P&L within ±1 SE of its costs).
5. Z book: best-day share of the improvement < 50% (improvement = Σ (cfg − REF) over REF days ≤ −10R; share = largest
   single-day delta / that sum). Per-setup hedge P&L reported better / worse (descriptive).
6. Live replay 10-23..11-25 (RAW, P4 lots as traded, LO): worst-5 improves, and no day worse by more than 3R.
If a config passes: DECISION draft in REPORT.md (journal-only `hedge_shadow` in Primary for 20 sessions first);
decisions.json is not edited. Caveat fixed now: on a losing book a hedge can only cut depth; red-day count is set by
the edge (memo A), so red-day % may rise on the Z and P books.
Educational only — not financial advice.
