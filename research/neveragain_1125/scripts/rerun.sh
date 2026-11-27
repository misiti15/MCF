#!/bin/bash
# post-close rerun: fresh Primary journal (partial blob fetch, own dir), bars for today, replay + score. Educational only.
set -e
N=/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/neveragain
cd $N/g && timeout 300 git fetch -q --depth=1 --filter=blob:none origin mcf-data && git log -1 --format='%ci %s' FETCH_HEAD && git show FETCH_HEAD:journal.db > $N/live/p_new.db
cd $N/../inbox && python $N/live_fetch.py $N/live $N/live/p_new.db --refresh=2026-11-25 2>&1 | grep -v -i warn | tail -3
cd $N && for b in RAW NEUTRAL; do python live_sim.py live primary $b "G5a=G1-3+G4;G5b=G1-3+G2-6+G4;G1-2+G4=G1-2+G4;G1-2+G4+SV=G1-2+G4" > /dev/null; python score_live.py live $b > live_score_$b.txt 2>&1; done
rm -f $N/live/p_new.db
head -20 $N/live_score_RAW.txt
