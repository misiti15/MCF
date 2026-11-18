Educational only — not financial advice

# U6 mechanism setups — working notes (2026-11-18, market hours, research only)

- PLAN.md committed and pushed (bef78a169) before any outcome was scored.
- Data streamed one session at a time from the public release assets (1min + 1day packs) and deleted after use; only
  trade rows were kept in scratch (deleted at the end). FIT = 168 sessions of 2-year backtest bars
  (2025-06-02..2026-01-30); CHECK = 31 live-session replay sessions (2026-10-06..2026-11-17). 199 of 199 sessions
  processed, 0 errors / skips. Locked block never read: 1day rows <= 2025-02-28 dropped and asserted absent.
- Earnings blackout (CHECK only): union of the 29 mcf-data earnings/<day>.json files (2,917 symbols), +-4 business days
  (np.busday_count, no holiday calendar). 10-06/10-07 have no file of their own; the union still covers them through
  later files' dates. FIT has no earnings data: FIT trades include earnings days (as PLAN says).
- Smoke test before scoring on 2025-09-15 (FIT) and 2026-11-05 (CHECK): printed trade COUNTS per setup/side and the
  M4 symbols only (no R). No parameter changed afterwards.
- Cost model detail: PLAN text puts the 3.8x entry multiplier "up to and incl. the 09:35 close"; mcf/research/gates.py
  edges give 2.1x at exactly 09:35. The code follows PLAN (more conservative, affects M1 bar-0 entries only). M1's
  GROSS avg R is +0.002 (FIT) / -0.049 (CHECK), so the multiplier does not decide its verdict.
- Category tags in the capture table: lev/inv ETF = symbol in the M4 pool that day (setup or random draws) or in a
  fixed list of the inverse/vol tickers seen in moves.csv; opening drive = decision <= 09:45; gap-go = |gap| >= 2% in
  the move's direction; afternoon = decision >= 13:00; tagged in that order. Gap-go non-earnings only (tradable set
  already excludes blackout).
- Configurations: 19 looks as registered (5 setups, 5 random controls, 9 side splits). No extra slices were scored.
  Running total for the U6 lineage: 19.
- No bug fixes after scoring. No parameter changed after scoring.
- Rule-change context: CHECK is a bar replay of new setups, so live rules do not act on these trades. Live capture
  (15.0%) comes from the as-traded journals, which ran under the ledger changes inside 10-29..11-17: 10-29 -2R
  per-setup latch and BAR90; 11-05 ROLL1; 11-11 TEAM-6 lineup; 11-12 LR8 after-cost R, Testing D/E/F opened;
  11-16 ROT1 rotation; 11-17 TSZ1 half-size testing, 15 WB copies, promotion hold.
