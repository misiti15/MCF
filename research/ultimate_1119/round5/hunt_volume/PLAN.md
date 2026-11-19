Educational only — not financial advice

# Round 5 volume-track hunt (H5V): pre-declared plan

Written 2026-11-19 before any H5V signal row was built. Research only: no setup, exit, YAML, account or ledger change.
Data: the 2-year cache only. FIT = 2024-10 + 2025-03-01..2025-09-30 (170 sessions); CHECK = 2025-10-01..2026-11-04
(276 sessions). The locked block 2024-11-01..2025-02-28 is never read. The fresh window (2023-01..2024-09) is not read.

## Goal
Find more narrow, liquid, event-style edges like legs E and M of BOOK-EM, so the book trades more per session without
lowering its avg R. Each leg is its own rule (its own universe, side, window and exit). Legs are not widened versions of
E or M.

## Legs and grid (40 configurations, module `H5V.py`)
| Leg | Side | Idea | Grid | Configs |
|---|---|---|---|---|
| F | long | ETF one-bar RSI collapse (EQB ETFs, adv20 >= $95M; the M trigger on funds) | RSI now {<= 30, <= 35} x buy-pressure gate {on, off} x exit {t1s1, t05s1} | 8 |
| S | short | heavyweight one-bar RSI spike fade (stocks) | adv20 {$500M, $1B} x RSI now {>= 70, >= 75} x exit {t1s1, t05s1} | 8 |
| C | short | heavyweight one-bar RSI collapse continuation, no buy pressure (the complement of M) | adv20 {$500M, $1B} x SPY gate {none, SPY below open}; exit t1s1 | 4 |
| X | short | WB4 mirror: late-afternoon ETF pop fade (W list, 14:00-15:00) | 15-min rise {>= +0.5%, >= +0.75%} x exit {t05s1, t1s1} | 4 |
| K | long | one-bar shock snap in liquid / leveraged ETFs (5-min drop <= -k x daily ATR%, volume climax >= 2) | universe {EQB adv20 >= $300M, LEV adv20 >= $95M} x k {0.2, 0.3} x exit {t1s1, t05s1} | 8 |
| V | long | capitulation bar in liquid stocks (adv20 >= $500M; 5-min drop <= -0.10 x ATR%, lower wick >= 0.3) | volume climax {>= 2, >= 3} x exit {t1s1, t05s1} | 4 |
| Q | long | sector / context ETF relative extreme vs SPY (11:00-15:00, RSI <= 35) | k {0.5, 0.75} x exit {t1s1, t05s1} | 4 |

**Grid amendment (before any outcome was computed).** A first signal-count pass on 2025-03 and 2025-07 (row counts
only, no returns or walks) showed legs F and V firing about once a month. Two changes followed. F's adv grid ($95M /
$300M) was replaced by a buy-pressure on/off gate. V was loosened from a -0.15 x ATR% drop with lower wick >= 0.4 and
volume climax {2.5, 4} to a -0.10 x ATR% drop with lower wick >= 0.3 and volume climax {2, 3}. The config count stays 40.
The count-only look is not counted as configs.

## Chassis (unchanged from round 4: `round4/ULT-28/bt.py` walk + cost_R)
- Entry at the open of the 1-minute bar that starts at the decision-bar close. Brackets sit around the decision close.
- Stop first, then target. A stop gap-through fills at the worse of open and stop. A target fills at the limit with no exit
  cost. Stops pay +2c.
- 45-min time exit; flat by 15:50.
- LR8 costs. Shorts pay borrow (1.2 bp of entry notional, 3 bp under $20) and trade only easy-to-borrow names
  (today's flag, a bias that favours shorts).
- Earnings blackout of ±4 sessions on the stock legs (S, C, V). With it, no stock-leg trade falls on a reaction day, so
  `evt = 0` is correct for all rows.
- Per leg: one lot per symbol, max 2 per symbol-session (the 2nd >= 30 min after the 1st exit), day cap 30.

## Selection (pre-declared)
1. **FIT.** Each leg's pick is the config with the highest FIT total R (ties go to the earlier config). A leg goes on to
   CHECK only if its FIT pick has total R > 0 and >= 15 trades.
2. **Freeze.** `fitsel.json` holds the picks, the module's P is set to them and the sha256 of the module and hunt.py is
   recorded. All of this is written before any CHECK row is built.
3. **CHECK, once per advancing leg.** A leg is kept if check avg R > 0 and check avg R w/o best day > 0 (costs in).
4. **Keep at most 6.** If more than 6 pass, keep the 6 with the highest FIT total R. CHECK is never used to rank.
5. **Report everything:** every config's FIT figures, every advancing leg's CHECK figures, random-entry controls, and
   overlap with BOOK-EM legs E / M (the same symbol-session).
6. **Configs counted:** 40 grid. Random controls and overlap diagnostics are not counted. The job's cumulative N before
   round 5 is 996 (up to 1,012), so after this hunt it is 1,036 (up to 1,052).

Kept legs are frozen into `round5/FREEZE_HUNT.json` / `round5/HUNT_FREEZE.md` (the volume-track slot of FRESH_PLAN.md
sec. 4) before any fresh byte exists.
