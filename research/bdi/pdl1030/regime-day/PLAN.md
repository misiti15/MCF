# pdl1030 / regime-day: pre-declaration (written 2026-10-30 ~05:40 UTC, before any configuration is scored)

*Educational only — not financial advice.*

Research only. No repo, config/, mcf/, ledger or backlog writes; nothing committed.
Lineage: Failed Prior-Day-Low Break Longs (CWT14-failbrk-pdl-p05 / p05-lowvol / p10 / p10-lowvol). N_prior 121566.

## Family: pre-open day regime chooses the side (long vs flip short) for the whole session
Why notes: gross edge ~0, the loss is SPY beta on down sessions (94-99% of the loss). If a regime known BEFORE the open
predicts the session's direction, the signal can be taken long on "up-regime" days and flipped short (same signal bar,
mirrored exits) on "down-regime" days. That keeps 100% of the signal count (side flips count as exposure).

### Daily SPY features (one value per session, all known before the first possible entry at 09:50)
| id | feature | when known |
|----|---------|-----------|
| GAP | SPY open gap % vs prior close (frame `gap`) | 09:30 open |
| PRNG | SPY prior-day range / SPY atr_d = dist_pdh_atr + dist_pdl_atr at the first bar (constant intraday; checked) | pre-open |
| PCLV | SPY prior-day close location in its prior range, (PC - PDL)/(PDH - PDL); PC = open/(1+gap/100), open = close/(1+fromOpen/100), PDL/PDH from dist_pdl/pdh_atr x atr_d at the first bar | pre-open |
| ATRP | SPY atr_d / PC (daily ATR %, a VIX-like volatility proxy; atr_d is from prior days) | pre-open |
| PRET | SPY prior-day return PC_t / PC_(t-1) - 1 (consecutive loaded sessions only; NaN on the first session after a skipped month: 2024-10-01, 2025-03-03, 2026-07-01 -> no trade those days) | pre-open |
Cut for each feature = the median over TRAIN sessions only (VALID never used to set a cut).
At the cut exactly / missing -> no trade.

### Base book (from earlier rounds, already counted there; re-scored here and counted again)
p05 signals (CWT14 `S6.b3_any`, PD level, side +1, p=0.05, adv20 >= 95M, 09:50-15:00, first per symbol-day),
**S3** exits (stop x3 = 0.75 ATR at the same $ risk; target 0.5R1 and 0.25R1 scale-out prices kept; r in 3R1 units),
**cost5** (skip when the round-trip cost estimate > 5% of R1 = 0.25 ATR; known at entry). ~54 trades/session.
Short leg = same sim with side -1 at the same signal-bar close (mirrored target/stop/scale-out).

## Configurations (17 counted; nothing added after scoring - any addition is disclosed and counted)
| id | rule |
|----|------|
| PAR-P05 | parity: p05 parent exits (swarm15 -0.0677 / -0.0675) |
| PAR-P05S3 | parity: p05 S3 (swarm15 -0.0210 / -0.0173) |
| REF-K3 | reference: S3 + cost5 + intraday SPY-VWAP flip (combo K3, +0.0062 / -0.0003) |
| R1A / R1B | S3 + cost5; GAP > cut -> long, < cut -> short (A) / reversed (B) |
| R2A / R2B | same with PRNG |
| R3A / R3B | same with PCLV |
| R4A / R4B | same with ATRP |
| R5A / R5B | same with PRET |
| G1 | gate: S3 + cost5, long only on the long-side half of the TRAIN-best R-row (by TRAIN avg R), skip the other half |
| C1 | TRAIN-best R-row, but take the trade only when its side agrees with the intraday SPY-VWAP side (SPY vwapDist > 0 long / < 0 short) at the signal-bar close; skip otherwise |
| C2 | TRAIN-best R-row with cost10 instead of cost5 (more exposure, ~114/sess) |
| C3 | TRAIN-best R-row on parent exits, no cost floor (full 153/sess exposure) |
"TRAIN-best" is picked on TRAIN avg R only, before looking at VALID for that row.

## Harness
Same as pdl1030/combo/build.py (CWT14 kernel, top5_1028 `sim`, costs 1c + 1 bp per side x time-of-day multiplier,
+2c stop exits, x3 extended tier, flatten 15:55). TRAIN <= 2025-12 (2024-10, 2025-03..12); VALID 2026-01..03 + 2026-07..09-15.
HOLD months (2026-04..06, 2026-09-16..10-07) and the locked block 2024-11..2025-02 are never loaded (asserted).
Parity first: PAR rows must match swarm15 within 0.005R, else stop.

## Bar (rule 22, BAR90)
N = 121566 + 3 x 17 = 121617 -> t_TV >= 0.9 x sqrt(2 ln N) = 4.355. Walk-forward >= 54% of months positive, avg R > 0 on
TRAIN and on VALID, beats p05 (-0.0677 / -0.0675) on both, exposure >= 76.6/sess or >= 25/sess (flip legs count).
Reported per row: train/valid avg R, day-clustered t, trades/session, wf%, up/down-day R, avg R w/o best day + best-day share.
