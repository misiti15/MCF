"""Pre-declared universe and search space for arena-index-etf (see PLAN.md). Educational only - not financial advice."""
from pathlib import Path

from mcf.research.arena.indicators import INDICATORS

HERE = Path(__file__).resolve().parent
SCREEN = HERE.parent / "arena" / "single_screen.parquet"

INDEX = "SPY QQQ IWM DIA VOO IVV VTI RSP SPLG QQQM VUG VGT IWF IVW SPYG SCHG MGK VONG VOOG MTUM SPMO MDY IJH IJR " \
        "SPMD SPSM VO VB IWR IWO IWN IWP VTWO SCHA VLUE AVUV"
SECTOR = "XLE XLF XLV XLI XLK XLU XLP XLY XLB XLC XLRE SMH SOXX SOXQ IGV XBI IBB KRE KBE KBWB XRT XOP OIH XME COPX " \
         "XHB ITB IYR VNQ SCHH GDX GDXJ SILJ ARKK ARKG ITA CIBR IHI URA JETS ICLN TAN VDE VFH IYW MAGS"
LEV = "SPXL SPXS SPXU UPRO SSO SDS SH SPDN TQQQ SQQQ QLD QID PSQ TNA TZA RWM URTY SRTY UWM TWM UDOW SDOW DDM DXD DOG " \
      "SOXL SOXS TECL TECS FAS FAZ LABU LABD NUGT DUST JNUG GDXU ERX ERY DPST FNGU BULZ"
GROUP = {s: g for g, txt in (("index", INDEX), ("sector", SECTOR), ("lev", LEV)) for s in txt.split()}
ETFS = sorted(GROUP)

LIVE = [n for n, i in INDICATORS.items() if i.live]
WINDOWS = [(950, 1100), (1100, 1400), (1400, 1500), (950, 1500)]
GEOMS = ["t05s1", "t1s1", "t1s05"]
SIDES = ["long", "short"]
FILTER_INDS = ["gap_atr", "from_pc_atr", "prev_range_atr", "day_vs_prev_range", "atr_d_pct", "rvol_day", "vwap_atr",
               "fromOpen_atr", "emaDiff", "di_diff7", "adx7", "day_pos", "dist_pdh_atr", "dist_pdl_atr",
               "sma50_dist_pct", "or_high_dist_atr"]
TRAIN_H1_END = "2025-07"      # train halves: <= 2025-07 / >= 2025-08
LINEAGE_PRIOR = {"arena": 20282, "arena-am-long": 23032, "arena-am-short": 22932, "arena-mid-long": 30752,
                 "arena-mid-short": 30572, "arena-pm-both": 61440, "bdi/idxdip1015": 1134, "bdi/indexlink": 2995}
