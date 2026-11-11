#!/bin/bash
# FWDCAL evening run (after research/regsw_rebreak/run_evening.sh). Read-only market-data fetches via the fwdrep code,
# refused before 16:05 ET. Mirror-live books for 11-04..11-11, delay 1 (live-like) then delay 0 (ablation), then audits.
# Educational only - not financial advice.
set -euo pipefail
hm=$(TZ=America/New_York date +%H%M); [ "$hm" -ge 1605 ] || { echo "refusing before 16:05 ET"; exit 1; }
cd "$(dirname "$0")"
python mirror.py --dates 2026-11-04..2026-11-11 --delay 1 --fetch --jobs 3 > out/run_d1.txt 2>&1
python mirror.py --dates 2026-11-04..2026-11-11 --delay 0 --jobs 3 > out/run_d0.txt 2>&1
tail -40 out/run_d1.txt; tail -40 out/run_d0.txt
