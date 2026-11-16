"""Mechanic RERUN CWT14-orl-p10 (2026-11-16): 1-minute exit simulation of every WB4-eligible candidate bar (ALL qualifying
bars, so refire / lot caps can be simulated), many experimental exit / entry configs at once.
Same engine + LR8 costs as the first run (code/sim.py): fill = open of the 1-minute bar starting `lat` minutes after the
signal bar closes; levels from the signal-bar close (anchor 'sig', as LabStrategy) or from the fill (anchor 'fill');
same-minute stop+target -> stop first; flat 15:55; R = net P/L / |fill - stop|.
Locked block 2024-11-01..2025-02-28: candidates never contain it and 1-minute rows inside it are dropped on read.
Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, "/home/user/MCF")
from mcf.research.gates import tod_cost_mult
OUT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech2-cwt14/"
TEAMD = ["2026-11-05", "2026-11-06", "2026-11-09", "2026-11-10"]
# name: dict(lat, anchor, tk (None = no target), sk, rf, be (move stop to fill after +be R), mh (max hold min), trail (after, dist))
D0 = dict(lat=1, anchor="sig", tk=0.5, sk=1.0, rf=0.30, be=None, mh=None, trail=None)
CFG = {"A": {}, "FA": dict(anchor="fill"), "BE3": dict(be=0.3), "MH30": dict(mh=30), "MH60": dict(mh=60),
       "TR": dict(tk=None, trail=(0.4, 0.3)), "T07": dict(tk=0.7), "S12": dict(sk=1.2), "S12FA": dict(sk=1.2, anchor="fill"),
       "L4": dict(lat=4), "L4FA": dict(lat=4, anchor="fill"), "P25": dict(rf=0.25)}
if len(sys.argv) > 1 and sys.argv[1] == "s3":
    CFG = {"A": {}, "S15": dict(sk=1.5), "S20": dict(sk=2.0), "S15T06": dict(sk=1.5, tk=0.6), "S15T04": dict(sk=1.5, tk=0.4),
           "S20T06": dict(sk=2.0, tk=0.6), "S12T04": dict(sk=1.2, tk=0.4), "S15MH60": dict(sk=1.5, mh=60), "S12BE4": dict(sk=1.2, be=0.4),
           "SLOD": dict(struct=0.05), "SLODT06": dict(struct=0.05, tk=0.6)}
CFG = {k: {**D0, "struct": None, **v} for k, v in CFG.items()}
FEE_SEC, TAF, CAT = 20.60e-6, 0.000195, 0.00005

def cost_entry(px, tod): return (0.01 + px * 1e-4) * tod_cost_mult([tod])[0] + px * 1e-4 + CAT
def cost_exit(px, why):
    base = 0.01 + px * 1e-4
    if why == "target": c = 0.0
    elif why == "stop": c = base + max(0.02, 4e-4 * px)
    else: c = base + max(0.01, 1e-4 * px)
    return c + FEE_SEC * px + TAF + CAT
def add_min(tod, k):
    h, m = divmod(tod, 100); t = h * 60 + m + k; return (t // 60) * 100 + t % 60
def mdiff(a, b): return (a // 100 * 60 + a % 100) - (b // 100 * 60 + b % 100)

TEAM = None
def init():
    global TEAM
    t = pd.concat([pd.read_parquet(f"/home/user/MCF/data/team/1Min/{d}.parquet") for d in TEAMD])
    t["ts"] = pd.to_datetime(t.ts).dt.tz_convert("America/New_York")
    TEAM = t

def run_one(o, h, l, c, mins, px, atr, tod, k, lod=None):
    R0 = k["rf"] * atr
    ent_t = add_min(tod, k["lat"])
    i0 = np.searchsorted(mins, ent_t)
    if i0 >= len(mins) or mins[i0] > add_min(ent_t, 4): return None
    fill = o[i0]; ref = px if k["anchor"] == "sig" else fill
    stop = ref - k["sk"] * R0
    if k.get("struct") is not None: stop = min(lod - k["struct"] * atr, ref - 0.5 * R0)   # structural: under the session low (poke low)
    tgt = None if k["tk"] is None else ref + k["tk"] * R0
    drift = (fill - px) / R0
    risk = fill - stop
    if risk <= 0:
        return dict(r=-1.0, why="gapstop", xt=int(mins[i0]), drift=drift)
    ce = cost_entry(fill, tod); cur = stop; peak = fill; why = None; ex = None
    for i in range(i0, len(mins)):
        if mins[i] >= 1555 or (k["mh"] and mdiff(mins[i], mins[i0]) >= k["mh"]):
            ex, why = o[i], "time"; break
        if l[i] <= cur:
            ex = min(cur, o[i]) if i > i0 else cur; why = "stop" if cur < fill else "be"; break
        if tgt is not None and h[i] >= tgt:
            ex, why = tgt, "target"; break
        peak = max(peak, h[i])
        if k["be"] is not None and peak >= fill + k["be"] * R0: cur = max(cur, fill)
        if k["trail"] is not None and peak >= fill + k["trail"][0] * R0: cur = max(cur, peak - k["trail"][1] * R0)
    else:
        ex, why = c[-1], "time"; i = len(mins) - 1
    pnl = ex - fill - cost_exit(ex, "stop" if why == "be" else why) - ce
    return dict(r=pnl / risk, why=why, xt=int(mins[i]), drift=drift)

def per_symbol(arg):
    sym, sigs = arg
    dates = sorted(sigs.date.unique())
    hd = [d for d in dates if d <= "2026-11-04"]
    frames = []
    if hd:
        try:
            df = pd.read_parquet(f"/home/user/MCF/data/cache_hist/1Min/{sym}.parquet")
            ds_ = df.index.strftime("%Y-%m-%d")
            df = df[~((ds_ >= "2024-11-01") & (ds_ <= "2025-02-28")) & np.isin(ds_, hd)]
            frames.append(df[["open", "high", "low", "close"]])
        except Exception:
            pass
    td = [d for d in dates if d in TEAMD]
    if td:
        t = TEAM[TEAM.symbol == sym].set_index("ts")[["open", "high", "low", "close"]]
        frames.append(t[np.isin(t.index.strftime("%Y-%m-%d"), td)])
    if not frames: return []
    df = pd.concat(frames)
    hm = df.index.hour * 100 + df.index.minute
    df = df[(hm >= 930) & (hm < 1600)]
    out = []
    byd = {d: g for d, g in df.groupby(df.index.strftime("%Y-%m-%d"))}
    for s in sigs.itertuples():
        g = byd.get(s.date)
        if g is None: continue
        mins = (g.index.hour * 100 + g.index.minute).to_numpy()
        o, h, l, c = (g[x].to_numpy(float) for x in ("open", "high", "low", "close"))
        rec = {"key": s.key}
        for name, k in CFG.items():
            r = run_one(o, h, l, c, mins, s.close, s.atr_d, s.tod, k, s.lod)
            if r is None:
                if name in ("A",): rec = None; break
                continue
            rec[f"{name}_r"] = r["r"]; rec[f"{name}_why"] = r["why"]; rec[f"{name}_xt"] = r["xt"]
            if name in ("A", "L4"): rec[f"{name}_drift"] = r["drift"]
        if rec: out.append(rec)
    return out

if __name__ == "__main__":
    sys.path.insert(0, OUT + "code")
    from ana import load
    s = load()
    s = s[s.m10 & (s.adv20 >= 95e6) & (s.atr_d / s.close >= 0.02) & (s.tod >= 950) & (s.tod <= (1200 if len(sys.argv) > 1 else 1300))]
    assert not ((s.date >= "2024-11-01") & (s.date <= "2025-02-28")).any()
    s = s[["key", "symbol", "date", "tod", "close", "atr_d", "lod"]]
    print(len(s), flush=True)
    jobs = [(k, g) for k, g in s.groupby("symbol")]
    with Pool(4, init) as p:
        res = p.map(per_symbol, jobs, chunksize=4)
    R = pd.DataFrame([r for x in res for r in x])
    R.to_parquet(OUT + ("sim3.parquet" if len(sys.argv) > 1 else "sim2.parquet")); print(R.shape)
