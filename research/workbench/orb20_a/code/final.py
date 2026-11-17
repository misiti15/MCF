"""Mechanic orb20_a: last combos around the finalists + the full side-by-side for the shortlist. Educational only - not financial advice."""
import sys
sys.argv = ["ana.py", "none"]
from ana import *
sys.path.insert(0, "/home/user/MCF"); sys.path.insert(0, "/home/user/MCF/research/history2y")
import lib as H
REG = H.regimes().reset_index() if "date" not in H.regimes().columns else H.regimes()
REG["date"] = REG["date"].astype(str)
regcol = [c for c in REG.columns if c != "date"][0] if "regime" not in REG.columns else "regime"
RG = dict(zip(REG.date, REG[regcol]))
def AND(*fs): return lambda G, s: np.logical_and.reduce([np.asarray(f(G, s)) for f in fs])
px = lambda x: (lambda G, s: G.pc >= x)
adv = lambda x: (lambda G, s: G.adv >= x)
cr = lambda x: (lambda G, s: G.cost_r <= x)
C = {
    "parent": {},
    "WB1 P4 top 10": {"top_n": 10},
    "WB2 P2 price >= 20": {"extra": px(20)},
    "WB3 P4 top 10 + P2 price >= 10": {"top_n": 10, "extra": px(10)},
    "x top10 + price>=20": {"top_n": 10, "extra": px(20)},
    "x top10 + price>=10 + ADV>=50M": {"top_n": 10, "extra": AND(px(10), adv(50e6))},
    "x price>=20 + ADV>=50M": {"extra": AND(px(20), adv(50e6))},
    "x top12 + price>=10": {"top_n": 12, "extra": px(10)},
    "x top8 + price>=10": {"top_n": 8, "extra": px(10)},
    "x WB3 + stop 0.75": {"top_n": 10, "extra": px(10), "stop_or": 0.75},
    "x WB3 + price>=15": {"top_n": 10, "extra": px(15)},
    "x WB3 + cost/R<=0.20": {"top_n": 10, "extra": AND(px(10), cr(0.20))},
}
rows = []; P = None; KEEP = {}
for name, v in C.items():
    row, T = ev2(name, v, None, P)
    if P is None:
        P = T; row, _ = ev2(name, v, None, P)
    t2 = S.period(T, S.TWO_Y)
    for k in ("up", "flat", "down"):
        row[f"2y_{k}"] = t2[t2.date.map(RG) == k].r.mean()
    for test, rng in (("replay", S.REPLAY), ("2y", S.TWO_Y)):
        t = S.period(T, rng)
        row[f"{test}_bps"] = float((t.r * (t.fill - t.stop).abs() / t.fill).sum() / len(t) * 1e4) if len(t) else np.nan
        hold = (t.xt // 100 * 60 + t.xt % 100) - (t.et // 100 * 60 + t.et % 100)
        row[f"{test}_hold"] = float(hold.median()) if len(t) else np.nan
        row[f"{test}_exits"] = json.dumps(t.exit_reason.value_counts(normalize=True).round(3).to_dict())
    rows.append(row); KEEP[name] = T
    g = lambda k: row.get(k, float('nan'))
    print(f"{name:34s} tr {g('train_avg'):+.3f} va {g('valid_avg'):+.3f} rp {g('replay_avg'):+.3f} ({g('replay_n')}) 2y {g('2y_avg'):+.3f} ({g('2y_n')}) "
          f"wob {g('2y_wo_best'):+.3f} wd {g('2y_worst_day'):+.1f} t {g('2y_t'):+.2f} | rp wob {g('replay_wo_best'):+.3f} wd {g('replay_worst_day'):+.1f} t {g('replay_t'):+.2f} "
          f"| u/f/d {g('2y_up'):+.3f}/{g('2y_flat'):+.3f}/{g('2y_down'):+.3f} bps {g('replay_bps'):+.1f}/{g('2y_bps'):+.1f}", flush=True)
pd.DataFrame(rows).to_csv(S.OUT + "exp_final.csv", index=False)
for n in ("parent", "WB1 P4 top 10", "WB2 P2 price >= 20", "WB3 P4 top 10 + P2 price >= 10"):
    KEEP[n].to_parquet(S.OUT + "trades_" + n.split()[0] + ".parquet", index=False)
