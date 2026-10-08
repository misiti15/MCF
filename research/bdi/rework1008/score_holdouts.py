"""One-time locked-holdout scoring of the 8 rework finalists of 2026-10-08 (production costs, as
research/owner1008/score_holdouts.py). ADV = mean RTH $ volume of the prior 20 sessions (min 5) from the 1-minute
cache of each period, so the 150M tiers are applied as live min_adv would. Educational only - not financial advice."""
import importlib.util, json, re, sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.argv += [] if len(sys.argv) > 1 else ["lab2_locked"]
exec(compile(Path("research/owner1008/score_holdouts.py").read_text().split("LOCK = Path")[0], "sh", "exec"))  # prod/score only


def adv(cache):
    out = []
    for f in sorted(Path(cache).glob("*.parquet")):
        d = pd.read_parquet(f, columns=["close", "volume"])
        idx = pd.DatetimeIndex(d.index).tz_convert("America/New_York")
        hm = idx.hour * 100 + idx.minute
        rth = (hm >= 930) & (hm < 1600)
        dv = (d["close"] * d["volume"])[rth].groupby(idx[rth].date).sum()
        a = dv.shift(1).rolling(20, min_periods=5).mean()
        out.append(pd.DataFrame({"symbol": f.stem, "date": list(a.index), "adv": a.to_numpy()}))
    return pd.concat(out)


LOCK = Path(sys.argv[1])
CACHE = {"test": "data/cache/1Min", "holdout_q2": "data/cache_q2/1Min"}
mods = sorted(Path("research/bdi/rework1008/modules").glob("RW*.py"))
out = {}
for s in ("test", "holdout_q2"):
    f = pd.read_parquet(LOCK / f"{s}.parquet").sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
    f["date"] = pd.to_datetime(f["date"]).dt.date
    f = f.merge(adv(CACHE[s]), on=["symbol", "date"], how="left")
    for p in mods:
        spec = importlib.util.spec_from_file_location(p.stem.replace("-", "_"), p)
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        mn = float(re.search(r"min_adv (\d+)", p.read_text()).group(1))
        mk = np.asarray(m.mask(f), bool)
        if mn > 95e6:   # the lab frames already hold the 95M universe; higher tiers need ADV (unknown ADV -> excluded)
            mk &= f["adv"].fillna(0).to_numpy() >= mn
        out.setdefault(p.stem, {})[s] = score(f, mk, m.SIDE, m.GEOM)
        print(s, p.stem, {k: out[p.stem][s].get(k) for k in ("n", "days", "exp_r", "t", "win_rate", "ex_best_day")}, flush=True)
json.dump(out, open("research/bdi/rework1008/holdouts.json", "w"), indent=1, default=str)
