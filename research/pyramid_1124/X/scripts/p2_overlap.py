import pandas as pd, numpy as np, itertools, hashlib
X = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/X/"
t = pd.read_parquet(X + "live_all.parquet"); t = t[t.r.notna() & np.isfinite(t.r)].copy()
for c in ("entry_time", "exit_time"): t[c] = pd.to_datetime(t[c], utc=True, format="mixed")
t["side_s"] = np.where(t.side == 1, "long", "short")
fam = lambda s: s.split("-", 1)[0] if "-" in s else s
t["fam"] = t.strategy.map(fam)
t["notional"] = t.entry.abs() * t.shares.abs()

def annotate(a):
    a = a.sort_values("entry_time").copy()
    held_other, stackpos, sameday_other, first_owner = [], [], [], []
    for (sym, day), g in a.groupby(["symbol", "date"]):
        g = g.sort_values("entry_time")
        first = g.strategy.iloc[0]
        for i, r in g.iterrows():
            prior = g[(g.entry_time < r.entry_time) & (g.exit_time > r.entry_time)]
            held_other.append((i, (prior.strategy != r.strategy).any()))
            stackpos.append((i, len(prior) + 1))
            sameday_other.append((i, (g.strategy != r.strategy).any()))
            first_owner.append((i, r.strategy == first))
    for nm, lst in (("held_other", held_other), ("stackpos", stackpos), ("sameday_other", sameday_other), ("day_owner", first_owner)):
        a[nm] = pd.Series(dict(lst))
    return a

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
out = {}
for acct in ("primary", "testing", "testing2"):
    a = annotate(t[t.account == acct]); out[acct] = a
    a["stacked"] = a.stackpos > 1
    print(f"\n===== {acct}: trades {len(a)}, setups {a.strategy.nunique()}, sessions {a.date.nunique()}, short share {(a.side==-1).mean():.2f}")
    print(f"  trades whose symbol was ALSO traded the same day by another setup (this account): {a.sameday_other.mean():.3f}")
    print(f"  trades entered while ANOTHER setup already held the symbol (stacked on another setup): {a.held_other.mean():.3f}")
    print(f"  trades entered as lot 2+ on the symbol (any setup incl. same-setup re-entry): {a.stacked.mean():.3f}")
    g = a.groupby("stacked").r.agg(["size", "mean", "sum"]); print("  R single lot vs stacked lot:\n", g.round(3).to_string())
    g = a.groupby("held_other").r.agg(["size", "mean", "sum"]); print("  R: entered with another setup holding (True) vs not:\n", g.round(3).to_string())
    # symbol-day concentration
    sd = a.groupby(["date", "symbol"]).agg(n=("r", "size"), R=("r", "sum"), setups=("strategy", "nunique"))
    print(f"  symbol-days {len(sd)}; with 2+ setups {int((sd.setups>=2).sum())} ({(sd.setups>=2).mean():.3f}); R on 2+-setup symbol-days {sd[sd.setups>=2].R.sum():.1f} of total {sd.R.sum():.1f}")
    # pairwise setup overlap: Jaccard of (date,symbol) sets, for setups with >= 20 trades
    ss = a.groupby("strategy").apply(lambda g: set(zip(g.date, g.symbol)))
    ss = ss[a.groupby("strategy").size() >= 20]
    rows = []
    for x, y in itertools.combinations(ss.index, 2):
        inter = len(ss[x] & ss[y])
        if inter == 0: continue
        rows.append({"a": x[:30], "b": y[:30], "shared_symday": inter, "share_of_a": inter / len(ss[x]), "share_of_b": inter / len(ss[y]), "jacc": inter / len(ss[x] | ss[y])})
    if rows:
        print("  top pairwise overlaps:\n", pd.DataFrame(rows).sort_values("shared_symday", ascending=False).head(8).round(2).to_string(index=False))
    # setup daily R correlation
    dr = a.pivot_table(index="date", columns="strategy", values="r", aggfunc="sum")
    dr = dr.loc[:, a.groupby("strategy").date.nunique().reindex(dr.columns) >= 10]
    if dr.shape[1] >= 2:
        C = dr.fillna(0).corr().values; iu = np.triu_indices_from(C, 1)
        sides = a.drop_duplicates("strategy").set_index("strategy").side.reindex(dr.columns).values
        same = np.array([sides[i] == sides[j] for i, j in zip(*iu)])
        print(f"  setup daily-R corr (>=10 days, {dr.shape[1]} setups): mean {C[iu].mean():+.3f}; same-side pairs {C[iu][same].mean():+.3f} (n{same.sum()}); long-short pairs {C[iu][~same].mean() if (~same).any() else float('nan'):+.3f} (n{(~same).sum()})")
pd.concat(out.values()).to_parquet(X + "overlap_annot.parquet")
# cross-account: Primary trades whose symbol was traded same day (same side) in Testing/Testing2
p = out["primary"]; o = pd.concat([out["testing"], out["testing2"]])
keys = set(zip(o.date, o.symbol, o.side))
p["x_acct"] = [(d, s, sd) in keys for d, s, sd in zip(p.date, p.symbol, p.side)]
print("\nPrimary trades whose symbol+side also traded the same day in Testing 1/2:", round(p.x_acct.mean(), 3))
