"""GEN exposure 2026-10-25: the screen's qualifying rows per setup, for matching against the replay and for refire.

    python research/ops/genexposure1025_rows.py OUT_PREFIX 2026-08 2026-09 2026-10

Per GEN setup with a `gen.spec` (config/account_gen.yaml), on each month's generator panel (mcf.research.generator):
  OUT_PREFIX_first.csv   the screen's trades: first qualifying 5-minute bar per symbol-day (setup, symbol, date, tod)
  OUT_PREFIX_refire.csv  per setup and date: first-bar signals vs the refire chain (LabStrategy refire, cooldown 1:
                         every qualifying decision bar fires unless the previous emitted signal was the bar before;
                         mcf.strategies.setups.refire_select) - what `refire: true` would add, same rows, same R model
                         not evaluated here (counts only).
Research only; nothing here trades. Educational only - not financial advice.
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import yaml

from mcf.research.generator.apply import spec_from_cfg
from mcf.research.generator.data import Panel, build_month
from mcf.research.generator.screen import first_rows, spec_mask_idx
from mcf.strategies.setups import refire_select


def main(prefix: str, months: list[str]) -> None:
    st = yaml.safe_load(open("config/account_gen.yaml"))["strategies"]
    specs = {n: spec_from_cfg(v) for n, v in st.items() if isinstance(v, dict) and (v.get("gen") or {}).get("spec")}
    first, refire = [], []
    for m in months:
        P = Panel([build_month(m)], [m])
        tod = P.a["tod"].astype(np.int64)
        barno = (tod // 100) * 12 + (tod % 100) // 5          # 5-minute bar number within the day
        for name, sp in specs.items():
            idx = spec_mask_idx(P, sp)
            r = P.a[f"r_{sp.side}_{sp.geom}"][idx].astype(np.float64)
            idx = idx[np.isfinite(r)]
            f = first_rows(P.sd, spec_mask_idx(P, sp))      # as screen.evaluate: first row, then finite R
            f = f[np.isfinite(P.a[f"r_{sp.side}_{sp.geom}"][f].astype(np.float64))]
            first.append(pd.DataFrame({"setup": name, "symbol": P.sym_names[P.sym_codes[f]],
                                       "date": P.days[P.day[f]], "tod": tod[f]}))
            sd = P.sd[idx]
            cuts = np.flatnonzero(np.r_[True, sd[1:] != sd[:-1]]) if len(idx) else np.empty(0, np.int64)
            n_ref = np.zeros(len(cuts), np.int64)
            for j, (a, b) in enumerate(zip(cuts, np.r_[cuts[1:], len(idx)])):
                n_ref[j] = len(refire_select(barno[idx[a:b]], 1))
            day = P.days[P.day[idx[cuts]]]
            c = pd.DataFrame({"date": day, "first": 1, "refire": n_ref}).groupby("date").sum()
            c = c.reindex(sorted(P.days), fill_value=0)
            refire.append(c.reset_index().assign(setup=name))
        print(m, "done", flush=True)
        del P
    pd.concat(first).to_csv(prefix + "_first.csv", index=False)
    pd.concat(refire).to_csv(prefix + "_refire.csv", index=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
