"""Date-scoped session rotation of setups (owner 2026-11-03 "Playing time"; GY-BENCH owner 2026-11-16).

Two per-setup config keys, resolved for ONE session date when the config is loaded (mcf/config.py), so the live runner,
the frozen setup snapshot (state/setups/<date>.json), the assignments file and the reports all see the same thing:

  benched: {from: "YYYY-MM-DD", until: "YYYY-MM-DD", reason: "...", away: <account>?}
      The setup sits out every session from `from` to `until` (inclusive) in THIS account and comes back by itself
      the session after `until`. Its block, rules and record are untouched. With `away: <account>` the setup is not
      resting but trading as a guest in that account for the window (it is never live in two accounts).
  guest: {from: "YYYY-MM-DD", until: "YYYY-MM-DD", home: <account>, reason: "..."}
      The block is live in THIS account only from `from` to `until`; outside the window it is off. Its home account
      carries the matching `benched: {..., away: <this account>}`. A guest's trades stay on its own setup record
      (tagged with this account); it is not this account's own setup (e.g. never "Graveyard-origin").

Only setups whose static `enabled` is true are affected. A benched session is logged in the snapshot's `rotation` block
({session, benched, away, guests}); the setup is not live that session, so it adds no traded session and no per-session
row (the playing-time report counts live sessions from the snapshot's enabled setups). Educational only - not financial
advice.
"""
from __future__ import annotations

import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

ROTATION_KEYS = ("benched", "guest")
NY = ZoneInfo("America/New_York")


def session_date(asof: str | date | None = None) -> date:
    """The session the config is resolved for: `asof`, else $MCF_ASOF, else today's date in New York."""
    v = asof if asof is not None else os.environ.get("MCF_ASOF")
    if v:
        return v if isinstance(v, date) else date.fromisoformat(str(v)[:10])
    return datetime.now(NY).date()


def _d(v) -> date:
    return v if isinstance(v, date) else date.fromisoformat(str(v)[:10])


def in_window(w: dict | None, d: date) -> bool:
    """True when session `d` lies in [from, until] (inclusive). A window needs both ends."""
    if not isinstance(w, dict) or not w.get("from") or not w.get("until"):
        return False
    return _d(w["from"]) <= d <= _d(w["until"])


def apply(cfg: dict, asof: str | date | None = None) -> dict:
    """Resolve `benched` / `guest` windows of cfg['strategies'] for one session (in place); returns the rotation log
    {session, benched, away, guests}, also stored as cfg['rotation']."""
    d = session_date(asof)
    log = {"session": d.isoformat(), "benched": [], "away": {}, "guests": {}}
    for k, v in (cfg.get("strategies") or {}).items():
        if not isinstance(v, dict) or not v.get("enabled"):
            continue
        b, g = v.get("benched"), v.get("guest")
        if g is not None and not in_window(g, d):
            v["enabled"] = False                     # a guest outside its window is back home
            continue
        if g is not None:
            log["guests"][k] = str(g.get("home") or "")
        if b is not None and in_window(b, d):
            v["enabled"] = False
            if b.get("away"):
                log["away"][k] = str(b["away"])
            else:
                log["benched"].append(k)
    cfg["rotation"] = log
    return log


def guests(strategies: dict) -> dict[str, dict]:
    """setup -> its `guest` window, for every block that has one (whatever the date)."""
    return {k: v["guest"] for k, v in (strategies or {}).items() if isinstance(v, dict) and isinstance(v.get("guest"), dict)}


def guest_dates(strategies: dict, setup: str, sessions) -> list[str]:
    """The sessions (ISO dates) of `sessions` that fall in `setup`'s guest window in this account."""
    g = guests(strategies).get(setup)
    return [s for s in sessions if g and in_window(g, _d(s))]


def window_violations(by_account: dict[str, dict]) -> list[str]:
    """Consistency of guest / away pairs across accounts (static configs, any date): every guest names a home whose
    block is benched `away` to this account over exactly the same window, and every `away` bench has its guest block."""
    bad = []
    for acct, st in by_account.items():
        for k, g in guests(st).items():
            home = (by_account.get(g.get("home")) or {}).get(k) or {}
            b = home.get("benched") if isinstance(home, dict) else None
            if not isinstance(b, dict) or b.get("away") != acct or str(b.get("from")) != str(g.get("from")) \
                    or str(b.get("until")) != str(g.get("until")):
                bad.append(f"{k}: guest in {acct} without a matching benched/away window in {g.get('home')}")
            if not isinstance(home, dict) or not home.get("enabled"):
                bad.append(f"{k}: home block in {g.get('home')} is not enabled (it could not come back by itself)")
        for k, v in (st or {}).items():
            b = v.get("benched") if isinstance(v, dict) else None
            if isinstance(b, dict) and b.get("away"):
                gst = ((by_account.get(b["away"]) or {}).get(k) or {}).get("guest")
                if not isinstance(gst, dict) or gst.get("home") != acct:
                    bad.append(f"{k}: benched away to {b['away']} from {acct} but no guest block there")
    return bad
