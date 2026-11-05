"""QR2 (QDAY setup, BDI 2026-11-04; pre-registered after QR1's descriptive table and BEFORE reading any trade list):
QR1 showed the quiet-close share falls from ~40% (SPY 09:30-10:00 range / 20-session mean daily range in the lower
three quintiles) to 20-24% (top two) - a wide opening half hour flags trend days. QR2 turns that into a two-sided
counter-index setup for range days:
  universe   the 2-year lab trade lists of every enabled lab setup (research/bdi/1104/bt_all.py), entries >= 10:05
  counter    short with spy_fo >= +0.25% at the entry bar, or long with spy_fo <= -0.25% (the swing1103-L6 definition)
  gate       or_ratio (QR1) < the TRAIN top-tercile cut 0.425  ("narrow open" -> range day more likely)
  PASS       gated counter entries: avg R after costs > 0 AND excess over the setup's own mean >= +0.05R in TRAIN and
             VALID, day-clustered t >= bar, n >= 1000, avg R > 0 on BOTH SPY up and down days (QDAY b), avg R w/o the
             best day > 0. Control (reported, not a pass): counter entries on wide-open days (or_ratio >= 0.425).
1 config. Usage: python qr2.py <scratch> <N_tonight>      Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib
from mcf.research.gates import t_required
S = Path(sys.argv[1]); BAR = t_required(int(sys.argv[2])); HERE = Path(__file__).resolve().parent
LK0, LK1 = "2024-11-01", "2025-02-28"; SPLIT = "2025-09-01"; CUT = 0.425; TZ = "America/New_York"
b = pd.read_parquet(ROOT / "data/cache_hist/1Min/SPY.parquet"); b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
d = b.index.strftime("%Y-%m-%d"); b = b[~((d >= LK0) & (d <= LK1))]; d = b.index.strftime("%Y-%m-%d"); m = b.index.hour * 60 + b.index.minute
k = (m >= 570) & (m < 960); b, d, m = b[k], d[k], m[k]
g = b.groupby(d); D = pd.DataFrame({"o": g.open.first(), "c": g.close.last(), "rng": g.high.max() - g.low.min(), "n": g.size()})
e = b[m < 600].groupby(d[m < 600]); D["or_hl"] = e.high.max() - e.low.min(); D = D[D.n >= 300]
D["or_ratio"] = D.or_hl / D.rng.shift(1).rolling(20, min_periods=15).mean(); D["oc"] = (D.c / D.o - 1) * 100
T = pd.concat([pd.read_parquet(p) for p in sorted((S / "bt").glob("sig_*.parquet"))], ignore_index=True); T["date"] = T.date.astype(str)
assert not T.date.between(LK0, LK1).any()
ctx = pd.concat([lib.load_context(mm) for mm in lib.months()], ignore_index=True); ctx["date"] = ctx.date.astype(str)
T = T.merge(ctx[["date", "tod", "spy_fo"]], on=["date", "tod"], how="left")
T["split"] = np.where(T.date < SPLIT, "train", "valid"); T["ex"] = T.r - T.groupby(["setup", "split"]).r.transform("mean")
T = T.join(D[["or_ratio", "oc"]], on="date"); T = T[(T.tod >= 1005) & T.or_ratio.notna()]
T["dtype"] = np.where(T.oc > 0.25, "up", np.where(T.oc < -0.25, "down", "quiet"))
T["counter"] = ((T.side == -1) & (T.spy_fo >= 0.25)) | ((T.side == 1) & (T.spy_fo <= -0.25))
def ctt(x, col):
    gg = x.groupby("date")[col].agg(["sum", "size"]); mu = gg["sum"].sum() / gg["size"].sum(); G = len(gg)
    v = ((gg["sum"] - mu * gg["size"]) ** 2).sum() / gg["size"].sum() ** 2 * G / max(G - 1, 1); return mu, mu / np.sqrt(v), G
P = []
def pr(*a): P.append(" ".join(str(x) for x in a)); print(P[-1], flush=True)
pr(f"trades >= 10:05 with SPY or_ratio: {len(T)} on {T.date.nunique()} sessions; counter {int(T.counter.sum())}; bar t {BAR:.2f}")
res = {}
for name, x in (("GATED narrow open (or_ratio < 0.425)", T[T.counter & (T.or_ratio < CUT)]), ("control wide open (>= 0.425)", T[T.counter & (T.or_ratio >= CUT)]),
                ("all counter", T[T.counter])):
    mu, t, G = ctt(x, "r"); mx, tx, _ = ctt(x, "ex"); dr = x.groupby("date").r.sum(); wob = (dr.sum() - dr.max()) / max(len(x) - (x.date == dr.idxmax()).sum(), 1)
    sp = {s: (x[x.split == s].r.mean(), x[x.split == s].ex.mean(), int((x.split == s).sum())) for s in ("train", "valid")}
    dt = {k_: (len(v), v.r.mean()) for k_, v in x.groupby("dtype")}
    pr(f"\n{name}: n {len(x)} on {G} days ({len(x) / max(G, 1):.1f}/day); avg R {mu:+.3f} (t {t:+.2f}); excess {mx:+.3f} (t {tx:+.2f}); w/o best day {wob:+.3f}R, best-day share {dr.max() / dr.sum() if dr.sum() > 0 else float('nan'):.2f}")
    pr(f"   train avg {sp['train'][0]:+.3f} ex {sp['train'][1]:+.3f} (n {sp['train'][2]}) | valid avg {sp['valid'][0]:+.3f} ex {sp['valid'][1]:+.3f} (n {sp['valid'][2]})")
    pr("   by SPY day type: " + "; ".join(f"{k_} n {n} {r:+.3f}R" for k_, (n, r) in dt.items()) + " | by side: " +
       "; ".join(f"{'long' if s == 1 else 'short'} n {len(v)} {v.r.mean():+.3f}" for s, v in x.groupby("side")))
    res[name] = dict(mu=mu, t=t, ex=mx, wob=wob, sp=sp, dt=dt, n=len(x))
r = res["GATED narrow open (or_ratio < 0.425)"]
ok = bool(r["mu"] > 0 and all(r["sp"][s][1] >= 0.05 and r["sp"][s][0] > 0 for s in ("train", "valid")) and r["t"] >= BAR and r["n"] >= 1000
          and r["dt"].get("up", (0, -1))[1] > 0 and r["dt"].get("down", (0, -1))[1] > 0 and r["wob"] > 0)
pr(f"\nQR2 PASS {ok}"); pr("Educational only - not financial advice."); (HERE / "qr2_out.txt").write_text("\n".join(P) + "\n")
