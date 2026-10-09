"""Rule-6 baselines for each candidate (same side, window, population, exit): (a) one random bar per symbol-day in the
window (seed 1009), (b) the big-move layer alone (the candidate's fromOpen filter, first bar per symbol-day), so the
stack is compared with what the move-from-open condition gives by itself. Writes baseline.json.
Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scan as S  # noqa: E402


def stats(idx, side, geom):
    r = S.B[f"p_{side}_{geom}"][idx].astype(float)
    ok = np.isfinite(r)
    r, day = r[ok], S.B["day"][idx][ok]
    rc = S.REGC[day]
    return {"n": int(len(r)), "exp": round(float(r.mean()), 4), "t": round(S.tstat(r, day), 2),
            "exp_up": round(float(r[rc == 1].mean()), 4), "exp_down": round(float(r[rc == -1].mean()), 4)}


def first(m):
    idx = np.flatnonzero(m)
    s = S.SD[idx]
    return idx[np.r_[True, s[1:] != s[:-1]]]


def main():
    out = {}
    rng = np.random.default_rng(1009)
    for c in json.load(open(HERE / "candidates.json")):
        side, geom, lo, hi = c["side"], c["geom"], c["lo"], c["hi"]
        s = 1 if side == "long" else -1
        w = (S.TOD >= lo) & (S.TOD <= hi)
        idx = np.flatnonzero(w)
        perm = idx[rng.permutation(len(idx))]
        _, firsts = np.unique(S.SD[perm], return_index=True)
        rand = np.sort(perm[firsts])
        res = {"random_bar": stats(rand, side, geom)}
        fo = [f for f in c["filters"] if f[0] in ("fo_with", "fo_against")]
        if fo:
            n, p = fo[0]
            x = S.B["fromOpen"].astype(float)
            with np.errstate(invalid="ignore"):
                m = (s * x > p) if n == "fo_with" else (s * x < -p)
            res[f"{n}{p}_alone"] = stats(first(m & w), side, geom)
        out[c["id"]] = res
        print(c["id"], res, flush=True)
    json.dump(out, open(HERE / "baseline.json", "w"), indent=1)


if __name__ == "__main__":
    main()
