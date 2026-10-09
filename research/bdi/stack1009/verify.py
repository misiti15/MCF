"""Stack study step 4: run each candidate module's mask(df) on the raw 2-year frames month by month (as the rescore
does: adv20 >= 95M, first qualifying bar per symbol-day, production costs) and compare with the scan numbers.
Also runs mask on a single symbol-day without symbol/date columns (live-frame shape) to check it agrees.
Writes verify.json. Educational only - not financial advice."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402


def load(p):
    spec = importlib.util.spec_from_file_location(p.stem.replace("-", "_"), p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    cands = json.load(open(HERE / "candidates.json"))
    mods = {c["id"]: load(HERE / "modules" / f"{c['id']}.py") for c in cands}
    trades = {k: [] for k in mods}
    live_ok = {k: [0, 0] for k in mods}
    for mo in lib.months():
        cols = ["close", "rsi", "rsi5", "emaDiff", "macdPct", "volumeRatio", "vwapDistPct", "buyPressure", "gap",
                "fromOpen", "tod", "atr_d", "dist_pdh_atr", "dist_pdl_atr", "dist_hod_atr", "dist_lod_atr",
                "sma20_dist_pct", "sma50_dist_pct", "sma20_slope_pct", "flow3", "symbol", "date", "adv20"]
        cols += [f"{k}_{s}_{g}" for s in ("long", "short") for g in ("t1s1", "t05s1", "t1s05") for k in ("r", "win")]
        df = lib.load_month(mo, cols)
        df = df[(df.tod >= 950) & (df.tod <= 1500) & (df.adv20 >= 95e6)].reset_index(drop=True)
        for k, m in mods.items():
            msk = m.mask(df)
            trades[k].append(gates.lab_trades(df, msk, m.SIDE, m.GEOM))
        # live-shape check on 40 random symbol-days
        sdk = df["symbol"].astype(str) + "|" + df["date"].astype(str)
        rng = np.random.default_rng(1)
        for key in rng.choice(sdk.unique(), 40, replace=False):
            sub = df[sdk == key]
            one = sub.drop(columns=["symbol", "date"]).reset_index(drop=True)
            for k, m in mods.items():
                a, b = m.mask(sub), m.mask(one)
                live_ok[k][0] += int((a == b).all())
                live_ok[k][1] += 1
        print(mo, flush=True)
    regs = lib.regimes()
    out = {}
    for c in cands:
        t = pd.concat(trades[c["id"]])
        s = gates.summary(t)
        rg = gates.regime_split(t, regs)
        out[c["id"]] = {"module": s, "scan": c["row"], "up": rg["up"].get("exp_r"), "down": rg["down"].get("exp_r"),
                        "live_shape_match": f"{live_ok[c['id']][0]}/{live_ok[c['id']][1]}"}
        print(c["id"], s["n"], s["exp_r"], s["t"], "scan", c["row"]["n"], c["row"]["exp"], c["row"]["t"], out[c["id"]]["live_shape_match"])
    json.dump(out, open(HERE / "verify.json", "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
