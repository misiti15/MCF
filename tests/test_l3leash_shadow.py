"""LEASH shadow (owner 2026-11-10): research/l3leash/shadow.py scoring (K11 half size on SPY >= +0.40%, K12 -1R latch
after UP-confirmed, -2R latch kept) and the idempotent scoreboard upsert. Educational only - not financial advice."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("l3shadow", ROOT / "research/l3leash/shadow.py")
SH = importlib.util.module_from_spec(spec); spec.loader.exec_module(SH)


def _day(r, e, x, spy, up, run=None):
    return pd.DataFrame(dict(r=r, e=e, x=x, spy_fo=spy, upso=up, run_id=run or [1] * len(r)))


def test_latch_k11_k12():
    # three losers closing before the next entry, then a winner: -2R latch blocks the 4th trade only after 2 losses
    t = _day(r=[-1.0, -1.0, -1.0, 2.0], e=[600, 610, 620, 630], x=[605, 615, 625, 700],
             spy=[0.1, 0.5, 0.5, 0.1], up=[False, True, True, True])
    s = SH.score(t)
    assert s["base_R"] == -1.0                     # actual = sum of run-1 R
    assert s["base_sim_R"] == -2.0                 # latch at -2R blocks trades 3 and 4
    assert s["K11_R"] == -1.0 - 0.5 - 0.5          # half size on the two SPY>=0.40 entries; -2R reached, 4th blocked
    assert s["K12_R"] == -1.0                      # -1R latch once UP-confirmed: blocks trade 2 onward
    assert s["dK12"] == 1.0 and s["n_cut_K12"] == 1
    assert s["n_half_K11"] == 2


def test_whatifs_only_enter_under_leash():
    # run-2 what-if (blocked live by the latch) is taken by K11 when halving kept the latch from firing
    t = _day(r=[-1.0, -1.0, 1.5], e=[600, 610, 620], x=[605, 615, 690], spy=[0.5, 0.5, 0.1], up=[False] * 3, run=[1, 1, 2])
    s = SH.score(t)
    assert s["n_trades"] == 2 and s["n_whatif"] == 1
    assert s["base_sim_R"] == -2.0 and s["K11_R"] == -1.0 + 1.5


def test_upsert_idempotent(tmp_path):
    b = tmp_path / "board.csv"
    row = lambda d, a, R: dict(date=d, account=a, kind="forward", seen_at_design=0, n_trades=1, n_whatif=0, base_R=R,
                               base_sim_R=R, K11_R=R / 2, K12_R=R, dK11=-R / 2, dK12=0.0, n_half_K11=1, n_cut_K12=0,
                               first_up_conf="", spy_fo_max_at_entry=0.5, compass_src="x", spy_src="x", updated_at="t")
    SH.upsert(b, [row("2026-11-11", "Primary", 1.0), row("2026-11-12", "Primary", 2.0)])
    df = SH.upsert(b, [row("2026-11-11", "Primary", 3.0)])          # re-run replaces, never duplicates
    assert len(df) == 2 and list(df.cum_base_R) == [3.0, 5.0] and list(df.sessions) == [1, 2]
    assert np.isclose(pd.read_csv(b).cum_dK11.iloc[-1], -2.5)
