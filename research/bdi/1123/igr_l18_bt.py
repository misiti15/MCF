"""BDI 2026-11-23: two pre-registered 2-year screens in one pass over the lab frames (both written before this run).
(1) IGR1 (backlog mech-1123-igr1-index-gap-rotation-long; configs 8): on SPY gap-up sessions buy names that gapped DOWN
    against the index (gap <= 0 and gap - SPY gap <= -K), t1s1 long; control = same K / entry on |SPY gap| < 0.25% sessions.
(2) swing1123-L18 (research/bdi/swings/hypotheses.jsonl; configs 1): RW3-FD / RW5-FD masks unchanged; class A = entries on
    sessions with SPY gap >= +0.75%, class B = the rest; A - B with a day-clustered t.
Engine E2 (lab frames + mcf.research.gates, production + TOD costs, one trade per symbol-day). Locked block 2024-11..2025-02
never read (lib.months()). Usage: python igr_l18_bt.py -> igr_l18_bt_out.txt. Educational only - not financial advice."""
import importlib.util, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
import lib  # noqa: E402
from mcf.research import gates as G  # noqa: E402
HERE = Path(__file__).resolve().parent; REPO = HERE.parents[2]
MODS = {}
for k in ("RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD"):
    sp = importlib.util.spec_from_file_location(k.replace("-", "_"), REPO / "research/bdi/fullday" / f"{k}.py")
    MODS[k] = importlib.util.module_from_spec(sp); sp.loader.exec_module(MODS[k])
# leveraged / inverse / vol ETPs (excluded from IGR1: their gap is the index's gap times leverage)
ETP = set("""SQQQ SPXS SPXU SDS SH PSQ QID SOXS TZA SRTY TECS FAZ UVXY UVIX VXX VIXY SDOW LABD TSLQ NVDQ NVD TSDD DUST YANG DOG
DXD ERY RWM TWM SPDN TQQQ SPXL UPRO SSO QLD SOXL TNA TECL FAS LABU NVDL TSLL MUU NUGT YINN UDOW SVIX SVXY BITX MSTU MSTX MSTZ
CONL BTCZ ETHU SBIT SNDQ AMDL AAPU GGLL METU AMZU TSLZ PLTU NVDU NVDX SOXX""".split()) - {"SOXX"}
GRID = [(g, k, e) for g in (0.75, 1.00) for k in (2.0, 3.5) for e in ("E1", "E2")]
TREQ_I, TREQ_L, NEAR = G.t_required(12), G.t_required(34), 1.35
D_ = lib.daily(); spd = D_[D_.symbol == "SPY"].sort_values("date").set_index("date")
oc = (spd.close / spd.open - 1) * 100; oc.index = oc.index.astype(str)
dtype = pd.Series(np.where(oc > .25, "up", np.where(oc < -.25, "down", "quiet")), index=oc.index)
I, L, SG = [], [], {}
for m in lib.months():
    assert m not in lib.LOCKED_MONTHS
    f = lib.load_month(m); f["date"] = f.date.astype(str); f["symbol"] = f.symbol.astype(str)
    s = f[(f.symbol == "SPY") & (f.tod == 950)].set_index("date").gap; SG.update(s.to_dict())
    f = f[(f.adv20 >= 95e6) & (f.tod >= 950) & (f.tod <= 1500)].sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
    f["spy_gap"] = f.date.map(s)
    # L18: module masks unchanged
    for k, M in MODS.items():
        t = G.lab_trades(f, M.mask(f), M.SIDE, M.GEOM); t["date"] = t.date.astype(str); t["setup"] = k; L.append(t)
    # IGR1
    base = (f.close >= 5) & (f.gap.abs() < 15) & ~f.symbol.isin(ETP) & (f.gap <= 0) & f.spy_gap.notna()
    for g, k, e in GRID:
        cand = base & (f.gap - f.spy_gap <= -k)
        if e == "E1":
            tm = f.tod == 950
        else:
            tm = (f.tod >= 955) & (f.tod <= 1030) & (f.fromOpen >= 0.25)
        for kind, day in (("rule", f.spy_gap >= g), ("control", f.spy_gap.abs() < 0.25)):
            mk = (cand & tm & day).to_numpy()
            t = G.lab_trades(f, mk, "long", "t1s1"); t["date"] = t.date.astype(str); t["cfg"] = f"G{g}-K{k}-{e}"; t["kind"] = kind; I.append(t)
    print(m, f.date.nunique(), flush=True); del f
I = pd.concat(I, ignore_index=True); L = pd.concat(L, ignore_index=True)
for X in (I, L):
    assert not X.date.between(*lib.LOCKED).any()
    X["split"] = np.where(X.date <= "2025-12-31", "TRAIN", np.where(X.date <= "2026-10-05", "VALID", "LATE"))
    X["dt"] = X.date.map(dtype).fillna("?")
out = []
def p(*a): out.append(" ".join(str(x) for x in a)); print(out[-1], flush=True)
sg = pd.Series(SG)
p(f"IGR1 + swing1123-L18 | E2 2-year screen (lab frames + gates), production + TOD costs | configs 8 (IGR1) + 1 (L18) = 9")
p(f"sessions {len(sg)}; SPY gap >= +0.75%: {(sg >= .75).sum()}, >= +1.00%: {(sg >= 1).sum()}, |gap| < 0.25%: {(sg.abs() < .25).sum()}")
p(f"IGR1 bar t_required(12) {TREQ_I:.2f}, near-miss {NEAR}; L18 bar t_required(34) {TREQ_L:.2f}")
p("\n== IGR1 (long; rule = SPY gap >= G, stock gap <= 0 and gap - SPY gap <= -K)")
verdict = {}
for c in [f"G{g}-K{k}-{e}" for g, k, e in GRID]:
    R = {}
    for kind in ("rule", "control"):
        X = I[(I.cfg == c) & (I.kind == kind)]
        for sp_ in ("ALL", "TRAIN", "VALID", "LATE"):
            R[(kind, sp_)] = G.summary(X if sp_ == "ALL" else X[X.split == sp_])
    X = I[(I.cfg == c) & (I.kind == "rule")]; a = R[("rule", "ALL")]
    ps = X.groupby("date").r.mean() if len(X) else pd.Series(dtype=float)
    ev = lambda kind, sp_: R[(kind, sp_)].get("exp_r") if R[(kind, sp_)].get("n") else None
    p(f"-- {c}: n {a.get('n')} sess {a.get('days')} avg {a.get('exp_r')} t {a.get('t')} win {a.get('win_rate')} w/o best {a.get('ex_best_day')} | "
      f"TRAIN {ev('rule', 'TRAIN')} ({R[('rule', 'TRAIN')].get('days')}) VALID {ev('rule', 'VALID')} ({R[('rule', 'VALID')].get('days')}) LATE {ev('rule', 'LATE')} | "
      f"control ALL {ev('control', 'ALL')} TRAIN {ev('control', 'TRAIN')} VALID {ev('control', 'VALID')} (n {R[('control', 'ALL')].get('n')})")
    if len(X):
        p(f"   per-session bet mean {ps.mean():+.3f} green {(ps > 0).mean():.0%}; trades/session median {X.groupby('date').size().median():.0f}; "
          "by SPY o->c: " + ", ".join(f"{k} sess {v.date.nunique()} n {len(v)} {v.r.mean():+.3f}" for k, v in X.groupby("dt")))
    base = ((ev("rule", "TRAIN") or -1) > 0 and (ev("rule", "VALID") or -1) > 0 and (a.get("ex_best_day") or -1) > 0
            and a.get("days", 0) >= 15 and R[("rule", "VALID")].get("days", 0) >= 5 and len(ps) and ps.mean() > 0
            and (ev("rule", "TRAIN") or -9) > (ev("control", "TRAIN") or 0) and (ev("rule", "VALID") or -9) > (ev("control", "VALID") or 0))
    verdict[c] = ("PASS" if base and (a.get("t") or 0) >= TREQ_I else "NEAR" if base and (a.get("t") or 0) >= NEAR else "FAIL")
    p(f"   verdict {verdict[c]}")
p("IGR1 verdicts: " + ", ".join(f"{k} {v}" for k, v in verdict.items()))


def diff(X):
    a, b = X[X.A], X[~X.A]
    if len(a) < 2 or len(b) < 2:
        return None, None
    ga, gb = a.groupby("date").r.agg(["sum", "size"]), b.groupby("date").r.agg(["sum", "size"])
    ma, mb = a.r.mean(), b.r.mean()
    sa = np.sqrt(((ga["sum"] - ga["size"] * ma) ** 2).sum()) / len(a); sb = np.sqrt(((gb["sum"] - gb["size"] * mb) ** 2).sum()) / len(b)
    return ma - mb, (ma - mb) / np.sqrt(sa ** 2 + sb ** 2)


p("\n== swing1123-L18 (RW3-FD + RW5-FD shorts; A = SPY gap >= +0.75% sessions)")
L["A"] = L.date.map(sg).fillna(0) >= 0.75
res = {}
for sp_ in ("ALL", "TRAIN", "VALID", "LATE"):
    X = L if sp_ == "ALL" else L[L.split == sp_]
    sa, sb = G.summary(X[X.A]), G.summary(X[~X.A]); d, t = diff(X); res[sp_] = (sa, sb, d, t)
    p(f"{sp_}: A n {sa.get('n')} sess {sa.get('days')} avg {sa.get('exp_r')} w/o best {sa.get('ex_best_day')} | B n {sb.get('n')} sess {sb.get('days')} "
      f"avg {sb.get('exp_r')} | A-B {d if d is None else round(d, 4)} t {t if t is None else round(t, 2)}")
for k, X in L.groupby("setup"):
    d, t = diff(X); p(f"  {k}: A n {int(X.A.sum())} avg {X[X.A].r.mean():+.3f} | B n {int((~X.A).sum())} avg {X[~X.A].r.mean():+.3f} | A-B {d:+.3f} t {t:.2f}")
A = L[L.A]
p("  A by SPY o->c: " + ", ".join(f"{k} sess {v.date.nunique()} n {len(v)} {v.r.mean():+.3f}" for k, v in A.groupby("dt")))
sa, sb, d, t = res["ALL"]
ok = (d is not None and t <= -TREQ_L and d <= -0.10 and (res["TRAIN"][2] or 0) < 0 and (res["VALID"][2] or 0) < 0
      and sa.get("n", 0) >= 60 and sa.get("days", 0) >= 15 and (sa.get("ex_best_day") or 9) < (sb.get("exp_r") or -9))
p(f"L18 PASS {bool(ok)}")
p("Educational only - not financial advice.")
(HERE / "igr_l18_bt_out.txt").write_text("\n".join(out) + "\n")
