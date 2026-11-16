from bps import *
c07 = lambda d: d.ccr <= 0.07; g3b = lambda d: d.spy_d950 >= -0.30; bo3 = lambda d: d.breadth_open >= 0.30
V = {
 "M1 C1+G3+S15 + max 30 trades/day": dict(**base, exitc="S15", maxday=30),
 "M2 C1+G3+S15 + max 60 trades/day": dict(**base, exitc="S15", maxday=60),
 "M3 cost/R<=0.07 + G3 + S15": dict(gate=both(c07, g3), exitc="S15"),
 "M4 C1 + SPY>=-0.30% + S15": dict(gate=both(c1, g3b), exitc="S15"),
 "M5 C1+G3+S15 + breadth_open>=0.30": dict(gate=both(c1, g3, bo3), exitc="S15"),
 "M6 C1+G3+S15 + window 10:15-12:00": dict(**base, exitc="S15", window=(1015, 1200)),
 "M7 C1+G3+S15 + max 2 lots (refire after exit)": dict(**base, exitc="S15", refire=2, cool=-1),
 "M8 C1+G3+S15 + drift guard 0.5R": dict(**base, exitc="S15", guard=lambda t: t.A_drift.abs() <= 0.5),
}
if __name__ == "__main__":
    rows = []
    for k, kw in V.items():
        t = trades(c3, **kw); t = t.assign(bp=bps(t, 1.5)); r = row(k, t)
        r["2y_bps"] = period(t, TWO_Y).bp.mean(); r["replay_bps"] = period(t, REPLAY).bp.mean(); rows.append(r)
    D = pd.DataFrame(rows); D.to_csv(O2 + "exp4.csv", index=False)
    pd.set_option("display.width", 260)
    print(D[["name", "train_avg", "valid_avg", "replay_n", "replay_avg", "replay_wo_best", "replay_worst_day", "2y_n", "2y_avg", "2y_wo_best", "2y_worst_day", "2y_bps", "up", "flat", "down"]].round(3).to_string())
