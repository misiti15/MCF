"""ARENASTARS-1127: bench10 lots for the P4 Primary setups + the 3 arena candidates (G05, G07, G37) + random-entry
control pools (RND-*). Wraps research/ultimate_1119/top10/bench10.py (squeeze_1125/gen.py pattern) with:
  - hold / holdtr geometry (stop 1R, no target; holdtr trails 1R behind the best price once MFE >= 1R, updated after
    each minute as mcf/backtest/engine.py; stop checked first inside a minute);
  - T2 context = ctx_t2.parquet (t2ctx.py: breadth / breadth_open from the T2 1-minute cache);
  - control pool: for each candidate, every eligible symbol-day (window, min_adv, atr > 0, close >= $5) enters with
    probability Q at one uniformly random eligible bar (seeded by symbol|date), same side / geometry.
Usage (cwd repo): python as_gen.py W sig1|walk1|t2. Locked block never read (bench10 guards + asserts).
Educational only - not financial advice."""
import sys
import zlib
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / "research/ultimate_1119/top10"))
import bench10 as B  # noqa: E402

CAND = [("GEN-261022-05-MACDhge0p079-UpWickge0p71-ORHdistlem0p38-PM-BRoplt0p35-holdtr-short", "account_explore1.yaml", "explore1"),
        ("GEN-261026-07-Flow3ge0p56-BBpctge0p98-ADX7le34-PM-BRvwlt0p3-holdtr-short", "account_testing2.yaml", "testing2"),
        ("GEN-261023-07-RSIslopege9p1-BarRngATRge0p087-VWAPcrossesge8-LUNCH-BRvwgt0p7-hold-long", "account_testing2.yaml", "testing2")]
TAG = {CAND[0][0]: "G05", CAND[1][0]: "G07", CAND[2][0]: "G37"}
B.SETUPS = [("L3-gap-slope-fromopen-FD", "default.yaml", "primary"),
            ("RW3-gapdn-rsi5pop-flowsell-short-FD", "default.yaml", "primary"),
            ("RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "default.yaml", "primary"),
            ("NM-ETF-late-dip-di-long", "default.yaml", "primary")] + CAND
B.GEOMS["hold"] = (np.nan, 1.0)
B.GEOMS["holdtr"] = (np.nan, 1.0)
Q = 0.05
_orig_signals = B.signals


def signals(f, fx, inv, mods):
    o = _orig_signals(f, fx, inv, mods)
    rows = []
    if f is not None and len(f):
        tod = f["tod"].to_numpy(); adv = f["adv20"].fillna(0).to_numpy(float); atr = f["atr_d"].to_numpy(float)
        c = f["close"].to_numpy(float); sy = f["symbol"].astype(str).to_numpy(); dt = f["date"].astype(str).to_numpy()
        gap = f["gap"].to_numpy(float)
        for st in inv:
            if st["setup"] not in TAG:
                continue
            ok = (tod >= max(950, st["w_lo"])) & (tod <= min(1500, st["w_hi"])) & (adv >= st["min_adv"]) & (atr > 0) & (c >= 5)
            hit = np.flatnonzero(ok)
            if not len(hit):
                continue
            key = pd.Series(sy[hit] + "|" + dt[hit])
            pick = []
            for k, ix in key.groupby(key).indices.items():
                h = zlib.crc32((TAG[st["setup"]] + k).encode())
                if (h % 10000) / 10000.0 < Q:
                    pick.append(hit[ix[(h // 10000) % len(ix)]])
            if not pick:
                continue
            idx = np.asarray(sorted(pick)); s = st["side"]; e = c[idx]; R = 0.25 * atr[idx]
            rows.append(pd.DataFrame({"setup": "RND-" + TAG[st["setup"]], "symbol": sy[idx], "date": dt[idx],
                                      "tod": tod[idx].astype(int), "side": s, "entry": e, "stop": e - s * R,
                                      "tgt": np.nan, "risk": R, "gap": gap[idx]}))
    if rows:
        o = pd.concat([o] + rows, ignore_index=True) if len(o) else pd.concat(rows, ignore_index=True)
        o = o[(o.risk > 0) & np.isfinite(o.risk)].reset_index(drop=True)
    if len(o):
        tr = {n: 1 for n, _, _ in CAND if "holdtr" in n}
        tr.update({"RND-G05": 1, "RND-G07": 1})
        o["trail"] = o.setup.map(tr).fillna(0).astype(int)
    return o


def walk_trades(T, b):
    """bench10.walk_trades + trailing (column trail): after each minute, MFE from the high/low; once MFE >= 1R the stop
    moves to entry + side x (MFE - 1) x risk (never loosened)."""
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


B.signals = signals
B.walk_trades = walk_trades

if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True)
    st = sys.argv[2]
    if st == "sig1":
        import research.history2y.lib as lib
        lib.DATA = B.DATA
        ms = [m for m in lib.months() if m not in B.LOCKED_MONTHS and not (W / f"sig1_{m}.parquet").exists()]
        with Pool(3) as p:
            for r in p.imap_unordered(B.month_job, [(m, str(W)) for m in ms]):
                print(r, flush=True)
    elif st == "walk1":
        B.walk1(W)
    elif st == "t2":
        c = pd.read_parquet(W / "ctx_t2.parquet"); c["date"] = c.date.astype(str)
        B.WCTX["ctx"] = c.drop(columns=["n"])
        B.t2(W)
    elif st == "inv":
        for x in B.inventory(): print(x)
