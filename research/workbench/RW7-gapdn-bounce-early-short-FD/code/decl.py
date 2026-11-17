# RW7 one-part tweaks, every part P2..P27 + new layers (declared 2026-11-16 ~16:10 ET after the live component analysis
# and the parent replay parity check, BEFORE any variant or 2-year score). PARENT = RW7 as it runs in Testing F now
# (refire off, cap 30, <= 3 lots/symbol, no latch, account cost filter stop cost <= 0.15R).
from sim2 import BASE
D = lambda **k: dict(BASE, **k)
ROUND1 = {
 "PARENT": BASE,
 "V01 ADV >= $150M (P2)": D(adv=150e6),
 "V02 price >= $10 (P3)": D(minpx=10.0),
 "V03 window start 09:50->10:15 (P6/P7)": D(w=(1015, 1500)),
 "V04 window start 09:50->11:00 (P6/P7)": D(w=(1100, 1500)),
 "V05 window end 15:00->14:00 (P6)": D(w=(950, 1400)),
 "V06 window end 15:00->13:00 (P6)": D(w=(950, 1300)),
 "V07 refire on, cooldown 6 (P8)": D(refire=True, cd=6),
 "V08 heat <= -25 (P9)": D(heat=-25.0),
 "V09 buyPressure < -0.20 (P10)": D(bp=-0.20),
 "V10 RSI(14) 55-60 (P11 upper)": D(rhi=60.0),
 "V11 RSI(14) 55-62.5 (P11 upper)": D(rhi=62.5),
 "V12 RSI(14) 57-65 (P11 lower)": D(rlo=57.0),
 "V13 + RSI(5) <= 90 (P11 extra)": D(rsi5max=90.0),
 "V14 gap < -0.5% (P12)": D(gap=-0.5),
 "V15 gap < -1.5% (P12)": D(gap=-1.5),
 "V16 lots/symbol 3 -> 1 (P15, tool)": D(symcap=1),
 "V17 latch -2R (P16, tool)": D(latch=-2.0),
 "V18 cost filter 0.15 -> 0.10 (P18)": D(costr=0.10),
 "V19 cost filter off (P18)": D(costr=None),
 "V20 1R 0.25 -> 0.30 ATR (P21)": D(rf=0.30),
 "V21 stop 1.0 -> 1.25R (P24)": D(dn=1.25),
 "V22 target 1.0 -> 0.8R (P25)": D(up=0.8),
 "V23 BE stop after +0.5R (P24 move)": D(be_at=0.5),
 "V24 max hold 120 min (P27)": D(maxhold=120),
 "V25 flat 15:55 -> 15:00 (P27, no live knob)": D(flat=1500),
 "V26 gate: skip SPY > +0.20% since 09:50 (new, sibling RW3/RW5)": D(spy950=0.20),
 "V27 gate: skip SPY above 09:30-09:50 high (new)": D(spyrng=1),
 "V28 skip SMA20 slope > +0.20%/bar (new: stock trending up)": D(slopemax=0.20),
 "V29 skip price > 1.0% below VWAP (new)": D(vwmin=-1.0),
 "V30 skip fromOpen > +1.0% (new: gap filled)": D(fomax=1.0),
 # added after the 5 worst / 5 best review (still before any variant score): best trades sit >= 3% below the open
 "V31 require fromOpen <= 0 (new: still below the open)": D(fomax=0.0),
 "V32 require fromOpen <= -1.0% (new: still >= 1% below the open)": D(fomax=-1.0),
}
# Round 2 (declared after ROUND1, before any combo score). Round-1 passes in both tests: SPY gate 0.20 (V26), SPY range gate
# (V27), end 13:00 (V06) / 14:00 (V05), gap < -0.5% (V14), 1R 0.30 ATR (V20), VWAP floor -1% (V29), RSI(5) <= 90 (V13),
# slope <= 0.20 (V28), fromOpen <= +1% (V30), price >= $10 (V02, ~0). Failed: latch -2R, cost 0.10 / off, stop 1.25R (2y worst
# day), target 0.8R, BE, max hold 120, bp -0.20, RSI band cuts, heat -25, gap -1.5%, refire, start 10:15/11:00 (2y), fromOpen <= 0 / -1.
G = dict(spy950=0.20)
ROUND2 = {
 "PARENT": BASE,
 "S1 skip SPY > +0.30% since 09:50": D(spy950=0.30),
 "S2 skip SPY > +0.10% since 09:50": D(spy950=0.10),
 "C1 SPY gate + end 13:00": D(**G, w=(950, 1300)),
 "C2 C1 + gap < -0.5%": D(**G, w=(950, 1300), gap=-0.5),
 "C3 C1 + 1R 0.30 ATR": D(**G, w=(950, 1300), rf=0.30),
 "C4 C1 + VWAP floor -1%": D(**G, w=(950, 1300), vwmin=-1.0),
 "C5 C1 + RSI(5) <= 90": D(**G, w=(950, 1300), rsi5max=90.0),
 "C6 C2 + 1R 0.30 ATR": D(**G, w=(950, 1300), gap=-0.5, rf=0.30),
 "C7 C2 + VWAP floor -1% + RSI(5) <= 90": D(**G, w=(950, 1300), gap=-0.5, vwmin=-1.0, rsi5max=90.0),
 "C8 SPY gate + gap < -0.5%": D(**G, gap=-0.5),
 "C9 SPY range gate + end 13:00 + gap < -0.5%": D(spyrng=1, w=(950, 1300), gap=-0.5),
 "C10 C2 + start 10:15 (sibling)": D(**G, w=(1015, 1300), gap=-0.5),
 "C11 C2 + slope <= +0.05%/bar (MF2 sibling layer)": D(**G, w=(950, 1300), gap=-0.5, slopemax=0.05),
 "C12 slope <= +0.05%/bar alone (MF2 sibling part)": D(slopemax=0.05),
 "C13 SPY gate + end 14:00 + gap < -0.5%": D(**G, w=(950, 1400), gap=-0.5),
}
# Round 3 (declared after ROUND2): replay gains are large, 2-year stays ~ -0.005 because losses are day-type (2y up days
# -0.19 / -0.49R). Tighter SPY gate (S2 0.10 > S1 0.30 > 0.20) and a NEW after-09:50 market gate: SPY change over the last
# 30 minutes (reference never before the 09:50 close), skip when > +0.10%.
G1 = dict(spy950=0.10)
ROUND3 = {
 "PARENT": BASE,
 "D1 gate 0.10 + end 13:00 + RSI(5) <= 90": D(**G1, w=(950, 1300), rsi5max=90.0),
 "D2 gate 0.10 + gap < -0.5%": D(**G1, gap=-0.5),
 "D3 gate 0.10 + end 13:00 + gap < -0.5%": D(**G1, w=(950, 1300), gap=-0.5),
 "D4 D3 + VWAP floor -1% + RSI(5) <= 90": D(**G1, w=(950, 1300), gap=-0.5, vwmin=-1.0, rsi5max=90.0),
 "D5 gate 0.00 (skip any SPY rise since 09:50)": D(spy950=0.0),
 "D6 gate 0.10 + end 13:00": D(**G1, w=(950, 1300)),
 "D7 D3 + slope <= +0.05%/bar": D(**G1, w=(950, 1300), gap=-0.5, slopemax=0.05),
 "D8 NEW gate: skip SPY up > +0.10% over the last 30 min (after 09:50)": D(spy30=0.10),
 "D9 D8 + SPY gate 0.20 since 09:50": D(spy30=0.10, spy950=0.20),
 "D10 D3 + D8 30-min gate": D(**G1, w=(950, 1300), gap=-0.5, spy30=0.10),
 "D11 D3 + RSI(5) <= 90 + slope <= 0.05": D(**G1, w=(950, 1300), gap=-0.5, rsi5max=90.0, slopemax=0.05),
}
# Round 4 (declared after ROUND3: D10 = gate 0.10 + 30-min gate + end 13:00 + gap < -0.5% is the only stack positive in every
# 2-year split with a better worst day; D11's RSI(5)/slope layers lift the replay). Neighbours and one stack.
G2 = dict(spy950=0.10, spy30=0.10, w=(950, 1300), gap=-0.5)
ROUND4 = {
 "PARENT": BASE,
 "D10 D3 + D8 30-min gate": D(**G2),
 "E1 D10 + RSI(5) <= 90 + slope <= 0.05": D(**G2, rsi5max=90.0, slopemax=0.05),
 "E2 D10 without gap < -0.5% (gates + end 13:00)": D(spy950=0.10, spy30=0.10, w=(950, 1300)),
 "E3 D10 with 30-min gate 0.20": D(**dict(G2, spy30=0.20)),
 "E4 D10 with end 14:00": D(**dict(G2, w=(950, 1400))),
 "E5 D10 with SPY-since-09:50 gate 0.20": D(**dict(G2, spy950=0.20)),
 "E6 D10 + RSI(5) <= 90": D(**G2, rsi5max=90.0),
}
# Round 5 (declared after the live-overlap check: in the 23 live sessions the SPY gates removed net-positive trades
# (since-09:50 part +4.7R, 30-min part +5.5R incl. the 3 best 11-05 trades) while gap and end-13:00 removed -12.7R / -28.4R).
# Ablation of E3: which parts carry each test.
ROUND5 = {
 "PARENT": BASE,
 "E3 D10 with 30-min gate 0.20": D(spy950=0.10, spy30=0.20, w=(950, 1300), gap=-0.5),
 "F1 end 13:00 + gap < -0.5% (no SPY gates)": D(w=(950, 1300), gap=-0.5),
 "F2 F1 + 30-min gate 0.20 only": D(spy30=0.20, w=(950, 1300), gap=-0.5),
 "F3 F1 + since-09:50 gate 0.10 only": D(spy950=0.10, w=(950, 1300), gap=-0.5),
}
