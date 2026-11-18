"""W5 Part B/D: Monte Carlo power of the old protocol vs WB2 on the demo's real paired noise.
Null deltas = the demo's X1/X2/X3 per-trade deltas demeaned within setup (true effect 0); one class gets a planted
effect delta per parent trade (added to the trades the class changes). Sessions are resampled with replacement.
Educational only - not financial advice."""
import math, numpy as np, pandas as pd
S = "<scratch>"
x = pd.read_pickle(f"{S}/demo_scored.pkl"); rng = np.random.default_rng(20261118)
BAR = max(1.5, math.sqrt(2 * math.log(15)))
K = ["X1", "X2", "X3"]; setups = sorted(x.s.unique()); dates = sorted(x.date.unique())
for k in K:
    ch = (x["d" + k].abs() > 1e-9)
    x["n" + k] = x["d" + k] - x.groupby("s")["d" + k].transform("mean")
    x["c" + k] = ch / ch.groupby(x.s).transform("mean")         # planted effect lands on changed trades, avg delta per trade
# daily arrays per setup: sum of null delta, sum of plant weights, count
A = {}
for (s, d), g in x.groupby(["s", "date"]):
    A[(s, d)] = (np.array([g["n" + k].sum() for k in K]), np.array([g["c" + k].sum() for k in K]), len(g))
def tstat(sums, cnts):
    n = cnts.sum(); k = (cnts > 0).sum()
    if n == 0 or k < 2: return 0.0, np.nan
    th = sums.sum() / n; se = math.sqrt(k / (k - 1) * ((sums - cnts * th) ** 2).sum()) / n
    return th, th / se if se > 0 else 0.0
def rep(delta, nsess):
    ds = rng.choice(dates, size=nsess, replace=True)
    order = np.arange(nsess); half = nsess // 2
    # per setup x class daily sums
    sums = np.zeros((len(setups), 3, nsess)); cnts = np.zeros((len(setups), nsess))
    for j, d in enumerate(ds):
        for i, s in enumerate(setups):
            a = A.get((s, d))
            if a is None: continue
            sums[i, :, j] = a[0] + np.array([delta, 0, 0]) * a[1]; cnts[i, j] = a[2]
    # old protocol: per setup choose best class on fit half, pass if check t>=BAR and >0
    old_true = old_false = 0
    for i in range(len(setups)):
        fit = sums[i, :, :half].sum(1); kb = int(np.argmax(fit))
        if fit[kb] <= 0: continue
        th, t = tstat(sums[i, kb, half:], cnts[i, half:])
        if t >= BAR and th > 0:
            if kb == 0: old_true += 1
            else: old_false += 1
    # WB2: per class pooled day-clustered t over all sessions + shrinkage (>=4/5 setups' shrunk > 0)
    wb_true = wb_false = 0
    for c in range(3):
        th, t = tstat(sums[:, c, :].sum(0), cnts.sum(0))
        thi = []; sei = []
        for i in range(len(setups)):
            a, ti = tstat(sums[i, c], cnts[i]); thi.append(a); sei.append(abs(a / ti) if ti else 1e9)
        thi, sei = np.array(thi), np.array(sei); w = 1 / sei ** 2
        mu = (w * thi).sum() / w.sum(); Q = (w * (thi - mu) ** 2).sum()
        tau2 = max(0, (Q - 4) / (w.sum() - (w ** 2).sum() / w.sum())); B = tau2 / (tau2 + sei ** 2)
        shr = th + B * (thi - th)
        if t >= BAR and (shr > 0).sum() >= 4:
            if c == 0: wb_true += 1
            else: wb_false += 1
    return old_true, old_false, wb_true, wb_false
rows = []
for nsess in [28, 56, 112]:
    for delta in [0.0, 0.03, 0.05, 0.10]:
        R = np.array([rep(delta, nsess) for _ in range(300)])
        rows.append(dict(sessions=nsess, delta=delta,
                         old_setups_passing_true=R[:, 0].mean(), old_any_true=(R[:, 0] > 0).mean(), old_false_pass_rate=(R[:, 1] > 0).mean(),
                         wb2_detect=(R[:, 2] > 0).mean(), wb2_false_pass_rate=(R[:, 3] > 0).mean()))
        print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv(f"{S}/B_powersim.csv", index=False)
