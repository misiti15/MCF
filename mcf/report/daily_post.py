"""Daily message-board post images (owner 2026-10-24).

Four PNGs + the post text and quick-facts text per session, built from the same data the dashboard reads (each data branch's status.json
and reports/scorecard.json, docs/live/assignments.json / setup_names.json / regimes.json). Day-trading accounts only
(the long-hold S6 account is left out, owner 2026-10-25):

  1-today.png         EOD balance, today's and since-start P/L per account, the owner's milestones (M1: Primary 3 green
                      days in a row; M2: 8 green of the last 10), cumulative P/L chart, last-5-sessions table - all from Day 1 (DAY1)
  2-top2.png          the day's top two setups explained in plain words (words from --top2 JSON, written by Claude each
                      night; without it the setup's own one-line description is used)
  3-leaderboard.png   setup leaderboard, top 10 (all accounts merged, Setup Generator excluded), same columns and rank as
                      the dashboard
  4-generator.png     generated setups leaderboard (Setup Generator account), top 10
  facts.txt           'Quick facts' (numbers) + 'Quick answers' (common questions), paste-ready text - owner 2026-10-26
  post.txt            the short post text (owner's template) incl. the "changes before today's open" line

    python -m mcf.report.daily_post --date 2026-10-23 [--top2 research/posts/2026-10-23.json] [--out docs/posts]

The --top2 file: {"setups": [{"setup": "<id>", "title": "...", "lines": [["When", "..."], ["Trigger", "..."], ...]}, ...]}.
Rendering uses headless Chromium (Playwright). Paper results. Educational only — not financial advice.
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACCOUNTS = [("primary", "Primary", "mcf-data", "promoted setups"), ("testing", "Testing 1", "mcf-data-testing", "testing"),
            ("testing2", "Testing 2", "mcf-data-testing2", "testing"), ("gen", "Setup Generator", "mcf-data-gen", "machine-generated setups"),
            ("graveyard", "Graveyard", "mcf-data-graveyard", "lowest performers")]   # day-trading only (no S6)
MILESTONES = (("M1", "3 green days in a row (Primary)"), ("M2", "8 green days out of the last 10 (Primary)"))
DAY1 = "2026-10-23"   # owner 2026-10-26: the post's stats (P/L, milestones, chart, last sessions) start at Day 1
LB_ACCOUNTS = ("primary", "testing", "testing2", "graveyard")
CHROME = ["/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell", "/opt/pw-browsers/chromium"]


def _show(branch: str, path: str):
    """A JSON file from a data branch (origin/<branch>), or None."""
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "show", f"origin/{branch}:{path}"], capture_output=True, check=True)
        return json.loads(out.stdout)
    except Exception:
        return None


def _local(path: str):
    p = ROOT / path
    return json.loads(p.read_text()) if p.exists() else None


def fetch():
    subprocess.run(["git", "-C", str(ROOT), "fetch", "-q", "origin"] + [b for _, _, b, _ in ACCOUNTS], check=False)


# ---------------------------------------------------------------- data
def accounts(date: str, since: str = DAY1) -> list[dict]:
    """Per account: balance (actual), today's P/L, and P/L + history from `since` (Day 1) on; full_history keeps all."""
    out = []
    for k, name, br, kind in ACCOUNTS:
        s = _show(br, "status.json") or {}
        t, ss = s.get("today") or {}, s.get("since_start") or {}
        if s.get("session_date") != date:
            t = next((h for h in s.get("history") or [] if h.get("date") == date), {})
        full = s.get("history") or []
        hist = [h for h in full if since <= h.get("date", "") <= date]
        out.append(dict(k=k, name=name, kind=kind, equity=(s.get("account") or {}).get("equity"), today=t.get("pnl"),
                        trades=t.get("trades"), since=sum((h.get("pnl") or 0) for h in hist),
                        history=hist, full_history=full))
    return out


def _sessions(primary: dict, date: str) -> list[dict]:
    return [x for x in primary.get("history", []) if x.get("date", "") <= date and x.get("trades")]


def milestones(primary: dict, date: str) -> dict:
    """M1 (3 green in a row) and M2 (8 green of the last 10) on Primary's daily P/L (paper fills, as the balance)."""
    h = _sessions(primary, date)
    run = streak(primary, date)[0]
    best, cur = 0, 0
    for x in h:
        cur = cur + 1 if (x.get("pnl") or 0) > 0 else 0
        best = max(best, cur)
    last10 = h[-10:]
    g10 = sum((x.get("pnl") or 0) > 0 for x in last10)
    return dict(run=run, best_run=best, m1=best >= 3, g10=g10, n10=len(last10), m2=len(last10) == 10 and g10 >= 8,
                dots=[(x["date"], (x.get("pnl") or 0) > 0) for x in last10])


def streak(primary: dict, date: str) -> tuple[int, int, int]:
    """(green days in a row ending at date, green days, sessions) from Primary's daily history (P/L as the dashboard)."""
    h = [x for x in primary.get("history", []) if x.get("date", "") <= date and x.get("trades")]
    run = 0
    for x in reversed(h):
        if (x.get("pnl") or 0) > 0:
            run += 1
        else:
            break
    return run, sum((x.get("pnl") or 0) > 0 for x in h), len(h)


def _merge(rows: list[dict]) -> dict:
    """All accounts' scorecard rows of one setup -> one record (same sums as the dashboard)."""
    if len(rows) == 1:
        return dict(rows[0])
    s = lambda k: sum((r.get(k) or 0) for r in rows)
    n, w = s("trades"), s("n_win")
    avg = s("total_r") / n if n else None
    var = (s("r_sq_sum") - n * avg * avg) / (n - 1) if n > 1 else 0
    aw = s("win_r_sum") / w if w else None
    al = s("loss_r_sum") / (n - w) if n - w else None
    days = sorted({d for r in rows for d in r.get("days") or []})
    daily: dict = {}
    for r in rows:
        for d, c, rr, p in r.get("daily") or []:
            a = daily.setdefault(d, [0, 0.0, 0.0])
            a[0] += c; a[1] += rr; a[2] += p
    return dict(rows[0], trades=n, n_win=w, win_rate=w / n if n else None, avg_r=avg, total_r=s("total_r"), pnl=s("pnl"),
                t_stat=(avg / (var / n) ** 0.5) if n and var > 0 else None,
                breakeven_wr=(al / (aw + al)) if aw and al else None, sessions_traded=len(days) or None,
                profit_factor=(s("win_pnl") / s("loss_pnl")) if s("loss_pnl") else None,
                daily=[[d, *v] for d, v in sorted(daily.items())], recent_avg_r=None)


def best_day(r: dict) -> tuple:
    """(avg R without the single best session, best session date, its share of total R) - owner 2026-10-25."""
    by: dict = {}
    for d, c, rr, _ in r.get("daily") or []:
        a = by.setdefault(d, [0, 0.0]); a[0] += c; a[1] += rr
    if len(by) < 2:
        return None, None, None
    d, (bn, br) = max(by.items(), key=lambda kv: kv[1][1])
    n, tot = r.get("trades") or 0, r.get("total_r") or 0.0
    return ((tot - br) / (n - bn) if n - bn > 0 else None), d, (br / tot if tot > 0 and br > 0 else None)


def _last4(r: dict, sessions: list[str]):
    d = [x for x in r.get("daily") or [] if x[0] in sessions]
    n = sum(x[1] for x in d)
    return sum(x[2] for x in d) / n if n else None


def _day(r: dict, date: str):
    return next((x for x in r.get("daily") or [] if x[0] == date), None)


def leaderboard(date: str, gen: bool = False, top: int = 10) -> list[dict]:
    asg = (_local("docs/live/assignments.json") or {}).get("setups", {})
    names = _local("docs/live/setup_names.json") or {}
    reg = (_local("docs/live/regimes.json") or {}).get("setups", {})
    accts = ("gen",) if gen else LB_ACCOUNTS
    by: dict[str, list] = {}
    sessions: set = set()
    for k in accts:
        sc = _show(dict((a, b) for a, _, b, _ in ACCOUNTS)[k], "reports/scorecard.json") or {}
        for r in sc.get("leaderboard") or []:
            if gen != r["setup"].startswith("GEN-"):
                continue
            by.setdefault(r["setup"], []).append(r)
            sessions.update(r.get("days") or [])
    last4 = sorted(d for d in sessions if d <= date)[-4:]
    rows = []
    for code, rs in by.items():
        a = asg.get(code) or {}
        if not a.get("accounts"):        # "Live setups" view: only setups enabled somewhere now
            continue
        r = _merge(rs)
        n = r.get("trades") or 0
        if not n:
            continue
        nm = names.get(code) or names.get(code[:-3] if code.endswith("-FD") else code) or {}
        ls = _day(r, date)
        rows.append(dict(setup=code, name=nm.get("name") or r.get("name") or code,
                         acct=" + ".join({"primary": "Primary", "testing": "Testing 1", "testing2": "Testing 2", "gen": "Setup Generator",
                                          "graveyard": "Graveyard"}.get(x, x) for x in a["accounts"]),
                         best=(reg.get(code) or {}).get("best"), ls_n=ls[1] if ls else None, ls_r=ls[2] if ls else None,
                         ls_pnl=ls[3] if ls else None, trades=n, sessions=r.get("sessions_traded"), per_day=(n / r["sessions_traded"]) if r.get("sessions_traded") else None,   # trades per session it traded
                         win=r.get("win_rate"), be=r.get("breakeven_wr"), avg_r=r.get("avg_r"), exbest=best_day(r), t=r.get("t_stat"),
                         total_r=r.get("total_r"), pnl=r.get("pnl"), pf=r.get("profit_factor"),
                         last4=r.get("recent_avg_r") if len(rs) == 1 and r.get("recent_avg_r") is not None else _last4(r, last4),
                         screen=((nm.get("screen") or {}).get("train_exp_r"), (nm.get("screen") or {}).get("valid_exp_r")),
                         rank_score=(r.get("avg_r") or 0) * n / (n + 20)))
    rows.sort(key=lambda x: -x["rank_score"])
    for i, x in enumerate(rows, 1):
        x["rank"] = i
    return rows[:top]


def top_of_day(date: str, n: int = 2) -> list[dict]:
    """The day's best setups by P/L across all intraday accounts (setups merged across accounts)."""
    names = _local("docs/live/setup_names.json") or {}
    agg: dict[str, dict] = {}
    for k, label, br, _ in ACCOUNTS[:5]:
        for r in (_show(br, "reports/scorecard.json") or {}).get("leaderboard") or []:
            d = _day(r, date)
            if not d:
                continue
            a = agg.setdefault(r["setup"], dict(setup=r["setup"], trades=0, r=0.0, pnl=0.0, accts=[]))
            a["trades"] += d[1]; a["r"] += d[2]; a["pnl"] += d[3]; a["accts"].append(label)
    if not agg:      # EOD scorecards not built yet: today's closed trades from each account's live status.json
        for k, label, br, _ in ACCOUNTS[:5]:
            st = _show(br, "status.json") or {}
            if st.get("session_date") != date:
                continue
            for c in st.get("closed") or []:
                a = agg.setdefault(c["strategy"], dict(setup=c["strategy"], trades=0, r=0.0, pnl=0.0, accts=[]))
                a["trades"] += 1; a["r"] += c.get("r") or 0.0; a["pnl"] += c.get("pnl") or 0.0
                if label not in a["accts"]:
                    a["accts"].append(label)
    out = sorted(agg.values(), key=lambda x: -x["pnl"])[:n]
    for x in out:
        nm = names.get(x["setup"]) or {}
        x["name"], x["what"], x["side"] = nm.get("name") or x["setup"], nm.get("what") or "", nm.get("side")
    return out


def green_streaks(date: str, accts: list[dict], min_run: int = 3) -> dict:
    """Owner 2026-10-26: per setup (all 5 accounts merged), green days = sessions with P/L > 0 after paper fills.
    current: setups green on each of the last N market sessions (N >= min_run, a day not traded breaks the streak);
    record: the longest such run any setup has had. Market sessions = days any account traded (all history)."""
    sessions = sorted({x["date"] for a in accts for x in a.get("full_history") or a.get("history") or []
                       if x.get("date", "") <= date and x.get("trades")})
    names = _local("docs/live/setup_names.json") or {}
    by: dict[str, list] = {}
    for k, _, br, _ in ACCOUNTS:
        for r in (_show(br, "reports/scorecard.json") or {}).get("leaderboard") or []:
            by.setdefault(r["setup"], []).append(r)
    cur, rec = [], []
    for s, rows in by.items():
        d = {x[0]: x for x in _merge(rows).get("daily") or []}
        green = [bool(x in d and d[x][1] and d[x][3] > 0) for x in sessions]
        run = 0
        for g in reversed(green):
            if not g:
                break
            run += 1
        best, c, end = 0, 0, None
        for i, g in enumerate(green):
            c = c + 1 if g else 0
            if c > best:
                best, end = c, i
        nm = (names.get(s) or {}).get("name") or s
        if run >= min_run:
            cur.append(dict(setup=s, name=nm, run=run, pnl=sum(d[x][3] for x in sessions[-run:])))
        if best:
            rec.append(dict(setup=s, name=nm, run=best, start=sessions[end - best + 1], end=sessions[end]))
    cur.sort(key=lambda x: (-x["run"], -x["pnl"]))
    rec.sort(key=lambda x: (x["run"], x["end"]), reverse=True)
    top = rec[0]["run"] if rec else 0
    return dict(current=cur, record=[x for x in rec if x["run"] == top], sessions=len(sessions))


def _streak_lines(gs: dict, limit: int = 6) -> list[str]:
    out = ["Green-day streaks (setups green every session in a row, all accounts)"]
    if gs["current"]:
        out += [f"- {x['name']}: {x['run']} in a row ({_money(x['pnl'])})" for x in gs["current"][:limit]]
        if len(gs["current"]) > limit:
            out.append(f"- +{len(gs['current']) - limit} more")
    else:
        out.append("- None at 3+ sessions in a row")
    if gs["record"]:
        r = gs["record"]
        out.append(f"Green-day record: {r[0]['run']} sessions in a row - " +
                   "; ".join(f"{x['name']} ({x['start'][5:]}..{x['end'][5:]})" for x in r[:3]) +
                   (f" (+{len(r) - 3} tied)" if len(r) > 3 else ""))
    return out


def facts(accts: list[dict]) -> dict:
    """Live counts for the quick-facts card."""
    asg = (_local("docs/live/assignments.json") or {}).get("setups", {})
    live = [k for k, v in asg.items() if v.get("accounts")]
    gen = [k for k in live if "gen" in asg[k]["accounts"]]
    lab = _local("docs/live/generator_lab.json") or {}
    rejected = 0
    p = ROOT / "research" / "backlog.jsonl"
    if p.exists():
        st = [json.loads(l).get("status") for l in p.read_text().splitlines() if l.strip()]
        rejected = sum(x in ("failed", "holdout_failed", "failed_locked", "rework") for x in st)
    rejected += max(0, (lab.get("specs_screened") or 0) - (lab.get("setups_generated") or 0))
    slip, n = 0.0, 0
    for k, _, br, _ in ACCOUNTS:
        ss = (_show(br, "status.json") or {}).get("since_start") or {}
        if ss.get("avg_entry_slip_bps") is not None and ss.get("trades"):
            slip += ss["avg_entry_slip_bps"] * ss["trades"]; n += ss["trades"]
    pr = next(a for a in accts if a["k"] == "primary")
    return dict(live=len(live) - len(gen), gen=len(gen), rejected=rejected, slip=(slip / n if n else None), trades=n,
                sessions=len([x for x in pr.get("full_history") or [] if x.get("trades")]),
                start=(pr.get("full_history") or [{}])[0].get("date"))


# ---------------------------------------------------------------- render
CSS = """
*{box-sizing:border-box} body{margin:0;background:#f7f7f5;font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#1b1b1b}
.wrap{width:1200px;padding:22px 24px 10px}
h1{font-size:22px;margin:0 0 2px} .sub{color:#666;font-size:13px;margin-bottom:14px}
.card{background:#fff;border:1px solid #e3e3e0;border-radius:12px;padding:14px 16px;margin-bottom:12px}
.card h2{font-size:15px;margin:0 0 10px}
.accts{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}
.acc{border:1px solid #e3e3e0;border-radius:10px;padding:9px 10px} .acc .n{font-weight:600;font-size:13px}
.acc .ty{font-size:10.5px;color:#888} .acc .eq{font-size:19px;font-weight:650;margin:3px 0;font-variant-numeric:tabular-nums}
.acc .ln{font-size:11.5px;color:#444;font-variant-numeric:tabular-nums}
.up{color:#15803d} .down{color:#b91c1c}
.strip{display:flex;gap:28px;font-size:13px;margin-top:10px;color:#333} .strip b{font-size:15px}
.top2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.ts{border:1px solid #e3e3e0;border-radius:10px;padding:11px 13px} .ts .t{font-weight:650;font-size:14.5px}
.ts .st{font-size:12px;color:#444;margin:3px 0 7px;font-variant-numeric:tabular-nums} .ts .id{font-size:10.5px;color:#888;word-break:break-all}
.ts table{width:100%;border-collapse:collapse;font-size:12.5px} .ts td{padding:3px 4px;vertical-align:top;border-top:1px solid #f0f0ee}
.ts td.k{width:84px;font-weight:600;color:#555;white-space:nowrap}
.side{display:inline-block;font-size:10px;font-weight:700;padding:1px 6px;border-radius:999px;border:1px solid currentColor;margin-left:6px;vertical-align:2px}
.lb{width:100%;border-collapse:collapse;font-size:12px;font-variant-numeric:tabular-nums}
.lb th{font-size:11px;color:#555;text-align:right;padding:5px 4px;max-width:66px;white-space:normal;border-bottom:1px solid #ddd;vertical-align:bottom;line-height:1.2}
.lb td{padding:5px 4px;text-align:right;border-bottom:1px solid #eee;white-space:nowrap}
.lb .l{text-align:left} .lb th.l{max-width:none} .lb .nm{max-width:215px;overflow:hidden;text-overflow:ellipsis} .lb .nm div{font-size:10.5px;color:#888;overflow:hidden;text-overflow:ellipsis}
.lb .ls{background:#eef3fb} .chip{display:inline-block;font-size:10.5px;padding:0 6px;border-radius:6px;border:1px solid #ccc;color:#444}
.chip.Bear{color:#b91c1c;border-color:#b91c1c} .chip.Bull{color:#15803d;border-color:#15803d} .chip.Choppy{color:#b45309;border-color:#b45309}
.gen{border-color:#c4b5fd;background:#faf8ff} .gb{display:inline-block;font-size:9.5px;font-weight:700;color:#fff;background:#7c3aed;border-radius:4px;padding:1px 5px;margin-right:5px;vertical-align:1px}
.foot{font-size:9px;color:#999;text-align:center;padding:4px 0 8px}
.accts5{grid-template-columns:repeat(5,1fr)}
.two{display:grid;grid-template-columns:1.25fr 1fr;gap:12px}
.ms{display:grid;grid-template-columns:1fr 1fr;gap:12px} .m{border:1px solid #e3e3e0;border-radius:10px;padding:10px 12px}
.m .t{font-weight:650;font-size:13.5px} .m .v{font-size:22px;font-weight:700;margin:2px 0;font-variant-numeric:tabular-nums}
.m .d{font-size:11.5px;color:#666} .dots{display:flex;gap:4px;margin-top:6px} .dot{width:16px;height:16px;border-radius:50%;background:#e5e5e2}
.dot.g{background:#16a34a} .dot.r{background:#dc2626} .done{color:#15803d;font-size:11px;font-weight:700;margin-left:6px}
.t5{width:100%;border-collapse:collapse;font-size:12.5px;font-variant-numeric:tabular-nums} .t5 th{font-size:11px;color:#555;text-align:right;padding:4px;border-bottom:1px solid #ddd}
.t5 td{padding:4px;text-align:right;border-bottom:1px solid #eee} .t5 .l{text-align:left}
.leg{display:flex;flex-wrap:wrap;gap:10px;font-size:11px;color:#444;margin-top:4px} .leg i{display:inline-block;width:12px;height:3px;margin-right:4px;vertical-align:3px}
.facts{display:grid;grid-template-columns:1fr 1fr;gap:12px} .fb{border:1px solid #e3e3e0;border-radius:10px;padding:10px 13px}
.fb h3{font-size:13.5px;margin:0 0 6px} .fb table{width:100%;border-collapse:collapse;font-size:12.5px} .fb td{padding:3px 4px;vertical-align:top;border-top:1px solid #f0f0ee}
.fb td.k{width:118px;font-weight:600;color:#555} pre.tree{font-size:12px;line-height:1.45;margin:0;font-family:ui-monospace,Menlo,Consolas,monospace;color:#222}
"""


def _e(s) -> str:
    return html.escape(str(s if s is not None else ""))


def _money(v, sign=True) -> str:
    if v is None:
        return "—"
    s = ("-" if v < 0 else ("+" if sign and v > 0 else "")) + "$" + f"{abs(v):,.2f}"
    return s


def _f(v, d=2, sign=True) -> str:
    if v is None:
        return "—"
    return (("+" if sign and v > 0 else "") + f"{v:.{d}f}")


def _pc(v) -> str:
    return "—" if v is None else f"{round(v * 100)}%"


def _cls(v) -> str:
    return "" if v is None else ("up" if v > 0 else "down" if v < 0 else "")


ONE_DAY = ' <span class="chip" style="font-size:9.5px;padding:0 4px">1 day</span>'
FOOT = '<div class="foot">Paper trading results · Educational only — not financial advice.</div>'


def page(body: str, title: str, sub: str) -> str:
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body><div class="wrap" id="cap">'
            f'<h1>{_e(title)}</h1><div class="sub">{_e(sub)}</div>{body}{FOOT}</div></body></html>')


COLORS = {"primary": "#2563eb", "testing": "#0d9488", "testing2": "#d97706", "gen": "#7c3aed", "graveyard": "#6b7280"}


def _chart(accts: list[dict], date: str) -> str:
    """Cumulative P/L per account since its first session (SVG lines) + the total."""
    days = sorted({x["date"] for a in accts for x in a.get("history") or [] if x.get("date", "") <= date})
    if not days:
        return '<div class="sub">No history yet.</div>'
    W, H, P = 600, 210, 64
    series = {}
    for a in accts:
        by = {x["date"]: (x.get("pnl") or 0) for x in a.get("history") or []}
        c, pts, started = 0.0, [], False
        for d in days:
            if d in by:
                started = True
                c += by[d]
            pts.append(c if started else None)
        series[a["k"]] = [0.0 if pts and pts[0] is not None else None] + pts   # every line starts at $0 (Day 1 open)
    days = ["start"] + days
    tot =[sum(series[k][i] or 0 for k in series) for i in range(len(days))]
    vals = [v for p in series.values() for v in p if v is not None] + tot + [0]
    lo, hi = min(vals), max(vals)
    x = lambda i: P + i * (W - P - 10) / max(1, len(days) - 1)
    y = lambda v: 10 + (hi - v) * (H - 34) / ((hi - lo) or 1)
    def path(p):
        out, pen = [], False
        for i, v in enumerate(p):
            if v is None:
                pen = False
                continue
            out.append(("L" if pen else "M") + f"{x(i):.1f} {y(v):.1f}")
            pen = True
        return "".join(out)
    lines = "".join(f'<path d="{path(series[k])}" fill="none" stroke="{COLORS[k]}" stroke-width="2"/>' for k in series)
    lines += f'<path d="{path(tot)}" fill="none" stroke="#111" stroke-width="2.6" stroke-dasharray="5 3"/>'
    ticks = "".join(f'<text x="{P - 6}" y="{y(v) + 4:.1f}" text-anchor="end" font-size="10" fill="#666">{_money(v, False).replace(".00", "") if abs(v) >= 1 else "$0"}</text>'
                    f'<line x1="{P}" x2="{W - 10}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="#eee"/>' for v in (hi, 0, lo))
    xl = f'<text x="{P}" y="{H - 6}" font-size="10" fill="#666">{days[1][5:]} open</text><text x="{W - 10}" y="{H - 6}" font-size="10" fill="#666" text-anchor="end">{days[-1][5:]}</text>'
    leg = "".join(f'<span><i style="background:{COLORS[a["k"]]}"></i>{_e(a["name"])}</span>' for a in accts) + '<span><i style="background:#111"></i>All 5 (dashed)</span>'
    return f'<svg viewBox="0 0 {W} {H}" width="100%">{ticks}{lines}{xl}</svg><div class="leg">{leg}</div>'


def _last5(accts: list[dict], date: str) -> str:
    days = sorted({x["date"] for a in accts for x in a.get("history") or [] if x.get("date", "") <= date and x.get("trades")})[-5:]
    rows = []
    for d in reversed(days):
        hs = [x for a in accts for x in a.get("history") or [] if x.get("date") == d]
        pnl, tr = sum(x.get("pnl") or 0 for x in hs), sum(x.get("trades") or 0 for x in hs)
        r = sum((x.get("avg_r") or 0) * (x.get("trades") or 0) for x in hs) / tr if tr else None
        pr = next((x for x in accts[0].get("history") or [] if x.get("date") == d), {})
        rows.append(f'<tr><td class="l">{d[5:]}</td><td class="{_cls(pnl)}">{_money(pnl)}</td><td class="{_cls(pr.get("pnl"))}">{_money(pr.get("pnl"))}</td>'
                    f'<td>{tr}</td><td class="{_cls(r)}">{_f(r)}</td></tr>')
    return ('<table class="t5"><thead><tr><th class="l">Session</th><th>All 5 P/L</th><th>Primary P/L</th><th>Trades</th><th>Avg R</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>')


def html_today(date: str, accts: list[dict]) -> str:
    cards = []
    for a in accts:
        l1 = f'Today <span class="{_cls(a["today"])}">{_money(a["today"])}</span> · {a["trades"] if a["trades"] is not None else "—"} trades'
        l2 = f'Since Day 1 <span class="{_cls(a.get("since"))}">{_money(a.get("since"))}</span>'
        cards.append(f'<div class="acc"><div class="n">{_e(a["name"])}</div><div class="ty">{_e(a["kind"])}</div>'
                     f'<div class="eq">{_money(a["equity"], sign=False)}</div><div class="ln">{l1}</div><div class="ln">{l2}</div></div>')
    today = sum((a["today"] or 0) for a in accts)
    since = sum((a.get("since") or 0) for a in accts)
    strip = (f'<div class="strip"><div>All 5 today: <b class="{_cls(today)}">{_money(today)}</b></div>'
             f'<div>All 5 since Day 1: <b class="{_cls(since)}">{_money(since)}</b></div><div>Paper money · day-trading accounts only</div></div>')
    m = milestones(accts[0], date)
    dots = "".join(f'<div class="dot {"g" if g else "r"}" title="{d}"></div>' for d, g in m["dots"]) + "".join('<div class="dot"></div>' for _ in range(10 - len(m["dots"])))
    ms = (f'<div class="ms"><div class="m"><div class="t">M1 · {MILESTONES[0][1]}{"<span class=done>REACHED</span>" if m["m1"] else ""}</div>'
          f'<div class="v">{min(m["run"], 3)} / 3</div><div class="d">Current streak {m["run"]} · best so far {m["best_run"]}</div></div>'
          f'<div class="m"><div class="t">M2 · {MILESTONES[1][1]}{"<span class=done>REACHED</span>" if m["m2"] else ""}</div>'
          f'<div class="v">{m["g10"]} / {m["n10"]}</div><div class="d">Need 8 of 10 · green / red, oldest → newest</div><div class="dots">{dots}</div></div></div>')
    return page(f'<div class="card"><h2>Accounts — end of day</h2><div class="accts accts5">{"".join(cards)}</div>{strip}</div>'
                f'<div class="card"><h2>Milestones</h2>{ms}</div>'
                f'<div class="two"><div class="card"><h2>Progress — cumulative P/L since Day 1 (10/23)</h2>{_chart(accts, date)}</div>'
                f'<div class="card"><h2>Last 5 sessions</h2>{_last5(accts, date)}</div></div>',
                f"MCF daily — {date}", "AI/algo day-trading system on paper money · end-of-day summary")


def html_top2(date: str, top: list[dict], words: dict) -> str:
    tops = []
    for i, t in enumerate(top, 1):
        w = words.get(t["setup"]) or {}
        lines = w.get("lines") or [["What", t["what"]]]
        side = (t.get("side") or "").lower()
        sd = f'<span class="side {"up" if side == "long" else "down"}">{"LONG" if side == "long" else "SHORT" if side == "short" else ""}</span>' if side else ""
        rows = "".join(f'<tr><td class="k">{_e(k)}</td><td>{_e(v)}</td></tr>' for k, v in lines)
        tops.append(f'<div class="ts"><div class="t">{i}. {_e(w.get("title") or t["name"])}{sd}</div>'
                    f'<div class="st">{t["trades"]} trades · <span class="{_cls(t["r"])}">{_f(t["r"], 1)}R</span> · '
                    f'<b class="{_cls(t["pnl"])}">{_money(t["pnl"])}</b> · {_e(" + ".join(sorted(set(t["accts"]))))}</div>'
                    f'<table>{rows}</table><div class="id" style="margin-top:6px">{_e(t["setup"])}</div></div>')
    note = words.get("_note") or "1 unit = ¼ of the stock's normal daily range (0.25 × daily ATR). Open trades close by 3:55 PM ET."
    return page(f'<div class="card"><h2>Top 2 setups today — in plain words</h2><div class="top2">{"".join(tops)}</div>'
                f'<div class="sub" style="margin:8px 0 0">{_e(note)} Not a recommendation; for research only.</div></div>',
                f"MCF daily — {date} · Top 2 setups", "The two setups that made the most today, explained so you can research them yourself")


def html_facts(date: str, fx: dict) -> str:
    row = lambda k, v: f'<tr><td class="k">{_e(k)}</td><td>{v}</td></tr>'
    stack = "".join([row("AI", "Claude (Opus 5.5) builds, tests and runs it"), row("Code", "Python (pandas / NumPy) · dashboard in HTML/JS"),
                     row("Broker / data", "Alpaca API · paper trading · SIP market data (all US exchanges)"),
                     row("Market", "US stocks and ETFs · intraday only (9:50 AM–3:55 PM ET) · long and short · nothing held overnight"),
                     row("Backtests", "2 years of 1-minute bars, train / validation split, a locked holdout never peeked at, costs in")])
    scale = "".join([row("Setups live", f'<b>{fx["live"]}</b> across Primary, Testing 1, Testing 2, Graveyard'),
                     row("Generated live", f'<b>{fx["gen"]}</b> in the Setup Generator account'),
                     row("Rejected so far", f'<b>~{fx["rejected"]:,}</b> setups failed backtests (plus many more variations)'),
                     row("Built from", "basic indicators: RSI, VWAP, volume / buy-sell pressure, gaps, opening range, prior-day highs and lows, ATR"),
                     row("Setup Generator", "a bot that invents 10 new setups a night from those indicators and trades them on its own paper account"),
                     row("Track record", f'{fx["sessions"]} sessions since {fx["start"] or "—"} · {fx["trades"]:,} paper trades')])
    stats = "".join([row("Avg R", "average result per trade in units of the risk taken; costs, fees and slippage are already in. +0.5R = earns half its risk per trade"),
                     row("Break-even win rate", "the win rate a setup needs just to not lose money, given its own average win and loss size"),
                     row("Confidence (t)", "how sure it isn't luck: 2+ solid, under 1 could be luck"),
                     row("Trades/session", "average trades per session it traded: how active it is"),
                     row("Slippage", f'entries fill on average <b>{_f(fx["slip"], 1, False)} bps</b> worse than the signal price (measured on paper fills)')])
    tree = ("Idea / Setup Generator\n └─ 2-year backtest (costs in)\n     └─ Replay on real sessions\n         └─ Testing 1 / Testing 2 / Setup Generator (paper)\n"
            "             └─ Primary (paper)\n                 └─ Live money (after milestones)\nLosers move down: Primary → Testing → Graveyard (never deleted)")
    ms = "".join(row(k, v) for k, v in MILESTONES)
    return page(f'<div class="facts"><div class="fb"><h3>Stack</h3><table>{stack}</table></div><div class="fb"><h3>Setups</h3><table>{scale}</table></div>'
                f'<div class="fb"><h3>Life cycle of a setup</h3><pre class="tree">{_e(tree)}</pre></div>'
                f'<div class="fb"><h3>What the stats mean</h3><table>{stats}</table></div>'
                f'<div class="fb" style="grid-column:1 / -1"><h3>Milestones before real money</h3><table>{ms}</table></div></div>',
                f"MCF — quick facts", f"Same every day; counts as of {date}")


def facts_text(date: str, fx: dict, accts: list[dict] | None = None, gs: dict | None = None) -> str:
    """Owner 2026-10-26: two text blocks - 'Quick facts' (numbers only) and 'Quick answers' (the common questions)."""
    sl = _f(fx["slip"], 1, False)
    lines = [f"Quick facts (as of {date})",
             f"- Sessions traded: {fx['sessions']} (since {fx['start'] or '—'}) · paper trades: {fx['trades']:,}",
             f"- Setups live: {fx['live']} + {fx['gen']} machine-generated",
             f"- Setups rejected by backtests so far: ~{fx['rejected']:,}",
             f"- Entry slippage: ~{sl} bps vs the signal price (measured, paper fills)"]
    if accts:
        pr = accts[0]
        m = milestones(pr, date)
        h = _sessions(pr, date)
        g = sum((x.get("pnl") or 0) > 0 for x in h)
        today = sum((a["today"] or 0) for a in accts)
        since = sum((a.get("since") or 0) for a in accts)
        lines += [f"- Today, 5 day-trading accounts: {_money(today)} · since Day 1 (10/23): {_money(since)}",
                  f"- Primary: today {_money(pr['today'])} · since Day 1 {_money(pr.get('since'))} · green days {g} of {len(h)}",
                  f"- Milestones: M1 (3 green in a row) {min(m['run'], 3)}/3 · M2 (8 of last 10 green) {m['g10']}/{m['n10']}"]
    if gs:
        lines += [""] + _streak_lines(gs)
    ans = ["Quick answers",
           "- What AI? Claude (Opus 5.5) builds, tests and runs it. Code is Python.",
           "- Broker / data? Alpaca API, paper trading, SIP market data (all US exchanges).",
           "- What's traded? US stocks + ETFs, intraday only (9:50 AM-3:55 PM ET), long and short, nothing held overnight.",
           "- How are setups built? Basic indicators: RSI, VWAP, volume / buy-sell pressure, gaps, opening range, prior-day highs/lows, ATR.",
           "- Setup Generator? A bot that invents 10 new setups a night and trades them on its own paper account.",
           "- Life cycle? Idea/generator -> 2-yr backtest (costs in) -> replay -> testing (paper) -> Primary (paper) -> real money after the milestones. Losers move down to the Graveyard, never deleted.",
           "- Avg R? Average result per trade in units of the risk taken, after costs, fees and slippage.",
           "- Break-even win rate? The win rate a setup needs just to not lose money.",
           "- Avg R w/o best day? Same, with its single best session removed - spots records carried by one big day.",
           "- Real money yet? No - paper until M1 (3 green days in a row) and M2 (8 green of the last 10).",
           "Not financial advice."]
    return "\n".join(lines) + "\n\n" + "\n".join(ans) + "\n"


def post_text(date: str, accts: list[dict], top: list[dict], words: dict, day_n: int, changes: str = "",
              gs: dict | None = None) -> str:
    m = milestones(accts[0], date)
    today = sum((a["today"] or 0) for a in accts)
    since = sum((a.get("since") or 0) for a in accts)
    pr = accts[0]
    best = top[0] if top else None
    bn = ((words.get(best["setup"]) or {}).get("title") or best["name"]) if best else "—"
    return (f"Day {day_n} – AI algo day-trading (paper)\n"
            f"Today: {_money(today).replace('.00', '')} across 5 day-trading accounts · Primary {_money(pr['today'])}\n"
            f"Since Day 1 (10/23): {_money(since)} · Best setup today: {bn} ({_money(best['pnl']) if best else '—'})\n"
            f"Milestones: M1 3 green in a row {min(m['run'], 3)}/3{' ✅' if m['m1'] else ''} · M2 8 of last 10 green {m['g10']}/{m['n10']}{' ✅' if m['m2'] else ''}\n"
            + (("Green-day streaks: " + (" · ".join(f"{x['name']} {x['run']}" for x in gs["current"][:3]) or "none at 3+")
                + (f" · record {gs['record'][0]['run']} in a row" if gs.get("record") else "") + "\n") if gs is not None else "")
            + (f"Changes before today's open: {changes.strip()}\n" if changes.strip() else "")
            + "(Quick facts + charts in pics) · Not financial advice\n")


def html_lb(date: str, rows: list[dict], gen: bool) -> str:
    if gen:
        head = ["#", "Setup", "Last-session trades", "Last-session R", "Last-session P/L", "Live trades", "Trades/day", "Win rate",
                "Break-even win rate", "Avg R", "Avg R w/o best day", "Confidence (t)", "Total R", "P/L", "Last 4 avg R", "Screen train R", "Screen valid R"]
    else:
        head = ["#", "Setup", "Account", "Best conditions", "Last-session trades", "Last-session R", "Last-session P/L", "Live trades",
                "Sessions", "Trades per session", "Win rate", "Break-even win rate", "Avg R", "Avg R w/o best day", "Confidence (t)", "Total R", "P/L", "PF", "Last 4 avg R"]
    ls_cols = {"Last-session trades", "Last-session R", "Last-session P/L"}
    th = "".join(f'<th class="{"l" if h in ("Setup", "Account", "Best conditions") else ""}{" ls" if h in ls_cols else ""}">{h}</th>' for h in head)
    trs = []
    for x in rows:
        edge = None if x["win"] is None or x["be"] is None else x["win"] - x["be"]
        be = _pc(x["be"]) + (f' <span style="font-size:10.5px">({edge * 100:+.0f})</span>' if edge is not None else "")
        nm = (f'<td class="l nm">{"<span class=gb>GENERATED</span>" if gen else ""}{_e(x["name"])}<div>{_e(x["setup"])}</div></td>')
        ls = (f'<td class="ls">{x["ls_n"] or "—"}</td><td class="ls {_cls(x["ls_r"]) if x["ls_n"] else ""}">{_f(x["ls_r"]) if x["ls_n"] else "—"}</td>'
              f'<td class="ls {_cls(x["ls_pnl"]) if x["ls_n"] else ""}">{_money(x["ls_pnl"]) if x["ls_n"] else "—"}</td>')
        common = (f'<td>{_pc(x["win"])}</td><td class="{_cls(edge)}">{be}</td><td class="{_cls(x["avg_r"])}">{_f(x["avg_r"])}</td>'
                  f'<td class="{_cls(x["exbest"][0])}">{_f(x["exbest"][0])}{ONE_DAY if (x["exbest"][2] or 0) >= 0.5 else ""}</td>'
                  f'<td>{_f(x["t"], 1, False)}</td><td class="{_cls(x["total_r"])}">{_f(x["total_r"], 1)}</td><td class="{_cls(x["pnl"])}">{_money(x["pnl"])}</td>')
        if gen:
            trs.append(f'<tr><td>{x["rank"]}</td>{nm}{ls}<td>{x["trades"]}</td><td>{_f(x["per_day"], 1, False)}</td>{common}'
                       f'<td class="{_cls(x["last4"])}">{_f(x["last4"])}</td><td class="{_cls(x["screen"][0])}">{_f(x["screen"][0], 3)}</td>'
                       f'<td class="{_cls(x["screen"][1])}">{_f(x["screen"][1], 3)}</td></tr>')
        else:
            best = f'<span class="chip {_e(x["best"])}">{_e(x["best"])}</span>' if x["best"] else "—"
            trs.append(f'<tr><td>{x["rank"]}</td>{nm}<td class="l">{_e(x["acct"])}</td><td class="l">{best}</td>{ls}'
                       f'<td>{x["trades"]}</td><td>{x["sessions"] or "—"}</td><td>{_f(x["per_day"], 1, False)}</td>{common}<td>{_f(x["pf"], 2, False)}</td>'
                       f'<td class="{_cls(x["last4"])}">{_f(x["last4"])}</td></tr>')
    title = "Generated setups — top 10 (Setup Generator account)" if gen else "Setup leaderboard — top 10, all accounts, since start"
    sub = ("Machine-generated setups on their own paper account; not tested edges. Ranked by avg R per trade, shrunk by trades ÷ (trades + 20)."
           if gen else "Ranked by avg R per trade shrunk by trades ÷ (trades + 20), so a few lucky trades don't outrank a long record. "
                       "Break-even win rate = win rate needed to make money (green = beating it). Setup Generator excluded.")
    return page(f'<div class="card{" gen" if gen else ""}"><table class="lb"><thead><tr>{th}</tr></thead><tbody>{"".join(trs)}</tbody></table>'
                f'<div class="sub" style="margin:8px 0 0">Last session = {date}. R = planned risk per trade; P/L after Alpaca paper fills.</div></div>',
                f"MCF daily — {date} · {title.split(' — ')[0]}", sub)


def render(htmls: dict[str, str], out: Path):
    from playwright.sync_api import sync_playwright

    out.mkdir(parents=True, exist_ok=True)
    exe = next((c for c in CHROME if Path(c).exists()), None)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe, args=["--no-sandbox"]) if exe else p.chromium.launch()
        pg = b.new_page(viewport={"width": 1248, "height": 800}, device_scale_factor=2)
        pg.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
        for name, h in htmls.items():
            (out / f"{name}.html").write_text(h)
            pg.set_content(h, wait_until="domcontentloaded")
            pg.locator("#cap").screenshot(path=str(out / f"{name}.png"))
            (out / f"{name}.html").unlink()
        b.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--date", required=True)
    ap.add_argument("--top2", help="JSON with plain-words descriptions of the day's top setups")
    ap.add_argument("--out", default="docs/posts")
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--changes", help="one short line: what changed before today's open (owner 2026-10-26)")
    ap.add_argument("--day", type=int, help="day number for the post title (default: Primary sessions so far)")
    a = ap.parse_args(argv)
    if not a.no_fetch:
        fetch()
    words = {}
    if a.top2 and Path(a.top2).exists():
        j = json.loads(Path(a.top2).read_text())
        words = {s["setup"]: s for s in j.get("setups", [])}
        if j.get("note"):
            words["_note"] = j["note"]
    top = top_of_day(a.date)
    out = ROOT / a.out / a.date
    acc = accounts(a.date)
    render({"1-today": html_today(a.date, acc), "2-top2": html_top2(a.date, top, words),
            "3-leaderboard": html_lb(a.date, leaderboard(a.date), gen=False),
            "4-generator": html_lb(a.date, leaderboard(a.date, gen=True), gen=True)}, out)
    gs = green_streaks(a.date, acc)
    (out / "facts.txt").write_text(facts_text(a.date, facts(acc), acc, gs))   # owner 2026-10-26: quick facts as text, 4 images max
    (out / "post.txt").write_text(post_text(a.date, acc, top, words, a.day or len(_sessions(acc[0], a.date)), a.changes or "", gs))
    print(json.dumps({"out": str(out), "top": [t["setup"] for t in top]}))


if __name__ == "__main__":
    main()
