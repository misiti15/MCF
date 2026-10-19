"""Setup Generator seeds from the weekly Setup lab scan (owner 2026-10-19). Educational only - not financial advice.

The weekly discover workflow (.github/workflows/discover.yml -> mcf/discovery.py) publishes discovery/latest.json on
the `mcf-data` branch: layered rules (mcf/layers.py labels such as "RSI14 > 65", "gap within 2%", "09:50-11:00") that
were found on older sessions and replicated on newer ones. Each REPLICATED candidate is translated here into a few
generator Specs, which join the random specs in the same quick screen, the same ranking and the same pick rules
(apply.run): no special treatment, and every seed screened counts in n_tried and goes to the registry.

Translation (mcf/layers.py definition -> live arena indicator on the 5-minute lab frame; units match):
  RSI14 < 35 / 35-65 / > 65     -> rsi (RSI(14), frame column)              <, range, >
  above / below 20 SMA          -> sma20_dist_pct (close vs 5-min SMA20 %)  > 0 / < 0
  above / below VWAP            -> vwap_atr (close - session VWAP)          > 0 / < 0
  gap down > 2% / within / up   -> gap (open vs prior close %)              < -2 / -2..2 / > 2
  down > 2% / within 2% / up > 2% from open -> fromOpen (close vs open %)   < -2 / -2..2 / > 2
  new high / low of day         -> new_hod / new_lod == 1
  HH:MM-HH:MM time layer        -> the generator WINDOW with the largest overlap / union
NOT mapped (the candidate is skipped and the reason recorded): rvol layers. The lab rule's rvol is cumulative volume
vs the same time of day on prior sessions; neither the screen panel nor the live LabStrategy frame has it (arena
rvol_day is a volumeRatio proxy on a different scale), so any threshold would be a different rule.

Generator rules a lab rule lacks are added as a small fixed set of variants (<= 6 per candidate):
  * context filter (lab rules have none): side-aligned SPY since open (> 0 long / < 0 short) and breadth vs VWAP
    (> 0.5 long / < 0.5 short)
  * time window, if the rule has none: AM, MID and PM (then only the SPY context)
  * geometry: t1s1 (the lab's own +1R-before-1R outcome), t05s1, holdtr; with no time layer only t1s1 and holdtr
Liquidity floor $20M (the panel floor). A lab rule may be state-only, so seeds need no trigger (spec.valid_seed).
Registry keys and prior families are respected exactly as for random specs.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from .spec import ADV_FLOORS, WINDOWS, Spec, valid_seed

ROOT = Path(__file__).resolve().parents[3]
BRANCH, PATH = "origin/mcf-data", "discovery/latest.json"
MAX_VARIANTS = 6

LAYER_MAP = {
    "RSI14 < 35": [("rsi", "<", 35.0)],
    "RSI14 35-65": [("rsi", ">=", 35.0), ("rsi", "<=", 65.0)],
    "RSI14 > 65": [("rsi", ">", 65.0)],
    "above 20 SMA": [("sma20_dist_pct", ">", 0.0)],
    "below 20 SMA": [("sma20_dist_pct", "<", 0.0)],
    "above VWAP": [("vwap_atr", ">", 0.0)],
    "below VWAP": [("vwap_atr", "<", 0.0)],
    "gap down > 2%": [("gap", "<", -2.0)],
    "gap within 2%": [("gap", ">=", -2.0), ("gap", "<=", 2.0)],
    "gap up > 2%": [("gap", ">", 2.0)],
    "down > 2% from open": [("fromOpen", "<", -2.0)],
    "within 2% of open": [("fromOpen", ">=", -2.0), ("fromOpen", "<=", 2.0)],
    "up > 2% from open": [("fromOpen", ">", 2.0)],
    "new high of day": [("new_hod", "==", 1.0)],
    "new low of day": [("new_lod", "==", 1.0)],
}
UNMAPPABLE = {
    "rvol": "rvol (cumulative volume vs the same time on prior sessions) is not in the screen panel or the live lab "
            "frame; arena rvol_day is a volumeRatio proxy on another scale",
}
CONTEXTS = {"long": [("spy_fo", ">", 0.0), ("breadth", ">", 0.5)],
            "short": [("spy_fo", "<", 0.0), ("breadth", "<", 0.5)]}
GEOMS_WINDOWED = ("t1s1", "t05s1", "holdtr")
GEOMS_NO_WINDOW = ("t1s1", "holdtr")
NO_WINDOW = ("AM", "MID", "PM")
_TIME = re.compile(r"^(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})$")


def _hhmm_min(h, m) -> int:
    return int(h) * 60 + int(m)


def nearest_window(layer: str) -> str | None:
    """'11:00-13:30' -> the WINDOWS name with the largest overlap / union (bar-close minutes)."""
    m = _TIME.match(layer.strip())
    if not m:
        return None
    a, b = _hhmm_min(m[1], m[2]), _hhmm_min(m[3], m[4])
    best, bj = None, 0.0
    for name, (lo, hi) in WINDOWS.items():
        lo_m, hi_m = _hhmm_min(lo // 100, lo % 100), _hhmm_min(hi // 100, hi % 100)
        inter = max(0, min(b, hi_m) - max(a, lo_m))
        union = max(b, hi_m) - min(a, lo_m)
        j = inter / union if union > 0 else 0.0
        if j > bj:
            best, bj = name, j
    return best


def translate(layers: list[str]) -> tuple[str | None, list | None, str | None]:
    """Lab layers -> (window or None, stock conditions, None) or (None, None, reason) when not faithfully mappable."""
    window, conds = None, []
    for lab in layers:
        lab = str(lab).strip()
        if _TIME.match(lab):
            w = nearest_window(lab)
            if w is None or window is not None:
                return None, None, f"time layer {lab!r} has no generator window (or two time layers)"
            window = w
            continue
        if lab in LAYER_MAP:
            conds += LAYER_MAP[lab]
            continue
        for prefix, why in UNMAPPABLE.items():
            if lab.startswith(prefix):
                return None, None, f"{lab!r}: {why}"
        return None, None, f"{lab!r}: no mapping to a live arena indicator"
    if not conds:
        return None, None, "no stock condition besides the time window"
    return window, conds, None


def variants(side: str, window: str | None, conds: list) -> list[Spec]:
    """The fixed variant set (see module doc), at most MAX_VARIANTS."""
    if window is None:
        wins, ctxs, geoms = NO_WINDOW, CONTEXTS[side][:1], GEOMS_NO_WINDOW
    else:
        wins, ctxs, geoms = (window,), CONTEXTS[side], GEOMS_WINDOWED
    out = [Spec(side, w, g, float(ADV_FLOORS[0]), [c] + list(conds)) for w in wins for c in ctxs for g in geoms]
    return out[:MAX_VARIANTS]


def load_discovery(path: str | Path | None = None, fetch: bool = True, log=print) -> dict | None:
    """The latest discovery report: a local path, else origin/mcf-data:discovery/latest.json via git. Fail soft."""
    try:
        if path is not None:
            return json.loads(Path(path).read_text())
        if fetch:
            subprocess.run(["git", "fetch", "-q", "origin", "mcf-data"], cwd=ROOT, capture_output=True, timeout=90)
        r = subprocess.run(["git", "show", f"{BRANCH}:{PATH}"], cwd=ROOT, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            log(f"seeds: no discovery report ({r.stderr.strip()[:120]})")
            return None
        return json.loads(r.stdout)
    except Exception as e:      # noqa: BLE001 - no seeds is a valid outcome
        log(f"seeds: no discovery report ({type(e).__name__}: {e})")
        return None


def generate(disc: dict | None, seen_keys: set, avoid_fams: set, log=print) -> tuple[list[Spec], dict, dict]:
    """Seed specs from a discovery report. Returns (specs, info for the run report, key -> seed record)."""
    info = {"source": None, "candidates": 0, "replicated": 0, "mapped": 0, "skipped": [], "variants": 0,
            "rejected": {"invalid": 0, "seen": 0, "tried_family": 0, "dup": 0}, "seeds": 0}
    if not disc:
        return [], info, {}
    src = f"discovery {disc.get('generated')}"
    cands = disc.get("candidates") or []
    info.update({"source": src, "candidates": len(cands)})
    specs, meta = [], {}
    for c in cands:
        if not c.get("replicated"):
            continue
        info["replicated"] += 1
        layers = [str(x) for x in (c.get("layers") or [])]
        side = c.get("side")
        if side not in CONTEXTS:
            info["skipped"].append({"side": side, "layers": layers, "reason": "unknown side"})
            continue
        window, conds, why = translate(layers)
        if why:
            info["skipped"].append({"side": side, "layers": layers, "reason": why})
            continue
        info["mapped"] += 1
        for s in variants(side, window, conds):
            info["variants"] += 1
            ok, _ = valid_seed(s)
            k = s.key()
            if not ok:
                info["rejected"]["invalid"] += 1
            elif k in seen_keys:
                info["rejected"]["seen"] += 1
            elif k in meta:
                info["rejected"]["dup"] += 1
            elif s.family() in avoid_fams:
                info["rejected"]["tried_family"] += 1
            else:
                specs.append(s)
                meta[k] = {"source": src, "layers": layers, "side": side,
                           "lab": {x: c.get(x) for x in ("train_n", "train_exp_r", "test_n", "test_exp_r")}}
    info["seeds"] = len(specs)
    log(f"seeds: {src}: {info['replicated']} replicated, {info['mapped']} mapped, {len(info['skipped'])} skipped, "
        f"{len(specs)} seed specs (rejected {info['rejected']})")
    return specs, info, meta
