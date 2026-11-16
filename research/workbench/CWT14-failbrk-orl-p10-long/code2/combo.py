from exp import *
def both(*fs): return lambda d: np.logical_and.reduce([f(d) for f in fs])
c1 = lambda d: d.ccr <= 0.10; g3 = lambda d: d.spy_d950 >= -0.20; g1 = lambda d: d.spy_d950 >= 0; g4 = lambda d: d.spy_rng >= 0
CB = {
 "K-a C1 + X7": dict(gate=c1, exitc="S12"),
 "K-b C1 + X7 + G3": dict(gate=both(c1, g3), exitc="S12"),
 "K-c C1 + X7 + T1": dict(gate=c1, exitc="S12", window=(1015, 1200)),
 "K-d C1 + X7 + G3 + T1": dict(gate=both(c1, g3), exitc="S12", window=(1015, 1200)),
 "K-e D3 + X7": dict(guard=lambda t: t.ccr_fill <= 0.15, exitc="S12"),
 "K-f C1 + X8": dict(gate=c1, exitc="S12FA"),
 "K-g C1 + X7 + G4": dict(gate=both(c1, g4), exitc="S12"),
 "K-h C1 + X7 + T2": dict(gate=c1, exitc="S12", window=(1030, 1200)),
 "K-i C1 + X7 + G3 + D1": dict(gate=both(c1, g3), exitc="S12", guard=lambda t: t.A_drift.abs() <= 0.5),
}
if __name__ == "__main__":
    rows = [row(k, trades(c, **kw)) for k, kw in CB.items()]
    D = pd.DataFrame(rows); D.to_csv(O2 + "exp2.csv", index=False)
    pd.set_option("display.width", 260)
    print(D[["name", "train_n", "train_avg", "valid_avg", "replay_n", "replay_avg", "replay_wo_best", "replay_worst_day", "2y_n", "2y_avg", "2y_wo_best", "2y_worst_day", "up", "flat", "down"]].round(3).to_string())
