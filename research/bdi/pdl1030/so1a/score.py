"""so1a scoring: R2A (S3 + cost5, SPY prior range/ATR > cut long else short) with half-off / none / first 2 by signal /
first 2 by trigger. Stats as regime-day/score.py. TRAIN+VALID only. Educational only - not financial advice."""
import sys, math, json
from pathlib import Path
import numpy as np, pandas as pd
C = Path(sys.argv[1])
T = pd.concat([pd.read_parquet(p) for p in sorted(C.glob("tr_*.parquet"))], ignore_index=True)
d = T["date"].astype(str); T["date"] = d
assert (d <= "2026-09-15").all()
assert not ((d >= "2024-11-01") & (d <= "2025-02-28")).any() and not d.str[:7].isin(["2026-04", "2026-05", "2026-06", "2026-10"]).any()
T["month"] = d.str[:7]; T["split"] = np.where(d <= "2025-12-31", "train", "valid")
NSESS = T["date"].nunique()
CUT = 0.7956493496894836
N0, COUNT = 121705, 4; N = N0 + COUNT
BAR = max(1.35, 0.9 * max(1.5, math.sqrt(2 * math.log(N))))
X = T[T["cost_rt_R"] <= 0.05].copy()
X = X[(X["prng"] > CUT) | (X["prng"] < CUT)].reset_index(drop=True)
lg = (X["prng"] > CUT).to_numpy()
X["side"] = np.where(lg, "long", "short")
X["r_SO"] = np.where(lg, X["rL_SO"], X["rS_SO"]); X["r_NO"] = np.where(lg, X["rL_NO"], X["rS_NO"])
X["stod"] = np.where(lg, X["stodL"], X["stodS"]); X["scaled"] = X["stod"] >= 0
# consistency: scale_hit mirror vs sim (r differs iff scaled, up to exact ties)
mis = ((X["r_SO"] != X["r_NO"]) != X["scaled"]).mean()
X = X.sort_values(["date", "tod", "symbol"]).reset_index(drop=True)
rk_sig = X.groupby("date").cumcount()
X["first2_sig"] = rk_sig < 2
Y = X[X["scaled"]].sort_values(["date", "stod", "tod", "symbol"])
rk_trg = Y.groupby("date").cumcount()
X["first2_trg"] = False; X.loc[Y.index[rk_trg.to_numpy() < 2], "first2_trg"] = True
CFG = {"SO1A-1 research (half-off on every trade)": X["r_SO"].to_numpy(),
       "SO1A-2 no half-off (plain bracket)": X["r_NO"].to_numpy(),
       "SO1A-3 half-off on first 2 per session by signal time": np.where(X["first2_sig"], X["r_SO"], X["r_NO"]),
       "SO1A-4 half-off on first 2 per session to reach +0.25 R1 (live cap rule)": np.where(X["first2_trg"], X["r_SO"], X["r_NO"])}
assert len(CFG) == COUNT


def tday(dates, r):
    mu = r.mean(); g = pd.Series(r - mu).groupby(dates).sum(); se = np.sqrt((g ** 2).sum()) / len(r)
    return mu, mu / se


def stats(r):
    out = {}
    for sp in ("train", "valid", "tv"):
        m = np.ones(len(X), bool) if sp == "tv" else (X["split"] == sp).to_numpy()
        mu, t = tday(X["date"].to_numpy()[m], r[m]); out[f"avg_{sp}"] = round(mu, 4); out[f"t_{sp}"] = round(t, 2)
    day = pd.Series(r).groupby(X["date"].to_numpy()).agg(["sum", "count"]); b = day["sum"].idxmax()
    out["ex_best"] = round((day["sum"].sum() - day.loc[b, "sum"]) / (day["count"].sum() - day.loc[b, "count"]), 4)
    out["best_share"] = round(day.loc[b, "sum"] / day["sum"].sum(), 3) if day["sum"].sum() > 0 else None
    out["best_day"] = b
    mo = pd.Series(r).groupby(X["month"].to_numpy()).sum(); out["wf_pct"] = round((mo > 0).mean() * 100, 1)
    out["win_pct"] = round((r > 0).mean() * 100, 1)
    out["avg_win"] = round(r[r > 0].mean(), 3); out["avg_loss"] = round(r[r <= 0].mean(), 3)
    for sp in ("train", "valid"):
        m = (X["split"] == sp).to_numpy(); out[f"win_{sp}"] = round((r[m] > 0).mean() * 100, 1)
    out["n"] = len(r); out["per_session"] = round(len(r) / NSESS, 1)
    out["passes_bar"] = bool(out["t_tv"] >= BAR)
    return out


rows = [dict(id=k, **stats(v)) for k, v in CFG.items()]
R = pd.DataFrame(rows)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(f"sessions {NSESS} N {N} BAR {BAR:.3f} trades {len(X)} mirror-mismatch {mis:.4%}")
print(R.to_string(index=False))
# edge from half-off
so, no = R.iloc[0], R.iloc[1]
for sp in ("train", "valid", "tv"):
    print(f"half-off lift {sp}: {so[f'avg_{sp}'] - no[f'avg_{sp}']:+.4f} R/trade")
# half-off demand per session
dem = X.groupby("date")["scaled"].sum().reindex(sorted(T["date"].unique()), fill_value=0)
print("scaled share of trades %.1f%%" % (X["scaled"].mean() * 100))
print("scale-outs wanted per session: median %.0f mean %.1f p90 %.0f max %d; sessions >2: %.1f%%" % (dem.median(), dem.mean(), dem.quantile(0.9), dem.max(), (dem > 2).mean() * 100))
sec = X[X["scaled"]].sort_values(["date", "stod"]).groupby("date")["stod"].apply(lambda s: s.iloc[1] if len(s) > 1 else np.nan)
print("tod when the 2nd slot is used: median %s p10 %s p90 %s" % tuple(sec.quantile([0.5, 0.1, 0.9]).round().astype(int)))
print("trades/session: median %.0f p90 %.0f" % tuple(X.groupby("date").size().quantile([0.5, 0.9])))
# per-trade lift of half-off when scaled: what the 2 capped trades are worth vs all
dl = X["r_SO"] - X["r_NO"]
print("half-off lift on scaled trades: mean %+.3f R; first2_trg %+.3f; others %+.3f" % (dl[X.scaled].mean(), dl[X.first2_trg].mean(), dl[X.scaled & ~X.first2_trg].mean()))
print("side split (n, avg SO, avg NO):"); print(X.groupby("side").agg(n=("r_SO", "size"), so=("r_SO", "mean"), no=("r_NO", "mean")).round(4))
code = np.where(lg[X.index] if False else (X["side"] == "long"), X["codeL"], X["codeS"])
print("exit codes (half-off run):", pd.Series(code).value_counts().sort_index().to_dict())
R.to_csv(sys.argv[2], index=False)
json.dump(dict(N=N, BAR=round(BAR, 3), sessions=NSESS, demand=dict(median=float(dem.median()), p90=float(dem.quantile(0.9)), mean=float(dem.mean()), gt2_pct=float((dem > 2).mean() * 100))), open(Path(sys.argv[2]).with_suffix(".json"), "w"), indent=1)
