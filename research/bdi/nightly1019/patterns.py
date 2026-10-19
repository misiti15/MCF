"""Classify 2026-10-19 losers (journal pnl < 0, real trades run 1) with the nightly1012/bdi1016 loss-type classifier
on SIP 1-min bars, and compare the mix with the earlier days in research/bdi/patterns.csv. Writes patterns_1019.csv in the
patterns.csv format (NOT merged into research/bdi/patterns.csv; the lead merges) and patterns_out.txt.
Order: stopped_then_reversed (stop, then the target traded later in the session) > wrong_side_after_big_swing (|stock
from-open| >= 3% at entry and the opposite 1R/1R trade from the entry wins) > gave_back_gains (MFE >= 0.5R) > late_hold
(flatten exit) > never_worked (MFE < 0.15R) > small MFE then failed (0.15-0.5R).
Usage: python patterns.py <scratch>   Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; D = "2026-10-19"; TZ = "America/New_York"
ROOT = Path("/home/user/MCF")
T = pd.read_csv(OUT / "trades.csv")
for c in ("nt", "et"): T[c] = pd.to_datetime(T[c], utc=True).dt.tz_convert(TZ)
bars = {}
def bar(s):
    if s not in bars:
        b = pd.read_parquet(S / "bars" / f"{s}.parquet"); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ)
        bars[s] = b.between_time("09:30", "15:59")
    return bars[s]
def opp_wins(path, side, px, R):
    s = -side; stop, tgt = px - s * R, px + s * R
    for h, l in zip(path.high.values, path.low.values):
        if (l <= stop) if s == 1 else (h >= stop): return False
        if (h >= tgt) if s == 1 else (l <= tgt): return True
    return False
NM = {"p": "primary", "t1": "testing", "t2": "testing2", "gen": "generator"}
rows = []
for r in T[T.pnl < 0].itertuples():
    b = bar(r.symbol); side = int(r.side)
    path = b[b.index >= r.nt.floor("min")]
    fo = (b.close.asof(r.nt) / b.open.iloc[0] - 1) * 100
    post = b[b.index > r.et.floor("min")]
    tgt = None if pd.isna(r.target) else float(r.target)
    mfe = r.mfe if r.mfe == r.mfe else 0.0
    if r.exit_reason == "stop" and tgt is not None and len(post) and ((post.high.max() >= tgt) if side == 1 else (post.low.min() <= tgt)):
        lt = "stopped_then_reversed"
    elif abs(fo) >= 3 and opp_wins(path, side, r.entry, r.R):
        lt = "wrong_side_after_big_swing"
    elif mfe >= 0.5: lt = "gave_back_gains"
    elif r.exit_reason == "flatten": lt = "late_hold"
    elif mfe < 0.15: lt = "never_worked"
    else: lt = "small MFE then failed (0.15-0.5R)"
    rows.append(dict(date=D, account=NM[r.acct], symbol=r.symbol, setup=r.strategy, side="long" if side == 1 else "short", loss_type=lt,
                     notes=f"nightly1019; r {r.r_multiple:.2f}; mfe {mfe:.2f}; lot {r.lot_no}; twin {bool(r.twin)}; entry {r.nt:%H:%M}", pnl_adj=r.pnl_adj))
X = pd.DataFrame(rows)
X.drop(columns="pnl_adj").to_csv(OUT / "patterns_1019.csv", index=False)
out = []
P = lambda *x: out.append(" ".join(str(y) for y in x))
P("== 2026-10-19 losers by account x loss type (count / $ after costs)")
P(X.pivot_table(index="loss_type", columns="account", values="pnl_adj", aggfunc=["size", "sum"], fill_value=0).round(1).to_string())
H = pd.read_csv(ROOT / "research" / "bdi" / "patterns.csv")
H = H[(H.loss_type != "win") & (H.loss_type != "artifact_excluded")]
P("\n== loss-type share: earlier days (patterns.csv, 10-06..10-16) vs today")
a = H.loss_type.value_counts(normalize=True).round(3); b = X.loss_type.value_counts(normalize=True).round(3)
P(pd.DataFrame({"earlier": a, "2026-10-19": b}).fillna(0).to_string())
P("\n== today, top setups by loss type (count)")
P(X.groupby(["loss_type", "setup"]).size().sort_values(ascending=False).groupby(level=0).head(3).to_string())
open(OUT / "patterns_out.txt", "w").write("\n".join(out) + "\n\nEducational only - not financial advice.\n")
print("\n".join(out))
