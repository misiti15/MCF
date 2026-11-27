"""GENSIBS-1127 fixed sibling grid (pre-registered; see PREREG.md). Deterministic: no data is read here.
Each config = (id, family, parent, side, geom, window, min_adv, conds). Context conds use the lab context columns
(breadth = share above VWAP "BRvw", breadth_open = share above open "BRop", qqq_fo / spy_fo % since open).
Educational only - not financial advice."""
CTX = {"breadth", "breadth_open", "qqq_fo", "spy_fo"}

PARENTS = {
    "P05": dict(name="GEN-261022-05-MACDhge0p079-UpWickge0p71-ORHdistlem0p38-PM-BRoplt0p35-holdtr-short",
                side="short", geom="holdtr", window=(1300, 1500), min_adv=150e6,
                gate=("breadth_open", "<", 0.35),
                core=[("macd_hist", ">=", 0.079), ("or_high_dist_atr", "<=", -0.38), ("upper_wick", ">=", 0.71)]),
    "P07": dict(name="GEN-261026-07-Flow3ge0p56-BBpctge0p98-ADX7le34-PM-BRvwlt0p3-holdtr-short",
                side="short", geom="holdtr", window=(1300, 1500), min_adv=150e6,
                gate=("breadth", "<", 0.3),
                core=[("adx7", "<=", 34.0), ("bb_pctb12", ">=", 0.98), ("flow3", ">=", 0.56)]),
    "P37": dict(name="GEN-261023-07-RSIslopege9p1-BarRngATRge0p087-VWAPcrossesge8-LUNCH-BRvwgt0p7-hold-long",
                side="long", geom="hold", window=(1130, 1400), min_adv=95e6,
                gate=("breadth", ">", 0.7),
                core=[("bar_range_atr", ">=", 0.087), ("rsiSlope", ">=", 9.1), ("vwap_cross_n", ">=", 8.0)]),
    "P09": dict(name="GEN-261020-09-EMAdChgge0p093-Z12lem0p82-VWAPcrossesle0-MID-QQQltm0p3-holdtr-long",
                side="long", geom="holdtr", window=(1100, 1300), min_adv=150e6,
                gate=("qqq_fo", "<", -0.3),
                core=[("emaDiff_chg3", ">=", 0.093), ("vwap_cross_n", "<=", 0.0), ("z12", "<=", -0.82)]),
}
GATE_NEIGH = {"P05": [("breadth_open", "<", 0.30), ("breadth_open", "<", 0.40), ("breadth_open", "<", 0.50)],
              "P07": [("breadth", "<", 0.25), ("breadth", "<", 0.35), ("breadth", "<", 0.40)],
              "P37": [("breadth", ">", 0.60), ("breadth", ">", 0.65), ("breadth", ">", 0.75)],
              "P09": [("qqq_fo", "<", -0.2), ("qqq_fo", "<", -0.4), ("qqq_fo", "<", -0.6)]}
GATE_SWAP = {"P05": [("breadth", "<", 0.3), ("qqq_fo", "<", -0.6)],
             "P07": [("breadth_open", "<", 0.35), ("qqq_fo", "<", -0.6)],
             "P37": [("breadth_open", ">", 0.65), ("qqq_fo", ">", 0.6)],
             "P09": [("breadth", "<", 0.3), ("breadth_open", "<", 0.35)]}
WIN_ALT = {"P05": (1100, 1500), "P07": (1100, 1500), "P37": (1130, 1500), "P09": (1100, 1400)}
GEOM_ALT = {"hold": "holdtr", "holdtr": "hold"}
# breadth-gate transplant onto simple single-trigger bases (weak-breadth PM short / strong-breadth lunch long)
TRANS_SHORT = [("rsi5", ">=", 80.0), ("z12", ">=", 1.5), ("vwapReclaim", "==", -1.0), ("macd_hist", "<=", -0.079)]
TRANS_LONG = [("rsi5", "<=", 20.0), ("z12", "<=", -1.5), ("vwapReclaim", "==", 1.0), ("macd_hist", ">=", 0.079)]


def grid():
    out = []

    def add(fam, par, side, geom, window, min_adv, conds):
        out.append(dict(id=f"S{len(out) + 1:02d}", family=fam, parent=par, side=side, geom=geom,
                        window=tuple(window), min_adv=float(min_adv), conds=list(conds)))

    for k, p in PARENTS.items():                     # A: parent replica (reference)
        add("A-parent", k, p["side"], p["geom"], p["window"], p["min_adv"], [p["gate"]] + p["core"])
    for k, p in PARENTS.items():                     # B: gate threshold neighbours
        for g in GATE_NEIGH[k]:
            add("B-gate-neigh", k, p["side"], p["geom"], p["window"], p["min_adv"], [g] + p["core"])
    for k, p in PARENTS.items():                     # C: gate swapped to another breadth / index gate
        for g in GATE_SWAP[k]:
            add("C-gate-swap", k, p["side"], p["geom"], p["window"], p["min_adv"], [g] + p["core"])
    for k, p in PARENTS.items():                     # D: gate removed (is the day-type gate the edge?)
        add("D-no-gate", k, p["side"], p["geom"], p["window"], p["min_adv"], p["core"])
    for k, p in PARENTS.items():                     # E: one core feature dropped
        for j in range(len(p["core"])):
            add("E-drop1", k, p["side"], p["geom"], p["window"], p["min_adv"],
                [p["gate"]] + [c for i, c in enumerate(p["core"]) if i != j])
    for k, p in PARENTS.items():                     # F: window widened
        add("F-window", k, p["side"], p["geom"], WIN_ALT[k], p["min_adv"], [p["gate"]] + p["core"])
    for k, p in PARENTS.items():                     # G: geometry hold <-> holdtr
        add("G-geom", k, p["side"], GEOM_ALT[p["geom"]], p["window"], p["min_adv"], [p["gate"]] + p["core"])
    for c in TRANS_SHORT:                            # H: weak-breadth gate (P07) transplanted, PM short holdtr
        add("H-transplant", "P07", "short", "holdtr", (1300, 1500), 150e6, [("breadth", "<", 0.3), c])
    for c in TRANS_LONG:                             # H: strong-breadth gate (P37) transplanted, lunch long hold
        add("H-transplant", "P37", "long", "hold", (1130, 1400), 95e6, [("breadth", ">", 0.7), c])
    return out


# random-control pools: one random eligible bar per sampled symbol-day; side x geom walked for each
RND_POOLS = [("short", "holdtr"), ("short", "hold"), ("long", "hold"), ("long", "holdtr")]

if __name__ == "__main__":
    g = grid()
    for x in g:
        print(x["id"], x["family"], x["parent"], x["side"], x["geom"], x["window"], int(x["min_adv"] / 1e6),
              " & ".join(f"{a} {o} {v}" for a, o, v in x["conds"]))
    print(len(g), "configs")
