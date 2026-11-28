"""Q2: book risk-budget rules (block new entries for the rest of the day in that account once a trigger fires).
Controls: U (same count of random lots in same account+period), TT (trigger time moved to a random non-trigger day of
the same account), neutral re-pricing. Usage: python q2_budget.py <scratch>. Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from common import load, dayt
rng = np.random.default_rng(7); ND = 300

def trig_book(g, kind, f):
    """return trigger minute (entries with emin > tau are blocked) or None. g = one account-day, sorted by emin."""
    L = g.L.iloc[0]
    ex = g.sort_values("xmin")
    if kind == "BR":
        c = ex.r.cumsum().values; hit = np.where(c <= -f * L)[0]
        return int(ex.xmin.values[hit[0]]) if len(hit) else None
    if kind == "BS":
        st = (ex.exit_reason == "stop").cumsum().values; hit = np.where(st >= max(1, f * L))[0]
        return int(ex.xmin.values[hit[0]]) if len(hit) else None
    if kind == "FH":
        return 630 if g.r[g.xmin <= 630].sum() <= -f * L else None

def block_mask(t, kind, f):
    blk = np.zeros(len(t), bool); trig = {}
    for (a, d), g in t.groupby(["account", "date"]):
        if kind == "SIDE":
            for s, gs in g.groupby("sidel"):
                Ls = max(1.0, g.L.iloc[0] * len(gs) / len(g))
                ex = gs.sort_values("xmin"); c = ex.r.cumsum().values; hit = np.where(c <= -f * Ls)[0]
                if len(hit):
                    tau = int(ex.xmin.values[hit[0]]); blk[gs.index[gs.emin > tau]] = True; trig[(a, d, s)] = tau
            continue
        tau = trig_book(g, kind, f)
        if tau is not None:
            blk[g.index[g.emin > tau]] = True; trig[(a, d)] = tau
    return blk, trig

def score(x, blk, trig, kind, label):
    base = x.groupby(["account", "date"]).r.sum(); new = x.r.where(~blk, 0).groupby([x.account, x.date]).sum()
    dd = (new - base); dday = dd.groupby(level=1).sum(); bday = base.groupby(level=1).sum(); nday = new.groupby(level=1).sum()
    saved = dd.sum(); nb = int(blk.sum())
    if nb == 0:
        return dict(rule=label, fired=0)
    # U control: random lots within account
    u = []
    acc_n = pd.Series(blk).groupby(x.account.values).sum()
    for _ in range(ND):
        s = 0.0
        for a, k in acc_n.items():
            if k:
                ra = x.r.values[(x.account == a).values]; s -= ra[rng.choice(len(ra), int(k), replace=False)].sum()
        u.append(s)
    # TT control: move each trigger time to a random non-trigger day of the same account
    tt = []
    days = x.groupby("account").date.unique()
    keys = [k for k in trig]
    for _ in range(ND):
        s = 0.0
        for k in keys:
            a, d = k[0], k[1]; tau = trig[k]
            cand = [dd_ for dd_ in days[a] if (a, dd_) not in trig and dd_ != d]
            if not cand:
                continue
            d2 = cand[rng.integers(len(cand))]
            m = (x.account == a) & (x.date == d2) & (x.emin > tau)
            if kind == "SIDE":
                m &= (x.sidel == k[2])
            s -= x.r[m].sum()
        tt.append(s)
    mean_acc = x.groupby("account").r.transform("mean")
    neutral = -(x.r - mean_acc)[blk].sum()
    acc_dd = dd.groupby(level=0).sum()
    return dict(rule=label, fired=len(trig), blocked=nb, cut_pct=100 * nb / len(x), saved=saved, per_wk=saved / (x.date.nunique() / 5),
                pctU=100 * np.mean(np.array(u) < saved), U=np.mean(u), pctTT=100 * np.mean(np.array(tt) < saved), TT=np.mean(tt),
                neutral=neutral, dt=dayt(dday.reindex(bday.index, fill_value=0)), blocked_avgR=x.r[blk].mean(), book_avgR=x.r.mean(),
                green_cost=dd[base > 0].sum(), red=f"{int((bday <= 0).sum())}->{int((nday <= 0).sum())}",
                worst5=f"{bday.nsmallest(5).sum():.1f}->{nday.nsmallest(5).sum():.1f}",
                best_share=(dday.max() / saved) if saved > 0 else np.nan,
                acct_better=int((acc_dd > 0.05).sum()), acct_worse=int((acc_dd < -0.05).sum()))

def main():
  S = sys.argv[1]; t = load(S); t = t[t.L.notna()].reset_index(drop=True)
  rules = [("BR", .10, "BR10"), ("BR", .20, "BR20"), ("BR", .30, "BR30"), ("BS", .15, "BS15"), ("BS", .30, "BS30"),
           ("FH", .05, "FH05"), ("FH", .10, "FH10"), ("SIDE", .20, "SIDE20")]
  out = []
  for bk in ["primary", "arena"]:
      for pe in ["DISC", "HOLD"]:
          x = t[(t.book == bk) & (t.period == pe)].reset_index(drop=True)
          if x.date.nunique() < 5:
              continue
          for kind, f, lab in rules:
              blk, trig = block_mask(x, kind, f)
              r = score(x, blk, trig, kind, lab); r.update(book=bk, period=pe, days=x.date.nunique(), lots=len(x)); out.append(r)
              print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
  pd.DataFrame(out).to_csv("q2_budget.csv", index=False)


if __name__ == "__main__":
    main()
