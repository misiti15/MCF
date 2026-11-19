"""REPS2 nightly re-score (owner REPS2 2026-11-17; USAGE1 3f: one scripted shadow / replay scorer). Scripts only, one
inbox-ready block. Run after the close, once the data branches have the session (git fetch first):

    git fetch origin mcf-data mcf-data-testing mcf-data-testing2 ... (every mcf-data* branch)
    python research/reps2/nightly.py [--replay] [--day YYYY-MM-DD]

Steps
  1. SHADOW SCORE   mcf.research.shadow_calib over every account journal -> research/reps2/shadow/ (match, extra, R bias
                    per family, tier from config/effective_sessions.json) + the earliest session each family can reach a
                    tier (>= calibration_min_days held-out days and >= calibration_min_live_entries live entries).
  2. REPLAY + REAL QUOTES (--replay; ~1 h, 3 accounts): the calibrated replay (research/replay_cal/params_v2.json, frozen)
                    of the day with the recorded quotes and with the modelled ones, each scored with
                    research/replay_cal/score.py -> research/reps2/replay_quotes/<day>/; rolling numbers over every
                    recorded-quote session in research/reps2/replay_quotes/rolling.json.
  3. FAST LANE      research/reps2/fastlane.py -> research/reps2/fastlane/
  4. EARLY DECISIONS research/reps2/sprt.py --verdicts-only -> research/reps2/sprt/
Writes research/reps2/nightly/<day>.md (the block) and appends research/reps2/nightly/history.jsonl. Alerts (in the
block) when the rolling numbers miss the targets. Research only: never edits config, setups or accounts.
Educational only - not financial advice."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
from mcf.research import effective as E          # noqa: E402
from mcf.research import shadow_calib as SC      # noqa: E402

ACCOUNTS = ["primary", "testing", "testing2"]
PARAMS = ROOT / "research" / "replay_cal" / "params_v2.json"


def shadow_step(out: Path) -> dict:
    rows = SC.branch_rows()
    s = SC.write(rows, out)
    c = E.load()
    df = pd.DataFrame(rows, columns=SC.COLS)
    days = sorted(df["day"].astype(str).unique())
    need_d, need_n = int(c["calibration_min_days"]), int(c["calibration_min_live_entries"])
    proj = {}
    for fam, a in s["families"].items():
        g = df[df["family"] == fam]
        per_day = a["live_entries"] / max(1, a["days"])
        more_days = max(0, need_d - a["days"])
        more_n = 0 if a["live_entries"] >= need_n else (None if per_day == 0 else
                                                        int(-(-(need_n - a["live_entries"]) // per_day)))
        wait = None if more_n is None else max(more_days, more_n)
        fidelity_ok = (a["match"] or 0) >= c["tiers"][0]["min_match"] and (a["extra_rate"] or 0) <= \
            c["tiers"][0]["max_extra"] and not a["optimistic"]
        proj[fam] = {"days": a["days"], "live_entries": a["live_entries"], "match": a["match"],
                     "extra": a["extra_rate"], "bias_r": a["bias_r"], "tier_now": a["tier"],
                     "sessions_to_eligible": wait, "on_track_for": "calibrated" if fidelity_ok else
                     ("partial" if (a["match"] or 0) >= c["tiers"][1]["min_match"] else "below")}
        del g
    s["projection"] = proj
    s["days_scored"] = days
    (out / "projection.json").write_text(json.dumps(proj, indent=1))
    return s


def _run(cmd: list[str], log: Path) -> int:
    with open(log, "a") as f:
        return subprocess.run(cmd, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT).returncode


def replay_step(day: str, out_root: Path, runs: Path) -> dict:
    """Calibrated replay of `day` with recorded vs modelled quotes, each scored like the held-out."""
    from mcf.replay import store
    if not store.pull_packs([pd.Timestamp(day).date()], daily=True, log=lambda m: None):
        return {"skipped": f"no session pack for {day} yet (store-bars workflow ~16:40 ET); re-run later with --replay"}
    out = out_root / day
    out.mkdir(parents=True, exist_ok=True)
    modelled = runs / "params_v2_modelled.json"
    runs.mkdir(parents=True, exist_ok=True)
    p = json.loads(PARAMS.read_text())
    p["recorded_quotes"] = False
    modelled.write_text(json.dumps(p))
    log = out / "run.log"
    live_dir = runs / "live"
    live_dir.mkdir(parents=True, exist_ok=True)
    for br in ("mcf-data", "mcf-data-testing", "mcf-data-testing2"):
        (live_dir / f"{br}.db").write_bytes(subprocess.run(["git", "-C", str(ROOT), "show", f"origin/{br}:journal.db"],
                                                           capture_output=True, check=True).stdout)
    res = {}
    for tag, params in (("recorded", PARAMS), ("modelled", modelled)):
        rd = runs / tag
        for acct in ACCOUNTS:
            _run([sys.executable, "-m", "mcf.replay", "run", "--account", acct, "--dates", day, "--as-live",
                  "--universe", "live", "--live-cal", str(params), "--jobs", "1", "--out", str(rd)], log)
        _run([sys.executable, str(ROOT / "research" / "replay_cal" / "score.py"), "--run", str(rd), "--dates", f"{day}..{day}",
              "--accounts", ",".join(ACCOUNTS), "--live-dir", str(live_dir), "--out", str(out / tag)], log)
        f = out / tag / "scorecard.json"
        res[tag] = json.loads(f.read_text()).get("pooled") if f.exists() else None
        q = {}
        for acct in ACCOUNTS:
            st = rd / acct / day / "stats.json"
            if st.exists():
                lc = (json.loads(st.read_text()).get("live_cal") or {})
                q[acct] = {k: lc.get(k) for k in ("quotes_real", "quotes_modelled")}
        res[f"{tag}_quote_sources"] = q
    (out / "result.json").write_text(json.dumps(res, indent=1, default=str))
    return res


def rolling(out_root: Path) -> dict:
    """Pooled numbers over every scored recorded-quote session (trade-weighted from each day's per-account files)."""
    tot = {"recorded": [], "modelled": []}
    for d in sorted(p for p in out_root.iterdir() if p.is_dir()):
        for tag in tot:
            f = d / tag / "per_account.csv"
            if f.exists():
                x = pd.read_csv(f)
                x = x[x["account"] != "pooled"]
                x["day"] = d.name
                tot[tag].append(x)
    out = {}
    for tag, xs in tot.items():
        if not xs:
            continue
        x = pd.concat(xs)
        n = float(x["live_trades"].sum())
        ext = float((x["replay_trades"] - x["matched"]).sum())
        out[tag] = {"sessions": int(x["day"].nunique()), "live_trades": int(n),
                    "match": round(float(x["matched"].sum()) / n, 4) if n else None,
                    "extra": round(ext / n, 4) if n else None}
    (out_root / "rolling.json").write_text(json.dumps(out, indent=1))
    return out


def block(day: str, sh: dict, rq: dict | None, roll: dict | None, fl: pd.DataFrame, sp: dict) -> str:
    o = sh.get("overall") or {}
    pc = lambda v: "–" if v is None else f"{v * 100:.1f}%"  # noqa: E731
    near = sorted(((k, v) for k, v in sh["projection"].items() if v["sessions_to_eligible"] is not None),
                  key=lambda kv: (kv[1]["sessions_to_eligible"], -kv[1]["live_entries"]))
    calib = [k for k, v in near if v["on_track_for"] == "calibrated"]
    lines = [f"## REPS2 nightly re-score — {day} (research/reps2/nightly.py)", "",
             f"- FYI | Shadow vs live ({len(sh['days_scored'])} held-out days): match {pc(o.get('match'))}, extra "
             f"{pc(o.get('extra_rate'))} ({o.get('resource_blocked', 0)} resource-blocked, not extra), R bias "
             f"{o.get('bias_r')}R (t {o.get('bias_t')}; shadow below live = conservative), daily R corr "
             f"{o.get('daily_r_corr')}. Families on track for the 0.35 tier: {len(calib)} of {len(near)}; tier earned "
             f"after >= 3 days and >= 30 live entries per family (config). SRCV1: blend weight stays 0 until "
             "research/src_value/score.py measures it (monthly).",
             ]
    if rq and rq.get("skipped"):
        lines.append(f"- FYI | Replay re-score skipped: {rq['skipped']}.")
    elif rq:
        r, m = rq.get("recorded") or {}, rq.get("modelled") or {}
        lines.append(f"- FYI | Replay {day}, real vs modelled quotes: match {pc(r.get('match'))} vs {pc(m.get('match'))}, "
                     f"extra {pc(r.get('extra'))} vs {pc(m.get('extra'))}, bias {r.get('bias'):+.3f} vs {m.get('bias'):+.3f}R."
                     + (f" Rolling real-quote ({roll['recorded']['sessions']} sessions): match "
                        f"{pc(roll['recorded']['match'])}, extra {pc(roll['recorded']['extra'])}."
                        if roll and roll.get("recorded") else ""))
        if r.get("match") is not None and (r["match"] < 0.98 or (r.get("extra") or 0) > 0.02):
            lines.append("- ALERT | replay below the 98% / 2% targets with real quotes (anti-rose-colored-glasses rule 2);"
                         " replay weight stays 0.")
    rc = fl["route"].value_counts().to_dict() if len(fl) else {}
    top = ", ".join(f"{r.setup} ({r.accounts}, {r.live_trades} live, {r.route})" for r in fl.head(5).itertuples())
    lines.append(f"- FYI | Low-rep fast lane: {len(fl)} current setups with 0-10 live trades; routes {rc}. Top 5: {top}. "
                 "Caveat SRCV1: evidence orders exposure only.")
    v = sp.get("configs", {}).get("d=0.20", {}).get("verdicts_current", {})
    lines.append(f"- FYI | Early decisions (SPRT, research/reps2/PREREG_SPRT.md; v1 NOT fit for decisions, bootstrap "
                 f"false-FAIL 10.4%): current setups {v}.")
    return "\n".join(lines) + "\n\nEducational only — not financial advice.\n"


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--day")
    p.add_argument("--replay", action="store_true", help="also run the replay re-score (~1 h)")
    p.add_argument("--runs", default=str(ROOT / "data" / "replay" / "runs" / "reps2"))
    a = p.parse_args(argv)
    sh = shadow_step(HERE / "shadow")
    day = a.day or sh["days_scored"][-1]
    rq = roll = None
    if a.replay:
        rq = replay_step(day, HERE / "replay_quotes", Path(a.runs) / day)
        roll = rolling(HERE / "replay_quotes")
    import fastlane
    import sprt
    fl = fastlane.build()
    fastlane.write(fl, HERE / "fastlane", day)
    sp = sprt.main(["--verdicts-only"])
    txt = block(day, sh, rq, roll, fl, sp)
    nd = HERE / "nightly"
    nd.mkdir(exist_ok=True)
    (nd / f"{day}.md").write_text(txt)
    with open(nd / "history.jsonl", "a") as f:
        f.write(json.dumps({"day": day, "shadow": sh.get("overall"), "replay": rq, "rolling": roll,
                            "fastlane": len(fl), "sprt": sp.get("configs", {}).get("d=0.20", {}).get("verdicts_current")},
                           default=str) + "\n")
    print(txt)


if __name__ == "__main__":
    main()
