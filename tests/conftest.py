"""Test-wide settings: no test downloads live-session bar packs from GitHub Releases (mcf/replay/store.py)."""
import os

os.environ.setdefault("MCF_REPLAY_PACKS", "0")
