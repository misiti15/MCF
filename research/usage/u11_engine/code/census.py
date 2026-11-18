"""U11 engine census: classify every .py under research/ and mcf/ by the simulation engine(s) it uses.
Read-only; reads the git tree at HEAD of the given repo; no bars, no journals."""
import re, subprocess, sys, csv, collections
repo, out = sys.argv[1], sys.argv[2]
def git(*a): return subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True).stdout
files = [f for f in git("ls-files").split("\n") if f.endswith(".py") and (f.startswith("research/") or f.startswith("mcf/") or f.startswith("scripts/"))]
# first-add date per file (one pass)
added = {}
cur = None
for line in git("log", "--diff-filter=A", "--name-only", "--format=@%cs").split("\n"):
    if line.startswith("@"): cur = line[1:]
    elif line.strip(): added[line.strip()] = cur   # log is newest first -> keep overwriting -> oldest add wins
PAT = {
 "BT_class": re.compile(r"\bBacktester\b"),
 "BT_simulate": re.compile(r"backtest(\.engine)?\s+import[^\n]*\b(simulate|Costs)\b|engine\.simulate\(|from mcf\.backtest\.engine import[^\n]*simulate"),
 "LAB_frames": re.compile(r"setup_lab|history2y|build_frames|arena\.data|arena import|load_month|backlog_lab|generator\.(data|screen)"),
 "REPLAY_live": re.compile(r"mcf\.replay\.(harness|livecal|fast|broker)|from \.\.?replay|run_session|from mcf\.replay import harness|mcf\.report\.team|python -m mcf\.replay run"),
 "PACKS_only": re.compile(r"mcf\.replay\.store|mcf\.replay\.packs|from mcf\.replay import (store|packs)"),
}
rows = []
for f in files:
    try: s = open(f"{repo}/{f}", encoding="utf-8", errors="ignore").read()
    except Exception: continue
    hits = [k for k, p in PAT.items() if p.search(s)]
    name = f.rsplit("/", 1)[-1]
    own = bool(re.search(r"(^|_)(sim|engine|replay|backtest)\d*\.py$|^sim\w*\.py$", name)) or bool(re.search(r"def simulate|def sim_trade|def run_trade|first_touch|def walk\(", s))
    eng = [h for h in hits if h != "PACKS_only"]
    if not eng and own: eng = ["BESPOKE"]
    if not eng and not hits: continue
    rows.append({"file": f, "added": added.get(f, ""), "area": "/".join(f.split("/")[:2]), "engines": "+".join(eng) or "PACKS_only",
                 "data_packs": int("PACKS_only" in hits)})
with open(out, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
c = collections.Counter(); c2 = collections.Counter()
for r in rows:
    period = "<=10-31" if r["added"] <= "2026-10-31" else ("11-01..11-10" if r["added"] <= "2026-11-10" else "11-11..11-18")
    for e in r["engines"].split("+"):
        c[(e, r["file"].split("/")[0])] += 1; c2[(e, period)] += 1
print("files classified:", len(rows))
for k, v in sorted(c.items()): print(k, v)
print()
for k, v in sorted(c2.items()): print(k, v)
