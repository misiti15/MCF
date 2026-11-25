"""REPS2 item 3: the low-rep fast lane - a daily list of current setups with 0-10 live trades (all accounts pooled), ranked
by shadow signals + research evidence, each with the fastest exposure route its own signal record points to.

    python research/reps2/fastlane.py            # -> research/reps2/fastlane/LIST.md + list.csv

CAVEAT SRCV1 (owner 2026-11-17, research/src_value/NOTES.md): no non-live source (2-year screen, 2-year backtest, Session
replay, Shadow) has predicted later live results (Spearman ~0). The evidence column only orders the queue for EXPOSURE;
it is never a verdict and never counts as reps. Live wins.

Columns
  live_trades / live_sessions   live record (closed trades, R after costs, all accounts)
  sig_per_session               live signals drawn per session in its current account(s) since its first session there
                                (entered + skipped), and where they went: entered / resource (slots, caps, max positions,
                                twin, halts) / quote_cost (spread, cost filter, size) / borrow (ETB) / other (latch, ...)
  shadow_trades / shadow_r      shadow trades (of_live twin, fill profile B, LR8 costs) - incl. the resource-blocked
                                ones live could not take; shadow R after the 0.02R haircut
  evidence_r                    mean of the available non-live numbers, each less its measured optimism (SRCV1):
                                2-year screen avg R - 0.157, 2-year backtest exp R - 0.064, replay snapshot avg R
                                (bias -0.03, not added back); None when there is none
  score                         (n_live x live avg R + n_sh x shadow R + 10 x evidence) / (n_live + n_sh + 10)
                                (evidence missing -> the live pool -0.13R as the prior); ties -> more signals first
Route (first that applies):
  spotlight          >= 30% of its signals lost to account resources  -> ROT spotlight (first in priority, per-setup cap)
  graveyard-filler   lives in the Graveyard and loses signals to resources -> Graveyard filler slots
  just-moved (wait)  < 2 sessions in its current account and no signal there yet
  check-wiring       0 signals although its 2-year screen expects >= 3 by now (P(0) < 5%) -> check universe / data / config
  full-universe      < 0.5 signals per session (rare trigger) -> shadow-only in a full-universe account (no slots used)
  fix-gate           >= 50% of its signals lost to quote/cost/borrow checks -> exposure will not help; gate review
  as-is              enough signals that enter: it gets reps where it is
Educational only - not financial advice."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import data as D  # noqa: E402

ROOT = D.ROOT
SCREEN_OPT, BT_OPT, SH_HAIRCUT, POOL, K0 = 0.157, 0.064, 0.02, -0.13, 10


def evidence() -> dict[str, dict]:
    out: dict[str, dict] = {}
    try:
        s = json.loads((ROOT / "docs" / "live" / "sim_inputs.json").read_text())["setups"]
        for k, v in s.items():
            if "backtest" in v and v["backtest"].get("avg_r") is not None:
                out.setdefault(k, {})["screen"] = float(v["backtest"]["avg_r"]) - SCREEN_OPT
                out[k]["screen_per_day"] = v["backtest"].get("per_day")
            if "replay" in v and v["replay"].get("avg_r") is not None:
                out.setdefault(k, {})["replay"] = float(v["replay"]["avg_r"])
    except (OSError, ValueError, KeyError):
        pass
    try:
        h = pd.read_csv(ROOT / "research" / "history2y" / "rescore.csv", usecols=["setup", "exp_r", "per_day"])
        for k, e, pdy in zip(h["setup"], h["exp_r"], h["per_day"]):
            if pd.notna(e):
                out.setdefault(str(k), {})["bt2y"] = float(e) - BT_OPT
                out[str(k)].setdefault("screen_per_day", pdy)
    except (OSError, ValueError):
        pass
    return out


def build(max_trades: int = 10) -> pd.DataFrame:
    a = D.assignments()
    cur: dict[str, list[str]] = {}
    for acct, names in a["accounts"].items():
        for n in names:
            cur.setdefault(n, []).append(acct)
    since = {k: (v.get("first_session") or "") for k, v in (a.get("setups") or {}).items()}
    x = D.load()
    live = x["live"].dropna(subset=["r"])
    sh = x["shadow"].dropna(subset=["r"])
    sig = D.live_signals()
    ev = evidence()
    lt = live.groupby("strategy")["r"].agg(["size", "sum"])
    ls = live.groupby("strategy")["date"].nunique()
    st = sh.groupby("strategy")["r"].agg(["size", "sum"])
    rows = []
    for k, accts in sorted(cur.items()):
        n = int(lt["size"].get(k, 0))
        if n > max_trades:
            continue
        s0 = since.get(k, "")
        g = sig[(sig["strategy"] == k) & sig["account"].isin(accts)]
        if s0:
            g = g[g["day"].astype(str) >= s0]
        # sessions the setup's account(s) ran since its first session there (any setup's signals that day = a session)
        acct_days = sig[sig["account"].isin(accts)]
        acct_days = acct_days[acct_days["day"].astype(str) >= s0] if s0 else acct_days
        sessions_there = int(acct_days["day"].nunique())
        sessions = max(1, sessions_there)
        cats = g.groupby("cat")["n"].sum().to_dict()
        tot = int(sum(cats.values()))
        e = ev.get(k, {})
        evs = [e[c] for c in ("screen", "bt2y", "replay") if c in e]
        evid = float(np.mean(evs)) if evs else None
        nsh = int(st["size"].get(k, 0))
        shr = (float(st["sum"].get(k, 0.0)) / nsh - SH_HAIRCUT) if nsh else None
        lr = float(lt["sum"].get(k, 0.0)) / n if n else None
        prior = evid if evid is not None else POOL
        score = ((n * lr if n else 0.0) + (nsh * shr if nsh else 0.0) + K0 * prior) / (n + nsh + K0)
        spp = tot / sessions
        res_share = cats.get("resource", 0) / tot if tot else 0.0
        gate_share = (cats.get("quote_cost", 0) + cats.get("borrow", 0)) / tot if tot else 0.0
        bpd = e.get("screen_per_day")
        expect = float(bpd) * sessions if bpd is not None and pd.notna(bpd) else None
        if sessions_there < 2 and tot == 0:
            route = "just-moved (wait)"
        elif tot == 0 and expect is not None and expect >= 3:
            route = "check-wiring"
        elif tot and res_share >= 0.30:
            route = "graveyard-filler" if accts == ["graveyard"] else "spotlight"
        elif spp < 0.5:
            route = "full-universe"
        elif gate_share >= 0.50:
            route = "fix-gate"
        else:
            route = "as-is"
        rows.append({"setup": k, "accounts": ",".join(accts), "since": s0 or None, "sessions_there": sessions_there,
                     "live_trades": n, "live_sessions": int(ls.get(k, 0)),
                     "live_avg_r": None if lr is None else round(lr, 3), "signals": tot,
                     "sig_per_session": round(spp, 2), "entered": cats.get("entered", 0),
                     "resource": cats.get("resource", 0), "quote_cost": cats.get("quote_cost", 0),
                     "borrow": cats.get("borrow", 0), "other": cats.get("other", 0) + cats.get("broker", 0),
                     "shadow_trades": nsh, "shadow_r": None if shr is None else round(shr, 3),
                     "evidence_r": None if evid is None else round(evid, 3),
                     "evidence_src": "+".join(c for c in ("screen", "bt2y", "replay") if c in e) or None,
                     "bt_per_day": e.get("screen_per_day"), "score": round(score, 4), "route": route})
    df = pd.DataFrame(rows)
    if len(df):
        df = df.sort_values(["score", "signals"], ascending=[False, False]).reset_index(drop=True)
        df.index += 1
    return df


def _f(v) -> str:
    return "–" if v is None or (isinstance(v, float) and np.isnan(v)) else str(v)


def write(df: pd.DataFrame, out: Path, asof: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "list.csv", index_label="rank")
    rc = df["route"].value_counts().to_dict() if len(df) else {}
    lines = [f"# Low-rep fast lane — {asof}", "",
             "*Educational only — not financial advice. Research list only: nothing here moves a setup. CAVEAT SRCV1: "
             "non-live sources (2-year screen, 2-year backtest, Session replay, Shadow) have not predicted later live "
             "results (Spearman ~0, research/src_value/NOTES.md); the evidence column only orders who gets exposure "
             "first. Live wins.*", "",
             f"{len(df)} current setups with 0-10 live trades (all accounts pooled). Routes: "
             + ", ".join(f"{k} {v}" for k, v in rc.items()) + ".", "",
             "| # | setup | account | live n | live avg R | sig/session | entered / resource / quote+cost / borrow | "
             "shadow n (R) | evidence R (src) | score | route |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in df.iterrows():
        lines.append(f"| {i} | {r.setup} | {r.accounts} | {r.live_trades} | {_f(r.live_avg_r)} | "
                     f"{r.sig_per_session} | {r.entered} / {r.resource} / {r.quote_cost} / {r.borrow} | "
                     f"{r.shadow_trades} ({_f(r.shadow_r)}) | {_f(r.evidence_r)} ({_f(r.evidence_src)}) | {r.score} | "
                     f"{r.route} |")
    (out / "LIST.md").write_text("\n".join(lines) + "\n\nEducational only — not financial advice.\n")
    write_lane(df, out, asof)


def write_lane(df, out: Path, asof: str) -> None:
    """REPS2-LANE (owner yes 2026-11-18): the 'full-universe' route (rare trigger) -> lane.json, which Testing A reads
    at session start as shadow-only setups (config shadow_setups_from; mcf/execution/shadow.py lane_setups)."""
    import json

    names = sorted(df.loc[df["route"] == "full-universe", "setup"].astype(str)) if len(df) else []
    rare = rare_setups()
    names = sorted(set(names) | set(rare))
    (out / "lane.json").write_text(json.dumps({
        "note": "REPS2-LANE shadow-only lane for Testing A (owner yes 2026-11-18): current setups with 0-10 live trades "
                "whose route is 'full-universe' (rare trigger, < 0.5 signals/session where they live). Re-picked nightly "
                "by research/reps2/fastlane.py, plus the ROT3 'rare' arena tags (research/rotation/rare_lane.json). Shadow reps are a separate column (SRCV1 weight 0), never live reps. "
                "Educational only - not financial advice.",
        "asof": asof, "account": "testing2", "route": "full-universe", "rare": rare, "rare_from": str(RARE.relative_to(HERE.parents[1])),
        "setups": names}, indent=1) + "\n")


RARE = HERE.parents[0] / "rotation" / "rare_lane.json"


def rare_setups() -> list[str]:
    """ROT3 rare lane (owner ROT3 yes 2026-11-25): arena setups tagged "rare" (< 0.5 signals per active day) at the last
    arena re-score (research/rotation/rare_lane.json) also get the shadow lane, whatever their live trade count. Missing
    or bad file -> none."""
    try:
        d = json.loads(RARE.read_text())
        return sorted(str(n) for n in (d.get("setups") or {}) if isinstance(n, str) and n)
    except Exception:
        return []


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=str(HERE / "fastlane"))
    p.add_argument("--max-trades", type=int, default=10)
    a = p.parse_args(argv)
    df = build(a.max_trades)
    asof = str(D.load()["live"]["date"].max())
    write(df, Path(a.out), asof)
    print(f"fast lane {asof}: {len(df)} setups; routes {df['route'].value_counts().to_dict() if len(df) else {}}")
    return df


if __name__ == "__main__":
    main()
