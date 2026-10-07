"""Configuration loading: config/default.yaml merged with config/local.yaml and env vars."""

from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"


def _merge(base: dict, override: dict) -> dict:
    out = deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    with open(CONFIG_DIR / "default.yaml") as f:
        cfg = yaml.safe_load(f)
    acct = os.environ.get("MCF_ACCOUNT", "primary")
    acct_file = CONFIG_DIR / f"account_{acct}.yaml" if acct != "primary" else None
    for extra in (acct_file, CONFIG_DIR / "local.yaml", Path(path) if path else None):
        if extra and extra.exists():
            with open(extra) as f:
                cfg = _merge(cfg, yaml.safe_load(f) or {})
    cfg["account_name"] = acct
    feed = os.environ.get("ALPACA_DATA_FEED")
    if feed:
        cfg["data"]["feed"] = feed
    return cfg


def load_dotenv(path: Path = ROOT / ".env") -> None:
    """Minimal .env loader so we don't need python-dotenv."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())
