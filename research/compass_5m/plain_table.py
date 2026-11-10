"""COMPASS-5M: the plain-English state table for the Market Compass (live) card. For each live state (W60 level at the
15-min marks, or "after a midday flip") x time block: % of (day, mark) readings where SPY then closed on the stated side
of its open. TRAIN+VALID pooled (headline), FWD shown. Usage: python plain_table.py <scratch> -> mcf/report/compass_plain.json
Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / "compass_learn"))
import engine as E  # noqa: E402

pan = E.Panel(pd.read_parquet(Path(sys.argv[1]) / "panel.parquet"))
M15 = list(range(585, 946, 15))                      # live marks 09:45 .. 15:45
BLOCKS = [("early", 585, 659, "09:45-10:59"), ("mid", 660, 779, "11:00-12:59"), ("late", 780, 945, "13:00-15:45")]
NAMES = {2: "UP-confirmed", 1: "leaning up", 0: "mixed", -1: "leaning down", -2: "DOWN-confirmed"}


def levels(p):
    cols = E.mi(M15)
    s, v1, v2, v3 = E.base_votes(p, cols)
    pw, nmk = E.persistence(s, M15, 60)
    v = s + v1 + v2 + v3 + pw
    ok = (nmk >= 2)[None, :]
    return np.where((v >= 4) & (pw == 1) & ok, 2, np.where(v >= 2, 1, np.where((v <= -4) & (pw == -1) & ok, -2,
                    np.where(v <= -2, -1, 0))))


def flips(p):
    """+1 / -1 = flipped to that side: SPY >= 0.20% from its open at 12:00, now (15-min mark >= 12:15) on the other side."""
    fo = np.nan_to_num(p.m["fo"])
    noon = fo[:, E.mi(720)]
    ms = np.where(noon >= 0.002, 1, np.where(noon <= -0.002, -1, 0))
    F = np.zeros((len(p.dates), len(M15)), int)
    for j, T in enumerate(M15):
        if T >= 735:
            now = np.sign(fo[:, E.mi(T)])
            F[:, j] = np.where((ms != 0) & (now == -ms), -ms, 0)
    return F


def table(p):
    L, F = levels(p), flips(p)
    eod = p.eod[:, None] * np.ones_like(L)
    out = {}
    for b, lo, hi, _ in BLOCKS + [("all", 585, 945, "")]:
        js = [j for j, T in enumerate(M15) if lo <= T <= hi]
        l, f, e = L[:, js], F[:, js], eod[:, js]
        for code, name in NAMES.items():
            k = (l == code) & (f == 0)
            side = 1 if code > 0 else (-1 if code < 0 else 1)          # mixed: share closing ABOVE the open
            out[(name, b)] = (int(((e == side) & k).sum()), int(k.sum()), int(k.any(1).sum()))
        for sd, name in ((1, "flipped up"), (-1, "flipped down")):
            k = f == sd
            out[(name, b)] = (int(((e == sd) & k).sum()), int(k.sum()), int(k.any(1).sum()))
    return out


def next_hour(p, h=60):
    """W60 confirmed: SPY's next-60-min direction equals the reading (15-min marks 10:00..14:45)."""
    L = levels(p); px = p.m["px"]; hit = n = 0
    for j, T in enumerate(M15):
        if T < 600 or T + h > 955:
            continue
        c = np.sign(L[:, j]) * (np.abs(L[:, j]) == 2)
        mv = np.sign(px[:, E.mi(T + h)] / px[:, E.mi(T)] - 1)
        ok = (c != 0) & (mv != 0) & np.isfinite(mv)
        hit += int(((mv == c) & ok).sum()); n += int(ok.sum())
    return hit, n


tv = pan.sub(np.isin(pan.period, ["TRAIN", "VALID"])); fw = pan.sub(pan.period == "FWD")
A, B = table(tv), table(fw)
states = {}
for (name, b), (h, n, d) in A.items():
    fh, fn, fd = B[(name, b)]
    states.setdefault(name, {})[b] = dict(hit=round(h / n, 4) if n else None, n=n, days=d,
                                          fwd_hit=round(fh / fn, 4) if fn else None, fwd_n=fn, fwd_days=fd)
nh, nn = next_hour(tv); fh, fn = next_hour(fw)
out = dict(
    window="the rest of today (where SPY closes vs its open)",
    why="COMPASS-5M (research/compass_5m/NOTES.md): no state, 5-, 10- or 15-min, calls SPY's next 5-90 min direction "
        "better than ~52% in VALID / FWD; the close-vs-open side is what the compass reads.",
    blocks=[dict(id=b, lo=lo, hi=hi, label=lab) for b, lo, hi, lab in BLOCKS],
    states=states,
    next_hour=dict(hit=round(nh / nn, 4), n=nn, fwd_hit=round(fh / fn, 4), fwd_n=fn),
    periods="TRAIN 2024-10 + 2025-03..12, VALID 2026-01-01..10-05 (pooled = hit); FWD 2026-10-06..11-04",
    unit="share of 15-min readings (day x mark) in that state after which SPY closed on the stated side of its open",
    source="research/compass_5m/plain_table.py", disclaimer="Educational only — not financial advice.")
(ROOT / "mcf" / "report" / "compass_plain.json").write_text(json.dumps(out, indent=1))
for name, v in states.items():
    print(f"{name:15s}", "  ".join(f"{b}: {x['hit']} n{x['n']}/{x['days']}d fwd {x['fwd_hit']} n{x['fwd_n']}" for b, x in v.items()))
print("next hour", out["next_hour"])
