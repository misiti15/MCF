"""Round-4 earnings variants (ULT-28 / 30 / 33 / 34 / 35) on the bench_var / bench10 normal-way engine, T1 only.
The event columns the live module reads from its daily allow-list (e_rd / e_surp, e_d2 / e_react, e_ok / e_r1 / e_k)
are added per month with each candidate's OWN frozen bt.py event builder (round4/ULT-*/bt.py), exactly as round 4
did; the rest (window, min_adv, 1-minute walk, time exit, LR8 + borrow, live book) is bench_var.
T2 is not computed: every event builder (and the modules' NYSE session list) starts 2024-08-01.
ULT-31 is not run: its frame needs ULT-11's extra feature build plus a per-half state table (see VARIANTS.md).
Educational only - not financial advice."""
from __future__ import annotations

import importlib.util
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bench10 as B  # noqa: E402
import bench_var as V  # noqa: E402

R4 = HERE.parent / "round4"
MODS = HERE.parent / "modules"
EARN_ENTRIES = {f"ULT-{k}-{s}": (MODS / f"ULT-{k}.py", 45) for k in (28, 30, 33, 34, 35) for s in ("long", "short")}
EARN_VARIANTS = {f"ULT-{k}": [f"ULT-{k}-long", f"ULT-{k}-short"] for k in (28, 30, 33, 34, 35)}


def bt(k):
    p = R4 / f"ULT-{k}" / "bt.py"
    sys.path.insert(0, str(p.parent))
    spec = importlib.util.spec_from_file_location(f"bt{k}", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def month_job(args):
    month, W = args
    import research.history2y.lib as lib
    lib.DATA = B.DATA
    V.ENTRIES.clear()
    V.ENTRIES.update(EARN_ENTRIES)
    inv = V.inventory()
    for st in inv:
        st["syms"] = None                    # live allow-list = the event columns below (today's list at import)
    mods = {st["setup"]: V.load(st["setup"], st["module"]) for st in inv}
    f = lib.load_month(month, context=True)
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    B.no_locked(f["date"].unique())
    k = f["symbol"] + "|" + f["date"]
    out = []
    # 28 / 33 / 35: reaction day (+ surprise)
    b28 = bt(28)
    ev, _, _ = b28.events()
    evm = ev[ev.rd.str[:7] == month]
    emap = dict(zip(evm.symbol.astype(str) + "|" + evm.rd, evm.surprise_pct))
    g = f.assign(e_rd=k.isin(emap.keys()).to_numpy(), e_surp=k.map(emap).astype(float).to_numpy())
    out.append(V.signals(g, [s for s in inv if s["setup"].startswith(("ULT-28", "ULT-33"))], mods))
    b35 = bt(35)
    ev = b35.events()
    ev = ev[0] if isinstance(ev, tuple) else ev
    evm = ev[ev.rd.str[:7] == month]
    emap = dict(zip(evm.symbol.astype(str) + "|" + evm.rd, evm.surprise_pct))
    g = f.assign(e_rd=k.isin(emap.keys()).to_numpy(), e_surp=k.map(emap).astype(float).to_numpy())
    out.append(V.signals(g, [s for s in inv if s["setup"].startswith("ULT-35")], mods))
    # 30: day-2 react
    b30 = bt(30)
    ev, _, sess, dl = b30.events()
    evm = ev[ev.d2.str[:7] == month]
    emap = dict(zip(evm.symbol.astype(str) + "|" + evm.d2, evm.react))
    evt = k.isin(emap.keys()).to_numpy()
    react = np.where(evt, k.map(emap).astype(float).to_numpy(), np.nan)   # live allow-list: event names only
    g = f.assign(e_d2=evt, e_react=react)
    out.append(V.signals(g, [s for s in inv if s["setup"].startswith("ULT-30")], mods))
    # 34: no-news day-2
    b34 = bt(34)
    ev = b34.event_table(mods["ULT-34-long"])
    ev = ev[ev.d.str[:7] == month]
    ek = ev.symbol + "|" + ev.d
    r1 = k.map(dict(zip(ek, ev.r1))).astype(float).to_numpy()
    pc = k.map(dict(zip(ek, ev.prev_close))).astype(float).to_numpy()
    ok = k.map(dict(zip(ek, (~ev.news) & ev.covered & (~ev.lev)))).fillna(False).astype(bool).to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        kk = np.abs(r1) / (100 * f["atr_d"].to_numpy(float) / pc)
    g = f.assign(e_ok=ok, e_r1=r1, e_k=kk)
    out.append(V.signals(g, [s for s in inv if s["setup"].startswith("ULT-34")], mods))
    o = pd.concat([x for x in out if len(x)], ignore_index=True) if any(len(x) for x in out) else pd.DataFrame()
    o.to_parquet(Path(W) / f"sig1e_{month}.parquet")
    return month, len(o), o.groupby("setup").size().to_dict() if len(o) else {}


if __name__ == "__main__":
    W = Path(sys.argv[1])
    import research.history2y.lib as lib
    lib.DATA = B.DATA
    ms = sys.argv[2].split(",") if len(sys.argv) > 2 and sys.argv[2] else [m for m in lib.months() if m not in B.LOCKED_MONTHS]
    ms = [m for m in ms if not (W / f"sig1e_{m}.parquet").exists()]
    with Pool(int(sys.argv[3]) if len(sys.argv) > 3 else 1) as p:
        for r in p.imap_unordered(month_job, [(m, str(W)) for m in ms]):
            print(r, flush=True)
