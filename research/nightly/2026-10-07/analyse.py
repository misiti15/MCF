"""Allocate each configuration with the production allocator and score it (train / valid).
Reads the candidate pickles written by collect.py. Educational only - not financial advice.

Configurations (vs `base` = config/default.yaml as is):
  H1a  hfs_start0955, hfs_start1000        heat_fade_short first allowed bar close 09:55 / 10:00
  H1b  hfs_range_k0.15, hfs_range_k0.25     skip heat_fade_short on a name whose 09:45-09:49 1-min bars
                                            span (max high - min low) > k x prior-day daily ATR(14)
  H2   opposite_side_block                  post-filter: after a same-day STOP exit on a symbol, drop later
                                            entries on it in the opposite direction (any setup), in time order
  H3   orb20a_until1030, orb20a_until1100   orb20_a entry_until
       exh_end1400, exh_end1430             exhaustion_short last bar close
Gate: total R AND expectancy better on train and on valid, valid day-clustered t of the paired daily
difference >= 1.0, ex-best-day difference still > 0 (train and valid).
"""
import sys, json, copy
sys.path.insert(0, ".")
import glob
import numpy as np
import pandas as pd
from mcf.backtest.engine import Backtester, Trade
from mcf.config import load_config
from mcf.data.store import BarStore
from mcf.data.bars import daily_from_intraday
from mcf import features as F

D = "research/nightly/2026-10-07/"
TRAIN_END, VALID_END = pd.Timestamp("2026-08-25"), pd.Timestamp("2026-09-15")
LIVE = ["heat_fade_short", "heat_fade_long", "exhaustion_short", "orb20_a", "intraday_momentum"]
cfg = load_config()
bt = Backtester([], cfg)

c = pd.concat([pd.read_pickle(p) for p in sorted(glob.glob(D + "cands_*.pkl"))], ignore_index=True)
c["date"] = pd.to_datetime(c["date"]).dt.date
c = c[pd.to_datetime(c["date"]) <= VALID_END]
print("candidates by strategy:\n", c.groupby("strategy").size())
DAYS = sorted(c["date"].unique())
SPLIT = {d: ("train" if pd.Timestamp(d) <= TRAIN_END else "valid") for d in DAYS}


def allocate(cands: pd.DataFrame) -> pd.DataFrame:
    trs = [Trade(**{k: v for k, v in r.items()}) for r in cands.to_dict("records")]
    out = bt.allocate(trs)
    out["split"] = out["date"].map(SPLIT)
    return out


def swap(base, live_name, variant_name):
    v = c[c["strategy"] == variant_name].copy()
    v["strategy"] = live_name
    return pd.concat([base[base["strategy"] != live_name], v], ignore_index=True)


# ---------- H1b: 09:45-09:49 range / ATR for heat_fade_short candidate symbol-days
def range_ratio(cands):
    store = BarStore(cfg["data"]["cache_dir"])
    out = {}
    for sym in sorted(cands["symbol"].unique()):
        df = store.load(sym, end="2026-09-16")
        atr = F.atr(daily_from_intraday(df)).shift(1)
        for d in cands.loc[cands["symbol"] == sym, "date"].unique():
            b = df[df.index.date == d].between_time("09:45", "09:49")
            a = atr.get(pd.Timestamp(d), np.nan)
            out[(sym, d)] = (b["high"].max() - b["low"].min()) / a if len(b) and a > 0 else np.nan
    return out


def opposite_filter(tr):
    tr = tr.sort_values(["entry_time", "symbol"]).reset_index(drop=True)
    keep, stops = [], {}   # (symbol, date) -> list of (exit_time, side) of KEPT stopped trades
    for i, r in tr.iterrows():
        k = (r.symbol, r.date)
        if any(r.entry_time >= et and r.side == -s for et, s in stops.get(k, [])):
            continue
        keep.append(i)
        if r.exit_reason == "stop":
            stops.setdefault(k, []).append((r.exit_time, r.side))
    return tr.loc[keep].reset_index(drop=True), tr.drop(index=keep)


def stats(tr, split, strat=None):
    x = tr[tr["split"] == split]
    if strat:
        x = x[x["strategy"] == strat]
    r = x["r_multiple"]
    days = [d for d in DAYS if SPLIT[d] == split]
    daily = x.groupby("date")["r_multiple"].sum().reindex(days, fill_value=0.0)
    n = len(r)
    return {"n": n, "exp": r.mean() if n else np.nan, "se": r.std(ddof=1) / np.sqrt(n) if n > 1 else np.nan,
            "wr": (r > 0).mean() if n else np.nan, "total": r.sum(),
            "ex_best_day": r.sum() - daily.max() if n else 0.0,
            "day_t": daily.mean() / (daily.std(ddof=1) / np.sqrt(len(daily))) if daily.std(ddof=1) > 0 else np.nan,
            "days": len(days)}


def diff(tr, base, split, strat=None):
    days = [d for d in DAYS if SPLIT[d] == split]
    def daily(t):
        x = t[t["split"] == split]
        if strat:
            x = x[x["strategy"] == strat]
        return x.groupby("date")["r_multiple"].sum().reindex(days, fill_value=0.0)
    dd = daily(tr) - daily(base)
    sd = dd.std(ddof=1)
    return {"d_total": dd.sum(), "d_t": dd.mean() / (sd / np.sqrt(len(dd))) if sd > 0 else np.nan,
            "d_ex_best_day": dd.sum() - dd.max(), "d_best_day": dd.max(), "d_days_nonzero": int((dd != 0).sum())}


base_c = c[c["strategy"].isin(LIVE)]
configs = {"base": base_c}
configs["hfs_start0955"] = swap(base_c, "heat_fade_short", "heat_fade_short__start955")
configs["hfs_start1000"] = swap(base_c, "heat_fade_short", "heat_fade_short__start1000")
hfs = base_c[base_c["strategy"] == "heat_fade_short"]
rr = range_ratio(hfs)
base_c = base_c.assign(rr=[rr.get((s, d), np.nan) if st == "heat_fade_short" else np.nan
                           for s, d, st in zip(base_c.symbol, base_c.date, base_c.strategy)])
for k in (0.15, 0.25):
    drop = (base_c["strategy"] == "heat_fade_short") & (base_c["rr"] > k)
    configs[f"hfs_range_k{k}"] = base_c[~drop].drop(columns="rr")
base_c = base_c.drop(columns="rr")
configs["orb20a_until1030"] = swap(base_c, "orb20_a", "orb20_a__until1030")
configs["orb20a_until1100"] = swap(base_c, "orb20_a", "orb20_a__until1100")
configs["exh_end1400"] = swap(base_c, "exhaustion_short", "exhaustion_short__end1400")
configs["exh_end1430"] = swap(base_c, "exhaustion_short", "exhaustion_short__end1430")

TARGET = {"hfs_start0955": "heat_fade_short", "hfs_start1000": "heat_fade_short",
          "hfs_range_k0.15": "heat_fade_short", "hfs_range_k0.25": "heat_fade_short",
          "orb20a_until1030": "orb20_a", "orb20a_until1100": "orb20_a",
          "exh_end1400": "exhaustion_short", "exh_end1430": "exhaustion_short", "opposite_side_block": None}

alloc = {k: allocate(v) for k, v in configs.items()}
alloc["opposite_side_block"], dropped = opposite_filter(alloc["base"])
dropped["split"] = dropped["date"].map(SPLIT)
base = alloc["base"]
for k, v in alloc.items():
    v.to_csv(D + f"trades_{k}.csv", index=False)

rows = []
for k, tr in alloc.items():
    for split in ("train", "valid"):
        row = {"config": k, "split": split, "scope": "portfolio", **stats(tr, split)}
        if k != "base":
            row.update(diff(tr, base, split))
        rows.append(row)
        s = TARGET.get(k)
        if s:
            row = {"config": k, "split": split, "scope": s, **stats(tr, split, s), **diff(tr, base, split, s)}
            rows.append(row)
for s in LIVE:
    for split in ("train", "valid"):
        rows.append({"config": "base", "split": split, "scope": s, **stats(base, split, s)})
res = pd.DataFrame(rows)
res.to_csv(D + "results.csv", index=False)

# gate
gate = {}
for k in TARGET:
    p = res[(res.config == k) & (res.scope == "portfolio")].set_index("split")
    b = res[(res.config == "base") & (res.scope == "portfolio")].set_index("split")
    ok = all(p.loc[s, "total"] > b.loc[s, "total"] and p.loc[s, "exp"] > b.loc[s, "exp"] for s in ("train", "valid"))
    gate[k] = {"better_train_valid": bool(ok), "valid_d_t": float(p.loc["valid", "d_t"]),
               "ex_best_day_pos": bool(p.loc["train", "d_ex_best_day"] > 0 and p.loc["valid", "d_ex_best_day"] > 0)}
    gate[k]["pass"] = bool(ok and gate[k]["valid_d_t"] >= 1.0 and gate[k]["ex_best_day_pos"])

# H2: random-drop control matched by setup and split (same number of trades dropped)
rng = np.random.default_rng(7)
ctrl = {}
for split in ("train", "valid"):
    bs = base[base.split == split]
    ds = dropped[dropped.split == split]
    actual = -ds["r_multiple"].sum()          # change in total R from dropping them
    sims = []
    for _ in range(2000):
        tot = 0.0
        for st, n in ds.groupby("strategy").size().items():
            pool = bs[bs.strategy == st]["r_multiple"].to_numpy()
            tot -= rng.choice(pool, size=min(n, len(pool)), replace=False).sum()
        sims.append(tot)
    sims = np.array(sims)
    ctrl[split] = {"n_dropped": len(ds), "dropped_by_setup": ds.groupby("strategy").size().to_dict(),
                   "dropped_mean_r": float(ds["r_multiple"].mean()) if len(ds) else None,
                   "delta_total": float(actual), "random_mean": float(sims.mean()),
                   "pct_random_below_actual": float((sims < actual).mean())}

# unresolved (time exits) per setup, all configs of interest
late = []
for k in ("base", "orb20a_until1030", "orb20a_until1100", "exh_end1400", "exh_end1430"):
    tr = alloc[k]
    for s in LIVE:
        for split in ("train", "valid"):
            x = tr[(tr.strategy == s) & (tr.split == split)]
            tm = x[x.exit_reason.str.endswith("time") | (x.exit_reason == "eod")]
            late.append({"config": k, "setup": s, "split": split, "n": len(x), "n_time_exit": len(tm),
                         "share": len(tm) / len(x) if len(x) else np.nan,
                         "mean_r_time_exit": tm["r_multiple"].mean() if len(tm) else np.nan,
                         "mean_r_resolved": x[~x.index.isin(tm.index)]["r_multiple"].mean() if len(x) > len(tm) else np.nan,
                         "exit_clock": ",".join(sorted({str(e)[11:16] for e in tm.exit_time}))})
late = pd.DataFrame(late)
late.to_csv(D + "late_holds.csv", index=False)

# H1 context: base heat_fade_short by entry time bucket
h = base[base.strategy == "heat_fade_short"].copy()
h["entry_hhmm"] = pd.to_datetime(h["entry_time"]).dt.strftime("%H:%M")
h["bucket"] = np.where(h["entry_hhmm"] < "10:01", "09:51-10:00", "10:01+")
h["mins_held"] = (pd.to_datetime(h.exit_time) - pd.to_datetime(h.entry_time)).dt.total_seconds() / 60
hb = h.groupby(["split", "bucket"]).agg(n=("r_multiple", "size"), exp=("r_multiple", "mean"),
                                         total=("r_multiple", "sum"), wr=("r_multiple", lambda r: (r > 0).mean()),
                                         stop_share=("exit_reason", lambda e: (e == "stop").mean()),
                                         med_mins=("mins_held", "median")).reset_index()
hb.to_csv(D + "hfs_buckets.csv", index=False)
rr_s = pd.Series([v for v in rr.values() if not np.isnan(v)])
json.dump({"gate": gate, "h2_control": ctrl,
           "hfs_range_ratio_quantiles": rr_s.quantile([.1, .25, .5, .75, .9]).round(3).to_dict()},
          open(D + "summary.json", "w"), indent=1, default=str)

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 200)
print(res.round(3).to_string())
print(json.dumps({"gate": gate, "h2_control": ctrl}, indent=1, default=str))
print(late.round(3).to_string()); print(hb.round(3).to_string())
print(rr_s.describe())
