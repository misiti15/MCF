"""Item 4: 2-year lab trades for the Primary five + MF family (open history, sessions <= 2026-10-05, locked block refused by
lib). Writes one small parquet of trades (setup, date, symbol, tod, r, gap, spy_fo). Usage: python item4_lab.py <out.parquet> [months...]
Educational only - not financial advice."""
import sys, time, importlib.util, numpy as np, pandas as pd
ROOT = "/home/user/MCF"
sys.path.insert(0, ROOT); sys.path.insert(0, f"{ROOT}/research/history2y")
from lib import load_month, months
from mcf.research import gates as G
LAST = "2026-10-05"
FD = f"{ROOT}/research/bdi/fullday"
S = {  # name: (module path, min_adv, window, gap_le prefilter)
 "L3-gap-slope-fromopen-FD": (f"{FD}/L3-gap-slope-fromopen-FD.py", 0, (950, 1500), -2.6573517322540283),
 "NM-ETF-late-dip-di-long": (f"{ROOT}/research/swarm1017/arena-index-etf/modules/AR-ETF-late-dip-di-long.py", 95e6, (1400, 1500), None),
 "RW3-gapdn-rsi5pop-flowsell-short-FD": (f"{FD}/RW3-gapdn-rsi5pop-flowsell-short-FD.py", 95e6, (950, 1500), None),
 "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": (f"{FD}/RW5-heat30-flowsell-rsi5pop-gapdn-short-FD.py", 95e6, (950, 1500), None),
 "ST7-rsi50dn-long-pm-t1s1-FD": (f"{FD}/ST7-rsi50dn-long-pm-t1s1-FD.py", 95e6, (950, 1500), None),
 "MF1-945-flowsell-vwapup-FD": (f"{FD}/MF1-945-flowsell-vwapup-FD.py", 95e6, (950, 1500), None),
 "MF2-open-rsimidhi-flowsell-FD": (f"{FD}/MF2-open-rsimidhi-flowsell-FD.py", 95e6, (950, 1500), None),
 "MF3-open-flowsell-rsi5hi-FD": (f"{FD}/MF3-open-flowsell-rsi5hi-FD.py", 95e6, (950, 1500), None),
 "MF4-h40-open-flowsell-FD": (f"{FD}/MF4-h40-open-flowsell-FD.py", 95e6, (950, 1500), None),
 "MF5-flowsell-vwapup-rsi5hi-FD": (f"{FD}/MF5-flowsell-vwapup-rsi5hi-FD.py", 95e6, (950, 1500), None),
}
def load(p, n):
    sys.path.insert(0, p.rsplit("/", 1)[0])
    s = importlib.util.spec_from_file_location(n.replace("-", "_"), p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
MOD = {k: load(v[0], k) for k, v in S.items()}
out_path = sys.argv[1]; mos = sys.argv[2:] or months()
out = []; t0 = time.time()
for mo in mos:
    df = load_month(mo, context=True)
    df = df[df.date.astype(str) <= LAST].reset_index(drop=True)
    if df.empty: continue
    tod = df.tod.to_numpy(float); adv = df.adv20.fillna(0).to_numpy(float); gap = df.gap.to_numpy(float)
    for name, (p, mina, (w0, w1), gle) in S.items():
        m = MOD[name]; side, geom = m.SIDE, m.GEOM
        base = (tod >= w0) & (tod <= w1) & (adv >= mina)
        if gle is not None: base &= gap <= gle
        mk = np.asarray(m.mask(df), bool) & base & np.isfinite(df[f"r_{side}_{geom}"].to_numpy(float)) & (df.atr_d.to_numpy(float) > 0)
        idx = G.first_per_symbol_day(df.symbol.to_numpy(), df.date.to_numpy(), mk)
        if not len(idx): continue
        r = G.prod_r(df[f"r_{side}_{geom}"].to_numpy(float)[idx], df[f"win_{side}_{geom}"].to_numpy(float)[idx],
                     df.close.to_numpy(float)[idx], df.atr_d.to_numpy(float)[idx], geom, tod=tod[idx])
        out.append(pd.DataFrame({"setup": name, "date": df.date.astype(str).to_numpy()[idx], "symbol": df.symbol.astype(str).to_numpy()[idx],
                                 "tod": tod[idx], "r": r, "gap": gap[idx], "spy_fo": df.spy_fo.to_numpy(float)[idx]}))
    print(mo, len(df), f"{time.time()-t0:.0f}s", flush=True); del df
pd.concat(out, ignore_index=True).to_parquet(out_path)
