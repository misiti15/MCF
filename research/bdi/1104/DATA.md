# 2-year lab data cache — rebuilt 2026-11-04 (BDI 1104)

*Educational only — not financial advice.*

The nightly loop of 11-04 found no 2-year lab frames / bar cache in this container. Tonight (after the close, Alpaca
market-data GET only, keys from the environment, never printed) they were rebuilt with the repo's own tools, in the
places the repo code expects them. All of it is git-ignored; nothing below is committed except this note and the scripts.

| what | path (canonical checkout `/home/user/MCF`) | built by | size / content |
|---|---|---|---|
| 1-minute SIP bars, 1,226 lab symbols, 2024-09-16..2026-11-04, RTH, split-adjusted | `data/cache_hist/1Min/<SYM>.parquet` | `research/history2y/download.py` logic via the scratch wrapper `dl.py` (below) | 4.4 GB, 1,226 ok / 0 failed |
| lab frames (5-min, setup_lab.build + adv20), open months | `research/history2y/data/frames/month=YYYY-MM/` | `python research/history2y/build_frames.py --workers 4 --context` | 39,137,734 rows, 1,226 symbols, 22 open months (2024-10, 2025-03..2026-11), 336 s; total dir 6.9 GB incl. locked |
| locked block 2024-11..2025-02 (written by the builder into its own directory, **never read**) | `research/history2y/data/locked/` | same | refused by `lib.load_month` without `MCF_HIST_ALLOW_LOCKED=1` |
| lab context tables (spy_fo, qqq_fo, breadth, breadth_open, qqq_vwap) | `research/history2y/data/context/month=YYYY-MM.parquet` | same (`--context`) | open months only |
| daily table (per symbol-day open/high/low/close/volume/adv20) | `research/history2y/data/daily.parquet` | same | |
| head / tail 5-min bars (09:35-09:45, 15:05-15:55) + rvol12 | `research/bdi/cwt/test_b/data/headtail.parquet`, `rvol12.parquet` | `research/bdi/cwt/test_b/prep.py` `one()` per symbol via the scratch wrapper `headtail.py` (prep's `daily_features()` needs `research/swarm1010/w3_daily/data/daily_2016.parquet`, which is **not** here; `daily_feat.parquet` was therefore NOT rebuilt) | |
| 2-year trade lists, every enabled & covered lab setup in the 5 account configs (entry + exit time, production costs, stop first, 15:55 flatten) | **`research/history2y/data/bt_lab1104/sig_<month>.parquet`** (+ setups.csv; 13 MB; copied from the scratch build dir `…/scratchpad/b1104/bt/`) | `python research/bdi/1104/bt_all.py <scratch> 4` (copy of latch_1103/bt_all.py) | 22 open months, 1,165,576 trades, 95 setups with trades (96 covered of 162 enabled); inventory in `research/bdi/1104/setups.csv` |

Not rebuilt tonight (not needed by tonight's tests; say so if a later run needs them): `research/history2y/data/lab_trades.parquet`
(rescore.py scan, 21 old setups — the bt_all lists above cover the 96 covered live lab setups), 1-minute
QQQ/IWM frames (`frames_tf`), the timeofday open frame, `daily_feat.parquet`.

**Differences vs the previous cache:** the frames now run to **2026-11-04** (the old ones ended 2026-10-07/08), so open
history is ~19 sessions longer; any number recomputed tonight can differ slightly from 10-xx reports for that reason.
The universe is today's `research/lab_symbols.txt` (survivorship bias as before).

## Rebuild (≈ 25 min download at 16 workers + frame build)
```bash
# 1) bars (the repo script stops at its STOP_UTC 2026-10-09; the wrapper only moves that guard and the end date)
S=/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/b1104      # wrapper scripts live here
python research/bdi/1104/dl_wrapper.py 2024-09-16 2026-11-05 16 research/lab_symbols.txt   # copy of $S/dl.py
# 2) frames + context + daily
cd /home/user/MCF && python research/history2y/build_frames.py --workers 4 --context
# 3) head/tail
python research/bdi/1104/headtail_wrapper.py                  # copy of $S/headtail.py
# 4) 2-year trade lists for every live lab setup (SIZE1 / FLOW1-2Y reuse these)
cd research/bdi/1104 && python bt_all.py $S 4 && mkdir -p /home/user/MCF/research/history2y/data/bt_lab1104 && cp $S/bt/*.parquet setups.csv /home/user/MCF/research/history2y/data/bt_lab1104/
```
Both wrappers are committed next to this note (`dl_wrapper.py`, `headtail_wrapper.py`): `dl.py` = run `research/history2y/download.py`'s `fetch()` in a Pool after setting
`download.STOP_UTC` to a future time; `headtail.py` = `prep.one(sym)` for every symbol, concatenated as in `prep.main()`.
Disk: 4.4 GB bars + 6.9 GB frames dir (+0.2 GB head/tail); 25 GB free before the build, 16 GB after.

Read the frames only through `research/history2y/lib.py` (it refuses the locked block). SIZE1 and FLOW1-2Y: load the
trade lists with `pd.concat(pd.read_parquet(p) for p in sorted(Path('/home/user/MCF/research/history2y/data/bt_lab1104').glob('sig_*.parquet')))` — columns setup, side,
geom, symbol, date, tod (entry bar close), xtod (exit bar), kind (0 flat / 1 stop / 2 target), r (production R after costs). Trades are uncapped signal chains (no position / slot limits), as in latch_1103.
All 2-year results tonight (leads_bt.py, qr2.py) read exactly these files.
