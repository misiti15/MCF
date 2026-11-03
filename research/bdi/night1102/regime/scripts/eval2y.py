"""night1102/regime step 6: two-year (open history, TRAIN to 2025-12-31, VALID 2026-01-01..10-05) regime map of the
covered live setups and the same switches as switch_live.py on the two-year signals (scan2y.py). Costs in (production
R). Day-clustered statistics. Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
SCR = Path(sys.argv[1])
OUT = Path(__file__).resolve().parents[1]
D = pd.read_parquet(SCR / "days2y.parquet")
S = pd.concat([pd.read_parquet(p) for p in sorted((SCR / "sig2y").glob("*.parquet"))], ignore_index=True)
S["date"] = pd.to_datetime(S["date"]).dt.date
S = S[S.date.isin(set(D.index))].dropna(subset=["R"])
S["split"] = np.where(S.date <= pd.Timestamp("2025-12-31").date(), "train", "valid")
S["eod3"] = S.date.map(D.eod3)
print("signals", len(S), "setups", S.setup.nunique(), "sessions", S.date.nunique())


def cl(r, d):
    n = len(r)
    if n == 0:
        return np.nan, np.nan, 0
    m = r.mean()
    g = pd.DataFrame({"r": r.to_numpy(), "d": d.to_numpy()}).groupby("d")["r"].agg(["sum", "size"])
    se = np.sqrt(((g["sum"] - m * g["size"]) ** 2).sum()) / n if len(g) > 1 else np.nan
    return m, (m / se if se and se > 0 else np.nan), n


# ---- per-setup map
rows = []
for s, t in S.groupby("setup"):
    r = {"setup": s, "side": "long" if t.side.iloc[0] > 0 else "short"}
    for sp in ("train", "valid"):
        x = t[t.split == sp]
        m, tt, n = cl(x.R, x.date)
        r[f"{sp}_n"], r[f"{sp}_avg"], r[f"{sp}_t"] = n, m, tt
        for L in ("up", "down", "quiet"):
            y = x[x.eod3 == L]
            r[f"{sp}_{L}"] = y.R.mean() if len(y) >= 30 else np.nan
    r["robust_2y"] = all((r.get(f"{sp}_{L}", np.nan) or -1) > 0 for sp in ("train", "valid") for L in ("up", "down", "quiet"))
    rows.append(r)
M = pd.DataFrame(rows).sort_values("valid_avg", ascending=False)
M.round(4).to_csv(OUT / "map_2y.csv", index=False)
pd.set_option("display.width", 300)
print(M.round(3).to_string(index=False))
print("robust in up/down/quiet in BOTH train and valid:", M.robust_2y.sum(), M[M.robust_2y].setup.tolist())

# ---- switches (same definitions as switch_live.py; SPY states only)
ST = {}
for t in (950, 1000, 1030):
    ST[f"vwap@{t}"] = pd.Series(np.where(D[f"vw_SPY@{t}"] >= 0, "up", "down"), index=D.index)
    ST[f"fo@{t}"] = pd.Series(np.where(D[f"fo_SPY@{t}"] >= 0, "up", "down"), index=D.index)
    ST[f"fo25@{t}"] = pd.Series(np.where(D[f"fo_SPY@{t}"] >= 0.25, "up", np.where(D[f"fo_SPY@{t}"] <= -0.25, "down", "flat")), index=D.index)
for t in (950, 1030):
    ST[f"rng@{t}"] = pd.Series(np.where(D[f"rngr@{t}"] >= (0.3 if t == 950 else 0.5), "active", "calm"), index=D.index)
from switch_rules import RULES  # noqa: E402
PRIMARY = ["L3-gap-slope-fromopen-FD", "L3-gap-slope-rsi5hi-FD", "MF2-open-rsimidhi-flowsell-FD", "MF4-h40-open-flowsell",
           "MF4-h40-open-flowsell-FD", "NS1-rsidip-rsi5pop-long", "NS5-sma50-flush-oversold-long",
           "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "ST7-rsi50dn-long-pm-t1s1-FD"]
CORE = ["MF2-open-rsimidhi-flowsell-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
        "L3-gap-slope-fromopen-FD", "L3-gap-slope-rsi5hi-FD", "MF4-h40-open-flowsell-FD", "RW1-gapdn-bounce-flowsell-short-FD"]
BOOKS = {"all": S, "primary": S[S.setup.isin(PRIMARY)], "longs": S[S.side > 0], "shorts": S[S.side < 0],
         "core7": S[S.setup.isin(CORE)]}


def score(t, keep):
    out = {}
    for sp in ("train", "valid"):
        x, k = t[t.split == sp], keep[(t.split == sp).to_numpy()]
        share = k.mean()
        dk = x[k].groupby("date").R.sum().reindex(sorted(x.date.unique()), fill_value=0)
        dt = x.groupby("date").R.sum()
        diff = dk - dt * share
        se = diff.std(ddof=1) / np.sqrt(len(diff))
        out.update({f"{sp}_kept_pct": 100 * share, f"{sp}_avg": x.R.mean(), f"{sp}_kept_avg": x[k].R.mean(),
                    f"{sp}_vs_random": diff.sum(), f"{sp}_vs_random_t": diff.mean() / se if se > 0 else np.nan})
        for L in ("up", "down", "quiet"):
            out[f"{sp}_kept_{L}"] = x[k & (x.eod3 == L).to_numpy()].R.mean()
    return out


rows = []
for sname, s in ST.items():
    tcut = int(sname.split("@")[1])
    for rname, f in RULES.items():
        if ("rng" in sname) != ("calm" in rname):
            continue
        if "fo25" not in sname and rname == "follow":
            continue
        for bname, t in BOOKS.items():
            st = t.date.map(s).to_numpy()
            keep = np.array([(e < tcut) or f(sd, x) for e, sd, x in zip(t.tod.to_numpy(), t.side.to_numpy(), st)])
            rows.append({"state": sname, "rule": rname, "book": bname, **score(t, keep)})
R = pd.DataFrame(rows)
R.round(4).to_csv(OUT / "switch_2y.csv", index=False)
print("2y switch configs", len(R))
pre = [("fo@1000", "fade"), ("rng@950", "skip_shorts_calm"), ("vwap@950", "fade")]
for st_, ru in pre:
    print(f"\n== pre-declared {st_} {ru}")
    print(R[(R.state == st_) & (R.rule == ru)].round(3).T.to_string())
for b in BOOKS:
    print(f"\n== top 6 on 2y by valid vs_random, {b} (descriptive only)")
    x = R[R.book == b].sort_values("valid_vs_random", ascending=False).head(6)
    print(x[["state", "rule", "train_kept_pct", "train_avg", "train_kept_avg", "train_vs_random_t", "valid_kept_pct",
             "valid_avg", "valid_kept_avg", "valid_vs_random_t"]].round(3).to_string(index=False))
