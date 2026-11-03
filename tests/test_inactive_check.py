"""INACT1 / INACT2 (owner 2026-11-03): nightly inactive-setups check -> one FYI line, a DECISION only when a fix
needs the owner; P-rule watch < 5%, alarm < 1%, index-gated setups exempt; weekly sessions-to-verdict on 60 trades.
Educational only - not financial advice."""
import pandas as pd

from mcf.report import inactive as I


def _df():
    return pd.DataFrame([
        dict(account="Testing 2", setup="A-short", gate="", p_quiet_exp=0.004, quiet_sessions_signal=8,
             cause="blocked: place in line", trades=3, trades_per_session=0.2, exp_per_session=0.5, sessions_enabled=15),
        dict(account="Testing 1", setup="B-long", gate="", p_quiet_exp=0.03, quiet_sessions_signal=4, cause="",
             trades=10, trades_per_session=1.0, exp_per_session=1.2, sessions_enabled=10),
        dict(account="Testing 2", setup="NM-RWN3-ns3-spyup-early-short", gate="SPY 1 0.0", p_quiet_exp=0.001,
             quiet_sessions_signal=12, cause="rare by design: index gate", trades=0, trades_per_session=0.0,
             exp_per_session=0.9, sessions_enabled=12),
        dict(account="Primary", setup="C-busy", gate="", p_quiet_exp=0.5, quiet_sessions_signal=0, cause="",
             trades=200, trades_per_session=10.0, exp_per_session=9.0, sessions_enabled=20),
        dict(account="Graveyard", setup="D-unexplained", gate="", p_quiet_exp=0.002, quiet_sessions_signal=6,
             cause="unexplained: P < 5% (replay check)", trades=5, trades_per_session=0.5, exp_per_session=1.0,
             sessions_enabled=10),
    ])


def test_p_rule_levels_and_index_exemption():
    f = I.flags(_df()).set_index("setup").level
    assert f["A-short"] == "alarm" and f["B-long"] == "watch" and f["C-busy"] == ""
    assert f["NM-RWN3-ns3-spyup-early-short"] == ""          # index-gated: exempt even at P 0.1%
    assert I.index_gated("LD2-qqq-dip015-breadthturn-tqqq-t05s1-long") is False
    assert I.index_gated("GEN-x-SPYgt0p5-long")


def test_one_fyi_and_decision_only_when_owner_needed(tmp_path):
    s = I.summarize(_df(), "2026-11-03")
    assert s["fyi"].startswith("inactive-check | 5 enabled setups") and "alarm (P<1%): 2" in s["fyi"]
    assert s["decision"] and "A-short" in s["decision"]          # a place-in-line block needs the owner
    assert "D-unexplained" not in s["decision"]                   # housekeeping: Claude checks it, no decision
    quiet = _df().drop(index=[0])
    assert I.summarize(quiet, "2026-11-03")["decision"] is None
    p = I.append_inbox("2026-11-03", [("FYI", s["fyi"])], inbox=tmp_path)
    I.append_inbox("2026-11-03", [("FYI", s["fyi"])], inbox=tmp_path)   # idempotent: one line a night
    assert p.read_text().count("## FYI | inactive-check") == 1


def test_inact2_sessions_to_verdict():
    v = I.verdicts(_df()).set_index("setup")
    assert "C-busy" not in v.index                                # >= 3 trades a session: judged normally
    assert v.loc["A-short", "sessions_to_verdict"] == 285         # (60 - 3) / 0.2
    assert v.loc["NM-RWN3-ns3-spyup-early-short", "rate_from"] == "expected"
    assert v.loc["NM-RWN3-ns3-spyup-early-short", "sessions_to_verdict"] == 67   # 60 / 0.9
    md = I.verdict_md(I.verdicts(_df()), "2026-11-03")
    assert md.startswith("Educational only") and "Explore 1" in md
