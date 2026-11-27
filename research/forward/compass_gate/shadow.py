"""Compass Gate forward shadow (owner 2026-11-19 "Do want the shadow test"). Rule frozen 2026-11-19 - see RULE.md.

    python research/forward/compass_gate/shadow.py --date YYYY-MM-DD [--date ...]     # idempotent per date
    python research/forward/compass_gate/shadow.py --backfill                         # every session with Compass marks
    python research/forward/compass_gate/shadow.py --score                            # tally + pass-bar status

RESEARCH ONLY - never changes trading: reads the account journals (git show origin/<data branch>:journal.db), the
recorded Compass marks (origin/mcf-data-compass:compass/<date>.csv) and stored 1-minute day packs (GitHub Release
bars-<YYYY-MM>, public download, no Alpaca quota) to fill marks the live job missed, using the live card's own code
(mcf.report.compass_live.compute, point-in-time). No order, no config, no runner input. Optional --alpaca fills a
missing pack with read-only Alpaca market-data GETs (only after 16:15 ET; never during the live trade job).
Writes forward.csv (one row per closed live trade of every account, upsert by date) and days.csv (one row per session:
mark source, gate timeline). Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
OUT, DAYS = HERE / "forward.csv", HERE / "days.csv"
CACHE = Path(os.environ.get("COMPASS_GATE_CACHE", HERE / ".cache"))
GIT = os.environ.get("MCF_GIT_DIR", str(ROOT))           # repo whose origin/* data branches are read
TZ = "America/New_York"
FROZEN = "2026-11-19"
FIRST_MARK_DAY = "2026-11-06"                             # first session on mcf-data-compass
FORWARD_FROM = "2026-11-20"                               # pass bar counts sessions from here (RULE.md)
LOCK_A, LOCK_B = "2024-11-01", "2025-02-28"
LAG_MIN = 2                                               # mark T acts on entries at or after T + 2 min
CONFIRMED = {"UP-confirmed": 1, "DOWN-confirmed": -1}     # the W60 compass (the card's main reading)
BRANCHES = {"primary": "mcf-data", "testing": "mcf-data-testing", "testing2": "mcf-data-testing2",
            "gen": "mcf-data-gen", "graveyard": "mcf-data-graveyard", "livelab": "mcf-data-livelab",
            "explore1": "mcf-data-explore1", "testingd": "mcf-data-testingd", "testinge": "mcf-data-testinge",
            "testingf": "mcf-data-testingf"}

# ---- frozen instrument classes (RULE.md section 2). beta sign: +1 default (stocks, long ETFs incl. leveraged,
# sector / country / crypto ETPs), -1 inverse equity / crypto ETPs and long-volatility ETPs, 0 not equity-market.
INVERSE = frozenset("""
SH SDS SPXU SPXS SPDN PSQ QID SQQQ DOG DXD SDOW RWM TWM TZA SRTY SOXS TECS FAZ SKF SEF LABD ERY DUG DRIP DUST JDST GDXD
YANG FXP EDZ EEV EUM EFZ REK SRS SIJ SMDD MZZ SBB SSG FNGD BERZ WEBS HIBS SARK BTAL
AAPD AMZD MSFD PLTD PLTZ NVD NVDQ NVDS NVDD TSDD TSLQ TSLZ TSLS MSTZ AMDD DAMD MUD MUZ SNDQ BMNZ LITZ SKDD SKHZ AVS
AAOZ NBIZ IREZ SPCG SPCQ SSPC SMST SNK BEZ AXTQ CBRZ CONI
BITI SBIT ETHD
""".split())
LONG_VOL = frozenset("VXX UVXY VIXY UVIX VIXM VXZ".split())
NEUTRAL = frozenset("""
GLD GLDM IAU IAUM AAAU SGOL OUNZ PHYS BAR SLV SIVR PSLV PPLT PALL GLL ZSL AGQ UGL USO BNO UCO SCO USL UNG BOIL KOLD
DBC PDBC DBA DBMF KMLM CTA TLT TMF TMV TBT TBF EDV VGLT SPTL IEF SHY BIL SGOV TLH ZROZ GOVT BND AGG LQD HYG JNK UUP
UDN FXE FXY CPER CORN WEAT
""".split())
COLS = ["date", "account", "setup", "family", "trade_id", "symbol", "side", "inst_class", "exposure", "entry_et",
        "exit_et", "gate_side", "gate_since", "w60_at_entry", "blocked", "R", "check", "frozen"]
DCOLS = ["date", "marks", "recorded", "recomputed", "source_mismatch", "first_confirm", "timeline", "trades",
         "blocked", "blocked_R", "status", "frozen"]


def beta_sign(sym: str) -> int:
    s = str(sym).upper()
    return -1 if s in INVERSE or s in LONG_VOL else (0 if s in NEUTRAL else 1)


def inst_class(sym: str) -> str:
    s = str(sym).upper()
    return "inverse" if s in INVERSE else "long_vol" if s in LONG_VOL else "neutral" if s in NEUTRAL else "long_beta"


def family_of(setup: str) -> str:                       # = mcf.research.shadow_calib.family_of
    import re
    s = str(setup or "")
    return s.split("-", 1)[0] if "-" in s else re.sub(r"_[a-z]$", "", s)


def _git_show(ref: str) -> bytes | None:
    r = subprocess.run(["git", "-C", GIT, "show", ref], capture_output=True)
    return r.stdout if r.returncode == 0 else None


def _fetch_branches(names) -> None:
    for b in names:
        subprocess.run(["git", "-C", GIT, "fetch", "-q", "origin", f"+refs/heads/{b}:refs/remotes/origin/{b}"],
                       capture_output=True)


# ------------------------------------------------------------------------------------------------------- compass
def recorded_marks(day: str) -> dict[int, str]:
    raw = _git_show(f"origin/mcf-data-compass:compass/{day}.csv")
    if not raw:
        return {}
    rows = list(csv.DictReader(raw.decode().splitlines()))
    return {int(r["T"][:2]) * 60 + int(r["T"][3:]): r["w60"] for r in rows if r.get("T")}


def pack_bars(day: str, syms: list[str], alpaca: bool = False) -> dict[str, pd.DataFrame]:
    """symbol -> RTH 1-minute bars (ET index) from the stored day pack (downloaded once into .cache/packs)."""
    p = CACHE / "packs" / f"1min-{day}.parquet"
    if not p.exists():
        url = f"https://github.com/misiti15/MCF/releases/download/bars-{day[:7]}/1min-{day}.parquet"
        try:
            import requests
            r = requests.get(url, timeout=120)
            if r.status_code == 200 and len(r.content) > 1000:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(r.content)
        except Exception:
            pass
    if p.exists():
        x = pd.read_parquet(p, filters=[("symbol", "in", sorted(set(syms)))])
    elif alpaca:
        now = pd.Timestamp.now(tz=TZ)
        if str(now.date()) == day and now.hour * 60 + now.minute < 16 * 60 + 15:
            print(f"compass_gate: {day} no pack and before 16:15 ET - Alpaca quota is the live job's; not fetching")
            return {}
        from mcf.replay.store import _fetch_bars          # read-only market data
        x = _fetch_bars(syms, f"{day}T13:30:00Z", f"{day}T21:00:00Z", "1Min")
    else:
        return {}
    if not len(x):
        return {}
    ts = pd.DatetimeIndex(pd.to_datetime(x["ts"], utc=True)).tz_convert(TZ)
    x = x.drop(columns="ts").set_index(ts)
    out = {}
    for s, g in x.groupby("symbol"):
        g = g[(g.index.hour * 60 + g.index.minute >= 570) & (g.index.hour * 60 + g.index.minute < 960)]
        out[str(s)] = g[["open", "high", "low", "close", "volume"]].astype(float).sort_index()
    return out


def compass_marks(day: str, alpaca: bool = False) -> tuple[dict[int, str], dict]:
    """mark minute -> W60 reading for the whole session: recorded live rows first, missing marks recomputed with the
    live code on the stored pack. info: counts and recorded-vs-recomputed mismatches."""
    from mcf.report import compass_live as cl
    rec = recorded_marks(day)
    marks = dict(rec)
    info = {"recorded": len(rec), "recomputed": 0, "mismatch": 0, "checked": 0}
    names = cl.universe()
    bars = pack_bars(day, list(dict.fromkeys(["SPY", "QQQ", "IWM"] + names)), alpaca)
    if "SPY" in bars:
        rows = cl.compute(bars, day, pd.Timestamp(f"{day} 23:00", tz=TZ), names)
        for r in rows:
            T = int(r["T"][:2]) * 60 + int(r["T"][3:])
            if T in rec:
                info["checked"] += 1
                info["mismatch"] += int(rec[T] != r["w60"])
            else:
                marks[T] = r["w60"]
                info["recomputed"] += 1
    return dict(sorted(marks.items())), info


def gate_timeline(marks: dict[int, str]) -> list[tuple[int, int]]:
    """[(effective minute, side)] - the gate side switches at a confirmed reading on the other side (flip); it is
    set by the first confirmed reading of the session and never cleared by a leaning / mixed reading."""
    tl, side = [], 0
    for T, w in sorted(marks.items()):
        s = CONFIRMED.get(w, 0)
        if s and s != side:
            side = s
            tl.append((T + LAG_MIN, s))
    return tl


def side_at(tl: list[tuple[int, int]], minute: float) -> tuple[int, int | None]:
    side, since = 0, None
    for m, s in tl:
        if minute >= m:
            side, since = s, m
    return side, since


# ------------------------------------------------------------------------------------------------------- journals
def journal_trades(day: str, accounts=None) -> pd.DataFrame:
    out = []
    for acct, br in BRANCHES.items():
        if accounts and acct not in accounts:
            continue
        raw = _git_show(f"origin/{br}:journal.db")
        if not raw:
            continue
        f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        try:  # write inside the try: a failed write (ENOSPC) must not leak the partial file
            with f:
                f.write(raw)
            c = sqlite3.connect(f.name)
            t = pd.read_sql("SELECT t.id, t.symbol, t.strategy, t.side, t.entry_time, t.exit_time, t.entry, t.stop, "
                            "t.shares, t.pnl, t.pnl_adj FROM trades t JOIN runs r ON r.id = t.run_id "
                            "WHERE r.kind NOT IN ('whatif', 'shadow') AND t.date = ?", c, params=(day,))
            c.close()
        finally:
            os.unlink(f.name)
        t["account"] = acct
        out.append(t)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def _et(ts) -> pd.Timestamp | None:
    if ts is None or (isinstance(ts, float) and np.isnan(ts)):
        return None
    t = pd.Timestamp(ts)
    t = t.tz_localize("UTC") if t.tzinfo is None else t
    return t.tz_convert(TZ)


# ------------------------------------------------------------------------------------------------------- run
def run(day: str, alpaca: bool = False, fetch: bool = True) -> dict:
    if LOCK_A <= day <= LOCK_B:
        raise SystemExit("locked block - never read")
    if fetch:
        _fetch_branches(["mcf-data-compass", *BRANCHES.values()])
    from mcf.report.compass_live import MARKS
    marks, info = compass_marks(day, alpaca)
    complete = len(marks) >= len(MARKS)              # all 25 marks 09:45 .. 15:45
    tl = gate_timeline(marks)
    tr = journal_trades(day)
    rows = []
    for _, t in tr.iterrows():
        ent, ex = _et(t.entry_time), _et(t.exit_time)
        if ent is None:
            continue
        risk = abs(float(t.entry) - float(t.stop)) * float(t.shares or 0)
        pnl = t.pnl_adj if pd.notna(t.pnl_adj) else t.pnl
        R = float(pnl) / risk if (ex is not None and pd.notna(pnl) and risk > 0) else np.nan
        minute = ent.hour * 60 + ent.minute + ent.second / 60
        side, since = side_at(tl, minute)
        exp = int(np.sign(t.side)) * beta_sign(t.symbol)
        blocked = int(complete and side != 0 and exp == -side)
        last = [w for T, w in marks.items() if T + LAG_MIN <= minute]
        rows.append(dict(date=day, account=t.account, setup=t.strategy, family=family_of(t.strategy),
                         trade_id=int(t.id), symbol=t.symbol, side=int(t.side), inst_class=inst_class(t.symbol),
                         exposure=exp, entry_et=f"{ent:%H:%M:%S}", exit_et=f"{ex:%H:%M:%S}" if ex is not None else "",
                         gate_side={1: "UP", -1: "DOWN", 0: ""}[side],
                         gate_since=f"{since // 60:02d}:{since % 60:02d}" if since else "",
                         w60_at_entry=last[-1] if last else "", blocked=blocked if complete else "",
                         R=round(R, 4) if np.isfinite(R) else "", check="" if complete else "marks incomplete",
                         frozen=FROZEN))
    status = "done" if complete and len(tr) else ("pending: Compass marks incomplete" if not complete else "no trades")
    if complete and len(tr) and tr.exit_time.isna().any():
        status = "partial: open trades (R blank)"
    upsert(OUT, COLS, rows, day)
    b = [r for r in rows if r["blocked"] == 1]
    first = next((f"{T // 60:02d}:{T % 60:02d} {w}" for T, w in marks.items() if w in CONFIRMED), "")
    drow = dict(date=day, marks=len(marks), recorded=info["recorded"], recomputed=info["recomputed"],
                source_mismatch=f"{info['mismatch']}/{info['checked']}", first_confirm=first,
                timeline=" ".join(f"{m // 60:02d}:{m % 60:02d}>{'UP' if s > 0 else 'DOWN'}" for m, s in tl),
                trades=len(rows), blocked=len(b), blocked_R=round(sum(r["R"] for r in b if r["R"] != ""), 3),
                status=status, frozen=FROZEN)
    upsert(DAYS, DCOLS, [drow], day)
    return drow


def upsert(path: Path, cols: list[str], rows: list[dict], day: str) -> None:
    old = []
    if path.exists():
        with open(path, newline="") as f:
            old = [r for r in csv.DictReader(f) if r["date"] != day]
    allr = old + [{k: r.get(k, "") for k in cols} for r in rows]
    allr.sort(key=lambda r: (r["date"], r.get("account", ""), r.get("entry_et", ""), str(r.get("trade_id", ""))))
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(allr)


def sessions_with_marks() -> list[str]:
    _fetch_branches(["mcf-data-compass"])
    r = subprocess.run(["git", "-C", GIT, "ls-tree", "--name-only", "origin/mcf-data-compass", "compass/"],
                       capture_output=True, text=True).stdout.split()
    return sorted(Path(p).stem for p in r if Path(p).stem[:4].isdigit())


# ------------------------------------------------------------------------------------------------------- score
def tstat(x) -> float:
    x = np.asarray(x, float)
    return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 1 and x.std(ddof=1) > 0 else float("nan")


def score(start: str = FORWARD_FROM, end: str = "9999") -> dict:
    f = pd.read_csv(OUT)
    d = pd.read_csv(DAYS)
    f = f[(f.date >= start) & (f.date <= end) & f.blocked.isin([0, 1, "0", "1"]) & f.R.notna()].copy()
    f["blocked"] = f.blocked.astype(int)
    f["R"] = f.R.astype(float)
    days = d[(d.date >= start) & (d.date <= end) & d.status.str.startswith("done")]
    b = f[f.blocked == 1]
    per_day = b.groupby("date").R.sum()
    best = per_day.idxmin() if len(per_day) else None              # the session where blocking saved the most
    saved = -per_day.sum()
    fam = b.groupby("family").R.agg(["count", "sum"])
    setup = b.groupby(["account", "setup"]).R.agg(["count", "sum"])
    prim = f[f.account == "primary"]
    out = dict(window=f"{start}..{end}", sessions=int(len(days)), sessions_with_confirm=int(
        (days.first_confirm.fillna("") != "").sum()), trades=int(len(f)), blocked=int(len(b)),
        blocked_avg_R=round(float(b.R.mean()), 3) if len(b) else None, blocked_t=round(tstat(b.R), 2) if len(b) > 1 else None,
        blocked_t_session=round(tstat(per_day), 2) if len(per_day) > 1 else None,
        blocked_sum_R=round(float(b.R.sum()), 2), ungated_R=round(float(f.R.sum()), 2),
        gated_R=round(float(f[f.blocked == 0].R.sum()), 2),
        primary_ungated_R=round(float(prim.R.sum()), 2), primary_gated_R=round(float(prim[prim.blocked == 0].R.sum()), 2),
        primary_blocked=int(prim.blocked.sum()),
        best_day=best, best_day_share=round(float(-per_day.min() / saved), 2) if saved > 0 else None,
        blocked_avg_R_wo_best_day=round(float(b[b.date != best].R.mean()), 3) if best and len(b[b.date != best]) else None,
        families_better=int((fam["sum"] < 0).sum()), families_worse=int((fam["sum"] > 0).sum()),
        family_worse_R=round(float(fam["sum"][fam["sum"] > 0].sum()), 2),
        family_better_R=round(float(-fam["sum"][fam["sum"] < 0].sum()), 2),
        setups_better=int((setup["sum"] < 0).sum()), setups_worse=int((setup["sum"] > 0).sum()),
        by_family={k: [int(v["count"]), round(float(v["sum"]), 2)] for k, v in fam.iterrows()},
        by_account={k: [int((g.blocked == 1).sum()), round(float(g[g.blocked == 1].R.sum()), 2)]
                    for k, g in f.groupby("account")})
    # pass bar (RULE.md section 5) - evaluated only once the sample bar is met
    ready = out["sessions"] >= 15 and (out["blocked"] >= 40 or out["sessions"] >= 40)
    checks = dict(
        blocked_avg_neg=bool(len(b) and b.R.mean() < 0),
        blocked_t=bool(len(b) > 1 and tstat(b.R) <= -1.5),
        blocked_t_session=bool(len(per_day) > 1 and tstat(per_day) <= -1.5),
        gated_beats_ungated_all=out["gated_R"] > out["ungated_R"],
        gated_beats_ungated_primary=out["primary_gated_R"] > out["primary_ungated_R"],
        one_big_day=bool(out["best_day_share"] is not None and out["best_day_share"] < 0.5
                         and (out["blocked_avg_R_wo_best_day"] or 0) < 0),
        families=bool(out["families_better"] > out["families_worse"]
                      and out["family_worse_R"] <= out["family_better_R"] / 3))
    out["pass_checks"] = checks
    out["verdict"] = ("PASS - write up as a DECISION for the owner" if all(checks.values()) else "FAIL - retire") \
        if ready else f"not scored yet (needs >= 15 sessions and >= 40 blocked trades, or 40 sessions)"
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", action="append", default=[])
    ap.add_argument("--backfill", action="store_true", help="every session since the Compass marks exist")
    ap.add_argument("--alpaca", action="store_true", help="fill a missing day pack from Alpaca (after 16:15 ET only)")
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--start", default=FORWARD_FROM)
    a = ap.parse_args()
    days = list(a.date)
    if a.backfill:
        days = sorted(set(days) | set(sessions_with_marks()))
    for i, d in enumerate(days):
        print(json.dumps(run(d, a.alpaca, fetch=(i == 0))))
    if a.score:
        print(json.dumps(score(a.start), indent=1))
