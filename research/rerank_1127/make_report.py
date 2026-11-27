"""Builds research/rerank_1127/tables.md from rerank.json (pasted into REPORT.md). Educational only - not financial advice."""
import json, pathlib, re
H = pathlib.Path(__file__).resolve().parent
d = json.load(open(H / "rerank.json")); wk = json.load(open(H / "rerank_week.json"))
sh = lambda s: re.match(r"(GEN-\d{6}-\d{2})", s).group(1) if s.startswith("GEN-") else s
f = lambda v, n=3: "–" if v is None else f"{v:+.{n}f}"
pc = lambda v: "–" if v is None else f"{v*100:.0f}%"
tag = lambda v: " `1 day`" if v is not None and v >= 0.5 else ""
L = []
L.append("| # | setup | account now | trades | sess | avg R | avg R w/o best day | best day (share) | trades left w/o best day | t | day t | shrunk rank | record from |")
L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
allwk = {}
for m in d["top20"]:
    L.append(f"| {m['rank_wobest']} | {sh(m['setup'])} | {m['account']} | {m['trades']} | {m['sessions']} | {f(m['avg_r'])} | **{f(m['exbest_r'])}** | {m['best_day'][5:]} ({pc(m['best_share'])}){tag(m['best_share'])} | {m['n_left']} | {f(m['t'],2)} | {f(m['t_day'],2)} | {m['rank_score']} | {m['record_from']} |")
L.append("")
L.append("| last wk # | setup | account now | 11-23 | 11-24 | 11-25 | 11-27 | week trades | week R | week avg R | record to 11-20 (n, avg R) | rank now (w/o best / shrunk) |")
L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
for x in d["last_week"]:
    w = wk.get(x["setup"], {})
    c = lambda dd: (f"{w[dd][0]} / {w[dd][1]:+.2f}" if dd in w else "–")
    L.append(f"| {x['last_rank']} | {sh(x['setup'])} | {x['account']} | {c('2026-11-23')} | {c('2026-11-24')} | {c('2026-11-25')} | {c('2026-11-27')} | {x['week_trades']} | {x['week_r']:+.2f} | {f(x['week_avg'])} | {x['pre_trades']}, {f(x['pre_avg'])} | {x.get('rank_wobest','out (GY)')} / {x.get('rank_score','–')} |")
L.append("")
L.append("| shrunk # | setup | account now | trades | avg R | avg R w/o best day | best-day share | w/o-best rank |")
L.append("|---|---|---|---|---|---|---|---|")
for m in d["shrunk_top20"]:
    L.append(f"| {m['rank_score']} | {sh(m['setup'])} | {m['account']} | {m['trades']} | {f(m['avg_r'])} | {f(m['exbest_r'])} | {pc(m['best_share'])}{tag(m['best_share'])} | {m.get('rank_wobest','– (1 session)')} |")
open(H / "tables.md", "w").write("\n".join(L) + "\n")
