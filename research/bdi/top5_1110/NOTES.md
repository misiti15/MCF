# Top-20 conditions + top-5 execution tune, 2026-11-10 (nineteenth run): FAILED the Testing bar, 0 of 95; 25 variants beat their parent

*Educational only - not financial advice.*

- **Live** numbers are **paper** trades (rule 7): a diagnosis, not evidence. **History** numbers are **backtests** on
  the open two-year history: production + time-of-day costs, x3 on the extended tier, TRAIN (<= 2025-12) and VALID
  (2026-01..03, 07..09-15). The locked block (2024-11-01..2025-02-28) was **never loaded**. No holdout was scored,
  because nothing reached the Testing bar.
- **Data:** 2-year cache per `research/bdi/1104/DATA.md` (frames to 2026-11-04). Part A's two-year reads use the BDI
  1104 trade lists (`bt_lab1104`). Live trades fetched tonight (all 6 data branches, 10-06..11-10, 15,844 rows).
- **Reused, not redone:** tonight's nightly loop (`research/bdi/nightly1110/`) and BDI run (`research/bdi/1110/`): the
  midday flip-up, the latch-vs-open-book finding and MFX1 (flip exit, fails VALID) are theirs. This run did not re-test
  a flip exit on the book; it tested a per-setup 13:00 clock exit (G08) and an 11:00 window split (G11/G12) instead.
- **Configurations scored tonight: 95** (19 one-knob execution variants x 5 setups, pre-declared in `PLAN.md` before
  any row was scored). Part A bucket reads are descriptive and tune nothing: 11 dimensions x 20 setups live, 6 setups
  on two years.
- **Result: 0 variants meet the Testing bar. No DECISION, no Testing proposal, no Primary change** (the Wednesday
  Primary decision, TEAM-6, is handled by the separate 18:33 ET task).
- **Parity:** every parent equals the cached production R (mean |d| <= 0.00007R, 100% within 0.01R).
- config/, mcf/, docs/live/ and workflows untouched. 31 lines appended to research/backlog.jsonl: 30 tag `top5-tune`
  (5 grid lines parked, 25 beat-parent lines rework) and 1 Part A idea (tag `top20-conditions`).

**Rule changes inside the stats windows (research/ledger.jsonl effective dates).**
- *Part A live window, 10-06..11-10:* per-lot stacking (10-13), refire B (10-14), RW5/RW3-FD promoted (10-15), MF2/MF4-FD
  promoted, twin cap and -2R setup stop (10-20), Testing setup stop off (10-23), GX1 5-minute clock (10-27), Primary
  ~$4k (10-28), Primary -2R latch (10-29), CF + BAR90 in Testing (10-30), L3 pair -> Primary (10-30), moves 10-30..11-04,
  RW3S-FD into T2 (11-03), UNI1 top-500 pool in T2 (11-04), ROLL1 low-rep homes (11-05), **EXPO1109 temporary GEN moves
  into Testing 1/2 (11-09 + 11-10; reverted from 11-11)**, compass display from 11-09 (no trading effect).
- *Part B live window, 11-04..11-10:* PLAN.md section 1. No setup or exit change touched the 5 setups since top5_1104.

## Part A - top-20 conditions (live, plus 2y for the deep set)
Full rows: `research/bdi/top20/CONDITIONS.md` (2026-11-10 block); outputs `research/bdi/top20/live_*`, `hist_bt_*`.
Deep tonight (rotation, not deep since 11-04..11-06): NM-MF3-FD, CWT09-vwaploss-g5, NS4-pm-FD, MF4-h40-open, ST4-FD (new
to the top 20), NM-HL (2y), orb20_a (new) and CWT09-bounce-g5-lowerhalf (live only, no 2y list). The 5 Part B setups
get their depth from Part B.

**Top "thrives when" findings tonight**
1. **RW3-FD: SPY below its open at 10:00** (live +0.71R, n 41) vs above (-0.14R, n 44); below at entry +0.64R (n 70, 86%
   of top-decile winners). **The record leans on 10-22** (55% of total R; +0.178R without it, BDI 1110).
2. **L3-gap-slope-fromopen-FD: SPY above its open at 10:00** (live +0.34R, n 124; compass UP +0.31R, n 130); below at
   10:00 -0.33R (n 35). Today (above at 10:00) it was Primary's only winner, +6.26R. 62% of its R is 10-20 (+0.103R
   without it). Live loses after 13:00 (-0.82R n 8 / -0.25R n 26) while 2y's best slice is 14:00+: still disagree.
3. **RW5-FD: ETFs** (live +0.63R, n 34) and SPY below its open at 10:00 (+0.53R, n 33); stocks carry 95% of losing R on
   75% of trades. **The record leans on 10-22** (55%; +0.128R without it).

**Other reads**
- MF2-FD: SPY above its open at 10:00 -0.48R (n 57, 59% of losing R); 233% of R on 10-22 (-0.152R without it).
- The **unconfirmed compass** is the losing state for both Graveyard CWT09 shorts (vwaploss -0.60R n 38; bounce -0.20R
  n 92) and RW7-FD (31% of losing R on 24%).
- **CWT09-vwaploss-g5, 2y:** price < $20 is -0.846R (TRAIN -1.04 / VALID -0.45, n 745). Skipping it passes the
  no-strangle screen (keeps 80% / 99% of top-decile) and lifts 2y -0.169 -> +0.005R. Live does not confirm (price < $20
  +0.02R, n 33). Logged as a backlog idea, not proposed.
- **NS4-pm-FD:** ATR% 2-3.5 is the weak bucket live and on 2y for the third night (2y -0.318R, both splits); skipping it
  still leaves 2y -0.053R. NS4-FD drop lean (M1) is unchanged.
- **NM-HL and ST4-FD:** live and 2y point opposite ways on gap; no condition.
- Screen-passing skips (keep >= 70% trades and >= 90% top-decile), live only, n small: RW3-FD skip compass UP (+0.325
  -> +0.407R), L3-rsi5hi-FD skip SPY below at 10:00 (+0.049 -> +0.151R), RW7-FD skip 13:00-14:00 (+0.005 -> +0.076R),
  orb20_a skip SPY above at entry. On deck only; none scored tonight.

## Part B - top-5 execution tuning
Selection (PLAN.md): RW7-FD (145 live, T1), MF2-FD (67, P), RW3-FD (42, P), L3-fromopen-FD (34, P), RW5-FD (33, P), the
next eligible after the rotation (all last tuned top5_1104).

### Live (paper, 11-04..11-10; reports r_multiple)
| setup | n | win | avg R | avg win / loss | BE win | med MFE / MAE | losers never +0.2R | where losers cluster |
|---|---|---|---|---|---|---|---|---|
| RW7-FD | 145 | 46.2% | -0.048 | +0.76 / -0.74 | 49.4% | 0.39 / 0.68 | 43 of 78 | 13:00-14:00 (-0.57R, n 34); 11-10 57 trades -28.3R (no latch in T1) |
| MF2-FD | 67 | 20.9% | -0.509 | +1.63 / -1.08 | 39.7% | 0.58 / 1.00 | 14 of 53 (26 reached +0.5R) | 10:30-11:30 (-0.84R, n 24); 11-06 -20.7R |
| RW3-FD | 42 | 50.0% | +0.233 | +1.15 / -0.68 | 37.2% | 0.31 / 0.73 | 9 of 21 | 11-10 17 trades -8.5R (latched 13:04) |
| L3-fromopen-FD | 34 | 64.7% | +0.266 | +0.81 / -0.73 | 47.4% | 0.68 / 0.41 | 7 of 12 | 14:00+ (-0.23R, n 4) |
| RW5-FD | 33 | 30.3% | -0.304 | +0.76 / -0.77 | 50.2% | 0.25 / 0.80 | 15 of 23 | 11:30-14:00 (-0.47R, n 25); 11-10 22 trades -12.3R |

### History (backtest parents, TRAIN+VALID)
| setup | n | win / BE | exp | TRAIN / VALID | up / down sessions | beat parent | best variant (d R; t) | its TRAIN / VALID |
|---|---|---|---|---|---|---|---|---|
| RW7-FD | 20,710 | 48.7 / 52.7% | -0.065 | -0.083 / -0.035 | -0.25 / +0.08 | 9 | G13 CF +0.040 (7.09) | -0.051 / -0.004 |
| MF2-FD | 4,049 | 37.1 / 41.5% | -0.117 | -0.055 / -0.194 | -0.36 / +0.00 | 2 | G13 CF +0.106 (4.82) | +0.082 / -0.131 |
| RW3-FD | 4,800 | 48.0 / 52.6% | -0.076 | -0.095 / -0.041 | -0.22 / +0.05 | 6 | G13 CF +0.045 (5.45) | -0.061 / -0.005 |
| L3-fromopen-FD | 33,873 | 54.1 / 55.0% | -0.017 | -0.023 / -0.006 | -0.05 / +0.06 | 3 | G14 skip < $20 +0.065 (3.72) | **+0.102 / +0.012** |
| RW5-FD | 4,499 | 48.6 / 52.6% | -0.063 | -0.054 / -0.078 | -0.22 / +0.10 | 5 | G13 CF +0.047 (4.16) | -0.010 / -0.040 |

- **Same picture as top5_1104, one week on.** CF (G13) is the best knob on 4 of 5, skip price < $20 (G14) and the
  wider stop (G01, x1.5 at the same $) beat the parent on 3-4, the tighter stop (G02) is the worst knob on all 5
  (d -0.025..-0.042R). All four RW/MF shorts still lose with CF; they lose in up sessions (-0.22..-0.36R) and earn in
  down sessions: down-tape bets, not stock edges.
- **L3-fromopen-FD is again the closest call.** G14 (skip < $20), G13 (CF) and G19 (ADV >= $95M) are positive in TRAIN
  and VALID, in up and down sessions, without the best day and vs random; G14 / G13 pass the no-strangle screen (keep
  72% / 81% of trades, 98% / 100% of top-decile; G19 keeps 73% / 89.7%, just under). They fail on strength: t TRAIN+VALID 0.90-1.07 vs BAR90 4.50; VALID only
  +0.004..+0.015R.
- **Tonight's new knobs, motivated by 11-10, did not hold on two years:**
  - G08 clock exit 13:00: d -0.012..+0.017R, best t 1.40 (RW3); L3-fromopen gets worse. The midday flip is a day
    pattern, not a per-setup clock edge (consistent with BDI 1110's MFX1 VALID fail).
  - G11 / G12 (entries before / from 11:00): the early half beats the parent on RW7 / RW3 (t 3.16 / 3.21) but keeps
    only 18-26% of trades and 19-20% of top-decile winners (strangles) and is still negative in TRAIN. For L3-fromopen
    the later half is the better one (+0.004R), the opposite of the 11-10 live day.
  - Compass (G17 / G18): helps RW7 (t 2.43, at the setup bar) and RW5 / RW3 slightly; hurts L3-fromopen (-0.072R TRAIN)
    and is flat on MF2. Per remedies rule: 3 better, 1 flat, 1 worse; not proposed.
  - Loser pattern as opportunity, SPY above its open (G16): beats the parent on RW3 / RW5 / RW7 but keeps 44-52% of
    trades (strangles); still negative.
- Per-setup study bar 2.43, study-wide 3.02. Configs counted: 95 (plus 0 Part A sizing checks tonight).

## Owner inbox
FYI lines for Part A and Part B appended to `research/owner_inbox/2026-11-10.md`. No DECISION.

## Files
`PLAN.md` (pre-declaration), `live_rank.py` / `live_rank.csv` / `live_top5*.{csv,txt}`, `build_cache.py`, `scan_1110.py`,
`report_1110.py` / `report_out.txt` / `results.csv` / `summary.json` / `hist_parent_detail.txt`, `make_proposals.py` /
`backlog_proposals.jsonl`. Part A scripts and outputs in `research/bdi/top20/`.
