"""Display names: every enabled setup has one, and the dashboard copy matches config. Educational only."""
import json
from pathlib import Path

import yaml

from mcf.setup_names import label, name

ROOT = Path(__file__).resolve().parents[1]


def _enabled(cfg: str) -> set[str]:
    st = (yaml.safe_load((ROOT / cfg).read_text()) or {}).get("strategies") or {}
    return {k for k, v in st.items() if isinstance(v, dict) and v.get("enabled")}


def test_primary_setups_have_names():
    names = yaml.safe_load((ROOT / "config/setup_names.yaml").read_text())
    missing = _enabled("config/default.yaml") - set(names)
    assert not missing, f"add display names for {sorted(missing)} in config/setup_names.yaml"


def test_dashboard_copy_in_sync():
    names = yaml.safe_load((ROOT / "config/setup_names.yaml").read_text())
    page = json.loads((ROOT / "docs/live/setup_names.json").read_text())
    assert {k: v["name"] for k, v in names.items()} == {k: v["name"] for k, v in page.items()}


def test_label_falls_back_to_code():
    assert label("no-such-setup") == "no-such-setup"
    assert name("heat_fade_short") != "heat_fade_short"
    assert label("heat_fade_short").endswith("(heat_fade_short)")


def test_longs1020_setups_starred_with_legend():
    """Owner 2026-10-20: the 8 longs1020 setups (LD1-LD8, not M1) carry a "* " name prefix, explained on the dashboard."""
    names = yaml.safe_load((ROOT / "config/setup_names.yaml").read_text())
    ld = {k: v for k, v in names.items() if k.startswith("LD")}
    assert len(ld) == 8 and all(v["name"].startswith("* ") for v in ld.values())
    assert not names["NM-MF3-qqqdn-gapdn-FD"]["name"].startswith("*")
    assert "* = long setup from the 2026-10-20 longs research, near-miss, observation only" in \
        (ROOT / "docs/live/index.html").read_text()
