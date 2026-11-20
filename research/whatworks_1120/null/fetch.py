"""OUT-NULL bar cache: 1-min SIP bars (read-only GET) for every symbol-date of a live trade of a setup with >=10 trades."""
import sys, os, numpy as np, pandas as pd
from datetime import datetime, timedelta, timezone
R, W = sys.argv[1], sys.argv[2]
sys.path.insert(0, R)
from mcf.data.alpaca_data import fetch_bars
t = pd.read_pickle(f"{W}/trades_full.pkl")
g = t.groupby("strategy").size(); t = t[t.strategy.isin(g[g >= 10].index)]
os.makedirs(f"{W}/bars", exist_ok=True)
for d, gg in sorted(t.groupby("date")):
    fn = f"{W}/bars/{d}.npz"
    if os.path.exists(fn): continue
    syms = sorted(gg.symbol.unique()); out = {}
    y, m, dd = map(int, d.split("-"))
    st = datetime(y, m, dd, 13, 0, tzinfo=timezone.utc); en = st + timedelta(hours=9)
    for i in range(0, len(syms), 150):
        ch = syms[i:i + 150]
        for att in range(3):
            try:
                got = fetch_bars(ch, st, en, feed="sip"); break
            except Exception as e:
                print("retry", d, e, flush=True); got = {}
        for s, b in got.items():
            idx = pd.DatetimeIndex(b.index).tz_convert("America/New_York")
            mi = (idx.hour * 60 + idx.minute) - 570
            ok = (mi >= 0) & (mi < 390)
            a = np.full((390, 4), np.nan, np.float32)
            a[mi[ok]] = b[["open", "high", "low", "close"]].to_numpy(np.float32)[ok]
            out[s] = a
    np.savez_compressed(fn, **out)
    print(d, len(syms), len(out), flush=True)
