"""stoplab C (lab): score time-stop / give-back variants on the 2-year lab walk (bt_variants.py output).
TRAIN <= 2025-12 (choose), VALID 2026-01..03 + 2026-07-01..09-15 (validate); HOLD not walked. d = r_variant - r_base per
trade (k = 1.0 walk, parity with the cached latch_1103 r). Educational only - not financial advice.
Usage: python analyze_lab.py /dev/shm/stopc_lab"""
import glob, math, re, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
OUT = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); OUT.append(s)

FAM8 = {"MF", "RW", "NS", "ST", "CWT", "L3", "GEN"}
def fam8(n):
    p = re.match(r"[A-Za-z]+", n).group(0); p = "L3" if p == "L" else p
    if n.startswith("NM-MF"): p = "MF"
    if n.startswith("NM-RW"): p = "RW"
    if n.startswith("NM1-cwt"): p = "CWT"
    return p if p in FAM8 else "other"

def tday(x, dates):
    s = pd.Series(np.asarray(x, float)).groupby(np.asarray(dates)).sum()
    return float(s.mean() / (s.std(ddof=1) / math.sqrt(len(s)))) if len(s) > 2 and s.std(ddof=1) > 0 else np.nan

fs = sorted(glob.glob(str(Path(sys.argv[1]) / "w_*.parquet")))
D = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
D["date"] = D.date.astype(str)
assert not ((D.date >= "2024-11-01") & (D.date <= "2025-02-28")).any()
d_ = pd.to_datetime(D.date)
D["sp"] = np.where(d_ <= "2025-12-31", "train",
                   np.where(((d_ >= "2026-01-01") & (d_ <= "2026-03-31")) | ((d_ >= "2026-07-01") & (d_ <= "2026-09-15")), "valid", "hold"))
D = D[D.sp != "hold"].reset_index(drop=True)
D["fam"] = D.setup.map(fam8)
CONF = [c[2:] for c in D.columns if c.startswith("r_") and c != "r_base"]
P(f"lab rows {len(D):,} (train {int((D.sp=='train').sum()):,}, valid {int((D.sp=='valid').sum()):,}), setups {D.setup.nunique()}, months {len(fs)}")
P(f"parity: base vs cached latch_1103 r on {int(D.bt_r.notna().sum()):,} rows, mean |d| {(D.r_base - D.bt_r).abs().mean():.2e}")
P(f"base avg R: train {D.r_base[D.sp=='train'].mean():+.4f}, valid {D.r_base[D.sp=='valid'].mean():+.4f}")

nv = D[D.sp == "valid"].groupby("setup").size(); S30 = set(nv[nv >= 30].index)
rows, per = [], []
for c in CONF:
    d = (D[f"r_{c}"] - D.r_base).astype(float); tr = D.sp == "train"; va = ~tr
    fired = D[f"r_{c}"] != D.r_base
    gs = pd.DataFrame({"setup": D.setup, "sp": D.sp, "d": d}).groupby(["setup", "sp"]).d.mean().unstack()
    gs = gs[gs.index.isin(S30)]
    dv = d[va].groupby(D.date[va]).sum()
    rows.append(dict(config=c, fired_va=fired[va].mean(), d_tr=d[tr].mean(), d_va=d[va].mean(), t_va=tday(d[va], D.date[va]),
                     t_tr=tday(d[tr], D.date[tr]), d_va_wo_best_day=(d[va].sum() - dv.max()) / va.sum(),
                     best_day_share_va=(dv.max() / d[va].sum() if d[va].sum() > 0 else np.nan),
                     setups=len(gs), up_va=int((gs.valid > 0).sum()), down_va=int((gs.valid < 0).sum()),
                     gain_va=gs.valid[gs.valid > 0].sum(), loss_va=gs.valid[gs.valid < 0].sum(), worst_va=gs.valid.min(),
                     up_both=int(((gs.train > 0) & (gs.valid > 0)).sum()), down_both=int(((gs.train < 0) & (gs.valid < 0)).sum())))
    for su, r in gs.iterrows():
        per.append(dict(config=c, setup=su, d_tr=r.train, d_va=r.valid))
G = pd.DataFrame(rows); G.to_csv(HERE / "lab_global.csv", index=False)
fmt = lambda df: df.to_string(index=False, float_format=lambda v: f"{v:,.4f}" if abs(v) < 10 else f"{v:,.1f}")
P("\n== global (every lab setup), d per trade =="); P(fmt(G))

# family / geometry (VALID)
fr = []
for c in CONF:
    d = (D[f"r_{c}"] - D.r_base).astype(float)
    for key in ("fam", "geom"):
        for k2, g in D[D.sp == "valid"].groupby(key):
            ps = d[g.index].groupby(g.setup).mean()
            ps_tr = d[(D.sp == "train") & (D[key] == k2)].groupby(D.setup).mean()
            fr.append(dict(config=c, by=key, group=k2, n_va=len(g), setups=len(ps), d_va=d[g.index].mean(),
                           d_tr=ps_tr.mean() if len(ps_tr) else np.nan, t_va=tday(d[g.index], g.date),
                           up=int((ps > 0).sum()), down=int((ps < 0).sum())))
F = pd.DataFrame(fr); F.to_csv(HERE / "lab_by_family_geom.csv", index=False)

# per-setup choice: best of {none} + 18 on TRAIN (n_train >= 30), scored on VALID
PS = pd.DataFrame(per); PS.to_csv(HERE / "lab_per_setup.csv", index=False)
BAR_SET = max(1.5, math.sqrt(2 * math.log(len(CONF))))
ch = []
for su, g in PS.groupby("setup"):
    b = g.loc[g.d_tr.idxmax()]
    if not (b.d_tr > 0):
        ch.append(dict(setup=su, choice="none", d_tr=0.0, d_va=0.0, t_va=np.nan)); continue
    m = (D.setup == su) & (D.sp == "valid")
    t = tday((D.loc[m, f"r_{b.config}"] - D.loc[m, "r_base"]), D.date[m])
    ch.append(dict(setup=su, choice=b.config, d_tr=b.d_tr, d_va=b.d_va, t_va=t))
CH = pd.DataFrame(ch); CH["fam"] = CH.setup.map(fam8); CH.to_csv(HERE / "lab_per_setup_choice.csv", index=False)
c2 = CH[CH.choice != "none"]
P(f"\nper-setup choice ({len(CONF)} variants + none, setups with >= 30 VALID trades): {len(CH)} setups, {len(c2)} pick a "
  f"variant on TRAIN; VALID improve {int((c2.d_va > 0).sum())} / worsen {int((c2.d_va < 0).sum())}; "
  f"t >= {BAR_SET:.2f} (per-setup bar) in {int((c2.t_va >= BAR_SET).sum())}, >= 2.96 (study) in {int((c2.t_va >= 2.96).sum())}")
P(c2.choice.value_counts().to_string())
P(fmt(c2.sort_values("t_va", ascending=False).head(15)))
(HERE / "lab_out.txt").write_text("\n".join(OUT) + "\n")
