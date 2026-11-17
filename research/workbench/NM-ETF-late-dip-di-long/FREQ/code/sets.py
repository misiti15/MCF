"""FREQ (frequency job) symbol sets for NM-ETF-late-dip-di-long. Built from the live universe.csv (origin/mcf-data, 2026-11-16)
names + ADV (liquidity floor: ADV >= $95M, price >= $5, as the parent; per-day adv20 >= $95M still applies in the engine).
Groups (each tested one at a time on top of the parent's 128-ETF list):
  PAR    the module's own 128 ETFs (24 of them are missing from the old 1,226-symbol cache -> fetched, so the parent is complete)
  EQ1X   more 1x equity ETFs (sector / industry / thematic / country / size / style) not already in the list
  LEVIX  leveraged / inverse index, sector, country ETFs not in the list (ADV >= $95M: few; LEV50 lowers ADV to $40M)
  SSLEV  single-stock leveraged / inverse ETFs (NVDL, TSLL, MUU, ...)
  CMDTY  commodity ETFs/ETNs (oil, gas, silver, gold) incl. leveraged
  CRYPTO spot / 2x crypto ETFs
  VIX    volatility ETPs - excluded (contango decay: a different mechanism), listed for completeness only
  STK    large-cap single stocks (ADV >= $1B) - only as a mechanism check
Educational only - not financial advice."""
import json, re, subprocess, io, importlib.util, pandas as pd
spec = importlib.util.spec_from_file_location("m", "/home/user/MCF/research/swarm1017/arena-index-etf/modules/AR-ETF-late-dip-di-long.py")
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
PAR = sorted(M.SYMBOLS)
VIX = ["UVXY", "UVIX", "VXX", "SVIX"]
SSLEV = ["INTW", "CRWG", "SNDQ", "MSTU", "RAM", "MUU", "AMDL", "NVDL", "SSPC", "SPCH", "TSLQ", "TSLL", "TSLG", "NVD", "GGLL",
         "MSFU", "METU", "PLTD", "AMZD"]
SSLEV50 = SSLEV + ["NVDU", "NVDX", "AMZU", "TSLZ", "SMCX"]
CMDTY = ["UCO", "SCO", "BOIL", "USO", "BNO", "UNG", "SLV", "SIVR", "GLD", "GLDM", "IAU", "SGOL", "IAUM", "PHYS", "PSLV", "PDBC"]
CRYPTO = ["IBIT", "FBTC", "GBTC", "BITO", "ETHA", "BITX"]
LEVIX = ["KORU", "TMF"]
LEV50 = LEVIX + ["USD", "NAIL", "YINN", "TMV", "GDXD", "ZSL", "ETHU"]
BOND_INC = ["TMF", "EDV", "ICVT", "PGX", "PFF", "JEPI", "JEPQ", "QYLD", "QQQI", "GPIQ", "SPYI"]

if __name__ == "__main__":
    raw = subprocess.run(["git", "-C", "/home/user/MCF", "show", "origin/mcf-data:universe.csv"], capture_output=True, check=True).stdout
    u = pd.read_csv(io.BytesIO(raw))
    pat = r"\bETF\b|\bETN\b|Fund|ProShares|Direxion|iShares|SPDR|VanEck|Leverage|\b2X\b|\b3X\b|Ultra|Daily Target|GraniteShares|Tradr|T-Rex|Roundhill|MicroSectors"
    stock_pat = r"Common Stock|Inc\.|Corporation|Ltd|plc|N\.V\.|S\.A\.|Class A|Ordinary|Depositary|Holdings"
    isetf = u.name.str.contains(pat, case=False, regex=True) & ~u.name.str.contains(stock_pat, case=False, regex=True)
    liq = (u.adv >= 95e6) & (u.price >= 5)
    other = set(PAR) | set(VIX) | set(SSLEV) | set(CMDTY) | set(CRYPTO) | set(LEVIX) | set(BOND_INC)
    EQ1X = sorted(u[isetf & liq & ~u.symbol.isin(other)].symbol)
    STK = sorted(u[~isetf & (u.adv >= 1e9) & (u.price >= 5)].symbol)
    S = dict(PAR=PAR, EQ1X=EQ1X, LEVIX=LEVIX, LEV50=LEV50, SSLEV=SSLEV, SSLEV50=SSLEV50, CMDTY=CMDTY, CRYPTO=CRYPTO, VIX=VIX, STK=STK)
    json.dump(S, open("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/etffreq/sets.json", "w"), indent=0)
    print({k: len(v) for k, v in S.items()})
    print("EQ1X", EQ1X); print("STK", len(STK), STK[:40])
