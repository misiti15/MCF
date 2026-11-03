Educational only — not financial advice

# ex30 / gen2 — a new ground-up setup generator (pre-declaration, written 2026-11-03 before any configuration was scored)

Owner 2026-11-03: two new EXPLORATORY paper accounts, 30 new unconventional setups; this lane delivers 5, made by a
new generator. Different from the paused random-combination Setup Generator (`mcf/research/generator`: random draws of
indicator thresholds + time bucket + market filter, screened on mean R). gen2 is a **grammar + beam search with a
regime-maximin fitness**: it only rewards rules that make money on SPY up, down AND quiet days at the same time — the
live book's known hole is that it is a market-direction bet with no quiet-day edge (night1102/regime).

## Grammar (every primitive is known at the bar close; only lab-frame columns + opt-in context spy_fo / breadth)

rule = 1 TRIGGER (an event at this bar) + 0..2 CONTEXTS (a state) + side {long, short} + geometry {t1s1, t05s1, t1s05}
+ window {W1 10:00-11:30, W2 11:30-14:00, W3 10:00-15:00} (bar close). Max 3 conditions. ADV floor 95M (adv20),
first qualifying bar per symbol-day, R = 0.25 x daily ATR, flat 15:55 (lab outcome columns).
Notation: o = close/(1+fromOpen/100) (today's open), fo_atr = (close-o)/atr_d, vwap_atr = (close-vwap)/atr_d with
vwap = close/(1+vwapDistPct/100), rng = (high-low)/atr_d, lag = previous bar of the same symbol-day (windows start at
10:00, so every lag read is a >= 09:50 bar, identical live and offline).

**Triggers (19):** vwup (vwapDistPct>0, lag<=0), vwdn (mirror), hod (dist_hod_atr<=0.01), lod (dist_lod_atr<=0.01),
volsurge (volumeSurge>=2.0), bulldiv (bull_div=1), beardiv (bear_div=1), uwick (upper_wick>=0.6 & rng>=0.10),
lwick (lower_wick>=0.6 & rng>=0.10), rsi5up (rsi5>=30, lag<30), rsi5dn (rsi5<=70, lag>70), macdup (macdPct>0, lag<=0),
macddn (mirror), flowup (flow3>=0.3 & flow9prev<=-0.1), flowdn (flow3<=-0.3 & flow9prev>=0.1), wide (rng>=0.18),
inside (high<=lag high & low>=lag low), round (dist_round_atr<=0.02), dry (volumeRatio<=0.3).
(`dry` is the "nothing happens" trigger.)

**Contexts (35):** fo_up/fo_dn (fo_atr >= 0.5 / <= -0.5), fo_flat (|fo_atr|<=0.2); gap_up/gap_dn (gap >=1 / <=-1),
gap_flat (|gap|<=0.3); pp_hi/pp_lo (pricePosition >=0.85 / <=0.15); d20_hi/d20_lo (sma20_dist_pct >=0.8 / <=-0.8);
slope_up/slope_dn (sma20_slope_pct >=0.3 / <=-0.3); abv_pdh (dist_pdh_atr<0), blw_pdl (dist_pdl_atr<0), inside_pd
(both >0); rsi_hi/rsi_lo (rsi >=70 / <=30); vr_lo (volumeRatio<=0.6), vs_hi (volumeSurge>=1.5); heat_hi/heat_lo
(heat >=25 / <=-25); bp_hi/bp_lo (buyPressure >=0.3 / <=-0.3); vol_hi/vol_lo (atr_d/close >=0.045 / <=0.017);
vw_up/vw_dn (vwap_atr >=0.5 / <=-0.5); spy_up/spy_dn (spy_fo >=0.3 / <=-0.3), spy_flat (|spy_fo|<=0.15);
br_hi/br_lo (breadth >=0.70 / <=0.30), br_mid (0.42..0.58); rs_up/rs_dn (fromOpen - spy_fo >= 1.5 / <= -1.5).
Thresholds were set from the 2025-06 (TRAIN) feature distribution only (5/95% tails; no outcome column read).

**Excluded up front (near-duplicates of live setups / exhausted families):** (vwup, short) NS3/NS4, (vwup, long)
vwap_reclaim, (rsi5up, long) NS1, (rsi5up, short) ST3, (flowdn, short) MF1-5, (hod, short) exhaustion / heat_fade_short,
(lod, long) heat_fade_long, (volsurge, *) ST6/ST8 vol spikes; PDL/PDH sweep-reclaim (blw_pdl + long, abv_pdh + short:
CWT14 / pdl1030*); gap-down bounce shorts (gap_dn + short + an up trigger: RW1/3/5/7). **Soft penalty -0.02** when the
(trigger, side) is the core token of a live GEN setup: (vwdn, long), (lod, short), (bulldiv, short), (beardiv, short),
(uwick, *), (lwick, long).

## Search (TRAIN only) and fitness

- Stage A: every trigger alone and trigger + 1 context, x side x geom x window (excluded pairs skipped, still counted
  if evaluated). Stage B (beam): the 300 best stage-A rules with TRAIN trades/session >= 1.5 (ranked by fitness without
  the frequency cap) each get every other context added. Every rule evaluated is counted; the total is reported.
- **Fitness F = min(avg R on SPY up days, down days, quiet days) on TRAIN - 0.01 x conditions - dup penalty**, with
  >= 30 trades in each day type and 1.5-25 TRAIN trades/session (else not eligible). Day type = SPY open-to-close
  (SIP 1-minute cache), up >= +0.25%, down <= -0.25%, else quiet.
- Shortlist: walk the eligible rules by F; keep one if its TRAIN trade set (symbol-days) has Jaccard < 0.30 with every
  rule already kept; stop at 30. **The 5 delivered = the first 5 shortlisted rules with distinct triggers (chosen on
  TRAIN only).** VALID is a check, not a selector: it is scored for all 30 shortlisted (information: does the
  generator's TRAIN fitness transfer?) but cannot change the 5.

## Data, splits, costs, controls (night1102/simple + ex30 harness)

- history2y open frames + context (`lib.load_month(..., context=True)`). TRAIN = 2024-10, 2025-03..2025-12; VALID =
  2026-01..03, 2026-07-01..09-15. 2026-04..06 and 2026-09-16.. not scored. **Locked block 2024-11-01..2025-02-28 never
  loaded** (asserted).
- Production costs: `gates.prod_r` (1c + 1 bps per side, +2c on stops, time-of-day entry multiplier) on the first
  qualifying bar per symbol-day (= `gates.lab_trades`).
- Random control: day-matched (trade R minus the mean production R of every eligible bar of the same side / geom /
  window / ADV floor that date).
- Light lane gate: avg R >= -0.02 on TRAIN and VALID, 1.5-25 trades/session (TRAIN+VALID), mask parity module vs
  harness on 2026-09 (modules = numpy `gen2_lib.py`, harness = independent pandas implementation in `gen.py`). No BAR90.
  A delivered setup failing the gate is still listed, gate_pass = false. Also reported: avg R without the best session
  and its share, day-clustered t, R by up / down / quiet day, configurations evaluated.
- Multiple testing caveat stated now: ~20k rules -> the best TRAIN rule is selected from noise of order
  sqrt(2 ln 20000) ~ 4.5 standard errors; the VALID check is the only honest read.
