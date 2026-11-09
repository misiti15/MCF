#!/usr/bin/env bash
# Guild Builder: rebuild the 2-year research data (MCF research/bdi/1104/DATA.md). Run ONLY after 16:00 ET.
# Educational only - not financial advice.
set -euo pipefail
H=$(TZ=America/New_York date +%H%M); [ "$H" -ge 1600 ] || { echo "refusing: market hours ($H ET)"; exit 1; }
M=/home/user/MCF; G=/home/user/guild/research/data; S=${SCRATCH:-/tmp/guild_build}; mkdir -p "$S" "$G/logs"
cd "$M"
python "$G/dl.py" 2024-09-16 2026-11-10 16 research/lab_symbols.txt          # 1) 1-min SIP bars (~25 min)
python research/history2y/build_frames.py --workers 4 --context              # 2) lab frames + context + daily
python research/bdi/timeofday/build_open.py --workers 4                       # 3) opening frame 09:35-10:30
python research/bdi/eu1103/preopen/build_o5.py "$S" && cp "$S/o5_hist.parquet" "$G/"   # 4) 09:30-09:35 bar
python research/bdi/1104/headtail_wrapper.py                                  # 5) head/tail for bt_all flatten
(cd research/bdi/1104 && python bt_all.py "$S" 4) && mkdir -p research/history2y/data/bt_lab1104 \
  && cp "$S"/bt/*.parquet research/bdi/1104/setups.csv research/history2y/data/bt_lab1104/   # 6) 2y trade lists
echo "rebuild done $(TZ=America/New_York date)"
