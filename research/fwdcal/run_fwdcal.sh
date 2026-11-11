#!/bin/bash
# FWDCAL evening run (after research/regsw_rebreak/run_evening.sh). Protocol (Skeptic/Lead 11-11, fixed before any run):
#  SELECT D in {0,1} on 11-04..11-06 only: higher ALL match rate; if within 0.02, smaller |ALL avg-R gap|; tie -> D=1.
#  HOLDOUT: rule 21 scored ONCE on 11-10..11-11 with the chosen D. 11-09 is in neither window (left out, stated).
# Read-only market-data fetches via the fwdrep code, refused before 16:05 ET. Educational only - not financial advice.
set -euo pipefail
hm=$(TZ=America/New_York date +%H%M); [ "$hm" -ge 1605 ] || { echo "refusing before 16:05 ET"; exit 1; }
cd "$(dirname "$0")"; mkdir -p out
# run_evening.sh fetches data branches with --depth=1, which cuts history; status.json per day needs it back (objects are local)
git -C /home/user/MCF fetch -q --shallow-since=2026-11-02 origin mcf-data mcf-data-testing mcf-data-testing2 mcf-data-gen mcf-data-graveyard mcf-data-explore1 mcf-data-livelab
git -C /home/user/MCF fetch -q --shallow-since=2026-10-28 origin claude/intraday-trading-system-witis4
for b in mcf-data mcf-data-testing mcf-data-gen; do git -C /home/user/MCF rev-list -1 --before=2026-11-04T09:30-05:00 origin/$b -- status.json | grep -q . || { echo "no status.json history on $b"; exit 1; }; done
python mirror.py --dates 2026-11-04..2026-11-06 --delay 1 --fetch --jobs 3 --tag _sel > out/sel_d1.txt 2>&1
python mirror.py --dates 2026-11-04..2026-11-06 --delay 0 --jobs 3 --tag _sel > out/sel_d0.txt 2>&1
D=$(python - <<'PY'
import pandas as pd
a = {d: pd.read_csv(f"out/audit_d{d}_sel.csv").set_index("acct").loc["ALL"] for d in (0, 1)}
m0, m1 = a[0].match_rate, a[1].match_rate
print(0 if m0 > m1 + 0.02 else 1 if m1 > m0 + 0.02 else (0 if abs(a[0].gap_avgR) < abs(a[1].gap_avgR) else 1))
PY
)
echo "chosen delay D=$D (selection window 11-04..11-06)" | tee out/chosen_delay.txt
python mirror.py --dates 2026-11-10..2026-11-11 --delay $D --fetch --jobs 3 --tag _hold > out/hold.txt 2>&1
tail -45 out/sel_d1.txt; tail -45 out/sel_d0.txt; cat out/chosen_delay.txt; tail -50 out/hold.txt
