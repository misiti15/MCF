"""Q4 (2 configs, added after Q1-Q3 were scored): does yesterday predict today? (a) account level: R/lot today vs
yesterday's R/lot; (b) setup level: a setup's R/lot today when it was red (<= -2R) yesterday vs otherwise (a
'sit out the day after a bad day' rule), with a random-skip control. Usage: python q4_daycarry.py <scratch>.
Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from scipy.stats import spearmanr
from common import load, dayt
S = sys.argv[1]; t = load(S); rng = np.random.default_rng(3)
a = t.groupby(["book", "account", "date"]).r.agg(["mean", "sum", "size"]).reset_index().sort_values(["account", "date"])
a["prev"] = a.groupby("account")["mean"].shift(1); a["prevsum"] = a.groupby("account")["sum"].shift(1)
for bk, x in a.dropna().groupby("book"):
    rho, p = spearmanr(x.prev, x["mean"])
    red = x[x.prevsum < 0]; grn = x[x.prevsum >= 0]
    print(f"{bk}: acct-days {len(x)} rho(prev R/lot, today R/lot) {rho:+.3f} (p {p:.3f}); after red day {np.average(red['mean'], weights=red['size']):+.3f}/lot "
          f"({len(red)} d) vs after green {np.average(grn['mean'], weights=grn['size']):+.3f}/lot ({len(grn)} d)")
# setup level, using each setup's own consecutive active sessions within account
s = t.groupby(["book", "account", "strategy", "date"]).r.agg(["sum", "size"]).reset_index().sort_values(["account", "strategy", "date"])
s["prev"] = s.groupby(["account", "strategy"])["sum"].shift(1)
s = s.dropna()
for bk in ["primary", "arena"]:
    for pe in ["DISC", "HOLD"]:
        x = s[(s.book == bk) & ((s.date >= "2026-10-23") == (pe == "DISC"))]
        if len(x) < 30:
            continue
        sk = x.prev <= -2
        saved = -x["sum"][sk].sum(); nlots = x["size"][sk].sum()
        # control: skip the same number of setup-days at random (same book/period)
        u = [-x["sum"].values[rng.choice(len(x), int(sk.sum()), replace=False)].sum() for _ in range(1000)]
        lots_r = (x["sum"].sum() / x["size"].sum())
        print(f"{bk} {pe}: setup-days {len(x)}; after a <= -2R day: {int(sk.sum())} setup-days, {int(nlots)} lots, avg R/lot {x['sum'][sk].sum()/max(nlots,1):+.3f} "
              f"vs other {x['sum'][~sk].sum()/x['size'][~sk].sum():+.3f}; skipping them saves {saved:+.1f}R; pct vs random setup-day skip {100*np.mean(np.array(u)<saved):.0f}; "
              f"lot-matched expectation {-nlots*lots_r:+.1f}R")

print("\n--- cool-off rule (skip a setup's next active session after a <= -2R session): lot-matched excess, day-clustered ---")
for bk in ["primary", "arena"]:
    for pe in ["DISC", "HOLD"]:
        x = s[(s.book == bk) & ((s.date >= "2026-10-23") == (pe == "DISC"))].copy()
        if len(x) < 30:
            continue
        mu = x.groupby("account").apply(lambda g: g["sum"].sum() / g["size"].sum()); x["mu"] = x.account.map(mu)
        x["exc"] = np.where(x.prev <= -2, -(x["sum"] - x["size"] * x.mu), 0.0)
        x["sav"] = np.where(x.prev <= -2, -x["sum"], 0.0)
        d = x.groupby("date")[["exc", "sav"]].sum()
        ex = x[x.prev <= -2]
        fam = ex.assign(fam=ex.strategy.str.extract(r"^([A-Za-z]+)")[0]).groupby("fam").exc.sum() if False else None
        per_setup = ex.groupby("strategy").apply(lambda g: -(g["sum"].sum()))
        print(f"{bk} {pe}: saved {d.sav.sum():+.1f}R (day t {dayt(d.sav):.2f}); excess over lot-matched size cut {d.exc.sum():+.1f}R (day t {dayt(d.exc):.2f}); "
              f"best-day share of excess {d.exc.max()/d.exc.sum() if d.exc.sum()>0 else float('nan'):.2f}; setups helped/hurt {int((per_setup>0).sum())}/{int((per_setup<0).sum())} (hurt total {per_setup[per_setup<0].sum():+.1f}R)")
