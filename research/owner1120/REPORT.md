Educational only — not financial advice

# Owner asks 11-19 evening: inverse handling, breakeven, GEN trail — report

**Owner summary (5 lines, with reply codes)**
1. **INV-H1 yes.** Every setup stops shorting inverse and long-vol funds (SQQQ, SPXS, SOXS, VXX type), because a short there is really long the market. No per-setup exceptions.
   - Live: 224 trades, -78.8R, in 51 setups; -55.9R without 11-19.
   - Per setup x account: 50 better (+99.3R), 24 worse (-20.6R, worst -2.65R). Families: 19 better, 4 worse.
   - Runs as a journal-only shadow from 11-20. Then backlog, then your decision, then live outside 09:30-16:00 ET. Primary changes only in the Friday epoch window.
2. **INV-LONGS yes (keep) and INV-BUY no.**
   - Inverse longs stay in play. We cannot show we can afford to drop them: the live +20.5R is all one day (11-02, -5.2R without it), and the lab says they lose. The shadow watches them.
   - "Buy the inverse instead of shorting the underlying" lost -20.6R, and -103R when every underlying short was doubled through the inverse. The engine cannot place that kind of order today.
3. **BE-NO yes.** Stop-to-entry was tested on 18,144 configs (9,072 independent), 2 years, costs in. 0 pass. All 216 whole-position rules lose book-wide, and the best 10% of days take 30-80% of each rule's loss.
4. **GT-KEEP yes.** A trail, 1R target or chandelier on GEN hold setups loses on both halves.
   - Check half: -0.049R/trade, t -2.61; 4 setups better, 21 worse.
   - Holdtr: neutral. Backlog parked.
5. **GT-BE optional (research only).** The one breakeven pocket not yet tested: stop to entry at +0.3R / +0.5R on GEN hold setups, 2 configs in the generator lab. The prior is strongly against it.

**Conflicts named**
- **Owner condition:** you only wanted inverses ruled out if we could afford it. Inverse shorts can be ruled out because blocking them gains R. Inverse longs are kept because their evidence is undetermined.
- **Primary:** Primary's two L3 copies change only in the Friday epoch window.
- **Backlog / no market-hours change:** respected.
- **Playing time:** three low-rep L3 WB copies lose most of their trades under INV-H1 (T2 18 of 24, Live Lab 2 of 2, Testing F 3 of 3). They need rotation, never switching off.
- **One big day:** L3's +30.4R is 64% from 11-19 (U9-ETB's first day). Primary L3-fromopen keeps its `1 day` tag at 70%.
- **Targeted remedy:** INV-H1 passes. The CWT14-heavy LONG_BLOCK list and the 7-setup SHORT_KEEP list are not proposed: they were picked using check data and are close to tailored.
- **Held-out data:** the live "check" window was not held out, so only the forward shadow decides INV-H1.

**Inverse shadow** (ready, journal-only, upheld by the Skeptic)
- I fixed it before any forward session:
  - Added the 19 missing inverse funds, each with its underlying. TTT moved to neutral.
  - Added a name rule (`inv_name`) on data/universe.csv names, so new inverse funds are caught when the universe is rebuilt.
  - `--score` now counts the pass bar on the default columns only. SHORT_KEEP and LONG_BLOCK are printed as separate exception columns.
  - RULE.md section 5 records the amendment. The frozen date stays 2026-11-20.
- Commands, run after each close:
  - `python research/owner1120/inverse/shadow.py --since 2026-11-20`
  - `python research/owner1120/inverse/shadow.py --score`
- Pass bar: at least 10 sessions, blocked shorts net below zero, at least 60% of affected setup x accounts not worse, none worse by more than 3R, kept longs net at or above zero.
- Wiring it into the nightly forward logs is left to the main session:
  - Run it after the journals are pushed. It is read-only: it fetches and reads each account's journal.db from the data branches.
  - Commit `research/owner1120/inverse/forward.csv` with the nightly brief.
  - Report nothing until the 10-session bar is decided.

**Committed in 8da5c52bc**
- `research/owner1120/` (inverse, breakeven, gentrail stages, with my shadow.py and RULE.md fixes)
- `research/owner_inbox/2026-11-20.md`: 6 DECISION blocks plus 1 FYI
- `docs/live/decisions.json`: INV-H1, INV-LONGS, INV-BUY, BE-NO, GT-KEEP, GT-BE, all open
- `research/backlog.jsonl`:
  - gb-1119-gen-hold-trail set to parked, configs_tried 14
  - new: inv-1120-short-skip-inverse-guard (idea, 12 configs)
  - new: inv-1120-inverse-buy-substitution (parked, 2)
  - new: be-1120-breakeven-grid-finding (parked, 18,144)
  - new: gb-1120-gen-hold-early-be (idea)

**REPORT.md content for the main session to save** (first line "Educational only — not financial advice"):
- **Header:** the 5-line owner summary above, then "Nothing here changes live trading, config or setups. Primary only in a Friday epoch window."
- **Checklist:** costs in (LR8 / production costs; borrow is the ETB availability; inverse-fund decay acts only at the daily reset). Locked block asserted absent in all three stages. Configs counted: 12 / 18,144 (9,072 independent) / 14. Fit/check per stage, and the inverse live check was not held out. WB2 paired. Avg R w/o best day given. Rule changes inside the live window: 10-13/14 stacking, 10-16/17 T2 scale-out, 10-23 latch, 10-26 GX2, 10-28 Primary sizing, 10-29 -2R latch, 10-30 cost filter, 11-05 ROLL1, 11-12 LR8 and REPV, 11-16 ROT1, 11-17 TSZ1/SPYEXIT/WB4, 11-18 GY-BENCH/SRCV1, 11-19 C3 Epoch 1 including U9-ETB. From 11-20 on: rounding fix, ultimate_1119 setups, FOOTRACE-EXIT.
- **Item 1:**
  - INV-H1 evidence: Skeptic re-score -78.8R; t -2.37 on 27 days; no single-day removal flips the sign; halves -50.3R / -28.4R; 2-year borrow proxy +79.6R (fit +13.3R, check +66.3R).
  - Weaknesses: the live check was not held out; the lab mechanism is unconfirmed (lab gain partly trims losing short setups); about +46R if blocked slots are refilled with the setup's average stock short; SQQQ and SOXS are 71% of the loss.
  - Per setup: largest worsenings heat_fade_short-FD Graveyard -2.65R, NM-RWR3 Live Lab -2.11R, GEN-261022-04 -1.73R. Worse families NS2 -1.0R, RW5 -0.9R, NS3V1 -0.8R, RW3S -0.4R. Largest gains L3 +30.4R, exhaustion_short +7.7R, CWT14 +7.6R, GEN +5.3R, RW2 +5.1R.
  - INV-LONGS, INV-BUY and the leveraged-long no-change, with the evidence above. H2S and CHOSEN are in-sample and not evidence (Skeptic F3).
  - The shadow section, as above.
- **Item 2:** grid 6 triggers x 3 stop levels x 4 activations x 3 conditions x 2 sizes, over 42 scopes. 1,165,484 lab trades. Engine check: L16 re-scores at -0.0070R. Results range -0.0001 to -0.037R/trade. The Skeptic's 250-symbol re-score and same-bar tie check agree. The live replay is a red-day effect (lab vs live correlation -0.58). The inverse/vol pocket (t 3.58, -0.0135R live) gets a re-look in about 6 months.
- **Item 3:** 47 specs, 107,892 trades. Hold fails on both halves. Holdtr is neutral (one day is 75% of its check gain). The fit-half hold baseline falls from +0.228R to +0.039R without 2025-04-09. Skeptic caveat: the specs were screened on the same panel. GT-BE closes the open gap the Skeptic flagged.

Main paths:
- /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rules1119/research/owner1120/inverse/shadow.py
- /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rules1119/research/owner1120/inverse/RULE.md
- /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rules1119/research/owner_inbox/2026-11-20.md
- /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rules1119/docs/live/decisions.json
- /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rules1119/research/backlog.jsonl
- Pre-fix copy of shadow.py: /tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/shadow_orig.py

sha: 8da5c52bc
