# Top-20 conditions + top-5 execution tune, 2026-11-06 (seventeenth run): FAILED the Testing bar, 0 of 90; 18 variants beat their parent

*Educational only - not financial advice.*

- **Live** numbers are **paper** trades (rule 7): a diagnosis, not evidence. **History** numbers are **backtests** on
  the open two-year history: production + time-of-day costs, x3 on the extended tier, TRAIN (<= 2025-12) and VALID
  (2026-01..03, 07..09-15). The locked block (2024-11-01..2025-02-28) was **never loaded**. No holdout was scored,
  because nothing reached the Testing bar.
- **Data:** the 2-year cache per `research/bdi/1104/DATA.md` (frames to 2026-11-04). Part A's two-year reads use the
  BDI 1104 trade lists (`bt_lab1104`, all 22 open months).
- **Configurations scored tonight: 90.** That is 18 one-knob execution variants per setup x 5, all pre-declared in
  `PLAN.md` before any row was scored. Part A's bucket reads are descriptive and tune nothing: 10 dimensions x 20 setups
  live, plus 7 setups on two years.
- **Result: 0 variants meet the Testing bar. There is no DECISION, no Testing proposal and no Primary change.**
  - 18 variants beat their parent: 9 on CWT13-z05-long and 9 on MF4-FD. Every one of the 18 still loses in TRAIN and
    in VALID.
  - 22 variants are positive in both TRAIN and VALID: 15 NS3 rows and 7 NM-HL rows, on parents that are already
    positive. None of them beats its parent.
  - The best TRAIN+VALID t of any variant is 2.94 (NS3 G14 CF), against a BAR90 of 4.41.
- **Parity:** every parent equals the cached production R (mean |d| <= 0.00004R, 100% within 0.01R).
- config/, mcf/, docs/live/ and the workflows are untouched. 23 lines were appended to research/backlog.jsonl, tag
  `top5-tune`: 5 grid lines (parked) and 18 beat-parent lines (rework).

**Rule changes inside the stats windows (research/ledger.jsonl effective dates).**
- *Part A live window, 10-06..11-06:* per-lot stacking (10-13), refire B (10-14), twin cap and -2R setup stop (10-20),
  Testing setup stop off (10-23), GX1 5-minute clock (10-27), Primary ~$4k (10-28), Primary -2R latch (10-29), CF +
  BAR90 in Testing (10-30), moves 10-30..11-04, UNI1 top-500 pool in Testing 2 (11-04), ROLL1 low-rep homes (11-05).
  Nothing changed on 11-06.
- *Part B live window, 11-02..11-06:* see PLAN.md section 1. All of it ran with CF in Testing 1/2, and Primary ran at
  ~$4k with the -2R latch. 11-05 (SPY -4.2%) and 11-06 (quiet, 10:41 squeeze) dominate several live records below.

## Failures first
| setup (acct) | beat parent | parent TRAIN / VALID (t TRAIN+VALID) | best variant (d R; t) | its TRAIN / VALID; up / down |
|---|---|---|---|---|
| `CWT13-vwapstretch-z05-long` (T2) | 9 | -0.068 / -0.079 (-4.53) | G14 CF: +0.036 (6.08) | -0.041 / -0.064; +0.02 / -0.07 |
| `MF4-h40-open-flowsell-FD` (P; DM-MF4 pending) | 9 | -0.119 / -0.071 (-5.04) | G14 CF: +0.057 (8.03) | -0.074 / -0.041; -0.15 / +0.02 |
| `NM-HL-T75-pm-long` (T2) | **0** | +0.052 / -0.003 (1.08) | G18 ADV x1.2: +0.011 (2.32, below 2.40) | +0.062 / +0.016; +0.06 / +0.04 |
| `exhaustion_short` (T1) | **0** | -0.053 / +0.105 (0.09) | G15 price >= $20: +0.019 (2.12) | -0.017 / +0.110 |
| `NS3-failed-vwap-reclaim-short` (T1) | **0** | **+0.063 / +0.166 (2.22)** | G14 CF: +0.014 (0.89) | +0.126 / +0.164; +0.07 / +0.20 |

- **CF (G14) is again the best knob on CWT13 and MF4-FD**, with the same numbers as top5_1102: t 6.08 and t 8.03. The
  setups still lose: CWT13 -0.049R, MF4-FD -0.061R.
  - CF already runs on CWT13 (Testing 2). MF4-FD's Primary copy has none.
  - Even with CF, MF4-FD loses in up sessions (-0.15R) and in TRAIN. That fits DM-MF4: its record is a down-tape bet.
- **NS3-failed-vwap-reclaim-short (base, 09:50-11:30, Testing 1) is the one positive parent of tonight's five.**
  - Two years: +0.109R on 1,031 trades, TRAIN +0.063 / VALID +0.166.
  - WF 82% of months positive. Up sessions +0.028R, down sessions +0.171R.
  - +0.086R without its best day, and +0.153R vs random entries.
  - t 2.22 is far below BAR90 4.41, and no knob beats it. CF (+0.144R, t 2.94) and price >= $20 (+0.133R) are better
    in TRAIN but worse in VALID.
  - Live it has 15 trades at -0.247R (11-05: 4 stops, -4.2R). That is not evidence either way.
  - **Keep it running in Testing 1 for reps.** No change.
- **NM-HL-T75:** parent +0.030R (WF 65%). 7 variants are positive in both splits; none beats the parent.
  - The closest is G18 (ADV >= 150M), t 2.32 against a bar of 2.40.
  - CF (G14) is a no-op: these are all ADV >= 125M names.
- **exhaustion_short:** flat (+0.004R; TRAIN -0.053 / VALID +0.105). No knob beats it.
- **Flush-chase guard (G13, new; per-setup effect, as the remedies rule asks):**
  - **MF4-FD** drops 24% of trades (1,404) and improves sum R (d +0.016R per parent signal, t 2.48). It counts as
    beats-parent, but **avg R falls** from -0.101 to -0.113R. In history MF4-FD's near-LOD shorts (-0.064R) are *less*
    bad than the rest.
  - **NS3** gets worse (-0.007R; its 36 near-LOD shorts were +0.19R).
  - CWT13 (8 dropped), NM-HL (1) and exhaustion_short (3) are flat.
  - On two years this confirms FB1 (1105): the 11-06 live split (near-low shorts -0.495R vs +0.195R) is **not a
    per-setup edge in history** for these setups. It stays a forward shadow (`fb1-flush-chase-shadow`), not a filter.
- **Tighter stop (G02, x0.75 at the same $) is the worst knob on CWT13 (t -5.25) and MF4-FD (-4.18), and worse
  than the parent on exhaustion_short (-1.86), NM-HL (VALID only) and NS3 (-1.08).** The wider stop G01 beats the parent on CWT13 and MF4-FD, as before.

**Recurring live loser patterns tested (Part B):**
- **One-bet days** (CWT13: 100 trades on 11-05 at -22.9R; NM-HL: 24 on 11-02 at -9.8R): G17 (first 5 per session)
  beats the parent on CWT13 (t 3.92) and MF4-FD (t 4.19), but both still lose. It lowers NM-HL (t -1.79) and NS3
  (t -3.12).
- **Never-worked losers** (live: CWT13 34 of 64, MF4-FD 16 of 30 never > +0.2R): the 30-min and 60-min time stops
  (G06 / G07) are flat to worse on all 5 (best t 0.38).
- **Burst-window losers** (MF4-FD live 10:30-11:30 31 trades -0.58R, both burst days): G11 (before 11:30) / G12 (from
  11:30) both beat the parent on two years. History has no 10:30-11:30 hole (-0.101R vs -0.101R parent), so the live
  loss is the 11-05 / 11-06 market, not a time-of-day effect.

## Part A - top-20 conditions deep dive (`research/bdi/top20/`, table `CONDITIONS.md`)
- **Top 20** = the leaderboard order (shrunk avg R, >= 20 trades, all accounts incl. Primary, Graveyard, Live Lab and
  Explore 1; GEN out).
  - All 20 were read live (10-06..11-06, 14,157 trades loaded).
  - MF2-FD fell from rank 2 to rank 5 after 11-06's -20.8R (28 shorts).
  - New: NS1-rsidip-rsi5pop-long (rank 16). Out: exhaustion_short.
- **Deep set (7):** the six last read in depth on 11-03 (NM-MF3-FD, ST7-FD, NS4-pm-FD, RW1-FD, L3-lowdist-FD), the
  newcomer NS1-rsidip, and MF2-FD (DM-MF2 pending). With 11-03 / 11-04 / 11-05, **all 20 have now been read in depth
  within 4 nights.**
- **One-day records** (avg R without best day, and best-day share):
  - MF2-FD: 151%, w/o it -0.10R. NS1-rsidip: 258%, -0.12R. NM-MF3-FD: 143%, -0.44R. L3-lowdist-FD: 144%, -0.05R.
  - ST7-FD: 109%, -0.01R. NS4-pm-FD: 98%, +0.005R. CWT09-vwaploss: 662%, -0.31R.
  - **Not one-day records:** RW3-FD (47%, +0.30R w/o best day), RW5-FD (41%, +0.29R), RW7-FD (48%, +0.04R) and RW1-FD
    (50%, +0.06R).
- **Thrives / struggles, tonight's deep 7 (point-in-time only):**
  - **NS4-pm-FD:** thrives at ATR% >= 5 (live +0.58R, 2y +0.041R both splits). Struggles at ATR% 2-3.5 (live -1.05R;
    2y -0.318R, TRAIN -0.416 / VALID -0.139).
    - Skipping ATR% 2-3.5 passes the no-strangle screen live (keeps 79% of trades / 100% of the top decile) and on two
      years (75% / 92%). On two years the setup is still -0.053R, so it is **on deck**.
  - **NS1-rsidip:** thrives with SPY flat at 10:00 (live +0.29R n 10; 2y +0.158R both splits) and at ADV $300M-1B
    (live +0.37R; 2y +0.153R both splits). Struggles at ADV $100-300M (live -0.16R; 2y -0.085R both splits). A skip
    there keeps only 47% on two years, so this is sizing / on deck only.
  - **NM-MF3-FD:** thrives on leveraged ETFs (2y +0.178R both splits; live +0.91R n 2) and price >= $150 (2y +0.083R;
    live +0.48R). Struggles on single stocks (88% of losing R live) and price $20-50 (2y -0.106R). The live 11:30-13:00
    edge is not on two years.
  - **ST7-FD:** thrives with SPY flat at 10:00 (2y +0.108R both splits), on ETFs (2y +0.41R, n 40) and at ADV >= $1B.
    Struggles with SPY above its open at 10:00 (2y -0.110R) and price < $20 (2y -0.239R, both splits). The live
    13:00-14:00 loss is not a 2y loser.
  - **RW1-FD:** live ETFs +0.44R, SPY below at entry +0.29R. Struggles with SPY flat at entry (live -0.40R). On two
    years no bucket is above -0.011R: no condition rescues it.
  - **L3-lowdist-FD:** 2y thrives with SPY flat at 10:00 (+0.089R both splits) and struggles at price < $20 (-0.300R
    both splits). Live and 2y disagree on 10:30-11:30 (live +0.43R, 2y -0.314R).
  - **MF2-FD:** **live and 2y disagree on every condition.** Price < $20 is live +0.95R vs 2y -0.43R. SPY below its open
    at 10:00 is live +0.43R vs 2y -0.223R, the worst bucket in both splits. Struggles live with SPY above its open at
    10:00 (-0.43R, n 47; 11-06 was such a day). Nothing rescues it on two years (-0.117R). This is consistent with
    DM-MF2.
- **Top 3 "thrives when" where live and 2y agree:**
  1. NS4-pm-FD at ATR% >= 5.
  2. NS1-rsidip with SPY flat at 10:00 / ADV $300M-1B.
  3. NM-MF3-FD on leveraged ETFs / price >= $150.
- **Filters:** none is proposed.
  - NS4-pm-FD's skip of ATR% 2-3.5 is the only skip that passes the 70% / 90% screen on both live and two years, and it
    leaves the setup negative.
  - Price < $20 is a 2y loser in both splits for 5 of the 7 deep setups. Part B tested it as G15: it beats the parent
    on CWT13 / MF4-FD, is near-flat on NM-HL / exhaustion_short, and is worse in VALID for NS3. CF does the same job.

## Selection (Part B)
Live paper trades 11-02..11-06 (run_id 1; S6 and GEN-* out; `live_rank.csv`). The exclusions are in PLAN.md section 1:
the 10 setups tuned in top5_1103..1105, the pdl lineage, CWT05 and intraday_momentum.
| setup | live n | live win / BE win | avg win / loss | avg R | losers never > +0.2R | live med MFE / MAE | give-back (losers) |
|---|---|---|---|---|---|---|---|
| CWT13-z05-long (T2) | 143 | 55.2 / 69.8% | +0.45 / -1.03 | -0.215 (11-05: 100 trades -22.9R) | 34 of 64 | 0.40 / 0.66 | 1.27R |
| MF4-FD (P) | 51 | 41.2 / 67.1% | +0.48 / -0.99 | -0.381 (11-05 -10.5R, 11-06 -5.3R) | 16 of 30 | 0.31 / 0.95 | 1.22R |
| NM-HL-T75 (T2) | 31 | 48.4 / 66.3% | +0.40 / -0.79 | -0.215 (11-02: 24 trades -9.8R) | 9 of 16 | 0.34 / 0.59 | 1.00R |
| exhaustion_short (T1) | 26 | 50.0 / 63.6% | +0.35 / -0.61 | -0.130 | 4 of 13 | 0.31 / 0.41 | 0.96R |
| NS3 base (T1) | 15 | 40.0 / 53.7% | +0.83 / -0.97 | -0.247 (11-05: 4 trades -4.2R) | 2 of 9 | 0.47 / 0.90 | 1.32R |

**Backtest parents** (TRAIN + VALID; `hist_parent_detail.txt`):
| setup | bt win / BE | exp | w/o best day | vs random | best / worst time | up / down sessions |
|---|---|---|---|---|---|---|
| CWT13 | 64.3 / 69.2% | -0.072 | -0.075 | -0.007 | 13:00-14:00 +0.020 / 11:30-13:00 -0.117 | -0.017 / -0.090 |
| MF4-FD | 61.0 / 68.3% | -0.101 | -0.105 | -0.017 | 10:00-10:30 -0.060 / 09:50-10:00 -0.162 | -0.197 / -0.011 |
| NM-HL-T75 | 66.4 / 64.0% | +0.030 | +0.019 | +0.092 | 11:30-13:00 +0.064 / 14:00+ +0.019 | +0.043 / +0.024 |
| exhaustion_short | 52.6 / 52.3% | +0.004 | -0.022 | +0.057 | 14:00+ +0.022 / 11:30-13:00 -0.068 | -0.062 / +0.092 |
| NS3 base | 58.7 / 52.8% | **+0.109** | +0.086 | +0.153 | 10:00-10:30 +0.202 / 10:30-11:30 +0.043 | +0.028 / +0.171 |

- Live and backtest agree on the win and loss sizes within ~0.1R for all 5. In live every setup sits 13-26 points below
  its break-even win rate. On two years only NM-HL and NS3 are above break-even.
- All three shorts lose most in SPY-up sessions on two years. The two longs (CWT13, NM-HL) are not hurt as much by
  down sessions as the shorts are by up sessions.
- Live losers cluster as follows:
  - CWT13 at 11:30-13:00 (81 trades, -0.27R), which is also its worst two-year slot.
  - MF4-FD at 10:30-11:30 (31, -0.58R).
  - NM-HL at 14:00+ (21, -0.34R).
  - exhaustion_short at 13:00-14:00 (10, -0.34R).
  - NS3 at 10:30-11:30 (8, -0.75R), which is also its weakest two-year slot (+0.043R). G12 (from 10:30 only) is the
    worse half there, and G11 (before 10:30) does not beat the parent in VALID.

## What would change the picture
- NS3 base is the only setup tonight whose two-year record supports what it does. Its forward record in Testing 1 is
  the test.
- CF on MF4-FD's Primary copy remains an owner question, as on 11-02. It is not proposed, because MF4-FD still loses
  with CF, and DM-MF4 is the live decision.
- Next top-5 run: rotate these 5 out. The eligible pool is thin. Next by live count: NM-AR-AM (12), ST7-FD and the
  L3 pair after their 3-run gap.

## Files
- `PLAN.md` (pre-declaration)
- `live_rank.py` / `live_rank.csv` / `live_top5.csv` / `live_top5_detail.txt`
- `build_cache.py`, `scan_1106.py`, `report_1106.py` (scratch in /dev/shm/t5_1106, deleted after the run)
- `results.csv`, `summary.json`, `report_out.txt`, `hist_parent_detail.txt`
- `make_proposals.py` / `backlog_proposals.jsonl`
- Part A: `research/bdi/top20/` (`fetch_live.py`, `conditions_live.py`, `conditions_2y_bt.py` re-dated to 11-06;
  `live_*` and `hist_bt_*` outputs; `CONDITIONS.md` rows dated 2026-11-06)
