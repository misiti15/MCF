"""Mechanic NM-RWN5: write the three copies' modules / YAML stubs / lineage by hand (the spawn tool cannot add a new
sensor, and the parent mask hard-codes its own 09:50 start next to the config window, so both are edited together).
Educational only - not financial advice."""
import json
from pathlib import Path
from common import WT, SETUP
D = Path(WT) / "research/workbench" / SETUP
PM = "research/swarm1017/rework-ns/modules/RWN5-ns3-mon-weakrs-short.py"
src = (Path(WT) / PM).read_text()
P = f"research/workbench/{SETUP}"
NAME = "Monday Weak-RS NS3 Short (near-miss)"
V = {
 "WB1": dict(param="cond.volumeRatio (new sensor)", old=None, new=">= 0.45", lo=950, vr=True,
             disp=f"{NAME} — WB1: reclaim bar volume >= 0.45x avg",
             note="Mechanic: new sensor P9b - the VWAP-reclaim bar's volume >= 0.45 x its 20-bar average (skip dead-volume crosses)"),
 "WB2": dict(param="window", old=[950, 1130], new=[1005, 1130], lo=1005, vr=False,
             disp=f"{NAME} — WB2: entries from 10:05",
             note="Mechanic: P6/P14 entry window start 09:50 -> 10:05 (config window and the module's own tod bound)"),
 "WB3": dict(param="cond.volumeRatio + window (combo WB1+WB2)", old=None, new="volumeRatio >= 0.45 AND window 1005-1130",
             lo=1005, vr=True, disp=f"{NAME} — WB3: reclaim volume >= 0.45x, from 10:05",
             note="Mechanic combo = WB1 + WB2 (each passed alone); counted as its own config; module set by hand"),
}
for f in D.glob("modules/*.py"): f.unlink()
for f in D.glob(f"{SETUP}-WB*.yaml"): f.unlink()
(D / "modules").mkdir(exist_ok=True)
recs = []
for wb, v in V.items():
    vid = f"{SETUP}-{wb}"
    m = src
    if v["lo"] != 950:
        m = m.replace("(tod >= 950) & (tod <= 1130)", f"(tod >= {v['lo']}) & (tod <= 1130)")
        m = m.replace("'09:50-11:30 ET'", f"'{v['lo'] // 100:02d}:{v['lo'] % 100:02d}-11:30 ET'")
    if v["vr"]:
        m = m.replace("    dow, spy = _dow(df), _spy_fo(df)\n", "    dow, spy = _dow(df), _spy_fo(df)\n    vr = col(\"volumeRatio\")   # Workbench P9b\n")
        m = m.replace("& (fo - spy < 0) &", "& (fo - spy < 0) & (vr >= 0.45) &")
        m = m.replace("'stock fromOpen below SPY fromOpen [live code needed]',", "'stock fromOpen below SPY fromOpen [live code needed]', 'reclaim bar volume >= 0.45 x its 20-bar average',")
    assert m != src
    hdr = (f"# WORKBENCH VARIANT {vid} (research only, not enabled in any account)\n"
           f"# parent: {SETUP} ({PM}); change: {v['param']} -> {v['new']}; 2026-11-16\n"
           "# Mechanic-tested (RESULTS.md); testing arena only after the close with ledger + assignments. Educational only - not financial advice.\n")
    (D / "modules" / f"{vid}.py").write_text(hdr + m)
    y = f"""# Workbench variant stub (research only). NOT an account config: no account loads this file.
# Parent {SETUP}; change: {v['param']} -> {v['new']}. Educational only - not financial advice.
strategies:
  {vid}:
    enabled: false
    type: lab
    module: {P}/modules/{vid}.py
    context:
    - spy_fo
    min_adv: 95000000
    window:
    - {v['lo']}
    - 1130
    refire: false
    scale_out_r: null
    tags:
    - workbench
    - parent:{SETUP}
    workbench:
      parent: {SETUP}
      param: "{v['param']}"
      old: {json.dumps(v['old'])}
      new: {json.dumps(v['new'])}
      date: '2026-11-16'
      note: "{v['note']}"
      display_name: "{v['disp']}"
"""
    (D / f"{vid}.yaml").write_text(y)
    recs.append((vid, v))
print("ok", [r[0] for r in recs])
