import re, pandas as pd
u = pd.read_csv("/home/user/MCF/data/universe.csv")[["symbol", "name"]]
NAME = dict(zip(u.symbol, u.name))

def itype(sym):
    n = str(NAME.get(sym, ""))
    nl = n.lower()
    etf = bool(re.search(r"\betf\b|trust|fund|shares|ishares|proshares|direxion|spdr|invesco|vaneck|graniteshares|tradr|defiance|leverage shares|t-rex|volatility", nl))
    lev = bool(re.search(r"\b[23]x\b|ultra|leveraged|daily .*(bull|bear)|1\.5x|2x|3x", nl))
    inv = bool(re.search(r"bear|short|inverse|-1x|-2x|-3x", nl)) and etf
    if inv: return "inverse ETF"
    if lev and etf: return "leveraged ETF"
    if etf: return "ETF"
    return "stock" if n else "unknown"

