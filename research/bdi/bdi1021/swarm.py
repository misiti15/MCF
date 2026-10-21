"""bdi1021 swarm: "index low is in" gate for short setups (and the "high is in" mirror for long setups), 196
pre-declared configurations (PLAN.md), scored with gates1021's evaluate() on gates1021's cached live-shaped signal
tables. The locked block 2024-11-01..2025-02-28 is never read (pyarrow row filter at read time + asserts).
Usage: python swarm.py            (G21SCR may point at the gates1021 scratch)
Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
G21 = HERE.parent / "gates1021" / "scripts"
sys.path.insert(0, str(G21))
from common import gates, no_locked  # noqa: E402
from load import load_sig  # noqa: E402
from part_b import evaluate  # noqa: E402

import importlib.util  # noqa: E402
_sp = importlib.util.spec_from_file_location("l20common", HERE.parent / "longs1020" / "scripts" / "common.py")
L20 = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(L20)  # load_1min: locked rows filtered at read


def spy_state() -> pd.DataFrame:
    """Per (date, tod) for tod = every 5-min decision close 09:35..15:55: state from SPY 1-min bars closed by tod."""
    b = L20.load_1min("SPY")
    b = b.between_time("09:30", "15:59")
    rows = []
    for d, g in b.groupby(b.index.date):
        mins = (g.index.hour * 60 + g.index.minute).to_numpy()
        tp = (g.high + g.low + g.close).to_numpy() / 3
        v = g.volume.to_numpy()
        cv = np.cumsum(tp * v) / np.maximum(np.cumsum(v), 1)
        lo = np.minimum.accumulate(g.low.to_numpy()); hi = np.maximum.accumulate(g.high.to_numpy())
        lo_i = np.array([np.argmin(g.low.to_numpy()[:k + 1]) for k in range(len(g))])
        hi_i = np.array([np.argmax(g.high.to_numpy()[:k + 1]) for k in range(len(g))])
        c = g.close.to_numpy()
        for t in range(9 * 60 + 35, 16 * 60, 5):
            k = np.searchsorted(mins, t) - 1            # last bar starting before t (closed by t)
            if k < 0: continue
            rows.append((d, (t // 60) * 100 + t % 60, c[k], cv[k], lo[k], mins[lo_i[k]], hi[k], mins[hi_i[k]]))
    s = pd.DataFrame(rows, columns=["date", "tod", "c", "vwap", "lo", "lo_min", "hi", "hi_min"])
    no_locked(s["date"].unique())
    s["up_off_low"] = (s.c / s.lo - 1) * 100
    s["dn_off_high"] = (1 - s.c / s.hi) * 100
    s["above_vwap"] = s.c > s.vwap
    return s


def masks(s: pd.DataFrame, side: str) -> dict:
    early = 10 * 60 + 30
    if side == "short":
        a = s["above_vwap"].to_numpy(bool); x = s["up_off_low"].to_numpy(float); m = s["lo_min"].to_numpy(float)
        p = "S"
    else:
        a = ~s["above_vwap"].to_numpy(bool); x = s["dn_off_high"].to_numpy(float); m = s["hi_min"].to_numpy(float)
        p = "L"
    with np.errstate(invalid="ignore"):
        return {f"{p}1 extreme by 10:30, >=0.30% off it, VWAP side": a & (x >= 0.30) & (m <= early),
                f"{p}2 extreme by 10:30, >=0.50% off it, VWAP side": a & (x >= 0.50) & (m <= early),
                f"{p}3 extreme any time, >=0.30% off it, VWAP side": a & (x >= 0.30),
                f"{p}4 extreme any time, >=0.50% off it, VWAP side": a & (x >= 0.50)}


def main():
    st = spy_state()
    us = pd.read_csv(HERE.parent / "gates1021" / "setups_scored.csv")
    sig = load_sig()
    sig = sig.merge(st[["date", "tod", "up_off_low", "dn_off_high", "above_vwap", "lo_min", "hi_min"]],
                    on=["date", "tod"], how="left")
    miss = sig["above_vwap"].isna().mean()
    sig["above_vwap"] = sig["above_vwap"].fillna(False).astype(bool)
    rows = []
    for _, u in us.iterrows():
        s = sig[sig["setup"] == u["setup"]].sort_values(["date", "tod", "symbol"]).reset_index(drop=True)
        if not len(s):
            rows.append({"setup": u["setup"], "gate": "(no trades)"}); continue
        ccol = f"c_{u['side']}_{u['geom']}"
        for gname, blk in masks(s, u["side"]).items():
            rows.append({"setup": u["setup"], "accounts": u["accounts"], "side": u["side"], "geom": u["geom"],
                         "gate": gname, **evaluate(s, np.asarray(blk, bool), ccol)})
    res = pd.DataFrame(rows)
    ok = res["gate"] != "(no trades)"
    N_study = int(ok.sum()); N_lin = 718 + N_study
    bar = gates.t_required(N_lin)
    stable = ok & (res["train_blocked_pct"] >= 3) & (res["valid_blocked_pct"] >= 3) & (res["train_delta"] > 0) & \
        (res["valid_delta"] > 0) & (res["train_delta_t"] >= 2.0) & (res["valid_delta_t"] >= 1.0)
    beta = (res["train_delta"] - res["train_ctrl_delta"] > 0) & (res["valid_delta"] - res["valid_ctrl_delta"] > 0)
    reg = (res["up_delta"] >= 0) & (res["down_delta"] >= 0)
    part = (res["train_blocked_pct"] <= 33) & (res["valid_blocked_pct"] <= 33)
    res["stable_split"] = stable
    res["not_only_beta"] = beta
    res["regimes_ok"] = reg
    res["participation_ok"] = part
    res["bar_ok"] = res["all_delta_t"] >= bar
    fin = stable & beta & reg & part & res["bar_ok"]
    res["verdict"] = np.where(fin & (res["train_gated_exp"] > 0) & (res["valid_gated_exp"] > 0), "finalist",
                              np.where(fin, "finalist: improves a losing setup",
                                       np.where(stable, "stable split only", "fail")))
    res.to_csv(HERE / "results.csv", index=False)
    cnt = {"configs_study": N_study, "setups": int(res.loc[ok, "setup"].nunique()), "lineage_N": N_lin,
           "bar_lineage": round(bar, 3), "bar_study": round(gates.t_required(N_study), 3),
           "sig_rows_missing_spy_state_pct": round(100 * miss, 3),
           "stable_split": int(stable.sum()), "finalists": int((res["verdict"] == "finalist").sum()),
           "finalists_losing_setup": int((res["verdict"] == "finalist: improves a losing setup").sum()),
           "verdicts": res.loc[ok, "verdict"].value_counts().to_dict()}
    json.dump(cnt, open(HERE / "counts.json", "w"), indent=1)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(cnt)
    g = res[ok].groupby("gate").agg(n=("setup", "size"), tr_blk=("train_blocked_pct", "median"),
                                   va_blk=("valid_blocked_pct", "median"), tr_d=("train_delta", "mean"),
                                   va_d=("valid_delta", "mean"), va_ctrl=("valid_ctrl_delta", "mean"),
                                   pos_both=("train_delta", lambda x: int(((x > 0) & (res.loc[x.index, "valid_delta"] > 0)).sum())),
                                   up=("up_delta", "mean"), down=("down_delta", "mean"))
    print("\n== by gate (mean over setups)"); print(g.round(4).to_string())
    cols = ["setup", "gate", "train_blocked_pct", "valid_blocked_pct", "train_parent_exp", "train_gated_exp",
            "valid_parent_exp", "valid_gated_exp", "train_delta_t", "valid_delta_t", "all_delta_t",
            "valid_ctrl_delta", "valid_delta", "up_delta", "down_delta", "verdict"]
    print("\n== stable split rows"); print(res[stable][cols].to_string())
    print("\n== top 10 by all_delta_t"); print(res[ok].sort_values("all_delta_t", ascending=False)[cols].head(10).to_string())
    return st


if __name__ == "__main__":
    main()
