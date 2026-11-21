"""swing1120-L17 - pre-registered 2-year screen (BDI 2026-11-20 step 0b; row in research/bdi/swings/hypotheses.jsonl written
before this run; configs 1). Engine: lab frames + mcf.research.gates (E2 2-year screen), production + TOD costs.
Lab rule = research/swarm1017/arena-index-etf/modules/AR-ETF-late-dip-di-long.py mask, unchanged (t05s1, one per
symbol-day). Class A = long-exposure (not inverse / long-vol) entries on a bar where SPY's lab fromOpen <= -1.00%;
class B = all other entries. Locked block never read. Usage: python l17_bt.py -> l17_bt_out.txt.
Educational only - not financial advice."""
import importlib.util, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
import lib  # noqa: E402
from mcf.research import gates as G  # noqa: E402
HERE = Path(__file__).resolve().parent; REPO = HERE.parents[2]
spec = importlib.util.spec_from_file_location("etfdip", REPO / "research/swarm1017/arena-index-etf/modules/AR-ETF-late-dip-di-long.py")
MOD = importlib.util.module_from_spec(spec); spec.loader.exec_module(MOD)
INV = {"DOG", "DUST", "DXD", "ERY", "FAZ", "LABD", "PSQ", "QID", "RWM", "SDOW", "SDS", "SH", "SOXS", "SPDN", "SPXS", "SPXU",
       "SQQQ", "SRTY", "TECS", "TWM", "TZA", "UVXY", "VXX", "UVIX", "VIXY"}
TREQ = G.t_required(33)
T = []
for m in lib.months():
    assert m not in lib.LOCKED_MONTHS
    f = lib.load_month(m); f["date"] = f.date.astype(str); f["symbol"] = f.symbol.astype(str)
    spy = f[f.symbol == "SPY"][["date", "tod", "fromOpen"]].rename(columns={"fromOpen": "spy_fo"})
    e = f[f.symbol.isin(MOD.SYMBOLS)].sort_values(["symbol", "date", "tod"]).reset_index(drop=True); del f
    mk = MOD.mask(e)
    t = G.lab_trades(e, mk, MOD.SIDE, MOD.GEOM); t["date"] = t.date.astype(str)
    if "tod" not in t.columns:
        raise SystemExit("lab_trades returned no tod column")
    t = t.merge(spy, on=["date", "tod"], how="left")
    T.append(t); print(m, len(t), flush=True)
T = pd.concat(T, ignore_index=True); assert not T.date.between(*lib.LOCKED).any()
T["inv"] = T.symbol.isin(INV)
T["A"] = ~T.inv & (T.spy_fo <= -1.00)
burst = T[~T.inv].groupby(["date", "tod"]).size().rename("burst")
T = T.merge(burst, on=["date", "tod"], how="left"); T["burst"] = T.burst.fillna(0)
T["split"] = np.where(T.date <= "2025-12-31", "TRAIN", np.where(T.date <= "2026-10-05", "VALID", "LATE"))
out = []
def p(*a): out.append(" ".join(str(x) for x in a)); print(out[-1], flush=True)
p(f"swing1120-L17 | E2 2-year screen (lab frames + gates; module mask unchanged), production + TOD costs | configs 1 | t_required(33) {TREQ:.2f}")
p(f"all module trades: n {len(T)}, sessions {T.date.nunique()}, avg {T.r.mean():+.4f}; SPY fo missing {T.spy_fo.isna().sum()}")


def diff(X):
    """A - B with a day-clustered SE (per-session sums, as gates.summary)."""
    a, b = X[X.A], X[~X.A]
    if len(a) < 2 or len(b) < 2:
        return None, None
    ga, gb = a.groupby("date").r.agg(["sum", "size"]), b.groupby("date").r.agg(["sum", "size"])
    ma, mb = a.r.mean(), b.r.mean()
    sa = np.sqrt(((ga["sum"] - ga["size"] * ma) ** 2).sum()) / len(a); sb = np.sqrt(((gb["sum"] - gb["size"] * mb) ** 2).sum()) / len(b)
    return ma - mb, (ma - mb) / np.sqrt(sa ** 2 + sb ** 2)


res = {}
for sp_ in ("ALL", "TRAIN", "VALID", "LATE"):
    X = T if sp_ == "ALL" else T[T.split == sp_]
    sa, sb = G.summary(X[X.A]), G.summary(X[~X.A]); d, t = diff(X); res[sp_] = (sa, sb, d, t)
    p(f"{sp_}: A n {sa.get('n')} sess {sa.get('days')} avg {sa.get('exp_r')} w/o best {sa.get('ex_best_day')} | "
      f"B n {sb.get('n')} sess {sb.get('days')} avg {sb.get('exp_r')} | A-B {d if d is None else round(d, 4)} t {t if t is None else round(t, 2)}")
X = T[~T.inv & (T.spy_fo > -1.0)]; s = G.summary(X); p(f"B split: long-exposure, SPY > -1%: n {s.get('n')} avg {s.get('exp_r')}")
X = T[T.inv]; s = G.summary(X); p(f"B split: inverse / long-vol entries: n {s.get('n')} avg {s.get('exp_r')}")
X = T[T.inv & (T.spy_fo <= -1.0)]; s = G.summary(X); p(f"  inverse entries on the same deep-down bars: n {s.get('n')} avg {s.get('exp_r')}")
A = T[T.A]
gA = A.groupby("date").r.sum(); w = gA.idxmin()
p(f"report only: A w/o its worst session {(gA.sum() - gA[w]) / max(1, len(A) - (A.date == w).sum()):+.4f} (worst {w} {gA[w]:+.2f}R)")
p("A by burst size (same-bar long-exposure signals): " + ", ".join(f"{k} n {len(v)} {v.r.mean():+.3f}" for k, v in A.groupby(pd.cut(A.burst, [0, 1, 3, 7, 999]), observed=True)))
p("long-exposure by SPY fo bucket: " + ", ".join(f"{k} n {len(v)} {v.r.mean():+.3f}" for k, v in T[~T.inv].groupby(pd.cut(T[~T.inv].spy_fo, [-99, -2, -1.5, -1, -0.5, 0, 0.5, 99]), observed=True)))
sa, sb, d, t = res["ALL"]
ok = (d is not None and t <= -TREQ and d <= -0.10 and (res["TRAIN"][2] or 0) < 0 and (res["VALID"][2] or 0) < 0
      and sa.get("n", 0) >= 60 and sa.get("days", 0) >= 15 and (sa.get("ex_best_day") or 9) < (sb.get("exp_r") or -9))
p(f"PASS {bool(ok)}")
p("Educational only - not financial advice.")
(HERE / "l17_bt_out.txt").write_text("\n".join(out) + "\n")
