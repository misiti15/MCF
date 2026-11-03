"""Exit what-ifs on the 2-year lab trades of the 10 lab setups that ran in Primary 10-20..11-02, simulated on the 5-minute
lab frames (entry at the signal bar's close, R = 0.25 x daily ATR, t1s1, exits by 15:55, stop-first, production costs
via sim.cost; the frames carry no open, so a gap through the stop fills at the prior close: slightly optimistic for every
variant alike). Paired vs the same engine's baseline. Locked block never loaded (asserted).
Usage: python test2y_exits.py <scratch>. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.dataset as ds
sys.path.insert(0, str(Path(__file__).parent))
from sim import run
PRIM = ["MF1-945-flowsell-vwapup", "MF2-open-rsimidhi-flowsell", "MF3-open-flowsell-rsi5hi", "MF4-h40-open-flowsell",
        "NS1-rsidip-rsi5pop-long", "NS3-failed-vwap-reclaim-short", "NS4-pm-vwap-reclaim-oversold-short",
        "NS5-sma50-flush-oversold-long", "RW3 bdi-rw-gapdn-rsi5pop-flowsell", "RW5 bdi-rw-heat30-flowsell-rsi5pop-gapdn"]  # = test2y_filters.PRIM
H = Path("/home/user/MCF/research/history2y/data")
S = Path(sys.argv[1])
t = pd.read_parquet(H / "lab_trades.parquet"); t = t[t.setup.isin(PRIM)].copy()
t["date"] = pd.to_datetime(t.date).dt.date.astype(str)
t["side"] = np.where(t.setup.str.contains("long"), 1, -1)
V = {"base": {}, "wide15": {"wide": 1.5}, "scr60": {"scratch": (12, 0.25)}, "ts60": {"time_stop": 12}, "be03": {"be_at": 0.3},
     "part05": {"partial": 0.5}}
rows = []
for mo in sorted(t.date.str[:7].unique()):
    assert mo not in ("2024-11", "2024-12", "2025-01", "2025-02")
    x = t[t.date.str[:7] == mo]
    syms = sorted(x.symbol.unique())
    f = ds.dataset(str(H / "frames" / f"month={mo}"), format="parquet").to_table(
        columns=["symbol", "date", "tod", "close", "high", "low", "atr_d"], filter=ds.field("symbol").isin(syms)).to_pandas()
    f["date"] = pd.to_datetime(f.date).dt.date.astype(str)
    G = {k: g.sort_values("tod") for k, g in f.groupby(["symbol", "date"])}
    for r in x.itertuples():
        g = G.get((r.symbol, r.date))
        if g is None:
            continue
        tod = g.tod.to_numpy(); j = np.searchsorted(tod, r.tod)
        if j >= len(tod) or tod[j] != r.tod:
            continue
        c = g.close.to_numpy(float); h = g.high.to_numpy(float); l = g.low.to_numpy(float)
        o = np.r_[c[0], c[:-1]]
        end = int(np.searchsorted(tod, 1555, side="right")) - 1
        if j + 1 > end:
            continue
        e = c[j]; d = 0.25 * float(g.atr_d.iloc[j])
        if not d > 0:
            continue
        out = dict(setup=r.setup, date=r.date, symbol=r.symbol, tod=r.tod, lab_r=r.r)
        for k, kw in V.items():
            out[k] = run(o, h, l, c, j + 1, r.side, e, d, d, end, **kw)[0]
        rows.append(out)
    print(mo, len(rows), flush=True)
R = pd.DataFrame(rows); R.to_parquet(S / "exits2y.parquet", index=False)
print("corr sim base vs lab r", R[["base", "lab_r"]].corr().iloc[0, 1], "means", R.base.mean(), R.lab_r.mean())
