"""Item 6: correlation recheck (L3-fromopen vs RW3; L3-rsi5hi vs NS1), Primary-only and pooled, trade R and account R.
Usage: python item6_corr.py <worktree> <tmpdir with j/*.db>.  Educational only - not financial advice."""
import sys, json, sqlite3, itertools, numpy as np, pandas as pd
WT, TMP = sys.argv[1:3]
sys.path.insert(0, WT)
from mcf.costs import cost_r_lr8, _report_cfg
ACC = {"mcf-data": "primary", "mcf-data-testing": "testing", "mcf-data-testing2": "testing2", "mcf-data-explore1": "explore1",
       "mcf-data-livelab": "livelab", "mcf-data-testingd": "testingd", "mcf-data-testinge": "testinge",
       "mcf-data-testingf": "testingf", "mcf-data-gen": "gen", "mcf-data-graveyard": "graveyard"}
EQ = {"primary": 84883.40, "testing": 94680.51, "testing2": 92146.22, "explore1": 100266.73, "livelab": 100190.09,
      "testingd": 100188.97, "testinge": 99024.04, "testingf": 99974.85, "gen": 89646.45, "graveyard": 91417.92}
FAM = {"L3F": ["L3-gap-slope-fromopen-FD"], "RW3": ["RW3-gapdn-rsi5pop-flowsell-short-FD"],
       "L3R": ["L3-gap-slope-rsi5hi-FD"], "NS1": ["NS1-rsidip-rsi5pop-long", "NS1-rsidip-rsi5pop-long-FD"]}
INV = {s: f for f, ss in FAM.items() for s in ss}
T = []
for b, a in ACC.items():
    c = sqlite3.connect(f"file:{TMP}/j/{b}.db?mode=ro", uri=True)
    t = pd.read_sql("select id,symbol,strategy,side,date,entry_time,entry,stop,target,exit,exit_reason,shares,pnl,pnl_adj,r_multiple"
                    " from trades where run_id=1 and exit_time is not null and date>='2026-10-06'", c); c.close()
    t["acct"] = a; T.append(t)
t = pd.concat(T, ignore_index=True)
t = t[t.strategy.isin(INV)].reset_index(drop=True)
t["R"] = cost_r_lr8(t, _report_cfg()).astype(float).values
t = t[t.R.notna()].copy()
risk = (t.entry - t.stop).abs() * t.shares.abs()
t["usd"] = np.where(risk > 0, t.R * risk, t.pnl_adj)
eh = json.load(open(f"{WT}/docs/live/equity_history.json"))["accounts"]["primary"]
# Primary equity per day: prior close (to 11-05), else reconstructed back from 11-19 last equity with booked journal $
c = sqlite3.connect(f"file:{TMP}/j/mcf-data.db?mode=ro", uri=True)
book = pd.read_sql("select date, sum(pnl) p from trades where run_id=1 and exit_time is not null group by date", c).set_index("date").p; c.close()
def eqp(d):
    prev = [x for x in sorted(eh) if x < d]
    if d <= "2026-11-05" and prev: return eh[prev[-1]]["equity_close"]
    return 84883.40 - book[(book.index >= d) & (book.index < "2026-11-19")].sum()
t["eqv"] = np.where(t.acct == "primary", t.date.map(lambda d: eqp(d)), t.acct.map(EQ))
t["aR"] = t.usd / (t["eqv"] * 0.0025)
t["fam"] = t.strategy.map(INV)
et = pd.to_datetime(t.entry_time, utc=True, format="ISO8601").dt.tz_convert("America/New_York")
t["k"] = t.strategy + "|" + t.symbol + "|" + t.date + "|" + et.dt.strftime("%H%M")
def series(d, col): return d.groupby("date")[col].sum()
def corr(a, b, how):
    if how == "both": idx = a.index.intersection(b.index)
    else: idx = a.index.union(b.index)
    x, y = a.reindex(idx, fill_value=0.0), b.reindex(idx, fill_value=0.0)
    if len(idx) < 4: return len(idx), np.nan, np.nan
    return len(idx), x.corr(y), x.corr(y, method="spearman")
rows = []
for p1, p2 in [("L3F", "RW3"), ("L3R", "NS1")]:
    for view in ["primary", "pooled"]:
        d = t[t.acct == "primary"] if view == "primary" else t.drop_duplicates("k")
        for col, lab in [("R", "trade R"), ("aR", "account R")]:
            a, b = series(d[d.fam == p1], col), series(d[d.fam == p2], col)
            for how in ["both", "union"]:
                n, pr, sp = corr(a, b, how)
                rows.append(dict(pair=f"{p1}~{p2}", view=view, unit=lab, days=how, n_days=n, pearson=pr, spearman=sp,
                                 n1=int((d.fam == p1).sum()), n2=int((d.fam == p2).sum())))
    # pooled split: same-account vs cross-account series pairs (per-account daily series, union days, zero-filled)
    accs = sorted(t.acct.unique())
    S = {(f, a): t[(t.fam == f) & (t.acct == a)].groupby("date").R.sum() for f in (p1, p2) for a in accs}
    S = {k: v for k, v in S.items() if len(v) >= 3}
    same, cross = [], []
    for (f1, a1), (f2, a2) in itertools.product([k for k in S if k[0] == p1], [k for k in S if k[0] == p2]):
        n, pr, _ = corr(S[(f1, a1)], S[(f2, a2)], "both")
        if n >= 4 and pr == pr: (same if a1 == a2 else cross).append((pr, n, a1, a2))
    rows.append(dict(pair=f"{p1}~{p2}", view="per-account pairs", unit="trade R", days="both",
                     n_days=f"same {len(same)} / cross {len(cross)}",
                     pearson=f"same {np.mean([x[0] for x in same]) if same else float('nan'):.2f} / cross {np.mean([x[0] for x in cross]) if cross else float('nan'):.2f}",
                     spearman="; ".join(f"{a1}-{a2} {pr:.2f} (n {n})" for pr, n, a1, a2 in same)))
R = pd.DataFrame(rows)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 200)
print(R.to_string())
# context: Primary days each setup traded, days in Primary
for f in FAM:
    d = t[(t.fam == f)]
    print(f, "primary days", d[d.acct == "primary"].date.nunique(), d[d.acct == "primary"].date.min(), d[d.acct == "primary"].date.max(),
          "| pooled days", d.date.nunique(), "accts", d.acct.value_counts().to_dict())
# pooled excluding 11-19 and excluding best day
d = t.drop_duplicates("k")
for p1, p2 in [("L3F", "RW3"), ("L3R", "NS1")]:
    a, b = series(d[d.fam == p1], "R"), series(d[d.fam == p2], "R")
    idx = a.index.intersection(b.index)
    x, y = a.reindex(idx), b.reindex(idx)
    top = (x.abs() + y.abs()).idxmax()
    print(p1, p2, "pooled both-days without the largest-|R| day", top, round(x.drop(top).corr(y.drop(top)), 3),
          "| without 11-19", round(x.drop("2026-11-19", errors="ignore").corr(y.drop("2026-11-19", errors="ignore")), 3))
    print(pd.DataFrame({p1: x, p2: y}).round(1).T.to_string())
