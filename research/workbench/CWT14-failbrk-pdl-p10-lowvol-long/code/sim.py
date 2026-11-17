"""Mechanic CWT14-pdl-p10-lowvol: 1-minute exit simulation of every candidate bar, many exit configs at once.
Engine and LR8 costs exactly as the sibling job (research/workbench/CWT14-failbrk-orl-p10-long/code2/sim2.py):
fill = open of the 1-minute bar `lat` min after the signal bar closes; stop / target from the signal-bar close ('sig',
as LabStrategy) or the fill; same-minute stop+target -> stop first; flat 15:55; R = net P/L / |fill - stop|.
Levels in daily-ATR units (parent t05s1 at 1R = 0.25 ATR: stop 0.25, target 0.125).
Locked block 2024-11-01..2025-02-28: never in the candidates; 1-minute rows inside it dropped on read.
Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, "/home/user/MCF")
from mcf.research.gates import tod_cost_mult
OUT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-cwt14pdl/"
TEAMD = ["2026-11-05", "2026-11-06", "2026-11-09", "2026-11-10"]
D0 = dict(lat=1, anchor="sig", s=0.25, t=0.125, mh=None, flat=1555, be=None)
CFG = {"A": {}, "T10": dict(t=0.10), "T175": dict(t=0.175), "T25": dict(t=0.25), "S20": dict(s=0.20), "S30T15": dict(s=0.30, t=0.15),
       "S375": dict(s=0.375), "S45": dict(s=0.45), "S45T15": dict(s=0.45, t=0.15), "S60": dict(s=0.60), "S60T15": dict(s=0.60, t=0.15),
       "S45T10": dict(s=0.45, t=0.10), "MH60": dict(mh=60), "MH120": dict(mh=120), "S45MH120": dict(s=0.45, mh=120),
       "F1330": dict(flat=1330), "S45F1330": dict(s=0.45, flat=1330), "FA": dict(anchor="fill"), "L4": dict(lat=4),
       "S45BE": dict(s=0.45, be=0.10)}
CFG = {k: {**D0, **v} for k, v in CFG.items()}
FEE_SEC, TAF, CAT = 20.60e-6, 0.000195, 0.00005

def cost_entry(px, tod): return (0.01 + px * 1e-4) * tod_cost_mult([tod])[0] + px * 1e-4 + CAT
def cost_exit(px, why):
    base = 0.01 + px * 1e-4
    c = 0.0 if why == "target" else (base + max(0.02, 4e-4 * px) if why == "stop" else base + max(0.01, 1e-4 * px))
    return c + FEE_SEC * px + TAF + CAT
def add_min(tod, k):
    h, m = divmod(tod, 100); t = h * 60 + m + k; return (t // 60) * 100 + t % 60
def mdiff(a, b): return (a // 100 * 60 + a % 100) - (b // 100 * 60 + b % 100)

TEAM = None
def init():
    global TEAM
    t = pd.concat([pd.read_parquet(f"/home/user/MCF/data/team/1Min/{d}.parquet") for d in TEAMD])
    t["ts"] = pd.to_datetime(t.ts).dt.tz_convert("America/New_York"); TEAM = t

def run_one(o, h, l, c, mins, px, atr, tod, k):
    ent_t = add_min(tod, k["lat"]); i0 = np.searchsorted(mins, ent_t)
    if i0 >= len(mins) or mins[i0] > add_min(ent_t, 4): return None
    fill = o[i0]; ref = px if k["anchor"] == "sig" else fill
    stop = ref - k["s"] * atr; tgt = None if k["t"] is None else ref + k["t"] * atr
    risk = fill - stop
    if risk <= 0: return dict(r=-1.0, why="gapstop", xt=int(mins[i0]), risk=0.0, fill=fill)
    ce = cost_entry(fill, tod); cur = stop; peak = fill; why = None
    for i in range(i0, len(mins)):
        if mins[i] >= k["flat"] or (k["mh"] and mdiff(mins[i], mins[i0]) >= k["mh"]):
            ex, why = o[i], "time"; break
        if l[i] <= cur:
            ex = min(cur, o[i]) if i > i0 else cur; why = "stop" if cur < fill else "be"; break
        if tgt is not None and h[i] >= tgt: ex, why = tgt, "target"; break
        peak = max(peak, h[i])
        if k["be"] is not None and peak >= fill + k["be"] * atr: cur = max(cur, fill)
    else:
        ex, why = c[-1], "time"; i = len(mins) - 1
    pnl = ex - fill - cost_exit(ex, "stop" if why == "be" else why) - ce
    return dict(r=pnl / risk, why=why, xt=int(mins[i]), risk=risk, fill=fill)

def per_symbol(arg):
    sym, sigs = arg
    dates = sorted(sigs.date.unique()); hd = [d for d in dates if d <= "2026-11-04"]; frames = []
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
    df = pd.concat(frames); hm = df.index.hour * 100 + df.index.minute; df = df[(hm >= 930) & (hm < 1600)]
    out = []; byd = {d: g for d, g in df.groupby(df.index.strftime("%Y-%m-%d"))}
    for s in sigs.itertuples():
        g = byd.get(s.date)
        if g is None: continue
        mins = (g.index.hour * 100 + g.index.minute).to_numpy()
        o, h, l, c = (g[x].to_numpy(float) for x in ("open", "high", "low", "close"))
        rec = {"key": s.key}
        for name, k in CFG.items():
            r = run_one(o, h, l, c, mins, s.close, s.atr_d, s.tod, k)
            if r is None:
                if name == "A": rec = None; break
                continue
            rec[f"{name}_r"] = r["r"]; rec[f"{name}_why"] = r["why"]
            if name in ("A", "S45T15", "S45", "S30T15", "S60T15"): rec[f"{name}_risk"] = r["risk"]
            if name == "A":
                rec["A_xt"] = r["xt"]; rec["fill"] = r["fill"]
                i0 = np.searchsorted(mins, add_min(s.tod, 1)); j = np.searchsorted(mins, 1555)
                rec["mfe_day"] = (h[i0:j].max() - r["fill"]) / s.atr_d if j > i0 else np.nan
                rec["mae_day"] = (r["fill"] - l[i0:j].min()) / s.atr_d if j > i0 else np.nan
        if rec: out.append(rec)
    return out

if __name__ == "__main__":
    s = pd.read_parquet(OUT + "sig.parquet")
    s = s[(s.m10v | s.m10a | s.m15v | s.m08v) & (s.adv20 >= 95e6) & (s.close >= 5) & (s.atr_d / s.close >= 0.01)].copy()
    s["key"] = s.symbol + "|" + s.date + "|" + s.tod.astype(str)
    assert not ((s.date >= "2024-11-01") & (s.date <= "2025-02-28")).any()
    print(len(s), flush=True)
    jobs = [(k, g[["key", "date", "tod", "close", "atr_d"]]) for k, g in s.groupby("symbol")]
    with Pool(4, init) as p:
        res = p.map(per_symbol, jobs, chunksize=4)
    R = pd.DataFrame([r for x in res for r in x]); R.to_parquet(OUT + "sim.parquet"); print(R.shape)
