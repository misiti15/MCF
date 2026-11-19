"""ETFDISP scoring, the "normal filter way" (research/ultimate_1119/top10/bench10.py functions, unchanged).
    python score.py WORK t1 | t2 | stats
Signals: the LIVE module (modules/ETFDISP-late-dip-hidisp-long.py) mask on lab frames (T1) / frames built from
cache_fresh 1-minute bars (T2) with spy_fo context and the disp_prev column (computed per date with
mcf.strategies.lab_context.cross_dispersion = the live function), YAML window 14:00-15:00, min_adv $95M,
refire chain cooldown 0 (the module thins). Ungated leg E (U32.mask) is scored on the same rows as a reference.
Exits: bench10 walk (entry decision-bar close; stop first; target traded through by $0.01; flat 15:55) AND the setup's
own 45-minute time exit (as configured live). Costs LR8 (bench10.add_r). Book: testing-arena rules (cap 100, 0.15R
cost filter, <= 3 lots per symbol, price >= $5). Locked block 2024-11-01..2025-02-28 never read.
Educational only - not financial advice."""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import os
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE.parent / "top10"))
import bench10 as B  # noqa: E402

from mcf.strategies.lab_context import cross_dispersion  # noqa: E402

MOD = ROOT / "research/ultimate_1119/modules/ETFDISP-late-dip-hidisp-long.py"
H2Y_DAILY = "/home/user/MCF/research/history2y/data/daily.parquet"
FRESH_DAILY = "/home/user/MCF/data/cache_fresh/daily.parquet"
FRAMES = "/home/user/MCF/research/history2y/data/frames"
L0, L1 = "2024-11-01", "2025-02-28"
CAP_MIN = 45


def load_module():
    spec = importlib.util.spec_from_file_location("lab_ETFDISP-late-dip-hidisp-long", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M = load_module()
W = sorted(M.SYMBOLS)
_wb = importlib.util.spec_from_file_location(
    "lab_wb4", ROOT / "research/workbench/NM-ETF-late-dip-di-long/modules/NM-ETF-late-dip-di-long-WB4.py")
WB4 = importlib.util.module_from_spec(_wb)
_wb.loader.exec_module(WB4)   # live Testing E setup (overlap reference only; YAML: refire, cooldown 1)


# ------------------------------------------------------------------ disp_prev per session (live function)
def disp_table(daily: pd.DataFrame, segments) -> pd.Series:
    """date -> disp_prev of that session: dispersion of the PRIOR session's returns (names with prior ADV20 >= $95M),
    only when the prior session (and the one before it) lie in the same contiguous segment (no locked-gap bridging)."""
    d = daily.copy()
    d["date"] = pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d")
    piv = d.pivot_table(index="date", columns="symbol", values="close").sort_index()
    adv = d.pivot_table(index="date", columns="symbol", values="adv20").reindex(piv.index)
    ret = piv.pct_change(fill_method=None)
    sess = list(piv.index)
    seg = np.array([segments(x) for x in sess])
    out = {}
    for i in range(2, len(sess)):
        if not (seg[i] == seg[i - 1] == seg[i - 2]):
            continue
        out[sess[i]] = cross_dispersion(ret.iloc[i - 1].to_numpy(float), adv.iloc[i - 1].to_numpy(float))
    return pd.Series(out, dtype=float)


def t1_disp():
    f = ds.field("date")
    y = ds.dataset(H2Y_DAILY).to_table(filter=(f < pd.Timestamp(L0)) | (f > pd.Timestamp(L1)),
                                       columns=["symbol", "date", "close", "adv20"]).to_pandas()
    y["date"] = pd.to_datetime(y.date).dt.strftime("%Y-%m-%d")
    B.no_locked(y.date.unique())
    return disp_table(y, lambda x: int(x > "2024-10-31"))


def t2_disp():
    x = pd.read_parquet(FRESH_DAILY, columns=["symbol", "date", "close", "adv20"])
    x["date"] = pd.to_datetime(x.date).dt.strftime("%Y-%m-%d")
    x = x[x.date <= "2024-09-13"]
    return disp_table(x, lambda _: 0)


# ------------------------------------------------------------------ signals (bench10.signals, inventory = this setup)
class Wrapped:
    """bench10 module interface; adds disp_prev by date (constant per session) then calls the live mask."""
    SIDE, GEOM = "long", "t05s1"

    def __init__(self, disp, gated):
        self.disp, self.gated = disp, gated

    def mask(self, df):
        g = df.assign(disp_prev=df["date"].astype(str).map(self.disp).astype(float))
        return M.mask(g) if self.gated else M.U32.mask(g)


def inventory():
    base = dict(module=str(MOD), side=1, geom="t05s1", w_lo=1400, w_hi=1500, min_adv=95e6, refire=True, cooldown=0,
                prefilter="", account="testing", cfg="(new)", struct=False, cwt=False)
    return [dict(base, setup="ETFDISP"), dict(base, setup="LEG-E-ungated"), dict(base, setup="WB4", cooldown=1)]


def sig(frame, disp):
    inv = inventory()
    mods = {"ETFDISP": Wrapped(disp, True), "LEG-E-ungated": Wrapped(disp, False), "WB4": WB4}
    return B.signals(frame, frame, inv, mods)


# ------------------------------------------------------------------ exits: bench10 walk + 45-minute cap
def walk_cap(T, b, cap=CAP_MIN):
    hhmm = b.index.hour * 100 + b.index.minute
    mins = b.index.hour * 60 + b.index.minute
    day = b.index.date.astype(str)
    O, H, Lo, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    byday = {dd: np.flatnonzero(day == dd) for dd in np.unique(day)}
    res = []
    for r in T.itertuples():
        ix = byday.get(r.date)
        if ix is None:
            res.append((r.Index, np.nan, -1, -1))
            continue
        em = (r.tod // 100) * 60 + r.tod % 100
        sel = ix[(hhmm[ix] >= r.tod) & (hhmm[ix] < 1555)]
        px = None
        for k in sel:
            if mins[k] >= em + cap:                       # time exit at the open of the bar starting entry + 45 min
                px, kd, xt = O[k], 0, hhmm[k]
                break
            if Lo[k] <= r.stop:
                px, kd, xt = min(O[k], r.stop), 1, hhmm[k]
                break
            if r.tgt == r.tgt and H[k] >= r.tgt + 0.01:
                px, kd, xt = r.tgt, 2, hhmm[k]
                break
        if px is None:
            if len(sel):
                px, kd, xt = C[sel[-1]], 0, hhmm[sel[-1]] + 1
            else:
                res.append((r.Index, np.nan, -1, -1))
                continue
        res.append((r.Index, px, kd, xt))
    return res


def walk_both(T, b):
    a = pd.DataFrame(B.walk_trades(T, b), columns=["i", "px", "kind", "xt"]).set_index("i")
    c = pd.DataFrame(walk_cap(T, b), columns=["i", "px45", "kind45", "xt45"]).set_index("i")
    return T.join(a).join(c)


# ------------------------------------------------------------------ T1
def t1_month(args):
    month, disp = args
    import research.history2y.lib as lib
    lib.DATA = B.DATA
    f = ds.dataset(f"{FRAMES}/month={month}", format="parquet").to_table(
        filter=ds.field("symbol").isin(W)).to_pandas()
    f["date"] = pd.to_datetime(f["date"]).dt.date
    f = f.merge(lib.load_context(month), on=["date", "tod"], how="left")
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    f = f[[c for c in f.columns if not c.startswith(("win_", "r_long", "r_short"))]]
    B.no_locked(f["date"].unique())
    return sig(f, disp)


def t1(work):
    disp = t1_disp()
    months = [m for m in sorted(p.name.split("=")[1] for p in Path(FRAMES).glob("month=*")) if m not in B.LOCKED_MONTHS]
    with Pool(3) as p:
        S = pd.concat([x for x in p.map(t1_month, [(m, disp) for m in months]) if len(x)], ignore_index=True)
    out = []
    for sym, g in S.groupby("symbol"):
        if (B.CACHE / f"{sym}.parquet").exists():
            out.append(walk_both(g, B.hist_bars(sym)))
    T = pd.concat(out)
    T.to_parquet(Path(work) / "t1.parquet")
    disp.to_frame("disp_prev").to_parquet(Path(work) / "disp_t1.parquet")
    print("T1", T.groupby("setup").size().to_dict(), "signals without 1-min bars:", len(S) - len(T))


# ------------------------------------------------------------------ T2 (same frame build as bench10.t2_job)
def t2_sym(args):
    sym, disp = args
    import research.history2y.build_frames as BF
    p = B.FRESH / "1Min" / f"{sym}.parquet"
    if not p.exists():
        return sym, "no1min", None
    b = pd.read_parquet(p)
    b.index = pd.DatetimeIndex(b.index).tz_convert(B.TZ)
    b = b.sort_index()
    d5 = BF.resample(b, "5min")
    if len(d5) < 300:
        return sym, "short", None
    dd = BF.daily_table(b, sym)
    x = BF.build({sym: d5}, log=lambda *_: None)
    if x is None or not len(x):
        return sym, "noframe", None
    x = x.reset_index(names="ts")
    x = x[[c for c in x.columns if not c.startswith(("win_", "r_long", "r_short"))]]
    x = x.merge(dd[["date", "adv20"]], on="date", how="left")
    x["date"] = x["date"].astype(str)
    x = x[(x.date >= B.T2_LO) & (x.date <= B.T2_HI)]
    if not len(x):
        return sym, "nodays", None
    c = pd.read_parquet(B.FRESH / "ctx.parquet")
    c["date"] = c["date"].astype(str)
    f = x.drop(columns=["ts"]).merge(c, on=["date", "tod"], how="left")
    f["symbol"] = sym
    f = f.sort_values(["date", "tod"], kind="mergesort").reset_index(drop=True)
    o = sig(f, disp)
    if not len(o):
        return sym, "ok", None
    return sym, "ok", walk_both(o, b)


def t2(work):
    disp = t2_disp()
    with Pool(3) as p:
        res = p.map(t2_sym, [(s, disp) for s in W])
    st = {}
    for _, s, _ in res:
        st[s] = st.get(s, 0) + 1
    T = pd.concat([o for _, _, o in res if o is not None and len(o)], ignore_index=True)
    T.to_parquet(Path(work) / "t2.parquet")
    disp.to_frame("disp_prev").to_parquet(Path(work) / "disp_t2.parquet")
    json.dump({"etf_symbols": len(W), "status": st,
               "with_1min": sorted(s for s, x, _ in res if x != "no1min")}, open(Path(work) / "t2_status.json", "w"))
    print("T2", T.groupby("setup").size().to_dict(), st)


if __name__ == "__main__":
    work, stage = sys.argv[1], sys.argv[2]
    Path(work).mkdir(parents=True, exist_ok=True)
    {"t1": t1, "t2": t2}[stage](work)
