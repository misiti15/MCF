"""EODREV1 (backlog wi-eod-reversal, BDI 2026-11-18 idea 3, COVERAGE): ONE pre-registered 2-year test, configs = 1.
Mechanism: end-of-day reversal of intraday losers (short covering / liquidity provision into the close), the same
mechanism as swing1118-L15 but as an entry. Rule fixed before the run (also in research/bdi/1118/NOTES.md):
  Universe: lab symbols with point-in-time adv20 >= $95M and price >= $5 (frames at 15:00); not SPY/QQQ/IWM.
  Signal: fromOpen at the 15:30 5-min close <= -2.0% (open = c1500 / (1 + fromOpen1500/100)). Long at the 15:30 close.
  R unit = 0.25 x atr_d. Stop = entry - 1R: hit if any 5-min low 15:35..15:55 <= stop, filled at stop - 2c.
  Otherwise exit at the 15:55 close. Costs 1c + 1 bp per side. Every qualifying symbol-day (one entry each).
  Baseline (beats-random check): same entry / exit on every universe name that day (no fromOpen condition).
Bar (Testing bar, RESEARCH_RULES 22; N = 1): avg R > 0; day-clustered t >= 1.35; > 0 in TRAIN and VALID; > 0 in SPY up
AND down sessions; beats the baseline by >= +0.05R; avg R w/o best day > 0 (best-day share reported).
COVERAGE read (reported): avg R and day sums on SPY up / quiet / down sessions (SPY open->close +-0.25%).
Data: research/history2y/data frames (lib.load_month) + research/bdi/cwt/test_b/data/headtail.parquet + daily.parquet.
Locked block 2024-11-01..2025-02-28 never read (lib.months() excludes it; asserted).
Usage: python eodrev_bt.py -> eodrev_bt_out.txt next to this file.  Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402
HT = ROOT / "research/bdi/cwt/test_b/data/headtail.parquet"; LK = ("2024-11-01", "2025-02-28"); HERE = Path(__file__).resolve().parent
THR, BAR = -2.0, 1.35
rows = []
for m in lib.months():
    assert m not in lib.LOCKED_MONTHS
    f = lib.load_month(m, columns=["symbol", "date", "tod", "close", "fromOpen", "atr_d", "adv20"])
    f = f[f.tod == 1500].copy(); f["symbol"] = f.symbol.astype(str); f["date"] = f.date.astype(str)
    f = f[(f.adv20 >= 95e6) & (f.close >= 5) & (f.atr_d > 0) & ~f.symbol.isin(["SPY", "QQQ", "IWM"])]
    f["open"] = f.close / (1 + f.fromOpen / 100)
    a = pd.Timestamp(m + "-01")
    h = pd.read_parquet(HT, columns=["symbol", "date", "tod", "l", "c"],
                        filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1)), ("tod", ">=", 1530)])
    h["symbol"] = h.symbol.astype(str); h["date"] = pd.to_datetime(h.date).dt.date.astype(str)
    e = h[h.tod == 1530][["symbol", "date", "c"]].rename(columns={"c": "entry"})
    x = h[h.tod == 1555][["symbol", "date", "c"]].rename(columns={"c": "x1555"})
    lo = h[h.tod > 1530].groupby(["symbol", "date"]).l.min().rename("lo").reset_index()
    t = f[["symbol", "date", "open", "atr_d"]].merge(e, on=["symbol", "date"]).merge(x, on=["symbol", "date"]).merge(lo, on=["symbol", "date"])
    rows.append(t); del f, h
    print(m, len(t), flush=True)
T = pd.concat(rows, ignore_index=True); assert not T.date.between(*LK).any()
T["Ru"] = 0.25 * T.atr_d; T["stop"] = T.entry - T.Ru; T["fo"] = (T.entry / T.open - 1) * 100
T["px"] = np.where(T.lo <= T.stop, T.stop - 0.02, T.x1555)
T["r"] = (T.px - T.entry) / T.Ru - (0.02 + (T.entry + T.px) * 1e-4) / T.Ru
D = pd.read_parquet(ROOT / "research/history2y/data/daily.parquet", columns=["symbol", "date", "open", "close"])
D["date"] = pd.to_datetime(D.date).dt.date.astype(str); s = D[D.symbol == "SPY"].set_index("date"); oc = (s.close / s.open - 1) * 100
T["dt"] = T.date.map(lambda d: "up" if oc.get(d, 0) > 0.25 else ("down" if oc.get(d, 0) < -0.25 else "quiet"))
T["split"] = np.where(T.date <= "2025-12-31", "TRAIN", np.where(T.date <= "2026-10-05", "VALID", "LATE"))
S = T[T.fo <= THR]
out = []
def p(*a): out.append(" ".join(str(x) for x in a)); print(out[-1], flush=True)
tt = lambda x: x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 2 and x.std() > 0 else np.nan
dd = S.groupby("date").r.sum(); dm = S.groupby("date").r.mean(); best = dd.idxmax(); share = dd.max() / dd.sum() if dd.sum() > 0 else np.nan
p(f"EODREV1 end-of-day reversal long | configs 1 | Testing bar t {BAR} | universe name-days {len(T)} on {T.date.nunique()} sessions")
p(f"SIGNAL (fromOpen <= {THR}% at 15:30): n {len(S)} on {S.date.nunique()} days, avg {S.r.mean():+.4f}R, win {100*(S.r>0).mean():.0f}%, "
  f"stopped {100*(S.lo<=S.stop).mean():.0f}%, day-t (daily mean) {tt(dm):.2f}, total {S.r.sum():+.1f}R")
p(f"  w/o best day ({best}, share {share:.0%}): avg {S[S.date!=best].r.mean():+.4f}R")
p(f"BASELINE (all universe names, same entry/exit): n {len(T)}, avg {T.r.mean():+.4f}R | signal - baseline {S.r.mean()-T.r.mean():+.4f}R")
for sp in ("TRAIN", "VALID", "LATE"):
    x = S[S.split == sp]; p(f"  {sp}: n {len(x)} days {x.date.nunique()} avg {x.r.mean():+.4f}R day-t {tt(x.groupby('date').r.mean()):.2f}")
for k in ("up", "quiet", "down"):
    x = S[S.dt == k]; b = T[T.dt == k]
    p(f"  SPY {k} sessions: n {len(x)} on {x.date.nunique()} days avg {x.r.mean():+.4f}R (baseline {b.r.mean():+.4f}), "
      f"sum/day {x.groupby('date').r.sum().mean():+.2f}R")
for lo_, hi_ in ((-99, -6), (-6, -4), (-4, -3), (-3, -2)):
    x = S[(S.fo > lo_) & (S.fo <= hi_)]; p(f"  fromOpen ({lo_},{hi_}]: n {len(x)} avg {x.r.mean():+.4f}R")
ok = (S.r.mean() > 0 and tt(dm) >= BAR and S[S.split == "TRAIN"].r.mean() > 0 and S[S.split == "VALID"].r.mean() > 0
      and S[S.dt == "up"].r.mean() > 0 and S[S.dt == "down"].r.mean() > 0 and S.r.mean() - T.r.mean() >= 0.05
      and S[S.date != best].r.mean() > 0)
p(f"PASS {bool(ok)}"); p("Educational only - not financial advice.")
(HERE / "eodrev_bt_out.txt").write_text("\n".join(out) + "\n")
