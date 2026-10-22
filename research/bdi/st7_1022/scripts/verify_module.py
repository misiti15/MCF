"""st7_1022: module-vs-scan parity for modules/ST7Q-... on every open month (frames + context + QQQ/SPY vwapDistPct at
the same (date, tod) as `qqq_vwap`), and the module without `qqq_vwap` fires nothing (fail safe). Also checks the parent
FD module reproduces P0. Writes verify.json. Educational only - not financial advice."""
import importlib.util
import json
from multiprocessing import Pool

import numpy as np
import pandas as pd

from core import load, first_per_symday, p0_cond
from sc import HERE, ROOT, lib, no_locked


def mod(p, nm):
    s = importlib.util.spec_from_file_location(nm, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


MQ = HERE / "modules" / "ST7Q-rsi50dn-qqqbelowvwap-long-t1s1-FD.py"
MP = ROOT / "research/bdi/fullday/ST7-rsi50dn-long-pm-t1s1-FD.py"


def job(month):
    f = lib.load_month(month, context=True)
    f["symbol"] = f["symbol"].astype(str)
    no_locked(f["date"].unique())
    ix = f[f["symbol"].isin(["QQQ"])].pivot_table(index=["date", "tod"], columns="symbol", values="vwapDistPct")
    ix.columns = ["qqq_vwap"]
    f = f.merge(ix.reset_index(), on=["date", "tod"], how="left")
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    tod = f["tod"].to_numpy()
    ok = (f["adv20"].fillna(0).to_numpy() >= 95e6) & (f["atr_d"].to_numpy(float) > 0) & \
        np.isfinite(f["r_long_t1s1"].to_numpy(float)) & (tod >= 950) & (tod <= 1500)
    out = {}
    for nm, p in (("q", MQ), ("p", MP)):
        with np.errstate(invalid="ignore"):
            mk = mod(p, "m" + nm).mask(f) & ok
        x = f.loc[mk, ["symbol", "date", "tod"]]
        x = x[~x.duplicated(["symbol", "date"])]
        out[nm] = set(zip(x.symbol, x.date.astype(str), x.tod.astype(int)))
    with np.errstate(invalid="ignore"):
        out["failsafe"] = int(mod(MQ, "mq2").mask(f.drop(columns="qqq_vwap")).sum())
    return month, out


def main():
    cand, *_ = load()
    base = p0_cond(cand)
    with np.errstate(invalid="ignore"):
        h1 = first_per_symday(cand, base & (cand["qqq_vwap"] <= 0).to_numpy())
    p0 = first_per_symday(cand, base)
    S = {"q": set(zip(cand.loc[h1].symbol, cand.loc[h1].date.astype(str), cand.loc[h1].tod.astype(int))),
         "p": set(zip(cand.loc[p0].symbol, cand.loc[p0].date.astype(str), cand.loc[p0].tod.astype(int)))}
    M = {"q": set(), "p": set()}
    fs = 0
    with Pool(3) as pool:
        for month, o in pool.imap_unordered(job, lib.months()):
            M["q"] |= o["q"]; M["p"] |= o["p"]; fs += o["failsafe"]
    res = {k: {"scan": len(S[k]), "module": len(M[k]), "same": len(S[k] & M[k])} for k in S}
    res["failsafe_signals_without_qqq_vwap"] = fs
    res["ok"] = all(res[k]["scan"] == res[k]["module"] == res[k]["same"] for k in ("q", "p")) and fs == 0
    print(json.dumps(res, indent=1))
    json.dump(res, open(HERE / "verify.json", "w"), indent=1)


if __name__ == "__main__":
    main()
