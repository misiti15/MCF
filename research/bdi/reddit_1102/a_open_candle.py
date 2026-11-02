"""reddit_1102 A: opening-candle range expansion, traded in the candle's direction (r/Daytrading 1xle3nm). PLAN.md section
A was written before this ran. Harness = research/bdi/saturday1031/open_long.py (same opening frame, blackout, old
holdouts dropped, regimes, WF), with a structural stop (opposite extreme of the 09:30-09:35 candle) and a 10:30 exit.
Usage: python a_open_candle.py > a_out.txt   Educational only - not financial advice."""
import glob, json, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT))
from mcf.research import gates as G
from mcf.research.generator import data as GD

COLS = ["symbol", "date", "tod", "close", "high", "low", "atr_d", "fromOpen", "adv20"]
F = pd.concat([pd.read_parquet(f, columns=COLS) for f in sorted(glob.glob(str(ROOT / "research/bdi/timeofday/data/open/*.parquet")))])
F["date"] = pd.to_datetime(F["date"]).dt.date
assert not ((F.date >= pd.Timestamp("2024-11-01").date()) & (F.date <= pd.Timestamp("2025-02-28").date())).any()
F = F.sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
# first-candle stats per symbol-day (point-in-time trailing median uses prior sessions only; computed before any drop)
O = F[F.tod == 935].copy()
O["open"] = O.close / (1 + O.fromOpen / 100)
O["rng"] = O.high - O.low
O["med20"] = O.groupby("symbol").rng.transform(lambda s: s.shift(1).rolling(20, min_periods=10).median())
O["rr"] = O.rng / O.med20
# later rows for the exit
L = F[F.tod > 935]
lmin = L.groupby(["symbol", "date"]).low.min(); lmax = L.groupby(["symbol", "date"]).high.max()
last = L[L.tod == 1030].set_index(["symbol", "date"]).close
k2 = pd.MultiIndex.from_arrays([O.symbol, O.date])
O["lmin"], O["lmax"], O["c1030"] = lmin.reindex(k2).to_numpy(), lmax.reindex(k2).to_numpy(), last.reindex(k2).to_numpy()
ds = O.date.astype(str)
O = O[~(ds.between("2026-04-01", "2026-06-30") | (ds >= "2026-09-16"))]
O = O[~GD._blackout(O.symbol.to_numpy(), O.date.to_numpy())]
O = O[np.isfinite(O.c1030) & np.isfinite(O.rr)].reset_index(drop=True)
D = pd.read_parquet(ROOT / "research/history2y/data/daily.parquet", columns=["symbol", "date", "open", "close"])
D["date"] = pd.to_datetime(D["date"]).dt.date
D = D[~((D.date >= pd.Timestamp("2024-11-01").date()) & (D.date <= pd.Timestamp("2025-02-28").date()))]
REG = G.session_regimes(D[["date", "open", "close"]])
SPLIT = pd.Timestamp("2025-08-31").date()
MULT = 3.8


def sim(X, side, stop):
    e = X.close.to_numpy(float); stop = np.asarray(stop, float)
    if side == "long":
        R = e - stop; hit = X.lmin.to_numpy(float) <= stop; g = np.where(hit, -1.0, (X.c1030.to_numpy(float) - e) / R)
    else:
        R = stop - e; hit = X.lmax.to_numpy(float) >= stop; g = np.where(hit, -1.0, (e - X.c1030.to_numpy(float)) / R)
    c = (G.SLIP_PS + e * G.SLIP_BPS) * MULT + (G.SLIP_PS + e * G.SLIP_BPS) + np.where(hit, G.STOP_EXTRA, 0.0)
    r = g - c / R
    ok = R >= 0.0005 * e
    return pd.DataFrame({"date": X.date.to_numpy(), "symbol": X.symbol.to_numpy(), "r": r, "R": R, "Rpct": R / e * 100})[ok]


def wf_share(t):
    m = t.groupby(pd.to_datetime(t.date).dt.to_period("M")).r.mean()
    return round(float((m > 0).mean()), 3), len(m)


N = 20; tfull = G.t_required(N); t90 = round(max(1.35, 0.9 * tfull), 2)
print(f"first-candle symbol-days {len(O)} (blackout + old holdouts removed); N {N}: full bar {tfull}, BAR90 {t90}")
out = []
for uni in ("stocks", "QQQ"):
    U = O[O.adv20 >= 95e6] if uni == "stocks" else O[O.symbol == "QQQ"]
    for side in ("long", "short"):
        bstop = U.close - U.rng - 0.01 if side == "long" else U.close + U.rng + 0.01
        base = sim(U, side, bstop); bday = base.groupby("date").r.mean()
        bs = G.summary(base)
        print(f"{uni} {side} baseline (every symbol-day, 09:35, stop one candle range away): n {bs['n']} exp {bs['exp_r']} t {bs['t']}")
        for k in (1.5, 2.0, 3.0):
            X = U[(U.rr >= k) & ((U.close > U.open) if side == "long" else (U.close < U.open))]
            t = sim(X, side, X.low - 0.01 if side == "long" else X.high + 0.01)
            s = G.summary(t)
            if not s["n"]:
                continue
            rg = G.regime_split(t, REG); tr, va = G.summary(t[t.date <= SPLIT]), G.summary(t[t.date > SPLIT])
            wf, nmo = wf_share(t)
            exc = t.r.to_numpy() - t.date.map(bday).to_numpy(float)
            te = pd.DataFrame({"date": t.date, "r": exc}); se_ = G.summary(te)
            day = t.groupby("date").r.agg(["sum", "size"]); b = day["sum"].idxmax()
            row = dict(config=f"A-opencandle-{uni}-{side}-k{k:g}", n=s["n"], per_session=round(s["n"] / O.date.nunique(), 2),
                       win=s["win_rate"], exp_r=s["exp_r"], t=s["t"], wo_best_day=s["ex_best_day"],
                       best_share=round(day.loc[b, "sum"] / day["sum"].sum(), 3) if day["sum"].sum() > 0 else np.nan,
                       train=tr.get("exp_r"), valid=va.get("exp_r"), up=rg["up"].get("exp_r"), down=rg["down"].get("exp_r"),
                       regime_pass=rg["pass"], wf_pos=wf, months=nmo, base_exp=bs["exp_r"], excess=se_["exp_r"], excess_t=se_["t"],
                       med_R_pct=round(float(t.Rpct.median()), 3))
            row["bar90_pass"] = bool((row["t"] or -9) >= t90 and wf >= 0.54 and rg["pass"] and (row["excess"] or -1) > 0
                                     and (row["train"] or -1) > 0 and (row["valid"] or -1) > 0)
            out.append(row)
R_ = pd.DataFrame(out)
pd.set_option("display.width", 260)
print(R_.to_string(index=False))
R_.to_csv(Path(__file__).with_name("a_results.csv"), index=False)
print(json.dumps({"configs": len(R_), "pass_bar90": int(R_.bar90_pass.sum()), "best_t": float(R_.t.max())}))
print("Educational only - not financial advice.")
