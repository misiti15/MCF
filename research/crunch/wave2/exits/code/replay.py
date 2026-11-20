"""Wave 2 exits: calibrated 1-min replay of live trades, parent vs Y1/Y2/Y3; SPY-exit counterfactual (RW3 0.30 / RW5 0.40).
Educational only - not financial advice."""
import math, pickle, sys, numpy as np, pandas as pd
sys.path.insert(0, "<worktree>")
from mcf.costs import live_model, lot_costs, parts_from_row
from mcf.config import load_config
MOD = live_model({"costs": load_config().get("costs")})
S = "<scratch>"
t = pd.read_pickle(f"{S}/trades.pkl"); P = pickle.load(open(f"{S}/paths.pkl", "rb"))
FAM = {"RW3-gapdn-rsi5pop-flowsell-short-FD": "RW3", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": "RW5",
       "L3-gap-slope-rsi5hi-FD": "L3-rsi5hi", "RW7-gapdn-bounce-early-short-FD": "RW7", "RW1-gapdn-bounce-flowsell-short-FD": "RW1"}
x = t[t.strategy.isin(FAM)].copy(); x["s"] = x.strategy.map(FAM)
x = x[x.date <= "2026-11-17"].copy()
def lr8(r):
    tg = r.target if r.target == r.target else None
    return (r.pnl - lot_costs(int(np.sign(r.side)), r.entry, abs(r.shares), parts_from_row(r), tg, r.date, MOD)["total"]) / r.risk
x["R_booked"] = x.R; x["R"] = [lr8(r) for r in x.itertuples()]
x["et"] = pd.to_datetime(x.entry_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
x["xt"] = pd.to_datetime(x.exit_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
def thr(px): return max(0.01, 3e-4 * px)
def flatc(px): return max(0.01, 1e-4 * px) + 0.01
def path(r):
    Pp = P.get((r.date, r.symbol))
    if Pp is None: return None
    em = (r.et.hour * 60 + r.et.minute) - 570
    k = max(np.searchsorted(Pp["m"], int(em)) - 1, 0); q = r.entry / Pp["c"][k]
    if abs(math.log(q)) <= 0.03: return Pp
    return dict(Pp, o=Pp["o"] * q, h=Pp["h"] * q, l=Pp["l"] * q, c=Pp["c"] * q)
def sim(r, Pp, T, trail):
    """walk from entry to 15:55; returns (gross R before live cost, exit type)."""
    side = int(np.sign(r.side)); e = r.entry; rps = abs(e - r.stop); stp = r.stop
    em = (r.et.hour * 60 + r.et.minute) - 570 + r.et.second / 60
    best = e; armed = False; tgt = T
    for m, o, h, l, c in zip(Pp["m"], Pp["o"], Pp["h"], Pp["l"], Pp["c"]):
        if m < math.ceil(em): continue
        if m >= 385:
            return o, "flatten"
        st = stp
        if armed: st = max(stp, best - 0.5 * rps) if side > 0 else min(stp, best + 0.5 * rps)
        if (side > 0 and l <= st) or (side < 0 and h >= st):
            px = min(o, st) if side > 0 else max(o, st)
            return px, ("trail" if armed and st != stp else "stop")
        if tgt is not None and ((side > 0 and h >= tgt + thr(tgt)) or (side < 0 and l <= tgt - thr(tgt))):
            return tgt, "target"
        best = max(best, h) if side > 0 else min(best, l)
        if trail and not armed and side * (best - e) / rps >= 1.0:
            armed = True; tgt = None
    return Pp["c"][-1], "flatten"
rows = []
for r in x.itertuples():
    Pp = path(r)
    if Pp is None or not (r.risk > 0): rows.append(dict(bars=False)); continue
    side = int(np.sign(r.side)); slip = r.slip_bps if r.slip_bps == r.slip_bps else 0.0
    sig = r.entry / (1 + side * slip / 1e4)
    k = abs(r.target - sig) / abs(r.stop - sig)
    T1 = sig + side * 1.25 * abs(r.target - sig)
    T3 = r.entry + side * k * abs(r.entry - r.stop)
    out = dict(bars=True, k=k)
    for nm, T, tr in [("P", r.target, False), ("Y1", T1, False), ("Y2", r.target, True), ("Y3", T3, False)]:
        px, why = sim(r, Pp, T, tr)
        c = lot_costs(side, r.entry, abs(r.shares), [(abs(r.shares), px, "stop" if why == "trail" else why)], T, r.date, MOD)["total"]
        out[nm] = (side * (px - r.entry) * abs(r.shares) - c) / r.risk; out[nm + "_x"] = why
    rows.append(out)
R = pd.DataFrame(rows, index=x.index); x = x.join(R)
# SPY-since-entry exit counterfactual on the live trade (earlier exits only)
SPYP = {"RW3": 0.30, "RW5": 0.40}
def spyx(r):
    pct = SPYP.get(r.s); Pp = path(r) if pct else None; Sp = P.get((r.date, "SPY"))
    if pct is None or Pp is None or Sp is None or not (r.risk > 0): return r.R, False
    side = int(np.sign(r.side))
    em = (r.et.hour * 60 + r.et.minute) - 570 + r.et.second / 60
    xm = (r.xt.hour * 60 + r.xt.minute) - 570 + r.xt.second / 60 if r.xt.strftime("%Y-%m-%d") == r.date else 385.0
    sc = dict(zip(Sp["m"], Sp["c"])); spy0 = sc.get(int(math.floor(em)) - 1)
    if spy0 is None: return r.R, True
    for m, o in zip(Pp["m"], Pp["o"]):
        if m < math.ceil(em): continue
        if m >= xm or m >= 385: break
        sp = sc.get(m - 1)
        if sp is None: continue
        mv = (sp / spy0 - 1) * 100
        if (side < 0 and mv >= pct - 1e-9) or (side > 0 and mv <= -pct + 1e-9):
            tg = r.target if r.target == r.target else None
            return (r.pnl + side * (o - r.exit) * abs(r.shares) - lot_costs(side, r.entry, abs(r.shares), [(abs(r.shares), o, "spy_exit")], tg, r.date, MOD)["total"]) / r.risk, True
    return r.R, True
sx = [spyx(r) for r in x.itertuples()]
x["SPYX"], x["spy_bars"] = zip(*sx)
x.drop(columns=["et", "xt"]).to_pickle(f"{S}/scored.pkl")
b = x[x.bars == True]
print("trades", len(x), "with bars", len(b))
for s, g in b.groupby("s"):
    cal = ((g.P - g.R).abs() <= 0.10) & (g.P_x == g.exit_reason)
    print(s, len(g), "calib %.0f%%" % (100 * cal.mean()), "P-live %+.3f" % (g.P - g.R).mean(), "k med %.2f" % g.k.median(),
          " ".join(f"{c}:{(g[c]-g.P).mean():+.3f}" for c in ["Y1", "Y2", "Y3"]))
