"""Pre-registration must be visibly first (inspector 1127 #16): for every study folder research/<study>/ that holds both a
PREREG.md and a REPORT.md, the commit that first added PREREG.md must be an earlier commit than the one that first added
REPORT.md (not the same commit). A lightweight check over git history (one `git log`). Educational only - not financial
advice."""
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Committed PREREG + REPORT together before this check existed (all five were FAIL / no-change studies; inspector 1127 #16).
GRANDFATHERED = {
    "research/breadth_1125": "31133ea1dd",
    "research/squeeze_1125": "6ddf89fb3e",
    "research/tape_1126": "d10c34bca1",
    "research/hedgeb_1126": "0dff8ef6c0",
    "research/ticksel_1125": "bb3f848ba2",
}


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True).stdout


def _first_adds() -> dict[str, tuple[int, str]]:
    """path -> (age rank, commit) of the oldest commit that added it; a higher rank is an older commit."""
    try:
        if _git("rev-parse", "--is-shallow-repository").strip() == "true":
            pytest.skip("shallow clone: history incomplete")
        out = _git("log", "--topo-order", "--diff-filter=A", "--name-only", "--format=@%H", "--",
                   "research/*PREREG.md", "research/*REPORT.md")
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("no git history available")
    adds, rank, cur = {}, 0, ""
    for line in out.splitlines():
        if line.startswith("@"):
            rank, cur = rank + 1, line[1:]
        elif line.strip():
            adds[line.strip()] = (rank, cur)      # log runs newest -> oldest, so the oldest add wins
    return adds


def test_prereg_committed_before_report():
    adds = _first_adds()
    bad = []
    for path, (rank, sha) in sorted(adds.items()):
        if not path.endswith("/PREREG.md"):
            continue
        study = path[: -len("/PREREG.md")]
        rep = study + "/REPORT.md"
        if rep not in adds:
            continue
        r_rank, r_sha = adds[rep]
        if rank > r_rank:                          # PREREG's commit is strictly older
            continue
        if GRANDFATHERED.get(study, "-") == sha[:10] == r_sha[:10]:
            continue
        bad.append(f"{study}: PREREG {sha[:10]} vs REPORT {r_sha[:10]}")
    assert not bad, "PREREG.md must be committed before REPORT.md (commit the PREREG before scoring): " + "; ".join(bad)


def test_grandfather_list_is_exact():
    """Each grandfathered study really did commit both files in the listed commit (keeps the list from growing silently)."""
    adds = _first_adds()
    for study, sha in GRANDFATHERED.items():
        p, r = adds.get(study + "/PREREG.md"), adds.get(study + "/REPORT.md")
        assert p and r and p[1][:10] == r[1][:10] == sha, study
