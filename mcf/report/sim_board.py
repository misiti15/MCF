"""Simulated leaderboard inputs (owner 2026-11-16, display only).

`python -m mcf.report.sim_board` writes docs/live/sim_inputs.json, read by the "Simulated leaderboard" card in
docs/live/index.html (right below the real setup leaderboard). It gathers the non-live evidence per setup:

  replay   - sessions replayed through the live runner (docs/live/replay.json today; a fresh all-setups replay run
             later: research/replay_all/latest.json, same per-setup shape, wins when present)
  backtest - the 2-year screen (Setup Generator run reports research/generator/runs/*.json -> picks[].screen.all;
             research/workbench/<setup>/sim_result.json when a workbench run writes one)

and the weights from config/effective_sessions.json (ONE source): live 1.0, replay per tier (0.35 calibrated, 0.2
until calibrated), 2-year history 0.175 (screening only). Replay/backtest avg R is haircut on the page by
(measured optimism + haircut_extra_r). The blend (also in `blend` below, which the tests pin):

  effective trades   = 1.0 x live trades + w_rp x replay trades + w_bt x backtest trades
  effective sessions = 1.0 x live sessions + w_rp x replay sessions + w_bt x backtest sessions
  blended avg R      = (live trades x live avg R + w_rp x replay trades x (replay avg R - haircut)
                        + w_bt x backtest trades x (backtest avg R - haircut)) / effective trades
  score              = blended avg R x eff. trades / (eff. trades + 20)  (same shrink as the real board)

Not live results - a what-if ranking. Educational only - not financial advice.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "live" / "sim_inputs.json"


def _load(p: Path):
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def weights(eff: dict | None) -> dict:
    """Replay / backtest weights and haircut from config/effective_sessions.json."""
    eff = eff or {}
    rp = eff.get("replay") or {}
    extra = float(eff.get("haircut_extra_r", 0.02))
    match, rp_extra, opt = rp.get("match"), rp.get("extra"), rp.get("optimism_r")
    w = eff.get("uncalibrated_weight", 0.2)
    if match is not None:
        w = eff.get("below_weight", 0.0)
        for t in sorted(eff.get("tiers") or [], key=lambda t: -t.get("min_match", 0)):
            ok = match >= t.get("min_match", 1)
            if ok and t.get("max_extra") is not None and (rp_extra is None or rp_extra > t["max_extra"]):
                ok = False
            if ok and t.get("no_optimism") and opt is not None and opt > eff.get("bias_tolerance_r", 0.01):
                ok = False
            if ok:
                w = t.get("weight", 0.0)
                break
    return {"live": float(eff.get("live_weight", 1.0)), "replay": float(w),
            "replay_tier": "uncalibrated" if match is None else "measured",
            "backtest": float(eff.get("history_weight", 0.175)),
            "haircut_r": round(max(0.0, float(opt or 0)) + extra, 4)}


def blend(live: dict | None, replay: dict | None, backtest: dict | None, w: dict) -> dict:
    """Blend live with haircut replay/backtest, weighted per trade (see module doc). Each source:
    {trades, sessions, avg_r}; missing/empty sources drop out."""
    parts = []
    for src, wt, hc in ((live, w["live"], 0.0), (replay, w["replay"], w["haircut_r"]), (backtest, w["backtest"], w["haircut_r"])):
        if src and src.get("trades") and src.get("avg_r") is not None and wt > 0:
            parts.append((wt * src["trades"], wt * (src.get("sessions") or 0), src["avg_r"] - hc))
    et = sum(p[0] for p in parts)
    es = sum(p[1] for p in parts)
    avg = sum(p[0] * p[2] for p in parts) / et if et else None
    return {"eff_trades": round(et, 2), "eff_sessions": round(es, 2),
            "avg_r": None if avg is None else round(avg, 4),
            "score": None if avg is None else round(avg * et / (et + 20), 4)}


def _rec(trades, sessions, avg_r, wo_best=None, **extra):
    r = {"trades": int(trades or 0), "sessions": int(sessions or 0), "avg_r": None if avg_r is None else round(float(avg_r), 4)}
    if wo_best is not None:
        r["wo_best"] = round(float(wo_best), 4)
    r.update({k: v for k, v in extra.items() if v is not None})
    return r


def build(root: Path = ROOT) -> dict:
    live = root / "docs" / "live"
    eff = _load(root / "config" / "effective_sessions.json")
    setups: dict[str, dict] = {}
    sources: dict[str, dict] = {}

    # replay: a future all-setups replay run (research/replay_all/latest.json) wins over the stale snapshot
    for path, label in ((root / "research" / "replay_all" / "latest.json", "all-setups replay"),
                        (live / "replay.json", "replay snapshot")):
        rp = _load(path)
        if rp and rp.get("setups"):
            win = str(rp.get("window") or "")
            frm, _, to = win.partition(" to ")
            sources["replay"] = {"file": str(path.relative_to(root)), "label": label, "from": frm or None, "to": to or None,
                                 "generated": rp.get("generated"), "setups": len(rp["setups"])}
            for sid, x in rp["setups"].items():
                setups.setdefault(sid, {})["replay"] = _rec(x.get("trades"), x.get("sessions"), x.get("avg_r"), x.get("wo_best"))
            break

    # backtest: the Setup Generator's 2-year screen (all = train + valid), one record per GEN setup
    dates, n_bt = [], 0
    for f in sorted((root / "research" / "generator" / "runs").glob("*.json")):
        d = _load(f) or {}
        for p in d.get("picks") or []:
            s = (p.get("screen") or {})
            a = s.get("all") or {}
            if p.get("name") and a.get("n"):
                setups.setdefault(p["name"], {})["backtest"] = _rec(
                    a["n"], a.get("days"), a.get("exp_r"), train_r=(s.get("train") or {}).get("exp_r"),
                    valid_r=(s.get("valid") or {}).get("exp_r"), per_day=s.get("per_day"))
                n_bt += 1
        if d.get("date"):
            dates.append(d["date"])
    # HOOK: research/workbench/<setup>/sim_result.json {setup, trades, sessions, avg_r, from, to} (2-year workbench run)
    wb = 0
    for f in sorted((root / "research" / "workbench").glob("*/sim_result.json")):
        x = _load(f) or {}
        sid = x.get("setup") or f.parent.name
        if x.get("trades"):
            setups.setdefault(sid, {})["backtest"] = _rec(x["trades"], x.get("sessions"), x.get("avg_r"), x.get("wo_best"),
                                                          source="workbench")
            wb += 1
    if n_bt or wb:
        sources["backtest"] = {"label": "2-year screen (Setup Generator runs" + (" + workbench" if wb else "") + ")",
                               "runs_from": min(dates) if dates else None, "runs_to": max(dates) if dates else None,
                               "history": "2-year open history (train + valid)", "setups": n_bt + wb}
    sources["weights"] = {"file": "config/effective_sessions.json", "owner_date": (eff or {}).get("owner_date"), **weights(eff)}
    return {"generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "sources": sources, "setups": setups,
            "note": "Inputs for the Simulated leaderboard: replay / backtest per setup; not live results - a what-if ranking. "
                    "Educational only - not financial advice."}


def main() -> None:
    d = build()
    OUT.write_text(json.dumps(d, indent=1, sort_keys=False) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(d['setups'])} setups, sources {', '.join(d['sources'])}")


if __name__ == "__main__":
    main()
