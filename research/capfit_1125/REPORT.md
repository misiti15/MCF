Educational only — not financial advice

# capfit_1125: should each strong setup get its own rolling daily loss cap? (research only)

Owner idea 11-25: replace the uniform −2R per-setup daily cap with a per-setup cap at the level where that setup's losing days typically "bottom out" before recovering, recalibrated on a rolling basis; also check a per-trade point of no return.

Pre-registered (PLAN.md, sha256 9c97ace7…43b1). Setup set: the top 20 by avg R per trade without best day (≥ 20 live trades, ≥ 8 sessions) plus NM-ETF = 21 setups; only 12 are positive without their best day and 17 carry the `1 day` tag. Live: 10-06..11-24, LR8, deduped. Lab: bench10 lots for the 4 Primary setups + GEN-261029-06, GEN-261023-06, ST5 (2023-24 / FIT / CHECK; locked block never read). Grid L ∈ {−1.0 … −4.0 step 0.25, none}. Policies: P1 (shallowest level with positive past gain and no negative deeper gain), P2 (P1 bounded to [−4, −1.5]), P3 (greedy best past level); baselines none and uniform −2R. Walk-forward weekly, min 8 sessions (5 as sensitivity). Bar: t ≥ 2.0 vs both baselines, more setups better than worse, no setup worse by > 3R.

## Verdict: No, not yet
- No knee: once a strong setup is down 1.5–4R, P(the day still ends above that level) is flat at ~0.25–0.39 (live) and ~0.2–0.5 drifting by period (lab). There is no level where recovery suddenly stops.
- Per-setup levels are unstable: the same setup's chosen level flips between −1R, −3R and none across lab periods (RW3 ranged over six levels within 2023). On a zero-expectancy (re-priced) book no per-setup rule beats a random trim (best t +0.99); the calibration really learns "this setup has been losing lately".
- Live walk-forward (155 setup-days, 16 setups, 22 dates): P1 102R vs none 147R (t −0.83); best version P2 roughly level with none and slightly ahead of −2R, almost entirely from not latching RW7 (+49R) — the known rules_1122 effect, not setup-specific timing. Best t 1.26 (estimated with latch-skipped what-if rows) vs bar 2.0.
- Per-trade: a soft point of no return exists around −0.75R (only 8–18% of trades end ≥ 0 after it), but a tighter stop there loses R on strong setups (L3-fromopen −37.7R lab, NM-ETF −14.7R lab; live −0.5R/−0.25R stops −43R/−125R net). It "helps" only setups that lose on average (RW3/RW5 lab, RW7 live). Consistent with ETF-STOP50.

## What would make it work (backlog)
Re-test when candidates have ≥ 40 live sessions; calibrate on the zero-expectancy book; accept a level only if the same knee (±0.25R) appears in ≥ 2 of 3 lab periods with positive neutral gain in each. If it ever passes: nightly calibration from trailing 60 active days, bounds [−4, −1.5], weekly update, Primary changes only at the Friday epoch with the owner's yes. Meanwhile the cleaner targeted remedy stays the existing backlog item: exempt the gap-down short family (esp. RW7) from the −2R latch.

Rule-change context: −2R latch in Testing 1/2 10-19..10-22 only, Graveyard from 10-21, Primary from 10-29 (33 of 109 days touching −2R were censored by the real latch, mostly Primary — handled with the journals' latch what-if rows as an estimate); L3 promotions 10-21/22/30; NM-ETF to Primary 11-11; LR8 re-costing; TSZ1 11-17; C3-EPOCH 11-19; burst brake / Remedy-Q / PSHADOW 11-23; owner LATCH-CLOSE no (11-21). Scripts/data: scratchpad capfit/ (not committed).
