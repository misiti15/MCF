#!/bin/bash
# Post-close re-pull and re-run of every live piece (research only). Usage: bash final.sh <scratch-pr29>
set -e
S=$1; H=/home/user/MCF/research/bdi/primary1029; cd /home/user/MCF
git fetch -q origin mcf-data; git show origin/mcf-data:journal.db > $S/p/journal.db
git log origin/mcf-data -1 --format='%cd %s'
python $H/fetch.py $S --force
python $H/autopsy.py $S > $H/autopsy_out.txt
python $H/live_days.py $S > $H/live_days_out.txt
python $H/live_rules.py $S > $H/live_rules_out.txt
python $H/live_wide.py $S --fetch > $H/live_wide_out.txt
python $H/stp_whatif.py $S > $H/stp_whatif_out.txt
python $H/regime_today.py $S > $H/regime_out.txt
python $H/other_accts.py $S > $H/other_accts_out.txt
echo done
