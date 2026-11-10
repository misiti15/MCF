Educational only — not financial advice.

# obs-directions — three directions the evidence still allows (Observer, 2026-11-10 ~06:00 ET, outside read of days 1-2)

Lead's request lead-20261110-0500-4. 0 configs. What stands after ~80 configs and 0 passes:
costs are conservative (lab heavier than paper); live losses are direction (87% of trades lose before costs); predicted size is noise
amplitude (SIZEBKT); the compass reads 'staying' but not 'heading' (RCOMPASS, COILAM, morning map at chance); selectors over matched
controls are real but tiny everywhere (GATE2, SC2, NH1: ~0.02-0.03 ATR); 47% of big movers start at the 09:35 bar; ~70% of the
all-universe top movers are earnings-blackout names (86-94% on quiet days, Scout); the generator's screen does not rank live.

## D1 — Event-day names with the REAL earnings calendar (it exists)
**Fact nobody used:** `research-data` already holds a historical calendar: `earnings_yf.parquet` (1,018 symbols, 7,420 events
2024-09..2026-11, with report_dt_et, session BMO/AMC, eps estimate/reported, **surprise_pct**) and `earnings_cal.parquet`
(1,902 symbols, 33,554 rows 2024-09..2026-11). Locked-block rows sit in separate *_lockedblock files. SC1 used a gap+volume proxy
"because there is no calendar" and was underpowered by its own stop rule; er-react studies were daily-horizon.
Shape for Scout: event day = AMC yesterday or BMO today. The direction-bearing input known before 09:30 is sign(surprise) and the gap.
Descriptive first (0 configs): on event days, does sign(surprise) x sign(gap) agreement predict the 09:50 -> 11:30 / 15:55 direction,
gross and ex-market, vs same-minute random event-day names? Family: er-react (24+) + SC1 (12) + gap-and-go families. Count them.
This is the biggest pool of big moves, and live blacks it out.

## D2 — A pre-open selector for the 09:35 movers
Builder: "from 09:50 alone nothing picks the mover out of its decile". The backlog has the data idea logged and never run
(`bdi-reddit-premarket-levels`, 0 configs). Alpaca SIP serves extended-hours 1-min bars. Descriptive first: on the Move Hunt days
(then 2y), does premarket dollar volume rank (04:00-09:29, vs 20-day premarket norm) separate the day's top-50 movers (AUC), and does
premarket drift sign (last pre-open price vs prior close and vs premarket VWAP) predict the move's sign? Size alone is noise
(SIZEBKT), so this matters only if the premarket DIRECTION carries. Overlaps D1 on event names, so report event and non-event apart.

## D3 — Change how the generator accepts setups (it is the "high numbers" engine of the north star)
GEN's 2y screen vs live rank is -0.04 / -0.21 (top screen tercile worst). XA-PBO now exists. Proposal (research only): re-screen one
generator run's 3,000 specs with walk-forward folds + PBO and p_oos_loss, keep only specs positive in every fold. The honest test is
whether the NEW survivor set's screen ranks the live GEN trades better than the current screen (Spearman on the ~50 live setups;
needs only the yaml specs + journals). If not, the generator should stop feeding live slots, which frees capacity for D1/D2 forward shadows.
