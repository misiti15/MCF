"""FOOTRACE (owner 2026-11-19, answer to research/ultimate_1119/footrace/PROPOSAL.md: "Exit rule + gy only - GY should
also have a similar footrace mentality as in, if there are, say the top 10-20 of setups who are best performing, they can
get the majority of the exposure while lower performing setups can be on a rotation."). Effective 2026-11-20.

Three pieces, all on the live record (every account's journal, run 1, R after costs on the LR8 basis, identical signals
across accounts counted once):

  (a) FOOTRACE-EXIT   the Friday-review exit for the testing arena (Testing A-F + Setup Generator); it REPLACES the
                      C3-EXIT100 thresholds. Move to the Graveyard when ALL hold: >= 15 active days (arena_reps.json),
                      >= 30 live trades, avg R <= 0, avg R w/o best day <= 0 and a day-clustered t <= -1.5 (t of the
                      per-day mean R). Untouched: below those reps, rare / day-gated setups (< 0.5 signals per active
                      day), setups admitted on 2026-11-20 (and later admissions in their first 15 active days), Workbench
                      copies in their first 15 active days. Leader priority in the testing arena is NOT adopted (held).
  (b) GY-LIFE archive at the Friday review: the GY-LIFE conditions 1-4 (research/graveyard_review_1118/RULE.md; 5 =
                      no pending test, checked by hand), at most 4 a week, never the two Compass exemptions.
  (c) GY foot race    the Graveyard's setups are ranked every night by the shrunk live score (mean of the ranks of total R
                      w/o best day and of avg R w/o best day shrunk by n / (n + 20), the leaderboard's SHRINK_N), with
                      the one-big-day tag. The top 15 (>= 10 live trades) are LEADERS: they play every session and come
                      first in setup_order (first claim on slots / buying power). The rest ROTATE by whole sessions (owner
                      playing-time rule 2026-11-03: benched sessions are logged and excluded from per-session stats;
                      never an in-session throttle), filled to <= 85% of the Graveyard's slots, and never benched more
                      than 2 sessions in a row (>= 1 session in 3). Rare / day-gated setups and setups the plan does not
                      know (new entrants) always play.

The plan for the next 3 sessions is written to docs/live/footrace.json by the nightly job (research/reps2/nightly.py
step 5, or `python -m mcf.report.footrace`); the trade run applies it once, before the open, when it writes the session's
setup snapshot (mcf/execution/session.py -> apply_gy). Missing file, bad file or no entry for the session -> today's
behaviour (every enabled Graveyard setup plays).

    python -m mcf.report.footrace [--asof YYYY-MM-DD] [--out docs/live/footrace.json] [--review]

Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "live" / "footrace.json"
DISCLAIMER = "Educational only - not financial advice."

# (a) FOOTRACE-EXIT (owner 2026-11-19)
EXIT_MIN_DAYS, EXIT_MIN_TRADES, EXIT_MAX_T, RARE_SIG_PER_DAY = 15, 30, -1.5, 0.5
EXIT_FROM = "2026-11-20"
ADMITTED_1120 = ("ETFDISP-late-dip-hidisp-long", "ULT-HV2-shock-snap-etf-long-K", "ULT-22-wb4-wide-etf-long",
                 "ULT-14-snap-long", "ULT-14-snap-short", "ULT-13-st7-sharp-long", "ULT-HV1-etf-late-pop-fade-short-X",
                 "ULT-05-withgap-cont-long", "ULT-05-withgap-cont-short", "ULT-09-failed-vwap-reclaim-short",
                 "ULT-07-pm-volatile-dip-long")
ARENA = ("testing2", "explore1", "livelab", "testingd", "testinge", "testingf", "gen")

# (b) GY-LIFE archive (owner GY-LIFE 2026-11-18; FOOTRACE 2026-11-19: up to 4 a week)
ARCHIVE_MAX = 4
COMPASS_EXEMPT = ("CWT14-failbrk-orl-p05-long", "heat_fade_short-FD")

# (c) GY foot race
GY_LEADERS, GY_MIN_TRADES, GY_SLOT_LINE, GY_MAX_BENCH_RUN, GY_HORIZON = 15, 10, 0.85, 2, 3
# peak concurrent lots per trade of the session, Graveyard 11-17 (374 trades -> 239 lots peak; the only busy unsaturated
# day in research/ultimate_1119/footrace/sim/capacity_1112_1118.csv; 11-18: 179 -> 87 = 0.49)
LOTS_PER_TRADE = 0.64


def _shrink_n() -> int:
    from .scorecard import SHRINK_N

    return int(SHRINK_N)


# ------------------------------------------------------------------------------------------------------- stats
def day_t(day_means: pd.Series) -> float:
    """Day-clustered t: mean of the per-day mean R over its standard error (0 with <= 2 days or no spread)."""
    x = day_means.astype(float)
    if len(x) <= 2:
        return 0.0
    sd = float(x.std(ddof=1))
    return 0.0 if not sd > 0 else float(x.mean() / (sd / math.sqrt(len(x))))


def setup_stats(trades: pd.DataFrame) -> pd.DataFrame:
    """Per setup from live trades (columns strategy, date, r): n, days, total, avg, w/o best day (total, avg), best-day
    share and `1 day` tag (>= 50%), day-clustered t, last-10-day total and the foot-race score inputs."""
    k = _shrink_n()
    rows = []
    for s, g in trades.groupby("strategy"):
        r = g["r"].astype(float)
        day = g.groupby(g["date"].astype(str))["r"]
        dsum, dmean = day.sum(), day.mean()
        best = dsum.idxmax()
        wo = g.loc[g["date"].astype(str) != best, "r"].astype(float)
        tot = float(r.sum())
        share = float(dsum.max()) / tot if tot > 0 else None
        rows.append({"setup": s, "n": int(len(r)), "days": int(len(dsum)), "total_r": tot, "avg_r": float(r.mean()),
                     "wo_total_r": float(wo.sum()), "wo_avg_r": float(wo.mean()) if len(wo) else 0.0,
                     "best_share": share, "one_day": bool(share is not None and share >= 0.5),
                     "t_day": day_t(dmean), "last10_r": float(dsum.sort_index().tail(10).sum()),
                     "shrunk_wo": float(wo.sum()) / (len(wo) + k),
                     "big_days": int((dsum >= 10).sum()), "big_sum": float(dsum[dsum >= 10].sum())})
    t = pd.DataFrame(rows).set_index("setup") if rows else pd.DataFrame(
        columns=["n", "days", "total_r", "avg_r", "wo_total_r", "wo_avg_r", "best_share", "one_day", "t_day",
                 "last10_r", "shrunk_wo", "big_days", "big_sum"])
    return t


def score(t: pd.DataFrame) -> pd.Series:
    """Foot-race score (lower = better): mean of the ranks of total R w/o best day and shrunk avg R w/o best day."""
    if not len(t):
        return pd.Series(dtype=float)
    return (t["wo_total_r"].rank(ascending=False) + t["shrunk_wo"].rank(ascending=False)) / 2


# ------------------------------------------------------------------------------------------------ (a) exit rule
def exit_flag(row: dict, reps: dict | None, exempt: bool = False) -> bool:
    """FOOTRACE-EXIT for one arena setup: row = setup_stats row (n, avg_r, wo_avg_r, t_day), reps = arena_reps row
    (active_days, signals)."""
    if exempt or not reps:
        return False
    days = float(reps.get("active_days") or 0)
    if days < EXIT_MIN_DAYS or int(row.get("n") or 0) < EXIT_MIN_TRADES:
        return False
    if float(reps.get("signals") or 0) / days < RARE_SIG_PER_DAY:       # rare / day-gated: never moved by this rule
        return False
    return (float(row["avg_r"]) <= 0 and float(row["wo_avg_r"]) <= 0 and float(row["t_day"]) <= EXIT_MAX_T)


def exit_review(t: pd.DataFrame, arena: dict[str, str], reps: dict, exempt: set | None = None) -> list[dict]:
    """The arena setups FOOTRACE-EXIT moves to the Graveyard at the Friday review. arena: setup -> account."""
    exempt = set(exempt or ()) | set(ADMITTED_1120)
    out = []
    for s, acct in sorted(arena.items()):
        if s not in t.index:
            continue
        row = t.loc[s].to_dict()
        rp = reps.get(s) or {}
        wb_young = "-WB" in s and float(rp.get("active_days") or 0) < EXIT_MIN_DAYS
        if exit_flag(row, rp, exempt=s in exempt or wb_young):
            out.append({"setup": s, "account": acct, "active_days": int(rp.get("active_days") or 0), "trades": int(row["n"]),
                        "total_r": round(row["total_r"], 1), "avg_r": round(row["avg_r"], 3),
                        "wo_avg_r": round(row["wo_avg_r"], 3), "t_day": round(row["t_day"], 2),
                        "one_day": bool(row["one_day"])})
    return sorted(out, key=lambda x: x["t_day"])


# --------------------------------------------------------------------------------------------- (b) GY archive
def archive_review(gy: pd.DataFrame, whole: pd.DataFrame, residents: list[str], pending: set | None = None,
                   max_n: int = ARCHIVE_MAX) -> list[dict]:
    """GY-LIFE archive candidates (conditions 1-4 of research/graveyard_review_1118/RULE.md; 5 = `pending` tests),
    Compass exemptions kept (the two named setups and any high-volume big-day-cluster setup), worst last-10 first,
    at most `max_n`. gy: setup_stats of Graveyard trades; whole: setup_stats of the whole live record (deduplicated)."""
    pending = set(pending or ())
    out = []
    for s in residents:
        if s not in gy.index or s not in whole.index or s in COMPASS_EXEMPT or s in pending:
            continue
        g, w = gy.loc[s], whole.loc[s]
        if compass_exempt(int(w["n"]) / max(1, int(w["days"])), int(w["big_days"]), float(w["big_sum"])):
            continue
        if not (g["n"] >= 100 and g["days"] >= 10 and g["avg_r"] <= -0.05 and g["wo_avg_r"] <= 0
                and w["n"] >= 150 and w["wo_avg_r"] <= -0.05 and w["last10_r"] <= 0):
            continue
        out.append({"setup": s, "gy_trades": int(g["n"]), "gy_avg_r": round(float(g["avg_r"]), 3),
                    "gy_wo_avg_r": round(float(g["wo_avg_r"]), 3), "trades": int(w["n"]),
                    "wo_avg_r": round(float(w["wo_avg_r"]), 3), "last10_r": round(float(w["last10_r"]), 1)})
    return sorted(out, key=lambda x: x["last10_r"])[:max_n]


def compass_exempt(trades_per_session: float, big_days: int, big_sum: float) -> bool:
    """Owner GY-LIFE exception (Market Compass candidate): >= 15 trades per session and >= 3 days >= +10R that together
    make >= +40R (sessions = traded days of the whole record)."""
    return trades_per_session >= 15 and big_days >= 3 and big_sum >= 40


# ------------------------------------------------------------------------------------------- (c) GY foot race
# NYSE full-day closures ahead (weekdays with no session; the plan skips them)
CLOSED = {"2026-11-26", "2026-12-25", "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26", "2027-05-31",
          "2027-06-18", "2027-07-05", "2027-09-06", "2027-11-25", "2027-12-24"}


def next_sessions(asof: date, n: int) -> list[str]:
    """The `n` weekday sessions after `asof`, NYSE closures skipped."""
    out, d = [], asof
    while len(out) < n:
        d += timedelta(days=1)
        if d.weekday() < 5 and d.isoformat() not in CLOSED:
            out.append(d.isoformat())
    return out


def bench_runs(prev: dict | None, upto: str) -> dict[str, int]:
    """Benched-in-a-row count per rotating setup after session `upto`, from the previous plan (its start_runs, then
    its schedule for the sessions <= upto)."""
    if not prev:
        return {}
    runs = {k: int(v) for k, v in (prev.get("start_runs") or {}).items()}
    pool = set(prev.get("rotation") or [])
    for d in sorted(prev.get("schedule") or {}):
        if d > upto:
            break
        play = set(prev["schedule"][d])
        for k in pool:
            runs[k] = 0 if k in play else runs.get(k, 0) + 1
    return runs


def gy_plan(members: list[str], t: pd.DataFrame, load: dict[str, float], sessions: list[str], slots: int,
            rare: set | None = None, runs: dict | None = None, n_leaders: int = GY_LEADERS) -> dict:
    """Leaders + a whole-session rotation for `sessions`. members: enabled Graveyard setups; t: setup_stats (whole live
    record); load: setup -> expected trades per session; slots: the Graveyard's slots. Leaders, rare setups and low-rep
    members (< GY_MIN_TRADES live trades) always play; the others are added best-first (longest bench run, then score) while the expected
    peak lots stay <= GY_SLOT_LINE x slots, and any setup benched GY_MAX_BENCH_RUN sessions in a row plays regardless."""
    rare = set(rare or ())
    sc = score(t.loc[[m for m in members if m in t.index]]) if len(t) else pd.Series(dtype=float)
    ranked = sorted(sc.index, key=lambda k: (sc[k], k))
    elig = [k for k in ranked if int(t.loc[k, "n"]) >= GY_MIN_TRADES]
    leaders = elig[:n_leaders]
    # always play: leaders, rare / day-gated setups and low-rep setups (< GY_MIN_TRADES live trades or no record):
    # a low-rep setup is never benched for a leader (playing time, owner 2026-11-03)
    always = set(leaders) | {m for m in members if m in rare or m not in t.index or int(t.loc[m, "n"]) < GY_MIN_TRADES}
    pool = sorted((m for m in members if m not in always), key=lambda k: (sc.get(k, 1e9), k))
    med = float(pd.Series([v for v in load.values() if v]).median()) if any(load.values()) else 10.0
    lots = {m: LOTS_PER_TRADE * float(load.get(m) or med) for m in members}
    line = GY_SLOT_LINE * slots
    base = sum(lots[m] for m in always)
    start = {k: int((runs or {}).get(k, 0)) for k in pool}
    cur, schedule, est = dict(start), {}, {}
    for d in sessions:
        must = [k for k in pool if cur[k] >= GY_MAX_BENCH_RUN]
        play, used = list(must), base + sum(lots[k] for k in must)
        for k in sorted((k for k in pool if k not in must), key=lambda k: (-cur[k], sc.get(k, 1e9), k)):
            if used + lots[k] <= line:
                play.append(k)
                used += lots[k]
        for k in pool:
            cur[k] = 0 if k in play else cur[k] + 1
        schedule[d] = sorted(play)
        est[d] = {"playing": len(always) + len(play), "benched": len(pool) - len(play),
                  "est_peak_lots": round(used), "est_slot_pct": round(100 * used / slots, 1)}
    rows = {k: {"rank": i + 1, "trades": int(t.loc[k, "n"]), "total_r": round(float(t.loc[k, "total_r"]), 1),
                "wo_total_r": round(float(t.loc[k, "wo_total_r"]), 1), "wo_avg_r": round(float(t.loc[k, "wo_avg_r"]), 3),
                "one_day": bool(t.loc[k, "one_day"]), "load": round(float(load.get(k) or med), 1)}
            for i, k in enumerate(ranked)}
    return {"leaders": leaders, "always": sorted(always - set(leaders)), "rotation": pool, "start_runs": start,
            "schedule": schedule, "estimate": est, "slots": slots, "slot_line": GY_SLOT_LINE, "table": rows}


def apply_gy(cfg: dict, asof=None, root=None) -> dict:
    """Trade run, once before the open (session.freeze_setups): in the Graveyard, bench for session `asof` the rotating
    setups the plan does not play and put the leaders first in live.setup_order (in place). Logged in
    cfg['rotation']['footrace']. Missing / bad / stale plan -> nothing changes (today's behaviour). Never raises."""
    from ..rotation import session_date

    fc = cfg.get("gy_footrace") or {}
    d = session_date(asof)
    if cfg.get("account_name") != "graveyard" or not fc.get("enabled") or d < date.fromisoformat(str(fc.get("from") or d)):
        return {}
    log = cfg.setdefault("rotation", {"session": d.isoformat(), "benched": [], "away": {}, "guests": {}})
    try:
        base = Path(root) if root else ROOT
        plan = (json.loads((base / str(fc.get("file") or "docs/live/footrace.json")).read_text()).get("gy") or {})
        play = plan["schedule"][d.isoformat()]
    except Exception as e:
        log["footrace"] = {"applied": False, "why": f"no plan for {d} ({type(e).__name__}); every Graveyard setup plays"}
        return log["footrace"]
    st = cfg.get("strategies") or {}
    on = [k for k, v in st.items() if isinstance(v, dict) and v.get("enabled")]
    bench = sorted(k for k in on if k in set(plan.get("rotation") or []) and k not in set(play))
    for k in bench:
        st[k]["enabled"] = False
    leaders = [k for k in plan.get("leaders") or [] if k in on]
    order = (cfg.get("live") or {}).get("setup_order")
    if isinstance(order, list) and leaders:
        cfg["live"]["setup_order"] = [k for k in order if k in leaders] + [k for k in order if k not in leaders]
    log["footrace"] = {"applied": True, "plan_asof": plan.get("asof"), "leaders": leaders, "benched": bench}
    return log["footrace"]


# ----------------------------------------------------------------------------------------------- data + CLI
def live_trades(remote: str = "origin") -> pd.DataFrame:
    """Closed live trades (run 1) of every account journal on the mcf-data* branches: account, strategy, symbol, date,
    r (LR8 basis), identical signals across accounts (setup|symbol|date|entry minute) counted once (first account)."""
    import sqlite3
    import subprocess
    import tempfile

    from ..config import load_config
    from ..costs import cost_r_lr8
    from ..research.shadow_calib import BRANCHES

    cfg, parts = load_config(), []
    for acct, br in BRANCHES.items():
        raw = subprocess.run(["git", "-C", str(ROOT), "show", f"{remote}/{br}:journal.db"], capture_output=True).stdout
        if not raw:
            continue
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            f.write(raw)
            f.flush()
            con = sqlite3.connect(f.name)
            x = pd.read_sql("SELECT strategy, symbol, date, entry_time, entry, stop, shares, pnl, pnl_adj, r_multiple "
                            "FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con)
            con.close()
        x["account"] = acct
        parts.append(x)
    t = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    if not len(t):
        return pd.DataFrame(columns=["account", "strategy", "symbol", "date", "r"])
    t["date"] = t["date"].astype(str).str[:10]
    t["r"] = cost_r_lr8(t, cfg).astype(float)
    t = t[t["r"].notna()]
    t["k"] = t["strategy"] + "|" + t["symbol"] + "|" + t["date"] + "|" + t["entry_time"].astype(str).str[:16]
    return t.drop_duplicates("k")[["account", "strategy", "symbol", "date", "r"]].reset_index(drop=True)


def _enabled(acct: str, asof) -> dict:
    from ..config import load_config

    old = os.environ.get("MCF_ACCOUNT")
    os.environ["MCF_ACCOUNT"] = acct
    try:
        return load_config(asof=asof)
    finally:
        if old is None:
            os.environ.pop("MCF_ACCOUNT", None)
        else:
            os.environ["MCF_ACCOUNT"] = old


def expected_load(g: pd.DataFrame, rp: dict) -> float:
    """Expected trades per session of one setup (for the slot line), the higher of its lifetime rate (trades / active
    days, arena_reps.json) and its recent rate (trades on its last 5 traded days / 5 x traded share of active days)."""
    days = float(rp.get("active_days") or 0)
    life = float(rp.get("trades") or 0) / days if days else 0.0
    if not len(g):
        return life
    last = sorted(g["date"].astype(str).unique())[-5:]
    share = min(1.0, float(rp.get("traded_days") or 0) / days) if days else 1.0
    return max(life, len(g[g["date"].astype(str).isin(last)]) / len(last) * share)


def build(trades: pd.DataFrame, reps: dict, asof: date, prev: dict | None = None) -> dict:
    whole = setup_stats(trades)
    sessions = next_sessions(asof, GY_HORIZON)
    gcfg = _enabled("graveyard", sessions[0])
    members = [k for k, v in (gcfg.get("strategies") or {}).items() if isinstance(v, dict) and v.get("enabled")]
    for d in sessions[1:]:     # union over the horizon (guest windows may end inside it)
        members += [k for k, v in (_enabled("graveyard", d).get("strategies") or {}).items()
                    if isinstance(v, dict) and v.get("enabled") and k not in members]
    load = {k: expected_load(trades[trades["strategy"] == k], reps.get(k) or {}) for k in members}
    rare = {k for k in members if float((reps.get(k) or {}).get("active_days") or 0) > 0
            and float(reps[k].get("signals") or 0) / float(reps[k]["active_days"]) < RARE_SIG_PER_DAY}
    slots = int((gcfg.get("account") or {}).get("slots") or 300)
    gy = gy_plan(members, whole, load, sessions, slots, rare, bench_runs(prev, asof.isoformat()))
    gy["asof"] = asof.isoformat()
    arena = {}
    for a in ARENA:
        for k, v in (_enabled(a, sessions[0]).get("strategies") or {}).items():
            if isinstance(v, dict) and v.get("enabled"):
                arena.setdefault(k, a)
    gt = setup_stats(trades[trades["account"] == "graveyard"])
    residents = [k for k, v in (gcfg.get("strategies") or {}).items() if isinstance(v, dict) and v.get("enabled")
                 and not v.get("guest")]
    return {"note": "FOOTRACE (owner 2026-11-19): GY foot race plan (read by the Graveyard trade run before the open), "
                    "FOOTRACE-EXIT watch list and GY-LIFE archive candidates for the Friday review. " + DISCLAIMER,
            "asof": asof.isoformat(), "gy": gy, "exit_review": exit_review(whole, arena, reps),
            "archive_review": archive_review(gt, whole, residents)}


def main(argv=None):
    ap = argparse.ArgumentParser(description="FOOTRACE: GY foot race plan + Friday exit / archive review")
    ap.add_argument("--asof", help="last completed session (default: today in New York)")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--reps", default=str(ROOT / "docs" / "live" / "arena_reps.json"))
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    from ..rotation import session_date

    asof = session_date(a.asof)
    reps = json.loads(Path(a.reps).read_text()).get("setups") or {}
    try:
        prev = json.loads(Path(a.out).read_text()).get("gy")
    except Exception:
        prev = None
    doc = build(live_trades(a.remote), reps, asof, prev)
    Path(a.out).write_text(json.dumps(doc, indent=1) + "\n")
    g = doc["gy"]
    print(f"GY foot race {asof}: {len(g['leaders'])} leaders, {len(g['always'])} always-on (low-rep / rare / new), "
          f"{len(g['rotation'])} rotating; " + "; ".join(f"{d}: {e['playing']} play, {e['benched']} benched, "
                                                         f"~{e['est_slot_pct']}% slots" for d, e in g["estimate"].items()))
    print(f"FOOTRACE-EXIT watch: {len(doc['exit_review'])}; GY-LIFE archive candidates: {len(doc['archive_review'])} -> {a.out}")
    print(DISCLAIMER)


if __name__ == "__main__":
    main()
