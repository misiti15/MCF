"""reddit_1103 B step 1: pre-open "range regime" predictors (r/Trading 1xme54j). PLAN.md section B was written before
this ran. Daily bars (research/history2y/data/daily.parquet); the locked block 2024-11-01..2025-02-28 and the old
holdouts are dropped at load. Universe = point-in-time top 250 non-ETF names by prior-day adv20, blackout removed.
Label: range day = (high - low) <= 0.8 ATR14 and |close - open| <= 0.3 ATR14 (ATR from prior days).
Gate: precision >= base + 15 points in TRAIN and VALID, n >= 300. Step 2 runs only if a predictor clears it.
Usage: python b_range_predictor.py > b_out.txt   Educational only - not financial advice."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT))
from mcf.research.generator import data as GD
from mcf.longhold.signals import etf_set

SPLIT = pd.Timestamp("2025-08-31").date()


def bad_day(ds):
    ds = pd.Series(ds).astype(str)
    return (ds.between("2024-11-01", "2025-02-28") | ds.between("2026-04-01", "2026-06-30") | (ds >= "2026-09-16")).to_numpy()


D = pd.read_parquet(ROOT / "research/history2y/data/daily.parquet", columns=["symbol", "date", "open", "high", "low", "close", "adv20"])
D["date"] = pd.to_datetime(D["date"]).dt.date
D = D[~bad_day(D.date)].sort_values(["symbol", "date"])
g = D.groupby("symbol")
pc = g.close.shift(1)
tr = np.maximum(D.high, pc) - np.minimum(D.low, pc)
D["atr14"] = tr.groupby(D.symbol).transform(lambda x: x.rolling(14).mean().shift(1))
D["adv_prev"] = g.adv20.shift(1)
rngd = D.high - D.low
D["prng"] = rngd.groupby(D.symbol).shift(1)
D["nr7"] = (D.prng <= D.prng.groupby(D.symbol).transform(lambda x: x.rolling(7).min()))
ph, pl = g.high.shift(1), g.low.shift(1)
D["inside"] = (ph <= g.high.shift(2)) & (pl >= g.low.shift(2))
D["r5"] = (rngd / tr.groupby(D.symbol).transform(lambda x: x.rolling(14).mean())).groupby(D.symbol).transform(lambda x: x.rolling(5).mean().shift(1))
D["r5_pct"] = D.r5.groupby(D.symbol).transform(lambda x: x.rolling(250, min_periods=120).apply(lambda a: (a[:-1] < a[-1]).mean() if len(a) > 1 else np.nan, raw=True))
D["gap_atr"] = (D.open - pc).abs() / D.atr14
D["label"] = (rngd <= 0.8 * D.atr14) & ((D.close - D.open).abs() <= 0.3 * D.atr14)
ETF = etf_set()
S = D[~D.symbol.isin(ETF) & D.adv_prev.notna() & D.atr14.notna()]
U = S.sort_values("adv_prev", ascending=False).groupby("date").head(250)
U = U[~GD._blackout(U.symbol.to_numpy(), U.date.to_numpy())]
small = U.gap_atr <= 0.2
P = {"P1-nr7-smallgap": U.nr7 & small, "P2-inside-smallgap": U.inside & small, "P3-r5low20-smallgap": (U.r5_pct <= 0.20) & small}
out = []
for k, m in P.items():
    row = dict(predictor=k)
    ok = True
    for lab, sl in (("train", U.date <= SPLIT), ("valid", U.date > SPLIT)):
        base = float(U.label[sl].mean()); n = int((m & sl).sum()); prec = float(U.label[m & sl].mean())
        row.update({f"{lab}_n": n, f"{lab}_base": round(base, 3), f"{lab}_prec": round(prec, 3), f"{lab}_lift_pts": round((prec - base) * 100, 1)})
        ok &= (n >= 300) and (prec - base >= 0.15)
    row["gate_pass"] = bool(ok)
    out.append(row)
# reference only (not a predictor): small gap alone
O = pd.DataFrame(out)
pd.set_option("display.width", 250)
print(f"universe symbol-days {len(U)}, sessions {U.date.nunique()}")
print(O.to_string(index=False))
print("reference, |gap| <= 0.2 ATR alone: precision", round(float(U.label[small].mean()), 3), "base", round(float(U.label.mean()), 3))
O.to_csv(Path(__file__).with_name("b_results.csv"), index=False)
print(json.dumps({"predictors": len(O), "pass": int(O.gate_pass.sum())}))
print("Educational only - not financial advice.")
