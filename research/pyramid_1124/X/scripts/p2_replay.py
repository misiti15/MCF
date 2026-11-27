import pandas as pd, numpy as np, hashlib
X = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/X/"
a = pd.read_parquet(X + "overlap_annot.parquet")
ROSTER = ["L3-gap-slope-fromopen-FD", "NM-ETF-late-dip-di-long", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD"]
def stats(g, sessions):
    d = g.groupby("date").r.sum().reindex(sessions, fill_value=0)
    return {"trades": len(g), "totR": g.r.sum(), "avgR": g.r.mean(), "R/session": d.mean(), "worst": d.min(), "worst5avg": d.nsmallest(5).mean(), "neg_days": (d < 0).mean()}
def per_setup(base, alt):
    b = base.groupby("strategy").r.sum(); x = alt.groupby("strategy").r.sum().reindex(b.index, fill_value=0); dlt = x - b
    return f"setups better {int((dlt>0.05).sum())} / worse {int((dlt<-0.05).sum())} / same {int((dlt.abs()<=0.05).sum())}; biggest loss {dlt.min():+.1f} ({dlt.idxmin()[:28]}), biggest gain {dlt.max():+.1f} ({dlt.idxmax()[:28]})"
pd.set_option("display.width", 250)
cases = [("Primary all 36 sessions", a[a.account == "primary"]),
         ("Primary current roster 11-11..11-24", a[(a.account == "primary") & (a.date >= "2026-11-11") & a.strategy.isin(ROSTER)]),
         ("Testing 1", a[a.account == "testing"]), ("Testing 2", a[a.account == "testing2"])]
for nm, g in cases:
    S = sorted(g.date.unique()); rows = {}
    rows["actual"] = stats(g, S)
    c1 = g[~g.held_other]; rows["(c1) owner while held: drop lots entered while another setup holds the symbol"] = stats(c1, S)
    c2 = g[g.day_owner]; rows["(c2) day owner: only the first setup to trade a symbol may trade it that day"] = stats(c2, S)
    c3 = g[g.stackpos == 1]; rows["(c3) 1 lot per symbol at a time (no stacking at all)"] = stats(c3, S)
    print(f"\n===== {nm}"); print(pd.DataFrame(rows).T.round(3).to_string())
    print("  c1:", per_setup(g, c1)); print("  c2:", per_setup(g, c2)); print("  c3:", per_setup(g, c3))
    # (d) symbol hash pools x setup groups: each setup assigned to one of 2 accounts (alternating by trade count),
    # each account trades only the symbols of its pool. 200 salts.
    setups = g.strategy.value_counts().index.tolist()
    grp = {s: i % 2 for i, s in enumerate(setups)}
    res = []
    for salt in range(200):
        pool = {s: int(hashlib.md5(f"{salt}:{s}".encode()).hexdigest(), 16) % 2 for s in g.symbol.unique()}
        k = g[[pool[s] == grp[st] for s, st in zip(g.symbol, g.strategy)]]
        res.append(stats(k, S))
    R = pd.DataFrame(res)
    print("  (d) 2 symbol pools x 2 setup groups, 200 random pool splits: median", R.median().round(3).to_dict())
    print("      5th-95th pct totR", R.totR.quantile([.05, .95]).round(1).tolist(), " worst-day", R.worst.quantile([.05, .95]).round(1).tolist())
    # side split: exposure check - the stacked pairs that are cross-side (blocked by rule today)
    # family split: share of held_other trades whose concurrent holder is same family
    fam_same = []
    for (sym, day), h in g.groupby(["symbol", "date"]):
        for i, r in h[h.held_other].iterrows():
            pr = h[(h.entry_time < r.entry_time) & (h.exit_time > r.entry_time) & (h.strategy != r.strategy)]
            fam_same.append(pr.fam.eq(r.fam).any())
    if fam_same:
        print(f"  stacked-on-another-setup lots whose holder is the SAME family: {np.mean(fam_same):.2f} (n{len(fam_same)})  -> a family split moves only the rest to another account")
