"""Declared copies (each one part unless marked combo). Educational only - not financial advice."""
V = {
    # P1/P2 intake
    "I1 gap>=8%": (dict(gap=8.0), "intake"), "I2 gap>=12%": (dict(gap=12.0), "intake"), "I3 gap>=15%": (dict(gap=15.0), "intake"),
    "I4 no ETFs": (dict(extra=lambda s: ~s.etf), "intake"),
    "I5 ADV>=$20M": (dict(min_adv=20e6), "intake"), "I6 ADV>=$50M": (dict(min_adv=50e6), "intake"),
    # P6 timer
    "T1 end 12:00": (dict(window=(1030, 1200)), "timer"), "T2 end 13:00": (dict(window=(1030, 1300)), "timer"),
    "T3 end 11:00": (dict(window=(1030, 1100)), "timer"),
    # P9 sensors
    "S1 VWAP loss >=0.5%": (dict(extra=lambda s: s.vwapDistPct <= -0.5), "sensor"),
    "S2 VWAP loss >=1.0%": (dict(extra=lambda s: s.vwapDistPct <= -1.0), "sensor"),
    "S3 first-hour CLOSE above VWAP": (dict(extra=lambda s: s.cab >= 1), "sensor"),
    "S4 below day open": (dict(extra=lambda s: s.fromOpen < 0), "sensor"),
    "S5 bounce >=0.15 ATR over VWAP": (dict(extra=lambda s: s.exc >= 0.15), "sensor"),
    "S6 stop dist <=1.0 ATR": (dict(extra=lambda s: (s.fh - s.close) / s.atr_d <= 1.0), "sensor/entry"),
    "S7 stop dist >=0.3 ATR": (dict(extra=lambda s: (s.fh - s.close) / s.atr_d >= 0.3), "sensor/entry"),
    # gates (after 09:50)
    "G1 SPY since 09:50 <=0": (dict(extra=lambda s: s.spy50 <= 0), "gate"),
    "G2 SPY since 09:50 <=+0.25%": (dict(extra=lambda s: s.spy50 <= 0.25), "gate"),
    "G3 SPY since 09:50 >=-0.25%": (dict(extra=lambda s: s.spy50 >= -0.25), "gate"),
    # P16/P17 stop
    "X1 stop cap 0.5 ATR": (dict(cap=0.5), "stop"), "X2 stop cap 0.75 ATR": (dict(cap=0.75), "stop"),
    "X3 stop cap 1.0 ATR": (dict(cap=1.0), "stop"), "X4 stop sig-bar/VWAP +0.05 ATR": (dict(stop="sig"), "stop"),
    # P20 target
    "Y1 target 1R": (dict(tgt=1.0), "target"), "Y2 target 2R": (dict(tgt=2.0), "target"), "Y3 target 3R": (dict(tgt=3.0), "target"),
    # stop management
    "Z1 BE after +1R": (dict(be=1.0), "stop mgmt"), "Z2 trail 1R after +1R": (dict(trail=(1.0, 1.0)), "stop mgmt"),
    "Z3 lock +0.5R after +1.5R": (dict(lock=(1.5, 0.5)), "stop mgmt"),
    # P22 time exit
    "E1 flat 13:00": (dict(tx=1300), "time exit"), "E2 flat 14:00": (dict(tx=1400), "time exit"), "E3 flat 15:00": (dict(tx=1500), "time exit"),
}
# ---- round 2: neighbours of the passes + combos (each counted)
_s4 = lambda s: s.fromOpen < 0
_s7 = lambda s: (s.fh - s.close) / s.atr_d >= 0.3
_s1 = lambda s: s.vwapDistPct <= -0.5
_s3 = lambda s: s.cab >= 1
V.update({
    "S4a below open by >=1%": (dict(extra=lambda s: s.fromOpen <= -1.0), "sensor"),
    "S4b below open by >=2%": (dict(extra=lambda s: s.fromOpen <= -2.0), "sensor"),
    "S4c within +1% of open or below": (dict(extra=lambda s: s.fromOpen < 1.0), "sensor"),
    "S7a stop dist >=0.2 ATR": (dict(extra=lambda s: (s.fh - s.close) / s.atr_d >= 0.2), "sensor/entry"),
    "S7b stop dist >=0.4 ATR": (dict(extra=lambda s: (s.fh - s.close) / s.atr_d >= 0.4), "sensor/entry"),
    "S1a VWAP loss >=0.3%": (dict(extra=lambda s: s.vwapDistPct <= -0.3), "sensor"),
    "S1b VWAP loss >=0.75%": (dict(extra=lambda s: s.vwapDistPct <= -0.75), "sensor"),
    "C1 S4+S7": (dict(extra=lambda s: _s4(s) & _s7(s)), "combo"),
    "C2 S4+S1": (dict(extra=lambda s: _s4(s) & _s1(s)), "combo"),
    "C3 S4+S7+S1": (dict(extra=lambda s: _s4(s) & _s7(s) & _s1(s)), "combo"),
    "C4 S4+S3": (dict(extra=lambda s: _s4(s) & _s3(s)), "combo"),
    "C5 S4+S7+S3": (dict(extra=lambda s: _s4(s) & _s7(s) & _s3(s)), "combo"),
    "C6 S4+S7+ADV50M": (dict(extra=lambda s: _s4(s) & _s7(s), min_adv=50e6), "combo"),
    "C7 S4+S7+S1+S3": (dict(extra=lambda s: _s4(s) & _s7(s) & _s1(s) & _s3(s)), "combo"),
    "C8 S4+BE1R": (dict(extra=_s4, be=1.0), "combo"),
    "C9 S4+S7+BE1R": (dict(extra=lambda s: _s4(s) & _s7(s), be=1.0), "combo"),
})
# ---- round 3: around C4 (each counted)
_s7a = lambda s: (s.fh - s.close) / s.atr_d >= 0.2
V.update({
    "C10 S4+S3+ADV50M": (dict(extra=lambda s: _s4(s) & _s3(s), min_adv=50e6), "combo"),
    "C11 S4+S3+ADV20M": (dict(extra=lambda s: _s4(s) & _s3(s), min_adv=20e6), "combo"),
    "C12 S4c+S3": (dict(extra=lambda s: (s.fromOpen < 1.0) & _s3(s)), "combo"),
    "C13 S4+S3+BE1R": (dict(extra=lambda s: _s4(s) & _s3(s), be=1.0), "combo"),
    "C14 S4+S3+S7a": (dict(extra=lambda s: _s4(s) & _s3(s) & _s7a(s)), "combo"),
    "C15 S4+S3+S1a": (dict(extra=lambda s: _s4(s) & _s3(s) & (s.vwapDistPct <= -0.3)), "combo"),
})
