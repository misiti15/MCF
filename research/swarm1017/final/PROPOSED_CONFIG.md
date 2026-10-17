# Proposed config after the 2026-10-17 weekend swarm

*Educational only — not financial advice. Backtests on history and paper trades only. Nothing here is applied:
config/*.yaml, research/ledger.jsonl and research/backlog.jsonl were not touched.*

## 1. Final candidates: none

- 1,054,906 configurations were scored across 13 group studies, plus 15 exit/filter replays of the live week.
- About 30 near-miss modules went to adversarial re-verification. **0 survived.** Every one fails its try-count bar
  `max(1.5, sqrt(2 ln N_lineage))` (bars 4.57–5.25). Several also fail on other grounds: they are near-duplicates of
  live setups (more than 60% trade overlap), one or two days carry them, or the live runner cannot execute them.
- With no survivors there was nothing to score on the locked block (2024-11-01..2025-02-28). **It was not loaded.**
  It stays clean, and no lineage has used a look on it this weekend (RESEARCH_RULES 18/19).
- Therefore there is **no Primary-account change and no live-funds candidate.**

## 2. Optional: Testing 1 forward observation (paper only, owner decision Q3)

These five are **near-misses, not candidates**. The only reason to run them is to collect forward data (BDI charter
routing: "Testing account: promising near-misses and experimental ideas, tagged"). Here is why these five:

- They are live-runnable as type: lab today, with standard exits.
- They do not rest on day-of-week cuts.
- None is a filtered copy of a live setup.
- Each passes every gate except the try-count bar.

Their mutual trade overlap was **not** computed. They sit in different windows or on different sides, but check
this before enabling them. Modules are copied to `research/swarm1017/final/modules/`.

| # | setup | history (open 2y, after costs) | bar | weak point |
|---|---|---|---|---|
| 1 | AR-AM-gapdown-capitulation (long) | train +0.33R n741 t1.71 / valid +0.20R n847 t2.51; up +0.36 / down +0.35; WF 0.65 | 4.62 | half of train in Apr 2025; entries only 10:50–10:55; VALID used for plateau pick |
| 2 | AMS-N1-downtrend-quiet-bounce (short) | train +0.184R n194 t4.02 / valid +0.082R n206 t1.93; WF 0.83 | 4.62 | neighbour stability 52% |
| 3 | NM-PM-S-gapdn-above-pdh-rvol (short) | train +0.32R n274 t3.46 / valid +0.11R n173 t1.36 | 4.93 | top-5 days = 89% of train P/L; needs min_adv 95M |
| 4 | NM1-cwt09-g10-vwaploss-fodn-slopeup (short) | n241 +0.191R (train +0.177 / valid +0.204), t2.49; WF 1.00; max day share 0.11 | 4.80 | small n; not adversarially re-checked |
| 5 | NM-HL-T75-pm-t05s1 (long) | n1860 +0.045R t1.93; up/down ≈ +0.02 each | 4.57 | edge is thin (re-check: valid t 1.14) |

```yaml
# config/account_testing.yaml  (strategies:)  — ONLY if the owner answers Q3 = A
  NM-AR-AM-gapdown-capitulation-long:
    enabled: true
    type: lab
    module: research/swarm1017/final/modules/AR-AM-gapdown-capitulation.py
    min_adv: 95000000
    window: [950, 1100]
    scale_out_r: null
    tags: [near-miss, swarm1017, forward-observation]
  NM-AMS-N1-quiet-morning-short:
    enabled: true
    type: lab
    module: research/swarm1017/final/modules/AMS-N1-downtrend-quiet-bounce.py
    min_adv: 95000000
    window: [1000, 1100]
    scale_out_r: null
    tags: [near-miss, swarm1017, forward-observation]
  NM-PM-gapdn-above-pdh-rvol-short:
    enabled: true
    type: lab
    module: research/swarm1017/final/modules/NM-PM-S-gapdn-above-pdh-rvol.py
    min_adv: 95000000          # required: the mask has no adv filter, and the result depends on it
    window: [1400, 1500]
    scale_out_r: null
    tags: [near-miss, swarm1017, forward-observation]
  NM1-cwt09-g10-vwaploss-short:
    enabled: true
    type: lab
    module: research/swarm1017/final/modules/NM1-cwt09-g10-vwaploss-fodn-slopeup-short.py
    min_adv: 1000000
    window: [1030, 1500]
    scale_out_r: null
    tags: [near-miss, swarm1017, forward-observation]
  NM-HL-T75-pm-long:
    enabled: true
    type: lab
    module: research/swarm1017/final/modules/NM-HL-T75-pm-t05s1-long.py
    min_adv: 125000000
    window: [1300, 1500]
    scale_out_r: null
    tags: [near-miss, swarm1017, forward-observation]
```

**Live-runner support notes**

- All five load in `LabStrategy` (import checked: SIDE/GEOM/mask present) and use geometries the live runner already
  has (t1s1, t05s1). No scale-out, trail or t05s05 is needed.
- Modules 1–3 import `mcf.research.arena.indicators`. That package is new swarm code (mcf/research/arena/) and must be
  committed with tests before these setups are enabled (backlog `swarm1017-arena-package`).
- Module 4 loads `research/bdi/cwt/live/cwt_live_lib.py` by relative path (parents[3]). That resolves from
  `research/swarm1017/final/modules/`, so do not move the file to another depth. It also needs the 09:35–10:30 bars
  that the live frame already carries for the CWT09 setups.
- Module 1: `ret12` is NaN before 10:50, so it can fire only at 10:50–10:55.

**Draft ledger lines** (to append only after approval, merged after the close):

```json
{"id": "2026-10-19-swarm1017-nm-forward", "date": "2026-10-19", "title": "Add 5 swarm1017 near-miss lab setups to Testing 1 as tagged forward observation (not candidates)", "patch": {"testing.strategies.NM-AR-AM-gapdown-capitulation-long": [null, "enabled lab"], "testing.strategies.NM-AMS-N1-quiet-morning-short": [null, "enabled lab"], "testing.strategies.NM-PM-gapdn-above-pdh-rvol-short": [null, "enabled lab"], "testing.strategies.NM1-cwt09-g10-vwaploss-short": [null, "enabled lab"], "testing.strategies.NM-HL-T75-pm-long": [null, "enabled lab"]}, "evidence": ["research/swarm1017/SUMMARY.md", "research/swarm1017/final/PROPOSED_CONFIG.md"], "metrics_at_approval": {"all_fail_try_count_bar": true, "locked_block_scored": false}, "approved_by": "owner (Q3)", "notes": "Paper only. Judged on forward sessions (>= 20 sessions, >= 60 trades). Educational only - not financial advice."}
```

## 3. Current live setups the evidence says should move to the Graveyard (never deletions)

Testing 2 becomes the Graveyard after 10-20. Under RESEARCH_RULES rule 20, each move needs an owner prompt with the
setup's stats. Former-primary setups (`former_primary`) also need 10 Testing sessions counted from their move. Every
setup below meets all three conditions:

- negative on 2y history after costs
- negative on the live paper week (n ≥ 10)
- its family rework found no variant clearing the bar

Live figures are avgR after costs, 10-06..10-16, paper. History figures are from the family NOTES.

**Testing 1 → Graveyard (owner prompt, Q4):**

| setup | live n / avgR / P/L | history |
|---|---|---|
| RW6-ns2-up3-short-FD | 35 / −0.605 / −$319 | RW6 family negative; rework-rw: retire |
| NS2-sma50break-overbought-short-FD | 65 / −0.443 / −$428 | −0.055R |
| heat_fade_long-FD | 91 / −0.536 / −$346 | −0.046 / −0.022R |
| ST1-ordn-long-pm-t05s1-FD | 22 / −0.593 / −$241 | −0.056R (n 1621) |
| exhaustion_short-FD | 20 / −0.321 / −$89 | −0.063R |
| L3-gap-slope-fromopen-FD | 41 / −0.275 / −$161 | −0.042R |
| L3-gap-slope-lowdist-FD | 16 / −0.261 / −$67 | −0.104R |
| MF1-945-flowsell-vwapup-FD | 26 / −0.301 / −$7 | −0.079R t −5.76 |
| RW2-exhaustion-noon-adv150-short-FD | 119 / −0.176 / −$233 | −0.059R |
| heat_fade_short-FD | 240 / −0.130 / −$218 | −0.043 / −0.024R |
| ST2-slope20up-long-am-t05s1-FD | 63 / −0.173 / −$181 | −0.051R |

**Former primary, in Testing 1 (rule-20 clock; prompt when 10 Testing sessions are reached, Q5):**
NS2-sma50break-overbought-short (54 / −0.490 / −$856), heat_fade_long (111 / −0.266 / −$353),
heat_fade_short (82 / −0.417 / −$295).

**Already in Testing 2 (becomes the Graveyard), flagged for the retirement prompt:**
CWT09-gapdn-vwaploss-g5-short (−0.751), CWT09-gapdn-bounce-g5-lowerhalf-short (−0.587, −$661),
CWT13-vwapstretch-z05-short (−0.371), CWT14-failbrk-orl-p05-lowvol-long (294 / −0.283 / −$634), and the other CWT14
parents (all −0.08 to −0.19R live, −0.084 to −0.094R history, no better than random).

**Primary → Testing 1 (demotion, not Graveyard; Q6):** MF1-945-flowsell-vwapup, MF3-open-flowsell-rsi5hi and
MF5-flowsell-vwapup-rsi5hi are negative on 2y history (FD versions −0.079 / −0.075 / −0.057R). MF4 is on its owner
review after 10-19. Live, MF1 was +0.18R on n 12, MF3 −0.03 on n 27 and MF5 −0.12 on n 33. That is noise-sized, and
it does not offset the history.

**Keep watching (no change):** RW3-gapdn-FD (+0.36R n34), RW5-heat30-FD (+0.41R n31), MF2-FD (+0.43R n19). Each has
fewer than 35 trades, and their 2y histories are ≤ 0, so this is not evidence.
