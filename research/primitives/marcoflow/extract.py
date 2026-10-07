"""Extract every rule stack MarcoFlow's strategy review mined (recommendations + avoid lists across all
84 StrategyReview runs) with its signal-level stats, plus the paper results of stacks that were traded.
Writes stacks.json. Educational only - not financial advice."""
import json
import sqlite3
from pathlib import Path

OUT = Path(__file__).with_name("stacks.json")


def main():
    c = sqlite3.connect("data/marcoflow.sqlite")
    stacks: dict[str, dict] = {}
    for run_at, rec, avoid in c.execute("select runAt, recommendations, avoid from StrategyReview order by runAt"):
        for kind, blob in (("rec", rec), ("avoid", avoid)):
            try:
                rows = json.loads(blob or "[]")
            except ValueError:
                continue
            for x in rows:
                d = stacks.setdefault(x["id"], {"id": x["id"], "kind": kind, "label": x.get("label"), "n_reviews": 0,
                                                "best_lb": None, "mf_trades": None, "mf_win": None, "mf_avg_ret": None,
                                                "first_seen": run_at, "last_seen": run_at})
                d["n_reviews"] += 1
                d["last_seen"] = run_at
                lb = x.get("winRateLB")
                if kind == "rec" and (d["best_lb"] is None or (lb or 0) > d["best_lb"]):
                    d.update(best_lb=lb, mf_trades=x.get("trades"), mf_win=x.get("winRate"), mf_avg_ret=x.get("avgReturn"))
                if kind == "avoid":
                    d.update(best_lb=lb, mf_trades=x.get("trades"), mf_win=x.get("winRate"), mf_avg_ret=x.get("avgReturn"))
    # best-rule picks (what actually drove alerts)
    for rid, in c.execute("select distinct bestRuleId from StrategyReview where bestRuleId is not null"):
        if rid in stacks:
            stacks[rid]["was_best"] = True
    # paper trades (clean window), linked by label
    by_label = {v["label"]: k for k, v in stacks.items()}
    for name, n, pnl, wins in c.execute(
            "select ruleName, count(*), sum(pnlDollars), sum(pnlDollars>0) from PaperTrade "
            "where entryTime >= '2026-08-28' and status='CLOSED' group by ruleName"):
        k = by_label.get(name)
        if k:
            stacks[k].update(paper_n=n, paper_pnl=round(pnl or 0, 2), paper_win=round(100 * wins / n, 1))
    OUT.write_text(json.dumps(sorted(stacks.values(), key=lambda d: d["id"]), indent=1))
    print(len(stacks), "stacks;", sum(d["kind"] == "rec" for d in stacks.values()), "recommended;",
          sum(bool(d.get("paper_n")) for d in stacks.values()), "paper-traded")


if __name__ == "__main__":
    main()
