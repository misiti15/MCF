"""ex30/time live-shape check: module masks on live-shaped single-symbol frames == history frames. Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
sys.argv = ["x", "."]
sys.path.insert(0, "/home/user/MCF/research/bdi/ex30/time")
import score as S
df = S.add_prng(S.lib.load_month("2026-09", columns=S.COLS + ["ts"], context=True))
keys = df[["symbol", "date"]].drop_duplicates().sample(400, random_state=1)
mods = {n: S.load_mod(n) for n in S.SETUPS}
bad = tot = fired = 0
for _, k in keys.iterrows():
    g = df[(df.symbol == k.symbol) & (df.date == k.date)].reset_index(drop=True)
    ref = {n: np.asarray(m.mask(g), bool) for n, m in mods.items()}
    pre = pd.concat([g.iloc[[0]]] * 3, ignore_index=True)
    pre["tod"] = [935, 940, 945]; pre["close"] = pre["close"] * [0.9, 1.1, 0.95]; pre["high"] = pre["close"] * 1.2
    pre["ts"] = g.ts.iloc[0] - pd.to_timedelta([15, 10, 5], unit="min")
    L = pd.concat([pre, g], ignore_index=True).set_index("ts").drop(columns=["symbol", "date"])
    for n, m in mods.items():
        got = np.asarray(m.mask(L), bool)[3:]
        tot += 1; fired += ref[n].any(); bad += not np.array_equal(got, ref[n])
print("checks", tot, "mismatches", bad, "symbol-days with a signal", fired)
