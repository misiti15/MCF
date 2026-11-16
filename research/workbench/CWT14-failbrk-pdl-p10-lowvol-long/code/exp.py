"""Every one-part config vs the parent, base exits (A) unless an exit config; train / valid / 2y / replay.
Educational only - not financial advice."""
import sys; sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-cwt14pdl/code")
from ana import *
s = load()
P = pick(s)
E = {  # name: (pick kwargs, exit cfg)
 "parent": ({}, "A"),
 # P2 / P1 / P3 intake
 "P2 ADV>=150M": (dict(min_adv=150e6), "A"), "P1 ATR%>=1.5": (dict(extra=lambda s: s.atrp >= .015), "A"),
 "P1 ATR%>=2.0": (dict(extra=lambda s: s.atrp >= .02), "A"), "P1 ATR%<=4.0": (dict(extra=lambda s: s.atrp <= .04), "A"),
 "P3 price>=10": (dict(extra=lambda s: s.close >= 10), "A"),
 "P13 cost/R<=0.10": (dict(extra=lambda s: cost_ps(s.close) / (0.25 * s.atr_d) <= .10), "A"),
 # P5 timer
 "P5 end 12:00": (dict(window=(950, 1200)), "A"), "P5 end 13:00": (dict(window=(950, 1300)), "A"),
 "P5 start 10:00": (dict(window=(1000, 1500)), "A"), "P5 end 11:00": (dict(window=(950, 1100)), "A"),
 # P8 sensors
 "P8 poke 0.15": (dict(mask="m15v"), "A"), "P8 poke 0.08": (dict(mask="m08v"), "A"), "P8 lowvol off": (dict(mask="m10a"), "A"),
 "P8 reclaim<=0.10": (dict(extra=lambda s: s.reclaim <= .10), "A"), "P8 reclaim>=0.05": (dict(extra=lambda s: s.reclaim >= .05), "A"),
 "P8 gap<0": (dict(extra=lambda s: s.gap < 0), "A"), "P8 gap>=0": (dict(extra=lambda s: s.gap >= 0), "A"),
 "P8 below VWAP": (dict(extra=lambda s: s.vwapDistPct < 0), "A"), "P8 rsi5<=30": (dict(extra=lambda s: s.rsi5 <= 30), "A"),
 "P8 range<=1.2ATR": (dict(extra=lambda s: s.rng_atr <= 1.2), "A"),
 # gates (after 09:50)
 "G SPY since0950>=-0.20": (dict(extra=lambda s: s.spy_d950 >= -0.20), "A"), "G SPY since0950>=0": (dict(extra=lambda s: s.spy_d950 >= 0), "A"),
 "G SPY>=VWAP": (dict(extra=lambda s: s.spy_vw >= 0), "A"), "G SPY rpos>=0.3": (dict(extra=lambda s: s.spy_rpos >= .3), "A"),
}
for k in ["T10", "T175", "T25", "S20", "S30T15", "S375", "S45", "S45T15", "S60", "S60T15", "S45T10", "MH60", "MH120", "S45MH120", "F1330", "S45F1330", "FA", "L4", "S45BE"]:
    E["EX " + k] = ({}, k)
rows = []
for nm, (kw, ex) in E.items():
    t = pick(s, **kw)
    for tn, rng in TESTS.items():
        a = period(t, rng); p = period(P, rng)
        st = stats(a, f"{ex}_r"); pp = paired(a, p, f"{ex}_r", "A_r")
        rows.append(dict(cfg=nm, test=tn, **st, bps=bps(a, ex).mean(), d=pp["diff"], t=pp["t"]))
D = pd.DataFrame(rows); D.to_csv(OUT + "exp1.csv", index=False)
pd.set_option("display.width", 250)
print("configs:", len(E))
print(D.pivot(index="cfg", columns="test", values="avg").round(3).join(D[D.test == "2y"].set_index("cfg")[["n", "wo_best", "worst_day", "bps", "t"]].round(3)).sort_values("train").to_string())
print(D[D.test == "replay"].set_index("cfg")[["n", "wo_best", "worst_day", "bps", "t"]].round(3).to_string())
