"""2008 / dot-com proxy for S6 (PLAN.md 4; diagnostic, not counted, not a gate).

The repo has no stock or ETF bars before 2016. The longest history is Ken French daily factors (Mkt-RF, RF, Mom,
1926..2026-08, saved by research/bdi/saturday1010/rework; locked-block rows already removed). S6's daily returns
are regressed on Mkt-RF and Mom over train+valid; the proxy RF + b_m (Mkt-RF) + b_u Mom (no intercept) is replayed
through the SAME book-level overlay code as protect.py (its source is extracted, not copied). Per-name stops and
breadth cannot be proxied with factor data. Usage: python proxy2008.py <cost per unit exposure change>.
Educational only - not financial advice.
"""
from __future__ import annotations

import ast
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
LH = HERE.parent
FF = LH.parents[1] / "research" / "bdi" / "saturday1010" / "rework" / "data"
CPU = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0003

src = (HERE / "protect.py").read_text()
fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "overlay")
ns = {"np": np, "math": math}
exec(compile(ast.Module([fn], []), "protect.overlay", "exec"), ns)
overlay = ns["overlay"]

f3 = pd.read_parquet(FF / "ff_factors3_daily.parquet")
fm = pd.read_parquet(FF / "ff_mom_daily.parquet")
ff = f3.merge(fm, on="date")
ff["date"] = pd.to_datetime(ff["date"])
ff = ff.set_index("date").sort_index()

ref = pd.read_parquet(LH / "data" / "daily_returns.parquet")
s6 = ref["S6_mom12_1rev_N20_W"]
tv = s6[(s6.index >= "2017-01-01") & (s6.index <= "2024-10-31")]
j = ff.join(tv.rename("y"), how="inner")
X = np.column_stack([np.ones(len(j)), j["Mkt-RF"], j["Mom"]])
y = j["y"] - j["RF"]
coef, *_ = np.linalg.lstsq(X, y, rcond=None)
resid = y - X @ coef
r2 = 1 - resid.var() / y.var()
a, bm, bu = coef
print(f"fit train+valid: alpha {a * 252:.3f}/yr  b_mkt {bm:.2f}  b_mom {bu:.2f}  R2 {r2:.2f}  days {len(j)}")

d = ff.index
r = (ff["RF"] + bm * ff["Mkt-RF"] + bu * ff["Mom"]).to_numpy()
mkt_idx = np.cumprod(1 + (ff["Mkt-RF"] + ff["RF"]).to_numpy())
n = len(d)
dser = pd.Series(np.arange(n), index=d)
month_end = dser.groupby([d.year, d.month]).max().to_numpy()
iso = d.isocalendar()
week_end = dser.groupby([iso.year.values, iso.week.values]).max().to_numpy()
sma = {k: pd.Series(mkt_idx).rolling(k, min_periods=k).mean().to_numpy() for k in (50, 200)}
me = pd.Series(mkt_idx[month_end], index=month_end)
m10 = np.full(n, np.nan); m10[month_end] = (me - me.rolling(10, min_periods=10).mean()).to_numpy()
lockd = np.zeros(n, bool)
zeros = np.zeros(n)
rf = ff["RF"].to_numpy()

CFG = {"BASE_proxy": None}
for X_ in (0.10, 0.15, 0.20):
    for re in ("4w", "8w", "s50", "s200"):
        CFG[f"B_dd{int(X_ * 100)}_{re}"] = ("dd", (X_, re))
for p in ("d200", "w200", "m10", "w200_half"):
    CFG[f"B_trend_{p}"] = ("trend", p)
for tg, daily in ((0.20, False), (0.30, False), (0.40, False), (0.30, True)):
    CFG[f"B_vt{int(tg * 100)}_20d" + ("_daily" if daily else "")] = ("vt", (tg, daily))

WIN = {"pre_1990_2015": ("1990-01-01", "2015-12-31"), "dotcom_2000_03": ("2000-03-01", "2003-03-31"),
       "gfc_2007_10_2009_03": ("2007-10-09", "2009-03-09"), "momcrash_2009_03_05": ("2009-03-09", "2009-05-29"),
       "gfc_full_2007_06_2010_12": ("2007-06-01", "2010-12-31"), "aug2015_feb2016": ("2015-08-01", "2016-02-29")}


def mdd(x):
    eq = np.cumprod(1 + x)
    return float((eq / np.maximum.accumulate(eq) - 1).min())


rows = []
win_starts = {k: int(np.searchsorted(d, pd.Timestamp(v[0]))) for k, v in WIN.items()}
for cid, spec in CFG.items():
    for wn, (a0, b0) in WIN.items():
        # each window is run from 2 years before its start so trend / vol state is warm; stats on the window only
        i0 = max(0, win_starts[wn] - 504)
        m = (d >= a0) & (d <= b0)
        sl = slice(i0, n)
        rr_full = r[sl]
        if spec is None:
            out = rr_full; expo = np.ones(len(rr_full))
        else:
            o = overlay(rr_full, zeros[sl], zeros[sl], zeros[sl], CPU, spec[0], spec[1], mkt_idx[sl],
                        {k: v[sl] for k, v in sma.items()}, set((week_end[week_end >= i0] - i0).tolist()),
                        set((month_end[month_end >= i0] - i0).tolist()), rf[sl], lockd[sl], m10[sl])
            out, expo = o["r"], o["s"]
        mm = m[sl]
        x = out[mm]
        yrs = len(x) / 252
        rows.append({"id": cid, "window": wn, "ret": float(np.prod(1 + x) - 1),
                     "cagr": float(np.prod(1 + x) ** (1 / yrs) - 1), "vol": float(x.std() * math.sqrt(252)),
                     "sharpe": float(x.mean() / x.std() * math.sqrt(252)), "maxdd": mdd(x),
                     "avg_exposure": float(expo[mm].mean())})
out = pd.DataFrame(rows)
out.to_csv(HERE / "proxy.csv", index=False, float_format="%.4f")
pd.set_option("display.width", 200)
print(out.pivot(index="id", columns="window", values="ret").round(3))
print(out[out.window == "pre_1990_2015"].set_index("id")[["cagr", "vol", "sharpe", "maxdd", "avg_exposure"]].round(3))
print(out.pivot(index="id", columns="window", values="maxdd").round(3))
