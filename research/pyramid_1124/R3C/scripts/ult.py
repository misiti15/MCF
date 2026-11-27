"""R3C: approximate re-cost of ultimate_1119 check trade files that carry price and ATR/risk (delta method:
r_cal = r + (research cost - calibrated cost)/risk, risk = 0.25 x daily ATR unless the file has it). Educational only."""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/R3C")
import rescore as RS, calib as CB
from mcf.research.gates import tod_cost_mult
U = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox/research/ultimate_1119/"
F = {"ULT-02": ("ULT-02-tapeflush-washout-long/check_trades.csv", "R"), "ULT-06": ("ULT-06-late-morning-turn-long/check_trades.csv", "R"),
     "ULT-10": ("ULT-10-regime-switch-book/check_trades.csv", "r"), "ULT-22": ("round3/ULT-22/check_trades.csv.gz", "r"),
     "ULT-23 check": ("round3/ULT-23/check_trades.csv.gz", "r"), "ULT-23 fit": ("round3/ULT-23/fit_trades.csv.gz", "r")}
out = {}
for nm, (f, rc) in F.items():
    t = pd.read_csv(U + f)
    r = t[rc].astype(float)
    side = t.side.to_numpy() if "side" in t else np.ones(len(t))
    price = (t.entry if "entry" in t else t.e if "e" in t else t.close).to_numpy(float)
    risk = (t.R.to_numpy(float) if nm == "ULT-10" else 0.25 * t.atr_d.to_numpy(float))
    if "kind" in t: kd = t.kind.to_numpy()
    elif "kd" in t: kd = t.kd.to_numpy()
    else: kd = np.where(r <= -0.95, 1, 0)
    px = t.px.to_numpy(float) if "px" in t else price
    ec = (0.01 + price * 1e-4) * tod_cost_mult(t.tod.to_numpy())
    xc = np.where(kd == 2, 0.0, 0.01 + px * 1e-4) + np.where(kd == 1, 0.02, 0.0)
    res = ec + xc + np.where(side < 0, 1.2e-4 * price, 0.0)
    kds = np.where(kd == 2, "target", np.where(kd == 1, "stop", "market"))
    c1 = RS.cal_ps(price, t.tod.to_numpy(), kd, side); c2 = CB.predict2_ps(RS.CELLS, RS.CELLS2, price, t.tod.to_numpy(), kds, side, risk)
    ok = np.isfinite(risk) & (risk > 0)
    r1 = r + (res - c1) / risk; r2 = r + (res - c2) / risk
    d = pd.DataFrame({"date": t.date.astype(str), "r": r, "r1": r1, "r2": r2})[ok]
    def wo(s):
        day = d.groupby("date")[s].sum(); b = day.idxmax(); return round(float(d.loc[d.date != b, s].mean()), 4)
    out[nm] = {"n": int(ok.sum()), "med_price": round(float(np.median(price)), 1), "res": round(d.r.mean(), 4), "cal": round(d.r1.mean(), 4),
               "cal2": round(d.r2.mean(), 4), "res_wo": wo("r"), "cal_wo": wo("r1"), "cal2_wo": wo("r2"),
               "delta_cal": round(float(((res - c1) / risk)[ok].mean()), 4)}
    print(nm, out[nm])
json.dump(out, open("ult_recost.json", "w"), indent=1)
