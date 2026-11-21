"""OPX1 (backlog mech-1120-opx1-failed-open-push-etp-long) - pre-registered 2-year screen (BDI 2026-11-20; card written
before this run; configs 2: A inverse / long-vol after a failed push up, B bull leveraged after a failed dip).
Engine: lab frames + mcf.research.gates (E2 2-year screen), production + time-of-day costs. Locked block 2024-11..2025-02
never read (lib.months()). Usage: python opx1_bt.py -> opx1_bt_out.txt. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/history2y"))
import lib  # noqa: E402
from mcf.research import gates as G  # noqa: E402
HERE = Path(__file__).resolve().parent
TREQ = G.t_required(76); NEAR = 1.35
LIST = {"A": ["SQQQ", "SPXU", "SPXS", "SDS", "SH", "PSQ", "QID", "SDOW", "SPDN", "UVXY", "VXX", "UVIX", "VIXY"],
        "B": ["TQQQ", "SPXL", "UPRO", "QLD", "SSO", "UDOW", "TNA"]}
D_ = lib.daily(); sp = D_[D_.symbol == "SPY"].sort_values("date").set_index("date")
oc = (sp.close / sp.open - 1) * 100; oc.index = oc.index.astype(str)
dtype = pd.Series(np.where(oc > .25, "up", np.where(oc < -.25, "down", "quiet")), index=oc.index)
cols = ["symbol", "date", "tod", "close", "fromOpen", "dist_hod_atr", "dist_lod_atr", "atr_d", "adv20", "r_long_t1s1", "win_long_t1s1"]
T, TRIG = [], []
for m in lib.months():
    assert m not in lib.LOCKED_MONTHS
    f = lib.load_month(m, columns=cols); f["date"] = f.date.astype(str); f["symbol"] = f.symbol.astype(str)
    s = f[(f.symbol == "SPY") & (f.tod >= 950) & (f.tod <= 1030)].copy()
    s["hod"] = s.fromOpen + s.dist_hod_atr * s.atr_d / s.close * 100
    s["lod"] = s.fromOpen - s.dist_lod_atr * s.atr_d / s.close * 100
    trig = {"A": s[(s.hod >= 0.30) & (s.fromOpen <= -0.10)].groupby("date").tod.min(),
            "B": s[(s.lod <= -0.30) & (s.fromOpen >= 0.10)].groupby("date").tod.min()}
    days = sorted(s.date.unique())
    e = f[f.symbol.isin(LIST["A"] + LIST["B"]) & (f.adv20 >= 95e6)].sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
    for c in ("A", "B"):
        tt = e.date.map(trig[c]); has = tt.notna()
        for kind, mask in (("rule", has & (e.tod == tt)), ("control", ~has & (e.tod == 1000))):
            mk = (mask & e.symbol.isin(LIST[c])).to_numpy()
            t = G.lab_trades(e, mk, "long", "t1s1"); t["date"] = t.date.astype(str); t["cfg"] = c; t["kind"] = kind
            T.append(t)
        TRIG += [dict(cfg=c, date=d, tod=int(trig[c][d])) for d in trig[c].index]
    print(m, len(days), {c: len(trig[c]) for c in trig}, flush=True); del f
T = pd.concat(T, ignore_index=True); assert not T.date.between(*lib.LOCKED).any()
TR = pd.DataFrame(TRIG)
T["split"] = np.where(T.date <= "2025-12-31", "TRAIN", np.where(T.date <= "2026-10-05", "VALID", "LATE"))
T["dt"] = T.date.map(dtype).fillna("?")
out = []
def p(*a): out.append(" ".join(str(x) for x in a)); print(out[-1], flush=True)
p(f"OPX1 | E2 2-year screen (lab frames + gates), production + TOD costs | configs 2 | t_required(76) {TREQ:.2f}, near-miss {NEAR}")
p(f"trigger sessions: A {len(TR[TR.cfg == 'A'])}, B {len(TR[TR.cfg == 'B'])}; trigger tod A {TR[TR.cfg == 'A'].tod.value_counts().sort_index().to_dict()}")
res = {}
for c in ("A", "B"):
    for kind in ("rule", "control"):
        X = T[(T.cfg == c) & (T.kind == kind)]
        p(f"== OPX1-{c} {kind}: ETPs {sorted(X.symbol.unique())}")
        s = G.summary(X); res[(c, kind, "ALL")] = s
        p(f"  ALL: n {s.get('n')} sessions {s.get('days')} avg {s.get('exp_r')} t {s.get('t')} win {s.get('win_rate')} green {s.get('green_days')} w/o best {s.get('ex_best_day')}")
        for sp_ in ("TRAIN", "VALID", "LATE"):
            s = G.summary(X[X.split == sp_]); res[(c, kind, sp_)] = s
            p(f"  {sp_}: n {s.get('n')} sessions {s.get('days')} avg {s.get('exp_r')} t {s.get('t')} w/o best {s.get('ex_best_day')}")
        p("  by SPY open->close: " + ", ".join(f"{k} sess {v.date.nunique()} n {len(v)} {v.r.mean():+.3f}" for k, v in X.groupby("dt")))
        if kind == "rule":
            ps = X.groupby("date").r.mean()
            p(f"  as one bet per session: mean {ps.mean():+.3f}R, sessions {len(ps)}, green {(ps > 0).mean():.0%}, t {ps.mean() / (ps.std(ddof=1) / np.sqrt(len(ps))):.2f}")
            p("  by ETP: " + ", ".join(f"{k} {len(v)} {v.r.mean():+.3f}" for k, v in X.groupby("symbol")))
for c in ("A", "B"):
    g = lambda k, sp_: (res[(c, k, sp_)].get("exp_r") if res[(c, k, sp_)].get("n") else None)
    a = res[(c, "rule", "ALL")]
    base = ((g("rule", "TRAIN") or -1) > 0 and (g("rule", "VALID") or -1) > 0 and (a.get("ex_best_day") or -1) > 0
            and a.get("days", 0) >= 30 and res[(c, "rule", "VALID")].get("days", 0) >= 10
            and (g("rule", "TRAIN") or -9) > (g("control", "TRAIN") or 0) and (g("rule", "VALID") or -9) > (g("control", "VALID") or 0))
    p(f"OPX1-{c}: PASS {bool(base and (a.get('t') or 0) >= TREQ)}; near-miss {bool(base and (a.get('t') or 0) >= NEAR)}")
p("Educational only - not financial advice.")
(HERE / "opx1_bt_out.txt").write_text("\n".join(out) + "\n")
