"""Markdown tables for research/replay/VALIDATION.md from the JSON outputs of validate.py, gap.py and broad.py.

    python research/replay/tables.py --val V.json [--val-costs VC.json] [--gap G.json] [--broad B.json]

Educational only - not financial advice."""

from __future__ import annotations

import argparse
import json


def _f(x, nd=3):
    if x is None:
        return "-"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def val_table(v: dict, title: str) -> str:
    out = [f"### {title}", "",
           "| account | sessions | live signals (in universe) | replay signals | matched | match % of live in-universe | "
           "status agree | live trades (in universe) | replay trades | matched trades | entry diff bps (median) | "
           "R diff matched (mean / median) | same exit | live R (in universe) | replay R |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for a, r in v.items():
        s, t, u = r["signals"], r["trades"], r["system_in_universe"]
        mr = s["matched"] / max(1, s.get("live_in_universe", s["live"]))
        out.append(f"| {a} | {len(r['sessions'])} | {s['live']} ({s.get('live_in_universe', '-')}) | {s['replay']} | "
                   f"{s['matched']} | {mr:.1%} | {_f(s['status_agree'])} | {t['live']} ({u['live_trades']}) | "
                   f"{t['replay']} | {t['matched']} | {_f(t.get('entry_diff_bps_median'), 1)} | "
                   f"{_f(t.get('r_diff_mean'))} / {_f(t.get('r_diff_median'))} | {_f(t.get('same_exit_reason'))} | "
                   f"{_f(u['live_total_r'], 1)} ({_f(u['live_avg_r'])}/tr) | {_f(u['replay_total_r'], 1)} "
                   f"({_f(u['replay_avg_r'])}/tr) |")
    return "\n".join(out) + "\n"


def disagreements(v: dict) -> str:
    out = []
    for a, r in v.items():
        d = r["signals"].get("status_disagreements") or {}
        out.append(f"**{a}** (matched signals with a different outcome; live -> replay):")
        out += [f"- {n} x `{k}`" for k, n in list(d.items())[:10]]
        out.append("")
    return "\n".join(out)


def per_setup(v: dict, n: int = 12) -> str:
    out = ["| account | setup | live trades | live avg R | replay trades | replay avg R |", "|---|---|---|---|---|---|"]
    for a, r in v.items():
        rows = sorted(r["per_setup"], key=lambda x: -(x["live_trades"] + x["replay_trades"]))[:n]
        for x in rows:
            out.append(f"| {a} | {x['setup']} | {x['live_trades']} | {_f(x['live_avg_r'])} | {x['replay_trades']} | "
                       f"{_f(x['replay_avg_r'])} |")
    return "\n".join(out) + "\n"


def gap_table(g: dict) -> str:
    keys = [("A_backtest", "A backtest (all signals, full session, costs)"),
            ("A_gated_out", "  of which lab signals the 5-bar gate never shows live"),
            ("A_after_gate", "A' after the 5-bar gate"),
            ("B_live_signals", "B signals the replayed runner journaled"),
            ("B_blocked", "  of which blocked (caps, twin, spread, risk...)"),
            ("B_taken", "  of which taken (simulated like A)"),
            ("C_taken_costs", "C taken, broker fills, costs, trade-through"),
            ("C_touch", "C' same with touch fills on targets"),
            ("D_paper", "D paper fills (half-spread, touch)"),
            ("E_live", "E live paper journal (all symbols)")]
    out = ["| step | " + " | ".join(f"{a} n / total R / avg R" for a in g) + " |",
           "|---|" + "---|" * len(g)]
    for k, label in keys:
        cells = []
        for a in g:
            x = g[a].get(k)
            cells.append("-" if not x else f"{x['n']} / {_f(x['total_r'], 1)} / {_f(x['avg_r'])}")
        out.append(f"| {label} | " + " | ".join(cells) + " |")
    return "\n".join(out) + "\n"


def blocks(g: dict) -> str:
    out = []
    for a, r in g.items():
        b = sorted((r.get("blocks_by_reason") or {}).items(), key=lambda kv: -kv[1]["n"])[:8]
        out.append(f"**{a}** blocked signals by reason (n, what they would have made in R, avg):")
        out += [f"- `{k}`: {v['n']}, {v['total_r']:+.1f}R ({_f(v['avg_r'])}/signal)" for k, v in b]
        out.append("")
    return "\n".join(out)


def broad_table(b: dict) -> str:
    out = ["| account | sessions | trades | avg R | day-clustered t | total R | touch-fill total R | up | flat | down | "
           "before 10-06 avg R | live weeks avg R | live weeks expected from regime mix |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for a, r in b.items():
        if a == "regimes":
            continue
        al, br, bp = r["all"], r["by_regime"], r["by_period"]
        tf = r.get("touch_fill_all") or {}
        out.append(f"| {a} | {al['sessions']} | {al['trades']} | {_f(al['avg_r'])} | {_f(al['t'], 2)} | "
                   f"{_f(al['total_r'], 1)} | {_f(tf.get('total_r'), 1)} | "
                   + " | ".join(f"{_f(br.get(k, {}).get('avg_r'))} ({br.get(k, {}).get('trades', 0)})"
                                for k in ("up", "flat", "down"))
                   + f" | {_f(bp.get('before (..10-05)', {}).get('avg_r'))} | "
                     f"{_f(bp.get('live weeks (10-06..)', {}).get('avg_r'))} | "
                     f"{_f(r.get('live_weeks_expected_from_regime_mix'))} |")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--val")
    ap.add_argument("--val-costs")
    ap.add_argument("--gap")
    ap.add_argument("--broad")
    a = ap.parse_args()
    if a.val:
        v = json.load(open(a.val))
        print(val_table(v, "Replay (paper fills) vs live"))
        print(disagreements(v))
        print(per_setup(v))
    if a.val_costs:
        print(val_table(json.load(open(a.val_costs)), "Replay (production costs, trade-through) vs live"))
    if a.gap:
        g = json.load(open(a.gap))
        print(gap_table(g))
        print(blocks(g))
    if a.broad:
        print(broad_table(json.load(open(a.broad))))


if __name__ == "__main__":
    main()
