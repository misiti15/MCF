"""Counterfactual Primary: only Claude's promotion/demotion recommendations followed (research only, read-only).

Usage: python research/bdi/cf1026/cf.py <dir with mcf-data.db, mcf-data-testing.db, mcf-data-testing2.db, mcf-data-graveyard.db>
Journals: git show origin/<branch>:journal.db. Writes per_session.csv, attribution.csv and tables.md next to this file.
Educational only - not financial advice.
"""
import sqlite3, sys, os, statistics as st
import pandas as pd

D = sys.argv[1]
OUT = os.path.dirname(os.path.abspath(__file__))
ACC = {"P": "mcf-data", "T1": "mcf-data-testing", "T2": "mcf-data-testing2", "GY": "mcf-data-graveyard"}

def load(acc, run):
    c = sqlite3.connect(os.path.join(D, ACC[acc] + ".db"))
    df = pd.read_sql(f"select * from trades where run_id={run}", c)
    df["acc"] = acc
    for c_ in ("shares", "entry", "stop", "pnl", "pnl_adj", "r_multiple"):
        df[c_] = pd.to_numeric(df[c_], errors="coerce").astype(float)
    risk = (df["shares"].fillna(0) * (df["entry"] - df["stop"]).abs())
    df["risk_usd"] = risk
    cost = (df["pnl"].fillna(0) - df["pnl_adj"].fillna(df["pnl"]).fillna(0))
    df["r_adj"] = df["r_multiple"] - (cost / risk.where(risk > 0)).fillna(0.0)
    return df

P = load("P", 1); W = load("P", 2)
O = pd.concat([load(a, 1) for a in ("T1", "T2", "GY")])
SESS = sorted(P["date"].unique())
DPR = float(P.loc[P.risk_usd > 0, "risk_usd"].median())  # Primary median $ per 1R

ORIG5 = ["heat_fade_short", "heat_fade_long", "exhaustion_short", "orb20_a", "intraday_momentum"]
MFNS = ["MF1-945-flowsell-vwapup", "MF2-open-rsimidhi-flowsell", "MF3-open-flowsell-rsi5hi", "MF4-h40-open-flowsell",
        "MF5-flowsell-vwapup-rsi5hi", "NS1-rsidip-rsi5pop-long", "NS2-sma50break-overbought-short",
        "NS3-failed-vwap-reclaim-short", "NS4-pm-vwap-reclaim-oversold-short", "NS5-sma50-flush-oversold-long"]
RW6G1 = "RW6G1-ns2-up3-vwap2sd-short"
TWIN = {"MF2-open-rsimidhi-flowsell": "MF2-open-rsimidhi-flowsell-FD", "MF4-h40-open-flowsell": "MF4-h40-open-flowsell-FD"}

def lineup_cf(day, scen, strict=False):
    """Setups in counterfactual Primary on a session. scen A = strict since 10-06; B = owner's 10-08/10-09 probation adds kept."""
    s = set(ORIG5)
    if day >= "2026-10-12":       # Claude 10-10 WEEKLY: retire heat_fade_short/long; exhaustion 'retire or Testing only'
        s -= {"heat_fade_short", "heat_fade_long"}
        if not strict: s -= {"exhaustion_short"}
        # orb20_a 'keep 4 more sessions', intraday_momentum 'no evidence either way' -> stay
    if scen == "B":
        if day >= "2026-10-08": s |= set(MFNS)
        if day >= "2026-10-09": s |= {RW6G1}
        if day >= "2026-10-14": s -= {"NS3-failed-vwap-reclaim-short"}      # 10-13 nightly 'demotion candidate'
        if day >= "2026-10-16" and not strict: s -= {"NS2-sma50break-overbought-short"}  # bdi1015 'review under flag'
        if day >= "2026-10-20": s -= {"MF3-open-flowsell-rsi5hi", "MF5-flowsell-vwapup-rsi5hi"}  # P2/P3 yes
        if day >= "2026-10-21": s -= {RW6G1}                                 # N2 yes (raised 10-20 eve)
        # no promotion was ever recommended: RW5/RW3/MF3-FD, MF2/MF4/NS3-FD, L3, CWT14-pdl never enter
    return s

def actual_lineup(day):
    return set(P.loc[P.date == day, "strategy"])  # only for reporting

def cf_trades(scen, strict=False, twin_whatif=True):
    rows = []
    for d in SESS:
        L = lineup_cf(d, scen, strict)
        pd_ = P[(P.date == d) & P.strategy.isin(L)].copy(); pd_["src"] = "Primary"; pd_["usd"] = pd_["pnl_adj"].fillna(pd_["pnl"])
        rows.append(pd_)
        inP = set(pd_.strategy) | set(P.loc[(P.date == d), "strategy"])
        # setups not running in actual Primary that day: take their live trades from the account they ran in
        for s_ in L:
            ran_in_primary = s_ in actual_cfg(d)
            if ran_in_primary: continue
            o = O[(O.date == d) & (O.strategy == s_)].copy()
            if len(o):
                o["src"] = o["acc"]; o["usd"] = o["r_adj"] * DPR; rows.append(o)
        if twin_whatif:
            for s_, tw in TWIN.items():
                if s_ in L and tw not in L and d >= "2026-10-20":
                    w = W[(W.date == d) & (W.strategy == s_) & W.meta.str.contains("twin held", na=False)].copy()
                    if len(w):
                        w["src"] = "Primary what-if (twin held)"; w["usd"] = w["r_adj"] * DPR; rows.append(w)
    return pd.concat(rows, ignore_index=True)

# actual Primary config per session (from config/default.yaml history; see NOTES.md)
def actual_cfg(d):
    s = set(ORIG5)
    if d >= "2026-10-08": s |= set(MFNS)
    if d >= "2026-10-09": s |= {RW6G1}
    if d >= "2026-10-12": s -= set(ORIG5)
    if d >= "2026-10-15": s -= {"NS3-failed-vwap-reclaim-short"}
    if d >= "2026-10-16": s = (s - {"NS2-sma50break-overbought-short"}) | {"RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "MF3-open-flowsell-rsi5hi-FD"}
    if d >= "2026-10-20": s = (s - {"MF3-open-flowsell-rsi5hi", "MF5-flowsell-vwapup-rsi5hi"}) | {"MF2-open-rsimidhi-flowsell-FD", "MF4-h40-open-flowsell-FD", "NS3-failed-vwap-reclaim-short-FD"}
    if d >= "2026-10-21": s = (s - {"MF3-open-flowsell-rsi5hi-FD"}) | {"L3-gap-slope-fromopen-FD", "CWT14-failbrk-pdl-p10-lowvol-long"}
    if d >= "2026-10-22": s -= {"NS3-failed-vwap-reclaim-short-FD", RW6G1}
    if d >= "2026-10-23": s -= {"L3-gap-slope-fromopen-FD"}
    return s

# sanity: every actual Primary trade's setup is in actual_cfg that day
bad = P[[s not in actual_cfg(d) for s, d in zip(P.strategy, P.date)]]
assert bad.empty, bad[["date", "strategy"]].drop_duplicates()

A = P.copy(); A["usd"] = A["pnl_adj"].fillna(A["pnl"]); A["src"] = "Primary"
CFA, CFB = cf_trades("A"), cf_trades("B")
CFA_s, CFB_s = cf_trades("A", strict=True), cf_trades("B", strict=True)
CFB_nw = cf_trades("B", twin_whatif=False)

def daily(t):
    g = t.groupby("date").agg(usd=("usd", "sum"), r=("r_adj", "sum"), n=("r_adj", "size"))
    return g.reindex(SESS).fillna(0)

def summary(t):
    dd = daily(t); r = t["r_adj"]
    best = dd["r"].idxmax() if len(dd) else None
    rest = t[t.date != best]["r_adj"]
    green = [u > 0 for u in dd["usd"]]
    streak = mx = 0
    for g in green:
        streak = streak + 1 if g else 0; mx = max(mx, streak)
    m2 = max((sum(green[i - 10:i]) for i in range(10, len(green) + 1)), default=0)
    return dict(trades=len(t), usd=round(dd["usd"].sum(), 2), R=round(r.sum(), 2), avgR=round(r.mean(), 3) if len(r) else 0,
                win=round((r > 0).mean(), 3) if len(r) else 0, best_day=best, best_day_R=round(dd["r"].max(), 2),
                best_share=round(dd["r"].max() / r.sum(), 2) if r.sum() > 0 else None,
                avgR_wo_best=round(rest.mean(), 3) if len(rest) else 0, green=f"{sum(green)}/{len(green)}",
                streak_now=streak, streak_max=mx, m2_best10=f"{m2}/10", last10=f"{sum(green[-10:])}/10")

out = pd.DataFrame({"actual_usd": daily(A)["usd"], "actual_R": daily(A)["r"], "actual_n": daily(A)["n"],
                    "cfA_usd": daily(CFA)["usd"], "cfA_R": daily(CFA)["r"], "cfA_n": daily(CFA)["n"],
                    "cfB_usd": daily(CFB)["usd"], "cfB_R": daily(CFB)["r"], "cfB_n": daily(CFB)["n"]}).round(2)
out.to_csv(os.path.join(OUT, "per_session.csv"))

# attribution vs actual (actual minus CF-B per owner decision that departs from Claude's recommendation)
def ptr(strats, frm="0000", to="9999"):
    t = A[A.strategy.isin(strats) & (A.date >= frm) & (A.date <= to)]
    return t["usd"].sum(), t["r_adj"].sum(), len(t)
def otr(strats, frm="2026-10-12"):
    t = CFB[CFB.strategy.isin(strats) & (CFB.date >= frm) & (CFB.src != "Primary")]
    return t["usd"].sum(), t["r_adj"].sum(), len(t)
att = []
u, r, n = ptr(["RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "MF3-open-flowsell-rsi5hi-FD"])
att.append(("10-15 owner promotes RW5-FD/RW3-FD/MF3-FD (Claude: 'nothing met the Primary bar')", u, r, n))
for s_, lab in [("MF2-open-rsimidhi-flowsell-FD", "10-19 owner promotes MF2-FD (Claude: no recommendation; below the proposed 40-trade rule)"),
                ("MF4-h40-open-flowsell-FD", "10-19 owner promotes MF4-FD (Claude: no recommendation; below the proposed 40-trade rule)")]:
    u, r, n = ptr([s_]); base = s_.replace("-FD", "")
    w = CFB[(CFB.strategy == base) & (CFB.src == "Primary what-if (twin held)")]
    att.append((lab + f"; net of {len(w)} twin-held original-setup what-ifs", u - w.usd.sum(), r - w.r_adj.sum(), n))
u, r, n = ptr(["NS3-failed-vwap-reclaim-short-FD"]); att.append(("10-19 owner promotes NS3-FD (Claude P5: 'wait')", u, r, n))
u, r, n = ptr(["L3-gap-slope-fromopen-FD"]); att.append(("10-20 owner promotes L3-fromopen-FD (Claude: on the Graveyard list)", u, r, n))
u, r, n = ptr(["CWT14-failbrk-pdl-p10-lowvol-long"]); att.append(("10-20 owner promotes CWT14-pdl-p10-lowvol (Claude: no recommendation; backtest 'retire')", u, r, n))
u, r, n = otr(["orb20_a", "intraday_momentum"]); att.append(("10-11 owner demotes orb20_a + intraday_momentum (Claude: 'keep 4 more sessions' / 'no evidence')", -u, -r, n))
AT = pd.DataFrame(att, columns=["decision", "owner_minus_claude_usd", "owner_minus_claude_R", "trades"]).round(2)
AT.to_csv(os.path.join(OUT, "attribution.csv"), index=False)

# scenario A extra attribution: owner probation adds
attA = []
for lab, ss in [("10-08 owner adds MF1-5 + NS1-5 (research gates failed)", MFNS), ("10-09 owner adds RW6G1 (t 2.39 vs bar 4.76)", [RW6G1])]:
    u, r, n = ptr(ss); attA.append((lab, round(u, 2), round(r, 2), n))

def md(df, index=True):
    df = df.reset_index() if index else df
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)

per_setup = lambda t: t.groupby(["strategy", "src"]).agg(n=("r_adj", "size"), R=("r_adj", "sum"), usd=("usd", "sum")).round(2)
with open(os.path.join(OUT, "tables.md"), "w") as f:
    f.write(f"Primary median $ per 1R (shares x |entry-stop|, {int((P.risk_usd>0).sum())} trades): ${DPR:.2f}\n\n")
    f.write(md(out) + "\n\n")
    for nm, t in [("actual", A), ("CF-A strict since 10-06", CFA), ("CF-B owner probation adds kept", CFB),
                  ("CF-A strict, ambiguous=not recommended", CFA_s), ("CF-B strict, ambiguous=not recommended", CFB_s),
                  ("CF-B without twin-held what-ifs", CFB_nw)]:
        f.write(f"- **{nm}**: " + ", ".join(f"{k}={float(v) if hasattr(v, 'item') else v}" for k, v in summary(t).items()) + "\n")
    f.write("\n" + md(AT, False) + "\n\nScenario A extra:\n")
    for a in attA: f.write(f"- {a}\n")
    f.write("\nCF-A per setup\n\n" + md(per_setup(CFA)) + "\n\nCF-B per setup\n\n" + md(per_setup(CFB)) + "\n")
    f.write("\nActual per setup\n\n" + md(per_setup(A)) + "\n\nEducational only - not financial advice.\n")
print(open(os.path.join(OUT, "tables.md")).read())

# moves both Claude and the owner made: what the setup did after leaving Primary (same setup name, any account, to the last session)
AGREED = [("10-11 heat_fade_short demoted (Claude: retire)", "heat_fade_short", "2026-10-12"),
          ("10-11 heat_fade_long demoted (Claude: retire)", "heat_fade_long", "2026-10-12"),
          ("10-11 exhaustion_short demoted (Claude: 'retire or Testing only', ambiguous)", "exhaustion_short", "2026-10-12"),
          ("10-14 NS3 demoted (Claude 10-13: 'demotion candidate')", "NS3-failed-vwap-reclaim-short", "2026-10-15"),
          ("10-16 NS2 demoted (Claude 10-15: 'review under flag', ambiguous)", "NS2-sma50break-overbought-short", "2026-10-16"),
          ("10-20 MF3 (windowed) demoted (P2 yes)", "MF3-open-flowsell-rsi5hi", "2026-10-20"),
          ("10-20 MF5 demoted (P3 yes)", "MF5-flowsell-vwapup-rsi5hi", "2026-10-20"),
          ("10-21 MF3-FD demoted (N1 yes)", "MF3-open-flowsell-rsi5hi-FD", "2026-10-21"),
          ("10-22 NS3-FD demoted (N5/R3 yes)", "NS3-failed-vwap-reclaim-short-FD", "2026-10-22"),
          ("10-22 RW6G1 demoted (N2 yes)", RW6G1, "2026-10-22"),
          ("10-23 L3-fromopen-FD demoted (L3-1 yes)", "L3-gap-slope-fromopen-FD", "2026-10-23")]
ag = []
for lab, s_, frm in AGREED:
    t = O[(O.strategy == s_) & (O.date >= frm)]
    ag.append((lab, len(t), round(t.r_adj.sum(), 2), round(t.r_adj.sum() * DPR, 2), ",".join(sorted(set(t.acc)))))
AG = pd.DataFrame(ag, columns=["move", "trades_after", "R_after", "usd_at_primary_rate", "accounts"])
AG.to_csv(os.path.join(OUT, "agreed_moves.csv"), index=False)
ex = {k: daily(t).drop("2026-10-22") for k, t in [("actual", A), ("CF-A", CFA), ("CF-B", CFB)]}
with open(os.path.join(OUT, "tables.md"), "a") as f:
    f.write("\nAgreed moves (no difference between actual and counterfactual; value of the move)\n\n" + md(AG, False) + "\n")
    f.write("\nExcluding 2026-10-22: " + "; ".join(f"{k} ${v.usd.sum():.2f} / {v.r.sum():.2f}R" for k, v in ex.items()) + "\n")
print(md(AG, False)); print({k: (round(v.usd.sum(), 2), round(v.r.sum(), 2)) for k, v in ex.items()})
