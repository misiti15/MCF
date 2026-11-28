"""shorts_autopsy: what did the shorts we could NOT borrow (skipped 'not shortable/ETB') do, versus shortable shorts that were
skipped for capacity reasons (halted / max positions / lot cap / daily loss / twin)? Both from the journals' what-if run
(run_id 2, bar-simulated gross R, no costs, same basis). Non-Graveyard, 10-23..11-27, deduped by setup|symbol|date|minute.
Usage: python etb_skips.py SCRATCH. Educational only - not financial advice."""
import sys, glob
import numpy as np, pandas as pd
D = sys.argv[1]
s = pd.concat([pd.read_parquet(p).assign(acct=p.split("skips_")[1][:-8]) for p in glob.glob(f"{D}/skips_*.parquet")])
s = s[(s.acct != "graveyard") & (s.side < 0)]
s["date"] = s.date.astype(str).str[:10]
s = s[(s.date >= "2026-10-23") & (s.date <= "2026-11-27") & s.r_multiple.notna()]
s["why"] = s.meta.str.extract(r"why=([^;0-9]+)")[0].str.strip()
s["k"] = s.strategy + "|" + s.symbol + "|" + s.date + "|" + s.entry_time.astype(str).str[:16]
s = s.drop_duplicates("k")
s["grp"] = np.where(s.why.str.contains("shortable"), "not shortable/ETB",
                    np.where(s.why.str.contains("halted|max positions|lot cap|daily loss|twin|already"), "shortable, capacity skip", "other"))
s["px"] = pd.cut(s.entry, [0, 5, 10, 20, 50, 1e6])
def st(g):
    ds = g.groupby("date").r_multiple.sum(); se = ds.std(ddof=1) / np.sqrt(len(ds))
    return pd.Series(dict(n=len(g), sess=len(ds), avg_gross=g.r_multiple.mean(), day_t=ds.mean() / se if se > 0 else np.nan,
                          wo_worst=(g.r_multiple.sum() - ds.min()) / len(g), wo_best=(g.r_multiple.sum() - ds.max()) / len(g)))
print(s.groupby("grp").apply(st).round(3).to_string())
print(s[s.grp != "other"].groupby(["grp", "px"], observed=True).apply(st).round(3).to_string())
print("\nTop not-shortable symbols:", s[s.grp == "not shortable/ETB"].symbol.value_counts().head(12).to_dict())
d = s[s.grp != "other"].groupby(["date", "grp"]).r_multiple.mean().unstack()
print("\nPaired by day (ETB minus capacity), mean %.3f, t %.2f, n days %d" % ((d.iloc[:, 1] - d.iloc[:, 0]).mean(),
      (d.iloc[:, 1] - d.iloc[:, 0]).mean() / ((d.iloc[:, 1] - d.iloc[:, 0]).std() / np.sqrt(d.dropna().shape[0])), d.dropna().shape[0]))
print(d.columns.tolist())
