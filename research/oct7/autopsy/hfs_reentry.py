"""heat_fade_short: one re-entry after a stop-out, at the next 5-minute bar close (<= 10:30) where the live
regime_9 rule still qualifies (CHTR 10-07: stopped 09:53, score 39 at 09:55, then fell 4R). Train/valid only.
Outcome = the setup-lab 5-minute 1R/1R short outcome (r_short_t1s1, costs in) from that bar's close: a SCREEN,
coarser than the 1-minute engine. 1 configuration (+1 variant: re-entry only if the score is stronger than at
the first entry). Educational only - not financial advice."""
import pickle
import numpy as np
import pandas as pd

OUT = "research/oct7/autopsy/"
cols = ["symbol", "date", "tod", "rsiHeat", "priceActionHeat", "momentumHeat", "vwapHeat", "fromOpen", "atr_d", "r_short_t1s1"]
L = pd.concat([pd.read_parquet(f"research/setups2/data/{s}.parquet", columns=cols) for s in ("train", "valid")])
L["date"] = L["date"].astype(str)
L = L[(L.date >= "2026-07-15") & (L.tod >= 950) & (L.tod <= 1030)]
L["score"] = -(L.rsiHeat + L.priceActionHeat - L.momentumHeat - L.vwapHeat) - 8 * 8.0 / L.atr_d
L["ok"] = (L.score >= 11.3) & (L.fromOpen < 0)
R = pd.read_parquet(OUT + "fix_trades.parquet")
B = R[(R.variant == "base") & (R.setup == "heat_fade_short")].copy()
sigs = pickle.load(open("research/exits/data/signals.pkl", "rb"))["signals"]
score0 = {(s["symbol"], s["date"]): s["sig"]["meta"].get("heat_score") for s in sigs if s["sig"]["strategy"] == "heat_fade_short"}
import sys
sys.path.insert(0, ".")
from dataclasses import fields
from mcf.backtest.engine import Costs, simulate
from mcf.config import load_config
from mcf.data.store import BarStore
from mcf.strategies.base import Signal, t
cfg = load_config()
store, costs, FLAT = BarStore(cfg["data"]["cache_dir"]), Costs.from_cfg(cfg["costs"]), t(cfg["session"]["flatten_by"])
FIELDS = {f.name for f in fields(Signal)}
Lk = {k: g.sort_values("tod") for k, g in L.groupby(["symbol", "date"])}
rows = []
hs = [s for s in sigs if s["sig"]["strategy"] == "heat_fade_short" and "2026-07-15" <= s["date"] <= "2026-09-15"]
for sym in sorted({s["symbol"] for s in hs}):
    df = store.load(sym, end="2026-09-16")
    days = {str(d): g for d, g in df.groupby(df.index.date)}
    for s in [x for x in hs if x["symbol"] == sym]:
        bars = days.get(s["date"])
        if bars is None:
            continue
        tr = simulate(Signal(**{k: v for k, v in s["sig"].items() if k in FIELDS}), bars, FLAT, costs)
        if tr is None:
            continue
        row = dict(symbol=sym, date=s["date"], r1=tr.r_multiple, reason=tr.exit_reason, re_r=np.nan, re_tod=None)
        if tr.exit_reason == "stop":
            et = tr.exit_time.hour * 100 + tr.exit_time.minute
            g = Lk.get((sym, s["date"]))
            if g is not None:
                # first qualifying 5-minute bar that CLOSES after the stop-out minute (bar close tod > exit minute)
                c = g[(g.tod > et) & g.ok]
                if len(c):
                    row.update(re_r=float(c.r_short_t1s1.iloc[0]), re_tod=int(c.tod.iloc[0]),
                               re_score=float(c.score.iloc[0]), first_score=-float(score0.get((sym, s["date"])) or np.nan))
        rows.append(row)
D = pd.DataFrame(rows)
D["split"] = np.where(D.date <= "2026-08-25", "train", "valid")
D.to_csv(OUT + "hfs_reentry.csv", index=False)


def tday(x, by):
    d = x.groupby(by).sum()
    return round(float(d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))), 2) if len(d) > 2 else np.nan


for name, m in (("reentry_any", D.re_r.notna()), ("reentry_stronger", D.re_r.notna() & (D.re_score > D.first_score))):
    for sp in ("train", "valid"):
        x = D[(D.split == sp) & m]
        print(name, sp, "stops", int(((D.split == sp) & (D.reason == "stop")).sum()), "re-entries", len(x), "days", x.date.nunique(),
              "mean R", round(x.re_r.mean(), 3), "win", round((x.re_r > 0).mean(), 3), "t_day", tday(x.re_r, x.date),
              "ex-best-day total R", round(x.re_r.sum() - x.groupby("date").re_r.sum().max(), 2), "total R", round(x.re_r.sum(), 2))
