"""Portfolio-wide view of ix-gate (NOTES 1.4 'portfolio-wide rule'): per condition, all 48 lists pooled (each list's
trades once), kept vs blocked, by side, day-clustered; plus the per-list improvement counts. Writes gate_pooled.csv.
Educational only - not financial advice."""
import numpy as np
import pandas as pd
from ix_gate import conditions, HERE, DATA, TREQ
from mcf.research import gates

t = pd.read_parquet(DATA / "gate_trades.parquet")
t = t[np.isfinite(t["r"])].reset_index(drop=True)
R = pd.read_csv(HERE / "gate_results.csv")
c = R[R.cond.str[:1].isin(["F", "N", "Z"])].copy()
c["imp_tr"], c["imp_va"] = c["train"] > c["base_train"], c["valid"] > c["base_valid"]
rows = []
parts = {nm: conditions(g.reset_index(drop=True)) for nm, g in t.groupby("list")}
for cn in parts[next(iter(parts))]:
    if cn.startswith("Z"):
        continue
    for side in ("all", "long", "short"):
        K, B = [], []
        for nm, g in t.groupby("list"):
            g = g.reset_index(drop=True)
            val, scope = parts[nm][cn]
            sc = np.ones(len(g), bool) if scope is None else scope
            m = sc & (np.ones(len(g), bool) if side == "all" else (g["side"].to_numpy() == side))
            k = np.asarray(val, bool)
            K.append(g.loc[m & k, ["date", "symbol", "r"]]); B.append(g.loc[m & ~k, ["date", "symbol", "r"]])
        K, B = pd.concat(K), pd.concat(B)
        if len(K) < 30 or len(B) < 30:
            continue
        sk, sb = gates.summary(K), gates.summary(B)
        cc = c[c.cond == cn]
        rows.append({"cond": cn, "side": side, "kept_n": sk["n"], "kept_exp": sk["exp_r"], "blocked_n": sb["n"],
                     "blocked_exp": sb["exp_r"], "diff": round(sk["exp_r"] - sb["exp_r"], 4),
                     "diff_t": round((sk["exp_r"] - sb["exp_r"]) / np.hypot(sk["se"], sb["se"]), 2),
                     "lists_improved_train": int(cc.imp_tr.sum()), "lists_improved_valid": int(cc.imp_va.sum()),
                     "lists_improved_both": int((cc.imp_tr & cc.imp_va).sum()), "lists": len(cc),
                     "consistent_rule_pass": bool(cc.imp_tr.mean() >= .75 and cc.imp_va.mean() >= .75
                                                  and (sk["exp_r"] - sb["exp_r"]) / np.hypot(sk["se"], sb["se"]) >= TREQ)})
out = pd.DataFrame(rows)
out.to_csv(HERE / "gate_pooled.csv", index=False)
print(out.to_string(index=False))
