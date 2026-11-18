"""U6 scoring: verdicts per PLAN.md, side splits, random controls, Move Hunt capture. Educational only - not financial advice."""
import glob, json, sys
import numpy as np, pandas as pd

OUT, MOVES, DST = sys.argv[1], sys.argv[2], sys.argv[3]
T = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{OUT}/*_t.csv"))], ignore_index=True)
RD = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{OUT}/*_r.csv"))], ignore_index=True)
INF = pd.DataFrame([json.load(open(f)) for f in sorted(glob.glob(f"{OUT}/*.json"))]).set_index("date")
for X in (T, RD):
    X["part"] = np.where(X.date >= "2026-10-06", "CHECK", "FIT")
T["spy_up"] = T.date.map(INF.spy_oc) > 0
TB = max(1.5, np.sqrt(2 * np.log(19)))
NAMES = {"M1": "U6-OD-drive", "M2": "U6-GAPGO-nonearn", "M3": "U6-SECLAG", "M4": "U6-LEVETF-drive", "M5": "U6-PMTREND"}


def ct(x):
    """day-clustered t of the per-trade mean."""
    m = x.r.mean(); n = len(x)
    s = ((x.r - m).groupby(x.date).sum() ** 2).sum()
    return m / (np.sqrt(s) / n) if s > 0 else np.nan


def stats(x, days_all):
    if len(x) == 0:
        return dict(n=0)
    dr = x.groupby("date").r.sum()
    tot = dr.sum(); bd = dr.idxmax(); rest = x[x.date != bd]
    return dict(n=len(x), days=len(dr), win=(x.r > 0).mean(), avg=x.r.mean(), avg_gross=x.r_gross.mean(), total=tot,
                t=ct(x), wo_best=rest.r.mean() if len(rest) else np.nan,
                best_day=bd, best_share=dr.max() / tot if tot > 0 else np.nan,
                worst_day=dr.min(), green=(dr > 0).mean(), tr_per_sess=len(x) / days_all,
                up=x[x.spy_up].r.mean(), dn=x[~x.spy_up].r.mean(),
                mpos=(x.groupby(x.date.str[:7]).r.mean() > 0).mean(), nm=x.date.str[:7].nunique())


rows = []
for part in ("FIT", "CHECK"):
    nd = (INF.index >= "2026-10-06").sum() if part == "CHECK" else (INF.index < "2026-10-06").sum()
    for sid in sorted(T.setup.unique()):
        for side in ("both", 1, -1):
            x = T[(T.part == part) & (T.setup == sid)]
            r = RD[(RD.part == part) & (RD.setup == sid)]
            if side != "both":
                if sid == "M4" and side == -1:
                    continue
                x = x[x.side == side]; r = r[r.side == side]
            st = stats(x, nd)
            st.update(part=part, setup=sid, name=NAMES[sid], side=side, rand_avg=r.r.mean() if len(r) else np.nan, rand_n=len(r))
            rows.append(st)
S = pd.DataFrame(rows)
S.to_csv(f"{DST}/u6_results.csv", index=False)

# verdicts
V = []
for sid in sorted(T.setup.unique()):
    f = S[(S.part == "FIT") & (S.setup == sid) & (S.side == "both")].iloc[0]
    c = S[(S.part == "CHECK") & (S.setup == sid) & (S.side == "both")].iloc[0]
    fp = bool(f.n >= 100 and f.avg > 0 and f.t >= TB and f.up > 0 and f.dn > 0 and f.mpos >= 0.6)
    cp = bool(c.n >= 25 and c.avg > 0 and c.wo_best > 0 and c.best_share < 0.5 and c.avg > c.rand_avg)
    V.append(dict(setup=sid, name=NAMES[sid], fit_pass=fp, check_pass=cp,
                  verdict="PASS" if fp and cp else ("WATCH" if fp or cp else "FAIL")))
V = pd.DataFrame(V); V.to_csv(f"{DST}/u6_verdicts.csv", index=False)

# Move Hunt capture (tradable set, 12 sessions)
M = pd.read_csv(MOVES); M = M[M.set == "tradable"].copy()
M["dmin"] = M.decision.str[:2].astype(int) * 60 + M.decision.str[3:].astype(int) - 570
M["xmin"] = M.extreme.str[:2].astype(int) * 60 + M.extreme.str[3:].astype(int) - 570
M["sd"] = np.where(M.side == "long", 1, -1)
M["live"] = M.caught_by.notna()
M["cat"] = np.select([M.symbol.isin(set(T[T.setup == "M4"].symbol) | set(RD[RD.setup == "M4"].symbol)) | M.symbol.str.match(r"^(SQQQ|TQQQ|UVXY|UVIX|VXX|VIXY|SOXS|SOXL|SPXU|SPXS|SDS|SPDN|SDOW|TZA|QID|PSQ|RWM|LABD|SNDQ|TSLQ|AMZD|SSPC|SCO|ERY)$"),
                      M.dmin <= 15, (M.gap.abs() >= 2) & (np.sign(M.gap) == M.sd), M.dmin >= 210],
                     ["lev/inv ETF", "opening drive", "gap-go", "afternoon"], "other")
cap = []
TC = T[T.date.isin(M.date.unique())]
for sid in list(sorted(T.setup.unique())) + ["ALL"]:
    x = TC if sid == "ALL" else TC[TC.setup == sid]
    j = M.merge(x[["date", "symbol", "side", "fill_min", "r", "setup"]].rename(columns={"side": "sd"}), on=["date", "symbol", "sd"], how="left")
    j["hit"] = (j.fill_min >= j.dmin - 30) & (j.fill_min <= j.xmin)
    h = j[j.hit].drop_duplicates(["date", "symbol", "sd", "setup"])
    mv = h.drop_duplicates(["date", "symbol", "sd"])
    new = mv[~mv.live]
    cap.append(dict(setup=sid, moves=len(M), captured=len(mv), new=len(new), live=int(M.live.sum()),
                    rate_live=M.live.mean(), rate_with=(M.live.sum() + len(new)) / len(M),
                    r_captured=h.r.sum(), r_new=h[~h.live].r.sum(),
                    setup_trades_in_window=len(x), setup_r_in_window=x.r.sum(),
                    **{f"new_{c}": int((new.cat == c).sum()) for c in ["opening drive", "gap-go", "lev/inv ETF", "afternoon", "other"]}))
CP = pd.DataFrame(cap); CP.to_csv(f"{DST}/u6_capture.csv", index=False)
cats = M.groupby("cat").agg(moves=("live", "size"), live=("live", "sum"))

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
cols = ["part", "setup", "side", "n", "tr_per_sess", "win", "avg_gross", "avg", "total", "t", "wo_best", "best_share", "worst_day", "green", "up", "dn", "mpos", "rand_avg"]
print("t bar", round(TB, 3))
print(S[cols].round(3).to_string(index=False))
print(V.to_string(index=False))
print(cats)
print(CP.round(3).to_string(index=False))
# cost share
T["cost"] = T.r_gross - T.r
print(T.groupby(["part", "setup"]).agg(cost_R=("cost", "mean"), stop_frac=("kind", lambda k: (k == 0).mean()), tgt_frac=("kind", lambda k: (k == 1).mean())).round(3))
