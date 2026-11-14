"""sat1114 give-back proposals G1-G4 (PLAN.md, pre-registered): per-setup trailing latch (2R / 3R from the setup's day high
of booked R) and account give-back brake (10R / 15R from the account's day high of booked R), both on top of the live
realised -2R latch; new entries only (open trades / exits untouched). Two-year lab trades (burst1/trades_2y.parquet,
production costs, locked block absent - asserted) and this week's live journals (run 1, R after costs).
Usage: python sim_g.py <trades_2y.parquet> <scratch with <acct>/journal.db>     Educational only - not financial advice."""
import heapq, math, os, re, sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
OUT = Path(__file__).resolve().parent; out = []; P = lambda *x: (out.append(" ".join(map(str, x))), print(*x))
fam = lambda s: re.sub(r"\d.*", "", s).split("-")[0]
BAR = max(1.5, math.sqrt(2 * math.log(40)))
CFG = {"G1_trail2": ("trail", 2.0), "G2_trail3": ("trail", 3.0), "G3_acct10": ("acct", 10.0), "G4_acct15": ("acct", 15.0)}


def setup_keep(m, xm, r, trail):
    """sequential per setup-day: block an entry once booked R (kept trades exited before it) <= -2, or <= high - trail."""
    keep = np.zeros(len(m), bool); ex = []; booked = 0.0; hi = 0.0
    for k in np.argsort(m, kind="stable"):
        while ex and ex[0][0] < m[k]:
            _, rr = heapq.heappop(ex); booked += rr; hi = max(hi, booked)
        if booked <= -2.0 or (trail and booked <= hi - trail): continue
        keep[k] = True; heapq.heappush(ex, (xm[k], r[k]))
    return keep


def acct_cut(m, xm, r, Y):
    """first entry minute at which the account's booked R <= max(high, 0) - Y (inf if never)."""
    ex = sorted(zip(xm, r)); booked = 0.0; hi = 0.0
    for x, rr in ex:
        booked += rr; hi = max(hi, booked)
        if booked <= hi - Y: return x  # entries strictly after this exit minute are blocked
    return np.inf


def run(T, acct_col, day_col, mcol, xcol):
    keys = {"base": None}; K = {}
    base = np.zeros(len(T), bool); tr = {c: np.zeros(len(T), bool) for c in CFG if CFG[c][0] == "trail"}
    for _, ix in T.groupby(["setup", day_col], sort=False).indices.items():
        m, xm, r = T[mcol].values[ix], T[xcol].values[ix], T.r.values[ix]
        base[ix] = setup_keep(m, xm, r, 0)
        for c in tr: tr[c][ix] = setup_keep(m, xm, r, CFG[c][1])
    K["base"] = base; K.update(tr)
    for c, (kind, Y) in CFG.items():
        if kind != "acct": continue
        k = base.copy()
        for _, ix in T[base].groupby([acct_col, day_col], sort=False).indices.items():
            ix = np.flatnonzero(base)[ix]
            cut = acct_cut(T[mcol].values[ix], T[xcol].values[ix], T.r.values[ix], Y)
            k[ix[T[mcol].values[ix] > cut]] = False
        K[c] = k
    return K


def dt(s): return s.mean() / s.std(ddof=1) * math.sqrt(len(s)) if len(s) > 1 and s.std(ddof=1) > 0 else 0.0


def giveback(T, k, acct, day_col, xcol):
    x = T[k & (T.account == acct)].sort_values([day_col, xcol])
    g = x.groupby(day_col).r.agg(lambda s: s.cumsum().clip(lower=0).max() - s.sum() if len(s) else 0)
    return g.mean(), g.quantile(0.9)


# ---------------------------------------------------------------- two years
T = pd.read_parquet(sys.argv[1], columns=["setup", "account", "date", "m", "xm", "r"])
assert not T.date.between("2024-11-01", "2025-02-28").any(), "locked block must be absent"
T = T.reset_index(drop=True); T["fam"] = T.setup.map(fam)
K = run(T, "account", "date", "m", "xm")
WIN = {"TRAIN": T.date <= "2026-02-28", "VALID": (T.date >= "2026-03-01") & (T.date <= "2026-10-05")}
rows, setrows, famrows = [], [], []
for c in CFG:
    rem = K["base"] & ~K[c]
    res = dict(config=c, removed_pct=rem.sum() / K["base"].sum())
    for w, msk in WIN.items():
        X = T[msk]; kb, kc = K["base"][msk.values], K[c][msk.values]
        mu = X[kb].groupby("setup").r.mean()
        dv = X.r * (kc.astype(float) - kb.astype(float)); dx = (X.r - X.setup.map(mu).fillna(0)) * (kc.astype(float) - kb.astype(float))
        dates = sorted(X.date.unique())
        dd = dv.groupby(X.date).sum().reindex(dates, fill_value=0); xd = dx.groupby(X.date).sum().reindex(dates, fill_value=0)
        res.update({f"{w}_d": dd.sum(), f"{w}_t": dt(dd), f"{w}_x": xd.sum(), f"{w}_xt": dt(xd), f"{w}_removed": int((kb & ~kc).sum())})
        ps = dv.groupby(X.setup).sum()
        res.update({f"{w}_set_better": int((ps > 1e-9).sum()), f"{w}_set_better_R": ps[ps > 0].sum(), f"{w}_set_worse": int((ps < -1e-9).sum()),
                    f"{w}_set_worse_R": ps[ps < 0].sum(), f"{w}_worst": f"{ps.idxmin()} {ps.min():+.1f}" if len(ps) else ""})
        for s, v in ps.items(): setrows.append(dict(config=c, window=w, setup=s, account=X[X.setup == s].account.iat[0], delta=v))
        harm = []
        for f, g in X.groupby("fam"):
            d = dv[g.index].groupby(g.date).sum().reindex(dates, fill_value=0); s = dv[g.index].groupby(g.setup).sum()
            fabs = X.r[g.index][kb[g.index.map(X.index.get_loc)]].abs().sum() if False else g.r[kb[[X.index.get_loc(i) for i in g.index]]].abs().sum()
            imp, wor = s[s > 0].sum(), -s[s < 0].sum()
            harmed = (d.sum() < 0 and dt(d) <= -1) or (wor > 2 * imp and d.sum() < -0.05 * fabs)
            famrows.append(dict(config=c, window=w, family=f, delta=d.sum(), t=dt(d), improved=int((s > 1e-9).sum()), worse=int((s < -1e-9).sum()), harmed=harmed))
            if harmed: harm.append(f)
        res[f"{w}_fam_harmed"] = ",".join(harm)
        pr = X.account == "primary"
        res[f"{w}_primary_d"] = dv[pr].sum()
        gb0 = giveback(X, kb, "primary", "date", "xm"); gb1 = giveback(X, kc, "primary", "date", "xm")
        res[f"{w}_primary_gb"] = f"{gb0[0]:.1f}->{gb1[0]:.1f} (p90 {gb0[1]:.1f}->{gb1[1]:.1f})"
    rows.append(res)
R = pd.DataFrame(rows)

# ---------------------------------------------------------------- live week (journals, R after costs)
S = Path(sys.argv[2]); L = []
AC = {"p": "Primary", "od": "On Deck", "ta": "Testing A", "tb": "Testing B", "tc": "Testing C", "td": "Testing D", "te": "Testing E", "tf": "Testing F"}
for a, nm in AC.items():
    j = pd.read_sql("select date, strategy as setup, entry, stop, shares, pnl_adj, entry_time, exit_time from trades where run_id=1 and exit is not null",
                    sqlite3.connect(S / a / "journal.db"))
    j = j[j.date.between("2026-11-09", "2026-11-13")].copy(); j["account"] = nm
    j["r"] = j.pnl_adj / ((j.entry - j.stop).abs() * j.shares)
    to_m = lambda s: (pd.to_datetime(s, utc=True, format="mixed").dt.tz_convert("America/New_York")).pipe(lambda x: x.dt.hour * 60 + x.dt.minute + x.dt.second / 60)
    j["m"], j["xm"] = to_m(j.entry_time), to_m(j.exit_time); L.append(j.dropna(subset=["r"]))
L = pd.concat(L, ignore_index=True)
KL = run(L, "account", "date", "m", "xm")
live = []
for c in CFG:
    rem = KL["base"] & ~KL[c]; d = -L.r[rem]
    by = d.groupby(L.account[rem]).sum().round(1).to_dict(); ps = d.groupby(L.setup[rem]).sum()
    # note: base here is the live record itself (the live latch already acted); the live replay of the base latch itself
    live.append(dict(config=c, live_removed=int(rem.sum()), live_removed_pct=rem.sum() / len(L), live_d=d.sum(),
                     live_by_acct=by, live_set_better=int((ps > 0).sum()), live_set_worse=int((ps < 0).sum()),
                     live_worst=f"{ps.idxmin()} {ps.min():+.1f}" if len(ps) else "", live_best=f"{ps.idxmax()} {ps.max():+.1f}" if len(ps) else ""))
R = R.merge(pd.DataFrame(live), on="config")
R["pass"] = ((R.VALID_t >= BAR) & (R.VALID_xt >= 1.0) & (R.TRAIN_d > 0) & (R.TRAIN_x > 0) & (R.live_d >= 0)
             & (R.TRAIN_fam_harmed == "") & (R.VALID_fam_harmed == "") & (R.removed_pct <= 0.10))
R.round(3).to_csv(OUT / "g_results.csv", index=False)
pd.DataFrame(setrows).round(2).to_csv(OUT / "g_setups.csv", index=False); pd.DataFrame(famrows).round(2).to_csv(OUT / "g_families.csv", index=False)
P(f"base latch replay: live base keeps {KL['base'].mean():.1%} of live trades (live latch already acted; non-100% = timing/booking differences)")
P(f"bar {BAR:.2f}; configs 4 (lineage 40)")
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 80)
for _, r in R.iterrows():
    P(f"\n## {r.config}: removed {r.removed_pct:.1%} of base 2y trades | PASS={r['pass']}")
    for w in ("TRAIN", "VALID"):
        P(f"  {w}: delta {r[w+'_d']:+.0f}R (t {r[w+'_t']:.2f}) excess {r[w+'_x']:+.0f} (t {r[w+'_xt']:.2f}) removed {r[w+'_removed']} | setups better "
          f"{r[w+'_set_better']} ({r[w+'_set_better_R']:+.0f}R) worse {r[w+'_set_worse']} ({r[w+'_set_worse_R']:+.0f}R), worst {r[w+'_worst']} | "
          f"fam harmed [{r[w+'_fam_harmed']}] | Primary book delta {r[w+'_primary_d']:+.0f}R, give-back/day {r[w+'_primary_gb']}")
    P(f"  LIVE 11-09..13: removed {r.live_removed} ({r.live_removed_pct:.1%}) delta {r.live_d:+.1f}R by acct {r.live_by_acct} | setups better "
      f"{r.live_set_better} worse {r.live_set_worse} | best {r.live_best} | worst {r.live_worst}")
open(OUT / "g_out.txt", "w").write("\n".join(out) + "\n\nEducational only - not financial advice.\n")
