"""FASTDEC engine smoke test on synthetic trades (research module; no journals needed)."""
import numpy as np
import pandas as pd

from research.fastdec import engine as E


def _trades():
    rng = np.random.default_rng(1)
    days = [f"2026-10-{d:02d}" for d in range(1, 21)]
    rows = []
    for s, mu, side in (("RW1-good-short-FD", 0.6, -1), ("CWT14-bad-long", -0.4, 1), ("MF2-noise-short", 0.0, -1),
                        ("GEN-261019-01-x-long", -0.1, 1), ("NS1-x-long", -0.1, 1), ("L3-x-short", -0.1, -1)):
        for d in days:
            for _ in range(6):
                rows.append(dict(date=d, strategy=s, side=side, R=rng.normal(mu, 0.8), acct="t1"))
    return pd.DataFrame(rows)


def test_family():
    assert E.family("L3-gap-slope-fromopen-FD") == "L3"
    assert E.family("GEN-261019-01-x") == "GEN"
    assert E.family("CWT14-failbrk-pdl-p10-long") == "CWT"
    assert E.family("exhaustion_short") == "CLS"


def test_evaluate_statuses():
    for m in ("flat", "eb", "ebx", "sprt"):
        S = E.evaluate(_trades(), m, E.load_priors())
        assert set(S.status) <= {"promote-ready", "on-track", "undecided", "demote-ready"}
        assert S.p_pos.between(0, 1).all()
    S = E.evaluate(_trades(), "flat")
    assert S.loc["RW1-good-short-FD", "status"] == "promote-ready"
    assert S.loc["CWT14-bad-long", "status"] == "demote-ready"
