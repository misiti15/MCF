"""GEN exposure 2026-10-25: the screen's expected signals on sessions the 2-year frames do not cover (2026-10-19..23).

    python research/ops/genexposure1025_frames.py OUT_PREFIX 2026-10-01 2026-10-02 ... [--workers 3]

Rebuilds lab frames for the lab universe (research/lab_symbols.txt) with the history pipeline
(research/history2y/build_frames.py: 1-minute bars -> 5-minute resample -> mcf.research.setup_lab.build, adv20 from the
prior 20 sessions' RTH dollar volume), from data/cache_hist (to 2026-10-16) + the replay store's 1-minute bars
(data/replay/1Min, 2026-10-19..23, read-only SIP fetch). History is cut at 2026-06-01 (~95 sessions; the frames'
longest lookbacks are 50 sessions). Then the lab context table over every frame row (context_from_frames, as the
history), the generator indicators (arena compute) and, per GEN setup with a `gen.spec`, the screen's first qualifying
bar per symbol-day (screen.spec_mask_idx semantics, float16 thresholds and values as the panel). R is not needed for a
count; rows are counted whether or not the path model has an outcome (the panel drops the few without one).
Universe rows as the panel: adv20 >= $20M, bar close 09:50..15:00, earnings blackout removed - two variants:
`screen` (the generator's own earnings file, research/bdi/earnings) and `live` (the Gen account's recorded blackout,
origin/mcf-data-gen earnings/<date>.json).
Writes OUT_PREFIX_first.csv (setup, symbol, date, tod, blackout_screen, blackout_live).
Validate on sessions the frames already hold (2026-10-01..07) against genexposure1025_rows.py.
Research only; nothing here trades. Educational only - not financial advice.
"""
from __future__ import annotations

import json
import subprocess
import sys
from multiprocessing import get_context

import numpy as np
import pandas as pd
import yaml

from mcf.data.bars import resample
from mcf.data.store import BarStore
from mcf.replay import store as RS
from mcf.research.arena.indicators import compute
from mcf.research.generator.apply import spec_from_cfg
from mcf.research.generator.data import _blackout
from mcf.research.generator.screen import _cmp
from mcf.research.generator.spec import CONTEXT, PANEL_NAMES, WINDOWS
from mcf.research.setup_lab import build
from mcf.strategies.lab_context import context_from_frames

START = "2026-06-01"
_DAYS: dict = {}


def _daily_adv(df: pd.DataFrame) -> pd.Series:
    dv = (df["close"] * df["volume"]).groupby(df.index.date).sum()
    return dv.shift(1).rolling(20, min_periods=5).mean()


def _one(args):
    syms, targets = args
    hs = BarStore(RS.ROOT / "data" / "cache_hist")
    out = []
    for s in syms:
        df = hs.load(s)
        df = df[df.index >= pd.Timestamp(START, tz=df.index.tz)] if len(df) else df
        extra = [_DAYS[d][s] for d in sorted(_DAYS) if s in _DAYS[d]
                 and (not len(df) or pd.Timestamp(d) > pd.Timestamp(df.index[-1].date()))]
        if extra:
            df = pd.concat([df] + extra).sort_index()
        if len(df) < 1000:
            continue
        x = build({s: resample(df, "5min")}, log=lambda *_: None)
        if x is None or not len(x):
            continue
        x = x[pd.Index(x["date"].astype(str)).isin(targets)].reset_index(drop=True)
        adv = _daily_adv(df)
        x["adv20"] = x["date"].map(adv).astype("float32")
        out.append(x)
    return pd.concat(out, ignore_index=True) if out else None


def main(prefix: str, targets: list[str], workers: int = 3) -> None:
    syms = sorted(set(open(RS.SYMBOLS_FILE).read().split()))
    for d in RS.available_days():
        if str(d) >= "2026-10-17":       # after the cache: the replay store's bars
            _DAYS[str(d)] = RS.load_day(d, syms)
    chunks = [(syms[i:i + 60], targets) for i in range(0, len(syms), 60)]
    with get_context("fork").Pool(workers) as pool:
        parts = [p for p in pool.imap_unordered(_one, chunks) if p is not None]
    df = pd.concat(parts, ignore_index=True)
    df["symbol"] = df["symbol"].astype(str)
    df = df.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    ctx = context_from_frames(df)                  # over every frame row (the lab universe), as the history
    df = df.merge(ctx, on=["date", "tod"], how="left")
    print("frames", len(df), "rows", df["symbol"].nunique(), "symbols", flush=True)
    df = df[df["adv20"].to_numpy(float) >= 20e6].reset_index(drop=True)
    ind = compute(df, names=list(PANEL_NAMES), context=False)
    tod = df["tod"].to_numpy()
    win = (tod >= 950) & (tod <= 1500)
    bl_screen = _blackout(df["symbol"].to_numpy(), df["date"].to_numpy())
    live_bl = set()
    for d in targets:
        r = subprocess.run(["git", "-C", str(RS.ROOT), "show", f"origin/mcf-data-gen:earnings/{d}.json"],
                           capture_output=True, text=True)
        if not r.returncode:
            live_bl |= {f"{s}|{d}" for s in json.loads(r.stdout).get("symbols", {})}
    key = df["symbol"] + "|" + df["date"].astype(str)
    bl_live = key.isin(live_bl).to_numpy()
    a = {"tod": tod, "adv20": df["adv20"].to_numpy(np.float32)}
    for k in PANEL_NAMES:
        a[k] = ind[k].to_numpy(np.float32).astype(np.float16)
    for k in CONTEXT:
        a[k] = df[k].to_numpy(np.float32).astype(np.float16)
    sd = pd.factorize(key)[0]
    st = yaml.safe_load(open("config/account_gen.yaml"))["strategies"]
    rows = []
    for name, v in st.items():
        sp = spec_from_cfg(v) if isinstance(v, dict) and (v.get("gen") or {}).get("spec") else None
        if sp is None:
            continue
        lo, hi = WINDOWS[sp.window]
        m = win & (tod >= lo) & (tod <= hi) & (a["adv20"] >= sp.min_adv)
        for c in sp.conds:
            if c[0] in CONTEXT:
                m &= _cmp(a[c[0]], c[1], np.float16(c[2]))
            else:
                m &= _cmp(a[c[0]].astype(np.float32), c[1], np.float32(np.float16(c[2])))
        for lab, bl in (("screen", bl_screen), ("live", bl_live)):
            idx = np.flatnonzero(m & ~bl)
            if not len(idx):
                continue
            s = sd[idx]
            f = idx[np.r_[True, s[1:] != s[:-1]]]
            rows.append(pd.DataFrame({"setup": name, "symbol": df["symbol"].to_numpy()[f],
                                      "date": df["date"].astype(str).to_numpy()[f], "tod": tod[f], "blackout": lab}))
    pd.concat(rows).to_csv(prefix + "_first.csv", index=False)
    print("wrote", prefix + "_first.csv")


if __name__ == "__main__":
    args = [x for x in sys.argv[2:] if not x.startswith("--")]
    w = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 3
    args = [x for x in args if x != str(w)] if "--workers" in sys.argv else args
    main(sys.argv[1], args, w)
