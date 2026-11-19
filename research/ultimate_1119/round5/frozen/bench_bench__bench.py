"""Ultimate-setup BENCHMARK (ultimate_1119): MCF's current best setups scored on the 2-year history.

Stage 1  signals   lab frames (research/history2y/data/frames, 5-min decision bars 09:50-15:00 ET) per open month:
                   module.mask & YAML window & point-in-time adv20 >= min_adv & prefilter & atr_d > 0, then the
                   LabStrategy refire chain (mcf.strategies.setups.refire_select) or first hit per symbol-day.
                   Entry = the decision bar's close, R = 0.25 x daily ATR (as LabStrategy / bt_lab1104).
Stage 2  exits     walked on the 1-MINUTE bars of data/cache_hist/1Min from the minute after the decision bar close
                   (stop checked first in a minute, then target; stop gap-through fills at the worse of open/stop;
                   holdtr: 1R trailing stop once +1R, from the next minute; flat at 15:55). A 5-minute walk (frames +
                   headtail tail rows, as research/bdi/1104/bt_all.py) is kept as a cross-check column.
Costs    LR8 research basis (mcf.research.gates): entry 1c + 1 bp x time-of-day multiplier; exit 1c + 1 bp except
         target (limit) fills; +2c on stops; x3 on the extended tier (|gap| >= 20% or price < $5). R per unit of risk.
Halves   FIT = 2024-10-01..2024-10-31 + 2025-03-01..2025-09-30; CHECK = 2025-10-01..latest (2026-11-04).
         The rule-19 locked block 2024-11-01..2025-02-28 is NEVER read (pyarrow filters + asserts).
    python research/ultimate_1119/benchmark/bench.py WORKDIR [stage]   (stage: sig | walk | all; default all)
Educational only - not financial advice."""
from __future__ import annotations

import importlib.util
import os
import re
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads
import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "benchmark never reads the locked block"
from mcf.research.gates import GEOMK, tod_cost_mult  # noqa: E402
from mcf.strategies.setups import refire_select  # noqa: E402

DATA = Path("/home/user/MCF/research/history2y/data")
CACHE = Path("/home/user/MCF/data/cache_hist/1Min")
HT = Path("/home/user/MCF/research/bdi/cwt/test_b/data/headtail.parquet")
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())
LOCKED_MONTHS = {"2024-11", "2024-12", "2025-01", "2025-02"}
GEOM = {**GEOMK, "holdtr": (None, 1.0)}
SETUPS = [  # (setup, config file holding its live definition)
    ("L3-gap-slope-fromopen-FD", "default.yaml"), ("L3-gap-slope-lowdist-FD", "account_testing.yaml"),
    ("L3-gap-slope-rsi5hi-FD", "account_testing.yaml"), ("RW3-gapdn-rsi5pop-flowsell-short-FD", "default.yaml"),
    ("RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "default.yaml"), ("NM-ETF-late-dip-di-long", "default.yaml"),
    ("ST7-rsi50dn-long-pm-t1s1-FD", "default.yaml"),
    ("GEN-261020-09-EMAdChgge0p093-Z12lem0p82-VWAPcrossesle0-MID-QQQltm0p3-holdtr-long", "account_gen.yaml"),
]


def no_locked(dates):
    d = pd.to_datetime(pd.Series(list(dates))).dt.date
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def load_mod(name, module):
    p = ROOT / module
    sys.path.insert(0, str(p.parent))
    spec = importlib.util.spec_from_file_location("bm_" + re.sub(r"\W", "_", name), p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def inventory():
    out = []
    for name, f in SETUPS:
        cfg = yaml.safe_load((ROOT / "config" / f).read_text())
        p = cfg["strategies"][name]
        m = load_mod(name, p["module"])
        w = p.get("window") or [950, 1500]
        out.append(dict(setup=name, module=p["module"], side=m.SIDE, geom=p.get("geom") or m.GEOM, w_lo=int(w[0]), w_hi=int(w[1]),
                        min_adv=float(p.get("min_adv", 0) or 0),
                        refire=bool(p.get("refire", (cfg.get("live") or {}).get("lab_refire", False))),
                        cooldown=int(p.get("refire_cooldown", 1)), prefilter=p.get("prefilter") or "",
                        enabled=bool(p.get("enabled")), cfg=f))
    return out


def bar_no(t):
    t = np.asarray(t, int)
    return ((t // 100) * 60 + t % 100 - 570) // 5


def chain(sym, date, tod, refire, cooldown):
    key = np.char.add(np.char.add(sym.astype(str), "|"), date.astype(str))
    if not len(key):
        return np.zeros(0, int)
    starts = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
    ends = np.r_[starts[1:], len(key)]
    if not refire:
        return starts
    b = bar_no(tod)
    out = []
    for a, e in zip(starts, ends):
        pos = {int(x): a + j for j, x in enumerate(b[a:e])}
        out.extend(pos[int(x)] for x in refire_select(list(b[a:e]), cooldown))
    return np.asarray(sorted(out), int)


def walk5(h, l, c, tod, e, s, R, up, dn, flat=1555):
    stop = e - s * dn * R
    tgt = None if up is None else e + s * up * R
    mfe = 0.0
    for k in range(len(c)):
        if tod[k] > flat:
            break
        if (s == 1 and l[k] <= stop) or (s == -1 and h[k] >= stop):
            return stop, tod[k], 1
        if tgt is not None and ((s == 1 and h[k] >= tgt) or (s == -1 and l[k] <= tgt)):
            return tgt, tod[k], 2
        if tgt is None:   # holdtr
            mfe = max(mfe, s * ((h[k] if s == 1 else l[k]) - e) / R)
            if mfe >= 1.0:
                ts = e + s * (mfe - 1.0) * R
                stop = max(stop, ts) if s == 1 else min(stop, ts)
        if tod[k] == flat:
            return c[k], tod[k], 0
    return (c[-1], tod[-1], 0) if len(c) else (e, flat, 0)


def month_job(args):
    month, W = args
    import research.history2y.lib as lib  # noqa: E402
    lib.DATA = DATA
    inv = inventory()
    f = lib.load_month(month, context=True)
    f["symbol"] = f["symbol"].astype(str)
    no_locked(f["date"].unique())
    a = pd.Timestamp(month + "-01")
    ht = pd.read_parquet(HT, filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1))])
    ht = ht[ht.tod > 1500].rename(columns={"h": "high", "l": "low", "c": "close"})
    ht["symbol"] = ht["symbol"].astype(str)
    ht["date"] = pd.to_datetime(ht["date"]).dt.date
    tod = f["tod"].to_numpy()
    adv = f["adv20"].fillna(0).to_numpy()
    atr = f["atr_d"].to_numpy(float)
    gap = f["gap"].to_numpy(float)
    rows = []
    for st in inv:
        m = load_mod(st["setup"], st["module"])
        with np.errstate(invalid="ignore", divide="ignore"):
            mk = np.asarray(m.mask(f), bool)
        ok = mk & (tod >= max(950, st["w_lo"])) & (tod <= min(1500, st["w_hi"])) & (adv >= st["min_adv"]) & (atr > 0)
        pf = st["prefilter"]
        if pf.startswith("gap_le:"):
            ok &= gap <= float(pf.split(":", 1)[1])
        elif pf.startswith("gap_ge:"):
            ok &= gap >= float(pf.split(":", 1)[1])
        hit = np.flatnonzero(ok)
        if not len(hit):
            continue
        idx = hit[chain(f["symbol"].to_numpy()[hit], f["date"].to_numpy()[hit], tod[hit], st["refire"], st["cooldown"])]
        rows.append(pd.DataFrame({"setup": st["setup"], "row": idx, "side": 1 if st["side"] == "long" else -1, "geom": st["geom"]}))
    if not rows:
        return month, 0
    sig = pd.concat(rows, ignore_index=True)
    P = pd.concat([f[["symbol", "date", "tod", "high", "low", "close"]], ht[["symbol", "date", "tod", "high", "low", "close"]]],
                  ignore_index=True).sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    key = (P.symbol + "|" + P.date.astype(str)).values
    st_ = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
    en_ = np.r_[st_[1:], len(key)]
    rng = {k: (x, y) for k, x, y in zip(key[st_], st_, en_)}
    Ph, Pl, Pc = (P[k].to_numpy(float) for k in ("high", "low", "close"))
    Pt = P["tod"].to_numpy()
    fs, fd, fc = f.symbol.to_numpy(), f.date.astype(str).to_numpy(), f.close.to_numpy(float)
    out = {k: [] for k in ("symbol", "date", "tod", "entry", "R", "gap", "x5", "k5", "px5")}
    for r in sig.itertuples():
        i = r.row
        sym, d, t0 = fs[i], fd[i], tod[i]
        e, R = fc[i], 0.25 * atr[i]
        x, y = rng[sym + "|" + d]
        tt = Pt[x:y]
        j = np.searchsorted(tt, t0, side="right")
        up, dn = GEOM[r.geom]
        px, et, kd = walk5(Ph[x:y][j:], Pl[x:y][j:], Pc[x:y][j:], tt[j:], e, r.side, R, up, dn)
        for k_, v_ in zip(out, (sym, d, t0, e, R, gap[i], et, kd, px)):
            out[k_].append(v_)
    o = pd.concat([sig.drop(columns=["row"]).reset_index(drop=True), pd.DataFrame(out)], axis=1)
    no_locked(o["date"].unique())
    o.to_parquet(Path(W) / f"sig_{month}.parquet")
    return month, len(o)


def cost_r(o, px, kind):
    tier = np.where((np.abs(o.gap) >= 20) | (o.entry < 5), 3.0, 1.0)
    dn = o.geom.map(lambda g: GEOM[g][1]).to_numpy(float)
    ecost = (0.01 + o.entry * 1e-4) * tod_cost_mult(o.tod.to_numpy())
    xcost = np.where(kind == 2, 0.0, 0.01 + px * 1e-4) + np.where(kind == 1, 0.02, 0.0)
    gross = o.side * (px - o.entry) / o.R
    return ((gross - tier * (ecost + xcost) / o.R) / dn).to_numpy(float)


def walk1_job(args):
    sym, T = args
    d = pads.dataset(str(CACHE / f"{sym}.parquet"), format="parquet")
    fld = pads.field("__index_level_0__")
    tz = "America/New_York"
    L0, L1 = pd.Timestamp("2024-11-01", tz=tz), pd.Timestamp("2025-03-01", tz=tz)
    b = d.to_table(filter=(fld < L0) | (fld >= L1)).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(tz)
    b = b.sort_index()
    no_locked(np.unique(b.index.date))
    hhmm = b.index.hour * 100 + b.index.minute
    day = b.index.date.astype(str)
    O, H, Lo, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    res = []
    byday = {}
    for dd in np.unique(day):
        byday[dd] = np.flatnonzero(day == dd)
    for r in T.itertuples():
        ix = byday.get(r.date)
        e, R, s = r.entry, r.R, r.side
        up, dn = GEOM[r.geom]
        if ix is None:
            res.append((r.Index, np.nan, -1, -1)); continue
        hm = hhmm[ix]
        sel = ix[(hm >= r.tod) & (hm <= 1554)]          # minutes starting at the decision bar close .. the 15:54 minute
        stop = e - s * dn * R
        tgt = None if up is None else e + s * up * R
        mfe, px, kd, xt = 0.0, None, 0, 1555
        for k in sel:
            if (s == 1 and Lo[k] <= stop) or (s == -1 and H[k] >= stop):
                px = min(O[k], stop) if s == 1 else max(O[k], stop)
                kd, xt = 1, hhmm[k]; break
            if tgt is not None and ((s == 1 and H[k] >= tgt) or (s == -1 and Lo[k] <= tgt)):
                px, kd, xt = tgt, 2, hhmm[k]; break
            if tgt is None:
                mfe = max(mfe, s * ((H[k] if s == 1 else Lo[k]) - e) / R)
                if mfe >= 1.0:
                    ts = e + s * (mfe - 1.0) * R
                    stop = max(stop, ts) if s == 1 else min(stop, ts)
        if px is None:
            if not len(sel):
                res.append((r.Index, np.nan, -1, -1)); continue
            px, kd, xt = C[sel[-1]], 0, hhmm[sel[-1]] + 1
        res.append((r.Index, px, kd, xt))
    return res


def walk_all(W):
    sig = pd.concat([pd.read_parquet(p) for p in sorted(Path(W).glob("sig_*.parquet"))], ignore_index=True)
    no_locked(sig["date"].unique())
    jobs = [(s, g) for s, g in sig.groupby("symbol") if (CACHE / f"{s}.parquet").exists()]
    with Pool(3) as p:
        out = [x for r in p.imap_unordered(walk1_job, jobs, chunksize=4) for x in r]
    a = pd.DataFrame(out, columns=["i", "px1", "k1", "x1"]).set_index("i")
    sig = sig.join(a)
    sig["r5"] = cost_r(sig, sig.px5.to_numpy(float), sig.k5.to_numpy())
    ok = sig.k1.notna() & (sig.k1 >= 0)
    sig["r1"] = np.nan
    sig.loc[ok, "r1"] = cost_r(sig[ok], sig.loc[ok, "px1"].to_numpy(float), sig.loc[ok, "k1"].to_numpy())
    sig.drop(columns=["px5", "px1"]).to_parquet(Path(W) / "trades.parquet")
    print(len(sig), "trades;", int((~ok).sum()), "without 1-min path")


if __name__ == "__main__":
    W = Path(sys.argv[1]); W.mkdir(parents=True, exist_ok=True)
    stage = sys.argv[2] if len(sys.argv) > 2 else "all"
    if stage in ("sig", "all"):
        import research.history2y.lib as lib
        lib.DATA = DATA
        ms = [m for m in lib.months() if m not in LOCKED_MONTHS and not (W / f"sig_{m}.parquet").exists()]
        with Pool(2) as p:
            for r in p.imap_unordered(month_job, [(m, str(W)) for m in ms]):
                print(r, flush=True)
    if stage in ("walk", "all"):
        walk_all(W)
