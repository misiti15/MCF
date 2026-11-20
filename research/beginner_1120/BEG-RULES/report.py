"""Tables for RULES_RESULTS.md from results.json. python report.py > tables.md  (Educational only - not financial advice.)"""
import json
from pathlib import Path
R = json.loads((Path(__file__).resolve().parent / "results.json").read_text())
OV = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "ALL", "MCF"]


def verdict(fit, chk):
    p, q = fit["paired"], chk["paired"] if chk else None
    if p["d_avg_r_session"] > 0 and p["t"] >= 1.5 and p["beats_random_pct"] >= 0.8 and fit["setups_improved"] >= fit["setups_worse"]:
        return "HELPS, CONFIRMED" if q and q["d_avg_r_session"] > 0 and q["beats_random_pct"] >= 0.6 else "HELPS on FIT, not confirmed"
    if p["d_avg_r_session"] < 0 and p["t"] <= -1.5:
        return "HURTS"
    if abs(p["t"]) < 1.5:
        return "NEUTRAL"
    return "THINNING ONLY (no better than random removal)"


def main_table(book, seg):
    x = R["books"][book][seg]
    b = x["base"]
    out = [f"**{book} / {seg}** ({x['sessions']} sessions; baseline {b['trades']} trades, total {b['total_r']:+.1f}R, "
           f"{b['avg_r_session']:+.2f}R/session, {b['avg_r_trade']:+.4f}R/trade, worst day {b['worst_day']:+.1f}R, green {b['green_pct']:.0%}, "
           f"avg R/trade w/o best day {b['avg_r_wo_best_day']:+.4f})", "",
           "| rule | trades kept | total R | R/session | R/trade | R/trade w/o best day | worst day | green % | d R/session | paired t | days helped/hurt | beats random | setups better/worse |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for ov in OV:
        if ov not in x["rules"]:
            continue
        v = x["rules"][ov]; m, p = v["m"], v["paired"]
        out.append(f"| {ov} | {m['trades']} | {m['total_r']:+.1f} | {m['avg_r_session']:+.2f} | {m['avg_r_trade']:+.4f} | "
                   f"{m.get('avg_r_wo_best_day', float('nan')):+.4f} | {m['worst_day']:+.1f} | {m['green_pct']:.0%} | {p['d_avg_r_session']:+.2f} | {p['t']:+.2f} | "
                   f"{p['helped']}/{p['hurt']} | {p['beats_random_pct']:.0%} | {v['setups_improved']}/{v['setups_worse']} |")
    return "\n".join(out) + "\n"


def setup_table(book, seg, field="delta"):
    x = R["books"][book][seg]["rules"]
    setups = sorted(x["S1"]["setups"])
    out = [f"| setup ({book} / {seg}) | base n | base R | " + " | ".join(o for o in OV if o in x) + " |",
           "|---|---|---|" + "---|" * len([o for o in OV if o in x])]
    for s in setups:
        b = x["S1"]["setups"][s]
        cells = []
        for o in OV:
            if o not in x:
                continue
            v = x[o]["setups"][s]
            cells.append(f"{v['delta']:+.1f} ({v['kept_n']})")
        out.append(f"| {s} | {b['base_n']} | {b['base_r']:+.1f} | " + " | ".join(cells) + " |")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    print("## Verdicts (pre-registered rule; BEG book FIT, confirmed on CHECK)\n")
    print("| rule | BEG book verdict | FIT d R/session (t, beats random) | CHECK d R/session (t, beats random) | T2 d (beats random) | BEG alone FIT / CHECK d | Primary live d R/session (t, beats random) |")
    print("|---|---|---|---|---|---|---|")
    bb = R["books"]
    for ov in OV:
        f, c, t2 = (bb["BEG_book"][s]["rules"][ov] for s in ("fit", "check", "t2"))
        al = [bb["BEG_alone"][s]["rules"].get(ov) for s in ("fit", "check")]
        pr = bb["Primary"]["live"]["rules"].get(ov)
        fmt = lambda v: f"{v['paired']['d_avg_r_session']:+.2f} ({v['paired']['t']:+.2f}, {v['paired']['beats_random_pct']:.0%})"
        print(f"| {ov} | {verdict(f, c)} | {fmt(f)} | {fmt(c)} | {t2['paired']['d_avg_r_session']:+.2f} ({t2['paired']['beats_random_pct']:.0%}) | "
              + (f"{al[0]['paired']['d_avg_r_session']:+.2f} / {al[1]['paired']['d_avg_r_session']:+.2f}" if al[0] else "n/a") + " | "
              + (fmt(pr) if pr else "n/a (already live)") + " |")
    print()
    for book, segs in (("BEG_book", ("fit", "check", "t2")), ("BEG_alone", ("fit", "check")), ("Primary", ("live",))):
        for s in segs:
            print(main_table(book, s))
    print("### Per-setup effect: delta total R (trades kept) vs no rules\n")
    for book, s in (("BEG_alone", "fit"), ("BEG_alone", "check"), ("BEG_book", "check"), ("Primary", "live")):
        print(setup_table(book, s))
