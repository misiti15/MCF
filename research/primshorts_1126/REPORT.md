Educational only — not financial advice
# PRIMSHORTS-1126: Primary's short family at LIVE costs, and L3's place in Primary (research only, for the Fri 11-27 epoch)
Count: **+0 setup/exit configs** (cost-fix re-score). 2 cost-model specs tried (v1 adopted; v2 side split validated worse, dropped); counting cost models as R3C did, N ≈ 2,269 → ≈ 2,271. 8 lineup replays = decision context. bench10 engine unchanged; parity with benchmark.json ±0.005R (L3 T2 −0.133 vs −0.120). Locked block never read. No config/ledger/decisions.json change.
## 1. LIVE-L cost model (calib_live.py → cells_live.json)
32,131 cleaned live trades (10-14..11-25, 10 journals, exit-minute SIP bars): fill vs decision-bar close + exit slippage vs engine fill + LR8 fees. Fit cost_R = a/width_bps + b per price bucket × exit kind (spread part + stop-scaled slippage; e.g. $100+ stops 3.3 bp + 0.092R). Odd-day validation: live 0.122R/trade, LR8 0.079 (−0.042), LIVE-L 0.108 (−0.013).
Live minus LR8 by price: $5–10 −0.048 (LR8 too harsh) · $10–20 −0.029 · $20–50 −0.003 · $50–100 +0.036 · $100+ +0.081 (too lenient). By stop: <50 bp −0.009 · 50–100 +0.048 · 100–200 +0.046 · 200+ +0.021. The sub-$20 harshness is real but these setups trade few sub-$20 names (L3 16–44%, RW3/RW5 4–6%), so LIVE-L makes every short ~0.035R/trade worse on CHECK.
## 2–3. Re-score, Primary book rules (cap 30, −2R latch): avg R LR8 → LIVE-L [w/o best day; day t]; worst-5 = CHECK, AM/PM = CHECK LIVE-L
| Setup | FIT | CHECK | T2 | Worst-5 | AM / PM | Live: avg [w/o best; best-day share], t, worst-5, AM / PM |
|---|---|---|---|---|---|---|
| L3-fromopen | −0.136→−0.153 | −0.062→**−0.100** [−0.111; −2.8] | −0.133→**−0.126** [−0.134; −3.3] | −116.8 | −0.093 / −0.112 | all +0.086 [+0.019; 81% 10-20], t 0.65, −65.2, +0.129/−0.040 · Primary 231 tr −0.024 [−0.204], −55.3, −0.047/+0.047 |
| RW3 | −0.139→−0.175 | −0.048→**−0.088** [−0.098; −3.2] | −0.105→**−0.142** [−0.149; −4.7] | −74.2 | −0.088 / −0.089 | +0.100 [−0.001; 101% 10-22], t 0.67, −36.9, +0.095/+0.104 |
| RW5 | −0.121→−0.155 | −0.052→**−0.092** [−0.101; −3.0] | −0.143→**−0.177** [−0.184; −5.8] | −85.0 | −0.088 / −0.096 | +0.074 [−0.007; 109% 10-22], t 0.53, −39.0, +0.012/+0.108 |
| L3-rsi5hi (PSHADOW) | −0.098→−0.130 | −0.079→**−0.128** [−0.135; −4.4] | −0.125→**−0.135** [−0.153; −3.6] | −141.3 | −0.174 / −0.085 | −0.382 [−0.439], −231.2; 11-25: 311 Testing trades −219R (cap 150, no latch); w/o that day +0.09 / 213 tr |
| RW6 (PSHADOW) | −0.140→−0.166 | −0.076→**−0.119** [−0.131; −3.6] | −0.061→**−0.080** [−0.105; −1.3] | −74.5 | −0.123 / −0.116 | +0.031 [−0.206; 542% 11-12], t 0.16, −40.9, +0.137/−0.111 |
Every bench row is negative in every window under both cost models; every live record is `1 day`. Fair costs widen the live-vs-backtest gap (confirms R3C): it is not a cost artefact. In the bench L3-fromopen is no worse per trade than RW3/RW5; only its live Primary record singles it out.
Rule changes in the live window (ledger): moves 10-15 RW3/RW5 → Primary · 10-20 L3 in, 10-22 out, 10-30 back (with L3-rsi5hi, out 11-11); rules 10-27 GX1 · 10-28 sizing · 10-29 −2R latch · 10-30 Testing cost filter · 11-12 LR8/LR3 · 11-17 TSZ1 · 11-19 Epoch 1/U9-TGT/DQ-P4 · 11-23 burst brake/PSHADOW/Remedy-Q.
## 4. Lineup options: L3 + RW3 + RW5 + NM-ETF, minute engine (booksim.py), LIVE-L on shorts; book R/session (Δ vs a, paired t)
| Option | CHECK LO off | CHECK LO on | T2 LO off | T2 LO on | Live, 18 L3 sessions, LO off / on (worst-5) |
|---|---|---|---|---|---|
| a keep | −3.03 | −2.05 | −1.75 | −1.53 | +0.10 (−102) / +1.43 (−51) |
| b L3 → On Deck | −2.08 (+0.95, t 2.8) | −1.28 (+0.77, t 3.4) | −1.36 (+0.39, t 3.2) | −1.17 (+0.36, t 3.7) | +0.16 (−67) / +1.67 (−41); Δ t 0.02 / 0.19 |
| c L3 half size | −2.58 (+0.46, t 2.7) | −1.68 (+0.37, t 3.3) | −1.55 (+0.20, t 3.2) | −1.35 (+0.18, t 3.7) | +0.13 (−84) / +1.55 (−44) |
| d L3 latch counts open R | −2.77 (+0.27, t 1.3) | = a | −1.72 (+0.03, t 0.5) | = a | −0.07 (−72) / = a |
Same ranking at LR8 (b CHECK +0.58/+0.50, T2 +0.39/+0.36); FIT agrees (b +1.17). Per setup, removing L3 costs RW3 −4.6R and RW5 −6.0R on CHECK (they take the freed slots); NM-ETF is unchanged, so the gain is all L3's own losses. Live deltas are noise (L3 +31R on 11-12, −33R on 11-25). Caveats: (c) needs a per-setup size multiplier the engine lacks; (d) = (a) under LATCH-OPEN; the live replay only drops or rescales lots that were taken.
## DECISION draft (Friday 11-27 epoch; the owner decides; text only)
**PRIM-L3.** The evidence supports less L3 weight in Primary, not a verdict that L3 is uniquely bad: the bench rates all three shorts ~−0.09R/trade, but L3 drags the book most per session (12 trades/session) and its Primary record is −0.024 (−0.204 w/o best day).
Recommended: **(b) L3-gap-slope-fromopen-FD Primary → On Deck (move), together with LATCH-OPEN**: CHECK +0.77, T2 +0.36 R/session (t 3.4 / 3.7); re-entry by C3-BAR2 from On Deck, so not final. Alternative if no move yet: **(c) half size**, about half of (b)'s gain, but needs a size-multiplier change with tests first, so not live 11-27. Do not adopt (d) alone (weak on T2, redundant under LATCH-OPEN).
Not now: cutting RW3/RW5. The bench says they lose too, but their live records are positive (`1 day`); per the no-premature-decisions rule, keep them and re-check at 20 Primary sessions under LIVE-L.
Either way: change outside 09:30–16:00 ET; ledger entry + `python -m mcf.research.ledger check`; regenerate `docs/live/assignments.json`; skeptic review. Backlog: research fill models should charge LIVE-L instead of LR8. Scripts: research/primshorts_1126/*.py; outputs rescore.json, options.json, calib_live.json.
