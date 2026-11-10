"""Week scorecard 2026-11-02..11-06 for all 7 accounts (paper, costs in: journal pnl_adj; R = pnl_adj / $ risk), with
SPY day type (open-to-close > +0.25% up, < -0.25% down, else quiet; QDAY split), per-setup avg R without its best session
over the whole live record, Alpaca $ (equity_history to 11-05 + nightly 11-06; Primary with / without the MTUM broker
booking), and the twin cap / per-setup -2R latch / -20R halt what-ifs of blocked signals (journal run 2, net of the
production cost model as in saturday1031/week.py).
Usage: python week.py <scratch with <acct>/journal.db> <scratch with live_idx1.parquet>
Educational only - not financial advice."""
import json, sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd
S, B2 = Path(sys.argv[1]), Path(sys.argv[2]); OUT = Path(__file__).resolve().parent
DAYS = ["2026-11-02", "2026-11-03", "2026-11-04", "2026-11-05", "2026-11-06"]
PREV = ["2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29", "2026-10-30"]
AC = {"p": "Primary", "t1": "Testing 1", "t2": "Testing 2", "gy": "Graveyard", "gen": "Gen", "ex1": "Explore 1", "ll": "Live Lab"}
EQ = {"p": "primary", "t1": "testing", "t2": "testing2", "gy": "graveyard", "gen": "gen", "ex1": "explore1", "ll": "livelab"}
# 11-06 Alpaca day P/L from the 11-06 nightly (research/owner_inbox/2026-11-06.md); 11-05 Primary "with MTUM" from the
# owner-inbox forensics (equity 94,876.57 -> 83,052.55); equity_history carries the trading-only figure for 11-05.
A1106 = {"p": -1238.60, "t1": -30.32, "t2": 51.95, "gy": 536.28, "gen": -157.92, "ex1": 51.12, "ll": -59.54}
P_WITHOUT_1106 = -1057.07; P_WITH_1105 = -11824.02
out = []; P = lambda *x: out.append(" ".join(str(y) for y in x))

I = pd.read_parquet(B2 / "live_idx1.parquet"); I = I[I.symbol == "SPY"]
g = I.sort_values("t").groupby("date"); oc = (g.c.last() / g.o.first() - 1) * 100
DT = pd.DataFrame({"spy_oc": oc.round(2), "dtype": np.where(oc > 0.25, "up", np.where(oc < -0.25, "down", "quiet"))})


def load(a, days=None):
    c = sqlite3.connect(S / a / "journal.db")
    q = "select date, symbol, strategy, side, entry, stop, shares, pnl, pnl_adj, exit_reason, entry_time from trades where run_id=1 and exit is not null"
    t = pd.read_sql(q, c)
    if days: t = t[t.date.isin(days)]
    t["risk"] = ((t.entry - t.stop).abs() * t.shares).replace(0, np.nan)
    t["R"] = t.pnl_adj / t.risk
    return t.dropna(subset=["R"])


def be(t):
    w, l = t[t.pnl_adj > 0], t[t.pnl_adj <= 0]
    return l.R.abs().mean() / (w.R.mean() + l.R.abs().mean()) if len(w) and len(l) else np.nan


def wobd(t):
    """avg R without the setup's best session, and that session's share of total R."""
    d = t.groupby("date").R.sum()
    if len(d) < 2: return np.nan, np.nan
    best = d.idxmax(); rest = t[t.date != best]
    return rest.R.mean(), (d.max() / d.sum() if d.sum() > 0 else np.nan)


eqh = json.load(open("/home/user/MCF/docs/live/equity_history.json"))["accounts"]
P("# Week 2026-11-02..11-06 scorecard, 7 accounts (paper, costs in)")
P("SPY day types:", "; ".join(f"{d[5:]} {DT.loc[d,'dtype']} ({DT.loc[d,'spy_oc']:+.2f}%)" for d in DAYS))
P("Rule changes in window (research/ledger.jsonl): UNI1 11-04 (Testing 2 top-500 universe), ROLL1 11-05 (Explore 1 / Live Lab low-rep homes); "
  "standing: Primary ~$4k lot 10-28, Primary -2R latch 10-29, -20R account halt (hit 11-06 10:55). MTUM broker glitch 11-05/11-06 (Primary $ only).")
rows, setup_rows = [], []
for a, nm in AC.items():
    t = load(a, DAYS); tp = load(a, PREV); tall = load(a)
    if not len(t): P(f"\n## {nm}: no trades"); continue
    d = t.groupby("date").agg(n=("R", "size"), R=("R", "sum"), pl=("pnl_adj", "sum"))
    alp = {x: (eqh[EQ[a]].get(x) or {}).get("alpaca_day_pl") for x in DAYS[:4]}; alp["2026-11-06"] = A1106[a]
    alp = {k: v for k, v in alp.items() if v is not None and k in d.index}
    alp_sum = sum(alp.values())
    extra = ""
    if a == "p":
        with_ = alp_sum - alp["2026-11-05"] + P_WITH_1105
        without = alp_sum - alp["2026-11-06"] + P_WITHOUT_1106
        extra = f" | Alpaca with MTUM {with_:+,.2f} / without {without:+,.2f}"
        alp_sum_s = f"{without:+,.2f} (without MTUM)"; alp_sum = without
    else:
        alp_sum_s = f"{alp_sum:+,.2f}"
    s = t.groupby("strategy").agg(n=("R", "size"), R=("R", "sum"), avgR=("R", "mean"), pl=("pnl_adj", "sum")).sort_values("R")
    for k in s.index:
        ar, sh = wobd(tall[tall.strategy == k]); s.loc[k, "rec_n"] = int((tall.strategy == k).sum())
        s.loc[k, "rec_avgR"] = tall[tall.strategy == k].R.mean(); s.loc[k, "rec_wobd"] = ar; s.loc[k, "rec_best_share"] = sh
        wk = t[t.strategy == k].groupby("date").R.sum()
        s.loc[k, "wk_wobd_avg"] = t[(t.strategy == k) & (t.date != wk.idxmax())].R.mean() if len(wk) > 1 else np.nan
    s["acct"] = nm; setup_rows.append(s.reset_index())
    dty = t.join(DT, on="date").groupby("dtype").agg(n=("R", "size"), R=("R", "sum"), avg=("R", "mean"))
    rows.append(dict(acct=nm, trades=len(t), sumR=t.R.sum(), avgR=t.R.mean(), win=(t.pnl_adj > 0).mean(), be=be(t),
                     journal_pl=t.pnl_adj.sum(), alpaca=alp_sum, green_R=int((d.R > 0).sum()), days=len(d),
                     wobd_R=d.R.sum() - d.R.max(), prevR=tp.R.sum(), prev_n=len(tp),
                     up_R=dty.R.get("up", 0), down_R=dty.R.get("down", 0), quiet_R=dty.R.get("quiet", 0),
                     long_R=t[t.side == 1].R.sum(), short_R=t[t.side != 1].R.sum()))
    P(f"\n## {nm}: {t.R.sum():+.1f}R | {len(t)} trades | avg {t.R.mean():+.3f}R | win {(t.pnl_adj>0).mean():.0%} vs BE {be(t):.0%} | "
      f"journal {t.pnl_adj.sum():+,.2f} | Alpaca {alp_sum_s}{extra} | green (R) {int((d.R>0).sum())}/{len(d)} | "
      f"longs {t[t.side==1].R.sum():+.1f}R n{int((t.side==1).sum())} shorts {t[t.side!=1].R.sum():+.1f}R n{int((t.side!=1).sum())}")
    P("   by day:", "; ".join(f"{k[5:]} {r.n} tr {r.R:+.1f}R jr ${r.pl:+.0f} alp ${alp.get(k, float('nan')):+.0f}" for k, r in d.iterrows()))
    P("   by SPY day type:", "; ".join(f"{k} {int(r.n)} tr {r.R:+.1f}R ({r.avg:+.3f})" for k, r in dty.iterrows()))
    P(f"   w/o best day: {d.R.sum() - d.R.max():+.1f}R (best {d.R.idxmax()[5:]} {d.R.max():+.1f}R) | prev week {len(tp)} tr {tp.R.sum():+.1f}R")
    fm = lambda k, r: (f"{k} {int(r.n)} tr {r.R:+.1f}R ({r.avgR:+.3f}; record {int(r.rec_n)} tr {r.rec_avgR:+.3f}, w/o best day {r.rec_wobd:+.3f}"
                       + (f", `1 day` {r.rec_best_share:.0%}" if r.rec_best_share >= 0.5 else "") + ")")
    P("   best: " + "; ".join(fm(k, r) for k, r in s.tail(3)[::-1].iterrows()))
    P("   worst: " + "; ".join(fm(k, r) for k, r in s.head(3).iterrows()))
pd.DataFrame(rows).round(4).to_csv(OUT / "week_scorecard.csv", index=False)
pd.concat(setup_rows).round(4).to_csv(OUT / "week_by_setup.csv", index=False)
P("\n" + pd.DataFrame(rows).round(3).to_string(index=False))
P("\n# Twin-exposure cap, per-setup -2R loss limit and account halt: what-if of blocked signals (net of production costs)")
caps = []
for a, nm in AC.items():
    c = sqlite3.connect(S / a / "journal.db")
    w = pd.read_sql(f"select date, strategy, entry, stop, exit, exit_reason, r_multiple, meta from trades where run_id=2 and exit is not null and date in ({','.join('?'*5)})", c, params=DAYS)
    w["why"] = w.meta.fillna("").str.extract(r"why=([^;]*)")[0].fillna("")
    w["why"] = np.where(w.why.str.startswith("halted"), "halted", w.why)
    R = (w.entry - w.stop).abs()
    cps = (0.01 + w.entry * 1e-4) + np.where(w.exit_reason == "target", 0.0, 0.01 + w.exit * 1e-4) + np.where(w.exit_reason == "stop", 0.02, 0.0)
    w["net"] = w.r_multiple - np.where(R > 0, cps / R, 0.0)
    for rsn in ("twin held", "setup daily loss limit", "halted"):
        x = w[w.why == rsn]
        caps.append(dict(acct=nm, rule=rsn, n=len(x), net=x.net.sum() if len(x) else 0.0))
        if len(x):
            byd = x.groupby("date").net.sum()
            P(f"  {nm:9s} {rsn:23s}: n {len(x):4d} net {x.net.sum():+7.1f}R avg {x.net.mean():+.3f} | by day " +
              " ".join(f"{k[5:]} {v:+.1f}" for k, v in byd.items()) + f" | worst setups {x.groupby('strategy').net.sum().sort_values().head(2).round(1).to_dict()}")
        else:
            P(f"  {nm:9s} {rsn:23s}: none blocked")
pd.DataFrame(caps).round(2).to_csv(OUT / "week_caps.csv", index=False)
open(OUT / "week_out.txt", "w").write("\n".join(out) + "\n\nEducational only - not financial advice.\n")
print("\n".join(out))
