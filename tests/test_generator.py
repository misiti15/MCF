"""Setup Generator (owner 2026-10-19): specs have >= 3 conditions (window + context + trigger), no duplicates,
deterministic names and seeds, point-in-time masks, honest screen stats. Educational only."""
from pathlib import Path

import numpy as np
import pandas as pd

from mcf.research.generator import screen as S
from mcf.research.generator.spec import (CONTEXT, IND, WINDOWS, Spec, display_name, module_slug, random_spec,
                                         setup_name, valid)

ROOT = Path(__file__).resolve().parents[1]


def _qtab():
    return {k: {q: (q - 0.5) * 10 for q in (0.05, 0.1, 0.2, 0.3, 0.7, 0.8, 0.9, 0.95)} for k in IND}


def test_generated_specs_are_layered_setups():
    specs, rej = S.generate(_qtab(), 300, seed=7, seen_keys=set(), avoid_fams=set())
    assert len(specs) == 300
    for s in specs:
        ok, why = valid(s)
        assert ok, why
        r = s.roles()
        assert s.n_conditions() >= 3 and s.n_conditions() <= 5
        assert r["trigger"] >= 1 and r["context"] == 1 and s.window in WINDOWS


def test_single_indicator_rules_are_rejected():
    assert not valid(Spec("long", "AM", "t1s1", 95e6, [("rsi", "<=", 25.0)]))[0]
    assert not valid(Spec("long", "AM", "t1s1", 95e6, [("rsi2", "<=", 5.0)]))[0]            # no context filter
    assert not valid(Spec("long", "AM", "t1s1", 95e6, [("spy_fo", ">", 0.0), ("rsi", "<=", 25.0)]))[0]   # no trigger
    assert valid(Spec("long", "AM", "t1s1", 95e6, [("spy_fo", ">", 0.0), ("rsi2", "<=", 5.0)]))[0]
    # two from one indicator group (near-duplicates) are not allowed
    assert not valid(Spec("long", "AM", "t1s1", 95e6, [("spy_fo", ">", 0.0), ("rsi2", "<=", 5.0), ("rsi5", "<=", 20.0)]))[0]


def test_no_duplicates_and_registry_respected():
    a, _ = S.generate(_qtab(), 200, seed=1, seen_keys=set(), avoid_fams=set())
    keys = [s.key() for s in a]
    assert len(keys) == len(set(keys))
    b, rej = S.generate(_qtab(), 200, seed=1, seen_keys=set(keys), avoid_fams=set())
    assert not ({s.key() for s in b} & set(keys)) and rej["seen"] > 0
    fams = {s.family() for s in a[:50]}
    c, rej = S.generate(_qtab(), 100, seed=2, seen_keys=set(), avoid_fams=fams)
    assert not ({s.family() for s in c} & fams)


def test_deterministic_with_a_seed():
    a, _ = S.generate(_qtab(), 50, seed=20261019, seen_keys=set(), avoid_fams=set())
    b, _ = S.generate(_qtab(), 50, seed=20261019, seen_keys=set(), avoid_fams=set())
    c, _ = S.generate(_qtab(), 50, seed=20261020, seen_keys=set(), avoid_fams=set())
    assert [s.key() for s in a] == [s.key() for s in b] != [s.key() for s in c]


def test_canonical_key_ignores_condition_order():
    s1 = Spec("short", "PM", "hold", 50e6, [("qqq_fo", "<", 0.0), ("rsi5", ">=", 80.0), ("gap", "<=", -2.0)])
    s2 = Spec("short", "PM", "hold", 50e6, [("gap", "<=", -2.0), ("qqq_fo", "<", 0.0), ("rsi5", ">=", 80.0)])
    assert s1.key() == s2.key()
    assert s1.key() != Spec("long", "PM", "hold", 50e6, s1.conds).key()


def test_names_are_specific():
    s = Spec("long", "AM", "t05s1", 95e6, [("spy_fo", ">", 0.0), ("rsi", "<=", 25.0), ("vwap_atr", "<=", -0.5)])
    s.conds.append(("rsi2", "<=", 5.0))
    n = setup_name(s, "2026-10-19", 1)
    assert n.startswith("GEN-261019-01-") and n.endswith("-t05s1-long")
    assert "RSI2le5" in n and "RSI14le25" in n and "VWAPatrlem0p5" in n
    assert "-AM-" in n and "SPYup" in n
    assert module_slug(s, "2026-10-19", 1) == "GEN-261019-01-rsi2-lo-am-long"
    assert display_name(s).startswith("Generated: ")


def _history_like(n_days=3, seed=0):
    """Synthetic frame rows (symbol, date, tod 950..1500) with the columns the module masks read."""
    from mcf.research.arena.indicators import FRAME_COLS

    rng = np.random.default_rng(seed)
    rows = []
    for d in pd.bdate_range("2026-03-02", periods=n_days):
        tods = [int(f"{h:02d}{m:02d}") for h in range(9, 16) for m in range(0, 60, 5)]
        tods = [t for t in tods if 950 <= t <= 1500]
        px = 50 + np.cumsum(rng.normal(0, 0.2, len(tods)))
        f = pd.DataFrame({c: rng.normal(0, 1, len(tods)) for c in FRAME_COLS})
        f["close"], f["high"], f["low"] = px, px + 0.1, px - 0.1
        f["tod"], f["atr_d"] = tods, 1.2
        f["rsi"], f["rsi5"] = rng.uniform(5, 95, len(tods)), rng.uniform(5, 95, len(tods))
        f["symbol"], f["date"] = "AAA", d.date()
        f["spy_fo"] = rng.normal(0, 0.4, len(tods))
        f["breadth"] = rng.uniform(0.2, 0.8, len(tods))
        rows.append(f)
    return pd.concat(rows, ignore_index=True)


def test_module_mask_is_point_in_time(tmp_path):
    """Truncating the day after bar i never changes the mask on bars <= i (no lookahead)."""
    import importlib.util

    from mcf.research.generator.apply import module_source

    s = Spec("long", "MID", "t1s1", 20e6, [("spy_fo", ">", 0.0), ("rsi2", "<=", 30.0), ("vwap_atr", "<=", 0.5),
                                          ("adx7", ">=", 10.0)])
    stats = {"date": "2026-10-19", "train": {"n": 1, "exp_r": 0, "t": 0}, "valid": {"n": 1, "exp_r": 0, "t": 0},
             "per_day": 1, "exp_up": 0, "exp_down": 0}
    p = tmp_path / "m.py"
    p.write_text(module_source(s, "GEN-T", stats, 10))
    spec = importlib.util.spec_from_file_location("genm", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.SIDE == "long" and mod.GEOM == "t1s1" and len(mod.CONDS) == 4
    df = _history_like(1, seed=3)
    full = mod.mask(df)
    for i in range(5, len(df), 7):
        part = mod.mask(df.iloc[: i + 1].copy())
        assert (part == full[: i + 1]).all()
    lo, hi = WINDOWS["MID"]
    assert not full[(df["tod"] < lo) | (df["tod"] > hi)].any()
    # missing context column -> fails safe (never fires)
    assert not mod.mask(df.drop(columns=["spy_fo"])).any()


def test_screen_stats_on_a_tiny_panel():
    """evaluate(): first qualifying bar per symbol-day, honest negative stats, day-clustered t."""
    class P:
        pass

    p = P()
    n = 12
    p.a = {"tod": np.array([950, 1000, 1010] * 4, np.int16), "adv20": np.full(n, 1e8, np.float32),
           "spy_fo": np.full(n, 0.5, np.float32), "rsi2": np.array([50, 5, 5] * 4, np.float16),
           "r_long_t1s1": np.array([0, -1, 1, 0, -1, 1, 0, 1, -1, 0, 1, 1], np.float32)}
    p.sd = np.repeat(np.arange(4), 3).astype(np.int32)
    p.day = np.repeat(np.arange(4), 3).astype(np.int32)
    p.split = np.array([0] * 6 + [1] * 6, np.int8)
    p.day_regime = np.array([2, 0, 2, 0], np.int8)
    p.n_days, p.n_days_split = 4, [2, 2]
    p.control = lambda out, idx: np.zeros(len(idx))
    s = Spec("long", "OPEN", "t1s1", 20e6, [("spy_fo", ">", 0.0), ("rsi2", "<=", 10.0)])
    r = S.evaluate(p, s)
    assert r["all"]["n"] == 4 and r["train"]["exp_r"] == -1.0 and r["valid"]["exp_r"] == 1.0
    assert r["per_day"] == 1.0 and r["tier1"] is False


def test_seeded_gen_setups_are_complete():
    import yaml

    st = yaml.safe_load((ROOT / "config/account_gen.yaml").read_text())["strategies"]
    keys = set()
    for k, v in st.items():
        g = v["gen"]
        if "observation" in (v.get("tags") or []):
            continue        # hand-added observation setups (pod1022, owner 2026-10-23): not generator specs
        s = Spec(g["spec"]["side"], g["spec"]["window"], g["spec"]["geom"], g["spec"]["min_adv"],
                 [tuple(c) for c in g["spec"]["conds"]])
        assert valid(s)[0] and s.key() == g["key"] and s.key() not in keys
        keys.add(s.key())
        assert (ROOT / v["module"]).exists() and list(WINDOWS[s.window]) == v["window"]
        assert v["context"] and set(v["context"]) <= set(CONTEXT)
