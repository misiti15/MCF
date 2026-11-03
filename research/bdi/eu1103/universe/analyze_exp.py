"""eu1103/universe step 3b: the LIVE-period (10-06..11-02) re-score on the larger universe (expand_live.py output).
Base = names at each setup's live ADV floor (adv20 from the bars); L2 = names ADDED by a $20M floor (20M..floor);
also S1 top-500 dollar-ATR (adv20 x ATR%, ranked per date among adv20 >= $95M names in this set), S5 ADV >= 300M and C1
R >= $0.25/share on the same frames. Costs in (production). Usage: python analyze_exp.py <scratch> -> analyze_exp_out.txt.
Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

S = Path(sys.argv[1])
HERE = Path(__file__).resolve().parent
FLOOR = {"heat_fade_short-FD": 125e6, "RW2-exhaustion-noon-adv150-short-FD": 150e6, "L3-gap-slope-fromopen-FD": 0.0}
T = pd.concat([pd.read_parquet(p) for p in sorted((S / "exp").glob("b*.parquet"))], ignore_index=True)
C = pd.concat([pd.read_parquet(p) for p in sorted((S / "exp").glob("c*.parquet"))], ignore_index=True)
T = T.merge(C, on=["date", "symbol", "side", "geom"], how="left")
T["exc"] = T.r - T.rc
T["floor"] = T.setup.map(FLOOR).fillna(95e6)
T = T[T.adv20 >= 20e6]


def st(x, col="r"):
    if not len(x):
        return dict(n=0)
    ds = x.groupby("date")[col].agg(["sum", "size"]); mu = x[col].mean()
    se = np.sqrt(((ds["sum"] - ds["size"] * mu) ** 2).sum()) / len(x)
    bd = ds["sum"].idxmax()
    return dict(n=len(x), per_day=round(len(x) / len(ds), 1), avgR=round(mu, 4), t=round(mu / se, 2),
                wo_best=round((ds["sum"].sum() - ds.loc[bd, "sum"]) / max(1, len(x) - ds.loc[bd, "size"]), 4),
                vs_rand=round(x.exc.mean(), 4), green=f"{int((ds['sum'] > 0).sum())}/{len(ds)}")


lines = [f"Educational only - not financial advice. LIVE-period re-score (lab frames from SIP 5-min bars, 10-06..11-02, "
         f"{T.symbol.nunique()} symbols with 10-05 ADV >= $20M, earnings blackout applied, production costs). Not live fills."]
T["adv_b"] = pd.cut(T.adv20, [20e6, 50e6, 95e6, 150e6, 300e6, 1e9, 1e14], labels=["20-50M", "50-95M", "95-150M", "150-300M", "300M-1B", ">1B"])
rows = [dict(bucket=str(b), **st(x)) for b, x in T.groupby("adv_b", observed=True)]
lines.append("\n== pooled 8 setups by ADV bucket (no floor)\n" + pd.DataFrame(rows).to_string(index=False))
base = T[T.adv20 >= T.floor].copy()
add = T[T.adv20 < T.floor]
rows = []
for s in ["ALL"] + sorted(T.setup.unique()):
    b = base if s == "ALL" else base[base.setup == s]
    a = add if s == "ALL" else add[add.setup == s]
    rows.append(dict(setup=s, **{f"base_{k}": v for k, v in st(b).items() if k in ("n", "avgR", "t", "vs_rand")},
                     **{f"added_{k}": v for k, v in st(a).items() if k in ("n", "avgR", "t", "vs_rand")},
                     both_avgR=round(pd.concat([a, b]).r.mean(), 4)))
lines.append("\n== L2: names added by a $20M floor vs the live-floor base\n" + pd.DataFrame(rows).to_string(index=False))
base["atrp"] = base.atr_d / base.px * 100
base["datr"] = base.adv20 * base.atrp
# S1 rank = that morning's live universe snapshot (adv x atr_pct among adv >= $95M), as live_rules.py
import glob
snaps = {"2026-10-05": pd.read_csv("/home/user/MCF/data/universe.csv")}
for p in sorted(glob.glob(str(S / "uni" / "*.csv"))):
    snaps[Path(p).stem] = pd.read_csv(p)
rk = {}
for k, u in snaps.items():
    u = u[u.adv >= 95e6]
    rk[k] = pd.Series((u.adv * u.atr_pct).rank(ascending=False).to_numpy(), index=u.symbol)
keys = sorted(rk)
base["rk"] = [rk[max(k for k in keys if k <= str(d))].get(s, np.nan) for s, d in zip(base.symbol, base.date)]
rows = []
for name, keep in (("S1 top-500 dollar-ATR", base.rk <= 500), ("S5 ADV >= 300M", base.adv20 >= 300e6),
                   ("C1 R >= $0.25/share", 0.25 * base.atr_d >= 0.25)):
    k, d = base[keep.fillna(False)], base[~keep.fillna(False)]
    dd = pd.concat([k.groupby("date").r.mean().rename("k"), d.groupby("date").r.mean().rename("d")], axis=1).dropna()
    diff = dd.k - dd.d
    rows.append(dict(rule=name, kept_share=round(len(k) / len(base), 3), **{f"kept_{a}": v for a, v in st(k).items() if a in ("avgR", "t", "wo_best", "green", "vs_rand")},
                     dropped_R=round(d.r.mean(), 4), kd=round(diff.mean(), 4), kd_t=round(diff.mean() / (diff.std() / np.sqrt(len(diff))), 2)))
lines.append(f"\n== smaller-universe rules on the live period (base n {len(base)}, avg R {base.r.mean():.4f}, green "
             f"{st(base)['green']})\n" + pd.DataFrame(rows).to_string(index=False))
(HERE / "analyze_exp_out.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
