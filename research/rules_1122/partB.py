"""Part B: BRAKE-BURST replay (live.burst_max_entries 30 / burst_window_min 10, per setup, rolling) on each account's full
chronological live order stream, run 1, LR8 cost-R. 'Without' = the journal as traded (the brake was not live before
2026-11-23). 'With' = the same incoming stream: an entry is skipped when that setup already took >= 30 entries in the
previous 10 minutes in that account; capacity it frees is offered back, in time order, to the same setup's signals the
journal skipped for 'max positions for this setup' (what-if rows, costed as part A: median live cost gap + 0.05R), only
while the braked book holds fewer open lots of that setup than the journal did (capacity the brake itself freed). Not modelled: account-slot / halt / buying-power changes (journals do not
record which other setups' signals those would admit), price impact. Exposure: open lots per underlying group
(groups.csv, signed: side x member sign), sampled at every entry. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from common import ts, whatif_cost_adjust

W = Path(sys.argv[1]); OUT = Path(__file__).parent
CAP = dict(primary=30, testing=150, testing2=100, testingd=100, testinge=100, testingf=100, gen=150, livelab=100,
           explore1=100, graveyard=75)
NMAX, WIN = 30, pd.Timedelta(minutes=10)
live = pd.read_parquet(W / "live.parquet")
live["et"], live["xt"] = ts(live.entry_time), ts(live.exit_time)
wi = pd.read_parquet(W / "whatif.parquet")
wi = wi[wi.why == "max positions for this setup"].copy()
wi["et"], wi["xt"] = ts(wi.entry_time), ts(wi.exit_time)
wi = wi[wi.et.notna() & wi.xt.notna() & wi.r_multiple.notna()]
wi["r"] = whatif_cost_adjust(wi, live[~live.dup])
G = pd.read_csv(W / "groups.csv").set_index("symbol")


def brake(acct_df, acct_wi, cap):
    """returns (kept live rows mask, admitted what-if rows)."""
    keep = pd.Series(True, index=acct_df.index)
    adds = []
    for (s, d), g in acct_df.groupby(["strategy", "date"]):
        g = g.sort_values("et")
        cand = acct_wi[(acct_wi.strategy == s) & (acct_wi.date == d)].sort_values("et")
        ev = [(r.et, 0, i) for i, r in g.iterrows()] + [(r.et, 1, i) for i, r in cand.iterrows()]
        if len(g) <= NMAX:          # cannot bind: fewer than 31 entries in the whole day
            continue
        ev.sort(key=lambda x: (x[0], x[1]))
        taken, open_x, open_act = [], [], []
        for t, kind, i in ev:
            open_x = [x for x in open_x if x > t]
            open_act = [x for x in open_act if x > t]
            recent = sum(1 for z in taken if z > t - WIN)
            if kind == 0:
                open_act.append(g.at[i, "xt"])
                if recent >= NMAX:
                    keep[i] = False
                    continue
                taken.append(t); open_x.append(g.at[i, "xt"])
            else:
                # only capacity the brake freed: the journal had the setup at its cap, the brake book has room
                if recent >= NMAX or len(open_x) >= min(cap, len(open_act)):
                    continue
                taken.append(t); open_x.append(cand.at[i, "xt"]); adds.append(i)
    return keep, acct_wi.loc[adds]


def exposure(df):
    """max |signed open lots| per underlying group over the stream (sampled at entries); returns per-date max and group."""
    df = df.assign(g=df.symbol.map(G["group"]).fillna(df.symbol), sg=df.side * df.symbol.map(G["sign"]).fillna(1))
    out = []
    for d, x in df.groupby("date"):
        x = x.sort_values("et")
        et, xt, gg, sg = x.et.values, x.xt.values, x.g.values, x.sg.values
        best = (0, "", 0)
        for k in range(len(x)):
            o = (et <= et[k]) & (xt > et[k])
            if not o.any():
                continue
            s = pd.Series(sg[o]).groupby(gg[o]).sum()
            m = s.abs().idxmax()
            if abs(s[m]) > best[0]:
                best = (abs(s[m]), m, int(o.sum()))
        out.append(dict(date=d, max_group_lots=best[0], group=best[1], open_lots_then=best[2]))
    return pd.DataFrame(out)


rows, blk_rows, exp_rows = [], [], []
for acct, df in live.groupby("account"):
    df = df.copy()
    k, adds = brake(df, wi[wi.account == acct], CAP[acct])
    a = df[k]
    w = pd.concat([a, adds.assign(src="whatif")], ignore_index=True)
    day0 = df.groupby("date").r.sum()
    day1 = w.groupby("date").r.sum().reindex(day0.index).fillna(0)
    b = df[~k].assign(day_R=lambda z: z.date.map(day0))
    blk_rows.append(b.assign(day_type=np.where(b.day_R > 0, "profitable day", "losing day")))
    e0, e1 = exposure(df), exposure(w)
    rows.append(dict(account=acct, trades=len(df), R_without=df.r.sum(), R_with=w.r.sum(), dR=w.r.sum() - df.r.sum(),
                     blocked=int((~k).sum()), blocked_R=df.r[~k].sum(), whatif_admitted=len(adds),
                     admitted_R=adds.r.sum() if len(adds) else 0.0,
                     blocked_on_green_days=int((b.day_R > 0).sum()), blocked_R_green=b.r[b.day_R > 0].sum(),
                     blocked_on_red_days=int((b.day_R <= 0).sum()), blocked_R_red=b.r[b.day_R <= 0].sum(),
                     days_changed=int((day1 - day0).abs().gt(1e-9).sum()), worst_day_without=day0.min(),
                     worst_day_with=day1.min(),
                     max_group_lots_without=e0.max_group_lots.max(), grp_without=e0.loc[e0.max_group_lots.idxmax(), "group"],
                     date_without=e0.loc[e0.max_group_lots.idxmax(), "date"],
                     max_group_lots_with=e1.max_group_lots.max(), grp_with=e1.loc[e1.max_group_lots.idxmax(), "group"],
                     date_with=e1.loc[e1.max_group_lots.idxmax(), "date"]))
    m = e0.merge(e1, on="date", suffixes=("_without", "_with"))
    m["account"] = acct
    exp_rows.append(m)
R = pd.DataFrame(rows)
R.round(2).to_csv(OUT / "B_accounts.csv", index=False)
B = pd.concat(blk_rows)
B.groupby(["account", "date", "strategy", "day_type"]).r.agg(["size", "sum"]).round(2).to_csv(OUT / "B_blocked_by_day.csv")
E = pd.concat(exp_rows)
E.to_csv(OUT / "B_exposure_by_day.csv", index=False)
pd.set_option("display.width", 250)
print(R.round(1).to_string(index=False))
print(B.groupby(["account", "date", "strategy", "day_type"]).r.agg(["size", "sum"]).round(1).to_string())
p = E[E.account == "primary"].sort_values("max_group_lots_without").tail(8)
print(p.to_string(index=False))
