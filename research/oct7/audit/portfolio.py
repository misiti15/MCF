"""AUDIT: filter tests vs heat_fade_long base, and portfolio impact via the production Backtester.allocate
(live setups' trades from research/oct7/exits Lab base + each finalist). Train/valid only.
Educational only - not financial advice."""
import copy
import json
import pickle
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
sys.path.insert(0, "research/oct7/audit")
from analyse import filt, stats, tday, TRAIN_END  # noqa: E402
from mcf.backtest.engine import Trade  # noqa: E402
from research.oct7.exits.study import Lab  # noqa: E402

C = pickle.load(open("research/oct7/audit/data/C.pkl", "rb"))
raw = pickle.load(open("research/oct7/audit/data/cands.pkl", "rb"))["cands"]
res = {}
# ---- 1. filters on heat_fade_long
B = C[C.setup == "hfl_base"].reset_index(drop=True)
B["key"] = B.symbol + "|" + B.date
for x in (3, 4, 5, 6):
    res[f"hfl_fo<=-{x}"] = filt(B, (B.fo_sig <= -x).to_numpy(), x)
D4 = C[C.setup == "hfl_deep4"]
k4 = set(D4.symbol + "|" + D4.date)
res["deep4_equals_filter"] = bool(k4 == set(B.key[B.fo_sig <= -4]))
for nm in ("hfl_pdl", "hfl_pdl_95m"):
    P = C[C.setup == nm].copy()
    P["key"] = P.symbol + "|" + P.date
    m = B.merge(P[["key", "entry_time"]], on="key", how="inner", suffixes=("", "_p"))
    res[f"{nm}_overlap"] = {"pdl_n": len(P), "same_symbol_day_as_base": len(m),
                            "same_entry_time": int((m.entry_time == m.entry_time_p).sum()),
                            "not_in_base_symbol_day": int(len(P) - len(m)),
                            "overlap_with_deep4": int(len(set(P.key) & k4))}
    out = {}
    for sp in ("train", "valid"):
        b, p = B[B.split == sp], P[P.split == sp]
        days = sorted(set(b.date) | set(p.date))
        diff = p.groupby("date").pnl.sum().reindex(days, fill_value=0) - b.groupby("date").pnl.sum().reindex(days, fill_value=0)
        out[sp] = {"d_usd_vs_base": round(diff.sum(), 0), "d_t_day": round(tday(diff), 2), "d_ex_best": round(diff.sum() - diff.max(), 0)}
    res[f"{nm}_vs_base"] = out
# daily-sum-R t for deep4/base (the autopsy reported $ t)
for nm in ("hfl_base", "hfl_deep4", "hfl_pdl", "gapdn", "gapdn_rsi3"):
    s = C[C.setup == nm]
    res[f"{nm}_t_dailysumR"] = {sp: round(tday(s[s.split == sp].groupby("date").r.sum()), 2) for sp in ("train", "valid")}
    res[f"{nm}_by_week_usd"] = {str(k): v for k, v in s.groupby(pd.to_datetime(s.date).dt.isocalendar().week.astype(int)).pnl.sum().round(0).items()}

# ---- 2. portfolio
lab = Lab()
live = [copy.copy(t) for t in lab.base.values() if t is not None]
live_nohfl = [t for t in live if t.strategy != "heat_fade_long"]


def trades(name, rename):
    out = []
    for c in raw:
        if c["setup"] == name:
            d = dict(c["trade"])
            d["strategy"] = rename
            out.append(Trade(**d))
    return out


def alloc(cands):
    df = lab.bt.allocate([copy.copy(t) for t in cands])
    df["date"] = df["date"].astype(str)
    df["split"] = np.where(df.date <= TRAIN_END, "train", "valid")
    df["r"] = df["r_multiple"]
    df["ext"] = False
    df["slot_bound"] = False
    df["reason"] = df["exit_reason"]
    return df


P0 = alloc(live)
port = {"live_current": P0}
port["replace_hfl_with_deep4"] = alloc(live_nohfl + trades("hfl_deep4", "heat_fade_long"))
port["replace_hfl_with_pdl"] = alloc(live_nohfl + trades("hfl_pdl", "heat_fade_long"))
port["live_plus_gapdn"] = alloc(live + trades("gapdn", "gapdn"))
port["live_plus_gapdn_rsi3"] = alloc(live + trades("gapdn_rsi3", "gapdn"))
# realistic cap: 20 gapdn per day (earliest entry, then alphabetical = allocator order)
g = sorted(trades("gapdn", "gapdn"), key=lambda t: (t.date, t.entry_time, t.symbol))
g20, cnt = [], {}
for t in g:
    cnt[t.date] = cnt.get(t.date, 0) + 1
    if cnt[t.date] <= 20:
        g20.append(t)
port["live_plus_gapdn_cap20"] = alloc(live + g20)
res["portfolio"] = {}
for k, df in port.items():
    r = {}
    for sp in ("train", "valid"):
        a, b = df[df.split == sp], P0[P0.split == sp]
        days = sorted(set(a.date) | set(b.date))
        diff = a.groupby("date").pnl.sum().reindex(days, fill_value=0) - b.groupby("date").pnl.sum().reindex(days, fill_value=0)
        tot = a.groupby("date").pnl.sum().reindex(days, fill_value=0)
        r[sp] = {"n": len(a), "usd": round(a.pnl.sum(), 0), "t_day_portfolio": round(tday(tot), 2),
                 "worst_day": round(tot.min(), 0), "d_usd_vs_live": round(diff.sum(), 0), "d_t_day": round(tday(diff), 2),
                 "d_ex_best": round(diff.sum() - diff.max(), 0),
                 "by_setup": a.groupby("strategy").pnl.agg(["size", "sum"]).round(0).to_dict("index"),
                 "max_concurrent_new": int(a[a.strategy == "gapdn"].groupby("date").size().max()) if "gapdn" in set(a.strategy) else None}
    res["portfolio"][k] = r
    print(k, json.dumps({sp: {x: r[sp][x] for x in r[sp] if x != "by_setup"} for sp in r}), flush=True)
    print("   ", {sp: r[sp]["by_setup"] for sp in r}, flush=True)
for k in [k for k in res if k != "portfolio"]:
    print(k, json.dumps(res[k], default=str))
json.dump(res, open("research/oct7/audit/portfolio.json", "w"), indent=1, default=str)
# overlap of gapdn with exhaustion_short (same symbol-day, both short in the afternoon)
ex = {(t.symbol, str(t.date)) for t in live if t.strategy == "exhaustion_short"}
gd = C[C.setup == "gapdn"]
res["gapdn_overlap_exhaustion_symbol_days"] = int(sum((s, d) in ex for s, d in zip(gd.symbol, gd.date)))
res["gapdn_entry_tod_share_1300"] = round(float((pd.to_datetime(gd.entry_time).dt.strftime("%H:%M") == "13:00").mean()), 3)
res["gapdn_per_day"] = gd.groupby("date").size().describe().round(1).to_dict()
print({k: res[k] for k in ("gapdn_overlap_exhaustion_symbol_days", "gapdn_entry_tod_share_1300", "gapdn_per_day")})
json.dump(res, open("research/oct7/audit/portfolio.json", "w"), indent=1, default=str)
