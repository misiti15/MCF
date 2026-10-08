"""Task 2(c) - volume ceiling of the live setups: treat EVERY qualifying 5-minute bar as its own trade (ignoring the
one-signal-per-day rule AND the one-open-position-per-symbol rule), simulated with the production engine + costs.
Splits first-bar trades from later bars, so the expectancy of the extra volume is visible. 3 configurations
(one per setup). Educational only - not financial advice."""
import sys

import pandas as pd

sys.path.insert(0, ".")
sys.path.insert(0, "research/oct7/bdi")
from lib import load, run, stats  # noqa: E402
from task2_freq import REENTRY, make_sig  # noqa: E402

H, bars, F = load()
ndays = {"train": int((F.date <= "2026-08-25").sum()), "valid": int((F.date > "2026-08-25").sum())}
rows = []
for setup in REENTRY:
    Q = H[(H.setup == setup) & (H.kind == "all")].sort_values("end").copy()
    Q["nth"] = Q.groupby(["symbol", "date"]).cumcount() + 1
    L = []
    for r in Q.itertuples():
        sig, R = make_sig(setup, r.symbol, r.end, r.side, r.px, r.atr)
        tr, _ = run(sig, bars[(r.symbol, r.date)], r.ext)
        if tr:
            L.append(dict(date=r.date, split=r.split, nth=r.nth, r=tr.r_multiple))
    L = pd.DataFrame(L)
    for sp in ("train", "valid"):
        for lab, sub in (("all bars", L[L.split == sp]), ("first bar", L[(L.split == sp) & (L.nth == 1)]),
                         ("bars 2+", L[(L.split == sp) & (L.nth > 1)])):
            st = stats(sub)
            rows.append(dict(setup=setup, split=sp, subset=lab, per_day=round(st["n"] / ndays[sp], 1),
                             **{k: st.get(k) for k in ("n", "win", "exp", "tot", "t_day", "ex_best")}))
R = pd.DataFrame(rows)
pd.set_option("display.width", 200)
print(R.to_string())
R.to_csv("research/oct7/bdi/task2c_volume.csv", index=False)
