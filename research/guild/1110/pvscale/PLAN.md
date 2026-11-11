# PVSCALE — partial volatility scaling for the compass M1 line and the size band (Builder, frozen 2026-11-10 ~18:20 ET, before any score)

*Educational only — not financial advice.* Lead lead-20261110-1700-1 (day-3 item 2), Skeptic skeptic-20261110-1651-2. ONE
counted look (third in the COMPCAL lineage, second in SZBAND's). Display research only.
- Factor for prior day j at mark T: f_j = (rg_today(T) / rg_j(T))^alpha, rg = SPY (high - low) of bars that START before T,
  in % of the open; prior days with rg_j = 0 dropped. SPY 1-min SIP cache, full sessions, locked block absent.
- **M1-alpha (close side):** as COMPCAL M1 (10-min marks 10:00..15:50) with each prior remaining move x f_j. Fit alpha on
  TRAIN only by Brier over the grid {0, 0.1, ..., 1}.
- **SIZE-alpha (band):** Scout's SZBAND definition (marks 09:45..15:15 every 15 min; |move| over 30 / 60 / 90 min and to
  the close; prior 60 sessions; median and 80th pct) with prior |moves| x f_j. Fit alpha on TRAIN only by the sum of
  pinball losses at tau 0.5 and 0.8 over all horizons.
- Periods: TRAIN <= 2025-09-30; VALID 2025-10-01..2026-10-07; FWD 2026-10-08..2026-11-09 (sanity only, never used to pick).
- **Scored once on VALID** vs alpha = 0 (= today's M1 / Scout's band): Brier (M1) / pinball (size), day-clustered t of the
  per-day difference; calibration by today's vol tercile (TRAIN terciles of rg at T); coverage in80 / in50 for size.
- **Adoption rule (fixed):** the card uses alpha* if VALID improves with day-t <= -1.0 AND FWD is not worse by more than one
  day-clustered se; otherwise alpha = 0.
