"""ROT design 2026-11-11: the three bar options (strict / balanced / lenient), today's tier counts, and a walk-forward
check of the bars on the 26 live (paper) sessions 2026-10-06..2026-11-10.

Inputs: trades_all.parquet (inventory.py; every closed run_id=1 trade of all 7 accounts, R after costs),
inventory.csv (the 72 in-scope setups after the TEAM-6 switch), SPY 1-minute SIP bars 10-06..11-10 (read-only market data).
Metrics at a date D use ONLY trades on or before D (no look-ahead), merged by setup across accounts as the dashboard does.
Ex-market R is recomputed per trade (mcf.analytics.market_beta.spy_moves, same rule as BETA1, y = R after costs).
The t bar is multiple-testing aware: m = sqrt(2 ln N), N = setups screened at D with >= the option's min trades.
Walk-forward universe: every non-GEN setup with a live record (any account, incl. Primary and Graveyard), because the bar
is meant to rank all of them; GEN-* is out (owner rule: Gen keeps its own setups). Configurations tried: 3 bar options x
2 tiers = 6 rule sets in v1 (fixed before the walk-forward was read) + the same 6 with traded-session minimums in v2
(owner input 21:55 ET; minimums only) = 12 rule sets, plus 20 minimum pairs in minimums.py. All reported.
Usage: python bars.py <spy parquet>   Educational only - not financial advice."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from mcf.analytics import market_beta

T = pd.read_parquet(HERE / "trades_all.parquet")
T = T[~T.strategy.str.startswith("GEN-")].copy()
I = pd.read_csv(HERE / "inventory.csv")
spy = pd.read_parquet(sys.argv[1])
for c in ("entry_time", "exit_time"):
    T[c] = pd.to_datetime(T[c], utc=True, format="mixed").dt.tz_convert("America/New_York")
T["x"] = market_beta.spy_moves(T, spy)
DATES = sorted(T[T.acct == "primary"].date.unique())
BT = I.set_index("setup").bt2y.to_dict()
PV = pd.read_csv(ROOT / "research/preval_1107/all_setups.csv").set_index("setup").bt2y.to_dict()
for k, v in PV.items():
    BT.setdefault(k, v)

# ---- the bar options (fixed before the walk-forward was read) ---------------------------------------------------
# tier "cand" = Candidate (earns a Testing 1 / Testing 2 seat); "deck" = On deck for Primary (owner decision)
# v1 (first draft, results kept in bars_out_v1.json / tiers_today_v1.csv): cand n/ses 40/10, 25/8, 15/5; deck 80/15, 60/12, 40/10.
# v2 (this version, after the owner's 21:55 input "organize by traded sessions, then trade count"): ses = TRADED sessions
# (>= 1 closed live trade) is the primary minimum, trades the secondary; minimums from minimums.py (20 pairs). Only the
# minimums changed between v1 and v2; every other threshold is the same.
BARS = {
    "strict":   {"cand": dict(ses=10, n=50, shrunk=0.05, exbest=0.0, share=0.50, tm=0.35, exmkt=0.0, last5=-0.10, bt=-0.05),
                 "deck": dict(ses=20, n=80, shrunk=0.10, exbest=0.05, share=0.35, tm=0.70, exmkt=0.0, last5=0.0, bt=0.0)},
    "balanced": {"cand": dict(ses=8, n=30, shrunk=0.03, exbest=0.0, share=0.60, tm=0.25, exmkt=0.0, last5=-0.15, bt=-0.10),
                 "deck": dict(ses=15, n=60, shrunk=0.07, exbest=0.03, share=0.50, tm=0.50, exmkt=0.0, last5=-0.05, bt=-0.05)},
    "lenient":  {"cand": dict(ses=5, n=15, shrunk=0.0, exbest=0.0, share=0.75, tm=0.0, exmkt=None, last5=-0.25, bt=-0.15),
                 "deck": dict(ses=10, n=40, shrunk=0.05, exbest=0.0, share=0.60, tm=0.35, exmkt=0.0, last5=-0.10, bt=-0.10)},
}
# down-moves (all options): Graveyard PROPOSAL when n >= 40 and shrunk <= -0.10 and avg w/o best day < 0 and last-5 < 0
GY = dict(n=40, shrunk=-0.10)


def metrics(g):
    n = len(g); day = g.groupby("date").R.sum(); k = len(day); tot = g.R.sum()
    bd = day.idxmax(); bn = int((g.date == bd).sum())
    exb = (tot - day.max()) / (n - bn) if k >= 2 and n > bn else np.nan
    share = day.max() / tot if tot > 0 and k >= 2 and day.max() > 0 else (np.nan if tot <= 0 else 1.0)
    tday = day.mean() / (day.std(ddof=1) / k ** .5) if k > 2 and day.std(ddof=1) > 0 else np.nan
    ex = market_beta.fit(market_beta.sums(g.x, g.R)).get("exmkt_r")
    l5 = g[g.date.isin(sorted(g.date.unique())[-5:])].R.mean()
    return dict(n=n, ses=k, avg=tot / n, shrunk=tot / (n + 20), exbest=exb, share=share, t=tday,
                exmkt=np.nan if ex is None else ex, last5=l5)


def passes(m, b, N, bt):
    tb = b["tm"] * (2 * np.log(max(N, 2))) ** .5
    ok = (m["n"] >= b["n"] and m["ses"] >= b["ses"] and m["shrunk"] >= b["shrunk"]
          and (m["exbest"] == m["exbest"] and m["exbest"] > b["exbest"]) and (m["share"] != m["share"] or m["share"] <= b["share"])
          and (b["tm"] == 0 or (m["t"] == m["t"] and m["t"] >= tb)) and m["last5"] > b["last5"]
          and (bt != bt or bt >= b["bt"]))
    if b["exmkt"] is not None:
        ok = ok and m["exmkt"] == m["exmkt"] and m["exmkt"] > b["exmkt"]
    return bool(ok)


def tier(m, opt, N, bt):
    if passes(m, BARS[opt]["deck"], N, bt): return "deck"
    if passes(m, BARS[opt]["cand"], N, bt): return "cand"
    if m["n"] >= GY["n"] and m["shrunk"] <= GY["shrunk"] and (m["exbest"] < 0) and m["last5"] < 0: return "gy?"
    return "pool"


def table(upto, setups=None):
    g = T[T.date <= upto]
    M = {s: metrics(x) for s, x in g.groupby("strategy") if setups is None or s in setups}
    return M


out = {"note": "Educational only - not financial advice. Paper (live) records; R after costs.", "bars": BARS, "gy": GY}
# ---- today's counts (in-scope setups only) ------------------------------------------------------------------------
scope = set(I.setup)
Mall = table(DATES[-1])
today = {}
for opt in BARS:
    N = {k: sum(1 for m in Mall.values() if m["n"] >= BARS[opt][k]["n"]) for k in ("cand", "deck")}
    rows = {}
    for s in sorted(scope):
        m = Mall.get(s)
        rows[s] = "pool (no trades)" if m is None else tier(m, opt, N["cand"] if m["n"] < BARS[opt]["deck"]["n"] else N["deck"], BT.get(s, np.nan))
    today[opt] = rows
TOD = pd.DataFrame(today); TOD.index.name = "setup"
TOD.to_csv(HERE / "tiers_today.csv")
print("today (in scope, after TEAM-6):")
for opt in BARS:
    print(" ", opt, TOD[opt].replace("pool (no trades)", "pool").value_counts().to_dict(),
          "| cand:", sorted(TOD.index[TOD[opt] == "cand"]), "| deck:", sorted(TOD.index[TOD[opt] == "deck"]))
# Primary TEAM-6 setups for reference: would today's Primary pass its own bar?
P6 = ["L3-gap-slope-fromopen-FD", "NS5-sma50-flush-oversold-long", "RW3-gapdn-rsi5pop-flowsell-short-FD",
      "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "ST7-rsi50dn-long-pm-t1s1-FD", "NM-ETF-late-dip-di-long"]
ref = {}
for s in P6:
    m = Mall.get(s)
    ref[s] = {opt: tier(m, opt, sum(1 for x in Mall.values() if x["n"] >= BARS[opt]["deck"]["n"]), BT.get(s, np.nan)) for opt in BARS}
    ref[s].update({k: (round(v, 3) if isinstance(v, float) else v) for k, v in m.items()})
print("TEAM-6 Primary vs the bars:"); print(pd.DataFrame(ref).T.to_string())
out["today_counts"] = {o: TOD[o].replace("pool (no trades)", "pool").value_counts().to_dict() for o in BARS}
out["primary_team6_vs_bars"] = ref

# ---- walk-forward ---------------------------------------------------------------------------------------------------
CK = list(range(9, len(DATES) - 2, 2))   # after session 10, 12, ... 24 (re-tier every 2 sessions)
wf = []
for i in CK:
    D = DATES[i]; nxt = DATES[i + 1: i + 6]   # next up-to-5 sessions
    M = table(D)
    for opt in BARS:
        Nc = sum(1 for m in M.values() if m["n"] >= BARS[opt]["cand"]["n"])
        Nd = sum(1 for m in M.values() if m["n"] >= BARS[opt]["deck"]["n"])
        for s, m in M.items():
            tr = tier(m, opt, Nd if m["n"] >= BARS[opt]["deck"]["n"] else Nc, BT.get(s, np.nan))
            f = T[(T.strategy == s) & T.date.isin(nxt)]
            fa = T[(T.strategy == s) & (T.date > D)]
            wf.append(dict(D=D, k=i + 1, opt=opt, setup=s, tier=tr, n=m["n"], f5_n=len(f), f5_R=f.R.sum(), fall_n=len(fa), fall_R=fa.R.sum()))
W = pd.DataFrame(wf); W.to_csv(HERE / "walkforward_rows.csv", index=False, float_format="%.4f")


def summ(x):
    n = x.f5_n.sum(); a = x.fall_n.sum()
    per = x[x.fall_n > 0]
    return pd.Series(dict(setup_dates=len(x), uniq=x.setup.nunique(), next5_trades=int(n), next5_avgR=x.f5_R.sum() / n if n else np.nan,
                          after_trades=int(a), after_avgR=x.fall_R.sum() / a if a else np.nan,
                          share_setups_pos_after=(per.fall_R > 0).mean() if len(per) else np.nan))


S = W.groupby(["opt", "tier"]).apply(summ, include_groups=False)
print("\nwalk-forward (checkpoints after sessions", [k + 1 for k in CK], "): forward R after costs of setups by tier at D")
print(S.round(3).to_string())
out["walkforward"] = {f"{a}|{b}": {k: (None if v != v else round(float(v), 4)) for k, v in r.items()} for (a, b), r in S.iterrows()}
# first-time-to-tier (time to promotion) and false promotions (deck setups whose next-5 R < 0)
ttp = {}
for opt in BARS:
    w = W[W.opt == opt]
    d = w[w.tier == "deck"].groupby("setup").k.min()
    c = w[w.tier.isin(["cand", "deck"])].groupby("setup").k.min()
    fd = w[(w.tier == "deck") & (w.f5_n > 0)]
    ttp[opt] = dict(deck_setups=sorted(d.index), deck_first_session=d.to_dict(), cand_setups=int(len(c)),
                    median_session_first_cand=float(c.median()) if len(c) else None,
                    deck_checks=int(len(fd)), deck_checks_next5_negative=int((fd.f5_R < 0).sum()))
print("\ntime to tier / false-promotion count:"); print(json.dumps(ttp, indent=1, default=str))
out["time_to_tier"] = ttp

# ---- past real moves: tier at the move date (records up to the session before), and R after -----------------------
MOVES = [("RW3-gapdn-rsi5pop-flowsell-short-FD", "2026-10-16", "promote T1->P"), ("RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "2026-10-16", "promote T1->P"),
         ("MF2-open-rsimidhi-flowsell-FD", "2026-10-21", "promote T1->P (back to T1 11-11)"), ("MF4-h40-open-flowsell-FD", "2026-10-21", "promote T1->P (back to T1 11-11)"),
         ("NS3-failed-vwap-reclaim-short-FD", "2026-10-21", "promote T1->P (later GY)"),
         ("L3-gap-slope-fromopen-FD", "2026-10-22", "promote T1->P"), ("CWT14-failbrk-pdl-p10-lowvol-long", "2026-10-22", "promote T2->P (demoted 10-28)"),
         ("ST7-rsi50dn-long-pm-t1s1-FD", "2026-10-26", "promote T1->P"), ("CWT13-vwapstretch-z05-long", "2026-10-26", "promote T2->P (demoted 10-27)"),
         ("L3-gap-slope-rsi5hi-FD", "2026-10-30", "promote T2->P (back to T1 11-11)"),
         ("MF3-open-flowsell-rsi5hi", "2026-10-20", "demote P->T1"), ("MF1-945-flowsell-vwapup", "2026-10-26", "demote P->T1"),
         ("NS4-pm-vwap-reclaim-oversold-short", "2026-10-28", "demote P->T2"), ("MF2-open-rsimidhi-flowsell", "2026-10-28", "demote P->T2"),
         ("RW3S-gapdn-flowsell-short-FD", "2026-11-11", "proposed T2->GY")]
pm = []
for s, d, what in MOVES:
    prev = [x for x in DATES if x < d]
    D = prev[-1]; M = table(D); m = M.get(s)
    after = T[(T.strategy == s) & (T.date >= d)]
    row = dict(setup=s, move=what, date=d, n_before=m["n"] if m else 0,
               avg_before=round(m["avg"], 3) if m else None, t_before=round(m["t"], 2) if m and m["t"] == m["t"] else None,
               exbest_before=round(m["exbest"], 3) if m and m["exbest"] == m["exbest"] else None,
               n_after=len(after), avg_after=round(after.R.mean(), 3) if len(after) else None)
    for opt in BARS:
        if m is None: row[opt] = "pool (no trades)"; continue
        Nd = sum(1 for x in M.values() if x["n"] >= BARS[opt]["deck"]["n"])
        row[opt] = tier(m, opt, Nd, BT.get(s, np.nan))
    pm.append(row)
PM = pd.DataFrame(pm); print("\npast moves vs the bars:"); print(PM.to_string(index=False))
PM.to_csv(HERE / "past_moves.csv", index=False)
out["past_moves"] = pm
json.dump(out, open(HERE / "bars_out.json", "w"), indent=1, default=lambda o: None if o != o else (float(o) if isinstance(o, (np.floating,)) else int(o) if isinstance(o, np.integer) else str(o)))
