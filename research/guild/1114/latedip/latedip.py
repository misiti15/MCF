"""LATEDIP (Observer obs-latedip ask, Lead lead-20261114-0300-4; descriptive, 0 configs, one look): 2-year lab trades of
AR-ETF-late-dip-di-long (NM-ETF-late-dip-di-long; module conds unchanged: ret3 <= -0.80%, +DI7 >= -DI7, daily ATR >= 3.6%,
bar close 14:00-15:00, t05s1, first signal per symbol-day; module symbol list, 100 of 124 ETFs are in the frames),
locked block never read. Per trade: net R (frame r_long_t05s1, production costs), SPY sign-so-far at entry (frame spy_fo at
the decision bar's close), and SAME-MINUTE cross-sectional controls among the module's other ETFs with daily ATR >= 3.6%
(similar leverage): A = all of them, B = those also down over the last 15 min (ret3 < 0). Excess = R - control mean.
    python latedip.py          Educational only - not financial advice."""
import importlib.util, os, sys
from pathlib import Path
import numpy as np, pandas as pd
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
HERE = Path(__file__).resolve().parent; ROOT = Path("/home/user/MCF")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
import lib  # noqa: E402
from mcf.research.arena.indicators import compute  # noqa: E402
spec = importlib.util.spec_from_file_location("m", ROOT / "research/swarm1017/arena-index-etf/modules/AR-ETF-late-dip-di-long.py")
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
ATR_MIN = M.CONDS[2][2]; TR_END, VA_END = "2025-09-30", "2026-10-07"
rows = []
for mo in [m for m in lib.months() if m not in lib.LOCKED_MONTHS]:
    f = lib.load_month(mo, context=True); f["symbol"] = f.symbol.astype(str)
    f = f[f.symbol.isin(M.SYMBOLS)].sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
    if not len(f):
        continue
    x = compute(f, names=["atr_d_pct", "di_diff7", "ret3"], context=False)
    f["atr_d_pct"], f["ret3"] = x["atr_d_pct"].to_numpy(float), x["ret3"].to_numpy(float)
    m = np.asarray(M.mask(f), bool) & np.isfinite(f.r_long_t05s1.to_numpy(float))
    sig = f[m].groupby(["symbol", "date"]).head(1)
    hv = f[(f.atr_d_pct >= ATR_MIN) & np.isfinite(f.r_long_t05s1)]
    for r in sig.itertuples():
        c = hv[(hv.date == r.date) & (hv.tod == r.tod) & (hv.symbol != r.symbol)]
        cb = c[c.ret3 < 0]
        rows.append(dict(date=str(r.date), symbol=r.symbol, tod=int(r.tod), r=float(r.r_long_t05s1), spy_fo=float(r.spy_fo),
                         ctrlA=c.r_long_t05s1.mean() if len(c) else np.nan, nA=len(c),
                         ctrlB=cb.r_long_t05s1.mean() if len(cb) else np.nan, nB=len(cb)))
    print(mo, len(sig), flush=True)
T = pd.DataFrame(rows)
T["per"] = np.where(T.date <= TR_END, "TRAIN", np.where(T.date <= VA_END, "VALID", "FWD"))
T["read"] = np.where(T.spy_fo > 0, "up", np.where(T.spy_fo < 0, "down", "flat"))
T["exA"], T["exB"] = T.r - T.ctrlA, T.r - T.ctrlB
T.to_csv(HERE / "latedip_trades.csv", index=False)


def cell(g, col):
    g = g[np.isfinite(g[col])]; d = g.groupby("date")[col].sum()
    t = d.mean() / (d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 2 and d.std() > 0 else np.nan
    return pd.Series(dict(n=len(g), days=len(d), mean=g[col].mean(), t_day=t,
                          best_share=d.max() / d.sum() if d.sum() > 0 else np.nan, tot_wo_best=d.sum() - d.max()))


pd.set_option("display.width", 220)
for col in ("r", "exA", "exB"):
    print(f"\n{col}  (r = net R; exA / exB = R minus same-minute high-vol ETF control A all / B also dipping)")
    print(pd.DataFrame({(p, rd): cell(g, col) for (p, rd), g in T.groupby(["per", "read"])}).T.round(3).to_string())
    print(pd.DataFrame({p: cell(g, col) for p, g in T.groupby("per")}).T.round(3).to_string())
T["ym"] = T.date.str[:7]
print("\nby month (n, mean r, mean exB):"); print(T.groupby("ym").agg(n=("r", "size"), r=("r", "mean"), exB=("exB", "mean")).round(3).to_string())
print("\nDescriptive only (0 configs). Educational only - not financial advice.")
