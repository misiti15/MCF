# LIMEX — limit entry at the signal close vs next-bar market entry, on the cost-killed setups (Builder, frozen 2026-11-10 ~22:30 ET, before any score)

*Educational only — not financial advice.* Lead lead-20261110-2100-3; pool = Observer's 14 cost-killed setups
(research/obs-stopcost/stopcost_out.txt [D]: gross > 0 live, lab net < 0) that have 2-year lab lists (bt_lab1104).
- **Baseline (B):** market entry at the open of the first 1-min bar after the signal bar close (lab tod), production
  entry cost (1c + 1bp) x tod multiplier; stop / target at the live geometry distances from the fill (R = 0.25 x ATR_d);
  walked on 1-min bars, stop-first, gap-through fills at the open, flat 15:55; exit costs as bt_all.
- **Limit (L_N):** limit at the signal bar close e. Filled only if a 1-min bar within the first N minutes after the signal
  trades THROUGH e by >= 1 cent (long: low <= e - 0.01; short: high >= e + 0.01); fill at e; entry cost 0.5 x (1c + 1bp),
  no tod multiplier (passive). Stop checked inside the fill bar (conservative); same exits. Not filled = no trade (0R).
- **Configs: N = 2 / 5 / 10 minutes = 3.** Family = 60 backlog lines on limit / execution entries (1,957 configs summed)
  + 3 = **N 1,960 → BAR90 3.50.**
- **Score:** per day, sum R(L_N) - sum R(B) over the pool; day-clustered t; TRAIN (<= 2025-09-30) / VALID; GROSS first
  (cost-free delta reported); per setup better / worse; fill share; **adverse selection**: B's R on the filled vs the
  missed signals; what the missed trades would have earned under B.
- **Pass:** excess t >= 3.50, TRAIN and VALID > 0, w/o best day > 0, more setups better than worse.
