"""ULT-10 regime-switch book - backtest (ultimate_1119 PLAN.md sec. 1-2, 3 "ULT-10", 5, 6).

Signals: lab frames (research/history2y/data/frames, 5-min decision bars, bar-close tod) + context (spy_fo), through the
SAME functions as the live module (modules/ULT-10-regime-switch-book.py: component_mask / regime / ult09_mask).
Exits walked on 1-minute bars (data/cache_hist/1Min) as benchmark/bench.py and ULT-01 bt.py: first minute = the one
starting at the decision-bar close; stop first, then target (same minute: stop); stop gap-through fills at the worse of
open/stop; time exit at the close of minute entry+cap-1 or the 15:49 minute (flat 15:50).
R scored per unit of RISK (divided by the stop distance in R, like bench.cost_r): TX exits (2R stop) are booked per 2R.
Costs LR8 (mcf.research.gates.tod_cost_mult): entry (1c + 1bp) x tod mult; exit 1c + 1bp except target fills; +2c on
stops. Book chassis (exact): day processed in time order (ties ADV20 desc, then leg priority); one lot per symbol
across the book; re-entry only >= 30 min after the exit; max 2 per symbol-session; day cap 30 entries.
FIT = 2024-10 + 2025-03..2025-09; CHECK = 2025-10-01..latest. Locked 2024-11-01..2025-02-28 never read.
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
MOD = HERE.parent / "modules" / "ULT-10-regime-switch-book.py"
SPECS = {"T": (1.0, 1.0, 45), "t05": (0.5, 1.0, 45), "X20": (None, 2.0, 20), "X30": (None, 2.0, 30),
         "X45": (None, 2.0, 45)}
U09 = {}   # ULT-09 grid (PLAN): S_T outer, W middle, exit inner
for _k, (_st, _w, _ex) in enumerate([(s, w, e) for s in (-0.20, 0.00) for w in (1400, 1500) for e in ("T", "X45")]):
    U09["09" + "abcdefgh"[_k]] = dict(s_t=_st, w_hi=_w, exit=_ex)


def no_locked(dates):
    s = pd.Series([str(x) for x in dates])
    assert not ((s >= LOCK[0]) & (s <= LOCK[1])).any(), "locked block row found"


def half_months(half):
    import research.history2y.lib as lib
    lib.DATA = DATA
    ms = [m for m in lib.months() if m not in lib.LOCKED_MONTHS]
    return FIT_MONTHS if half == "fit" else [m for m in ms if m >= "2025-10"]


def load_mod():
    spec = importlib.util.spec_from_file_location("ult10_bt", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def m2(t):
    t = np.asarray(t, int)
    return (t // 100) * 60 + t % 100


def flag_names(mod):
    """Distinct component configs needed by sets a and b (+ the ULT-09 superset)."""
    out = {}
    for st in ("a", "b"):
        for leg, p in mod.CONFIGS[st].items():
            if leg != "09":
                out[p["cfg"]] = (leg, p)
    out["09sup"] = ("09", dict(cfg="09sup", window=(1030, 1500), s_t=0.00, exit="T"))
    return out


def month_job(month):
    import research.history2y.lib as lib
    lib.DATA = DATA
    mod = load_mod()
    f = lib.load_month(month, context=True)
    no_locked(f["date"].unique())
    f = f[f["adv20"].fillna(0).to_numpy() >= mod.MIN_ADV].reset_index(drop=True)   # adv20 is fixed per symbol-day
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    spy = mod.spy_features(f)
    flags = {}
    with np.errstate(invalid="ignore", divide="ignore"):
        for name, (leg, p) in flag_names(mod).items():
            flags[name] = mod.component_mask(f, leg, p, spy=spy)
    anyf = np.zeros(len(f), bool)
    for v in flags.values():
        anyf |= v
    cols = ["symbol", "date", "tod", "close", "atr_d", "adv20"]
    sig = f.loc[anyf, cols].copy()
    sig["s930"], sig["r30"], sig["s950"] = spy[0][anyf], spy[1][anyf], spy[2][anyf]
    for k, v in flags.items():
        sig["f_" + k] = v[anyf]
    # random-control pool: intake-U bars 10:15-15:00 of the symbol-sessions that carry any component signal
    key = f.symbol + "|" + f.date
    sk = set(sig.symbol + "|" + sig.date)
    with np.errstate(invalid="ignore", divide="ignore"):
        u = np.asarray(mod.intake(f), bool)
    tod = f.tod.to_numpy()
    pool = f.loc[key.isin(sk).to_numpy() & u & (tod >= 1015) & (tod <= 1500), ["symbol", "date", "tod", "close", "atr_d"]]
    days = sorted(set(lib.load_context(month)["date"].astype(str)))
    return month, sig, pool.copy(), days


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
    hm_all = m2(b.index.hour * 100 + b.index.minute)
    day = np.array([str(x) for x in b.index.date])
    O, H, L, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    byday = {dd: np.flatnonzero(day == dd) for dd in np.unique(day)}
    res = []
    for r in T.itertuples():
        ix = byday.get(r.date)
        out = []
        sel = None
        if ix is not None:
            hm = hm_all[ix]
            t0 = m2(r.tod)
            sel = ix[(hm >= t0) & (hm <= min(t0 + 44, m2(1549)))]
            if not len(sel):
                sel = None
        for s in (1, -1):
            for sp, (up, dn, cap) in SPECS.items():
                if sel is None:
                    out += [np.nan, -1, -1]; continue
                e, R = r.entry, r.R
                tm = hm_all[sel] - m2(r.tod)
                k = sel[tm < cap]
                if not len(k):
                    out += [np.nan, -1, -1]; continue
                stop = e - s * dn * R
                hit_s = (L[k] <= stop) if s == 1 else (H[k] >= stop)
                if up is None:
                    hit_t = np.zeros(len(k), bool)
                else:
                    tgt = e + s * up * R
                    hit_t = (H[k] >= tgt) if s == 1 else (L[k] <= tgt)
                i_s = int(np.argmax(hit_s)) if hit_s.any() else 10**9
                i_t = int(np.argmax(hit_t)) if hit_t.any() else 10**9
                if i_s <= i_t and i_s < 10**9:
                    px = min(O[k[i_s]], stop) if s == 1 else max(O[k[i_s]], stop)
                    out += [px, 1, hm_all[k[i_s]] + 1]
                elif i_t < 10**9:
                    out += [tgt, 2, hm_all[k[i_t]] + 1]
                else:
                    out += [C[k[-1]], 0, hm_all[k[-1]] + 1]
        res.append((r.Index, *out))
    return res


def walk_cols():
    return [f"{a}_{'L' if s == 1 else 'S'}{sp}" for s in (1, -1) for sp in SPECS for a in ("px", "k", "x")]


def walk(T, half, procs=3):
    jobs = [(s, g, half) for s, g in T.groupby("symbol") if (CACHE / f"{s}.parquet").exists()]
    with Pool(procs) as p:
        out = [x for r in p.imap_unordered(walk_job, jobs, chunksize=4) for x in r]
    cols = []
    for s in ("L", "S"):
        for sp in SPECS:
            cols += [f"px_{s}{sp}", f"k_{s}{sp}", f"x_{s}{sp}"]
    a = pd.DataFrame(out, columns=["i"] + cols).set_index("i")
    return T.join(a)


def r_after_cost(e, R, tod, px, kind, side, dn):
    ecost = (0.01 + e * 1e-4) * tod_cost_mult(tod)
    xcost = np.where(kind == 2, 0.0, 0.01 + px * 1e-4) + np.where(kind == 1, 0.02, 0.0)
    gross = side * (px - e) / R
    return (gross - (ecost + xcost) / R) / dn


if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True)
    stage, half = sys.argv[2], sys.argv[3]
    if stage == "sig":
        if half == "check":
            assert (HERE / "fitsel.json").exists(), "freeze fitsel.json before loading any check data"
        sigs, pools, days = [], [], []
        with Pool(2) as p:
            for m, s, pl, d in p.imap_unordered(month_job, half_months(half)):
                print(m, len(s), len(pl), flush=True)
                sigs.append(s); pools.append(pl); days += d
        S = pd.concat(sigs, ignore_index=True)
        P = pd.concat(pools, ignore_index=True)
        for X in (S, P):
            X["entry"] = X["close"]
            X["R"] = 0.25 * X["atr_d"]
        no_locked(S.date.unique()); no_locked(P.date.unique()); no_locked(days)
        S.to_parquet(W / f"sig_{half}.parquet"); P.to_parquet(W / f"pool_{half}.parquet")
        pd.Series(sorted(days)).to_frame("date").to_parquet(W / f"days_{half}.parquet")
    elif stage == "walk":
        S = pd.read_parquet(W / f"sig_{half}.parquet")
        walk(S, half).to_parquet(W / f"walked_{half}.parquet")
        print("walked", len(S))
