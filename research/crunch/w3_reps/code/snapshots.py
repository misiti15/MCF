"""Enabled setups per account per session from the frozen snapshots (state/setups/<day>.json on each mcf-data* branch).
Writes snapshots.csv: account, day, setup, enabled(1/0), benched(1/0), away(1/0). Educational only."""
import csv, json, subprocess, sys
REPO = "/home/user/MCF"
ACC = {"primary": "mcf-data", "ondeck": "mcf-data-testing", "tA": "mcf-data-testing2", "tB": "mcf-data-explore1",
       "tC": "mcf-data-livelab", "tD": "mcf-data-testingd", "tE": "mcf-data-testinge", "tF": "mcf-data-testingf",
       "gen": "mcf-data-gen", "gy": "mcf-data-graveyard"}
out = csv.writer(open(sys.argv[1], "w", newline=""))
out.writerow(["account", "day", "setup", "enabled", "benched", "away"])
for a, br in ACC.items():
    names = subprocess.run(["git", "-C", REPO, "ls-tree", "--name-only", f"origin/{br}", "setups/"],
                           capture_output=True, text=True).stdout.split()
    for p in names:
        day = p.split("/")[-1].replace(".json", "")
        d = json.loads(subprocess.run(["git", "-C", REPO, "show", f"origin/{br}:{p}"], capture_output=True, text=True).stdout)
        rot = d.get("rotation") or {}
        ben = set(rot.get("benched") or [])
        away = set((rot.get("away") or {}).keys())
        for s, v in (d.get("strategies") or {}).items():
            out.writerow([a, day, s, int(bool(v.get("enabled", True))), int(s in ben), int(s in away)])
