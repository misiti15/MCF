Educational only — not financial advice
# TAPE-1126: consultant B's tape-steering rules (S1, S2, S3+H1) and hedge longs (H1, H2) on the bench (research only; nothing changed)
Pre-registered: PREREG.md (sha256 c6e7b3f8…346d, 18:32 UTC, before any score). The owner's 11-26 request lifts the rule-26 guard for this work. **Configs: 7** (S1, S2, S3+H1 SPY/IWM, H1 SPY/IWM, H2); cumulative N ≈ 2,273 + REGSTEER-1's 7 → **≈ 2,287**. Engine E4 = squeeze_1125 minute book (P4 lineup, 30-lot cap, −2R latch, −20R halt), HEDGE-B's bench10 lots (LIVE-L on shorts), 4 contexts (BASE / LO / L3-OUT / LO+L3-OUT). Base CHECK −3.03 R/day = primshorts. Splits: CHECK 276, T2 415, FIT 170 sessions; the locked block is never read (asserted in every script). Controls: 20 random brakes (same share per setup × split), constant cut, placebos. B's thresholds used as written.
**Verdict: 0 of 7 pass.** Nothing reaches t 2 against its random control on both splits, and no hedge moves the worst-5 days.

| Rule (BASE book; LO+L3-OUT in brackets) | CHECK ΔR/day (random, const) | T2 ΔR/day (random, const) | t vs random CHECK / T2 | Worst-5 CHECK / T2 | Per setup | Bar |
|---|---|---|---|---|---|---|
| S1 down-tape long brake | +0.03 (0.00, 0.00) [+0.02] | +0.00 (0.00, 0.00) [+0.00] | 1.04 / 0.45 [0.91 / 0.61] | unchanged | NM-ETF +7.8 / +0.4R; GEN-261020-09 −0.40 / +0.24 R/day (t vs random −1.97 / −0.14); GEN-261023-07 −0.11 R/day (CHECK only) | FAIL |
| S2 midday-chop short pause | **+0.88** (+0.72, +0.83) [+0.36] | **+0.60** (+0.44, +0.50) [+0.41] | 0.58 / 1.41 [0.96 / 0.97] | −178 → −171 / −122 → −116 | L3 +83/+52, RW3 +93/+85, RW5 +67/+110R (3 of 3 better) | FAIL |
| S3+H1-SPY (hedge to −4R/1%, freeze fades) | −4.4 R/yr | +14.1 R/yr | placebo p90 0% | 0% / 3% better | 4 / 3 fire days; hedge +2.4 / +7.5R | FAIL |
| S3+H1-IWM | −3.7 R/yr | +9.8 R/yr | placebo p90 0% | 0% / 3% better | same fires; hedge +3.2 / +0.4R | FAIL |
| H1-SPY standalone, 1R | +0.11R/tr (n 14; 81% one day) | −0.01R/tr (n 22) | placebo −0.19 / −0.14R | +1% / +1% | on worst-10 book days: 0 / +2.4R | FAIL |
| H1-IWM standalone, 1R | +0.13R/tr (87% one day) | −0.08R/tr | placebo −0.12 / −0.12R | +1% / +1% | worst-10: 0 / +1.9R | FAIL |
| H2 trapped-short reclaim long | **−0.071R/tr** (n 717, t −1.5) | **−0.127R/tr** (n 366, t −2.0) | control −0.041 / −0.097R; R05 +0.010 | +5% / +1% for −46 / −29 R/yr | 48% / 45% winners | FAIL |

**Read (honest, and what can be salvaged).**
- **S2 is the only rule that moves R, and it does so by trading less of a losing list.** It removes about 30-48% of eligible fades and all 3 fades get better, but a random brake of the same size gets 73-82% of the gain (t 0.58 / 1.41; LO T2 2.59, CHECK 1.63). Against a constant cut it is t 0.18 / 0.96. Goal metrics (BASE, CHECK): red days per month 13.1 → 12.3, worst-5 −178 → −171R, 20-session floor −237 → −215R (T2 −124 → −85R). This matches GATE1: the chop cut is size, not timing.
- **S1 barely binds in Primary.** It blocks 79 / 53 NM-ETF lots, about 52-55% of its eligible lots, but NM-ETF is ~1 lot/day. On GEN-261020-09 (a "QQQ < −0.3%" dip-buyer) S1 removes 83% of its eligible trades, and on CHECK it does worse than random. Live t −2.43 was in-sample and does not carry over.
- **S3 fires 4 / 3 times in 276 / 415 sessions** (B estimated ~7 with the gap filter). The worst-5 days are not V-reclaim days, which is the same finding as R2 in squeeze_1125. H1 beats its random-time placebo per trade (+0.11 vs −0.19 on CHECK), but 81-87% of that is one day, it is negative on T2, and it has 14-22 trades in total. It is a lead at best, not insurance.
- **H2 loses more than a random L3-universe long at the same minute** on both splits, and does worse than R05. The open reclaim plus SPY ≥ VWAP picks failed reclaims. Park it.
- Stricter C bar (t ≥ 3.46): nothing comes close (best 2.59, S2 on LO T2 only).

**Deviations (disclosed):** (1) REGSTEER-1's contender lots have no 1-min paths, so S1 on the two contenders is scored at trade level on all raw signals, without book rules. GEN-261023-07 has no T2 lots. (2) H2's T2 universe is the 469 cached 2023-24 names. (3) The IWM configs use the SPY trigger and trade IWM on its own levels.
**Rule-change context:** the bench replays today's Primary rules on every day, so no ledger change falls inside the bench windows. B's live window (10-01..11-25) spans 10-28 sizing, 10-29 −2R latch, 11-12 LR8, 11-17 TSZ1, 11-19 Epoch 1, 11-20 stop rounding and 11-23 burst brake / ST7 out. That is part of why its live cuts are in-sample only.
**Recommendation:** no DECISION draft and no shadow tag. Record S1/S2/S3/H1/H2 as tested-and-failed (TAPE-1126) next to GATE1 / R2. The tape effect is size, so the lever is the book's edge (PRIM-L3, LATCH-OPEN), not steering. If anything is kept, it is H1 as a ≤ 1-config journal-only tag, and only if the owner wants more V-day samples.
Scripts: build_idx.py, signals.py, sim.py, h2.py, cont.py, score.py; outputs score.json, cont.json.
