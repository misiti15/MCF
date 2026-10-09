"""Verify the RD modules reproduce the scan (research/bdi/reddit/modules): module mask on the lab rows -> trades
(first per symbol-day, 09:50-15:00) -> compare row indices and production R with the engine's configuration; then
the live shape: on random symbol-days without symbol/date columns the mask equals the full-frame mask.
Writes verify.json. Educational only - not financial advice."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import engine as E  # noqa: E402
import strategies as S  # noqa: E402

MODS = {"RD1-gapgo-lodbreak-rvol-short-FD": ("R04-gap-go", ("rvol",)),
        "RD2-gapfill-openloss-rvol-slope-short-FD": ("R05-gap-fill", ("rvol", "trend")),
        "RD3-vwapfade-band1-slope-inplay-long-FD": ("R03-vwap-fade", ("trend", "inplay"))}
COLS = ["close", "atr_d", "gap", "fromOpen", "volumeRatio", "sma20_slope_pct", "vwapDistPct", "dist_lod_atr", "tod"]


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / "modules" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    D = E.Data()
    df = pd.DataFrame({k: D.B[k].astype(float) for k in COLS})
    df["symbol"] = D.B["sym"]
    df["date"] = D.B["day"]
    rng = np.random.default_rng(1009)
    starts = np.flatnonzero(D.new)
    ends = np.r_[starts[1:], len(D.c)]
    vf = HERE / "verify.json"
    out = json.load(open(vf)) if vf.exists() else {}
    only = sys.argv[1:]
    for name, (strat, fs) in MODS.items():
        if only and name not in only:
            continue
        mod = load(name)
        m_mod = mod.mask(df)
        fn, p, grid, key = S.STRATS[strat]
        s = 1 if mod.SIDE == "long" else -1
        o = fn(D, s, p)
        m_eng = o["ev"].copy()
        for f in fs:
            m_eng &= S.filt(D, f, s)
        i1, r1 = E.trades(D, m_mod, mod.SIDE, mod.GEOM, None, None, 950, 1500)
        i2, r2 = E.trades(D, m_eng, mod.SIDE, mod.GEOM, None, None, 950, 1500)
        same = len(i1) == len(i2) and bool(np.array_equal(i1, i2))
        # live shape: symbol-days with a signal plus random ones
        pick = list(rng.choice(len(starts), 150, replace=False))
        sig_sd = np.unique(D.B["sd"][i1])[:150]
        pick += [int(np.searchsorted(D.B["sd"][starts], x)) for x in sig_sd]
        ok = 0
        for j in pick:
            a, b = starts[j], ends[j]
            sub = df.iloc[a:b][COLS].reset_index(drop=True)
            ok += bool(np.array_equal(mod.mask(sub), m_mod[a:b]))
        out[name] = {"module_n": len(i1), "scan_n": len(i2), "identical_trades": same,
                     "module_exp": round(float(r1.mean()), 4), "scan_exp": round(float(r2.mean()), 4),
                     "only_module": int(len(np.setdiff1d(i1, i2))), "only_scan": int(len(np.setdiff1d(i2, i1))),
                     "live_shape_checks": f"{ok}/{len(pick)}"}
        print(name, out[name], flush=True)
        json.dump(out, open(vf, "w"), indent=1)
        del m_mod, m_eng, o, i1, i2, r1, r2
        import gc
        gc.collect()


if __name__ == "__main__":
    main()
