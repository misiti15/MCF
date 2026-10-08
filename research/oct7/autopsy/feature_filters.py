"""Entry-time feature filters suggested by the autopsy (owner's short-term RSI layer; ORB 'already extended').
Train/valid only. Features come from the setup-lab 5-minute frame (research/setups2/data, sessions < 2026-09-16),
joined to each base trade's signal bar. $ P/L per trade from fix_trades.parquet (base variant).
Educational only - not financial advice."""
import pickle
import numpy as np
import pandas as pd

OUT = "research/oct7/autopsy/"
cols = ["symbol", "date", "tod", "rsi", "rsi5", "fromOpen", "vwapDistPct", "pricePosition", "gap"]
L = pd.concat([pd.read_parquet(f"research/setups2/data/{s}.parquet", columns=cols) for s in ("train", "valid")])
L["date"] = L["date"].astype(str)
L = L[L.date >= "2026-07-15"]
sigs = pickle.load(open("research/exits/data/signals.pkl", "rb"))["signals"]
tod = {}
SIDE = {(x['symbol'], x['date'], x['sig']['strategy']): x['sig']['side'] for x in sigs}
for s in sigs:
    if "2026-07-15" <= s["date"] <= "2026-09-15":
        m = 9 * 60 + 30 + s["sig"]["bar_index"] + 1
        tod[(s["symbol"], s["date"], s["sig"]["strategy"])] = (m // 60) * 100 + m % 60
R = pd.read_parquet(OUT + "fix_trades.parquet")
B = R[R.variant == "base"].copy()
B["tod"] = [tod.get((a, b, c)) for a, b, c in zip(B.symbol, B.date, B.setup)]
X = B.merge(L, on=["symbol", "date", "tod"], how="left")
print("feature match rate by setup:", X.groupby("setup").rsi.apply(lambda x: x.notna().mean()).round(3).to_dict())
X.to_parquet(OUT + "base_with_features.parquet")


def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 and x.std(ddof=1) > 0 else np.nan


rng = np.random.default_rng(11)
rows = []
side_sign = {"orb20_a": None}
tests = []
for th in (50, 60, 70, 80):
    tests.append(("heat_fade_short", f"keep rsi5>{th}", lambda d, th=th: d.rsi5 > th))
for th in (85, 90, 95):
    tests.append(("orb20_a", f"skip rsi14 beyond {th}/{100-th} in trade direction",
                  lambda d, th=th: ~(((d.rsi > th) & (d.dir == 1)) | ((d.rsi < 100 - th) & (d.dir == -1)))))
for th in (3, 5, 8):
    tests.append(("orb20_a", f"skip |fromOpen|>{th}%", lambda d, th=th: d.fromOpen.abs() <= th))
for setup, name, f in tests:
    for split in ("train", "valid"):
        s = X[(X.setup == setup) & (X.split == split)].copy()
        s["dir"] = [SIDE[(a, b, setup)] for a, b in zip(s.symbol, s.date)]   # side recovered from the signals
        m = f(s).fillna(True).to_numpy(bool)
        keep = s[m]
        db = s.groupby("date").pnl.sum()
        dk = keep.groupby("date").pnl.sum().reindex(db.index, fill_value=0.0)
        frac = m.mean()
        sims = np.array([s.pnl.to_numpy()[rng.random(len(s)) < frac].sum() for _ in range(2000)])
        rows.append(dict(setup=setup, filter=name, split=split, n=len(s), n_keep=int(m.sum()), base_usd=round(s.pnl.sum(), 1),
                         keep_usd=round(keep.pnl.sum(), 1), base_pt=round(s.pnl.mean(), 2), keep_pt=round(keep.pnl.mean(), 2),
                         drop_pt=round(s[~m].pnl.mean(), 2) if (~m).any() else None,
                         d_vs_random_t_day=round(tstat(dk - frac * db), 2), p_random_better=round(float((sims >= keep.pnl.sum()).mean()), 3),
                         ex_best=round(((dk - db).sum() - (dk - db).max()), 1)))
F = pd.DataFrame(rows)
F.to_csv(OUT + "feature_filters.csv", index=False)
print(F.to_string())

# ---- added after the classification: heat_fade_long 'falling knife' (big drop from the open) ----------------
rows2 = []
H = X[X.setup == "heat_fade_long"].copy()
print("\nheat_fade_long by fromOpen at entry (lab frame):")
print(H.groupby([pd.cut(H.fromOpen, [-100, -8, -6, -4, -3, -2, 0, 100]), "split"], observed=True).agg(
    n=("pnl", "size"), usd=("pnl", "mean"), win=("pnl", lambda x: (x > 0).mean()), days=("date", "nunique")).round(2).to_string())
for th in (3, 4, 5, 6):
    for split in ("train", "valid"):
        s = H[H.split == split]
        m = (s.fromOpen >= -th).to_numpy()
        keep = s[m]
        db = s.groupby("date").pnl.sum()
        dk = keep.groupby("date").pnl.sum().reindex(db.index, fill_value=0.0)
        frac = m.mean()
        sims = np.array([s.pnl.to_numpy()[rng.random(len(s)) < frac].sum() for _ in range(2000)])
        rows2.append(dict(setup="heat_fade_long", filter=f"skip fromOpen<-{th}%", split=split, n=len(s), n_keep=int(m.sum()),
                          base_usd=round(s.pnl.sum(), 1), keep_usd=round(keep.pnl.sum(), 1), base_pt=round(s.pnl.mean(), 2),
                          keep_pt=round(keep.pnl.mean(), 2), drop_pt=round(s[~m].pnl.mean(), 2) if (~m).any() else None,
                          d_vs_random_t_day=round(tstat(dk - frac * db), 2),
                          p_random_better=round(float((sims >= keep.pnl.sum()).mean()), 3),
                          ex_best=round(((dk - db).sum() - (dk - db).max()), 1)))
F2 = pd.DataFrame(rows2)
pd.concat([F, F2]).to_csv(OUT + "feature_filters.csv", index=False)
print(F2.to_string())
