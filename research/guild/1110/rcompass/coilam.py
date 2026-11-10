"""COILAM scorer (PLAN_COIL.md, frozen 2026-11-10 03:40 ET). One rule: skip CWT12 coil longs when e_checkpoint == DOWN.
    python coilam.py <coil_tagged.csv.gz> > coilam_out.txt          python coilam.py --selftest
Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
LK0, LK1, SPLIT = "2024-11-01", "2025-02-28", "2025-09-30"; N, BAR = 2605, 3.57
RNG = np.random.default_rng(20261110)


def block_excess(g, col):
    """per day: mean of k random removals minus mean of the rule removals (200 draws); -> list of (date, excess)."""
    out = []
    for d, gd in g.groupby("date"):
        k = int(gd.rm.sum())
        if k == 0 or k == len(gd): continue
        v = gd[col].to_numpy()
        rnd = np.mean([v[RNG.choice(len(v), k, replace=False)].mean() for _ in range(200)])
        out.append((d, rnd - gd[gd.rm][col].mean()))
    return out


def tstat(x):
    x = np.asarray(x, float)
    return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 and x.std() > 0 else np.nan


def selftest():
    d = pd.DataFrame(dict(date=["a"] * 4 + ["b"] * 4, r=[-1.0, -1.0, 1.0, 1.0] * 2, rm=[True, True, False, False] * 2))
    ex = block_excess(d, "r"); assert len(ex) == 2 and all(abs(e - 1.0) < 0.3 for _, e in ex), ex   # random mean ~0, rule -1
    allrm = d.assign(rm=True); assert block_excess(allrm, "r") == []
    assert abs(tstat([1, 1.1, 0.9]) - 1.0 / (0.1 / np.sqrt(3))) < 1e-9
    print("selftest ok: same-day random block excess, all-removed days skipped, t")


def main():
    t = pd.read_csv(sys.argv[1]); t["date"] = t.date.astype(str)
    assert not ((t.date >= LK0) & (t.date <= LK1)).any()
    t = t[t.setup.str.startswith("CWT12-coil")].copy()
    t["rm"] = t.e_checkpoint.astype(str).eq("DOWN")
    t["sm"] = t.side * t.spy_move.fillna(0)
    for s, g in t.groupby("setup"):                       # beta per setup on TRAIN only
        tr = g[g.date <= SPLIT]; b = np.cov(tr.sm, tr.gross)[0, 1] / tr.sm.var(ddof=1)
        t.loc[g.index, "ex"] = g.gross - b * g.sm; t.loc[g.index, "beta"] = b
    D = pd.read_csv("/home/user/guild/research/compassbf/compass_2y.csv.gz", usecols=["date", "T", "spy_fo"])
    oc = D.groupby("date").spy_fo.last()                  # SPY % from open at the 15:45 mark (proxy for o-c)
    dt = oc.map(lambda v: "up" if v > .0025 else ("down" if v < -.0025 else "quiet")); t["dtype"] = t.date.map(dt)
    print(f"coil trades {len(t)} ({t.date.nunique()} days); removed by rule {int(t.rm.sum())} ({t.rm.mean():.1%}); "
          f"beta per setup (TRAIN): {t.groupby('setup').beta.first().round(3).to_dict()}")
    for s, g in list(t.groupby("setup")) + [("ALL", t)]:
        kept, rem = g[~g.rm], g[g.rm]
        top = g[(g.date <= SPLIT)]; cut = top.gross.quantile(.9)
        tw = g[g.gross >= cut]
        print(f"\n== {s}: n {len(g)}, removed {len(rem)} ({len(rem)/len(g):.1%}); kept gross {kept.gross.mean():+.4f} net {kept.r.mean():+.4f} | "
              f"removed gross {rem.gross.mean():+.4f} net {rem.r.mean():+.4f} ex {rem.ex.mean():+.4f} vs kept ex {kept.ex.mean():+.4f}; "
              f"retention trades {len(kept)/len(g):.1%}, top-decile winners {(~tw.rm).mean():.1%}")
        grp = [g] if s != "ALL" else [x for _, x in t.groupby("setup")]
        for col in ("gross", "r", "ex"):
            ex = [e for x in grp for e in block_excess(x, col)]
            if not ex: print(f"   {col}: no informative days"); continue
            E = pd.DataFrame(ex, columns=["date", "e"]); E["dtype"] = E.date.map(dt)
            gd = E.groupby("date").e.sum(); wob = (gd.sum() - gd.max()) / max(1, len(gd) - 1)
            line = (f"   {col:5s} excess {E.e.mean():+.4f} t {tstat(E.e):.2f} days {len(E)} | TRAIN {E[E.date <= SPLIT].e.mean():+.4f} "
                    f"(t {tstat(E[E.date <= SPLIT].e):.2f}) VALID {E[E.date > SPLIT].e.mean():+.4f} (t {tstat(E[E.date > SPLIT].e):.2f}) | ")
            line += " ".join(f"{k} {v.mean():+.4f} (n {len(v)})" for k, v in E.groupby("dtype").e)
            line += f" | w/o best day {wob:+.4f}, best share {gd.max() / gd.sum():.2f}" if gd.sum() > 0 else f" | sum {gd.sum():+.2f}"
            print(line)
    print(f"\nrule: skip when e_checkpoint == DOWN (strict-< tag); excess = random same-day block minus rule-removed (>0 = rule removes worse);"
          f"\nex = gross minus TRAIN beta x signed SPY move over the hold; family N {N} -> BAR90 {BAR} on the ex-market excess t."
          f"\nSize control: a skip rule's kept avg vs all-trades avg is the 'trade less' comparison; reported above as kept vs removed.")
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
