"""Parity: run each module's mask(df) on the raw open frames (month by month) through mcf.research.gates.lab_trades and
compare with the scan numbers. Educational only - not financial advice."""
import importlib.util, json, sys
from pathlib import Path
import pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2])); sys.path.insert(0, str(HERE / "modules"))
from mcf.research import gates
from research.history2y import lib
MODS = {"NM-HL-T75-pm-t05s1-long": 125e6, "NM-HL-atrhi-fri-midday-t05s1-long": 125e6, "NM-HS-fo1-mon-open-t05s1-short": 125e6}
COLS = ["symbol", "date", "tod", "close", "atr_d", "adv20", "fromOpen", "gap", "atrPct", "rsiHeat", "priceActionHeat",
        "momentumHeat", "vwapHeat"] + [f"{k}_{s}_{g}" for s in ("long", "short") for g in ("t1s1", "t05s1", "t1s05") for k in ("r", "win")]
mods = {}
for k in MODS:
    sp = importlib.util.spec_from_file_location(k, HERE / "modules" / f"{k}.py"); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); mods[k] = m
tr = {k: [] for k in MODS}
for mo in lib.months():
    d = lib.load_month(mo, COLS)
    for k, m in mods.items():
        e = d[d.adv20 >= MODS[k]].reset_index(drop=True)
        tr[k].append(gates.lab_trades(e, m.mask(e), m.SIDE, m.GEOM))
out = {}
for k in MODS:
    t = pd.concat(tr[k]); t["split"] = (pd.to_datetime(t.date) < "2026-01-01").map({True: "train", False: "valid"})
    out[k] = {s: {"n": int(len(x)), "exp_r": round(float(x.r.mean()), 4)} for s, x in t.groupby("split")}
    out[k]["all"] = gates.summary(t)
print(json.dumps(out, indent=1)); json.dump(out, open(HERE / "verify.json", "w"), indent=1)
