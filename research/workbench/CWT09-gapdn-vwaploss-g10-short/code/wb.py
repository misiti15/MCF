"""Mechanic CWT09-gapdn-vwaploss-g10-short: candidate selection, 1-minute exit simulation and scoring (both tests,
identical for parent and every copy). Educational only - not financial advice.
Fill: open of the 1-minute bar starting 1 minute after the signal bar closes (live fills ~0.5-1.5 min after the close).
Stop (parent): the 09:30-10:30 high (module a7_stop); no target; flat at the 15:55 open. R = net P/L / |fill - stop|
(the live R). Same-minute stop + target -> stop first. A fill at/above the stop is no trade (both parent and copies).
Costs (LR8 live model on the research model, short side): entry sale (1c + 1 bp) x time-of-day mult + 1 bp cushion +
SEC 20.60/M + TAF + CAT; buy-to-cover: target limit 0, stop (1c + 1 bp) + max(2c, 4 bps), market/time (1c + 1 bp) +
max(1c, 1 bp), + CAT. Selection: gap <= -g, adv20 >= min_adv, price >= $5, ETB (replay: that day's universe snapshot,
in universe, earnings blackout list as live; 2y: symbol ETB rate >= 0.9 over the snapshots, no earnings data),
first qualifying bar per symbol-day inside the window."""
import bisect, importlib.util, json, math, pickle, sys
import numpy as np, pandas as pd
from common import OUT, REPLAY, TWO_Y, TRAIN_END, CODE_ROOT
sys.path.insert(0, CODE_ROOT)
from mcf.research.gates import tod_cost_mult
FEE_SEC, TAF, CAT = 20.60e-6, 0.000195, 0.00005
ETF_RX = r"\bETF\b|ETN|ProShares|Direxion|\bTrust\b|Leverage|2X|3X|-1X|Bull|Bear|Ultra|iShares|SPDR|Invesco|Fund|Shares"

def tmin(t): return (t // 100) * 60 + t % 100
def cost_entry(px, tod): return (0.01 + px * 1e-4) * tod_cost_mult([tod])[0] + px * 1e-4 + FEE_SEC * px + TAF + CAT
def cost_exit(px, why):
    base = 0.01 + px * 1e-4
    if why == "target": c = 0.0
    elif why == "stop": c = base + max(0.02, 4e-4 * px)
    else: c = base + max(0.01, 1e-4 * px)
    return c + CAT

BASE = dict(gap=10.0, min_adv=1e6, window=(1030, 1500), extra=None, stop="fh", cap=None, tgt=None, be=None,
            trail=None, tx=1555, lock=None)

def run_one(p, s, cfg):
    mn, o, h, l, c = p
    ent = tmin(int(s.tod)) + 1
    i0 = np.searchsorted(mn, ent)
    if i0 >= len(mn) or mn[i0] > ent + 4: return None
    fill = o[i0]
    stop = s.fh
    if cfg["stop"] == "sig": stop = max(s.high, s.vwap) + 0.05 * s.atr_d      # experimental: signal-bar / VWAP stop
    if cfg["cap"] is not None: stop = min(stop, fill + cfg["cap"] * s.atr_d)
    risk = stop - fill
    if not risk > 0: return None
    tgt = fill - cfg["tgt"] * risk if cfg["tgt"] else None
    txm = tmin(cfg["tx"])
    cur = stop; low = fill; mfe = mae = 0.0; why = xt = px = None
    for i in range(i0, len(mn)):
        if mn[i] >= txm:
            px, why, xt = o[i], "time", mn[i]; break
        if h[i] >= cur:
            px = max(cur, o[i]) if i > i0 else cur
            why = "stop" if cur >= stop - 1e-9 else ("be" if abs(cur - fill) < 1e-9 else "trail"); xt = mn[i]; break
        if tgt is not None and l[i] <= tgt:
            px, why, xt = tgt, "target", mn[i]; break
        low = min(low, l[i]); mfe = max(mfe, (fill - l[i]) / risk); mae = min(mae, (fill - h[i]) / risk)
        if cfg["be"] is not None and mfe >= cfg["be"]: cur = min(cur, fill)
        if cfg["lock"] is not None and mfe >= cfg["lock"][0]: cur = min(cur, fill - cfg["lock"][1] * risk)
        if cfg["trail"] is not None and mfe >= cfg["trail"][0]: cur = min(cur, low + cfg["trail"][1] * risk)
    else:
        px, why, xt = c[-1], "time", mn[-1]
    pnl = (fill - px) - cost_entry(fill, int(s.tod)) - cost_exit(px, why)
    return dict(r=pnl / risk, gross=(fill - px) / risk, why=why, et=int(mn[i0]), xt=int(xt), hold=int(xt - mn[i0]),
                mfe=mfe, mae=mae, risk_pct=risk / fill, risk_atr=risk / s.atr_d, fill=fill, stop_px=stop, exit_px=px)

# ------------------------------------------------------------------ data
def _spy(P):
    rows = []
    for (sym, d), (mn, o, h, l, c) in P.items():
        if sym != "SPY": continue
        k = np.searchsorted(mn, tmin(950) - 1)
        if k >= len(mn) or mn[k] != tmin(950) - 1: continue
        base = c[k]
        for t in range(1030, 1505, 5):
            if t % 100 >= 60: continue
            j = np.searchsorted(mn, tmin(t) - 1)
            if j < len(mn) and mn[j] == tmin(t) - 1: rows.append((d, t, (c[j] / base - 1) * 100))
    sp = pd.DataFrame(rows, columns=["date", "tod", "spy50"])
    day = {d: (c[-1] / o[0] - 1) * 100 for (sym, d), (mn, o, h, l, c) in P.items() if sym == "SPY" and len(mn) > 300}
    return sp, day

def load(test):
    P = pickle.load(open(OUT + f"paths_{test}.pkl", "rb"))
    s = pd.read_parquet(OUT + f"sig_{test}.parquet"); s["tod"] = s.tod.astype(int)
    U = pd.read_parquet(OUT + "univ_snaps.parquet")
    names = U.drop_duplicates("symbol", keep="last").set_index("symbol").name.astype(str)
    s["etf"] = s.symbol.map(names).fillna("").str.contains(ETF_RX, regex=True)
    if test == "replay":
        ER = json.load(open(OUT + "earn_replay.json"))
        days = sorted(U.day.unique()); snap = lambda d: days[max(bisect.bisect_right(days, d) - 1, 0)]
        Ud = U.drop_duplicates(["day", "symbol"], keep="last").set_index(["day", "symbol"]).etb.to_dict()
        k = list(zip(s.date.map(snap), s.symbol))
        s["ok"] = [Ud.get(x) is True or Ud.get(x) == 1 for x in k]
        s["ok"] &= ~np.array([sy in set(ER.get(d, [])) for sy, d in zip(s.symbol, s.date)])
        s = s[(s.date >= REPLAY[0]) & (s.date <= REPLAY[1])]
    else:
        U["ok"] = U.etb.astype(float)
        rate = U.groupby(["day", "symbol"]).ok.mean().groupby("symbol").mean()
        s["ok"] = s.symbol.map(rate).fillna(0) >= 0.9
        s = s[(s.date >= TWO_Y[0]) & (s.date <= TWO_Y[1])]
    s = s[s.ok & (s.close >= 5)].copy()
    sp, day = _spy(P)
    s = s.merge(sp, on=["date", "tod"], how="left")
    s["spyday"] = s.date.map(day)
    s["dtype"] = np.where(s.spyday > 0.3, "up", np.where(s.spyday < -0.3, "down", "flat"))
    return s.sort_values(["symbol", "date", "tod"]).reset_index(drop=True), P

def pick(s, cfg):
    m = (s.gap <= -cfg["gap"]) & (s.adv20 >= cfg["min_adv"]) & (s.tod >= cfg["window"][0]) & (s.tod <= cfg["window"][1])
    if cfg["extra"] is not None: m &= cfg["extra"](s)
    return s[m].drop_duplicates(["symbol", "date"])

def trades(s, P, cfg):
    t = pick(s, cfg); out = []
    for row in t.itertuples():
        p = P.get((row.symbol, row.date))
        if p is None: continue
        r = run_one(p, row, cfg)
        if r is None: continue
        out.append({**row._asdict(), **r})
    return pd.DataFrame(out)

# ------------------------------------------------------------------ scoring (as the CWT14 Workbench, research/workbench/CWT14-failbrk-orl-p10-long/code/ana.py)
def stats(t, col="r"):
    if not len(t): return dict(n=0)
    r = t[col]; day = t.groupby("date")[col].sum()
    best = day.idxmax(); nb = (t.date != best).sum()
    return dict(n=len(t), days=t.date.nunique(), win=float((r > 0).mean()), avg=float(r.mean()),
                wo_best=float((r.sum() - day[best]) / nb) if nb else float("nan"),
                total=float(r.sum()), worst_day=float(day.min()), best_day=float(day.max()),
                best_share=float(day[best] / r.sum()) if r.sum() > 0 else float("nan"),
                avg_win=float(r[r > 0].mean()) if (r > 0).any() else float("nan"),
                avg_loss=float(r[r <= 0].mean()) if (r <= 0).any() else float("nan"),
                hold=float(t.hold.median()))

def paired(tv, tp, col="r"):
    a = tv.groupby("date")[col].mean(); b = tp.groupby("date")[col].mean()
    d = (a - b).dropna()
    if len(d) < 3 or d.std() == 0: return dict(pdays=len(d), pdiff=float(d.mean()) if len(d) else float("nan"), pt=float("nan"))
    return dict(pdays=len(d), pdiff=float(d.mean()), pt=float(d.mean() / d.std(ddof=1) * math.sqrt(len(d))))

def bar(n): return max(1.5, math.sqrt(2 * math.log(n)))
def split(d): return "train" if d <= TRAIN_END else "valid"
