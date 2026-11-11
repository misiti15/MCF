"""FASTDEC decision engine (research, 2026-11-11). Educational only - not financial advice.

Turns every setup's live (paper) record into a posterior for its true avg R per trade (after costs) and a status:
    promote-ready / on-track / undecided / demote-ready
plus P(avg R > 0), P(avg R < -0.05) and the expected live sessions to a verdict at the setup's current trade rate.

The unit of evidence is the SESSION, not the trade: a setup's trades on one day move together (ROT design effect ~3.8),
so the standard error of avg R is the session-clustered (ratio-estimator) one, regularised toward a pooled value while
a setup has few traded sessions.

Methods (all reported in research/fastdec/NOTES.md; walk-forward in study.py):
  eb     hierarchical empirical Bayes: setup mean ~ N(family x side mean (leave-one-out, itself shrunk to the side
         mean), tau^2); tau^2 by DerSimonian-Laird on the day of the decision.
  ebx    the same on day x side "excess" R (the common same-side pool's R that day removed), plus the side pool's
         long-run mean.
  flat   Bayesian sequential on the setup's own record, weak prior N(0, 0.20^2).    <- RECOMMENDED (default), together
         with the REPS-MIN demote floor (repsmin_demote_floor=True): this pair is "M4" in NOTES.
  sprt   Wald SPRT H0: mu = -0.05 vs H1: mu = +0.05, alpha = beta = 0.10, on the clustered SE.
  bt     borrowed strength: prior = 2-year lab backtest of the same setup (shorts: lab restricted to names that were
         shortable+ETB on >= 90% of the live borrow snapshots, the L3LEASH-2 'E90' proxy) + an empirical lab->live gap
         per side, with the gap and its spread re-estimated by DL on the day; setups without a backtest fall back to eb.

Decision rule (pre-set, not tuned): a call needs >= MIN_SESS traded sessions and >= MIN_TRADES trades;
  promote-ready  P(mu > 0)     >= 0.90
  demote-ready   P(mu < -0.05) >= 0.90
  on-track       neither, but the projection (posterior mean held, variance shrinking at the setup's own
                 traded-session rate) reaches a verdict within ON_TRACK_SESSIONS live sessions
  undecided      otherwise.
The one-big-day check (owner 2026-10-25) is reported alongside (avg R w/o best day, best-day share, `1 day` tag at >= 50%);
it is a flag, not part of the gate (study.py tested it as a gate: see NOTES).

Replays (rule 21) never enter the posterior. The forward-replay hook (research/fwdrep) is read only as a FILTER column
(`fwdrep_avgR`, `fwdrep_flag`) when its output file exists; interface in NOTES.md section 6.

Nightly use (after the close; reads the data branches with `git show`, no broker calls):
    python -m research.fastdec.engine                       # writes research/fastdec/out/decisions.{json,csv}
    python -m research.fastdec.engine --journals DIR        # DIR/<p|t1|t2|gy|gen|ex1|ll>/journal.db instead of git
    python -m research.fastdec.engine --asof 2026-11-10 --method eb --out DIR
    python -m research.fastdec.engine --build-priors        # rebuild priors.csv from the 2y lab cache (slow-ish, offline)
The JSON is the dashboard-facing contract: {"version", "asof", "method", "params", "sessions", "setups": [...]}.
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import math
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
VERSION = 1

ACCOUNTS = {"p": "mcf-data", "t1": "mcf-data-testing", "t2": "mcf-data-testing2", "gy": "mcf-data-graveyard",
            "gen": "mcf-data-gen", "ex1": "mcf-data-explore1", "ll": "mcf-data-livelab"}
ACCT_NAME = {"p": "primary", "t1": "testing", "t2": "testing2", "gy": "graveyard", "gen": "gen", "ex1": "explore1",
             "ll": "livelab"}

PARAMS = dict(
    min_sess=4, min_trades=10,          # experience floor for any call (pre-set)
    p_promote=0.90, p_demote=0.90,      # posterior thresholds
    demote_line=-0.05,                  # "clearly losing" line, R per trade after costs
    k0=4.0,                             # sessions of pooled variance mixed into the clustered variance
    tau2_floor=0.02 ** 2,               # never pool a setup completely into its family
    flat_prior_sd=0.20,
    sprt_h0=-0.05, sprt_h1=0.05, sprt_alpha=0.10, sprt_beta=0.10,
    on_track_sessions=10, horizon=60,
    repsmin_demote_floor=True,          # demote-ready also when REPS-MIN 8/30 is reached and the ROT Graveyard-floor shape
                                        # holds (shrunk avg R <= -0.10, w/o best day < 0, last-5 < 0) - the M4 engine
    own_agree=True,                     # a call also needs the setup's OWN avg R on that side of 0 (fair-chance guard:
                                        # no setup is demoted / promoted by its family's record alone)
)


# ----------------------------------------------------------------------------------------------------------- data
def family(sid: str) -> str:
    if sid.startswith("GEN-"):
        return "GEN"
    if sid.startswith("NM"):
        return "NM"
    m = re.match(r"([A-Za-z]+)(\d*)", sid)
    a = m.group(1)
    if a == "L":
        return "L3"
    if a.islower() or a in ("heat",):
        return "CLS"            # classic named setups: exhaustion_short, orb20_a, intraday_momentum, heat...
    return a.upper()


def _git(*a: str) -> bytes:
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, check=True).stdout


def load_trades(journals: str | Path | None = None, asof: str | None = None) -> pd.DataFrame:
    """Closed run_id=1 trades of all 7 accounts, R after costs = pnl_adj / (|entry - stop| x shares)."""
    tmp = None
    if journals is None:
        tmp = tempfile.TemporaryDirectory()
        journals = Path(tmp.name)
        for a, br in ACCOUNTS.items():
            (journals / a).mkdir()
            try:
                (journals / a / "journal.db").write_bytes(_git("show", f"origin/{br}:journal.db"))
            except subprocess.CalledProcessError:
                (journals / a / "journal.db").unlink(missing_ok=True)
    journals = Path(journals)
    rows = []
    for a in ACCOUNTS:
        f = journals / a / "journal.db"
        if not f.exists():
            continue
        c = sqlite3.connect(f)
        t = pd.read_sql("select date, strategy, side, entry, stop, shares, pnl, pnl_adj from trades "
                        "where run_id=1 and exit is not null", c)
        c.close()
        t["acct"] = a
        rows.append(t)
    if tmp is not None:
        tmp.cleanup()
    T = pd.concat(rows, ignore_index=True)
    T["pnl_adj"] = T.pnl_adj.fillna(T.pnl)
    T["risk"] = (T.entry - T.stop).abs() * T.shares
    T = T[T.risk > 0].copy()
    T["R"] = T.pnl_adj / T.risk
    T["date"] = T.date.astype(str)
    if asof:
        T = T[T.date <= asof]
    T["side"] = pd.to_numeric(T.side, errors="coerce")
    return T[["date", "strategy", "side", "R", "acct"]].reset_index(drop=True)


def default_asof(now: dt.datetime | None = None) -> str:
    """Last fully closed session: today after 16:15 ET, else yesterday (weekends are simply absent from the data)."""
    now = now or dt.datetime.now(dt.timezone.utc)
    et = now.astimezone(dt.timezone(dt.timedelta(hours=-5)))   # EST; 16:15 EST ~ 17:15 EDT, both after the close
    d = et.date() if (et.hour, et.minute) >= (16, 15) else et.date() - dt.timedelta(days=1)
    return d.isoformat()


# ----------------------------------------------------------------------------------------------- per-setup stats
def day_table(T: pd.DataFrame) -> pd.DataFrame:
    return T.groupby(["strategy", "date"]).agg(y=("R", "sum"), n=("R", "size"), side=("side", "mean")).reset_index()


def setup_stats(D: pd.DataFrame) -> pd.DataFrame:
    """Per setup: trades N, traded sessions k, avg R m, clustered var of m, w/o-best-day, best-day share, side."""
    out = []
    for s, g in D.groupby("strategy", sort=False):
        y, n = g.y.to_numpy(float), g.n.to_numpy(float)
        N, k = n.sum(), len(g)
        m = y.sum() / N
        e = y - m * n
        vcl = (k / (k - 1)) * (e ** 2).sum() / N ** 2 if k > 1 else np.nan
        # per-trade-scale numbers for the pooled fallback
        j = int(np.argmax(y))
        exb = (y.sum() - y[j]) / (N - n[j]) if k >= 2 and N > n[j] else np.nan
        share = y[j] / y.sum() if y.sum() > 0 and k >= 2 and y[j] > 0 else np.nan
        sd = g.side.mean()
        l5 = g.sort_values("date").iloc[-5:]
        last5 = l5.y.sum() / l5.n.sum()
        out.append(dict(setup=s, last5=last5, family=family(s), side="short" if sd < 0 else "long" if sd > 0 else "both",
                        N=int(N), k=int(k), m=m, vcl=vcl, exbest=exb, best_share=share,
                        first=g.date.min(), last=g.date.max()))
    return pd.DataFrame(out).set_index("setup")


def pooled_var(S: pd.DataFrame, T: pd.DataFrame | None = None) -> tuple[float, float, float]:
    """Pooled effective per-trade variance c = median(clustered var x N) over setups with k>=8, N>=30 (it carries the
    design effect), plus the plain per-trade variance s2 and the implied design effect (for reporting)."""
    big = S[(S.k >= 8) & (S.N >= 30) & S.vcl.notna()]
    c = float(np.median(big.vcl * big.N)) if len(big) >= 5 else float((S.vcl * S.N).median())
    if T is not None:
        mu = T.groupby("strategy").R.transform("mean")
        s2 = float(((T.R - mu) ** 2).mean())
    else:
        s2 = np.nan
    return c, s2, (c / s2 if s2 and s2 == s2 else np.nan)


def regularised_var(S: pd.DataFrame, c: float, k0: float) -> pd.Series:
    vpool = c / S.N
    vcl = S.vcl.fillna(vpool)
    return (S.k * vcl + k0 * vpool) / (S.k + k0)


def excess_day_table(D: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Remove the common day x side factor: x = y - n * (same-side pool avg R that day, leave-one-setup-out).
    Returns the excess table and, per side, the long-run pool mean (equal weight per session) and its variance."""
    D = D.copy()
    D["sg"] = np.sign(D.side).fillna(0)
    P = D.groupby(["date", "sg"]).agg(Y=("y", "sum"), Nn=("n", "sum")).reset_index()
    D = D.merge(P, on=["date", "sg"], how="left")
    pool = (D.Y - D.y) / (D.Nn - D.n).replace(0, np.nan)
    allday = D.groupby("date").apply(lambda g: g.y.sum() / g.n.sum(), include_groups=False)
    pool = pool.fillna(D.date.map(allday))
    D["x"] = D.y - D.n * pool
    fbar = {}
    for sg, nm_ in ((-1.0, "short"), (1.0, "long"), (0.0, "both")):
        f = (P[P.sg == sg].set_index("date").eval("Y / Nn") if sg != 0 else allday)
        if len(f) < 3:
            f = allday
        fbar[nm_] = (float(f.mean()), float(f.var(ddof=1) / len(f)), len(f))
    out = D[["strategy", "date", "x", "n", "side"]].rename(columns={"x": "y"})
    return out, fbar


def _dl_tau2(r: np.ndarray, v: np.ndarray) -> float:
    """DerSimonian-Laird between-unit variance of residuals r with sampling variances v."""
    w = 1 / v
    if len(r) < 3:
        return 0.0
    rbar = (w * r).sum() / w.sum()
    Q = (w * (r - rbar) ** 2).sum()
    den = w.sum() - (w ** 2).sum() / w.sum()
    return max(0.0, (Q - (len(r) - 1)) / den) if den > 0 else 0.0


# ------------------------------------------------------------------------------------------------------- priors
def eb_prior(S: pd.DataFrame, V: pd.Series, p=PARAMS) -> tuple[pd.Series, pd.Series]:
    """Family x side prior (leave-one-out), group means shrunk to the side mean; returns prior mean, prior var."""
    grp = S.family + "|" + S.side
    tau2 = 0.01
    for _ in range(3):
        w = 1 / (V + tau2)
        # leave-one-out group mean
        gw = w.groupby(grp).transform("sum")
        gwm = (w * S.m).groupby(grp).transform("sum")
        loo_w = gw - w
        loo_m = (gwm - w * S.m) / loo_w.replace(0, np.nan)
        # side means (leave-one-out)
        sw = w.groupby(S.side).transform("sum")
        swm = (w * S.m).groupby(S.side).transform("sum")
        side_m = ((swm - w * S.m) / (sw - w).replace(0, np.nan)).fillna((w * S.m).sum() / w.sum())
        # between-group variance (DL on group means around side means)
        G = pd.DataFrame(dict(g=grp, side=S.side, w=w, m=S.m)).groupby(["g", "side"]).apply(
            lambda x: pd.Series(dict(gm=(x.w * x.m).sum() / x.w.sum(), gv=1 / x.w.sum())), include_groups=False
        ).reset_index()
        G["sm"] = G.side.map(lambda sd: (w[S.side == sd] * S.m[S.side == sd]).sum() / w[S.side == sd].sum())
        tg2 = _dl_tau2((G.gm - G.sm).to_numpy(), G.gv.to_numpy()) if len(G) >= 3 else 0.0
        lam = (loo_w / (loo_w + 1 / max(tg2, 1e-6))).fillna(0.0)          # how much to trust the LOO group mean
        pm = (lam * loo_m.fillna(0) + (1 - lam) * side_m)
        tau2 = max(_dl_tau2((S.m - pm).to_numpy(), V.to_numpy()), p["tau2_floor"])
    return pm, pd.Series(tau2, index=S.index)


def load_priors(path: Path | None = None) -> pd.DataFrame:
    path = path or HERE / "priors.csv"
    if not path.exists():
        return pd.DataFrame(columns=["bt_mean", "bt_se", "bt_n", "bt_src"])
    return pd.read_csv(path).set_index("setup")


def bt_prior(S: pd.DataFrame, V: pd.Series, P: pd.DataFrame, col: str = "bt_mean", p=PARAMS
             ) -> tuple[pd.Series, pd.Series, dict]:
    """Backtest prior + empirical lab->live gap per side (DL); setups without a backtest fall back to eb."""
    em, ev = eb_prior(S, V, p)
    has = S.index.intersection(P.index[P[col].notna()])
    pm, pv, info = em.copy(), ev.copy(), {}
    for side in ("long", "short"):
        ids = [s for s in has if S.loc[s, "side"] == side]
        if len(ids) < 5:
            continue
        b = P.loc[ids, col].astype(float)
        sec = col.replace("_mean", "") + "_se" if col != "bt_mean" else "bt_se"
        bse2 = P.loc[ids, sec].astype(float).fillna(0.0) ** 2
        r = (S.loc[ids, "m"] - b).to_numpy()
        v = (V[ids] + bse2).to_numpy()
        t2 = _dl_tau2(r, v)
        w = 1 / (v + t2)
        gap = float((w * r).sum() / w.sum())
        t2 = max(t2, p["tau2_floor"])
        pm[ids] = b + gap
        pv[ids] = t2 + bse2
        info[side] = dict(gap=gap, tau=math.sqrt(t2), n=len(ids))
    return pm, pv, info


# -------------------------------------------------------------------------------------------------- posteriors
def posterior(S, V, prior_m, prior_v):
    pv = 1 / (1 / V + 1 / prior_v)
    pm = pv * (S.m / V + prior_m / prior_v)
    return pm, pv


def sprt_llr(S, V, p=PARAMS):
    h0, h1 = p["sprt_h0"], p["sprt_h1"]
    return (h1 - h0) * (S.m - (h0 + h1) / 2) / V


def evaluate(T: pd.DataFrame, method: str = "eb", priors: pd.DataFrame | None = None, p=PARAMS,
             bt_col: str = "bt_mean") -> pd.DataFrame:
    """Posterior + call for every setup in trades T (data known at the decision date only)."""
    D = day_table(T)
    S = setup_stats(D)
    c, s2, deff = pooled_var(S, T)
    V = regularised_var(S, c, p["k0"])
    S["se"] = np.sqrt(V)
    shared_v = pd.Series(0.0, index=S.index)            # variance shared by all setups of a side (ebx only)
    if method == "ebx":
        Dx, fbar = excess_day_table(D)
        Sx = setup_stats(Dx)
        cx, _, _ = pooled_var(Sx)
        Vx = regularised_var(Sx, cx, p["k0"])
        am0, av0 = eb_prior(Sx, Vx, p)
        av = 1 / (1 / Vx + 1 / av0)
        am = av * (Sx.m / Vx + am0 / av0)
        fm = S.side.map(lambda sd: fbar[sd][0])
        shared_v = S.side.map(lambda sd: fbar[sd][1])
        pm0, pv0 = fm + am0, shared_v + av0
        pm, pv = fm + am, shared_v + av
        S["alpha"], S["alpha_se"] = Sx.m, np.sqrt(Vx)
        V_info = Vx
    else:
        if method == "eb":
            pm0, pv0 = eb_prior(S, V, p)
        elif method == "bt":
            pm0, pv0, _ = bt_prior(S, V, priors if priors is not None else load_priors(), bt_col, p)
        elif method in ("flat", "sprt"):
            pm0 = pd.Series(0.0, index=S.index)
            pv0 = pd.Series(p["flat_prior_sd"] ** 2, index=S.index)
        else:
            raise ValueError(method)
        pm, pv = posterior(S, V, pm0, pv0)
        V_info = V
    S["prior_m"], S["prior_sd"] = pm0, np.sqrt(pv0)
    S["post_m"], S["post_sd"] = pm, np.sqrt(pv)
    S["p_pos"] = norm.sf(0, pm, np.sqrt(pv))
    S["p_neg05"] = norm.cdf(p["demote_line"], pm, np.sqrt(pv))
    ok = (S.k >= p["min_sess"]) & (S.N >= p["min_trades"])
    if method == "sprt":
        llr = sprt_llr(S, V, p)
        A = math.log((1 - p["sprt_beta"]) / p["sprt_alpha"])
        B = math.log(p["sprt_beta"] / (1 - p["sprt_alpha"]))
        S["llr"] = llr
        prom, dem = ok & (llr >= A), ok & (llr <= B)
    else:
        prom = ok & (S.p_pos >= p["p_promote"])
        dem = ok & (S.p_neg05 >= p["p_demote"])
    if p.get("own_agree"):
        prom, dem = prom & (S.m > 0), dem & (S.m < 0)
    if p.get("repsmin_demote_floor"):
        floor = ((S.k >= 8) & (S.N >= 30) & (S.m * S.N / (S.N + 20) <= -0.10)
                 & ~(S.exbest >= 0) & (S.last5 < 0))
        dem = (dem | floor) & ~prom
    S["call"] = np.where(prom, "promote", np.where(dem, "demote", ""))
    # projection: sessions until a threshold is crossed if the posterior mean holds
    sessions_live = T.date.nunique()
    rate_k = S.k / S.apply(lambda r: max(1, (T.date.unique() >= r["first"]).sum()), axis=1)   # traded sessions/session
    per_sess_info = 1 / (V_info * S.k)                    # information added by one traded session
    own_v = pv - shared_v
    n_days = T.date.nunique()
    zp, zd = norm.ppf(p["p_promote"]), norm.ppf(p["p_demote"])
    exp_sess = []
    for s, r in S.iterrows():
        if r.call:
            exp_sess.append(0.0)
            continue
        best = np.inf
        for h in range(1, p["horizon"] + 1):
            k_new = h * rate_k[s]
            v_h = 1 / (1 / own_v[s] + k_new * per_sess_info[s]) + shared_v[s] * n_days / (n_days + h)
            sd_h = math.sqrt(v_h)
            # experience floor reached?
            if r.k + k_new < p["min_sess"] or r.N + k_new * r.N / r.k < p["min_trades"]:
                continue
            okp = r.m > 0 or not p.get("own_agree")
            okd = r.m < 0 or not p.get("own_agree")
            if (okp and pm[s] / sd_h >= zp) or (okd and (p["demote_line"] - pm[s]) / sd_h >= zd):
                best = h
                break
        exp_sess.append(best)
    S["exp_sessions"] = exp_sess
    S["lean"] = np.where(S.post_m > 0, "promote", np.where(S.post_m < p["demote_line"], "demote", "middle"))
    S["status"] = np.select(
        [S.call == "promote", S.call == "demote", S.exp_sessions <= p["on_track_sessions"]],
        ["promote-ready", "demote-ready", "on-track"], "undecided")
    S["one_day"] = S.best_share >= 0.5
    S.attrs.update(sessions=sessions_live, s2=s2, deff=deff, c=c)
    return S


# ------------------------------------------------------------------------------------------------- priors build
def build_priors(bt_dir: Path, out: Path = HERE / "priors.csv") -> pd.DataFrame:
    """Per setup 2y lab mean and day-clustered SE (locked block 2024-11..2025-02 out, to 2026-10-05, i.e. pre-live),
    raw and E90-borrow-restricted for shorts. -FD setups without their own lab list borrow the base's."""
    import glob
    lab = pd.concat(pd.read_parquet(f, columns=["setup", "side", "symbol", "date", "r"])
                    for f in sorted(glob.glob(str(bt_dir / "sig_*.parquet"))))
    lab["date"] = lab.date.astype(str)
    lab = lab[~lab.date.between("2024-11-01", "2025-02-28") & (lab.date <= "2026-10-05")]
    # ETB history from the committed morning universe.csv snapshots (L3LEASH-2 method)
    snaps = []
    for br in ("mcf-data", "mcf-data-testing", "mcf-data-testing2"):
        for h in _git("log", "--format=%H", f"origin/{br}", "--", "universe.csv").decode().split():
            try:
                u = pd.read_csv(io.BytesIO(_git("show", f"{h}:universe.csv")),
                                usecols=["symbol", "shortable", "easy_to_borrow", "built_at"])
            except Exception:
                continue
            snaps.append(u)
    U = pd.concat(snaps).drop_duplicates(["symbol", "built_at"])
    U["day"] = pd.to_datetime(U.built_at, utc=True).dt.strftime("%Y-%m-%d")
    U["ok"] = (U.shortable.astype(bool) & U.easy_to_borrow.astype(bool)).astype(float)
    rate = U.groupby(["day", "symbol"]).ok.mean().groupby("symbol").mean()
    lab["e90"] = (lab.side > 0) | (lab.symbol.map(rate).fillna(0) >= 0.9)

    def agg(x):
        d = x.groupby("date").r.agg(["sum", "size"])
        N, k = d["size"].sum(), len(d)
        m = d["sum"].sum() / N
        e = d["sum"] - m * d["size"]
        se = math.sqrt(k / (k - 1) * (e ** 2).sum()) / N if k > 1 else np.nan
        return m, se, N

    rows = []
    for s, x in lab.groupby("setup"):
        m, se, n = agg(x)
        me, see, ne = agg(x[x.e90]) if x.e90.any() else (np.nan, np.nan, 0)
        rows.append(dict(setup=s, bt_mean=m, bt_se=se, bt_n=n, bt_e90=me, bt_e90_se=see, bt_e90_n=ne,
                         bt_src="2y lab", etb_snapshots=int(U.day.nunique())))
    P = pd.DataFrame(rows).set_index("setup")
    out.write_text(P.reset_index().to_csv(index=False, float_format="%.5f"))
    return P


def expand_priors(P: pd.DataFrame, setups) -> pd.DataFrame:
    """-FD setups without their own lab list use the base's (flagged bt_src='2y lab (base)')."""
    P = P.copy()
    for s in setups:
        if s not in P.index and s.endswith("-FD") and s[:-3] in P.index:
            P.loc[s] = P.loc[s[:-3]]
            P.loc[s, "bt_src"] = "2y lab (base)"
    return P


def fwdrep_filter(path: Path = ROOT / "research/fwdrep/out/setup_fwd.csv") -> pd.DataFrame | None:
    """Forward-replay hook. Contract (see NOTES section 6): CSV with setup, sessions, trades, avgR, se, audit_pass.
    Used ONLY as a filter column (rule 21) - never in the posterior."""
    if not path.exists():
        return None
    f = pd.read_csv(path).set_index("setup")
    return f[f.get("audit_pass", True).astype(bool)] if "audit_pass" in f else f


# -------------------------------------------------------------------------------------------------------- nightly
def _action(status: str, homes: list, sid: str) -> str:
    """What the status suggests. Every move is still the owner's decision (promotion = move, rule 20, GEN / Graveyard)."""
    if status == "promote-ready":
        return "keep" if "primary" in homes else "promote-review"
    if status == "demote-ready":
        if "graveyard" in homes:
            return "stay-graveyard"          # already at the bottom; retiring is the owner's call
        if sid.startswith("GEN-") or "gen" in homes:
            return "propose-owner"           # no GEN setup is demoted without the owner's consent
        return "demote-review"
    return "collect"


def nightly(journals=None, asof=None, method="flat", out=HERE / "out") -> dict:
    asof = asof or default_asof()
    T = load_trades(journals, asof)
    P = expand_priors(load_priors(), T.strategy.unique())
    S = evaluate(T, method, P)
    S = S[S.N >= 5]
    try:
        from mcf import setup_names
        nm = setup_names.name
    except Exception:  # pragma: no cover
        nm = lambda s: s
    homes = {}
    try:
        A = json.loads((ROOT / "docs/live/assignments.json").read_text())["accounts"]
        for acct, ss in A.items():
            for s in ss:
                homes.setdefault(s, []).append(acct)
    except Exception:
        pass
    FW = fwdrep_filter()
    rows = []
    for s, r in S.sort_values(["status", "p_pos"], ascending=[True, False]).iterrows():
        rows.append(dict(
            setup=s, name=nm(s), family=r.family, side=r.side, home="+".join(homes.get(s, [])),
            trades=int(r.N), traded_sessions=int(r.k), avgR=round(r.m, 4), se_clustered=round(r.se, 4),
            prior_mean=round(r.prior_m, 4), post_mean=round(r.post_m, 4), post_sd=round(r.post_sd, 4),
            p_avgR_gt_0=round(r.p_pos, 3), p_avgR_lt_m005=round(r.p_neg05, 3),
            exp_sessions_to_verdict=None if not np.isfinite(r.exp_sessions) else int(r.exp_sessions),
            lean=r.lean, status=r.status,
            action=_action(r.status, homes.get(s, []), s),
            last5_avgR=round(r.last5, 4),
            avgR_wo_best_day=None if pd.isna(r.exbest) else round(r.exbest, 4),
            best_day_share=None if pd.isna(r.best_share) else round(r.best_share, 3), one_day=bool(r.one_day),
            bt_prior=None if s not in P.index or pd.isna(P.loc[s, "bt_mean"]) else round(float(P.loc[s, "bt_mean"]), 4),
            fwdrep_avgR=None if FW is None or s not in FW.index else round(float(FW.loc[s, "avgR"]), 4),
        ))
    res = dict(version=VERSION, asof=asof, generated=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
               method=method, params=PARAMS, sessions=int(T.date.nunique()),
               pooled=dict(per_trade_var=round(S.attrs.get("s2", np.nan), 4), design_effect=round(S.attrs.get("deff", np.nan), 2)),
               note="Paper results. P() are model posteriors, not guarantees. Educational only - not financial advice.",
               counts={k: int((S.status == k).sum()) for k in ("promote-ready", "on-track", "undecided", "demote-ready")},
               setups=rows)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "decisions.json").write_text(json.dumps(res, indent=1, default=float))
    pd.DataFrame(rows).to_csv(out / "decisions.csv", index=False)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description="FASTDEC nightly decision engine (research; educational only)")
    ap.add_argument("--journals", help="dir with <acct>/journal.db (default: git show origin/mcf-data*)")
    ap.add_argument("--asof", help="last session to include (default: last closed session)")
    ap.add_argument("--method", default="flat", choices=["eb", "ebx", "flat", "sprt", "bt"])
    ap.add_argument("--out", default=str(HERE / "out"))
    ap.add_argument("--build-priors", metavar="BT_DIR", nargs="?", const=str(ROOT / "research/history2y/data/bt_lab1104"))
    a = ap.parse_args(argv)
    if a.build_priors:
        P = build_priors(Path(a.build_priors))
        print(f"priors.csv: {len(P)} setups")
        return
    res = nightly(a.journals, a.asof, a.method, a.out)
    print(f"FASTDEC {res['asof']} ({res['sessions']} sessions, method {res['method']}): {res['counts']}")
    for st in ("promote-ready", "demote-ready"):
        for r in res["setups"]:
            if r["status"] == st:
                print(f"  {st:14s} {r['setup']:55s} n={r['trades']:4d} k={r['traded_sessions']:2d} "
                      f"avgR={r['avgR']:+.3f} post={r['post_mean']:+.3f} P>0={r['p_avgR_gt_0']:.2f}"
                      f"{'  1 day' if r['one_day'] else ''}")
    print("Educational only - not financial advice.")


if __name__ == "__main__":
    sys.exit(main())
