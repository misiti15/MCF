# SZ-PROOF - sizing by proof for Primary (owner 2026-10-27)

*Educational only - not financial advice. Paper results (live paper account), backtests and simulations are labelled
separately. NOTHING here is implemented: no config, engine or sizing change.*

Owner: size Primary trades by how well each setup has proven itself (0.5x new / 1x proven / up to 1.5x strongly
proven), with an automatic DRIFT monitor that steps size down when a setup's recent trades fall well below its own
record (down automatic, up only with the owner's OK). Total account risk cap unchanged. Worry: "tiering may just
balance out" (bigger and smaller positions cancelling).

## 0. Pre-declaration (written 2026-10-27 before any tiered replay was scored)

### 0.1 Data
- **Live (paper) replay:** every Primary trade in `origin/mcf-data:journal.db`, run_id = 1 (704 trades, 16 sessions
  2026-10-06..2026-10-27). R after costs = journal `pnl_adj` / $ risk (shares x |entry - stop|), as the nightly
  reviews. Flat = each trade exactly as it was taken ($ = pnl_adj). Tiered = the same trade times its multiplier
  ($ = multiplier x pnl_adj, R = multiplier x R). Exactly the same trades in both books.
- **Proof stream for a setup on session D (live):** that setup id's live paper trades in ALL accounts (Primary,
  Testing 1, Testing 2, Graveyard, Setup Generator journals, run_id = 1) dated strictly before D (the Primary bar
  merges accounts), plus its two-year backtest record from trades dated before 2026-10-06 (the first live session),
  so nothing dated on or after D is used.
- **Two-year replay:** the 8 setups in Primary from 2026-10-28 (docs/live/assignments.json), their live-shaped
  backtest trade lists on the open history (2024-10..2026-10-07 minus the locked block, which is never read), costs
  in (production costs, time-of-day entry costs, 3x on the extended tier) - built by
  `research/ops/late_entry1027/build_cache.py` (the gates1021 scan code). Proof for a setup on date D = its own
  backtest trades dated before D (walk-forward; every setup starts with no proof in Oct 2024). $ per 1R = $15.88,
  the median $ risk of a Primary live trade. Caps / slots / daily stop are not simulated (1 unit per trade).

### 0.2 Tier rule (T-main)
Per setup, at the start of each session, from the proof stream (n, avg R, avg R without its best session, win %,
break-even win % = avg loss / (avg win + avg loss)) and the backtest line:
- **1.5x strongly proven:** n >= 50, avg R >= +0.10, avg R w/o best day >= +0.05, win % > break-even, backtest avg R > 0.
- **1.0x proven:** n >= 30, avg R > 0, avg R w/o best day > 0, win % > break-even, backtest avg R >= -0.02 (not
  clearly negative) unless n >= 100 (a large live record may overrule it, as the Primary bar).
- **0.5x new / unproven:** everything else.
- In the two-year replay the proof stream IS the backtest record, so the separate backtest line is the same stream.
- A live setup with no two-year list (CWT / IDX / LD ... not covered by the lab harness): the backtest line counts
  as met for 1.0x (no evidence against) and as NOT met for 1.5x (1.5x needs a positive backtest).

### 0.3 Drift monitor
- Rolling last-20 trades of the proof stream vs the long-run avg R of all earlier trades in the stream (needs >= 40
  trades). Drift = last-20 avg < long-run avg - 0.30R AND last-20 avg < 0. On drift the setup drops one tier
  (1.5 -> 1.0 -> 0.5, floor 0.5x) from the next session, automatically.
- Any step UP (a new tier, or recovery after drift) takes effect only at the weekly review: the first session after
  a Friday (models "up only with the owner's OK"). Steps down take effect the next session.

### 0.4 Configurations (all counted, all reported)
V1 T-main + drift (headline); V2 T-main, no drift; V3 drift on last-30 instead of last-20; V4 no 1.5x tier
(0.5 / 1.0 only) + drift; V5 live-only proof (backtest line ignored) + drift; V6 backtest-only proof + drift.
6 configurations x 2 replays = **12 scored rows (N = 12)**; bar = max(1.5, sqrt(2 ln 12)) = **2.23** on the
day-clustered t of (tiered - risk-matched flat) per day. (In the two-year replay V5 = V6 = V1 by construction; they are
still counted.)

### 0.5 Metrics and the "balances out" test
For flat and tiered: total R and $, avg R per trade, max drawdown (daily closes), worst day, total without the book's
best day, and **R per unit of risk** (sum of multiplier x R / sum of multipliers). Tiering changes two things: how much
risk is deployed in total, and WHERE it is deployed. To separate them, the tiered book is also compared with a
**risk-matched flat** book (every trade at c = mean multiplier, the same total risk). If tiered - risk-matched flat is
not clearly > 0 (t below the bar), sizing by proof adds nothing beyond trading smaller or bigger overall: it
**balances out**. The gain vs flat is also reported without its best day (the day where tiered - flat is largest).

## Results (scored 2026-10-27, after section 0 was written)

**Configurations scored: 12** (6 rules x 2 replays), all reported below; bar t >= 2.23. Code `sizing_proof/replay.py`
-> `sizing_proof/replay_out.txt`, `sizing_proof/results.csv` (every row), `sizing_proof/tiers_live.csv` (V1 tier
per setup and session). Trade lists: `late_entry1027/build_cache.py` (scratch cache, not in git).

### Verdict first: it balances out
- **Against a flat book of the same total risk, tiering adds nothing** in 11 of 12 rows (tiered - risk-matched flat:
  live V1 -0.4R, t -0.19; two-year V1 +10.3R on 30,203 trades = +0.0003R/trade, t 1.13). R per unit of risk is the
  same as flat (live -0.026 vs -0.025; two-year -0.064 vs -0.065). Bigger and smaller positions cancel.
- **The headline "gain" vs flat is only trading smaller.** Primary's record is negative (live -17.6R / -$992 over 16
  sessions; the 8 current setups' two-year backtest -1,949R), and 94% (live) / 99% (two-year) of trades sit in the
  0.5x tier because few setups have proof. Half size halves the loss, the max drawdown and the worst day - any 0.5x
  flat cut does the same. Live V1: -$493 vs -$992, max DD -$1,131 vs -$2,263, worst day -$463 vs -$927 (10-15);
  two-year V1: -970R vs -1,949R, max DD -1,082R vs -2,163R, worst day -83.6R vs -167.1R. The +7.9R vs flat (live
  V1) is t 0.20 and turns negative without its best day (-6.7R).
- **The one row over the bar is not proof:** V5 (live-only proof, two-year line ignored) on live Primary: +22.8R /
  +$216 vs flat -17.6R / -$992; vs risk-matched flat +33.8R, **t 2.39 vs bar 2.23**. But it is 16 sessions and two
  setups: Gap-Down Pop Fade, Heavy Selling (all day) `RW3-gapdn-rsi5pop-flowsell-short-FD` and Gap-Down Pop Fade
  (all day) `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD` reached 1.0x on 10-19 (from their Testing records) and then
  had 10-22 (+65.8R flat book day). Best day 10-22 = 40% of the gain vs matched, 10-22 + 10-27 = 60% (**1-2 big
  days carry it**; without 10-22 +20.3R). The same rule on the two-year history (V5 = V1 there) balances out
  (t 1.13). It drops the owner's own "2-year backtest not clearly negative" line, and RW3-FD / RW5-FD backtest
  -0.071R / -0.060R. Not a pass in the sense of rule 19; noted as the thing to re-check on forward sessions.

### All 12 rows (R after costs; $ live = pnl_adj x multiplier, two-year = R x $15.88)
| Replay | Config | mean mult | flat R / $ | tiered R / $ | tiered - flat (t) | w/o best day | tiered - matched flat (t) | max DD flat / tiered | worst day flat / tiered |
|---|---|---|---|---|---|---|---|---|---|
| live Primary (704 tr, 16 s) | V1 T-main+drift20 | 0.53 | -17.6 / -$992 | -9.8 / -$493 | +7.9 (0.20) | -6.7 | -0.4 (-0.19) | -78.9R / -39.5R | -29.1R / -14.6R |
| live | V2 no drift | 0.53 | same | -9.8 / -$493 | +7.9 (0.20) | -6.7 | -0.4 (-0.19) | -78.9 / -39.5 | -29.1 / -14.6 |
| live | V3 drift last-30 | 0.53 | same | -9.8 / -$493 | +7.9 (0.20) | -6.7 | -0.4 (-0.19) | -78.9 / -39.5 | -29.1 / -14.6 |
| live | V4 no 1.5x | 0.53 | same | -9.8 / -$493 | +7.9 (0.20) | -6.7 | -0.4 (-0.19) | -78.9 / -39.5 | -29.1 / -14.6 |
| live | **V5 live-only proof** | 0.63 | same | **+22.8 / +$216** | +40.4 (1.89) | +25.8 | **+33.8 (2.39)** | -78.9 / -38.9 | -29.1 / -14.6 |
| live | V6 backtest-only proof | 0.51 | same | -10.1 / -$546 | +7.6 (0.19) | -7.0 | -1.0 (-0.73) | -78.9 / -40.9 | -29.1 / -14.6 |
| two-year 8 Primary (30,203 tr, 426 s) | V1 | 0.50 | -1,949 / -$30,950 | -970 / -$15,408 | +979 (4.61) | +895 | +10.3 (1.13) | -2,163 / -1,082 | -167.1 / -83.6 |
| two-year | V2 no drift | 0.50 | same | -975 | +974 (4.60) | +890 | +6.1 (0.60) | -2,163 / -1,088 | -167.1 / -83.6 |
| two-year | V3 last-30 | 0.50 | same | -974 | +975 (4.61) | +892 | +7.8 (0.78) | -2,163 / -1,086 | -167.1 / -83.6 |
| two-year | V4 no 1.5x | 0.50 | same | -970 | +979 (4.61) | +895 | +10.3 (1.13) | same as V1 | same |
| two-year | V5 (= V1 here) | 0.50 | same | -970 | +979 | +895 | +10.3 (1.13) | same | same |
| two-year | V6 (= V1 here) | 0.50 | same | -970 | +979 | +895 | +10.3 (1.13) | same | same |

(The two-year "tiered - flat" t 4.6 is the size cut on a losing book, not selection: the risk-matched row is the test.)

### Why so few trades get above 0.5x
- Live: with the two-year line in, only CWT14-failbrk-pdl-p10-lowvol-long (no two-year list -> counted as met for
  1.0x) reached 1.0x (from 10-26, 40 trades, -1.9R). RW3-FD / RW5-FD / MF2-FD / MF4-FD have positive live records but
  negative two-year backtests and < 100 live trades, so the Primary-bar line keeps them at 0.5x.
- Two-year: the 8 Primary setups' own walk-forward records are negative for almost the whole history (6 of 8 lose
  -0.04..-0.10R/trade); only NS1-rsidip-rsi5pop-long (+0.031R) and ST7-rsi50dn-long-pm-t1s1-FD (+0.024R) touch 1.0x,
  briefly. No trade was ever sized 1.5x. The drift monitor fired a few times (V1 vs V2: +5.2R on 30,203 trades), immaterial.

### Caveats
- 16 live sessions; per-day t on 16 points is fragile. Paper fills (fill-realism adjustments in pnl_adj stay on).
- Two-year: no slots / caps / daily stop simulated; survivorship as RESCORE.md; the history overlaps the first two
  live sessions (10-06, 10-07) only in the two-year replay, not in the live proof (live proof uses backtest < 10-06).
- The total-account risk cap is unchanged by design: tiering only redistributes, so in a capped book a 1.5x trade
  would crowd out others - not modelled, and with these results it would not matter.

### What it would take
Sizing by proof can only help once there are setups with real proof (live >= 50 trades, positive without their best
day, AND a two-year record that is not negative). Today Primary has none that clear all lines. Re-run this replay on
forward sessions (V1 and V5) at the weekly Friday review; nothing changes live.
