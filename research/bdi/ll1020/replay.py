"""Replay 16 per-setup daily loss-limit rules (pre-declared in NOTES.md) on the live paper trades of 2026-10-12..10-21 (10-21 + Graveyard added by nightly1021).
Candidates = journal run-1 trades per account (+ from 2026-10-20 on the signals the -2R limit blocked, priced by the
journal's what-if run 2 less the production cost model, as nightly1020/caps.py). Trips on journal r_multiple
(as runner.py does), scores net R after costs. Writes candidates.csv, setup_days.csv, replay_out.md.
Usage: python replay.py <scratch>   (expects <scratch>/<acct>/journal.db from the mcf-data* branches)
Educational only - not financial advice."""
import sys, sqlite3
from pathlib import Path
import numpy as np, pandas as pd

S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; TZ = "America/New_York"
DAYS = ["2026-10-12", "2026-10-13", "2026-10-14", "2026-10-15", "2026-10-16", "2026-10-19", "2026-10-20", "2026-10-21"]  # 10-21 added by nightly1021 (LL-1.5 monitor)
ACCTS = ["t1", "t2", "gen", "p", "gy"]; LIM = ["t1", "t2", "gen", "gy"]   # gy = Graveyard (from 2026-10-21)
ts = lambda s: pd.to_datetime(s, utc=True, format="mixed").dt.tz_convert(TZ)

rows, hist = [], {}
for a in ACCTS:
    c = sqlite3.connect(S / a / "journal.db")
    h = pd.read_sql("select date, strategy from trades where run_id=1", c)
    hist[a] = h.groupby(["strategy", "date"]).size().rename("n").reset_index()
    t = pd.read_sql("select * from trades where run_id=1 and date between ? and ?", c, params=(DAYS[0], DAYS[-1]))
    t["src"] = "live"
    risk = (t.entry - t.stop).abs() * t.shares
    t["netR"] = np.where(risk > 0, t.pnl_adj / risk, np.nan)
    w = pd.read_sql("select * from trades where run_id=2 and date >= '2026-10-20'", c)   # blocked signals are priced from 10-20 on
    w = w[w.meta.fillna("").str.contains("why=setup daily loss limit")].copy()
    if len(w):
        R = (w.entry - w.stop).abs()
        cps = (0.01 + w.entry * 1e-4) + np.where(w.exit_reason == "target", 0.0, 0.01 + w.exit * 1e-4) \
            + np.where(w.exit_reason == "stop", 0.02, 0.0)
        w["netR"] = w.r_multiple - np.where(R > 0, cps / R, 0.0)
        w["src"] = "whatif"
    x = pd.concat([t, w], ignore_index=True)
    x["acct"] = a
    rows.append(x[["acct", "date", "strategy", "symbol", "side", "src", "entry_time", "exit_time", "r_multiple", "netR", "pnl_adj"]])
C = pd.concat(rows, ignore_index=True)
bad = C.netR.isna().sum()
C["netR"] = C.netR.fillna(C.r_multiple)          # zero-risk rows (none expected) fall back to journal R
C["nt"], C["et"] = ts(C.entry_time), ts(C.exit_time)
C["et"] = C.et.fillna(pd.Timestamp("2100-01-01", tz=TZ))
C = C.sort_values(["acct", "date", "strategy", "nt"]).reset_index(drop=True)
C.drop(columns=["nt", "et"]).to_csv(OUT / "candidates.csv", index=False)


def md(df, index=True):
    """minimal markdown table (no tabulate dependency)"""
    df = df.reset_index() if index else df
    f = lambda v: f"{v:+.2f}" if isinstance(v, (float, np.floating)) else str(v)
    return "\n".join(["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
                     + ["| " + " | ".join(f(v) for v in r) + " |" for r in df.itertuples(index=False)])


def avg_tpd(a, st, day):
    h = hist[a]; h = h[(h.strategy == st) & (h.date < day)].sort_values("date").tail(10)
    return float(h.n.mean()) if len(h) else 0.0


def realized(tk, t):
    """cum realized r_multiple path of taken trades exited before t (sorted by exit) -> (now, hwm, first time <= -2)."""
    d = sorted((e, r) for (_, e, r) in tk if e < t)
    cum, hwm, t2 = 0.0, 0.0, None
    for e, r in d:
        cum += r; hwm = max(hwm, cum)
        if t2 is None and cum <= -2:
            t2 = e
    return cum, hwm, t2


def make(rule, X=None):
    def f(t, tk, ctx):
        cum, hwm, t2 = realized(tk, t)
        if rule == "none":
            return True
        if rule == "fixed":
            return cum > -X
        if rule == "openrisk":
            return cum - sum(1 for (n, e, _) in tk if n <= t < e) > -X
        if rule == "pause":
            if t2 is None:
                return True
            if t < t2 + pd.Timedelta(minutes=X):
                return False
            return cum > -3
        if rule == "freq_sqrt":
            return cum > -max(2.0, 0.5 * np.sqrt(ctx["tpd"]))
        if rule == "freq_step":
            return cum > -(3.0 if ctx["tpd"] >= 20 else 2.0)
        if rule == "giveback":
            lvl = hwm - 3 if X is None else max(hwm - 3, X)
            return cum > lvl
        if rule == "tod11":
            return t.hour < 11 or cum > -2
    return f


RULES = {"none": make("none")}
for X in (1.5, 2, 2.25, 2.5, 3, 4):
    RULES[f"fixed{X:g}"] = make("fixed", X)
RULES["openrisk2"] = make("openrisk", 2); RULES["openrisk3"] = make("openrisk", 3)
RULES["pause60"] = make("pause", 60); RULES["pause30"] = make("pause", 30)
RULES["freq_sqrt"] = make("freq_sqrt"); RULES["freq_step"] = make("freq_step")
RULES["giveback3"] = make("giveback"); RULES["giveback3_floor2"] = make("giveback", -2)
RULES["tod11"] = make("tod11")
assert len(RULES) == 16

recs = []
for (a, d, st), g in C.groupby(["acct", "date", "strategy"], sort=False):
    ctx = {"tpd": avg_tpd(a, st, d)}
    for name, f in RULES.items():
        tk, net, blk, nw = [], 0.0, 0, 0
        for r in g.itertuples():
            if f(r.nt, tk, ctx):
                tk.append((r.nt, r.et, r.r_multiple)); net += r.netR; nw += r.src == "whatif"
            else:
                blk += 1
        recs.append((name, a, d, st, len(g), len(tk), blk, nw, net, ctx["tpd"]))
SD = pd.DataFrame(recs, columns=["rule", "acct", "date", "strategy", "cand", "taken", "blocked", "whatif_taken", "netR", "tpd"])
SD.to_csv(OUT / "setup_days.csv", index=False)

base = SD[SD.rule == "none"].set_index(["acct", "date", "strategy"]).netR
cur = SD[SD.rule == "fixed2"].set_index(["acct", "date", "strategy"]).netR
o = []; P = o.append
P("# Loss-limit replay output (generated by replay.py)\n")
P(f"Candidates: {len(C)} trades ({(C.src == 'whatif').sum()} priced 10-20 blocked signals); setup-days {len(base)}; "
  f"rows without $risk: {bad}. Total = t1 + t2 + gen (accounts with the limit); p (Primary) has no limit, info only.\n")
# sanity: fixed2 on 10-20 should reproduce the live set
z = SD[(SD.rule == "fixed2") & (SD.date == "2026-10-20") & SD.acct.isin(LIM)]
P(f"Sanity, fixed2 on 10-20 (should be ~live): whatif rows taken {int(z.whatif_taken.sum())} of {(C[(C.date=='2026-10-20')].src=='whatif').sum()}, "
  f"live rows blocked {int((z.cand - z.taken - (C[C.date=='2026-10-20'].groupby(['acct','strategy']).src.apply(lambda s:(s=='whatif').sum()).reindex(list(zip(z.acct,z.strategy))).values - z.whatif_taken)).sum())}\n")

L = SD[SD.acct.isin(LIM)]
# random-blocking controls (rule 6): expected delta if the same number of entries were dropped at random
#  ctrlA: at the account's average net R per candidate over all 7 days (no knowledge of the day)
#  ctrlB: at that setup-day's own average (knows the day is bad; tests whether *when* the rule stops adds anything)
mA = C[C.acct.isin(LIM)].groupby("acct").netR.mean()
mB = C.groupby(["acct", "date", "strategy"]).netR.mean()
nb = base.reindex(mB.index)
BAD = set(nb[nb <= -3].index) & set(L[L.rule == "none"].set_index(["acct", "date", "strategy"]).index)
GOOD = set(nb[nb > 0].index) & set(L[L.rule == "none"].set_index(["acct", "date", "strategy"]).index)
tab = []
for name in RULES:
    s = L[L.rule == name].set_index(["acct", "date", "strategy"])
    dlt = s.netR - base.reindex(s.index)
    mf = s.netR.get(("t1", "2026-10-20", "MF1-945-flowsell-vwapup-FD"), np.nan)
    pa = SD[(SD.rule == name) & (SD.acct == "p")].netR.sum()
    tab.append(dict(rule=name, total=s.netR.sum(), t1=s.xs("t1").netR.sum(), t2=s.xs("t2").netR.sum(), gen=s.xs("gen").netR.sum(), gy=s.xs("gy").netR.sum() if "gy" in s.index.get_level_values(0) else 0.0,
                    vs_none=dlt.sum(), saved=dlt[dlt > 0].sum(), forgone=dlt[dlt < 0].sum(),
                    stopped=int((s.blocked > 0).sum()), blocked=int(s.blocked.sum()), worst=s.netR.min(),
                    sd_lt_m3=int((s.netR <= -3).sum()), mf1_1020=mf, primary_info=pa,
                    ctrlA=-(s.blocked * mA.reindex(s.index.get_level_values(0)).values).sum(),
                    ctrlB=-(s.blocked * mB.reindex(s.index).values).sum(),
                    bad_hit=f"{sum(1 for i in BAD if s.blocked.get(i, 0) > 0)}/{len(BAD)}",
                    bad_saved=dlt[dlt.index.isin(list(BAD))].sum(),
                    good_cut=f"{sum(1 for i in GOOD if s.blocked.get(i, 0) > 0)}/{len(GOOD)}",
                    good_lost=dlt[dlt.index.isin(list(GOOD))].sum()))
TB = pd.DataFrame(tab).set_index("rule")
P("## All 16 rules (net R after costs, all sessions in DAYS)\n")
P(TB.pipe(md))
P("\nsaved = sum of setup-day improvements vs none; forgone = sum of setup-day losses vs none; stopped = setup-days with >=1 "
  "blocked entry; sd_lt_m3 = setup-days ending <= -3R; mf1_1020 = T1 MF1-945-flowsell-vwapup-FD on 10-20.\n"
  "ctrlA = expected vs_none if the same number of entries were dropped at random at the account's 7-day mean net R per "
  "trade; ctrlB = same at the setup-day's own mean. bad_hit = bad setup-days (none <= -3R) with >= 1 block; bad_saved = "
  "R saved on them; good_cut / good_lost = same for setup-days that ended positive without a limit.\n")

PD = L.groupby(["rule", "date"]).netR.sum().unstack().reindex(list(RULES))
P("## Per day (t1+t2+gen, + gy from 10-21)\n"); P(PD.pipe(md))
P("\n## Per day, delta vs none\n"); P((PD - PD.loc["none"]).pipe(md))
P("\n## Per day, delta vs fixed2 (current rule)\n"); D2 = PD - PD.loc["fixed2"]; P(D2.pipe(md))
st = pd.DataFrame({"mean_day": D2.mean(axis=1), "se": D2.std(axis=1, ddof=1) / np.sqrt(D2.shape[1]),
                   "days_better": (D2 > 0).sum(axis=1), "days_worse": (D2 < 0).sum(axis=1)})
st["t"] = st.mean_day / st.se
P("\n## Day-clustered delta vs fixed2 (n = len(DAYS) days)\n"); P(st.pipe(md))

P("\n## Leave-one-day-out: best rule (by total) with each day dropped, and rank of selected rules\n")
lo = []
for d in DAYS:
    tot = PD.drop(columns=d).sum(axis=1).sort_values(ascending=False)
    rk = {r: int(list(tot.index).index(r)) + 1 for r in ("none", "fixed2", "fixed2.25", "fixed3", "openrisk3", "pause60", "freq_step", "tod11")}
    lo.append(dict(dropped=d, best=tot.index[0], best_R=tot.iloc[0], second=tot.index[1], **{f"rank_{k}": v for k, v in rk.items()}))
P(pd.DataFrame(lo).pipe(md, index=False))
P("\nSame, excluding the two open-risk rules (they drop ~70% of all entries, see ctrlA):\n")
lo2 = []
for d in DAYS:
    tot = PD.drop(index=["openrisk2", "openrisk3"]).drop(columns=d).sum(axis=1).sort_values(ascending=False)
    lo2.append(dict(dropped=d, best=tot.index[0], second=tot.index[1], third=tot.index[2],
                    rank_fixed2=int(list(tot.index).index("fixed2")) + 1, rank_fixed2_25=int(list(tot.index).index("fixed2.25")) + 1))
P(pd.DataFrame(lo2).pipe(md, index=False))
P("\n## Primary (no per-setup limit configured; info only), total by rule\n")
P(SD[SD.acct == "p"].groupby("rule").netR.sum().reindex(list(RULES)).pipe(md))
P("\n## Setup-days the current rule (fixed2) changes, largest effects\n")
dd = (cur - base).rename("delta").reset_index(); dd = dd[dd.acct.isin(LIM) & (dd.delta != 0)].sort_values("delta")
dd["none_R"] = base.reindex(list(zip(dd.acct, dd.date, dd.strategy))).values
P(dd.head(10).pipe(md, index=False)); P(""); P(dd.tail(10).pipe(md, index=False))
P("\nEducational only - not financial advice.")
(OUT / "replay_out.md").write_text("\n".join(o) + "\n")
print("\n".join(o))
