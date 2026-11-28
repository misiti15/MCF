"""shorts_autopsy: live replay of Primary's existing −2R per-setup latch (closed R only, as live 10-29) applied to the
non-Primary, non-Graveyard accounts, 10-23..11-27 (LR8 journal lots; a lot is dropped if, at its entry time, that
setup's closed R in that account that day is <= −2). Lower bound of LATCH-OPEN (which also counts open R). Descriptive, in-sample.
Usage: python live_latch_testing.py SCRATCH. Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
D = sys.argv[1]
t = pd.read_parquet(f"{D}/live_feat.parquet")
t = t[t.account != "primary"].sort_values(["account", "strategy", "date", "et"]).copy()
keep = np.ones(len(t), bool); pos = {i: k for k, i in enumerate(t.index)}
for _, g in t.groupby(["account", "strategy", "date"]):
    et, xt, r = g.et.to_numpy(), g.xt.to_numpy(), g.r.to_numpy(); kept = []
    for j in range(len(g)):
        closed = sum(r[k] for k in kept if xt[k] <= et[j])
        if closed <= -2.0: keep[pos[g.index[j]]] = False
        else: kept.append(j)
t["keep"] = keep
def summ(z):
    d0 = z.groupby("date").r.sum(); d1 = z[z.keep].groupby("date").r.sum().reindex(d0.index, fill_value=0)
    dd = d1 - d0; se = dd.std(ddof=1) / np.sqrt(len(dd))
    return pd.Series(dict(lots=len(z), dropped=int((~z.keep).sum()), R_before=d0.sum(), R_after=d1.sum(), dR=dd.sum(), day_t=dd.mean() / se if se > 0 else np.nan,
                          worst_before=d0.min(), worst_after=d1.min(), green_before=int((d0 > 0).sum()), green_after=int((d1 > 0).sum()),
                          dR_ex1125=dd.drop("2026-11-25", errors="ignore").sum(), best_share=dd.max() / dd.sum() if dd.sum() > 0 else np.nan,
                          avgR_dropped=z[~z.keep].r.mean()))
pd.set_option("display.width", 250)
print(t.groupby("fam").apply(summ).round(2).to_string())
print(t.groupby("account").apply(summ).round(2).to_string())
ps = t.groupby("strategy").apply(lambda z: z[~z.keep].r.sum() * -1)
print(f"\nsetups improved {(ps > 0).sum()}, worse {(ps < 0).sum()}, unchanged {(ps == 0).sum()}; worst setup effect {ps.min():.1f}, best {ps.max():.1f}")
