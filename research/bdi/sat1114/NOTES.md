# BDI Saturday deep run 2026-11-14 (week 11-09..11-13)

*Educational only — not financial advice. Live numbers are **paper** trades, R after costs (journal run 1, `pnl_adj` / $ risk);
$ = Alpaca day P/L (each state branch's `reports/pl_reconcile/<date>.json`). History = two-year lab trade lists with
production costs. The locked block 2024-11-01..2025-02-28 was never read (absent from the input file, asserted;
`MCF_HIST_ALLOW_LOCKED` never set). No holdout scored. No config, setup, exit or assignment change. `PLAN.md` was committed
(b6a381520) before anything was scored.*

**Configurations tried tonight: 4 (give-back G1-G4; BURST / give-back lineage 36 → 40, bar 2.72). 0 pass → no proposal,
no new owner decision.** Rule-18 rework round and the new-idea scan: skipped tonight (time; nothing new queued for them).

## Rule changes inside the window (research/ledger.jsonl): read every number with these in mind
- **11-09/11-10 EXPO1109** temporary GEN moves (reverted after the 11-10 close).
- **11-11 TEAM-6** in Primary (NM-ETF, NS5, L3-fromopen, RW3, RW5, ST7; frozen to 11-13). Primary 11-09/11-10 = the old roster
  (MF2-FD, MF4-FD and others), so Primary's week mixes two rosters.
- **11-12 LR2/LR3/LR8**: R after costs everywhere, new live cost model (~−0.04R per trade vs the old basis, so R before /
  after 11-12 is not like-for-like), Primary −2R latch and −20R halt count R after costs.
  **On Deck built** (the former Testing 1 account); **Testing D/E/F live** (2 sessions); Testing A back to the full universe;
  generic per-setup cap 30 in B-F; account halt 300R in On Deck / Testing / Gen.
- **11-13** Primary late start 09:46 (manual dispatch); Gen / Graveyard close-out glitch (out of scope here; excluded from records).
- Account names: Testing A = testing2 (old Testing 2), B = explore1 (old Explore 1), C = livelab (old Live Lab).

## 1. Discover workflow
**Not run yet**: scheduled Sat 14:17 UTC, no run listed at 15:50 UTC (last success 11-07, run 42383860037, 36 min). GitHub's
cron has run 30-40 min late before; today it is > 1.5 h. Bar cache / backlog re-test therefore still at 11-07.

## 2. Weekly give-back review (`giveback.py` → `giveback_week.csv`, `giveback_out.txt`, `caps_week.csv`, `giveback_setups.csv`)
Curve = the runner's per-poll mtm snapshots (realised + open lots' marks); peak = the day's highest marked total;
give-back = peak − close. Peak→close split: lots open at the peak (booked R − their mark at the peak), entries after the peak.

| account | 11-09 | 11-10 | 11-11 | 11-12 | 11-13 | week give-back | open winners | entries after peak | twins | late flatten |
|---|---|---|---|---|---|---|---|---|---|---|
| Primary | +0.4 → −18.1 | **+9.5 (10:52) → −31.3** | +3.9 → −26.6 | +43.7 → +39.9 | +0.2 → −1.4 | 95.2R | −23.7 | **−68.8** | −8.7 | −11.4 |
| On Deck | +3.7 → −1.7 | **+1.2 → −44.9** | +3.5 → −28.5 | +40.4 → +40.2 | +2.6 → −30.3 | 116.6R | −37.5 | **−71.1** | −11.3 | −19.9 |
| Testing A | +6.6 → −5.1 | **+14.9 (12:42) → −27.1** | +0.2 → −17.7 | +12.1 → +6.5 | +8.4 → −1.3 | 86.9R | **−43.9** | −28.9 | −6.9 | −27.8 |
| Testing B / C / D | small | | | | | 3.3 / 4.0 / 7.7R | | | | |
| Testing E | – | – | – | **+12.4 (10:10) → −20.4** | +4.8 → −21.1 | 58.7R | **−57.6** | +3.5 | 0 | −1.5 |
| Testing F | – | – | – | +4.8 → −17.5 | +2.3 → −2.9 | 27.4R | −10.6 | −15.0 | 0 | −5.4 |

- **Biggest give-back days.** On Deck 11-10 (46.1R: 124 entries after a 09:57 peak, RW7-FD −28.7R of them), Testing A 11-10
  (42.0R: RW3S-FD shorts open at the 12:42 peak stopped together, −31.4R), Primary 11-10 (40.8R: peak +9.5R at 10:52, then
  80 new entries −39.2R; RW5-FD −12.5R, MF2-FD / RW3-FD the rest) and Testing E 11-12 (32.8R: open GEN-261027-07 shorts −31.8R).
  SPY (% from open): 11-09 +1.5 close (shorts squeezed all day); 11-10 high +0.55 at 10:09, low −0.37 at 12:42, close +0.37
  (the afternoon recovery stopped the post-peak shorts); 11-12 high +1.19 at 11:22; 11-13 −0.78.
- **Primary's give-back was entries after the peak (−68.8R of 95), not open winners (−23.7R).** It was the old roster on
  11-09/11-10 (MF4-FD −17.1R after the peak on 11-09; RW5-FD / MF2-FD / RW3-FD on 11-10). TEAM-6 days: 11-11 30.5R
  (open L3 / RW5 lots −14.8R, entries after −12.2R), 11-12 3.8R, 11-13 1.7R. In Testing A / E the give-back was correlated
  stops of open shorts (RW3S-FD −57R over both accounts; now in the Graveyard from 11-16) — the burst problem again.
- **Latch and twin cap helped (Primary only; run-2 what-ifs of blocked signals, with costs).** Per-setup −2R latch: 63
  blocked, **net −20.2R avoided** (11-10 −19.0R: MF2-FD −6.9, RW5-FD −6.8, RW3-FD −5.3; 11-11 +1.0R of blocked winners; 11-12
  none; 11-13 RW3-FD latched at 15:52, nothing blocked after). Cost-in counting (from 11-12) has had no blocked signal to
  judge yet — 2 sessions, too few. Twin cap: 25 blocked, **net −17.6R avoided** (11-09 MF4 base twins −18.0R);
  On Deck 3 blocked, −1.2R. Neither is in Testing A-F, where most of the week's give-back sat.

### Proposals (PLAN.md; `sim_g.py` → `g_results.csv`, `g_setups.csv`, `g_families.csv`, `g_out.txt`)
Both act only on new entries after a give-back has started (open trades and exits untouched).
| config | 2y trades removed | TRAIN Δ (t / excess t) | VALID Δ (t / excess t) | VALID setups better / worse | families harmed | Primary book VALID Δ, give-back/day | live week Δ |
|---|---|---|---|---|---|---|---|
| G1 per-setup trailing latch 2R from the setup's day high | 14.9% | +6,739 (8.82 / 0.66) | +3,758 (5.87 / **0.22**) | 44 (+4,047R) / 30 (−289R) | NM, ST | +273R, 19.6 → 16.4 | **−23.4R** (Primary −27.1: L3-fromopen −29.3 on 11-12) |
| G2 same, 3R | 10.5% | +4,545 (7.16 / 0.25) | +2,672 (4.90 / **−0.14**) | 39 (+2,904R) / 14 (−232R) | ST | +75R, 19.6 → 18.2 | +1.1R (1 trade) |
| G3 account brake 10R from the day high | **57.2%** | +18,417 (9.05 / −1.15) | +11,527 (8.43 / **−0.08**) | 49 / 45 | GEN, NM, exhaustion | +223R, 19.6 → 15.4 | +17.6R (On Deck +11.8) |
| G4 account brake 15R | **48.0%** | +15,808 (8.46 / −0.83) | +10,009 (8.36 / **0.17**) | 48 / 46 | GEN, NM, exhaustion | −114R, 19.6 → 18.4 | +37.1R (On Deck +37.5) |
**All four fail.** Each looks large in raw Δ only because it trades less of a book that loses on average (lab mean −0.069R):
the excess over removing random trades at the setup's mean is ≈ 0 (t −0.14..+0.22 VALID). G1 also cuts this week's best winner
(L3-fromopen dipped 2R below its booked high on 11-12, then made +27R), which is what the owner does not want. The account
brakes remove half the two-year trades (the lab "accounts" hold 26-43 setups) and harm GEN / NM. Same verdict as BURST1/2
and sat1107 A1-A7: no entry rule cuts give-back on two years beyond trading less.

**What remains worth doing (optimism, not a proposal):** the give-back sits where setups were weak anyway (RW7-FD, RW3S-FD,
MF4-FD, GEN-261027-07 — all already moved / under review) — the setup moves did the job a rule could not. The open-winner
part (correlated short stops) is still unsolved; the cluster profit lock (`bdi1022-short-cluster-profit-lock`, parked)
is the one exit idea not yet scored on mtm snapshots — candidate for a future run once ≥ 10 snapshot sessions exist.

## 3. Week scorecard (`week.py` → `week_out.txt`, `week_scorecard.csv`, `week_setups_*.csv`)
| group | R | trades | avg R | Alpaca $ | green days (R) |
|---|---|---|---|---|---|
| **Primary** | **−37.5R** | 266 | −0.141 | **+$1,786.72** | 1/5 |
| On Deck | −65.1R | 443 | −0.147 | −$696.47 | 1/5 |
| Testing (all A-F) | −65.7R | 939 | −0.070 | −$793.48 | — |
| A / B / C | −44.6 / +16.3 / +6.8R | 542 / 49 / 30 | | −$426.84 / +$335.14 / +$226.53 | 1/5, 5/5, 4/5 |
| D / E / F (2 sessions) | +17.7 / −41.5 / −20.4R | 88 / 115 / 115 | | +$185.87 / −$897.90 / −$216.28 | 2/2, 0/2, 0/2 |

- **Primary: R and $ disagree** because the $ risk per trade rose with TEAM-6 (avg $29-53 on 11-09..11-11, $66-68 on 11-12/13):
  11-12 +39.9R = +$2,843; 11-09..11-11 −75.9R = −$952. By day R: −18.1 / −31.2 / −26.6 / +39.9 / −1.4. TEAM-6 3 days +11.8R /
  131 trades (+$2,060.59), without 11-12 −0.501R avg (`1 day`).
- **Primary best:** Gap-Down Recovery Fade (all day) (L3-gap-slope-fromopen-FD) +32.4R / 83 (avg +0.391; w/o best day +0.047,
  `1 day` 96%). **Worst:** Gap-Down Pop Fade (all day) (RW5-heat30-flowsell-rsi5pop-gapdn-short-FD) −23.5R / 56 (w/o best day
  −0.560); Early Sellers, Strong Heat (all day) (MF4-h40-open-flowsell-FD, old roster) −22.3R / 37; Gap-Down Pop Fade, Heavy
  Selling (all day) (RW3-gapdn-rsi5pop-flowsell-short-FD) −14.4R / 50.
- **On Deck best:** Gap-Down Bounce-off-Low Fade (all day) (L3-gap-slope-lowdist-FD) +19.0R / 33 (`1 day` 96%); Gap-Down Rebound
  Overbought Short (all day) (L3-gap-slope-rsi5hi-FD) +12.2R / 40 (`1 day` 108%, w/o best day −0.511). **Worst:** Gap-Down
  Early Bounce Short (all day) (RW7-gapdn-bounce-early-short-FD) −38.9R / 131 (→ Testing F from 11-16); Generated: Open Below-Prior-Low Buy (big bar)
  (GEN-261021-02-…-OPEN-SPYgt0p5-t1s1-long) −15.4R / 62; Early Sellers into a Pop (MF3-open-flowsell-rsi5hi) −8.7R / 19.
- **Testing best:** Failed Prior-Day-Low Break Long (0.1 ATR, low volume) (CWT14-failbrk-pdl-p10-lowvol-long, A) +18.7R / 90
  (w/o best day +0.162, 54% `1 day`); NS2 Short, SPY Up 0.5%, Not Friday (NM-RWN4-ns2-spyup05-notfri-short, F) +9.4R / 32 (one
  session); CWT14-failbrk-pdl-p10-long (A) +8.5R / 148. **Worst:** Gap-Down Heavy-Selling Short, no RSI condition
  (RW3S-gapdn-flowsell-short-FD; A −28.2R / 80 + E −17.2R / 77 = −45.4R / 157; → Graveyard 11-16); Generated: Lunch Failed
  Breakdown Buy (GEN-261020-05-…-LUNCH-SPYgt0p25-holdtr-long, F) −24.1R / 37; Generated: Morning Up-Stock Dip Short
  (GEN-261027-07-RSI14le35-FromOpenge2-AM-BRvwlt0p5-t1s1-short, E) −24.0R / 26.
- Testing D/E/F: 2 sessions only — too early to read; E's loss is two setups (RW3S, GEN-261027-07).

## 4. Plan for next week
- **Up-day / direction research re-anchored after 09:50** (owner rule 11-14): reference = the 09:50 state and the 09:30-09:50
  range; score readings by the return after the decision time; redo the compass / up-day benchmarks on that anchor.
- **Workbench** build + **arena rotation block 1 (Sun 11-15)** for the testing accounts (Testing A-F equal weight).
- **HK-FLAT-1113** fix (final state push before the job limit / successor adopts broker positions) before Monday; then
  **LEDGER-CHK** (pending: `python -m mcf.research.ledger check` on the week's moves).
- Reviews: **GY-RW6 On Deck review Mon 11-16**, **RW7 Graveyard review Wed 11-18**, **LATCH-CLOSE re-ask Fri 11-20**.
- **TEAM6-1116** decision pending (recommend keep, frozen to 11-20); give-back watch on the snapshot curves daily.
- Re-run the discover workflow check (not run at 15:50 UTC today).

Scripts: `giveback.py`, `sim_g.py`, `week.py` (scratch: journals from the state branches; snapshots read via `git show`).
Educational only — not financial advice.
