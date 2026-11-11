"""RCOMPASS stage 1 (descriptive; plan research/rcompass/PLAN.md frozen 2026-11-09 23:30 ET before any data).
Morning reading M from the 10:30 / 11:00 checkpoint; flips F1 (SPY back across its open at a mark >= 11:15), F2 (W60
confirmed opposite at a mark >= 11:15), F3 (GATE1 state != M at a checkpoint >= 11:30). A mark T is usable for an entry
whose bar ends at E only if T < E (published at T+1 min at the earliest; Skeptic 2026-11-10 01:00) - applied here from the
compass table itself, independent of any pre-computed tags. Afternoon trades (bar end >= 12:00) on morning-reading days:
POST-FLIP (flip mark < entry) vs HELD-DAY (no flip that day) vs PRE-FLIP (flip later), per family x side x alignment, within
entry-hour buckets; gross and net R; ex-market (residual of R on SPY's move over the hold); SPY-move terciles; same-day
random standby of equal size (200 draws). 3 looks (F1-F3). 0 configs scored as rules.
    python rcompass.py <trades.csv[.gz]|.parquet> <compass_2y.csv.gz> [out_prefix]      python rcompass.py --selftest
Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd

LK0, LK1 = "2024-11-01", "2025-02-28"
RNG = np.random.default_rng(20261110)
BUCKETS = [(1200, 1259, "12h"), (1300, 1359, "13h"), (1400, 1600, "14h+")]
OPP = {"UP": "DOWN-confirmed", "DOWN": "UP-confirmed"}


def mins(hhmm):
    """'HH:MM' or HHMM int -> minutes since midnight."""
    if isinstance(hhmm, str): h, m = hhmm.split(":"); return int(h) * 60 + int(m)
    return int(hhmm) // 100 * 60 + int(hhmm) % 100


def day_flips(C):
    """compass rows of one day -> (M, {F1: t_f, F2: t_f, F3: t_f}) with t_f in minutes (None = no flip)."""
    C = C.assign(Tm=C["T"].map(mins)).sort_values("Tm")
    def cp(t):
        r = C[C.Tm == t]
        return r.checkpoint.iloc[0] if len(r) else None
    M = cp(630) if cp(630) in ("UP", "DOWN") else (cp(660) if cp(660) in ("UP", "DOWN") else None)
    if M is None: return None, {}
    s = 1 if M == "UP" else -1; out = {}
    a = C[(C.Tm >= 675) & (np.sign(C.spy_fo) == -s)]; out["F1"] = int(a.Tm.iloc[0]) if len(a) else None
    b = C[(C.Tm >= 675) & (C.w60 == OPP[M])]; out["F2"] = int(b.Tm.iloc[0]) if len(b) else None
    cps = C[(C.Tm >= 690) & (C.Tm <= 930) & ((C.Tm - 600) % 30 == 0) & C.gate1_state.notna()]
    c = cps[cps.gate1_state != M]; out["F3"] = int(c.Tm.iloc[0]) if len(c) else None
    return M, out


def classify(entry_min, t_f):
    if t_f is None: return "held_day"
    return "post_flip" if t_f < entry_min else "pre_flip"            # strict: mark usable only after T


def spy_move_from_marks(C_day, e_min, x_min):
    """fallback (labelled): SPY % from open at the last mark <= exit minus that at the last mark < entry (15-min grain)."""
    Tm = C_day["T"].map(mins).to_numpy(); fo = C_day.spy_fo.to_numpy()
    i = np.flatnonzero(Tm < e_min); j = np.flatnonzero(Tm <= x_min)
    return float(fo[j[-1]] - fo[i[-1]]) if len(i) and len(j) else np.nan


def day_t(a, b):
    """difference of day-level means (a minus b) and its t, days as the unit."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 3 or len(b) < 3: return np.nan, np.nan
    d = a.mean() - b.mean(); se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return d, (d / se if se > 0 else np.nan)


def selftest():
    T = [f"{h:02d}:{m:02d}" for h in range(9, 16) for m in (0, 15, 30, 45) if (9 * 60 + 45) <= h * 60 + m <= 15 * 60 + 45]
    def day(fo, chk1030="UP", w60="UP-confirmed", g="UP", flip_at=None, w_flip=None, g_flip=None):
        rows = []
        for t in T:
            tm = mins(t)
            rows.append(dict(T=t, spy_fo=(-0.001 if (flip_at and tm >= flip_at) else fo),
                             checkpoint=(chk1030 if tm >= 630 else np.nan),
                             w60=("DOWN-confirmed" if (w_flip and tm >= w_flip) else w60),
                             gate1_state=(("MIXED" if (g_flip and tm >= g_flip) else g) if (tm >= 600 and (tm - 600) % 30 == 0) else np.nan)))
        return pd.DataFrame(rows)
    M, f = day_flips(day(0.004)); assert M == "UP" and f == {"F1": None, "F2": None, "F3": None}, f
    M, f = day_flips(day(0.004, flip_at=780, w_flip=795, g_flip=810)); assert f == {"F1": 780, "F2": 795, "F3": 810}, f
    M, f = day_flips(day(0.004, flip_at=660)); assert f["F1"] == 675, f                    # flips before 11:15 count from 11:15
    M, f = day_flips(day(0.001, chk1030="UNCONFIRMED")); assert M is None
    assert classify(mins(1305), 780) == "post_flip" and classify(mins(1300), 780) == "pre_flip"   # mark 13:00 not usable at 13:00
    assert classify(mins(1400), None) == "held_day"
    C = day(0.004); assert abs(spy_move_from_marks(C, mins(1215), mins(1400)) - 0.0) < 1e-12
    d, t = day_t([1, 1.1, 0.9, 1.0], [0, 0.1, -0.1, 0.0]); assert abs(d - 1) < 1e-9 and t > 10
    print("selftest ok: morning reading, F1/F2/F3 flip times (>= 11:15 / 11:30), strict-< classification, SPY-move fallback, day-t")


def main():
    tp, cp_, pre = sys.argv[1], sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else "rcompass")
    t = pd.read_parquet(tp) if tp.endswith(".parquet") else pd.read_csv(tp)
    C = pd.read_csv(cp_)
    for df in (t, C): df["date"] = df["date"].astype(str)
    assert not ((t.date >= LK0) & (t.date <= LK1)).any() and not ((C.date >= LK0) & (C.date <= LK1)).any()
    t = t[t.tod.astype(int) >= 1200].copy()
    t["family"] = np.where(t.setup.str.startswith("GEN"), "GEN", t.setup.str.split("-").str[0])
    has_gross, has_spy = "gross" in t.columns, "spy_move" in t.columns
    print(f"afternoon trades {len(t)}, setups {t.setup.nunique()}, days {t.date.nunique()}; gross column: {has_gross}; "
          f"spy_move column: {has_spy} (else 15-min mark fallback, labelled)")
    CD = {d: g for d, g in C.groupby("date")}
    FL = {d: day_flips(g) for d, g in CD.items()}
    nd = sum(1 for v in FL.values() if v[0]); print(f"compass days {len(FL)}; morning reading on {nd} "
          f"(UP {sum(1 for v in FL.values() if v[0] == 'UP')}, DOWN {sum(1 for v in FL.values() if v[0] == 'DOWN')})")
    for k in ("F1", "F2", "F3"):
        ts_ = [v[1][k] for v in FL.values() if v[0] and v[1][k] is not None]
        print(f"  {k}: flips on {len(ts_)} of {nd} reading days; median flip time "
              f"{(int(np.median(ts_)) // 60):02d}:{(int(np.median(ts_)) % 60):02d}" if ts_ else f"  {k}: no flips")
    t["M"] = t.date.map(lambda d: FL.get(d, (None, {}))[0])
    t = t[t.M.notna()].copy()
    t["e_min"] = t.tod.astype(int).map(mins); t["x_min"] = t.xtod.astype(int).map(mins) if "xtod" in t.columns else 955
    t["aligned"] = np.where(t.side == np.where(t.M == "UP", 1, -1), "aligned", "counter")
    t["bucket"] = pd.cut(t.tod.astype(int), [1199, 1259, 1359, 1600], labels=[b[2] for b in BUCKETS])
    if not has_spy:
        t["spy_move"] = [spy_move_from_marks(CD[d], e, x) for d, e, x in zip(t.date, t.e_min, t.x_min)]
    t["spy_signed"] = t.spy_move * t.side
    fam_rows = []
    for k in ("F1", "F2", "F3"):
        t[k] = [classify(e, FL[d][1][k]) for d, e in zip(t.date, t.e_min)]
    print("\nskip funnel: afternoon trades on reading days", len(t), "| by F1 class", t.F1.value_counts().to_dict())
    for k in ("F1", "F2", "F3"):
        for (fam, side, al), g in t.groupby(["family", "side", "aligned"]):
            # ex-market residual within this family-side-alignment (pooled OLS of r on signed SPY move)
            x = g.spy_signed.fillna(0).to_numpy(); y = g.r.to_numpy()
            b = np.cov(x, y)[0, 1] / x.var(ddof=1) if x.var() > 0 else 0.0
            g = g.assign(r_ex=y - b * x)
            row = dict(look=k, family=fam, side=side, aligned=al, n=len(g), days=g.date.nunique(), beta_spy=round(b, 2))
            for cls in ("post_flip", "held_day", "pre_flip"):
                row[f"n_{cls}"] = int((g[k] == cls).sum())
            for col, nm in (("r", "net"), ("gross", "gross"), ("r_ex", "ex")):
                if col not in g.columns: continue
                diffs = []
                for bk, gb in g.groupby("bucket", observed=True):        # within entry-hour buckets
                    a = gb[gb[k] == "post_flip"].groupby("date")[col].mean(); h = gb[gb[k] == "held_day"].groupby("date")[col].mean()
                    d_, t_ = day_t(a, h)
                    if np.isfinite(d_): diffs.append((d_, t_, len(a)))
                if diffs:
                    w = np.array([z[2] for z in diffs], float)
                    row[f"{nm}_post_minus_held"] = round(float(np.average([z[0] for z in diffs], weights=w)), 4)
                    row[f"{nm}_t_comb"] = round(float(np.sum([z[1] * np.sqrt(z[2]) for z in diffs]) / np.sqrt(w.sum())), 2)
                row[f"{nm}_post"] = round(float(g[g[k] == "post_flip"][col].mean()), 4) if (g[k] == "post_flip").any() else None
                row[f"{nm}_held"] = round(float(g[g[k] == "held_day"][col].mean()), 4) if (g[k] == "held_day").any() else None
            # SPY-afternoon terciles (hindsight, descriptive): post minus held inside each
            q = pd.qcut(g.spy_signed.rank(method="first"), 3, labels=["spy_against", "spy_flat", "spy_with"])
            for tq, gq in g.groupby(q, observed=True):
                a, h = gq[gq[k] == "post_flip"].r, gq[gq[k] == "held_day"].r
                row[f"{tq}_post_minus_held"] = round(float(a.mean() - h.mean()), 4) if len(a) and len(h) else None
            # same-day random standby of equal size
            ex = []
            for d, gd in g.groupby("date"):
                rm = gd[gd[k] == "post_flip"]
                kk = len(rm)
                if kk == 0 or kk == len(gd): continue
                draws = [gd.r.to_numpy()[RNG.choice(len(gd), kk, replace=False)].mean() for _ in range(200)]
                ex.append(np.mean(draws) - rm.r.mean())
            if len(ex) >= 3:
                ex = np.array(ex); row["standby_excess"] = round(float(ex.mean()), 4)
                row["standby_t"] = round(float(ex.mean() / (ex.std(ddof=1) / np.sqrt(len(ex)))), 2) if ex.std() > 0 else None
                row["standby_days"] = len(ex)
            fam_rows.append(row)
    R = pd.DataFrame(fam_rows); pd.set_option("display.width", 400); pd.set_option("display.max_columns", 60)
    R.to_csv(f"{pre}_family.csv", index=False)
    show = [c for c in ["look", "family", "side", "aligned", "n", "n_post_flip", "n_held_day", "net_post", "net_held",
                        "net_post_minus_held", "net_t_comb", "gross_post_minus_held", "ex_post_minus_held", "ex_t_comb",
                        "spy_against_post_minus_held", "spy_flat_post_minus_held", "spy_with_post_minus_held",
                        "standby_excess", "standby_t", "standby_days"] if c in R.columns]
    print(R[show].to_string(index=False))
    print("\nsummary per look: family-sides with post-flip worse than held (ex-market), and standby excess > 0")
    for k in ("F1", "F2", "F3"):
        r = R[R.look == k]
        print(f"  {k}: ex-market post<held in {int((r.ex_post_minus_held < 0).sum())} of {int(r.ex_post_minus_held.notna().sum())}; "
              f"standby excess > 0 in {int((r.standby_excess > 0).sum())} of {int(r.standby_excess.notna().sum())}" if "ex_post_minus_held" in r else f"  {k}: n/a")
    print("\npost_flip = entry after the flip mark (strict <); held_day = no flip that day; pre_flip = afternoon entry before a later flip"
          "\n(reported, not compared). ex = residual of R on the trade-signed SPY move over the hold; SPY terciles are hindsight"
          "\n(descriptive). standby_excess = mean R of a same-day random block of equal size minus mean R of the post-flip block"
          "\n(> 0 = the rule removes worse trades than chance). Gross only if the input carries a gross column.")
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
