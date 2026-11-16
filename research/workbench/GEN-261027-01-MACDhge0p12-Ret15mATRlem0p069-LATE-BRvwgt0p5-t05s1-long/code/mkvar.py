"""Mechanic GEN-261027-01: hand-built copies WB3 (new gate: breadth change since 09:50 <= +0.20), WB4 = WB1 + WB3,
WB5 = WB1 + WB2 + WB3 (module + YAML stub + lineage + README log), in the style of the spawn tool. Educational only - not financial advice."""
import json, re, yaml
from pathlib import Path
S = "GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long"
D = Path("research/workbench") / S
src = Path("research/generator/modules/GEN-261027-01-macdh-hi-late-long.py").read_text()
GATE = '''

# Workbench gate (Mechanic 2026-11-16): market breadth must not have widened by more than BR_CHG_MAX since 09:50:
# br_chg = breadth at this bar - breadth at the 09:50 bar of the same session (owner rule: market-state gates are
# measured AFTER 09:50, vs the 09:50 state). Missing 09:50 value -> NaN -> no entry (fail safe).
BR_CHG_MAX = 0.20


def br_chg(df) -> np.ndarray:
    import pandas as pd
    if "breadth" not in df.columns:
        return np.full(len(df), np.nan)
    b = df["breadth"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    day = df["date"].astype(str).to_numpy() if "date" in df.columns else np.zeros(len(df), dtype=object)
    s = pd.Series(np.where(tod == 950, b, np.nan)).groupby(day).transform("max").to_numpy(dtype=float)
    return b - s
'''
def make(n, window, min_adv, desc, name, param, old, new, note):
    s = src
    s = s.replace("WINDOW = (1400, 1500)", f"WINDOW = ({window[0]}, {window[1]})")
    s = s.replace("MIN_ADV = 20000000.0", f"MIN_ADV = {float(min_adv)}")
    s = s.replace("'window 1400-1500']", f"'window {window[0]}-{window[1]}', 'breadth change since 09:50 <= +0.20']")
    s = s.replace("\n\ndef mask(df)", GATE + "\n\ndef mask(df)")
    s = s.replace("    return np.asarray(m, dtype=bool)", "        m &= br_chg(df) <= BR_CHG_MAX\n    return np.asarray(m, dtype=bool)")
    vid = f"{S}-WB{n}"
    hdr = (f"# WORKBENCH VARIANT {vid} (research only, not enabled in any account)\n"
           f"# parent: {S} (research/generator/modules/GEN-261027-01-macdh-hi-late-long.py); change: {desc}; 2026-11-16\n"
           f"# Built by hand (the spawn tool changes one existing part; this adds a new gate). Educational only - not financial advice.\n")
    mp = D / "modules" / f"{vid}.py"; mp.write_text(hdr + s)
    blk = {"enabled": False, "type": "lab", "module": str(mp), "context": ["breadth"], "min_adv": int(min_adv),
           "window": list(window), "refire": False, "scale_out_r": None,
           "tags": ["workbench", f"parent:{S}"],
           "workbench": {"parent": S, "param": param, "old": old, "new": new, "date": "2026-11-16", "note": note, "display_name": name}}
    y = (f"# Workbench variant stub (research only). NOT an account config: no account loads this file.\n"
         f"# Parent {S}; change: {desc}. Educational only - not financial advice.\n")
    (D / f"{vid}.yaml").write_text(y + yaml.safe_dump({"strategies": {vid: blk}}, sort_keys=False, allow_unicode=True))
    rec = {"id": vid, "parent": S, "param": param, "old": old, "new": new, "date": "2026-11-16", "note": note,
           "parent_account": "testinge", "status": "research only (not enabled in any account)",
           "files": {"module": str(mp), "config": str(D / f"{vid}.yaml")}, "display_name": name}
    with open(D / "variants.jsonl", "a") as f: f.write(json.dumps(rec) + "\n")
    with open(D / "README.md", "a") as f:
        f.write(f"- 2026-11-16 `{vid}`: {desc} - {note}. Status: research only; next: backtest.\n")
make(3, (1400, 1500), 20e6, "new gate: breadth change since 09:50 <= +0.20",
     "Generated: Late Pullback Buy (MACD rising) — WB3: breadth not up > 0.20 since 09:50",
     "gate.br_chg (new)", None, "<= 0.20", "Mechanic: new gate P11b - skip when the share of stocks above VWAP has risen more than 0.20 since the 09:50 bar (broad rally / squeeze afternoons)")
make(4, (1400, 1430), 20e6, "combo WB1 + WB3: window 14:00-14:30 AND breadth change since 09:50 <= +0.20",
     "Generated: Late Pullback Buy (MACD rising) — WB4: 14:00-14:30 + breadth gate",
     "window + gate.br_chg (combo WB1+WB3)", [1400, 1500], "window [1400, 1430] AND br_chg <= 0.20", "Mechanic combo = WB1 + WB3 (each passed alone); counted as its own config; module set by hand")
make(5, (1400, 1430), 100e6, "combo WB1 + WB2 + WB3: window 14:00-14:30 AND min_adv $100M AND breadth change since 09:50 <= +0.20",
     "Generated: Late Pullback Buy (MACD rising) — WB5: 14:00-14:30, $100M ADV, breadth gate",
     "window + min_adv + gate.br_chg (combo WB1+WB2+WB3)", [1400, 1500], "window [1400, 1430] AND min_adv 100000000 AND br_chg <= 0.20", "Mechanic combo = WB1 + WB2 + WB3 (each passed alone); counted as its own config; module set by hand")
print("ok")
