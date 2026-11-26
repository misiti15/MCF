Educational only — not financial advice
# squeeze_1125: book-level remedies for swing-midday-flip (one-sided short book during an index reversal), research only
Pre-registered (PREREG.md, sha256 702eccc…3c57, 06:12 UTC 11-26). 5 configs: R1 NET-BETA BUDGET B 8/12/16 (no new same-direction entry while |net beta-weighted open R per 1% SPY| is past B), R2 SQUEEZE EXIT reclaim VWAP/OPEN (SPY ≥ 0.4% below open earlier, back above VWAP/open, 30-min return > +0.5% → close all shorts and no new shorts; mirrored for longs). Cumulative N ≈ 2,264 → **≈ 2,269**. Bench: neveragain minute engine, Primary P4 lineup and book rules (BASE −1,713R; hsscale −1,710R), bench10 lots rebuilt tonight (52,544 candidates, LR8 + borrow), 861 sessions (CHECK 276, T2 415, FIT 170); locked block never read. Live: Primary journal 10-23..11-25 (928 lots), Alpaca 1-min bars. Scored book RAW; "Z" = zero-expectancy book (each lot shifted by its setup's average), shown so trading less on a losing book stays visible.

| Config (vs ref) | CHECK dR/yr | Worst-5 CHECK | Worst-5 T2 | Days ≤ −10R CHECK / T2 | Recovered-day dR | Fires/yr CHECK / T2 | Best-day share | Z dR/yr pooled (CHECK) | Setups better / worse (RAW) | Live dR (11-25) | Bar |
|---|---|---|---|---|---|---|---|---|---|---|---|
| LO vs BASE (context) | +175 | −34.3 → −24.5 | −24.7 → −14.6 | 57→38 / 29→21 | −68.7 | — | 6% | +54 (+81) | 4 / 0 | +33.2 (−40.1 → −8.3) | ref |
| **LO+B8 vs LO** | **+78** | −24.5 → −12.9 (**47%**) | −14.6 → −11.4 (**22%**) | 38→15 / 21→4 | +22.7 | 185 / 118 | 11% | **−41 (−154)** | 4 / 0 (Z: 1 / 3) | +27.9 (−8.3 → −8.3) | **PASS** |
| LO+B12 vs LO | +42 | 42% | 11% | 38→25 / 21→11 | +25.9 | 139 / 82 | 19% | −43 (−121) | 3 / 1 (RW3 −3.2) | +22.3 | FAIL (T2) |
| LO+B16 vs LO | +40 | 34% | 9% | 38→31 / 21→13 | +30.5 | 106 / 50 | 27% | −34 (−97) | 3 / 1 (RW5 −0.2) | +25.6 | FAIL (T2) |
| LO+SV vs LO | +76 | 4% | 1% | 38→33 / 21→18 | +2.6 | 35 trig, 27 acted / 39 | 15% | **+43 (+22)** | 3 / 1 (NM-ETF −5.2) | +14.8 (−8.3 → 0.0) | FAIL (tail) |
| LO+SO vs LO | +74 | 4% | 1% | 38→33 / 21→18 | 0.0 | 28 trig, 23 acted / 30 | 14% | +34 (+52) | 3 / 1 (NM-ETF −10.6) | +22.1 (−8.3 → 0.0) | FAIL (tail) |

**Without LATCH-OPEN (each vs BASE):** B8, B12 and B16 all pass. Worst-5 improves by 50/50%, 48/43% and 43/36% on CHECK/T2, all 4 setups are better, and CHECK gains are +200/+167/+118R/yr. SV and SO fail (worst-5 improves only 1–3%). B8 is the only config that passes both with and without LATCH-OPEN, and its gain is not one-day carried (best day 11%).
**Per setup (owner's remedy rule; RAW, pooled, dR vs ref).**
- **LO+B8:** L3-fromopen +121.3, RW3 +73.3, RW5 +132.6, NM-ETF +3.9 (4 better, 0 worse). On Z: NM-ETF +5.5; L3 −26.6, RW3 −42.6, RW5 −75.6 (1 better, 3 worse).
- **LO+SV:** L3 +106.6, RW3 +65.2, RW5 +62.2, NM-ETF −5.2 (3 better, 1 worse). On Z: +58.8 / +47.0 / +39.0 / +0.6.
- **Live, LO+B8 vs LO:** RW5 −16.2, L3 −10.3, RW3 −0.1; MF2 +39.2, MF4 +10.6 (4 setups better, 3 worse).
**Honest read.**
- **R1-B8 passes the pre-registered bar but acts as a cap that is nearly always on, not a squeeze remedy.** It fires on 185 of 252 sessions a year and takes about 29% fewer lots. On the Z book it costs −154R/yr on CHECK, and all 3 gap-down shorts get worse. Most of the RAW gain comes from trading a losing book less. Label: **insurance, not edge** (red→green days 40, green→red 25).
- **R2 barely changes the worst days.** Most worst-5 days are not V-reclaim days.
- **R2-SV is the only remedy positive on the Z book in all 3 periods** (FIT +179, CHECK +22, T2 +0.8 R/yr). This was seen after the run, so it is a lead, not a pass.
- **11-25:** R2 fired at 10:04 on the early V (SPY −0.9% at 09:44, then back above VWAP), not at the 11:56 turn, and it blocked all 41 shorts. R1-B8 alone took the day from −40.1 to −18.1R. With LATCH-OPEN the day was already −8.3R, and B8 adds nothing.
**DECISION draft (Friday 11-27 epoch; the owner decides; decisions.json not edited).** NETBETA-B8.
- **Option A, recommended: Testing-first shadow.** The Primary and Testing 1/2 journals log a `netbeta_block` tag wherever B8 would block an entry. No trades change, so there is no playing-time cost. Review after 20 Primary sessions: shadow dR on actual lots, red-day share, and fires per session.
- **Option B, Primary option:** enforce B8 on top of LATCH-OPEN, labelled insurance. Expected effect: live worst-5 −16.8 → −11.8R, about 29% fewer lots, Z cost about −40R/yr once the book is at break-even.
- **Either option:** ledger entry + `python -m mcf.research.ledger check`, skeptic review, outside 09:30–16:00 ET. **Also:** add R2-SV as a journal-only forward tag (≤ 1 config). Do not adopt B12/B16 (fail T2) or SO.
**Rule-change context (ledger), live window 10-23..11-25.**
- Changes in the window: 10-28 Primary sizing; 10-29 −2R latch (Primary); 11-11 NM-ETF to Primary; 11-12 LR8; 11-16 ROT1; 11-17 TSZ1; 11-19 C3 Epoch 1; 11-20 stop rounding / FOOTRACE-EXIT; 11-21 cost-basis fix; 11-23 ST7 out, BRAKE-BURST, PSHADOW.
- The live base applies the −2R latch and −20R halt as a what-if on every day. The MF2/MF4 lots are early-window Primary setups; the bench covers today's 4 setups only. Caveats: β is a 60-day daily beta, shrunk; buying power is not modelled; the live window is 24 sessions. Scripts are in research/squeeze_1125/*.py.
