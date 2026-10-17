"""Kernel parity: kern.py at the parent parameters vs research/bdi/cwt/live/cwt_live_lib.py (the live signal code) on
the live-like frame, every frame row 09:50-15:00, two open months, first 200 $95M symbols (python loops are slow).
-> parity.json. Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build as B  # noqa: E402

L = B.L
out = {}
for m in ("2025-06", "2026-03"):
    f, P, _ = B.month_frame(m)
    big = sorted(set(f.loc[f.adv20 >= 95e6, "symbol"]))[:200]
    P = P[P.symbol.isin(big)].reset_index(drop=True)
    x, E = B.kernels(P)
    keep = (P["_fi"].to_numpy() >= 0) & (x.tod >= 950) & (x.tod <= 1500)
    chk = {}
    for bi, (a, dt, tg) in enumerate(B.B1V):
        if dt == 0.4 and a in (1.5, 2.5):
            chk[f"b1 a{a} trig{tg}"] = (L.b1(P, a, tg), (E["b1bits"] >> bi) & 1 == 1)
    for z in (0.5, 0.75):
        with np.errstate(invalid="ignore"):
            chk[f"b2 z{z} short"] = (L.b2(P, z, "short"), E["b2zs"] >= z)
            chk[f"b2 z{z} long"] = (L.b2(P, z, "long"), E["b2zl"] >= z)
    for k in (4, 6):
        chk[f"b4a k{k}"] = (L.b4a(P, k), E[f"b4a{k}"] >= 3)
    with np.errstate(invalid="ignore"):
        chk["b4b s1"] = (L.b4b(P, 1.0), (E["b4bpush"] >= 1.0) & (E["b4bd"] >= 0.3) & (E["b4bd"] <= 0.5))
    for bi, (mm, v) in enumerate(B.B5V):
        if mm in (0.5, 0.75) and v in (3, 5):
            chk[f"b5 m{mm} v{v}"] = (L.b5(P, mm, v), (E["b5bits"] >> bi) & 1 == 1)
    for g in (5, 10):
        for tg in (1, 2):
            mine = (E["a7t1"] if tg == 1 else E["a7t2"]) & (x.gap <= -g)
            chk[f"a7 g{g} trig{tg}"] = (L.a7(P, g, tg), mine)
    out[m] = {}
    for k, (ref, mine) in chk.items():
        ref, mine = np.asarray(ref, bool) & keep, np.asarray(mine, bool) & keep
        out[m][k] = {"ref": int(ref.sum()), "mine": int(mine.sum()), "both": int((ref & mine).sum())}
        print(m, k, out[m][k], flush=True)
json.dump(out, open(HERE / "parity.json", "w"), indent=1)
