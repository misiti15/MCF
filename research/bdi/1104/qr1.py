"""QR1 (QDAY focus, BDI 2026-11-04): an ex-ante quiet-day predictor at 10:00 from SPY's own opening half hour.
QD1 (research/bdi/1103) found 'quiet so far' barely predicts a quiet close (37% vs 33% base) and set the bar for any
re-test: a predictor must beat the base rate of quiet closes by >= 15 points. Pre-registered 2026-11-04 before reading:

  quiet close   SPY open-to-close |ret| <= 0.25% (the QDAY day-type definition)
  features at 10:00 (09:30-09:59 1-minute SIP bars, known at the 10:00 decision):
    or_ratio    SPY 09:30-10:00 high-low range / mean SPY daily high-low range of the prior 20 sessions
    fo10        SPY % from its open at the 09:59 close
  configs (3): P1 = or_ratio in the bottom tercile (cut from TRAIN days) and |fo10| <= 0.25%
               P2 = or_ratio in the top tercile and |fo10| <= 0.25%
               P3 = |fo10| <= 0.10% and the prior session was quiet (|o-c| <= 0.25%)
  PASS stage 1: P(quiet | flag) >= base + 15 points in TRAIN (< 2025-09-01) AND VALID (>= 2025-09-01), flag on >= 10% of
               days in each. Stage 2 (counter-index lab entries after 10:00 on flagged days) runs only for a passing config.
Data: data/cache_hist/1Min/SPY.parquet (research/bdi/1104/DATA.md); the locked block 2024-11-01..2025-02-28 is filtered
out at read and never used (no rolling window spans it: the 20-session mean skips its days).
Usage: python qr1.py    Educational only - not financial advice."""
from pathlib import Path
import numpy as np, pandas as pd
TZ = "America/New_York"; LK0, LK1 = "2024-11-01", "2025-02-28"; SPLIT = "2025-09-01"
b = pd.read_parquet("/home/user/MCF/data/cache_hist/1Min/SPY.parquet")
b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
d = b.index.normalize().tz_localize(None).strftime("%Y-%m-%d")
b = b[~((d >= LK0) & (d <= LK1))]; d = b.index.normalize().tz_localize(None).strftime("%Y-%m-%d")
m = b.index.hour * 60 + b.index.minute
b = b[(m >= 570) & (m < 960)]; d = d[(m >= 570) & (m < 960)]; m = m[(m >= 570) & (m < 960)]
g = b.groupby(d)
D = pd.DataFrame({"o": g.open.first(), "c": g.close.last(), "h": g.high.max(), "l": g.low.min(), "n": g.size()})
D = D[(D.n >= 300) & (D.index >= "2024-10-01")]
early = b[m < 600]; ge = early.groupby(d[m < 600])
D["or_hl"] = ge.high.max() - ge.low.min(); D["c959"] = ge.close.last()
D["oc"] = (D.c / D.o - 1) * 100; D["fo10"] = (D.c959 / D.o - 1) * 100
D["rng"] = D.h - D.l
D["rng20"] = D.rng.shift(1).rolling(20, min_periods=15).mean()          # prior sessions only (locked days are absent)
D["or_ratio"] = D.or_hl / D.rng20
D["quiet"] = D.oc.abs() <= 0.25; D["prevq"] = D.quiet.shift(1).fillna(False).astype(bool)
D = D.dropna(subset=["or_ratio"]); D["split"] = np.where(D.index < SPLIT, "train", "valid")
lo, hi = D.loc[D.split == "train", "or_ratio"].quantile([1 / 3, 2 / 3])
C = {"P1 low OR & |fo10|<=0.25": (D.or_ratio <= lo) & (D.fo10.abs() <= 0.25),
     "P2 high OR & |fo10|<=0.25": (D.or_ratio >= hi) & (D.fo10.abs() <= 0.25),
     "P3 |fo10|<=0.10 & prior quiet": (D.fo10.abs() <= 0.10) & D.prevq}
print(f"sessions {len(D)} ({D.index.min()}..{D.index.max()}; locked block absent), train {int((D.split == 'train').sum())} / valid {int((D.split == 'valid').sum())}; "
      f"or_ratio terciles (train) {lo:.3f} / {hi:.3f}")
for s in ("train", "valid"):
    x = D[D.split == s]; print(f"  base rate {s}: quiet {x.quiet.mean():.1%} (up {(x.oc > 0.25).mean():.1%}, down {(x.oc < -0.25).mean():.1%})")
res = []
for k, f in C.items():
    row = {"config": k}
    for s in ("train", "valid"):
        x = D[D.split == s]; fx = f[D.split == s]
        row[f"{s}_flag_share"] = fx.mean(); row[f"{s}_quiet_if_flag"] = x.quiet[fx].mean(); row[f"{s}_base"] = x.quiet.mean()
        row[f"{s}_lift_pts"] = (x.quiet[fx].mean() - x.quiet.mean()) * 100; row[f"{s}_n"] = int(fx.sum())
        row[f"{s}_up_if_flag"] = (x.oc[fx] > 0.25).mean(); row[f"{s}_down_if_flag"] = (x.oc[fx] < -0.25).mean()
    row["PASS"] = bool(all(row[f"{s}_lift_pts"] >= 15 and row[f"{s}_flag_share"] >= 0.10 for s in ("train", "valid")))
    res.append(row)
R = pd.DataFrame(res)
print(R.round(3).to_string(index=False))
# descriptive (no test): quiet-close rate by or_ratio decile, all open days
D["dec"] = pd.qcut(D.or_ratio, 5, labels=False)
print("\nquiet-close share by or_ratio quintile (all open days, descriptive):",
      D.groupby("dec").agg(n=("quiet", "size"), quiet=("quiet", "mean"), absoc=("oc", lambda v: v.abs().mean())).round(3).to_dict("index"))
t = D.loc["2026-11-04"] if "2026-11-04" in D.index else None
if t is not None:
    print(f"\n2026-11-04: or_ratio {t.or_ratio:.2f}, fo10 {t.fo10:+.2f}%, close {t.oc:+.2f}% -> flags " +
          ", ".join(k.split()[0] for k, f in C.items() if bool(f.get("2026-11-04", False))))
R.to_csv(Path(__file__).with_name("qr1_results.csv"), index=False)
print("Educational only - not financial advice.")
