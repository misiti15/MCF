"""stoplab grid A: per-setup daily stop level, replayed on live trades (+ latch what-ifs) session by session.
Usage: python replay.py [--a2]  -> CSVs + out.txt in this folder (RESULTS.md is written by hand from out.txt).
PLAN: ../PLAN.md (A1 realised-R latch levels, A2 realised+open, A3 per-setup choice, A4 per-family choice,
A5 give-back stop, A6 sensitivities). Educational only - not financial advice."""
import math, os, re, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = Path("/home/user/MCF")
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
OUT = open(HERE / "out.txt", "w")
def P(*a):
    print(*a); print(*a, file=OUT, flush=True)

LEVELS = [1.0, 1.25, 1.5, 1.6, 1.75, 1.8, 2.0, 2.01, 2.25, 2.5, 3.0, 4.0]   # stop at -L
GRID = ["off"] + LEVELS                                                     # neighbour order: tight .. loose, off = loosest
NBR = {g: [] for g in GRID}
_ord = [str(L) for L in LEVELS] + ["off"]
for i, g in enumerate(_ord):
    NBR[g] = [_ord[j] for j in (i - 1, i + 1) if 0 <= j < len(_ord)]
GIVE = [1.5, 2.0, 2.5, 3.0]
N_STUDY = 64; BAR = max(1.5, math.sqrt(2 * math.log(N_STUDY))); BAR_SETUP = max(1.5, math.sqrt(2 * math.log(12)))
EPS = 1e-9

# ---------------- data ----------------
T = pd.read_csv(HERE.parent / "trades.csv.gz")
d_ = pd.to_datetime(T.date)
assert not ((d_ >= "2024-11-01") & (d_ <= "2025-02-28")).any()
T["ent_s"] = ((pd.to_datetime(T.entry_time, utc=True) - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta("1s")).astype("int64")
T["ext_s"] = ((pd.to_datetime(T.exit_time, utc=True) - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta("1s")).astype("int64")
assert T.ent_s.min() > 1.7e9 and (T.ext_s >= T.ent_s - 1).mean() > 0.99
T = T[~T.whatif | T.blocked_latch | T.blocked_halt].copy()
T = T[np.isfinite(T.R)].copy()
# the live runner latches on journal r_multiple (what-ifs: r_multiple too); trades are SCORED on R (pnl_adj basis)
T["RL"] = T.r_multiple.where(np.isfinite(T.r_multiple), T.R)

def fam5(n):
    s = n.lower()
    if n.startswith("GEN-"): return "GEN"
    if n.startswith("MF") or n.startswith("NM-MF"): return "MF early sellers"
    if "coil" in s or "flag" in s: return "coils/flags"
    if "flush" in s and "short" not in s: return "flush longs"
    if "gapdn" in s and ("short" in s or n.startswith("RW")): return "gap-down shorts"
    return "other"
FAM8 = {"MF", "RW", "NS", "ST", "CWT", "L3", "GEN"}
def fam8(n):
    p = re.match(r"[A-Za-z]+", n).group(0); p = "L3" if p == "L" else p
    if n.startswith("NM-MF"): p = "MF"
    if n.startswith("NM-RW"): p = "RW"
    if n.startswith("NM1-cwt"): p = "CWT"
    return p if p in FAM8 else "other"

# splits per setup (pooled across accounts, live session dates)
live = T[~T.whatif]
SPL = {}
for su, g in live.groupby("setup"):
    ds = sorted(g.date.unique()); k = math.ceil(0.6 * len(ds))
    SPL[su] = (set(ds[:k]), len(ds))
def split_of(su, d):
    ch, n = SPL.get(su, (set(), 0))
    return "choose" if d in ch else "validate"

def baseline_L(acct, d):
    if acct == "primary" and d >= "2026-10-29": return 2.0
    if acct == "graveyard": return 2.0
    return None

# ---------------- simulator ----------------
def sim(r, ent, ext, mode, x, openmark=None, rl=None):
    """Entry order. mode 'latch': block from the first entry where realised R (taken trades exited at/before entry)
    <= -x [x None = off]. mode 'open': realised + marked open R (openmark[i][j] = mark of trade j at entry i).
    mode 'give': block once realised <= max(0, running peak realised) - x. Latched for the rest of the day.
    Returns taken mask."""
    n = len(r); taken = np.zeros(n, bool)
    r = r if rl is None else rl        # trigger basis
    if x is None:
        taken[:] = True; return taken
    for i in range(n):
        prev = np.flatnonzero(taken[:i])
        done = prev[ext[prev] <= ent[i]]
        real = r[done].sum()
        if mode == "latch":
            hit = real <= -x + EPS
        elif mode == "open":
            opn = prev[ext[prev] > ent[i]]
            m = openmark(i, opn)
            if m is None: return None
            hit = real + m <= -x + EPS
        else:
            if len(done):
                o = done[np.argsort(ext[done], kind="stable")]
                peak = max(0.0, np.cumsum(r[o]).max())
            else:
                peak = 0.0
            hit = real <= peak - x + EPS
        if hit:
            return taken
        taken[i] = True
    return taken

def units(df):
    df = df.sort_values(["account", "setup", "date", "ent_s", "symbol"], kind="mergesort")
    for (a, su, d), g in df.groupby(["account", "setup", "date"], sort=False):
        yield a, su, d, g

def run(df, configs, tag, openmark_factory=None):
    """configs: list of (name, mode, x). Returns per-unit frame with R_<name>, n_<name>."""
    rows = []
    for a, su, d, g in units(df):
        r = g.R.to_numpy(float); rl = g.RL.to_numpy(float); en = g.ent_s.to_numpy(); ex = g.ext_s.to_numpy()
        rec = dict(account=a, setup=su, date=d, split=split_of(su, d), n_all=len(r), n_live=int((~g.whatif).sum()),
                   fam5=fam5(su), fam8=fam8(su))
        om = openmark_factory(g) if openmark_factory else None
        for name, mode, x in configs:
            tk = sim(r, en, ex, mode, x, om, rl)
            if tk is None:
                rec[f"R_{name}"] = np.nan; rec[f"n_{name}"] = np.nan
            else:
                rec[f"R_{name}"] = float(r[tk].sum()); rec[f"n_{name}"] = int(tk.sum())
        bl = baseline_L(a, d)
        rec["R_base"] = rec["R_off"] if bl is None else rec["R_2.0"]
        rec["n_base"] = rec["n_off"] if bl is None else rec["n_2.0"]
        rows.append(rec)
    U = pd.DataFrame(rows)
    return U

CONF = [("off", "latch", None)] + [(str(L), "latch", L) for L in LEVELS] + [(f"g{G}", "give", G) for G in GIVE]
NAMES = [c[0] for c in CONF]

# own avg R per setup on CHOOSE (off sequence: live + latch what-ifs) for the excess control
def own_mu(df):
    s = df.assign(split=[split_of(a, b) for a, b in zip(df.setup, df.date)])
    return s[s.split == "choose"].groupby("setup").R.mean()

def tstat(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) < 2 or x.std(ddof=1) == 0: return np.nan
    return x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))

def level_table(U, mu, ref="base", names=NAMES):
    out = []
    muv = U.setup.map(mu).fillna(0).to_numpy()
    for nm in names:
        rec = dict(level=nm)
        for sp in ["all", "choose", "validate"]:
            V = U if sp == "all" else U[U.split == sp]
            m = muv if sp == "all" else muv[(U.split == sp).to_numpy()]
            R = V[f"R_{nm}"]; n = V[f"n_{nm}"]
            day = V.groupby("date")[f"R_{nm}"].sum()
            dd = (V[f"R_{nm}"] - V[f"R_{ref}"]).groupby(V.date).sum()
            exc = (V[f"R_{nm}"] - V[f"R_{ref}"]) - (V[f"n_{nm}"] - V[f"n_{ref}"]) * m
            p = "" if sp == "all" else sp[0] + "_"
            rec.update({f"{p}R": R.sum(), f"{p}n": n.sum(), f"{p}avgR": R.sum() / max(n.sum(), 1),
                        f"{p}green_days": int((day > 0).sum()), f"{p}days": len(day), f"{p}worst_day": day.min(),
                        f"{p}R_wo_best_day": R.sum() - day.max(),
                        f"{p}setupday_green": float((V[f"R_{nm}"] > 0).mean()),
                        f"{p}d_vs_{ref}": dd.sum(), f"{p}t": tstat(dd), f"{p}d_wo_best_day": dd.sum() - dd.max(),
                        f"{p}best_day_share": (dd.max() / dd.sum()) if dd.sum() > 0 else np.nan,
                        f"{p}excess": exc.sum(), f"{p}latched_units": int((V[f"n_{nm}"] < V["n_all"]).sum())})
        out.append(rec)
    return pd.DataFrame(out)

def fmt(df, cols):
    return df[cols].to_string(index=False, float_format=lambda v: f"{v:,.2f}")

# =============== A1 / A5 main run ===============
P("stoplab A - per-setup daily stop level. Educational only - not financial advice.")
P(f"rows: live {int((~T.whatif).sum())}, latch what-ifs {int(T.blocked_latch.sum())}, halt what-ifs {int(T.blocked_halt.sum())}")
MAIN = T[~T.blocked_halt]
mu = own_mu(MAIN)
U = run(MAIN, CONF, "main")
U.to_csv(HERE / "units_main.csv.gz", index=False)
P(f"units (account,setup,date): {len(U)}; choose {int((U.split=='choose').sum())}, validate {int((U.split=='validate').sum())}")

# sanity: baseline vs actual live where the rule was on
for a in ["primary", "graveyard"]:
    V = U[(U.account == a) & ((U.date >= "2026-10-29") if a == "primary" else True)]
    act = live[(live.account == a) & ((live.date >= "2026-10-29") if a == "primary" else True)].R.sum()
    P(f"sanity {a}: simulated baseline R {V.R_base.sum():.2f} vs actual live R {act:.2f} "
      f"(live runner books exits at reconciliation, a few seconds-minutes late; sim = exits known at fill time)")

LT = level_table(U, mu, "base")
LT_off = level_table(U, mu, "off")
LT.to_csv(HERE / "A1_global_levels_vs_baseline.csv", index=False)
LT_off.to_csv(HERE / "A1_global_levels_vs_off.csv", index=False)
P("\n=== A1+A5 GLOBAL (all accounts, all setups), vs live baseline (Primary -2 from 10-29, Graveyard -2, others off) ===")
P(fmt(LT, ["level", "R", "n", "avgR", "green_days", "days", "worst_day", "R_wo_best_day", "setupday_green",
           "d_vs_base", "c_d_vs_base", "v_d_vs_base", "v_t", "v_d_wo_best_day", "c_excess", "v_excess", "latched_units"]))
P("\n=== same, vs OFF ===")
P(fmt(LT_off, ["level", "d_vs_off", "c_d_vs_off", "c_t", "v_d_vs_off", "v_t", "v_d_wo_best_day", "v_best_day_share", "c_excess", "v_excess"]))

# per account
acc_rows = []
for a, V in U.groupby("account"):
    t = level_table(V, mu, "off"); t.insert(0, "account", a); acc_rows.append(t)
ACC = pd.concat(acc_rows)
ACC.to_csv(HERE / "A1_by_account_vs_off.csv", index=False)
P("\n=== by account: R per level (vs off) ===")
pv = ACC.pivot(index="level", columns="account", values="R").reindex(NAMES)
P(pv.to_string(float_format=lambda v: f"{v:,.1f}"))
pvv = ACC.pivot(index="level", columns="account", values="v_d_vs_off").reindex(NAMES)
P("validate delta vs off:"); P(pvv.to_string(float_format=lambda v: f"{v:,.1f}"))

# Primary only, since the latch went live (10-29..)
PR = U[(U.account == "primary") & (U.date >= "2026-10-29")]
P("\n=== Primary 10-29..11-09 (latch live), vs baseline -2.0 ===")
P(fmt(level_table(PR, mu, "base"), ["level", "R", "n", "avgR", "green_days", "days", "worst_day", "R_wo_best_day", "d_vs_base", "t", "excess"]))

# global choice on choose split (for setups with < 5 sessions and as the global answer)
lvl_names = ["off"] + [str(L) for L in LEVELS]
cR = LT.set_index("level").loc[lvl_names, "c_R"]
GBEST = cR.idxmax()
P(f"\nGLOBAL best level on CHOOSE (A1, max choose R): {GBEST}; choose R {cR.max():.1f}, at -2.0 {cR['2.0']:.1f}, off {cR['off']:.1f}")
vb = LT.set_index("level")
pos_nb = [vb.loc[nb, "v_d_vs_base"] > 0 for nb in NBR[GBEST]]
P(f"   validate delta vs baseline {vb.loc[GBEST,'v_d_vs_base']:.1f} (t {vb.loc[GBEST,'v_t']:.2f}), neighbours "
  f"{NBR[GBEST]} validate deltas {[round(vb.loc[nb,'v_d_vs_base'],1) for nb in NBR[GBEST]]}; plateau={all(pos_nb)}")

# =============== A3 per-setup choice ===============
def tie_key(nm):
    return 99.0 if nm == "off" else abs(float(nm) - 2.0)
SU = []
for su, V in U.groupby("setup"):
    nlive = int(V.n_live.sum()); ns = SPL.get(su, (set(), 0))[1]
    C = V[V.split == "choose"]; W = V[V.split == "validate"]
    cr = {nm: C[f"R_{nm}"].sum() for nm in lvl_names}
    mx = max(cr.values())
    best = sorted([nm for nm in lvl_names if cr[nm] >= mx - 1e-9], key=tie_key)[0]
    if ns < 5: best_used = GBEST
    else: best_used = best
    vr = {nm: W[f"R_{nm}"].sum() for nm in lvl_names}
    dday = (W[f"R_{best_used}"] - W["R_2.0"]).groupby(W.date).sum()
    allday = V.groupby("date")["R_2.0"].sum()
    n20 = V["n_2.0"].sum()
    mus = mu.get(su, 0.0)
    exc_v = ((W[f"R_{best_used}"] - W["R_2.0"]) - (W[f"n_{best_used}"] - W["n_2.0"]) * mus).sum()
    nb_ok = all(vr[nb] - vr["2.0"] > 0 for nb in NBR[best_used]) if best_used != "2.0" else False
    rec = dict(setup=su, fam5=fam5(su), fam8=fam8(su), accounts=",".join(sorted(V.account.unique())), n_live=nlive,
               n_whatif=int((V.n_all - V.n_live).sum()), sessions=ns, R_off=V.R_off.sum(), R_m2=V["R_2.0"].sum(),
               avgR_m2=V["R_2.0"].sum() / max(n20, 1),
               avgR_m2_wo_best_day=(V["R_2.0"].sum() - allday.max()) / max(n20 - V[V.date == allday.idxmax()]["n_2.0"].sum(), 1),
               best_day_share_m2=(allday.max() / V["R_2.0"].sum()) if V["R_2.0"].sum() > 0 else np.nan,
               latched_days_m2=int((V["n_2.0"] < V.n_all).sum()),
               best_choose=best, best_used=best_used, too_few=ns < 5,
               choose_gain=cr[best_used] - cr["2.0"], validate_gain=vr[best_used] - vr["2.0"],
               validate_gain_vs_off=vr[best_used] - vr["off"], val_t=tstat(dday), val_excess=exc_v,
               plateau=nb_ok)
    rec["sign_holds"] = (rec["choose_gain"] > 0) and (rec["validate_gain"] > 0)
    rec["robust"] = bool(rec["sign_holds"] and nb_ok and (rec["val_t"] >= BAR_SETUP) and exc_v > 0 and not rec["too_few"])
    for nm in lvl_names:
        rec[f"c_{nm}"] = cr[nm]; rec[f"v_{nm}"] = vr[nm]
    SU.append(rec)
SU = pd.DataFrame(SU).sort_values("n_live", ascending=False)
SU.to_csv(HERE / "A3_per_setup_all.csv", index=False)
S20 = SU[SU.n_live >= 20]
S20.to_csv(HERE / "A3_per_setup_n20.csv", index=False)
P(f"\n=== A3 per-setup (n_live >= 20: {len(S20)} setups; {int((~S20.too_few).sum())} with >= 5 sessions choose their own) ===")
P(f"best level on CHOOSE (own choice, >=5 sessions): " + str(S20[~S20.too_few].best_choose.value_counts().to_dict()))
P(f"best == -2.0 (no change): {int((S20.best_used=='2.0').sum())}; sign holds (choose>0 & validate>0): {int(S20.sign_holds.sum())}; "
  f"robust (t>={BAR_SETUP:.2f}, plateau, excess>0): {int(S20.robust.sum())}")
ch = S20[S20.best_used != "2.0"]
P(f"of {len(ch)} setups whose choice differs from -2.0: validate improves {int((ch.validate_gain>0).sum())} (+{ch.validate_gain[ch.validate_gain>0].sum():.1f}R), "
  f"worsens {int((ch.validate_gain<0).sum())} ({ch.validate_gain[ch.validate_gain<0].sum():.1f}R, worst {ch.validate_gain.min():.1f}), "
  f"same {int((ch.validate_gain==0).sum())}; net {ch.validate_gain.sum():.1f}R")
P(fmt(S20, ["setup", "n_live", "sessions", "R_off", "R_m2", "avgR_m2", "avgR_m2_wo_best_day", "best_used", "choose_gain", "validate_gain", "val_t", "val_excess", "plateau", "robust"]))
# A3 as a rule (all setups): per-setup choices applied on validate vs baseline / vs -2.0
pick = SU.set_index("setup").best_used
Vv = U[U.split == "validate"].copy()
Vv["R_a3"] = [r[f"R_{pick[r.setup]}"] for _, r in Vv.iterrows()]
dd = (Vv.R_a3 - Vv["R_2.0"]).groupby(Vv.date).sum(); db = (Vv.R_a3 - Vv.R_base).groupby(Vv.date).sum()
P(f"A3 rule on VALIDATE (all setups): vs uniform -2.0 {dd.sum():+.1f}R (t {tstat(dd):.2f}, w/o best day {dd.sum()-dd.max():+.1f}); "
  f"vs live baseline {db.sum():+.1f}R (t {tstat(db):.2f})")

# =============== A4 per-family choice ===============
P("\n=== A4 per family (choose best on CHOOSE, score on VALIDATE vs -2.0) ===")
FR = []
for famcol in ["fam5", "fam8"]:
    for f, V in U.groupby(famcol):
        C = V[V.split == "choose"]; W = V[V.split == "validate"]
        cr = {nm: C[f"R_{nm}"].sum() for nm in lvl_names}; mx = max(cr.values())
        best = sorted([nm for nm in lvl_names if cr[nm] >= mx - 1e-9], key=tie_key)[0]
        vr = {nm: W[f"R_{nm}"].sum() for nm in lvl_names}
        dday = (W[f"R_{best}"] - W["R_2.0"]).groupby(W.date).sum()
        # remedies: per setup in the family, validate change of the family level vs -2.0
        ps = (W[f"R_{best}"] - W["R_2.0"]).groupby(W.setup).sum()
        rec = dict(scheme=famcol, family=f, setups=V.setup.nunique(), n_live=int(V.n_live.sum()), R_off=V.R_off.sum(),
                   R_m2=V["R_2.0"].sum(), best=best, choose_gain=cr[best] - cr["2.0"], validate_gain=vr[best] - vr["2.0"],
                   val_t=tstat(dday), plateau=all(vr[nb] - vr["2.0"] > 0 for nb in NBR[best]) if best != "2.0" else False,
                   setups_up=int((ps > 0).sum()), R_up=ps[ps > 0].sum(), setups_down=int((ps < 0).sum()), R_down=ps[ps < 0].sum(),
                   worst_setup=ps.min() if len(ps) else np.nan)
        for nm in lvl_names:
            rec[f"all_{nm}"] = V[f"R_{nm}"].sum()
        FR.append(rec)
FR = pd.DataFrame(FR); FR.to_csv(HERE / "A4_family.csv", index=False)
P(fmt(FR, ["scheme", "family", "setups", "n_live", "R_off", "R_m2", "best", "choose_gain", "validate_gain", "val_t", "plateau", "setups_up", "R_up", "setups_down", "R_down"]))
P("family R across levels (all sessions):")
P(FR.set_index(["scheme", "family"])[[f"all_{nm}" for nm in lvl_names]].rename(columns=lambda c: c[4:]).to_string(float_format=lambda v: f"{v:,.0f}"))

# =============== Remedies table for the global levels vs -2.0 (per setup) ===============
P("\n=== Remedies: each level vs uniform -2.0, per setup (all sessions; validate in brackets) ===")
RM = []
for nm in lvl_names + [f"g{G}" for G in GIVE]:
    ps = (U[f"R_{nm}"] - U["R_2.0"]).groupby(U.setup).sum()
    W = U[U.split == "validate"]; pv_ = (W[f"R_{nm}"] - W["R_2.0"]).groupby(W.setup).sum()
    RM.append(dict(level=nm, up=int((ps > 1e-9).sum()), R_up=ps[ps > 1e-9].sum(), down=int((ps < -1e-9).sum()),
                   R_down=ps[ps < -1e-9].sum(), worst=ps.min(), best=ps.max(), net=ps.sum(),
                   v_up=int((pv_ > 1e-9).sum()), v_down=int((pv_ < -1e-9).sum()), v_net=pv_.sum()))
RM = pd.DataFrame(RM); RM.to_csv(HERE / "remedies_vs_m2.csv", index=False)
P(fmt(RM, list(RM.columns)))


# =============== global vs uniform -2.0 (day-clustered t) ===============
LT2 = level_table(U, mu, "2.0")
LT2.to_csv(HERE / "A1_global_levels_vs_m2.csv", index=False)
P("\n=== A1+A5 GLOBAL vs uniform -2.0 everywhere ===")
P(fmt(LT2, ["level", "R", "d_vs_2.0", "c_d_vs_2.0", "c_t", "v_d_vs_2.0", "v_t", "v_d_wo_best_day", "v_best_day_share", "c_excess", "v_excess"]))

# =============== diagnostic (unplanned, added after the family table; NOT a candidate): split by the setup's own
# CHOOSE-split average R (off sequence) - positive vs negative expectancy setups
P("\n=== DIAGNOSTIC (post-hoc, not counted as a candidate): setups by own CHOOSE avg R sign; R by level ===")
U["exp_sign"] = np.where(U.setup.map(mu).fillna(0) > 0, "choose avgR > 0", "choose avgR <= 0")
DG = []
for k, V in U.groupby("exp_sign"):
    for sp in ["choose", "validate"]:
        W = V[V.split == sp]
        rec = dict(group=k, split=sp, setups=W.setup.nunique(), units=len(W))
        for nm in lvl_names + [f"g{G}" for G in GIVE]:
            rec[nm] = W[f"R_{nm}"].sum()
        DG.append(rec)
    W = V[V.split == "validate"]
    for nm in ["off", "1.0", "1.5", "2.5", "3.0"]:
        dd = (W[f"R_{nm}"] - W["R_2.0"]).groupby(W.date).sum()
        ps = (W[f"R_{nm}"] - W["R_2.0"]).groupby(W.setup).sum()
        P(f"  {k} VALIDATE {nm} vs -2.0: {dd.sum():+.1f}R t {tstat(dd):.2f} w/o best day {dd.sum()-dd.max():+.1f}; "
          f"setups up {int((ps>1e-9).sum())} ({ps[ps>1e-9].sum():+.1f}), down {int((ps<-1e-9).sum())} ({ps[ps<-1e-9].sum():+.1f}, worst {ps.min():+.1f})")
DG = pd.DataFrame(DG); DG.to_csv(HERE / "diag_by_expectancy.csv", index=False)
P(DG.to_string(index=False, float_format=lambda v: f"{v:,.1f}"))

# =============== A6 sensitivity: halt what-ifs included ===============
P("\n=== A6a sensitivity: account-halt what-ifs included (as if no account halt) ===")
mu_h = own_mu(T)
Uh = run(T, CONF[:13], "halt")
LTh = level_table(Uh, mu_h, "off", lvl_names)
LTh.to_csv(HERE / "A6_halt_included_vs_off.csv", index=False)
P(fmt(LTh, ["level", "R", "n", "avgR", "green_days", "worst_day", "R_wo_best_day", "d_vs_off", "c_d_vs_off", "v_d_vs_off", "v_t", "v_excess"]))

if "--a2" in sys.argv:
    import a2  # noqa
    a2.main(MAIN, run, level_table, mu, P, LEVELS, HERE, fmt)
OUT.close()
