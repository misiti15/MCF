"""ROT design 2026-11-11: inventory of every setup in Testing 1 / Testing 2 / Explore 1 / Live Lab AFTER the TEAM-6 switch
(owner "Team yes" 2026-11-10: MF2-FD, MF4-FD, L3-rsi5hi-FD -> Testing 1; MF4, NS1 -> Testing 2; NM-ETF Live Lab -> Primary).

Live (paper) record = every closed run_id=1 trade of the setup in ANY of the 7 accounts, merged by setup id as the dashboard
does. R after costs = pnl_adj / (|entry - stop| x shares). Ex-market R = scorecard BETA1 sums merged over all accounts.
2y = bt_lab1104 two-year lab (open part, locked block 2024-11..2025-02 out, to 2026-10-05), else preval_1107 fallbacks.
Primary-rules proxy = the record with Primary's -2R per-setup daily stop applied after the fact (a trade is dropped when the
setup's closed R that day was <= -2 before its entry). It ignores lot size and crowding: the Team engine gives the real one.

Usage: python inventory.py <scratch with p/t1/t2/gy/gen/ex1/ll journal.db + reports/scorecard.json>
Writes inventory.csv, trades_all.parquet. Educational only - not financial advice."""
import sys, json, glob, sqlite3
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from mcf.analytics import market_beta
from mcf.report.scorecard import _expected
from mcf import setup_names

S = Path(sys.argv[1])
AC = {"p": "primary", "t1": "testing", "t2": "testing2", "gy": "graveyard", "gen": "gen", "ex1": "explore1", "ll": "livelab"}
A = json.load(open(ROOT / "docs/live/assignments.json"))["accounts"]
# post-switch homes (TEAM-6, effective 2026-11-11)
HOME = {}
for acct in ("testing", "testing2", "explore1", "livelab"):
    for s in A[acct]:
        HOME.setdefault(s, []).append(acct)
HOME.pop("NM-ETF-late-dip-di-long", None)
for s in ("MF2-open-rsimidhi-flowsell-FD", "MF4-h40-open-flowsell-FD", "L3-gap-slope-rsi5hi-FD"):
    HOME[s] = ["testing"]
for s in ("MF4-h40-open-flowsell", "NS1-rsidip-rsi5pop-long"):
    HOME[s] = ["testing2"]
EXPRIM = {"MF2-open-rsimidhi-flowsell-FD", "MF4-h40-open-flowsell-FD", "L3-gap-slope-rsi5hi-FD", "MF4-h40-open-flowsell",
          "NS1-rsidip-rsi5pop-long", "MF1-945-flowsell-vwapup", "MF3-open-flowsell-rsi5hi", "CWT13-vwapstretch-z05-long",
          "CWT14-failbrk-pdl-p10-lowvol-long", "NS4-pm-vwap-reclaim-oversold-short"}

rows = []
for a, lab in AC.items():
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select date, strategy, side, entry_time, exit_time, entry, stop, shares, pnl, pnl_adj from trades "
                    "where run_id=1 and exit is not null", c)
    t["acct"] = lab; rows.append(t)
T = pd.concat(rows, ignore_index=True)
T["pnl_adj"] = T.pnl_adj.fillna(T.pnl)
T["risk"] = (T.entry - T.stop).abs() * T.shares
T = T[T.risk > 0].copy(); T["R"] = T.pnl_adj / T.risk
T["date"] = T.date.astype(str)
T.to_parquet(HERE / "trades_all.parquet")
DATES = sorted(T[T.acct == "primary"].date.unique())  # 26 live sessions 10-06..11-10

# ex-market
parts = {}
for a in AC:
    for r in json.load(open(S / a / "reports" / "scorecard.json"))["leaderboard"]:
        if r.get("mkt_n"):
            parts.setdefault(r["setup"], []).append({k: r[k] for k in market_beta.KEYS})
EX = {k: (market_beta.fit(market_beta.merge(v)) or {}) for k, v in parts.items()}
# playing time (cumulative, per account, home accounts only)
PT = {}
for a, lab in AC.items():
    pt = (json.load(open(S / a / "reports" / "scorecard.json")).get("playing_time") or {}).get("cumulative") or {}
    for r in pt.get("setups", []):
        PT.setdefault(r["setup"], {})[lab] = r
# 2y
LOCK = ("2024-11-01", "2025-02-28")
lab2 = pd.concat(pd.read_parquet(p, columns=["setup", "date", "r"]) for p in
                 sorted(glob.glob("/home/user/MCF/research/history2y/data/bt_lab1104/sig_*.parquet")))
lab2["date"] = lab2.date.astype(str); lab2 = lab2[~lab2.date.between(*LOCK) & (lab2.date <= "2026-10-05")]
BT2 = lab2.groupby("setup").r.agg(["mean", "size"])
PV = pd.read_csv(ROOT / "research/preval_1107/all_setups.csv").set_index("setup")
EXP = _expected()


def bt2y(s):
    if s in BT2.index: return BT2.loc[s, "mean"], int(BT2.loc[s, "size"]), "2y lab"
    b = s[:-3] if s.endswith("-FD") else None
    if s in PV.index and PV.loc[s, "bt2y"] == PV.loc[s, "bt2y"]: return PV.loc[s, "bt2y"], PV.loc[s, "bt2y_n"], "preval_1107"
    if EXP.get(s) is not None: return EXP[s], "", "screen"
    if b and b in BT2.index: return BT2.loc[b, "mean"], int(BT2.loc[b, "size"]), "2y lab (base)"
    return np.nan, "", ""


def latch(g):
    """Primary -2R per-setup daily stop applied after the fact."""
    keep = []
    for d, x in g.sort_values("entry_time").groupby("date"):
        x = x.sort_values("entry_time")
        for i, r in x.iterrows():
            closed = x[(x.exit_time < r.entry_time)].R.sum()
            keep.append(i if closed > -2 else None)
    k = [i for i in keep if i is not None]
    return g.loc[k]


def stats(g, dates=None):
    n = len(g)
    if not n: return dict(trades=0, sessions=0)
    day = g.groupby("date").R.sum(); k = len(day); tot = g.R.sum()
    bd = day.idxmax(); bn = int((g.date == bd).sum())
    exb = (tot - day.max()) / (n - bn) if k >= 2 and n > bn else np.nan
    share = day.max() / tot if tot > 0 and k >= 2 and day.max() > 0 else np.nan
    tday = day.mean() / (day.std(ddof=1) / k ** .5) if k > 2 and day.std(ddof=1) > 0 else np.nan
    return dict(trades=n, sessions=k, avgR=tot / n, totR=tot, shrunk=tot / n * n / (n + 20), exbest=exb, best_share=share,
                t_day=tday, green=(day > 0).mean())


out = []
for s, homes in sorted(HOME.items()):
    g = T[T.strategy == s]
    st = stats(g)
    last5d = sorted(g.date.unique())[-5:]
    l5 = g[g.date.isin(last5d)]
    lt = latch(g) if len(g) else g
    lst = stats(lt)
    e = EX.get(s) or {}
    b, bn, bsrc = bt2y(s)
    pt = PT.get(s, {})
    sig = sum(v.get("signals", 0) for v in pt.values()); ses = sum(v.get("sessions", 0) for v in pt.values())
    skip = {}
    for v in pt.values():
        for kk, vv in (v.get("skipped") or {}).items(): skip[kk] = skip.get(kk, 0) + vv
    since = {}
    out.append(dict(setup=s, name=setup_names.name(s), home="+".join({"testing": "T1", "testing2": "T2", "explore1": "EX1",
                    "livelab": "LL"}[h] for h in homes), ex_primary=s in EXPRIM,
                    side=("short" if (g.side.astype(float) < 0).all() else "long" if (g.side.astype(float) > 0).all() else "both") if len(g) else ("short" if "short" in s else "long" if "long" in s else "?"),
                    trades=st.get("trades", 0), sessions=st.get("sessions", 0), avgR=st.get("avgR"), shrunk=st.get("shrunk"),
                    exbest=st.get("exbest"), best_share=st.get("best_share"), t_day=st.get("t_day"), green=st.get("green"),
                    totR=st.get("totR"), exmkt=e.get("exmkt_r"), beta=e.get("beta"),
                    last5_n=len(l5), last5_avgR=l5.R.mean() if len(l5) else np.nan, last5_sumR=l5.R.sum() if len(l5) else np.nan,
                    bt2y=b, bt2y_n=bn, bt2y_src=bsrc,
                    prim_rules_avgR=lst.get("avgR"), prim_rules_trades=lst.get("trades", 0),
                    pt_sessions=ses, pt_signals_per_session=sig / ses if ses else np.nan,
                    pt_entries_per_session=sum(v.get("entries", 0) for v in pt.values()) / ses if ses else np.nan,
                    pt_expected_per_day=max([v.get("expected_per_day") or 0 for v in pt.values()] or [np.nan]),
                    pt_slots_full_share=(skip.get("slots_full", 0) + skip.get("setup_cap", 0)) / sig if sig else np.nan,
                    pt_held_share=skip.get("held_by_other", 0) / sig if sig else np.nan,
                    pt_verdict="/".join(sorted({v.get("verdict") or "" for v in pt.values()} - {""})),
                    accts_traded="+".join(sorted(set(g.acct))) if len(g) else ""))
I = pd.DataFrame(out)
I.to_csv(HERE / "inventory.csv", index=False, float_format="%.4f")
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
print("live sessions:", len(DATES), DATES[0], DATES[-1], "| setups in scope:", len(I), I.home.value_counts().to_dict())
print(I[["setup", "home", "trades", "sessions", "avgR", "shrunk", "exbest", "best_share", "t_day", "exmkt", "last5_avgR", "bt2y",
         "prim_rules_avgR", "pt_signals_per_session", "pt_slots_full_share", "pt_verdict"]].round(3).to_string(index=False))
