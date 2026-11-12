"""Observer: the 39 unrated setups in Scout's REPS3 forecast (Lead lead-20261111-1905-2) + Testing A's full-universe lever.
Expected setup-days/week = 5 x p_day, p_day = 1 - exp(-0.193 x lab trades/day) (Scout's REPS2 fit, corr 0.76).
Lab rate source, in order: GEN -> gen.screen.per_day in config/account_gen.yaml (2y screen, first qualifying bar per symbol-day);
others -> the trades/day a research note states (cited); else 'no lab rate found' (needs Builder's bt lists).
Testing A: signals/session by status and submitted-trade R, before (10-20..11-03) vs after (11-04..11-10) the top-500 pool.
Descriptive, 0 configs. usage: python unrated.py <journal_dir>. Educational only - not financial advice."""
import sys, glob, os, math, sqlite3, yaml, numpy as np, pandas as pd
pd.set_option("display.width", 220)
F = pd.read_csv("../guild/research/reps3/forecast_setups.csv"); U = F[F.src == "unknown"].copy()
Y = {}
for p in glob.glob("config/account_*.yaml"):
    for k, v in ((yaml.safe_load(open(p)) or {}).get("strategies") or {}).items(): Y.setdefault(k, v)
DOC = {  # trades/day stated in research notes (lab, 2y)
    "LD1-ns1-breadthup-t05s1-long": (0.35, "longs1020 NOTES B5-NS1-BRDUP"),
    "LD3-st2-idxturn-t05s1-long": (0.26, "longs1020 NOTES B5-ST2-IDXTURN"),
    "IDX5-spy050-0945-3x-trail": (0.04, "longs1020 NOTES P-IDX5 parent replica"),
}
rows = []
for _, r in U.iterrows():
    s = r.setup; rate, src = np.nan, "no lab rate found"
    if s.startswith("GEN"):
        sc = ((Y.get(s) or {}).get("gen") or {}).get("screen") or {}
        if sc.get("per_day") is not None: rate, src = float(sc["per_day"]), "gen.screen.per_day (2y)"
    elif s in DOC: rate, src = DOC[s]
    p = 1 - math.exp(-0.193 * rate) if rate == rate else np.nan
    rows.append(dict(account=r.account, setup=s, lab_per_day=rate, p_day=p, days_week=5 * p if p == p else np.nan, source=src))
R = pd.DataFrame(rows).sort_values("days_week", ascending=False)
print(f"unrated setups {len(R)}; with a lab rate {int(R.days_week.notna().sum())}; expected setup-days/week total {R.days_week.sum():.1f}")
print(R.round(3).to_string(index=False))
print("\nby account:", R.groupby("account").days_week.agg(["count", "sum"]).round(1).to_dict("index"))
# Testing A (testing2) before / after the top-500 pool (11-04)
c = sqlite3.connect(os.path.join(sys.argv[1], "mcf-data-testing2.db"))
S = pd.read_sql("select day, status, reason from signals where run_id=1 and day between '2026-10-20' and '2026-11-10'", c)
T = pd.read_sql("select date, strategy, entry, stop, shares, pnl_adj from trades where run_id=1 and date between '2026-10-20' and '2026-11-10' and exit is not null", c)
T["R"] = T.pnl_adj / ((T.entry - T.stop).abs() * T.shares).replace(0, np.nan)
for lab, a, b in (("before (10-20..11-03)", "2026-10-20", "2026-11-03"), ("after top-500 (11-04..11-10)", "2026-11-04", "2026-11-10")):
    s = S[(S.day >= a) & (S.day <= b)]; t = T[(T.date >= a) & (T.date <= b)]; nd = s.day.nunique()
    uni = s.reason.fillna("").str.contains("universe|top-500|top500|pool", case=False)
    sd = t.groupby("strategy").date.nunique().sum()
    print(f"\nTesting A {lab}: sessions {nd}; signals/session {len(s) / nd:.0f} (submitted {(s.status == 'submitted').sum() / nd:.0f}); "
          f"universe-skips/session {uni.sum() / nd:.1f}; trades/session {len(t) / nd:.0f}, avg R {t.R.mean():+.3f}; setup-days/session {sd / nd:.1f}")
print("Rule changes inside: CF cost filter 10-30 (Testing A), UNI1 top-500 11-04, ROLL1 homes 11-05, TEAM-6 11-11. Educational only - not financial advice.")
# calibration: GEN setups WITH a live p_day (REPS3 src 'live') - screen-predicted vs live submitted-day share
L = F[(F.src == "live") & F.setup.str.startswith("GEN")].copy()
L["screen_per_day"] = [float((((Y.get(s) or {}).get("gen") or {}).get("screen") or {}).get("per_day") or np.nan) for s in L.setup]
L["p_pred"] = 1 - np.exp(-0.193 * L.screen_per_day); L = L[L.p_pred.notna()]
print(f"\ncalibration on {len(L)} GEN setups with live p_day: predicted mean {L.p_pred.mean():.3f} vs live {L.p_day.mean():.3f}; "
      f"corr {L.p_pred.corr(L.p_day):.2f}; live/predicted ratio median {(L.p_day / L.p_pred).median():.2f}")
