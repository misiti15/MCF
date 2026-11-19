"""Build the EQB universe, leverage / inverse flags and exposure groups for ULT-21 (round3/PLAN.md sec. 2), from fund
names / types only (no outcomes). Written 2026-11-19 before any round-3 fit scoring. Educational only - not financial advice."""
import json
from datetime import datetime, timezone
from pathlib import Path

ULT = Path(__file__).resolve().parents[2]
U = json.loads((ULT / "modules" / "ULT-12_symbols.json").read_text())
WB4 = sorted(U["WB4"])
# lab ETFs outside the WB4 list whose holdings are an equity basket of >= 10 stocks (any leverage, long or inverse)
EXTRA = ["ACWX", "AIRR", "ASHR", "AVDE", "AVDV", "AVEM", "BAI", "BBJP", "BLCR", "CGGR", "CORO", "DRAM", "EEM", "EFA",
         "EFG", "EFV", "EMXC", "EWC", "EWJ", "EWT", "EWY", "EWZ", "FNDF", "FXI", "IDEV", "IEFA", "IEMG", "IXUS", "KORU",
         "KWEB", "RAM", "SCHE", "SCHF", "SCZ", "SHLD", "SPDW", "VEA", "VEU", "VFLO", "VGK", "VT", "VWO", "VXUS"]
EXCLUDED = {"single-stock": ["AAOX", "AAPD", "AMDL", "AMZD", "AVS", "AXTX", "BMNU", "CONL", "GGLL", "INTW", "METU", "MSFU",
                             "MSTU", "MSTX", "MULL", "MUU", "NVDL", "SNDQ", "SNDU", "SNXX", "SPCH", "SSPC", "TSLG", "TSLL", "TSLQ"],
            "commodity/metal/energy futures": ["AGQ", "BNO", "BOIL", "BWET", "GLD", "GLDM", "IAU", "IAUM", "PDBC", "PHYS",
                                               "PSLV", "SCO", "SGOL", "SLV", "UCO", "UGL", "UNG", "USO", "ZSL"],
            "crypto": ["BITO", "BITX", "ETHA", "ETHU", "FBTC", "GBTC", "IBIT"], "volatility": ["UVXY", "VXX"],
            "bond": ["EDV", "IGLB", "SPTL", "TLT", "TMF", "VCLT", "VGLT"], "managed futures / option income": ["DBMF", "QQQI"]}
EQB = sorted(set(WB4) | set(EXTRA))
assert set(EQB) | {s for v in EXCLUDED.values() for s in v} == set(U["E"]) - {"SPY"} | {"SPY"} | set(EQB)
LEV = {**{s: 3 for s in ["TQQQ", "SQQQ", "UPRO", "SPXL", "SPXU", "SPXS", "TNA", "TZA", "URTY", "SRTY", "UDOW", "SDOW",
                         "SOXL", "SOXS", "TECL", "TECS", "LABU", "LABD", "DPST", "FAS", "FAZ", "GDXU", "FNGU", "BULZ", "KORU"]},
       **{s: 2 for s in ["QLD", "QID", "SSO", "SDS", "UWM", "TWM", "DDM", "DXD", "ERX", "ERY", "NUGT", "DUST", "JNUG", "RAM"]}}
INV = ["SQQQ", "QID", "PSQ", "SPXU", "SPXS", "SDS", "SH", "SPDN", "TZA", "SRTY", "TWM", "RWM", "SDOW", "DXD", "DOG",
       "SOXS", "TECS", "LABD", "FAZ", "ERY", "DUST"]
GROUPS = {
    "NDX": ["QQQ", "QQQM", "QLD", "TQQQ", "PSQ", "QID", "SQQQ"],
    "SPX": ["SPY", "IVV", "VOO", "SPLG", "SSO", "UPRO", "SPXL", "SH", "SDS", "SPXU", "SPXS", "SPDN", "RSP", "VTI", "BLCR", "VFLO", "VLUE"],
    "LCG": ["IWF", "VUG", "SCHG", "VONG", "MGK", "IVW", "SPYG", "VOOG", "MAGS", "FNGU", "BULZ", "MTUM", "SPMO", "CGGR"],
    "R2K": ["IWM", "VTWO", "TNA", "TZA", "UWM", "TWM", "URTY", "SRTY", "RWM", "IWN", "IWO", "AVUV", "SCHA", "VB", "IJR", "SPSM"],
    "MID": ["IJH", "MDY", "SPMD", "IWR", "IWP", "VO"],
    "DOW": ["DIA", "DDM", "UDOW", "DOG", "DXD", "SDOW"],
    "SEMI": ["SMH", "SOXX", "SOXQ", "SOXL", "SOXS", "DRAM", "RAM"],
    "TECH": ["XLK", "VGT", "IYW", "TECL", "TECS", "IGV", "CIBR", "BAI", "ARKK"],
    "BIO": ["XBI", "IBB", "LABU", "LABD", "ARKG"],
    "RBANK": ["KRE", "KBE", "DPST", "KBWB"],
    "FIN": ["XLF", "VFH", "FAS", "FAZ"],
    "ENERGY": ["XLE", "VDE", "ERX", "ERY", "XOP", "OIH"],
    "GOLDMIN": ["GDX", "GDXJ", "GDXU", "NUGT", "DUST", "JNUG", "SILJ"],
    "HOME": ["ITB", "XHB"],
    "REIT": ["IYR", "VNQ", "SCHH", "XLRE"],
    "METALS": ["XME", "COPX"],
    "CHINA": ["FXI", "KWEB", "ASHR"],
    "KOREA": ["EWY", "KORU"],
    "EM": ["EEM", "IEMG", "VWO", "AVEM", "SCHE", "EMXC"],
    "DEVX": ["EFA", "IEFA", "VEA", "SCHF", "IDEV", "SPDW", "AVDE", "FNDF", "EFG", "EFV", "SCZ", "AVDV", "VGK"],
    "WORLDX": ["ACWX", "IXUS", "VEU", "VXUS", "CORO"],
}
grp = {}
for g, ss in GROUPS.items():
    for s in ss:
        assert s in EQB, s
        assert s not in grp, s
        grp[s] = g
for s in EQB:
    grp.setdefault(s, s)            # others: own group
assert all(s in EQB for s in LEV) and all(s in EQB for s in INV)
out = {"note": "ULT-21 / round-3 EQB universe (equity-basket ETFs of >= 10 stocks, any leverage, long or inverse), "
               "built from fund names/types only before any round-3 fit scoring. Educational only - not financial advice.",
       "frozen_utc": datetime.now(timezone.utc).isoformat(), "WB4": WB4, "EQB": EQB, "excluded_from_E": EXCLUDED,
       "leverage": {s: LEV.get(s, 1) for s in EQB}, "inverse": sorted(INV), "group": grp}
(ULT / "modules" / "ULT-21_universe.json").write_text(json.dumps(out, indent=1))
print(len(EQB), "EQB names;", len(set(grp.values())), "exposure groups")
