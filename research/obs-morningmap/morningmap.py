"""Observer: where could a MORNING on/off condition possibly help? (Lead lead-20261110-0300-4). Descriptive map, 2 counted looks
(L1 = aligned minus counter, L2 = aligned minus no-reading), both on ex-market R. Family N 2,605 (Skeptic) applies to anything built on it.
Reading at entry = e_checkpoint: the latest 30-min checkpoint STRICTLY before the entry bar close (Builder's re-tag, Skeptic's fix);
UP / DOWN = confirmed, anything else = 'none'. aligned = reading equals the trade side, counter = opposite.
ex-market R = gross - beta x (side x SPY move over the hold), beta fitted per setup on TRAIN only (as Scout's coilam.py).
Split as coilam.py: TRAIN <= 2025-09-30 < VALID; locked block 2024-11-01..2025-02-28 never present (asserted).
Per family-side: between-day contrasts (day-level means, Welch t, days as the unit) in TRAIN and VALID; 'consistent' = same sign in both and |t| >= 1 in both.
usage: python morningmap.py <tagged.csv.gz|parquet> [out_csv]. Works on coil_tagged.csv.gz and trades_tagged.parquet.
Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
pd.set_option("display.width", 230)
SPLIT, LK0, LK1 = "2025-09-30", "2024-11-01", "2025-02-28"
p = sys.argv[1]; t = pd.read_parquet(p) if p.endswith(".parquet") else pd.read_csv(p)
t["date"] = t.date.astype(str)
assert not ((t.date >= LK0) & (t.date <= LK1)).any(), "locked block present"
t = t[t.gross.notna() & t.spy_move.notna()].copy()
t["sm"] = t.side * t.spy_move
for s, g in t.groupby("setup"):
    tr = g[g.date <= SPLIT]; b = np.cov(tr.sm, tr.gross)[0, 1] / tr.sm.var(ddof=1) if len(tr) > 30 else 0.0
    t.loc[g.index, "ex"] = g.gross - b * g.sm
rd = t.e_checkpoint.where(t.e_checkpoint.isin(["UP", "DOWN"]), "none")
t["cls"] = np.where(rd == "none", "none", np.where((rd == "UP") == (t.side == 1), "aligned", "counter"))
t["fam"] = t.setup.str.extract(r"^(GEN-\d+|[A-Za-z]+\d*)")[0] + np.where(t.side == 1, "-L", "-S")
t["period"] = np.where(t.date <= SPLIT, "TRAIN", "VALID")
def contrast(g, a, b):
    """between-day: day-level mean ex R of class a days vs class b days (a one-side family has one reading per day,
    so a same-day contrast is impossible); Welch-style t with days as the unit (as rcompass.day_t)."""
    d = g.groupby(["cls", "date"]).ex.mean()
    if a not in d.index.get_level_values(0) or b not in d.index.get_level_values(0): return np.nan, np.nan, 0
    x, y = d.loc[a].to_numpy(), d.loc[b].to_numpy()
    if len(x) < 5 or len(y) < 5: return np.nan, np.nan, min(len(x), len(y))
    m = x.mean() - y.mean(); se = np.sqrt(x.var(ddof=1) / len(x) + y.var(ddof=1) / len(y))
    return m, (m / se if se > 0 else np.nan), min(len(x), len(y))
rows = []
for fam, g in t.groupby("fam"):
    r = dict(fam=fam, n=len(g), share_aligned=(g.cls == "aligned").mean(), share_counter=(g.cls == "counter").mean())
    for per in ("TRAIN", "VALID"):
        h = g[g.period == per]
        for lab, (a, b) in (("L1", ("aligned", "counter")), ("L2", ("aligned", "none"))):
            m, tt, nd = contrast(h, a, b); r[f"{lab}_{per}"] = m; r[f"{lab}_{per}_t"] = tt; r[f"{lab}_{per}_days"] = nd
    rows.append(r)
F = pd.DataFrame(rows).set_index("fam")
for lab in ("L1", "L2"):
    a, b = F[f"{lab}_TRAIN"], F[f"{lab}_VALID"]
    F[f"{lab}_cons"] = np.select([(a > 0) & (b > 0) & (F[f"{lab}_TRAIN_t"] >= 1) & (F[f"{lab}_VALID_t"] >= 1),
                                  (a < 0) & (b < 0) & (F[f"{lab}_TRAIN_t"] <= -1) & (F[f"{lab}_VALID_t"] <= -1)], ["+", "-"], "")
print(f"trades {len(t)}, family-sides {len(F)}, dates {t.date.min()}..{t.date.max()}; classes {t.cls.value_counts().to_dict()}")
print("pooled ex-market R by class:", t.groupby(["period", "cls"]).ex.mean().round(4).to_dict())
for lab, txt in (("L1", "aligned minus counter"), ("L2", "aligned minus no-reading")):
    ok = F[F[f"{lab}_TRAIN"].notna() & F[f"{lab}_VALID"].notna()]
    same = ((ok[f"{lab}_TRAIN"] > 0) == (ok[f"{lab}_VALID"] > 0)).sum()
    print(f"\n{lab} ({txt}): testable {len(ok)}; same sign TRAIN/VALID {same} (coin flip ~{len(ok) / 2:.0f}); "
          f"aligned better in both {int(((ok[f'{lab}_TRAIN'] > 0) & (ok[f'{lab}_VALID'] > 0)).sum())}, worse in both {int(((ok[f'{lab}_TRAIN'] < 0) & (ok[f'{lab}_VALID'] < 0)).sum())}; "
          f"consistent |t|>=1 both: + {int((ok[f'{lab}_cons'] == '+').sum())} / - {int((ok[f'{lab}_cons'] == '-').sum())}")
cols = ["n", "share_aligned", "share_counter", "L1_TRAIN", "L1_TRAIN_t", "L1_VALID", "L1_VALID_t", "L1_cons", "L2_TRAIN", "L2_VALID", "L2_cons"]
print("\nfamily-sides with a consistent L1 or L2 sign:\n", F[(F.L1_cons != "") | (F.L2_cons != "")][cols].round(3).to_string())
if len(sys.argv) > 2: F.round(4).to_csv(sys.argv[2])
print("\nReminder: any rule built on this map faces N 2,605 (BAR90 3.57) and a same-day random-block control. Educational only - not financial advice.")
