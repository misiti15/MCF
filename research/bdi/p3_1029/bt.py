"""p3_1029 step 3a: two-year signals of Primary's current 8 setups with per-trade exits under every pre-declared exit
variant (PLAN.md). Open months only (lib refuses the locked block; the tail file is filtered to open months and every
output is asserted free of locked dates). Writes <scratch>/p3bt/sig_<month>.parquet.
Usage: python bt.py <scratch> [procs]      Educational only - not financial advice."""
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path("/home/user/MCF")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research" / "history2y"))
sys.path.insert(0, str(ROOT / "research" / "bdi" / "gates1021" / "scripts"))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "p3_1029 never reads the locked block"
import lib  # noqa: E402
from common import chain, load_mod, no_locked  # noqa: E402
from mcf.research.gates import GEOMK, tod_cost_mult  # noqa: E402

S = Path(sys.argv[1]); OUTD = S / "p3bt"; OUTD.mkdir(parents=True, exist_ok=True)
HT = ROOT / "research" / "bdi" / "cwt" / "test_b" / "data" / "headtail.parquet"
CFG = yaml.safe_load((ROOT / "config" / "default.yaml").read_text())
ORDER = CFG["live"]["setup_order"]
SETUPS = []
for name, p in CFG["strategies"].items():
    if p.get("enabled"):
        m = load_mod(name, p["module"])
        SETUPS.append(dict(setup=name, module=p["module"], window=tuple(p["window"]), min_adv=float(p["min_adv"]),
                           refire=bool(p.get("refire", False)), cooldown=int(p.get("refire_cooldown", 1)),
                           side=m.SIDE, geom=p.get("geom") or getattr(m, "GEOM", "t1s1")))
assert len(SETUPS) == 8, [s["setup"] for s in SETUPS]
# exit variants: name -> (flatten tod, tighten tod, tighten distance in R units of 0.25 ATR, applies to: 0 both, 1 longs)
VARIANTS = {"base": (1555, None, None), "f1545": (1545, None, None), "f1530": (1530, None, None),
            "f1540": (1540, None, None), "f1550": (1550, None, None), "t1500_050": (1555, 1500, 0.5),
            "t1500_025": (1555, 1500, 0.25), "t1500_075": (1555, 1500, 0.75)}
SL, BP, SX = 0.01, 1e-4, 0.02


def walk(h, l, c, tod, entry, s, R, up, dn, flat, ttod, tdist):
    """h,l,c,tod: bars AFTER the entry bar. Returns (exit price, exit tod, kind 1 stop / 2 target / 0 flatten)."""
    stop = entry - s * dn * R; tgt = entry + s * up * R
    for k in range(len(c)):
        if tod[k] > flat:
            break
        if (s == 1 and l[k] <= stop) or (s == -1 and h[k] >= stop):
            return stop, tod[k], 1
        if (s == 1 and h[k] >= tgt) or (s == -1 and l[k] <= tgt):
            return tgt, tod[k], 2
        if ttod is not None and tod[k] == ttod:
            ns = c[k] - s * tdist * R
            stop = max(stop, ns) if s == 1 else min(stop, ns)
        if tod[k] == flat:
            return c[k], tod[k], 0
    k = max(0, min(len(c), np.searchsorted(tod, flat, side="right")) - 1)
    return (c[k], tod[k], 0) if len(c) else (entry, flat, 0)


def month_job(month):
    t0 = time.time()
    f = lib.load_month(month, context=True)
    f["symbol"] = f["symbol"].astype(str)
    no_locked(f["date"].unique())
    a = pd.Timestamp(month + "-01")
    ht = pd.read_parquet(HT, filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1))])
    ht = ht[ht.tod > 1500].rename(columns={"h": "high", "l": "low", "c": "close"})
    ht["symbol"] = ht["symbol"].astype(str); ht["date"] = pd.to_datetime(ht["date"]).dt.date
    no_locked(ht["date"].unique())
    tod = f["tod"].to_numpy(); adv = f["adv20"].fillna(0).to_numpy(); atr = f["atr_d"].to_numpy(float)
    rows = []
    for st in SETUPS:
        m = load_mod(st["setup"], st["module"])
        with np.errstate(invalid="ignore", divide="ignore"):
            mk = np.asarray(m.mask(f), bool)
        lo, hi = st["window"]
        ok = mk & (tod >= max(950, lo)) & (tod <= min(1500, hi)) & (adv >= st["min_adv"]) & (atr > 0) \
            & np.isfinite(f[f"r_{st['side']}_{st['geom']}"].to_numpy(float))
        hit = np.flatnonzero(ok)
        if not len(hit):
            continue
        idx = hit[chain(f["symbol"].to_numpy()[hit], f["date"].to_numpy()[hit], tod[hit], st["refire"], st["cooldown"])]
        rows.append(pd.DataFrame({"setup": st["setup"], "row": idx, "side": 1 if st["side"] == "long" else -1, "geom": st["geom"],
                                  "lab_r": f[f"r_{st['side']}_{st['geom']}"].to_numpy(float)[idx],
                                  "lab_win": f[f"win_{st['side']}_{st['geom']}"].to_numpy(float)[idx]}))
    sig = pd.concat(rows, ignore_index=True)
    P = pd.concat([f[["symbol", "date", "tod", "high", "low", "close"]], ht[["symbol", "date", "tod", "high", "low", "close"]]],
                  ignore_index=True).sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    key = P.symbol + "|" + P.date.astype(str)
    starts = {k: i for k, i in zip(key[np.r_[True, key.values[1:] != key.values[:-1]]], np.flatnonzero(np.r_[True, key.values[1:] != key.values[:-1]]))}
    ends = np.r_[np.flatnonzero(key.values[1:] != key.values[:-1]) + 1, len(P)]
    endmap = dict(zip(sorted(starts.values()), ends))
    Ph, Pl, Pc = (P[k].to_numpy(float) for k in ("high", "low", "close"))
    Pt = P["tod"].to_numpy()
    out = {k: [] for k in ("symbol", "date", "tod", "entry", "R", "gap", "atr_d")}
    res = {v: ([], [], []) for v in VARIANTS}
    for r in sig.itertuples():
        i = r.row
        sym, d, t0r = f.symbol.iat[i], f.date.iat[i], tod[i]
        e = float(f.close.iat[i]); R = 0.25 * atr[i]
        a0 = starts[sym + "|" + str(d)]; z0 = endmap[a0]
        seg = slice(a0, z0); tt = Pt[seg]; j = np.searchsorted(tt, t0r, side="right")
        h, l, c, tt = Ph[seg][j:], Pl[seg][j:], Pc[seg][j:], tt[j:]
        up, dn = GEOMK[r.geom]
        for v, (flat, ttod, td) in VARIANTS.items():
            px, et, kd = walk(h, l, c, tt, e, r.side, R, up, dn, flat, ttod, td)
            res[v][0].append(px); res[v][1].append(et); res[v][2].append(kd)
        out["symbol"].append(sym); out["date"].append(d); out["tod"].append(t0r); out["entry"].append(e); out["R"].append(R)
        out["gap"].append(float(f.gap.iat[i])); out["atr_d"].append(atr[i])
    o = pd.concat([sig.reset_index(drop=True), pd.DataFrame(out)], axis=1)
    tier = np.where((np.abs(o.gap) >= 20) | (o.entry < 5), 3.0, 1.0)
    dn = o.geom.map(lambda g: GEOMK[g][1]).to_numpy(float)
    ecost = (SL + o.entry * BP) * tod_cost_mult(o.tod.to_numpy())
    for v in VARIANTS:
        px, et, kd = (np.asarray(x) for x in res[v])
        gross = o.side * (px - o.entry) / o.R
        xcost = np.where(kd == 2, 0.0, SL + px * BP) + np.where(kd == 1, SX, 0.0)
        o[f"r_{v}"] = (gross - tier * (ecost + xcost) / o.R) / dn           # live R units (per unit of stop distance)
        o[f"x_{v}"] = et; o[f"k_{v}"] = kd
    o["cost_stop_r"] = (tier * (2 * (SL + o.entry * BP) + SX) / o.R) / dn    # round-trip cost of a stop exit, in R
    o["R_ps"] = o.R * dn                                                      # stop distance $/share
    o = o.drop(columns=["row"])
    no_locked(o["date"].unique())
    o.to_parquet(OUTD / f"sig_{month}.parquet")
    return month, len(o), round(time.time() - t0, 1)


if __name__ == "__main__":
    ms = [m for m in lib.months() if m not in lib.LOCKED_MONTHS]
    with Pool(int(sys.argv[2]) if len(sys.argv) > 2 else 2) as p:
        for r in p.imap_unordered(month_job, ms):
            print(r, flush=True)
