"""Playing time per setup: does every setup get enough signals and entries to be judged? (owner 2026-10-12)

"We need to monitor all accounts to make sure all setups are getting enough playing time and frequency with
testing; our setup counts may be too high per account."  RESEARCH_RULES rule 20: when setups compete for the same
symbol, report how many signals each lost to another setup; a setup's count is not judged without that context.

Report only. Nothing here changes which trades are taken. It reads the journal's `signals` table (every signal is
journaled: taken, skipped with a reason, or shadow), the `trades` table, and the per-session setup snapshot
(<state>/setups/<date>.json, written by the runner's freeze) for which setups were live and in what priority.

Per account, per setup, for today and cumulatively over the sessions the setup was live:
  signals, entries taken, closed trades, skips by reason (held by another setup - and which one -, slots full,
  per-setup cap, trades/day cap, daily loss cap, window, missed trigger, borrow, fill realism, price, broker reject,
  other), entries/day vs the setup's expected trades/day, weekly pace, and a verdict.

Expected trades/day comes from, in order: research/bdi/playingtime/expected_rates.json (two-year lab, 5 busiest
sessions left out), a "~X/day" note on the setup in the account config, the time-of-day study
(research/bdi/timeofday/results.csv: 'current' window, or 'full' for -FD copies), or the Apr-Jun backtest count in
config/validation.json / 62 sessions. These are lab rates on the two-year history (first qualifying bar
per symbol-day, no competition from other setups, lab universe), so live rates run below them for reasons other
than competition too; the verdict thresholds leave room for that.

Simulated playing time (owner 2026-10-13): the runner's what-if run (PaperRunner.what_if, journal run kind
'whatif', written at the flatten) replays every signal NOT taken - skipped, shadow, rejected - on the day's bars with
backtest costs. Per setup it is reported as sim_trades / sim_win_rate / sim_avg_r / sim_total_r (and the part lost
to another setup: sim_held_trades / sim_held_avg_r). SIMULATED: no fill-realism checks, so optimistic; it is
never added to the live trades, P/L or win rate.

Earnings blackout removes symbols before any setup scans, so it shows only as an account-level count.
Educational only - not financial advice.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from ..setup_names import name as setup_name

ROOT = Path(__file__).resolve().parents[2]
DISCLAIMER = "Educational only — not financial advice."
APR_JUN_SESSIONS = 62            # Apr-Jun 2026 NYSE sessions (Good Friday, Memorial Day, Juneteenth closed)

# Verdict thresholds, fixed before any account was scored (2026-10-12).
TARGET_PER_WEEK = 15.0           # 60 trades in 20 sessions (rule 18 probation) = 3 entries/day
CROWDED_SHARE = 0.25             # >= 25% of a setup's signals lost to other setups (and >= 3 signals) -> crowded-out
STARVED_RATIO = 0.25             # entries/day below 25% of expected (with >= 4 expected in the window) -> starved
SILENT_MIN_EXPECTED = 3.0        # 0 signals when >= 3 were expected (Poisson P(0) < 5%) -> silent
MIN_SESSIONS = 3                 # silent / starved need >= 3 live sessions (one session is noise); 'watch' before

BUCKETS = ["taken", "held_by_other", "slots_full", "setup_cap", "trades_cap", "daily_loss", "window",
           "missed_trigger", "borrow", "split_gate", "realism", "price", "rejected", "other"]
BUCKET_LABEL = {
    "taken": "Taken", "held_by_other": "Symbol held by another setup", "slots_full": "Slots full",
    "setup_cap": "Per-setup cap", "trades_cap": "Trades/day cap", "daily_loss": "Daily loss cap",
    "window": "Outside window (shadow)", "missed_trigger": "Trigger missed between polls",
    "borrow": "Not shortable / shorts off", "split_gate": "Split-tape short gate", "realism": "Spread / quote / size", "price": "Price through stop/target",
    "rejected": "Broker rejected", "other": "Other",
}


def classify(status: str, reason: str | None) -> str:
    """Map a journaled signal (status, reason) to one playing-time bucket."""
    s, r = str(status or ""), str(reason or "").lower()
    if s in ("submitted", "dry_run"):
        return "taken"
    if s == "shadow":
        return "window"
    if s == "rejected":
        return "rejected"
    if r.startswith("already in symbol") or r.startswith("opposite side held") or r.startswith("lot cap"):
        return "held_by_other"
    if r.startswith("max concurrent positions"):
        return "slots_full"
    if r.startswith("max positions for this setup"):
        return "setup_cap"
    if r.startswith("max trades/day"):
        return "trades_cap"
    if r.startswith("daily loss limit") or r == "halted":
        return "daily_loss"
    if r.startswith("missed"):
        return "missed_trigger"
    if "shortable" in r or "shorts disabled" in r:
        return "borrow"
    if r.startswith("split-tape short gate"):
        return "split_gate"
    if r.startswith(("spread", "no quote", "no two-sided", "size <")):
        return "realism"
    if r.startswith(("price already", "price below")):
        return "price"
    return "other"


# ---------------------------------------------------------------- expected trades/day
def _config_notes(paths) -> dict[str, float]:
    """'~X/day' written in the comment line right above a setup's key in the YAML config."""
    out: dict[str, float] = {}
    rx_rate, rx_key = re.compile(r"~\s*([0-9]+(?:\.[0-9]+)?)\s*/day"), re.compile(r"^  ([A-Za-z0-9_.\-]+):")
    for p in paths:
        p = Path(p)
        if not p.exists():
            continue
        pending = None
        for line in p.read_text().splitlines():
            st = line.strip()
            if st.startswith("#"):
                m = rx_rate.search(st)
                pending = float(m.group(1)) if m else pending
                continue
            m = rx_key.match(line)
            if m and pending is not None:
                out[m.group(1)] = pending
            pending = None
    return out


def expected_rates(account: str = "primary", root: Path = ROOT) -> dict[str, dict]:
    """{setup: {"per_day": float, "source": str}} - lab rates, see the module note."""
    out: dict[str, dict] = {}
    v = root / "config" / "validation.json"
    if v.exists():
        for k, x in json.loads(v.read_text()).get("setups", {}).items():
            if x.get("apr_jun_n"):
                out[k] = {"per_day": round(float(x["apr_jun_n"]) / APR_JUN_SESSIONS, 2), "source": "Apr-Jun backtest"}
    tod = root / "research" / "bdi" / "timeofday" / "results.csv"
    if tod.exists():
        t = pd.read_csv(tod, usecols=["setup", "set", "per_day"])
        for r in t[t["set"].isin(["current", "full"])].itertuples():
            key = r.setup if r.set == "current" else f"{r.setup}-FD"
            out[key] = {"per_day": float(r.per_day), "source": f"two-year lab ({r.set})"}
    trimmed = root / "research" / "bdi" / "playingtime" / "expected_rates.json"
    files = [root / "config" / "default.yaml"]
    if account and account != "primary":
        files.append(root / "config" / f"account_{account}.yaml")
    for k, x in _config_notes(files).items():
        out[k] = {"per_day": x, "source": "config note"}
    if trimmed.exists():   # preferred: same lab rates without the busiest sessions (research/bdi/playingtime)
        for k, x in json.loads(trimmed.read_text()).get("setups", {}).items():
            out[k] = {"per_day": float(x["per_day"]), "source": "two-year lab, 5 busiest days out"}
    return out


# ---------------------------------------------------------------- active setups per session
def _rank(strategies: dict, order: list | None) -> list[str]:
    on = [k for k, v in (strategies or {}).items() if isinstance(v, dict) and v.get("enabled", True)]
    pos = {n: i for i, n in enumerate(order or [])}
    return sorted(on, key=lambda n: pos.get(n, len(pos)))   # same rule as build_strategies (stable sort)


def active_setups(day: str, state_dir=None, cfg: dict | None = None, signals: pd.DataFrame | None = None):
    """(setups in priority order, source) for one session: the frozen snapshot, else the config (today only),
    else the setups that journaled any signal that day (approximate: a silent setup is invisible)."""
    if state_dir:
        p = Path(state_dir) / "setups" / f"{day}.json"
        if p.exists():
            try:
                snap = json.loads(p.read_text())
                return _rank(snap.get("strategies", {}), (snap.get("live") or {}).get("setup_order")), "snapshot"
            except (OSError, ValueError):
                pass
    if cfg is not None:
        return _rank(cfg.get("strategies", {}), (cfg.get("live") or {}).get("setup_order")), "config"
    if signals is not None and len(signals):
        return list(dict.fromkeys(signals.loc[signals["day"].astype(str) == day, "strategy"])), "signals (approx.)"
    return [], "none"


# ---------------------------------------------------------------- attribution
def attribute(sig: pd.DataFrame) -> pd.DataFrame:
    """Adds `bucket` and, for signals skipped because the symbol was held, `held_by` (the setup holding it).
    held_by comes from the runner's log (info.held_by, from 2026-10-12) or, for older rows, the latest earlier
    taken signal on the same symbol and day."""
    s = sig.copy()
    if not len(s):
        return s.assign(bucket=pd.Series(dtype=str), held_by=pd.Series(dtype=object))
    s["bucket"] = [classify(a, b) for a, b in zip(s["status"], s["reason"])]
    s["held_by"] = None
    if "id" not in s:
        s["id"] = range(len(s))
    taken = s[s["bucket"] == "taken"]
    for i, r in s[s["bucket"] == "held_by_other"].iterrows():
        h = None
        try:
            h = json.loads(r.get("info") or "{}").get("held_by")
        except (TypeError, ValueError):
            pass
        if not h:
            prior = taken[(taken["symbol"] == r["symbol"]) & (taken["day"].astype(str) == str(r["day"])) & (taken["id"] < r["id"])]
            h = prior["strategy"].iloc[-1] if len(prior) else None
        if isinstance(h, (list, tuple)):          # stacked lots: every setup holding the symbol, comma-joined
            h = ",".join(str(x) for x in h)
        s.at[i, "held_by"] = h or "unknown"
    return s


SIM_NOTE = ("SIMULATED: what-if replays of signals not taken (skipped, blocked, shadow) on the day's bars with backtest "
            "costs; no fill-realism checks, so optimistic. Never part of live trades, P/L or win rate.")


def _whatif(wi: pd.DataFrame | None) -> pd.DataFrame:
    """What-if trades with `date` (str) and the bucket of the signal they replay (meta 'status=..;why=..')."""
    if wi is None or not len(wi):
        return pd.DataFrame(columns=["date", "strategy", "r_multiple", "bucket"])
    w = wi.copy()
    w["date"] = w["date"].astype(str)
    meta = w["meta"].fillna("").astype(str) if "meta" in w else pd.Series("", index=w.index)
    st = meta.str.extract(r"status=([^;]*)")[0]
    why = meta.str.extract(r"why=(.*)$")[0]
    w["bucket"] = [classify(a, b) for a, b in zip(st.fillna(""), why.fillna(""))]
    return w


def _sim(w: pd.DataFrame) -> dict:
    r = w["r_multiple"].astype(float) if len(w) else pd.Series(dtype=float)
    h = r[w["bucket"] == "held_by_other"] if len(w) else r
    return {"sim_trades": int(len(r)), "sim_win_rate": round(float((r > 0).mean()), 3) if len(r) else None,
            "sim_avg_r": round(float(r.mean()), 3) if len(r) else None, "sim_total_r": round(float(r.sum()), 2),
            "sim_held_trades": int(len(h)), "sim_held_avg_r": round(float(h.mean()), 3) if len(h) else None}


def _peak_open(trades: pd.DataFrame) -> int:
    if trades is None or not len(trades):
        return 0
    ev = []
    for a, b in zip(pd.to_datetime(trades["entry_time"], utc=True, errors="coerce"),
                    pd.to_datetime(trades["exit_time"], utc=True, errors="coerce")):
        if pd.notna(a):
            ev += [(a, 1), (b if pd.notna(b) else a, -1)]
    cur = peak = 0
    for _, d in sorted(ev, key=lambda x: (x[0], x[1])):
        cur += d
        peak = max(peak, cur)
    return peak


# ---------------------------------------------------------------- rows and verdicts
def _verdict(n_sig, n_taken, held, sessions, per_day_exp) -> tuple[str, str]:
    exp_window = per_day_exp * sessions if per_day_exp else None
    early = sessions < MIN_SESSIONS
    if n_sig == 0:
        if exp_window is None:
            return ("silent", f"no signals in {sessions} session(s); no expected rate on file") if sessions >= 3 else \
                   ("quiet - wait", f"no signals in {sessions} session(s); too early to tell")
        if exp_window >= SILENT_MIN_EXPECTED and early:
            return "watch", f"no signals in {sessions} session(s), ~{exp_window:.1f} expected"
        if exp_window >= SILENT_MIN_EXPECTED:
            return "silent", f"no signals in {sessions} session(s), ~{exp_window:.1f} expected"
        return "quiet - wait", f"no signals yet; only ~{exp_window:.1f} expected so far"
    if held >= 3 and held / n_sig >= CROWDED_SHARE:
        return "crowded-out", f"{held} of {n_sig} signals ({held / n_sig:.0%}) lost to setups already holding the symbol"
    if exp_window is not None and exp_window >= 4 and n_taken / sessions < STARVED_RATIO * per_day_exp:
        if early:
            return "watch", f"{n_taken / sessions:.2f} entries/day vs ~{per_day_exp:.2f} expected"
        return "starved", f"{n_taken / sessions:.2f} entries/day vs ~{per_day_exp:.2f} expected"
    pace = n_taken / sessions * 5
    if pace < TARGET_PER_WEEK:
        weeks = 60 / pace if pace else float("inf")
        return "slow", f"{pace:.1f} entries/week; ~{weeks:.0f} weeks to 60 trades" if pace else "no entries yet"
    return "ok", f"{pace:.1f} entries/week"


def _holders(h: pd.Series) -> pd.Series:
    """held_by values, one per holding setup (stacked lots log several, comma-joined)."""
    h = h.dropna().astype(str)
    return h.str.split(",").explode().str.strip() if len(h) else h


def _rows(s: pd.DataFrame, tr: pd.DataFrame, sessions_by_setup: dict[str, int], rank: dict[str, int],
          expected: dict[str, dict], wi: pd.DataFrame | None = None) -> list[dict]:
    rows = []
    wi = _whatif(None) if wi is None else wi
    for st in sorted(set(sessions_by_setup) | set(s["strategy"] if len(s) else []), key=lambda n: (rank.get(n, 999), n)):
        g = s[s["strategy"] == st] if len(s) else s
        n_sess = max(int(sessions_by_setup.get(st, 0)), 1)
        counts = g["bucket"].value_counts().to_dict() if len(g) else {}
        skipped = {b: int(counts.get(b, 0)) for b in BUCKETS if b != "taken" and counts.get(b)}
        holders = _holders(g[g["bucket"] == "held_by_other"]["held_by"]) if len(g) else pd.Series(dtype=object)
        lost = holders.value_counts().to_dict() if len(holders) else {}
        higher = sum(v for k, v in lost.items() if rank.get(k, 999) < rank.get(st, 999))
        others = s[s["strategy"] != st] if len(s) else s     # its own lots blocking itself (re-entry) take nothing
        took = int((_holders(others["held_by"]) == st).sum()) if len(others) else 0
        n_sig, n_taken = int(len(g)), int(counts.get("taken", 0))
        n_trades = int((tr["strategy"] == st).sum()) if len(tr) else 0
        e = expected.get(st) or {}
        verdict, why = _verdict(n_sig, n_taken, int(counts.get("held_by_other", 0)), n_sess, e.get("per_day"))
        rows.append({
            "setup": st, "name": setup_name(st), "priority": rank.get(st), "sessions": n_sess,
            "signals": n_sig, "entries": n_taken, "trades": n_trades,
            "entries_per_day": round(n_taken / n_sess, 2), "signals_per_day": round(n_sig / n_sess, 2),
            "expected_per_day": e.get("per_day"), "expected_source": e.get("source"),
            "weekly_pace": round(n_taken / n_sess * 5, 1),
            "skipped": skipped, "lost_to": {k: int(v) for k, v in sorted(lost.items(), key=lambda kv: -kv[1])},
            "lost_to_higher_priority": int(higher), "lost_to_earlier_lower_priority": int(sum(lost.values()) - higher),
            "took_from_others": took, "verdict": verdict, "why": why,
            **_sim(wi[wi["strategy"] == st]),   # SIMULATED (what-if), separate from signals / entries / trades
        })
    return rows


def build(signals: pd.DataFrame, trades: pd.DataFrame | None, day: str, account: str = "primary",
          state_dir=None, cfg: dict | None = None, expected: dict | None = None, slots: int | None = None,
          earnings_excluded: int | None = None, whatif: pd.DataFrame | None = None) -> dict:
    """Playing-time report for one account: `today` (session `day`) and `cumulative` (every journaled session).
    `signals` / `trades` are the account's journal tables for its paper run; `whatif` its what-if run's trades
    (simulated, reported apart from the live counts)."""
    wi = _whatif(whatif)
    expected = expected_rates(account) if expected is None else expected
    sig = signals.copy() if signals is not None else pd.DataFrame(columns=["day", "strategy", "status", "reason", "symbol"])
    sig["day"] = sig["day"].astype(str)
    tr = trades.copy() if trades is not None and len(trades) else pd.DataFrame(columns=["date", "strategy"])
    tr["date"] = tr["date"].astype(str)
    days = sorted(set(sig["day"]) | ({day} if day else set()))
    active, src = {}, {}
    for d in days:
        active[d], src[d] = active_setups(d, state_dir, cfg if d == day else None, sig)
    att = attribute(sig)
    rank_today = {n: i + 1 for i, n in enumerate(active.get(day, []))}
    sess_cum: dict[str, int] = {}
    for d in days:
        live = set(active[d]) | set(att.loc[att["day"] == d, "strategy"])
        for st in live:
            sess_cum[st] = sess_cum.get(st, 0) + 1
    rank_cum = dict(rank_today)
    for d in reversed(days):   # setups no longer live keep their last known priority, after today's
        for i, n in enumerate(active[d]):
            rank_cum.setdefault(n, len(rank_today) + 1 + i)
    t_today = att[att["day"] == day]
    today_rows = _rows(t_today, tr[tr["date"] == day], {n: 1 for n in active.get(day, [])} |
                       {n: 1 for n in t_today["strategy"]}, rank_today, expected, wi[wi["date"] == day])
    cum_rows = _rows(att, tr, sess_cum, rank_cum, expected, wi)
    for r in cum_rows:
        r["live_today"] = r["setup"] in rank_today

    def summary(a: pd.DataFrame, rows: list[dict], n_days: int, t: pd.DataFrame) -> dict:
        n = len(a)
        held = int((a["bucket"] == "held_by_other").sum()) if n else 0
        by = {v: [r["setup"] for r in rows if r["verdict"] == v] for v in ("silent", "crowded-out", "starved", "watch", "slow")}
        return {"sessions": n_days, "setups": len(rows), "signals": int(n),
                "entries": int((a["bucket"] == "taken").sum()) if n else 0, "trades": int(len(t)),
                "lost_to_other_setups": held, "lost_share": round(held / n, 3) if n else 0.0,
                "skipped": {b: int(c) for b, c in (a["bucket"].value_counts().items() if n else []) if b != "taken"},
                "peak_open_positions": _peak_open(t), **{k.replace("-", "_"): v for k, v in by.items()}}

    s_today = summary(t_today, today_rows, 1, tr[tr["date"] == day])
    s_today.update(_sim(wi[wi["date"] == day]))
    s_today.update(setups_live=len(active.get(day, [])), slots=slots, earnings_excluded=earnings_excluded,
                   setup_source=src.get(day))
    return {
        "account": account, "day": day, "window": f"{days[0]} to {days[-1]}" if days else "no sessions",
        "target_per_week": TARGET_PER_WEEK, "today": {"summary": s_today, "setups": today_rows},
        "cumulative": {"summary": {**summary(att, cum_rows, len(days), tr), **_sim(wi)}, "setups": cum_rows},
        "sim_note": SIM_NOTE,
        "rules": (f"silent: no signals when >= {SILENT_MIN_EXPECTED:g} were expected; crowded-out: >= "
                  f"{CROWDED_SHARE:.0%} of signals (and >= 3) skipped because another setup held the symbol; starved: "
                  f"entries/day < {STARVED_RATIO:.0%} of the expected rate (>= 4 expected); slow: on track but below "
                  f"{TARGET_PER_WEEK:g} entries/week (60 trades in 20 sessions); ok otherwise. Expected rates are lab "
                  f"rates without competition, so they are an upper reference. silent / starved need >= {MIN_SESSIONS} live "
                  f"sessions ('watch' before that)."),
        "note": f"Report only; it does not change which trades are taken. {DISCLAIMER}",
    }


def from_journal(journal, run_id: int, day: str, cfg: dict, state_dir=None) -> dict:
    """Convenience for the EOD job: read the account's journal and state, then build()."""
    sig = pd.read_sql("SELECT * FROM signals WHERE run_id=? ORDER BY id", journal.db, params=[run_id])
    tr = journal.trades(run_id=run_id)
    wi = journal.trades(kind="whatif")   # read only: the runner writes it at the flatten
    eb = None
    if state_dir:
        p = Path(state_dir) / "earnings" / f"{day}.json"
        if p.exists():
            try:
                eb = len(json.loads(p.read_text()).get("symbols", {}))
            except (OSError, ValueError):
                eb = None
    return build(sig, tr, day, cfg.get("account_name", "primary"), state_dir, cfg,
                 slots=(cfg.get("account") or {}).get("max_concurrent_positions"), earnings_excluded=eb, whatif=wi)


# ---------------------------------------------------------------- EOD section
VERDICT_COLOR = {"watch": "#b45309", "silent": "#d03b3b", "crowded-out": "#b45309", "starved": "#d03b3b", "slow": "#52514e",
                 "quiet - wait": "#898781", "ok": "#0b8a3e"}


def html(rep: dict | None) -> str:
    if not rep:
        return ""
    td = "style='padding:3px 8px;border-bottom:1px solid #e1e0d9;text-align:left'"
    st, cs = rep["today"]["summary"], rep["cumulative"]["summary"]
    today = {r["setup"]: r for r in rep["today"]["setups"]}
    acct = {"primary": "Primary", "testing": "Testing 1", "testing2": "Testing 2", "gen": "Setup Generator"}.get(rep["account"], rep["account"])

    def lost(r):
        return ", ".join(f"{k} {v}" for k, v in list(r["lost_to"].items())[:3]) or "–"

    def skip(r):
        return ", ".join(f"{BUCKET_LABEL.get(k, k).lower()} {v}" for k, v in sorted(r["skipped"].items(), key=lambda kv: -kv[1])[:3]) or "–"

    rows = []
    for r in rep["cumulative"]["setups"]:
        if not r.get("live_today"):
            continue
        t = today.get(r["setup"], {})
        e = "–" if r["expected_per_day"] is None else f"{r['expected_per_day']:.2f}"
        c = VERDICT_COLOR.get(r["verdict"], "#52514e")
        sim = (f"{r.get('sim_trades', 0)} / " + ("–" if r.get("sim_avg_r") is None else f"{r['sim_avg_r']:+.2f}R")
               + ("" if r.get("sim_win_rate") is None else f" / {r['sim_win_rate']:.0%}"))
        rows.append(f"<tr><td {td}>{r['priority']}</td><td {td}>{r['name']}<br><span style='font-size:11px;color:#898781'>{r['setup']}</span></td>"
                    f"<td {td}>{t.get('signals', 0)} / {t.get('entries', 0)}</td><td {td}>{r['sessions']}</td>"
                    f"<td {td}>{r['signals']} / {r['entries']} / {r['trades']}</td><td {td}>{r['entries_per_day']:.2f}</td><td {td}>{e}</td>"
                    f"<td {td}>{r['skipped'].get('held_by_other', 0)}</td><td {td}>{lost(r)}</td>"
                    f"<td {td}>{skip(r)}</td><td {td}><i>{sim}</i></td><td {td}><b style='color:{c}'>{r['verdict']}</b><br><span style='font-size:11px;color:#52514e'>{r['why']}</span></td></tr>")
    head = ("Prio", "Setup", "Today sig / taken", "Sessions", "Signals / taken / trades", "Taken/day", "Expected/day",
            "Lost to other setups", "Lost to (setup n)", "Top skip reasons", "SIMULATED: not-taken n / avg R / win", "Verdict")
    flags = []
    for k, lab in (("silent", "Silent"), ("crowded_out", "Crowded out"), ("starved", "Starved")):
        if cs.get(k):
            flags.append(f"<b>{lab}:</b> {', '.join(cs[k])}")
    eb = f" Earnings blackout removed {st['earnings_excluded']} symbols before scanning." if st.get("earnings_excluded") else ""
    slots = f" Peak open positions today {st['peak_open_positions']} of {st['slots']} slots." if st.get("slots") else ""
    return (f"<h3>Playing time — {acct} account</h3>"
            f"<p style='font-size:13px'>{st['setups_live']} setups live today. Today: {st['signals']} signals, {st['entries']} taken, "
            f"<b>{st['lost_to_other_setups']}</b> lost because another setup held the symbol ({st['lost_share']:.0%}). "
            f"Since {rep['window'].split(' to ')[0]} ({cs['sessions']} sessions): {cs['signals']} signals, {cs['entries']} taken, "
            f"{cs['lost_to_other_setups']} lost to other setups ({cs['lost_share']:.0%}).{slots}{eb}</p>"
            + (f"<p style='font-size:13px'><i>Simulated playing time (not live): {cs['sim_trades']} what-if trades of signals not "
               f"taken, avg {cs['sim_avg_r']:+.2f}R, {cs['sim_win_rate']:.0%} winners; of them {cs['sim_held_trades']} lost to "
               f"another setup" + ("" if cs.get("sim_held_avg_r") is None else f" (avg {cs['sim_held_avg_r']:+.2f}R)") + ".</i></p>"
               if cs.get("sim_trades") else "")
            + (f"<p style='font-size:13px'>{' · '.join(flags)}</p>" if flags else "")
            + "<table style='border-collapse:collapse;font-size:12px'><tr>" + "".join(f"<th {td}>{h}</th>" for h in head) + "</tr>"
            + ("".join(rows) or f"<tr><td colspan={len(head)}>No setups live.</td></tr>") + "</table>"
            f"<div style='font-size:11px;color:#52514e'>Cumulative over the sessions each setup was live. {rep['rules']} "
            f"Signals lost to another setup are still simulated in the what-if run. {rep.get('sim_note', SIM_NOTE)} {rep['note']}</div>")
