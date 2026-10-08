"""Oct-7 exits study: (1) hard max-loss % cap on the stop, (2) give-back protection, per setup and portfolio,
production engine (simulate + Backtester.allocate, config/default.yaml) on 2026-07-15..2026-09-15.
Grid is pre-declared in GRID below and every configuration is counted. Educational only - not financial advice.
Run: python -m research.oct7.exits.study  (needs data/sigs.pkl from collect.py)"""
from __future__ import annotations

import copy
import json
import pickle
import sys
from dataclasses import fields

import numpy as np
import pandas as pd

from mcf.backtest.engine import Backtester, simulate
from mcf.config import load_config
from mcf.strategies.base import Signal, t
from research.oct7.exits.sim import simulate2

OUT = "research/oct7/exits"
TRAIN_END, VALID_END = "2026-08-25", "2026-09-15"
SETUPS = ["orb20_a", "heat_fade_short", "heat_fade_long", "exhaustion_short", "intraday_momentum"]
CAPS = [0.75, 1.0, 1.5, 2.0, 3.0]
_SIG_FIELDS = {f.name for f in fields(Signal)}


def grid_for(setup: str) -> list[dict]:
    """Pre-declared exit grid (written before any result was seen). Each item: id, family, params."""
    g = []
    for b in (0.5, 0.75):
        g.append({"family": "be", "be_at_r": b})
    for tr in (0.5, 0.75, 1.0):
        for af in (0.75, 1.0, 1.5):
            g.append({"family": "trail", "trail_r": tr, "trail_after_r": af})
    for fr in (0.33, 0.5):
        g.append({"family": "scale", "scale_out_r": 0.5, "scale_out_frac": fr})
    for x, ys in ((0.5, (0.0, 0.25)), (0.75, (0.0, 0.25, 0.5)), (1.0, (0.0, 0.25, 0.5))):
        for y in ys:
            g.append({"family": "gb", "gb": (x, y)})
    for x in (0.75, 1.0):
        for y in (0.25, 0.5):
            g.append({"family": "lock", "lock": (x, y)})
    if setup != "intraday_momentum":           # enters at 15:30; a 14:30-15:30 profit take is a no-op there
        for lt in ("14:30", "15:00", "15:30"):
            for m in (0.0, 0.25):
                g.append({"family": "late", "late": (lt, m)})
        g.append({"family": "late_ctrl", "exit_by": "15:30"})
    for c in g:
        c["id"] = setup + ":" + ",".join(f"{k}={v}" for k, v in c.items() if k != "family")
        c["setup"] = setup
    return g


def neighbours(c: dict, grid: list[dict]) -> list[dict]:
    """Adjacent settings in the same family (one parameter one step away)."""
    fam = [g for g in grid if g["family"] == c["family"] and g["id"] != c["id"]]
    def vec(g):
        if g["family"] == "be": return (g["be_at_r"],)
        if g["family"] == "trail": return (g["trail_r"], g["trail_after_r"])
        if g["family"] == "scale": return (g["scale_out_frac"],)
        if g["family"] in ("gb", "lock"): return tuple(g[g["family"]])
        if g["family"] == "late": return (t(g["late"][0]).hour * 60 + t(g["late"][0]).minute, g["late"][1])
        return (0,)
    axes = {}
    for g in [c] + fam:
        for i, v in enumerate(vec(g)):
            axes.setdefault(i, set()).add(v)
    axes = {i: sorted(v) for i, v in axes.items()}
    out = []
    vc = vec(c)
    for g in fam:
        vg = vec(g)
        diff = [i for i in range(len(vc)) if vg[i] != vc[i]]
        if len(diff) == 1:
            i = diff[0]
            if abs(axes[i].index(vg[i]) - axes[i].index(vc[i])) == 1:
                out.append(g)
    return out


class Lab:
    def __init__(self):
        d = pickle.load(open(f"{OUT}/data/sigs.pkl", "rb"))
        self.cfg = load_config()
        self.bt = Backtester([], self.cfg)
        self.sigs = [s for s in d["signals"] if s["date"] <= VALID_END]
        self.bars = d["bars"]
        self.arr = {k: (*(b[c].to_numpy() for c in ("open", "high", "low", "close")), np.array(b.index.time))
                    for k, b in self.bars.items()}
        for s in self.sigs:
            b = self.bars[(s["symbol"], s["date"])]
            sg = s["sig"]
            s["ref"] = sg["entry_price"] if sg.get("entry_price") is not None else float(b["close"].iloc[sg["bar_index"]])
            s["key"] = (s["symbol"], s["date"], sg["strategy"])
        self.base = {s["key"]: self.sim(s, {}) for s in self.sigs}

    def costs(self, s):
        return self.bt.costs_ext if s["ext"] else self.bt.costs

    def sim(self, s, v: dict):
        d = {k: val for k, val in s["sig"].items() if k in _SIG_FIELDS}
        if "cap" in v:
            lim = s["ref"] * v["cap"] / 100
            if d["side"] * (s["ref"] - d["stop"]) > lim:
                d["stop"] = s["ref"] - d["side"] * lim
        for k in ("be_at_r", "trail_r", "trail_after_r", "scale_out_r", "scale_out_frac"):
            if k in v:
                d[k] = v[k]
        if "exit_by" in v:
            d["exit_by"] = t(v["exit_by"])
        late = (t(v["late"][0]), v["late"][1]) if "late" in v else None
        key = (s["symbol"], s["date"])
        return simulate2(Signal(**d), self.bars[key], self.bt.flatten, self.costs(s), gb=v.get("gb"),
                         lock=v.get("lock"), late=late, _arr=self.arr[key])

    def verify(self) -> int:
        bad = 0
        for s in self.sigs:
            d = {k: val for k, val in s["sig"].items() if k in _SIG_FIELDS}
            a = simulate(Signal(**d), self.bars[(s["symbol"], s["date"])], self.bt.flatten, self.costs(s))
            b = self.base[s["key"]]
            if (a is None) != (b is None) or (a is not None and (abs(a.r_multiple - b.r_multiple) > 1e-9
                                                                  or a.exit_reason != b.exit_reason)):
                bad += 1
        return bad

    def portfolio(self, v: dict, setup: str | None) -> pd.DataFrame:
        """Allocate all setups' trades with the production allocator; variant v applied to `setup` (None = all)."""
        cands, orig_stop = [], {}
        for s in self.sigs:
            tr = self.sim(s, v) if (v and (setup is None or s["sig"]["strategy"] == setup)) else self.base[s["key"]]
            if tr is None:
                continue
            tr = copy.copy(tr)
            cands.append(tr)
            orig_stop[s["key"]] = s["sig"]["stop"]
        df = self.bt.allocate(cands)
        df["date"] = df["date"].astype(str)
        os_ = np.array([orig_stop[(r.symbol, r.date, r.strategy)] for r in df.itertuples()])
        df["r0"] = df["pnl"] / (df["shares"] * (df["entry"] - os_).abs())   # original R units (R-unit trap guard)
        df["ret_pct"] = df["side"] * (df["exit"] / df["entry"] - 1) * 100
        df["mae_pct"] = df["mae_r"] * (df["entry"] - df["stop"]).abs() / df["entry"] * 100
        df["notional"] = df["shares"] * df["entry"]
        df["split"] = np.where(df["date"] <= TRAIN_END, "train", "valid")
        return df


def compare(df: pd.DataFrame, base: pd.DataFrame, setup: str | None, split: str) -> dict:
    a = df[df.split == split]; b = base[base.split == split]
    if setup:
        a, b = a[a.strategy == setup], b[b.strategy == setup]
    days = sorted(set(b.date) | set(a.date))
    da = a.groupby("date")[["r0", "pnl"]].sum().reindex(days, fill_value=0)
    db = b.groupby("date")[["r0", "pnl"]].sum().reindex(days, fill_value=0)
    dd = da - db
    n = max(len(b), 1)
    def tstat(x):
        x = x.to_numpy(); s = x.std(ddof=1)
        return float(x.mean() / s * np.sqrt(len(x))) if len(x) > 1 and s > 0 else 0.0
    return {"n": int(len(a)), "n_base": int(len(b)), "days": len(days),
            "exp_r0": round(float(a.r0.mean()), 4) if len(a) else None,
            "base_exp_r0": round(float(b.r0.mean()), 4) if len(b) else None,
            "d_r0": round(float(dd.r0.sum() / n), 4), "d_r0_t": round(tstat(dd.r0), 2),
            "d_r0_ex_best": round(float((dd.r0.sum() - dd.r0.max()) / n), 4) if len(dd) else 0.0,
            "pnl": round(float(a.pnl.sum()), 0), "base_pnl": round(float(b.pnl.sum()), 0),
            "d_pnl": round(float(dd.pnl.sum()), 0), "d_pnl_t": round(tstat(dd.pnl), 2),
            "d_pnl_ex_best": round(float(dd.pnl.sum() - dd.pnl.max()), 0) if len(dd) else 0.0,
            "win": round(float((a.pnl > 0).mean()), 3) if len(a) else None,
            "base_win": round(float((b.pnl > 0).mean()), 3) if len(b) else None,
            "worst_ret_pct": round(float(a.ret_pct.min()), 2) if len(a) else None}


def recovery_table(base: pd.DataFrame) -> list[dict]:
    """MarcoFlow-style question on our own trades: once a trade is down >= x%, how does it finish?"""
    rows = []
    for setup in [None] + SETUPS:
        b = base if setup is None else base[base.strategy == setup]
        for x in (0.5, 0.75, 1.0, 1.5, 2.0, 3.0):
            hit = b[b.mae_pct <= -x]
            if not len(hit):
                rows.append({"setup": setup or "ALL", "x": x, "n": 0}); continue
            rows.append({"setup": setup or "ALL", "x": x, "n": int(len(hit)), "of": int(len(b)),
                         "closed_green": round(float((hit.ret_pct > 0).mean()), 3),
                         "mean_final_pct": round(float(hit.ret_pct.mean()), 3),
                         "hold_vs_exit_at_x_pct": round(float(hit.ret_pct.mean() + x), 3),
                         "se": round(float(hit.ret_pct.std(ddof=1) / np.sqrt(len(hit))), 3) if len(hit) > 1 else None})
    return rows


def main():
    lab = Lab()
    bad = lab.verify()
    print(f"simulate2 vs engine.simulate mismatches: {bad} of {len(lab.sigs)}", flush=True)
    assert bad == 0
    base = lab.portfolio({}, None)
    res = {"n_signals": len(lab.sigs), "verify_mismatch": bad, "configs": [], "baseline": {}}
    for sp in ("train", "valid"):
        res["baseline"][sp] = {st: compare(base, base, st, sp) for st in [None] + SETUPS}
    res["slot_bound_frac"] = round(float((base.notional >= 0.9 * 1930).mean()), 3)
    res["stop_pct_quantiles"] = {st: base[base.strategy == st].eval("abs(entry-stop)/entry*100").quantile(
        [0.1, 0.5, 0.9, 0.99]).round(2).tolist() for st in SETUPS}
    res["recovery"] = recovery_table(base)
    # (1) % caps: portfolio-wide (one config each), reported per setup and for the portfolio
    for x in CAPS:
        df = lab.portfolio({"cap": x}, None)
        capped = sum(1 for s in lab.sigs if s["sig"]["side"] * (s["ref"] - s["sig"]["stop"]) > s["ref"] * x / 100)
        row = {"id": f"cap={x}%", "family": "cap", "capped_signals": capped,
               "train": {st or "ALL": compare(df, base, st, "train") for st in [None] + SETUPS},
               "valid": {st or "ALL": compare(df, base, st, "valid") for st in [None] + SETUPS}}
        res["configs"].append(row)
        print(row["id"], "ALL train", row["train"]["ALL"], "\n   valid", row["valid"]["ALL"], flush=True)
    # (2) give-back grid, one setup at a time
    for st in SETUPS:
        grid = grid_for(st)
        for c in grid:
            v = {k: val for k, val in c.items() if k not in ("id", "family", "setup")}
            df = lab.portfolio(v, st)
            c2 = dict(c)
            c2["train"] = compare(df, base, st, "train")
            c2["valid"] = compare(df, base, st, "valid")
            c2["portfolio_train"] = compare(df, base, None, "train")
            c2["portfolio_valid"] = compare(df, base, None, "valid")
            res["configs"].append(c2)
            print(c2["id"], "dR0 tr", c2["train"]["d_r0"], c2["train"]["d_r0_t"], "va", c2["valid"]["d_r0"],
                  c2["valid"]["d_r0_t"], flush=True)
        # plateau / gate after the setup's grid is complete
        done = {c["id"]: c for c in res["configs"] if c.get("setup") == st}
        for c in grid:
            r = done[c["id"]]
            nb = [done[g["id"]] for g in neighbours(c, grid)]
            r["neighbours"] = [g["id"] for g in nb]
            r["plateau"] = bool(nb) and all(g["train"]["d_r0"] > 0 for g in nb)
            r["pass"] = (r["train"]["d_r0"] >= 0.03 and r["valid"]["d_r0"] >= 0.03 and r["train"]["d_r0_t"] >= 1.0
                         and r["train"]["d_r0_ex_best"] > 0 and r["valid"]["d_r0_ex_best"] > 0
                         and r["train"]["d_pnl"] > 0 and r["valid"]["d_pnl"] > 0 and r["plateau"])
    res["n_configs"] = len(res["configs"])
    json.dump(res, open(f"{OUT}/results.json", "w"), indent=1, default=str)
    base.to_csv(f"{OUT}/data/baseline_trades.csv", index=False)
    print("configs:", res["n_configs"], "pass:", [c["id"] for c in res["configs"] if c.get("pass")])


if __name__ == "__main__":
    main()
