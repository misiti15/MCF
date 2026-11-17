"""Mechanic NM-RWN5: module parity - each copy's module mask (and the parent's) on the 2y + replay candidate rows equals the
sim's selection rule (before first-bar / cost filter). Result: parent 447/81, WB1 328/54, WB2 402/71, WB3 288/47 rows, all
match. Educational only - not financial advice."""
import importlib.util, pandas as pd, numpy as np
from sim import *
from common import WT, SETUP
D = load(); C2, _ = D["y2"]; RC, _ = D["rep"]
VR = (("volumeRatio", ">=", 0.45),)
for wb, v in {"parent": {}, "WB1": {"extra": VR}, "WB2": {"lo": 1005}, "WB3": {"lo": 1005, "extra": VR}}.items():
    path = f"{WT}/research/swarm1017/rework-ns/modules/RWN5-ns3-mon-weakrs-short.py" if wb == "parent" else f"{WT}/research/workbench/{SETUP}/modules/{SETUP}-{wb}.py"
    sp = importlib.util.spec_from_file_location("m", path); M = importlib.util.module_from_spec(sp); sp.loader.exec_module(M)
    for nm, C in (("2y", C2), ("rep", RC)):
        x = C.copy(); x["date"] = pd.to_datetime(x.date)
        a = x.copy(); a["vwapDistPct"] = a.prev_vwap; a["tod"] = a.tod - 5        # the previous bar, then this bar
        f = pd.concat([a, x]).sort_index(kind="stable").reset_index(drop=True)
        f["symbol"] = np.repeat(np.arange(len(x)), 2).astype(str)
        mk = M.mask(f)[1::2] & (x.adv20 >= 95e6).to_numpy() & (x.close >= 5).to_numpy()
        vv = {**PARENT, **v}; cc = C
        m2 = (cc.tod >= vv["lo"]) & (cc.tod <= vv["hi"]) & (cc.fromOpen < -2) & (cc.adv20 >= 95e6) & (cc.close >= 5) & (cc.vwapDistPct > 0) \
            & (cc.prev_vwap <= 0) & (cc.sma50_dist_pct > 0) & ((cc.fromOpen - cc.spy_fo) < 0) & (cc.dow == 0)
        for col, op, val in vv["extra"]: m2 &= OPS[op](cc[col], val)
        print(wb, nm, int(mk.sum()), int(m2.sum()), "match", int(mk.sum()) == int(m2.sum()) and bool((mk == m2.to_numpy()).all()))
