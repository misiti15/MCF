Educational only — not financial advice

# U5 day-type specialists — working notes (2026-11-18, market hours, research only)

- Pre-registration PLAN.md committed and pushed (321a3c61d) before any scoring.
- Data streamed one session at a time from the public release assets (1min + 1day packs), deleted after use; only trade
  rows were kept. FIT = 168 sessions of the 2-year backtest bars (2025-06-02..2026-01-30); CHECK = 31 Session replay
  sessions of the live window (2026-10-06..2026-11-17). Locked block never read: 1day rows <= 2025-02-28 dropped and
  asserted absent; fit starts 2025-06-02.
- q40 (outcome-blind frequency rule) = 0.2805 (SPY OR30 / SPY ATR14). The quiet cue is a per-day threshold, so the
  processor ran with no OR30 cut and the cut was applied at scoring (identical to applying it in the signal step,
  because it is constant within a day).
- One code smoke test on 2026-11-02 (a CHECK session) printed that day's per-setup averages before scoring (S4 cue
  120 trades +0.08R that day). No parameter was changed afterwards; recorded here for transparency.
- No bug fixes after scoring. No parameter changed after scoring.
- Random control: 3 random universe names per setup trade, same minute/side/R-in-ATR/target-multiple, no 15-position
  cap (the cap is applied to the setups only); its R is therefore an unweighted pool.
- Configurations: 12 scored as registered (4 setups, 4 no-cue versions, 4 random controls) + 8 descriptive slices
  (stop >= 0.25 ATR subsets, 4 setups x cue/no-cue; not used for any verdict) = 20 looks.
- Cost model check: median stop distance came out at ~0.14 ATR for all four (structural stops at the break
  extreme / day low / VWAP). Costs are 0.10-0.18R per trade at that size — larger than any gross edge found.
- Rule-change context: the CHECK window is a bar replay of new setups, so live rules do not act on these trades. The
  Primary day R used in the overlay is the as-traded journal (run 1) and is affected by the ledger changes inside
  10-06..11-17: 10-20 twin-symbol block; 10-22/23 per-setup latch off in Testing 1/2; 10-27 slots 160 -> 77;
  10-28 Primary sizing (~$4k); 10-29 -2R per-setup latch and BAR90; 11-05 ROLL1; 11-11 TEAM-6 lineup; 11-12 LR8
  after-cost R; 11-16 ROT1; 11-17 TSZ1, WB copies, promotion hold.
- Scratch (packs, trades) deleted at the end; the worktree is removed after the push.
