"""Pattern filters on the 2-year lab trades (research/history2y/data/lab_trades.parquet: production costs, R = 0.25 x
daily ATR, first bar per symbol-day per setup), outside the rule-19 locked block (asserted; those months are not in
the file). Context spy_fo from research/history2y/data/context. Educational only - not financial advice.
Usage: python test2y_filters.py"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from symtype import symtype
H = Path("/home/user/MCF/research/history2y/data")
t = pd.read_parquet(H / "lab_trades.parquet")
t["date"] = pd.to_datetime(t.date).dt.date.astype(str)
assert not t.date.between("2024-11-01", "2025-02-28").any(), "locked block present"
t["side"] = np.where(t.setup.str.contains("long|NS1|NS5"), 1, -1)
ctx = pd.concat([pd.read_parquet(p) for p in sorted((H / "context").glob("month=*.parquet")) if p.stem.split("=")[1] not in ("2024-11", "2024-12", "2025-01", "2025-02")])
ctx["date"] = pd.to_datetime(ctx.date).dt.date.astype(str)
t = t.merge(ctx[["date", "tod", "spy_fo"]], on=["date", "tod"], how="left")
t["ty"] = t.symbol.map(symtype)
PRIM = ["MF1-945-flowsell-vwapup", "MF2-open-rsimidhi-flowsell", "MF3-open-flowsell-rsi5hi", "MF4-h40-open-flowsell",
        "NS1-rsidip-rsi5pop-long", "NS3-failed-vwap-reclaim-short", "NS4-pm-vwap-reclaim-oversold-short",
        "NS5-sma50-flush-oversold-long", "RW3 bdi-rw-gapdn-rsi5pop-flowsell", "RW5 bdi-rw-heat30-flowsell-rsi5pop-gapdn"]
reg = pd.read_csv("/home/user/MCF/research/history2y/rescore.csv") if False else None


def flags(x):
    x = x.sort_values(["date", "tod", "setup"]).reset_index(drop=True)
    x["sym_day_pos"] = x.groupby(["date", "symbol"]).cumcount() + 1
    # 10-minute chains of same-side entries per day (tod HHMM -> minutes)
    mins = (x.tod // 100) * 60 + x.tod % 100
    x["mins"] = mins
    pos = np.zeros(len(x), int)
    for _, g in x.groupby(["date", "side"]):
        m = g.mins.to_numpy(); cid = np.cumsum(np.r_[1, np.diff(m) > 10])
        pos[g.index] = pd.Series(cid).groupby(cid).cumcount().to_numpy() + 1
    x["clu_pos"] = pos
    ext = lambda th, tm: (x.tod >= tm) & (np.sign(x.spy_fo) == x.side) & (x.spy_fo.abs() >= th)
    F = {"A_one_per_symbol_day": x.sym_day_pos > 1,
         "B_no_inverse_short": (x.ty == "inverse") & (x.side < 0),
         "B2_no_inverse_or_lev": x.ty.isin(["inverse", "lev"]),
         "C_late_with_extended_spy_1330_075": ext(0.75, 1330), "C_n_1330_050": ext(0.5, 1330), "C_n_1330_100": ext(1.0, 1330),
         "C_n_1300_075": ext(0.75, 1300), "C_n_1400_075": ext(0.75, 1400),
         "E_stack_cap3_10min": x.clu_pos > 3, "E_n_stack_cap5": x.clu_pos > 5}
    return x, F


# session regime (universe median open-to-close terciles, as gates.py) for the up / down split
try:
    sys.path.insert(0, "/home/user/MCF/research/history2y")
    import lib
    rg = lib.regimes() if hasattr(lib, "regimes") else None
except Exception as e:  # noqa
    rg = None
rows = []
for pname, x0 in [("primary10", t[t.setup.isin(PRIM)]), ("all21", t)]:
    x, F = flags(x0.copy())
    for name, m in F.items():
        dl = -x.r.where(m, 0.0).groupby(x.date).sum()  # day R change from skipping
        dl = dl.reindex(x.date.unique(), fill_value=0)
        tt = dl.mean() / (dl.std(ddof=1) / np.sqrt(len(dl)))
        # walk-forward style: share of months where skipping helped
        mo = dl.groupby(pd.Index(dl.index).str[:7]).sum()
        rows.append(dict(portfolio=pname, filter=name, n=len(x), n_cut=int(m.sum()), avgR_cut=x.r[m].mean(),
                         avgR_before=x.r.mean(), avgR_after=x.r[~m].mean(), sumR_before=x.r.sum(), sumR_after=x.r[~m].sum(),
                         day_t=tt, months_helped=f"{int((mo > 0).sum())}/{len(mo)}",
                         best_day_share=(dl.max() / dl.sum()) if dl.sum() > 0 else np.nan))
o = pd.DataFrame(rows); o.to_csv(Path(__file__).parent / "filters_2y.csv", index=False, float_format="%.4f")
pd.set_option("display.width", 220); print(o.round(3).to_string())
print("symbol types in lab trades:", t.ty.value_counts().to_dict(), "regime fn:", rg is not None)
