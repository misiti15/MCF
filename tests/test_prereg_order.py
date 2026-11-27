"""Pre-registration must be visibly first (inspector 1127 #16): the commit that first added a study's pre-registration
must be an earlier commit than the one that first added its report (not the same commit). Layouts covered:
  research/<study>/PREREG.md or PLAN.md          -> research/<study>/REPORT.md
  research/<study>/<X>/PREREG.md or <X>/PLAN.md  -> research/<study>/<X>_REPORT.md   (sub-studies, e.g. pyramid_1124)
Other names (FB1_PLAN.md, TESTPLAN.md, NOTES.md ...) are not checked. A lightweight check over git history (one
`git log`). No CI workflow runs pytest, so this guards local runs only. Educational only - not financial advice."""
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PRE_NAMES = ("/PREREG.md", "/PLAN.md")

# pre-registration path -> (commit that added it, commit that added its report), for the pairs that broke the order
# before this check existed (inspector 1127 #16 and its review). Exact: test_grandfather_list_is_exact keeps it from
# growing silently. Never add a new study here; commit its PREREG / PLAN first.
GRANDFATHERED = {
    # PREREG/PLAN + REPORT committed together
    "research/bdi/mh4_1122/PLAN.md": ("7efa4af749", "7efa4af749"),
    "research/breadth_1125/PREREG.md": ("31133ea1dd", "31133ea1dd"),
    "research/capfit_1125/PLAN.md": ("9241deec81", "9241deec81"),
    "research/etfstop_1123/PLAN.md": ("bebfdafaa8", "bebfdafaa8"),
    "research/hardstop_1123/PLAN.md": ("f4668f57eb", "f4668f57eb"),
    "research/hedgeb_1126/PREREG.md": ("0dff8ef6c0", "0dff8ef6c0"),
    "research/hsscale_1125/PLAN.md": ("2250ec92ff", "2250ec92ff"),
    "research/neveragain_1125/PLAN.md": ("b0a213a8a2", "b0a213a8a2"),
    "research/s8cap_1125/PLAN.md": ("c1c64a81df", "c1c64a81df"),
    "research/squeeze_1125/PREREG.md": ("6ddf89fb3e", "6ddf89fb3e"),
    "research/tape_1126/PREREG.md": ("d10c34bca1", "d10c34bca1"),
    "research/ticksel_1125/PREREG.md": ("bb3f848ba2", "bb3f848ba2"),
    # pyramid_1124 sub-study pre-registrations committed from the scratchpad (b53782c717) after their reports
    "research/pyramid_1124/E/PLAN.md": ("b53782c717", "3b96bbe761"),
    "research/pyramid_1124/G/PREREG.md": ("b53782c717", "3b96bbe761"),
    "research/pyramid_1124/L1/PLAN.md": ("b53782c717", "3b96bbe761"),
    "research/pyramid_1124/L2/PREREG.md": ("b53782c717", "3b96bbe761"),
    "research/pyramid_1124/L3/PREREG.md": ("b53782c717", "3b96bbe761"),
    "research/pyramid_1124/R3B/PREREG.md": ("b53782c717", "dc9e549510"),
    "research/pyramid_1124/R3C/PREREG.md": ("b53782c717", "dc9e549510"),
    "research/pyramid_1124/R3N/PREREG.md": ("b53782c717", "dc9e549510"),
}


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True).stdout


def _first_adds() -> dict[str, tuple[int, str]]:
    """path -> (age rank, commit) of the oldest commit that added it; a higher rank is an older commit."""
    try:
        if _git("rev-parse", "--is-shallow-repository").strip() == "true":
            pytest.skip("shallow clone: history incomplete")
        out = _git("log", "--topo-order", "--diff-filter=A", "--name-only", "--format=@%H", "--",
                   "research/*PREREG.md", "research/*PLAN.md", "research/*REPORT.md")
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("no git history available")
    adds, rank, cur = {}, 0, ""
    for line in out.splitlines():
        if line.startswith("@"):
            rank, cur = rank + 1, line[1:]
        elif line.strip():
            adds[line.strip()] = (rank, cur)      # log runs newest -> oldest, so the oldest add wins
    return adds


def _pairs(adds: dict) -> list[tuple[str, str]]:
    """(pre-registration path, report path) for every pair present in history."""
    out = []
    for path in sorted(adds):
        for pre in PRE_NAMES:
            if path.endswith(pre):
                d = path[: -len(pre)]
                out += [(path, rep) for rep in (d + "/REPORT.md", d + "_REPORT.md") if rep in adds]
    return out


def test_prereg_committed_before_report():
    adds = _first_adds()
    bad = []
    for pre, rep in _pairs(adds):
        (rank, sha), (r_rank, r_sha) = adds[pre], adds[rep]
        if rank > r_rank:                          # the pre-registration's commit is strictly older
            continue
        if GRANDFATHERED.get(pre) == (sha[:10], r_sha[:10]):
            continue
        bad.append(f"{pre} {sha[:10]} vs {rep} {r_sha[:10]}")
    assert not bad, "PREREG/PLAN must be committed before its REPORT (commit it before scoring): " + "; ".join(bad)


def test_grandfather_list_is_exact():
    """Each grandfathered pair really was added in the listed commits, out of order (keeps the list from growing)."""
    adds = _first_adds()
    pairs = dict(_pairs(adds))
    for pre, (p_sha, r_sha) in GRANDFATHERED.items():
        assert pre in pairs, pre
        p, r = adds[pre], adds[pairs[pre]]
        assert (p[1][:10], r[1][:10]) == (p_sha, r_sha) and p[0] <= r[0], pre
