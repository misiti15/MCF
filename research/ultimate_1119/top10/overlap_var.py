"""Overlap of every variant's booked T1 symbol-sessions (fit + check) with: the live top 10 + ST7-FD (home books,
top10w/booked_trades.parquet), three more live setups that share a mechanism (signal level: NM-ETF-late-dip-di-long-WB4
Testing E, NM-ETF-late-dip-di-long-WB1 Explore 1, NS3-failed-vwap-reclaim-short Testing E), and every other variant.
    python overlap_var.py WORK  -> overlap.json. Educational only - not financial advice."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bench10 as B, score_var as S, bench_var as V, bench_var_earn as E  # noqa
W = Path(sys.argv[1])
etb = pd.read_parquet(HERE / "etb_rate.parquet").rate
T1 = B.add_r(pd.read_parquet(W / "trades_t1.parquet")); T1["half"] = B.half(T1.date)
disp = pd.read_parquet(W / "disp.parquet").disp
allv = {**V.VARIANTS, **E.EARN_VARIANTS, **S.GATED}
ks = lambda t: set(zip(t.symbol.astype(str), t.date.astype(str)))
vs = {}
for v, ens in allv.items():
    bs = []
    for en in ens:
        a = T1[(T1.setup == en)]
        if v in S.GATED:
            thr = np.where(a.half == "fit", S.DISP_THR["fit"], S.DISP_THR["check"])
            a = a[(a.date.map(disp) >= thr).to_numpy()]
        bs.append(B.book(a, B.TESTING_RULES, etb))
    b = pd.concat(bs); vs[v] = ks(b[b.half != "none"])
live = pd.read_parquet(W.parent / "top10w" / "booked_trades.parquet")
live = live[(live.test == "T1") & (live.half != "none")]
ls = {s: ks(g) for s, g in live.groupby("setup")}
x = pd.concat([pd.read_parquet(p) for p in sorted((W / "livex").glob("sig1_*.parquet"))])
x = x[B.half(x.date) != "none"]
for s, g in x.groupby("setup"):
    ls[s + " (signal level)"] = ks(g)
out = {}
for v, a in vs.items():
    n = len(a)
    L = {s: round(len(a & b) / n, 3) for s, b in ls.items()} if n else {}
    Vv = {u: round(len(a & b) / n, 3) for u, b in vs.items() if u != v} if n else {}
    out[v] = {"n_symbol_sessions": n, "live": dict(sorted(L.items(), key=lambda z: -z[1])[:3]),
              "variants_ge70": {u: z for u, z in sorted(Vv.items(), key=lambda z: -z[1]) if z >= 0.7},
              "variants_top": dict(sorted(Vv.items(), key=lambda z: -z[1])[:3])}
    print(v, n, out[v]["live"], out[v]["variants_top"])
(HERE / "overlap.json").write_text(json.dumps(out, indent=1))
