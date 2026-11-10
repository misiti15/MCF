# GATE2 (queue, owner 2026-11-05) — trade WITH the held side after a confirmed compass reading. Pre-registered 2026-11-06
~23:40 ET before any two-year number. *Educational only — not financial advice.* Research only.

Seed: research/bdi/gate1/NOTES.md — once SPY is ≥ 0.30 % from its open at a checkpoint, it closes on that side 89 / 89 /
97 % (TRAIN / VALID / live), while the rest-of-day direction is near a coin flip. So a setup should use "it will *stay*
on this side", not "it will keep going": buy pullbacks that rely on the side holding. QDAY focus: such a rule trades long
on held-up days and short on held-down days (both directions), and is reported by day type.

**Two configurations (tonight's total N = 4 with SQZ1 and MH1106-P1 → full bar max(1.5, √(2 ln 4)) = 1.67, BAR90 1.50).**
Confirmed reading at the entry bar: lab context `spy_fo` ≥ +0.30 % (held UP → longs) / ≤ −0.30 % (held DOWN → shorts),
entry bars 10:30–14:00, first signal per symbol-day, adv20 ≥ $95M, close ≥ $5, t1s1 (0.25 × daily ATR target and stop,
15:55 flatten), frame outcome re-costed to production costs (as MH1106-P1).
- **GATE2-A VWAP pullback with the held side:** long: stock fromOpen ≥ +0.50 %, 0 ≤ vwapDistPct ≤ +0.20 %, rsi5 ≤ 40.
  Short: mirrored (fromOpen ≤ −0.50 %, −0.20 ≤ vwapDistPct ≤ 0, rsi5 ≥ 60).
- **GATE2-B open-hold pullback:** long: stock fromOpen between 0 and +0.30 % after having been ≥ 0.50 ATR higher
  (dist_hod_atr ≥ 0.50). Short: mirrored (fromOpen between −0.30 % and 0, dist_lod_atr ≥ 0.50).

**Contrast (does the compass add?):** the same stock pattern on bars where |spy_fo| < 0.30 % (side by the spy_fo sign).
Reported as "confirmed minus unconfirmed" avg R.

**Pass (Testing / Live Lab candidate on BAR90):** avg R after costs > 0 on TRAIN (≤ 2026-02-28) and VALID
(2026-03-01..2026-11-04); day-clustered t ≥ 1.50 on all days; positive on up AND down sessions (SPY o-c ±0.25 %);
months positive ≥ 54 %; avg R without the best day > 0 (share reported); confirmed minus unconfirmed > 0. Reported
regardless: QDAY split by day type and by SPY vs its open at 10:00; long and short legs separately. Locked block
2024-11-01..2025-02-28 never read (asserted).
