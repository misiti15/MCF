"""BURST1: enrich the 2-year lab trade lists (bt_lab1104) with entry price, stop % and 5-min mark-to-market / MFE paths
(stop units, gross) on the same frames + head/tail bars bt_all.py walked. Open months only (locked block never read).
Usage: python enrich.py <scratch> [procs] -> <scratch>/enr/<month>.parquet + <month>_mk.npy / _mfe.npy (float16, 74 slots
09:50..15:55). Educational only - not financial advice."""
import os, sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT / "research" / "history2y"))
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "burst1 never reads the locked block"
import lib  # noqa: E402

BT = ROOT / "research/history2y/data/bt_lab1104"
HT = ROOT / "research/bdi/cwt/test_b/data/headtail.parquet"
DN = {"t1s1": 1.0, "t05s1": 1.0, "t1s05": 0.5, "t05s05": 0.5}
NS = 74


def slot(tod):
    tod = np.asarray(tod)
    return ((tod // 100) * 60 + tod % 100 - 590) // 5


def job(args):
    month, S = args
    T = pd.read_parquet(BT / f"sig_{month}.parquet").reset_index(drop=True)
    f = lib.load_month(month, columns=["symbol", "date", "tod", "high", "low", "close", "atr_d"])
    f["symbol"] = f.symbol.astype(str); f["date"] = f.date.astype(str)
    a = pd.Timestamp(month + "-01")
    ht = pd.read_parquet(HT, filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1))])
    ht = ht[ht.tod > 1500].rename(columns={"h": "high", "l": "low", "c": "close"})
    ht["symbol"] = ht.symbol.astype(str); ht["date"] = pd.to_datetime(ht.date).dt.date.astype(str)
    P = pd.concat([f[["symbol", "date", "tod", "high", "low", "close"]], ht[["symbol", "date", "tod", "high", "low", "close"]]],
                  ignore_index=True).sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    key = (P.symbol + "|" + P.date).values
    st = np.flatnonzero(np.r_[True, key[1:] != key[:-1]]); en = np.r_[st[1:], len(key)]
    rng = dict(zip(key[st], zip(st, en)))
    Ph, Pl, Pc = (P[k].to_numpy(float) for k in ("high", "low", "close")); Pt = P.tod.to_numpy()
    fk = (f.symbol + "|" + f.date + "|" + f.tod.astype(str)).values
    fi = dict(zip(fk, range(len(f))))
    fc, fa = f.close.to_numpy(float), f.atr_d.to_numpy(float)
    n = len(T); MK = np.full((n, NS), np.nan, np.float16); MF = np.full((n, NS), np.nan, np.float16)
    E = np.full(n, np.nan); SP = np.full(n, np.nan)
    for i, r in enumerate(T.itertuples()):
        j0 = fi.get(f"{r.symbol}|{r.date}|{r.tod}")
        if j0 is None:
            continue
        e = fc[j0]; Ru = 0.25 * fa[j0] * DN[r.geom]; E[i] = e; SP[i] = Ru / e
        a_, b_ = rng[r.symbol + "|" + r.date]; tt = Pt[a_:b_]
        j = np.searchsorted(tt, r.tod, side="right"); k = np.searchsorted(tt, r.xtod, side="right")
        s0 = int(slot(r.tod)); MK[i, s0] = 0; MF[i, s0] = 0
        if k > j:
            ts = slot(tt[j:k]); ok = (ts >= 0) & (ts < NS)
            mk = r.side * (Pc[a_:b_][j:k] - e) / Ru
            ex = (Pl[a_:b_][j:k] if r.side == -1 else Ph[a_:b_][j:k])
            mf = np.maximum.accumulate(r.side * (ex - e) / Ru)
            MK[i, ts[ok]] = np.clip(mk[ok], -60, 60); MF[i, ts[ok]] = np.clip(mf[ok], -60, 60)
    T["entry"] = E; T["stop_pct"] = SP
    out = Path(S) / "enr"; T.to_parquet(out / f"{month}.parquet")
    np.save(out / f"{month}_mk.npy", MK); np.save(out / f"{month}_mfe.npy", MF)
    return month, n, int(np.isnan(E).sum())


if __name__ == "__main__":
    S = Path(sys.argv[1]); (S / "enr").mkdir(parents=True, exist_ok=True)
    ms = [m for m in lib.months() if m not in lib.LOCKED_MONTHS and (BT / f"sig_{m}.parquet").exists()]
    with Pool(int(sys.argv[2]) if len(sys.argv) > 2 else 4) as p:
        for r in p.imap_unordered(job, [(m, str(S)) for m in ms]):
            print(r, flush=True)
