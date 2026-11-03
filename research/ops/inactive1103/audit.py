"""Inactive-setups audit (owner 2026-11-03): sessions since each enabled setup's last signal / last trade, its
expected rate, the chance of its quiet streak, and why it is quiet. Read-only.

    python research/ops/inactive1103/audit.py <scratch>
      <scratch>/j/<branch>/journal.db   git show origin/<branch>:journal.db  (pulled 2026-11-03 ~11:05 ET)
      <scratch>/cfg/config/             git archive <last commit before 09:30 ET 11-03> config  (today's live set)

Enabled sessions come from each account's frozen setups/<day>.json (the runner's snapshot; it already reflects every
move / promotion), plus 11-03 from the pre-open config. A setup's quiet streak counts only completed sessions it was
enabled in, in that account (11-03 is in progress and only marks "active today").
Writes research/ops/inactive1103/table.csv and results.json. Educational only - not financial advice."""
from __future__ import annotations

import json
import math
import os
import sqlite3
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from mcf.config import _merge                                   # noqa: E402
from mcf.report.playing_time import classify, expected_rates     # noqa: E402

S = Path(sys.argv[1])
OUT = Path(__file__).resolve().parent
TODAY = "2026-11-03"
ACCTS = {"Primary": ("mcf-data", "primary"), "Testing 1": ("mcf-data-testing", "testing"),
         "Testing 2": ("mcf-data-testing2", "testing2"), "Graveyard": ("mcf-data-graveyard", "graveyard"),
         "Generated": ("mcf-data-gen", "gen")}


def git_show(br: str, path: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), "show", f"origin/{br}:{path}"], capture_output=True,
                          text=True).stdout


def cfg_today(acct: str) -> dict:
    d = S / "cfg" / "config"
    cfg = yaml.safe_load((d / "default.yaml").read_text())
    if acct != "primary":
        over = yaml.safe_load((d / f"account_{acct}.yaml").read_text()) or {}
        cfg = _merge(cfg, over)
        if over.get("strategies_exclusive"):
            own = set(over.get("strategies") or {})
            for k in list(cfg.get("strategies") or {}):
                if k not in own:
                    cfg["strategies"][k] = {**(cfg["strategies"][k] or {}), "enabled": False}
    return {k: cfg.get(k) for k in ("strategies", "exits", "shorts", "live", "universe")}


def on(s) -> bool:
    return isinstance(s, dict) and s.get("enabled", True) is not False


# ---------------------------------------------------------------- expected rates from research files
def walk(o, out: dict, src: str):
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, dict):
                for key in ("per_day", "trades_per_day", "per_session", "n_per_day"):
                    if isinstance(v.get(key), (int, float)) and isinstance(k, str) and len(k) > 3:
                        out.setdefault(k, (float(v[key]), src))
                        break
                walk(v, out, src)
    elif isinstance(o, list):
        for v in o:
            if isinstance(v, dict) and isinstance(v.get("name") or v.get("setup"), str):
                nm = v.get("name") or v.get("setup")
                for key in ("per_day", "trades_per_day", "per_session"):
                    if isinstance(v.get(key), (int, float)):
                        out.setdefault(nm, (float(v[key]), src))
                        break
            walk(v, out, src)


def research_rates() -> dict:
    out: dict = {}
    for p in sorted(ROOT.glob("research/**/verify*.json")) + sorted(ROOT.glob("research/**/expected*.json")):
        if p.stat().st_size > 5e6:
            continue
        try:
            walk(json.loads(p.read_text()), out, str(p.relative_to(ROOT)))
        except Exception:
            pass
    return out


def config_notes() -> dict:
    """'X/day' in an inline comment on the setup's setup_order line or in the comment block above its key."""
    import re
    rx, out = re.compile(r"([0-9]*\.?[0-9]+)\s*/\s*day"), {}
    for p in sorted((S / "cfg" / "config").glob("*.yaml")):
        lines = p.read_text().splitlines()
        for i, ln in enumerate(lines):
            m = re.match(r"^\s+- ([A-Za-z0-9_.\-]+)\s+#(.*)$", ln)
            if m and rx.search(m.group(2)):
                out.setdefault(m.group(1), (float(rx.search(m.group(2)).group(1)), f"config {p.name} order comment"))
            m = re.match(r"^  ([A-Za-z0-9_.\-]+):\s*$", ln)
            if m:
                j = i - 1
                while j >= 0 and lines[j].strip().startswith("#"):
                    if rx.search(lines[j]):
                        out.setdefault(m.group(1), (float(rx.search(lines[j]).group(1)), f"config {p.name} comment"))
                        break
                    j -= 1
    return out


# hand-read lab figures (2-year open history, ~480 sessions) for setups no machine-readable file covers
H = 480
MANUAL = {
    "IDX1-qqq100-0955-TQQQ-trail": (10 / H, 1 - 10 / H, "idxdip1015 NOTES: 10 dip days in 2y (1 trade/dip day)"),
    "IDX1-qqq100-0955-TQQQ-hold": (10 / H, 1 - 10 / H, "idxdip1015 NOTES: 10 dip days in 2y"),
    "IDX2-spy075-0945-3x-trail": (5 / H, 1 - 5 / H, "idxdip1015 NOTES: 5 dip days in 2y"),
    "IDX3-spy075-0955-3x-trail": (9 / H, 1 - 9 / H, "idxdip1015 NOTES: 9 dip days in 2y"),
    "IDX5-spy050-0945-3x-trail": (17 / H, 1 - 17 / H, "idxdip1015 NOTES: 17 dip days in 2y"),
    "NM-AR-AM-gapdown-capitulation-long": (1588 / H, None, "swarm1017 PROPOSED_CONFIG: n 741+847, clustered (half of train Apr 2025)"),
    "NM-AMS-N1-quiet-morning-short": (400 / H, None, "swarm1017 PROPOSED_CONFIG: n 194+206"),
    "NM-PM-gapdn-above-pdh-rvol-short": (447 / H, None, "swarm1017 PROPOSED_CONFIG: n 274+173, top-5 days 89% of train P/L"),
    "NM1-cwt09-g10-vwaploss-short": (241 / H, None, "swarm1017 PROPOSED_CONFIG: n 241"),
    "NM-HL-T75-pm-long": (1860 / H, None, "swarm1017 PROPOSED_CONFIG: n 1860"),
}
CN = config_notes()

GEN_EXP = json.loads((ROOT / "research/generator/expected_live.json").read_text()).get("setups", {})
RR = research_rates()


def expected(name: str, s: dict, ex: dict) -> tuple[float | None, float | None, str]:
    """(signals/session, share of sessions with 0 signals or None, source)."""
    c = GEN_EXP.get(name, {}).get("counts60")
    if c:
        return float(np.mean(c)), sum(1 for x in c if x == 0) / len(c), "generator screen, last 60 sessions"
    sc = ((s or {}).get("gen") or {}).get("screen") or {}
    a, pdy = sc.get("all") or {}, sc.get("per_day")
    if a.get("n") and pdy:
        return float(pdy), 1 - a["days"] / (a["n"] / pdy), "generator screen (all)"
    if name in MANUAL:
        return MANUAL[name]
    if name in ex:
        return ex[name]["per_day"], None, ex[name]["source"]
    if name in CN:
        return CN[name][0], None, CN[name][1]
    if name in RR:
        return RR[name][0], None, RR[name][1]
    base = name[:-3] if name.endswith("-FD") else None
    if base and base in RR:
        return RR[base][0], None, RR[base][1] + " (non-FD parent; FD runs a longer window)"
    return None, None, "none"


def p_quiet(rate, p0, n):
    """P(n quiet sessions in a row). With a zero-day share p0 (screen) it is p0**n; with a rate only, a clustered
    Poisson: signals come in days, so use P(0 in a day) = exp(-rate / 3) (a day with signals carries ~3 on
    average in the lab files, a conservative guess that makes rare-looking streaks less alarming than plain Poisson)."""
    if rate is None or n == 0:
        return None
    z = p0 if p0 is not None else math.exp(-rate / 3.0)
    return z ** n


rows = []
blocked_rows = []
for acct, (br, key) in ACCTS.items():
    c = sqlite3.connect(S / "j" / br / "journal.db")
    sig = pd.read_sql("select id, day, ts, symbol, strategy, side, status, reason, info from signals where run_id=1", c)
    tr = pd.read_sql("select strategy, date, r_multiple from trades where run_id=1", c)
    wi = pd.read_sql("select strategy, date, symbol, signal_time, r_multiple, entry, stop, exit, exit_reason, meta "
                     "from trades where run_id=2", c)
    sig["bucket"] = [classify(a, b) for a, b in zip(sig.status, sig.reason)]
    files = [Path(f).stem for f in subprocess.run(["git", "-C", str(ROOT), "ls-tree", "--name-only", f"origin/{br}",
                                                    "setups/"], capture_output=True, text=True).stdout.split()]
    snaps = {d: json.loads(git_show(br, f"setups/{d}.json") or "{}") for d in files}
    snaps[TODAY] = cfg_today(key)
    days = sorted(snaps)
    done = [d for d in days if d < TODAY]
    cur = snaps[TODAY]["strategies"]
    order = (snaps[TODAY].get("live") or {}).get("setup_order") or []
    ex = expected_rates(key)
    per = sig.groupby(["strategy", "day"]).size()
    for name, s in cur.items():
        if not on(s):
            continue
        en = [d for d in done if on((snaps[d].get("strategies") or {}).get(name))]
        # the current enabled run: consecutive enabled sessions ending at the last completed session
        run = []
        for d in reversed(done):
            if on((snaps[d].get("strategies") or {}).get(name)):
                run.append(d)
            else:
                break
        run = run[::-1]
        first = run[0] if run else TODAY
        ss = sig[(sig.strategy == name) & (sig.day >= first)]
        st = tr[(tr.strategy == name) & (tr.date >= first)]
        sd = sorted(ss.day.unique())
        tdays = sorted(set(st.date) | set(ss[ss.bucket == "taken"].day))
        last_sig = max([d for d in sd if d < TODAY], default=None)
        last_tr = max([d for d in tdays if d < TODAY], default=None)
        q_sig = len([d for d in run if last_sig is None or d > last_sig])
        q_tr = len([d for d in run if last_tr is None or d > last_tr])
        today_sig = int((ss.day == TODAY).sum())
        today_tr = int(((ss.day == TODAY) & (ss.bucket == "taken")).sum())
        rate, p0, src = expected(name, s, ex)
        n_run = len(run)
        live_sig = len(ss[ss.day < TODAY])
        zero_days = sum(1 for d in run if per.get((name, d), 0) == 0)
        prior = [d for d in run if last_sig and d <= last_sig]
        p0_live = (sum(1 for d in prior if per.get((name, d), 0) == 0) + 1) / (len(prior) + 2) if run else None
        pq = p_quiet(rate, p0, q_sig)
        pq_live = p0_live ** q_sig if (p0_live is not None and q_sig) else None
        if today_sig:
            bucket = "active today"
        elif live_sig == 0:
            bucket = "never fired since enabled" if n_run else "new today"
        elif q_sig == 0:
            bucket = "fired last session"
        elif q_sig <= 2:
            bucket = "quiet 1-2"
        elif q_sig <= 4:
            bucket = "quiet 3-4"
        else:
            bucket = "quiet 5+"
        # block mix of the current enabled run, and of the quiet streak's what-if
        bk = Counter(ss[ss.day < TODAY].bucket)
        wis = wi[(wi.strategy == name) & (wi.date >= first) & (wi.date < TODAY)]
        R = (wis.entry - wis.stop).abs()
        cps = (0.01 + wis.entry * 1e-4) + np.where(wis.exit_reason == "target", 0.0, 0.01 + wis.exit * 1e-4) \
            + np.where(wis.exit_reason == "stop", 0.02, 0.0)
        wnet = (wis.r_multiple - np.where(R > 0, cps / R, 0.0)).sum() if len(wis) else 0.0
        trs = st[st.date < TODAY]
        rows.append(dict(
            account=acct, setup=name, type=s.get("type", "rule"), order_pos=(order.index(name) + 1) if name in order else None,
            first_session=first, sessions_enabled=n_run, enabled_any_account_sessions=len(en),
            signals=live_sig, signals_per_session=round(live_sig / n_run, 2) if n_run else None,
            trades=len(trs), trades_per_session=round(len(trs) / n_run, 2) if n_run else None,
            live_R=round(trs.r_multiple.sum(), 2) if len(trs) else 0.0,
            zero_signal_sessions=zero_days,
            last_signal=last_sig, quiet_sessions_signal=q_sig, last_trade=last_tr, quiet_sessions_trade=q_tr,
            today_signals=today_sig, today_taken=today_tr, bucket=bucket,
            exp_per_session=round(rate, 2) if rate is not None else None,
            exp_zero_share=round(p0, 3) if p0 is not None else None, exp_source=src,
            p_quiet_exp=round(pq, 4) if pq is not None else None,
            p_quiet_live=round(pq_live, 4) if pq_live is not None else None,
            taken=bk.get("taken", 0), held_by_other=bk.get("held_by_other", 0), slots_full=bk.get("slots_full", 0),
            setup_cap=bk.get("setup_cap", 0), daily_loss=bk.get("daily_loss", 0), borrow=bk.get("borrow", 0),
            realism=bk.get("realism", 0), window=bk.get("window", 0), rejected=bk.get("rejected", 0),
            other=bk.get("other", 0), missed_trigger=bk.get("missed_trigger", 0), split_gate=bk.get("split_gate", 0),
            whatif_n=len(wis), whatif_net_R=round(float(wnet), 2),
            window_cfg=str(s.get("window")), min_adv=s.get("min_adv"), context=str(s.get("context")) if s.get("context") else "",
            module=s.get("module") or "", module_exists=(ROOT / s["module"]).exists() if s.get("module") else None,
        ))
        # "other" reasons of this setup for the diagnosis
        for r, n in Counter(ss[(ss.day < TODAY) & (ss.bucket != "taken")].reason.fillna("")
                            .str.replace(r"[0-9.]+", "#", regex=True)).most_common(6):
            blocked_rows.append(dict(account=acct, setup=name, reason=r, n=n))

df = pd.DataFrame(rows)
df.to_csv(OUT / "table.csv", index=False)
pd.DataFrame(blocked_rows).to_csv(S / "reasons.csv", index=False)
print(df.groupby(["account", "bucket"]).size().unstack(fill_value=0))
print(df.bucket.value_counts())
print("no expected rate:", (df.exp_source == "none").sum())
print(df[df.exp_source == "none"][["account", "setup"]].to_string())
