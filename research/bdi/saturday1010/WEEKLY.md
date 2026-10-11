# BD&I Saturday deep run, 2026-10-10: week of Oct 5–9 and the plan for Oct 12–16

*Educational only - not financial advice. Paper accounts; backtest numbers are labelled as such.*

## Week in numbers (journal P/L)
| | Oct 6 | Oct 7 | Oct 8 | Oct 9 | week |
|---|---|---|---|---|---|
| Primary (trades) | -33.62 (34) | -262.03 (16) | -120.66 (48) | -238.87 (70) | **-655.18 (168)** |
| Testing (trades) | - | - | - | -25.03 (46) | -25.03 (46) |

- **Primary by entry time (4 sessions):**
  - 09:50-10:30: -$482, 73 trades
  - 10:30-11:30: -$286, 43 trades
  - after 11:30: +$27, 62 trades
- **Primary on Oct 9 by side:** shorts -$247 (54 trades), longs +$8 (16 trades).
- **RW6G1:** 0 trades. Setups earlier in the list took its symbols first. The setup_order fix takes effect Monday.

## 4-session scorecard: decisions due (owner decides)
The five original setups have now run 4 sessions (Oct 6-9). All five failed the Apr-Jun holdout in backtest.

| setup | n | avg R | P/L | backtest exp R | scorecard | BDI recommendation |
|---|---|---|---|---|---|---|
| heat_fade_short | 50 | -0.280 | -177.24 | -0.015 | below backtest - review | retire |
| heat_fade_long | 43 | -0.112 | -161.00 | -0.138 | negative so far | retire |
| exhaustion_short | 23 | -0.256 | -72.33 | -0.020 | below backtest - review | retire or keep on Testing only |
| orb20_a | 9 | -0.149 | -247.64 | -0.040 | too few trades | keep 4 more sessions |
| intraday_momentum | 0 | - | - | -0.091 | no trades | no evidence either way |

- **MF1-5 and NS1-5:** 2 sessions so far; their decision is due after Oct 13.
- **Testing account:** 1 session; its decision is due after Oct 14.

## Saturday research (every configuration counted)
| workstream | configs | result |
|---|---|---|
| Rule-18 rework, longer holds (`rework/`) | 104 | Two finalists, each scored once by the lead on the locked block (look 2, bar t >= 1.5). Both **fail**: Connors RSI3 + VIX percentile n329, -103 bps, t -1.58; weekly reversal + VIX term structure + short-volume filter n341, +272 bps, t 0.94 (11 sessions). 18 momentum crash guards: all fail. Earnings exclusion hurts both. |
| New ideas (`new/`) | 124 | **0 pass.** Post-earnings drift: best t 2.01 vs a 3.10 bar, only in small names. FINRA short-volume ratio: fails as a long signal and as an S6 filter. |
| Weekly discover workflow | - | Bar cache refreshed (1,226 symbols). **The backlog re-test is a no-op** (see below). |

- **What the new data adds:** the VIX term structure (VIX/VIX3M) improved which stocks the reversal strategy picked, on the same trades. This is the one real finding from the new data, but there are too few independent episodes to trade on. It goes in the backlog for a larger sample.
- **Week total:** about 1.3M intraday configs plus 105 longhold, 158 W3, 104 rework and 124 new-idea configs. Only **S6 weekly momentum** has passed the locked block.

## Tooling gap found
`python -m mcf.research.backlog run` scores only entries that have a `module` field, using the old reddit_bt framework. None of the 277 entries has one, so the weekly re-test has done nothing. Rule 17 (continuous re-test) is therefore not being met. The two-year history used since rule 19 lives only in the research container, not on GitHub runners.

Proposed housekeeping fix:
- Teach the backlog runner the lab-module interface (SIDE, GEOM, LAYERS, mask) through gates.lab_trades.
- Re-test on the bar cache the discover job already refreshes (Jun 15 onward, so open forward data only).
- Report forward drift for each live/probation setup.

## Plan for Oct 12-16
1. **Monday:**
   - Watch the setup_order and SMA50-parity fixes in their first live session, and confirm RW6G1 takes trades.
   - Watch the time-of-day costs; they apply to research scoring only.
2. **Owner decision on the original five**, merged outside 09:30-16:00 with a ledger entry. Recommendation: retire heat_fade_short and heat_fade_long. Together they lost -$338 over 93 trades and are negative in both backtest and live.
3. **Long-hold runner:**
   - Build `mcf/longhold` per research/longhold/DESIGN.md.
   - The signal, plan file and dry run need only the data keys that already exist, so the 2-week dry run can start this week.
   - Orders wait for the third paper account (ALPACA_LONGHOLD_* secrets).
4. **Backlog re-test fix** (housekeeping, above).
5. **Research queue:**
   - Post-earnings drift rework: large caps only, idle cash in SPY.
   - VIX term structure as a stock-selection layer, with a capped basket on 10 years of data.
   - Any next locked look on the Connors or reversal lineages needs t >= 2.0.
6. **MF/NS 4-session review after Oct 13; Testing account review after Oct 14.**
