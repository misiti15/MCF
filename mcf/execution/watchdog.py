"""Independent outage watchdog (owner 2026-10-16, outage plan step 5). Runs from .github/workflows/watchdog.yml every
~10 minutes during the session, per account, in its own job (never inside the trading run it watches).

It reads the account's state-branch status.json (asof, phase, health.data_stale) and the broker account (GET only) and
decides:
  * run_dead   - status.json is older than live.outage.watchdog_dead_min (or missing) during the session while MCF
                 positions or MCF orders are open: the trading run is not managing them
  * data_stale - the run reports health.data_stale for longer than live.outage.flatten_min (the run should already have
                 flattened itself; this is the backstop)
  flatten_failed - (LR7, owner 2026-11-11) the run reports health.flatten_failed (symbols its closing flatten could not
                 close) while MCF positions are still held
  after_flatten  - (LR7) MCF positions or orders still open from 3 minutes after the flatten time (calendar-aware: 15:55,
                 12:55 on a 13:00 half day) until the calendar close + 5 min
Any one -> cancel this account's open MCF orders and flatten its MCF positions through the same broker code as the
runner's flatten (prefix mcf- / mct- / mt2- / mcg- / mgy- / mll- / mx1- / mtd- / mte- / mtf- only; the long-hold mcl- book and anything else are never touched).

mode "dry" (the default) only logs what it would do; "act" does it (watchdog.yml: Primary runs in act from 2026-11-12,
LR7). Window: 09:35 ET to the calendar close + 5 min (LR1: 13:05 on a half day). No emails or alerts. Educational only -
not financial advice."""

from __future__ import annotations

import argparse
import json
import os
from datetime import time

import pandas as pd

from .outage import MCF_PREFIXES, check_prefix, flatten_prefix, mcf_symbols_today, open_order_count, outage_cfg

NY = "America/New_York"
SESSION = (time(9, 35), time(16, 5))      # LR7: until the calendar close + 5 min (16:05; 13:05 on a 13:00 half day)
AFTER_FLATTEN_GRACE_MIN = 3               # the run's own closing flatten gets 3 min before the watchdog steps in


def decide(status: dict | None, now: pd.Timestamp, mcf_positions: list[str], open_orders: int, live: dict,
           close: time = time(16, 0), flatten_at: time = time(15, 55)) -> dict:
    """Pure decision. now is tz-aware; mcf_positions = symbols MCF traded today that the account still holds.
    close / flatten_at: today's calendar close and the run's flatten time (LR1)."""
    from .market_calendar import plus

    o = outage_cfg(live)
    now = now.tz_convert(NY)
    end = plus(close, 5)
    out = {"at": str(now), "action": "none", "reasons": [], "mcf_positions": sorted(mcf_positions),
           "open_mcf_orders": int(open_orders), "status_asof": None, "status_age_min": None, "phase": None,
           "data_stale_min": None, "thresholds": {"dead_min": o["watchdog_dead_min"], "flatten_min": o["flatten_min"]},
           "close": f"{close:%H:%M}", "flatten_at": f"{flatten_at:%H:%M}"}
    if now.weekday() >= 5 or not (SESSION[0] <= now.time() < end):
        out["note"] = f"outside {SESSION[0]:%H:%M}-{end:%H:%M} ET weekdays"
        return out
    if not o["enabled"]:
        out["note"] = "live.outage.enabled is false"
        return out
    exposed = bool(mcf_positions) or open_orders > 0
    asof = None
    if status:
        try:
            asof = pd.Timestamp(status.get("asof"))
            asof = asof.tz_localize("UTC") if asof.tzinfo is None else asof
        except (TypeError, ValueError):
            asof = None
        out["phase"] = status.get("phase")
    if asof is not None:
        out["status_asof"] = str(asof.tz_convert(NY))
        out["status_age_min"] = round((now - asof).total_seconds() / 60, 1)
    dead = asof is None or out["status_age_min"] > o["watchdog_dead_min"]
    if dead and exposed:
        out["reasons"].append(f"run_dead: status.json {'missing' if asof is None else str(out['status_age_min']) + ' min old'}"
                              f" (> {o['watchdog_dead_min']:g}) with MCF exposure")
    ds = ((status or {}).get("health") or {}).get("data_stale") if not dead else None
    if ds and ds.get("since"):
        try:
            since = pd.Timestamp(ds["since"])
            since = since.tz_localize(NY) if since.tzinfo is None else since
            out["data_stale_min"] = round((now - since).total_seconds() / 60, 1)
        except (TypeError, ValueError):
            pass
        if out["data_stale_min"] is not None and out["data_stale_min"] > o["flatten_min"] and exposed:
            out["reasons"].append(f"data_stale: {out['data_stale_min']} min (> {o['flatten_min']:g}) with MCF exposure")
    failed = ((status or {}).get("health") or {}).get("flatten_failed") or []
    if failed and mcf_positions:
        out["reasons"].append(f"flatten_failed: the run could not close {sorted(failed)}; still held {sorted(mcf_positions)}")
    if now.time() >= plus(flatten_at, AFTER_FLATTEN_GRACE_MIN) and exposed:
        out["reasons"].append(f"after_flatten: MCF exposure after the {flatten_at:%H:%M} flatten "
                              f"({len(mcf_positions)} positions, {open_orders} open orders)")
    if out["reasons"]:
        out["action"] = "flatten"
    return out


def run(status: dict | None, broker, prefix: str, live: dict, mode: str = "dry", now: pd.Timestamp | None = None,
        sleep=None, session: dict | None = None) -> dict:
    """Read the broker (GET only), decide, and in mode 'act' cancel + flatten this prefix's orders/positions."""
    from .market_calendar import flatten_time, session_close

    check_prefix(prefix)
    if mode not in ("dry", "act"):
        raise ValueError("mode must be dry or act")
    now = now if now is not None else pd.Timestamp.now(tz=NY)
    session = session or {}
    try:
        close = session_close(now.tz_convert(NY).date(), broker)
    except Exception:
        close = time(16, 0)
    flat = flatten_time(session.get("flatten_by", "15:55"), close, float(session.get("flatten_lead_min", 5)))
    after = now.tz_convert(NY).normalize().to_pydatetime()
    try:
        mine = mcf_symbols_today(broker, prefix, after)
        held = sorted(mine & set(broker.positions()))
        n_open = open_order_count(broker, prefix, after)
    except Exception as e:                            # the broker is unreachable from here too: nothing we can do
        return {"at": str(now), "action": "none", "mode": mode, "prefix": prefix,
                "error": f"broker read failed: {type(e).__name__}: {str(e)[:200]}"}
    d = {**decide(status, now, held, n_open, live, close, flat), "mode": mode, "prefix": prefix}
    if d["action"] == "flatten":
        if mode == "act":
            left = flatten_prefix(broker, prefix, set(held), sleep=sleep)
            d.update(done=True, left=left)
            print(f"WATCHDOG FLATTENED {prefix}*: {held} (left {left}); reasons {d['reasons']}")
        else:
            d.update(done=False, would=f"cancel {n_open} open {prefix}* orders and flatten {held}")
            print(f"WATCHDOG (dry) would cancel {n_open} open {prefix}* orders and flatten {held}: {d['reasons']}")
    else:
        print(f"WATCHDOG ok ({prefix}*): {d.get('note') or 'no action'}; status age {d.get('status_age_min')} min, "
              f"{len(held)} MCF positions, {n_open} open MCF orders")
    return d


def _summary(d: dict) -> str:
    rows = "\n".join(f"| {k} | {json.dumps(v, default=str)} |" for k, v in d.items())
    return (f"### MCF watchdog ({os.environ.get('MCF_ACCOUNT', 'primary')}): **{d['action']}** (mode {d.get('mode')})\n\n"
            f"| field | value |\n|---|---|\n{rows}\n\n*Educational only - not financial advice.*\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--status", help="path to the state branch's status.json (missing file = no status)")
    ap.add_argument("--mode", default=os.environ.get("MCF_WATCHDOG_MODE") or "dry", choices=["dry", "act"])
    ap.add_argument("--out", help="write the decision as JSON here")
    a = ap.parse_args(argv)
    from ..config import load_config
    from .alpaca_broker import AlpacaBroker

    prefix = os.environ.get("MCF_COID_PREFIX", "mcf-")
    if prefix not in MCF_PREFIXES:
        raise SystemExit(f"bad MCF_COID_PREFIX {prefix!r}")
    status = None
    if a.status and os.path.exists(a.status):
        try:
            with open(a.status) as f:
                status = json.load(f)
        except (OSError, ValueError) as e:
            print(f"status.json unreadable: {e}")
    cfg = load_config()
    d = run(status, AlpacaBroker(paper=True), prefix, cfg.get("live") or {}, a.mode, session=cfg.get("session"))
    if a.out:
        with open(a.out, "w") as f:
            json.dump(d, f, indent=1, default=str)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(_summary(d))
    return d


if __name__ == "__main__":
    main()
