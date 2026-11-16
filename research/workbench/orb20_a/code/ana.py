"""Mechanic orb20_a: every part, one change at a time (+ combos), parent and copies through the identical pipeline.
Writes exp_<name>.csv. Usage: python ana.py <stage>   (stage = single | combo | final). Educational only - not financial advice."""
import sys, json, math
import numpy as np, pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-orb20")
import sim as S

F, A, SPY = S.load()
# SPY state at 09:50 (bars 09:30-09:49 only): close vs its 09:30-09:49 range, and SPY 1-minute closes for later checks
sp = SPY.copy(); sp["m"] = sp.ts.dt.hour * 100 + sp.ts.dt.minute
r49 = sp[sp.m <= 949].groupby("date").agg(sh=("high", "max"), sl=("low", "min"), so=("open", "first"), sc=("close", "last"))
r49["spos"] = (r49.sc - r49.sl) / (r49.sh - r49.sl)          # 0 = at the 09:30-09:49 low, 1 = at the high
F = F.merge(r49[["spos", "so", "sc"]], left_on="date", right_index=True, how="left")
F["width_atr"] = (F.hi - F.lo) / F.atr
F["atr_pct"] = F.atr / F.pc
F["width_pct"] = (F.hi - F.lo) / F.c49
lvl = np.where(F.c49 > F.op, F.hi + 0.01, F.lo - 0.01)
F["cost_r"] = (2 * (np.where(F.ext, 0.03, 0.01) + lvl * 1e-4) + np.maximum(0.02, 4e-4 * lvl)) / (0.5 * (F.hi - F.lo))
F["dirsign"] = np.sign(F.c49 - F.op)
DAYS = {"replay": sorted(F[F.date.between(*S.REPLAY)].date.unique()), "2y": sorted(F[F.date.between(*S.TWO_Y)].date.unique())}


def ev(name, v, P=None):
    T = S.run(F, A, v)
    row = dict(name=name, cfg=json.dumps({k: (str(x) if callable(x) else x) for k, x in (v or {}).items() if k != "extra"}))
    for test, rng in (("replay", S.REPLAY), ("2y", S.TWO_Y), ("train", ("2024-10-01", S.TRAIN_END)), ("valid", ("2026-01-01", S.TWO_Y[1]))):
        t = S.period(T, rng)
        st = S.stats(t)
        for k, x in st.items():
            row[f"{test}_{k}"] = x
        if P is not None and test in DAYS:
            d, tt = S.paired(t, S.period(P, rng), DAYS[test])
            row[f"{test}_pd"], row[f"{test}_t"] = d, tt
    return row, T


def X(f):
    return f

# SPY close at each minute (for entry-time gates): spyc[(date, hhmm)] = close of the bar that STARTED at hhmm-1 (known at hhmm)
_sp = sp.set_index(["date", "m"]).close
def spy_since950(T):
    """SPY % change from its 09:49 close to the close of the bar before the entry bar (known when the stop triggers)."""
    prev = [(d, (m // 100 * 60 + m % 100 - 1) // 60 * 100 + (m // 100 * 60 + m % 100 - 1) % 60) for d, m in zip(T.date, T.et)]
    c = _sp.reindex(pd.MultiIndex.from_tuples(prev)).to_numpy()
    return c / T.sc.to_numpy() - 1


def ev2(name, v, post=None, P=None):
    T = S.run(F, A, v)
    if post is not None:
        T = T[post(T)].reset_index(drop=True)
    row = dict(name=name)
    for test, rng in (("replay", S.REPLAY), ("2y", S.TWO_Y), ("train", ("2024-10-01", S.TRAIN_END)), ("valid", ("2026-01-01", S.TWO_Y[1]))):
        t = S.period(T, rng)
        for k, x in S.stats(t).items():
            row[f"{test}_{k}"] = x
        if P is not None and test in DAYS:
            row[f"{test}_pd"], row[f"{test}_t"] = S.paired(t, S.period(P, rng), DAYS[test])
    return row, T


SINGLE = {
    "parent": ({}, None),
    # P1 / P2 intake
    "P1 core tier only (ADV >= 5M, no extended)": ({"extra": lambda G, s: ~G.ext}, None),
    "P1 ADV >= 20M": ({"extra": lambda G, s: G.adv >= 20e6}, None),
    "P1 ADV >= 50M": ({"extra": lambda G, s: G.adv >= 50e6}, None),
    "P2 price >= 10": ({"extra": lambda G, s: G.pc >= 10}, None),
    "P1 ATR >= 2% of price": ({"extra": lambda G, s: G.atr_pct >= 0.02}, None),
    # P4 / P5 in play
    "P4 top 10": ({"top_n": 10}, None),
    "P4 top 30": ({"top_n": 30}, None),
    "P5 rvol >= 2.0": ({"min_rvol": 2.0}, None),
    "P5 rvol >= 3.0": ({"min_rvol": 3.0}, None),
    "P5 rvol >= 1.2": ({"min_rvol": 1.2}, None),
    # P6 range width
    "P6 range >= 0.3 ATR": ({"extra": lambda G, s: G.width_atr >= 0.3}, None),
    "P6 range >= 0.4 ATR": ({"extra": lambda G, s: G.width_atr >= 0.4}, None),
    "P6 range >= 0.5 ATR": ({"extra": lambda G, s: G.width_atr >= 0.5}, None),
    "P6 range <= 1.5 ATR": ({"extra": lambda G, s: G.width_atr <= 1.5}, None),
    # P7 window
    "P7 until 10:30": ({"until": 1030}, None),
    "P7 until 11:00": ({"until": 1100}, None),
    "P7 until 12:00": ({"until": 1200}, None),
    # P9 / P10 sensors
    "P9 long only": ({"sides": (1,)}, None),
    "P9 short only": ({"sides": (-1,)}, None),
    "P9 move >= 0.25 ATR open->09:49": ({"extra": lambda G, s: (G.c49 - G.op).abs() / G.atr >= 0.25}, None),
    "P10 VWAP off": ({"vwap": False}, None),
    "P10 close in outer third of range": ({"extra": lambda G, s: np.where(s == 1, (G.c49 - G.lo) / (G.hi - G.lo) >= 2 / 3, (G.hi - G.c49) / (G.hi - G.lo) >= 2 / 3)}, None),
    # P12 cost filter (backtest version)
    "P12 cost/R <= 0.15": ({"extra": lambda G, s: G.cost_r <= 0.15}, None),
    "P12 cost/R <= 0.10": ({"extra": lambda G, s: G.cost_r <= 0.10}, None),
    # gates: market state measured AFTER 09:50 (SPY at 09:50 vs its 09:30-09:49 range; SPY since 09:50 at the trigger)
    "G1 SPY 09:50 position agrees (long spos>=0.5 / short <=0.5)": ({"extra": lambda G, s: np.where(s == 1, G.spos >= 0.5, G.spos <= 0.5)}, None),
    "G2 SPY since 09:50 not against the trade by > 0.20%": ({}, lambda T: T.side * spy_since950(T) >= -0.002),
    "G3 SPY since 09:50 with the trade (>= 0)": ({}, lambda T: T.side * spy_since950(T) >= 0),
    # P15 entry
    "P15 skip 09:50 triggers (live 'missed')": ({"skip950": True}, None),
    "P15 start 09:55": ({"start": 955}, None),
    # P17 stop / P18 target / P19 time / P20 management
    "P17 stop 0.4 range": ({"stop_or": 0.4}, None),
    "P17 stop 0.6 range": ({"stop_or": 0.6}, None),
    "P17 stop 0.75 range": ({"stop_or": 0.75}, None),
    "P17 stop 1.0 range (other side)": ({"stop_or": 1.0}, None),
    "P18 target 0.5 range": ({"target_or": 0.5}, None),
    "P18 target 1.0 range": ({"target_or": 1.0}, None),
    "P18 target 1.5 range": ({"target_or": 1.5}, None),
    "P18 no target (hold)": ({"target_or": None}, None),
    "P19 exit 12:00": ({"exit": 1200}, None),
    "P19 exit 13:30": ({"exit": 1330}, None),
    "P19 exit 15:00": ({"exit": 1500}, None),
    "P19 time stop 60 min if < +0.5R": ({"tstop_min": 60, "tstop_r": 0.5}, None),
    "P20 breakeven at +1R": ({"be_r": 1.0}, None),
    "P20 trail 1R after +1R": ({"trail_r": 1.0, "trail_after": 1.0}, None),
}

if __name__ == "__main__" and sys.argv[1] == "single":
    rows = []
    P = None
    for name, (v, post) in SINGLE.items():
        row, T = ev2(name, v, post, P)
        if name == "parent":
            P = T
            row, _ = ev2(name, v, post, P)
            T.to_parquet(S.OUT + "parent_trades.parquet", index=False)
        rows.append(row)
        g = lambda k: row.get(k, float('nan'))
        print(f"{name:58s} tr {g('train_avg'):+.3f} va {g('valid_avg'):+.3f} rp {g('replay_avg'):+.3f} ({g('replay_n')}) 2y {g('2y_avg'):+.3f} ({g('2y_n')}) "
              f"wob {g('2y_wo_best'):+.3f} wd {g('2y_worst_day'):+.1f} t {g('2y_t'):+.2f} | rp wob {g('replay_wo_best'):+.3f} wd {g('replay_worst_day'):+.1f}", flush=True)
    pd.DataFrame(rows).to_csv(S.OUT + "exp_single.csv", index=False)
