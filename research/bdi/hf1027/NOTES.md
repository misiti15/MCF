Educational only — not financial advice.

# BDI 2026-10-27 (evening): high-frequency setups, and Coil Under the High (4 bars)

Owner question: "Do not move Coil Under the High - 4 bar (CWT12-coil-k4-long, Testing 2) yet. Let's try one more day.
For some reason I am drawn to setups that can trade that many times in a day. What can we learn from this? Are there any
tweaks at all that can be made to these high frequency setups?"

**Scope and counts.** Live = paper trades from the five journals (Primary, Testing 1, Testing 2, Graveyard, Setup
Generator), copied read-only from the `mcf-data*` state branches; sessions 2026-10-09..10-27 (13), 8,745 trades, 122 setups.
Two-year = open history 2024-09..2026-10-07 through the `top5_1021/scan_1021.py` harness (coil kernel parity-checked
there); **the locked block 2024-11..2025-02 was never loaded** (asserts in `scan_hf.py` / `eval2y.py`). **No holdout was
scored. No config, setup, exit or engine file was changed.** Costs are in everywhere: live = journal `pnl_adj` / $ risk;
replays and two-year = the backtest cost model (1c + 1 bp each side, +2c on stops, target exits free).

**Configurations tried in this study: 52.** Two-year: 5 (coil-k4 targets 0.5 / 0.75 / 1.0R without the scale-out; parent
with cost floor 5% / 8%). Live what-ifs: 39 (3 alternative targets × 13 half-R HF setups), 2 cost floors across HF,
3 cost floors on coil-k4, 3 daily-stop levels. Plus ~25 descriptive splits (hour, burst, day rank, stop width, exit
reason, sequence, lot), so some splits will look strong by chance. Coil-k4 lineage now N = 230 (top5_1021) + 12 (bdi1026)
+ 5 = **247**, two-year bar t ≥ 3.32.

## Failures first

1. **High trade count is not an edge.** Of 76 setups with ≥ 3 live sessions, the 13 that trade 20+ times a session are
   **0 of 13 positive** (trade-weighted −0.127R, −635R total); 10-20/session 3 of 11 positive (−0.138R); 3-10/session
   9 of 29 (−0.082R); < 3/session 11 of 23 (−0.088R). Spearman(trades/session, avg R) = −0.14, but
   Spearman(trades/session, |total R|) = **+0.78**: frequency multiplies whatever the per-trade edge is. With a
   −0.08R edge, 29 trades a day is −2.3R a day.
2. **None of the 3 profitable HF setups survives the one-big-day check.** All three have their best session > 100%
   of total R, and without it they are negative:
   - Generated: ORBfailUp MID long `GEN-261021-06-ORBfailUp-Gapge1p2-MID-BRopgt0p5-hold-long` (Gen): +0.336R → −0.058R (share 106%, 3 sessions).
   - Gap-Down Recovery Fade (all day) `L3-gap-slope-fromopen-FD` (Testing 1): +0.140R → −0.047R (share 120%).
   - Failed Prior-Day-Low Break Long (0.1 ATR, low volume) `CWT14-failbrk-pdl-p10-lowvol-long` (Testing 2): +0.030R → −0.006R (share 119%).
3. **Wider targets fail for the coil on two years** (all three worse than the parent, t of delta −2.4 to −4.1; a wider
   target only makes the up-day / down-day split bigger). Live replay agrees for half-R HF setups as a group
   (−0.162 → −0.146 / −0.158R at 0.75 / 1R). Not proposed.
4. **Coil-k4 has no re-entry or lot stacking to cap.** All 349 trades are the first coil-k4 trade in their symbol that
   day (max seq 1, max lots 1). Its 29 trades a session come from many symbols firing together, not from refires. The
   burst-skip idea already failed on two years (bdi1026, 0 of 12). The only refire setup in the HF group is
   `L3-gap-slope-fromopen-FD`, and its repeats are its *best* trades (+0.227R vs +0.004R for first entries), so a
   repeat cap is not supported.
5. **The live replay runs about 0.03-0.05R worse than the journal** (model costs vs paper fills; 96-97% sign
   agreement). Read the replays as deltas between settings, not as levels.

## 1. The high-frequency setups (≥ 10 live trades per traded session, ≥ 3 sessions): 24 setups, 6,477 trades

`hf_table_out.txt`, `hf_setups.csv`. Live paper; avgR after costs; ex-best = avg R without the best session; t = day-clustered.

| setup (display name) | id | account | trades | sess | /sess | win | BE win | avgR | ex-best | best share | t |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Generated: ORBfailUp MID long | GEN-261021-06-ORBfailUp-Gapge1p2-MID-BRopgt0p5-hold-long | Gen | 37 | 3 | 12.3 | 59.5% | 26.5% | +0.336 | −0.058 | 106% **1 day** | 0.92 |
| Gap-Down Recovery Fade (all day) | L3-gap-slope-fromopen-FD | T1 | 200 | 11 | 18.2 | 59.5% | 49.1% | +0.140 | −0.047 | 120% **1 day** | 0.71 |
| Failed PDL Break Long (0.1 ATR, low vol) | CWT14-failbrk-pdl-p10-lowvol-long | T2 | 172 | 12 | 14.3 | 69.8% | 66.3% | +0.030 | −0.006 | 119% **1 day** | 0.46 |
| Failed Prior-Day-Low Break Long | CWT14-failbrk-pdl-p10-long | T2 | 310 | 12 | 25.8 | 66.5% | 67.0% | −0.039 | −0.098 | – | −0.31 |
| (no display name) | RW7-gapdn-bounce-early-short-FD | T1 | 264 | 12 | 22.0 | 50.4% | 52.3% | −0.043 | −0.108 | – | −0.55 |
| Generated: ORBfailDn LUNCH long | GEN-261020-05-ORBfailDn-VWAPcrossesge4-SMA20dlem0p31-LUNCH-SPYgt0p25-holdtr-long | Gen | 44 | 4 | 11.0 | 45.5% | 48.1% | −0.050 | −0.114 | – | −0.49 |
| **Coil Under the High (4 bars)** | **CWT12-coil-k4-long** | **T2** | **349** | **12** | **29.1** | **64.5%** | **68.9%** | **−0.078** | **−0.109** | – | **−0.75** |
| Failed PDL Break Long (shallow) | CWT14-failbrk-pdl-p05-long | T1 | 541 | 12 | 45.1 | 61.9% | 66.4% | −0.089 | −0.129 | – | −0.88 |
| (no display name) | heat_fade_short-FD | GY | 481 | 12 | 40.1 | 47.0% | 52.3% | −0.095 | −0.147 | – | −0.78 |
| Failed ORL Break Long (low volume) | CWT14-failbrk-orl-p10-lowvol-long | GY | 315 | 12 | 26.2 | 64.1% | 69.4% | −0.108 | −0.136 | – | −2.25 |
| Failed ORL Break Long (0.1 ATR) | CWT14-failbrk-orl-p10-long | GY | 346 | 12 | 28.8 | 63.6% | 69.1% | −0.113 | −0.138 | – | −2.26 |
| Failed ORL Break Long (0.05 ATR) | CWT14-failbrk-orl-p05-long | GY | 640 | 12 | 53.3 | 61.1% | 68.5% | −0.123 | −0.158 | – | −2.86 |
| Failed PDL Break Long (0.05 ATR, low vol) | CWT14-failbrk-pdl-p05-lowvol-long | T2 | 347 | 12 | 28.9 | 59.4% | 66.8% | −0.129 | −0.163 | – | −1.60 |
| Opening-Range Low Sweep Reversal | LIQ-orl-sweep-open15-s25-long | GY | 218 | 11 | 19.8 | 39.9% | 49.4% | −0.155 | −0.272 | – | −1.09 |
| (no display name) | ST2-slope20up-long-am-t05s1-FD | GY | 126 | 11 | 11.5 | 49.2% | 62.4% | −0.166 | −0.192 | – | −2.50 |
| Failed ORL Break Long (0.05 ATR, low vol) | CWT14-failbrk-orl-p05-lowvol-long | GY | 569 | 12 | 47.4 | 59.6% | 70.3% | −0.178 | −0.212 | – | −2.88 |
| Failed PDH Break Short (0.1 ATR) | CWT14-failbrk-pdh-p10-short | GY | 287 | 12 | 23.9 | 59.2% | 69.8% | −0.185 | −0.251 | – | −1.82 |
| Early Sellers into a Pop (all day) | MF3-open-flowsell-rsi5hi-FD | T1 | 124 | 12 | 10.3 | 47.6% | 57.8% | −0.195 | −0.239 | – | −1.38 |
| Failed PDH Break Short (0.05 ATR, low vol) | CWT14-failbrk-pdh-p05-lowvol-short | GY | 293 | 12 | 24.4 | 56.3% | 68.6% | −0.196 | −0.216 | – | −2.33 |
| Failed PDH Break Short (low volume) | CWT14-failbrk-pdh-p10-lowvol-short | GY | 143 | 11 | 13.0 | 55.2% | 67.5% | −0.200 | −0.261 | – | −2.48 |
| Coil Under the High (6 bars) | CWT12-coil-k6-long | GY | 101 | 10 | 10.1 | 33.7% | 38.4% | −0.213 | −0.329 | – | −1.30 |
| (no display name) | RW2-exhaustion-noon-adv150-short-FD | GY | 243 | 12 | 20.2 | 37.0% | 54.6% | −0.339 | −0.406 | – | −2.48 |
| Morning Bounce Fade | heat_fade_short | GY | 162 | 12 | 13.5 | 38.3% | 58.0% | −0.350 | −0.399 | – | −2.07 |
| (no display name) | heat_fade_long-FD | GY | 165 | 12 | 13.8 | 31.5% | 55.6% | −0.385 | −0.471 | – | −1.78 |

(Accounts are where each setup runs now per `docs/live/assignments.json`; records are merged across accounts by setup
name, as the dashboard does. coil-k6 moved to the Graveyard on 10-27.)

## 2. What the profitable vs unprofitable HF setups share (live)

| group | setups | trades | avgR | median target | median stop width | win | reach +1R | repeat entries | stacked lots | long |
|---|---|---|---|---|---|---|---|---|---|---|
| profitable | 3 | 409 | +0.111 | 0.75R | 137 bps | 63.8% | 16.9% | 30% | 25% | 51% |
| unprofitable | 21 | 6,068 | −0.146 | 0.55R | 82 bps | 55.4% | 6.4% | 0% | 0% | 67% |

- **Half-R targets dominate the HF list.** 13 of 24 HF setups (4,438 trades) set a target ≤ 0.6R: the CWT14 failed-break
  family, both coil setups' parents and ST2. They win 60-70% of the time and still need 66-70% because an average win is
  only +0.42-0.48R against an average loss of about −1.0R. Every one of them is below its break-even win rate, except
  pdl-p10-lowvol, which beats it by 3.5 points on the back of one day.
- **Costs take a bigger bite the tighter the stop.** On the half-R HF trades, entry-side cost (1c + 1 bp) as a share
  of R vs live result (`costfloor_out.txt`): ≤ 3% −0.106R, 3-5% −0.093, 5-8% −0.101, 8-12% **−0.181**, > 12% **−0.398**
  (n 1,571 / 1,213 / 1,004 / 453 / 197). Across all HF trades by stop-width quintile: < 50 bps −0.210R … > 147 bps −0.071R.
  The modelled round-trip cost is about 0.10R per trade on the half-R setups, roughly 20-25% of an average win.
- **Repeats and stacking** exist only in L3-gap-slope-fromopen-FD (61% repeats, 52% stacked), and there they are the
  better trades. Elsewhere the HF count is breadth, so a repeat cap has nothing to bite on.
- **Exits:** the losers are full stops (−1.12R avg, 2,161 trades), not give-backs: only 6.4% of unprofitable-HF trades
  ever reach +1R, and 17-25% of each setup's trades are losers that never reached +0.2R.
- **Time of day:** the profitable three made their R between 10:00 and 12:59; the unprofitable group loses in every hour
  and worst at 09:xx (−0.229R, 719 trades).
- Profitable HF setups are not "more frequent" (12-18/session vs up to 53 for the worst); trade count sorts nothing.

## 3. Coil Under the High (4 bars) `CWT12-coil-k4-long`: where the loss comes from (`coil_out.txt`)

Live (Testing 2): 349 trades, 12 sessions, 64.5% win, −0.078R after costs (−27.3R); avg win +0.426R, avg loss −0.993R,
so break-even is **70.0%** on R after costs (68.9% on the journal R). Two-year: parent −0.061R/trade (n 44,505, 104.7/day,
t_day −6.0; up sessions +0.045, flat −0.108, down −0.182; +0.005R over the same-minute random control).

1. **Two sessions are the whole loss.** 10-16 (−15.5R, 22 trades, 27% win) and 10-26 (−29.8R, 52 trades, 31% win) =
   −45.3R. The other 10 sessions: **+18.0R on 275 trades (+0.065R)**. Without the best day (10-23, +7.3R) it is −0.109R.
   That is the market-direction bet bdi1026 found on two years: a long that wins up sessions and loses down sessions
   in bursts. The losers mostly never worked (80 of 124 never reached +0.2R).
2. **Cost drag:** the journal shows +0.028R entry slip vs the signal price + 0.018R stop extra = **0.046R/trade**. The
   backtest cost model on the same trades is 0.074R. The fill sits a median 4.1 bps above the signal price, so the
   half-R target is really **0.435R** of the fill-to-stop risk. Before costs the setup is −0.032R; costs make up 11-17%
   of an average win.
3. **Wider target:** live replay −0.106 (as live) / −0.109 (0.5R) / −0.132 (0.75R) / **−0.085 (1R)**, with t of the
   delta vs live −0.81 / +0.51. That is noise: 36% of trades reached +1R before the stop. On two years
   (`eval2y_out.txt`) every wider target is worse: 0.5R without the scale-out −0.074, 0.75R −0.081, 1R −0.087, against
   the parent's −0.061 (t of delta −4.1 / −2.6 / −2.4). The live 0.35R scale-out is the best of these, consistent with
   top5_1021 (R0 −0.013, t −3.5). CWT package B already scored t1s1 / t1s05 / S geometries: all worse.
4. **First vs repeat trades:** none; every trade is the first coil-k4 trade in its symbol that day. By order in the day:
   the first 10 trades −0.045R, 11-20 −0.010, 21-40 −0.170, 41+ −0.061. Bursts of 10+ entries in one poll: 65 trades
   −0.452R, all of them on the bad days. Burst-skip already failed on two years (bdi1026).
5. **Time window:** live 10:15-10:44 −0.023R (138), 10:45-11:14 +0.050 (116), **11:15-11:30 −0.315 (95)**. Two years
   does not support cutting the late part: 11:15-11:30 −0.052 vs 10:15-10:44 −0.079, and top5_1021's "until 11:00" was
   worse (−0.067). The live late window is the 10-26 burst.
6. **Tight stops (cost > X% of R):** live entry-side cost/R ≤ 3% −0.018R (167), 3-5% −0.163 (83), 5-8% −0.048 (67),
   8-12% −0.317 (29). Two years: ≤ 3% **−0.027R** (n 26,446; random control −0.064), 3-5% −0.071, 5-8% −0.135,
   8-12% −0.211, > 12% −0.386. This is the one clean, monotone pattern, and it shows on both live and two years.
   It does not make coil-k4 positive: a 5% floor gives −0.040R on two years (down sessions −0.163).

**Answer for coil-k4:** the per-trade edge is negative on two years and live, after costs. The live record is a
regime split (+0.065R on 10 ordinary sessions, −0.61R/trade on 2 down-burst sessions). One more day can only add one
more sample of that split. No target or window tweak fixes it, and a cost floor only makes the loss smaller.

## 4. Tweak candidates (proposals only; NOT appended to the backlog)

Two candidates and one failed record. Each must go through the backlog gates (`mcf/research/backlog.py`) and the
locked holdouts before anything changes live.

**A. Minimum stop width for half-R HF setups: skip an entry when the entry-side cost (1c + 1 bp) exceeds 5% of R.**
- Live: on 4,438 half-R HF trades it keeps 63%; kept −0.100R vs dropped −0.158R; day-clustered t of the daily
  R change +3.30; dropped trades worse than kept in 10 of 13 setups. At 8%: keep 85%, dropped −0.247R, t +2.63.
  Coil-k4 live: kept −0.066 vs dropped −0.109 (5%).
- Two years, coil-k4 only: 5% floor −0.040R vs −0.061 (delta +0.027, t +12.0; train −0.031 / valid −0.048; down
  sessions still −0.163). 8% floor −0.051 (delta +0.013, t +11.8). Excess over random rises from +0.005 to +0.025R.
- Configurations tried: 2 (two years) + 5 (live). Not yet run on the CWT14 family on two years; that is the next step.
- **Caveat:** it reduces the loss and does not create an edge. Every kept group is still negative.

**B. A per-setup daily loss stop of −2R for HF setups in Testing 1 / Testing 2 (the Graveyard already runs one).**
- *Lead note:* Testing 1/2 ran this stop until the owner switched it off on 2026-10-22 (ST-A: testing runs like Primary). Not appended to the backlog; shown for the record only.
- Live replay (`daystop_out.txt`; no new entries once that setup's *realized* R that day is ≤ −X): all HF trades
  −841R → −610R at X = 2 (t +2.51, 11 sessions better, 2 worse), −655R at X = 3, −750R at X = 5. Average per trade
  −0.130 → −0.112R. Graveyard setups already run a −2R stop from 10-21, so part of their record is already capped and
  the replay understates their effect.
- **It barely helps coil-k4** (−27.3 → −24.3R): its burst losers are all entered before the first stop is realized.
- Two years: not run (the scan has no per-trade exit times). Configurations tried: 3 (live).
- This is a risk control, not an edge. Each setup would still have to stand on its own record.

**C. (failed, for the record) Wider target on half-R HF setups (0.75R / 1R).** Coil-k4 two years: 3 of 3 worse
(t −2.6 / −2.4). Live replay on 13 setups: mixed; overall −0.162 → −0.146 / −0.158R; 39 configurations. Not proposed.

Proposed backlog lines (for the lead to append; `status` proposed, not run through the gates):

```json
{"added": "2026-10-27", "source": "BDI hf1027 (research/bdi/hf1027/NOTES.md)", "module": null, "variant": null, "id": "hf1027-costfloor-halfR", "title": "Half-R HF setups: skip entries whose entry-side cost (1c + 1 bp) exceeds 5% (alt 8%) of R", "category": "filter", "parent": null, "tags": ["hf1027", "bdi", "testing1", "testing2", "graveyard", "cost"], "hypothesis": "Tight-stop entries lose to costs: live half-R HF trades with cost/R > 5% -0.158R vs -0.100R kept (t +3.30); coil-k4 two years <=5% -0.040R vs parent -0.061R (delta t +12). Reduces losses; does not by itself create an edge.", "status": "proposed", "configs_tried": 7, "notes": "Two years run for CWT12-coil-k4-long only (locked block not read, no holdout). Next: CWT14 failbrk family on two years; plateau check at 3/5/8%."}
{"added": "2026-10-27", "source": "BDI hf1027 (research/bdi/hf1027/NOTES.md)", "module": null, "variant": null, "id": "hf1027-hf-daily-stop-2R", "title": "HF setups in Testing 1 / Testing 2: per-setup daily loss stop at -2R realized (as in the Graveyard)", "category": "risk", "parent": null, "tags": ["hf1027", "bdi", "testing1", "testing2", "risk"], "hypothesis": "Bad days for HF setups come in bursts; stopping a setup's new entries after -2R realized cut live HF losses -841R -> -610R over 13 sessions (t +2.51), avg -0.130 -> -0.112R. Risk control, not edge; little effect on burst-entry setups (coil-k4 -27.3 -> -24.3R).", "status": "proposed", "configs_tried": 3, "notes": "Live replay only; two-year test needs exit times per trade (scan harness extension)."}
{"added": "2026-10-27", "source": "BDI hf1027 (research/bdi/hf1027/NOTES.md)", "module": null, "variant": null, "id": "hf1027-halfR-wider-target", "title": "Half-R HF setups: target 0.75R / 1.0R instead of 0.5R", "category": "setup", "parent": "CWT12-coil-k4-long", "tags": ["hf1027", "bdi", "coil"], "hypothesis": "Some losers reached +1R first, so a wider target might convert win rate into R.", "status": "failed", "configs_tried": 42, "notes": "Coil-k4 two years: 0.5R no scale-out -0.074, 0.75R -0.081, 1R -0.087 vs parent -0.061 (delta t -4.1/-2.6/-2.4). Live replay 13 half-R HF setups: -0.162 -> -0.146/-0.158R, mixed per setup."}
```

## 5. Plain-language conclusion

- **Trading many times a day is not an edge in itself. It is a magnifier.** It makes a good per-trade edge show up fast,
  and a bad one cost money fast. In our data the busiest setups are the worst: 0 of 13 setups with 20+ trades a session
  is positive. The three HF setups that are up are each carried by a single day.
- The pull of HF setups is real but misleading. Lots of trades and a 60-70% win rate *feel* like proof. With a half-R
  target and a 1R stop, though, 64.5% wins is a loss, because the bar is about 70%. Roughly 0.05-0.10R of costs on every
  trade is a big slice of a 0.43R win.
- **Coil-k4** is not "almost there". It is a bet on the market going up: +0.065R/trade on 10 ordinary sessions and −45R
  on 2 down-burst sessions; on two years +0.045R in up sessions and −0.182R in down sessions. One more day is the
  owner's call and costs little in a paper account. Whichever way it goes, it cannot change the two-year answer, and the
  one-big-day check shows −0.109R without its best day.
- **What would make an HF setup worth having:** a per-trade edge that is positive after costs on two years in *both* up
  and down sessions, a stop wide enough that costs stay under ~5% of R, and a record that is not carried by one day.
  Only then does high frequency become an advantage: more trades shrink the noise around a real edge faster.

## Files

`build.py` (all live trades → scratch `all_trades.parquet`), `hf_table.py` → `hf_table_out.txt`, `hf_setups.csv`,
`all_setups.csv`; `fetch.py` (SIP 1-min bars for HF symbol-days, read-only market data); `replay.py` → `replay_out.txt`,
`replay_targets.csv`; `coil.py` → `coil_out.txt`; `costfloor.py` → `costfloor_out.txt`; `daystop.py` → `daystop_out.txt`;
`scan_hf.py` (two-year coil-k4, 4 variants) and `eval2y.py` → `eval2y_out.txt`, `results2y.csv`.
Run: `python build.py <scratch>` (with `<scratch>/<p|t1|t2|gy|gen>/journal.db` from `git show origin/mcf-data*:journal.db`),
then `hf_table.py`, `fetch.py`, `replay.py`, `coil.py`, `costfloor.py`, `daystop.py` with `<scratch>`; `scan_hf.py`, then `eval2y.py`.

Educational only — not financial advice.
