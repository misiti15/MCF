# OBS-HALTFLIP — Graveyard's -2R per-setup latch sits on a two-stop knife edge (Observer, 2026-11-12 ~01:45 ET)

Context: Builder's FWDCAL lever 2 (builder-20261112-0120-2): with quotes in, 37% of live-only misses are halt timing,
and 182 of 192 replay trades taken after live halted are in Graveyard. Live journal only, 11-04..11-11 (6 sessions), 0 configs.
Repro: `python haltflip.py <graveyard journal.db>` -> haltflip_out.txt.

- Two different halts: Graveyard = per-setup latch 'setup daily loss limit' (max_setup_daily_loss_r 2.0, raw realized R,
  latched on touch); Gen = account 'halted' at max_daily_loss_r (120 until 11-11; 300 from 11-12, c64d75df0).
  So Gen's account halt (11-04 / 11-05 live) will very likely not trip in the fresh 11-12..11-13 window.
- Graveyard: 180 setup-days (33 setups). 89 latched (49%), causing 3,341 skipped signals.
- The crossing is almost always two full stop-outs: cum R before the crossing trade median -1.12, crossing trade -1.05.
  25 of 89 latches landed within 0.10R of -2 (17 within 0.05R); 52 (58%) within 0.25R. Zero setup-days ended with a
  minimum in (-2, -1.75]: stops slip adversely, so two losers almost always reach -2.0.
- So a replay whose stop fills are a few hundredths less adverse (FWDCAL Graveyard matched gap +0.010R, optimistic)
  misses the latch on those setup-days and keeps trading: that is the direction of Builder's 182 Graveyard replay-only trades.
Suggestions: (1) score latch agreement per setup-day as its own audit line; (2) to isolate the other causes, run one
diagnostic with live's latch minute fed in as given; (3) owner-level angle, not a change request: at 2.0 the latch is in
practice 'stop after two full losers'. A count rule (2 stop-outs) would behave almost the same and replay deterministically.
Rule-change context: Graveyard latch unchanged in the window; account halts in the testing areas / Gen rose to 300R from 11-12.
Educational only — not financial advice.
