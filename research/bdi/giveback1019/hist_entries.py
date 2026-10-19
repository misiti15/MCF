"""Step 5a: entries of the 12 Primary lab setups (config/default.yaml, enabled) on the history2y 5-min lab frames, open
months only (lib.load_month refuses the locked block 2024-11..2025-02). First qualifying bar per symbol-day.
Writes <scratch>/hist_entries.parquet. Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path("/home/user/MCF")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
from lib import load_month, months  # noqa: E402
from mcf.research import gates as G  # noqa: E402
from mcf.research.timeframes import load_module  # noqa: E402
from common import S  # noqa: E402

cfg = yaml.safe_load((ROOT / "config/default.yaml").read_text())["strategies"]
SET = {k: v for k, v in cfg.items() if v.get("enabled") and v.get("type") == "lab"}
mods = {k: load_module(v["module"]) for k, v in SET.items()}
rows = []
for mo in months():
    df = load_month(mo)
    tod, adv = df["tod"].to_numpy(), df["adv20"].fillna(0).to_numpy()
    for k, v in SET.items():
        m = mods[k]
        side, geom = m.SIDE, getattr(m, "GEOM", "t1s1")
        lo, hi = v.get("window") or (950, 1500)
        base = (tod >= max(950, lo)) & (tod <= min(1500, hi)) & (adv >= float(v.get("min_adv", 0)))
        with np.errstate(invalid="ignore"):
            mk = np.asarray(m.mask(df), bool) & base & np.isfinite(df[f"r_{side}_{geom}"].to_numpy(float)) & (df["atr_d"].to_numpy(float) > 0)
        idx = G.first_per_symbol_day(df["symbol"].to_numpy(), df["date"].to_numpy(), mk)
        if not len(idx):
            continue
        x = df.iloc[idx][["date", "symbol", "tod", "close", "atr_d"]].copy()
        x["setup"], x["side"], x["geom"] = k, side, geom
        x["frame_r"] = G.prod_r(df[f"r_{side}_{geom}"].to_numpy(float)[idx], df[f"win_{side}_{geom}"].to_numpy(float)[idx],
                                x.close.to_numpy(float), x.atr_d.to_numpy(float), geom, tod=x.tod.to_numpy(float))
        rows.append(x)
    print(mo, len(df), sum(len(r) for r in rows), flush=True)
    del df
E = pd.concat(rows, ignore_index=True)
E["symbol"] = E.symbol.astype(str)
E.to_parquet(S / "hist_entries.parquet", index=False)
print(E.groupby("setup").size())
