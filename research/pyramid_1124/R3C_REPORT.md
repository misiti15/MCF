Educational only — not financial advice

# Project Pyramid round 3 — Team C: live-calibrated costs and a re-score of every candidate (2026-11-25)

Research only. Pre-registered (R3C/PREREG.md, 14:57 UTC; addendum 15:02 UTC before model 2 was scored). 2 configs (cost models). Live: 29,420 cleaned run-1 trades from 10 journals, 10-06..11-24, joined to their submitted signals; exit-minute SIP bars via Alpaca GET. Locked block never scored.

## Headline — corrects round 2 Team G
- Counting entry slippage (~+5 bp vs the decision-bar close) and exit slippage, live trades cost 0.122R per trade vs 0.079R in the research model: the research model is ~0.042R per trade too LENIENT overall (gap-down family 0.108 live vs 0.065 research; L3-fromopen 0.100 vs 0.089). It is too harsh only on $5–20 names (+0.03..0.05R), which are few in the lab.
- Model 1 (live-calibrated; fit on even days, validated on odd days; overall error +0.000R) accepted; model 2 (adds stop width) failed its acceptance rule and is a sensitivity only.
- No candidate's verdict improves; five drop to FAIL (G B3+TT1, G A1+TT1, L3 A1t, L2 C3a, ULT-22). The top-10 benchmark also gets worse (check median −0.037 → −0.082). 0 candidates beat the top 10 in both halves under any model.
- The live-vs-backtest gap for the gap-down shorts is not a cost artefact; on fair costs the gap is larger.

## Survivors (TIER B under all models; forward-test only)
- NM-ETF-late-dip-di-long + "SPY ≥ open" gate: check +0.117 (w/o best day +0.094, best day 29%), t 2.32, win 68% vs 55% break-even — beats the top-10 best on check but loses on 2023-24 (−0.056) and trades 0.33 per session.
- NM-ETF + TT1 (check +0.060, best day 79%); L2 C1a capitulation seed (`1 day`, best hedge piece); GEN-261019-02 (≈ break-even); NM-RWN4 and CWT09 (benchmark, `1 day`).

## Next (backlog)
Backtest fill models should charge the measured ~+5 bp entry slippage instead of 1c + 1 bp; add a spread/liquidity term (needs a lab-side spread proxy). NM-ETF + SPY gate stays the only long worth forward-testing.

Rule-change context (live window): 10-28 Primary sizing; 10-30 testing cost filter; 11-12 LR8; 11-16 SPYEXIT; 11-17 TSZ1; 11-23 burst brake. Slippage is from Alpaca paper fills. Scripts: scratchpad pyramid/R3C/.
