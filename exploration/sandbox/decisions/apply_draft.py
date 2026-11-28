"""Apply one prepared decision draft (or the Monday combo) to a checkout of claude/intraday-trading-system-witis4.

DRAFT TOOL - written by the 2026-11-28 exploration session for a dry run in a throwaway worktree. It never commits,
never pushes. Every edit is an exact string replacement that must match exactly once, so a drifted config fails loudly
instead of applying half a change. Educational only - not financial advice.

Usage (from anywhere; --repo is the checkout to edit):
  python apply_draft.py --repo DIR --code LATCH-OPEN --when monday --date 2026-11-29 --where chat
  python apply_draft.py --repo DIR --code L3-OUT --when monday ...      # then: python -m mcf.report.assignments
  python apply_draft.py --repo DIR --code COMBO --when monday ...       # LATCH-OPEN + L3-OUT + B8-SHADOW
Codes: LATCH-OPEN (--variant 3R optional), L3-OUT, B8-SHADOW, ARENA-LATCH-F, HS-SCALE, COMBO.
Placeholders in the ledger drafts: <DATE> (decision date), <EFFECTIVE> (first session), <WHERE> (where approved).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EFFECTIVE = {"monday": "2026-11-30", "friday": "2026-12-07"}

# (file, old, new) - each `old` must occur exactly once in the file.
EDITS: dict[str, list[tuple[str, str, str]]] = {
    "LATCH-OPEN": [
        ("config/default.yaml",
         "  latch_counts_open: false       # LATCH-OPEN (neveragain_1125 G1-2): per-setup latch on closed + open R (no new entries)\n",
         "  latch_counts_open: true        # LATCH-OPEN (neveragain_1125 G1-2): per-setup latch on closed + open R (no new entries); owner <DATE> (<WHERE>), from session <EFFECTIVE>\n"),
    ],
    "LATCH-OPEN-3R": [
        ("config/default.yaml",
         "  latch_open_r: null             # closed + open threshold (R)",
         "  latch_open_r: 3                # closed + open threshold (R)"),
    ],
    "L3-OUT": [
        ("config/default.yaml",
         "    enabled: true    # re-promoted from Testing 1 2026-10-30 (owner); promotion = move. Demoted 10-22 after 23 Primary trades -0.308R\n",
         "    enabled: false   # L3-OUT (owner <DATE>, override of PRIME-RULES probation): moved to On Deck from session <EFFECTIVE>; Primary record 10-30..11-27 stays here\n"),
        ("config/default.yaml",
         "    - L3-gap-slope-fromopen-FD   # re-promoted 2026-10-30 (~19/day live)\n",
         ""),
        ("config/account_testing.yaml",
         "    enabled: false   # re-promoted to Primary 2026-10-30 (owner); its Testing 1 record stays here\n",
         "    enabled: true    # L3-OUT (owner <DATE>): back from Primary (move) from session <EFFECTIVE>; On Deck rules (no per-setup stop, 300R account backstop)\n"),
        ("config/account_testing.yaml",
         "    - ST7-rsi50dn-long-pm-t1s1-FD   # from Primary 2026-11-21 (ST7-MOVE); 43 Primary trades -7.08R (LR8)\n",
         "    - ST7-rsi50dn-long-pm-t1s1-FD   # from Primary 2026-11-21 (ST7-MOVE); 43 Primary trades -7.08R (LR8)\n"
         "    - L3-gap-slope-fromopen-FD   # from Primary <EFFECTIVE> (L3-OUT); Primary 10-30..11-27: 215 lots -3.1R (LR8, from 10-23 basis), w/o best day -0.209R/lot\n"),
    ],
    "B8-SHADOW": [
        ("config/default.yaml",
         "  netbeta_shadow:                # B8 shadow (squeeze_1125 R1-B8): journal tag + status only, never blocks\n    enabled: false\n",
         "  netbeta_shadow:                # B8 shadow (squeeze_1125 R1-B8): journal tag + status only, never blocks\n"
         "    enabled: true                # B8-SHADOW owner <DATE>, from session <EFFECTIVE>; review after 20 Primary sessions (size-matched random + constant-cut controls)\n"),
    ],
    "ARENA-LATCH-F": [
        ("config/account_testingf.yaml",
         "  max_setup_daily_loss_r: null\n  max_trades_per_day: 1500\n",
         "  max_setup_daily_loss_r: 2.0   # ARENA-LATCH-F (owner <DATE>): frozen forward block from session <EFFECTIVE> (10 sessions), then re-decided; raw R (not in loss_stops_cost_r_accounts)\n"
         "  max_trades_per_day: 1500\n"),
    ],
    "HS-SCALE": [
        ("config/default.yaml",
         "  shock_v:                       # SHOCK-V glitch failsafe (hsscale_1125 Layer 1): no new entries + alert, never a flatten\n    enabled: false\n",
         "  shock_v:                       # SHOCK-V glitch failsafe (hsscale_1125 Layer 1): no new entries + alert, never a flatten\n"
         "    enabled: true                # HS-SCALE shock-only, owner <DATE>, from session <EFFECTIVE>; never flattens\n"),
        ("config/default.yaml", "    v1_floor_r: 8\n", "    v1_floor_r: 16                # HS-SCALE: scored level at N = 4, X = 32R (hsscale_1125)\n"),
        ("config/default.yaml", "    v2_floor_r: 12\n", "    v2_floor_r: 24\n"),
    ],
}

LEDGER_FILE = {
    "LATCH-OPEN": {"monday": "LATCH-OPEN/ledger_monday_1130.jsonl", "friday": "LATCH-OPEN/ledger_epoch_1204.jsonl"},
    "L3-OUT": "L3-OUT/ledger_out.jsonl",
    "B8-SHADOW": "B8-SHADOW/ledger.jsonl",
    "ARENA-LATCH-F": "ARENA-LATCH-F/ledger.jsonl",
    "HS-SCALE": "HS-SCALE/ledger.jsonl",
}

# Test expectations that flip when a Friday switch is turned on. tests/test_friday_switches.py asserted every switch
# defaults OFF in every account, and its two no-op tests (runner no-op, flags-off golden) read the repo config. The
# base edit (applied once, idempotent) turns the first into "off unless approved" (APPROVED_ON) and pins the switches
# off inside the two no-op tests (they test the flags-off code path, not the repo config). Each switch draft then adds
# one APPROVED_ON line. Found by the 2026-11-28 dry run; see DRYRUN.md.
TF = "tests/test_friday_switches.py"
MARK = "# APPROVED_ON additions (one line per approved switch, with its ledger code):\n"
TESTS_BASE: list[tuple[str, str, str]] = [
    (TF,
     """# ------------------------------------------------------------------------------------------------ defaults: all OFF
@pytest.mark.parametrize("acct", ACCTS)
def test_every_switch_defaults_off_in_every_account(acct, monkeypatch):
    monkeypatch.setenv("MCF_ACCOUNT", acct)
    cfg = load_config()
    rk = cfg["risk"]
    assert rk["latch_counts_open"] is False
    for k in ("scaled_halt", "shock_v", "netbeta_shadow"):
        assert rk[k]["enabled"] is False, k
    rm = RiskManager(cfg, 100000)
    assert not rm.latch_counts_open and not rm.scaled.enabled
    assert not S.ShockV(rk["shock_v"], acct).enabled and not S.NetBetaShadow(rk["netbeta_shadow"], acct).enabled
""",
     """# ------------------------------------------------------------------------------------------------ defaults: OFF unless approved
# Switches the owner has turned on (each with its research/ledger.jsonl entry); every other switch stays OFF everywhere.
APPROVED_ON: set[str] = set()
""" + MARK + """

def _switches_off(cfg):
    \"\"\"Pin every Friday switch off: the no-op tests are about the flags-off code path, not about the repo config.\"\"\"
    rk = dict(cfg.get("risk") or {})
    rk["latch_counts_open"] = False
    for k in ("scaled_halt", "shock_v", "netbeta_shadow"):
        rk[k] = {**(rk.get(k) or {}), "enabled": False}
    cfg["risk"] = rk
    return cfg


@pytest.mark.parametrize("acct", ACCTS)
def test_every_switch_off_unless_approved(acct, monkeypatch):
    monkeypatch.setenv("MCF_ACCOUNT", acct)
    cfg = load_config()
    rk = cfg["risk"]
    assert rk["latch_counts_open"] is ("latch_counts_open" in APPROVED_ON)
    for k in ("scaled_halt", "shock_v", "netbeta_shadow"):
        assert rk[k]["enabled"] is (k in APPROVED_ON), k
    rm = RiskManager(cfg, 100000)
    assert bool(rm.latch_counts_open) == ("latch_counts_open" in APPROVED_ON and S.latch_open_on(cfg))
    assert bool(rm.scaled.enabled) == ("scaled_halt" in APPROVED_ON and acct in rk["scaled_halt"]["accounts"])
    assert S.ShockV(rk["shock_v"], acct).enabled == ("shock_v" in APPROVED_ON and acct in rk["shock_v"]["accounts"])
    assert S.NetBetaShadow(rk["netbeta_shadow"], acct).enabled == (
        "netbeta_shadow" in APPROVED_ON and acct in rk["netbeta_shadow"]["accounts"])
"""),
    (TF,
     """def test_default_off_runner_noop(tmp_path, monkeypatch):
    r, b = _runner(tmp_path, monkeypatch)
""",
     """def test_default_off_runner_noop(tmp_path, monkeypatch):
    import tests.test_live_ready_lr as LR
    monkeypatch.setattr(LR, "load_config", lambda *a, **k: _switches_off(load_config(*a, **k)))
    r, b = _runner(tmp_path, monkeypatch)
"""),
    (TF,
     """def _golden_run(tmp_path, monkeypatch, mutate=None, polls=12):
    cfg = load_config()
""",
     """def _golden_run(tmp_path, monkeypatch, mutate=None, polls=12):
    cfg = _switches_off(load_config())   # flags-off baseline; `mutate` turns a switch on
"""),
]
SWITCH_OF = {"LATCH-OPEN": "latch_counts_open", "B8-SHADOW": "netbeta_shadow", "HS-SCALE": "shock_v"}
TEST_EDITS: dict[str, list[tuple[str, str, str]]] = {
    c: [(TF, MARK, MARK + f'APPROVED_ON.add("{k}")   # {c} (owner <DATE>)\n')] for c, k in SWITCH_OF.items()}
# LATCH-OPEN variant -3R: the latch tests build RiskManager from the repo config and expect the 2R default threshold.
TEST_EDITS["LATCH-OPEN-3R"] = [(
    TF,
    '''    if risk is not None:
        cfg["risk"] = {**cfg["risk"], **risk}
''',
    '''    if risk is not None:   # latch_open_r pinned to the 2R default unless a test sets it (variant -3R sets 3 in config)
        cfg["risk"] = {**cfg["risk"], "latch_open_r": None, **risk}
''')]
# ARENA-LATCH-F: tests/test_new_accounts_1111.py asserts every Testing D-F account has no per-setup stop (None, = Testing B).
NA = "tests/test_new_accounts_1111.py"
TEST_EDITS["ARENA-LATCH-F"] = [
    (NA, "SPOTLIGHT_CAP = {}   #",
     'ARENA_LATCH = {"testingf": 2.0}   # ARENA-LATCH-F (owner <DATE>): frozen 10-session -2R per-setup stop block from <EFFECTIVE>\n'
     "SPOTLIGHT_CAP = {}   #"),
    (NA,
     '''        if k == "max_positions_per_strategy" and acct in SPOTLIGHT_CAP:
''',
     '''        if k == "max_setup_daily_loss_r" and acct in ARENA_LATCH:
            assert a[k] == ARENA_LATCH[acct], k
            continue
        if k == "max_positions_per_strategy" and acct in SPOTLIGHT_CAP:
'''),
    (NA,
     "    assert a[\"max_setup_daily_loss_r\"] is None                                    # no -2R per-setup stop (testing areas)\n",
     "    assert a[\"max_setup_daily_loss_r\"] == ARENA_LATCH.get(acct)                   # no -2R per-setup stop (testing areas) except ARENA-LATCH-F\n"),
]
# L3-OUT: tests/test_c3_epoch_rot_score.py counts the setups enabled in Primary's config (4 -> 3).
TEST_EDITS["L3-OUT"] = [(
    "tests/test_c3_epoch_rot_score.py",
    '    assert "NS5-sma50-flush-oversold-long" not in on and len(on) == 4   # ST7-MOVE 2026-11-21: ST7 left Primary too\n',
    '    assert "NS5-sma50-flush-oversold-long" not in on and len(on) == 3   # ST7-MOVE 2026-11-21: ST7 left Primary too;'
    ' L3-OUT <EFFECTIVE>: L3 too\n'
    '    assert "L3-gap-slope-fromopen-FD" not in on\n'), (
    # tests/test_remedyq_1120.py: the Remedy-Q parents must be enabled in Primary; L3 is now enabled On Deck instead.
    "tests/test_remedyq_1120.py",
    '        assert s[parent]["enabled"] is True and s[parent]["window"] == [950, 1500], parent\n',
    '        assert s[parent]["window"] == [950, 1500], parent\n'
    '        assert s[parent]["enabled"] is True or (parent == "L3-gap-slope-fromopen-FD" and parent in _on(_raw("testing"))), \\\n'
    '            parent   # L3-OUT <EFFECTIVE>: L3 moved unchanged to On Deck\n')]


def _sub(text: str, ph: dict) -> str:
    for k, v in ph.items():
        text = text.replace(k, v)
    return text


def _edit(repo: Path, path: str, old: str, new: str, ph: dict) -> None:
    f = repo / path
    s = f.read_text()
    n = s.count(old)
    if n != 1:
        raise SystemExit(f"{path}: expected exactly 1 match, found {n}:\n{old}")
    f.write_text(s.replace(old, _sub(new, ph)))


def apply(repo: Path, code: str, when: str, ph: dict, variant: str | None = None) -> list[str]:
    done = []
    keys = [code] + (["LATCH-OPEN-3R"] if code == "LATCH-OPEN" and variant == "3R" else [])
    if code in SWITCH_OF and MARK not in (repo / TF).read_text():
        for path, old, new in TESTS_BASE:
            _edit(repo, path, old, new, ph)
    for k in keys:
        for path, old, new in EDITS[k] + TEST_EDITS.get(k, []):
            _edit(repo, path, old, new, ph)
    lf = LEDGER_FILE[code]
    lf = lf[when] if isinstance(lf, dict) else lf
    lines = [l for l in (HERE / lf).read_text().splitlines() if l.strip() and not l.startswith("#")]
    led = repo / "research" / "ledger.jsonl"
    body = led.read_text()
    if not body.endswith("\n"):
        body += "\n"
    for l in lines:
        e = json.loads(_sub(l, ph))
        if variant == "3R" and code == "LATCH-OPEN":
            e["patch"]["risk.latch_open_r"] = [None, 3]
        body += json.dumps(e, ensure_ascii=False) + "\n"
    led.write_text(body)
    done.append(f"{code}: config + ledger ({lf})")
    return done


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--code", required=True, choices=[*LEDGER_FILE, "COMBO"])
    ap.add_argument("--when", default="monday", choices=list(EFFECTIVE))
    ap.add_argument("--date", required=True, help="decision date YYYY-MM-DD (the owner's reply)")
    ap.add_argument("--where", default="chat")
    ap.add_argument("--variant", default=None, choices=["3R"], help="LATCH-OPEN only: -3R threshold")
    a = ap.parse_args()
    ph = {"<DATE>": a.date, "<EFFECTIVE>": EFFECTIVE[a.when], "<WHERE>": a.where}
    codes = ["LATCH-OPEN", "L3-OUT", "B8-SHADOW"] if a.code == "COMBO" else [a.code]
    for c in codes:
        for msg in apply(Path(a.repo), c, a.when, ph, a.variant):
            print(msg)
    if "L3-OUT" in codes:
        print("next: python -m mcf.report.assignments   (same commit; tests/test_assignments.py)")


if __name__ == "__main__":
    main()
