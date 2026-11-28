"""Loss levers replayed on live lots (journal R after LR8 costs), with size-matched random controls.
Each lever = a rule that SKIPS some lots (no re-fill of freed slots is modelled). Controls:
  W  = within the same setup-day, skip the same number of lots at random positions (does WHICH lot matter?)
  U  = across the whole book, skip the same total number of lots at random (does concentrating on blow-up days matter?)
Usage: python levers.py <scratch>. Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from common import dayt
S = sys.argv[1]; rng = np.random.default_rng(7)
f = pd.read_parquet(f"{S}/feat.parquet")
f = f.sort_values(["account", "date", "strategy", "entry_et"]).reset_index(drop=True)
g = f.groupby(["account", "date", "strategy"])
f["sd_lot"] = g.cumcount() + 1
# open lots of the same setup at entry
op = np.zeros(len(f), int)
for _, idx in g.indices.items():
    e = f.entry_et.values[idx]; x = f.exit_et.values[idx]
    for j, i in enumerate(idx):
        op[i] = ((e[:j] < e[j]) & (x[:j] > e[j])).sum()
f["sd_open"] = op
# closed setup R at entry (for a -2R latch on closed R)
cl = np.zeros(len(f))
for _, idx in g.indices.items():
    e = f.entry_et.values[idx]; x = f.exit_et.values[idx]; r = f.r.values[idx]
    for j in range(len(idx)):
        m = x < e[j]; cl[idx[j]] = r[m].sum()
f["sd_closed"] = cl
f.to_parquet(f"{S}/feat2.parquet")

def metrics(x, keep):
    d = x.assign(rk=np.where(keep, x.r, 0.0)).groupby(["account", "date"]).rk.sum() if False else None
    return None

def book_eval(x, keep):
    day = x.assign(rk=np.where(keep, x.r, 0.0)).groupby("date").rk.sum()
    return day

def report(name, x, keep, ndraw=200):
    base = x.groupby("date").r.sum(); new = book_eval(x, keep); skip = ~keep
    nskip = int(skip.sum()); saved = new.sum() - base.sum(); wk = len(base) / 5
    green = base > 0
    out = {"lever": name, "skipped": nskip, "skip%": 100 * nskip / len(x), "saved_R": saved, "saved_R/wk": saved / wk,
           "on_green_days": (new - base)[green].sum(), "on_red_days": (new - base)[~green].sum(),
           "worst5_base": base.nsmallest(5).sum(), "worst5_new": new.nsmallest(5).sum(),
           "red_base": int((base <= 0).sum()), "red_new": int((new <= 0).sum()), "days": len(base),
           "dt_saved": dayt(new - base), "best_day_share": (new - base).max() / saved if saved > 0 else np.nan}
    # per-setup effect
    ps = x.assign(d=np.where(keep, 0.0, -x.r)).groupby("strategy").d.sum()
    ps = ps[ps != 0]; out["setups_better"] = int((ps > 0).sum()); out["setups_worse"] = int((ps < 0).sum())
    out["worse_sum"] = ps[ps < 0].sum()
    # controls
    if nskip:
        cnt = x.assign(s=skip).groupby(["account", "date", "strategy"]).s.sum()
        gi = x.groupby(["account", "date", "strategy"]).indices
        wv, uv = [], []
        r = x.r.values
        for _ in range(ndraw):
            m = np.ones(len(x), bool)
            for k, n in cnt[cnt > 0].items():
                m[rng.choice(gi[k], int(n), replace=False)] = False
            wv.append(r[m].sum() - r.sum())
            m2 = np.ones(len(x), bool); m2[rng.choice(len(x), nskip, replace=False)] = False
            uv.append(r[m2].sum() - r.sum())
        wv, uv = np.array(wv), np.array(uv)
        out["ctrl_W_mean"] = wv.mean(); out["pct_vs_W"] = 100 * (wv < saved).mean()
        out["ctrl_U_mean"] = uv.mean(); out["pct_vs_U"] = 100 * (uv < saved).mean()
        # tail control: worst-5 under U
    return out

rows = []
for book in ["primary", "arena"]:
    x = f[f.book == book].reset_index(drop=True)
    for K in [3, 5, 8, 10, 15]:
        rows.append({"book": book, **report(f"FIRSTK{K}: max {K} lots per setup-day", x, (x.sd_lot <= K).values)})
    for K in [2, 3, 5, 8]:
        rows.append({"book": book, **report(f"OPENK{K}: max {K} open lots per setup", x, (x.sd_open < K).values)})
    for L in [-2, -3, -5]:
        rows.append({"book": book, **report(f"LATCH{L}: no new lot once setup closed R <= {L}", x, (x.sd_closed > L).values)})
    for K in [5, 10]:
        rows.append({"book": book, **report(f"LATCH-2+OPENK{K}", x, ((x.sd_closed > -2) & (x.sd_open < K)).values)})
    rows.append({"book": book, **report("SPRD6: skip stop < 6 spreads", x, ~(x.stop_spreads < 6).values)})
r = pd.DataFrame(rows)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
print(r.round(2).to_string(index=False))
r.to_csv(f"{S}/levers.csv", index=False)
