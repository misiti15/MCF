"""Parity: each module's mask on full open frames (2 months) == the scan's mask; guard parity on 40 symbol-days;
LabStrategy loads every module. Educational only - not financial advice."""
import ast
import importlib.util
import json

import numpy as np
import pandas as pd

import common as C
from mcf.data.bars import resample
from mcf.strategies.setups import LabStrategy
from research.history2y import lib

FN = pd.read_csv(C.HERE / "finalists.csv")
IDX = json.load(open(C.HERE / "modules" / "index.json"))
ctx = pd.read_parquet(C.SCR / "ctx.parquet")[["date", "tod", "spy_fo"]]
ctx["date"] = pd.to_datetime(ctx["date"]).dt.date
res = {}
mods = {}
for e in IDX:
    p = C.HERE / "modules" / f"{e['name']}.py"
    LabStrategy(e["name"], str(p), min_adv=95e6, window=(950, 1500))
    sp = importlib.util.spec_from_file_location(e["name"], p)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    mods[e["name"]] = m
for month in ("2025-05", "2026-03"):
    d = lib.load_month(month)
    d = d[(d.tod >= 950) & (d.tod <= 1500)].reset_index(drop=True)
    d = d.merge(ctx, on=["date", "tod"], how="left")
    d = d.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    big = (d.adv20 >= 95e6) & (d.atr_d > 0)
    for e in IDX:
        r = FN.iloc[e["i"]]
        mm = mods[e["name"]].mask(d) if e["k"] is None else None
        if e["k"] is not None:   # frames carry no volume: check the base layers, guard checked separately
            d2 = d.assign(volume=1.0)
            src = open(C.HERE / "modules" / f"{e['name']}.py").read()
            ns = {}
            exec(src.replace("return m & ~vwap_band_block", "return m | 0 * vwap_band_block"), ns)
            mm = ns["mask"](d2)
        got = set(map(tuple, d.loc[np.asarray(mm, bool) & big.to_numpy(), ["symbol", "date", "tod"]].astype(str).to_numpy()))
        th = ast.literal_eval(r.th)
        if e["k"] is not None:
            th = (th[0], th[1], "none")
        cm = C.core(r.parent, th) & C.WM[r.win]
        if isinstance(r.filters, str):
            for f in r.filters.split("+"):
                cm = cm & C.F[f]
        sel = cm & (pd.to_datetime(C.S.date).dt.strftime("%Y-%m").to_numpy() == month)
        want = set(map(tuple, C.S.loc[sel, ["symbol", "date", "tod"]].astype(str).to_numpy()))
        res.setdefault(e["name"], []).append({"month": month, "module": len(got), "scan": len(want), "equal": got == want})
    del d
# guard parity
G = C.G.copy()
G["ds"] = G.date.astype(str)
sd = G[["symbol", "ds"]].drop_duplicates().sample(40, random_state=1)
ok = tot = 0
for sym, ds_ in sd.itertuples(index=False):
    m1 = pd.read_parquet(C.ROOT / "data" / "cache_hist" / "1Min" / f"{sym}.parquet")
    m1 = m1[m1.index.strftime("%Y-%m-%d") == ds_]
    hm = m1.index.hour * 100 + m1.index.minute
    d5 = resample(m1[(hm >= 930) & (hm < 1600)], "5min")
    end = d5.index + pd.Timedelta(minutes=5)
    df = d5.copy()
    df["tod"] = end.hour * 100 + end.minute
    blk = mods["RWN1-rw6g1-rsi65-k25-t05s1-short"].vwap_band_block(df, 2.5)
    g = G[(G.symbol == sym) & (G.ds == ds_)].set_index("tod")["blk25"]
    s = pd.Series(blk, index=df.tod.to_numpy()).reindex(g.index)
    ok += int((s.to_numpy() == g.to_numpy()).sum())
    tot += len(g)
res["guard_parity_k2.5"] = {"bars": tot, "equal": ok}
json.dump(res, open(C.HERE / "verify.json", "w"), indent=1)
print(json.dumps(res, indent=1))
