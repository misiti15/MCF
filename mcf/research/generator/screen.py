"""Setup Generator quick screen: generate random specs, score them on the open history, pick the best N per day.

Trades: the FIRST qualifying 5-minute bar per symbol-day inside the window (bar close lo <= tod <= hi, as the YAML
`window` binds LabStrategy), production-cost R (generator.data). Day-clustered statistics (trades on one day are
correlated: se = sqrt(sum_d (S_d - n_d mu)^2) / n). Random baseline: the same-date same-minute universe mean of the
same side x geometry; excess = r - baseline.

Quality score (fixed before the first run, 2026-10-19; the account is for exploration and the owner set NO promotion
rules for GEN setups, so this only orders candidates):
  tier 1 = train AND valid expectancy > 0 AND 1..40 trades/day universe-wide (enough to collect data, selective
           enough to be a setup rather than a market-wide regime bet; 80 slots, 16 per setup)
  score  = min(day-clustered t train, t valid) + 0.5 [expectancy > 0 in up AND down sessions]
           + 0.25 [excess over random > 0 on train AND valid] - 1 [< 1 trade/day]
  ranked by (tier 1, score); a candidate needs >= 30 train and >= 15 valid trades and <= 100 trades/day to be ranked.
Overlap: a pick is skipped when its symbol-day trades overlap > 60% (|A and B| / min(|A|, |B|)) with an enabled
setup of any account (lab modules evaluated on sample months) or with another GEN setup (on the full history).
Every spec scored is counted (n_tried) and its key goes to the registry. Educational only - not financial advice.
"""
from __future__ import annotations

import ast
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .spec import CONTEXT, IND, QUANT_HI, QUANT_LO, WINDOWS, Spec, family_sig, random_spec, valid

ROOT = Path(__file__).resolve().parents[3]
MIN_TRAIN, MIN_VALID = 30, 15
MIN_PER_DAY, MAX_PER_DAY_TIER1, MAX_PER_DAY = 1.0, 40.0, 100.0
OVERLAP_MAX = 0.60
_P = None          # the Panel, shared with forked workers (copy-on-write)


# ------------------------------------------------------------------------------------------------ thresholds
def quantile_table(P, names=None, seed: int = 0, n: int = 400_000) -> dict:
    """indicator -> {q: value} from a fixed random sample of TRAIN rows (thresholds are never fit on valid)."""
    rng = np.random.default_rng(seed)
    tr = np.flatnonzero(P.split == 0)
    pick = np.sort(rng.choice(tr, size=min(n, len(tr)), replace=False))
    out = {}
    for k in (names or [k for k in IND if k in P.a]):
        v = P.a[k][pick].astype(np.float64)
        v = v[np.isfinite(v)]
        if len(v) < 1000:
            continue
        qs = np.quantile(v, QUANT_LO + QUANT_HI)
        out[k] = {q: float(x) for q, x in zip(QUANT_LO + QUANT_HI, qs)}
    return out


# ------------------------------------------------------------------------------------------------ evaluation
def _cmp(a, op, v):
    with np.errstate(invalid="ignore"):
        if op == "<=":
            return a <= v
        if op == "<":
            return a < v
        if op == ">=":
            return a >= v
        if op == ">":
            return a > v
        return a == v


def spec_mask_idx(P, spec: Spec) -> np.ndarray:
    """Row indices where every condition holds (ascending)."""
    lo, hi = WINDOWS[spec.window]
    tod = P.a["tod"]
    ctx = [c for c in spec.conds if c[0] in CONTEXT]
    m = (tod >= lo) & (tod <= hi) & (P.a["adv20"] >= spec.min_adv)
    for c in ctx:
        m &= _cmp(P.a[c[0]], c[1], np.float16(c[2]))
    idx = np.flatnonzero(m)
    for c in spec.conds:
        if c[0] in CONTEXT:
            continue
        idx = idx[_cmp(P.a[c[0]][idx].astype(np.float32), c[1], np.float32(np.float16(c[2])))]
        if not len(idx):
            break
    return idx


def first_rows(sd: np.ndarray, idx: np.ndarray) -> np.ndarray:
    if not len(idx):
        return idx
    s = sd[idx]
    return idx[np.r_[True, s[1:] != s[:-1]]]


def _dstats(r, day):
    n = len(r)
    if n == 0:
        return {"n": 0, "exp_r": None, "t": None, "win": None, "days": 0}
    mu = float(r.mean())
    u, inv = np.unique(day, return_inverse=True)
    S = np.bincount(inv, r)
    N = np.bincount(inv)
    se = float(np.sqrt(((S - N * mu) ** 2).sum()) / n)
    return {"n": int(n), "exp_r": round(mu, 4), "t": round(mu / se, 2) if se > 0 else None,
            "win": round(float((r > 0).mean()), 3), "days": int(len(u))}


def evaluate(P, spec: Spec, keep_keys: bool = False) -> dict:
    out = f"{spec.side}_{spec.geom}"
    idx = first_rows(P.sd, spec_mask_idx(P, spec))
    r = P.a["r_" + out][idx].astype(np.float64)
    ok = np.isfinite(r)
    idx, r = idx[ok], r[ok]
    day = P.day[idx]
    sp = P.split[idx]
    res = {"key": spec.key()}
    for k, lab in ((0, "train"), (1, "valid")):
        res[lab] = _dstats(r[sp == k], day[sp == k])
    res["all"] = _dstats(r, day)
    reg = P.day_regime[day]
    for k, lab in ((2, "exp_up"), (0, "exp_down"), (1, "exp_flat")):
        res[lab] = round(float(r[reg == k].mean()), 4) if (reg == k).sum() >= 10 else None
    c = P.control(out, idx)
    x = r - c
    for k, lab in ((0, "excess_train"), (1, "excess_valid")):
        sel = (sp == k) & np.isfinite(x)
        res[lab] = round(float(x[sel].mean()), 4) if sel.sum() else None
    res["per_day"] = round(len(r) / max(1, P.n_days), 3)
    res["per_day_valid"] = round(int((sp == 1).sum()) / max(1, P.n_days_split[1]), 3)
    tr, va = res["train"], res["valid"]
    tier1 = bool((tr["exp_r"] or -1) > 0 and (va["exp_r"] or -1) > 0
                 and MIN_PER_DAY <= res["per_day"] <= MAX_PER_DAY_TIER1)
    if (tr["n"] < MIN_TRAIN or va["n"] < MIN_VALID or tr["t"] is None or va["t"] is None
            or res["per_day"] > MAX_PER_DAY):
        score = None
    else:
        score = (min(max(tr["t"], -5), max(va["t"], -5))
                 + 0.5 * bool((res["exp_up"] or -1) > 0 and (res["exp_down"] or -1) > 0)
                 + 0.25 * bool((res["excess_train"] or -1) > 0 and (res["excess_valid"] or -1) > 0)
                 - 1.0 * (res["per_day"] < MIN_PER_DAY))
    res["tier1"] = tier1
    res["score"] = None if score is None else round(float(score), 3)
    if keep_keys:
        res["_keys"] = np.unique(P.sd[idx])
    return res


def _worker(args):
    specs = args
    return [evaluate(_P, s) for s in specs]


def generate(qtab: dict, n: int, seed: int, seen_keys: set, avoid_fams: set, log=print) -> tuple[list[Spec], dict]:
    """n new valid specs, none with a key in seen_keys or a family in avoid_fams. Deterministic for a seed."""
    rng = np.random.default_rng(seed)
    out, keys = [], set()
    rej = {"invalid": 0, "seen": 0, "tried_family": 0, "dup": 0}
    tries = 0
    while len(out) < n and tries < n * 50:
        tries += 1
        s = random_spec(rng, qtab)
        ok, _ = valid(s)
        if not ok:
            rej["invalid"] += 1
            continue
        k = s.key()
        if k in seen_keys:
            rej["seen"] += 1
            continue
        if k in keys:
            rej["dup"] += 1
            continue
        if s.family() in avoid_fams:
            rej["tried_family"] += 1
            continue
        keys.add(k)
        out.append(s)
    return out, rej


def screen(P, specs: list[Spec], workers: int = 4, log=print) -> list[dict]:
    global _P
    _P = P
    for o in {f"{s.side}_{s.geom}" for s in specs}:      # build the random baselines once, before forking
        P.control(o, np.empty(0, np.int64))
    t0 = time.time()
    chunks = [specs[i:i + 50] for i in range(0, len(specs), 50)]
    res = []
    if workers > 1 and len(chunks) > 1:
        from multiprocessing import get_context

        with get_context("fork").Pool(workers) as pool:
            for i, r in enumerate(pool.imap(_worker, chunks)):
                res += r
                if i % 10 == 0:
                    log(f"screen: {len(res)}/{len(specs)} specs ({time.time() - t0:.0f}s)")
    else:
        for c in chunks:
            res += _worker(c)
    return res


# ------------------------------------------------------------------------------------------------ prior research
def tried_families() -> set:
    """Family signatures of arena-style modules already in research/ (SIDE, WINDOW, CONDS literals), incl. GEN."""
    fams = set()
    for p in (ROOT / "research").rglob("*.py"):
        try:
            if p.stat().st_size > 200_000:
                continue
            src = p.read_text(errors="ignore")
        except OSError:
            continue
        if "CONDS = [" not in src or "SIDE = " not in src:
            continue
        try:
            tree = ast.parse(src)
            v = {}
            for node in tree.body:
                if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                    if node.targets[0].id in ("SIDE", "WINDOW", "CONDS"):
                        v[node.targets[0].id] = ast.literal_eval(node.value)
            if {"SIDE", "WINDOW", "CONDS"} <= set(v):
                fams.add(family_sig([(c[0], c[1]) for c in v["CONDS"]], v["SIDE"], v["WINDOW"]))
        except Exception:
            continue
    return fams


# ------------------------------------------------------------------------------------------------ overlap
def existing_keys(P, months=("2025-06", "2026-03"), log=print, accounts=("primary", "testing", "testing2", "gen"),
                  exclude_prefix="GEN-") -> tuple[dict, list]:
    """Enabled lab setups of every account -> set of panel symbol-day ids where they would trade (first qualifying
    bar, its window and liquidity floor), on sample months. Non-lab setups and modules that fail are listed."""
    import yaml

    from ...strategies.setups import LabStrategy

    specs = {}
    base = yaml.safe_load((ROOT / "config/default.yaml").read_text())["strategies"]
    for acct in accounts:
        st = dict(base) if acct == "primary" else {}
        f = ROOT / "config" / f"account_{acct}.yaml"
        if acct != "primary":
            if not f.exists():
                continue
            st = (yaml.safe_load(f.read_text()) or {}).get("strategies") or {}
        for k, v in st.items():
            if isinstance(v, dict) and v.get("enabled") and not k.startswith(exclude_prefix):
                specs.setdefault(k, v)
    lab = {k: v for k, v in specs.items() if v.get("type") == "lab"}
    skipped = sorted(set(specs) - set(lab))
    key_of = {}
    lib = __import__("mcf.research.arena.data", fromlist=["_lib"])._lib()
    # map (symbol, date) -> panel sd id
    first = np.flatnonzero(np.r_[True, P.sd[1:] != P.sd[:-1]])
    sym = P.sym_names[P.sym_codes[first]]
    dates = P.days[P.day[first]]
    for s, d, k in zip(sym, dates, P.sd[first]):
        key_of[(s, d)] = int(k)
    out = {k: set() for k in lab}
    for m in months:
        f = lib.load_month(m, context=True)
        f["symbol"] = f["symbol"].astype(str)
        for name, v in lab.items():
            try:
                st = LabStrategy(name, v["module"], window=v.get("window"))
                g = f[f["adv20"].to_numpy(float) >= float(v.get("min_adv") or 0)]
                if st.symbols is not None:
                    g = g[g["symbol"].isin(st.symbols)]
                g = g.reset_index(drop=True)
                lo, hi = v.get("window") or (950, 1500)
                tod = g["tod"].to_numpy()
                msk = np.asarray(st.mod.mask(g), bool) & (tod >= max(950, lo)) & (tod <= min(1500, hi))
                hit = g.loc[msk, ["symbol", "date"]].drop_duplicates()
                for s, d in zip(hit["symbol"], hit["date"].astype(str)):
                    k = key_of.get((s, d))
                    if k is not None:
                        out[name].add(k)
            except Exception as e:      # noqa: BLE001 - a module that cannot run on the frames is reported, not fatal
                skipped.append(f"{name} ({type(e).__name__})")
        log(f"overlap: existing setups on {m} done")
    return {k: np.array(sorted(v), np.int64) for k, v in out.items()}, sorted(set(skipped))


def overlap(a: np.ndarray, b: np.ndarray) -> float:
    if not len(a) or not len(b):
        return 0.0
    return len(np.intersect1d(a, b, assume_unique=True)) / min(len(a), len(b))


def rank(results: list[dict]) -> list[dict]:
    r = [x for x in results if x.get("score") is not None]
    return sorted(r, key=lambda x: (x["tier1"], x["score"], x["all"]["n"]), reverse=True)


def pick(P, specs_by_key: dict, ranked: list[dict], n: int, existing: dict, prior_gen: dict, months_mask=None,
         log=print) -> list[dict]:
    """Greedy best-first with the overlap rule. existing keys are on sample months only: compare there."""
    picks = []
    for r in ranked:
        if len(picks) >= n:
            break
        s = specs_by_key[r["key"]]
        full = evaluate(P, s, keep_keys=True)
        keys = full.pop("_keys")
        sub = keys[months_mask[keys]] if months_mask is not None else keys
        worst, with_ = 0.0, None
        for name, k in existing.items():
            o = overlap(sub, k)
            if o > worst:
                worst, with_ = o, name
        for name, k in list(prior_gen.items()) + [(p["name_tmp"], p["_keys"]) for p in picks]:
            o = overlap(keys, k)
            if o > worst:
                worst, with_ = o, name
        if worst > OVERLAP_MAX:
            r["skipped_overlap"] = [with_, round(worst, 3)]
            continue
        full.update({"name_tmp": r["key"], "_keys": keys, "max_overlap": round(worst, 3), "overlap_with": with_})
        picks.append(full)
    return picks


def default_workers() -> int:
    return max(1, min(4, (os.cpu_count() or 2)))
