"""SRC-VALUE (owner 2026-11-16 "src value, yes"): how well each non-live source predicted LATER live results.

For every setup with live trades, each source's per-setup avg R (from its own data window) is compared with the setup's
live avg R over trades dated AFTER that window (live run only, R after costs = pnl_adj / risk via mcf.costs.cost_r,
all accounts pooled). Sources (docs/GLOSSARY.md names):
  2-year screen    docs/live/sim_inputs.json sources.backtest (Setup Generator runs; open history to 2026-10-07)
  2-year backtest  research/history2y/rescore.csv (rule-19 re-score; history 2024-10-01..2026-10-07, locked block excluded)
  Session replay   docs/live/replay.json snapshot (2026-09-01..2026-10-21)
  Shadow           journal run kind 'shadow' (forward only; first day 2026-11-17, so no later live exists yet)
Reads only summary files and the journals - never bars, never the locked block 2024-11-01..2025-02-28.

  git fetch origin 'refs/heads/mcf-data*:refs/remotes/origin/mcf-data*'
  python research/src_value/score.py            # writes research/src_value/{src_value.csv, per_setup.csv, summary.json}
Educational only - not financial advice."""

from __future__ import annotations

import csv
import json
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from mcf.costs import cost_r                                  # noqa: E402
from mcf.research.shadow_calib import BRANCHES, family_of    # noqa: E402

OUT = ROOT / "research" / "src_value"
K_SHRINK = 20          # bias shrink: (src - live) x n / (n + K) - K = live trades for half credibility
MIN_LIVE = (10, 20)    # later-live trades per setup (primary 10, sensitivity 20)
B = 2000               # bootstrap resamples (setups)
RNG = np.random.default_rng(20261117)
SCREEN_END = BT_END = "2026-10-07"


def live_trades() -> tuple[pd.DataFrame, pd.DataFrame]:
    live, shadow = [], []
    for acct, br in BRANCHES.items():
        try:
            raw = subprocess.run(["git", "-C", str(ROOT), "show", f"origin/{br}:journal.db"], capture_output=True,
                                 check=True).stdout
        except subprocess.CalledProcessError:
            continue
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            f.write(raw)
            f.flush()
            con = sqlite3.connect(f.name)
            runs = pd.read_sql("SELECT id, kind FROM runs", con)
            for kind, sink in (("paper", live), ("shadow", shadow)):
                ids = runs.loc[runs.kind == kind, "id"].tolist()
                if not ids:
                    continue
                t = pd.read_sql("SELECT * FROM trades WHERE run_id=? AND exit_time IS NOT NULL", con,
                                params=[int(min(ids))])
                if len(t):
                    t["r"] = cost_r(t).astype(float)
                    t["account"] = acct
                    sink.append(t[["account", "strategy", "date", "r"]])
            con.close()
    cat = lambda x: pd.concat(x, ignore_index=True) if x else pd.DataFrame(columns=["account", "strategy", "date", "r"])
    return cat(live), cat(shadow)


def sources(live_names: set[str], shadow: pd.DataFrame) -> dict[str, dict]:
    """Variant -> {window_end, setups: {setup: (avg_r, n)}}."""
    out = {}
    si = json.loads((ROOT / "docs/live/sim_inputs.json").read_text())
    scr = {k: v["backtest"] for k, v in si["setups"].items() if "backtest" in v}
    out["2-year screen (avg R)"] = {"end": SCREEN_END, "setups": {k: (v["avg_r"], v["trades"]) for k, v in scr.items()}}
    out["2-year screen (valid R)"] = {"end": SCREEN_END, "setups": {k: (v["valid_r"], v["trades"]) for k, v in scr.items()
                                                                    if v.get("valid_r") is not None}}
    bt_exp, bt_un = {}, {}
    for r in csv.DictReader(open(ROOT / "research/history2y/rescore.csv")):
        if not r["exp_r"]:
            continue
        name = r["setup"]
        if " " in name:   # "RW3 bdi-rw-..." -> the base live setup "RW3-...-short" (no -FD / -WB / G1 / S variants)
            code = name.split()[0]
            m = [n for n in live_names if n.startswith(code + "-") and "-FD" not in n and "-WB" not in n]
            if len(m) != 1:
                continue
            name = m[0]
        bt_exp[name] = (float(r["exp_r"]), int(float(r["n"])))
        if r["unseen_exp"]:
            bt_un[name] = (float(r["unseen_exp"]), int(float(r["unseen_n"])))
    out["2-year backtest (exp R)"] = {"end": BT_END, "setups": bt_exp}
    out["2-year backtest (unseen exp R)"] = {"end": BT_END, "setups": bt_un}
    rp = json.loads((ROOT / "docs/live/replay.json").read_text())
    out["Session replay (snapshot)"] = {"end": rp["window"].split(" to ")[1],
                                        "setups": {k: (v["avg_r"], v["trades"]) for k, v in rp["setups"].items()}}
    sh_end = str(shadow["date"].max()) if len(shadow) else "9999-12-31"
    g = shadow.groupby("strategy")["r"] if len(shadow) else None
    out["Shadow"] = {"end": sh_end, "setups": {k: (float(v.mean()), len(v)) for k, v in g} if g is not None else {}}
    return out


def metrics(d: pd.DataFrame) -> dict:
    n = len(d)
    if n < 3:
        return {"n_setups": n}
    s, l, w = d.src.values, d.live.values, d.n_live.values

    def stats(i):
        ss, ll, ww = s[i], l[i], w[i]
        hit = float(np.mean(np.sign(ss) == np.sign(ll)))
        bias = float(np.mean((ss - ll) * ww / (ww + K_SHRINK)))
        den = float(np.sum(ww * ss))
        ratio = float(np.sum(ww * ll) / den) if abs(den) > 1e-9 else np.nan
        rho = spearmanr(ss, ll).statistic if len(set(ss)) > 1 and len(set(ll)) > 1 else np.nan
        naive = float(max(np.mean(ll < 0), np.mean(ll > 0)))
        return hit, bias, ratio, float(rho), naive

    pt = stats(np.arange(n))
    bs = np.array([stats(RNG.integers(0, n, n)) for _ in range(B)])
    ci = lambda j: [round(float(np.nanpercentile(bs[:, j], 2.5)), 3), round(float(np.nanpercentile(bs[:, j], 97.5)), 3)]
    return {"n_setups": n, "live_trades": int(w.sum()),
            "src_avg_r": round(float(np.mean(s)), 3), "live_avg_r": round(float(np.mean(l)), 3),
            "hit": round(pt[0], 3), "hit_ci": ci(0), "naive_hit": round(pt[4], 3),
            "bias_shrunk": round(pt[1], 3), "bias_ci": ci(1),
            "ratio": round(pt[2], 2) if pt[2] == pt[2] else None, "ratio_ci": ci(2),
            "spearman": round(pt[3], 3) if pt[3] == pt[3] else None, "spearman_ci": ci(3)}


def weight(m: dict) -> float:
    """Measured weight (pre-set rule): 0 unless the Spearman CI and the hit-rate CI both clear their bars
    (rho_lo > 0, hit_lo > naive hit); then rho_lo x clip(ratio_lo, 0, 1), capped at 0.35 (the calibrated replay tier)."""
    if m.get("n_setups", 0) < 8 or m.get("spearman_ci") is None:
        return 0.0
    if not (m["spearman_ci"][0] > 0 and m["hit_ci"][0] > m["naive_hit"]):
        return 0.0
    return round(min(0.35, m["spearman_ci"][0] * min(1.0, max(0.0, m["ratio_ci"][0]))), 3)


def main():
    live, shadow = live_trades()
    srcs = sources(set(live.strategy), shadow)
    rows, per_setup, configs = [], [], 0
    for name, src in srcs.items():
        for mn in MIN_LIVE:
            configs += 1
            later = live[live.date.astype(str) > src["end"]]
            g = later.groupby("strategy")["r"].agg(["mean", "size"])
            recs = [{"setup": k, "family": family_of(k), "src": v[0], "n_src": v[1],
                     "live": float(g.loc[k, "mean"]), "n_live": int(g.loc[k, "size"])}
                    for k, v in src["setups"].items() if k in g.index and g.loc[k, "size"] >= mn and v[0] == v[0]]
            d = pd.DataFrame(recs, columns=["setup", "family", "src", "n_src", "live", "n_live"])
            if mn == MIN_LIVE[0]:
                per_setup += [{"source": name, **r} for r in recs]
            d["group"] = d["family"].map(lambda f: (re.match(r"[A-Z]+", f) or [f])[0] + "*")   # MF1, MF2 -> MF*
            groups = [("ALL", d)] + [(f, x) for f, x in d.groupby("family") if len(x) >= 3] \
                + [(f, x) for f, x in d.groupby("group") if len(x) >= 3 and x["family"].nunique() > 1]
            for fam, x in groups:
                m = metrics(x)
                rows.append({"source": name, "window_end": src["end"], "min_live": mn, "family": fam, **m,
                             "weight": weight(m) if fam == "ALL" else None})
    OUT.mkdir(parents=True, exist_ok=True)
    flat = [{k: (f"{v[0]}..{v[1]}" if isinstance(v, list) else v) for k, v in r.items()} for r in rows]
    pd.DataFrame(flat).to_csv(OUT / "src_value.csv", index=False)
    pd.DataFrame(per_setup).round(4).to_csv(OUT / "per_setup.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps({"generated": pd.Timestamp.now(tz="America/New_York").isoformat()[:16],
                                                  "configurations": configs, "k_shrink": K_SHRINK, "bootstrap": B,
                                                  "live_last_day": str(live.date.max()),
                                                  "shadow_days": sorted(set(shadow.date.astype(str))),
                                                  "rows": rows}, indent=1))
    for r in flat:
        if r["family"] == "ALL":
            print(r)
    print("configurations:", configs)


if __name__ == "__main__":
    main()
