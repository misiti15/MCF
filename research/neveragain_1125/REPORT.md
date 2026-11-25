Educational only — not financial advice

# neveragain_1125: guards against squeeze days like 11-25 (research only)

Owner 11-25 midday: "A day like today simply cannot happen… explore ways of making sure this doesn't happen again." Pre-registered (PLAN.md, sha256 1e6e33e4…99de, 17:50 UTC): 8 guards + 1 disclosed combo + 20 placebo draws. Bench: s8cap/hsscale minute engine re-implemented, lineup P4, books RAW / zero-expectancy / +0.10R per lot, 738 scored sessions, locked block never read. Live: Primary journal 10-06..11-25 (11-25 through 13:02 ET), Alpaca SIP minute bars, 100% coverage.

## What happened on 11-25
Gap-Down Recovery Fade (L3-fromopen) took 30 lots and RW3 5, all 10:20–12:00 ET (17 L3 lots 11:15–11:40) while SPY was still below its open; SPY/IWM then V-reversed (+1.4% in ~30 min). Replay: −20R ~12:05, −32.6R 12:18, −37.4R by 13:00 (actual LR8 −39.6R so far). Main cause: the −2R per-setup latch counts CLOSED R only, so L3 kept entering while open losses piled up.

## Results (failures first)
- G3 squeeze guard (no new gap-down shorts while SPY and IWM ≥ +0.5% over their open and rising): FAIL — negative in every bench period, worse than placebo; would not have helped 11-25 (condition true only from ~12:15).
- G2-6 (≤ 6 open lots per setup, as a risk cap): FAIL — costliest on a profitable book (−186R/yr); cuts recovery days (10-22 +62.7 → +15.6R).
- G4 (SCALED-K4 alone): insurance only; 11-25 flatten at ~−32.6R vs −39.6R; deepened one CHECK worst day when used alone.
- G1-2 (the −2R per-setup latch counts closed + OPEN R; no new entries, nothing flattened): best insurance — 11-25 replay −37.4 → −8.3R; live worst-5 −28.2 → −17.0R; bench days ≤ −20R cut ~75% (33 → 8 in 2.9 yrs); all 4 setups better at zero expectancy. Costs ~20% of lots; on a +0.10R/lot book −87R/yr and more green→red days; cuts recovery days (11-12 L3 +31R → +1R). Not skill — insurance (t 1.77; fails "positive in every period").
- G1-3 (−3R variant): milder; 11-25 −37 → −23R; one third of the profitable-book cost.
- No guard passes the full bar; nothing qualifies as an evidence-based emergency rule.

## "Positive every single day"
Bench: even a +0.5R per lot book (≈ 5× anything seen live) is red 11% of days; live Primary is −0.11R per lot and red 25 of 36 days. Realistic targets: no day worse than ~−20 to −25R; worst-5 average ~−17R; green days > red days once per-lot edge is positive. All-green needs setup quality, not risk rules.

## Recommended change set (Friday 11-27 epoch; owner's yes, skeptic review, ledger)
1. SCALED-K4 + SHOCK-V + bug guards (s8cap_1125), keep the fixed −20R halt.
2. G1-2: per-setup −2R latch counts closed + open R (implementation: per-setup open marks — risk.py latch reads realized_r_by_strategy; the runner already marks lots for the LR3 halt). Re-check after 20 Primary sessions; relax to −3R if Primary shows real positive edge.
3. Do not adopt G2 or G3.
Owner may choose G1-2 as a stopgap sooner (owner's insurance choice, applied outside market hours with a ledger entry).

Rule-change context in the live window: L3 promotions 10-21/22/30; Primary −2R latch 10-29; NM-ETF to Primary 11-11; LR8 11-12; TSZ1 11-17; C3-EPOCH 11-19; burst brake / Remedy-Q / PSHADOW / ST7 out 11-23. Scripts/data: scratchpad neveragain/ (rerun.sh re-scores after the close).
