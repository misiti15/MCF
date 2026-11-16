"""Shadow trust check (owner 2026-11-16): shadow-of-live vs the real live trades of the same setups, per day.

Every live setup also runs in shadow (mcf/execution/shadow.py, mode of_live). Per (day, setup):
  live entries      live signals submitted (run kind 'paper'), decision bar = info.bar_time
  shadow entries    shadow signals entered with mode of_live
  matched           same setup, symbol, side and decision bar +-1 minute (as research/replay/validate.py matches)
  missing           live entries shadow did not take
  resource_blocked  shadow entries whose live twin was skipped for an ACCOUNT reason (slots, caps, twin, max positions,
                    halts, broker rejects) - expected, shadow ignores the account's resources; never counted as extra
  extra             the other unmatched shadow entries
  R bias            per matched pair with both trades closed: shadow R - live R (both after costs, LR8); summed exactly
                    (n, sum, sum of squares) so any window aggregates without the raw rows
  daily R           live total R vs shadow R of the comparable entries (matched + extra) per setup-day: correlation
Targets (same as replay; numbers in config/effective_sessions.json): >= 98% match, <= 2% extra, |bias| <= 0.01R and
never optimistic (one-sided), measured on held-out days (days after calibration_fit_until; all days while nothing is
fitted). The tier per setup family (name prefix before the first '-') sets its shadow session weight.

  python -m mcf.research.shadow_calib --journal state/journal.db --out research/shadow     # one account
  python -m mcf.research.shadow_calib --branches --out research/shadow                     # every account (nightly)
Writes calibration.csv (per day x account x setup), summary.json and SUMMARY.md. Educational only - not financial advice."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sqlite3
import subprocess
import tempfile
from pathlib import Path

import pandas as pd

from . import effective as E

ROOT = Path(__file__).resolve().parents[2]
RESOURCE = ("halted", "daily loss limit", "max trades/day", "max concurrent positions", "max positions for this setup",
            "twin held", "already in symbol", "opposite side held", "lot cap", "position mismatch")
BRANCHES = {"primary": "mcf-data", "testing": "mcf-data-testing", "testing2": "mcf-data-testing2", "gen": "mcf-data-gen",
            "graveyard": "mcf-data-graveyard", "livelab": "mcf-data-livelab", "explore1": "mcf-data-explore1",
            "testingd": "mcf-data-testingd", "testinge": "mcf-data-testinge", "testingf": "mcf-data-testingf"}
COLS = ["day", "account", "setup", "family", "live_entries", "shadow_entries", "matched", "missing", "extra",
        "resource_blocked", "r_n", "r_sum", "r_sq", "live_r", "shadow_r"]


def family_of(setup: str) -> str:
    s = str(setup or "")
    if "-" in s:
        return s.split("-", 1)[0]
    return re.sub(r"_[a-z]$", "", s)


def _info(x) -> dict:
    try:
        v = json.loads(x) if x else {}
        return v if isinstance(v, dict) else {}
    except (TypeError, ValueError):
        return {}


def _minute(info: dict, ts) -> int | None:
    bt = str(info.get("bar_time") or "")
    if re.fullmatch(r"\d{4}", bt):
        return int(bt[:2]) * 60 + int(bt[2:])
    try:
        t = pd.Timestamp(ts)
        t = t.tz_convert("America/New_York") if t.tzinfo else t
        return t.hour * 60 + t.minute - 1          # no bar_time: the decision bar is the minute before the poll
    except (TypeError, ValueError):
        return None


def _lot_r(tr: pd.DataFrame) -> dict[str, float]:
    """Order id -> R after costs of the whole lot (sum pnl_adj / (|entry - stop| x shares))."""
    if tr is None or not len(tr) or "broker_order_id" not in tr:
        return {}
    t = tr.dropna(subset=["broker_order_id"]).copy()
    if not len(t):
        return {}
    adj = pd.to_numeric(t.get("pnl_adj"), errors="coerce") if "pnl_adj" in t else pd.Series(float("nan"), index=t.index)
    t["_adj"] = adj.fillna(pd.to_numeric(t["pnl"], errors="coerce"))
    t["_risk"] = (pd.to_numeric(t["entry"], errors="coerce") - pd.to_numeric(t["stop"], errors="coerce")).abs() \
        * pd.to_numeric(t["shares"], errors="coerce").abs()
    out = {}
    for oid, g in t.groupby(t["broker_order_id"].astype(str)):
        e, s = float(g["entry"].iloc[0]), float(g["stop"].iloc[0])
        risk = abs(e - s) * float(pd.to_numeric(g["shares"], errors="coerce").sum())
        if risk > 0:
            out[oid] = float(g["_adj"].sum()) / risk
    return out


def _match(a: list[dict], b: list[dict], tol: int = 1) -> list[tuple[int, int]]:
    """Greedy one-to-one match of entries on (setup, symbol, side) and decision minute within tol."""
    used, pairs = set(), []
    idx: dict = {}
    for j, y in enumerate(b):
        idx.setdefault((y["setup"], y["symbol"], y["side"]), []).append(j)
    for i, x in enumerate(a):
        best = None
        for j in idx.get((x["setup"], x["symbol"], x["side"]), []):
            if j in used or x["min"] is None or b[j]["min"] is None:
                continue
            d = abs(x["min"] - b[j]["min"])
            if d <= tol and (best is None or d < best[0]):
                best = (d, j)
        if best is not None:
            used.add(best[1])
            pairs.append((i, best[1]))
    return pairs


def day_rows(live_sig: pd.DataFrame, live_tr: pd.DataFrame, sh_sig: pd.DataFrame, sh_tr: pd.DataFrame, day: str,
             account: str = "") -> list[dict]:
    """Per-setup trust-check counts for one account and day (empty when shadow-of-live did not run that day)."""
    ls = live_sig[live_sig["day"].astype(str) == day] if len(live_sig) else live_sig
    ss = sh_sig[sh_sig["day"].astype(str) == day] if len(sh_sig) else sh_sig
    if not len(ss):
        return []
    sinfo = [_info(x) for x in ss["info"]]
    ss = ss.assign(xmode=[i.get("mode", "of_live") for i in sinfo], xinfo=sinfo)
    ss = ss[ss["xmode"] == "of_live"]
    setups = set(ss["strategy"].astype(str))
    if not setups:
        return []
    linfo = [_info(x) for x in ls["info"]] if len(ls) else []
    ls = ls.assign(xinfo=linfo) if len(ls) else ls

    def ent(df, status):
        if not len(df):
            return []
        d = df[df["status"].isin(status) & df["strategy"].astype(str).isin(setups)]
        return [{"setup": str(r.strategy), "symbol": str(r.symbol), "side": int(r.side), "min": _minute(r.xinfo, r.ts),
                 "oid": None if pd.isna(r.broker_order_id) else str(r.broker_order_id)}
                for r in d.itertuples()]

    live_e = ent(ls, ["submitted", "dry_run"])
    sh_e = ent(ss, ["shadow_entered"])
    blocked = []
    if len(ls):
        rb = ls[(ls["status"] == "rejected") | ((ls["status"] == "skipped") & ls["reason"].astype(str).isin(RESOURCE))]
        blocked = ent(rb, list(set(rb["status"])))
    pairs = _match(live_e, sh_e)
    m_live = {i for i, _ in pairs}
    m_sh = {j for _, j in pairs}
    rest = [sh_e[j] for j in range(len(sh_e)) if j not in m_sh]
    rb_pairs = _match(rest, blocked)
    rb_idx = {i for i, _ in rb_pairs}
    lr, sr = _lot_r(live_tr), _lot_r(sh_tr)
    out = {s: dict(day=day, account=account, setup=s, family=family_of(s), live_entries=0, shadow_entries=0,
                   matched=0, missing=0, extra=0, resource_blocked=0, r_n=0, r_sum=0.0, r_sq=0.0, live_r=0.0,
                   shadow_r=0.0) for s in setups}
    for i, x in enumerate(live_e):
        o = out[x["setup"]]
        o["live_entries"] += 1
        if i not in m_live:
            o["missing"] += 1
        if x["oid"] in lr:
            o["live_r"] += lr[x["oid"]]
    for j, y in enumerate(sh_e):
        out[y["setup"]]["shadow_entries"] += 1
    for k, y in enumerate(rest):
        o = out[y["setup"]]
        if k in rb_idx:
            o["resource_blocked"] += 1
        else:
            o["extra"] += 1
            o["shadow_r"] += sr.get(y["oid"], 0.0)
    for i, j in pairs:
        x, y = live_e[i], sh_e[j]
        o = out[x["setup"]]
        o["matched"] += 1
        o["shadow_r"] += sr.get(y["oid"], 0.0)
        if x["oid"] in lr and y["oid"] in sr:
            d = sr[y["oid"]] - lr[x["oid"]]
            o["r_n"] += 1
            o["r_sum"] += d
            o["r_sq"] += d * d
    return [out[s] for s in sorted(out)]


def journal_rows(con: sqlite3.Connection, account: str = "", days: list[str] | None = None) -> list[dict]:
    """Trust-check rows of every day with shadow-of-live data in one account journal (sqlite connection)."""
    runs = pd.read_sql("SELECT id, kind FROM runs", con)
    live = runs.loc[runs.kind == "paper", "id"].tolist()
    sh = runs.loc[runs.kind == "shadow", "id"].tolist()
    if not live or not sh:
        return []
    lid, sid = int(min(live)), int(min(sh))
    q = "SELECT * FROM signals WHERE run_id=?"
    ls, ss = pd.read_sql(q, con, params=[lid]), pd.read_sql(q, con, params=[sid])
    tq = "SELECT * FROM trades WHERE run_id=? AND exit_time IS NOT NULL"
    lt, st = pd.read_sql(tq, con, params=[lid]), pd.read_sql(tq, con, params=[sid])
    out = []
    for d in sorted(set(ss["day"].astype(str))) if len(ss) else []:
        if days and d not in days:
            continue
        out += day_rows(ls, lt[lt["date"].astype(str) == d] if len(lt) else lt,
                        ss, st[st["date"].astype(str) == d] if len(st) else st, d, account)
    return out


def _agg(df: pd.DataFrame) -> dict:
    live, sh = int(df["live_entries"].sum()), int(df["shadow_entries"].sum())
    comp = sh - int(df["resource_blocked"].sum())
    n = int(df["r_n"].sum())
    bias = float(df["r_sum"].sum()) / n if n else None
    t = None
    if n > 1:
        var = (float(df["r_sq"].sum()) - n * bias * bias) / (n - 1)
        t = bias / math.sqrt(var / n) if var > 1e-12 else (0.0 if abs(bias) < 1e-12 else math.copysign(99.0, bias))
    cells = df[(df["live_entries"] > 0) | (df["shadow_entries"] > 0)]
    corr = None
    if len(cells) >= 3 and cells["live_r"].std() > 0 and cells["shadow_r"].std() > 0:
        corr = float(cells["live_r"].corr(cells["shadow_r"]))
    return {"days": int(df["day"].nunique()), "live_entries": live, "shadow_entries": sh,
            "matched": int(df["matched"].sum()), "missing": int(df["missing"].sum()), "extra": int(df["extra"].sum()),
            "resource_blocked": int(df["resource_blocked"].sum()),
            "match": round(int(df["matched"].sum()) / live, 4) if live else None,
            "extra_rate": round(int(df["extra"].sum()) / comp, 4) if comp > 0 else None,
            "r_pairs": n, "bias_r": None if bias is None else round(bias, 4),
            "bias_t": None if t is None else round(t, 2), "daily_r_corr": None if corr is None else round(corr, 3)}


def fill_advice(o: dict | None, profile: str = "B", min_pairs: int = 30, min_days: int = 3) -> dict:
    """Owner "fills B" 2026-11-16: shadow should come out SLIGHTLY below live. Advice only - the profile is changed by the
    owner, never automatically. bias = mean (shadow - live) R per matched trade."""
    b, n, d = (o or {}).get("bias_r"), (o or {}).get("r_pairs", 0), (o or {}).get("days", 0)
    if b is None or n < min_pairs or d < min_days:
        return {"profile": profile, "verdict": "not enough matched trades yet", "advice": f"keep {profile}"}
    if b > 0:
        return {"profile": profile, "verdict": f"shadow ABOVE live by {b:+.3f}R (optimistic)",
                "advice": "tighten to C: through max(3c, 0.05%), entry 2.5x median slip (min 2c), stop +0.05% (owner decides)"}
    if b < -0.04:
        return {"profile": profile, "verdict": f"shadow below live by {b:+.3f}R (harsher than needed)",
                "advice": "ease to A: through max(2c, 0.02%), entry 1.75x median slip, stop +0.02% (owner decides)"}
    return {"profile": profile, "verdict": f"shadow slightly below live ({b:+.3f}R) - as desired", "advice": f"keep {profile}"}


def summarize(rows: pd.DataFrame | list, cfg: dict | None = None) -> dict:
    """Held-out trust-check verdicts: overall, per family (tier + weight) and per setup (gap = bias)."""
    c = cfg or E.load()
    df = pd.DataFrame(rows, columns=COLS) if isinstance(rows, list) else rows.copy()
    fit = c.get("calibration_fit_until")
    held = df[df["day"].astype(str) > str(fit)] if fit else df
    out = {"held_out_from": None if not fit else f"after {fit}", "targets": {
        "match": c["tiers"][0]["min_match"], "extra": c["tiers"][0]["max_extra"], "bias_r": c["bias_tolerance_r"]},
        "overall": _agg(held) if len(held) else None, "families": {}, "setups": {}}
    out["fills"] = fill_advice(out["overall"])
    for fam, g in held.groupby("family") if len(held) else []:
        a = _agg(g)
        a["optimistic"] = E.optimism(a["bias_r"], a["bias_t"], c)
        a["tier"], a["weight"] = E.tier(a["match"], a["extra_rate"], a["bias_r"], a["bias_t"], a["days"],
                                        a["live_entries"], c)
        a["haircut_r"] = E.haircut(a["bias_r"], c)
        out["families"][str(fam)] = a
    for s, g in held.groupby("setup") if len(held) else []:
        a = _agg(g)
        out["setups"][str(s)] = {"family": family_of(s), "days": a["days"], "match": a["match"],
                                 "extra_rate": a["extra_rate"], "gap_r": a["bias_r"], "gap_n": a["r_pairs"],
                                 "live_entries": a["live_entries"], "shadow_entries": a["shadow_entries"]}
    return out


def family_weight(summary: dict | None, setup: str, cfg: dict | None = None) -> tuple[str, float, float]:
    """(tier, weight, haircut R) for a setup's shadow sessions: its family's verdict, else the lower tier."""
    c = cfg or E.load()
    f = ((summary or {}).get("families") or {}).get(family_of(setup))
    if not f:
        return "uncalibrated", float(c["uncalibrated_weight"]), E.haircut(None, c)
    return f["tier"], float(f["weight"]), float(f["haircut_r"])


def write(rows: list[dict], out_dir: str | Path, cfg: dict | None = None) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows, columns=COLS).sort_values(["day", "account", "setup"]) if rows else pd.DataFrame(columns=COLS)
    df.to_csv(out / "calibration.csv", index=False, float_format="%.5f")
    s = summarize(df, cfg)
    s["generated"] = pd.Timestamp.now(tz="America/New_York").isoformat(timespec="minutes")
    (out / "summary.json").write_text(json.dumps(s, indent=1))
    o = s["overall"] or {}
    lines = ["# Shadow trust check (shadow-of-live vs live)", "",
             "*Educational only - not financial advice. Shadow is not live trading; live wins any disagreement.*", "",
             f"Generated {s['generated']}. Held-out days: {o.get('days', 0)}. Targets: match >= 98%, extra <= 2%, "
             "|R bias| <= 0.01R and never optimistic.", "",
             f"Overall: {o.get('live_entries', 0)} live entries, {o.get('shadow_entries', 0)} shadow entries, "
             f"match {_pc(o.get('match'))}, extra {_pc(o.get('extra_rate'))}, "
             f"{o.get('resource_blocked', 0)} blocked live by account resources (not extra), "
             f"R bias {o.get('bias_r')} (t {o.get('bias_t')}, {o.get('r_pairs', 0)} pairs), "
             f"daily R corr {o.get('daily_r_corr')}.", "",
             f"Fill profile {s['fills']['profile']}: {s['fills']['verdict']} -> {s['fills']['advice']}.", "",
             "| family | days | live | shadow | match | extra | bias R | t | corr | tier | weight | haircut R |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, a in sorted(s["families"].items()):
        lines.append(f"| {k} | {a['days']} | {a['live_entries']} | {a['shadow_entries']} | {_pc(a['match'])} | "
                     f"{_pc(a['extra_rate'])} | {a['bias_r']} | {a['bias_t']} | {a['daily_r_corr']} | {a['tier']} | "
                     f"{a['weight']} | {a['haircut_r']} |")
    (out / "SUMMARY.md").write_text("\n".join(lines) + "\n")
    return s


def _pc(v) -> str:
    return "–" if v is None else f"{v * 100:.1f}%"


def branch_rows(branches: dict[str, str] | None = None) -> list[dict]:
    rows = []
    for acct, br in (branches or BRANCHES).items():
        try:
            raw = subprocess.run(["git", "-C", str(ROOT), "show", f"origin/{br}:journal.db"], capture_output=True,
                                 check=True).stdout
        except Exception:
            continue
        f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        try:
            f.write(raw)
            f.close()
            con = sqlite3.connect(f.name)
            try:
                rows += journal_rows(con, acct)
            finally:
                con.close()
        finally:
            os.unlink(f.name)
    return rows


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--journal", help="one account journal.db")
    p.add_argument("--account", default="")
    p.add_argument("--branches", action="store_true", help="every account journal from its data branch (git fetch first)")
    p.add_argument("--out", default=str(ROOT / "research" / "shadow"))
    a = p.parse_args(argv)
    if a.branches:
        rows = branch_rows()
    elif a.journal:
        con = sqlite3.connect(a.journal)
        rows = journal_rows(con, a.account)
        con.close()
    else:
        p.error("--journal or --branches")
    s = write(rows, a.out)
    o = s["overall"] or {}
    print(f"shadow trust check: {len(rows)} setup-days, match {_pc(o.get('match'))}, extra {_pc(o.get('extra_rate'))}, "
          f"bias {o.get('bias_r')}R -> {a.out}")


if __name__ == "__main__":
    main()
