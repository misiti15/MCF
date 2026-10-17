"""Q10: decision-time "skip trades against the index" filter on the rework parent families (PLAN.md Q10).
    python research/swarm1017/followup/q10_index_filter.py TRADES.parquet
Writes q10_results.csv (family rows = the gate; setup rows = diagnostics) and q10_summary.json.
Educational only - not financial advice."""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from mcf.research import gates  # noqa: E402
from research.history2y import lib  # noqa: E402

T = pd.read_parquet(sys.argv[1])
T["date"] = pd.to_datetime(T["date"]).dt.date
assert not ((T.date >= pd.Timestamp("2024-11-01").date()) & (T.date <= pd.Timestamp("2025-02-28").date())).any()
REG = lib.regimes()
T["regime"] = T.date.map(REG["regime"])
T["train"] = pd.to_datetime(T.date) < "2026-01-01"
sgn = np.where(T.side.eq("long"), 1.0, -1.0)

FILTERS = {}
for X in (0.25, 0.5, 0.75, 1.0):
    for I, col in (("SPY", ["spy_fo"]), ("QQQ", ["qqq_fo"]), ("ANY", ["spy_fo", "qqq_fo"]), ("SEC", ["sec_fo"])):
        sk = np.zeros(len(T), bool)
        for cn in col:
            v = sgn * T[cn].to_numpy(float)          # < 0: the index moves against the trade side
            sk |= v < -X
        FILTERS[f"{I}_{X:.2f}"] = sk
for b in (0.25, 0.35, 0.45):
    br = T.breadth.to_numpy(float)
    FILTERS[f"BRD_{b:.2f}"] = np.where(sgn > 0, br < b, br > 1 - b)

n_setups = T.setup.nunique()
N_FAM = len(FILTERS) * T.family.nunique()
N = N_FAM + len(FILTERS) * n_setups + 912 + 1052
BAR = gates.t_required(N)
rng = np.random.default_rng(20261017)


def stats(t):
    s = gates.summary(t[["date", "r"]]) if len(t) else {"n": 0}
    return s.get("n", 0), s.get("exp_r"), s.get("t")


def rand_pct(r, k, kept_mean, draws=1000):
    """Percentile of kept_mean among `draws` random skips that drop each trade with probability k/n."""
    n = len(r)
    if k == 0 or k >= n:
        return None
    p = k / n
    res = []
    for _ in range(draws // 50):
        M = (rng.random((50, n), dtype=np.float32) >= p).astype(np.float32)
        res.append((M @ r.astype(np.float32)) / M.sum(1))
    res = np.concatenate(res)
    return float((res < kept_mean).mean()), float(np.quantile(res, 0.95))


rows = []
for level, keyname in (("family", "family"), ("setup", "setup")):
    for key, idx in T.groupby(keyname).indices.items():
        base = T.iloc[idx]
        bn, be, bt = stats(base)
        btr, bva = base.r[base.train].mean(), base.r[~base.train].mean()
        for fn, sk in FILTERS.items():
            s = sk[idx]
            kept, blk = base[~s], base[s]
            kn, ke, kt = stats(kept)
            row = {"level": level, "key": key, "filter": fn, "n_base": bn, "exp_base": be, "t_base": bt,
                   "n_kept": kn, "exp_kept": ke, "t_kept": kt, "n_blocked": int(s.sum()),
                   "exp_blocked": stats(blk)[1], "t_blocked": stats(blk)[2],
                   "exp_base_tr": btr, "exp_base_va": bva,
                   "exp_kept_tr": kept.r[kept.train].mean(), "exp_kept_va": kept.r[~kept.train].mean()}
            if level == "family":
                rs = gates.regime_split(kept[["date", "r"]], REG)
                wf = gates.walk_forward(kept[["date", "r"]], exclude_months=lib.LOCKED_MONTHS)
                pr = rand_pct(base.r.to_numpy(float), int(s.sum()), ke if ke is not None else -9)
                xs = gates.summary(kept[["date"]].assign(r=kept.r - kept.ctrl)) if kn else {}
                row.update({"up_kept": rs["up"].get("exp_r"), "flat_kept": rs["flat"].get("exp_r"), "down_kept": rs["down"].get("exp_r"),
                            "up_base": base.r[base.regime.eq("up")].mean(), "flat_base": base.r[base.regime.eq("flat")].mean(),
                            "down_base": base.r[base.regime.eq("down")].mean(),
                            "regime_pass": rs["pass"], "wf_share": wf["share_positive"],
                            "rand_pct": pr[0] if pr else None, "rand_q95": pr[1] if pr else None,
                            "excess_kept": xs.get("exp_r"), "ex_best_day_kept": gates.summary(kept[["date", "r"]]).get("ex_best_day") if kn else None})
                helps = (row["exp_kept_tr"] > btr) and (row["exp_kept_va"] > bva) and (pr is not None and pr[0] >= 0.95)
                row["helps"] = bool(helps)
                row["passes"] = bool(helps and (ke or -1) > 0 and (kt or 0) >= BAR and rs["pass"] and (wf["share_positive"] or 0) >= 0.6)
            rows.append(row)
R = pd.DataFrame(rows)
R.to_csv(HERE / "q10_results.csv", index=False, float_format="%.4f")
F = R[R.level == "family"]
S = R[R.level == "setup"]
# share of a family's setups improved in train AND valid (diagnostic)
fam_of = T.groupby("setup").family.first()
S = S.assign(family=S.key.map(fam_of), both=(S.exp_kept_tr > S.exp_base_tr) & (S.exp_kept_va > S.exp_base_va))
share = S.groupby(["family", "filter"]).both.mean().rename("setups_improved_share").reset_index()
F = F.merge(share, left_on=["key", "filter"], right_on=["family", "filter"], how="left").drop(columns="family")
F.to_csv(HERE / "q10_family.csv", index=False, float_format="%.4f")
summ = {"configs": {"family": int(N_FAM), "setup_diagnostic": int(len(FILTERS) * n_setups), "sibling_lineages": 1964, "N": int(N)},
        "bar": BAR, "n_trades": int(len(T)), "setups": int(n_setups),
        "helps": F[F.helps][["key", "filter", "exp_base", "exp_kept", "t_kept", "exp_kept_tr", "exp_kept_va", "up_kept", "down_kept", "wf_share", "rand_pct"]].to_dict("records"),
        "passes": F[F.passes][["key", "filter"]].to_dict("records"),
        "base": F.drop_duplicates("key")[["key", "n_base", "exp_base", "t_base", "exp_base_tr", "exp_base_va", "up_base", "flat_base", "down_base"]].to_dict("records")}
(HERE / "q10_summary.json").write_text(json.dumps(summ, indent=1, default=float))
pd.set_option("display.width", 250)
print("N", N, "bar", BAR)
print(F[["key", "filter", "n_base", "exp_base", "n_kept", "exp_kept", "t_kept", "exp_blocked", "exp_kept_tr", "exp_base_tr", "exp_kept_va", "exp_base_va", "up_kept", "down_kept", "wf_share", "rand_pct", "setups_improved_share", "helps", "passes"]].round(3).to_string())
