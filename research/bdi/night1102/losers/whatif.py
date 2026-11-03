"""Paired what-if table on ALL live trades and on the loser subset. Usage: python whatif.py <scratch>"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); t = pd.read_parquet(S / "feat.parquet")
V = ["wait0", "wait1", "wait3", "wait5", "lim_vwap", "lim_pb25", "ts30", "ts60", "be03", "scr15", "scr30", "scr60", "part05", "wide15", "opposite"]


def dct(x, col):  # day-clustered t of the paired delta
    g = x.groupby("date")[col].sum() / x.groupby("date").size().mean()
    s = x.groupby("date")[col].sum()
    return s.mean() / (s.std(ddof=1) / np.sqrt(len(s))) if len(s) > 2 and s.std() > 0 else np.nan


out = []
for scope, x in [("all", t)] + [(a, t[t.account == a]) for a in ["primary", "testing1", "testing2", "graveyard", "gen"]] + [("losers_all", t[t.loser]), ("losers_primary", t[t.loser & (t.account == "primary")])]:
    for v in V:
        ref = "R_wait0" if v.startswith(("wait", "lim")) and v != "wait0" else "R_base"  # entry variants vs the same no-slippage open fill
        dlt = x[f"R_{v}"] - x[ref]
        y = x.assign(dl=dlt)
        out.append(dict(scope=scope, variant=v, n=len(x), ref=ref[2:], refR=x[ref].mean(), var=x[f"R_{v}"].mean(), delta=dlt.mean(),
                        day_t=dct(y, "dl"), days_better=(y.groupby("date").dl.sum() > 0).sum(), days=y.date.nunique()))
o = pd.DataFrame(out)
o.to_csv(Path(__file__).parent / "whatif_live.csv", index=False, float_format="%.4f")
pd.set_option("display.width", 200)
print(o.round(3).to_string())
