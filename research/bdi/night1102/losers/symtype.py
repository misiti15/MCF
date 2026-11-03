"""Symbol type from data/universe.csv names: stock / etf / lev (2x-3x long) / inverse (any short/bear/inverse ETF)."""
import re
import pandas as pd
U = pd.read_csv("/home/user/MCF/data/universe.csv")[["symbol", "name"]].drop_duplicates("symbol").set_index("symbol").name.fillna("")
INV = re.compile(r"\bBear\b|UltraShort|Ultra Short|Inverse|\bShort\b|-1X|-2X|-3X|\bSH\b", re.I)
LEV = re.compile(r"\b[1-3](\.\d+)?X\b|\bUltra(Pro)?\b|Leveraged|\bBull\b|2x|3x", re.I)
ETF = re.compile(r"\bETF\b|\bETN\b|\bFund\b|iShares|SPDR|ProShares|Direxion|Invesco|Vanguard|\bTrust\b.*(Gold|Silver|Bitcoin|Ether)", re.I)
FALLBACK = {"SQQQ": "inverse", "SOXS": "inverse", "SPXU": "inverse", "SDS": "inverse", "SH": "inverse", "PSQ": "inverse",
            "TZA": "inverse", "UVIX": "inverse", "UVXY": "inverse", "VXX": "inverse", "VIXY": "inverse", "DOG": "inverse", "TQQQ": "lev", "SOXL": "lev", "SPXL": "lev", "TNA": "lev",
            **{k: "etf" for k in "SPLV IWB IWV SPY SCHD HDV SPHQ JEPQ SCHB VTI".split()}}
# "inverse" = moves against its underlying / against the equity market (inverse ETFs and long-VIX products)


def symtype(sym: str) -> str:
    if sym in FALLBACK:
        return FALLBACK[sym]
    n = U.get(sym, "")
    if not n:
        return "unknown"
    if ETF.search(n) or LEV.search(n) and ("Daily" in n or "Shares" in n):
        if INV.search(n):
            return "inverse"
        if LEV.search(n):
            return "lev"
        return "etf"
    return "stock"
