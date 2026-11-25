Educational only — not financial advice

# WT1 wide target: FROZEN 2026-11-25 (watch-only forward shadow)

*Research only. Journal-only: no order, no config, no setup or exit change, nothing sent to the runner, no account runs this.*

Owner 2026-11-25: "WT yes". Source: crunch Wave 2 item 5, class **Y1** (`research/crunch/wave2/exits/RESULTS.md`,
`research/crunch/WAVE2.md` §5 and the Skeptic note, `research/crunch/FINAL.md` item 8) and its never-started shadow
**WB2-Y1-SHADOW** (`docs/live/decisions.json`: approved as optional / deferred 2026-11-21, batch D). This file states Y1
as it was found. It is not re-tuned. Any change to anything below is a new rule with a new freeze date and a fresh count.
Configurations tried: **1** (this rule). Lineage behind it: W5 16 configs + Wave 2 15 looks = 31 (bar 2.62 vs t 2.58,
the reason it is forward-only).

## 1. Rule (frozen)

- **Setups:** Gap-Down Pop Fade Heavy Selling `RW3-gapdn-rsi5pop-flowsell-short-FD` and Gap-Down Pop Fade
  `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD` (both Primary, exit t1s1: 1R = 0.25 x daily ATR, target 1R, 15:55 flatten).
- **Change:** the take-profit sits at **1.25x the live target distance** from the signal price. t1s1 is symmetric, so
  the signal reference is (stop + target) / 2 and wide = ref + side x 1.25 x |target − ref|, rounded to the cent toward
  the entry (the live 11-20 rounding direction). For a short it is 0.25 R further below the live target.
- **Everything else identical:** same signals, entries, fills, share counts, stop price, 15:55 flatten, and for the WB4
  copies their SPY-since-entry exit (RW3-WB4 +0.30%, RW5-WB4 +0.40%). No trail, no scale-out, no stop move.

## 2. Accounts and lots

Every closed live lot (journal runs of kind `whatif` / `shadow` excluded, so BASE1 / PSHADOW rows never count) of RW3 /
RW5 **and any copy of them** (a setup named parent + `-suffix`) in any account: today Primary (`mcf-data`), the
Remedy-Q copies `-RQa-1230` (Testing A = testing2, Testing B = explore1, from 11-23) and the SPYEXIT copies `-WB4`
(Live Lab, Testing D). A new copy added later is picked up by name. **One signal, one count:** a lot is logged but not
scored (`dup = 1`) when an account earlier in the order Primary, testing, testing2, explore1, livelab, testingd,
testinge, testingf, gen, graveyard already holds a lot of the same family, symbol and side signalled within 5 minutes.
RW3 and RW5 on the same symbol are different setups and both count.

## 3. Method (per lot, `shadow.py`)

- **Parent arm** = the live exit parts priced with the LR8 live cost model (`mcf.costs.lot_costs`); it reproduces the
  journal's R after costs (max |diff| 0 on the 2026-11-12..11-24 lots).
- **Wide arm:** the walk from the entry is identical to the live lot until the live target fills, because a path can
  only reach the wider target through the live one. So a lot that ended by stop, flatten, SPY exit or anything other
  than a target fill has **ΔR = 0** with no bars needed. A lot whose live target filled is re-walked on **Alpaca 1-minute
  SIP bars** (read-only market-data GET via `mcf.replay.store._fetch_bars`; keys from the environment, never written)
  from the fill bar: per bar, SPY exit at the open (WB4 copies, from the next bar) → stop (fill bar: at the stop price;
  later bars: at the stop, or the open if it gapped through) → wide target (fills only on a touch-through of
  max(1c, 3 bp)) → 15:55 flatten at the open. A stop is taken before a target inside a bar (conservative). The wide arm
  is priced with the same LR8 model. **ΔR = R_wide − R_parent**, per lot, in the lot's own R (risk = |entry − stop| x
  shares).
- `bars_check` flags a lot whose fill bar does not reach the live target on the SIP bars (reported, not excluded).
- Not modelled: Primary's −2R per-setup latch reading realized R later, partial fills, U9-TGT quote checks. The paired
  ΔR is per lot as taken.

## 4. Pass bar (fixed now, scored once)

Forward sessions from **2026-11-23** (C3 rule epoch) onward. 11-23 and 11-24 were backfilled on 11-25, the freeze day,
before their results were looked at, and count. The 2026-11-12..11-20 sanity backfill is seen data: reported, never
counted. Scored **once**, at the first nightly `--score` with **≥ 20 complete sessions and ≥ 60 scored lots**. PASS needs
**all** of:

1. ΔR per lot **> 0**, with a **day-clustered t ≥ 1.5** (trades within a session are not independent).
2. **ΔR per lot without the best ΔR session > 0**, and the best session's share of the total ΔR **< 50%** (one-big-day).
3. **Both setups not worse:** total ΔR ≥ 0 for RW3 (parent + copies) and for RW5 (parent + copies), each with the
   better / worse lot counts reported (Remedies rule).
4. **Primary alone:** total ΔR > 0 (the decision is a Primary exit change).

Harm stop: at any nightly score with ≥ 10 sessions, ΔR per lot < 0 with day-clustered t ≤ −2.0 → retire early.
Every score also prints parent vs wide avg R and avg R w/o best day, the wide-arm exit mix of the changed lots
(target / flatten / stop), and per account.

## 5. Decision it feeds

PASS → write it up as a **DECISION for the owner**: a Primary exit change for RW3 / RW5 (target 1.0 R → 1.25 R), made
only in the **Friday-after-close epoch window** (C3-EPOCH), with the owner's yes, the adversarial review, a ledger entry
(`research/ledger.jsonl`, PROT-27 t1s1 guard evidence: beat t1s1 on the same signals, per setup, costs in, ≥ 15
sessions), never during 09:30-16:00 ET. Copies follow their parent only if the owner says so. FAIL or harm stop →
retire WT1, logged, no re-tune on the same forward data (WB2-NEXT-2 / 1.5x stays closed).

## 6. Backfill on the freeze day (2026-11-25)

| window | sessions | scored lots | target fills changed | ΔR / lot | day-clustered t | ΔR total | wide exits of changed lots |
|---|---|---|---|---|---|---|---|
| **Forward 11-23..11-24 (counts)** | 2 | 37 (33 Primary) | 6 | −0.014 | −0.27 | −0.53 R | 4 target, 2 flatten |
| Sanity 11-12..11-20 (not counted) | 7 | 109 (103 Primary) | 45 | +0.052 | 3.97 | +5.66 R | 30 target, 15 flatten, 0 stop |
| of which 11-18..11-20 (after the Y1 sample) | 3 | 52 | 20 | +0.046 | 2.74 | +2.41 R | 14 target, 6 flatten |

Forward so far: RW3 −0.01 R (3 better / 1 worse), RW5 −0.52 R (1 / 1); 11-23 −1.18 R (VTR: RW3 and RW5 in Primary filled
the live target near 12:44 and the wide arm was flattened at 15:55; the RW5 RQa copy's VTR lot is a logged dup), 11-24 +0.65 R. Two sessions say
nothing yet. Sanity window: RW3 +2.83 R (19 better / 6 worse), RW5 +2.83 R (16 / 4), best ΔR day 11-17 = 28%.

**Rule changes inside these windows** (`research/ledger.jsonl`): 11-12 LR8 cost model; 11-16 ROT1; 11-17 TSZ1, WB
copies, SPYEXIT WB4 copies, promotion hold; 11-18 GY-BENCH, SRCV1; 11-19 C3 batch (C3-EPOCH / BASE1, EXIT100, BAR2,
ROT), U9-ETB, U9-TGT; 11-20 FOOTRACE-EXIT, stop / take-profit rounding, ultimate_1119 admissions; 11-23 Remedy-Q
`-RQa-1230` copies (new RW3 / RW5 lots in Testing A / B), BRAKE-BURST, BRAKE-WATCHDOG, ST7-MOVE, Friday-review moves,
PSHADOW, beginner_1120 admissions. None changes RW3 / RW5's exit; the paired ΔR is unaffected by sizing changes.

## Running it

    python research/forward/wide_target/shadow.py --date YYYY-MM-DD     # after 16:15 ET (idempotent; re-run replaces the day)
    python research/forward/wide_target/shadow.py --score               # running tally vs the pass bar
    python research/forward/wide_target/shadow.py --score --start 2026-11-12 --end 2026-11-20   # sanity window

`forward.csv`: one row per lot (upsert by date): account, setup, family, prices, live target and wide target, live
and wide exit / reason / time, R_live (journal), R_parent, R_wide, dR, bars_check, dup, status. `days.csv`: one row per
session (lots, scored, target fills, changed, ΔR, status). A run before 16:15 ET on the same day writes `pending` and
fetches nothing (the live job owns the market-data quota).
