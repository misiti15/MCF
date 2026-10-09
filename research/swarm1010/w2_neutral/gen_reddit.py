"""The 40 Reddit base rules (20 strategies x long/short, no filter, t1s1, full day 09:50-15:00, first bar per
symbol-day) generated with research/bdi/reddit/engine.py + strategies.py exactly as research/bdi/regime1009/gen_reddit.py,
but over row chunks (whole symbols) so memory stays < ~1.5 GB (the engine's Data loads ~5 GB). Every strategy only uses
within-symbol-day information plus SPY at the same (day, tod), which is precomputed once. Output (git-ignored):
data/reddit_trades.parquet (date, symbol, tod, r, setup, side). Educational only - not financial advice."""
import sys
import zipfile

import numpy as np
import pandas as pd

from common import DATA, ROOT, lib

RD = ROOT / "research" / "bdi" / "reddit"
sys.path.insert(0, str(RD))
import engine as E  # noqa: E402
import strategies as S  # noqa: E402

BASE = E.SDIR / "base.npz"
zb = zipfile.ZipFile(BASE)


def read_slice(key, a, b):
    f = zb.open(key + ".npy")
    v = np.lib.format.read_magic(f)
    rd = np.lib.format.read_array_header_1_0 if v == (1, 0) else np.lib.format.read_array_header_2_0
    shape, fortran, dtype = rd(f)
    off = f.tell()
    f.seek(off + a * dtype.itemsize)
    return np.frombuffer(f.read((b - a) * dtype.itemsize), dtype=dtype).copy()


sym = np.load(BASE)["sym"]
NR = len(sym)
ext = np.load(RD / "data" / "extra.npz")
EXT = {k: ext[k] for k in ext.files}
dates = pd.read_csv(E.SDIR / "dates.csv").iloc[:, 0].tolist()
symbols = pd.read_csv(E.SDIR / "symbols.csv").iloc[:, 0].astype(str).tolist()
reg = lib.regimes()
regd = reg.reindex(pd.to_datetime(dates).date)["regime"].to_numpy()
regc = np.select([regd == "up", regd == "down"], [1, -1], 0)

# SPY series keyed by day*10000+tod (global)
spy = symbols.index("SPY")
sr = np.flatnonzero(sym == spy)
_z = np.load(BASE)
g = {k: _z[k][sr] for k in ("z", "fromOpen", "close", "atr_d", "day", "tod")}
del _z
kspy = g["day"].astype(np.int64) * 10000 + g["tod"].astype(np.int64)
c_, a_, fo_ = g["close"].astype(float), g["atr_d"].astype(float), g["fromOpen"].astype(float)
SPY_Z = pd.Series(g["z"].astype(float), index=kspy)
SPY_FO = pd.Series((fo_ / 100) * c_ / (1 + fo_ / 100) / a_, index=kspy)


class ChunkData(E.Data):
    def __init__(self, a, b):
        self.B = {k: read_slice(k, a, b) for k in E.KEYS}
        self.B.update({k: v[a:b] for k, v in EXT.items()})
        self.dates, self.symbols, self.regc, self.reg, self.nd = dates, symbols, regc, reg, len(dates)
        sd = self.B["sd"]
        self.new = np.r_[True, sd[1:] != sd[:-1]]
        self._cache = {}
        B = self.B
        c, at = B["close"].astype(float), B["atr_d"].astype(float)
        self.c, self.atr, self.tod = c, at, B["tod"]
        self.h = c + B["hi_atr"].astype(float) * at
        self.l = c - B["lo_atr"].astype(float) * at
        self.hod = c + B["dist_hod_atr"].astype(float) * at
        self.lod = c - B["dist_lod_atr"].astype(float) * at
        self.open_d = c / (1 + B["fromOpen"].astype(float) / 100)
        self.pdc = self.open_d / (1 + B["gap"].astype(float) / 100)
        self.chg = (c / self.pdc - 1) * 100
        self.vwap = c / (1 + B["vwapDistPct"].astype(float) / 100)
        self.sma20 = c / (1 + B["sma20_dist_pct"].astype(float) / 100)
        k = B["day"].astype(np.int64) * 10000 + B["tod"].astype(np.int64)
        self.spy_z = SPY_Z.reindex(k).to_numpy()
        self.spy_fo_atr = SPY_FO.reindex(k).to_numpy()
        self.fo_atr = (c - self.open_d) / at


sdall = np.load(BASE)["sd"]
assert (np.diff(sdall) >= 0).all(), "rows not sorted by symbol-day"
cuts = np.flatnonzero(np.r_[True, sdall[1:] != sdall[:-1]])
bounds = [int(cuts[int(i)]) for i in np.linspace(0, len(cuts), 13)[:-1]] + [NR]
del sdall
del sym
out = []
for a, b in zip(bounds[:-1], bounds[1:]):
    D = ChunkData(a, b)
    for name, (fn, p, grid, key) in S.STRATS.items():
        for s in (1, -1):
            side = "long" if s > 0 else "short"
            o = fn(D, s, p)
            idx, r = E.trades(D, o["ev"], side, "t1s1", None, None, 950, 1500)
            out.append(pd.DataFrame({"day": D.B["day"][idx].astype(np.int32), "tod": D.tod[idx].astype(np.int32),
                                     "sym": D.B["sym"][idx].astype(np.int32), "r": r.astype(np.float32),
                                     "setup": f"RDT-{name}-{side}", "side": side}))
    print("chunk", a, b, sum(len(x) for x in out), flush=True)
    del D
T = pd.concat(out, ignore_index=True)
T["date"] = np.array(pd.to_datetime(dates).date)[T["day"].to_numpy()]
T["symbol"] = np.array(symbols)[T["sym"].to_numpy()]
T = T.drop(columns=["sym", "day"])
T["setup"] = T["setup"].astype("category")
T.to_parquet(DATA / "reddit_trades.parquet")
for k, gg in T.groupby("setup", observed=True):
    print(k, len(gg), round(float(gg["r"].mean()), 4))
