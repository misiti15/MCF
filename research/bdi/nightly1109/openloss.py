"""burst1-openloss-latch3 forward tally 2026-11-09 (Primary + Graveyard): a setup is shadow-latched at its first new entry
when its realised + 5-min marked open R <= -3; later taken entries are 'blocked' (taken-entry R only). Rule as
research/bdi/1106/forward_1106.py. Usage: python openloss.py <scratch>   Educational only - not financial advice."""
import sys
from pathlib import Path
import pandas as pd
S = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent; TZ = "America/New_York"
T = pd.read_csv(HERE / "trades.csv"); T = T[T.run_id == 1].copy()
for c in ("nt", "et"): T[c] = pd.to_datetime(T[c], utc=True, format="mixed").dt.tz_convert(TZ)
T["risk_d"] = (T.entry - T.stop).abs() * T.shares
PX = {}
def px(s):
    if s not in PX:
        b = pd.read_parquet(S / "bars" / f"{s}.parquet"); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ); PX[s] = b.close
    return PX[s]
def mtm(r, t):
    p = px(r.symbol); x = p[p.index < t.floor("5min")]
    return 0.0 if x.empty else float((x.iloc[-1] - r.entry) * r.side * r.shares / r.risk_d)
res = []
for a in ("p", "gy"):
    for s, g in T[T.acct == a].sort_values("nt").groupby("strategy"):
        lat = None
        for _, r in g.iterrows():
            prior = g[g.nt < r.nt]
            if lat is None and len(prior):
                v = prior[prior.et <= r.nt].radj.sum() + sum(mtm(x, r.nt) for _, x in prior[prior.et > r.nt].iterrows())
                if v <= -3: lat = (r.nt, v)
            if lat is not None: res.append(dict(acct=a, setup=s, latch=lat[0], at=round(lat[1], 2), R=r.radj))
X = pd.DataFrame(res)
out = []
if len(X):
    by = X.groupby(["acct", "setup"]).agg(t=("latch", "first"), at=("at", "first"), n=("R", "size"), R=("R", "sum"))
    for a, g in by.groupby(level=0): out.append(f"{a}: shadow - live {-g.R.sum():+.2f}R over {int(g.n.sum())} blocked taken entries; setups {len(g)} "
                                                  f"(better {(g.R < 0).sum()}, worse {(g.R > 0).sum()})")
    out.append(by.round(2).to_string())
else:
    out.append("no setup reached -3R")
txt = "\n".join(out); (HERE / "openloss_out.txt").write_text(txt + "\n\nEducational only - not financial advice.\n"); print(txt)
