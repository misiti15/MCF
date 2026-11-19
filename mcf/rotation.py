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


# ------------------------------------------------------------------------------------------- C3-ROT family caps
# Owner C3-ROT yes 2026-11-18 (research/consultant_p3/RESULTS.md #9): per-session rotation caps on the families that hog
# arena reps - at most 2 CWT14 variants across the whole testing arena and at most 6 GEN setups per arena account in one
# session. The rest of the family sits the session out (benched, logged in the setup snapshot's `rotation.family_benched`,
# excluded from per-session stats exactly like a GY-BENCH bench). Never in Primary, On Deck or the Graveyard; never an
# in-session throttle. Order: fewest reps first (docs/live/arena_reps.json: live active days + shadow days, refreshed by
# `python -m mcf.report.arena_reps`), then a round-robin by session so every member plays even if the reps file is stale.
# Applied by the live trade command (mcf/cli.py) for the session it trades; load_config() itself is unchanged.
ARENA_ACCOUNTS = ("testing2", "explore1", "livelab", "testingd", "testinge", "testingf", "gen")


def _bdays(a: date, b: date) -> int:
    n, d = 0, a
    step = 1 if b >= a else -1
    while d != b:
        d = date.fromordinal(d.toordinal() + step)
        if d.weekday() < 5:
            n += step
    return n


def _reps(path) -> dict:
    import json
    from pathlib import Path

    try:
        d = json.loads(Path(path).read_text())
        return {k: float((v or {}).get("active_days", 0) or 0) + float((v or {}).get("shadow_days", 0) or 0)
                for k, v in (d.get("setups") or {}).items()}
    except Exception:
        return {}


def _resource_frac(path, acct: str):
    """ROT2: this account's resource-skip share of signals from the resource file ({accounts: {acct: {resource_skip_frac}}}),
    or None when there is no file / row."""
    import json
    from pathlib import Path

    try:
        v = ((json.loads(Path(path).read_text()).get("accounts") or {}).get(acct) or {}).get("resource_skip_frac")
        return None if v is None else float(v)
    except Exception:
        return None


def _rare(path, below) -> set:
    """ROT2: setups whose signals per active day (arena_reps.json) are under `below` (rare or day/index-gated)."""
    if below is None:
        return set()
    import json
    from pathlib import Path

    try:
        d = json.loads(Path(path).read_text()).get("setups") or {}
    except Exception:
        return set()
    out = set()
    for k, v in d.items():
        days, sig = float((v or {}).get("active_days") or 0), float((v or {}).get("signals") or 0)
        if days > 0 and sig / days < float(below):
            out.add(k)
    return out


def pick(members: list[str], cap: int, d: date, start: date, reps: dict | None = None) -> list[str]:
    """The `cap` members that play session `d`: members ordered by reps (fewest first, then name), then a window of
    `cap` that advances by `cap` every weekday since `start` (round-robin)."""
    if cap <= 0 or len(members) <= cap:
        return sorted(members)
    reps = reps or {}
    ring = sorted(members, key=lambda k: (reps.get(k, 0.0), k))
    off = (max(0, _bdays(start, d)) * cap) % len(ring)
    return sorted((ring + ring)[off:off + cap])


def family_caps(cfg: dict, asof=None, members_by_account: dict | None = None, root=None) -> dict:
    """Bench, for session `asof`, the family members over their cap in this account (cfg['account_name']); in place.
    `members_by_account`: account -> enabled setup names after the date windows (default: loaded from the configs).
    Returns {family: {"cap", "scope", "playing", "benched"}} and stores the benched names in cfg['rotation']."""
    rc = cfg.get("arena_rotation") or {}
    acct = cfg.get("account_name", "primary")
    d = session_date(asof)
    if not rc.get("enabled") or acct not in (rc.get("accounts") or ARENA_ACCOUNTS):
        return {}
    start = _d(rc.get("from") or d)
    if d < start:
        return {}
    from pathlib import Path

    base = Path(root) if root else Path(__file__).resolve().parents[1]
    reps = _reps(base / str(rc.get("reps_file") or "docs/live/arena_reps.json"))
    mine = [k for k, v in (cfg.get("strategies") or {}).items() if isinstance(v, dict) and v.get("enabled")]
    # ROT2 (owner yes 2026-11-18, amends C3-ROT): caps apply only in an account whose resource skips (slots, buying
    # power, per-setup cap, halt, crowding) exceed min_resource_skip_frac of its signals in the resource file (refreshed
    # by the blocked-signal audit); no file / no row / at or under the line -> no family cap in this account today.
    gate = rc.get("min_resource_skip_frac")
    if gate is not None:
        frac = _resource_frac(base / str(rc.get("resource_file") or "docs/live/arena_resources.json"), acct)
        if frac is None or frac <= float(gate):
            log = cfg.setdefault("rotation", {"session": d.isoformat(), "benched": [], "away": {}, "guests": {}})
            log["family_benched"] = {}
            log["family_caps_off"] = {"resource_skip_frac": frac, "line": float(gate)}
            return {}
    rare = _rare(base / str(rc.get("reps_file") or "docs/live/arena_reps.json"), rc.get("never_bench_below_signals"))
    out = {}
    for fam, spec in (rc.get("caps") or {}).items():
        prefix, cap, scope = str(spec.get("prefix", fam)), int(spec.get("cap", 0)), str(spec.get("scope", "account"))
        import re as _re

        skip = _re.compile(str(spec.get("exclude_regex") or r"-WB\d+$"))   # Workbench copies keep their priority exposure
        if scope == "arena":
            if members_by_account is None:
                members_by_account = _arena_members(rc.get("accounts") or ARENA_ACCOUNTS, d)
            pool = sorted({k for a, ks in members_by_account.items() for k in ks if k.startswith(prefix) and not skip.search(k)}
                          | {k for k in mine if k.startswith(prefix) and not skip.search(k)})
        else:
            pool = [k for k in mine if k.startswith(prefix) and not skip.search(k)]
        # ROT2: rare / day-gated setups (signals per active day under never_bench_below_signals) are never benched;
        # they keep every session and take no place in the capped pool
        pool = [k for k in pool if k not in rare]
        play = set(pick(pool, cap, d, start, reps))
        bench = sorted(k for k in mine if k.startswith(prefix) and not skip.search(k) and k not in play and k not in rare)
        for k in bench:
            cfg["strategies"][k]["enabled"] = False
        out[fam] = {"cap": cap, "scope": scope, "pool": len(pool), "playing": sorted(k for k in mine if k in play),
                    "benched": bench}
    log = cfg.setdefault("rotation", {"session": d.isoformat(), "benched": [], "away": {}, "guests": {}})
    log["family_benched"] = {f: v["benched"] for f, v in out.items() if v["benched"]}
    return out


def _arena_members(accounts, d: date) -> dict[str, list[str]]:
    """account -> enabled setups for session d (configs + date windows), for the arena-wide caps."""
    from .config import load_config

    old = os.environ.get("MCF_ACCOUNT")
    out = {}
    try:
        for a in accounts:
            os.environ["MCF_ACCOUNT"] = a
            st = load_config(asof=d).get("strategies") or {}
            out[a] = [k for k, v in st.items() if isinstance(v, dict) and v.get("enabled")]
    finally:
        if old is None:
            os.environ.pop("MCF_ACCOUNT", None)
        else:
            os.environ["MCF_ACCOUNT"] = old
    return out
