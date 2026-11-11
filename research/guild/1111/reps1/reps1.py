"""REPS1 lever table (owner P1 'live reps faster', item 1; Lead lead-20261111-1100-2). Descriptive, 0 configs.
Every live paper signal 10-20..11-10 (7 accounts) by skip reason -> lever; reps/session each lever would add; and a what-if
GROSS R for skipped signals with a SIMPLIFIED exit (5-min bars: entry = signal ref price, stop first if a bar spans both,
target if set, else 15:50-bar close). The same simplified exit is run on SUBMITTED signals and compared with their live gross R,
so the replay gap is printed beside every what-if (rule 21: this is a filter-level estimate, never a record).
    python -I reps1.py <signals.csv.gz> <trades.csv.gz> <m5.csv.gz>       Educational only - not financial advice."""
import sys, re, numpy as np, pandas as pd
S = pd.read_csv(sys.argv[1]); T = pd.read_csv(sys.argv[2])
LEVER = [(r"not shortable|ETB", "borrow: not shortable / ETB"), (r"^setup daily loss limit", "setup daily loss cap"),
         (r"^daily loss limit", "account daily loss limit"), (r"spread", "spread filters (bps / % of stop)"),
         (r"max positions for this setup", "per-setup max positions"), (r"insufficient buying power|buying_power", "buying power"),
         (r"^halted", "account halt"), (r"opposite side held|twin held|already in symbol", "symbol conflict / twin block"),
         (r"cost filter", "cost filter (stop+exit cost in R)"), (r"lot cap|after liquidity cap", "size / liquidity caps"),
         (r"tape short gate", "split-tape short gate"), (r"price below minimum", "minimum price"),
         (r"take_profit|stop_loss|base_price", "bracket order reject (price rounding)"),
         (r"crosscheck|missed|already through|no quote", "execution / timing checks")]
def lever(r):
    r = str(r)
    for p, n in LEVER:
        if re.search(p, r, re.I): return n
    return "other"
S["lever"] = np.where(S.status == "submitted", "SUBMITTED", S.reason.map(lever))
nsess = S.day.nunique()
# groups: Gen account setups; low-rep = < 20 submitted live trades across all accounts in the window, or homed in Explore 1 / Live Lab
sub_n = S[S.status == "submitted"].groupby("strategy").size()
low = set(sub_n[sub_n < 20].index) | (set(S.strategy) - set(sub_n.index)) | set(S[S.acct.isin(["mcf-data-explore1", "mcf-data-livelab"])].strategy)
S["grp"] = np.where(S.acct == "mcf-data-gen", "Gen", np.where(S.strategy.isin(low), "low-rep", "other"))
print(f"signals {len(S)} on {nsess} sessions, {S.strategy.nunique()} setups; submitted {int((S.status=='submitted').sum())}")
print(f"groups (setups): Gen {S[S.grp=='Gen'].strategy.nunique()}, low-rep {S[S.grp=='low-rep'].strategy.nunique()}, other {S[S.grp=='other'].strategy.nunique()}")
# ---- simplified exit on 5-min bars ----
m = pd.read_csv(sys.argv[3]); m["t"] = pd.to_datetime(m.t, utc=True).dt.tz_convert("America/New_York")
m["day"] = m.t.dt.strftime("%Y-%m-%d"); m["hm"] = m.t.dt.hour * 100 + m.t.dt.minute; m = m[(m.hm >= 930) & (m.hm <= 1550)]
G = {k: g.sort_values("t") for k, g in m.groupby(["symbol", "day"])}
def sim(r):
    g = G.get((r.symbol, r.day))
    if g is None or not (r.ref_price > 0) or r.stop == r.ref_price: return np.nan
    ts = pd.Timestamp(r.ts).tz_convert("America/New_York")
    g = g[g.t >= ts.floor("5min") + pd.Timedelta(minutes=5)]          # bars that START after the signal's bar
    if len(g) == 0: return np.nan
    e, s, tg, sd = r.ref_price, r.stop, r.target, np.sign(r.side)
    risk = abs(e - s)
    for b in g.itertuples():
        if (sd > 0 and b.l <= s) or (sd < 0 and b.h >= s): return -1.0
        if tg == tg and ((sd > 0 and b.h >= tg) or (sd < 0 and b.l <= tg)): return sd * (tg - e) / risk
    return sd * (g.c.iloc[-1] - e) / risk
S["sim"] = [sim(r) for r in S.itertuples()]
# calibration: submitted signals with a live trade (match acct, strategy, symbol, day, signal minute)
T["k"] = T.acct + "|" + T.strategy + "|" + T.symbol + "|" + T.date
T["risk"] = (T.entry - T.stop).abs() * T.shares; T = T[T.risk > 0]; T["gR"] = T.pnl / T.risk; T["nR"] = T.pnl_adj / T.risk
tl = T.groupby("k").agg(gR=("gR", "mean"), nR=("nR", "mean"))
S["k"] = S.acct + "|" + S.strategy + "|" + S.symbol + "|" + S.day
C = S[(S.status == "submitted")].drop_duplicates("k").join(tl, on="k").dropna(subset=["sim", "gR"])
print(f"\nCALIBRATION (submitted signals with a live trade, n {len(C)}): simplified-exit gross {C.sim.mean():+.3f}R vs live gross {C.gR.mean():+.3f}R "
      f"(gap {C.sim.mean()-C.gR.mean():+.3f}), live net {C.nR.mean():+.3f}R; corr {C[['sim','gR']].corr().iloc[0,1]:.2f}")
for g_, c in C.groupby(np.where(C.acct == "mcf-data-gen", "Gen", "non-Gen")):
    print(f"   {g_}: n {len(c)}, sim {c.sim.mean():+.3f} vs live gross {c.gR.mean():+.3f}")
print("A what-if below is the simplified exit; read it against the submitted row of the same group, not as an absolute R.")
# ---- lever table ----
pd.set_option("display.width", 220)
def table(df, tag):
    o = df.groupby("lever").agg(n=("sim", "size"), setups=("strategy", "nunique"), sim_n=("sim", "count"), sim=("sim", "mean"),
                                 longs=("side", lambda x: (x > 0).mean()))
    o["per_session"] = o.n / nsess
    o = o.sort_values("n", ascending=False)
    print(f"\n{tag}  (reps/session if the lever were fully released; what-if gross R, simplified exit)")
    print(o[["n", "per_session", "setups", "longs", "sim_n", "sim"]].round(3).to_string())
table(S, "ALL SETUPS"); table(S[S.grp == "Gen"], "GEN ACCOUNT"); table(S[S.grp == "low-rep"], "LOW-REP SETUPS")
# twin/duplicate check: a skipped signal whose (strategy, symbol, day) was also submitted elsewhere adds no new rep
dup = S[S.status != "submitted"].k.str.split("|", n=1).str[1].isin(set(S[S.status == "submitted"].k.str.split("|", n=1).str[1]))
print(f"\nskipped signals whose setup+symbol+day was traded in another account (no new information): {int(dup.sum())} of {int((S.status!='submitted').sum())}")
S.drop(columns=["k"]).to_csv("reps1_signals_sim.csv.gz", index=False)
print("Educational only - not financial advice.")
