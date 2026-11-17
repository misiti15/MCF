"""Write the hand-built Workbench copies WB2 / WB3 (module + YAML stub + lineage), same format as mcf.research.workbench spawn."""
import json, yaml
from pathlib import Path
P = "RW6G1-ns2-up3-vwap2sd-short-FD"; NAME = "Big Gainer Fade, VWAP Band Guard (all day)"
D = Path(f"research/workbench/{P}"); src = Path(f"research/bdi/fullday/{P}.py").read_text()
ZFUN = '''

def vwap_z(df) -> np.ndarray:
    """(close - VWAP) / volume-weighted SD of today's 5-min bars (typical price), the same VWAP / SD as vwap_band_block.
    NaN without volume or while SD = 0 (first bar) -> no signal (fail safe)."""
    if "volume" not in df:
        return np.full(len(df), np.nan)
    key = _keys(df)
    h, l, c, v = (df[x].to_numpy(dtype=float) for x in ("high", "low", "close", "volume"))
    tp = (h + l + c) / 3
    g = pd.Series(key)
    cv = pd.Series(v).groupby(g).cumsum().to_numpy().copy()
    cv[cv == 0] = np.nan
    vw = pd.Series(tp * v).groupby(g).cumsum().to_numpy() / cv
    sd = np.sqrt(np.clip(pd.Series(tp * tp * v).groupby(g).cumsum().to_numpy() / cv - vw * vw, 0, None))
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(sd > 0, (c - vw) / sd, np.nan)
'''
def build(n, title, what, clauses, layers, window, min_adv, note, tests, verdict):
    wid = f"{P}-WB{n}"; disp = f"{NAME} — WB{n}: {title}"
    head = (f'"""{wid} - Workbench copy (Mechanic 2026-11-16) of {P}: {what}.\nDisplay name: "{disp}". Research only until deployed '
            f'by the Workbench rules (RESULTS.md). Parent text follows.\n')
    body = src.split('"""', 2)
    s = head + body[1] + '"""' + body[2]
    s = s.replace('    "full day: bar close 09:50-15:00 ET (YAML window [950, 1500])",\n',
                  "".join(f'    "{x} (Workbench WB{n})",\n' for x in layers) + f'    "bar close {window[0]//100:02d}:{window[0]%100:02d}-15:00 ET (YAML window {list(window)})",\n')
    s = s.replace("\n\ndef mask(df)", ZFUN + "\n\ndef mask(df)")
    s = s.replace("    return base & ~vwap_band_block(df)", "    base = base & ~vwap_band_block(df)\n" + clauses + "    return base")
    (D / "modules" / f"{wid}.py").write_text(s)
    cfg = {"strategies": {wid: {"enabled": False, "refire": True, "refire_cooldown": 1, "type": "lab",
           "module": f"research/workbench/{P}/modules/{wid}.py", "min_adv": min_adv, "window": list(window), "scale_out_r": None,
           "live_scale_out": False, "tags": ["workbench", f"parent:{P}"],
           "workbench": {"parent": P, "param": "module clause + window/min_adv" if n == 3 else "module clause", "old": None, "new": what, "date": "2026-11-16", "note": note}}}}
    (D / f"{wid}.yaml").write_text("# Workbench variant stub (research only). NOT an account config: no account loads this file.\n"
                                   f"# Parent {P}; {what}. Mechanic 2026-11-16. Educational only - not financial advice.\n" + yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True))
    rec = {"id": wid, "parent": P, "display_name": disp, "param": cfg["strategies"][wid]["workbench"]["param"], "old": None, "new": what,
           "date": "2026-11-16", "note": note, "parent_account": "graveyard", "verdict": verdict.split(";")[0], "status": verdict,
           "files": {"module": f"research/workbench/{P}/modules/{wid}.py", "config": f"research/workbench/{P}/{wid}.yaml"}, "tests": tests}
    with open(D / "variants.jsonl", "a") as f: f.write(json.dumps(rec) + "\n")
    return wid
import sys
T = json.loads(sys.argv[1])
Z = "    with np.errstate(invalid=\"ignore\"):\n        base = base & (vwap_z(df) >= 0.5)   # WB: close at least +0.5 SD above VWAP (NaN -> no signal)\n"
G = "    with np.errstate(invalid=\"ignore\"):\n        base = base & (col(\"gap\") <= 2.0)   # WB: opening gap <= +2% (no gap-and-go runners)\n"
build(2, "close >= VWAP + 0.5 SD at the signal bar", "new sensor: close >= VWAP + 0.5 SD (module clause)", Z,
      ["close at least +0.5 SD above VWAP at the signal bar"], (950, 1500), 95000000, "Mechanic: bench config 'V27'", T["WB2"], T["WB2s"])
build(3, "start 11:00 + close >= VWAP + 0.5 SD + ADV >= $150M + gap <= +2%",
      "start 11:00 + close >= VWAP + 0.5 SD + ADV >= $150M + opening gap <= +2%", Z + G,
      ["close at least +0.5 SD above VWAP at the signal bar", "opening gap <= +2%", "20-day ADV >= $150M (YAML min_adv)"],
      (1100, 1500), 150000000, "Mechanic: bench config 'D2 C2 + gap <= +2%'", T["WB3"], T["WB3s"])
