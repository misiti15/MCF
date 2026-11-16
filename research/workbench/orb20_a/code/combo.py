"""Mechanic orb20_a: finer grid on the parts that improved both tests + combinations. Educational only - not financial advice."""
import sys
sys.argv = ["ana.py", "none"]
from ana import *
def cr(x): return lambda G, s: G.cost_r <= x
def AND(*fs): return lambda G, s: np.logical_and.reduce([np.asarray(f(G, s)) for f in fs])
px10 = lambda G, s: G.pc >= 10
adv50 = lambda G, s: G.adv >= 50e6
atr2 = lambda G, s: G.atr_pct >= 0.02
C = {
    "parent": {},
    "P4 top 15": {"top_n": 15},
    "P12 cost/R <= 0.12": {"extra": cr(0.12)},
    "P12 cost/R <= 0.20": {"extra": cr(0.20)},
    "P2 price >= 20": {"extra": lambda G, s: G.pc >= 20},
    "C1 top10 + cost/R<=0.15": {"top_n": 10, "extra": cr(0.15)},
    "C2 top15 + cost/R<=0.15": {"top_n": 15, "extra": cr(0.15)},
    "C3 top10 + price>=10": {"top_n": 10, "extra": px10},
    "C4 top10 + cost/R<=0.15 + price>=10": {"top_n": 10, "extra": AND(cr(0.15), px10)},
    "C5 cost/R<=0.15 + price>=10": {"extra": AND(cr(0.15), px10)},
    "C6 cost/R<=0.15 + price>=10 + ADV>=50M": {"extra": AND(cr(0.15), px10, adv50)},
    "C7 top10 + cost/R<=0.15 + ADV>=50M": {"top_n": 10, "extra": AND(cr(0.15), adv50)},
    "C8 top10 + cost/R<=0.10": {"top_n": 10, "extra": cr(0.10)},
    "C9 C1 + stop 0.75": {"top_n": 10, "extra": cr(0.15), "stop_or": 0.75},
    "C10 C1 + stop 0.6": {"top_n": 10, "extra": cr(0.15), "stop_or": 0.6},
    "C11 C1 + ATR>=2%": {"top_n": 10, "extra": AND(cr(0.15), atr2)},
    "C12 C1 + until 10:30": {"top_n": 10, "extra": cr(0.15), "until": 1030},
    "C13 C4 + ADV>=50M": {"top_n": 10, "extra": AND(cr(0.15), px10, adv50)},
    "C14 top15 + cost/R<=0.15 + price>=10": {"top_n": 15, "extra": AND(cr(0.15), px10)},
}
rows = []; P = None
for name, v in C.items():
    row, T = ev2(name, v, None, P)
    if P is None:
        P = T; row, _ = ev2(name, v, None, P)
    rows.append(row)
    g = lambda k: row.get(k, float('nan'))
    print(f"{name:40s} tr {g('train_avg'):+.3f} va {g('valid_avg'):+.3f} rp {g('replay_avg'):+.3f} ({g('replay_n')}) 2y {g('2y_avg'):+.3f} ({g('2y_n')}) "
          f"wob {g('2y_wo_best'):+.3f} wd {g('2y_worst_day'):+.1f} t {g('2y_t'):+.2f} | rp wob {g('replay_wo_best'):+.3f} wd {g('replay_worst_day'):+.1f} t {g('replay_t'):+.2f}", flush=True)
pd.DataFrame(rows).to_csv(S.OUT + "exp_combo.csv", index=False)
