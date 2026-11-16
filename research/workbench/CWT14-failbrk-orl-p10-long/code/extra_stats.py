from ana import *
s = load(); reg = regime_map()
s["hold"] = (s.base_xt // 100 * 60 + s.base_xt % 100) - (s.base_et // 100 * 60 + s.base_et % 100)
atr20 = lambda d: d.atr_d / d.close >= 0.02
V = {"parent": (dict(), "base"), "WB1": (dict(), "r30"), "WB2": (dict(extra=atr20), "base"),
     "WB3": (dict(window=(1030, 1200)), "base"), "WB4": (dict(extra=atr20), "r30")}
for vn, (kw, c) in V.items():
    t = period(pick(s, **kw), TWO_Y).copy(); t["reg"] = t.date.map(reg.regime)
    g = t.groupby("reg")[c + "_r"].mean().round(3).to_dict()
    hold = t.hold.median() if c == "base" else None
    print(vn, "2y by day type", g, "median hold (min, base exits)", hold, "stop share", round((t[c + "_why"].isin(["stop","gapstop"])).mean(), 3))
