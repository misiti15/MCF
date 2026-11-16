"""Mechanic CWT14-orl-p10: 1-minute exit simulation for every candidate signal, many exit configs at once.
Fill: open of the 1-minute bar starting 1 minute after the signal bar closes (live sends ~1.3 min after; fwdcal D=1).
Levels from the signal-bar close (as LabStrategy): stop = px - sk*rf*ATR, target = px + tk*rf*ATR. Same-minute
stop+target -> stop first. Flat at the 15:55 open. R = net P/L / |fill - stop| (the live R definition).
Costs (every config identical, LR8 live model on top of the research entry/spread model):
  entry  (1c + 1 bp) x time-of-day mult (gates.TOD_COST) + LR8 1 bp entry cushion
  target 0 (limit, filled at the limit; improvement given back)
  stop   (1c + 1 bp) + LR8 max(2c, 4 bps)
  market (time exit / scale-out) (1c + 1 bp) + LR8 max(1c, 1 bp)
  fees   SEC 20.60/M on sale, TAF 0.000195/sh, CAT 0.00005/sh/side
Locked block: signals never contain it (frames), and 1-minute rows inside 2024-11-01..2025-02-28 are dropped on read.
Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, "/home/user/MCF")
from mcf.research.gates import tod_cost_mult
OUT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-cwt14/"
TEAMD = ["2026-11-05", "2026-11-06", "2026-11-09", "2026-11-10"]
# name: (tk, sk, rf, scale_out_r or None, time_exit hhmm)
CFG = {"base": (0.5, 1.0, 0.25, None, 1555), "s08": (0.5, 0.8, 0.25, None, 1555), "s12": (0.5, 1.2, 0.25, None, 1555),
       "t04": (0.4, 1.0, 0.25, None, 1555), "t06": (0.6, 1.0, 0.25, None, 1555), "so35": (0.5, 1.0, 0.25, 0.35, 1555),
       "r30": (0.5, 1.0, 0.30, None, 1555), "tx13": (0.5, 1.0, 0.25, None, 1300)}
FEE_SEC, TAF, CAT = 20.60e-6, 0.000195, 0.00005

def cost_entry(px, tod): return (0.01 + px * 1e-4) * tod_cost_mult([tod])[0] + px * 1e-4 + CAT
def cost_exit(px, why):
    base = 0.01 + px * 1e-4
    if why == "target": c = 0.0
    elif why == "stop": c = base + max(0.02, 4e-4 * px)
    else: c = base + max(0.01, 1e-4 * px)
    return c + FEE_SEC * px + TAF + CAT

def hm(ts): return ts.hour * 100 + ts.minute
def add_min(tod, k):
    h, m = divmod(tod, 100); t = h * 60 + m + k; return (t // 60) * 100 + t % 60

TEAM = None
def init():
    global TEAM
    t = pd.concat([pd.read_parquet(f"/home/user/MCF/data/team/1Min/{d}.parquet") for d in TEAMD])
    t["ts"] = pd.to_datetime(t.ts).dt.tz_convert("America/New_York")
    TEAM = t

def run_one(o, h, l, c, mins, px, atr, tod, cfg):
    tk, sk, rf, so, tx = cfg
    R0 = rf * atr; stop = px - sk * R0; tgt = px + tk * R0
    ent_t = add_min(tod, 1)
    i0 = np.searchsorted(mins, ent_t)
    if i0 >= len(mins) or mins[i0] > add_min(ent_t, 4): return None
    fill = o[i0]; risk = fill - stop
    if risk <= 0:                                  # opened through the stop: out at the fill as a stop
        return dict(r=-1.0, why="gapstop", win=0, et=mins[i0], xt=mins[i0], mfe=0.0, mae=-1.0, risk=0.0)
    ce = cost_entry(fill, tod)
    legs = []; frac = 1.0; cur_stop = stop; scaled = False
    mfe = mae = 0.0; why = None; xt = None
    for i in range(i0, len(mins)):
        if mins[i] >= tx:
            legs.append((frac, o[i], "time")); why = why or "time"; xt = mins[i]; break
        lo, hi = l[i], h[i]
        mae = min(mae, (lo - fill) / risk); mfe = max(mfe, (hi - fill) / risk)
        if lo <= cur_stop:
            ex = min(cur_stop, o[i]) if i > i0 else cur_stop
            legs.append((frac, ex, "stop")); why = "be" if scaled else "stop"; xt = mins[i]; break
        if so is not None and not scaled and hi >= fill + so * risk:
            legs.append((0.5, fill + so * risk, "market")); frac = 0.5; scaled = True; cur_stop = fill
            if hi >= tgt:
                legs.append((frac, tgt, "target")); why = "target"; xt = mins[i]; break
            continue
        if hi >= tgt:
            legs.append((frac, tgt, "target")); why = "target"; xt = mins[i]; break
    else:
        legs.append((frac, c[-1], "time")); why = "time"; xt = mins[-1]
    pnl = sum(f * (ex - fill - cost_exit(ex, w)) for f, ex, w in legs) - ce
    return dict(r=pnl / risk, why=why, win=int(pnl > 0), et=int(mins[i0]), xt=int(xt), mfe=mfe, mae=mae, risk=risk / fill)

def per_symbol(arg):
    sym, sigs = arg
    dates = sorted(sigs.date.unique())
    hd = [d for d in dates if d <= "2026-11-04"]
    frames = []
    if hd:
        try:
            df = pd.read_parquet(f"/home/user/MCF/data/cache_hist/1Min/{sym}.parquet")
            ds_ = df.index.strftime("%Y-%m-%d")
            locked = (ds_ >= "2024-11-01") & (ds_ <= "2025-02-28")
            df = df[~locked & np.isin(ds_, hd)]
            frames.append(df)
        except Exception:
            pass
    td = [d for d in dates if d in TEAMD]
    if td:
        t = TEAM[TEAM.symbol == sym].set_index("ts")[["open", "high", "low", "close", "volume"]]
        frames.append(t[np.isin(t.index.strftime("%Y-%m-%d"), td)])
    if not frames: return []
    df = pd.concat(frames)
    if not len(df): return []
    df = df[(df.index.hour * 100 + df.index.minute >= 930) & (df.index.hour * 100 + df.index.minute < 1600)]
    out = []
    byd = {d: g for d, g in df.groupby(df.index.strftime("%Y-%m-%d"))}
    for s in sigs.itertuples():
        g = byd.get(s.date)
        if g is None: continue
        mins = (g.index.hour * 100 + g.index.minute).to_numpy()
        o, h, l, c = (g[k].to_numpy(float) for k in ("open", "high", "low", "close"))
        rec = {"key": s.key}
        for name, cfg in CFG.items():
            r = run_one(o, h, l, c, mins, s.close, s.atr_d, s.tod, cfg)
            if r is None: rec = None; break
            for k, v in r.items():
                if name == "base" or k in ("r", "why", "win"):
                    rec[f"{name}_{k}"] = v
        if rec: out.append(rec)
    return out

if __name__ == "__main__":
    s = pd.read_parquet(OUT + sys.argv[1])
    s["date"] = s.date.astype(str)
    assert not ((s.date >= "2024-11-01") & (s.date <= "2025-02-28")).any()
    s["key"] = s.symbol + "|" + s.date + "|" + s.tod.astype(str)
    s = s.drop_duplicates("key")
    jobs = [(k, g) for k, g in s.groupby("symbol")]
    with Pool(4, init) as p:
        res = p.map(per_symbol, jobs, chunksize=4)
    R = pd.DataFrame([r for x in res for r in x])
    R.to_parquet(OUT + sys.argv[2]); print(R.shape)
