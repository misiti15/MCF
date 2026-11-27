"""Direction-correct inverse handling: JOURNAL-ONLY forward shadow (owner 2026-11-19 "INV yes ... done correctly").
Rule frozen 2026-11-20 - see RULE.md. RESEARCH ONLY: reads the account journals (git show origin/<data branch>:journal.db),
never places, changes or blocks an order, never writes config.

    python research/owner1120/inverse/shadow.py --date YYYY-MM-DD [--date ...]   # upsert rows for those sessions
    python research/owner1120/inverse/shadow.py --since 2026-11-20               # every session from a date
    python research/owner1120/inverse/shadow.py --score                          # tally + pass-bar status

Writes forward.csv: one row per closed run-1 trade (any account) on an inverse / long-vol / leveraged-long symbol, plus
one row per short signal on an underlying that has an inverse fund (the "inverse buy" opportunity), with the frozen
handling's verdict (block / keep / inverse_buy) and the trade's R after costs. Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / "forward.csv"
FROZEN = "2026-11-20"
FORWARD_FROM = "2026-11-20"
LOCK_A, LOCK_B = "2024-11-01", "2025-02-28"
BRANCHES = {"primary": "mcf-data", "testing": "mcf-data-testing", "testing2": "mcf-data-testing2",
            "gen": "mcf-data-gen", "graveyard": "mcf-data-graveyard", "livelab": "mcf-data-livelab",
            "explore1": "mcf-data-explore1", "testingd": "mcf-data-testingd", "testinge": "mcf-data-testinge",
            "testingf": "mcf-data-testingf"}

# ---------------------------------------------------------------- frozen classes (same names as compass_gate/shadow.py)
INV_BROAD = frozenset("SH SDS SPXU SPXS SPDN PSQ QID SQQQ DOG DXD SDOW RWM TWM TZA SRTY MZZ SMDD SBB HIBS".split())
INV_SECTOR = frozenset("""SOXS TECS FAZ SKF SEF LABD ERY DUG DRIP DUST JDST GDXD YANG FXP EDZ EEV EUM EFZ REK SRS SIJ SSG
FNGD BERZ WEBS SARK BTAL DRV OILD HDGE""".split())
INV_CRYPTO = frozenset("BITI SBIT ETHD".split())
INV_SINGLE = frozenset("""AAPD AMZD MSFD PLTD PLTZ NVD NVDQ NVDS NVDD TSDD TSLQ TSLZ TSLS MSTZ AMDD DAMD MUD MUZ SNDQ BMNZ
LITZ SKDD SKHZ AVS AAOZ NBIZ IREZ SPCG SPCQ SSPC SMST SNK BEZ AXTQ CBRZ CONI
METD METQ IONZ RKLZ RGTZ QBTZ GGLS ORCZ ORCS RAMZ APLZ SMZ PALD ASTN WNTR FIAT""".split())  # 2nd line: skeptic F5, added 11-19 pre-forward
INVERSE = INV_BROAD | INV_SECTOR | INV_CRYPTO | INV_SINGLE
LONG_VOL = frozenset("VXX UVXY VIXY UVIX VIXM VXZ".split())
NEUTRAL = frozenset("""GLD GLDM IAU IAUM AAAU SGOL OUNZ PHYS BAR SLV SIVR PSLV PPLT PALL GLL ZSL AGQ UGL USO BNO UCO SCO
USL UNG BOIL KOLD DBC PDBC DBA DBMF KMLM CTA TLT TMF TMV TBT TBF EDV VGLT SPTL IEF SHY BIL SGOV TLH ZROZ GOVT BND AGG
LQD HYG JNK UUP UDN FXE FXY CPER CORN WEAT TTT""".split())
# leveraged LONG funds (2x/3x, single-stock and index), frozen 2026-11-20 from data/universe.csv names
LEV_LONG = frozenset("""AAPB AAPU AAPX AMDG AMDL AMUU AMZU AMZZ APLX ARMG ASMG ASMU AVGG AVGU AVGX AVL AXTU AXTX BABX BITU
BITX BMNG BMNU BOEU BRZU BTCL BTCU BULZ CBRX CONL CONX COTG CRCA CRCG CRDU CRMG CRWG CRWL CRWU CURE CWEB DDM DFEN DIG DPST
DRN EDC ERX ETHT ETHU FAS FBL FNGU GDXU GGLL GOOX GUSH HIBL HOOG HOOX INTW IONL IONX JNUG KORU LABU LABX LITU LITX MIDU
MQQQ MRAL MSFL MSFU MSFX MSTU MSTX MULL MUU MVV NAIL NBIL NEBX NFXL NRGU NUGT NVDG NVDL NVDU NVDX OILU ORCU ORCX PALU
PLTU PTIR QLD QPUX QQQU QUBX RETL RGTX RKLX ROM SMCL SMCX SNDU SOFX SOLT SOXL SPXL SPYU SSO TECL TMF TNA TQQQ TSLL TSLR
TSLT TSMU TSMX UBT UCO UDOW UGL UPRO URAA URTY USD UTSL UWM UXRP UYG WEBL XXRP YINN AGQ BOIL""".split()) - NEUTRAL
# underlying + leverage of each inverse fund (None = no tradeable equity underlying in the universe)
UNDERLYING = {
    **{s: ("SPY", l) for s, l in [("SH", 1), ("SDS", 2), ("SPXU", 3), ("SPXS", 3), ("SPDN", 1), ("HIBS", 3)]},
    **{s: ("QQQ", l) for s, l in [("PSQ", 1), ("QID", 2), ("SQQQ", 3)]},
    **{s: ("DIA", l) for s, l in [("DOG", 1), ("DXD", 2), ("SDOW", 3)]},
    **{s: ("IWM", l) for s, l in [("RWM", 1), ("TWM", 2), ("TZA", 3), ("SRTY", 3)]},
    **{s: ("MDY", l) for s, l in [("MZZ", 2), ("SMDD", 3)]}, "SBB": ("IJR", 1),
    "SOXS": ("SOXX", 3), "SSG": ("SOXX", 2), "TECS": ("XLK", 3), "FAZ": ("XLF", 3), "SKF": ("XLF", 2), "SEF": ("XLF", 1),
    "LABD": ("XBI", 3), "ERY": ("XLE", 2), "DUG": ("XLE", 2), "DRIP": ("XOP", 2), "DUST": ("GDX", 2), "GDXD": ("GDX", 3),
    "JDST": ("GDXJ", 2), "YANG": ("FXI", 3), "FXP": ("FXI", 2), "EDZ": ("EEM", 3), "EEV": ("EEM", 2), "EUM": ("EEM", 1),
    "EFZ": ("EFA", 1), "REK": ("IYR", 1), "SRS": ("IYR", 2), "SIJ": ("XLI", 2), "SARK": ("ARKK", 1), "FNGD": (None, 3),
    "BERZ": (None, 3), "WEBS": (None, 3), "BTAL": (None, 1),
    "AAPD": ("AAPL", 1), "AMZD": ("AMZN", 1), "MSFD": ("MSFT", 1), "PLTD": ("PLTR", 1), "PLTZ": ("PLTR", 2),
    "NVD": ("NVDA", 2), "NVDQ": ("NVDA", 2), "NVDS": ("NVDA", 1.5), "NVDD": ("NVDA", 1), "TSDD": ("TSLA", 2),
    "TSLQ": ("TSLA", 2), "TSLZ": ("TSLA", 2), "TSLS": ("TSLA", 1), "MSTZ": ("MSTR", 2), "SMST": ("MSTR", 2),
    "AMDD": ("AMD", 1), "DAMD": ("AMD", 2), "MUD": ("MU", 1), "MUZ": ("MU", 2), "SNDQ": ("SNDK", 2), "BMNZ": ("BMNR", 2),
    "LITZ": ("LITE", 2), "AVS": ("AVGO", 1), "AAOZ": ("AAOI", 2), "NBIZ": ("NBIS", 2), "IREZ": ("IREN", 2),
    "AXTQ": ("AXTI", 2), "CONI": ("COIN", 2), "CBRZ": ("CBRS", 2), "BEZ": (None, 2), "SKDD": (None, 2), "SKHZ": (None, 1),
    "SPCG": (None, 2), "SPCQ": (None, 2), "SSPC": (None, 2), "SNK": (None, 2),
    "BITI": ("IBIT", 1), "SBIT": ("IBIT", 2), "ETHD": ("ETHA", 2),
    # skeptic F5 additions (2026-11-19 evening, before the first forward session)
    "METD": ("META", 1), "METQ": ("META", 2), "IONZ": ("IONQ", 2), "RKLZ": ("RKLB", 2), "RGTZ": ("RGTI", 2),
    "QBTZ": ("QBTS", 2), "GGLS": ("GOOGL", 1), "ORCZ": ("ORCL", 2), "ORCS": ("ORCL", 1), "RAMZ": (None, 2),
    "APLZ": ("APLD", 2), "SMZ": ("SMR", 2), "PALD": ("PANW", 1), "ASTN": ("ASTS", 2), "WNTR": ("MSTR", 1),
    "FIAT": ("COIN", 1), "DRV": (None, 3), "OILD": ("XOP", 3), "HDGE": (None, 1),
}
INVERSE_OF: dict[str, list[str]] = {}
for _x, (_u, _l) in UNDERLYING.items():
    if _u:
        INVERSE_OF.setdefault(_u, []).append(_x)

# ---------------------------------------------------------------- frozen per-setup handling (RULE.md section 3)
# default for every setup: SHORT on INVERSE/LONG_VOL -> block; LONG on INVERSE/LONG_VOL -> keep; short signal on an
# underlying U not executed for borrow/spread/cost -> inverse_buy (journal only). Exceptions below (empty = none).
SHORT_KEEP = frozenset({                    # setups whose inverse SHORTS are kept (H2S fit + check both >= 0)
    "GEN-261022-07-Z12lem1p9-FlowShiftlem0p96-ATRdge3p6-AM-BRopgt0p5-t1s1-short",
    "GEN-261027-07-RSI14le35-FromOpenge2-AM-BRvwlt0p5-t1s1-short", "NM-AMS-N1-quiet-morning-short",
    "NM-RWR3-ns3-qqqup-early-short", "NS2-sma50break-overbought-short-FD", "NS3V1-am-widestop-short",
    "RW1-gapdn-bounce-flowsell-short-FD"})
LONG_BLOCK = frozenset({                    # setups whose inverse LONGS are blocked (live and lab-check both < 0)
    "CWT12-coil-k6-long", "CWT14-failbrk-orl-p05-long", "CWT14-failbrk-orl-p05-lowvol-long",
    "CWT14-failbrk-orl-p10-long", "CWT14-failbrk-orl-p10-lowvol-long", "CWT14-failbrk-pdl-p05-long",
    "CWT14-failbrk-pdl-p10-lowvol-long",
    "GEN-261023-04-EMAdChglem0p028-PDHdistle0p074-EMAdifflem0p46-PM-QQQltm0p6-t1s1-long",
    "NS5-sma50-flush-oversold-long-FD", "ST2-slope20up-long-am-t05s1-FD"})
INVBUY_REASONS = re.compile(r"not shortable|ETB|spread|cost filter|size < 1", re.I)


def family_of(setup: str) -> str:
    s = str(setup or "")
    return s.split("-", 1)[0] if "-" in s else re.sub(r"_[a-z]$", "", s)


# Name rule (skeptic F5): a fund not in the lists above whose data/universe.csv name reads as inverse (Bear / Inverse /
# Short / -Nx) is classed inv_name, so new launches are caught when the universe is rebuilt. Treasury/bond/duration and
# VIX names are excluded (handled by NEUTRAL / LONG_VOL / beta +1 short-vol funds such as SVXY, SVIX).
_INV_NAME = re.compile(r"\bBear\b|\bInverse\b|\bShort\b|-\d(?:\.\d+)?[xX]\b", re.I)
_INV_EXCL = re.compile(r"Short[- ]Term|Short Treasury|Short Duration|Short Maturity|Treasury|Bond|Muni|Long/Short|"
                       r"Long-Short|VIX|Volatility", re.I)
_FUND = re.compile(r"\bET[FN]s?\b|\bFund\b|\bTrust\b|ProShares|Direxion|Tradr|Defiance|GraniteShares|MicroSectors|T-Rex", re.I)
_NAME_INV: frozenset[str] | None = None


def _name_inverse() -> frozenset[str]:
    global _NAME_INV
    if _NAME_INV is None:
        try:
            u = pd.read_csv(ROOT / "data" / "universe.csv", usecols=["symbol", "name"]).fillna("")
            m = u.name.str.contains(_INV_NAME) & u.name.str.contains(_FUND) & ~u.name.str.contains(_INV_EXCL)
            _NAME_INV = frozenset(u.symbol[m].str.upper())
        except Exception:  # universe missing: fall back to the frozen lists only
            _NAME_INV = frozenset()
    return _NAME_INV


def pclass(sym: str) -> str:
    s = str(sym).upper()
    for name, st in (("inv_broad", INV_BROAD), ("inv_sector", INV_SECTOR), ("inv_single", INV_SINGLE),
                     ("inv_crypto", INV_CRYPTO), ("long_vol", LONG_VOL), ("neutral", NEUTRAL), ("lev_long", LEV_LONG)):
        if s in st:
            return name
    if s in _name_inverse():
        return "inv_name"
    return "stock_etf"


def beta_sign(sym: str) -> int:
    c = pclass(sym)
    return -1 if c.startswith("inv") or c == "long_vol" else 0 if c == "neutral" else 1


def verdict(setup: str, side: int, sym: str) -> str:
    """Frozen handling for one trade: 'block' | 'keep' | 'none' (not an inverse/long-vol symbol)."""
    if beta_sign(sym) != -1:
        return "none"
    if side < 0:
        return "keep" if setup in SHORT_KEEP else "block"
    return "block" if setup in LONG_BLOCK else "keep"


# ---------------------------------------------------------------- journal reading
def _journal(branch: str, git_dir: str) -> Path | None:
    subprocess.run(["git", "-C", git_dir, "fetch", "-q", "origin", f"+refs/heads/{branch}:refs/remotes/origin/{branch}"],
                   capture_output=True)
    r = subprocess.run(["git", "-C", git_dir, "show", f"origin/{branch}:journal.db"], capture_output=True)
    if r.returncode or not r.stdout:
        return None
    fd, name = tempfile.mkstemp(prefix=f"invshadow_{branch}_", suffix=".db")
    p = Path(name)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(r.stdout)
    except BaseException:
        p.unlink(missing_ok=True)
        raise
    return p  # the caller unlinks it (rows_for: finally; leftover copies filled /tmp, inspector 11-27 #15)


def rows_for(dates: list[str], git_dir: str = str(ROOT)) -> pd.DataFrame:
    sys.path.insert(0, str(ROOT))
    from mcf.costs import with_cost_r
    out = []
    for acct, br in BRANCHES.items():
        p = _journal(br, git_dir)
        if p is None:
            continue
        c = None
        try:
            c = sqlite3.connect(p)
            q = ",".join("?" * len(dates))
            t = pd.read_sql(f"select * from trades where run_id=1 and exit is not null and shares>0 and entry!=stop "
                            f"and date in ({q})", c, params=dates)
            if len(t):
                t = with_cost_r(t)
                t = t[t.symbol.map(lambda s: pclass(s) in ("inv_broad", "inv_sector", "inv_single", "inv_crypto",
                                                                "inv_name", "long_vol", "lev_long"))]
                for r in t.itertuples():
                    out.append(dict(date=r.date, account=acct, setup=r.strategy, family=family_of(r.strategy),
                                    kind="trade", symbol=r.symbol, side=int(r.side), pclass=pclass(r.symbol),
                                    exposure=int(r.side) * beta_sign(r.symbol),
                                    thesis_match=int(int(r.side) * beta_sign(r.symbol) == int(r.side)),
                                    verdict=verdict(r.strategy, int(r.side), r.symbol), R=round(float(r.r_multiple), 4),
                                    reason="", frozen=FROZEN))
            s = pd.read_sql(f"select day,symbol,strategy,side,status,reason from signals where run_id=1 and side=-1 "
                            f"and day in ({q})", c, params=dates)
            s = s[s.symbol.isin(INVERSE_OF) & (s.status == "skipped") & s.reason.fillna("").str.contains(INVBUY_REASONS)]
            for (d, sym, st), g in s.groupby(["day", "symbol", "strategy"]):
                out.append(dict(date=d, account=acct, setup=st, family=family_of(st), kind="inverse_buy_opportunity",
                                symbol=sym, side=-1, pclass="underlying", exposure=-1, thesis_match=1,
                                verdict="inverse_buy:" + "/".join(INVERSE_OF[sym]), R=float("nan"),
                                reason=str(g.reason.iloc[0]), frozen=FROZEN))
        finally:
            if c is not None:
                c.close()
            p.unlink(missing_ok=True)
    return pd.DataFrame(out)


def upsert(df: pd.DataFrame, dates: list[str]) -> None:
    old = pd.read_csv(OUT) if OUT.exists() else pd.DataFrame()
    if len(old):
        old = old[~old.date.isin(dates)]
    new = pd.concat([old, df], ignore_index=True).sort_values(["date", "account", "setup", "symbol"])
    new.to_csv(OUT, index=False)


def score() -> None:
    if not OUT.exists():
        print("no forward.csv yet")
        return
    f = pd.read_csv(OUT)
    f = f[(f.date >= FORWARD_FROM) & (f.kind == "trade")]
    days = f.date.nunique()
    # default columns carry the pass bar; the per-setup exceptions (SHORT_KEEP, LONG_BLOCK) are read separately
    # (skeptic F3: both lists were picked partly on check data, so only this forward record can test them)
    blk = f[(f.verdict == "block") & (f.side < 0)]
    keep = f[(f.verdict == "keep") & (f.side > 0)]
    sk = f[(f.verdict == "keep") & (f.side < 0)]
    lb = f[(f.verdict == "block") & (f.side > 0)]
    g = blk.groupby(["account", "setup"]).R.sum()
    worse = (g > 0.005)          # blocking a setup's net-positive inverse shorts makes it worse
    print(f"sessions {days} (bar: >= 10)")
    print(f"blocked inverse shorts: {len(blk)} trades, {blk.R.sum():+.2f}R (bar: < 0); setups {len(g)}, "
          f"not worse {int((~worse).sum())} ({(~worse).mean() if len(g) else float('nan'):.0%}; bar >= 60%); "
          f"largest worsening {g.max() if len(g) else 0:+.2f}R (bar <= 3R)")
    print(f"kept inverse longs: {len(keep)} trades, {keep.R.sum():+.2f}R (bar: >= 0)")
    print(f"SHORT_KEEP column (exception, read separately): {len(sk)} kept inverse shorts, {sk.R.sum():+.2f}R "
          f"(exception holds if >= 0)")
    print(f"LONG_BLOCK column (exception, read separately): {len(lb)} blocked inverse longs, {lb.R.sum():+.2f}R "
          f"(exception holds if < 0)")
    nm = f[f.pclass == "inv_name"]
    print(f"name-rule (inv_name) trades: {len(nm)}, {nm.R.sum():+.2f}R")
    lev = f[f.pclass == "lev_long"]
    print(f"leveraged-long trades (info): {len(lev)}, {lev.R.sum():+.2f}R")
    ok = days >= 10 and blk.R.sum() < 0 and (len(g) == 0 or ((~worse).mean() >= 0.6 and g.max() <= 3)) \
        and keep.R.sum() >= 0
    print("PASS" if ok else ("pending" if days < 10 else "FAIL"), "- Educational only - not financial advice")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", action="append", default=[])
    ap.add_argument("--since")
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--git-dir", default=str(ROOT))
    a = ap.parse_args()
    if a.score:
        return score()
    dates = list(a.date)
    if a.since:
        dates += [str(d.date()) for d in pd.bdate_range(a.since, pd.Timestamp.now().normalize())]
    dates = sorted({d for d in dates if not (LOCK_A <= d <= LOCK_B)})
    if not dates:
        ap.error("give --date, --since or --score")
    df = rows_for(dates, a.git_dir)
    upsert(df, dates)
    print(f"inverse shadow: {len(df)} rows for {len(dates)} date(s) -> {OUT}")


if __name__ == "__main__":
    main()
