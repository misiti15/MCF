Educational only — not financial advice

# s8cap_1125: per-setup cap + lineup-scaled account stop — one package (research only)

Owner 11-25: finalize ONE package — a per-setup cap that lets setups breathe + an account stop that never halts prematurely but stops a crash/glitch. Pre-registered (PLAN.md, sha256 632964e3…ed26, 15:05 UTC): 8 candidates (per-setup closed + open cap at −6R, −8R, −10R, or σ-scaled clip(1.5σ, 4, 12)R; each with the −2R latch kept (L) or replaced (N)), all with SCALED-K4; bar t ≥ 2.0 (≈ 3.0 counting earlier studies), positive in all three periods on the zero-expectancy book, no setup worse by > 10R, worst day not worse, live not worse. hsscale engine re-simulated minute by minute; lineups P4 (today's Primary) and P9; RAW / zero-expectancy / +0.10R books; ~2.9 scored years; locked block never read. Live replay: all journals 10-06..11-24, LR8.

## Verdict: none of the 8 per-setup caps passes
- Zero-expectancy book: every latch-on cap loses R on P4 in CHECK; best t +0.11; at least one setup > 10R worse in every variant (gap-down shorts RW3/RW5/RW7 recover from deep holes and are hurt; L3-fromopen helped). "R saved on bad days" ≈ "R lost on days that recovered" — the same no-knee finding as capfit_1125.
- Caps do buy a shallower tail: P4 worst-5 days −34.9 → −24..−32R; P9 −72.7 → −46..−58R; cost ≈ 3–90R/yr on the zero-expectancy bench — insurance, not edge.
- Dropping the −2R latch ("let setups breathe") loses in every bench comparison (−40R/yr P4, −98R/yr P9 at zero expectancy); every latch-off cap is worse than its latch-on twin. (On a +0.10R-edge book the opposite holds — the latch question depends on whether the book has real edge.)
- Live replay favours caps (Primary C8L +37R, t 2.31; C6L +46R at zero expectancy), mostly from runaway account-days on a wide lineup of losing setups; only 36 Primary sessions and 44% of lots with minute bars — SCALED-K4 + SHOCK-V already handle runaway days at the account level.
- Side finding: the scaled no-new-entries halt H = max(20, 0.6X) costs R on larger lineups; keep the fixed −20R halt.

## Recommended package (Primary change: Friday epoch, skeptic review, owner's yes, ledger)
SCALED-K4 account stop (flatten + no new entries at −X, X = clip(4σ, 2.5R×N, 8R×N); ≈ −32R today) + SHOCK-V glitch failsafe (no new entries + alert on a sharp R drop within 2–10 minutes) + keep the −2R per-setup latch + keep the fixed −20R no-new-entries halt + bug guards (broker-vs-journal $ mismatch, order-size guard). No per-setup crash cap.
Optional owner insurance (did not pass the bar): C10L — per-setup −10R closed + open cap with the latch kept; zero-expectancy cost −3R/yr (P4) / −21R/yr (P9); worst day not worse in any period; live Primary +18R at zero expectancy; fires ~10–13×/yr per main setup (RW7 ~67×/yr on P9). Re-test at ≥ 40 Primary sessions with full minute bars.

Rule-change context: −2R latch Testing 1/2 10-19..10-22, Graveyard from 10-21, Primary from 10-29; L3 promotions 10-21/22/30; NM-ETF to Primary 11-11; LR8 re-costing; TSZ1 11-17; C3-EPOCH 11-19; burst brake / Remedy-Q / PSHADOW 11-23. Scripts/data: scratchpad s8cap/ (not committed).
