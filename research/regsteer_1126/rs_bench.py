"""REGSTEER-1126: bench10 lots (engine unchanged, research/ultimate_1119/top10/bench10.py) for Primary's 4 setups and the
4 top live contenders (>= 30 live trades, highest live total R outside Primary, fixed in PREREG.md before scoring), each
with its live config block from its home account. Stages: inv | sig1 | walk1 | t2.
Usage (repo root): python research/regsteer_1126/rs_bench.py WORK STAGE [POOL]. Locked block 2024-11-01..2025-02-28 is
never read (bench10 guards: lib refuses it, pyarrow filters + asserts). Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/ultimate_1119/top10"))
import bench10 as B  # noqa: E402

PRIMARY4 = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
            "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "NM-ETF-late-dip-di-long"]
CONTENDERS = [  # (setup, home config) - top 4 by live total R with >= 30 live trades, outside Primary (live 10-06..11-25)
    ("GEN-261022-05-MACDhge0p079-UpWickge0p71-ORHdistlem0p38-PM-BRoplt0p35-holdtr-short", "account_explore1.yaml"),
    ("GEN-261026-07-Flow3ge0p56-BBpctge0p98-ADX7le34-PM-BRvwlt0p3-holdtr-short", "account_testing2.yaml"),
    ("GEN-261020-09-EMAdChgge0p093-Z12lem0p82-VWAPcrossesle0-MID-QQQltm0p3-holdtr-long", "account_gen.yaml"),
    ("GEN-261023-07-RSIslopege9p1-BarRngATRge0p087-VWAPcrossesge8-LUNCH-BRvwgt0p7-hold-long", "account_testing2.yaml"),
]
B.SETUPS = [(s, "default.yaml", "primary") for s in PRIMARY4] + [(s, f, "testing") for s, f in CONTENDERS]
# The GEN contenders use the live "hold" (stop 1R, no target, flat 15:55) and "holdtr" (+ 1R trail behind the best price
# once +1R; mcf/strategies/setups.py TRAIL, runner.py managed stops) geometries, which bench10 does not list. Added here
# without touching bench10: R = 0.25 x daily ATR as every bench10 geom; the trail is walked on 1-minute bars (stop checked
# first in a bar with the stop as of the previous bar close, then best/stop updated from the bar's extreme) - conservative.
import numpy as np  # noqa: E402

B.GEOMS = dict(B.GEOMS, hold=(float("nan"), 1.0), holdtr=(float("nan"), 1.0))
TRAIL_SETUPS = {s for s, _ in CONTENDERS if "-holdtr-" in s}
_walk0 = B.walk_trades


def walk_trades(T, b):
    tr = T[T.setup.isin(TRAIL_SETUPS)]
    res = _walk0(T[~T.setup.isin(TRAIL_SETUPS)], b) if len(tr) < len(T) else []
    if not len(tr):
        return res
    hhmm = b.index.hour * 100 + b.index.minute
    day = b.index.date.astype(str)
    O, H, Lo, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    byday = {dd: np.flatnonzero(day == dd) for dd in np.unique(day)}
    for r in tr.itertuples():
        ix = byday.get(r.date)
        if ix is None:
            res.append((r.Index, np.nan, -1, -1)); continue
        hm = hhmm[ix]
        sel, after = ix[(hm >= r.tod) & (hm < 1555)], ix[hm >= 1555]
        s, e, stop, risk = r.side, r.entry, r.stop, r.risk
        best, px = 0.0, None
        for k in sel:
            if (s == 1 and Lo[k] <= stop) or (s == -1 and H[k] >= stop):
                px, kd, xt = (min(O[k], stop) if s == 1 else max(O[k], stop)), 1, hhmm[k]
                break
            best = max(best, s * ((H[k] if s == 1 else Lo[k]) - e) / risk)
            if best >= 1.0:
                t_ = e + s * (best - 1.0) * risk
                stop = max(stop, t_) if s == 1 else min(stop, t_)
        if px is None:
            if len(after):
                px, kd, xt = O[after[0]], 0, 1555
            elif len(sel):
                px, kd, xt = C[sel[-1]], 0, hhmm[sel[-1]] + 1
            else:
                res.append((r.Index, np.nan, -1, -1)); continue
        res.append((r.Index, px, kd, xt))
    return res


B.walk_trades = walk_trades

if __name__ == "__main__":
    W, stage = Path(sys.argv[1]), sys.argv[2]
    npool = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    W.mkdir(parents=True, exist_ok=True)
    if stage == "inv":
        for x in B.inventory():
            print(x)
    elif stage == "sig1":
        import research.history2y.lib as lib
        lib.DATA = B.DATA
        ms = [m for m in lib.months() if m not in B.LOCKED_MONTHS and not (W / f"sig1_{m}.parquet").exists()]
        with Pool(npool) as p:
            for r in p.imap_unordered(B.month_job, [(m, str(W)) for m in ms]):
                print(r, flush=True)
    elif stage == "walk1":
        B.walk1(W)
    elif stage == "t2":
        B.t2(W)
