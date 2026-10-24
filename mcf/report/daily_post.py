"""Daily message-board post images (owner 2026-10-24).

Three PNGs per session, built from the same data the dashboard reads (each data branch's status.json and
reports/scorecard.json, docs/live/assignments.json / setup_names.json / regimes.json):

  1-accounts.png      EOD balance, today's P/L and since-start P/L per account, Primary green-day streak, and the
                      day's top two setups explained in plain words (the words come from --top2 JSON, written by
                      Claude each night; without it the setup's own one-line description is used)
  2-leaderboard.png   setup leaderboard, top 10 (all accounts merged, Setup Generator excluded), same columns and
                      rank as the dashboard
  3-generator.png     generated setups leaderboard (Setup Generator account), top 10

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
            ("graveyard", "Graveyard", "mcf-data-graveyard", "lowest performers"),
            ("longhold", "Long-hold (S6)", "mcf-data-longhold", "weekly momentum")]
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
def accounts(date: str) -> list[dict]:
    out = []
    for k, name, br, kind in ACCOUNTS:
        if k == "longhold":
            s = _show(br, "longhold/status.json") or {}
            x, mk, lp = s.get("intraday") or {}, s.get("mark") or {}, s.get("last_plan") or {}
            use_x = x.get("asof") and (not mk.get("date") or x["asof"][:10] >= mk["date"])
            ss = s.get("since_start") or {}
            out.append(dict(k=k, name=name, kind=kind, equity=(x.get("equity") if use_x else mk.get("equity", lp.get("equity"))),
                            today=(x.get("day_pl") if use_x else mk.get("day_pl")), trades=None,
                            holdings=len(s.get("positions") or {}), since_pct=ss.get("return")))
            continue
        s = _show(br, "status.json") or {}
        t, ss = s.get("today") or {}, s.get("since_start") or {}
        if s.get("session_date") != date:
            t = next((h for h in s.get("history") or [] if h.get("date") == date), {})
        out.append(dict(k=k, name=name, kind=kind, equity=(s.get("account") or {}).get("equity"), today=t.get("pnl"),
                        trades=t.get("trades"), since=ss.get("pnl"), history=s.get("history") or []))
    return out


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
                         ls_pnl=ls[3] if ls else None, trades=n, sessions=r.get("sessions_traded"), per_day=(n / len(r.get("days") or [1])),
                         win=r.get("win_rate"), be=r.get("breakeven_wr"), avg_r=r.get("avg_r"), t=r.get("t_stat"),
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
    out = sorted(agg.values(), key=lambda x: -x["pnl"])[:n]
    for x in out:
        nm = names.get(x["setup"]) or {}
        x["name"], x["what"], x["side"] = nm.get("name") or x["setup"], nm.get("what") or "", nm.get("side")
    return out


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
.lb{width:100%;border-collapse:collapse;font-size:12.5px;font-variant-numeric:tabular-nums}
.lb th{font-size:11px;color:#555;text-align:right;padding:5px 5px;border-bottom:1px solid #ddd;vertical-align:bottom;line-height:1.2}
.lb td{padding:5px 5px;text-align:right;border-bottom:1px solid #eee;white-space:nowrap}
.lb .l{text-align:left} .lb .nm{max-width:270px;overflow:hidden;text-overflow:ellipsis} .lb .nm div{font-size:10.5px;color:#888;overflow:hidden;text-overflow:ellipsis}
.lb .ls{background:#eef3fb} .chip{display:inline-block;font-size:10.5px;padding:0 6px;border-radius:6px;border:1px solid #ccc;color:#444}
.chip.Bear{color:#b91c1c;border-color:#b91c1c} .chip.Bull{color:#15803d;border-color:#15803d} .chip.Choppy{color:#b45309;border-color:#b45309}
.gen{border-color:#c4b5fd;background:#faf8ff} .gb{display:inline-block;font-size:9.5px;font-weight:700;color:#fff;background:#7c3aed;border-radius:4px;padding:1px 5px;margin-right:5px;vertical-align:1px}
.foot{font-size:9px;color:#999;text-align:center;padding:4px 0 8px}
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


FOOT = '<div class="foot">Paper trading results · Educational only — not financial advice.</div>'


def page(body: str, title: str, sub: str) -> str:
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body><div class="wrap" id="cap">'
            f'<h1>{_e(title)}</h1><div class="sub">{_e(sub)}</div>{body}{FOOT}</div></body></html>')


def html_accounts(date: str, accts: list[dict], top: list[dict], words: dict) -> str:
    cards = []
    for a in accts:
        if a["k"] == "longhold":
            l1 = f'Today <span class="{_cls(a["today"])}">{_money(a["today"])}</span> · {a["holdings"]} holdings'
            sp = a.get("since_pct")
            l2 = f'Since start <span class="{_cls(sp)}">{"—" if sp is None else f"{sp * 100:+.1f}%"}</span>'
        else:
            l1 = f'Today <span class="{_cls(a["today"])}">{_money(a["today"])}</span> · {a["trades"] if a["trades"] is not None else "—"} trades'
            l2 = f'Since start <span class="{_cls(a.get("since"))}">{_money(a.get("since"))}</span>'
        cards.append(f'<div class="acc"><div class="n">{_e(a["name"])}</div><div class="ty">{_e(a["kind"])}</div>'
                     f'<div class="eq">{_money(a["equity"], sign=False)}</div><div class="ln">{l1}</div><div class="ln">{l2}</div></div>')
    pr = next(a for a in accts if a["k"] == "primary")
    run, green, n = streak(pr, date)
    intraday = sum((a["today"] or 0) for a in accts if a["k"] != "longhold")
    strip = (f'<div class="strip"><div>Intraday accounts today: <b class="{_cls(intraday)}">{_money(intraday)}</b></div>'
             f'<div>Primary green-day streak: <b>{run}</b> ({green} of {n} sessions green)</div>'
             f'<div>Start: $100,000 per account (paper)</div></div>')
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
    return page(f'<div class="card"><h2>Accounts — end of day</h2><div class="accts">{"".join(cards)}</div>{strip}</div>'
                f'<div class="card"><h2>Top 2 setups today — in plain words</h2><div class="top2">{"".join(tops)}</div>'
                f'<div class="sub" style="margin:8px 0 0">{_e(note)} Not a recommendation; for research only.</div></div>',
                f"MCF daily — {date}", "AI/algo day-trading system on paper money · end-of-day summary")


def html_lb(date: str, rows: list[dict], gen: bool) -> str:
    if gen:
        head = ["#", "Setup", "Last-session trades", "Last-session R", "Last-session P/L", "Live trades", "Trades/day", "Win rate",
                "Break-even win rate", "Avg R", "Confidence (t)", "Total R", "P/L", "Last 4 avg R", "Screen train R", "Screen valid R"]
    else:
        head = ["#", "Setup", "Account", "Best conditions", "Last-session trades", "Last-session R", "Last-session P/L", "Live trades",
                "Sessions", "Win rate", "Break-even win rate", "Avg R", "Confidence (t)", "Total R", "P/L", "PF", "Last 4 avg R"]
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
                  f'<td>{_f(x["t"], 1, False)}</td><td class="{_cls(x["total_r"])}">{_f(x["total_r"], 1)}</td><td class="{_cls(x["pnl"])}">{_money(x["pnl"])}</td>')
        if gen:
            trs.append(f'<tr><td>{x["rank"]}</td>{nm}{ls}<td>{x["trades"]}</td><td>{x["per_day"]:.1f}</td>{common}'
                       f'<td class="{_cls(x["last4"])}">{_f(x["last4"])}</td><td class="{_cls(x["screen"][0])}">{_f(x["screen"][0], 3)}</td>'
                       f'<td class="{_cls(x["screen"][1])}">{_f(x["screen"][1], 3)}</td></tr>')
        else:
            best = f'<span class="chip {_e(x["best"])}">{_e(x["best"])}</span>' if x["best"] else "—"
            trs.append(f'<tr><td>{x["rank"]}</td>{nm}<td class="l">{_e(x["acct"])}</td><td class="l">{best}</td>{ls}'
                       f'<td>{x["trades"]}</td><td>{x["sessions"] or "—"}</td>{common}<td>{_f(x["pf"], 2, False)}</td>'
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
    render({"1-accounts": html_accounts(a.date, accounts(a.date), top, words),
            "2-leaderboard": html_lb(a.date, leaderboard(a.date), gen=False),
            "3-generator": html_lb(a.date, leaderboard(a.date, gen=True), gen=True)}, out)
    print(json.dumps({"out": str(out), "top": [t["setup"] for t in top]}))


if __name__ == "__main__":
    main()
