"""RE-BREAK reporting (Skeptic skeptic-20261111-0901-2 (c)): SPY open->close on gap-up / gap-down / flat days (gap = SPY open
vs prior close, +-0.25%; the first session after the locked block NaN). Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF/research/history2y"); import lib
d = lib.daily(); s = d[d.symbol == "SPY"].sort_values("date").copy()
s["pc"] = s.close.shift(1); s.loc[pd.to_datetime(s.date).diff().dt.days > 5, "pc"] = np.nan
s["gap"] = s.open / s.pc - 1; s["oc"] = (s.close / s.open - 1) * 100
s["cls"] = np.where(s.gap > .0025, "gap up", np.where(s.gap < -.0025, "gap down", np.where(s.gap.notna(), "flat", "n/a")))
s["split"] = np.where(pd.to_datetime(s.date) <= "2025-12-31", "TRAIN", np.where(pd.to_datetime(s.date) <= "2026-10-05", "VALID", "FWD"))
t = s[s.cls != "n/a"].groupby(["split", "cls"]).oc.agg(["size", "mean", "median", lambda x: (x > 0).mean()])
t.columns = ["days", "mean o->c %", "median o->c %", "share up"]; print(t.round(3).to_string())
print("Educational only - not financial advice.")
