"""W5 Part D: WB2 demonstration - 3 exit classes x 5 gap-down short setups, paired counterfactual on live trades.
Educational only - not financial advice."""
import math, pickle, numpy as np, pandas as pd
S = "<scratch>"
x = pd.read_pickle(f"{S}/demo_trades.pkl"); P = pickle.load(open(f"{S}/paths.pkl", "rb"))
SHORT = {"RW7-gapdn-bounce-early-short-FD": "RW7", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": "RW5",
         "RW3-gapdn-rsi5pop-flowsell-short-FD": "RW3", "RW1-gapdn-bounce-flowsell-short-FD": "RW1", "L3-gap-slope-rsi5hi-FD": "L3-rsi5hi"}
x["s"] = x.strategy.map(SHORT)
x["et"] = pd.to_datetime(x.entry_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
x["xt"] = pd.to_datetime(x.exit_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
NCFG = 15; BAR = max(1.5, math.sqrt(2 * math.log(NCFG)))
def thr(px): return max(0.01, 3e-4 * px)
def flatc(px): return max(0.01, 1e-4 * px) + 0.01
def raw(r):
    Pp = P.get((r.date, r.symbol))
    if Pp is None: return None
    em = (r.et.hour * 60 + r.et.minute) - 570
    k = max(np.searchsorted(Pp["m"], int(em)) - 1, 0); q = r.entry / Pp["c"][k]
    if abs(math.log(q)) <= 0.03: return Pp
    return dict(Pp, o=Pp["o"] * q, h=Pp["h"] * q, l=Pp["l"] * q, c=Pp["c"] * q)
def walk(r):
    """Returns (R_X1, R_X2, R_X3, has_bars). Earlier-exit-only variants on the live trade."""
    Pp = raw(r)
    if Pp is None or not (r.risk > 0): return r.R, r.R, r.R, False
    side = int(np.sign(r.side)); rps = abs(r.entry - r.stop)
    em = (r.et.hour * 60 + r.et.minute) - 570 + r.et.second / 60
    xm = (r.xt.hour * 60 + r.xt.minute) - 570 + r.xt.second / 60 if r.xt.strftime("%Y-%m-%d") == r.date else 385.0
    xm = min(xm, 385.0)
    tR = abs(r.target - r.entry) / rps if r.target == r.target and r.target else None
    T = r.entry + side * 0.75 * tR * rps if tR else None
    out = [None, None, None]; mfe = 0.0; be_on = False
    for m, o, h, l, c in zip(Pp["m"], Pp["o"], Pp["h"], Pp["l"], Pp["c"]):
        if m < math.ceil(em) or m + 1 > xm: continue
        fav = (h - r.entry) / rps if side > 0 else (r.entry - l) / rps
        # X2 break-even: stop at entry active from the bar after MFE >= 0.5R (stop-first)
        if out[1] is None and be_on and ((side > 0 and l <= r.entry) or (side < 0 and h >= r.entry)):
            px = min(o, r.entry) if side > 0 else max(o, r.entry)
            out[1] = (r.pnl_adj + (side * (px - r.exit) - flatc(px)) * r.shares) / r.risk
        # X1 earlier target
        if out[0] is None and T is not None and ((side > 0 and h >= T + thr(T)) or (side < 0 and l <= T - thr(T))):
            out[0] = (r.pnl_adj + side * (T - r.exit) * r.shares) / r.risk
        mfe = max(mfe, fav)
        if mfe >= 0.5: be_on = True
        # X3 60-min stop if MFE < 0.25R
        if out[2] is None and m + 1 >= em + 60 and m + 1 < em + 61 + 1e-9:
            if mfe < 0.25: out[2] = (r.pnl_adj + (side * (c - r.exit) - flatc(c)) * r.shares) / r.risk
            else: out[2] = r.R
        if all(v is not None for v in out): break
    return tuple(r.R if v is None else v for v in out) + (True,)
res = [walk(r) for r in x.itertuples()]
x["X1"], x["X2"], x["X3"], x["bars"] = zip(*res)
for k in ["X1", "X2", "X3"]: x["d" + k] = x[k] - x.R
x.to_pickle(f"{S}/demo_scored.pkl")
print("trades", len(x), "with bars", int(x.bars.sum()), " with target (X1 applicable)", int((x.target.notna() & (x.target != 0)).sum()))
