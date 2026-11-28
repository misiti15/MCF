"""Q2b (2 add-on configs, BR30 and BS30): does a book budget add anything ON TOP of a per-setup -2R closed-R latch?
Arena only (it has no per-setup stop). Step 1: simulate the per-setup latch (block a setup's entries after its closed
R <= -2 that day; blocked lots do not count). Step 2: on the surviving lots, apply the book rule. Controls as q2.
Also reports each Q2 arena rule ex-11-25. Usage: python q2b_on_latch.py <scratch>. Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from common import load, dayt
import q2_budget as Q  # reuses block_mask / score (q2 main guarded below)

def latch_mask(x, L=2.0):
    blk = np.zeros(len(x), bool)
    for _, g in x.groupby(["account", "date", "strategy"]):
        if g.r.sum() > -L:
            # quick exit only if total never below -L is not guaranteed; do the proper walk
            pass
        idx = g.index.values; em = g.emin.values; xm = g.xmin.values; r = g.r.values
        order = np.argsort(em, kind="stable"); taken = []
        for j in order:
            closed = sum(r[k] for k in taken if xm[k] <= em[j])
            if closed <= -L:
                blk[idx[order[np.searchsorted(em[order], em[j]):]]] = True  # latched for the rest of the day
                break
            taken.append(j)
    return blk

def main():
    S = sys.argv[1]; t = load(S); t = t[t.L.notna()].reset_index(drop=True)
    for pe in ["DISC", "HOLD"]:
        x0 = t[(t.book == "arena") & (t.period == pe)].reset_index(drop=True)
        lb = latch_mask(x0)
        print(f"\n===== arena {pe}: per-setup -2R closed latch alone: blocks {lb.sum()} of {len(x0)} lots, saves {-x0.r[lb].sum():+.1f}R "
              f"(blocked avg {x0.r[lb].mean():+.3f} vs book {x0.r.mean():+.3f})")
        x = x0[~lb].reset_index(drop=True)
        # L stays the original point-in-time lot count (rule thresholds unchanged)
        for kind, f, lab in [("BR", .30, "BR30"), ("BS", .30, "BS30"), ("BR", .20, "BR20"), ("SIDE", .20, "SIDE20")]:
            blk, trig = Q.block_mask(x, kind, f)
            r = Q.score(x, blk, trig, kind, lab + "+latch")
            print({k: (round(float(v), 3) if isinstance(v, (float, np.floating)) else v) for k, v in r.items()}, flush=True)
            if pe == "DISC":
                y = x[x.date != "2026-11-25"].reset_index(drop=True); b2, t2 = Q.block_mask(y, kind, f)
                print(f"   ex-11-25: saved {-y.r[b2].sum():+.1f}R, blocked avg {y.r[b2].mean():+.3f} vs book {y.r.mean():+.3f}, neutral {-(y.r - y.groupby('account').r.transform('mean'))[b2].sum():+.1f}")
    # Q2 arena rules ex-11-25 without latch
    x = t[(t.book == "arena") & (t.period == "DISC") & (t.date != "2026-11-25")].reset_index(drop=True)
    print("\n===== arena DISC ex-11-25, no latch")
    for kind, f, lab in [("BR", .10, "BR10"), ("BR", .20, "BR20"), ("BR", .30, "BR30"), ("BS", .15, "BS15"), ("BS", .30, "BS30"), ("SIDE", .20, "SIDE20")]:
        b2, t2 = Q.block_mask(x, kind, f)
        print(f"{lab}: saved {-x.r[b2].sum():+.1f}R blocked avg {x.r[b2].mean():+.3f} vs book {x.r.mean():+.3f} neutral {-(x.r - x.groupby('account').r.transform('mean'))[b2].sum():+.1f}")

if __name__ == "__main__":
    main()
