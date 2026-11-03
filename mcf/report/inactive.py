"""Nightly inactive-setups check (owner INACT1 / INACT2, 2026-11-03) for the 19:17 owner brief.

INACT1: runs research/ops/inactive1103/audit.py on fresh journals (git show origin/<data branch>:journal.db) and the
current config, then writes ONE FYI line a night to research/owner_inbox/<date>.md. The P-rule (fixed before any table
was read): a setup is on WATCH when P(its quiet streak | its expected signal rate) < 5%, on ALARM when < 1%; setups
gated on an index move (SPY/QQQ in the name) are exempt. A DECISION is written only when a fix needs the owner: an
alarm whose cause is a block the owner controls (place in line, caps, buying power, cost filters). Broken / unexplained
alarms are housekeeping (Claude checks them; listed in the FYI line).
INACT2: rare setups are judged on trade COUNT (60 trades), not sessions. `verdicts()` lists, per enabled setup under 3
trades a session, how many more sessions it needs to reach 60 trades at its live rate (expected rate when it has no
live trades yet). Weekly (Mondays, or --weekly): research/ops/inactive/verdicts_<date>.md + one FYI line.

    python -m mcf.report.inactive --date 2026-11-03 --next 2026-11-04 [--inbox] [--weekly]
Report only: it never changes a setup. Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import math
import os
import subprocess
import sys
import tempfile
from datetime import date as _date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "research" / "ops" / "inactive1103" / "audit.py"
INBOX = ROOT / "research" / "owner_inbox"
VERDICT_DIR = ROOT / "research" / "ops" / "inactive"
BRANCHES = ("mcf-data", "mcf-data-testing", "mcf-data-testing2", "mcf-data-graveyard", "mcf-data-gen")
WATCH_P, ALARM_P = 0.05, 0.01
VERDICT_TRADES = 60
RARE_PER_SESSION = 3.0
OWNER_BLOCKS = ("blocked: place in line", "blocked: buying power", "blocked: spread / cost filter")
DISCLAIMER = "Educational only - not financial advice."


def index_gated(setup: str, gate: str | float | None = None) -> bool:
    if isinstance(gate, str) and gate.strip():
        return True
    import re

    return bool(re.search(r"(SPY|QQQ)(gt|ltm)\d+p\d+|(spy|qqq|QQQ)up", setup))


def flags(df: pd.DataFrame) -> pd.DataFrame:
    """Adds `level` (alarm / watch / '') with the P-rule and the index-gate exemption."""
    out = df.copy()
    p = pd.to_numeric(out.get("p_quiet_exp"), errors="coerce")
    exempt = [index_gated(s, g) for s, g in zip(out["setup"], out.get("gate", [None] * len(out)))]
    out["level"] = ["" if ex or pd.isna(x) else "alarm" if x < ALARM_P else "watch" if x < WATCH_P else ""
                    for x, ex in zip(p, exempt)]
    return out


def summarize(df: pd.DataFrame, day: str) -> dict:
    """One FYI line, plus a DECISION only when an alarm needs the owner."""
    f = flags(df)
    al, wa = f[f.level == "alarm"], f[f.level == "watch"]
    causes = f.get("cause", pd.Series([""] * len(f))).fillna("")
    broken = f[causes.str.startswith("broken")]
    quiet5 = int((pd.to_numeric(f.get("quiet_sessions_signal"), errors="coerce") >= 5).sum())
    names = lambda d: ", ".join(f"{r.setup} ({r.account}, {int(r.quiet_sessions_signal)} quiet, P {r.p_quiet_exp:.1%})"
                                for r in d.itertuples())[:400]
    fyi = (f"inactive-check | {len(f)} enabled setups; quiet 5+ sessions: {quiet5}; "
           f"alarm (P<1%): {len(al)}; watch (P<5%): {len(wa)}; index-gated exempt; broken: {len(broken)}"
           + (f" | alarm: {names(al)}" if len(al) else "") + (f" | watch: {names(wa)}" if len(wa) else ""))
    need = al[causes.loc[al.index].str.startswith(OWNER_BLOCKS)] if len(al) else al
    dec = None
    if len(need):
        r = need.iloc[0]
        dec = (f"inactive-check | {r.setup} ({r.account}) has not signalled/traded for {int(r.quiet_sessions_signal)} sessions "
               f"(P {r.p_quiet_exp:.2%} at its expected rate) - {r.cause}; change its place in line / cap?"
               + (f" (+{len(need) - 1} more)" if len(need) > 1 else ""))
    return {"date": day, "fyi": fyi, "decision": dec, "alarm": al.setup.tolist(), "watch": wa.setup.tolist()}


def verdicts(df: pd.DataFrame, n: int = VERDICT_TRADES) -> pd.DataFrame:
    """INACT2: sessions each rare setup (< 3 trades a session) still needs to reach n trades."""
    rows = []
    for r in df.itertuples():
        live = getattr(r, "trades_per_session", None)
        exp = getattr(r, "exp_per_session", None)
        rate = live if live == live and live else exp
        if rate is None or rate != rate:
            rate = None
        if rate is not None and rate >= RARE_PER_SESSION:
            continue
        have = int(getattr(r, "trades", 0) or 0)
        left = max(0, n - have)
        need = math.ceil(left / rate) if rate else None
        rows.append({"account": r.account, "setup": r.setup, "trades": have, "per_session": rate,
                     "rate_from": "live" if rate is not None and rate == live else "expected" if rate else "none",
                     "sessions_enabled": int(getattr(r, "sessions_enabled", 0) or 0), "sessions_to_verdict": need})
    out = pd.DataFrame(rows, columns=["account", "setup", "trades", "per_session", "rate_from", "sessions_enabled",
                                      "sessions_to_verdict"])
    return out.sort_values("sessions_to_verdict", na_position="last", ascending=False).reset_index(drop=True)


def verdict_md(v: pd.DataFrame, day: str) -> str:
    lines = [DISCLAIMER, "", f"# Sessions to verdict - rare setups judged on {VERDICT_TRADES} trades ({day})", "",
             "INACT2 (owner 2026-11-03): setups under 3 trades a session are judged on trade count, not on 20 sessions. "
             "Sessions to verdict = (60 - trades so far) / trades per session (live rate; expected rate before the first trade). "
             "Trimmed low-activity setups move to a testing account (Explore 1 when it opens), never just switched off.", "",
             "| Account | Setup | Trades | Per session | Rate from | Sessions enabled | Sessions to verdict |",
             "|---|---|---|---|---|---|---|"]
    for r in v.itertuples():
        ps = "-" if r.per_session is None or r.per_session != r.per_session else f"{r.per_session:.2f}"
        sv = "-" if r.sessions_to_verdict is None or r.sessions_to_verdict != r.sessions_to_verdict else str(int(r.sessions_to_verdict))
        lines.append(f"| {r.account} | `{r.setup}` | {r.trades} | {ps} | {r.rate_from} | {r.sessions_enabled} | {sv} |")
    return "\n".join(lines) + "\n"


def verdict_fyi(v: pd.DataFrame, day: str) -> str:
    s = pd.to_numeric(v.sessions_to_verdict, errors="coerce")
    return (f"inactive-check (weekly) | {len(v)} rare setups judged on {VERDICT_TRADES} trades; over 100 sessions to verdict: "
            f"{int((s > 100).sum())}; no rate yet: {int(s.isna().sum())}; median {s.median():.0f} sessions"
            f" -> research/ops/inactive/verdicts_{day}.md")


def append_inbox(day: str, items: list[tuple[str, str]], inbox: Path = INBOX) -> Path:
    """items: [("FYI" | "DECISION", text)] appended to research/owner_inbox/<day>.md (owner_inbox/README.md format)."""
    p = inbox / f"{day}.md"
    old = p.read_text() if p.exists() else f"{DISCLAIMER}\n\n# Owner inbox {day}\n"
    add = ""
    for kind, text in items:
        line = f"## {kind} | {text}"
        if line not in old:
            add += "\n" + line + ("\nReply: \"INACT yes\" / \"INACT no\"\n" if kind == "DECISION" else "\n")
    p.write_text(old.rstrip("\n") + "\n" + add if add else old)
    return p


def run_audit(next_session: str, scratch: Path) -> pd.DataFrame:
    """Fresh journals + current config into `scratch`, then audit.py; returns its table."""
    for br in BRANCHES:
        d = scratch / "j" / br
        d.mkdir(parents=True, exist_ok=True)
        with open(d / "journal.db", "wb") as f:
            subprocess.run(["git", "-C", str(ROOT), "show", f"origin/{br}:journal.db"], stdout=f, check=True)
    (scratch / "cfg").mkdir(parents=True, exist_ok=True)
    subprocess.run(f"git -C {ROOT} archive HEAD config | tar -x -C {scratch / 'cfg'}", shell=True, check=True)
    env = dict(os.environ, MCF_INACTIVE_OUT=str(scratch / "out"),
               MCF_INACTIVE_ASOF=f"nightly; completed sessions before {next_session}")
    subprocess.run([sys.executable, str(AUDIT), str(scratch), next_session], check=True, env=env, cwd=ROOT,
                   stdout=subprocess.DEVNULL)
    return pd.read_csv(scratch / "out" / "table.csv")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=str(_date.today()), help="the session just closed (inbox file date)")
    ap.add_argument("--next", required=True, help="the next session date (audit counts sessions before it)")
    ap.add_argument("--table", help="use an existing audit table.csv instead of running the audit")
    ap.add_argument("--inbox", action="store_true", help="append the FYI / DECISION to research/owner_inbox/<date>.md")
    ap.add_argument("--weekly", action="store_true", help="also write the INACT2 sessions-to-verdict list (default: Mondays)")
    a = ap.parse_args(argv)
    if a.table:
        df = pd.read_csv(a.table)
    else:
        with tempfile.TemporaryDirectory() as t:
            df = run_audit(a.next, Path(t))
    s = summarize(df, a.date)
    items = [("FYI", s["fyi"])] + ([("DECISION", s["decision"])] if s["decision"] else [])
    if a.weekly or _date.fromisoformat(a.date).weekday() == 0:
        v = verdicts(df)
        VERDICT_DIR.mkdir(parents=True, exist_ok=True)
        (VERDICT_DIR / f"verdicts_{a.date}.md").write_text(verdict_md(v, a.date))
        items.append(("FYI", verdict_fyi(v, a.date)))
    for k, t in items:
        print(f"{k}: {t}")
    if a.inbox:
        append_inbox(a.date, items)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
