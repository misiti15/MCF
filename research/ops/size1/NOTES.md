# SIZE1 — sizing for live funds (owner 2026-11-04) — results

*Educational only — not financial advice. Backtest (2-year lab lists), and live paper results are labelled
separately. Research only: nothing in config/ or the trading path changed.* Pre-registration: `PLAN.md` (written before
scoring). Code: `prep.py` → `sim.py` → `finalists.py`, `diag.py`. Tables: `results.csv` (every config × window),
`finalists.csv` / `finalists_out.txt`, `diag_out.txt`, `books.txt`, `train_rank.txt`, `selection.txt`.

## Failures first
- **No rule clears the bar.** 190 distinct configs scored (192 pre-registered; book A's "ALL" = HQ1 alone, so 2
  duplicates), + 4 hindsight diagnostic rows + 6 live buying-power checks = **200 looks**. Bar max(1.5, sqrt(2 ln N)) =
  3.24 (N 192) / 3.26 (N 200) on the VALID day-clustered t vs baseline. Best VALID t vs baseline: book A 0.38
  (0.30%/2x/FC), book B 2.15 (0.25%/1x/QX — only "trade less of a losing book"). **No DECISION.**
- **Both books lose on the 2-year lab lists, at every size.** Baseline 0.25% risk / 4x / first-come:
  - Book B (Primary 10): TRAIN −93.4% (DD −93.6%, avg R −0.109), VALID −67.0% (DD −75.6%, avg R −0.037, 38% green).
  - Book A, TRAIN-ranked top 5 (NM-AR, NM-HL, NS2, RW6-FD, RW4-FD): TRAIN −51.9% / DD −64.5%, VALID −7.1% / DD −34.8%.
    Their TRAIN record (uncapped lists, +0.01..+0.33R) was carried by the April-2025 tariff days; with the engine's
    caps (3 lots/symbol, 30/setup, 77 open, −2R setup latch) the taken trades are −0.046R.
  - The named live top 5 on the 2-year lists (hindsight book, diagnostic only): TRAIN −79.8%, VALID −58.4% at baseline.
  - So the 2-year lab says: **sizing cannot rescue these books; smaller is better only because they lose.** Same story as
    SZ-PROOF (Primary's two-year record negative).
- **Live paper (22 sessions 10-06..11-04) disagrees with the lab**: both books are positive there. Paper fills; the live
  list is censored (signals the live caps blocked are absent); best-day shares 34-47%.

## Baseline vs selected (return, max DD, green days in R, avg R w/o best day [best-day share])
| book | config | TRAIN | VALID | LIVE |
|---|---|---|---|---|
| A | **baseline 0.25%/4x/FC** | −51.9%, −64.5%, 38%, −0.05 | −7.1%, −34.8%, 49%, −0.00 | **+15.9%, −2.3%, 72%, +0.116 [34%]** |
| A | TRAIN-selected 0.10%/1x/FC | −20.0%, −27.6%, 39%, −0.05 | −0.4%, −14.0%, 48%, −0.00 | +4.1%, −1.2%, 67%, +0.076 [51%, `1 day`] |
| A | 0.10%/4x/FC | −28.5%, −37.8%, 37%, −0.06 | −3.9%, −18.4%, 48%, −0.01 | **+9.3%, −0.7%, 67%, +0.164 [30%]** |
| B | **baseline 0.25%/4x/FC** | −93.4%, −93.6%, 36%, −0.11 | −67.0%, −75.6%, 38%, −0.04 | **+12.5%, −4.3%, 55%, +0.054 [47%]** |
| B | TRAIN-selected 0.10%/1x/FAM | −46.5%, −47.1%, 36%, −0.10 | −24.6%, −30.3%, 40%, −0.04 | +0.5%, −2.2%, 40%, −0.006 [142%] |
| B | 0.10%/4x/FC | −74.2%, −75.1%, 39%, −0.10 | −46.9%, −54.4%, 39%, −0.04 | **+10.0%, −0.9%, 60%, +0.114 [30%]** |
VALID t vs baseline: A selected +0.05, A 0.10%/4x −0.08; B selected +1.83, B 0.10%/4x +1.56 (all below 3.24). LIVE t vs
baseline: A selected −2.06, B selected −1.39 — the TRAIN pick (small size, 1x) is clearly worse live.

## Knob findings
- **Buying power: 4x beats 1x/2x live, at every risk level** (A 0.25%: 1x −0.4%, 2x +8.9%, 4x +15.9%; B: −4.0 / +0.9 /
  +12.5%). With a ~0.9% median stop, 0.25% risk = ~28% of equity per position, so 1x holds ~3-4 positions. On the lab
  (losing books) 1x "wins" only by taking fewer trades.
- **Risk %: what matters is risk ÷ buying power.** Uncapped (1000x) live avg R is +0.284 (A) / +0.205 (B); at 4x it falls
  to +0.20 at 0.10% and +0.155 at 0.25% (A), because the burst signals that BP turns away are the winners (same-direction
  bursts on big days, e.g. 10-22). Live at 4x: 0.10% best return/DD (A 13.0, B 10.6; DD < 1%); more risk buys more
  return only for A (+15.9% at 0.25%, +18.1% at 0.50%, DD −2.3% → −7.7%); B peaks at 0.25% (+12.5%, DD −4.3%) and
  falls to +1.2% (DD −13.6%) at 0.50%.
- **Quality-ranked allocation does not beat first-come.** Same risk/BP, QS / QX vs FC: live A 0.25%/4x +14.9 / +15.6 vs
  +15.9%; live B +12.7 / +12.2 vs +12.5%; VALID B −64.0 / −61.7 vs −67.0% (t 0.78 / 1.23). Signals in one 5-min bar are
  the same trade (same family, same tape), so ranking them changes little.
- **One-per-family-per-burst (FAM) hurts live** (A 0.25%/4x +6.4% vs +15.9%, t −1.95; B +1.7% vs +12.5%, t −1.64): it
  throws away the bursts that make the money on good days. It only "helps" on the lab because the books lose.
- **TRAIN weights (WT) add nothing** (VALID t +0.18 A / +0.49 B; live −0.08 / −0.04) — consistent with SZ-PROOF.
- **Quiet-day half size:** HQ1 (SPY |from open| < 0.15%) VALID A t −1.21, B +0.56; live +0.47 / +1.98 — signs disagree
  across books/windows, not a rule. HQ2 (SPY 30-min range < 20-day median): VALID +0.32 / −0.11, live −0.54 / +0.17 —
  nothing.
- **Burst half size (HB, 3rd+ same-family entry in 15 min):** VALID −1.34 (A) / +0.52 (B), live −1.68 / −1.05 — hurts live.
- **10% per-position notional cap** (sensitivity): baseline + cap, VALID t +0.31 / +1.64, live −0.01 / +0.76 (B live
  +16.7%, DD −2.0% vs −4.3%). Not over the bar; it shrinks tight-stop positions and frees BP. Worth a re-look on forward
  sessions only.

## Recommendation for live funds (plain words)
- Keep **4x intraday buying power** and **first-come**; do not add quality ranking, per-setup weights, family limits or
  quiet-day / burst half-sizing — none helped on VALID and the family/burst cuts hurt live.
- **Start live funds at 0.10% risk per trade** (not 0.25%): live paper 0.10%/4x kept ~2/3 of the 0.25% return (A +9.3%
  vs +15.9%, B +10.0% vs +12.5%) at a third or less of the drawdown (−0.7% / −0.9% vs −2.3% / −4.3%) with a smaller
  best-day share (30% vs 34-47%); and if the lab is right that these books have no edge, 0.10% loses less (VALID A −3.9%
  / DD −18.4% vs −7.1% / −34.8%; B −46.9% / −54.4% vs −67.0% / −75.6%). Step up to 0.20-0.25% only after the live-funds record itself holds (Phase 5 decay
  monitor). Not a proven edge — this is the lower-regret size, not a rule that passed the bar.
- Paper Primary is unchanged (today's rule is the baseline: 0.25% risk inside ~$4k lots); nothing to approve tonight.

## Rule changes inside the live window (research/ledger.jsonl effective dates)
Per-lot stacking (3 lots) 10-13; RW5-FD / RW3-FD to Primary 10-15, MF2-FD / MF4-FD 10-20 (moves 10-21); per-setup −2R
latch in Testing 10-20/10-23, off in Testing 10-23; GX1 5-minute clock gate (all accounts) 10-27; Primary lots ~$5k
10-28 → ~$4k 10-28; Primary per-setup −2R latch 10-29; Testing cost filter CF 10-30; L3-rsi5hi-FD / L3-fromopen-FD to
Primary 10-30; RW3S (T2) 11-03; DM-N3 + UNI1 (T2 top-500) 11-04. Live trades are rescaled to risk % here, so the lot-size
changes do not enter; blocked trades (latch, caps, CF, UNI1) are absent from the live list.

## Caveats
22 live sessions (t on 22 days fragile); paper fills (pnl_adj on). Lab: today's universe applied to the past
(survivorship), uncapped signal chains capped by the engine above, entry at bar close, costs as `bt_all.py`. VALID ends
2026-10-05; locked block 2024-11..2025-02 never read.
