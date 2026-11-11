"""RCOMPASS v2 (plan PLAN_V2.md, frozen before any v2 score). Post-flip vs NOT-YET-FLIPPED trades (both labels known at entry), within
family x side x 30-min entry bucket, ex-market gross, with a shared-day permutation null of flip times. 3 looks (F1-F3).
    python rcompass_v2.py <trades.parquet|csv> <compass_2y.csv.gz> [out_prefix]      python rcompass_v2.py --selftest
Educational only - not financial advice."""
import sys, os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rcompass import day_flips, mins
LK0, LK1, SPLIT = "2024-11-01", "2025-02-28", "2025-09-30"; BAR = 2.76; NDRAW = 500
RNG = np.random.default_rng(20261111)

def prep(t, FL):
    t = t[t.tod.astype(int) >= 1200].copy()
    t["date"] = t.date.astype(str); t["M"] = t.date.map(lambda d: FL.get(d, (None, {}))[0]); t = t[t.M.notna()].copy()
    t["family"] = np.where(t.setup.str.startswith("GEN"), "GEN", t.setup.str.split("-").str[0])
    t["e_min"] = t.tod.astype(int).map(mins); t["bucket"] = (t.e_min // 30) * 30
    t["aligned"] = np.where(t.side == np.where(t.M == "UP", 1, -1), "aligned", "counter")
    t["period"] = np.where(t.date <= SPLIT, "TRAIN", "VALID")
    t["sm"] = t.side * t.spy_move.fillna(0)
    for s, g in t.groupby("setup"):
        tr = g[g.period == "TRAIN"]; b = np.cov(tr.sm, tr.gross)[0, 1] / tr.sm.var(ddof=1) if len(tr) > 30 and tr.sm.var() > 0 else 0.0
        t.loc[g.index, "ex"] = g.gross - b * g.sm
    return t

def contrast(g, post):
    """per bucket: day-mean(post) - day-mean(not-yet); returns combined diff, combined t, n post days."""
    out = []
    for bk, gb in g.groupby("bucket"):
        p = post.loc[gb.index]
        a = gb[p].groupby("date").ex.mean(); b = gb[~p].groupby("date").ex.mean()
        if len(a) < 3 or len(b) < 3: continue
        d = a.mean() - b.mean(); se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
        out.append((d, d / se if se > 0 else 0.0, len(a)))
    if not out: return np.nan, np.nan, 0
    w = np.array([o[2] for o in out], float)
    return float(np.average([o[0] for o in out], weights=w)), float(np.sum([o[1] * np.sqrt(o[2]) for o in out]) / np.sqrt(w.sum())), int(w.sum())

def book_S(A, flip_by_day):
    """aligned trades A; flip_by_day: date -> flip minute or None. Returns S (post-trade-weighted mean contrast) and per-family rows."""
    post = A.date.map({k: (np.nan if v is None else v) for k, v in flip_by_day.items()}).astype(float)
    post = (post < A.e_min) & post.notna()
    rows, num, den = [], 0.0, 0
    for (fam, side), g in A.groupby(["family", "side"]):
        d, tt, n = contrast(g, post.loc[g.index])
        if n: rows.append(dict(family=fam, side=side, diff=d, t=tt, post_days=n, n=len(g), n_post=int(post.loc[g.index].sum()))); num += d * n; den += n
    return (num / den if den else np.nan), pd.DataFrame(rows), post

def run_look(t, FL, k, label):
    A = t[t.aligned == "aligned"]
    flip = {d: FL[d][1].get(k) for d in A.date.unique()}
    S, F, post = book_S(A, flip)
    # gross contrast (same buckets) for the gross-first check
    Ag = A.assign(ex=A.gross); Sg, _, _ = book_S(Ag, flip)
    # book day-t: per day, mean ex of post minus mean ex of not-yet in the same buckets (pooled), Welch across days
    a = A[post].groupby("date").ex.mean(); b = A[~post].groupby("date").ex.mean()
    bt = (a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b)) if len(a) > 2 and len(b) > 2 else np.nan
    wo = (a.drop(a.idxmin()).mean() - b.mean()) if len(a) > 3 else np.nan
    # shared-day null: permute flip times across reading days with the same M (one permutation for all family-sides)
    days = pd.Series({d: FL[d][0] for d in flip}); draws = []
    for _ in range(NDRAW):
        perm = {}
        for m, ds in days.groupby(days):
            idx = list(ds.index); vals = [flip[d] for d in idx]; RNG.shuffle(vals); perm.update(dict(zip(idx, vals)))
        s, _, _ = book_S(A, perm); draws.append(s)
    draws = np.array(draws); p = float(np.mean(draws <= S)) if np.isfinite(S) else np.nan
    print(f"  [{label} {k}] aligned trades {len(A)}, post-flip {int(post.sum())} on {A[post].date.nunique()} days | S_ex {S:+.4f} (gross {Sg:+.4f}) | "
          f"null p {p:.3f} (5th pct {np.nanpercentile(draws, 5):+.4f}) | book day-t {bt:+.2f}, w/o worst post day {wo:+.4f} | "
          f"family-sides worse {int((F['diff'] < 0).sum()) if len(F) else 0} of {len(F)}")
    return dict(look=k, period=label, S=S, Sg=Sg, p=p, t=bt, wo=wo, worse=(F['diff'] < 0).mean() if len(F) else np.nan), F.assign(look=k, period=label)

def main():
    tp, cp_, pre = sys.argv[1], sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else "rcompass_v2")
    t = pd.read_parquet(tp) if tp.endswith(".parquet") else pd.read_csv(tp); C = pd.read_csv(cp_)
    for df in (t, C): df["date"] = df["date"].astype(str)
    assert not ((t.date >= LK0) & (t.date <= LK1)).any() and not ((C.date >= LK0) & (C.date <= LK1)).any()
    FL = {d: day_flips(g) for d, g in C.groupby("date")}
    t = prep(t, FL)
    print(f"afternoon trades on reading days {len(t)}, setups {t.setup.nunique()}, days {t.date.nunique()} (TRAIN {t[t.period == 'TRAIN'].date.nunique()}, VALID {t[t.period == 'VALID'].date.nunique()})")
    res, fams = [], []
    for k in ("F1", "F2", "F3"):
        for per in ("TRAIN", "VALID"):
            r, F = run_look(t[t.period == per], FL, k, per); res.append(r); fams.append(F)
    R = pd.DataFrame(res); F = pd.concat(fams); F.to_csv(f"{pre}_family.csv", index=False); R.to_csv(f"{pre}_looks.csv", index=False)
    print("\nverdict per look (PLAN_V2 pass rule: S<0 & gross<0 both periods, null p<0.05 both, >=60% family-sides worse both, VALID day-t <= -2.76, w/o worst day < 0):")
    for k, g in R.groupby("look"):
        tr, va = g[g.period == "TRAIN"].iloc[0], g[g.period == "VALID"].iloc[0]
        ok = all([tr.S < 0, va.S < 0, tr.Sg < 0, va.Sg < 0, tr.p < 0.05, va.p < 0.05, tr.worse >= 0.6, va.worse >= 0.6, va.t <= -BAR, va.wo < 0])
        print(f"  {k}: {'STANDBY CANDIDATE' if ok else 'closed'}  (TRAIN S {tr.S:+.4f} p {tr.p:.2f} worse {tr.worse:.0%} | VALID S {va.S:+.4f} p {va.p:.2f} worse {va.worse:.0%} t {va.t:+.2f})")
    print("Educational only - not financial advice.")

def selftest():
    global NDRAW; NDRAW = 60
    rng = np.random.default_rng(1); T = [f"{h:02d}:{m:02d}" for h in range(9, 16) for m in (0, 15, 30, 45) if 585 <= h * 60 + m <= 945]
    C, trades = [], []
    dates = pd.bdate_range("2025-03-03", periods=120).strftime("%Y-%m-%d")
    for i, d in enumerate(dates):
        flip = 780 if i % 3 == 0 else None
        for tt in T:
            tm = mins(tt)
            C.append(dict(date=d, T=tt, spy_fo=(-0.002 if flip and tm >= flip else 0.004), checkpoint=("UP" if tm >= 630 else np.nan),
                          w60=("DOWN-confirmed" if flip and tm >= flip else "UP-confirmed"),
                          gate1_state=(("MIXED" if flip and tm >= flip else "UP") if (tm >= 600 and (tm - 600) % 30 == 0) else np.nan)))
        for j in range(40):
            tod = int(rng.choice([1215, 1245, 1315, 1345, 1415, 1445])); em = mins(tod)
            post = flip is not None and flip < em
            g = rng.normal(0, 1) - (0.5 if post else 0.0)                      # planted: post-flip aligned trades worse
            trades.append(dict(setup=f"S{j % 4}-x", side=1, date=d, tod=tod, xtod=1555, r=g, gross=g, spy_move=rng.normal(0, 0.002)))
    t = pd.DataFrame(trades); Cd = pd.DataFrame(C); FL = {d: day_flips(g) for d, g in Cd.groupby("date")}
    t = prep(t, FL); t["period"] = "VALID"
    r, F = run_look(t, FL, "F1", "VALID"); assert r["S"] < -0.3 and r["p"] < 0.05, r
    t2 = t.copy(); t2["ex"] = rng.normal(0, 1, len(t2))                         # null: no effect
    r2, _ = run_look(t2, FL, "F1", "VALID-null"); assert r2["p"] > 0.02, r2
    print("selftest ok: planted post-flip effect found (S < 0, null p < 0.05); no-effect data not flagged")

if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
