# cf1026: Primary if only Claude's promotion/demotion recommendations had been followed

Owner question (2026-10-26): "Rerun Primary showing how it would currently look if I had only used Claude's
recommendations as they related to Primary's promotions/demotions."

This is research only and read-only. No config, setup or exit changed. The sessions run from 2026-10-06 to 2026-10-23,
which is the last closed session in the journals; 10-26 is still open. Moves effective 2026-10-26 (MF1 demoted,
CWT13-z05-long and ST7-FD promoted) **have no closed sessions yet** and so add nothing to either column.
Script: `cf.py`. Outputs: `per_session.csv`, `attribution.csv`, `agreed_moves.csv`, `tables.md`.
Educational only — not financial advice.

## Sources
- `research/ledger.jsonl`: approved_by and effective date for every Primary move.
- `config/default.yaml` git history: setup enabled flags at each commit. This was checked against the setups that
  actually traded in Primary on each date; the script asserts that every Primary trade's setup was enabled that day.
- Claude's recommendations came from:
  - `research/bdi/saturday1010/WEEKLY.md` (the original five)
  - `research/bdi/nightly1013/NOTES.md` (NS3)
  - `research/bdi/bdi1015/NOTES.md` (NS2, and "nothing met the Primary bar")
  - `research/owner_inbox/2026-10-19.md` (P1-P5), `2026-10-20.md` (N1, N2), `2026-10-21.md` (N5),
    `2026-10-22.md` (L3-1), `2026-10-23.md` (MF1-D)
  - `docs/live/decisions.json` (PROMO-Z05L, PROMO-ST7, both "Optional — owner's call")
  - `docs/DECISIONS.md` and the closed table in `research/owner_inbox/OPEN_ITEMS.md`
- Trades: journals `git show origin/<branch>:journal.db` for mcf-data, -testing, -testing2 and -graveyard, using
  `trades` run_id=1. Run_id=2 holds Primary's what-if trades for skipped signals; it is used only for the "twin held"
  blocks.

## Step 1: decision log (every move into or out of Primary since 2026-10-06)

| # | Move | Claude's recommendation at the time | Owner | Effective (first session) | Class |
|---|---|---|---|---|---|
| 0 | Starting lineup: orb20_a, intraday_momentum, heat_fade_short, heat_fade_long, exhaustion_short (added mid-session 10-06) | Claude's own research picks (setup screen and heat swarm) | approved | 10-06 | Claude's baseline |
| 1 | **+MF1-MF5, NS1-NS5** into Primary | Not recommended: all failed the research gates or holdouts ("owner overriding the research gates") | did it | 10-08 | owner without/against Claude |
| 2 | **+RW6G1** into Primary | Not recommended: t 2.39 vs a required 4.76 | did it | 10-09 | owner without/against Claude |
| 3 | **−heat_fade_short, −heat_fade_long** | "retire" | did it | 10-12 | Claude recommended & owner did it |
| 4 | **−exhaustion_short** | "retire or keep on Testing only" | did it | 10-12 | **ambiguous** (leans demote); base case counts it as recommended |
| 5 | **−orb20_a** | "keep 4 more sessions" | demoted | 10-12 | owner against Claude |
| 6 | **−intraday_momentum** | "no evidence either way" (0 trades because of a live-timing bug) | demoted | 10-12 | owner without Claude |
| 7 | **−NS3** (windowed) | 10-13: "demotion candidate … Owner decision" | did it (10-14 evening) | 10-15 (Claude's date would be 10-14; NS3 had 0 trades on 10-14) | Claude recommended (soft) & owner did it |
| 8 | **+RW5-FD, RW3-FD, MF3-FD** | Not recommended: bdi1015 "Nothing met the Primary bar"; the owner explicitly overrode rule 19 | did it | 10-16 | owner without/against Claude |
| 9 | **−NS2** | 10-15: "Primary, owner decision: review NS2 under its scorecard flag" (history flat, fails the regime gate) | did it | 10-16 | **ambiguous** (flagged, no explicit yes); base case counts it as recommended |
| 10 | Keep MF4 (P1) | "keep" | kept | — | agreed (no move) |
| 11 | **−MF3 windowed** (P2) | "yes" | did it | 10-20 | Claude recommended & owner did it |
| 12 | **−MF5** (P3) | "yes" | did it | 10-20 | Claude recommended & owner did it |
| 13 | Keep MF1 (P4) | "not yet, re-check at 40 trades" | kept | — | agreed (no move) |
| 14 | **+NS3-FD** (P5) | "wait … t 0.9 could be luck; re-check at 60 trades" | promoted | 10-20 | owner against Claude |
| 15 | **+MF2-FD, MF4-FD** | No recommendation: neither met the proposed rule (≥ 40 trades) and P5 named NS3-FD as the only candidate | promoted | 10-20 | owner without Claude |
| 16 | **+L3-gap-slope-fromopen-FD** | Not recommended: it was on Claude's Graveyard list for 10-20 ("stays on tonight's Graveyard list unless you say otherwise") | promoted | 10-21 | owner against Claude |
| 17 | **+CWT14-failbrk-pdl-p10-lowvol-long** | No recommendation (CWT backtest verdict "retire", t −8.85) | promoted | 10-21 | owner without Claude |
| 18 | **−MF3-FD** (N1) | "yes" (raised 10-20 evening) | first "keep ON WATCH", then demoted the same evening | 10-21 | Claude recommended; the owner hesitated, then did it with no session lost |
| 19 | **−NS3-FD** (N5/R3) | "yes" (10-21 evening) | did it 07:40 ET | 10-22 | Claude recommended & owner did it |
| 20 | **−RW6G1** (N2) | "yes" (10-20 evening, so Claude's date is 10-21) | did it 10-22 ~07:50 ET | 10-22 | Claude recommended, owner one session later (RW6G1 had 0 Primary trades on 10-21, so $0) |
| 21 | **−L3-fromopen-FD** (L3-1) | "Yes — demote" | did it | 10-23 | Claude recommended & owner did it |
| 22 | **−MF1** (MF1-D) | "Yes - demote" | did it | 10-26 | Claude recommended & owner did it (no closed session yet) |
| 23 | **+CWT13-vwapstretch-z05-long** | "Optional — owner's call; backtest is negative" | promoted | 10-26 | owner without Claude (no closed session yet) |
| 24 | **+ST7-rsi50dn-long-pm-t1s1-FD** | "Optional — owner's call; small sample" | promoted | 10-26 | owner without Claude (no closed session yet) |

Tally:
- Claude never recommended a promotion into Primary. Every promotion (rows 1, 2, 8, 14-17, 23, 24) was the owner's call.
- 10 of Claude's 11 demotion recommendations were carried out on the same session Claude's timing implies. RW6G1 came
  one session late, which cost $0.
- The owner made two demotions Claude did not recommend: orb20_a and intraday_momentum.

## Step 2: counterfactual lineups

There are two readings, because the 10-08/10-09 probation adds (rows 1 and 2) were direct additions to Primary that
Claude did not recommend:

- **CF-A, strict since 10-06.** Only Claude's moves happen.
  - 10-06 to 10-09: the original five.
  - From 10-12: orb20_a and intraday_momentum only, because the heat fades and exhaustion_short were retired per Claude.
  - Nothing is ever promoted.
- **CF-B, owner's 10-08/10-09 probation adds kept.** This tests only the later Testing→Primary promotions and the
  demotions.
  - Lineup: the original five, plus MF1-5 and NS1-5 (10-08), plus RW6G1 (10-09).
  - 10-12: the heat fades and exhaustion_short go; orb20_a and intraday_momentum stay.
  - 10-14: NS3 out. 10-16: NS2 out. 10-20: MF3 and MF5 out. 10-21: RW6G1 out.
  - No RW5/RW3/MF3-FD, MF2/MF4/NS3-FD, L3 or CWT14-pdl.
  - From 10-21 the lineup is MF1, MF2, MF4, NS1, NS4, NS5, orb20_a and intraday_momentum.
- **Strict variants.** These treat the ambiguous recommendations (rows 4 and 9) as "not recommended", so exhaustion_short
  and NS2 stay. They are reported as a sensitivity check.

## Step 3: scoring
- **Setups in actual Primary that day:** Primary's own trades. R is after costs:
  `r_adj = r_multiple − (pnl − pnl_adj) / (shares × |entry − stop|)`. Dollars are `pnl_adj`.
- **Setups that were not in Primary that day:** their live trades that day under the same setup name, from the account
  they ran in. In practice that is only orb20_a and intraday_momentum, both from Testing 1.
- **Dollar conversion for those trades:** R × Primary's median $ per 1R, which is **$16.79**. That is the median of
  shares × |entry − stop| over Primary's 624 trades. Primary's slot cap (equity × 3.2 / 160 ≈ $2k) binds well before the
  0.25%-of-equity risk does, so a Primary R is small in dollars and varies a lot by stop width.
- **Twin blocks:** in CF-B the windowed MF2 and MF4 would not have been blocked by their -FD twins from 10-20. Their 14
  Primary what-if trades (run_id 2, `why=twin held`) are added at $16.79/R. This adds +1.54R; the CF-B result without
  them is also shown.

## Step 4: results

### Per session (after costs; Primary $)

| Session | Actual $ | Actual R (n) | CF-A $ | CF-A R (n) | CF-B $ | CF-B R (n) |
|---|---|---|---|---|---|---|
| 10-06 | −127.73 | −5.43 (44) | −127.73 | −5.43 (44) | −127.73 | −5.43 (44) |
| 10-07 | −264.73 | −5.17 (16) | −264.73 | −5.17 (16) | −264.73 | −5.17 (16) |
| 10-08 | −140.80 | −7.93 (48) | −122.73 | −7.34 (21) | −140.80 | −7.93 (48) |
| 10-09 | −254.09 | −12.58 (70) | −171.86 | −9.76 (44) | −254.09 | −12.58 (70) |
| 10-12 | **+115.77** | +7.86 (22) | 0.00 | 0 (0) | **+115.77** | +7.86 (22) |
| 10-13 | −101.67 | −3.83 (18) | **+5.80** | +0.35 (4) | −95.87 | −3.49 (22) |
| 10-14 | **+60.35** | +3.12 (11) | **+1.50** | +0.09 (3) | **+61.85** | +3.21 (14) |
| 10-15 | −926.53 | −29.12 (48) | **+28.16** | +1.68 (1) | −898.37 | −27.44 (49) |
| 10-16 | −14.41 | −6.34 (36) | **+13.92** | +0.83 (2) | −87.37 | −6.16 (21) |
| 10-19 | −63.92 | −6.47 (37) | −20.46 | −1.22 (2) | −48.26 | −5.74 (19) |
| 10-20 | −46.13 | −3.67 (70) | −54.95 | −3.27 (5) | −67.54 | −7.86 (32) |
| 10-21 | −626.57 | −14.78 (46) | −20.25 | −1.21 (3) | −10.21 | −0.33 (5) |
| 10-22 | **+1,369.10** | +65.77 (126) | **+78.45** | +4.67 (7) | **+120.55** | +5.79 (16) |
| 10-23 | −92.06 | −2.05 (32) | −41.78 | −2.49 (3) | −121.86 | −5.74 (8) |

### Totals since start (14 sessions, 10-06 to 10-23)

| | Actual | CF-A strict | CF-B (probation adds kept) |
|---|---|---|---|
| Trades | 624 | 155 | 386 |
| P/L after costs | **−$1,113.42** | **−$696.66** | **−$1,818.68** |
| Total R | −20.63R | −28.28R | −71.01R |
| Avg R / trade | −0.033 | −0.182 | −0.184 |
| Win rate | 50.3% | 39.4% | 42.5% |
| Best session | 10-22 +65.77R (more than the whole total; total is negative) | 10-22 +4.67R | 10-12 +7.86R |
| **Avg R without best day** | **−0.173** (`1 day`) | −0.223 | −0.217 |
| Excluding 10-22 | −$2,482.52 / −86.40R | −$775.12 / −32.95R | −$1,939.23 / −76.80R |
| Green days | 3 / 14 | 5 / 14 | 3 / 14 |
| M1 (3 green in a row) | not reached (longest 1) | reached 10-15, streak 10-13 to 10-16 = 4, but on 1-4 trades/day worth +$1.50 to +$28 | not reached (longest 1) |
| M2 (8 of last 10) | 3/10 | 5/10 | 3/10 |

Sensitivity checks:
- With the ambiguous recommendations counted as "not recommended" (exhaustion_short and NS2 stay):
  - CF-A: −$661.50, −26.18R, avg −0.150, 3/14 green, longest streak 2.
  - CF-B: −$1,768.28, −68.01R, avg −0.164.
- CF-B without the twin-held what-ifs: −$1,844.54, −72.55R.

### Per-decision attribution
"Owner − Claude" is actual minus counterfactual for each departure from Claude's recommendations. Positive means the
owner's call added P/L.

| Owner decision that departed from Claude | $ | R | Trades |
|---|---|---|---|
| 10-15 promote RW5-FD / RW3-FD / MF3-FD (Claude: nothing met the bar) | **+1,074.74** | **+39.52** | 137 |
| 10-19 promote MF2-FD (no recommendation; net of 2 twin-held MF2 what-ifs) | **+402.88** | **+28.90** | 28 |
| 10-19 promote NS3-FD (Claude P5: "wait") | **−484.71** | **−11.97** | 32 |
| 10-20 promote L3-fromopen-FD (Claude: Graveyard list) | −192.05 | −7.07 | 23 |
| 10-20 promote CWT14-pdl-p10-lowvol (no recommendation) | −101.18 | +1.29 | 38 |
| 10-11 demote orb20_a + intraday_momentum (Claude: keep / no view) | +9.62 | +0.57 | 30 |
| 10-19 promote MF4-FD (net of 12 twin-held MF4 what-ifs) | −4.04 | −0.87 | 24 |
| CF-A only: 10-08 add MF1-5 + NS1-5 | −1,045.70 | −41.07 | 214 |
| CF-A only: 10-09 add RW6G1 | −102.18 | −3.21 | 3 |

**Top 5 by $ impact:**
1. RW5/RW3/MF3-FD promotion: +$1,075 (owner right).
2. MF1-5/NS1-5 adds: −$1,046 (owner wrong; CF-A only).
3. NS3-FD promotion: −$485 (Claude right).
4. MF2-FD promotion: +$403 (owner right).
5. L3-fromopen-FD promotion: −$192 (Claude right).

**One-big-day caveat.** Most of the gain from the owner's promotions comes from 10-22:
- RW5-FD, RW3-FD and MF2-FD together made +$1,510 in total, and most of it on 10-22. Actual Primary on 10-22 was
  +$1,369.10 / +65.77R.
- Without 10-22, actual Primary is −86.4R against −76.8R for CF-B. On every other session, the owner's departures
  combined lost about 9.6R against Claude's lineup.
- RW5-FD, RW3-FD and MF3-FD all had negative two-year backtests (−0.058 to −0.071R) when they were promoted.

**Moves both made** (no difference between the columns): what each setup did after it left Primary, in any account, at
$16.79/R.
- Heat fades: heat_fade_short −35.18R (≈ −$591) and heat_fade_long −37.19R (≈ −$624) after demotion. These are by
  far the most valuable moves.
- NS3, MF5 and MF3-FD: small losses avoided.
- exhaustion_short +2.09R, NS2 +0.91R, MF3 +0.83R and L3 +1.98R: small gains given up.
- RW6G1: 0 trades after its move.

## Caveats (big)
1. **Caps and blocks were not re-simulated.** Shared slots, lot caps, "already in symbol" and setup_order were not
   re-run. Without the -FD promotions, the windowed MF/NS setups would have had more symbols and slots. Only the
   "twin held" what-ifs (14 trades) are added. "Lot cap" and other skips are not.
2. **Fills differ across accounts.** orb20_a and intraday_momentum come from Testing 1 at Testing 1's fills, converted
   at Primary's median $/R. Testing 1 caps were higher.
3. **Mixed dollar basis.** Trades from Primary use real $; trades from other accounts use R × $16.79. Primary's
   realised $/R varies a lot. For example, orb20_a lost −1.39R but −$250 in Primary. **R is the cleaner comparison.** CF-A
   is ahead of actual in $ (+$417) but behind in R (−7.65R).
4. **Split-ticker copies.** From 10-21 Testing 1/2 run some setups on half-universe copies. orb20_a and
   intraday_momentum had no split copies. Setups that left Primary and were split are not used in either
   counterfactual.
5. **Missing sessions.** Setups that did not trade anywhere that day contribute 0. orb20_a and intraday_momentum have
   no 10-12 trades in Testing 1. intraday_momentum never fired in Primary because of a timing bug fixed 10-12.
6. **Unknown future reviews.** Claude's later reviews of orb20_a and intraday_momentum are unknown, because Claude never
   reviewed them for Primary again. CF-A and CF-B keep them through 10-23.
7. **Ambiguous recommendations** (exhaustion_short, NS2) are counted as recommended in the base case. The strict
   variants are listed above.
8. **Small sample.** 14 sessions of paper trading cannot separate skill from luck. Every setup here has a negative or
   failed two-year backtest except where noted. Paper fills are not real fills.

## Verdict
Following only Claude's recommendations would **not** have left Primary better off on the measure that matters:
- **CF-B, the realistic reading (owner's probation adds kept):** −$1,819 / −71.0R, against actual −$1,113 / −20.6R.
- **CF-A, strict since 10-06:** loses less money (−$697) on a quarter of the trades, but is worse per trade
  (−0.18R against −0.03R).
- The owner's lead comes almost entirely from 10-22, which RW3-FD, RW5-FD and MF2-FD carried. Without that day the two
  are close (−86.4R against −76.8R for CF-B), and actual Primary's avg R without its best day is −0.173.
- Claude's demotions were right on balance, especially the heat fades and NS3-FD. Claude's caution on promotions cost
  money once (RW3/RW5/MF2-FD) and saved money twice (NS3-FD and L3).

Educational only — not financial advice.
