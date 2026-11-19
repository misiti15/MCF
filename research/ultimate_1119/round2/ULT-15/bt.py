"""ULT-15 CONFLUENCE backtest (ultimate_1119 round2/PLAN.md sec. 1-2, 3 "ULT-15", 5, 6). Adapted from round2/ULT-14/bt.py.

Signals: lab frames (research/history2y/data/frames, 5-min decision bars, bar-close tod) + context (spy_fo); base,
triggers and trigger count from the LIVE module itself (modules/ULT-15.py: features(), base()). A superset (base at L2,
>= 2 counted triggers, both sides, shorts ETB only, L1 flag) is built once per half; every grid config is a sub-filter.
Base gate (FIT only, before any trigger is scored): per side x liquidity, ONE random base-eligible bar per base-eligible
symbol-session (numpy default_rng seeded from 1119, month, side, liquidity), walked through the chassis exit; the base
passes for an exit if its random avg R >= 0 in BOTH fit sub-halves A (2024-10 + 2025-03..05) and B (2025-06..09).
Chassis (round 2): entry at the OPEN of the 1-minute bar that starts at the decision-bar close (LR8 entry cost on it);
TX-n: no target, catastrophic stop at 2u around the decision close (u = 0.25 x prior-day daily ATR), time exit at the
close of minute entry+n-1 or the 15:49 minute; R per 2u (actual risk); r_u = R in 0.25-dATR units (x2). Walked on
1-minute bars (data/cache_hist/1Min): stop gap-through at the worse of open/stop.
Costs LR8 (entry (1c + 1bp) x tod mult; exit 1c + 1bp; +2c stops) + 1.2 bp of entry notional borrow fee on every short.
One lot per symbol (both sides share it); refire only >= 30 min after the exit; max 2 per symbol-session; day cap 30
over both sides (first by time, ties ADV20 desc). Halves: FIT = 2024-10 + 2025-03..09; CHECK = 2025-10-01..latest.
Locked 2024-11-01..2025-02-28 never read.
    python bt.py WORK sig fit|check ; python bt.py WORK walk fit|check ; python bt.py WORK base|fit|fitrandom|check|plateau
Educational only - not financial advice."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE.parents[1] / "benchmark"))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "never reads the locked block"
from mcf.research.gates import tod_cost_mult  # noqa: E402

DATA = Path("/home/user/MCF/research/history2y/data")
CACHE = Path("/home/user/MCF/data/cache_hist/1Min")
LOCK = ("2024-11-01", "2025-02-28")
FIT_MONTHS = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 10)]
MOD = HERE.parents[1] / "modules" / "ULT-15.py"
N_CUM = 774
DAY_CAP = 30
BORROW = 1.2e-4
EXITS = {"X30": 30, "X45": 45}
LIQ = {"L1": {1: (200e6, 0.05), -1: (100e6, 0.05)}, "L2": {1: (50e6, 0.08), -1: (50e6, 0.08)}}
WIN = {1: (1030, 1500), -1: (1100, 1500)}


def no_locked(dates):
    s = pd.Series([str(x) for x in dates])
    assert not ((s >= LOCK[0]) & (s <= LOCK[1])).any(), "locked block row found"


def load_mod():
    spec = importlib.util.spec_from_file_location("ult15", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def etb_set():
    u = pd.read_csv(ROOT / "data" / "universe.csv")
    return set(u.loc[u.easy_to_borrow.astype(str).str.lower() == "true", "symbol"].astype(str))


def half_months(half):
    import research.history2y.lib as lib
    lib.DATA = DATA
    ms = [m for m in lib.months() if m not in lib.LOCKED_MONTHS]
    return FIT_MONTHS if half == "fit" else [m for m in ms if m >= "2025-10"]


def m2(t):
    t = np.asarray(t, int)
    return (t // 100) * 60 + t % 100


def hhmm(mins):
    mins = np.asarray(mins, int)
    return (mins // 60) * 100 + mins % 60


# ---------------------------------------------------------------- stage 1: signal superset + base random bars
def month_job(month):
    import research.history2y.lib as lib
    lib.DATA = DATA
    mod = load_mod()
    f = lib.load_month(month, context=True)
    f = f[[c for c in f.columns if not (c.startswith(("win_", "r_long", "r_short")) or "heat" in c.lower())]]
    assert not any(c.startswith(("win_", "r_long", "r_short")) or "heat" in c.lower() for c in f.columns)
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    no_locked(f["date"].unique())
    r = mod.features(f)
    adv = f["adv20"].fillna(0).to_numpy()
    etb = f["symbol"].isin(etb_set()).to_numpy()
    cols = ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap"]
    sig, rnd = [], []
    mi = int(month.replace("-", ""))
    for sgn in (1, -1):
        ok_side = etb if sgn < 0 else np.ones(len(f), bool)
        bl = {}
        for lv in ("L1", "L2"):
            a, cm = LIQ[lv][sgn]
            bl[lv] = mod.base(r, sgn, cm) & (adv >= a) & ok_side
        n = r["n_long"] if sgn > 0 else r["n_short"]
        mk = bl["L2"] & (n >= 2)
        s = f.loc[mk, cols].copy()
        s["side"] = sgn
        s["ntrig"] = n[mk]
        s["liq1"] = bl["L1"][mk]
        for k in ("TL1", "TL2", "TL3", "TS1", "TS2", "TS3"):
            s[k] = r[k][mk] if k[1] == ("L" if sgn > 0 else "S") else False
        sig.append(s)
        for j, lv in enumerate(("L1", "L2")):
            rng = np.random.default_rng([1119, mi, 2 + sgn, j])
            idx = np.flatnonzero(bl[lv])
            if not len(idx):
                continue
            g = pd.Series(idx).groupby(f["symbol"].to_numpy()[idx] + "|" + f["date"].to_numpy()[idx], sort=True)
            pick = [int(v.to_numpy()[rng.integers(len(v))]) for _, v in g]
            b = f.loc[pick, cols].copy()
            b["side"] = sgn
            b["liq"] = lv
            rnd.append(b)
    S = pd.concat(sig, ignore_index=True)
    B = pd.concat(rnd, ignore_index=True)
    days = sorted(str(x) for x in set(lib.load_context(month)["date"]))
    return month, S, B, days


# ---------------------------------------------------------------- stage 2: 1-minute walk (TX30 / TX45, side-aware)
def walk_job(args):
    sym, T, seed = args
    d = pads.dataset(str(CACHE / f"{sym}.parquet"), format="parquet")
    fld = pads.field("__index_level_0__")
    tz = "America/New_York"
    dmin = pd.Timestamp(min(T.date), tz=tz)
    dmax = pd.Timestamp(max(T.date), tz=tz) + pd.Timedelta(days=1)
    L0, L1 = pd.Timestamp("2024-11-01", tz=tz), pd.Timestamp("2025-03-01", tz=tz)
    b = d.to_table(filter=((fld < L0) | (fld >= L1)) & (fld >= dmin) & (fld < dmax)).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(tz)
    b = b.sort_index()
    no_locked(np.unique(b.index.date))
    hm_all = (b.index.hour * 100 + b.index.minute).to_numpy()
    day = b.index.date.astype(str)
    O, Hh, Lo, Cc = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    byday = {}
    if len(day):
        st = np.flatnonzero(np.r_[True, day[1:] != day[:-1]])
        en = np.r_[st[1:], len(day)]
        byday = {day[a]: np.arange(a, e) for a, e in zip(st, en)}

    def path(ix, j0, sgn, stop, tend):
        px, kd, xt = None, 0, None
        for q in ix[j0:]:
            if hm_all[q] > tend:
                break
            if sgn > 0 and Lo[q] <= stop:
                px, kd, xt = min(O[q], stop), 1, hm_all[q]; break
            if sgn < 0 and Hh[q] >= stop:
                px, kd, xt = max(O[q], stop), 1, hm_all[q]; break
            px, xt = Cc[q], hm_all[q]
        return px, kd, xt

    def one(ix, tod, u, dclose, sgn):
        hm = hm_all[ix]
        j0 = np.searchsorted(hm, tod)
        if j0 >= len(ix) or m2(hm[j0]) - m2(tod) > 4 or hm[j0] >= 1550:
            return None
        e = O[ix[j0]]
        if dclose is None:          # random control: decision close = close of the minute before tod
            if j0 == 0 or m2(hm[j0 - 1]) < m2(tod) - 5:
                return None
            dclose = Cc[ix[j0 - 1]]
        res = [e, dclose]
        for g, n in EXITS.items():
            tend = min(int(hhmm(m2(hm[j0]) + n - 1)), 1549)
            p, k, x = path(ix, j0, sgn, dclose - sgn * 2 * u, tend)
            if p is None:
                return None
            res += [p, k, int(hhmm(m2(x) + 1))]
        return tuple(res)

    res = []
    for r in T.itertuples():
        ix = byday.get(r.date)
        u = 0.25 * r.atr_d
        a = None if ix is None else one(ix, r.tod, u, None if r.random else r.close, int(r.side))
        res.append((r.Index,) + (a if a else (np.nan,) * 8))
    return res


def cost_R(side, tod, e, px, kd, u, borrow=True):
    ec = (0.01 + e * 1e-4) * tod_cost_mult(tod)
    xc = np.where(kd == 2, 0.0, 0.01 + px * 1e-4) + np.where(kd == 1, 0.02, 0.0)
    bf = np.where((side < 0) & borrow, BORROW * e, 0.0)
    return (side * (px - e) - ec - xc - bf) / u


def walk(T, random=False):
    T = T.reset_index(drop=True).copy()
    no_locked(T["date"].unique())
    T["random"] = random
    jobs = [(s, g, 1119 + i) for i, (s, g) in enumerate(T.groupby("symbol")) if (CACHE / f"{s}.parquet").exists()]
    with Pool(3) as p:
        out = [x for r in p.imap_unordered(walk_job, jobs, chunksize=4) for x in r]
    a = pd.DataFrame(out, columns=["i", "e", "dclose", "px30", "kd30", "xt30", "px45", "kd45", "xt45"]).set_index("i")
    T = T.drop(columns=["random"]).join(a)
    u2 = 2 * 0.25 * T.atr_d.to_numpy()
    tod = T.tod.to_numpy()
    sd = T.side.to_numpy()
    for g in ("30", "45"):
        T["r" + g] = cost_R(sd, tod, T.e.to_numpy(), T["px" + g].to_numpy(), T["kd" + g].to_numpy(), u2)
        T["rsc" + g] = cost_R(sd, tod, T.dclose.to_numpy(), T["px" + g].to_numpy(), T["kd" + g].to_numpy(), u2,
                              borrow=False)                        # bias diagnostic: signal-close fill, no borrow
        T["xmin" + g] = np.where(T["xt" + g].notna(), m2(T["xt" + g].fillna(0)), np.nan)
    return T


def bind(T, ex):
    """Expose exit ex ('X30'/'X45') under the generic names stats() reads (r, kd, xmin, hold, r_sigclose, r_u)."""
    g = ex[1:]
    T = T.copy()
    T["r"], T["kd"], T["xmin"], T["r_sigclose"] = T["r" + g], T["kd" + g], T["xmin" + g], T["rsc" + g]
    T["r_u"] = 2.0 * T["r"]
    T["hold"] = T["xmin"] - m2(T.tod)
    return T


# ---------------------------------------------------------------- stage 3: configs + chassis
def configs():
    out, names = {}, iter("abcdefgh")
    for c in (2, 3):
        for ex in ("X30", "X45"):
            for lv in ("L1", "L2"):
                out["15" + next(names)] = dict(conf=c, exit=ex, liq=lv, label=f"C{c}of3-T{ex}-{lv}")
    return out


def select(S, cfg, sides, cap=DAY_CAP):
    S = bind(S, cfg["exit"])
    m = (S.ntrig >= cfg["conf"]) & S.r.notna() & S.side.isin(sides)
    if cfg["liq"] == "L1":
        m &= S.liq1.astype(bool)
    s = S[m].sort_values(["symbol", "date", "tod", "side"], kind="mergesort")
    keep = []
    for _, g in s.groupby(["symbol", "date"], sort=False):
        n, free_at = 0, -1
        for i, t, x in zip(g.index, m2(g.tod.to_numpy()), g.xmin.to_numpy()):
            if n >= 2:
                break
            if t >= free_at:
                keep.append(i); n += 1; free_at = x + 30
    s = S.loc[keep].sort_values(["date", "tod", "adv20"], ascending=[True, True, False], kind="mergesort")
    if cap:
        s = s.groupby("date", sort=False).head(cap)
    return s


# ---------------------------------------------------------------- stage 4: statistics
SPY = None


def spy_types():
    global SPY
    if SPY is None:
        from stats import spy_days
        SPY = spy_days()
    return SPY


def stats(t, n_sessions, col="r", sides=True):
    t = t[t[col].notna()]
    if not len(t):
        return {"trades": 0, "sessions": int(n_sessions), "trades_per_session": 0.0, "total_r_wo_best_day": 0.0,
                "avg_r": None, "long": {"trades": 0}, "short": {"trades": 0}}
    day = t.groupby("date")[col].sum()
    tot = float(t[col].sum())
    avg = float(t[col].mean())
    best = day.idxmax()
    dev = (t[col] - avg).groupby(t["date"]).sum()
    se = float(np.sqrt((dev ** 2).sum())) / len(t)
    tps = len(t) / day.size
    ty = t.date.map(spy_types()["type"])
    o = {"trades": int(len(t)), "sessions": int(n_sessions), "sessions_traded": int(day.size),
         "trades_per_session": round(len(t) / n_sessions, 3), "win": round(float((t[col] > 0).mean()), 3),
         "avg_r": round(avg, 4), "avg_r_u025": round(float(t["r_u"].mean()), 4),
         "avg_r_wo_best_day": round(float(t.loc[t.date != best, col].mean()), 4)
         if (t.date != best).any() else None, "best_day": str(best),
         "best_day_r": round(float(day.max()), 2),
         "best_day_share": round(float(day.max() / tot), 3) if tot > 0 else None, "total_r": round(tot, 2),
         "total_r_wo_best_day": round(tot - float(day.max()), 2),
         "total_r_per_session": round(tot / n_sessions, 4), "worst_day": round(float(day.min()), 2),
         "worst_day_date": str(day.idxmin()),
         "worst_day_per_trade_session": round(float(day.min()) / tps, 3),
         "t_day_clustered": round(avg / se, 2) if se > 0 else None}
    for k in ("up", "flat", "down"):
        x = t.loc[ty == k, col]
        o[f"avg_r_spy_{k}"] = round(float(x.mean()), 4) if len(x) else None
        o[f"n_spy_{k}"] = int(len(x))
    ex = t[~t.date.between("2025-04-03", "2025-04-09")]
    o["avg_r_ex_0403_0409"] = round(float(ex[col].mean()), 4) if len(ex) else None
    o["n_ex_0403_0409"] = int(len(ex))
    o["median_hold_min"] = float(np.nanmedian(t["hold"]))
    o["exit_mix"] = {k: int(v) for k, v in t.kd.map({0: "time", 1: "stop", 2: "target"}).value_counts().items()}
    d = sorted(t.date.unique())
    if len(d) > 1:
        mid = d[len(d) // 2]
        o["first_half_avg_r"] = round(float(t.loc[t.date < mid, col].mean()), 4)
        o["second_half_avg_r"] = round(float(t.loc[t.date >= mid, col].mean()), 4)
    if sides:
        for nm, sg in (("long", 1), ("short", -1)):
            x = t[t.side == sg]
            o[nm] = ({k: v for k, v in stats(x, n_sessions, col, sides=False).items()
                      if k in ("trades", "trades_per_session", "win", "avg_r", "avg_r_wo_best_day", "best_day_share",
                               "total_r", "t_day_clustered", "worst_day", "avg_r_ex_0403_0409", "first_half_avg_r",
                               "second_half_avg_r", "avg_r_spy_up", "avg_r_spy_flat", "avg_r_spy_down")}
                     if len(x) else {"trades": 0})
    return o


def sub_halves(t):
    a = t[(t.date < "2025-06-01")]
    b = t[(t.date >= "2025-06-01")]
    return {"A_avg_r": round(float(a.r.mean()), 4) if len(a) else None, "A_n": int(len(a)),
            "B_avg_r": round(float(b.r.mean()), 4) if len(b) else None, "B_n": int(len(b))}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def random_control(sel, cfg, seed=1119):
    """Same symbol-sessions, sides and count as the selected trades; a random decision bar in the side's window; same
    exit (the bar need not meet the base's tape rule - the base gate is the base read)."""
    rng = np.random.default_rng(seed)
    R = sel[["symbol", "date", "atr_d", "close", "tod", "side"]].copy()
    tods = []
    for sd in R.side.to_numpy():
        lo, hi = WIN[int(sd)]
        tods.append(int(hhmm(rng.choice(np.arange(m2(lo), m2(hi) + 1, 5)))))
    R["tod"] = tods
    W = walk(R, random=True)
    return bind(W, cfg["exit"])


def load_half(work, half, what="walked"):
    S = pd.read_parquet(Path(work) / f"{what}_{half}.parquet")
    no_locked(S.date.unique())
    days = pd.read_parquet(Path(work) / f"days_{half}.parquet").date.tolist()
    no_locked(days)
    return S, len(days)


def rand_block(t, cfg):
    Rc = random_control(t, cfg)
    ok = Rc.r.notna().to_numpy() & t.r.notna().to_numpy()
    tr = t.r.to_numpy()
    o = {"random_avg_r": round(float(Rc.r[ok].mean()), 4),
         "signal_minus_random": round(float(tr[ok].mean() - Rc.r[ok].mean()), 4), "random_n": int(ok.sum())}
    for nm, sg in (("long", 1), ("short", -1)):
        k = ok & (t.side.to_numpy() == sg)
        if k.any():
            o[f"random_avg_r_{nm}"] = round(float(Rc.r[k].mean()), 4)
            o[f"signal_minus_random_{nm}"] = round(float(tr[k].mean() - Rc.r[k].mean()), 4)
    return o


def base_eval(B):
    """Base gate numbers per side x liquidity x exit: random avg R in fit sub-halves A and B (and all FIT)."""
    out = {}
    for sgn, nm in ((1, "long"), (-1, "short")):
        for lv in ("L1", "L2"):
            x = B[(B.side == sgn) & (B.liq == lv)]
            o = {"n": int(len(x))}
            for ex in EXITS:
                y = bind(x, ex)
                y = y[y.r.notna()]
                a, b = y[y.date < "2025-06-01"].r, y[y.date >= "2025-06-01"].r
                o[ex] = {"all_avg_r": round(float(y.r.mean()), 4) if len(y) else None, "n": int(len(y)),
                         "A_avg_r": round(float(a.mean()), 4) if len(a) else None, "A_n": int(len(a)),
                         "B_avg_r": round(float(b.mean()), 4) if len(b) else None, "B_n": int(len(b)),
                         "all_avg_r_u025": round(float(y.r_u.mean()), 4) if len(y) else None,
                         "avg_r_ex_0403_0409": round(float(y[~y.date.between("2025-04-03", "2025-04-09")].r.mean()), 4)
                         if len(y) else None}
                o[ex]["pass"] = bool(len(a) and len(b) and a.mean() >= 0 and b.mean() >= 0)
            out[f"{nm}_{lv}"] = o
    return out


def sides_for(gate, cfg):
    return [sg for sg, nm in ((1, "long"), (-1, "short")) if gate[f"{nm}_{cfg['liq']}"][cfg["exit"]]["pass"]]


if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True)
    stage = sys.argv[2]
    if stage == "sig":
        half = sys.argv[3]
        if half == "check":
            assert (HERE / "fitsel.json").exists(), "freeze fitsel.json before any check data is built"
        sigs, rnds, days = [], [], []
        with Pool(2) as p:
            for m, s, b, d in p.imap_unordered(month_job, half_months(half)):
                print(m, len(s), int((s.side > 0).sum()), int((s.side < 0).sum()), "base rnd", len(b), flush=True)
                sigs.append(s); rnds.append(b); days += d
        S = pd.concat(sigs, ignore_index=True)
        B = pd.concat(rnds, ignore_index=True)
        for X in (S, B):
            X["date"] = X["date"].astype(str)
            no_locked(X.date.unique())
        no_locked(days)
        S.to_parquet(W / f"sig_{half}.parquet")
        B.to_parquet(W / f"base_{half}.parquet")
        pd.DataFrame({"date": sorted(days)}).to_parquet(W / f"days_{half}.parquet")
    elif stage == "walk":
        half = sys.argv[3]
        if half == "check":
            assert (HERE / "fitsel.json").exists()
        for what in ("base", "sig"):
            S = pd.read_parquet(W / f"{what}_{half}.parquet")
            t0 = time.time()
            T = walk(S, random=False)
            T.to_parquet(W / f"walked{what}_{half}.parquet")
            print("walked", what, len(T), int(T.r45.isna().sum()), "no path", round(time.time() - t0), "s", flush=True)
    elif stage == "base":
        assert not (HERE / "fit_grid.json").exists(), "base gate is decided before any trigger is scored"
        B, _ = load_half(W, "fit", "walkedbase")
        g = base_eval(B)
        g["note"] = ("Educational only - not financial advice. ULT-15 base gate (FIT only, scored before any trigger): "
                     "one random base-eligible bar per base-eligible symbol-session; pass = random avg R >= 0 in both "
                     "fit sub-halves A and B, per exit.")
        g["frozen_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        (HERE / "base_gate.json").write_text(json.dumps(g, indent=1, default=float))
        print(json.dumps(g, indent=1, default=float))
    elif stage == "fit":
        gate = json.loads((HERE / "base_gate.json").read_text())
        S, n = load_half(W, "fit", "walkedsig")
        res, ungated = {}, {}
        for name, cfg in configs().items():
            sides = sides_for(gate, cfg)
            t = select(S, cfg, sides)
            o = stats(t, n)
            if len(t):
                o.update(sub_halves(t))
            o["sides_on"] = sides
            o["cfg"] = cfg
            res[name] = o
            tu = select(S, cfg, [1, -1])        # diagnostic only: the same config with the base gate ignored
            ou = stats(tu, n)
            ou.update(sub_halves(tu) if len(tu) else {})
            ungated[name] = {k: ou.get(k) for k in ("trades_per_session", "avg_r", "avg_r_wo_best_day", "total_r",
                                                     "total_r_wo_best_day", "A_avg_r", "B_avg_r",
                                                     "avg_r_ex_0403_0409")}
            ungated[name]["long"] = {k: ou["long"].get(k) for k in ("trades", "avg_r", "total_r")}
            ungated[name]["short"] = {k: ou["short"].get(k) for k in ("trades", "avg_r", "total_r")}
            print(name, cfg["label"], "sides", sides, o["trades_per_session"], o.get("avg_r"),
                  o.get("avg_r_wo_best_day"), o.get("total_r"), o.get("total_r_wo_best_day"), "| ungated",
                  ungated[name], flush=True)
        grid = dict(res)
        scored = {k: v for k, v in grid.items() if v["trades"] > 0}
        elig = {k: v for k, v in scored.items() if v["trades_per_session"] >= 2.0}
        pool = elig if elig else scored
        pick = (max(pool, key=lambda k: (pool[k]["total_r_wo_best_day"], -list(grid).index(k))) if pool else None)
        ue = {k: v for k, v in ungated.items() if (v["trades_per_session"] or 0) >= 2.0}
        upool = ue if ue else ungated
        upick = max(upool, key=lambda k: (upool[k]["total_r_wo_best_day"], -list(grid).index(k)))
        (HERE / "fit_grid.json").write_text(json.dumps({"gated": res, "ungated_diagnostic": ungated}, indent=1,
                                                       default=float))
        fs = {"note": "Educational only - not financial advice. ULT-15 fit pick, frozen BEFORE any check data is built.",
              "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "pick": pick,
              "cfg": grid[pick]["cfg"] if pick else None, "sides_on": grid[pick]["sides_on"] if pick else [],
              "eligible_2_per_session": sorted(elig), "configs_with_any_side_open": sorted(scored),
              "rule": "max fit total R minus best fit day among configs >= 2.0/session whose base passed (PLAN sec. 5)",
              "fit": grid[pick] if pick else None, "sha256_bt": sha(__file__), "sha256_module_at_freeze": sha(MOD),
              "configs_counted_this_candidate": 14,
              "configs_note": "8 grid + 4 base-gate evaluations + 1 bias diagnostic (PLAN sec. 4) + 1 ungated "
                              "diagnostic check score",
              "n_cumulative": N_CUM,
              "diagnostic_ungated_pick": upick, "diagnostic_ungated_cfg": grid[upick]["cfg"],
              "diagnostic_ungated_fit": ungated[upick],
              "diagnostic_note": ("Added 2026-11-19 after the base gate closed every side and BEFORE any check data: the "
                                  "same selection rule applied with the base gate ignored, frozen here, scored once on "
                                  "check as a DIAGNOSTIC (counted, +1 config). It cannot change the tier: the "
                                  "pre-registered rule says a config whose bases fail scores nothing.")}
        (HERE / "fitsel.json").write_text(json.dumps(fs, indent=1, default=float))
        print("PICK", pick, "eligible:", sorted(elig), "scored:", sorted(scored))
    elif stage == "check":
        fs = json.loads((HERE / "fitsel.json").read_text())
        assert fs["pick"], "no fit pick: nothing to score"
        assert not (HERE / "check_once.json").exists(), "check is scored ONCE"
        S, n = load_half(W, "check", "walkedsig")
        cfg = fs["cfg"]
        sides = fs["sides_on"]
        t = select(S, cfg, sides)
        o = stats(t, n)
        o["bias_diag_sigclose_noborrow_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        o["uncapped"] = {k: v for k, v in stats(select(S, cfg, sides, cap=0), n, sides=False).items()
                         if k in ("trades", "trades_per_session", "avg_r", "avg_r_wo_best_day", "t_day_clustered")}
        o.update(rand_block(t, cfg))
        z = max(1.5, float(np.sqrt(2 * np.log(N_CUM))))
        fit = fs["fit"]
        tierA = (o["avg_r"] > 0 and (o["avg_r_wo_best_day"] or -1) > 0 and fit["avg_r"] > 0
                 and o["trades_per_session"] >= 2.0)
        beats = (tierA and o["avg_r"] > 0.0836 and o["avg_r_wo_best_day"] > 0.0734 and o["total_r_per_session"] > 0
                 and o["worst_day_per_trade_session"] >= -2.152 and (o["t_day_clustered"] or 0) >= z)
        tierB = fit["avg_r"] > 0 and o["avg_r"] > -0.02
        o["t_bar"] = round(z, 3)
        o["tier"] = "BEATS" if beats else ("A" if tierA else ("B" if tierB else "FAIL"))
        o["pick"] = fs["pick"]
        o["scored_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        (HERE / "check_once.json").write_text(json.dumps(o, indent=1, default=float))
        print(json.dumps(o, indent=1, default=float))
    elif stage == "checkdiag":
        fs = json.loads((HERE / "fitsel.json").read_text())
        assert not (HERE / "check_diag_ungated.json").exists(), "diagnostic is scored ONCE"
        S, n = load_half(W, "check", "walkedsig")
        cfg = fs["diagnostic_ungated_cfg"]
        t = select(S, cfg, [1, -1])
        o = stats(t, n)
        o["bias_diag_sigclose_noborrow_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        o.update(rand_block(t, cfg))
        o["t_bar"] = round(max(1.5, float(np.sqrt(2 * np.log(N_CUM + 1)))), 3)
        o["pick"] = fs["diagnostic_ungated_pick"]
        o["note"] = "DIAGNOSTIC ONLY (base gate ignored); cannot set the tier"
        o["scored_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        (HERE / "check_diag_ungated.json").write_text(json.dumps(o, indent=1, default=float))
        print(json.dumps(o, indent=1, default=float))
    elif stage == "fitranddiag":
        fs = json.loads((HERE / "fitsel.json").read_text())
        S, n = load_half(W, "fit", "walkedsig")
        t = select(S, fs["diagnostic_ungated_cfg"], [1, -1])
        o = rand_block(t, fs["diagnostic_ungated_cfg"])
        o["bias_diag_sigclose_noborrow_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        (HERE / "fit_random_diag.json").write_text(json.dumps(o, indent=1, default=float))
        print(o)
    elif stage == "checkbase":
        assert (HERE / "check_once.json").exists(), "reporting only, after the single check score"
        B, _ = load_half(W, "check", "walkedbase")
        g = base_eval(B)
        (HERE / "check_base_random.json").write_text(json.dumps(g, indent=1, default=float))
        print(json.dumps(g, indent=1, default=float))
    elif stage == "plateau":
        assert (HERE / "check_once.json").exists(), "plateau only after the single check score"
        gate = json.loads((HERE / "base_gate.json").read_text())
        S, n = load_half(W, "check", "walkedsig")
        res = {}
        for name, cfg in configs().items():
            row = {"label": cfg["label"]}
            for tag, sides in (("gated", sides_for(gate, cfg)), ("ungated", [1, -1])):
                t = select(S, cfg, sides)
                o = stats(t, n)
                row[tag] = {k: o.get(k) for k in ("trades_per_session", "avg_r", "avg_r_wo_best_day", "best_day_share",
                                                   "total_r", "t_day_clustered", "worst_day_per_trade_session",
                                                   "first_half_avg_r", "second_half_avg_r")}
                row[tag]["long_avg_r"] = o["long"].get("avg_r"); row[tag]["long_n"] = o["long"].get("trades")
                row[tag]["short_avg_r"] = o["short"].get("avg_r"); row[tag]["short_n"] = o["short"].get("trades")
            res[name] = row
            print(name, row, flush=True)
        (HERE / "check_plateau.json").write_text(json.dumps(res, indent=1, default=float))
    elif stage == "fitrandom":
        fs = json.loads((HERE / "fitsel.json").read_text())
        S, n = load_half(W, "fit", "walkedsig")
        t = select(S, fs["cfg"], fs["sides_on"])
        o = rand_block(t, fs["cfg"])
        o["bias_diag_sigclose_noborrow_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        o["uncapped"] = {k: v for k, v in stats(select(S, fs["cfg"], fs["sides_on"], cap=0), n, sides=False).items()
                         if k in ("trades", "trades_per_session", "avg_r", "avg_r_wo_best_day", "t_day_clustered")}
        (HERE / "fit_random.json").write_text(json.dumps(o, indent=1, default=float))
        print(o)
