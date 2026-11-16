from ana import *
import json
s = load()
atr20 = lambda d: d.atr_d / d.close >= 0.02
V = {"parent": (dict(), "base_r"), "WB1 r_atr_frac 0.30": (dict(), "r30_r"), "WB3 ATR%>=2.0": (dict(extra=atr20), "base_r"),
     "WB2 window 1030-1200": (dict(window=(1030, 1200)), "base_r"), "WB4 r30 + ATR%>=2.0": (dict(extra=atr20), "r30_r")}
tests = {"replay 2026-10-12..11-10": REPLAY, "2y 2024-10..2026-10-09": TWO_Y, "  train ..2025-12": (TWO_Y[0], TRAIN_END), "  valid 2026-01..10-09": ("2026-01-01", TWO_Y[1])}
rows = []
P0 = pick(s)
for tn, rng in tests.items():
    P = period(P0, rng)
    for vn, (kw, col) in V.items():
        t = period(pick(s, **kw), rng)
        st = stats(t, col); pr = paired(t, P, col, "base_r")
        avgw = t.loc[t[col] > 0, col].mean(); avgl = t.loc[t[col] <= 0, col].mean()
        rows.append(dict(test=tn, copy=vn, **st, avg_win=avgw, avg_loss=avgl, pdiff=pr["diff"], pt=pr["t"]))
D = pd.DataFrame(rows); D.to_csv(OUT + "results.csv", index=False)
pd.set_option("display.width", 250)
print(D[["test","copy","n","win","avg","wo_best","wo_worst","total","worst_day","avg_win","avg_loss","pdiff","pt"]].round(3).to_string())
