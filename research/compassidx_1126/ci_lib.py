"""COMPASSIDX-1126 shared loaders: SPY 1-min RTH bars per day (bench caches via regsteer_1126/rs_states.bars, which filters
and asserts the locked block 2024-11-01..2025-02-28; live window from the compass_rd_1126 Alpaca SIP copy), W60 marks
(regsteer point-in-time rebuild; live = compute() backfill), splits, the PREREG hash gate, LIVE-L cost and the CI-1 trade.
Educational only - not financial advice."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

H = Path(__file__).resolve().parent
ROOT = H.parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/regsteer_1126"))
import rs_states as S  # noqa: E402

SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad")
MARKS_BENCH = SCR / "rsw/st/marks.parquet"            # rs_states.py output (REGSTEER run, frozen)
MARKS_LIVE = SCR / "rsw/live_compass_marks.parquet"   # compute() on Alpaca bars 10-06..11-25 (compass_rd_1126 copy)
BARS_LIVE = SCR / "crd/idx_bars.parquet"               # Alpaca SIP 1-min SPY/QQQ/IWM 10-01..11-25
LOCK = S.LOCK
CELLS = json.load(open(ROOT / "research/primshorts_1126/cells_live.json"))
EXIT_M = 955                                            # 15:55 bar open


def no_locked(dates):
    S.no_locked(dates)


LIVE_MODE = False   # set True (alone) to score the live window 10-23..11-25 from live marks / Alpaca bars


def period(d):
    if LIVE_MODE:
        return "LIVE" if "2026-10-23" <= d <= "2026-11-25" else "none"
    if ("2024-10-01" <= d <= "2024-10-31") or ("2025-03-01" <= d <= "2025-09-30"):
        return "FIT"
    if "2025-10-01" <= d <= "2026-11-04":
        return "CHECK"
    if "2023-01-03" <= d <= "2024-09-13":
        return "T2"
    return "none"


def prereg_gate():
    """CHECK / T2 / LIVE may only be scored once PREREG.md is frozen (its sha256 on file and matching)."""
    p, h = H / "PREREG.md", H / "PREREG.sha256"
    assert p.exists() and h.exists(), "PREREG not frozen"
    assert hashlib.sha256(p.read_bytes()).hexdigest() == h.read_text().split()[0], "PREREG changed after freeze"


def spy_days(splits):
    """dict date -> DataFrame(m, open, high, low, close) for SPY RTH minutes, only days in `splits`."""
    out = {}
    if {"FIT", "CHECK", "T2"} & set(splits):
        b = pd.concat([S.bars("SPY", S.FRESH), S.bars("SPY", S.HIST)])
        b = b[~b.index.duplicated()]
        d = b.index.date.astype(str)
        for k, g in b.groupby(d):
            if period(k) in splits:
                out[k] = pd.DataFrame({"m": g.index.hour * 60 + g.index.minute, "open": g.open.to_numpy(),
                                       "high": g.high.to_numpy(), "low": g.low.to_numpy(), "close": g.close.to_numpy()})
    if "LIVE" in splits:
        b = pd.read_parquet(BARS_LIVE); b = b[b.symbol == "SPY"].copy()
        b["ts"] = b.ts.dt.tz_convert("America/New_York"); b["date"] = b.ts.dt.date.astype(str)
        b["m"] = b.ts.dt.hour * 60 + b.ts.dt.minute
        b = b[(b.m >= 570) & (b.m < 960)]
        for k, g in b.groupby("date"):
            if period(k) == "LIVE":
                out[k] = g[["m", "open", "high", "low", "close"]].reset_index(drop=True)
    no_locked(out.keys())
    return out


def marks(splits):
    """dict date -> (T array, level array)."""
    out = {}
    if {"FIT", "CHECK", "T2"} & set(splits):
        M = pd.read_parquet(MARKS_BENCH); no_locked(M.date.unique())
        for k, g in M.sort_values(["date", "T"]).groupby("date"):
            if period(k) in splits:
                out[k] = (g["T"].to_numpy(int), g.level.to_numpy(int))
    if "LIVE" in splits:
        L = pd.read_parquet(MARKS_LIVE)
        L["level"] = L.w60.map({"UP-confirmed": 2, "leaning up": 1, "mixed": 0, "leaning down": -1, "DOWN-confirmed": -2})
        for k, g in L.sort_values(["date", "m"]).groupby("date"):
            if period(k) == "LIVE":
                out[k] = (g["m"].to_numpy(int), g.level.fillna(0).to_numpy(int))
    no_locked(out.keys())
    return out


def cost_R(width_bps, kind):
    """LIVE-L (primshorts_1126 cells_live.json, $100+ bucket): cost_R = a / width_bps + b; kind 'stop' or 'market'."""
    a, b, _ = CELLS[f"100+|{kind}"]
    return a / width_bps + b


def bar_at(g, m):
    k = np.searchsorted(g.m.to_numpy(), m)
    return k if k < len(g) else None


def first_conf(T, L, lo=600, hi=780):
    """first mark with |level| == 2 among marks in [lo, hi] (the day's first confirmation if none earlier): (T, side)."""
    for t, l in zip(T, L):
        if abs(l) == 2:
            return (int(t), int(np.sign(l))) if lo <= t <= hi else (None, 0)
    return None, 0


def trade(g, T, L, t0, side, cap=0.006, floor=0.001, flip="exit", exit_after=None):
    """CI-1 trade: entry open of bar t0+1; stop = session extreme opposite the call through bar t0 (bars < t0+1),
    distance capped at `cap` and floored at `floor` of entry; exit at the stop (gap-through fills at the bar open), at the
    open of bar T'+1 for the first later mark T' with level == -2*side (flip='exit'), or at 15:55. Returns dict or None.
    exit_after: force the non-stop exit minute (placebos reuse the real trade's time/flip exit minute)."""
    m = g.m.to_numpy(); k0 = np.searchsorted(m, t0 + 1)
    if k0 >= len(g) or m[k0] > t0 + 5:
        return None
    ent = float(g.open.iloc[k0])
    ext = float(g.low.iloc[:k0].min()) if side > 0 else float(g.high.iloc[:k0].max())
    dist = min(max(side * (ent - ext), floor * ent), cap * ent)
    stop = ent - side * dist
    if exit_after is None:
        xm = EXIT_M
        if flip == "exit":
            for t, l in zip(T, L):
                if t > t0 and l == -2 * side and t + 1 < EXIT_M:
                    xm = int(t) + 1; break
    else:
        xm = exit_after
    kx = np.searchsorted(m, xm)
    kind, px, xmin = "market", None, xm
    for k in range(k0, min(kx, len(g))):
        if (side > 0 and g.low.iloc[k] <= stop) or (side < 0 and g.high.iloc[k] >= stop):
            o = float(g.open.iloc[k])
            px = min(stop, o) if side > 0 else max(stop, o)
            kind, xmin = "stop", int(m[k]); break
    if px is None:
        px = float(g.open.iloc[kx]) if kx < len(g) else float(g.close.iloc[-1])
    w = dist / ent * 1e4
    rg = side * (px - ent) / dist
    return dict(em=int(m[k0]), xm=xmin, tx=xm, side=side, entry=ent, dist_bps=w, kind=kind, r_gross=rg,
                r=rg - cost_R(w, kind), ret_bps=side * (px / ent - 1) * 1e4)


def tstat(x):
    x = np.asarray(x, float)
    return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 and x.std() > 0 else float("nan")
