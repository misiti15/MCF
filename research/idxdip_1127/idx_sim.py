"""IDXDIP-1127 simulator (PREREG.md). Engine E4 = QQQOPEN-1127 qo_sim rules (FADE-LONG / FADE-SHORT) with the check time T,
bounce fraction B and a +2R target exit as parameters, plus the +1 minute entry stress (S1). Gross R only; costs in
idx_score.py. Locked block 2024-11-01..2025-02-28 dropped at load and asserted absent.
    python research/idxdip_1127/idx_sim.py OUT_DIR RAW_DIR[,RAW_DIR2...]
Educational only - not financial advice."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "qqqopen_1127"))
import qo_sim  # noqa: E402

MAIN = Path("/home/user/MCF")
LOCK = qo_sim.LOCK
PAIRS = {"SPY": "SPXL", "QQQ": "TQQQ", "IWM": "TNA", "DIA": "UDOW"}


def configs():
    out = []
    for sig in ("SPY", "QQQ", "IWM"):
        for X in (0.75, 1.0, 1.5):
            for T in (585, 595, 615):
                out.append(dict(grp="G1", sig=sig, X=X, T=T, B=0.20, exit="TRAIL", side=1))
    for X in (0.75, 1.0, 1.5):
        out.append(dict(grp="G2", sig="DIA", X=X, T=595, B=0.20, exit="TRAIL", side=1))
    for sig, X in (("SPY", 0.75), ("QQQ", 1.5)):
        out.append(dict(grp="G3", sig=sig, X=X, T=595, B=0.35, exit="TRAIL", side=1))
        out.append(dict(grp="G3", sig=sig, X=X, T=595, B=0.20, exit="HOLD", side=1))
        out.append(dict(grp="G3", sig=sig, X=X, T=595, B=0.20, exit="TGT2", side=1))
    for sig, X in (("SPY", 0.75), ("SPY", 1.0), ("QQQ", 1.0), ("QQQ", 1.5)):
        out.append(dict(grp="G4", sig=sig, X=X, T=595, B=0.20, exit="TRAIL", side=-1))
    for c in out:
        c["trd"] = PAIRS[c["sig"]]
        c["name"] = f"{c['grp']}|{'L' if c['side'] == 1 else 'S'}|{c['sig']}|{c['X']}|{c['T'] // 60:02d}{c['T'] % 60:02d}|B{c['B']}|{c['exit']}"
    assert len(out) == 40
    return out


def load(sym: str, raws) -> pd.DataFrame:
    raw = [r / f"{sym}_2016_2022.parquet" for r in raws if (r / f"{sym}_2016_2022.parquet").exists()][0]
    parts = [pd.read_parquet(raw), pd.read_parquet(MAIN / "data/cache_fresh/1Min" / f"{sym}.parquet"),
             pd.read_parquet(MAIN / "data/cache_hist/1Min" / f"{sym}.parquet")]
    out = []
    for p in parts:
        p = p[["open", "high", "low", "close", "volume"]].copy()
        p.index = pd.DatetimeIndex(p.index).tz_convert("America/New_York")
        out.append(p)
    df = pd.concat(out).sort_index()
    df = df[~df.index.duplicated(keep="last")].between_time("09:30", "15:59")
    d = df.index.date
    df = df[~((d >= LOCK[0]) & (d <= LOCK[1]))]
    df = df[df.index.date <= pd.Timestamp("2026-11-04").date()]
    assert not ((df.index.date >= LOCK[0]) & (df.index.date <= LOCK[1])).any()
    return df


def simulate(o, h, l, c, mins, j, fill, stop, side, exit_min, trail, tgt):
    risk = side * (fill - stop)
    if risk <= 0:
        return None
    mfe = 0.0
    tp = fill + side * tgt * risk if tgt else None
    for k in range(j, len(o)):
        if mins[k] >= exit_min:
            return side * (o[k] - fill) / risk, 0, k, o[k], risk
        hit = (l[k] <= stop) if side == 1 else (h[k] >= stop)
        if hit:
            gap = (o[k] < stop) if side == 1 else (o[k] > stop)
            px = o[k] if (gap and k > j) else stop
            return side * (px - fill) / risk, 1, k, px, risk
        if tp is not None and ((h[k] >= tp) if side == 1 else (l[k] <= tp)):
            gap = (o[k] > tp) if side == 1 else (o[k] < tp)
            px = o[k] if (gap and k > j) else tp
            return side * (px - fill) / risk, 2, k, px, risk
        fav = h[k] if side == 1 else l[k]
        mfe = max(mfe, side * (fav - fill) / risk)
        if trail and mfe >= 1.0:
            tr = fill + side * (mfe - 1.0) * risk
            stop = max(stop, tr) if side == 1 else min(stop, tr)
    return side * (c[-1] - fill) / risk, 0, len(o) - 1, c[-1], risk


def day_rows(ix, tx, cfgs):
    rows = []
    if len(ix) < 60 or len(tx) < 60:
        return rows
    imin = qo_sim.tmin(ix.index); tmn = qo_sim.tmin(tx.index)
    if imin[0] != 570 or tmn[0] != 570:
        return rows
    exit_min = min(955, max(imin[-1], tmn[-1]) + 1 - 5)
    io, ih, il, ic = (ix[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    to_, th, tl, tc = (tx[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    O = io[0]; tO = to_[0]; ends = imin + 1
    run_lo = np.minimum.accumulate(il); run_hi = np.maximum.accumulate(ih)
    day = ix.index[0].date()
    for cf in cfgs:
        side, X, T, B = cf["side"], cf["X"], cf["T"], cf["B"]
        thr = O * (1 - X / 100) if side == 1 else O * (1 + X / 100)
        dipped = ((run_lo <= thr) if side == 1 else (run_hi >= thr)) & (ends <= T)
        if not dipped.any():
            continue
        i0 = int(np.argmax(dipped)); trig = None
        for i in range(i0, len(ix)):
            if ends[i] > T + 10:
                break
            if ends[i] < T - 5:
                continue
            ok = (ic[i] >= run_lo[i] + B * (O - run_lo[i])) if side == 1 else (ic[i] <= run_hi[i] - B * (run_hi[i] - O))
            if ok:
                trig = i; break
        if trig is None:
            continue
        k = int(np.searchsorted(tmn, imin[trig], side="right")) - 1
        if k < 0 or k + 2 >= len(tx):
            continue
        seg_lo = tl[: k + 1].min(); seg_hi = th[: k + 1].max(); px = tc[k]
        if side == 1:
            drop = tO - seg_lo
            if not (drop > 0 and px > seg_lo):
                continue
            stop = seg_lo - 0.10 * drop
        else:
            rise = seg_hi - tO
            if not (rise > 0 and px < seg_hi):
                continue
            stop = seg_hi + 0.10 * rise
        base = None
        for var, j in (("BASE", k + 1), ("S1", k + 2)):
            if tmn[j] >= exit_min:
                break
            fill = to_[j]
            r = simulate(to_, th, tl, tc, tmn, j, fill, stop, side, exit_min, cf["exit"] == "TRAIL",
                         2.0 if cf["exit"] == "TGT2" else 0.0)
            if r is None:
                if var == "BASE":
                    break
                # S1: price already through the stop at the delayed fill -> stopped at the fill (loss of the gap)
                g, kind, kx, xp, risk = (-1.0 if base is None else -abs(base["risk"]) / base["risk"]), 1, j, fill, base["risk"]
                rows.append(dict(base, var="S1", entry=fill, exit_px=xp, kind=1, gross=-1.0, risk=base["risk"],
                                 emin=int(tmn[j]), tod=int(tx.index[j].hour * 100 + tx.index[j].minute)))
                continue
            g, kind, kx, xp, risk = r
            row = dict(name=cf["name"], grp=cf["grp"], date=str(day), split=qo_sim.split_of(day), sig=cf["sig"],
                       trd=cf["trd"], side=side, var=var, entry=fill, exit_px=xp, risk=risk, kind=kind, gross=g,
                       tod=int(tx.index[j].hour * 100 + tx.index[j].minute), emin=int(tmn[j]), xmin=int(tmn[kx]),
                       stop_pct=risk / fill * 100)
            if var == "BASE":
                base = row
            rows.append(row)
    return rows


def main(out, raws):
    out = Path(out); raws = [Path(r) for r in raws.split(",")]
    cfgs = configs()
    rows = []
    ctx = []
    for sig, trd in PAIRS.items():
        I = load(sig, raws); T = load(trd, raws)
        gI = {d: g for d, g in I.groupby(I.index.date)}
        gT = {d: g for d, g in T.groupby(T.index.date)}
        cs = [c for c in cfgs if c["sig"] == sig]
        for d in sorted(gI):
            if d in gT:
                rows += day_rows(gI[d], gT[d], cs)
        dd = I.groupby(I.index.date).agg(c=("close", "last"))
        dd["above50"] = dd.c.shift(1) > dd.c.rolling(50).mean().shift(1)
        dd["sig"] = sig
        ctx.append(dd.reset_index(names="date"))
        print(sig, len(gI), "days", flush=True)
    df = pd.DataFrame(rows)
    d = pd.to_datetime(df.date).dt.date
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any()
    df.to_csv(out / "idx_trades.csv.gz", index=False)
    c = pd.concat(ctx); c["date"] = c.date.astype(str); c.to_csv(out / "idx_ctx.csv.gz", index=False)
    print(df[df["var"] == "BASE"].groupby("name").size().to_string())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
