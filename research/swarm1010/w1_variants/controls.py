"""W1 amendment (2026-10-10, after section 2's first read): every probation passer uses the SMA100 layer, which is NaN
until today's 40th bar (live parity, ~12:50). Control: is it the SMA100 side or just the time? For each passer,
C1 = the same configuration without its SMA100 term but restricted to bars where SMA100 exists (time-only control),
C2 = the same with the SMA100 term flipped (above <-> below). Both are counted configurations (data/controls.csv).
Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import eng  # noqa: E402
import families as FM  # noqa: E402
from run import STAT_KEYS, _restore  # noqa: E402


def main():
    res = pd.read_csv(HERE / "results.csv")
    res["params"] = pd.read_csv(HERE / "data" / "params.csv")["params"]
    specs = {s["name"]: s for s in FM.all_specs()}
    D = eng.D()
    ok100 = np.isfinite(D.F("sma100"))
    rows = []
    for _, row in res[res["probation"]].iterrows():
        sp = specs[row["family"]]
        P = _restore(sp, json.loads(row["params"]))
        s = 1 if sp["side"] == "long" else -1
        ctl = []
        if P.get("ma") == "a100":
            ctl.append(("C1 time-only (no SMA100 side)", dict(P, ma=None), True))
            ctl.append(("C2 SMA100 side flipped (w100)", dict(P, ma="w100"), False))
        elif P.get("sma") == 100:
            ctl.append(("C1 time-only (SMA term dropped)", dict(P, sma=None), True))
            ctl.append(("C2 SMA100 side flipped", dict(P, sma=-100), False))
        for lab, Q, late in ctl:
            if Q.get("sma") == -100:      # flip: NS3/RW4 require SMA > 0; flipped = SMA100 < 0
                Q2 = dict(Q, sma=None)
                m = sp["fn"](D, Q2, s) & (D.F("sma100") < 0)
            else:
                m = sp["fn"](D, Q, s)
            m = FM.common(D, Q, s, m)
            if late:
                m = m & ok100
            idx, r = D.trades(m, sp["side"], Q["geom"], sp["min_adv"])
            st = D.stats(idx, r)
            rows.append({"family": row["family"], "passer": row["variant"], "control": lab}
                        | {k: st.get(k) for k in STAT_KEYS})
            print(rows[-1]["family"], row["variant"], lab, st["n"], round(st["exp"], 4), round(st["t"], 2),
                  round(st.get("exp_up", np.nan), 3), round(st.get("exp_down", np.nan), 3), flush=True)
    pd.DataFrame(rows).round(4).to_csv(HERE / "controls.csv", index=False)


if __name__ == "__main__":
    main()
