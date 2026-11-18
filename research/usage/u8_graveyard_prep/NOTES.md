Educational only — not financial advice

# U8 notes (process log, 2026-11-18, market hours — research only)

1. ~13:05 ET: journals (run_id 1) of the ten state branches copied to scratch; Graveyard residents = config/account_graveyard.yaml
   `strategies` minus the 20 GY-BENCH guests = 34. Headline per-setup records looked at (descriptive only).
2. ~13:10 ET: PLAN.md written (menu, split, ranking score, verdict rule) before any tune was scored.
3. Entry features streamed from bars-2026-10/11 1-min packs one session at a time (31 sessions, each pack deleted after
   use); prior closes from the 11-17 1day pack, days strictly before each session only. Locked block never touched.
4. code/analyze.py: ranking + FIT tune choice + CHECK verdicts in one pass; output in score_out.txt, u8_ranking.csv,
   u8_tunes.csv. 1,100 configurations counted (bar 3.74).

Deviations / corrections, stated openly:
- PLAN.md says 13 CWT12/CWT14 residents; the count is 11 (the other CWT names in the YAML are CWT09/CWT13 or arena guests).
  No effect on the procedure.
- RW6-ns2-up3-short-FD and ST4-emadn-long-am-t1s05-FD are `enabled: false` in the Graveyard since 11-13 (moved to Testing C /
  Testing B, ledger 2026-11-13-gy-rw6-st4-arena). Noticed after scoring. RW6 stayed in the pre-registered top 10 (rank 3);
  its verdict is reported but informational. The top 10 was not re-drawn after seeing results.
- RW3S (rank 7) had no FIT trades, so no tune could be chosen; per PLAN the next eligible setup (MF1, rank 11) was tuned.
- The correlation points use |rho|, so LIQ's negative correlation (-0.53) cost it a point; left as pre-registered.
- Random-subset control for gate+exit tunes compares with parent trades without the exit (lenient); no tune was near 95%
  anyway except MF1/MF3 (pure / mostly gate tunes, 92%).

Guardrails kept: no config/code/runtime change, no PR/merge, no new CWT12/CWT14 variant, no hedge/sizing/switch work, no
replay or 2-year pass, L3-gap-slope-fromopen-FD untouched. Scratch data deleted at the end.
