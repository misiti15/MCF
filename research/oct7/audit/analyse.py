"""AUDIT scoring (train 07-15..08-25, valid 08-26..09-15). Production costs are already inside the fills
(engine.simulate with config costs: 1c/share + 1 bps per side, +2c on stops, 3c/share on extended-tier names,
next-1-minute-bar entry, stop-first). Sizing = Backtester.allocate rule: shares = int(min($250 / per-share risk,
slot $ / price)). Standalone = every candidate sized alone; portfolio = Backtester.allocate together with the
live setups' trades (research/oct7/exits Lab base, verified identical to engine.simulate).
Educational only - not financial advice."""
import json
import pickle
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from mcf.backtest.engine import Trade, slot_notional  # noqa: E402
from mcf.config import load_config  # noqa: E402

TRAIN_END = "2026-08-25"
cfg = load_config()
SLOT = slot_notional(cfg["account"])
RISK = cfg["account"]["starting_equity"] * cfg["account"]["risk_per_trade_pct"] / 100
rng = np.random.default_rng(11)


def frame(cands):
    rows = []
    for c in cands:
        tr = c["trade"]
        ps = abs(tr["entry"] - tr["stop"])
        sh = int(min(RISK / ps, SLOT / tr["entry"])) if ps > 0 else 0
        if sh < 1:
            continue
        pnl = tr["side"] * (tr["exit"] - tr["entry"]) * sh
        rows.append({**{k: c[k] for k in c if k != "trade"}, "entry": tr["entry"], "stop": tr["stop"], "exit": tr["exit"],
                     "reason": tr["exit_reason"], "r": tr["r_multiple"], "r_atr": tr["side"] * (tr["exit"] - tr["entry"]) / (0.25 * c["atr"]),
                     "shares": sh, "pnl": pnl, "slot_bound": sh * tr["entry"] >= 0.9 * SLOT,
                     "entry_time": tr["entry_time"], "mfe_r": tr["mfe_r"]})
    df = pd.DataFrame(rows)
    df["split"] = np.where(df.date <= TRAIN_END, "train", "valid")
    return df


def tday(daily):
    daily = np.asarray(daily, float)
    if len(daily) < 3 or daily.std(ddof=1) == 0:
        return float("nan")
    return float(daily.mean() / (daily.std(ddof=1) / np.sqrt(len(daily))))


def stats(s, all_days=None):
    if not len(s):
        return {"n": 0}
    d = s.groupby("date").pnl.sum()
    dr = s.groupby("date").r.mean()
    if all_days is not None:
        d = d.reindex(all_days, fill_value=0.0)
    best = d.idxmax()
    return {"n": int(len(s)), "days": int(s.date.nunique()), "usd_total": round(s.pnl.sum(), 0), "usd_pt": round(s.pnl.mean(), 2),
            "r_pt": round(s.r.mean(), 4), "r_se": round(s.r.std(ddof=1) / np.sqrt(len(s)), 4) if len(s) > 1 else None,
            "win": round((s.pnl > 0).mean(), 3), "t_day_usd": round(tday(d), 2), "t_day_meanR": round(tday(dr), 2),
            "ex_best_usd": round(d.sum() - d.max(), 0), "best_share": round(d.max() / d.sum(), 2) if d.sum() > 0 else None,
            "green_days": round((d > 0).mean(), 2), "slot_bound": round(s.slot_bound.mean(), 2),
            "ext_share": round(s.ext.mean(), 3), "stop_rate": round((s.reason == "stop").mean(), 3)}


def filt(base, keep_mask, label):
    """Kept-set stats, paired daily difference vs base, random-subset p (same keep fraction, rule 6)."""
    out = {}
    for sp in ("train", "valid"):
        b = base[base.split == sp]
        k = b[keep_mask[base.split == sp]]
        days = sorted(b.date.unique())
        diff = k.groupby("date").pnl.sum().reindex(days, fill_value=0) - b.groupby("date").pnl.sum().reindex(days, fill_value=0)
        frac = len(k) / len(b)
        sims = np.array([b.pnl.to_numpy()[rng.random(len(b)) < frac].mean() for _ in range(4000)])
        out[sp] = {**stats(k), "base": stats(b), "d_usd_vs_base": round(diff.sum(), 0), "d_t_day": round(tday(diff), 2),
                   "p_random_subset_pt": round(float((sims >= k.pnl.mean()).mean()), 3)}
    return out


if __name__ == "__main__":
    C = frame(pickle.load(open("research/oct7/audit/data/cands.pkl", "rb"))["cands"])
    res = {"slot": SLOT, "risk": RISK, "standalone": {}}
    for st in sorted(C.setup.unique()):
        res["standalone"][st] = {sp: stats(C[(C.setup == st) & (C.split == sp)]) for sp in ("train", "valid")}
    print(json.dumps(res["standalone"], indent=0, default=str))
    pickle.dump(C, open("research/oct7/audit/data/C.pkl", "wb"))
    json.dump(res, open("research/oct7/audit/standalone.json", "w"), indent=1, default=str)
