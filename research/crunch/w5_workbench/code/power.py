"""W5 Part B: analytic power table (80% power, one-sided bar t). Educational only - not financial advice."""
import math, numpy as np, pandas as pd
S = "<scratch>"
x = pd.read_pickle(f"{S}/demo_scored.pkl")
def icc(df, col):
    d = df.groupby("date")[col]; k = d.ngroups; n = len(df)
    msb = (d.size() * (d.mean() - df[col].mean()) ** 2).sum() / (k - 1); msw = ((df[col] - d.transform("mean")) ** 2).sum() / (n - k)
    m0 = (n - (d.size() ** 2).sum() / n) / (k - 1); return max(0, (msb - msw) / (msb + (m0 - 1) * msw))
ic_d = np.median([icc(g, "dX1") for _, g in x.groupby("s")] + [icc(g, "dX2") for _, g in x.groupby("s")] + [icc(g, "dX3") for _, g in x.groupby("s")])
sd_d = np.median([x["d" + k].std() for k in ["X1", "X2", "X3"]])
SIG, ICC = 0.836, 0.223
print("paired delta: sd", round(sd_d, 3), "ICC", round(ic_d, 3))
rows = []
for m in [3, 10]:
    for design, sig, ic in [("unpaired copy vs parent", SIG * math.sqrt(2), ICC), ("paired gate, drop 1/3", SIG * math.sqrt(1 / 3), ICC),
                            ("paired exit tune", sd_d, ic_d)]:
        deff = 1 + (m - 1) * ic
        for bar in [1.645, 2.45, 3.34]:
            for d in [0.05, 0.10]:
                n = ((bar + 0.8416) * sig * math.sqrt(deff) / d) ** 2
                rows.append(dict(trades_per_day=m, design=design, bar=bar, delta=d, trades=int(round(n)), sessions=int(math.ceil(n / m))))
T = pd.DataFrame(rows)
pv = T.pivot_table(index=["trades_per_day", "design", "bar"], columns="delta", values=["trades", "sessions"])
pd.set_option("display.width", 200); print(pv.to_string()); T.to_csv(f"{S}/B_power.csv", index=False)
# what U7-sized checks could see: SE of a check-half difference for a typical U7 check (n=30, 6 days)
for n, k in [(15, 4), (30, 6), (60, 9), (430, 13)]:
    m = n / k; se_u = SIG * math.sqrt(2 * (1 + (m - 1) * ICC) / n); se_p = sd_d * math.sqrt((1 + (m - 1) * ic_d) / n)
    print(f"check n={n}, days={k}: SE of avg diff unpaired {se_u:.3f}R, paired exit {se_p:.3f}R, gate-1/3 {SIG*math.sqrt((1+(m-1)*ICC)/(3*n)):.3f}R")
