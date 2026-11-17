# UPDAY — candidate short setups for up-day copies (Step A)
Educational only — not financial advice. Mechanic 2026-11-17 (built after hours, ~02:00 UTC).

Owner batch 2026-11-17: rework the number-one short setup (Gap-Down Recovery Fade, all day) and other very high-volume,
successful short setups on the Workbench so they also hold up on UP-market days. Interpretation: build copies of the SHORT
setups that hold up or succeed on up days; they are not turned into longs.

**Source:** every account journal (`git show origin/<data branch>:journal.db`, `run_id = 1`, closed trades; Primary, On Deck,
Testing A-F, Setup Generator, Graveyard), sessions 2026-10-06..2026-11-16. R = pnl_adj / (|entry − stop| × shares) (R after
costs). Short = `side = -1`. Filter: ≥ 60 live trades, avg R > 0 and avg R w/o best day > 0; ranked by trade count.
43 short setups have ≥ 60 trades; **exactly 6 pass both filters** (all shown).

**Day type** (owner direction rule: post-09:50 anchors only): SPY close at 09:50 → SPY close at 16:00; up > +0.25%,
down < −0.25%, quiet in between. In the live window: 10 up, 8 down, 12 quiet sessions.

| setup | id | accounts | trades | sessions | avg R | avg R w/o best day | best-day share | up-day avg R | down-day avg R | quiet-day avg R |
|---|---|---|---|---|---|---|---|---|---|---|
| Gap-Down Recovery Fade (all day) | `L3-gap-slope-fromopen-FD` | primary,testing | 371 | 22 | +0.249 | +0.202 | 36% | +0.106 (162 tr / 8 s) | +0.220 (68 tr / 6 s) | +0.426 (141 tr / 8 s) |
| Gap-Down Pop Fade (all day) | `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD` | primary,testing | 193 | 25 | +0.133 | +0.037 | 76% `1 day` | −0.231 (53 tr / 7 s) | +0.570 (60 tr / 8 s) | +0.047 (80 tr / 10 s) |
| Gap-Down Pop Fade, Heavy Selling (all day) | `RW3-gapdn-rsi5pop-flowsell-short-FD` | primary,testing | 182 | 25 | +0.218 | +0.099 | 61% `1 day` | −0.173 (30 tr / 7 s) | +0.676 (80 tr / 8 s) | −0.127 (72 tr / 10 s) |
| Gap-Down Rebound Overbought Short (all day) | `L3-gap-slope-rsi5hi-FD` | primary,testing,testing2 | 148 | 21 | +0.108 | +0.026 | 82% `1 day` | +0.200 (33 tr / 6 s) | −0.103 (24 tr / 6 s) | +0.131 (91 tr / 9 s) |
| Generated: PM Upper-Band Fade (weak mkt) | `GEN-261026-07-Flow3ge0p56-BBpctge0p98-ADX7le34-PM-BRvwlt0p3-holdtr-short` | gen,testing2 | 125 | 5 | +0.047 | +0.007 | 91% `1 day` | — (0 trades) | +0.024 (115 tr / 4 s) | +0.318 (10 tr / 1 s) |
| Gap-Down Bounce-off-Low Fade (all day) | `L3-gap-slope-lowdist-FD` | testing | 106 | 17 | +0.232 | +0.086 | 74% `1 day` | +0.197 (28 tr / 6 s) | +0.174 (17 tr / 5 s) | +0.264 (61 tr / 6 s) |

Reading it (small samples; 6-10 sessions per day type):
- Only L3-fromopen is a clean, broad record (best day 36%). Its up days are its weakest but still positive live (+0.106).
- RW5 and RW3 (the gap-down pop fades) are the real up-day sufferers live (−0.231 / −0.173) and earn on down days — the
  next candidates for an up-day copy after L3.
- L3-rsi5hi and L3-lowdist are already positive on up days live; their records lean on one big day (82% / 74%).
- The GEN PM fade has traded on 5 sessions, none an up day (it gates itself on a weak market) — no up-day evidence.

**Rule changes inside the window** (research/ledger.jsonl): LR8 live cost model + LR2/LR3 R-after-costs (effective
2026-11-12; earlier trades booked the lighter cost allowance), Testing cost filter CF (Testing 1/2, 10-30), moves: RW5/RW3
promotion-is-a-move (10-21), L3-rsi5hi Testing 2 → Primary (10-30), L3-fromopen Testing 1 → Primary (10-30), Primary
TEAM-6 (11-11, open-ended 11-16), On Deck build (11-12), Testing rotation ROT1 (11-16). Account mixes and cost booking
differ before/after these dates, so the per-day-type splits mix rule regimes.

## Which ones go to the up-day Workbench (coordinator 2026-11-17)
- **Reworked:** `L3-gap-slope-fromopen-FD` (`L3-gap-slope-fromopen-FD/`), and the two with the biggest live up-day losses —
  `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD` (up −0.231) and `RW3-gapdn-rsi5pop-flowsell-short-FD` (up −0.173) — each compared
  with its parent AND its previous Workbench copy WB3 (`RW5-.../`, `RW3-.../`).
- **Skipped:** `L3-gap-slope-rsi5hi-FD` (+0.200 on up days live) and `L3-gap-slope-lowdist-FD` (+0.197) — already positive on up
  days, no up-day problem to fix (their records lean on one big day instead, 82% / 74%); `GEN-261026-07-...` — 0 trades on up
  days (it gates itself on a weak market), so there is no up-day evidence to work on.
