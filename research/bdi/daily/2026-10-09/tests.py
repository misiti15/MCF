"""10-09 nightly-loop checks on the open 2-year history (diagnosis -> hypothesis; declared before scoring):
T1 heat_fade_short entries barely below the open: fromOpen in (-0.15%, 0) at the signal bar vs <= -0.15%.
T2 heat_fade_short on gap-up names (gap > 0) vs gap <= 0.
Both on the live window (timeofday set 'current') and full day ('full'); 2 splits x 2 sets = 4 configurations for the
'kept' side (the complement is reported, not counted separately). Gates: mcf.research.gates (regime split, walk-forward,
t vs t_required with N = 19,200 heat lineage + 7 timeofday + 4). Locked block not loaded. Educational only - not
financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402

SD = ROOT / "research" / "bdi" / "stack1009" / "data"
z = np.load(SD / "base.npz")
B = {k: z[k] for k in ("fromOpen", "gap", "day", "tod", "sym")}
dates = pd.read_csv(SD / "dates.csv").iloc[:, 0].astype(str).tolist()
syms = pd.read_csv(SD / "symbols.csv").iloc[:, 0].astype(str).tolist()
key = (pd.Series(np.array(syms)[B["sym"]]) + "|" + pd.Series(np.array(dates)[B["day"]]) + "|" + pd.Series(B["tod"]).astype(str))
F = pd.DataFrame({"fo": B["fromOpen"].astype(float), "gap": B["gap"].astype(float)}, index=key.to_numpy())
F = F[~F.index.duplicated()]
T = pd.read_parquet(ROOT / "research" / "bdi" / "timeofday" / "data" / "trades.parquet")
T = T[(T.setup == "heat_fade_short") & T.set.isin(["current", "full"])].copy()
k = T["symbol"].astype(str) + "|" + T["date"].astype(str) + "|" + T["tod"].astype(str)
T["fo"] = F["fo"].reindex(k.to_numpy()).to_numpy()
T["gap"] = F["gap"].reindex(k.to_numpy()).to_numpy()
REG = lib.regimes()
N = 19200 + 7 + 4
rows = []
for st, g in T.groupby("set"):
    g = g[np.isfinite(g.fo)]
    for name, m in (("T1 near-open (-0.15<fo<0)", (g.fo > -0.15) & (g.fo < 0)), ("T1c fo<=-0.15", g.fo <= -0.15),
                    ("T2 gap>0", g.gap > 0), ("T2c gap<=0", g.gap <= 0), ("all", np.ones(len(g), bool))):
        tr = pd.DataFrame({"date": pd.to_datetime(g["date"][m]).dt.date, "r": g["r"][m].to_numpy()})
        sm = gates.summary(tr)
        rg = gates.regime_split(tr, REG)
        wf = gates.walk_forward(tr, exclude_months=lib.LOCKED_MONTHS)
        v, f = gates.verdict(sm, rg, wf, N)
        rows.append({"set": st, "split": name, "n": sm.get("n"), "exp": sm.get("exp_r"), "t": sm.get("t"),
                     "up": rg["up"].get("exp_r"), "flat": rg["flat"].get("exp_r"), "down": rg["down"].get("exp_r"),
                     "wf": wf["share_positive"], "ex_best": sm.get("ex_best_day"), "verdict": v})
R = pd.DataFrame(rows)
R.to_csv(HERE / "tests_heat_split.csv", index=False)
print("matched", int(np.isfinite(T.fo).sum()), "of", len(T), "t_req", gates.t_required(N))
print(R.to_string())
