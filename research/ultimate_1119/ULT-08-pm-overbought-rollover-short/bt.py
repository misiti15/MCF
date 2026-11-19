"""ULT-08 afternoon overbought roll-over short - backtest (ultimate_1119 PLAN.md sec. 1-2, 3 "ULT-08"). Adapted from ULT-04 bt.py.

Signals: lab frames (research/history2y/data/frames, 5-min decision bars, bar-close tod) + context (spy_fo), through the
SAME mask as the live module (modules/ULT-08-pm-overbought-rollover-short.py, superset params RUN 1.5 / RSI_MIN 80), then
every grid config is a sub-filter. Exits walked on 1-minute bars (data/cache_hist/1Min) as benchmark/bench.py:
first minute = the one starting at the decision-bar close; stop first, then target; stop gap-through fills at the worse
of open/stop; time exit at the close of minute entry+44 (45 min) or the 15:49 minute (flat 15:50).
  X20 / X30 = TX20 / TX30: no target, catastrophic stop at 2R, 20 / 30-min time exit. Scored per unit of RISK (2R) like bench.cost_r (/dn),
      i.e. as live risk-based sizing would book it; the 0.25-ATR-unit figure is 2x.
Costs LR8 (mcf.research.gates): entry (1c + 1bp) x tod mult; exit 1c + 1bp except target fills; +2c on stops.
Chassis: one lot per symbol; refire only >= 30 min after the exit; max 2 per symbol-session; day cap 30 entries
(first by time, ties ADV20 desc); window 14:00-15:00 bar close (frames stop at 15:00).
Halves: FIT = 2024-10 + 2025-03..2025-09; CHECK = 2025-10-01..latest. Locked 2024-11-01..2025-02-28 never read.
    python bt.py WORK sig fit|check ; python bt.py WORK walk fit|check
Educational only - not financial advice."""
from __future__ import annotations

import importlib.util
import os
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "never reads the locked block"
from mcf.research.gates import tod_cost_mult  # noqa: E402

DATA = Path("/home/user/MCF/research/history2y/data")
CACHE = Path("/home/user/MCF/data/cache_hist/1Min")
LOCK = ("2024-11-01", "2025-02-28")
FIT_MONTHS = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 10)]
MOD = HERE.parent / "modules" / "ULT-08-pm-overbought-rollover-short.py"


def no_locked(dates):
    s = pd.Series([str(x) for x in dates])
    assert not ((s >= LOCK[0]) & (s <= LOCK[1])).any(), "locked block row found"


def half_months(half):
    import research.history2y.lib as lib
    lib.DATA = DATA
    ms = [m for m in lib.months() if m not in lib.LOCKED_MONTHS]
    return FIT_MONTHS if half == "fit" else [m for m in ms if m >= "2025-10"]


def load_mod():
    spec = importlib.util.spec_from_file_location("ult08", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def m2(t):
    t = np.asarray(t, int)
    return (t // 100) * 60 + t % 100


def month_job(month):
    import research.history2y.lib as lib
    lib.DATA = DATA
    mod = load_mod()
    mod.WINDOW, mod.RUN, mod.RSI_MIN, mod.THIN = (1400, 1500), 1.5, 80.0, False         # superset; configs filter below
    f = lib.load_month(month, context=True)
    f["symbol"] = f["symbol"].astype(str)
    no_locked(f["date"].unique())
    with np.errstate(invalid="ignore", divide="ignore"):
        mk = np.asarray(mod.mask(f), bool)
    mk &= f["adv20"].fillna(0).to_numpy() >= mod.MIN_ADV
    f["foa"] = mod.from_open_atr(f)
    f["rsi5p"] = mod.rsi5_prev(f)
    cols = ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap", "rsi5", "rsi5p", "foa", "upper_wick", "spy_fo"]
    sig = f.loc[mk, cols].copy()
    # random-control pool: every intake-U bar in 14:00-15:00 of the symbol-sessions that carry a signal
    key = f.symbol + "|" + f.date.astype(str)
    sk = set(sig.symbol + "|" + sig.date.astype(str))
    with np.errstate(invalid="ignore", divide="ignore"):
        u = np.asarray(mod.intake(f), bool) & (f["adv20"].fillna(0).to_numpy() >= mod.MIN_ADV)
    pool = f.loc[key.isin(sk).to_numpy() & u & (f.tod.to_numpy() >= 1400) & (f.tod.to_numpy() <= 1500), cols].copy()
    days = sorted(set(lib.load_context(month)["date"]))
    return month, sig, pool, days


def walk_job(args):
    sym, T, half = args
    d = pads.dataset(str(CACHE / f"{sym}.parquet"), format="parquet")
    fld = pads.field("__index_level_0__")
    tz = "America/New_York"
    L0, L1, C0 = (pd.Timestamp(x, tz=tz) for x in ("2024-11-01", "2025-03-01", "2025-10-01"))
    filt = ((fld < L0) | ((fld >= L1) & (fld < C0))) if half == "fit" else (fld >= C0)
    b = d.to_table(filter=filt).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(tz)
    b = b.sort_index()
    no_locked(np.unique(b.index.date))
    hhmm = (b.index.hour * 100 + b.index.minute).to_numpy()
    day = np.array([str(x) for x in b.index.date])
    O, H, L, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    byday = {dd: np.flatnonzero(day == dd) for dd in np.unique(day)}
    res = []
    for r in T.itertuples():
        ix = byday.get(r.date)
        if ix is None:
            res.append((r.Index,) + (np.nan, -1, -1) * 2); continue
        hm = hhmm[ix]
        e, R = r.entry, r.R
        out = []
        for up, dn, cap in ((None, 2.0, 20), (None, 2.0, 30)):          # X20, X30 (short)
            tend = min(m2(r.tod) + cap - 1, m2(1549))
            sel = ix[(m2(hm) >= m2(r.tod)) & (m2(hm) <= tend)]
            if not len(sel):
                out += [np.nan, -1, -1]; continue
            stop, tgt = e + dn * R, (None if up is None else e - up * R)
            px = None
            for k in sel:
                if H[k] >= stop:
                    px, kd, xt = max(O[k], stop), 1, m2(hhmm[k]) + 1; break
                if tgt is not None and L[k] <= tgt:
                    px, kd, xt = tgt, 2, m2(hhmm[k]) + 1; break
            if px is None:
                px, kd, xt = C[sel[-1]], 0, m2(hhmm[sel[-1]]) + 1
            out += [px, kd, xt]
        res.append((r.Index, *out))
    return res


def walk(T, half, procs=3):
    jobs = [(s, g, half) for s, g in T.groupby("symbol") if (CACHE / f"{s}.parquet").exists()]
    with Pool(procs) as p:
        out = [x for r in p.imap_unordered(walk_job, jobs, chunksize=4) for x in r]
    a = pd.DataFrame(out, columns=["i", "pxX20", "kX20", "xX20", "pxX30", "kX30", "xX30"]).set_index("i")
    return T.join(a)


def r_after_cost(e, R, tod, px, kind, dn):
    ecost = (0.01 + e * 1e-4) * tod_cost_mult(tod)
    xcost = np.where(kind == 2, 0.0, 0.01 + px * 1e-4) + np.where(kind == 1, 0.02, 0.0)
    gross = -(px - e) / R
    return (gross - (ecost + xcost) / R) / dn


def configs():
    out = {}
    names = iter("abcdefgh")
    for run in (1.5, 2.0):
        for rmin in (80, 85):
            for ex in ("X20", "X30"):
                out["08" + next(names)] = dict(run=run, rsi_min=rmin, ex=ex, label=f"RUN{run:g}-R{rmin}-{ex}")
    return out


def cfg_filter(S, cfg):
    return S[(S.tod >= 1400) & (S.tod <= 1500) & (S.foa >= cfg["run"]) & (S.rsi5p >= cfg["rsi_min"])
             & S["k" + cfg["ex"]].ge(0)]


def dn_of(ex):
    return 2.0


def select(S, cfg, cap=30, chain=True):
    """Apply config filter + chassis (one lot, refire >= 30 min after exit, max 2/symbol-session, day cap)."""
    ex = cfg["ex"]
    s = cfg_filter(S, cfg)
    s = s.sort_values(["symbol", "date", "tod"], kind="mergesort")
    keep = []
    if chain:
        for _, g in s.groupby(["symbol", "date"], sort=False):
            n, free_at = 0, -1
            for i, t, x in zip(g.index, m2(g.tod.to_numpy()), g["x" + ex].to_numpy()):
                if n >= 2:
                    break
                if t >= free_at:
                    keep.append(i); n += 1; free_at = x + 30
    else:
        keep = list(s.index)
    s = S.loc[keep].sort_values(["date", "tod", "adv20"], ascending=[True, True, False], kind="mergesort")
    if cap:
        s = s.groupby("date", sort=False).head(cap)
    dn = dn_of(ex)
    s = s.assign(r=r_after_cost(s.entry.to_numpy(), s.R.to_numpy(), s.tod.to_numpy(), s["px" + ex].to_numpy(),
                                s["k" + ex].to_numpy(), dn),
                 hold=s["x" + ex] - m2(s.tod.to_numpy()), kind=s["k" + ex])
    return s


if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True)
    stage, half = sys.argv[2], sys.argv[3]
    if stage == "sig":
        sigs, pools, days = [], [], []
        with Pool(2) as p:
            for m, s, pl, d in p.imap_unordered(month_job, half_months(half)):
                print(m, len(s), len(pl), flush=True)
                sigs.append(s); pools.append(pl); days += d
        S = pd.concat(sigs, ignore_index=True)
        P = pd.concat(pools, ignore_index=True)
        for X in (S, P):
            X["date"] = X["date"].astype(str)
            X["entry"] = X["close"]
            X["R"] = 0.25 * X["atr_d"]
        no_locked(S.date.unique()); no_locked(P.date.unique()); no_locked(days)
        S.to_parquet(W / f"sig_{half}.parquet"); P.to_parquet(W / f"pool_{half}.parquet")
        pd.Series(sorted(str(x) for x in days)).to_frame("date").to_parquet(W / f"days_{half}.parquet")
    elif stage == "walk":
        S = pd.read_parquet(W / f"sig_{half}.parquet")
        walk(S, half).to_parquet(W / f"walked_{half}.parquet")
        print("walked", len(S))
