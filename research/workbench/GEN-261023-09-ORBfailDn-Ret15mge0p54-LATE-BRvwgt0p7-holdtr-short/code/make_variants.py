"""Mechanic GEN-261023-09: write the copies' modules / YAML stubs / lineage by hand (the spawn tool cannot add a sensor;
all four written the same way for consistency). Educational only - not financial advice."""
import json
from pathlib import Path
from common import WT, SETUP
D = Path(WT) / "research/workbench" / SETUP
SRC = "research/generator/modules/GEN-261023-09-orbfaildn-late-short.py"
src = (Path(WT) / SRC).read_text()
P = f"research/workbench/{SETUP}"
NAME = "Generated: Late Failed-Breakdown Pop Short"
RA = ("ret3_atr", ">=", 0.20, "3-bar return in daily ATRs (Workbench P11b: the pop is big for THIS stock)")
AD = ("adx7", ">=", 44.0, "ADX(7) (Workbench P11c: the pop is a strong directional push, not chop)")
V = {
 "WB1": dict(param="window", old=[1400, 1500], new=[1430, 1500], window=(1430, 1500), add=[],
             disp=f"{NAME} — WB1: window 14:30-15:00", note="Mechanic: P6/P7 entry window start 14:00 -> 14:30"),
 "WB2": dict(param="cond.ret3_atr (new sensor)", old=None, new=">= 0.20", window=(1400, 1500), add=[RA],
             disp=f"{NAME} — WB2: pop >= 0.20 daily ATR", note="Mechanic: new sensor P11b - the 15-minute pop must also be >= 0.20 daily ATRs (size relative to the stock's own range, not only 0.54%)"),
 "WB3": dict(param="window + cond.ret3_atr (combo WB1+WB2)", old=None, new="window 1430-1500 AND ret3_atr >= 0.20", window=(1430, 1500), add=[RA],
             disp=f"{NAME} — WB3: 14:30-15:00, pop >= 0.20 ATR", note="Mechanic combo = WB1 + WB2 (each passed alone); counted as its own config; module set by hand"),
 "WB4": dict(param="window + cond.ret3_atr + cond.adx7 (combo WB3 + new layer)", old=None, new="window 1430-1500 AND ret3_atr >= 0.20 AND adx7 >= 44",
             window=(1430, 1500), add=[RA, AD], disp=f"{NAME} — WB4: 14:30-15:00, pop >= 0.20 ATR, ADX(7) >= 44",
             note="Mechanic combo = WB3 + new layer P11c ADX(7) >= 44 (experimental layer; fails alone, helps on top of WB3); counted as its own config; module set by hand"),
}
for f in D.glob("modules/*.py"): f.unlink()
for f in D.glob(f"{SETUP}-WB*.yaml"): f.unlink()
for wb, v in V.items():
    vid = f"{SETUP}-{wb}"
    m = src.replace("WINDOW = (1400, 1500)", f"WINDOW = ({v['window'][0]}, {v['window'][1]})")
    names = ["orb_fail_dn", "ret3"] + [a[0] for a in v["add"]]
    m = m.replace("names=['orb_fail_dn', 'ret3']", f"names={names!r}")
    adds = "".join(f"    ('{a[0]}', '{a[1]}', {a[2]}),   # {a[3]}\n" for a in v["add"])
    m = m.replace("    ('ret3', '>=', 0.54),\n]", "    ('ret3', '>=', 0.54),\n" + adds + "]")
    lay = "".join(f"'{a[0]} {a[1]} {a[2]:g}', " for a in v["add"])
    m = m.replace("'ret3 >= 0.54', 'window 1400-1500'", f"'ret3 >= 0.54', {lay}'window {v['window'][0]}-{v['window'][1]}'")
    assert m != src or wb == "WB1"
    hdr = (f"# WORKBENCH VARIANT {vid} (research only, not enabled in any account)\n"
           f"# parent: {SETUP} ({SRC}); change: {v['param']} -> {v['new']}; 2026-11-16\n"
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
    - breadth
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
json.dump({wb: dict(param=v["param"], old=v["old"], new=v["new"], disp=v["disp"], note=v["note"], window=v["window"]) for wb, v in V.items()},
          open(D / "code" / "variants_def.json", "w"), indent=1)
print("ok")
