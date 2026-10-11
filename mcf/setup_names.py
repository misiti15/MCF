"""Plain-English setup names for reports (config/setup_names.yaml). Display only. Educational only - not financial advice."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

NAMES = Path(__file__).resolve().parents[1] / "config" / "setup_names.yaml"


@lru_cache(maxsize=1)
def _names() -> dict:
    try:
        return yaml.safe_load(NAMES.read_text()) or {}
    except (OSError, yaml.YAMLError):
        return {}


def name(code: str) -> str:
    """Display name, or the code itself when the setup has no display name yet."""
    return (_names().get(code) or {}).get("name") or code


def label(code: str) -> str:
    """'Display name (code)' for tables; just the code when there is no display name."""
    n = name(code)
    return code if n == code else f"{n} ({code})"


def describe(code: str) -> str:
    return (_names().get(code) or {}).get("what", "")
