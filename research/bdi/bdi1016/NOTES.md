# BDI 2026-10-16: every trade on a one-way down day; early-session day-class direction gate

*Educational only - not financial advice.*

- Section 1 is one live **paper** session (rule 7): a diagnosis, not evidence. The week replay (B4) is descriptive.
- Section B is a backtest on the open history (2024-09-16..2026-10-07 without the locked block; 426 sessions),
  production + time-of-day costs in. The rule-19 locked block (2024-11-01..2025-02-28) was never loaded: the
  history2y loader refuses it, the script asserts `MCF_HIST_ALLOW_LOCKED` is unset and that no hit or feature row
  falls inside it.
- `PLAN.md` was written before any configuration was scored.

**Configurations scored tonight: 84** (12 gates x 6 parents + 12 on the pooled book).
- **0 meet the Primary bar.** The pooled book fails all 12 gates.
- **3 meet the pre-declared Testing bar**, all on short setups, all economically small (+0.004..+0.007R on parents
  that stay negative). One is proposed for Testing 1 (owner's call, weak, concentrated); see the proposal section.

## vs yesterday (2026-10-15)
| | 10-15 | 10-16 | why |
|---|---|---|---|
| Primary (journal) | -$861.83 (48 trades, 47 shorts) | **+$7.17** (36; 32 shorts +$92, 4 longs -$85) | Down day suited the short-heavy book; the three promoted FD shorts made +$91.62 |
| Testing 1 | -$1,673.02 (halted 11:10) | **-$19.40** | Shorts +$794.11 vs longs -$813.51 |
| Testing 2 | -$1,097.71 | **-$982.49** (halted 11:20) | Long-heavy book: longs -$1,114.75 (274), shorts +$132.26 |
| BDI | 99 configs, 0 research-bar pass | 84 configs, 0 Primary, 3 Testing-bar (small) | |

Same lesson mirrored: 10-15 the shorts lost on a reversal-up day; 10-16 the longs lost on a trend-down day. Over
10-12..10-16 all three accounts lost (journal P -$768.59, T1 -$2,223.87, T2 -$3,690.53), and each day's loss sat on the
side against the day's direction (table in B4). The system did not change; the direction of the day did. Tonight's
test asks whether that direction is knowable early enough to act on. Answer below: the class is, the setups'
sensitivity to it is not.

## 1. Every trade (747: Primary 36, T1 323, T2 388). Rule values, path, what-ifs, opposite side, loss type
`analyse_1016.py` is `bdi1015/analyse_1015.py` re-dated (nightly1016 `trades.csv` + SIP bars); per trade in
`trades_analysis_1016.csv`, per setup in `per_setup_1016.csv`. Base re-simulation vs journal R correlation: 0.987 (P),
0.958 (T1), 0.906 (T2).

| acct / side | n | journal R | base | BE@0.5R | t 0.5R | hold 15:55 | SAR | opposite 1R/1R | P/L |
|---|---|---|---|---|---|---|---|---|---|
| P short | 32 | -0.028 | -0.184 | -0.145 | +0.036 | -0.054 | -0.368 | -0.339 | +$92 |
| P long | 4 | -0.760 | -0.872 | -0.656 | -0.356 | -0.872 | -0.496 | +0.676 | -$85 |
| T1 short | 169 | **+0.304** | +0.241 | +0.129 | +0.121 | **+0.543** | +0.227 | -0.468 | +$794 |
| T1 long | 154 | -0.491 | -0.466 | -0.393 | -0.346 | -0.541 | -0.395 | +0.389 | -$814 |
| T2 short | 114 | +0.034 | -0.031 | -0.021 | +0.030 | **+0.704** | -0.151 | -0.397 | +$132 |
| T2 long | 274 | -0.365 | -0.393 | -0.363 | -0.438 | -0.755 | -0.218 | +0.546 | -$1,115 |

**Exits.** No exit overlay rescues the wrong side (BE / 0.5R target move longs by +0.03..+0.15R, still -0.35R or
worse). On the right side, holding to 15:55 doubles T1 short R (+0.54) and turns T2 shorts from +0.03 to +0.70: the
fixed-target shorts left the trend on the table. This is 10-15's "hold the longs" result with the sign flipped:
direction, not an exit rule.

**SAR / re-entry.** SAR legs on stopped longs +0.36R (T2, 133) / +0.12R (T1, 91); on stopped shorts -0.44R (T2, 31).
Re-entry after a stop: longs -0.78R (T1, 16) / -0.39R (T2, 23). Both follow the day (bdi1014 showed SAR has no edge of
its own on history).

**Rule values at entry, longs (median, winners vs losers).** T2: fromOpen -0.74 vs -0.78%, VWAP -0.31 vs -0.38%,
RSI5 40 vs 38, QQQ fromOpen -0.54 vs -0.57%. T1: fromOpen -4.12 vs -3.28%, RSI5 27 vs 15. No entry value separates them.

**Opposite side, hindsight check.** The pointer (QQQ fromOpen >= 0.25% against the trade and the stock beyond its
VWAP) was set on 379 trades, **all longs**; opposite R +0.497 vs -0.302 when not set. On 10-15 it pointed the other
way (shorts), on 10-14 it was noise. Its causal per-bar form failed on history (bdi1015 C2, ix-gate); its day-level
form is tonight's Part B.

**Timing.** T2: 245 of 274 longs entered in the 10:00 hour (-$1,032.67), i.e. before or at a 10:30 decision and
mostly before the index trend was visible (SPY -0.24% at 10:00, -0.30% at 10:30, -0.79% at 12:00).

**Loss types** (365 losers, merged into `patterns.csv` by date, idempotent):

| account | wrong_side_big_swing | never_worked | small MFE then failed | gave_back | stopped_then_reversed | late_hold |
|---|---|---|---|---|---|---|
| Primary (19) | 1 | 3 | 3 | 5 | **6** | 1 |
| T1 (169) | **59** | 22 | 20 | 33 | 18 | 17 |
| T2 (177) | 32 | **66** | 35 | 16 | 28 | 0 |

Worst setups: T2 CWT14-orl-p05-lowvol-long -$255.06 (64), CWT12-coil-k4-long -$238.50 (22, 27% wins), T1
heat_fade_long-FD -$231.93 (49), ST1-ordn-long-pm-FD -$210.08 (19), T2 CWT14-orl-p05-long -$195.79 (60). Best: T1
heat_fade_short-FD +$284.71 (35), RW7-FD +$134.69 (22), RW2-FD +$80.64 (19), heat_fade_short +$77.90 (7), T2
CWT14-pdh-p10-short +$52.34 (42).

## 2. Recurring patterns -> rules (105 setup x loss-type pairs on 3+ days; 80 of them recur today)
| pattern (days) | testable rule (known at entry) | status |
|---|---|---|
| CWT14 orl/pdl longs never_worked (5 days), small MFE (4-5), wrong_side (3) | day-class gate: no long after T on a trend-down day | **tested tonight, failed** (B) |
| heat_fade_long(-FD) wrong_side_after_big_swing (5 / 3 days), gave_back (5 / 4) | same gate | not testable (heat type, not in lab frames); heat-frame harness still queued |
| CWT14-pdh shorts stopped_then_reversed (5 days p05-lowvol, 4 days p10) | one re-entry after stop when price re-crosses the entry within 60 min | queued `bdi1016-cwt14pdh-reentry-after-stop` |
| RW7-FD late_hold (4 days) | per-setup late exit, split by day class | queued `bdi1016-rw7-late-exit` |
| Long/short book losses follow day direction (5 of 5 days this week) | early day class | tested tonight (B); allow-list and later-decision reworks queued |
| CWT12-coil-k4-long never_worked (4 days) | - | already in the CWT Testing-2 rule-20 review pack |

## B. Early-session day-class direction gate (new). 84 configurations; 0 Primary, 3 Testing-bar (small)
`regime_gate.py`, pre-declared in `PLAN.md` Part B. Results: `regime_results.csv` (every configuration),
`regime_by_class.csv` (parent exp per class), `regime_class_days.csv` (class frequencies vs rule-19 regime).
Bars: study max(1.5, sqrt(2 ln 84)) = **2.98**; market-context-gate lineage 2,366 + 84 = 2,450 -> **3.95**.

**How it differs from the earlier failures.** ix-gate (912), bdi-rg-g1..g5 (1,052), splitgate (370), the
CWT14/LIQ index-confirm and short-index-up vetoes all re-tested one index sign at every entry bar, splitting every
session in two. Here the class is fixed once at T, needs several features to agree, and has a chop class that gates
nothing (chop = 69-94% of sessions). The per-bar SPY-vs-VWAP / split-tape / SPY-up rules were not re-run.

### B1. Failures first
- **Pooled 6-setup book: 0 of 12.** Delta -0.004..+0.002R on -0.081R (n 277,461).
- **Long parents: 0 of 36.** Blocked longs on trend-down days are only slightly worse than the parent average.
  - CWT14-orl-p05-long: parent -0.092R (n 105,023). Best gate K1 k0.25 10:00: blocked 15,616 at -0.107R (t -3.77), delta +0.003, but the plateau neighbour (k0.50) is -0.002.
  - CWT14-pdl-p05-long: parent -0.086R. Best K1 k0.25 10:00: delta +0.002, blocked t -3.26; plateau fails (k0.50 -0.000) and WF 0.50.
  - LIQ-orl-sweep-long: parent -0.002R (n 13,336). Blocked t -0.75..+1.16; on K2 gates the blocked longs are *better* than the kept ones (+0.11..+0.17R).
- **Short parents: RW2-FD 0 of 12** (best K2 k0.50 10:00 delta +0.008, blocked t -2.63, plateau -0.002).
- **Every gated configuration still has negative expectancy** (best gated exp: LIQ K1 k0.25 10:00 +0.011R, t 0.3).

### B2. Per-regime result of the ungated parents (exp R by class)
| parent | K1 k0.25 @10:00: down / chop / up | K3 k0.25 @10:30: down / chop / up | K3 k0.50 @10:00: down / chop / up |
|---|---|---|---|
| CWT14-orl-p05-long | -0.107 / -0.090 / -0.082 | -0.136 / -0.085 / -0.061 | -0.075 / -0.095 / +0.006 |
| CWT14-pdl-p05-long | -0.126 / -0.087 / -0.030 | -0.148 / -0.091 / -0.002 | -0.113 / -0.090 / +0.071 |
| LIQ-orl-sweep-long | -0.060 / -0.010 / +0.230 | +0.019 / -0.025 / +0.088 | -0.122 / -0.003 / +0.538 (244) |
| CWT14-pdh-p05-lowvol-short | -0.059 / -0.098 / -0.101 | -0.018 / -0.090 / -0.158 | -0.010 / -0.097 / -0.097 |
| RW7-gapdn-bounce-early-short-FD | +0.000 / -0.059 / -0.132 | -0.065 / -0.048 / -0.103 | +0.011 / -0.055 / -0.346 |
| RW2-exhaustion-noon-FD | +0.012 / -0.078 / -0.019 | +0.002 / -0.062 / -0.088 | -0.110 / -0.054 / -0.131 |

**The classifier works; the setups do not care enough.** K1 k0.25 at 10:00 calls 50 trend-down days (35 are rule-19
down sessions, 5 up) and 45 trend-up days (30 up, 5 down); at 10:30, 61 and 61 (43 / 44 correct). The cells have
the expected sign (longs worse on down days, shorts worse on up days), but the gap is 0.01-0.05R for the CWT14
family. They lose -0.06..-0.15R in every class, so removing the against-trend days cannot make them positive.

### B3. The 3 Testing-bar passes (every finalist reported)
| gate / setup | blocked n / days / exp / t | delta (H1 / H2) | WF | random 95th | plateau | gated exp (t) | up / down sessions |
|---|---|---|---|---|---|---|---|
| K3 k0.50 @10:00 / RW7-FD | 662 / 11 / -0.343 / -3.01 | +0.0074 (+0.010 / +0.0045) | 5/7 | +0.0045 | K3 k0.25 +0.012 (t -2.87) | -0.051 (-2.58) | -0.27 / +0.12 |
| K1 k0.50 @10:00 / RW7-FD | 584 / 9 / -0.372 / -2.98 | +0.0072 (+0.010 / +0.0041) | 4/5 | +0.0051 | K1 k0.25 +0.0085 (t -1.76) | -0.051 (-2.59) | -0.27 / +0.12 |
| K1 k0.25 @10:30 / CWT14-pdh-p05-lowvol-short | 3,971 / 61 / -0.131 / -4.98 | +0.0037 (+0.0037 / +0.0035) | 0.60 (20) | +0.0029 | k0.50 +0.0008 (t -2.59) | -0.090 (-10.8) | -0.22 / +0.002 |

- **Concentration (rule 5), RW7.** 2025-04-07 and 2025-04-09 (tariff-crash rebound days) carry 233 of the 662 blocked
  trades and -147R of -227R. Without the worst day the blocked trades are still -0.24R. So it is a real but
  episodic effect: "don't short gap-down bounces on a broad 10:00 rip".
- **CWT14-pdh:** robust (61 days) but trivial (+0.004R on -0.094R). Not proposed; the family belongs to the rule-20
  review.
- None meets the Primary bar (gated exp < 0, t far below 3.95, up sessions negative).

### B4. Week replay (live paper, descriptive; `week_replay.py`, `week_replay_out.txt`)
Features rebuilt from SIP bars for 10-12..10-16 (breadth on the full 1,223-symbol lab universe).
| day | SPY / QQQ / IWM fromOpen @10:30 | breadth @10:30 | class by gate | live P/L shorts / longs (P+T1+T2) |
|---|---|---|---|---|
| 10-12 | -0.11 / -0.47 / -0.12 | 0.49 | chop (all 12) | +$318 / -$604 |
| 10-13 | +0.02 / +0.43 / -0.60 | 0.32 | chop (all 12) | -$1,030 / +$203 |
| 10-14 | -0.26 / -0.25 / -0.09 | 0.27 | **down** for K2/K3 k0.25 @10:30 | +$690 / -$1,340 |
| 10-15 | +0.15 / +0.22 / +0.45 | 0.62 | chop (all 12) | **-$3,929** / +$296 |
| 10-16 | -0.30 / -0.70 / -0.37 | 0.48 | **down** for K1 k0.25 @10:30 | +$1,018 / -$2,014 |

- At 10:00 every gate called every day chop.
- K1 k0.25 @10:30 would have blocked 260 live longs on 10-16 (-$1,310.60 of the -$2,014). K2/K3 k0.25 @10:30 would
  have blocked 82 longs on 10-14 (-$586.39).
- **The week's biggest loss, 10-15 (shorts -$3,929), was unclassifiable by 10:30** (SPY was still below its open at
  10:00; the reversal came later).
- Five sessions; this is not evidence and none of these four gates passed on history for the long side.

## Proposed changes (nothing applied; parent applies after hours only with the owner's decision)
### P1. Testing 1, optional and weak: day-class gate on RW7-gapdn-bounce-early-short-FD (K3 k0.50 @10:00)
It is the only pass worth a forward test. It is concentrated, the setup stays negative on history, and it **needs a
code change in mcf/** (not made; another agent is editing mcf/execution/). Recommendation: add it only if the owner
wants the day-class family watched forward. Otherwise keep it in the backlog.

`config/account_testing.yaml`, under the existing `RW7-gapdn-bounce-early-short-FD:` block (keep every other key):
```yaml
  RW7-gapdn-bounce-early-short-FD:
    # ... existing keys unchanged (enabled, type lab, module, min_adv 95000000, window [950, 1500]) ...
    day_gate:                 # NEW option (bdi1016): fixed day class at decide_at; chop days and earlier bars unchanged
      classifier: K3          # 6 votes: SPY/QQQ/IWM fromOpen beyond +-k, SPY vs prior close beyond +-k,
                              # breadth (share of universe above session VWAP) <= 0.40 / >= 0.60, SPY close vs 09:30-09:45 OR
      k_pct: 0.50
      votes_needed: 5
      decide_at: "10:00"      # bar closing at 10:00
      block: trend_up         # short setup: no new entry from 10:00 on a trend-up day
    testing_note: {added: "2026-10-19", source: "research/bdi/bdi1016", variant: "K3-k0.50-T1000", bar: "Testing bar only (blocked t -3.01 vs 2.98); concentrated in 2025-04-07/09; gated exp -0.051R"}
```
Code change needed (describe only):
1. `mcf/strategies/day_gate.py` (new): `classify(spy, qqq, iwm, breadth, spy_prev_close, spy_or, k_pct, votes_needed, classifier) -> -1/0/+1`. The definitions must match `research/bdi/bdi1016/regime_gate.py::classify` exactly.
2. Runner: compute the class once at `decide_at` from SPY/QQQ/IWM 1-minute bars, the 09:30-09:45 SPY range, SPY's prior RTH close and breadth over the scanned universe. Keep the class for the session, log it in status.json (`day_class`), and skip a strategy's signals at or after `decide_at` when its side matches `block`.
3. Backtester parity: the same hook in `mcf/backtest`, and a test reproducing the `regime_results.csv` row (gated n 25,502 on the open history).
4. Fail safe: if any input is missing, class = chop (no gating).

`research/ledger.jsonl` (only if approved), then `python -m mcf.research.ledger check`:
```json
{"id": "2026-10-19-testing-rw7-daygate", "date": "2026-10-19", "title": "Testing 1: day-class gate (K3 k0.50 at 10:00, block on trend-up) on RW7-gapdn-bounce-early-short-FD", "patch": {"testing.strategies.RW7-gapdn-bounce-early-short-FD.day_gate": [null, {"classifier": "K3", "k_pct": 0.5, "votes_needed": 5, "decide_at": "10:00", "block": "trend_up"}]}, "evidence": ["research/bdi/bdi1016/PLAN.md", "research/bdi/bdi1016/NOTES.md", "research/bdi/bdi1016/regime_results.csv"], "metrics_at_approval": {"configs_tried": 84, "lineage_configs": 2450, "study_bar_t": 2.98, "lineage_bar_t": 3.95, "parent": {"n": 26164, "exp_r": -0.0584}, "gated": {"n": 25502, "exp_r": -0.051, "t": -2.58}, "blocked": {"n": 662, "days": 11, "exp_r": -0.343, "t": -3.01}, "delta_H1": 0.010, "delta_H2": 0.0045, "wf": "5/7", "random95": 0.0045, "concentration": "2025-04-07/09 carry 233 trades, -147R of -227R"}, "approved_by": "owner (pending)", "notes": "Testing bar only; gated setup still negative. Educational only - not financial advice."}
```

### P2. Nothing for Primary. Nothing for the long books: no long-side gate passed.

## Backlog (`add_backlog.py`; `research/BACKLOG.md` regenerated, 426 entries)
| id | status | configs |
|---|---|---|
| `bdi1016-dayclass-direction-gate` | failed (3 Testing-bar children) | 84 |
| `bdi1016-dayclass-gate-rw7` | finalist (Testing bar only, P1) | in the 84 |
| `bdi1016-dayclass-gate-cwt14pdh` | finalist (not proposed) | in the 84 |
| `bdi1016-dayclass-trade-with-trend` | idea (allow-list form; the aligned-day cells are the only positive ones) | 0 |
| `bdi1016-dayclass-late-decision` | idea (rework at 11:00 / 12:00) | 0 |
| `bdi1016-cwt14pdh-reentry-after-stop` | idea (pattern, 5 days) | 0 |
| `bdi1016-rw7-late-exit` | idea (pattern, 4 days) | 0 |
| `nightly-1016-trend-day-long-reversal-veto` | idea; note added (its day-level form failed here; per-bar form untested) | - |

## Queued
1. `bdi1016-dayclass-trade-with-trend`: pre-declare it, count it in the 2,450 lineage (bar 3.95).
2. Heat-frame harness, so that heat_fade_long/short can be scored against the day class. They carried T1's swing both days.
3. LIQ-orl and RW7-FD per-setup late exits, split by day class.
4. The rule-20 review pack for the CWT14/CWT12 Testing 2 family. They are -0.06..-0.15R on history in every day class.

## Files
- `PLAN.md`.
- `analyse_1016.py`, which writes `trades_analysis_1016.csv` and `per_setup_1016.csv` and merges into `patterns.csv`.
- `regime_gate.py`, which writes `regime_results.csv`, `regime_by_class.csv` and `regime_class_days.csv`. Its hits and features cache is in the scratchpad.
- `fetch_week.py` and `week_replay.py`, which write `week_features.csv`, `week_replay_out.csv` and `week_replay_out.txt`.
- `add_backlog.py`.
