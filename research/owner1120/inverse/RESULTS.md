Educational only — not financial advice

# Owner item 1 — direction-correct inverse / leveraged handling for ALL setups: results

Pre-registered in PLAN.md (this folder) before scoring. Research only: no config, setup, exit, order or runner change.
**Configurations tried: 12** (H1, H1M, H2, H2D, H2S, H1-broad, H1-sector, H1-single, H1-crypto, H1-vol, LEV-X, and the
pre-registered per-setup choice "CHOSEN"). All are reported. Costs are in: live uses LR8 on every row via with_cost_r, the
lab uses production costs. Intraday borrow fee is 0 at Alpaca because MCF is flat by 15:55. The real borrow cost is the
ETB availability, and that is already in the live record. Inverse-fund decay acts at the daily reset only. The locked
block 2024-11-01..2025-02-28 is asserted absent and was never read. Fit/check: lab < / >= 2025-11-01; live 10-06..11-05 /
11-06..11-19.

**Rule changes inside the live window 2026-10-06..11-19 (research/ledger.jsonl):** stacking/refire 10-13/10-14; Primary
sizing 10-28 (twice); Primary -2R latch 10-29; ROLL1 low-rep homes 11-05; LR8 live costs 11-12 (all rows re-costed on
LR8 here); GY-BENCH 11-18; C3-EXIT100, C3-ROT/ROT2, U9-TGT, U9-ETB effective 11-19. Effective from 11-20, so outside the
window but inside the shadow: 9 ultimate_1119 setups, FOOTRACE-EXIT, GY-FOOTRACE, the stop-rounding fix. Lab window
2024-10..2026-11-04: 118 enabled lab setups, first fire per symbol-day, no caps, no ETB.

## (a) Audit: which setups can reach these products, and what they did
- **Reach:** 238 enabled setups across 10 accounts (audit_enabled.csv). 229 draw from the scanner universe. That universe
  holds 69 inverse/long-vol products (14 broad-index inverse, 16 sector/country, 31 single-stock, 3 crypto, 5 long-vol)
  and 134 leveraged-long funds. No setup has a product-type filter. In 128 of them, inverse, long-vol or leveraged
  symbols produced live signals.
- The 9 fixed-list setups (IDX1/2/3/5, LD2/6/8 on TQQQ/SPXL, GEN-POD breadth ETF) trade leveraged LONG funds only.
  IDX setups already work direction-correctly: they compute the signal on QQQ/SPY (`signal_symbol`) and trade the 3x
  fund.
- **Live trades in inverse / long-vol products (run 1, all accounts): 811 trades (2.9% of 28,118), in 118 setups.**
  Every one has market exposure opposite to the setup's side (thesis mismatch).
  - **Shorts: 224 trades, -78.8R, avg -0.352R, in 51 setups.** By class: broad-index -43.3R (101), sector -24.9R (77),
    single -5.2R (20), long-vol -5.4R (26).
    These are "short weak names" trades that end up long the market. L3 is the largest: 65 trades, -30.4R, across 7
    copies. Its symbols are SQQQ, SPXS, SOXS, BEZ, AAOZ, UVXY and VXX. L3 never shorted an index ETF itself: 0 live,
    22 lab fires.
  - **Longs: 587 trades, +20.5R, avg +0.035R, in 67 setups.** By class: broad -1.1R, sector +9.5R, single +18.7R,
    long-vol -6.6R. These are long setups that end up short the market.
- **Leveraged longs** (direction-correct: exposure = side): 1,075 trades, -162.7R (longs 735 / -145.4R, shorts 340 /
  -17.2R). The product is not the cause. The same setups' own stock trades average -0.175R (longs) and -0.131R (shorts),
  against -0.198R and -0.051R on the levered funds. **No change proposed.** LEV-X, blocking them both sides, shows
  +162.7R live / +770R lab. That gain is the trimming of losing setups, not a remedy targeted at the product, and 92
  setups get worse by up to 11R.
- Full lists: audit_live_trades.csv, audit_inverse_by_setup.csv.

## (b) The handlings tested (headline; tables/headline.md has every window; better/worse = setup x account live, setup lab)
| config | live all: better / worse, net | live ex 11-19 | live check (11-06..) | lab check half | largest live worsening |
|---|---|---|---|---|---|
| H1 shorts skip inverse/vol | 50 (+99.3) / 24 (-20.6), **+78.8R** | +55.9R | +28.4R | +486.8R | -2.65R |
| H1M block both sides | 91 / 80, +58.3R | +36.5R | +27.5R | +2,173R | **-18.9R** |
| H2 direction-correct (H1 + keep longs + inverse-buy) | 54 / 36, +58.1R | +35.2R | +18.4R | = H1 | -4.20R |
| H2D + duplicate inverse for every underlying short | 74 / 83, **-103.2R** | -126.8R | -46.1R | +142R (fit -283R) | -30.3R |
| H2S keep where fit was positive (fit/check clean) | 89 / 68, +116.6R | +94.8R | **+39.0R** | +1,937R | -7.13R |
| CHOSEN (pre-registered per-setup rule; in-sample) | 63 / 26, **+116.4R** | +93.5R | +38.2R | +1,530R | -2.65R |

- **The "inverse buy" does not help.** Under H2, a short setup buys the inverse when its short on the underlying is
  skipped. There were 94 such cases: -20.6R, -0.22R each. The 24 on index underlyings made -7.0R. Doubling every index
  short through an inverse fund (H2D) loses -103R live and -140R lab. These setups' short signals on underlyings are not
  good enough to express twice.
- **By product class (H1 decomposition, live):** broad +43.3R (29 better / 16 worse), sector +24.9R (28/16, but check
  window -2.5R), single +5.2R, long-vol +5.4R (largest worsening -5.3R), crypto 0. Lab check: broad +280R, sector +34R,
  single +127R, vol +45R. All four classes point the same way on shorts.
- **Is the product the problem? (tables/inverse_vs_stock.md, paired by setup)**
  - Live inverse SHORTS are -0.38R/trade worse than the same setups' stock shorts. The gap holds in both halves (-0.31,
    -0.38), and 32 of 49 setups are worse on inverse.
  - In the lab the short gap is about 0 (fit +0.04, check -0.05). The lab's H1 gain is therefore partly generic trimming
    of negative short setups. The live gap is the targeted evidence.
  - Inverse LONGS: live +0.22R/trade *better* than the same setups' stocks (both halves +0.34 / +0.15). Lab: worse
    (-0.09 / -0.14). The sources disagree on sign, and the disagreement persists. This is market regime: an inverse long
    is a short-market bet.

## Per setup / family (CHOSEN, live; tables/live_CHOSEN*.csv, per_setup_handling.csv)
- **Families: 21 better (+118.0R) / 3 worse (-1.7R):** RW5 -0.90, RW3S -0.38, NS2 -0.37 (1-4 trades each).
  - Better: CWT14 +34.9R (200 trades, mostly the long block), L3 +30.4R (avg w/o best day 0.06 -> 0.13; best-day share
    62% -> 48%), exhaustion_short +7.7, GEN +5.8, RW2 +5.1, ST2 +4.3, CWT13 +3.8, CWT09 +3.7, CWT12 +3.4, RW3 +3.2,
    NS3 +3.1, others < 2.5R.
- **Primary:**
  - L3-fromopen-FD +13.94R (16 removed; avg w/o best day -0.01 -> +0.12; best-day share 103% -> 70%, so the `1 day` tag
    weakens but stays).
  - L3-rsi5hi-FD +2.58R, RW3-FD +2.18R, MF2-FD +1.33R, exhaustion_short +1.14R.
  - Worse: RW5-FD -0.90R (1 trade), CWT14-pdl-p10-lowvol -0.46R (1 trade).
- **Largest worsenings (none > 3R):** heat_fade_short-FD Graveyard -2.65R, GEN-261022-04 -1.73R, GEN-261023-03 -1.64R,
  NS3-failed-vwap-reclaim T-E -1.41R, GEN-261026-07 -1.13R, exhaustion_short T1 -1.06R.
- **The pre-registered choice rule gives:**
  - Inverse shorts blocked in 69 setups (live 211 trades, -80.5R).
  - Inverse shorts KEPT in 7 setups on fit+check evidence (13 live trades, +1.8R; lab 631, +57R): GEN-261022-07,
    GEN-261027-07, NM-AMS-N1, NM-RWR3, NS2-sma50break-FD, NS3V1-am-widestop, RW1-gapdn-bounce-FD.
  - Inverse longs kept in 71 setups (live 336, +56.3R).
  - Inverse longs BLOCKED in 10 setups (live 251, -35.9R; lab check -1,023R): 7 CWT14 variants, CWT12-coil-k6,
    ST2-slope20up-FD, NS5-sma50-flush-FD, GEN-261023-04.
  - **Caveats:** the 10-setup long block is concentrated in one family (CWT14), and in the live check window 4 of those
    CWT14 variants were positive (+0.2 to +1.9R). CHOSEN is scored partly in-sample. Its clean read is the forward
    shadow.

## "Can we afford to drop them?"
- **Inverse SHORTS: yes.**
  - Blocking them gives up 224 reps (0.8% of live trades) and gains +78.8R live (+55.9R ex 11-19, +28.4R in the check
    window), with no setup worse by more than 2.65R.
  - The few positive ones are small: UVXY +2.3, TZA +3.0, TWM +2.0, AAOZ +1.5R. The 7 H2S exceptions keep the only
    setups with positive inverse-short evidence.
- **Inverse LONGS: no, not on the live record.**
  - Dropping all of them costs -20.5R live: 80 setups worse (-133R), 364 reps.
  - The worst hits: GEN-261022-01 -18.9R, GEN-261021-02 -17.9R, GEN-261020-07 -9.4R, GEN-261027-03 -7.1R,
    heat_fade_long-FD -4.6R.
  - The lab says the opposite (+2,530R). Keep them, and watch them in the shadow.
- **Playing time:** the short block takes most of the activity of three low-rep L3 copies: L3-fromopen-WB4 T2 18 of 24
  trades, L3-rsi5hi-WB5 Live Lab 2 of 2, L3-lowdist-WB4 T-F 3 of 3. It also takes 2-9 trades from 5 GEN setups.

## Conflicts with standing owner rules (for the conflict check)
1. This is a setup/filter change. It goes to the backlog (RESEARCH_RULES 15-17), never takes effect during 09:30-16:00
   ET, and reaches Primary only in the Friday epoch window (C3-EPOCH). Any BASE1-vs-Epoch read must note the guard.
2. Playing time / low-rep rotation (11-03, 11-04): the three L3 WB copies above would need their rotation clock counted
   on stock-only signals.
3. Remedies rule (11-05): the short block is targeted (51 setups affected, all families reported, 3 families worse by
   < 1R). The long block in CHOSEN is CWT14-heavy, so it is close to "tailored to one family". It stays a shadow column
   only and is not proposed live without the owner's nod.
4. "Tweaked copies are new setups": not applicable. The guard filters symbols. It does not change any setup's rule.

## (c) Shadow
RULE.md and shadow.py (journal-only, forward from 2026-11-20, pass bar fixed in PLAN.md and RULE.md). forward.csv holds
11-19 as a smoke-test day: 36 blocked shorts -22.85R and 8 kept longs +1.0R. 11-19 is before FORWARD_FROM and is not
scored.

Educational only — not financial advice.
