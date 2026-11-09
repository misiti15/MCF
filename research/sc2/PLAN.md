# SC2 — cross-asset driver -> equity laggard catch-up (Scout plan, FROZEN 2026-11-09 09:40 ET, before any score)

*Educational only — not financial advice. Pre-registration; nothing has been scored. Builder scores it after 16:00 ET
(Lead decision lead-20261109-0900-2, order GATE2 -> Observer 09:50 -> SC2 -> C3FR).*

## Hypothesis
Commodity / crypto tapes move first and the linked equities follow with a lag (slow information diffusion across
asset classes). A follower that has not yet moved with a sharp driver move catches up in the next 30-60 minutes. The
driver is not the equity index, so the signal should not depend on the day type (up / quiet / down).

## Groups (lab symbols only; fixed now)
| group | driver | followers |
|---|---|---|
| OIL | USO | XLE XOP XOM CVX COP OXY DVN EOG APA FANG HAL SLB EQT AR RRC |
| GOLD | GLD | GDX GDXJ NEM AEM GFI KGC WPM PAAS AU FNV AG CDE RGLD |
| CRYPTO | IBIT | MSTR COIN MARA RIOT CLSK HUT CIFR WULF HOOD |

Amendments vs IDEAS.md (made now, before any data): one driver per group (UCO is 2x USO, SLV dropped as a second gold
driver); "driver on the same side of its VWAP" replaced by "driver close on the same side of its session open" (no
volume dependency).

## Data
- 1-minute SIP cache `data/cache_hist/1Min/<SYM>.parquet` -> 5-minute RTH bars, the same `bars()` as research/gate2/gate2.py.
  **Locked block 2024-11-01..2025-02-28 filtered at read and asserted absent** (bars and daily table).
- Daily: `research/history2y/lib.daily()` (locked removed): ATR14 (prior days), adv20; earnings blackout via
  `mcf.research.generator.data._blackout` (follower skipped inside +-4 days); 60-day beta to SPY (prior days) for the hedge.
- Rolling windows that would span the locked gap (> 5 calendar days between consecutive sessions) restart (NaN).

## Rule (5-minute bars, b = bar index, close c[b])
- Driver 15-min return `rD = cD[b]/cD[b-3] - 1`; `sigma` = stdev of the driver's 15-min returns at bar closes 10:00..15:00
  over the prior 20 sessions (>= 15 sessions needed); `z = rD / sigma`.
- **Driver event:** bar close 10:00..15:00 where |z| >= Z and |z| < Z on the previous bar (a fresh crossing), and the
  driver's close is on the side `s = sign(rD)` of its session open.
- **Follower eligible:** adv20 >= $60M, ATR known, not in blackout; beta to driver (5-min returns 09:40..16:00, prior 20
  sessions, >= 15 sessions) >= 0.5; follower 15-min return `rF` with `s * rF < L * beta * |rD|` (laggard); no open SC2
  trade in that follower.
- **Entry** next bar open, side s. **Stop** 0.25 x ATR_d from entry (R = 0.25 ATR_d); **target** +1R; **time exit** at the
  close of bar ib + H/5 or 15:55, whichever first. Stop first inside a bar; a bar opening through the stop fills at its open.
- **Costs:** production as gate2 `trade()`: (1c + 1bp) x tod multiplier + 4.4bp spread x tod multiplier on entry, 1c + 1bp
  on exit, + 2c extra on stops.

## Grid (12 configs, all reported)
Z {1.5, 2.0, 2.5} x L {0.3, 0.5} x H {30, 60}. **Lineage N = 12** (new family): full bar max(1.5, sqrt(2 ln 12)) = 2.23,
**BAR90 = 2.01**.

## Controls and reports (no extra configs)
- **C1 same-minute random follower (Lead standard):** for each trade, a random lab name the same day (adv20 >= $60M, not
  in any SC2 group, not in blackout, not SPY/QQQ/IWM/DIA), same side, same entry bar, same exit rules. Excess = r - r_C1.
- **C2 same follower, random event-free bar** (bar close 10:00..15:00 on the same day with |z| < 1), same side. Excess r - r_C2.
- **Hedged (report only):** r_hedged = r - beta_SPY x s x (SPY move over the same holding) / R x entry price, SPY costs added.
- Per group (OIL / GOLD / CRYPTO), per side, per day type (SPY o-c beyond +-0.25% = up / down, else quiet), TRAIN
  (<= 2025-09-30) / VALID (after) / live window (>= 2026-10-06), walk-forward share of positive months, avg R without the
  best day and its share, trades per session.
- Slice (report only): OIL events at the 10:35..11:00 bar closes on Wednesdays (EIA report 10:30 ET).

## Pass (Testing, BAR90) — all required
day-clustered t >= 2.01 **and** C1-excess t >= 2.01; TRAIN > 0 and VALID > 0; up-day and down-day avg R > 0; walk-forward
positive months >= 54%; avg R w/o best day > 0 (flag best-day share >= 50%). A pass is scored once on the locked block
only by the Lead's process later. Trades per session reported (expect < 1: a pass would need an owner exception or be
pooled with another setup).
