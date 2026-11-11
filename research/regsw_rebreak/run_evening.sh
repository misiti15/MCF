#!/usr/bin/env bash
# Builder evening run 2026-11-11 (after 16:05 ET): FAMC session 1, then the GAP-U re-break (ETB on / off). Educational only.
set -uo pipefail
H=$(TZ=America/New_York date +%H%M); [ "$H" -ge 1605 ] || { echo "refusing: before 16:05 ET ($H)"; exit 1; }
M=/home/user/MCF; G=/home/user/guild; SC=/tmp/claude-0/-home-user-MCF/14615c23-3a58-5ec1-a24c-76299e68a66c/scratchpad
cd $M
echo "== FAMC"; python $G/research/data/append_day.py 2026-11-11
git fetch -q --depth=1 origin mcf-data && git show FETCH_HEAD:earnings/2026-11-11.json > $SC/earn_20261111.json
(cd $G && python research/evd1/famc_shadow.py --date 2026-11-11 --calendar research/evd1/famc_calendar.csv --live-earnings $SC/earn_20261111.json)
echo "== RE-BREAK data"; R=$SC/rebreak; mkdir -p $R/j
for b in mcf-data mcf-data-testing mcf-data-testing2 mcf-data-graveyard mcf-data-livelab mcf-data-explore1 mcf-data-gen; do
  git fetch -q --depth=1 origin $b && git show FETCH_HEAD:journal.db > $R/j/$b.db; done
python $G/research/regsw_rebreak/fetch_live.py $R
python $G/research/regsw_rebreak/live_compass.py $R
cp -r $R ${R}_etboff
python $G/research/regsw_rebreak/base.py $R > $G/research/regsw_rebreak/base_out.txt 2>&1
REGSW_ETB_OFF=1 python $G/research/regsw_rebreak/base.py ${R}_etboff > $G/research/regsw_rebreak/base_etboff_out.txt 2>&1
echo "== RE-BREAK score"; cd $G/research/regsw_rebreak
python score.py $R > score_etbon_out.txt 2>&1; mkdir -p etbon && mv -f *.csv etbon/ 2>/dev/null
python score.py ${R}_etboff > score_etboff_out.txt 2>&1; mkdir -p etboff && mv -f *.csv etboff/ 2>/dev/null
python gapdays.py > gapdays_out.txt 2>&1
echo "evening run done $(TZ=America/New_York date)"
