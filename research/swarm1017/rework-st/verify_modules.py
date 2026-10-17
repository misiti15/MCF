"""Run each candidate module's own mask over every open month (frames + SPY fromOpen merged as 'spy_fo'), select trades as
the live runner would (min_adv, window, first bar or refire cd1) and compare with the scan. Educational only - not
financial advice."""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from mcf.research.gates import prod_r  # noqa: E402
from mcf.strategies.setups import refire_select  # noqa: E402
from research.history2y import lib  # noqa: E402

idx = json.load(open(HERE / "modules/index.json"))
mods = {}
for name in idx:
    spec = importlib.util.spec_from_file_location(name, HERE / "modules" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    mods[name] = m
rows = {n: [] for n in idx}
for mo in lib.months():
    d = lib.load_month(mo)
    spy = d.loc[d.symbol == "SPY", ["date", "tod", "fromOpen"]].rename(columns={"fromOpen": "spy_fo"})
    d = d.merge(spy, on=["date", "tod"], how="left")
    d = d.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    for n, m in mods.items():
        meta = idx[n]
        g, s = m.GEOM, m.SIDE
        ok = (d.adv20.to_numpy(float) >= meta["min_adv"]) & (d.atr_d.to_numpy(float) > 0) & np.isfinite(d[f"r_{s}_{g}"].to_numpy(float))
        tod = d.tod.to_numpy()
        ok &= (tod >= meta["window"][0]) & (tod <= meta["window"][1])
        if meta.get("prefilter"):
            ok &= d.gap.to_numpy(float) <= float(meta["prefilter"].split(":")[1])
        hit = np.flatnonzero(np.asarray(m.mask(d), bool) & ok)
        if not len(hit):
            continue
        key = d.symbol.to_numpy()[hit].astype(str) + "|" + d.date.astype(str).to_numpy()[hit]
        sel = []
        for k in pd.unique(key):
            h = hit[key == k]
            if meta.get("refire"):
                bi = ((tod[h] // 100) * 60 + tod[h] % 100 - 570) // 5
                sel += [h[np.searchsorted(bi, b)] for b in refire_select(bi.tolist(), meta.get("refire_cooldown", 1))]
            else:
                sel.append(h[0])
        sel = np.array(sel)
        r = prod_r(d[f"r_{s}_{g}"].to_numpy(float)[sel], d[f"win_{s}_{g}"].to_numpy(float)[sel], d.close.to_numpy(float)[sel],
                   d.atr_d.to_numpy(float)[sel], g, tod=tod[sel].astype(float))
        rows[n].append(pd.DataFrame({"date": d.date.to_numpy()[sel], "r": r}))
    print(mo, {n: sum(len(x) for x in v) for n, v in rows.items()}, flush=True)
    del d
out = {}
for n, v in rows.items():
    t = pd.concat(v)
    tr = pd.to_datetime(t.date) < "2026-01-01"
    out[n] = {"n": len(t), "exp": round(float(t.r.mean()), 4), "n_tr": int(tr.sum()), "exp_tr": round(float(t.r[tr].mean()), 4),
              "n_va": int((~tr).sum()), "exp_va": round(float(t.r[~tr].mean()), 4)}
print(out)
json.dump(out, open(HERE / "verify_modules.json", "w"), indent=1)
