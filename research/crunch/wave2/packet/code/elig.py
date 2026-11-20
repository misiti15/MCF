"""Per-session enabled setups from setups/<date>.json on each state branch -> work/elig.csv. Educational only."""
import subprocess, json, csv, sys
OUT = sys.argv[1]
BR = ["mcf-data", "mcf-data-testing", "mcf-data-testing2", "mcf-data-explore1", "mcf-data-livelab", "mcf-data-testingd",
      "mcf-data-testinge", "mcf-data-testingf", "mcf-data-gen", "mcf-data-graveyard"]
w = csv.writer(open(OUT, "w")); w.writerow(["branch", "date", "setup", "signals_ok"])
for b in BR:
    fs = subprocess.run(["git", "ls-tree", "--name-only", f"origin/{b}", "setups/"], capture_output=True, text=True).stdout.split()
    for f in fs:
        d = f.split("/")[-1][:10]
        if d < "2026-10-06" or d > "2026-11-19": continue
        try: j = json.loads(subprocess.run(["git", "show", f"origin/{b}:{f}"], capture_output=True, text=True).stdout)
        except Exception: continue
        for s, v in (j.get("strategies") or {}).items():
            if isinstance(v, dict) and v.get("enabled", True) and not v.get("archived"): w.writerow([b, d, s, 1])
