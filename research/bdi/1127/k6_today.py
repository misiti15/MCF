"""BDI 1127 Move Hunt context: the MOVEHUNT_1127 K6 09:50 big-mover ranker (research/movehunt_1127, FAIL as a setup;
direction ~ coin flip) applied to 11-27 (half day). Frozen K6 coefficients from results.json; features exactly as
score.py (gap, rvol, rng, mv, idio, pdr, dv, atrp; log1p except dv) but standardised on TODAY's cross-section (the FIT
mean / sd were not saved; a per-day z-score changes the scale of each feature, so the ranking is an approximation).
Eligible: universe names with ADV20 >= $60M (fetch floor; the study used >= $20M), price >= $5, ATR > 0, 20-session
09:30-09:49 volume median > 0. Target as the study: M = |C_last - P50| / ATR, C_last = the 12:59 close (half day),
top 2% = movers. Reports capture@20/50 vs base, the continuation direction hit rate, and the overlap with today's
Move Hunt catalogue (research/bdi/moves/moves.csv, 11-27 rows). Read-only. Usage: python k6_today.py <scratch> <day>.
Educational only - not financial advice."""
import json, pickle, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
S, D = Path(sys.argv[1]), sys.argv[2]; HERE = Path(__file__).resolve().parent; TZ = "America/New_York"
coef = json.loads((HERE.parents[1] / "movehunt_1127/results.json").read_text())["logit_coef"]
FEATS = ["gap", "rvol", "rng", "mv", "idio", "pdr", "dv", "atrp"]
B1 = pd.read_parquet(S / "cov/days" / D / "bars.parquet"); PRI = pickle.loads((S / "cov/days" / D / "priors.pkl").read_bytes())
B5 = pd.read_parquet(S / "mh" / D / "bars5.parquet"); B5 = B5[B5.index < pd.Timestamp(D, tz=TZ)]
B5 = B5[B5.index.strftime("%H%M") <= "0945"]
v20h = B5.groupby(["symbol", B5.index.date]).volume.sum()
v20med = v20h.groupby(level=0).apply(lambda s: s.tail(20).median())
hm = B1.index.strftime("%H%M")
w = B1[hm <= "0949"]; last = B1[hm <= "1259"]
g = w.groupby("symbol"); gl = last.groupby("symbol")
X = pd.DataFrame({"open": g.open.first(), "p50": g.close.last(), "h20": g.high.max(), "l20": g.low.min(), "v20": g.volume.sum(),
                  "c_last": gl.close.last()})
X["prev_close"] = X.index.map(lambda s: PRI[s].prev_close if s in PRI else np.nan)
X["atr"] = X.index.map(lambda s: PRI[s].atr if s in PRI else np.nan)
X["adv20"] = X.index.map(lambda s: PRI[s].adv if s in PRI else np.nan)
X["pdr_raw"] = X.index.map(lambda s: (PRI[s].prev_high - PRI[s].prev_low) if s in PRI else np.nan)
X["v20_med"] = v20med.reindex(X.index)
spy_r20 = X.loc["SPY", "p50"] / X.loc["SPY", "open"] - 1
X = X[(X.p50 >= 5) & (X.adv20 >= 60e6) & (X.atr > 0) & (X.v20_med > 0) & X.prev_close.notna()].copy()
X["atrp"] = X.atr / X.prev_close; X["gap_s"] = X.open / X.prev_close - 1; X["gap"] = X.gap_s.abs() / X.atrp
X["rvol"] = X.v20 / X.v20_med; X["rng"] = (X.h20 - X.l20) / X.atr; X["mv"] = (X.p50 - X.open).abs() / X.atr
X["r20"] = X.p50 / X.open - 1; X["idio"] = (X.r20 - spy_r20).abs() / X.atrp; X["pdr"] = X.pdr_raw / X.atr; X["dv"] = np.log(X.adv20)
Z = np.column_stack([np.log1p(X[f].clip(lower=0)) if f != "dv" else X[f] for f in FEATS]); Z = (Z - Z.mean(0)) / Z.std(0)
X["K6"] = Z @ np.array([coef[f] for f in FEATS])
X["M"] = (X.c_last - X.p50).abs() / X.atr; X["mdir"] = np.sign(X.c_last - X.p50); X["D"] = np.sign(X.p50 - X.open)
ntop = max(1, round(0.02 * len(X))); X["mover"] = X.M.rank(ascending=False, method="first") <= ntop
X = X.sort_values("K6", ascending=False); X["k6rank"] = np.arange(1, len(X) + 1)
print(f"{D}: eligible {len(X)}, movers (top 2% by M to the 12:59 close) {ntop}")
for N in (20, 50, 100):
    cap = X.head(N).mover.sum() / ntop; base = N / len(X)
    print(f"capture@{N}: {X.head(N).mover.sum()}/{ntop} = {cap:.1%} vs base {base:.1%} (lift {cap / base:.1f}x)")
top = X.head(20)
print(f"direction (continuation D = sign(P50 - open) vs sign(C_last - P50)) on the top-20 list: {(top.D == top.mdir).mean():.0%} "
      f"(n 20); on movers inside the top 50: {(X.head(50)[X.head(50).mover].D == X.head(50)[X.head(50).mover].mdir).mean():.0%}")
mc = pd.read_csv(HERE.parent / "moves" / "moves.csv"); mc = mc[(mc.date == D) & (mc.set == "all")]
ins = mc.symbol.isin(X.head(50).index)
print(f"Move Hunt catalogue (top 25 / side, 30-90 min moves): {ins.sum()}/{len(mc)} names were in K6's 09:50 top 50 "
      f"(long {ins[mc.side == 'long'].sum()}, short {ins[mc.side == 'short'].sum()}); caught by a live setup among them: "
      f"{(ins & mc.n_right.gt(0)).sum()}")
pd.set_option("display.width", 200)
print("\nK6 top 20 at 09:50:")
print(top[["k6rank", "K6", "gap_s", "rvol", "rng", "mv", "D", "M", "mdir", "mover"]].round(3).to_string())
print("\nmovers and their K6 rank:")
print(X[X.mover].sort_values("M", ascending=False)[["k6rank", "M", "mdir", "D", "gap_s", "rvol"]].round(3).to_string())
print("Educational only - not financial advice.")
