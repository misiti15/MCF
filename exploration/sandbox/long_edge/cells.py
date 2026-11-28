"""Long-edge condition scan on live lots (LR8 R after costs). Universe A = Primary + 8 arena accounts (Graveyard out,
identical signals once). Universe B = Graveyard longs (replication on different setups).
For each condition cell: lots, R, avg R, gross, day-clustered t, R w/o best day, best-day share, avg R w/o 11-25,
setups, share of setups (>=10 lots) positive, and a within-day control: avg R of random long lots drawn from the SAME
days in the same per-day counts (2,000 draws) -> percentile. Usage: python cells.py <scratch>
Educational only - not financial advice."""
import sys, re
import numpy as np, pandas as pd
S = sys.argv[1]; rng = np.random.default_rng(7)
L = pd.read_parquet(f"{S}/longs.parquet")
u = pd.read_csv("/home/user/MCF/data/universe.csv")
inv = re.compile(r"Bear|Short|Inverse|UltraShort|VIX|Volatil|-1x|-2x|-3x", re.I)
invs = set(u.loc[u.name.fillna("").str.contains(inv), "symbol"]) | {"SQQQ", "SOXS", "SPXU", "SDOW", "TZA", "UVXY", "UVIX", "VXX", "LABD", "TSLQ", "SPXS", "FAZ", "TECS", "YANG"}
L["inverse"] = L.symbol.isin(invs)
L["inst"] = np.where(L.inverse, "inverse/vol ETF", np.where(L.etf, "ETF (long-bias)", "stock"))
L["tb"] = pd.cut(L.emin, [0, 600, 630, 690, 750, 840, 960], right=False,
                 labels=["09:30-10:00", "10:00-10:30", "10:30-11:30", "11:30-12:30", "12:30-14:00", "14:00+"])
L["spy_day"] = pd.cut(L.spy_oc, [-99, -0.3, 0.3, 99], labels=["SPY down", "SPY flat", "SPY up"])  # OUTCOME
L["spy_gapb"] = pd.cut(L.spy_gap, [-99, -0.3, 0.3, 99], labels=["SPY gap dn", "SPY gap flat", "SPY gap up"])
L["spy_atb"] = pd.cut(L.spy_from_open, [-99, -0.5, -0.15, 0.15, 0.5, 99], labels=["SPY<-0.5", "SPY -0.5..-0.15", "SPY flat", "SPY +0.15..0.5", "SPY>+0.5"])
L["gapb"] = pd.cut(L.gap, [-99, -3, -1, -0.25, 0.25, 1, 3, 99], labels=["gap<-3", "gap -3..-1", "gap -1..-.25", "gap flat", "gap .25..1", "gap 1..3", "gap>3"])
L["fob"] = pd.cut(L.from_open_atr, [-99, -1, -0.5, -0.2, 0.2, 0.5, 1, 99], labels=["<-1ATR", "-1..-.5ATR", "-.5..-.2ATR", "flat", ".2..5ATR", ".5..1ATR", ">1ATR"])
L["rsb"] = pd.cut(L.rs_from_open, [-99, -2, -0.5, 0.5, 2, 99], labels=["RS<-2", "RS -2..-.5", "RS flat", "RS .5..2", "RS>2"])
L["pb"] = pd.cut(L.entry, [0, 10, 20, 50, 150, 1e9], labels=["<$10", "$10-20", "$20-50", "$50-150", ">$150"])
L["atrb"] = pd.cut(L.atr_pct, [0, 2, 3.5, 6, 999], labels=["ATR<2%", "ATR 2-3.5%", "ATR 3.5-6%", "ATR>6%"])
L["prevb"] = pd.cut(L.prev_ret, [-99, -3, -1, 1, 3, 99], labels=["prev<-3", "prev -3..-1", "prev flat", "prev 1..3", "prev>3"])
L["r5b"] = pd.cut(L.ret5, [-99, -8, -3, 3, 8, 99], labels=["5d<-8", "5d -8..-3", "5d flat", "5d 3..8", "5d>8"])
L["holdb"] = pd.cut(L.hold_min, [-1, 15, 60, 180, 999], labels=["hold<15m", "15-60m", "60-180m", ">180m"])  # OUTCOME
L["stopb"] = pd.cut(L.stop_bp, [0, 50, 100, 200, 1e9], labels=["stop<50bp", "50-100bp", "100-200bp", ">200bp"])
L["sprb"] = pd.cut(L.stop_spreads, [0, 6, 12, 25, 1e9], labels=["<6 spr", "6-12 spr", "12-25 spr", ">25 spr"])
L["fam"] = np.where(L.strategy.str.startswith("GEN"), "GEN", L.strategy.str.extract(r"^([A-Z]+\d*)", expand=False).fillna("?"))
L.to_parquet(f"{S}/longs2.parquet")
DIMS = ["tb", "spy_gapb", "spy_atb", "gapb", "fob", "rsb", "inst", "pb", "atrb", "prevb", "r5b", "stopb", "sprb", "spy_day", "holdb", "fam"]

def dayt(s):
    return s.mean() / (s.std(ddof=1) / np.sqrt(len(s))) if len(s) > 2 and s.std(ddof=1) > 0 else np.nan

def ctrl(U, cell, n=2000):
    """Within-day control: same per-day counts drawn at random from all longs of that day in universe U."""
    cnt = cell.groupby("date").size()
    pools = {d: U.loc[U.date == d, "r"].values for d in cnt.index}
    tot = cnt.sum(); sims = np.empty(n)
    for i in range(n):
        s = 0.0
        for d, c in cnt.items():
            s += rng.choice(pools[d], c, replace=len(pools[d]) < c).sum()
        sims[i] = s / tot
    return (sims < cell.r.mean()).mean() * 100, sims.mean()

def summ(U, g, do_ctrl):
    d = g.groupby("date").r.sum(); tot = g.r.sum()
    st = g.groupby("strategy").r.agg(["count", "sum"]); st = st[st["count"] >= 10]
    w = g[g.date != "2026-11-25"]
    out = {"lots": len(g), "days": len(d), "R": tot, "avgR": g.r.mean(), "gross": g.gross_r.mean(), "day_t": dayt(d),
           "R_wo_best": tot - d.max(), "best_share": d.max() / tot if tot > 0 else np.nan,
           "avg_wo_1125": w.r.mean(), "t_wo_1125": dayt(w.groupby("date").r.sum()),
           "setups": g.strategy.nunique(), "setups10_pos": f"{int((st['sum'] > 0).sum())}/{len(st)}"}
    if do_ctrl and len(g) >= 30:
        p, m = ctrl(U, g); out["ctrl_pct"] = p; out["ctrl_mean"] = m
    return out

pd.set_option("display.width", 250)
for name, U in [("A: Primary + arena (no Graveyard)", L[L.book != "graveyard"]), ("B: Graveyard (replication)", L[L.book == "graveyard"])]:
    print(f"\n######## {name}: lots {len(U)}, R {U.r.sum():.1f}, avg {U.r.mean():.3f}, gross {U.gross_r.mean():.3f}")
    for dim in DIMS:
        rows = {str(k): summ(U, g, name.startswith("A")) for k, g in U.groupby(dim, observed=True)}
        print(f"\n--- {dim}"); print(pd.DataFrame(rows).T.to_string(float_format=lambda x: f"{x:.3f}"))
