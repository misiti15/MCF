"""Part A finalists: terminal account equity ($100k, $500 buys of SPXL, hold, idle cash in T-bills) for the dip rule vs
every schedule offset and 200 random-day draws -- the "final dollars" view next to XIRR.
Usage: python partA_terminal.py DAILY.parquet OUTDIR. Educational only - not financial advice."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ETFS  # noqa: E402
from partA import FAM_D, FAM_M, daily_triggers, load_daily, minute_fills, outcomes  # noqa: E402
from partA_checks import FINALISTS  # noqa: E402

RNG = np.random.default_rng(11173)
D, E0, CPS, BPS = 500.0, 100_000.0, 0.01, 1e-4


def terminal(bi, px, close_last, bil_growth_to_end):
    """Terminal equity: E0 compounding in T-bills, minus each D at its date (with its forgone T-bill growth),
    plus the slice's liquidation value at the end."""
    sh = D / (px[bi] * (1 + BPS) + CPS)
    val = (sh * (close_last * (1 - BPS) - CPS)).sum()
    return E0 * bil_growth_to_end[0] - (D * bil_growth_to_end[bi]).sum() + val


def main(daily_path, outdir):
    d = load_daily(daily_path)
    rows = []
    for seg in ["A", "B"]:
        idx, trig = daily_triggers(d, seg)
        closes = {s: d["close"][s].reindex(idx) for s in ETFS}
        bil = d["close"]["BIL"].reindex(idx).values
        g = bil[-1] / bil                                     # T-bill growth from each date to the end
        fills = {"open": {s: d["open"][s].reindex(idx).values for s in ETFS},
                 "close": {s: closes[s].values for s in ETFS}}
        if seg == "B":
            spy_px, pcs, mf = minute_fills(d, idx)
            for k in FAM_M:
                trig[(k, 0.01)] = (spy_px[k] <= pcs * 0.99).fillna(False).values.astype(bool)
                fills[k] = {s: mf[(k, s)] for s in ETFS}
        for fam, x in FINALISTS:
            if fam.startswith("m_") and seg == "A":
                continue
            ft = FAM_D.get(fam, fam)
            ok = np.isfinite(fills[ft]["SPY"]) & np.isfinite(fills[ft]["SPXL"])
            pool = np.nonzero(ok)[0]
            b = np.nonzero(trig[(fam, x)] & ok)[0]
            k = max(1, len(pool) // len(b))
            for s in ("SPXL", "SPY"):
                px, cl = fills[ft][s], closes[s].values[-1]
                rule = terminal(b, px, cl, g)
                sch = np.array([terminal(pool[o::k][:len(b)], px, cl, g) for o in range(k) if len(pool[o::k][:len(b)]) == len(b)])
                rnd = np.array([terminal(np.sort(RNG.choice(pool, len(b), replace=False)), px, cl, g) for _ in range(200)])
                rows.append(dict(seg=seg, family=fam, x=x, instr=s, n_buys=len(b), deployed=D * len(b),
                                 terminal_rule=rule, terminal_sched_mean=sch.mean(), sched_pct_beaten=(rule > sch).mean(),
                                 terminal_rand_mean=rnd.mean(), rand_pct_beaten=(rule > rnd).mean(),
                                 spy_bh_terminal=E0 * closes["SPY"].values[-1] / closes["SPY"].values[0],
                                 cash_only_terminal=E0 * g[0]))
    pd.DataFrame(rows).to_csv(Path(outdir) / "partA_terminal.csv", index=False, float_format="%.6g")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
