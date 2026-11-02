"""MH3 (BDI 2026-10-30, Move Hunt): opening pop into the prior-day high, faded (short); mirror: opening flush into the
prior-day low, bought (long).

Why: on 10-30, 33 of the 50 biggest tradable moves started at the 09:35-09:45 decision bars and live caught 0 of them.
Among the 25 biggest short moves, 10+ were names up from the open with RSI5 >= 70 sitting within ~0.3 daily ATR of the
prior-day high (WSM, MTN, GAP, QLYS, M, ULTA, KSS, NOC, BUG, DOV). Today's one-day precision (decision rows, hindsight
labels): >= 0.5 ATR down within 90 min on 51% of k=0.30 short signals vs a 34% base rate; the long mirror 5% vs 7%.

Pre-declared (written before any two-year row was scored):
  data    research/bdi/timeofday/data/open (lab-pipeline 5-minute rows 09:35..10:30 from the 1-minute SIP cache; the
          locked block 2024-11-01..2025-02-28 was dropped at build time and is never read) + research/history2y daily
          table (prior-day high / low). adv20 >= $95M, earnings blackout (+-4 trading days) removed.
  signal  first of the 09:35 / 09:40 / 09:45 bar closes per symbol-day where
          short: |close - PDH| <= k x ATR_d, fromOpen > 0, RSI5 >= 70
          long:  |close - PDL| <= k x ATR_d, fromOpen < 0, RSI5 <= 30
  k       0.15, 0.30
  exits   t1s1   lab target / stop 0.25 x ATR_d (frame outcome, exit by 15:55), production costs with tod entry costs
          h1030  stop 0.25 x ATR_d checked on each later 5-minute bar's high / low, else exit at the 10:30 close;
                 costs 1c + 1 bps per side (entry side x tod multiplier), +2c on stops
  configs 2 sides x 2 k x 2 exits = 8, plus (added after the first 8 were scored, declared before scoring them) the
          index-gated variant MH3G: k = 0.30, both exits, and SPY fromOpen at the same bar close <= -0.10% (short) /
          >= +0.10% (long) - known at the decision bar. N = 12. Split: train <= 2025-09-30, valid after. Random baseline: first 09:35 bar of
          every eligible symbol-day, same side and exit. Bars: full max(1.5, sqrt(2 ln N)), BAR90 = 0.9 x that.
Usage: python research/bdi/1030/mh3_open_pdh.py > research/bdi/1030/mh3_out.txt
Educational only - not financial advice."""
import glob, json, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT))
from mcf.research import gates as G
from mcf.research.generator import data as GD

COLS = ["symbol", "date", "tod", "close", "high", "low", "atr_d", "fromOpen", "rsi5", "adv20",
        "r_long_t1s1", "win_long_t1s1", "r_short_t1s1", "win_short_t1s1"]
F = pd.concat([pd.read_parquet(f, columns=COLS) for f in sorted(glob.glob(str(ROOT / "research/bdi/timeofday/data/open/*.parquet")))])
F["date"] = pd.to_datetime(F["date"]).dt.date
assert not ((F.date >= pd.Timestamp("2024-11-01").date()) & (F.date <= pd.Timestamp("2025-02-28").date())).any()
F = F[F.adv20 >= 95e6]
D = pd.read_parquet(ROOT / "research/history2y/data/daily.parquet", columns=["symbol", "date", "open", "high", "low", "close"])
D["date"] = pd.to_datetime(D["date"]).dt.date
D = D.sort_values(["symbol", "date"])
D["pdh"] = D.groupby("symbol").high.shift(1); D["pdl"] = D.groupby("symbol").low.shift(1)
F = F.merge(D[["symbol", "date", "pdh", "pdl"]], on=["symbol", "date"], how="left")
F = F[~GD._blackout(F.symbol.to_numpy(), F.date.to_numpy())]
F = F.sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
REG = G.session_regimes(D[["date", "open", "close"]])
SPLIT = pd.Timestamp("2025-09-30").date()

# ---------------------------------------------------------------- h1030 exit: path on later rows of the same symbol-day
key = F.symbol.astype(str) + "|" + F.date.astype(str)
grp = {k: v for k, v in F.groupby(key).indices.items()}
hi, lo, cl, tod = F.high.to_numpy(), F.low.to_numpy(), F.close.to_numpy(), F.tod.to_numpy()


def h1030(i, sgn, R):
    rows = grp[key.iat[i]]; rows = rows[tod[rows] > tod[i]]
    e = cl[i]; stop = e - sgn * R
    for j in rows:
        if (sgn > 0 and lo[j] <= stop) or (sgn < 0 and hi[j] >= stop):
            return -1.0, True
    if not len(rows):
        return np.nan, False
    return sgn * (cl[rows[-1]] - e) / R, False


def trades(mask, side, exitk):
    idx = G.first_per_symbol_day(F.symbol.to_numpy(), F.date.to_numpy(), mask & (F.atr_d > 0).to_numpy())
    sgn = 1 if side == "long" else -1
    if exitk == "t1s1":
        r = G.prod_r(F[f"r_{side}_t1s1"].to_numpy()[idx], F[f"win_{side}_t1s1"].to_numpy()[idx], cl[idx],
                     F.atr_d.to_numpy()[idx], "t1s1", tod=tod[idx])
    else:
        R = 0.25 * F.atr_d.to_numpy()[idx]; r = np.empty(len(idx))
        mult = G.tod_cost_mult(tod[idx])
        for n, i in enumerate(idx):
            g, stopped = h1030(i, sgn, R[n])
            c = (G.SLIP_PS + cl[i] * G.SLIP_BPS) * (mult[n] + 1) + (G.STOP_EXTRA if stopped else 0)
            r[n] = g - c / R[n]
    t = pd.DataFrame({"date": F.date.to_numpy()[idx], "symbol": F.symbol.to_numpy()[idx], "tod": tod[idx], "r": r})
    return t[np.isfinite(t.r)]


def wf_share(t):
    m = t.groupby(pd.to_datetime(t.date).dt.to_period("M")).r.mean()
    return round(float((m > 0).mean()), 3), len(m)


early = F.tod.isin([935, 940, 945]).to_numpy()
pdh_d = ((F.close - F.pdh).abs() / F.atr_d).to_numpy(); pdl_d = ((F.close - F.pdl).abs() / F.atr_d).to_numpy()
fo, r5 = F.fromOpen.to_numpy(), F.rsi5.to_numpy()
spy = F[F.symbol == "SPY"].set_index(["date", "tod"]).fromOpen
spyfo = pd.Series(list(zip(F.date, F.tod))).map(spy).to_numpy(float)
N = 12; tfull = G.t_required(N); t90 = round(max(1.35, 0.9 * tfull), 2)
print(f"rows {len(F)} (adv20 >= 95M, blackout removed, 09:35..10:30), symbol-days {key.nunique()}; N = {N}: full bar {tfull}, BAR90 {t90}")
out = []
for side in ("short", "long"):
    for exitk in ("t1s1", "h1030"):
        base = trades((F.tod == 935).to_numpy(), side, exitk)
        bs = G.summary(base)
        for k, gate in ((0.15, False), (0.30, False), (0.30, True)):
            m = early & ((pdh_d <= k) & (fo > 0) & (r5 >= 70) if side == "short" else (pdl_d <= k) & (fo < 0) & (r5 <= 30))
            if gate:
                m = m & ((spyfo <= -0.10) if side == "short" else (spyfo >= 0.10))
            t = trades(m, side, exitk); s = G.summary(t); rg = G.regime_split(t, REG)
            tr, va = G.summary(t[t.date <= SPLIT]), G.summary(t[t.date > SPLIT])
            wf, nm = wf_share(t)
            name = f"MH3{'G' if gate else ''}-open-{'pdh-pop-fade-short' if side == 'short' else 'pdl-flush-buy-long'}-k{int(k * 100):02d}-{exitk}"
            row = dict(config=name, n=s["n"], days=s.get("days"), win=s.get("win_rate"), exp_r=s.get("exp_r"), t=s.get("t"),
                       ex_best_day=s.get("ex_best_day"), train=tr.get("exp_r"), train_t=tr.get("t"), valid=va.get("exp_r"),
                       valid_t=va.get("t"), up=rg["up"].get("exp_r"), flat=rg["flat"].get("exp_r"), down=rg["down"].get("exp_r"),
                       regime_pass=rg["pass"], wf_pos=wf, months=nm, base_exp=bs.get("exp_r"),
                       excess=round(s.get("exp_r", np.nan) - bs.get("exp_r", np.nan), 4))
            row["bar90_pass"] = bool((row["t"] or -9) >= t90 and wf >= 0.54 and rg["pass"] and row["excess"] > 0)
            out.append(row)
O = pd.DataFrame(out)
pd.set_option("display.width", 250)
print(O.to_string(index=False))
O.to_csv(Path(__file__).with_name("mh3_results.csv"), index=False)
print(json.dumps({"configs": N, "pass_bar90": int(O.bar90_pass.sum()), "best_t": float(O.t.max())}))
print("Educational only - not financial advice.")
