"""Observer scan of research/bdi/moves/moves.csv (MCF default branch). Descriptive only, 0 configs.
Run from the MCF checkout: python ../guild/research/obs-open-movers/scan.py
Educational only - not financial advice."""
import pandas as pd
d = pd.read_csv("research/bdi/moves/moves.csv")
m = lambda s: int(s[:2]) * 60 + int(s[3:])
for s in ["all", "tradable"]:
    g = d[d.set == s]
    print(f"[{s}] rows={len(g)} dates={g.date.nunique()} blackout_share={g.blackout.mean():.2f}")
    print("  miss:", g.miss_reason.fillna("").str.split(":").str[0].value_counts().to_dict())
    print(f"  caught={int((g.n_right>0).sum())} R_captured={g.r_captured.sum():+.2f} wrong_trades={int(g.n_wrong.sum())} R_wrong={g.r_wrong.sum():+.2f}")
t = d[d.set == "tradable"].copy()
t["dec"] = t.decision.map(m); t["ext"] = t.extreme.map(m)
for lab, x in [("decision 09:35", t[t.dec == 575]), ("decision >= 09:40", t[t.dec > 575])]:
    print(f"\n[tradable, {lab}] n={len(x)} caught={int((x.n_right>0).sum())} ({(x.n_right>0).mean():.0%})")
    print("  miss:", x.miss_reason.fillna("").str.split(":").str[0].value_counts().to_dict())
x = t[t.dec == 575]
for lab, y in [("all days", x), ("excl 2026-11-05", x[x.date != "2026-11-05"])]:
    print(f"\n09:35 movers {lab}: n={len(y)} extreme>=10:00 {(y.ext>=600).mean():.0%}  extreme>=10:20 {(y.ext>=620).mean():.0%}  median move_atr {y.move_atr.median():.2f}")
