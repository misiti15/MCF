"""ULT-29 EARN-CONFL backtest (ultimate_1119 round4/PLAN.md sec. 2, 3 "ULT-29", 4, 5, 6). Adapted from
round3/ULT-24/bt.py (same chassis, walk, gates and statistics).

Signals: lab frames + context (spy_fo); reaction days from round4/data/earnings_yf.parquet via the LIVE module's
rd_events() (rows dated in the locked block are dropped before use); bases EB-L / EB-S and the eight triggers from the
LIVE module (modules/ULT-29.py: features(), within()). Superset per half: every base row (EB-S: ETB only) with its
on-bar and within-3-bars trigger bits; every gate / grid config is a sub-filter.
Base gate (FIT only, before any trigger is scored): per base ONE random base-eligible bar per base-eligible
symbol-session (numpy default_rng([1119, month, base])), walked through TX-45 (X) and t1s1 cap45 (H); a base opens for
an exit if its random avg R >= 0 in BOTH fit sub-halves A (2024-10 + 2025-03..05) and B (2025-06..09).
Trigger gate (FIT only, after the base gate, before any confluence is scored): per (base open under >= 1 exit,
trigger): rows where the trigger is true on the bar, chassis chain without day cap, TX-45; survives if signal avg R minus
the base's random avg R (TX-45) >= 0 in BOTH sub-halves.
Chassis: entry at the OPEN of the 1-minute bar starting at the decision-bar close (LR8 entry cost); u = 0.25 x prior-day
daily ATR. X = TX-45: 2u catastrophic stop, no target, time exit at the close of minute entry+44 or 15:49, R per 2u.
H = t1s1 cap45: +1u limit (no exit cost) / -1u stop, R per u. Stop first, gap-through at the worse of open/stop, +2c
on stops. LR8 costs; on a reaction-day bar with decision tod < 10:30 entry and exit costs x1.5; borrow on shorts:
5 bp of entry notional (8 bp if < $20) in the earnings window, else 1.2 bp (3 bp if < $20). One lot per symbol across
sides; refire >= 30 min after the exit; max 2 per symbol-session; day cap 30 (first by time, ties ADV20 desc).
    python bt.py WORK sig fit|check ; python bt.py WORK walk fit|check ;
    python bt.py WORK basegate | triggate | fit | fitrandom | check | plateau | checkgates | twin fit|check
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
EARN = HERE.parent / "data" / "earnings_yf.parquet"
LOCK = ("2024-11-01", "2025-02-28")
FIT_MONTHS = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 10)]
MOD = HERE.parents[1] / "modules" / "ULT-29.py"
N_CUM = 996
DAY_CAP = 30
BASES = ("EB-L", "EB-S")
BSIDE = {"EB-L": 1, "EB-S": -1}
TRIGS = {1: ("L1", "L2", "L3", "L4"), -1: ("S1", "S2", "S3", "S4")}
WIN = (1000, 1300)
SEASON_MIN = 8          # a session with >= 8 lab-list reaction days counts as "earnings season" (reporting only)


def no_locked(dates):
    s = pd.Series([str(x)[:10] for x in dates])
    assert not ((s >= LOCK[0]) & (s <= LOCK[1])).any(), "locked block row found"


def load_mod():
    spec = importlib.util.spec_from_file_location("ult29", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def etb_set():
    u = pd.read_csv(ROOT / "data" / "universe.csv")
    return set(u.loc[u.easy_to_borrow.astype(str).str.lower() == "true", "symbol"].astype(str))


def lev_inverse():
    p = HERE.parents[1] / "modules" / "ULT-25_symbols.json"      # leveraged / inverse funds (names/types only)
    return set(json.loads(p.read_text())["LEV"])


def earn_table():
    e = pd.read_parquet(EARN, columns=["symbol", "date", "session"])
    s = e["date"].dt.strftime("%Y-%m-%d")
    e = e[(s < LOCK[0]) | (s > LOCK[1])].copy()        # earnings rows dated in the locked block are never used
    no_locked(e["date"].dt.strftime("%Y-%m-%d").unique())
    e["symbol"] = e["symbol"].astype(str)
    return e


def half_months(half):
    import research.history2y.lib as lib
    lib.DATA = DATA
    ms = [m for m in lib.months() if m not in lib.LOCKED_MONTHS]
    return FIT_MONTHS if half == "fit" else [m for m in ms if m >= "2025-10"]


def half_days(half):
    import research.history2y.lib as lib
    lib.DATA = DATA
    d = []
    for m in half_months(half):
        d += sorted(str(x) for x in set(lib.load_context(m)["date"]))
    no_locked(d)
    return sorted(d)


def rd_set(half):
    mod = load_mod()
    ev = mod.rd_events(earn_table(), half_days(half))
    no_locked(ev.rd.unique())
    return ev


def twin_excl():
    """symbol-days inside any event's earnings window (calendar approximation of RD-5..RD+1: report date -8..+4 days)."""
    e = earn_table()
    out = set()
    for sym, d in zip(e.symbol, e["date"]):
        for k in range(-8, 5):
            out.add(sym + "|" + (d + pd.Timedelta(days=k)).strftime("%Y-%m-%d"))
    return out


def m2(t):
    t = np.asarray(t, int)
    return (t // 100) * 60 + t % 100


def hhmm(mins):
    mins = np.asarray(mins, int)
    return (mins // 60) * 100 + mins % 60


# ---------------------------------------------------------------- stage 1: superset + base random bars
COLS = ["symbol", "date", "tod", "close", "atr_d", "adv20", "gap"]


def _frame(month, keep_keys=None, twin_excl_keys=None):
    import research.history2y.lib as lib
    lib.DATA = DATA
    f = lib.load_month(month, context=True)
    f = f[[c for c in f.columns if not (c.startswith(("win_", "r_long", "r_short")) or "heat" in c.lower())]]
    assert not any(c.startswith(("win_", "r_long", "r_short")) or "heat" in c.lower() for c in f.columns)
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    no_locked(f["date"].unique())
    k = (f["symbol"] + "|" + f["date"]).to_numpy()
    if keep_keys is not None:
        sel = pd.Series(k).isin(keep_keys).to_numpy()
    else:   # twin: non-earnings gap names
        sel = (np.abs(f["gap"].to_numpy(float)) >= 2.0) & ~pd.Series(k).isin(twin_excl_keys).to_numpy()
    f = f[sel].sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    f["earn_rd"] = True        # evaluation rows: RD names (or the twin's no-news gap names under the same rule)
    return f


def month_job(args):
    month, keys = args
    import research.history2y.lib as lib
    lib.DATA = DATA
    mod = load_mod()
    f = _frame(month, keep_keys=keys)
    days = sorted(str(x) for x in set(lib.load_context(month)["date"]))
    if not len(f):
        return month, pd.DataFrame(), pd.DataFrame(), days
    r = mod.features(f)
    etb = f["symbol"].isin(etb_set() - lev_inverse()).to_numpy()
    mi = int(month.replace("-", ""))
    sig, rnd = [], []
    wb = {k: (r["trig"][k], mod.within(r, k, 3)) for sg in (1, -1) for k in TRIGS[sg]}
    for bi, b in enumerate(BASES):
        sg = BSIDE[b]
        bm = r["bases"][b] & (etb if sg < 0 else True)
        on = np.zeros(len(f), int); w3 = np.zeros(len(f), int)
        for j, k in enumerate(TRIGS[sg]):
            o, a3 = wb[k]
            on |= o.astype(int) << j; w3 |= a3.astype(int) << j
        s = f.loc[bm, COLS].copy()
        s["side"] = sg; s["base"] = b; s["evt"] = True
        s["on"] = on[bm]; s["w3"] = w3[bm]
        sig.append(s)
        rng = np.random.default_rng([1119, mi, bi])
        idx = np.flatnonzero(bm)
        if len(idx):
            g = pd.Series(idx).groupby(f["symbol"].to_numpy()[idx] + "|" + f["date"].to_numpy()[idx], sort=True)
            pick = [int(v.to_numpy()[rng.integers(len(v))]) for _, v in g]
            B = f.loc[pick, COLS].copy()
            B["side"] = sg; B["base"] = b; B["evt"] = True
            rnd.append(B)
    S = pd.concat(sig, ignore_index=True)
    B = pd.concat(rnd, ignore_index=True) if rnd else pd.DataFrame(columns=COLS + ["side", "base", "evt"])
    return month, S, B, days


def twin_job(args):
    """Non-earnings twin: the frozen rule (W, C, survivors) on |gap| >= 2% names with no earnings in the window."""
    month, excl, W, C, surv = args
    mod = load_mod()
    f = _frame(month, twin_excl_keys=excl)
    r = mod.features(f)
    etb = f["symbol"].isin(etb_set() - lev_inverse()).to_numpy()
    lev = f["symbol"].isin(lev_inverse()).to_numpy()
    out = []
    for b in BASES:
        sg = BSIDE[b]
        names = surv.get(b, [])
        if len(names) < C:
            continue
        cnt = sum(mod.within(r, k, W).astype(int) for k in names)
        m = r["bases"][b] & ~lev & (etb if sg < 0 else True) & (cnt >= C)
        s = f.loc[m, COLS].copy()
        s["side"] = sg; s["base"] = b; s["evt"] = False
        out.append(s)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame(columns=COLS + ["side", "base", "evt"])


# ---------------------------------------------------------------- stage 2: 1-minute walk (X = TX-45, H = t1s1 cap45)
def walk_job(args):
    sym, T = args
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

    def path(ix, j0, sgn, stop, tgt, tend):
        px, kd, xt = None, 0, None
        for q in ix[j0:]:
            if hm_all[q] > tend:
                break
            if (sgn > 0 and Lo[q] <= stop) or (sgn < 0 and Hh[q] >= stop):
                px, kd, xt = (min(O[q], stop) if sgn > 0 else max(O[q], stop)), 1, hm_all[q]; break
            if tgt is not None and ((sgn > 0 and Hh[q] >= tgt) or (sgn < 0 and Lo[q] <= tgt)):
                px, kd, xt = tgt, 2, hm_all[q]; break
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
        tend = min(int(hhmm(m2(hm[j0]) + 44)), 1549)
        pX, kX, xX = path(ix, j0, sgn, dclose - sgn * 2 * u, None, tend)
        pH, kH, xH = path(ix, j0, sgn, dclose - sgn * u, dclose + sgn * u, tend)
        if pX is None or pH is None:
            return None
        return e, dclose, pX, kX, int(hhmm(m2(xX) + 1)), pH, kH, int(hhmm(m2(xH) + 1))

    res = []
    for r in T.itertuples():
        ix = byday.get(r.date)
        u = 0.25 * r.atr_d
        a = None if ix is None else one(ix, r.tod, u, None if r.random else r.close, int(r.side))
        res.append((r.Index,) + (a if a else (np.nan,) * 8))
    return res


def cost_R(side, tod, e, px, kd, unit, evt, borrow=True, surcharge=True):
    sur = np.where(evt & (tod < 1030) & surcharge, 1.5, 1.0)
    ec = (0.01 + e * 1e-4) * tod_cost_mult(tod) * sur
    xc = (np.where(kd == 2, 0.0, 0.01 + px * 1e-4)) * sur + np.where(kd == 1, 0.02, 0.0)
    bps = np.where(evt, np.where(e < 20, 8e-4, 5e-4), np.where(e < 20, 3e-4, 1.2e-4))
    bf = np.where((side < 0) & borrow, bps * e, 0.0)
    return (side * (px - e) - ec - xc - bf) / unit


def walk(T, random=False):
    T = T.reset_index(drop=True).copy()
    no_locked(T["date"].unique())
    T["random"] = random
    jobs = [(s, g) for s, g in T.groupby("symbol") if (CACHE / f"{s}.parquet").exists()]
    with Pool(3) as p:
        out = [x for r in p.imap_unordered(walk_job, jobs, chunksize=2) for x in r]
    a = pd.DataFrame(out, columns=["i", "e", "dclose", "pxX", "kdX", "xtX", "pxH", "kdH", "xtH"]).set_index("i")
    T = T.drop(columns=["random"]).join(a)
    u = 0.25 * T.atr_d.to_numpy()
    tod = T.tod.to_numpy()
    sd = T.side.to_numpy()
    evt = T.evt.to_numpy().astype(bool)
    for g, unit in (("X", 2 * u), ("H", u)):
        T["r" + g] = cost_R(sd, tod, T.e.to_numpy(), T["px" + g].to_numpy(), T["kd" + g].to_numpy(), unit, evt)
        T["rsc" + g] = cost_R(sd, tod, T.dclose.to_numpy(), T["px" + g].to_numpy(), T["kd" + g].to_numpy(), unit,
                              evt, borrow=False, surcharge=False)   # bias diagnostic: signal-close fill, no borrow/surcharge
        T["xmin" + g] = np.where(T["xt" + g].notna(), m2(T["xt" + g].fillna(0)), np.nan)
    return T


def bind(T, g):
    """Expose exit g ('X' / 'H') under the generic names stats() reads (r, kd, xmin, hold, r_sigclose, r_u)."""
    T = T.copy()
    T["r"], T["kd"], T["xmin"], T["r_sigclose"] = T["r" + g], T["kd" + g], T["xmin" + g], T["rsc" + g]
    T["r_u"] = T["r"] * (2.0 if g == "X" else 1.0)
    T["hold"] = T["xmin"] - m2(T.tod)
    return T


# ---------------------------------------------------------------- stage 3: configs + chassis
def configs():
    """Grid (8): W {1, 3} x C {2, 3} x exit {H t1s1 cap45, X TX-45}; W outer, C middle, exit inner (29a..29h)."""
    out, names = {}, iter("abcdefgh")
    for w in (1, 3):
        for c in (2, 3):
            for ex in ("H", "X"):
                out["29" + next(names)] = dict(W=w, C=c, exit=ex,
                                               label=f"W{w}-C{c}-{'t1s1cap45' if ex == 'H' else 'TX45'}")
    return out


def chain(s, cap):
    """One lot per symbol (across sides), refire >= 30 min after the exit, max 2 per symbol-session, day cap."""
    s = s.sort_values(["symbol", "date", "tod", "side"], kind="mergesort")
    keep = []
    for _, g in s.groupby(["symbol", "date"], sort=False):
        n, free_at = 0, -1
        for i, t, x in zip(g.index, m2(g.tod.to_numpy()), g.xmin.to_numpy()):
            if n >= 2:
                break
            if t >= free_at:
                keep.append(i); n += 1; free_at = x + 30
    s = s.loc[keep].sort_values(["date", "tod", "adv20"], ascending=[True, True, False], kind="mergesort")
    if cap:
        s = s.groupby("date", sort=False).head(cap)
    return s


def nbits(x, bits):
    return sum(((x >> j) & 1) * ((bits >> j) & 1) for j in range(4))


def surv_bits(survive, base):
    tr = TRIGS[BSIDE[base]]
    return sum(1 << tr.index(k) for k in survive.get(base, []))


def select(S, cfg, gate, survive, cap=DAY_CAP):
    S = bind(S, cfg["exit"])
    m = np.zeros(len(S), bool)
    wcol = S["on" if cfg["W"] == 1 else "w3"].to_numpy().astype(int)
    for b in BASES:
        if not gate[b][cfg["exit"]]["pass"]:
            continue
        bits = surv_bits(survive, b)
        if bin(bits).count("1") < cfg["C"]:
            continue
        m |= (S.base.to_numpy() == b) & (nbits(wcol, bits) >= cfg["C"])
    m &= S.r.notna().to_numpy()
    return chain(S[m], cap)


# ---------------------------------------------------------------- stage 4: statistics
SPY = None
SEASON = {}


def spy_types():
    global SPY
    if SPY is None:
        from stats import spy_days
        SPY = spy_days()
    return SPY


def season_days(half):
    if half not in SEASON:
        ev = rd_set(half)
        c = ev.rd.value_counts()
        SEASON[half] = set(c[c >= SEASON_MIN].index)
    return SEASON[half]


def stats(t, n_sessions, col="r", sides=True, half=None):
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
    if half is not None:
        sd = season_days(half)
        ins = t.date.isin(sd)
        o["season"] = {"sessions_season": len(sd), "n_season": int(ins.sum()),
                       "avg_r_season": round(float(t.loc[ins, col].mean()), 4) if ins.any() else None,
                       "n_off": int((~ins).sum()),
                       "avg_r_off": round(float(t.loc[~ins, col].mean()), 4) if (~ins).any() else None}
    if sides:
        for nm, sg in (("long", 1), ("short", -1)):
            x = t[t.side == sg]
            o[nm] = ({k: v for k, v in stats(x, n_sessions, col, sides=False).items()
                      if k in ("trades", "trades_per_session", "win", "avg_r", "avg_r_wo_best_day", "best_day_share",
                               "total_r", "t_day_clustered", "worst_day", "avg_r_ex_0403_0409", "first_half_avg_r",
                               "second_half_avg_r")} if len(x) else {"trades": 0})
    return o


def sub_halves(t):
    a = t[(t.date < "2025-06-01")]
    b = t[(t.date >= "2025-06-01")]
    return {"A_avg_r": round(float(a.r.mean()), 4) if len(a) else None, "A_n": int(len(a)),
            "B_avg_r": round(float(b.r.mean()), 4) if len(b) else None, "B_n": int(len(b))}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def random_control(sel, cfg, seed=1119):
    """Same symbol-sessions, sides and count as the selected trades; a random decision bar 10:00-13:00; same exit."""
    rng = np.random.default_rng(seed)
    R = sel[["symbol", "date", "atr_d", "close", "tod", "side", "evt"]].copy()
    R["tod"] = hhmm(rng.choice(np.arange(m2(WIN[0]), m2(WIN[1]) + 1, 5), size=len(R)))
    return bind(walk(R, random=True), cfg["exit"])


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


def load(work, half, what):
    S = pd.read_parquet(Path(work) / f"{what}_{half}.parquet")
    no_locked(S.date.unique())
    days = pd.read_parquet(Path(work) / f"days_{half}.parquet").date.tolist()
    no_locked(days)
    return S, len(days)


def half_split(y):
    return y[y.date < "2025-06-01"].r, y[y.date >= "2025-06-01"].r


def base_eval(B, fit=True):
    out = {}
    for b in BASES:
        x = B[B.base == b]
        o = {"n": int(len(x))}
        for ex in ("X", "H"):
            y = bind(x, ex)
            y = y[y.r.notna()]
            e = {"all_avg_r": round(float(y.r.mean()), 4) if len(y) else None, "n": int(len(y)),
                 "all_avg_r_u025": round(float(y.r_u.mean()), 4) if len(y) else None,
                 "sigclose_noborrow_avg_r": round(float(y.r_sigclose.mean()), 4) if len(y) else None,
                 "gross_before_costs_avg_r": round(float((y.side * (y["px" + ex] - y.e) / (y.atr_d * 0.25 * (2 if ex == "X" else 1))).mean()), 4)
                 if len(y) else None,
                 "avg_r_ex_0403_0409": round(float(y[~y.date.between("2025-04-03", "2025-04-09")].r.mean()), 4)
                 if len(y) else None}
            if fit:
                a, bb = half_split(y)
                e.update({"A_avg_r": round(float(a.mean()), 4) if len(a) else None, "A_n": int(len(a)),
                          "B_avg_r": round(float(bb.mean()), 4) if len(bb) else None, "B_n": int(len(bb))})
                e["pass"] = bool(len(a) and len(bb) and a.mean() >= 0 and bb.mean() >= 0)
            o[ex] = e
        out[b] = o
    return out


def trig_eval(S, B, gate, fit=True):
    out = {}
    for b in BASES:
        if fit and not (gate[b]["X"]["pass"] or gate[b]["H"]["pass"]):
            out[b] = {"skipped": "base closed under both exits"}
            continue
        rb = bind(B[B.base == b], "X")
        rb = rb[rb.r.notna()]
        ra, rbb = half_split(rb)
        o = {}
        for j, k in enumerate(TRIGS[BSIDE[b]]):
            x = bind(S[(S.base == b).to_numpy() & (((S.on.to_numpy().astype(int) >> j) & 1) == 1)], "X")
            x = chain(x[x.r.notna()], 0)
            a, bb = half_split(x)
            e = {"n": int(len(x)), "avg_r": round(float(x.r.mean()), 4) if len(x) else None,
                 "minus_random_all": round(float(x.r.mean() - rb.r.mean()), 4) if len(x) else None}
            if fit:
                da = float(a.mean() - ra.mean()) if len(a) else np.nan
                db = float(bb.mean() - rbb.mean()) if len(bb) else np.nan
                e.update({"A_n": int(len(a)), "B_n": int(len(bb)), "A_avg_r": round(float(a.mean()), 4) if len(a) else None,
                          "B_avg_r": round(float(bb.mean()), 4) if len(bb) else None,
                          "A_minus_random": round(da, 4) if np.isfinite(da) else None,
                          "B_minus_random": round(db, 4) if np.isfinite(db) else None,
                          "survives": bool(np.isfinite(da) and np.isfinite(db) and da >= 0 and db >= 0)})
            o[k] = e
        out[b] = o
    return out


def survivors(tg):
    return {b: [k for k, v in tg[b].items() if isinstance(v, dict) and v.get("survives")] for b in BASES
            if "skipped" not in tg[b]}


def grid(S, n, gate, surv, half="fit"):
    res = {}
    for name, cfg in configs().items():
        t = select(S, cfg, gate, surv)
        o = stats(t, n, half=half)
        if len(t):
            o.update(sub_halves(t))
            o["by_base"] = {b: {"trades": int((t.base == b).sum()),
                                "avg_r": round(float(t.loc[t.base == b, "r"].mean()), 4) if (t.base == b).any() else None}
                            for b in BASES}
        o["cfg"] = cfg
        res[name] = o
        print(name, cfg["label"], o["trades_per_session"], o.get("avg_r"), o.get("avg_r_wo_best_day"),
              o.get("total_r"), o.get("total_r_wo_best_day"), o.get("A_avg_r"), o.get("B_avg_r"),
              o.get("by_base"), flush=True)
    return res


def pick_of(res):
    scored = {k: v for k, v in res.items() if v["trades"] > 0}
    elig = {k: v for k, v in scored.items() if v["trades_per_session"] >= 2.0}
    pool = elig if elig else scored
    pick = max(pool, key=lambda k: (pool[k]["total_r_wo_best_day"], -list(res).index(k))) if pool else None
    return pick, elig, scored


if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True)
    stage = sys.argv[2]
    if stage == "sig":
        half = sys.argv[3]
        if half == "check":
            assert (HERE / "fitsel.json").exists(), "freeze fitsel.json before any check data is built"
        ev = rd_set(half)
        ev["k"] = ev.symbol + "|" + ev.rd
        jobs = [(m, set(ev.loc[ev.rd.str.startswith(m), "k"])) for m in half_months(half)]
        print(half, "reaction-day symbol-sessions", len(ev), flush=True)
        sigs, rnds, days = [], [], []
        with Pool(2) as p:
            for m, s, b, d in p.imap_unordered(month_job, jobs):
                print(m, len(s), s.base.value_counts().to_dict() if len(s) else {}, "base rnd", len(b), flush=True)
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
            print("walked", what, len(T), int(T.rX.isna().sum()), "no path", round(time.time() - t0), "s", flush=True)
    elif stage == "basegate":
        assert not (HERE / "trigger_gate.json").exists(), "base gate is decided before any trigger is scored"
        B, _ = load(W, "fit", "walkedbase")
        g = base_eval(B)
        g["note"] = ("Educational only - not financial advice. ULT-29 base gate (FIT only, scored before any trigger): one "
                     "random base-eligible bar per base-eligible symbol-session; pass = random avg R >= 0 in both fit "
                     "sub-halves A and B, per exit (X = TX-45 per 2u, H = t1s1 cap45 per u).")
        g["frozen_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        (HERE / "base_gate.json").write_text(json.dumps(g, indent=1, default=float))
        print(json.dumps(g, indent=1, default=float))
    elif stage == "triggate":
        assert not (HERE / "fit_grid.json").exists(), "trigger gate is decided before any confluence is scored"
        gate = json.loads((HERE / "base_gate.json").read_text())
        B, _ = load(W, "fit", "walkedbase")
        S, _ = load(W, "fit", "walkedsig")
        tg = trig_eval(S, B, gate)
        tg["survivors"] = survivors(tg)
        tg["note"] = ("Educational only - not financial advice. ULT-29 trigger gate (FIT only, after the base gate): "
                      "trigger true on the bar, chassis chain, TX-45; survives if signal minus same-base random >= 0 "
                      "in both fit sub-halves.")
        tg["frozen_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        (HERE / "trigger_gate.json").write_text(json.dumps(tg, indent=1, default=float))
        print(json.dumps(tg, indent=1, default=float))
    elif stage == "fit":
        gate = json.loads((HERE / "base_gate.json").read_text())
        surv = json.loads((HERE / "trigger_gate.json").read_text())["survivors"]
        S, n = load(W, "fit", "walkedsig")
        res = grid(S, n, gate, surv)
        pick, elig, scored = pick_of(res)
        (HERE / "fit_grid.json").write_text(json.dumps(res, indent=1, default=float))
        fs = {"note": "Educational only - not financial advice. ULT-29 fit pick, frozen BEFORE any check data is built.",
              "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "pick": pick,
              "cfg": res[pick]["cfg"] if pick else None, "eligible_2_per_session": sorted(elig),
              "configs_with_trades": sorted(scored),
              "base_open": {b: {ex: gate[b][ex]["pass"] for ex in ("H", "X")} for b in BASES}, "survivors": surv,
              "rule": "max fit total R minus best fit day among configs >= 2.0/session (PLAN sec. 5)",
              "fit": res[pick] if pick else None, "sha256_bt": sha(__file__), "sha256_module_at_freeze": sha(MOD),
              "sha256_earnings": sha(EARN),
              "configs_counted_this_candidate": 21,
              "configs_note": "8 grid + 4 base-gate + 8 trigger-gate evaluations (PLAN sec. 4: 20) + 1 bias diagnostic",
              "partly_check_informed": True, "needs_owner_blackout_exception": True, "n_cumulative": N_CUM}
        (HERE / "fitsel.json").write_text(json.dumps(fs, indent=1, default=float))
        print("PICK", pick, "eligible:", sorted(elig), "scored:", sorted(scored))
    elif stage == "diagfit":
        # DIAGNOSTIC (only if the FIT gates leave nothing to trade): trigger gate and grid with the base gate ignored.
        assert not (HERE / "check_once.json").exists() and not Path(W / "sig_check.parquet").exists()
        fs = json.loads((HERE / "fitsel.json").read_text())
        B, _ = load(W, "fit", "walkedbase")
        S, n = load(W, "fit", "walkedsig")
        opened = {b: {ex: {"pass": True} for ex in ("X", "H")} for b in BASES}
        tg = trig_eval(S, B, opened)
        tg["survivors"] = survivors(tg)
        tg["note"] = "DIAGNOSTIC: trigger gate with every base forced open (base gate ignored); FIT only"
        (HERE / "trigger_gate_diag_ungated.json").write_text(json.dumps(tg, indent=1, default=float))
        print(json.dumps(tg, indent=1, default=float))
        res = grid(S, n, opened, tg["survivors"])
        upick, elig, _ = pick_of(res)
        (HERE / "fit_grid_diag_ungated.json").write_text(json.dumps(res, indent=1, default=float))
        fs.update({"diagnostic_ungated_pick": upick, "diagnostic_ungated_cfg": res[upick]["cfg"] if upick else None,
                   "diagnostic_ungated_survivors": tg["survivors"], "diagnostic_ungated_eligible": sorted(elig),
                   "diagnostic_ungated_fit": res[upick] if upick else None,
                   "diagnostic_frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "diagnostic_note": ("Added because the pre-registered FIT gates left nothing to trade, BEFORE any check "
                                       "data: the same trigger gate and selection rule with the base gate ignored, frozen "
                                       "here, scored once on check as a DIAGNOSTIC (counted +1 config and the trigger-gate "
                                       "evaluations it ran). It cannot change the tier."),
                   "sha256_bt_at_diag_freeze": sha(__file__)})
        (HERE / "fitsel.json").write_text(json.dumps(fs, indent=1, default=float))
        print("DIAG PICK", upick, "eligible", sorted(elig))
    elif stage == "diagcheck":
        fs = json.loads((HERE / "fitsel.json").read_text())
        assert fs.get("diagnostic_ungated_pick"), "no diagnostic pick"
        assert not (HERE / "check_diag_ungated.json").exists(), "diagnostic is scored ONCE"
        opened = {b: {ex: {"pass": True} for ex in ("X", "H")} for b in BASES}
        S, n = load(W, "check", "walkedsig")
        cfg = fs["diagnostic_ungated_cfg"]
        t = select(S, cfg, opened, fs["diagnostic_ungated_survivors"])
        o = stats(t, n, half="check")
        o["bias_diag_sigclose_noborrow_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        o.update(rand_block(t, cfg))
        o["t_bar"] = round(max(1.5, float(np.sqrt(2 * np.log(N_CUM)))), 3)
        o["pick"] = fs["diagnostic_ungated_pick"]
        o["note"] = "DIAGNOSTIC ONLY (base gate ignored); cannot set the tier"
        o["scored_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        (HERE / "check_diag_ungated.json").write_text(json.dumps(o, indent=1, default=float))
        print(json.dumps(o, indent=1, default=float))
    elif stage == "diagfitall":
        # DIAGNOSTIC 2 (added 2026-11-19 after the FIT base gate closed all four base x exit cells AND the base-ignored
        # trigger gate left < 2 survivors per base, BEFORE any check data): every base open, all four triggers counted
        # (no gates at all), same grid and selection rule; frozen here, scored once on check; cannot set the tier.
        assert not (HERE / "check_once.json").exists() and not Path(W / "sig_check.parquet").exists()
        fs = json.loads((HERE / "fitsel.json").read_text())
        S, n = load(W, "fit", "walkedsig")
        opened = {b: {ex: {"pass": True} for ex in ("X", "H")} for b in BASES}
        allt = {b: list(TRIGS[BSIDE[b]]) for b in BASES}
        res = grid(S, n, opened, allt)
        upick, elig, _ = pick_of(res)
        (HERE / "fit_grid_diag_nogates.json").write_text(json.dumps(res, indent=1, default=float))
        fs.update({"diagnostic_nogates_pick": upick, "diagnostic_nogates_cfg": res[upick]["cfg"] if upick else None,
                   "diagnostic_nogates_survivors": allt, "diagnostic_nogates_eligible": sorted(elig),
                   "diagnostic_nogates_fit": res[upick] if upick else None,
                   "diagnostic_nogates_frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "diagnostic_nogates_note": ("No-gates diagnostic (base gate and trigger gate ignored), frozen BEFORE any "
                                               "check data; scored once on check; counted +1 config; cannot set the tier."),
                   "sha256_bt_at_diag2_freeze": sha(__file__), "sha256_module_at_diag2_freeze": sha(MOD)})
        (HERE / "fitsel.json").write_text(json.dumps(fs, indent=1, default=float))
        print("DIAG2 PICK", upick, "eligible", sorted(elig))
    elif stage == "diagcheckall":
        fs = json.loads((HERE / "fitsel.json").read_text())
        assert fs.get("diagnostic_nogates_pick"), "no diagnostic pick"
        assert not (HERE / "check_diag_nogates.json").exists(), "diagnostic is scored ONCE"
        opened = {b: {ex: {"pass": True} for ex in ("X", "H")} for b in BASES}
        S, n = load(W, "check", "walkedsig")
        cfg = fs["diagnostic_nogates_cfg"]
        t = select(S, cfg, opened, fs["diagnostic_nogates_survivors"])
        o = stats(t, n, half="check")
        o["bias_diag_sigclose_noborrow_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        o["uncapped"] = {k: v for k, v in stats(select(S, cfg, opened, fs["diagnostic_nogates_survivors"], cap=0), n,
                                                sides=False).items()
                         if k in ("trades", "trades_per_session", "avg_r", "avg_r_wo_best_day", "t_day_clustered")}
        o.update(rand_block(t, cfg))
        o["t_bar"] = round(max(1.5, float(np.sqrt(2 * np.log(N_CUM)))), 3)
        o["pick"] = fs["diagnostic_nogates_pick"]
        o["note"] = "DIAGNOSTIC ONLY (no gates); cannot set the tier"
        o["scored_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        (HERE / "check_diag_nogates.json").write_text(json.dumps(o, indent=1, default=float))
        t[["symbol", "date", "tod", "side", "base", "r", "r_u", "kd", "hold"]].to_csv(HERE / "check_trades_diag.csv.gz",
                                                                                       index=False)
        print(json.dumps(o, indent=1, default=float))
    elif stage == "diagfitrandomall":
        fs = json.loads((HERE / "fitsel.json").read_text())
        opened = {b: {ex: {"pass": True} for ex in ("X", "H")} for b in BASES}
        S, n = load(W, "fit", "walkedsig")
        t = select(S, fs["diagnostic_nogates_cfg"], opened, fs["diagnostic_nogates_survivors"])
        o = rand_block(t, fs["diagnostic_nogates_cfg"])
        o["bias_diag_sigclose_noborrow_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        (HERE / "fit_random_diag_nogates.json").write_text(json.dumps(o, indent=1, default=float))
        print(o)
    elif stage == "diagfitrandom":
        fs = json.loads((HERE / "fitsel.json").read_text())
        opened = {b: {ex: {"pass": True} for ex in ("X", "H")} for b in BASES}
        S, n = load(W, "fit", "walkedsig")
        t = select(S, fs["diagnostic_ungated_cfg"], opened, fs["diagnostic_ungated_survivors"])
        o = rand_block(t, fs["diagnostic_ungated_cfg"])
        o["bias_diag_sigclose_noborrow_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        (HERE / "fit_random_diag.json").write_text(json.dumps(o, indent=1, default=float))
        print(o)
    elif stage == "fitrandom":
        fs = json.loads((HERE / "fitsel.json").read_text())
        gate = json.loads((HERE / "base_gate.json").read_text())
        S, n = load(W, "fit", "walkedsig")
        t = select(S, fs["cfg"], gate, fs["survivors"])
        o = rand_block(t, fs["cfg"])
        o["bias_diag_sigclose_noborrow_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        o["uncapped"] = {k: v for k, v in stats(select(S, fs["cfg"], gate, fs["survivors"], cap=0), n,
                                                sides=False).items()
                         if k in ("trades", "trades_per_session", "avg_r", "avg_r_wo_best_day", "t_day_clustered")}
        (HERE / "fit_random.json").write_text(json.dumps(o, indent=1, default=float))
        print(o)
    elif stage == "check":
        fs = json.loads((HERE / "fitsel.json").read_text())
        assert fs["pick"], "no fit pick: nothing to score"
        assert not (HERE / "check_once.json").exists(), "check is scored ONCE"
        gate = json.loads((HERE / "base_gate.json").read_text())
        S, n = load(W, "check", "walkedsig")
        cfg = fs["cfg"]
        t = select(S, cfg, gate, fs["survivors"])
        o = stats(t, n, half="check")
        o["bias_diag_sigclose_noborrow_avg_r"] = round(float(t.r_sigclose.mean()), 4)
        o["uncapped"] = {k: v for k, v in stats(select(S, cfg, gate, fs["survivors"], cap=0), n, sides=False).items()
                         if k in ("trades", "trades_per_session", "avg_r", "avg_r_wo_best_day", "t_day_clustered")}
        o.update(rand_block(t, cfg))
        z = max(1.5, float(np.sqrt(2 * np.log(N_CUM))))
        fit = fs["fit"]
        tierA = (o["avg_r"] is not None and o["avg_r"] > 0 and (o["avg_r_wo_best_day"] or -1) > 0
                 and fit["avg_r"] > 0 and o["trades_per_session"] >= 2.0)
        beats = (tierA and o["avg_r"] > 0.0836 and o["avg_r_wo_best_day"] > 0.0734 and o["total_r_per_session"] > 0
                 and o["worst_day_per_trade_session"] >= -2.152 and (o["t_day_clustered"] or 0) >= z)
        tierB = fit["avg_r"] > 0 and (o["avg_r"] or -1) > -0.02
        o["t_bar"] = round(z, 3)
        o["tier"] = "BEATS" if beats else ("A" if tierA else ("B" if tierB else "FAIL"))
        o["pick"] = fs["pick"]
        o["scored_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        (HERE / "check_once.json").write_text(json.dumps(o, indent=1, default=float))
        t[["symbol", "date", "tod", "side", "base", "r", "r_u", "kd", "hold"]].to_csv(HERE / "check_trades.csv.gz",
                                                                                       index=False)
        print(json.dumps(o, indent=1, default=float))
    elif stage == "plateau":
        assert any((HERE / f).exists() for f in ("check_once.json", "check_diag_ungated.json", "check_diag_nogates.json"))
        gate = json.loads((HERE / "base_gate.json").read_text())
        surv = json.loads((HERE / "trigger_gate.json").read_text())["survivors"]
        fs = json.loads((HERE / "fitsel.json").read_text())
        S, n = load(W, "check", "walkedsig")
        res = {}
        keys = ("trades_per_session", "avg_r", "avg_r_wo_best_day", "best_day_share", "total_r", "t_day_clustered",
                "worst_day_per_trade_session", "first_half_avg_r", "second_half_avg_r")
        for name, cfg in configs().items():
            o = stats(select(S, cfg, gate, surv), n)
            res[name] = {k: o.get(k) for k in keys}
            res[name]["label"] = cfg["label"]
            opened = {b: {ex: {"pass": True} for ex in ("X", "H")} for b in BASES}
            for dk in ("diagnostic_ungated", "diagnostic_nogates"):
                if fs.get(dk + "_survivors") is not None:
                    ou = stats(select(S, cfg, opened, fs[dk + "_survivors"]), n)
                    res[name][dk] = {k: ou.get(k) for k in keys}
            print(name, res[name], flush=True)
        (HERE / "check_plateau.json").write_text(json.dumps(res, indent=1, default=float))
    elif stage == "checkgates":
        assert any((HERE / f).exists() for f in ("check_once.json", "check_diag_ungated.json", "check_diag_nogates.json"))
        B, _ = load(W, "check", "walkedbase")
        S, _ = load(W, "check", "walkedsig")
        o = {"base_random": base_eval(B, fit=False), "trigger_vs_random": trig_eval(S, B, None, fit=False),
             "note": "reporting only (never used to select)"}
        (HERE / "check_gates_diag.json").write_text(json.dumps(o, indent=1, default=float))
        print(json.dumps(o, indent=1, default=float))
    elif stage == "twin":
        half = sys.argv[3]
        fs = json.loads((HERE / "fitsel.json").read_text())
        if half == "check":
            assert any((HERE / f).exists() for f in ("check_once.json", "check_diag_ungated.json",
                                                      "check_diag_nogates.json"))
        dk = ("diagnostic_nogates" if fs.get("diagnostic_nogates_pick") else "diagnostic_ungated")
        diag = not fs.get("pick")
        cfg = fs[dk + "_cfg"] if diag else fs["cfg"]
        surv = fs[dk + "_survivors"] if diag else fs["survivors"]
        gate = ({b: {ex: {"pass": True} for ex in ("X", "H")} for b in BASES} if diag
                else json.loads((HERE / "base_gate.json").read_text()))
        surv = {b: (v if gate[b][cfg["exit"]]["pass"] else []) for b, v in surv.items()}
        excl = twin_excl()
        jobs = [(m, excl, cfg["W"], cfg["C"], surv) for m in half_months(half)]
        with Pool(2) as p:
            parts = list(p.imap_unordered(twin_job, jobs))
        T = pd.concat(parts, ignore_index=True)
        T["date"] = T["date"].astype(str)
        no_locked(T.date.unique())
        print("twin rows", len(T), flush=True)
        T = bind(walk(T), cfg["exit"])
        T = chain(T[T.r.notna()], DAY_CAP)
        n = len(half_days(half))
        o = stats(T, n)
        o["pick"] = fs.get("pick") or fs.get("diagnostic_ungated_pick")
        o["note"] = ("non-earnings twin: the frozen rule on |gap| >= 2% names with no earnings report within -8..+4 "
                     "calendar days (approx. RD-5..RD+1); reporting only")
        (HERE / f"twin_{half}.json").write_text(json.dumps(o, indent=1, default=float))
        print(json.dumps({k: o.get(k) for k in ("trades", "trades_per_session", "avg_r", "avg_r_wo_best_day",
                                                 "t_day_clustered")}, default=float))
