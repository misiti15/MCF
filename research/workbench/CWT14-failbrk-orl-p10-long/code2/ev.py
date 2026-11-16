"""Mechanic RERUN CWT14-orl-p10: evaluate WB4 + experimental layers vs the parent on identical tests.
Educational only - not financial advice."""
import sys
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech2-cwt14/code")
from ana import *
O2 = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech2-cwt14/"
TESTS = {"replay": REPLAY, "2y": TWO_Y, "train": (TWO_Y[0], TRAIN_END), "valid": ("2026-01-01", TWO_Y[1])}

def cost_ps(px): return 2 * (0.01 + px * 1e-4) + 0.02          # runner CF: round-trip + stop slippage per share

def build():
    s = load()
    S2 = pd.read_parquet(O2 + "sim2.parquet"); X = pd.read_parquet(O2 + "ctx.parquet")
    c = s.merge(S2, on="key").merge(X, on=["date", "tod"], how="left")
    c["R0"] = 0.30 * c.atr_d
    c["ccr"] = cost_ps(c.close) / c.R0                              # cost-to-R at the signal close (module-implementable)
    fill = c.close + c.A_drift * c.R0
    c["ccr_fill"] = cost_ps(fill) / (fill - (c.close - c.R0)).clip(lower=1e-9)   # CF as the runner sees it (px ~ fill)
    c["min"] = c.tod // 100 * 60 + c.tod % 100
    return s, c

def mins(t): return t // 100 * 60 + t % 100

def trades(c, window=(950, 1200), gate=None, exitc="A", refire=1, cool=10, guard=None, latch=None, maxday=None):
    m = (c.tod >= window[0]) & (c.tod <= window[1]) & c[exitc + "_r"].notna()
    if gate is not None: m &= gate(c)
    x = c[m].sort_values(["symbol", "date", "tod"])
    first = x.drop_duplicates(["symbol", "date"])
    if refire >= 2:
        x2 = x.merge(first[["symbol", "date", "tod", exitc + "_xt"]].rename(columns={"tod": "t1", exitc + "_xt": "x1"}), on=["symbol", "date"])
        x2 = x2[(mins(x2.tod) >= mins(x2.t1) + cool) if cool >= 0 else (x2.tod >= x2.x1)]
        x2 = x2.drop_duplicates(["symbol", "date"]).drop(columns=["t1", "x1"])
        t = pd.concat([first, x2])
    else:
        t = first
    if guard is not None: t = t[guard(t)]
    t = t.assign(R=t[exitc + "_r"], xt=t[exitc + "_xt"]).sort_values(["date", "tod"])
    if maxday: t = t.groupby("date").head(maxday)
    if latch is not None:
        keep = []
        for d, g in t.groupby("date", sort=False):
            done = []
            for r in g.itertuples():
                real = sum(rr for xt, rr in done if mins(xt) <= r.min + 1)
                if real <= -latch: continue
                keep.append(r.Index); done.append((r.xt, r.R))
        t = t.loc[keep]
    return t

def score(t, P, col="R"):
    out = {}
    for tn, rng in TESTS.items():
        a = period(t, rng); b = period(P, rng)
        st = stats(a, col); pr = paired(a, b, col, "base_r")
        out[tn] = dict(**st, avg_win=a.loc[a[col] > 0, col].mean(), avg_loss=a.loc[a[col] <= 0, col].mean(), pdiff=pr["diff"], pt=pr["t"])
    return out
