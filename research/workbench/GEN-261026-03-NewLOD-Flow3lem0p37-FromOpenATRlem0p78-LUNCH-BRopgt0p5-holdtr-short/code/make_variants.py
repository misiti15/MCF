"""Mechanic GEN-261026-03: write the three copies' modules / YAML stubs / lineage by hand (the spawn tool cannot add a new
sensor; its two window spawns were renumbered so WB1 = the new sensor, WB2 = the window, WB3 = the combo).
Educational only - not financial advice."""
import json, re
from pathlib import Path
from common import WT, SETUP
D = Path(WT) / "research/workbench" / SETUP
src = (Path(WT) / "research/generator/modules/GEN-261026-03-newlod-lunch-short.py").read_text()
P = f"research/workbench/{SETUP}"
V = {
 "WB1": dict(param="cond.from_pc_atr (new sensor)", old=None, new="<= -1.3", window=(1130, 1400), sensor=True,
             disp="Generated: Lunch New-Low Short (selling) — WB1: down >= 1.3 ATR on the day",
             note="Mechanic: new sensor P11b - close vs prior close <= -1.3 daily ATRs: short only names already down hard on the day (not gap-up fades)"),
 "WB2": dict(param="window", old=[1130, 1400], new=[1130, 1300], window=(1130, 1300), sensor=False,
             disp="Generated: Lunch New-Low Short (selling) — WB2: window ends 13:00",
             note="Mechanic: P6/P7 entry window end 14:00 -> 13:00"),
 "WB3": dict(param="cond.from_pc_atr + window (combo WB1+WB2)", old=None, new="from_pc_atr <= -1.3 AND window 1130-1300",
             window=(1130, 1300), sensor=True, disp="Generated: Lunch New-Low Short (selling) — WB3: down >= 1.3 ATR, window to 13:00",
             note="Mechanic combo = WB1 + WB2 (each passed alone); counted as its own config; module set by hand"),
}
for f in D.glob("modules/*.py"): f.unlink()
for f in D.glob(f"{SETUP}-WB*.yaml"): f.unlink()
lines = []
for wb, v in V.items():
    vid = f"{SETUP}-{wb}"
    m = src.replace("WINDOW = (1130, 1400)", f"WINDOW = ({v['window'][0]}, {v['window'][1]})")
    if v["sensor"]:
        m = m.replace("    ('new_lod', '==', 1.0),\n]", "    ('new_lod', '==', 1.0),\n    ('from_pc_atr', '<=', -1.3),   # Workbench P11b (close vs prior close, daily ATRs)\n]")
        m = m.replace("names=['flow3', 'fromOpen_atr', 'new_lod']", "names=['flow3', 'fromOpen_atr', 'new_lod', 'from_pc_atr']")
        m = m.replace("'new_lod == 1', ", "'new_lod == 1', 'from_pc_atr <= -1.3', ")
    m = m.replace("'window 1130-1400'", f"'window {v['window'][0]}-{v['window'][1]}'")
    hdr = (f"# WORKBENCH VARIANT {vid} (research only, not enabled in any account)\n"
           f"# parent: {SETUP} (research/generator/modules/GEN-261026-03-newlod-lunch-short.py); change: {v['param']} -> {v['new']}; 2026-11-16\n"
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
    - breadth_open
    min_adv: 150000000
    window:
    - {v['window'][0]}
    - {v['window'][1]}
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
print("ok")
