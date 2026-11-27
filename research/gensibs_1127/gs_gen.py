"""GENSIBS-1127: bench10 lots for the 56 pre-registered sibling configs (gs_grid.py) + random-entry pools.
Wraps research/ultimate_1119/top10/bench10.py (as research/arenastars_1127/as_gen.py does) with:
  - inventory = the grid (no config file is read; each config is a CONDS mask on the lab frame);
  - indicators computed once per frame for the union of names (shared cache), then each config masks;
  - hold / holdtr geometry (stop 1R, no target; holdtr trails 1R behind the best price once MFE >= 1R);
  - random pools: per symbol-day with prob Q (crc32 seeded) one uniformly random eligible bar 09:50-15:00
    (adv20 >= $95M, atr > 0, close >= $5), emitted as short/long x hold/holdtr with the bar's context columns;
  - T2 context = ctx_t2.parquet (breadth / breadth_open from the T2 1-minute cache; ARENASTARS t2ctx.py output).
Usage (cwd = repo root): python research/gensibs_1127/gs_gen.py W sig1|walk1|t2. Locked block never read
(bench10 guards: lib refuses locked months, hist_bars filters them, no_locked asserts on every signal set).
Educational only - not financial advice."""
import os
import sys
import zlib
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / "research/ultimate_1119/top10"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "never reads the locked block"
import bench10 as B  # noqa: E402
from gs_grid import CTX, RND_POOLS, grid  # noqa: E402
from mcf.research.arena.indicators import compute  # noqa: E402

G = grid()
NAMES = sorted({c[0] for x in G for c in x["conds"] if c[0] not in CTX})
Q = 0.05
CTXCOLS = ["breadth", "breadth_open", "qqq_fo", "spy_fo"]
B.GEOMS["hold"] = (np.nan, 1.0)
B.GEOMS["holdtr"] = (np.nan, 1.0)


def _cmp(a, op, v):
    with np.errstate(invalid="ignore"):
        return {"<=": a <= v, "<": a < v, ">=": a >= v, ">": a > v, "==": a == v}[op]


_IND = {}


def _ind(df):
    k = (id(df), len(df))
    if k not in _IND:
        _IND.clear()
        _IND[k] = compute(df, names=NAMES, context=False)
    return _IND[k]


class Mod:
    def __init__(self, cfg):
        self.c = cfg
        self.SIDE, self.GEOM = cfg["side"], cfg["geom"]

    def mask(self, df):
        x = _ind(df)
        m = np.ones(len(df), bool)
        for nm, op, v in self.c["conds"]:
            if nm in CTX:
                a = df[nm].to_numpy(float) if nm in df.columns else np.full(len(df), np.nan)
            else:
                a = x[nm].to_numpy(dtype=np.float32).astype(float)
                v = float(np.float32(v))
            m &= _cmp(a, op, v)
        return m


def inventory():
    return [dict(setup=x["id"], module=x["id"], side=1 if x["side"] == "long" else -1, geom=x["geom"],
                 w_lo=x["window"][0], w_hi=x["window"][1], min_adv=x["min_adv"], refire=False, cooldown=1,
                 prefilter="", account="testing", cfg="grid", struct=False, cwt=False) for x in G]


_BYID = {x["id"]: x for x in G}


def load_mod(name, module):
    return Mod(_BYID[name])


_orig_signals = B.signals


def signals(f, fx, inv, mods):
    o = _orig_signals(f, fx, inv, mods)
    rows = []
    if f is not None and len(f):
        tod = f["tod"].to_numpy(); adv = f["adv20"].fillna(0).to_numpy(float); atr = f["atr_d"].to_numpy(float)
        c = f["close"].to_numpy(float); sy = f["symbol"].astype(str).to_numpy(); dt = f["date"].astype(str).to_numpy()
        gap = f["gap"].to_numpy(float)
        ok = (tod >= 950) & (tod <= 1500) & (adv >= 95e6) & (atr > 0) & (c >= 5)
        hit = np.flatnonzero(ok)
        if len(hit):
            key = pd.Series(sy[hit] + "|" + dt[hit])
            pick = []
            for k, ix in key.groupby(key).indices.items():
                h = zlib.crc32(("GS" + k).encode())
                if (h % 10000) / 10000.0 < Q:
                    pick.append(hit[ix[(h // 10000) % len(ix)]])
            if pick:
                idx = np.asarray(sorted(pick)); e = c[idx]; R = 0.25 * atr[idx]
                for side, geom in RND_POOLS:
                    s = 1 if side == "long" else -1
                    d = pd.DataFrame({"setup": f"RND-{side}-{geom}", "symbol": sy[idx], "date": dt[idx],
                                      "tod": tod[idx].astype(int), "side": s, "entry": e, "stop": e - s * R,
                                      "tgt": np.nan, "risk": R, "gap": gap[idx], "adv20": adv[idx]})
                    for cc in CTXCOLS:
                        d[cc] = f[cc].to_numpy(float)[idx] if cc in f.columns else np.nan
                    rows.append(d)
    if rows:
        o = pd.concat([o] + rows, ignore_index=True) if len(o) else pd.concat(rows, ignore_index=True)
        o = o[(o.risk > 0) & np.isfinite(o.risk)].reset_index(drop=True)
    if len(o):
        geo = {x["id"]: x["geom"] for x in G}
        g = o.setup.map(geo)
        g = g.where(g.notna(), o.setup.str.split("-").str[-1])
        o["trail"] = (g == "holdtr").astype(int)
        B.no_locked(o["date"].unique())
    return o


def walk_trades(T, b):
    """bench10.walk_trades + trailing (column trail), as research/arenastars_1127/as_gen.py: after each minute, MFE
    from the high/low; once MFE >= 1R the stop moves to entry + side x (MFE - 1) x risk (never loosened)."""
    hhmm = b.index.hour * 100 + b.index.minute
    day = b.index.date.astype(str)
    O, H, Lo, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    byday = {dd: np.flatnonzero(day == dd) for dd in np.unique(day)}
    res = []
    for r in T.itertuples():
        ix = byday.get(r.date)
        if ix is None:
            res.append((r.Index, np.nan, -1, -1)); continue
        hm = hhmm[ix]
        sel = ix[(hm >= r.tod) & (hm < 1555)]
        after = ix[hm >= 1555]
        s, e, stop, tgt = r.side, r.entry, r.stop, r.tgt
        risk = abs(e - stop); trail = int(getattr(r, "trail", 0) or 0); mfe = 0.0
        px = None
        for k in sel:
            if (s == 1 and Lo[k] <= stop) or (s == -1 and H[k] >= stop):
                px, kd, xt = (min(O[k], stop) if s == 1 else max(O[k], stop)), 1, hhmm[k]
                break
            if tgt == tgt and ((s == 1 and H[k] >= tgt + 0.01) or (s == -1 and Lo[k] <= tgt - 0.01)):
                px, kd, xt = tgt, 2, hhmm[k]
                break
            if trail:
                fav = H[k] if s == 1 else Lo[k]
                mfe = max(mfe, s * (fav - e) / risk)
                if mfe >= 1.0:
                    nst = e + s * (mfe - 1.0) * risk
                    stop = max(stop, nst) if s == 1 else min(stop, nst)
        if px is None:
            if len(after):
                px, kd, xt = O[after[0]], 0, 1555
            elif len(sel):
                px, kd, xt = C[sel[-1]], 0, hhmm[sel[-1]] + 1
            else:
                res.append((r.Index, np.nan, -1, -1)); continue
        res.append((r.Index, px, kd, xt))
    return res


B.inventory = inventory
B.load_mod = load_mod
B.signals = signals
B.walk_trades = walk_trades

if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True)
    st = sys.argv[2]
    if st == "sig1":
        import research.history2y.lib as lib
        lib.DATA = B.DATA
        ms = [m for m in lib.months() if m not in B.LOCKED_MONTHS and not (W / f"sig1_{m}.parquet").exists()]
        if len(sys.argv) > 3:
            ms = [m for m in ms if m in sys.argv[3].split(",")]
        with Pool(int(os.environ.get("GS_WORKERS", 3))) as p:
            for r in p.imap_unordered(B.month_job, [(m, str(W)) for m in ms]):
                print(r[0], r[1], flush=True)
    elif st == "walk1":
        B.walk1(W)
    elif st == "t2":
        c = pd.read_parquet(W / "ctx_t2.parquet"); c["date"] = c.date.astype(str)
        B.WCTX["ctx"] = c.drop(columns=["n"])
        B.t2(W)
