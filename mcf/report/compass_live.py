"""Market Compass (live): the research compass recorded during the day (owner "Compass live: yes", 2026-11-09).

    python -m mcf.report.compass_live --date 2026-11-09            # compute the 15-min marks so far into data/compass/local
    python -m mcf.report.compass_live --date 2026-11-09 --push     # ... on the mcf-data-compass data branch (dashboard card)

DISPLAY / RESEARCH ONLY - NOT A TRADING SIGNAL. It reads no trading config, writes no config, places no orders and feeds
nothing to the runner. Read-only Alpaca MARKET DATA GETs (1-minute SIP bars; mcf.replay.store._fetch_bars), nothing else.

Every 15 minutes from 09:45 ET (marks 09:45 .. 15:45), point-in-time only (bars that START before the mark, i.e. closed
by it), it records:
  * SPY / QQQ / IWM % from the open (first 1-minute bar's open), SPY vs its session VWAP;
  * breadth_open = share of the 200 Hunch names (research/hunch/universe200.txt, as the COMP15 live day 11-05) above
    their open; 0.5 at 09:45 (no breadth row at 09:45, GATE1 / COMP15 convention);
  * the W60 15-min rolling compass (research/bdi/hc1/comp15.py, forward shadow `comp15-w60-early`): votes = SPY fo sign,
    VWAP side, breadth side, SPY/QQQ/IWM agreement, + persistence (fo sign the same at every 15-min mark of the last 60
    min); confirmed = |votes| >= 4 with that persistence and >= 2 marks; 09:45 = low confidence (1 mark);
  * the 30-min GATE1 compass (research/bdi/gate1/compass.py / comp15.py C30: checkpoints 09:45 (persistence input only),
    10:00, 10:30, ... 15:30; votes = fo sign, VWAP side, persist2, breadth side, agreement; confirmed = |v| >= 4 with
    persist3), held between its checkpoints;
  * the 30-min checkpoint state (from 10:30): UP / DOWN when SPY is >= 0.30% from its open on that side at the latest
    30-min checkpoint ("strong move": holds its side of the open to the close 89% / 89% / 97% TRAIN / VALID / LIVE,
    research/bdi/gate1/NOTES.md), else UNCONFIRMED;
  * the GATE1 state (UP / DOWN / MIXED, forward shadow `gate1-checkpoint-gate`) at the latest 30-min checkpoint.
Research evidence: "staying" (SPY closes on the same side of its open) is readable; "heading" (where it goes from here)
is a coin flip on every clock. So the card shows where the day stands, not where it goes.

Output: compass/<date>.csv (one row per mark, appended; a mark computed more than 10 minutes late is tagged
backfilled) and compass/latest.json. Idempotent: rerunning computes only the missing marks (catch-up after a missed
cron run); the hourly BDI monitor can run the same command to backfill. Educational only — not financial advice.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
NY = "America/New_York"
BRANCH = "mcf-data-compass"
RAW_URL = f"https://raw.githubusercontent.com/misiti15/MCF/{BRANCH}/compass/latest.json"
WORK = ROOT / "data" / "compass"
UNIVERSE = ROOT / "research" / "hunch" / "universe200.txt"
DISCLAIMER = "Educational only — not financial advice."
LABEL = "Display only — not a trading signal"
MARKS = list(range(585, 946, 15))                 # 09:45 .. 15:45, minutes since midnight ET
CPS = [585] + list(range(600, 931, 30))          # 30-min GATE1 clock: 09:45 (persistence input only), 10:00 .. 15:30
STRONG = 0.003                                    # 30-min checkpoint state: |SPY from open| >= 0.30%
NAMES = {2: "UP-confirmed", 1: "leaning up", 0: "mixed", -1: "leaning down", -2: "DOWN-confirmed"}
COLS = ["date", "T", "spy_fo", "qqq_fo", "iwm_fo", "spy_vwap", "breadth_open", "breadth_n", "v_fo", "v_vwap",
        "v_breadth", "v_agree", "v_persist", "votes", "w60", "w60_low_conf", "agreement", "c30", "c30_at", "checkpoint",
        "checkpoint_at", "gate1_state", "computed_at", "backfilled"]

lab = lambda T: f"{T // 60:02d}:{T % 60:02d}"
sg = lambda x: 0 if x is None or not np.isfinite(x) else int(np.sign(x))


def universe() -> list[str]:
    return [ln.split()[0] for ln in UNIVERSE.read_text().splitlines() if ln.strip() and not ln.startswith("#")]


# ------------------------------------------------------------------------------------------------------------- compute
def snap(b: pd.DataFrame | None, T: int) -> dict | None:
    """fo / vwap / last close of one symbol from the bars that start before minute T (closed by T). None = no bar yet."""
    if b is None or not len(b):
        return None
    m = b.index.hour * 60 + b.index.minute
    x = b[(m >= 570) & (m < T)]
    if not len(x):
        return None
    o = float(b.open.iloc[0])
    c = x.close.values.astype(float)
    tp = ((x.high + x.low + x.close) / 3).values.astype(float)
    v = x.volume.values.astype(float)
    vw = (tp * v).sum() / v.sum() if v.sum() > 0 else np.nan
    return dict(fo=c[-1] / o - 1, vw=c[-1] / vw - 1 if np.isfinite(vw) else np.nan)


def breadth(bars: dict, names: list[str], T: int) -> tuple[float, int]:
    if T == 585:
        return 0.5, 0                              # no breadth row at 09:45 (GATE1 / COMP15 convention)
    up = [s["fo"] > 0 for s in (snap(bars.get(n), T) for n in names) if s is not None]
    return (float(np.mean(up)) if up else np.nan), len(up)


def base_votes(spy: dict, qqq: dict | None, iwm: dict | None, bo: float) -> dict:
    s = sg(spy["fo"])
    agree = s if (qqq and iwm and sg(qqq["fo"]) == s and sg(iwm["fo"]) == s) else 0
    bside = 1 if bo > 0.5 else (-1 if bo < 0.5 else 0) if np.isfinite(bo) else 0
    return dict(v_fo=s, v_vwap=sg(spy["vw"]), v_breadth=bside, v_agree=agree)


def level(v: int, p: int, ok: bool = True) -> int:
    """5-level compass from votes v and persistence p (research rule): confirmed needs |v| >= 4 AND persistence."""
    if v >= 4 and p == 1 and ok:
        return 2
    if v >= 2:
        return 1
    if v <= -4 and p == -1 and ok:
        return -2
    if v <= -2:
        return -1
    return 0


def compute(bars: dict, day: str, now: pd.Timestamp, names: list[str] | None = None, skip=()) -> list[dict]:
    """Rows for every 15-min mark that is closed by `now` (mark + 1 min) and not in `skip`. Pure: point-in-time only."""
    names = universe() if names is None else names
    now = pd.Timestamp(now)
    now = now.tz_localize(NY) if now.tzinfo is None else now.tz_convert(NY)
    t_now = now.hour * 60 + now.minute if str(now.date()) == day else (9999 if str(now.date()) > day else -1)
    st: dict[int, dict] = {}                       # mark -> SPY state (cached for persistence look-backs)

    def state(T):
        if T not in st:
            spy = snap(bars.get("SPY"), T)
            if spy is None:
                st[T] = None
            else:
                q, w = snap(bars.get("QQQ"), T), snap(bars.get("IWM"), T)
                bo, bn = breadth(bars, names, T)
                st[T] = dict(spy=spy, qqq=q, iwm=w, bo=bo, bn=bn, **base_votes(spy, q, w, bo))
        return st[T]

    def c30_at(cp):                                # GATE1 30-min compass at a checkpoint >= 10:00
        i = CPS.index(cp)
        x = [state(c) for c in CPS[max(0, i - 2):i + 1]]
        if any(y is None for y in x):
            return None
        s = [y["v_fo"] for y in x]
        p2 = s[-1] if len(s) >= 2 and s[-1] == s[-2] else 0
        p3 = s[-1] if len(s) >= 3 and s[-1] == s[-2] == s[-3] else 0
        y = x[-1]
        v = y["v_fo"] + y["v_vwap"] + y["v_breadth"] + y["v_agree"] + p2
        return level(v, p3)

    def gate1(cp):
        y = state(cp)
        if y is None:
            return ""
        fo, vw, bo = y["spy"]["fo"], y["spy"]["vw"], y["bo"]
        q = (y["qqq"] or {}).get("fo", np.nan); w = (y["iwm"] or {}).get("fo", np.nan)
        if fo >= 0.0015 and vw > 0 and bo >= 0.5 and (q > 0 or w > 0):
            return "UP"
        if fo <= -0.0015 and vw < 0 and bo <= 0.5 and (q < 0 or w < 0):
            return "DOWN"
        return "MIXED"

    rows = []
    for T in MARKS:
        if T in skip or t_now < T + 1:
            continue
        y = state(T)
        if y is None:
            continue
        marks = [t for t in MARKS if T - 60 < t <= T]
        ss = [state(t)["v_fo"] if state(t) else 0 for t in marks]
        pw = ss[-1] if ss[-1] != 0 and all(s == ss[-1] for s in ss) else 0
        votes = y["v_fo"] + y["v_vwap"] + y["v_breadth"] + y["v_agree"] + pw
        w60 = level(votes, pw, len(marks) >= 2)
        cp = max([c for c in CPS if 600 <= c <= T], default=None)
        c30 = c30_at(cp) if cp else None
        kcp = max([c for c in CPS if 630 <= c <= T], default=None)
        chk = ""
        if kcp:
            f = state(kcp)["spy"]["fo"]
            chk = "UP" if f >= STRONG else ("DOWN" if f <= -STRONG else "UNCONFIRMED")
        sq, sw = y["qqq"], y["iwm"]
        signs = [sg(y["spy"]["fo"]), sg(sq["fo"]) if sq else 0, sg(sw["fo"]) if sw else 0]
        agreement = "all up" if all(s > 0 for s in signs) else ("all down" if all(s < 0 for s in signs) else "mixed")
        r4 = lambda v: None if v is None or not np.isfinite(v) else round(float(v), 5)
        rows.append(dict(
            date=day, T=lab(T), spy_fo=r4(y["spy"]["fo"]), qqq_fo=r4(sq["fo"]) if sq else None,
            iwm_fo=r4(sw["fo"]) if sw else None, spy_vwap=r4(y["spy"]["vw"]), breadth_open=r4(y["bo"]), breadth_n=y["bn"],
            v_fo=y["v_fo"], v_vwap=y["v_vwap"], v_breadth=y["v_breadth"], v_agree=y["v_agree"], v_persist=pw,
            votes=votes, w60=NAMES[w60], w60_low_conf=int(T == 585), agreement=agreement,
            c30=NAMES[c30] if c30 is not None else "", c30_at=lab(cp) if cp else "", checkpoint=chk,
            checkpoint_at=lab(kcp) if kcp else "", gate1_state=gate1(cp) if cp else "",
            computed_at=f"{now:%Y-%m-%d %H:%M}", backfilled=int(t_now > T + 10)))
    return rows


# ------------------------------------------------------------------------------------------------------------- data
def fetch(day: str, syms: list[str], now: pd.Timestamp, log=print) -> dict[str, pd.DataFrame]:
    """symbol -> 1-minute RTH SIP bars of `day` that started before min(now, 16:00) ET (read-only market data GET)."""
    from ..replay import store

    end = min(pd.Timestamp(now).tz_convert(NY), pd.Timestamp(f"{day} 16:00", tz=NY))
    start = pd.Timestamp(f"{day} 09:30", tz=NY)
    if end <= start:
        return {}
    log(f"compass: fetching 1-minute bars for {len(syms)} symbols, {day} 09:30 -> {end:%H:%M} ET")
    df = store._fetch_bars(list(syms), start.tz_convert("UTC").isoformat(), end.tz_convert("UTC").isoformat(), "1Min")
    out = {}
    if not len(df):
        return out
    df = df.set_index("ts")
    df.index = df.index.tz_convert(NY)
    df = df[(df.index >= start) & (df.index < end)]
    for s, g in df.groupby("symbol"):
        out[str(s)] = g[["open", "high", "low", "close", "volume"]].astype(float).sort_index()
    return out


# ------------------------------------------------------------------------------------------------------------- files
def read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open() as f:
        return list(csv.DictReader(f))


def _typed(r: dict) -> dict:
    """CSV strings back to numbers (latest.json carries numbers; '' -> None)."""
    out = {}
    for k, v in r.items():
        if isinstance(v, str) and k not in ("date", "T", "computed_at", "c30_at", "checkpoint_at"):
            if v == "":
                v = None
            else:
                try:
                    v = int(v) if v.lstrip("-").isdigit() else float(v)
                except ValueError:
                    pass
        out[k] = v
    return out


def latest(day: str, rows: list[dict], now: pd.Timestamp) -> dict:
    rows = [_typed(r) for r in rows]
    tl = [{k: r.get(k) for k in ("T", "spy_fo", "qqq_fo", "iwm_fo", "agreement", "breadth_open", "votes", "w60",
                                 "w60_low_conf", "c30", "checkpoint", "gate1_state", "backfilled")} for r in rows]
    last = rows[-1] if rows else {}
    t = now.hour * 60 + now.minute
    phase = "pre-open" if not rows else ("closed" if str(now.date()) > day or t >= 960 else "intraday")
    return dict(date=day, asof=last.get("T"), phase=phase, computed_at=f"{now:%Y-%m-%d %H:%M} ET", latest=last,
                timeline=tl, label=LABEL, disclaimer=DISCLAIMER,
                method="research/bdi/gate1/NOTES.md (30-min compass, checkpoint = SPY >= 0.30% from open), "
                       "research/bdi/hc1/NOTES.md (W60 15-min compass); mcf/report/compass_live.py")


def update(out: Path, day: str, now: pd.Timestamp, bars_fn=fetch, names: list[str] | None = None, log=print) -> int:
    """Append the missing marks of `day` to out/compass/<day>.csv and rewrite out/compass/latest.json. Returns rows added."""
    path = out / "compass" / f"{day}.csv"
    have = read_rows(path)
    done = {int(r["T"][:2]) * 60 + int(r["T"][3:]) for r in have}
    names = universe() if names is None else names
    t_now = now.hour * 60 + now.minute if str(now.date()) == day else 9999
    due = [T for T in MARKS if T not in done and t_now >= T + 1]
    new = []
    if due:
        bars = bars_fn(day, list(dict.fromkeys(["SPY", "QQQ", "IWM"] + names)), now, log=log)
        if "SPY" not in bars:
            log(f"compass: no SPY bars for {day} (holiday / before the open?) - nothing written")
            return 0
        new = compute(bars, day, now, names, skip=done)
    if not have and not new:
        log(f"compass: {day} no mark closed yet (first at 09:46 ET) - nothing written")
        return 0
    rows = have + [{k: ("" if r[k] is None else r[k]) for k in COLS} for r in new]
    rows.sort(key=lambda r: r["T"])
    path.parent.mkdir(parents=True, exist_ok=True)
    if new or not path.exists():
        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLS)
            w.writeheader()
            w.writerows(rows)
    lj = out / "compass" / "latest.json"
    prev = json.loads(lj.read_text()) if lj.exists() else {}
    if new or prev.get("date") != day or not lj.exists():
        lj.write_text(json.dumps(latest(day, rows, now), indent=1))
    log(f"compass: {day} +{len(new)} marks ({len(rows)} total)" + (f", latest {rows[-1]['T']} W60 {rows[-1]['w60']}, "
        f"checkpoint {rows[-1]['checkpoint'] or '-'}" if rows else ""))
    return len(new)


# ------------------------------------------------------------------------------------------------------------- branch
def _g(wd: Path, *a, log=print) -> bool:
    r = subprocess.run(["git", "-C", str(wd), *a], capture_output=True, text=True)
    if r.returncode:
        err = re.sub(r"//[^@/\s]+@", "//***@", r.stderr.strip())     # never log a token
        log(f"git {' '.join(a[:2])}: {err[:200]}")
    return r.returncode == 0


def open_branch(wd: Path, log=print) -> bool:
    """Check out the mcf-data-compass data branch in `wd` (created as an orphan branch when it does not exist yet)."""
    if not (wd / ".git").exists():
        url = subprocess.run(["git", "-C", str(ROOT), "remote", "get-url", "origin"], capture_output=True, text=True).stdout
        if not url.strip():
            log("push: no origin remote")
            return False
        wd.mkdir(parents=True, exist_ok=True)
        _g(wd, "init", "-q", log=log)
        _g(wd, "remote", "add", "origin", url.strip(), log=log)
    if _g(wd, "fetch", "-q", "--depth", "1", "origin", BRANCH, log=lambda *_: None):
        _g(wd, "checkout", "-q", "-f", "-B", BRANCH, f"origin/{BRANCH}", log=log)
    elif not _g(wd, "rev-parse", "-q", "--verify", "HEAD", log=lambda *_: None):
        _g(wd, "checkout", "-q", "--orphan", BRANCH, log=log)
    readme = wd / "README.md"
    if not readme.exists():
        readme.write_text("# mcf-data-compass\n\nMarket Compass (live): compass/<date>.csv (one row per 15-min mark) and "
                          "compass/latest.json, written by `python -m mcf.report.compass_live --date D --push` "
                          "(.github/workflows/compass.yml). See mcf/report/compass_live.py on the main branch. "
                          f"{LABEL}. {DISCLAIMER}\n")
    return True


def push(wd: Path, msg: str, log=print) -> bool:
    _g(wd, "add", "-A", log=log)
    if subprocess.run(["git", "-C", str(wd), "diff", "--cached", "--quiet"]).returncode == 0:
        log("push: nothing new")
        return True
    ident = ["-c", "user.name=mcf-bot", "-c", "user.email=mcf-bot@users.noreply.github.com"]
    _g(wd, *ident, "commit", "-q", "-m", msg, log=log)
    for _ in range(3):
        if _g(wd, "push", "-q", "origin", f"HEAD:{BRANCH}", log=log):
            log(f"push: {BRANCH} -> {RAW_URL}")
            return True
        _g(wd, *ident, "pull", "-q", "--rebase", "origin", BRANCH, log=log) or _g(wd, "rebase", "--abort", log=log)
    return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Market Compass (live) - display only, not a trading signal")
    ap.add_argument("--date", default=None, help="session date (default: today ET)")
    ap.add_argument("--now", default=None, help="pretend clock (ET), e.g. '2026-11-06 11:31' (tests / replays)")
    ap.add_argument("--push", action="store_true", help=f"record on the {BRANCH} data branch (dashboard card)")
    ap.add_argument("--state-dir", default=None, help="data-branch checkout (default data/compass/branch)")
    a = ap.parse_args(argv)
    now = pd.Timestamp(a.now, tz=NY) if a.now else pd.Timestamp.now(tz=NY)
    day = a.date or str(now.date())
    if pd.Timestamp(day).dayofweek >= 5:
        print(f"compass: {day} is a weekend - nothing to do")
        return 0
    if a.push:
        wd = Path(a.state_dir) if a.state_dir else WORK / "branch"
        if not open_branch(wd):
            return 1
        n = update(wd, day, now)
        return 0 if push(wd, f"compass {day} {now:%H:%M} ET (+{n})") else 1
    update(Path(a.state_dir) if a.state_dir else WORK / "local", day, now)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
