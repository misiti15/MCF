"""Write the Testing 2 lab modules (research/bdi/cwt/live/<NAME>.py), config/account_testing2.yaml, the Testing 2
block of config/setup_names.yaml and docs/live/setup_names.json, all from selection.py.
Educational only - not financial advice.

    python research/bdi/cwt/live/build.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
from selection import S  # noqa: E402

SESSIONS = 426            # open two-year history sessions (package A/B)

TEMPLATE = '''"""Testing 2 (owner-directed forward test, 2026-10-12): {title}.
Educational only - not financial advice. Did NOT pass the gates (open-history result in verify.json / NOTES.md).

Source: CWT package {pkg}, configuration {cfg} (id {cid}), research/bdi/cwt/test_{pkgl}/.
{what}
Exit: {exit_txt} via LabStrategy. Window in config/account_testing2.yaml: {window}.
Signal code: cwt_live_lib.py (ports of the scored rules). Parity: verify.py / verify_a.py -> verify.json.
"""
import cwt_live_lib as L

SIDE = "{side}"
GEOM = "{geom}"
LAYERS = ["{cfg}"]


def mask(df):
    return L.{call}
'''
STOP = '''

def stop_price(f, i):
    return L.{stop}
'''


def stats() -> dict:
    b = pd.read_csv(HERE.parent / "test_b" / "results.csv").set_index("id")
    a = pd.read_csv(HERE.parent / "test_a" / "results.csv").set_index("cid")
    out = {}
    for s in S:
        r = (b if s["pkg"] == "B" else a).loc[s["cid"]]
        verdict = r["verdict"] if s["pkg"] == "B" else ("pass" if r["probation_pass"] else "fail")
        out[s["name"]] = {"n": int(r["n"]), "exp": float(r["exp"]), "t": float(r["t"]), "per_day": r["n"] / SESSIONS,
                          "verdict": verdict}
    return out


def modules():
    for s in S:
        exit_txt = ("structural: stop at the 09:30-10:30 high (stop_price), no target, flat 15:55" if s["geom"] == "S"
                    else f"{s['geom']} (R = 0.25 x daily ATR, flat 15:55)")
        txt = TEMPLATE.format(pkgl=s["pkg"].lower(), exit_txt=exit_txt, **s)
        if s.get("stop"):
            txt += STOP.format(stop=s["stop"])
        (HERE / f"{s['name']}.py").write_text(txt)


HEADER = """# Testing 2 account config (MCF_ACCOUNT=testing2 overlay on config/default.yaml; orders mt2-*, state branch
# mcf-data-testing2, secrets ALPACA_TESTING2_API_KEY / ALPACA_TESTING2_SECRET_KEY). Owner 2026-10-12: a second "minor
# leagues" paper account (the existing Testing account is shown as "Testing 1") that runs "the best 30 setups found from
# the CWT research, even if they are different variants of others".
#
# READ THIS FIRST: NONE of these setups passed the research gates. Every CWT configuration failed (packages A, B, C:
# research/bdi/cwt/test_*/NOTES.md); most are NEGATIVE after costs on the open two-year history. This is an
# owner-directed forward test to collect live data, not a promotion. Only {n_rule} setups qualify under the selection
# rule (research/bdi/cwt/live/NOTES.md; all 942 configurations ranked in ranking.csv); the rest are FILLS, marked
# "[fill]" (next best by expectancy, over the 4-per-family cap). Parity of every module with its scored version, trade
# for trade on the open history: research/bdi/cwt/live/verify.json.
#
# All primary and Testing-1 setups are OFF here, so Testing 2 trades only its own batch. Each setup is a LabStrategy
# module in research/bdi/cwt/live/ (entry at the close of the first qualifying 5-minute bar in its window; exit t1s1 /
# t05s1 / t1s05 with R = 0.25 x daily ATR, or the structural exit "S" = the scored chart-level stop, no target; flat
# 15:55). min_adv = the scored universe (package B adv20 >= $95M, package A >= $1M; the live universe tiers still apply).
# Comments per setup: source configuration, open-history n / exp (R after costs, R = 0.25 x daily ATR) / trades per day.
# Educational only - not financial advice.
account:
  slots: 400
  buying_power_multiple: 3.8
  max_concurrent_positions: 400
  # Playing time: a per-setup cap well below the slot count, so the busy setups (up to ~250 signals/day) cannot fill
  # the account and every setup gets entries (Testing 1 uses 150 with fewer busy setups).
  max_positions_per_strategy: 25
  max_daily_loss_r: 60
  max_trades_per_day: 3000
live:
  # One position per symbol across setups: narrowest (fewest open-history trades/day) first, so subsets are not
  # starved by supersets (swarm W4, 2026-10-10).
  setup_order:"""


def account_yaml(st: dict):
    d = yaml.safe_load((ROOT / "config" / "default.yaml").read_text())
    rows = sorted(S, key=lambda s: st[s["name"]]["per_day"])
    L = [HEADER.format(n_rule=sum(1 for s in S if not s.get("fill")))]
    L += [f"    - {s['name']}   # {st[s['name']]['per_day']:.2f}/day" for s in rows]
    L.append("strategies:\n  # ---- everything from config/default.yaml OFF (primary setups and the disabled library)")
    L += [f"  {k}: {{enabled: false}}" for k in d["strategies"]]
    L.append("  # ---- Testing 2 batch: CWT setups (parity-verified; see research/bdi/cwt/live/verify.json)")
    for s in S:
        x = st[s["name"]]
        L.append(f"  # {s['title']}: CWT package {s['pkg']} {s['cfg']} (id {s['cid']}); open history n {x['n']}, "
                 f"exp {x['exp']:+.4f}R, t {x['t']:.2f}, {x['per_day']:.2f}/day; verdict {x['verdict']}"
                 + (f"; NOTE {s['note']}" if s.get("note") else ""))
        L.append(f"  {s['name']}:\n    enabled: true\n    type: lab\n    module: research/bdi/cwt/live/{s['name']}.py\n"
                 f"    min_adv: {s.get('min_adv', 95_000_000)}\n    window: [{s['window'][0]}, {s['window'][1]}]\n"
                 f"    scale_out_r: null\n    testing2: {{batch: cwt-2026-10-12, source: \"{s['cfg']}\", "
                 f"fill: {str(bool(s.get('fill'))).lower()}}}")
    (ROOT / "config" / "account_testing2.yaml").write_text("\n".join(L) + "\n")


MARK = "# ---- Testing 2 account (owner 2026-10-12)"


def names():
    p = ROOT / "config" / "setup_names.yaml"
    txt = p.read_text()
    if MARK in txt:
        txt = txt[: txt.index(MARK)]
    L = [MARK + ": CWT setups, owner-directed forward test. None passed the gates.",
         "#      Source and open-history numbers: research/bdi/cwt/live/NOTES.md and config/account_testing2.yaml."]
    for s in S:
        what = s["what"].replace('"', '\\"')
        L.append(f"{s['name']}:\n  name: \"{s['title']}\"\n  side: {s['side']}\n  what: \"{what}\"\n  account: testing2")
    p.write_text(txt.rstrip("\n") + "\n" + "\n".join(L) + "\n")
    y = yaml.safe_load(p.read_text())
    (ROOT / "docs" / "live" / "setup_names.json").write_text(json.dumps(y, indent=1) + "\n")


def main():
    st = stats()
    modules()
    account_yaml(st)
    names()
    print(len(S), "setups:", sum(1 for s in S if not s.get("fill")), "by rule +", sum(1 for s in S if s.get("fill")),
          "fills")
    assert len({re.sub(r"\W", "", s["name"]) for s in S}) == len(S)


if __name__ == "__main__":
    main()
