"""REPS2 item 4: pre-registered sequential early-decision test (research/reps2/PREREG_SPRT.md). Two Wald SPRTs per setup
on its live, cost-in record (session unit): FAILS (H1 mu = -d) and WORKS (H1 mu = +d) against break-even (mu = 0).

    python research/reps2/sprt.py                      # verdicts today + error-rate checks -> research/reps2/sprt/
    python research/reps2/sprt.py --verdicts-only      # nightly: verdicts only (fast)

Educational only - not financial advice."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import data as D  # noqa: E402

ALPHA, BETA = 0.05, 0.20
A_UP, B_DN = math.log((1 - BETA) / ALPHA), math.log(BETA / (1 - ALPHA))
MAX_K, MAX_N = 60, 600
SEED = 20261118
MUS = [-0.30, -0.20, -0.10, 0.0, 0.10, 0.20, 0.30]


def nuisance(live: pd.DataFrame) -> tuple[float, float]:
    """Pooled sigma^2 (per trade, around each setup's mean) and same-session correlation rho (moment estimates)."""
    x = live.dropna(subset=["r"])
    res = x["r"] - x.groupby("strategy")["r"].transform("mean")
    s2 = float((res ** 2).mean())
    g = pd.DataFrame({"k": list(zip(x["strategy"], x["date"])), "e": res, "q": res ** 2}).groupby("k")
    sm, sq, n = g["e"].sum(), g["q"].sum(), g["e"].size()
    rho = float(((sm ** 2 - sq).sum() / (n * (n - 1)).sum()) / s2)
    return s2, max(0.0, min(rho, 0.9))


def sessions_of(live: pd.DataFrame) -> dict[str, pd.DataFrame]:
    x = live.dropna(subset=["r"])
    g = x.groupby(["strategy", "date"])["r"].agg(n="size", s="sum").reset_index().sort_values(["strategy", "date"])
    return {k: v.reset_index(drop=True) for k, v in g.groupby("strategy")}


def _guard_ok(n: np.ndarray, s: np.ndarray, i: int) -> bool:
    """One-big-day guard on sessions 0..i: avg R without the best session > 0 and best session < 50% of total R."""
    nn, ss = n[: i + 1], s[: i + 1]
    b = int(np.argmax(ss))
    rest = nn.sum() - nn[b]
    tot = ss.sum()
    return rest > 0 and (tot - ss[b]) / rest > 0 and tot > 0 and ss[b] / tot < 0.5


def run_test(n: np.ndarray, s: np.ndarray, d: float, s2: float, rho: float, a_up: float = A_UP) -> dict:
    """Sequential pass over sessions (n trades, s sum R each). Returns the first crossing of each test. A WORKS crossing
    counts only when the one-big-day guard holds at that session; otherwise the test goes on (PREREG_SPRT.md)."""
    v = n * s2 * (1 + (n - 1) * rho)
    out = {}
    for name, mu1 in (("fail", -d), ("works", d)):
        inc = n * mu1 * (s - n * mu1 / 2) / v
        llr = np.cumsum(inc)
        cn = np.cumsum(n)
        verdict, at, flagged = "continue", None, None
        for i, l in enumerate(llr):
            if i + 1 > MAX_K or cn[i] > MAX_N:
                verdict, at = "truncated", i
                break
            if l >= a_up:
                if name == "works" and not _guard_ok(n, s, i):
                    flagged = i if flagged is None else flagged
                    continue
                verdict, at = "call", i
                break
            if l <= B_DN:
                verdict, at = "no", i
                break
        out[name] = {"verdict": verdict, "at": at, "llr": float(llr[-1]) if len(llr) else 0.0, "flagged_1day": flagged}
    return out


def one_big_day(sess: pd.DataFrame) -> tuple[float | None, float | None]:
    """(avg R without the best session, best session's share of total R)."""
    n, tot = int(sess["n"].sum()), float(sess["s"].sum())
    if n == 0:
        return None, None
    b = int(sess["s"].idxmax())
    rest_n = n - int(sess.loc[b, "n"])
    wo = (tot - float(sess.loc[b, "s"])) / rest_n if rest_n else None
    share = float(sess.loc[b, "s"]) / tot if tot > 0 else None
    return wo, share


def verdict_of(t: dict, sess: pd.DataFrame) -> str:
    f, w = t["fail"], t["works"]
    if f["verdict"] == "call":
        return "FAIL"
    if w["verdict"] == "call":
        return "WORKS"
    if w["verdict"] == "continue" and w.get("flagged_1day") is not None and w["llr"] >= A_UP:
        return "WORKS?-1day (continue)"
    if f["verdict"] == "truncated" or w["verdict"] == "truncated":
        return "UNDECIDED (truncated)"
    if f["verdict"] == "no" and w["verdict"] == "no":
        return "neither big (continue)"
    if w["verdict"] == "no":
        return "not a big winner (continue)"
    if f["verdict"] == "no":
        return "not a big loser (continue)"
    return "continue"


def verdicts(live: pd.DataFrame, d: float = 0.20, current: dict | None = None, a_up: float = A_UP) -> pd.DataFrame:
    s2, rho = nuisance(live)
    ss = sessions_of(live)
    names = sorted(set(ss) | set(current or {}))
    rows = []
    for k in names:
        sess = ss.get(k, pd.DataFrame(columns=["date", "n", "s"]))
        n, s = sess["n"].to_numpy(float), sess["s"].to_numpy(float)
        t = run_test(n, s, d, s2, rho, a_up) if len(sess) else {"fail": {"verdict": "continue", "at": None, "llr": 0.0},
                                                          "works": {"verdict": "continue", "at": None, "llr": 0.0}}
        v = verdict_of(t, sess) if len(sess) else "continue"
        wo, share = one_big_day(sess) if len(sess) else (None, None)
        at = t["fail"]["at"] if v == "FAIL" else (t["works"]["at"] if v.startswith("WORKS") else None)
        rows.append({"setup": k, "accounts": ",".join((current or {}).get(k, [])), "trades": int(n.sum()),
                     "sessions": len(sess), "avg_r": round(float(s.sum() / n.sum()), 4) if n.sum() else None,
                     "avg_r_wo_best": None if wo is None else round(wo, 4),
                     "best_day_share": None if share is None else round(share, 3), "verdict": v,
                     "called_on": None if at is None else str(sess.loc[at, "date"]),
                     "llr_fail": round(t["fail"]["llr"], 3), "llr_works": round(t["works"]["llr"], 3)})
    df = pd.DataFrame(rows)
    df.attrs.update(sigma2=s2, rho=rho, d=d)
    return df


# ------------------------------------------------------------------------------------------------ error-rate checks
def _paths(draw, mu: float, d: float, s2: float, rho: float, reps: int, rng, a_up: float = A_UP) -> list[dict]:
    out = []
    for _ in range(reps):
        n, s = draw(mu, rng)
        t = run_test(n, s, d, s2, rho, a_up)
        f, w = t["fail"], t["works"]
        first = [x["at"] for x in (f, w) if x["verdict"] in ("call",) and x["at"] is not None]
        out.append({"fail": f["verdict"] == "call", "works": w["verdict"] == "call",
                    "trunc": f["verdict"] == "truncated" and w["verdict"] == "truncated",
                    "k": (min(first) + 1) if first else min(MAX_K, len(n)),
                    "n": float(np.cumsum(n)[min(first)]) if first else float(min(n.sum(), MAX_N))})
    return out


def _summ(p: list[dict]) -> dict:
    p = pd.DataFrame(p)
    return {"p_fail": round(p["fail"].mean(), 4), "p_works": round(p["works"].mean(), 4),
            "p_truncated": round(p["trunc"].mean(), 4), "asn_sessions": round(p["k"].mean(), 1),
            "asn_trades": round(p["n"].mean(), 1)}


def parametric(live: pd.DataFrame, d: float, reps: int = 20000) -> dict:
    s2, rho = nuisance(live)
    ns = live.dropna(subset=["r"]).groupby(["strategy", "date"]).size().to_numpy()
    rng = np.random.default_rng(SEED)

    def draw(mu, rng):
        n = rng.choice(ns, MAX_K + 1).astype(float)
        sd = np.sqrt(n * s2 * (1 + (n - 1) * rho))
        return n, n * mu + rng.standard_normal(len(n)) * sd

    return {f"{mu:+.2f}": _summ(_paths(draw, mu, d, s2, rho, reps, rng)) for mu in MUS}


def bootstrap(live: pd.DataFrame, d: float, reps: int = 200, min_k: int = 15, a_up: float = A_UP, mus=None) -> dict:
    """Session-block bootstrap of each setup's real record (>= min_k sessions), re-centred to mu."""
    s2, rho = nuisance(live)
    x = live.dropna(subset=["r"])
    rng = np.random.default_rng(SEED)
    out = {}
    recs = []
    for k, g in x.groupby("strategy"):
        if g["date"].nunique() < min_k:
            continue
        m = g["r"].mean()
        gs = g.assign(r=g["r"] - m).groupby("date")["r"].agg(n="size", s="sum")
        recs.append((gs["n"].to_numpy(float), gs["s"].to_numpy(float)))
    for mu in (mus or MUS):
        allp = []
        for n0, s0 in recs:
            def draw(mu_, rng, n0=n0, s0=s0):
                i = rng.integers(0, len(n0), MAX_K + 1)
                return n0[i], s0[i] + n0[i] * mu_
            allp += _paths(draw, mu, d, s2, rho, reps, rng, a_up)
        out[f"{mu:+.2f}"] = _summ(allp)
    out["setups"] = len(recs)
    return out


def walk_forward(live: pd.DataFrame, d: float, min_later: int = 10) -> dict:
    """First crossing per setup on its record so far; later live avg R after the call vs the call's sign."""
    s2, rho = nuisance(live)
    ss = sessions_of(live)
    rows = []
    for k, sess in ss.items():
        n, s = sess["n"].to_numpy(float), sess["s"].to_numpy(float)
        t = run_test(n, s, d, s2, rho)
        v = verdict_of(t, sess)
        if v not in ("FAIL", "WORKS"):
            continue
        at = t["fail"]["at"] if v == "FAIL" else t["works"]["at"]
        later = sess.iloc[at + 1:]
        if later["n"].sum() < min_later:
            continue
        lr = float(later["s"].sum() / later["n"].sum())
        rows.append({"setup": k, "verdict": v, "called_on": str(sess.loc[at, "date"]), "later_trades": int(later["n"].sum()),
                     "later_avg_r": round(lr, 4), "right": (lr < 0) if v == "FAIL" else (lr > 0)})
    df = pd.DataFrame(rows)
    base = None
    tot = pd.concat(ss.values()) if ss else None
    out = {"calls_scored": len(df)}
    for v in ("FAIL", "WORKS"):
        g = df[df["verdict"] == v] if len(df) else df
        k, m = (int(g["right"].sum()), len(g)) if len(g) else (0, 0)
        out[v] = {"calls": m, "right": k, "precision": None if not m else round(k / m, 3), "wilson95": wilson(k, m),
                  "later_avg_r_mean": None if not m else round(float(g["later_avg_r"].mean()), 4)}
    # base rate: share of setups (>= 2*min_later trades) whose second half is negative
    neg, tot_n = 0, 0
    for k, sess in ss.items():
        if sess["n"].sum() < 2 * min_later:
            continue
        h = sess.iloc[len(sess) // 2:]
        if h["n"].sum() >= min_later:
            tot_n += 1
            neg += int(h["s"].sum() < 0)
    out["base_rate_later_negative"] = None if not tot_n else round(neg / tot_n, 3)
    out["rows"] = rows
    del base, tot
    return out


def calibrate_a(live: pd.DataFrame, d: float, grid=(2.773, 3.0, 3.25, 3.5, 3.75, 4.0, 4.5)) -> dict:
    """ADDENDUM A (v2, post hoc - see NOTES.md): the smallest call boundary whose block-bootstrap false-call rate at
    mu = 0 is <= ALPHA for BOTH tests. Not pre-registered; for a forward check only, never for a decision yet."""
    rows = {}
    for a in grid:
        b = bootstrap(live, d, a_up=a, mus=[0.0, -0.20, 0.20])
        rows[str(a)] = {"false_fail": b["+0.00"]["p_fail"], "false_works": b["+0.00"]["p_works"],
                        "power_fail": b["-0.20"]["p_fail"], "power_works": b["+0.20"]["p_works"],
                        "asn_trades_mu0": b["+0.00"]["asn_trades"]}
        if max(rows[str(a)]["false_fail"], rows[str(a)]["false_works"]) <= ALPHA:
            return {"chosen": a, "grid": rows}
    return {"chosen": None, "grid": rows}


def wilson(k: int, n: int, z: float = 1.96):
    if not n:
        return None
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(c - h, 3), round(c + h, 3)]


def current_setups() -> dict[str, list[str]]:
    a = D.assignments()
    out: dict[str, list[str]] = {}
    for acct, names in a["accounts"].items():
        for n in names:
            out.setdefault(n, []).append(acct)
    return out


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=str(Path(__file__).resolve().parent / "sprt"))
    p.add_argument("--verdicts-only", action="store_true")
    a = p.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    live = D.load()["live"]
    cur = current_setups()
    res = {"alpha": ALPHA, "beta": BETA, "A": round(A_UP, 3), "B": round(B_DN, 3), "max_sessions": MAX_K,
           "max_trades": MAX_N, "through": str(live["date"].max()), "configs": {}}
    for d in (0.20, 0.15, 0.30):
        v = verdicts(live, d, cur)
        res["sigma2"], res["rho"] = round(v.attrs["sigma2"], 4), round(v.attrs["rho"], 4)
        curv = v[v["setup"].isin(cur)]
        c = {"current_setups": len(curv), "verdicts_current": curv["verdict"].value_counts().to_dict(),
             "verdicts_all_live": v[v["trades"] > 0]["verdict"].value_counts().to_dict(),
             "lowrep_0_10_current": curv[curv["trades"] <= 10]["verdict"].value_counts().to_dict()}
        if d == 0.20:
            v.to_csv(out / "verdicts.csv", index=False)
            per_acct = {}
            for acct in sorted({x for xs in cur.values() for x in xs}):
                g = curv[curv["accounts"].str.split(",").apply(lambda xs: acct in xs)]
                per_acct[acct] = g["verdict"].value_counts().to_dict()
            c["per_account"] = per_acct
            if not a.verdicts_only:
                c["parametric"] = parametric(live, d)
                c["bootstrap"] = bootstrap(live, d)
                wf = walk_forward(live, d)
                pd.DataFrame(wf.pop("rows")).to_csv(out / "walk_forward.csv", index=False)
                c["walk_forward"] = wf
        res["configs"][f"d={d:.2f}"] = c
    if not a.verdicts_only:
        cal = calibrate_a(live, 0.20)
        res["addendum_A_v2"] = cal
        if cal["chosen"]:
            v2 = verdicts(live, 0.20, cur, cal["chosen"])
            v2.to_csv(out / "verdicts_v2.csv", index=False)
            curv = v2[v2["setup"].isin(cur)]
            res["addendum_A_v2"]["verdicts_current"] = curv["verdict"].value_counts().to_dict()
    (out / "summary.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: v for k, v in res.items() if k != "configs"}, default=str))
    for k, c in res["configs"].items():
        print(k, "current:", c["verdicts_current"], "| low-rep:", c["lowrep_0_10_current"])
    return res


if __name__ == "__main__":
    main()
