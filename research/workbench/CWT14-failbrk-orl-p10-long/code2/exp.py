"""Every configuration tried on top of WB4 (counted). Selection on TRAIN only. Educational only - not financial advice."""
from ev import *
import json
s, c = build()
P = pick(s)                                 # parent, first qualifying bar, base exits
reg = regime_map()
G = {
 # family: market-state gates measured after 09:50 (owner direction rule)
 "G1 SPY since 09:50 >= 0": dict(gate=lambda d: d.spy_d950 >= 0),
 "G2 SPY since 09:50 >= -0.10%": dict(gate=lambda d: d.spy_d950 >= -0.10),
 "G3 SPY since 09:50 >= -0.20%": dict(gate=lambda d: d.spy_d950 >= -0.20),
 "G4 SPY not below its 09:30-09:50 low": dict(gate=lambda d: d.spy_rng >= 0),
 "G5 SPY above session VWAP": dict(gate=lambda d: d.spy_vw >= 0),
 "G6 breadth_open >= 0.40": dict(gate=lambda d: d.breadth_open >= 0.40),
 "G7 breadth_open not lower than at 09:50": dict(gate=lambda d: d.br_d950 >= 0),
 "G8 SPY since 09:50 >= -0.10% and SPY fo >= -0.5%": dict(gate=lambda d: (d.spy_d950 >= -0.10) & (d.spy_fo1 >= -0.5)),
 # family: cost-to-R intake (module rule: 1R must be >= cost/x)
 "C1 cost/R <= 0.10": dict(gate=lambda d: d.ccr <= 0.10),
 "C2 cost/R <= 0.15": dict(gate=lambda d: d.ccr <= 0.15),
 "C3 cost/R <= 0.20": dict(gate=lambda d: d.ccr <= 0.20),
 # family: entry-drift guard (order time)
 "D1 |fill drift| <= 0.5R": dict(guard=lambda t: t.A_drift.abs() <= 0.5),
 "D2 fill drift >= -0.25R": dict(guard=lambda t: t.A_drift >= -0.25),
 "D3 runner CF at fill <= 0.15": dict(guard=lambda t: t.ccr_fill <= 0.15),
 # family: lots per symbol
 "L1 max 2 lots/symbol (refire, 10-min cooldown)": dict(refire=2, cool=10),
 "L2 max 2 lots/symbol (2nd only after 1st exits)": dict(refire=2, cool=-1),
 # family: time of day
 "T1 window 10:15-12:00": dict(window=(1015, 1200)),
 "T2 window 10:30-12:00": dict(window=(1030, 1200)),
 "T3 window 09:50-11:00": dict(window=(950, 1100)),
 "T4 window 09:50-13:00": dict(window=(950, 1300)),
 # family: exits
 "X1 levels from the fill": dict(exitc="FA"),
 "X2 breakeven after +0.3R": dict(exitc="BE3"),
 "X3 max hold 30 min": dict(exitc="MH30"),
 "X4 max hold 60 min": dict(exitc="MH60"),
 "X5 no target, trail 0.3R after +0.4R": dict(exitc="TR"),
 "X6 target 0.7R": dict(exitc="T07"),
 "X7 stop 1.2R (target 0.5R)": dict(exitc="S12"),
 "X8 stop 1.2R from the fill": dict(exitc="S12FA"),
 # family: day-level caps
 "K1 setup day latch -10R": dict(latch=10),
 "K2 setup day latch -20R": dict(latch=20),
 "K3 max 40 trades/day": dict(maxday=40),
}
def row(name, t):
    sc = score(t, P)
    tt = period(t, TWO_Y).copy(); tt["reg"] = tt.date.map(reg.regime)
    dt = tt.groupby("reg").R.mean().to_dict()
    return dict(name=name, **{f"{k}_{m}": v[m] for k, v in sc.items() for m in ("n", "avg", "wo_best", "worst_day", "win", "pdiff", "pt", "avg_win", "avg_loss", "best_share")},
                up=dt.get("up"), flat=dt.get("flat"), down=dt.get("down"))
if __name__ == "__main__":
    rows = []
    Pt = P.assign(R=P.base_r); rows.append(row("parent", Pt))
    rows.append(row("WB4", trades(c)))
    for k, kw in G.items():
        rows.append(row(k, trades(c, **kw)))
    D = pd.DataFrame(rows); D.to_csv(O2 + "exp1.csv", index=False)
    pd.set_option("display.width", 260); pd.set_option("display.max_rows", 200)
    print(D[["name", "train_n", "train_avg", "train_pt", "valid_avg", "replay_n", "replay_avg", "replay_wo_best", "replay_worst_day", "2y_n", "2y_avg", "2y_worst_day", "up", "flat", "down"]].round(3).to_string())
