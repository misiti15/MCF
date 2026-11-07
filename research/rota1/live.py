"""ROTA1 live part (paper journals, all 7 accounts pooled by setup, same capping as the 2-year series):
(a) descriptive live walk-forward of the representative rule (W=10, qualify >= 15 trades) vs the static Primary set;
(b) rule vs Claude's Team vs Primary set on 11-05 / 11-06; (c) Monday 11-09: light-version flags + shadow picks.
Live = paper fills (rule 7). Post hoc / descriptive, n is tiny. Educational only — not financial advice.

    python research/rota1/live.py <scratch_dir>
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wf  # noqa: E402
from common import tstat, window_metrics  # noqa: E402

S = Path(sys.argv[1])
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]


def main():
    R = pd.read_parquet(S / "live_R.parquet"); N = pd.read_parquet(S / "live_N.parquet")
    setups = list(R.columns); dates = list(R.index)
    Rv, Nv = R.to_numpy(), N.to_numpy()
    st = [setups.index(s) for s in wf.PRIMARY if s in setups]
    wf.MINN = 15
    res = []
    # (a) live walk-forward, W=10 as the long window
    for h in (3, 5):
        cache = {}
        for i in range(10, len(dates) + 1):
            m = window_metrics(Rv, Nv, i, 10)
            cache[("L", 10, i)] = m
            cache[("S", i)] = window_metrics(Rv, Nv, i, 20)
        cfg = {"h": h, "L": 10, "score": "S2", "m": 0.20, "swaps": 1, "k": 8, "flag": 0}
        out, held, sw, book = wf.simulate(Rv, Nv, cfg, cache, 10, len(dates))
        static = Rv[10:][:, st].mean(1)
        res.append(f"| live h={h} | {len(out)} | {out.mean():+.3f} | {static.mean():+.3f} | {(out - static).mean():+.3f} "
                   f"| {tstat(out - static):.2f} | {len(sw)} |")
    # light version on live (demotion-only, 20-session window = all live so far)
    for h in (3, 5):
        out = np.zeros(len(dates) - 10); flagged_log = []
        for i in range(10, len(dates), h):
            f = wf.flagged(window_metrics(Rv, Nv, i, 20))
            act = [b for b in st if not f[b]]
            flagged_log += [(dates[i], setups[b]) for b in st if f[b]]
            hi = min(i + h, len(dates))
            out[i - 10:hi - 10] = Rv[i:hi][:, act].sum(1) / len(st)
        static = Rv[10:][:, st].mean(1)
        res.append(f"| live LIGHT h={h} | {len(out)} | {out.mean():+.3f} | {static.mean():+.3f} | {(out - static).mean():+.3f} "
                   f"| {tstat(out - static):.2f} | {len(flagged_log)} flags |")
    # (b) Team comparison
    team = {d: [p["id"] for p in json.load(open(ROOT / f"research/shadow_primary/picks/{d}.json"))["setups"]]
            for d in ("2026-11-06",)}
    tb = []
    for d in ("2026-11-05", "2026-11-06"):
        i = dates.index(d)
        m = window_metrics(Rv, Nv, i, 10); q = m["n"] >= 15
        sc = np.nan_to_num(wf.score_fn("S2", m, window_metrics(Rv, Nv, i, 20), q), nan=-9)
        rule = list(np.argsort(sc)[::-1][:8])
        tp = [setups.index(s) for s in team["2026-11-06"] if s in setups]
        tb.append(f"| {d} | {Rv[i, rule].mean():+.3f} | {Rv[i, tp].mean():+.3f} ({len(tp)}) | {Rv[i, st].mean():+.3f} |")
    # (c) Monday 11-09
    i = len(dates)
    mS = window_metrics(Rv, Nv, i, 20)
    f = wf.flagged(mS)
    mon = []
    for b in st:
        mon.append(f"| {setups[b]} | {int(mS['n'][b])} | {mS['avg'][b]:+.3f} | {mS['green'][b]:.2f} | {mS['wob'][b]:+.3f} "
                   f"| {mS['worst'][b]:+.2f} | {'FLAG (sit out)' if f[b] else 'keep'} |")
    m = window_metrics(Rv, Nv, i, 20); q = m["n"] >= 30
    mem = np.zeros(len(setups), bool); mem[st] = True
    sc = np.nan_to_num(wf.score_fn("S2", m, mS, q | mem), nan=-9)
    top = [(setups[j], round(sc[j], 3), int(m["n"][j]), round(m["wob"][j], 3)) for j in np.argsort(sc)[::-1][:10]]
    weakest = sorted([(setups[b], round(sc[b], 3)) for b in st], key=lambda x: x[1])[:3]
    txt = ["## live walk-forward (descriptive)", "| run | sessions | rule R/setup-session | static | diff | t | swaps |",
           "|---|---|---|---|---|---|---|", *res, "", "## rule vs Team vs Primary set (live R per setup-session)",
           "| day | rule (8) | Team (n) | Primary set |", "|---|---|---|---|", *tb, "",
           "## Monday 11-09 light version (live, 20 sessions through 11-06)",
           "| setup | trades | avg R | green | wob | worst | flag |", "|---|---|---|---|---|---|---|", *mon, "",
           "shadow S2 top-10 on live (all live, qualify >= 30 trades): " + str(top),
           "weakest 3 Primary by S2: " + str(weakest)]
    (OUT / "live_out.md").write_text("Educational only — not financial advice. Live = paper fills.\n\n" + "\n".join(txt) + "\n")
    print("\n".join(txt))


if __name__ == "__main__":
    main()
