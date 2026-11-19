"""GUD1 (backlog mech-1119-gud1-gapup-gapdn-reclaim-long) - ONE pre-registered 2-year screen (BDI 2026-11-19; card written
before this run; configs 1). Engine: lab frames + mcf.research.gates (E2 2-year screen), production + time-of-day costs.
Rule: adv20 >= $95M, close >= $5; SPY gap (daily open / prior close - 1) >= +0.30%; stock gap <= -1.5%; first 5-min bar
09:50-11:00 with fromOpen >= +0.5% and vwapDistPct > 0 -> long t1s1, one per symbol-day. Control = same rule on sessions
with SPY gap < +0.30%. Locked block 2024-11..2025-02 never read (lib.months()). Usage: python gud1_bt.py -> gud1_bt_out.txt.
Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
import lib  # noqa: E402
from mcf.research import gates as G  # noqa: E402
HERE = Path(__file__).resolve().parent; BAR = 1.35
D_ = lib.daily(); sp = D_[D_.symbol == "SPY"].sort_values("date").set_index("date")
spy_gap = (sp.open / sp.close.shift(1) - 1) * 100; oc = (sp.close / sp.open - 1) * 100
dtype = pd.Series(np.where(oc > .25, "up", np.where(oc < -.25, "down", "quiet")), index=sp.index)
gapup = set(spy_gap[spy_gap >= 0.30].index.astype(str))
cols = ["symbol", "date", "tod", "close", "gap", "fromOpen", "vwapDistPct", "atr_d", "adv20", "r_long_t1s1", "win_long_t1s1"]
T = []
for m in lib.months():
    assert m not in lib.LOCKED_MONTHS
    f = lib.load_month(m, columns=cols); f["date"] = f.date.astype(str); f["symbol"] = f.symbol.astype(str)
    f = f[(f.adv20 >= 95e6) & (f.close >= 5) & ~f.symbol.isin(["SPY", "QQQ", "IWM"])].sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
    mask = (f.gap <= -1.5) & (f.tod >= 950) & (f.tod <= 1100) & (f.fromOpen >= 0.5) & (f.vwapDistPct > 0)
    t = G.lab_trades(f, mask.to_numpy(), "long", "t1s1"); t["date"] = t.date.astype(str)
    T.append(t); print(m, len(t), flush=True); del f
T = pd.concat(T, ignore_index=True); assert not T.date.between(*lib.LOCKED).any()
T["gu"] = T.date.isin(gapup); T["dt"] = T.date.map(lambda d: dtype.get(pd.Timestamp(d).date(), "?") if pd.Timestamp(d).date() in dtype.index else dtype.get(d, "?"))
T["split"] = np.where(T.date <= "2025-12-31", "TRAIN", np.where(T.date <= "2026-10-05", "VALID", "LATE"))
out = []
def p(*a): out.append(" ".join(str(x) for x in a)); print(out[-1], flush=True)
nday = {sp_: len({d for d in sp.index.astype(str) if (d <= "2025-12-31" if sp_ == "TRAIN" else ("2026-01-01" <= d <= "2026-10-05" if sp_ == "VALID" else d >= "2026-10-06")) and d in gapup}) for sp_ in ("TRAIN", "VALID", "LATE")}
p(f"GUD1 | E2 2-year screen (lab frames + gates), production + TOD costs | configs 1 | Testing bar t {BAR} | SPY gap-up sessions per split {nday}")
res = {}
for lab, X in (("RULE (SPY gap-up sessions)", T[T.gu]), ("CONTROL (other sessions)", T[~T.gu])):
    p(f"== {lab}")
    s = G.summary(X); p(f"  ALL: n {s.get('n')} days {s.get('days')} avg {s.get('exp_r')} t {s.get('t')} win {s.get('win_rate')} w/o best {s.get('ex_best_day')}")
    res[(lab[:4], "ALL")] = s
    for sp_ in ("TRAIN", "VALID", "LATE"):
        s = G.summary(X[X.split == sp_]); res[(lab[:4], sp_)] = s
        p(f"  {sp_}: n {s.get('n')} days {s.get('days')} avg {s.get('exp_r')} t {s.get('t')} w/o best {s.get('ex_best_day')}")
    p("  by SPY open->close day type: " + ", ".join(f"{k} n {len(v)} {v.r.mean():+.3f}" for k, v in X.groupby("dt")))
R = T[T.gu]
p(f"trades per gap-up session: {len(R) / max(1, R.date.nunique()):.2f}")
r, c = res, lambda k: (r[k].get("exp_r") if r[k].get("n") else None)
ok = ((c(("RULE", "TRAIN")) or -1) > 0 and (c(("RULE", "VALID")) or -1) > 0 and (r[("RULE", "ALL")].get("t") or 0) >= BAR
      and (r[("RULE", "ALL")].get("ex_best_day") or -1) > 0 and r[("RULE", "VALID")].get("n", 0) >= 30
      and (c(("RULE", "TRAIN")) or -1) > (c(("CONT", "TRAIN")) or 0) and (c(("RULE", "VALID")) or -1) > (c(("CONT", "VALID")) or 0))
p(f"PASS {bool(ok)}"); p("Educational only - not financial advice.")
(HERE / "gud1_bt_out.txt").write_text("\n".join(out) + "\n")
