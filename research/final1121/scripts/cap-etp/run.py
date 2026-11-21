"""cap-etp grid (pre-declared, 15 configs) on FIT; CHECK + T2 only for finalists (python run.py fit | python run.py check NAMES).
Educational only - not financial advice."""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine as E  # noqa: E402
from build import INV, BULL, bars1  # noqa: E402

W = Path(__file__).resolve().parent
LO, HI = 950, 1300
CFGS = []
for trig in ("onset", "brk", "vwhold"):
    for geom in ("t1s1", "t05s1"):
        CFGS.append(dict(name=f"A-{trig}-{geom}", group="INV", side=1, dir=1, want=-2, trig=trig, geom=geom, lo=LO, hi=HI))
        CFGS.append(dict(name=f"B-{trig}-{geom}", group="BULL", side=-1, dir=-1, want=-2, trig=trig, geom=geom, lo=LO, hi=HI))
    CFGS.append(dict(name=f"C-{trig}-t1s1", group="BULL", side=1, dir=1, want=2, trig=trig, geom="t1s1", lo=LO, hi=HI))
# round 2 (pre-declared after round 1, before any CHECK/T2 read): strong-move filter on the vwhold mechanism
CFGS.append(dict(name="A2-vwhold-s30-t1s1", group="INV", side=1, dir=1, want=-2, trig="vwhold", geom="t1s1", lo=LO, hi=HI, spyfo=-0.30))
CFGS.append(dict(name="B2-vwhold-s30-t1s1", group="BULL", side=-1, dir=-1, want=-2, trig="vwhold", geom="t1s1", lo=LO, hi=HI, spyfo=-0.30))
CFGS.append(dict(name="A3-vwhold-nocomp-s30-t1s1", group="INV", side=1, dir=1, want=None, trig="vwhold", geom="t1s1", lo=LO, hi=HI, spyfo=-0.30))
CFGS.append(dict(name="B3-vwhold-nocomp-s30-t1s1", group="BULL", side=-1, dir=-1, want=None, trig="vwhold", geom="t1s1", lo=LO, hi=HI, spyfo=-0.30))
N = len(CFGS)
BAR = max(1.5, math.sqrt(2 * math.log(N)))


def spyday(F):
    s = F[F.symbol == "SPY"].groupby("date").agg(o=("dopen", "first"), c=("close", "last"))
    r = (s.c / s.o - 1) * 100
    return pd.Series(np.where(r >= 0.3, "up", np.where(r <= -0.3, "down", "flat")), index=s.index)


_BARS = {}


def bars_for(test, syms):
    for s in syms:
        if (test, s) not in _BARS:
            _BARS[(test, s)] = bars1(s, test)
    return {s: _BARS[(test, s)] for s in syms if _BARS[(test, s)] is not None}


def trades(test, F, C, cfg):
    sig = E.signals(F, C, cfg)
    if not len(sig):
        return sig
    bars = bars_for(test, sig.symbol.unique())
    sig = sig[sig.symbol.isin(bars)].reset_index(drop=True)
    return E.book(E.add_r(E.walk(sig, bars)))


def null_random_day(test, F, t, sessions, cfg, draws=20, seed=7):
    """matched random-entry null: each booked trade's symbol + entry tod moved to a random session of the same period;
    same geometry, costs, book. Returns the per-draw avg R list."""
    rng = np.random.default_rng(seed)
    fx = F[F.symbol.isin(t.symbol.unique())].set_index(["symbol", "date", "tod"])
    outs = []
    for d in range(draws):
        rd = rng.choice(sessions, size=len(t))
        keys = list(zip(t.symbol, rd, t.tod))
        ok = fx.index.isin(keys)
        h = fx[ok].reset_index()
        h = h[h.atr_d > 0]
        up, dn = E.GEOMS[cfg["geom"]]
        R = 0.25 * h.atr_d.to_numpy()
        e = h.close.to_numpy()
        s = cfg["side"]
        sig = pd.DataFrame({"symbol": h.symbol.values, "date": h.date.values, "tod": h.tod.values.astype(int), "side": s,
                            "entry": e, "stop": e - s * dn * R, "tgt": e + s * up * R, "risk": dn * R,
                            "gap": h.gap.fillna(0).values, "adv20": h.adv20.values})
        bars = bars_for(test, sig.symbol.unique())
        b = E.book(E.add_r(E.walk(sig.reset_index(drop=True), bars)))
        outs.append(float(b.r.mean()) if len(b) else np.nan)
    return outs


if __name__ == "__main__":
    mode = sys.argv[1]
    F = E.load("T1")
    C = E.compass(F)
    SD = spyday(F)
    h = E.half(SD.index)
    fit_s = list(SD.index[h == "fit"])
    chk_s = list(SD.index[h == "check"])
    print(f"N configs {N}, WB2 bar {BAR:.2f}, testing bar {max(1.35, 0.9 * BAR):.2f}; FIT sessions {len(fit_s)}, CHECK {len(chk_s)}")
    st = C[C.date.isin(fit_s)]
    dn_days = st[(st.state == -2) & (st.tod.between(LO, HI))].date.nunique()
    up_days = st[(st.state == 2) & (st.tod.between(LO, HI))].date.nunique()
    print(f"FIT sessions with DN state 09:50-13:00: {dn_days}; UP: {up_days}")
    if mode == "fit":
        rows = []
        allt = {}
        only = sys.argv[2].split(",") if len(sys.argv) > 2 else None
        for cfg in CFGS:
            if only and cfg["name"] not in only:
                continue
            t = trades("T1", F, C, cfg)
            t["half"] = E.half(t.date) if len(t) else []
            f = t[t.half == "fit"] if len(t) else t
            allt[cfg["name"]] = f
            s = E.stats(f, len(fit_s), SD)
            rows.append(dict(cfg=cfg["name"], **s))
            print(cfg["name"], s, flush=True)
        tag = "r2" if only else "r1"
        pd.DataFrame(rows).to_csv(W / f"fit_grid_{tag}.csv", index=False)
        pd.concat([v.assign(cfg=k) for k, v in allt.items() if len(v)]).to_parquet(W / f"fit_trades_{tag}.parquet")
    elif mode == "null":
        names = sys.argv[2].split(",")
        ft = pd.concat([pd.read_parquet(p) for p in sorted(W.glob("fit_trades_*.parquet"))])
        for nm in names:
            cfg = [c for c in CFGS if c["name"] == nm][0]
            t = ft[ft.cfg == nm]
            nl = null_random_day("T1", F, t, fit_s, cfg)
            nl = np.array(nl)
            print(nm, "actual", round(t.r.mean(), 4), "null mean", round(np.nanmean(nl), 4), "null sd", round(np.nanstd(nl), 4),
                  "pct", round(float((nl < t.r.mean()).mean()), 2), flush=True)
    elif mode == "check":
        names = sys.argv[2].split(",")
        for nm in names:
            cfg = [c for c in CFGS if c["name"] == nm][0]
            t = trades("T1", F, C, cfg)
            t["half"] = E.half(t.date)
            print("CHECK", nm, E.stats(t[t.half == "check"], len(chk_s), SD), flush=True)
            t[t.half == "check"].to_parquet(W / f"check_{nm}.parquet")


def t2(names):
    F2 = E.load("T2")
    F2 = F2[(F2.date >= "2023-01-03") & (F2.date <= "2024-09-13")]
    C2 = E.compass(F2)
    SD2 = spyday(F2)
    for nm in names:
        cfg = [c for c in CFGS if c["name"] == nm][0]
        t = trades("T2", F2, C2, cfg)
        print("T2", nm, E.stats(t, len(SD2), SD2), flush=True)
        t.to_parquet(W / f"t2_{nm}.parquet")


if __name__ == "__main__" and sys.argv[1] == "t2":
    t2(sys.argv[2].split(","))
