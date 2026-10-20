"""Testing-account allocator (owner 2026-10-20, "Goals for copies"): which testing setup runs in Testing 1 (`testing`)
and which in Testing 2 (`testing2`), and which crowded-out setups get split-ticker copies in both.

    python -m mcf.research.allocate                 # dry run: research/allocation/<date>.md + .json, configs untouched
    python -m mcf.research.allocate --apply         # also edit config/account_testing*.yaml + docs/live/assignments.json

Inputs
  * current assignments: mcf.report.assignments.current() (setups enabled in testing / testing2; Primary, Graveyard and
    the Setup Generator are never touched);
  * each account's cumulative playing time: `git show origin/mcf-data-<account>:reports/scorecard.json`
    (playing_time.cumulative.setups: signals, sessions, expected_per_day, verdict, lost_to, skipped).

Per setup
  * load = signals per day: observed signals / sessions when it has >= 3 sessions, else the backtest expectation
    (expected_per_day) when there is one, else the observed rate (0 for a setup with no record yet);
  * crowding loss = signals skipped for held_by_other + setup_cap + daily_loss (slots, lot cap, per-setup loss limit),
    per session;
  * pair conflict w(a, b) = (a's signals lost to b + b's lost to a) per session, from every scorecard record.

Heuristic (deterministic). Minimise
    cost = 0.5 x |load(Testing 1) - load(Testing 2)|                    (a) balance, signals/day
         + CONFLICT_W x sum of w(a, b) over pairs sharing an account     (b) crowding pairs apart
         + FD_W x number of setup / -FD pairs sharing an account          (c) a setup and its -FD variant apart
         + MOVE_W x number of setups moved (a new split copy counts 1)    (d) few moves
  1. Split copies (e): at most N setups (default 6) whose verdict is starved / crowded-out, with crowding loss
     >= --min-lost per session and not pinned to fixed symbols, ranked by crowding loss, run in BOTH accounts with
     ticker_split part 0 (Testing 1) / part 1 (Testing 2): half the load and half their conflicts on each side. Existing
     split copies stay split. Rule (c) cannot hold for a split copy (it is in both accounts), so it is waived for it.
  2. Local search from the current assignment: repeatedly apply the single move or pairwise swap (one setup each way)
     that lowers the cost most, until nothing improves it. Ties break by setup name, so the same data gives the same
     proposal.
Moving a setup also changes its account-level rules (Testing 1: per-setup lot cap 150 and the split-tape short gate;
Testing 2: lot cap 50); the report lists the moves so the owner can judge them. A setup move is a setup change:
apply only outside market hours (RESEARCH_RULES 9) - --apply refuses 09:30-16:00 ET on weekdays.

Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "research" / "allocation"
TESTING = ("testing", "testing2")
LABEL = {"testing": "Testing 1", "testing2": "Testing 2", "both": "both (split)"}
CROWD_REASONS = ("held_by_other", "setup_cap", "daily_loss")
SPLIT_VERDICTS = ("starved", "crowded-out")
CONFLICT_W, FD_W, MOVE_W, BALANCE_W = 5.0, 1000.0, 8.0, 0.5
NY = ZoneInfo("America/New_York")


# ------------------------------------------------------------------------------------------------ inputs
def load_scorecard(account: str, fetch: bool = True) -> dict:
    """playing_time.cumulative of origin/mcf-data-<account>:reports/scorecard.json ({} when unavailable)."""
    br = f"mcf-data-{account}"
    if fetch:
        subprocess.run(["git", "fetch", "-q", "origin", br], cwd=ROOT, capture_output=True)
    r = subprocess.run(["git", "show", f"origin/{br}:reports/scorecard.json"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        print(f"allocate: no scorecard for {account} ({r.stderr.strip()[:120]})", file=sys.stderr)
        return {}
    d = json.loads(r.stdout)
    pt = d.get("playing_time") or {}
    return {"day": pt.get("day"), **(pt.get("cumulative") or {})}


def _fd_pair(name: str) -> str:
    return name[:-3] if name.endswith("-FD") else name + "-FD"


def setup_stats(names: list[str], current: dict[str, str], cards: dict[str, dict]) -> dict[str, dict]:
    """name -> load / crowding / verdict / lost_to per session, from the accounts' cumulative playing time."""
    recs: dict[str, list[tuple[str, dict]]] = {}
    for acct, c in cards.items():
        for r in c.get("setups") or []:
            recs.setdefault(r["setup"], []).append((acct, r))
    out = {}
    for n in names:
        rs = recs.get(n, [])
        here = [r for a, r in rs if a == current.get(n) or current.get(n) == "both"] or [r for _, r in rs]
        sess = sum(r.get("sessions") or 0 for _, r in rs)
        sig = sum(r.get("signals") or 0 for _, r in rs)
        exp = next((r.get("expected_per_day") for _, r in rs if r.get("expected_per_day") is not None), None)
        obs = sig / sess if sess else 0.0
        load = obs if sess >= 3 else (exp if exp is not None else obs)
        crowd = sum((r.get("skipped") or {}).get(k, 0) for _, r in rs for k in CROWD_REASONS)
        lost: dict[str, float] = {}
        for _, r in rs:
            for o, k in (r.get("lost_to") or {}).items():
                if o != n and r.get("sessions"):
                    lost[o] = lost.get(o, 0.0) + k / r["sessions"]
        verdict = (max(here, key=lambda r: r.get("sessions") or 0).get("verdict") if here else None) or "no record"
        out[n] = {"load": round(float(load), 2), "observed_per_day": round(obs, 2), "expected_per_day": exp,
                  "sessions": sess, "signals": sig, "verdict": verdict,
                  "crowd_lost_per_day": round(crowd / sess, 2) if sess else 0.0, "lost_to_per_day": lost}
    return out


# ------------------------------------------------------------------------------------------------ the search
class Problem:
    def __init__(self, stats: dict, current: dict[str, str], fixed_symbols: set[str]):
        self.names = sorted(stats)
        self.stats, self.current, self.fixed = stats, current, fixed_symbols
        self.w: dict[tuple[str, str], float] = {}
        for a in self.names:
            for b, v in stats[a]["lost_to_per_day"].items():
                if b in stats and b != a:
                    k = tuple(sorted((a, b)))
                    self.w[k] = self.w.get(k, 0.0) + v
        self.fd = sorted({tuple(sorted((n, _fd_pair(n)))) for n in self.names if _fd_pair(n) in stats})

    @staticmethod
    def share(x: str, y: str) -> float:
        """How much of two setups' tickers meet in one account (split copies: the halves are the same crc32 halves)."""
        if x == "both" and y == "both":
            return 1.0
        if x == "both" or y == "both":
            return 0.5
        return 1.0 if x == y else 0.0

    def parts(self, asg: dict[str, str]) -> dict:
        load = {"testing": 0.0, "testing2": 0.0}
        for n, a in asg.items():
            if a == "both":
                for k in load:
                    load[k] += self.stats[n]["load"] / 2
            else:
                load[a] += self.stats[n]["load"]
        conflict = sum(v * self.share(asg[a], asg[b]) for (a, b), v in self.w.items())
        fd = sum(1 for a, b in self.fd if asg[a] == asg[b] != "both")
        moves = sum(1 for n, a in asg.items() if a != self.current.get(n))
        new_split = sum(1 for n, a in asg.items() if a == "both" != self.current.get(n))
        return {"load": load, "imbalance": abs(load["testing"] - load["testing2"]), "conflict": conflict, "fd": fd,
                "moves": moves, "new_split": new_split}

    def cost(self, asg: dict[str, str]) -> float:
        p = self.parts(asg)
        return BALANCE_W * p["imbalance"] + CONFLICT_W * p["conflict"] + FD_W * p["fd"] + MOVE_W * p["moves"]

    def split_candidates(self, n: int, min_lost: float) -> list[str]:
        keep = [s for s in self.names if self.current.get(s) == "both"]
        cand = [s for s in self.names if s not in keep and s not in self.fixed
                and self.stats[s]["verdict"] in SPLIT_VERDICTS and self.stats[s]["crowd_lost_per_day"] >= min_lost]
        cand.sort(key=lambda s: (-self.stats[s]["crowd_lost_per_day"], s))
        return keep + cand[: max(0, n - len(keep))]

    def solve(self, n_split: int = 6, min_lost: float = 1.0, max_iter: int = 500) -> dict[str, str]:
        asg = {s: self.current.get(s, "testing") for s in self.names}
        for s in self.split_candidates(n_split, min_lost):
            asg[s] = "both"
        free = [s for s in self.names if asg[s] != "both"]
        best = self.cost(asg)
        flip = {"testing": "testing2", "testing2": "testing"}
        for _ in range(max_iter):
            step, bc = None, best
            for i, a in enumerate(free):
                t = dict(asg)
                t[a] = flip[asg[a]]
                c = self.cost(t)
                if c < bc - 1e-9:
                    step, bc = t, c
                for b in free[i + 1:]:
                    if asg[b] == asg[a]:
                        continue
                    t2 = dict(t)
                    t2[b] = flip[asg[b]]
                    c = self.cost(t2)
                    if c < bc - 1e-9:
                        step, bc = t2, c
            if step is None:
                break
            asg, best = step, bc
        return asg

    def reason(self, n: str, asg: dict[str, str]) -> str:
        st, cur, new = self.stats[n], self.current.get(n), asg[n]
        if new == "both":
            r = f"split copy: {st['verdict']}, {st['crowd_lost_per_day']:.1f} signals/day lost to crowding"
            return r + (" (already split)" if cur == "both" else "")
        if new == cur:
            return "stays"
        sib = _fd_pair(n)
        if sib in asg and asg[sib] == cur:
            return f"moved: keeps it apart from {sib}"
        before = dict(asg)
        before[n] = cur
        partners = sorted(((v * (self.share(cur, before[b if a == n else a]) - self.share(new, asg[b if a == n else a])),
                            b if a == n else a) for (a, b), v in self.w.items() if n in (a, b)), reverse=True)
        if partners and partners[0][0] > 0.05:
            return f"moved: apart from {partners[0][1]} ({partners[0][0]:.1f} lost signals/day between them)"
        return "moved: balances signals/day"


# ------------------------------------------------------------------------------------------------ report
def propose(n_split: int = 6, min_lost: float = 1.0, fetch: bool = True, cards: dict | None = None) -> dict:
    from ..report import assignments as A

    strat = A._strategies()
    acc = A.current(strat)
    current: dict[str, str] = {}
    for a in TESTING:
        for s in acc.get(a, []):
            current[s] = "both" if s in current else a
    cards = cards if cards is not None else {a: load_scorecard(a, fetch) for a in TESTING}
    stats = setup_stats(sorted(current), current, cards)
    fixed = {n for n in current for a in TESTING
             if (strat[a].get(n) or {}).get("enabled") and ((strat[a][n].get("symbols") or strat[a][n].get("trade_candidates")))}
    prob = Problem(stats, current, fixed)
    asg = prob.solve(n_split, min_lost)
    p0, p1 = prob.parts({s: current[s] for s in prob.names}), prob.parts(asg)
    rows = [{"setup": n, "current": current[n], "proposed": asg[n], "signals_per_day": stats[n]["load"],
             "verdict": stats[n]["verdict"], "crowd_lost_per_day": stats[n]["crowd_lost_per_day"],
             "reason": prob.reason(n, asg)} for n in prob.names]
    return {"generated": datetime.now(NY).strftime("%Y-%m-%d %H:%M ET"),
            "scorecards": {a: c.get("day") for a, c in cards.items()},
            "params": {"n_split": n_split, "min_lost": min_lost, "weights": {"balance": BALANCE_W, "conflict": CONFLICT_W,
                                                                               "fd": FD_W, "move": MOVE_W}},
            "before": _summary(p0, current), "after": _summary(p1, asg), "rows": rows,
            "moves": [r["setup"] for r in rows if r["proposed"] != r["current"] and r["proposed"] != "both"],
            "split_copies": [r["setup"] for r in rows if r["proposed"] == "both"],
            "note": "Educational only - not financial advice."}


def _summary(p: dict, asg: dict) -> dict:
    cnt = {a: sum(1 for v in asg.values() if v in (a, "both")) for a in TESTING}
    return {"setups": cnt, "signals_per_day": {k: round(v, 1) for k, v in p["load"].items()},
            "imbalance": round(p["imbalance"], 1), "same_account_conflict_per_day": round(p["conflict"], 1),
            "fd_pairs_together": p["fd"], "moves": p["moves"] - p["new_split"], "new_split_copies": p["new_split"]}


def markdown(d: dict) -> str:
    b, a = d["before"], d["after"]
    out = [f"# Testing allocation proposal ({d['generated']})", "",
           "*Educational only — not financial advice.* Proposal only until applied (`python -m mcf.research.allocate "
           "--apply`, outside market hours). Heuristic and inputs: `mcf/research/allocate.py`.", "",
           f"Scorecards: Testing 1 {d['scorecards'].get('testing')}, Testing 2 {d['scorecards'].get('testing2')} "
           "(cumulative playing time). Signals/day = observed per session (>= 3 sessions) else the backtest expectation.", "",
           "| | Testing 1 setups | Testing 2 setups | Testing 1 signals/day | Testing 2 signals/day | same-account crowding (lost/day) | setup + -FD together | moves | new split copies |",
           "|---|---|---|---|---|---|---|---|---|"]
    for k, s in (("current", b), ("proposed", a)):
        out.append(f"| {k} | {s['setups']['testing']} | {s['setups']['testing2']} | {s['signals_per_day']['testing']} | "
                   f"{s['signals_per_day']['testing2']} | {s['same_account_conflict_per_day']} | {s['fd_pairs_together']} | "
                   f"{s['moves'] if k == 'proposed' else '–'} | {s['new_split_copies'] if k == 'proposed' else '–'} |")
    out += ["", f"**Moves ({len(d['moves'])}):** " + (", ".join(d["moves"]) or "none"),
            f"**Split-ticker copies ({len(d['split_copies'])}):** " + (", ".join(d["split_copies"]) or "none")
            + " — each runs in both testing accounts, Testing 1 on ticker half 0 and Testing 2 on half 1 "
              "(crc32(symbol) % 2), so no signal is traded twice and the leaderboard shows one combined record.", "",
           "Caveat: a moved setup takes on its new account's own rules (Testing 1: per-setup lot cap 150, split-tape "
           "short gate; Testing 2: lot cap 50, live scale-outs capped at 2/day). A split copy keeps its -FD sibling in "
           "the same account on one half (rule c is waived for split copies).", "",
           "| Setup | Current | Proposed | Signals/day | Verdict | Crowding lost/day | Reason |", "|---|---|---|---|---|---|---|"]
    order = {"both": 0}
    for r in sorted(d["rows"], key=lambda r: (r["proposed"] == r["current"], order.get(r["proposed"], 1), r["setup"])):
        out.append(f"| {r['setup']} | {LABEL[r['current']]} | {LABEL[r['proposed']]} | {r['signals_per_day']:.2f} | "
                   f"{r['verdict']} | {r['crowd_lost_per_day']:.2f} | {r['reason']} |")
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------------------------------------ --apply
def _section(lines: list[str], key: str) -> tuple[int, int]:
    """[start, end) line range of a top-level `key:` section."""
    s = next(i for i, ln in enumerate(lines) if ln.rstrip() == f"{key}:")
    e = next((i for i in range(s + 1, len(lines)) if lines[i][:1] not in ("", " ", "#", "\n")), len(lines))
    return s, e


def _entry(lines: list[str], name: str) -> tuple[int, int] | None:
    """[start, end) of the `  name:` entry inside `strategies:` (inline {..} entries are one line)."""
    s, e = _section(lines, "strategies")
    pat = re.compile(rf"^  {re.escape(name)}:(\s|$)")
    for i in range(s + 1, e):
        if pat.match(lines[i]):
            j = i + 1
            while j < e and (lines[j].strip() == "" or lines[j].startswith("   ")):
                j += 1
            while j > i + 1 and lines[j - 1].strip() == "":
                j -= 1
            return i, j
    return None


def _dump_block(name: str, block: dict) -> list[str]:
    body = yaml.safe_dump({name: block}, sort_keys=False, default_flow_style=None, width=200)
    return ["  " + ln + "\n" for ln in body.splitlines()]


def _set_enabled(lines: list[str], name: str, on: bool, note: str) -> None:
    ent = _entry(lines, name)
    if ent is None:
        if on:
            raise ValueError(f"{name}: no block to enable")
        s, e = _section(lines, "strategies")
        lines.insert(e, f"  {name}: {{enabled: false}}   # {note}\n")
        return
    i, j = ent
    if "{" in lines[i]:
        lines[i] = re.sub(r"enabled:\s*\w+", f"enabled: {'true' if on else 'false'}", lines[i]).rstrip("\n")
        lines[i] = re.sub(r"\s*#.*$", "", lines[i]) + f"   # {note}\n"
        return
    for k in range(i + 1, j):
        if re.match(r"^    enabled:", lines[k]):
            lines[k] = f"    enabled: {'true' if on else 'false'}   # {note}\n"
            return
    lines.insert(i + 1, f"    enabled: {'true' if on else 'false'}   # {note}\n")


def _set_split(lines: list[str], name: str, split: dict | None) -> None:
    i, j = _entry(lines, name)
    for k in range(j - 1, i, -1):
        if re.match(r"^    ticker_split:", lines[k]):
            del lines[k]
    if split:
        lines.insert(i + 1, f"    ticker_split: {{part: {split['part']}, of: {split['of']}}}   # split copy (allocator)\n")


def _order_edit(lines: list[str], add: list[str], remove: list[str], load: dict[str, float]) -> None:
    s = next(i for i, ln in enumerate(lines) if ln.strip() == "setup_order:")
    e = s + 1
    while e < len(lines) and (lines[e].startswith("    - ") or lines[e].strip().startswith("#") or lines[e].strip() == ""):
        e += 1
    while lines[e - 1].strip() == "" or lines[e - 1].strip().startswith("#"):
        e -= 1
    item = lambda ln: ln.split("#")[0].strip()[2:].strip()   # noqa: E731
    for k in range(e - 1, s, -1):
        if lines[k].startswith("    - ") and item(lines[k]) in remove:
            del lines[k]
            e -= 1
    for n in add:
        if any(lines[k].startswith("    - ") and item(lines[k]) == n for k in range(s + 1, e)):
            continue
        pos = next((k for k in range(s + 1, e) if lines[k].startswith("    - ")
                    and load.get(item(lines[k]), 0.0) > load.get(n, 0.0)), e)
        lines.insert(pos, f"    - {n}   # {load.get(n, 0.0):.2f}/day (allocator)\n")
        e += 1


def apply(d: dict, config_dir: Path | None = None, today: str | None = None) -> list[str]:
    """Edit config/account_testing.yaml / account_testing2.yaml to the proposal; returns the changed setups."""
    from .. import config as C
    from ..report import assignments as A

    cdir = Path(config_dir or C.CONFIG_DIR)
    today = today or datetime.now(NY).strftime("%Y-%m-%d")
    strat = A._strategies()
    files = {a: cdir / f"account_{a}.yaml" for a in TESTING}
    lines = {a: files[a].read_text().splitlines(keepends=True) for a in TESTING}
    want: dict[str, dict[str, dict | None]] = {a: {} for a in TESTING}    # account -> setup -> ticker_split or None
    for r in d["rows"]:
        for i, a in enumerate(TESTING):
            if r["proposed"] in (a, "both"):
                want[a][r["setup"]] = {"part": i, "of": 2} if r["proposed"] == "both" else None
    load = {r["setup"]: r["signals_per_day"] for r in d["rows"]}
    changed = []
    for a in TESTING:
        L = lines[a]
        on_now = {k for k, v in strat[a].items() if isinstance(v, dict) and v.get("enabled")}
        add, remove = [], []
        for r in d["rows"]:
            n = r["setup"]
            if n in on_now and n not in want[a]:
                _set_enabled(L, n, False, f"allocator {today}: runs in {LABEL[r['proposed']]}")
                remove.append(n)
                changed.append(n)
            elif n in want[a]:
                split = want[a][n]
                if n in on_now and _entry(L, n) and "{" not in L[_entry(L, n)[0]]:
                    if (strat[a][n].get("ticker_split") or None) != split:
                        _set_split(L, n, split)
                        changed.append(n)
                    continue
                if n in on_now and (strat[a][n].get("ticker_split") or None) == split:
                    continue
                src = next((b for b in TESTING if (strat[b].get(n) or {}).get("enabled")), a)
                block = {k: copy.deepcopy(v) for k, v in strat[src][n].items() if k not in ("enabled", "ticker_split")}
                block = {"enabled": True, **({"ticker_split": split} if split else {}), **block}
                ent = _entry(L, n)
                new = [f"  # ---- {n}: moved here by the allocator {today} (mcf/research/allocate.py)\n"] + _dump_block(n, block)
                if ent:
                    L[ent[0]:ent[1]] = new
                else:
                    s, e = _section(L, "strategies")
                    L[e:e] = new
                add.append(n)
                changed.append(n)
        _order_edit(L, add, remove, load)
    for a in TESTING:
        files[a].write_text("".join(lines[a]))
    return sorted(set(changed))


def verify(d: dict) -> list[str]:
    """After --apply: the configs give exactly the proposed accounts and splits."""
    from ..report import assignments as A

    strat = A._strategies()
    acc, spl = A.current(strat), A.splits(strat)
    bad = []
    for r in d["rows"]:
        n, p = r["setup"], r["proposed"]
        here = [a for a in TESTING if n in acc[a]]
        exp = list(TESTING) if p == "both" else [p]
        if here != exp:
            bad.append(f"{n}: enabled in {here}, proposed {exp}")
        if p == "both" and spl.get(n) != {"testing": {"part": 0, "of": 2}, "testing2": {"part": 1, "of": 2}}:
            bad.append(f"{n}: split {spl.get(n)}")
        if p != "both" and n in spl:
            bad.append(f"{n}: still split {spl[n]}")
    return bad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--apply", action="store_true", help="edit the testing configs and regenerate assignments.json")
    ap.add_argument("--n-split", type=int, default=6, help="max setups proposed as split-ticker copies (default 6)")
    ap.add_argument("--min-lost", type=float, default=1.0, help="min crowding loss (signals/day) for a split copy")
    ap.add_argument("--no-fetch", action="store_true", help="use the local origin/mcf-data-* refs as they are")
    ap.add_argument("--force", action="store_true", help="allow --apply during market hours (do not)")
    a = ap.parse_args(argv)
    now = datetime.now(NY)
    if a.apply and not a.force and now.weekday() < 5 and (9, 30) <= (now.hour, now.minute) < (16, 0):
        print("refusing --apply during market hours (RESEARCH_RULES 9); run after the close")
        return 2
    d = propose(a.n_split, a.min_lost, fetch=not a.no_fetch)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    day = now.strftime("%Y-%m-%d")
    (OUT_DIR / f"{day}.md").write_text(markdown(d))
    (OUT_DIR / f"{day}.json").write_text(json.dumps(d, indent=1) + "\n")
    b, f = d["before"], d["after"]
    print(f"allocation: Testing 1 {f['setups']['testing']} setups / {f['signals_per_day']['testing']} signals/day, "
          f"Testing 2 {f['setups']['testing2']} / {f['signals_per_day']['testing2']} (was {b['signals_per_day']['testing']} / "
          f"{b['signals_per_day']['testing2']}); {len(d['moves'])} moves; split copies: {', '.join(d['split_copies']) or 'none'}")
    print(f"wrote {OUT_DIR / (day + '.md')}")
    if not a.apply:
        print("dry run: configs unchanged (--apply to edit them)")
        return 0
    from ..report import assignments as A

    backup = {p: p.read_text() for p in (ROOT / "config").glob("account_testing*.yaml")}
    changed = apply(d)
    bad = verify(d)
    if bad:
        for p, t in backup.items():
            p.write_text(t)
        print("apply failed, configs restored:\n  " + "\n  ".join(bad))
        return 1
    A.write()
    print(f"applied: {len(changed)} setups changed; docs/live/assignments.json regenerated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
