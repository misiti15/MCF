# BURST2 — short-burst remedy re-test with 11-05 + 11-06 as live evidence (owner Remedies rule 2026-11-05)

*Educational only — not financial advice.* Live = **paper** journals (run_id 1; R = pnl_adj / (|entry − stop| × shares),
costs in), 7 accounts, 2026-10-06..11-06, 24,137 rows incl. latch- and halt-blocked what-ifs (before costs). 2-year =
lab trade lists (bt_lab1104, 95 setups, uncapped, production costs; 1,102,755 trades) re-enriched with 5-min marks,
TRAIN ≤ 2026-02-28, VALID 2026-03-01..10-05. Locked block 2024-11..2025-02 never read. Research only — nothing in
config/ or the trading path changed. Pre-registered in `PLAN.md` (commit 6db92ace3) before any score.
**Configurations: 13 tonight, 29 in the BURST lineage (bar max(1.5, √(2 ln 29)) = 2.60; BAR90 2.34 for reference).
0 pass.**

## Failures first
- **No remedy passes.** Every gate that blocks a lot of trades (family gate B, compass C-sym) looks big on two years
  (VALID t 4–7.6) only because it trades less of a losing book: excess t −1.9..−2.4. Same verdict as BURST1.
- **The open-loss latch (A) again cannot catch the burst on the day.** 11-06: MF2-FD's 10:20–10:35 shorts were in profit
  (MFE 0.6–1.8R) when the 10:40 wave of 14 entered, so the open + closed R was well above −2R until the 10:44–10:52 stops.
  vs the live latch it changes 11-06 by −3.4R (−2R), −0.6R (−3R / −4R).
- **The compass gate (C, SPY from-open side for burst shorts) is the 11-06 fix but not a general one.** On 11-06 SPY was
  +0.46..+0.85% above its open during MF2's burst, so C blocks it (+24.1R on Primary 11-06); on 11-05 SPY was far below
  its open, so it does nothing (0R) — the 11-05 MF4 burst was "with" the tape. Two years: VALID t 0.92, excess −2.41.
- **The flush gate (D, QQQ already −0.4% in 30 min) is the only rule that fixes both days**, but two years do not support it
  (VALID t 1.99 < 2.60, excess −0.38; MF family −56.7R in VALID).

## Results (`decision.csv`; TRAIN / VALID raw delta (t), VALID excess t, live; Primary days)
| config | TRAIN Δ (t) | VALID Δ (t) | VALID excess t | live all Δ (t) | Primary Δ | 11-04 | 11-05 | 11-06 | live setups +/− | VALID setups +/− | fam harmed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A open-loss −2 vs live latch | +10.1k (9.2) | +6.3k (6.8) | −0.31 | +284 (2.6) | +1.8 | +0.3 | −9.2 | −3.4 | 53/29 | 51/35 | 0 |
| A open-loss −3 vs live latch | +7.0k (6.8) | +4.7k (5.4) | +0.09 | +61 (0.6) | +2.4 | −2.6 | +4.6 | −0.6 | 48/38 | 49/37 | 0 |
| **A open-loss −4 vs live latch** | +4.1k (4.1) | +4.1k (4.8) | **+1.14** | **−49 (−0.5)** | +2.4 | −2.6 | +9.5 | −0.6 | 43/43 | 45/43 | 0 |
| B family gate N=4/6/8 | +37.6k/+33.8k/+31.2k (8.3/7.5/7.0) | +20.4k/+19.1k/+18.1k (7.6/7.2/6.9) | −2.34/−2.10/−1.90 | +1,474/+1,293/+1,145 (4.1/4.1/4.0) | +27.6/+17.7/+9.2 | +4.7/+0.9/+0.6 | +1.5/−1.8/−4.5 | +25.7/+26.0/+24.3 | 107/42, 94/43, 83/39 | 41/54 each | 2/3/3 |
| C compass B=2 x=0 / x=0.25% | +6.8k/+3.0k (2.8/1.4) | +1.4k/+0.4k (0.9/0.4) | −2.41/−1.79 | +328/+144 (1.3/0.7) | +59.6/+53.2 | +7.4 | 0 | +24.1 | 39/17, 31/24 | 26/15, 25/16 | 0 |
| C compass B=3 x=0 / x=0.25% | +5.2k/+2.1k (2.3/1.0) | +1.1k/+0.2k (0.8/0.2) | −2.37/−1.80 | +298/+157 (1.3/0.9) | +57.1/+55.2 | +6.5 | 0 | +26.9 | 39/12, 32/19 | 22/18, 23/17 | 0 |
| C-sym B=2 x=0 | +22.2k (6.4) | +8.6k (4.0) | −2.39 | +858 (2.7) | +60.8 | +7.4 | 0 | +24.1 | 78/27 | 50/35 | 3 (GEN, NM, ST) |
| **D flush B=2 y=0.4%** | +2.5k (1.5) | +715 (1.99) | −0.38 | **+150 (2.3)** | **+36.7** | 0 | **+18.9** | **+11.6** | 31/6 | 26/18 | 1 (GEN) |
| D flush B=2 y=0.7% | +1.4k (1.2) | −11 (−0.1) | −1.34 | +61 (1.8) | +17.6 | 0 | +17.6 | 0 | 18/4 | 23/18 | 2 (GEN, MF) |

## Owner Remedies table (per setup / family; `effect_summary.csv`, `families.csv`, `setups_effect.csv`)
- **D flush 0.4%** — Primary: 5 setups better, **0 worse** (+36.7R; MF2-FD +17.6, MF4-FD; MF family +31.5R, heat_fade_short
  +5.2R). All accounts: 31 better (+204R) / 6 worse (−54R; worst CWT09-vwaploss-g5 −22R). VALID: 26 better (+958R) / 18
  worse (−243R); families 6 better / 2 worse (GEN −158R, **MF −57R**). Targeted (acts only on the 3rd+ short in 15 min
  after an index flush; 2.5% of two-year trades), not tailored to one setup — but on two years the MF family it is meant to
  help loses.
- **A open-loss −4** — Primary 7 better / 6 worse (+25 / −23R; worst L3-fromopen −8.8R). All accounts 43 / 43 (+220 /
  −269R). VALID 45 / 43 (+4,606 / −556R); families 6 better / 3 worse (RW −73R, ST −11R, NM −3R).
- **C compass x=0** — Primary 10 better / 4 worse (+69 / −9R; RW5-FD −7.4R); all accounts 39 / 17; VALID 26 / 15, NS
  family −44R.
- **B family gate 4** — over-broad: Primary 11 / 5 with RW −41R (RW5-FD −24.7R; the RW pop-fade bursts are its winners);
  VALID 41 better / 54 worse.

## Best near-miss and forward shadows (`research/bdi/swings/hypotheses.jsonl`)
- **Pre-registered near-miss (highest VALID excess t with TRAIN > 0): `burst2-openloss-latch4`** — an open + closed −4R
  latch in place of the realised −2R latch passes every two-year test (VALID t 4.76, excess t 1.14, TRAIN excess +842R,
  0 families harmed) and **fails only the live test** (−49R, t −0.46). Journal-only shadow.
- **Targeted runner-up: `burst2-flush-gate-short`** — the only rule that fixes 11-05 and 11-06 and harms no Primary setup;
  fails the two-year bar. Journal-only shadow.
- What would still help (next step, not tested): the two failing days share a cause — MF2 / MF4 enter *after* the index
  flush with 0.125–0.25 × ATR stops. That is the setup's own trigger (BURST1 step 0), so the remedy that fits the Remedies
  rule best is a setup-level rework (RW3-style pop or "QQQ not already −0.4% in 30 min" as an entry condition, tested
  on its own 2-year record), carried in backlog `burst2-mf-after-flush-rework`.

## Rule changes in the live window (research/ledger.jsonl effective dates)
10-20 MF2-FD / MF4-FD promoted to Primary; 10-23 per-setup stop off in T1 / T2 / Gen; 10-27 GX1; **10-28 Primary lot ~$4k**;
**10-29 Primary −2R latch**; 10-30 Testing CF; 11-02..11-03 Graveyard moves; 11-04 UNI1 (T2 top-500); 11-05 ROLL1
(Explore 1 / Live Lab). 11-06: no rule change (the −20R account halt is the standing account limit; restored after the 14:38
restart). R is unaffected by sizing; $ is.

Files: `live.py` (live inputs), `sim2.py` (keep flags), `score2.py` (copy of burst1/score.py, N = 29, + P_11-06),
`decision.csv`, `results.csv`, `families.csv`, `setups_effect.csv`, `effect_summary.csv`. Scratch (2-year enrichment,
bars) outside the repo.
