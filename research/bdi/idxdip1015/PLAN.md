# Index open-dip bounce (owner request 2026-10-15) — pre-declared plan

*Educational only — not financial advice.* Written before any grid result was computed.

## Prior look (counted in the lineage)
Quick scan 2026-10-15 (126 configs, fixed clock entry/exit, 1 bp cost, no stop): after SPY/QQQ fall from the open by
09:45-09:55, a 09:55 buy tended to bounce (best t ~2.0, n 7-10). The owner picked four variants from it:
V1 QQQ down >= 1% by 09:55; V2 SPY down >= 0.75% by 09:45; V3 SPY down >= 0.75% by 09:55; V5 SPY down >= 0.5% by 09:45.
The variants were chosen after seeing that scan, so the 126 configurations count in the lineage (N_lineage = 126 + this grid).

## Data and samples
SIP 1-minute bars, data/cache_hist/1Min (2024-09-16 .. 2026-10-07). SPUU downloaded 2026-10-15 with the history2y
downloader (`scripts/fetch_spuu.py`).
* **Locked block 2024-11-01 .. 2025-02-28: excluded entirely** (never loaded into results).
* **DEV (selection)**: every other session except the two older holdouts below.
* **Older holdouts** (rule 2; not clean, many lineages have looked): Apr 1 – Jun 30 2026 and Sep 16 – Oct 7 2026 (data end).
  Scored once, for the chosen finalists only, after selection.
* Halves inside DEV for stability: H1 < 2025-09-01 <= H2.

## Definitions (fixed)
* Dip: index running low since the 09:30 open <= open x (1 - dip%) on a bar that has closed by the variant's time.
* Trigger window: index bar closing 09:50 .. 10:05 ET, after the dip; first trigger only; one trade per instrument-day.
* Entry: market, next bar open of the traded symbol (engine `simulate`, conservative fills).
* Stop: traded symbol's running low - 0.10 x (traded open - traded running low). Not varied.
* Costs: config/default.yaml (1 bp + 1c/share per side, +2c on stops); SPUU (extended tier, ADV ~$3M) at 3c/share.
* Sizing: risk-based on the traded symbol's own stop distance (R is per trade; leveraged ETFs get proportionally fewer
  dollars, so R is comparable across instruments).
* Backstop flatten 15:55 for every rule.

## Grid (every configuration counted)
| dimension | values | n |
|---|---|---|
| variant (signal) | V1 QQQ 1.0%/09:55, V2 SPY 0.75%/09:45, V3 SPY 0.75%/09:55, V5 SPY 0.5%/09:45 | 4 |
| trigger | recovery 5% / 10% / 15% / 20% of the drop off the low; hi3 (close > prior 3-bar high); vwap (close > session VWAP) | 6 |
| exit | T1030 (fixed 10:30 exit, stop in place; baseline); R50 / R75 / R100 (target = low + 50% / 75% / 100% of the drop); VWAP (target = VWAP at trigger); TRAIL (no target; trail 1R behind the best once +1R); HOLD (stop only, to 15:55) | 7 |
| instrument | SPY variants: SPY, SSO, SPUU, SPXL, UPRO; QQQ variant: QQQ, QLD, TQQQ | 5 / 3 |

Total N = (3 x 5 + 1 x 3) x 6 x 7 = **756** configurations. **Selection uses the index-ETF rows only**
(4 x 6 x 7 = 168); the leveraged rows are reported for every configuration and judged as consistency checks (they trade
the same signal, so they are not independent tests), but they are counted in N.

## Bars
* Day-clustered t (one trade per instrument-day, so per-trade t) must reach max(1.5, sqrt(2 ln N)):
  N = 756 -> 3.64; lineage N = 882 -> 3.68. (Index-only selection N = 168 -> 3.20, reported for information.)
* Rule 6 controls, per configuration and instrument: (a) same dip days, entry at a random bar closing 09:50-10:05
  (20 seeded draws, same exit geometry) — tests the trigger; (b) all sessions, random bar closing 09:50-10:05, same
  geometry (drop floor 0.05% of the open) — tests the dip condition. Compared in bps and R.
* Concentration: mean without the best day. Halves H1/H2 both reported.

## Choice rule (for the Testing proposal, pre-declared)
Per variant, rank index-ETF rows on DEV by t of R with n >= 8; choose the trigger x exit whose neighbours (adjacent
recovery fraction, adjacent retrace) are also positive (plateau). If no single choice is clearly best, propose 2 exits.
Testing is a forward paper test (rule 20 account); passing the research bar is NOT required for Testing, but whether it
was met is stated.
