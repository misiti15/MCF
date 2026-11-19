"""ULT-06 late morning-turn long: backtest per research/ultimate_1119/PLAN.md (Workbench Mechanic 2026-11-19).

Signals  lab frames (research/history2y/data/frames + context), the candidate MODULE's own mask
         (research/ultimate_1119/modules/ULT-06-late-morning-turn-long.py, make_mask per grid config) & YAML-side
         filters: point-in-time ADV20 >= $20M, bar close inside the config window W (union 10:30..12:00 ET). Entry = decision-bar close, R = 0.25 x ATR_d.
Exits    1-minute bars (data/cache_hist/1Min) from the minute starting at the decision bar close, as benchmark/bench.py:
         stop checked first in a minute, then target; stop gap-through at the worse of open/stop; flat 15:50.
           TX30 / TX45: time exit after 30 / 45 min with a catastrophic stop at -2R (R = 0.25 ATR; results in that R)
Chain    one lot per symbol; the next entry on the symbol only at a decision bar >= exit time + 30 min; max 2 per
         symbol-session; day cap 30 entries (first by time, ties by ADV20 desc).
Costs    LR8 research basis (mcf.research.gates): entry 1c + 1 bp x time-of-day multiplier; exit 1c + 1 bp except target
         limit fills; +2c on stops; x3 extended tier.
Halves   FIT = 2024-10 + 2025-03..2025-09; CHECK = 2025-10-01..latest. The locked block 2024-11-01..2025-02-28 is
         never read (month list excludes it, pyarrow filters on 1-minute loads, asserts on every frame / trade list).
    python bt.py WORK cand fit            union candidates (grid superset) + control pools, fit months
    python bt.py WORK walk fit            1-minute exits
    python bt.py WORK score fit           8 grid configs (+ uncapped diag of the selected) -> fit_grid.csv, fitsel.json
    python bt.py WORK cand check [all]    check half: only the frozen config's mask (or the full grid with 'all', plateau)
Educational only - not financial advice."""
from __future__ import annotations

import importlib.util
import json
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
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())
LOCKED_MONTHS = {"2024-11", "2024-12", "2025-01", "2025-02"}
FIT_MONTHS = ["2024-10", "2025-03", "2025-04", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09"]
MOD_PATH = ROOT / "research/ultimate_1119/modules/ULT-06-late-morning-turn-long.py"
TZ = "America/New_York"
COLS = ["symbol", "date", "tod", "close", "low", "fromOpen", "atr_d", "dist_lod_atr", "rsiSlope", "gap", "adv20"]
EXITS = ["TX30", "TX45"]
WINDOWS = {"W1": (1050, 1130), "W2": (1030, 1200)}


def grid():
    out = []
    k = 0
    for w in ("W1", "W2"):
        for rcl in (0.3, 0.5):
            for ex in EXITS:
                out.append(dict(name="06" + "abcdefgh"[k], window=w, lo=WINDOWS[w][0], hi=WINDOWS[w][1], rcl=rcl,
                                exit=ex))
                k += 1
    return out


def no_locked(dates):
    d = pd.to_datetime(pd.Series(list(dates))).dt.date
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def load_mod():
    spec = importlib.util.spec_from_file_location("ult06", MOD_PATH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def half_months(half):
    import research.history2y.lib as lib
    lib.DATA = DATA
    ms = [m for m in lib.months() if m not in LOCKED_MONTHS]
    return FIT_MONTHS if half == "fit" else [m for m in ms if m >= "2025-10"]


def cand_job(args):
    month, W, half, which = args
    import research.history2y.lib as lib
    lib.DATA = DATA
    mod = load_mod()
    f = lib.load_month(month, columns=COLS, context=True)
    f["symbol"] = f["symbol"].astype(str)
    no_locked(f["date"].unique())
    if half == "check":
        assert all(str(d) >= "2025-10-01" for d in f["date"].unique())
    tod = f["tod"].to_numpy()
    if which == "union":
        lo, hi, rcl = 1030, 1200, 0.3
    else:
        p = json.loads(which)
        lo, hi, rcl = p["lo"], p["hi"], p["rcl"]
    # the mask is computed on the full frame (09:50..15:00 rows) so the new-low look-back and SPY minimum see every bar
    base = (f["adv20"].fillna(0).to_numpy() >= 20e6) & (tod >= lo) & (tod <= hi)
    m = mod.make_mask(rcl)(f) & base
    close, atr = f["close"].to_numpy(float), f["atr_d"].to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        cost_r = (2 * (0.01 + close * 1e-4) + 0.02) / (0.25 * atr)
    f["spyturn"] = mod.spy_turn(f)
    f["cost_r"] = cost_r
    keep = ["symbol", "date", "tod", "close", "atr_d", "gap", "adv20", "fromOpen", "dist_lod_atr", "rsiSlope", "spyturn"]
    c = f.loc[m, keep].assign(kind="sig")
    rng = np.random.default_rng(int(month.replace("-", "")))
    # control (a): same symbol-session, 6 random decision bars in the union window (intake price / cost only)
    intake = base & (close >= 10) & (atr > 0) & (np.abs(f["gap"].to_numpy(float)) < 20) & (cost_r <= 0.10)
    sd = set(zip(c.symbol, c.date))
    pool_a = f.loc[intake & np.array([(s, d) in sd for s, d in zip(f.symbol, f.date)]), keep]
    pool_a = pool_a.sample(frac=1.0, random_state=int(rng.integers(1 << 30)))
    a = pool_a[pool_a.groupby(["symbol", "date"]).cumcount() < 6].assign(kind="ctlA")
    # control (b): same moment (date, tod) as any signal, 3 random intake-U names (no trigger required)
    mom = set(zip(c.date, c.tod))
    pool_b = f.loc[intake & np.array([(d, t) in mom for d, t in zip(f.date, f.tod)]), keep]
    pool_b = pool_b.sample(frac=1.0, random_state=int(rng.integers(1 << 30)))
    b = pool_b[pool_b.groupby(["date", "tod"]).cumcount() < 3].assign(kind="ctlB")
    o = pd.concat([c, a, b], ignore_index=True)
    no_locked(o["date"].unique())
    o.to_parquet(Path(W) / f"cand_{half}_{month}.parquet")
    return month, int(m.sum()), len(a), len(b)


def walk_job(args):
    sym, T, lo, hi = args
    d = pads.dataset(str(CACHE / f"{sym}.parquet"), format="parquet")
    fld = pads.field("__index_level_0__")
    L0, L1 = pd.Timestamp("2024-11-01", tz=TZ), pd.Timestamp("2025-03-01", tz=TZ)
    a, b = pd.Timestamp(lo, tz=TZ), pd.Timestamp(hi, tz=TZ) + pd.Timedelta(days=1)
    flt = (fld >= a) & (fld < b) & ((fld < L0) | (fld >= L1))
    x = d.to_table(filter=flt).to_pandas()
    if "__index_level_0__" in x.columns:
        x = x.set_index("__index_level_0__")
    x.index = pd.DatetimeIndex(x.index).tz_convert(TZ)
    x = x.sort_index()
    no_locked(np.unique(x.index.date))
    hhmm = x.index.hour * 100 + x.index.minute
    mins = (x.index.hour * 60 + x.index.minute).to_numpy()
    day = np.asarray(x.index.date).astype(str)
    O, H, Lo, C = (x[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    byday = {}
    if len(day):
        st = np.flatnonzero(np.r_[True, day[1:] != day[:-1]])
        en = np.r_[st[1:], len(day)]
        byday = {day[s]: np.arange(s, e) for s, e in zip(st, en)}
    res = []
    for r in T.itertuples():
        ix = byday.get(str(r.date))
        e, R = r.close, 0.25 * r.atr_d
        t0 = (r.tod // 100) * 60 + r.tod % 100
        row = [r.Index]
        if ix is None:
            res.append(row + [np.nan] * 3 * len(EXITS))
            continue
        sel = ix[(mins[ix] >= t0) & (hhmm[ix] <= 1549)]
        if not len(sel):
            res.append(row + [np.nan] * 3 * len(EXITS))
            continue
        for ex in EXITS:
            hold = 30 if ex == "TX30" else 45
            stop, tgt = e - 2.0 * R, None
            s2 = sel[mins[sel] < t0 + hold]
            px, kd, xt = None, 0, None
            for k in s2:
                if Lo[k] <= stop:
                    px, kd, xt = min(O[k], stop), 1, mins[k] + 1
                    break
                if tgt is not None and H[k] >= tgt:
                    px, kd, xt = tgt, 2, mins[k] + 1
                    break
            if px is None:
                k = s2[-1] if len(s2) else sel[0]
                px, kd, xt = C[k], 0, mins[k] + 1
            row += [px, kd, xt]
        res.append(row)
    return res


def cost_r(o, px, kind):
    tier = np.where((np.abs(o.gap) >= 20) | (o.close < 5), 3.0, 1.0)
    ecost = (0.01 + o.close * 1e-4) * tod_cost_mult(o.tod.to_numpy())
    xcost = np.where(kind == 2, 0.0, 0.01 + px * 1e-4) + np.where(kind == 1, 0.02, 0.0)
    R = 0.25 * o.atr_d
    return ((px - o.close) / R - tier * (ecost + xcost) / R).to_numpy(float)


def walk(W, half):
    c = pd.concat([pd.read_parquet(p) for p in sorted(Path(W).glob(f"cand_{half}_*.parquet"))], ignore_index=True)
    no_locked(c["date"].unique())
    lo, hi = str(min(c.date)), str(max(c.date))
    jobs = [(s, g, lo, hi) for s, g in c.groupby("symbol") if (CACHE / f"{s}.parquet").exists()]
    with Pool(3) as p:
        out = [x for r in p.imap_unordered(walk_job, jobs, chunksize=4) for x in r]
    cols = ["i"] + [f"{a}_{ex}" for ex in EXITS for a in ("px", "k", "xt")]
    a = pd.DataFrame(out, columns=cols).set_index("i")
    c = c.join(a)
    for ex in EXITS:
        ok = c[f"k_{ex}"].notna()
        c[f"r_{ex}"] = np.nan
        c.loc[ok, f"r_{ex}"] = cost_r(c[ok], c.loc[ok, f"px_{ex}"].to_numpy(float), c.loc[ok, f"k_{ex}"].to_numpy())
        c[f"hold_{ex}"] = c[f"xt_{ex}"] - ((c.tod // 100) * 60 + c.tod % 100)
    c.drop(columns=[f"px_{ex}" for ex in EXITS]).to_parquet(Path(W) / f"trades_{half}.parquet")
    print(len(c), "rows;", int(c[f"k_{EXITS[0]}"].isna().sum()), "without a 1-minute path")


def select_trades(c, cfg, cap=30):
    """The chain (one lot, 30 min after exit, max 2 per symbol-session) and the day cap for one config."""
    s = c[(c.kind == "sig") & (c.tod >= cfg["lo"]) & (c.tod <= cfg["hi"]) & (c.dist_lod_atr >= cfg["rcl"])]
    ex = cfg["exit"]
    s = s[s[f"r_{ex}"].notna()].sort_values(["symbol", "date", "tod"])
    keep = []
    for (_, _), g in s.groupby(["symbol", "date"], sort=False):
        nxt, n = -1, 0
        for i, t, xt in zip(g.index, g.tod.to_numpy(), g[f"xt_{ex}"].to_numpy()):
            tm = (t // 100) * 60 + t % 100
            if n >= 2:
                break
            if tm >= nxt:
                keep.append(i)
                n += 1
                nxt = xt + 30
    s = s.loc[keep].copy()
    if cap:
        s = s.sort_values(["date", "tod", "adv20"], ascending=[True, True, False])
        s = s[s.groupby("date").cumcount() < cap]
    s["R"] = s[f"r_{ex}"]
    s["hold"] = s[f"hold_{ex}"]
    return s.sort_values(["date", "tod", "symbol"])


def spy_daytype(lo, hi):
    d = pads.dataset(str(CACHE / "SPY.parquet"), format="parquet")
    fld = pads.field("__index_level_0__")
    L0, L1 = pd.Timestamp("2024-11-01", tz=TZ), pd.Timestamp("2025-03-01", tz=TZ)
    x = d.to_table(filter=(fld >= pd.Timestamp(lo, tz=TZ)) & (fld < pd.Timestamp(hi, tz=TZ) + pd.Timedelta(days=1))
                   & ((fld < L0) | (fld >= L1))).to_pandas()
    if "__index_level_0__" in x.columns:
        x = x.set_index("__index_level_0__")
    x.index = pd.DatetimeIndex(x.index).tz_convert(TZ)
    m = x.index.hour * 100 + x.index.minute
    x = x[(m >= 930) & (m <= 1559)]
    no_locked(np.unique(x.index.date))
    g = x.groupby(np.asarray(x.index.date).astype(str))
    r = (g["close"].last() / g["open"].first() - 1) * 100
    return r.apply(lambda v: "up" if v >= 0.30 else ("down" if v <= -0.30 else "flat"))


def stats(s, sessions, dtype=None):
    n = len(s)
    if not n:
        return dict(trades=0, per_session=0.0, total=0.0)
    day = s.groupby("date")["R"].sum()
    tot = float(s.R.sum())
    bd = day.idxmax()
    nb = int((s.date == bd).sum())
    out = dict(trades=n, per_session=n / sessions, traded_sessions=int(day.size), win=float((s.R > 0).mean()),
               avg=float(s.R.mean()), avg_wo_best=(tot - day.max()) / (n - nb) if n > nb else float("nan"),
               best_share=(day.max() / tot) if tot > 0 else float("nan"), total=tot, r_session=tot / sessions,
               worst_day=float(day.min()), best_day=float(day.max()), best_date=str(bd),
               median_hold=float(s.hold.median()))
    dd = pd.to_datetime(s.date.astype(str))
    xa = ~((dd >= "2025-04-03") & (dd <= "2025-04-09"))
    out["avg_ex_apr3_9"] = float(s.R[xa.values].mean()) if xa.any() else float("nan")
    if dtype is not None:
        t = s.date.astype(str).map(dtype)
        for k in ("up", "flat", "down"):
            out[f"avg_{k}"] = float(s.R[(t == k).values].mean()) if (t == k).any() else float("nan")
            out[f"n_{k}"] = int((t == k).sum())
    return out


def n_sessions(half):
    import research.history2y.lib as lib
    lib.DATA = DATA
    ds = set()
    for m in half_months(half):
        ds |= set(lib.load_context(m)["date"].astype(str))
    no_locked(ds)
    return len(ds), sorted(ds)


if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True)
    stage, half = sys.argv[2], sys.argv[3]
    if stage == "cand":
        which = "union"
        if half == "check":
            fs = json.loads((HERE / "fitsel.json").read_text())
            which = "union" if (len(sys.argv) > 4 and sys.argv[4] == "all") else json.dumps(fs["config"])
        with Pool(2) as p:
            for r in p.imap_unordered(cand_job, [(m, str(W), half, which) for m in half_months(half)]):
                print(r, flush=True)
    elif stage == "walk":
        walk(W, half)
