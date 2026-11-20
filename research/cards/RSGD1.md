# Mechanism card RSGD1 — relative-strength LONG on SPY gap-down mornings (Mechanism Scout, 2026-11-19 ~20:30 ET)
Educational only — not financial advice. USAGE1 gap team (research/usage_review_1118/APPLY_1118.md). Plan only; nothing scored.
Gap targeted: the top gap named in USAGE1 ('which name and which side' for the ~4.5 missed non-ETF moves/day with >= 1 ATR left
after 09:50; A1 / SIDEHUNT). research/gaps/GAPS.md does not exist yet, so this uses the gap USAGE1 names.

## Mechanism (C3-MECH: day-type known by 09:50 + falsifiable reason)
- **Day type (known at 09:30):** SPY opens <= -0.30% vs the prior close (a market-wide gap-down). 102 of 453 sessions in the 2-year history.
- **Reason:** on a market-wide gap-down, index and ETF selling hits every name. A name that opens flat or up AND holds above its own
  09:30 open through 09:50 is absorbing that selling: idiosyncratic demand (news, accumulation) is beating the tape. Once the
  market's opening selling exhausts, the absorbed demand should carry the name higher for the rest of the day.
- **Falsifiable:** if absorption carries no information, these names' 09:50 -> 15:55 return (ex-market) equals that of random in-play
  names with the SAME 09:30-09:50 return on the same days. The control matches the competitor exactly, so a relabel of the early move
  cannot pass (SIDEHUNT step-0 lesson).

## Rule (2 parts, pre-registered)
1. SPY open / prior close - 1 <= -0.30% (day type).
2. Stock open / prior close - 1 >= 0 AND the 09:50 price > the 09:30 open. Universe: ADV20 >= $95M, non-blackout, not an ETF (strict ETF list).
Entry long at the 09:50 decision bar; exit at 15:55 (time exit) or a stop at the 09:30-09:50 low. One trade per symbol-day. Costs LR8.

## Test (for the Builder, one look)
- Engine: an EXISTING one (ENG1-A), namely the MCF 2-year lab frames with the production cost model, as used by the mh-* tests. No new simulator.
- Controls: (a) random same-day in-play longs matched on the 09:30-09:50 return bucket (the competitor); (b) ex-market (beta x SPY over the hold).
- Report: gross, then net; day-clustered t; avg w/o best day and best-day share; TRAIN / VALID split; per-month signs.
- **Power, stated before any look:** with ~102 qualifying days and ICC ~0.22, the MDE floor is (2.64 + 0.84) x 1.0 x sqrt(0.22/102)
  = **~0.16R per trade**. Smaller effects are invisible here. A close says 'nothing above ~0.16R'.
- Configs: 1. Lineage: relative-strength longs (t4-rel-strength 30 + rw-t4 long variants 2 + this 1 = **N 33**) -> bar max(1.5,
  sqrt(2 ln 33)) = **2.64**.
- Overlap: the owner's PK1 (t4-rel-strength re-test after 09:50) is the unconditioned parent. RSGD1 is its day-type sub-case, so the
  parent session should not run the same day-type slice twice.

## Guardrail check (rule 26)
Not a day-type switch on a live setup: the day type is part of a NEW setup's entry (allowed by C3-MECH). Not a CWT variant, sizing
tilt, cap, or GEN output. Long side (live shorts' ETB gate does not apply).
