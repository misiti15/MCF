"""Dollar P/L reconciliation: Alpaca vs journal vs status.json (owner 2026-11-05: "The dashboard shows a different P/L.
We have to make sure that lines up with anything EOD and Alpaca.").

ONE dollar truth: an account's day P/L is its Alpaca equity change vs the prior close (equity - last_equity). The journal
sum(pnl) (broker fills paired into trades) and status.json today.pnl should match it; the modelled real-book stop penalty
(pnl_adj, mcf/execution/reconcile.py) is NOT a dollar figure - it lives only inside R (conservative R = pnl_adj / risk).

Per account and date:
  alpaca   equity close (Alpaca portfolio history, or account equity/last_equity for the current session; without keys the
           last status.json snapshot of that session vs the one before - source "status_snapshot")
  journal  sum(pnl) of the journal's live trades dated D (whatif runs excluded)
  status   status.json today.pnl / history[D].pnl
Flags |alpaca - journal| or |alpaca - status| > max($10, 2% of |alpaca day|). With the account's keys, fills are matched
per symbol (Alpaca FILL cash flow vs journal pnl; a flat intraday book's cash flow is its realised P/L) and non-fill
activities (fees, borrow, dividends, ...) are listed.

    python -m mcf.report.reconcile_pl --date 2026-11-05 [--account primary] [--json out.json] [--fyi]
    python -m mcf.report.reconcile_pl --backfill       # writes docs/live/equity_history.json from git history + Alpaca

`--fyi` prints one line (the nightly loop reads it; also saved by the EOD job as reports/pl_reconcile/<date>.txt).
Paper results. Educational only — not financial advice.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
ET = ZoneInfo("America/New_York")
EQUITY_HISTORY = ROOT / "docs" / "live" / "equity_history.json"
DISCLAIMER = "Educational only — not financial advice."
BRANCH = {"primary": "mcf-data", "testing": "mcf-data-testing", "testing2": "mcf-data-testing2", "gen": "mcf-data-gen",
          "graveyard": "mcf-data-graveyard", "livelab": "mcf-data-livelab", "explore1": "mcf-data-explore1"}
KEYS = {"primary": "ALPACA", "testing": "ALPACA_TESTING", "testing2": "ALPACA_TESTING2", "gen": "ALPACA_GEN",
        "graveyard": "ALPACA_GRAVEYARD", "livelab": "ALPACA_LIVELAB", "explore1": "ALPACA_EXPLORE1"}
ABS_TOL, REL_TOL, SYM_TOL = 10.0, 0.02, 1.0
PAPER_START = 100_000.0
PAPER = "https://paper-api.alpaca.markets/v2"


def tolerance(day_pl: float | None) -> float:
    return max(ABS_TOL, REL_TOL * abs(day_pl or 0.0))


# ---------------------------------------------------------------- Alpaca (read-only GETs)
def _keys(acct: str):
    """(key, secret) for the account: ALPACA_<ACCT>_API_KEY, or ALPACA_TRADE_* when MCF_ACCOUNT is this account (the EOD
    job), or ALPACA_API_KEY for Primary. None when not available."""
    p = KEYS[acct]
    k, s = os.environ.get(f"{p}_API_KEY"), os.environ.get(f"{p}_SECRET_KEY")
    if os.environ.get("MCF_ACCOUNT", "primary") == acct and os.environ.get("ALPACA_TRADE_API_KEY"):
        k, s = os.environ["ALPACA_TRADE_API_KEY"], os.environ.get("ALPACA_TRADE_SECRET_KEY")
    return (k, s) if k and s else None


def _get(acct: str, path: str, params: dict | None = None):
    import requests

    k = _keys(acct)
    if not k:
        return None
    r = requests.get(PAPER + path, headers={"APCA-API-KEY-ID": k[0], "APCA-API-SECRET-KEY": k[1]}, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def alpaca_closes(acct: str) -> dict[str, float]:
    """{ET date: equity at that session's close} from Alpaca portfolio history (daily bars are stamped at the evening of
    the session in UTC, so the ET date is the session), plus the current session from the account (equity now)."""
    out: dict[str, float] = {}
    try:
        ph = _get(acct, "/account/portfolio/history", {"period": "3M", "timeframe": "1D"})
    except Exception:
        ph = None
    for t, e in zip((ph or {}).get("timestamp") or [], (ph or {}).get("equity") or []):
        if e is not None:
            out[datetime.fromtimestamp(t, timezone.utc).astimezone(ET).date().isoformat()] = float(e)
    try:
        a = _get(acct, "/account")
    except Exception:
        a = None
    if a:
        today = datetime.now(ET).date().isoformat()
        if a.get("last_equity"):
            prev = [d for d in out if d < today]
            if prev:
                out[max(prev)] = float(a["last_equity"])   # the broker's own base for today's P/L
        if datetime.now(ET).hour >= 16 or today in out:
            out[today] = float(a["equity"])
    return out


def alpaca_activities(acct: str, date: str) -> list[dict] | None:
    """The account's activities that belong to session `date`, or None without keys: fills dated `date`, plus non-fill
    activities (fees, borrow, ...) that name the session ("REG fee ... on <date>": Alpaca posts the day's regulatory
    fees with the next day's date but they are already in that session's closing equity) or are dated `date` and name
    no other session."""
    import re

    if not _keys(acct):
        return None
    nxt = (datetime.fromisoformat(date) + timedelta(days=1)).date().isoformat()
    out = []
    for d in (date, nxt, (datetime.fromisoformat(date) + timedelta(days=3)).date().isoformat()):
        for a in _activities(acct, d, fills=d == date):
            if a.get("activity_type") == "FILL":
                if d == date:
                    out.append(a)
                continue
            m = re.search(r"\bon (\d{4}-\d{2}-\d{2})\b", a.get("description") or "")
            ad = str(a.get("date") or "")[:10]
            if (m.group(1) == date) if m else (ad == date or (not ad and d == date)):
                if all(a.get("id") != b.get("id") for b in out):
                    out.append(a)
    return out


NON_FILL = "FEE,CFEE,PTC,DIV,DIVCGL,DIVCGS,DIVNRA,DIVROC,DIVTXEX,INT,JNLC,JNLS,MA,NC,REORG,SC"
ROUTINE = {"FEE", "CFEE"}   # regulatory (REG/TAF/CAT) and borrow fees: listed, not flagged (inside the day's equity)


def _activities(acct: str, date: str, fills: bool = True) -> list[dict]:
    acts, tok = [], None
    for _ in range(50):
        p = {"date": date, "page_size": 100, "direction": "asc"}
        if not fills:
            p["activity_types"] = NON_FILL
        if tok:
            p["page_token"] = tok
        page = _get(acct, "/account/activities", p) or []
        acts += page
        if len(page) < 100:
            break
        tok = page[-1].get("id")
    return acts


def fill_check(acts: list[dict], journal_by_sym: dict[str, float]) -> dict:
    """Per symbol: Alpaca fill cash flow (sells +, buys -) vs journal pnl. Symbols not flat at the broker that day are
    reported as open (their cash flow is not P/L). Non-fill activities listed with net_amount."""
    flow: dict[str, float] = {}
    pos: dict[str, float] = {}
    other = []
    for a in acts:
        if a.get("activity_type") == "FILL":
            q, px, sym = float(a["qty"]), float(a["price"]), a["symbol"]
            sgn = 1 if a["side"] in ("sell", "sell_short") else -1
            flow[sym] = flow.get(sym, 0.0) + sgn * q * px
            pos[sym] = pos.get(sym, 0.0) - sgn * q
        else:
            other.append({"type": a.get("activity_type"), "symbol": a.get("symbol"), "net_amount": float(a.get("net_amount") or 0),
                          "description": a.get("description")})
    unmatched, open_syms = [], []
    for sym in sorted(set(flow) | set(journal_by_sym)):
        if abs(pos.get(sym, 0.0)) > 1e-9:
            open_syms.append(sym)
            continue
        d = flow.get(sym, 0.0) - journal_by_sym.get(sym, 0.0)
        if abs(d) > SYM_TOL:
            unmatched.append({"symbol": sym, "alpaca": round(flow.get(sym, 0.0), 2), "journal": round(journal_by_sym.get(sym, 0.0), 2),
                              "diff": round(d, 2)})
    return {"fills": sum(a.get("activity_type") == "FILL" for a in acts), "fill_pnl": round(sum(flow.values()), 2),
            "unmatched": unmatched, "not_flat": open_syms, "other": other,
            "fees": round(sum(o["net_amount"] for o in other), 2)}


# ---------------------------------------------------------------- data branches
def _git(*args) -> bytes | None:
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, check=True).stdout
    except Exception:
        return None


def status_now(acct: str, state_dir: str | None = None) -> dict:
    if state_dir:
        try:
            return json.loads((Path(state_dir) / "status.json").read_text())
        except Exception:
            return {}
    raw = _git("show", f"origin/{BRANCH[acct]}:status.json")
    return json.loads(raw) if raw else {}


def status_snapshots(acct: str, since: str = "2026-10-01") -> dict[str, dict]:
    """{session date: last status.json of that session} from the data branch's git history (one `git show` per day)."""
    raw = _git("log", "--format=%H %cI", f"--since={since}", f"origin/{BRANCH[acct]}", "--", "status.json")
    by_day: dict[str, str] = {}
    for line in (raw or b"").decode().splitlines():
        h, t = line.split()
        d = datetime.fromisoformat(t).astimezone(ET).date().isoformat()
        by_day.setdefault(d, h)        # newest first: the first commit seen is the day's last
    out = {}
    for d, h in sorted(by_day.items()):
        s = _git("show", f"{h}:status.json")
        try:
            s = json.loads(s) if s else None
        except ValueError:
            s = None
        if s and s.get("session_date") == d and (s.get("account") or {}).get("equity") is not None:
            out[d] = s
    return out


def journal_day(acct: str, date: str, state_dir: str | None = None) -> dict:
    """{'pnl', 'pnl_adj', 'trades', 'by_symbol'} from the account's journal.db (live runs, trades dated `date`)."""
    import sqlite3
    import tempfile

    if state_dir:
        jp = Path(state_dir) / "journal.db"
        raw = jp.read_bytes() if jp.exists() else None
    else:
        raw = _git("show", f"origin/{BRANCH[acct]}:journal.db")
    if not raw:
        return {}
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        f.write(raw)
    try:
        db = sqlite3.connect(f.name)
        rows = db.execute("SELECT t.symbol, t.pnl, t.pnl_adj FROM trades t JOIN runs r ON r.id = t.run_id "
                          "WHERE r.kind != 'whatif' AND t.date = ? AND t.exit_time IS NOT NULL", (date,)).fetchall()
    except Exception:
        return {}
    finally:
        os.unlink(f.name)
    by: dict[str, float] = {}
    for s, p, _ in rows:
        by[s] = by.get(s, 0.0) + (p or 0.0)
    return {"trades": len(rows), "pnl": round(sum(p or 0 for _, p, _ in rows), 2),
            "pnl_adj": round(sum((pa if pa is not None else (p or 0)) for _, p, pa in rows), 2), "by_symbol": by}


def snapshot_closes(snaps: dict[str, dict]) -> dict[str, float]:
    """{date: equity} from the sessions' last status.json; an account's first session is measured from the paper start
    (PAPER_START) when its first status shows equity within 5% of it."""
    closes = {d: float(s["account"]["equity"]) for d, s in snaps.items()}
    if closes:
        first = min(closes)
        hist = snaps[first].get("history") or []
        if (not hist or hist[0].get("date") == first) and abs(closes[first] - PAPER_START) < 0.05 * PAPER_START:
            closes["0000-00-00"] = PAPER_START
    return closes


def equity_history(acct: str) -> dict[str, dict]:
    """The stored broker truth {date: {equity_close, alpaca_day_pl, source}} (docs/live/equity_history.json)."""
    try:
        return (json.loads(EQUITY_HISTORY.read_text()).get("accounts") or {}).get(acct) or {}
    except Exception:
        return {}


def day_rows(closes: dict[str, float], source: str) -> dict[str, dict]:
    """{date: {equity_close, alpaca_day_pl (vs the prior session's close), source}} from {date: equity close}."""
    out, prev = {}, None
    for d in sorted(closes):
        e = closes[d]
        out[d] = {"equity_close": round(e, 2), "alpaca_day_pl": round(e - prev, 2) if prev is not None else None, "source": source}
        prev = e
    return out


# ---------------------------------------------------------------- the check
def reconcile(date: str, acct: str, with_fills: bool = True, state_dir: str | None = None) -> dict:
    """The day's check for one account; state_dir = a local data-branch checkout (the EOD job), else origin/<branch>."""
    st = status_now(acct, state_dir)
    hist = {h.get("date"): h for h in st.get("history") or []}
    s_pnl = (st.get("today") or {}).get("pnl") if st.get("session_date") == date else (hist.get(date) or {}).get("pnl")
    closes = alpaca_closes(acct)
    src, alp, eq = "alpaca", None, None
    if date not in closes:
        stored = equity_history(acct)
        if (stored.get(date) or {}).get("alpaca_day_pl") is not None:
            closes = {}
            alp, eq, src = stored[date]["alpaca_day_pl"], stored[date]["equity_close"], stored[date].get("source", "stored")
        else:
            snaps = {} if state_dir else status_snapshots(acct, (datetime.fromisoformat(date) - timedelta(days=10)).date().isoformat())
            for d, r in ((st.get("equity_history") or {}).items() if state_dir else ()):
                if r.get("equity_close") is not None:
                    snaps[d] = {"account": {"equity": r["equity_close"]}}
            closes = snapshot_closes(snaps)
            src = "status_snapshot"
    if closes:
        prior = [d for d in closes if d < date]
        eq = closes.get(date)
        alp = round(eq - closes[max(prior)], 2) if eq is not None and prior else None
    jd = journal_day(acct, date, state_dir)
    out = {"account": acct, "date": date, "alpaca_day_pl": alp, "equity_close": eq, "source": src,
           "journal_pnl": jd.get("pnl"), "journal_pnl_adj": jd.get("pnl_adj"), "journal_trades": jd.get("trades"),
           "status_pnl": s_pnl, "tolerance": round(tolerance(alp), 2)}
    flags = []
    for k in ("journal_pnl", "status_pnl"):
        if alp is not None and out[k] is not None:
            out[k.replace("_pnl", "_diff")] = d = round(out[k] - alp, 2)
            if abs(d) > out["tolerance"]:
                flags.append(f"{k.split('_')[0]} {d:+.2f} vs Alpaca")
    if alp is None:
        flags.append("no Alpaca equity for the day")
    if with_fills and src == "alpaca":
        try:
            acts = alpaca_activities(acct, date)
        except Exception as e:
            acts, out["fills_error"] = None, type(e).__name__
        if acts is not None:
            out["fills"] = fc = fill_check(acts, jd.get("by_symbol") or {})
            if fc["unmatched"]:
                flags.append(f"{len(fc['unmatched'])} symbols' fills differ from the journal")
            odd = [o for o in fc["other"] if o["type"] not in ROUTINE]
            if odd:
                flags.append(f"{len(odd)} non-fee activities ({sum(o['net_amount'] for o in odd):+.2f})")
            if alp is not None and jd.get("pnl") is not None:
                out["fees"] = fc["fees"]
                out["residual"] = round(alp - jd["pnl"] - fc["fees"], 2)   # what fills + fees do not explain
    out["flags"], out["ok"] = flags, not flags
    return out


def fyi(rows: list[dict]) -> str:
    """One line for the nightly loop / EOD output."""
    bad = [r for r in rows if not r["ok"]]
    head = f"P/L reconcile {rows[0]['date'] if rows else ''}: " + ("all match Alpaca" if not bad else f"{len(bad)} of {len(rows)} accounts off")
    parts = []
    for r in rows:
        a = r["alpaca_day_pl"]
        parts.append(f"{r['account']} Alpaca {a:+.2f}" if a is not None else f"{r['account']} Alpaca n/a")
        if not r["ok"]:
            parts[-1] += " (" + "; ".join(r["flags"]) + ")"
    return head + " · " + " · ".join(parts)


def save(rows: list[dict], state_dir: str, date: str) -> str:
    """reports/pl_reconcile/<date>.json + .txt (the one-line FYI the nightly loop reads) in the account's state dir."""
    d = Path(state_dir) / "reports" / "pl_reconcile"
    d.mkdir(parents=True, exist_ok=True)
    line = fyi(rows)
    (d / f"{date}.json").write_text(json.dumps({"rows": rows, "fyi": line, "disclaimer": DISCLAIMER}, indent=1, default=str) + "\n")
    (d / f"{date}.txt").write_text(line + "\n")
    return line


def backfill(accounts=tuple(BRANCH), since: str = "2026-10-01") -> dict:
    """docs/live/equity_history.json: per account, Alpaca portfolio history when the account's keys are here, else the
    last status.json snapshot of each session (git history); a stored Alpaca row is never replaced by a snapshot."""
    try:
        doc = json.loads(EQUITY_HISTORY.read_text())
    except Exception:
        doc = {}
    accts = doc.setdefault("accounts", {})
    for a in accounts:
        closes = {d: e for d, e in alpaca_closes(a).items() if d >= since}
        rows = day_rows(closes, "alpaca") if closes else {}
        snap_rows = day_rows(snapshot_closes(status_snapshots(a, since)), "status_snapshot")
        snap_rows.pop("0000-00-00", None)
        cur = accts.setdefault(a, {})
        for d, r in snap_rows.items():
            if (cur.get(d) or {}).get("source") != "alpaca":
                cur[d] = r
        cur.update({d: r for d, r in rows.items() if r["alpaca_day_pl"] is not None or d not in cur})
        cur.pop("0000-00-00", None)
        accts[a] = dict(sorted(cur.items()))
    doc.update(asof=datetime.now(timezone.utc).isoformat(timespec="seconds"), disclaimer=DISCLAIMER,
               note="Broker truth per session: equity_close and alpaca_day_pl = equity_close - prior session's close. "
                    "source alpaca = Alpaca portfolio history; status_snapshot = last status.json of the session (approx.).")
    EQUITY_HISTORY.write_text(json.dumps(doc, indent=1) + "\n")
    return doc


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m mcf.report.reconcile_pl")
    p.add_argument("--date", default=datetime.now(ET).date().isoformat())
    p.add_argument("--account", action="append", choices=sorted(BRANCH))
    p.add_argument("--json")
    p.add_argument("--fyi", action="store_true", help="print only the one-line summary")
    p.add_argument("--no-fills", action="store_true")
    p.add_argument("--backfill", action="store_true")
    a = p.parse_args(argv)
    accts = a.account or list(BRANCH)
    if a.backfill:
        doc = backfill(accts)
        print(f"wrote {EQUITY_HISTORY.relative_to(ROOT)} ({', '.join(f'{k}: {len(v)}' for k, v in doc['accounts'].items())})")
        return 0
    rows = [reconcile(a.date, x, not a.no_fills) for x in accts]
    if a.json:
        Path(a.json).write_text(json.dumps({"rows": rows, "fyi": fyi(rows), "disclaimer": DISCLAIMER}, indent=1, default=str) + "\n")
    if a.fyi:
        print(fyi(rows))
        return 0
    for r in rows:
        f = r.get("fills") or {}
        print(f"{r['account']:9s} {r['date']} Alpaca {r['alpaca_day_pl']} ({r['source']}) · journal {r['journal_pnl']} "
              f"(adj {r['journal_pnl_adj']}, {r['journal_trades']} trades) · status {r['status_pnl']} · "
              + (f"fees {r['fees']:+.2f} · residual {r['residual']:+.2f} · " if r.get("fees") is not None else "")
              + ("OK" if r["ok"] else "FLAG: " + "; ".join(r["flags"])))
        for u in f.get("unmatched") or []:
            print(f"    fill mismatch {u['symbol']}: Alpaca {u['alpaca']:+.2f} journal {u['journal']:+.2f} ({u['diff']:+.2f})")
        for o in f.get("other") or []:
            print(f"    activity {o['type']} {o.get('symbol') or ''} {o['net_amount']:+.2f} {o.get('description') or ''}")
    print(fyi(rows))
    print(DISCLAIMER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
