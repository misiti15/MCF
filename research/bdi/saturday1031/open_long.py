"""saturday1031 D: two new LONG ideas for the 09:35-09:50 window (Move Hunt lineage). PLAN.md section D was written
before this ran. Harness = research/bdi/1030/mh3_open_pdh.py (same data, costs, blackout, h-exit logic), with:
  data    research/bdi/timeofday/data/open (09:35..10:30 5-min rows; the locked block was dropped at build time and is
          asserted absent) + history2y daily (PDL). adv20 >= $95M, earnings blackout removed. Old holdouts 2026-04..06 and
          >= 2026-09-16 dropped before scoring.
  D1  opening capitulation reversal, volume-confirmed: gap <= -1%, prior row RSI5 <= 20, close > prior close,
      buyPressure > 0, volumeRatio >= V, close <= PDL + 0.25 ATR_d.   V in {1.5, 3}
  D2  gap-and-go opening drive: gap >= +1%, from-open move >= +0.25 ATR_d, close above VWAP, volumeRatio >= V,
      SPY fromOpen > 0 at the same bar.                                V in {1.5, 3}
  first qualifying bar per symbol-day among the 09:40 / 09:45 / 09:50 closes.
  exits   t1s1 (frame outcome, prod_r with ToD entry costs); h1030w: stop 0.5 ATR_d on each later row, else the 10:30
          close, R = 0.5 ATR_d, costs 1c + 1 bps per side (entry x ToD multiplier), +2c on stops.
  N = 12 (mh-1030) + 8 = 20 -> full bar sqrt(2 ln 20) = 2.45, BAR90 2.20. Split train <= 2025-08-31.
  Baseline: the first 09:40 row of every eligible symbol-day, same exit.
Usage: python open_long.py > open_long_out.txt   Educational only - not financial advice."""
import glob, json, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT))
from mcf.research import gates as G
from mcf.research.generator import data as GD

COLS = ["symbol", "date", "tod", "close", "high", "low", "atr_d", "gap", "fromOpen", "vwapDistPct", "rsi5", "volumeRatio",
        "buyPressure", "adv20", "r_long_t1s1", "win_long_t1s1"]
F = pd.concat([pd.read_parquet(f, columns=COLS) for f in sorted(glob.glob(str(ROOT / "research/bdi/timeofday/data/open/*.parquet")))])
F["date"] = pd.to_datetime(F["date"]).dt.date
assert not ((F.date >= pd.Timestamp("2024-11-01").date()) & (F.date <= pd.Timestamp("2025-02-28").date())).any()
ds = F.date.astype(str)
F = F[~(ds.between("2026-04-01", "2026-06-30") | (ds >= "2026-09-16"))]
spy = F[F.symbol == "SPY"].set_index(["date", "tod"]).fromOpen
F = F[F.adv20 >= 95e6]
D = pd.read_parquet(ROOT / "research/history2y/data/daily.parquet", columns=["symbol", "date", "open", "high", "low", "close"])
D["date"] = pd.to_datetime(D["date"]).dt.date
D = D.sort_values(["symbol", "date"]); D["pdl"] = D.groupby("symbol").low.shift(1)
F = F.merge(D[["symbol", "date", "pdl"]], on=["symbol", "date"], how="left")
F = F[~GD._blackout(F.symbol.to_numpy(), F.date.to_numpy())]
F = F.sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
REG = G.session_regimes(D[["date", "open", "close"]])
SPLIT = pd.Timestamp("2025-08-31").date()
key = F.symbol.astype(str) + "|" + F.date.astype(str)
grp = {k: v for k, v in F.groupby(key).indices.items()}
hi, lo, cl, tod = F.high.to_numpy(), F.low.to_numpy(), F.close.to_numpy(), F.tod.to_numpy()
same = (key == key.shift(1)).to_numpy()
prev_r5 = np.where(same, F.rsi5.shift(1).to_numpy(), np.nan); prev_c = np.where(same, F.close.shift(1).to_numpy(), np.nan)
spyfo = pd.Series(list(zip(F.date, F.tod))).map(spy).to_numpy(float)


def hexit(i, R):
    rows = grp[key.iat[i]]; rows = rows[tod[rows] > tod[i]]
    e = cl[i]; stop = e - R
    for j in rows:
        if lo[j] <= stop:
            return -1.0, True
    if not len(rows):
        return np.nan, False
    return (cl[rows[-1]] - e) / R, False


def trades(mask, exitk):
    idx = G.first_per_symbol_day(F.symbol.to_numpy(), F.date.to_numpy(), mask & (F.atr_d > 0).to_numpy())
    if exitk == "t1s1":
        r = G.prod_r(F.r_long_t1s1.to_numpy()[idx], F.win_long_t1s1.to_numpy()[idx], cl[idx], F.atr_d.to_numpy()[idx], "t1s1", tod=tod[idx])
    else:
        R = 0.5 * F.atr_d.to_numpy()[idx]; r = np.empty(len(idx)); mult = G.tod_cost_mult(tod[idx])
        for n, i in enumerate(idx):
            g, stopped = hexit(i, R[n])
            c = (G.SLIP_PS + cl[i] * G.SLIP_BPS) * (mult[n] + 1) + (G.STOP_EXTRA if stopped else 0)
            r[n] = g - c / R[n]
    t = pd.DataFrame({"date": F.date.to_numpy()[idx], "symbol": F.symbol.to_numpy()[idx], "tod": tod[idx], "r": r})
    return t[np.isfinite(t.r)]


def wf_share(t):
    m = t.groupby(pd.to_datetime(t.date).dt.to_period("M")).r.mean()
    return round(float((m > 0).mean()), 3), len(m)


win = F.tod.isin([940, 945, 950]).to_numpy()
atr, gap, fo, vw, vr, bp = (F[c].to_numpy(float) for c in ("atr_d", "gap", "fromOpen", "vwapDistPct", "volumeRatio", "buyPressure"))
with np.errstate(invalid="ignore", divide="ignore"):
    fo_atr = (fo / 100) * cl / (1 + fo / 100) / atr
    D1 = lambda V: win & (gap <= -1) & (prev_r5 <= 20) & (cl > prev_c) & (bp > 0) & (vr >= V) & (cl <= F.pdl.to_numpy() + 0.25 * atr)
    D2 = lambda V: win & (gap >= 1) & (fo_atr >= 0.25) & (vw > 0) & (vr >= V) & (spyfo > 0)
N = 20; tfull = G.t_required(N); t90 = round(max(1.35, 0.9 * tfull), 2)
print(f"rows {len(F)} (adv20 >= 95M, blackout and old holdouts removed), symbol-days {key.nunique()}; N {N}: full bar {tfull}, BAR90 {t90}")
out = []
for exitk in ("t1s1", "h1030w"):
    base = trades((F.tod == 940).to_numpy(), exitk); bs = G.summary(base)
    print(f"baseline 09:40 long {exitk}: n {bs['n']} exp {bs.get('exp_r')} t {bs.get('t')}")
    for nm, fn in (("D1-open-capitulation-reversal-long", D1), ("D2-open-gap-and-go-long", D2)):
        for V in (1.5, 3.0):
            t = trades(fn(V), exitk); s = G.summary(t); rg = G.regime_split(t, REG)
            tr, va = G.summary(t[t.date <= SPLIT]), G.summary(t[t.date > SPLIT])
            wf, nmo = wf_share(t)
            day = t.groupby("date").r.agg(["sum", "size"]); b = day["sum"].idxmax() if len(day) else None
            row = dict(config=f"{nm}-v{V:g}-{exitk}", n=s["n"], per_session=round(s["n"] / max(1, F.date.nunique()), 2),
                       win=s.get("win_rate"), exp_r=s.get("exp_r"), t=s.get("t"),
                       wo_best_day=round((day["sum"].sum() - day.loc[b, "sum"]) / max(1, day["size"].sum() - day.loc[b, "size"]), 4) if b is not None else np.nan,
                       best_share=round(day.loc[b, "sum"] / day["sum"].sum(), 3) if b is not None and day["sum"].sum() > 0 else np.nan,
                       train=tr.get("exp_r"), train_t=tr.get("t"), valid=va.get("exp_r"), valid_t=va.get("t"),
                       up=rg["up"].get("exp_r"), flat=rg["flat"].get("exp_r"), down=rg["down"].get("exp_r"), regime_pass=rg["pass"],
                       wf_pos=wf, months=nmo, base_exp=bs.get("exp_r"), excess=round(s.get("exp_r", np.nan) - bs.get("exp_r", np.nan), 4))
            row["bar90_pass"] = bool((row["t"] or -9) >= t90 and wf >= 0.54 and rg["pass"] and row["excess"] > 0
                                     and (row["train"] or -1) > 0 and (row["valid"] or -1) > 0)
            out.append(row)
O = pd.DataFrame(out)
pd.set_option("display.width", 250)
print(O.to_string(index=False))
O.to_csv(Path(__file__).with_name("open_long.csv"), index=False)
print(json.dumps({"configs": 8, "pass_bar90": int(O.bar90_pass.sum()), "best_t": float(O.t.max())}))
print("Educational only - not financial advice.")
