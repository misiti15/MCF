"""longs1013 Q3 mechanisms: lab replay of the primary and Testing 1 books under the live one-position-per-symbol rule
and six alternatives (PLAN.md section 4). Events: research/bdi/timeofday/data/trades.parquet (first qualifying bar per
symbol-day, open history, production-cost lab R). Hold 120 minutes (live mean ~118-137 min). Entry counts and existing
lab R only; no new setup is scored. Educational only - not financial advice.
"""
from __future__ import annotations

import heapq
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LAB = ROOT / "research" / "bdi" / "timeofday" / "data" / "trades.parquet"
FLAT = 15 * 60 + 55
HOLD = 120

PRIMARY = ["RW6G1-ns2-up3-vwap2sd-short", "NS1-rsidip-rsi5pop-long", "MF2-open-rsimidhi-flowsell",
           "NS5-sma50-flush-oversold-long", "NS4-pm-vwap-reclaim-oversold-short", "NS3-failed-vwap-reclaim-short",
           "MF1-945-flowsell-vwapup", "NS2-sma50break-overbought-short", "MF4-h40-open-flowsell",
           "MF3-open-flowsell-rsi5hi", "MF5-flowsell-vwapup-rsi5hi"]


def testing_order():
    y = yaml.safe_load(open(ROOT / "config" / "account_testing.yaml"))
    return y["live"]["setup_order"]


def events(names):
    t = pd.read_parquet(LAB)
    parts, missing = [], []
    for n in names:
        base, st = (n[:-3], "full") if n.endswith("-FD") else (n, "current")
        x = t[(t.setup == base) & (t.set == st)]
        if not len(x):
            missing.append(n)
            continue
        parts.append(x.assign(name=n)[["date", "symbol", "tod", "r", "side", "name"]])
    ev = pd.concat(parts, ignore_index=True)
    ev["m"] = (ev.tod // 100) * 60 + ev.tod % 100
    ev["s"] = np.where(ev.side == "long", 1, -1)
    return ev, missing


def replay(ev, order, slots, cap, longs_first=False, reserve=0, pyramid=0):
    """One position per symbol (pyramid > 0: a long may join a symbol held only by longs, up to `pyramid` positions)."""
    pri = {n: i for i, n in enumerate(order)}
    e = ev[ev.name.isin(pri)].copy()
    e["p"] = e.name.map(pri)
    e["sp"] = np.where(longs_first & (e.s == 1), 0, 1) if longs_first else 0
    e = e.sort_values(["date", "m", "sp", "p"], kind="stable")
    taken, why = [], []
    cur = None
    for d, sym, m, n, s in zip(e.date.to_numpy(), e.symbol.to_numpy(), e.m.to_numpy(), e.name.to_numpy(), e.s.to_numpy()):
        if d != cur:
            held, q, per, nshort, cur = {}, [], {}, 0, d
        while q and q[0][0] <= m:
            _, nn, ss, sy = heapq.heappop(q)
            per[nn] -= 1
            nshort -= ss == -1
            h = held[sy]
            h[0] -= 1
            if h[0] == 0:
                del held[sy]
        h = held.get(sym)
        if h is not None:
            if not (pyramid and s == 1 and h[1] == 1 and h[0] < pyramid):
                taken.append(False); why.append("short" if h[1] == -1 else "long"); continue
        if len(q) >= slots:
            taken.append(False); why.append("slots"); continue
        if s == -1 and reserve and nshort >= slots - reserve:
            taken.append(False); why.append("reserve"); continue
        if per.get(n, 0) >= cap:
            taken.append(False); why.append("cap"); continue
        until = min(FLAT, m + HOLD)
        heapq.heappush(q, (until, n, s, sym))
        if h is None:
            held[sym] = [1, s]
        else:
            h[0] += 1
        per[n] = per.get(n, 0) + 1
        nshort += s == -1
        taken.append(True); why.append(None)
    return e.assign(taken=taken, why=why)


def summarise(r, nd):
    out = {}
    for sd, nm in ((1, "long"), (-1, "short")):
        x = r[r.s == sd]
        tk = x[x.taken]
        out[f"{nm}_signals_day"] = round(len(x) / nd, 2)
        out[f"{nm}_taken_day"] = round(len(tk) / nd, 2)
        out[f"{nm}_exp"] = round(float(tk.r.mean()), 4) if len(tk) else None
        out[f"{nm}_lost_share"] = round(1 - len(tk) / len(x), 3) if len(x) else None
        out[f"{nm}_lost_to_short_day"] = round(((~x.taken) & (x.why == "short")).sum() / nd, 2)
        out[f"{nm}_lost_to_long_day"] = round(((~x.taken) & (x.why == "long")).sum() / nd, 2)
        out[f"{nm}_lost_caps_day"] = round(((~x.taken) & x.why.isin(["slots", "cap", "reserve"])).sum() / nd, 2)
        out[f"{nm}_blocked_exp"] = round(float(x[~x.taken].r.mean()), 4) if (~x.taken).any() else None
    return out


def diff(base, alt, nd):
    """Extra long trades/day (and their R), short trades displaced/day (and their R)."""
    k = ["date", "symbol", "name", "m"]
    b = base.set_index(k)["taken"]
    a = alt.set_index(k)["taken"].reindex(b.index)
    rr = base.set_index(k)["r"]
    ss = base.set_index(k)["s"]
    gained = (a & ~b)
    lost = (~a & b)
    out = {}
    for sd, nm in ((1, "long"), (-1, "short")):
        g, l_ = gained & (ss == sd), lost & (ss == sd)
        out[f"{nm}_gained_day"] = round(g.sum() / nd, 2)
        out[f"{nm}_gained_exp"] = round(float(rr[g].mean()), 4) if g.any() else None
        out[f"{nm}_lost_day"] = round(l_.sum() / nd, 2)
        out[f"{nm}_lost_exp"] = round(float(rr[l_].mean()), 4) if l_.any() else None
    out["net_R_day"] = round(float((rr[gained].sum() - rr[lost].sum()) / nd), 3)
    return out


def main():
    res = {}
    rows = []
    for acct, order, slots, cap in (("primary", PRIMARY, 160, 100), ("testing1", testing_order(), 400, 150)):
        ev, missing = events(order)
        order_lab = [n for n in order if n not in missing]
        nd = ev.date.nunique()
        base = replay(ev, order_lab, slots, cap)
        sc = {"M0 baseline": base,
              "Ma longs first on the same bar": replay(ev, order_lab, slots, cap, longs_first=True),
              "Mb reserve 10% of slots for longs": replay(ev, order_lab, slots, cap, reserve=int(0.10 * slots)),
              "Mb reserve 25% of slots for longs": replay(ev, order_lab, slots, cap, reserve=int(0.25 * slots)),
              "Mc long pyramid, 2 per symbol": replay(ev, order_lab, slots, cap, pyramid=2),
              "Ma+Mc": replay(ev, order_lab, slots, cap, longs_first=True, pyramid=2)}
        longs = [n for n in order_lab if ev[ev.name == n].s.iloc[0] == 1]
        lo = replay(ev, longs, slots, cap)                      # Me: long setups alone in a book
        res[acct] = {"missing": missing, "sessions": int(nd), "long_setups": longs, "scenarios": {}}
        for nm, r in sc.items():
            row = {"account": acct, "scenario": nm, **summarise(r, nd)}
            if nm != "M0 baseline":
                row.update(diff(base, r, nd))
            rows.append(row)
        # Me: compare each long setup's taken trades alone vs in the full book
        b_l = base[base.s == 1]
        row = {"account": acct, "scenario": "Me long setups in a long-only book", **summarise(lo, nd)}
        k = ["date", "symbol", "name", "m"]
        bb = b_l.set_index(k)["taken"]
        aa = lo.set_index(k)["taken"].reindex(bb.index)
        g = aa & ~bb
        row["long_gained_day"] = round(g.sum() / nd, 2)
        row["long_gained_exp"] = round(float(b_l.set_index(k)["r"][g].mean()), 4) if g.any() else None
        sh = base[(base.s == -1)]
        row["short_lost_day"] = None
        rows.append(row)
        # Md: shadow (what-if) trades = every blocked long signal counted as a simulated trade
        bl = base[(base.s == 1) & ~base.taken]
        rows.append({"account": acct, "scenario": "Md shadow trades (what-if) for blocked longs",
                     "long_gained_day": round(len(bl) / nd, 2), "long_gained_exp": round(float(bl.r.mean()), 4) if len(bl) else None,
                     "note": "statistical trades only, no capital"})
        # per long setup table under baseline / Ma / Mc / Me
        per = []
        for n in longs:
            x0 = base[base.name == n]
            d = {"setup": n, "signals_day": round(len(x0) / nd, 2), "base_taken_day": round(x0.taken.sum() / nd, 2),
                 "base_lost": round(1 - x0.taken.mean(), 3),
                 "lost_to_short": round(((~x0.taken) & (x0.why == "short")).mean(), 3),
                 "lost_to_long": round(((~x0.taken) & (x0.why == "long")).mean(), 3)}
            for nm, key in (("Ma", "Ma longs first on the same bar"), ("Mc", "Mc long pyramid, 2 per symbol"), ("Ma+Mc", "Ma+Mc")):
                y = sc[key][sc[key].name == n]
                d[f"{nm}_lost"] = round(1 - y.taken.mean(), 3)
            y = lo[lo.name == n]
            d["Me_lost"] = round(1 - y.taken.mean(), 3)
            d["exp_all_signals"] = round(float(x0.r.mean()), 4)
            d["exp_blocked"] = round(float(x0[~x0.taken].r.mean()), 4) if (~x0.taken).any() else None
            per.append(d)
        pd.DataFrame(per).to_csv(HERE / "tables" / f"crowd_lab_{acct}_longs.csv", index=False)
        print(acct, "\n", pd.DataFrame(per).to_string())
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "tables" / "crowd_lab_mechanisms.csv", index=False)
    pd.set_option("display.width", 300)
    print(out.T.to_string())
    json.dump(res, open(HERE / "tables" / "crowd_lab_meta.json", "w"), indent=1)


if __name__ == "__main__":
    main()
