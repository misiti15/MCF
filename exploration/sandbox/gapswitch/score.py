"""GAPSWITCH scoring (exploration/findings/gapswitch_prereg.md): SPY gap-up day switch on the Primary book.
Book = research/primshorts_1126/booksim.sim_day (Primary rules, LATCH-OPEN off, no open marks), candidates =
regsteer_1126 cand.parquet (bench10 lots, LIVE-L shorts / LR8 research NM-ETF). Locked block never read (asserted).
Usage (from the worktree root): python exploration/sandbox/gapswitch/score.py RSW_DIR. Educational only - not financial advice."""
import sys, warnings
warnings.filterwarnings("ignore")
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "research/primshorts_1126"))
from booksim import sim_day  # noqa: E402
RSW = Path(sys.argv[1]); LOCK = ("2024-11-01", "2025-02-28")
L3, RW3, RW5, ETF = ("L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
                     "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "NM-ETF-late-dip-di-long")
ROSTER = {"A": [RW3, RW5, ETF], "B": [L3, RW3, RW5, ETF]}
SHORT = {L3, RW3, RW5}
CFG = {"A-G25": ("A", 0.0025, "off"), "A-G50": ("A", 0.005, "off"), "B-G25": ("B", 0.0025, "off"),
       "B-G50": ("B", 0.005, "off"), "A-H25": ("A", 0.0025, "half")}
def period(d):
    if ("2024-10-01" <= d <= "2024-10-31") or ("2025-03-01" <= d <= "2025-09-30"): return "FIT"
    if "2025-10-01" <= d <= "2026-11-04": return "CHECK"
    if "2023-01-03" <= d <= "2024-09-13": return "T2"
    return "none"
def nolock(ds):
    d = pd.Series(list(ds)).astype(str); assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked row"
C = pd.read_parquet(RSW / "cand.parquet"); C["date"] = C.date.astype(str); nolock(C.date.unique())
G = pd.read_parquet(RSW / "st/gap.parquet"); G["date"] = G.date.astype(str); nolock(G.date); gap = G.set_index("date").gap
SESS = {p: sorted(d for d in gap.index if period(d) == p) for p in ("FIT", "CHECK", "T2")}
def book(roster, mode):
    """per-day per-setup R for the roster under mode: base / off (no shorts) / half (shorts weight 0.5)."""
    S = ROSTER[roster]; N = len(S)
    p = C[C.setup.isin(S)].copy(); p["si"] = p.setup.map({s: i for i, s in enumerate(S)})
    if mode == "off": p = p[~p.setup.isin(SHORT)]
    p = p.sort_values(["date", "em", "si", "symbol"], kind="mergesort")
    w = np.array([0.5 if (mode == "half" and s in SHORT) else 1.0 for s in S]); lo = np.zeros(N, bool)
    rows = {}
    for d, g in p.groupby("date"):
        R, tk, tot, _ = sim_day(g.si.to_numpy(), pd.factorize(g.symbol)[0], g.side.to_numpy(float), g.entry.to_numpy(float),
                                g.risk.to_numpy(float), np.zeros(len(g)), g.em.to_numpy(int), g.xm.to_numpy(int),
                                g.r.to_numpy(float), lambda o, m: np.full(len(o), np.nan), N, w, lo)
        rows[d] = {**{S[i]: R[i] * w[i] for i in range(N)}, "N": int(tk.sum())}
    return pd.DataFrame.from_dict(rows, orient="index").reindex(columns=S + ["N"])
BK = {}
for r in ROSTER:
    for m in ("base", "off", "half"):
        if r == "B" and m == "half": continue
        BK[(r, m)] = book(r, m).fillna(0.0)
rng = np.random.default_rng(20261128)
def dayt(x):
    se = x.std(ddof=1) / np.sqrt(len(x)); return x.mean() / se if se > 0 else np.nan
out, per_setup = [], []
for cid, (ro, th, mode) in CFG.items():
    S = ROSTER[ro]
    for per, days in SESS.items():
        b = BK[(ro, "base")].reindex(days, fill_value=0.0); v = BK[(ro, mode)].reindex(days, fill_value=0.0)
        fire = pd.Series([bool(gap.get(d, np.nan) >= th) for d in days], index=days)  # NaN gap -> no fire
        sw = b[S].where(~fire, v[S], axis=0)
        bd, sd = b[S].sum(1), sw[S].sum(1); diff = sd - bd
        dall = (v[S].sum(1) - bd).to_numpy()   # gain if the switch fired on each day
        k = int(fire.sum()); n = len(days); obs = diff.sum() / n
        sims = np.array([dall[rng.choice(n, size=k, replace=False)].sum() / n for _ in range(1000)]) if k else np.zeros(1)
        pval = ((sims >= obs - 1e-12).sum() + 1) / (len(sims) + 1)
        gpos = diff[diff > 0]
        best_share = diff.max() / diff.sum() if diff.sum() > 0 else np.nan
        def wob(x): return (x.sum() - x.max()) / (len(x) - 1)
        lots_b = int(b.N.sum()); lots_s = int(b.N.where(~fire, v.N).sum())
        out.append(dict(cfg=cid, split=per, sessions=n, fire_days=k, lots_base=lots_b, lots_sw=lots_s,
                        Rday_base=bd.mean(), Rday_sw=sd.mean(), gain_day=obs, t=dayt(diff), p_rand=pval,
                        rand_med=np.median(sims), red_base=int((bd < 0).sum()), red_sw=int((sd < 0).sum()),
                        worst5_base=bd.nsmallest(5).sum(), worst5_sw=sd.nsmallest(5).sum(),
                        wobd_base=wob(bd), wobd_sw=wob(sd), best_share=best_share,
                        gain_on_fire_days_mean=diff[fire].mean() if k else np.nan))
        for s in S:
            ds = (sw[s] - b[s]).sum()
            per_setup.append(dict(cfg=cid, split=per, setup=s.split("-")[0], dR_total=ds, dR_day=ds / n,
                                  base_R_on_fire=b[s][fire].sum(), base_R_other=b[s][~fire].sum()))
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
O = pd.DataFrame(out); P = pd.DataFrame(per_setup)
print("## Config results (book R per session, LIVE-L shorts)"); print(O.round(3).to_string(index=False))
print("\n## Per setup"); print(P.round(2).to_string(index=False))
# descriptive: base book R by gap bucket per split
print("\n## Descriptive: base book R/day by SPY gap bucket")
for ro in ROSTER:
    for per, days in SESS.items():
        b = BK[(ro, "base")].reindex(days, fill_value=0.0); g = gap.reindex(days)
        bk = pd.cut(g, [-1, -0.005, -0.0025, 0.0025, 0.005, 1])
        t = b.assign(bk=bk).groupby("bk", observed=True)[ROSTER[ro]].agg(["mean"]).round(3)
        t["days"] = b.assign(bk=bk).groupby("bk", observed=True).size()
        print(f"[{ro} {per}]"); print(t.to_string())
O.to_csv(Path(__file__).with_name("results.csv"), index=False); P.to_csv(Path(__file__).with_name("per_setup.csv"), index=False)
