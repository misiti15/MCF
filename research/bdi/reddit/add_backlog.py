"""Append the bdi-rdt-* backlog entries (one per Reddit strategy, failures included) from results.csv / best_few.json.
Run once. Educational only - not financial advice."""
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BL = ROOT / "research" / "backlog.jsonl"
R = pd.read_csv(HERE / "results.csv")
BF = {x["cfg"].split("|")[0] + "|" + x["cfg"].split("|")[1]: x for x in json.load(open(HERE / "best_few.json"))}
CNT = json.load(open(HERE / "counts.json"))
PARENT = {"R02-vwap-reclaim": "bdi-reddit-vwap-reclaim-hold", "R04-gap-go": "bdi-reddit-gap-go-hod-fullday",
          "R06-red-green": "wi-red-to-green", "R08-bull-flag": "bdi-reddit-bull-flag-pole",
          "R14-ict-fvg": "bdi-reddit-ict-fvg-retrace", "R18-orb-fvg": "bdi-reddit-ict-fvg-retrace",
          "R15-sweep": "bdi-reddit-level-sweep-reclaim", "R16-rel-strength": "bdi-reddit-rdt-rrs-fullday",
          "R17-pd-retest": "bdi-reddit-pdhl-break-retest"}
MODS = {"R04-gap-go|short": "research/bdi/reddit/modules/RD1-gapgo-lodbreak-rvol-short-FD.py",
        "R05-gap-fill|short": "research/bdi/reddit/modules/RD2-gapfill-openloss-rvol-slope-short-FD.py",
        "R03-vwap-fade|long": "research/bdi/reddit/modules/RD3-vwapfade-band1-slope-inplay-long-FD.py"}


def main():
    have = {json.loads(l)["id"] for l in BL.read_text().splitlines() if l.strip()}
    from strategies import STRATS  # noqa: E402
    new = []
    for name, (fn, p, grid, key) in STRATS.items():
        sub = R[R.strategy == name]
        eid = "bdi-rdt-" + name.lower()
        if eid in have:
            continue
        doc = " ".join((fn.__doc__ or "").split())
        parts = []
        for x in sub.itertuples():
            parts.append(f"{x.side}: base {x.base_geom} n {x.base_n} ({x.base_per_day:.0f}/day) {x.base_exp:+.3f}R t {x.base_t} "
                         f"(up {x.base_up:+.3f} / flat {x.base_flat:+.3f} / down {x.base_down:+.3f}); best of 64 by t "
                         f"[{x.best_cfg}] n {x.best_n} {x.best_exp:+.3f}R t {x.best_t} (up {x.best_up:+.3f} / down "
                         f"{x.best_down:+.3f}, busiest day {x.best_maxday:.0%}); {x.positive_exp}/{x.configs} configs exp > 0")
        bf = [v for k, v in BF.items() if k.startswith(name + "|")]
        extra = ""
        for v in bf:
            extra += (f" Best-few (amendment A) {v['cfg']}: n {v['n']} exp {v['exp']:+.4f} t {v['t']} WF {v['wf_share']} "
                      f"plateau {v['plateau_mean']:+.4f} ex-best-day {v['ex_best_day']:+.4f} -> fails the probation bar.")
        e = {"id": eid, "title": f"Reddit {name}: {doc.split(':')[0].split(' (')[0][:90]} (full day, long+short, 16 filter sets)",
             "added": "2026-10-09", "source": "BDI Reddit dump study 2026-10-09 (research/bdi/reddit/NOTES.md; 1.70M posts/comments 2019-2025)",
             "category": "setup", "hypothesis": doc[:600], "module": None, "variant": None, "status": "failed",
             "configs_tried": int(sub.configs.sum()),
             "notes": ("Open 2-year lab history, 09:50-15:00 bar close, first trade per symbol-day, production costs, exits "
                       "t1s1/t05s1/t1s05 + structural S. " + " | ".join(parts) + "." + extra +
                       f" Study N = {CNT['configs_total']} (t_required {CNT['t_required']}); no configuration met the live-probation "
                       "bar (n>=150, up>0 and down>0, t>=2, WF>=0.6, plateau>0, ex-best-day>0, busiest day<=10%). Longs are "
                       "positive only in up sessions and shorts only in down sessions (market beta). Rework (rule 18) would need "
                       "a regime gate known at entry. Not scored on the locked block. Educational only - not financial advice.")}
        if name in PARENT:
            e["parent"] = PARENT[name]
            e["notes"] = f"Tests the earlier idea {PARENT[name]} (that entry stays as written). " + e["notes"]
        for k, path in MODS.items():
            if k.startswith(name + "|"):
                e["lab_module"] = path
        new.append(e)
    with open(BL, "a") as fh:
        for e in new:
            fh.write(json.dumps(e) + "\n")
    print("appended", len(new))


if __name__ == "__main__":
    main()
