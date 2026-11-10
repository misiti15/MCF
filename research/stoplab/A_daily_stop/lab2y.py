"""A6b sensitivity: grid-A latch levels on the 2-year lab trade lists (latch_1103 bt_lab1104, production costs,
account caps 3 lots/symbol + 30 open per setup as latch_1103). TRAIN <= 2025-12; VALID 2026-01..03 + 2026-07-01..09-15.
HOLD (2026-04..06, 2026-09-16 onward) is never loaded. Locked block 2024-11-01..2025-02-28 never read.
Educational only - not financial advice."""
import math, os, re, sys
from pathlib import Path
import numpy as np, pandas as pd
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
HERE = Path(__file__).resolve().parent
SRC = Path("/home/user/MCF/research/history2y/data/bt_lab1104")
LEVELS = [1.0, 1.25, 1.5, 1.6, 1.75, 1.8, 2.0, 2.01, 2.25, 2.5, 3.0, 4.0]
HOLD_MONTHS = {"2026-04", "2026-05", "2026-06", "2026-10", "2026-11"}
fr = []
for f in sorted(SRC.glob("sig_*.parquet")):
    m = f.stem[4:]
    if m in HOLD_MONTHS: continue
    if m == "2026-09":
        fr.append(pd.read_parquet(f, filters=[("date", "<=", "2026-09-15")]))
    else:
        fr.append(pd.read_parquet(f))
bt = pd.concat(fr, ignore_index=True); bt["date"] = bt.date.astype(str)
d_ = pd.to_datetime(bt.date)
assert not ((d_ >= "2024-11-01") & (d_ <= "2025-02-28")).any()
assert not (((d_ >= "2026-04-01") & (d_ <= "2026-06-30")) | (d_ >= "2026-09-16")).any()
bt = bt.sort_values(["setup", "date", "tod", "symbol"], kind="mergesort").reset_index(drop=True)
bt["split"] = np.where(bt.date <= "2025-12-31", "train", "valid")

def caps(sym, en, ex, per_sym=3, per_setup=30):
    keep = np.zeros(len(en), bool)
    for i in range(len(en)):
        o = keep[:i] & (ex[:i] > en[i])
        if o.sum() < per_setup and (o & (sym[:i] == sym[i])).sum() < per_sym:
            keep[i] = True
    return keep

rows = []; kept = []
for (su, d), g in bt.groupby(["setup", "date"], sort=False):
    k = caps(g.symbol.to_numpy(), g.tod.to_numpy(), g.xtod.to_numpy()); g = g[k]; kept.append(g)
    r = g.r.to_numpy(float); en = g.tod.to_numpy(); ex = g.xtod.to_numpy(); n = len(r)
    M = (ex[None, :] <= en[:, None]) & np.tri(n, k=-1, dtype=bool)
    real = M.astype(float) @ r            # realised R before entry i (all earlier trades taken until the latch)
    rec = dict(setup=su, date=d, split=g.split.iloc[0], n=n, R_off=r.sum())
    cs = np.concatenate([[0.0], np.cumsum(r)])
    for L in LEVELS:
        hit = np.flatnonzero(real <= -L + 1e-9)
        i0 = hit[0] if len(hit) else n
        rec[f"R_{L}"] = cs[i0]; rec[f"n_{L}"] = i0
    rows.append(rec)
SD = pd.DataFrame(rows); SD["n_off"] = SD.n
bt = pd.concat(kept, ignore_index=True)
mu = bt[bt.split == "train"].groupby("setup").r.mean()
SD.to_csv(HERE / "units_lab2y.csv.gz", index=False)

def t(x):
    x = np.asarray(x, float); return x.mean() / (x.std(ddof=1) / math.sqrt(len(x))) if len(x) > 1 and x.std() > 0 else np.nan
out = []
m = SD.setup.map(mu).fillna(0)
for nm in ["off"] + LEVELS:
    rec = dict(level=str(nm))
    for sp in ["train", "valid"]:
        V = SD[SD.split == sp]; mv = m[V.index]
        dd = (V[f"R_{nm}"] - V["R_2.0"]).groupby(V.date).sum()
        do = (V[f"R_{nm}"] - V["R_off"]).groupby(V.date).sum()
        exc = ((V[f"R_{nm}"] - V["R_2.0"]) - (V[f"n_{nm}"] - V["n_2.0"]) * mv).groupby(V.date).sum()
        ps = (V[f"R_{nm}"] - V["R_2.0"]).groupby(V.setup).sum()
        rec.update({f"{sp}_R": V[f"R_{nm}"].sum(), f"{sp}_d_vs_off": do.sum(), f"{sp}_d_vs_m2": dd.sum(), f"{sp}_t_vs_m2": t(dd),
                    f"{sp}_excess_vs_m2": exc.sum(), f"{sp}_excess_t": t(exc),
                    f"{sp}_setups_up": int((ps > 1e-9).sum()), f"{sp}_setups_down": int((ps < -1e-9).sum())})
    out.append(rec)
O = pd.DataFrame(out); O.to_csv(HERE / "A6_lab2y_levels.csv", index=False)
with open(HERE / "lab2y_out.txt", "w") as fh:
    s = (f"2-year lab: {len(bt)} trades after caps, {SD.setup.nunique()} setups, {len(SD)} setup-days; "
         f"train {int((SD.split=='train').sum())}, valid {int((SD.split=='valid').sum())} setup-days\n" +
         O.to_string(index=False, float_format=lambda v: f"{v:,.1f}"))
    print(s); fh.write(s + "\n")
