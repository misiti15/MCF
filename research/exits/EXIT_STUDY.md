# Exit / time-in-trade study (2026-10-06)

*Educational only — not financial advice.*

**Question:** when should each live setup get out to make the most of winners and cut losers? Entries were left unchanged and only exits were tested.

**Data:**
- The live setups' own entries on SIP 1-minute data, Jul 8 – Oct 5 2026: 3,237 signals.
- Train: to Aug 25. Valid: Aug 26 – Sep 15. Test: locked and not used, because nothing passed valid.

**Search:**
- One swarm agent per setup, plus an auditor. 489 exit configurations were tried in total.
- Families: time stops, breakeven moves, trailing stops, target size, stop size, and earlier time exits.
- To pass, a rule had to beat the current exits by at least +0.03R on both train and valid, without dropping trades and without depending on one day.

## Verdict: keep the current exits on all five setups

| Setup | Current exits (train / valid) | What time in trade shows | Verdict |
|---|---|---|---|
| orb20_a | +0.056R / +0.050R, average hold 3–4 h | Losers resolve early (trades closed within 30 min averaged −0.27R); winners resolve late (held over 2 h, +0.22R). Stalled trades (below +0.5R at 60 min) bleed a little; early time exits cut the late-day drift that is this setup's edge. A 60–90 min time stop for stalled trades kept about the same result in half the holding time, but did not improve it. | Keep. Retest the stalled-trade time stop on more data. |
| heat_fade_short | +0.107R / +0.180R | The fade works within 30–60 min (median target hit 26 min). After that open trades go flat but do not bleed. Time stops, breakeven moves and trails all made it worse. | Keep |
| heat_fade_long | +0.091R / −0.025R | Slow (median target hit 73 min). 35% of trades are still open at 15:55 and average −0.07R. Every exit tweak that helped on train hurt on valid. | Keep exits. The setup itself is weak on valid: watch it. |
| exhaustion_short | +0.245R / +0.178R | Holding longer helps and cutting early bleeds. Wider targets (1.25–2R) passed the gate, but 85–99% of the train gain came from one day (Jul 29); without it the gain is +0.004 to +0.019R. | Doubtful. Keep the 1R target and retest as live data accrues. |
| intraday_momentum | −0.028R / +0.033R | Every trade lasts about 25 min (15:30–15:55) and costs about 0.09R per round trip. Earlier exits looked good on train and failed on valid. | Keep. Break-even at best. |

## Findings beyond exits
- **The R-unit trap.** Position size is capped by the slot (about $1,930), so the 0.25%-of-equity risk cap never binds. A tighter stop then only makes R smaller: results look better in R but are not better in dollars. The heat_fade_short "tighter stop" passes were this artefact. Future studies report stop-size changes in the original R units, or in bps of notional.
- **The day-clustering trap.** Many train "wins" came from one or two days. The auditor's paired, day-clustered checks are now part of every exit study.
