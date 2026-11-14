"""Nightly FAMC calendar builder (Observer, Lead lead-20261110-1900-2). HYBRID classifier, frozen in fulldenom.py look 3
(precision 0.887 / recall 0.756 on 7 evenings, full lab denominator):
  name X reported AFTER THE CLOSE on D  <=>  (a) an Alpaca news item created D 16:00-19:59 ET whose ONLY symbol is X, headline matches EARN
  and not PREVIEW, (b) X had no such earnings headline D 04:00-15:59 ET (first earnings news of the day), and (c) X is listed with report
  date D in the live job's PRE-OPEN snapshot mcf-data/earnings/<D>.json.
Skeptic's checks (skeptic-20261110-1855-1): asserts the snapshot was written by a pre-open job of D and never changed after (see snapshot();
a git commit time cannot be pre-open because the live job commits state at day end); snapshot_at = the news
query time; a label-free health line each night (share of earlier flags whose reaction-session |gap| > 2x the name's normal).
Appends to research/evd1/famc_calendar.csv (symbol,report_date,timing,source,snapshot_at); re-running a date replaces its rows.
Read-only GETs (Alpaca news + daily bars); refuses before 20:00 ET on D (evening news incomplete) and 07:30-16:00 ET on weekdays.
usage (from the MCF checkout): python ../guild/research/obs-amcnews/build_famc_cal.py [--date YYYY-MM-DD]. Educational only - not financial advice."""
import argparse, json, os, re, subprocess, sys, time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd, requests
ET = ZoneInfo("America/New_York"); G = Path(__file__).resolve().parents[2]
CAL = Path(os.environ.get("FAMC_CAL", G / "research/evd1/famc_calendar.csv")); HEALTH = Path(os.environ.get("FAMC_HEALTH", G / "research/obs-amcnews/famc_cal_health.csv"))
EARN = re.compile(r"\b(earnings|results|quarter|Q[1-4]|revenue|EPS|guidance|beats?|miss(es)?|reports?|reported|profit|sales)\b", re.I)
PREVIEW = re.compile(r"\b(to report|will report|ahead of|preview|expected to|expects to|scheduled|set to|on deck|what to expect|earnings date|to announce|will announce|conference call|webcast|upcoming|week ahead|next week|this week)\b", re.I)
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
def news(D, h0, h1):
    a = datetime.fromisoformat(D).replace(hour=h0, tzinfo=ET); b = a.replace(hour=h1, minute=59, second=59)
    p = {"start": a.isoformat(), "end": b.isoformat(), "limit": 50, "sort": "asc"}; out = []
    while True:
        r = requests.get("https://data.alpaca.markets/v1beta1/news", headers=H, params=p, timeout=30)
        if r.status_code == 429: time.sleep(3); continue
        r.raise_for_status(); j = r.json(); out += j.get("news", []); time.sleep(0.3)
        if not j.get("next_page_token"): return out
        p["page_token"] = j["next_page_token"]
def snapshot(D):
    """live pre-open snapshot. Skeptic check 1, as amended 2026-11-10 (Observer): the live job builds earnings/<D>.json at its pre-open
    start (mcf/data/earnings.py blackout(), cached in state/) but COMMITS state to mcf-data only at day end (e.g. 11-10: 'job 08:56 done',
    committed 14:37 ET), so a git commit time can never be pre-open. Assert instead: exactly ONE commit ever touched the file (unchanged
    since written), and that commit is the job whose start time in its subject ('job HH:MM done D') is before 09:30 ET on D."""
    subprocess.run(["git", "fetch", "-q", "--depth=5000", "origin", "mcf-data"], check=True)
    body = subprocess.run(["git", "show", f"FETCH_HEAD:earnings/{D}.json"], check=True, capture_output=True, text=True).stdout
    log = subprocess.run(["git", "log", "FETCH_HEAD", "--format=%cI|%s", "--", f"earnings/{D}.json"], check=True, capture_output=True, text=True).stdout.strip().splitlines()
    assert len(log) == 1, f"earnings/{D}.json touched by {len(log)} commits - not provably the pre-open version: {log}"
    m = re.search(r"job (\d\d):(\d\d) done (\d{4}-\d\d-\d\d)", log[0].split("|", 1)[1])
    assert m and m.group(3) == D and int(m.group(1)) * 60 + int(m.group(2)) < 570, f"snapshot commit is not a pre-open job of {D}: {log[0]}"
    first = pd.Timestamp(f"{D} {m.group(1)}:{m.group(2)}", tz=ET)
    j = json.loads(body)
    # Skeptic skeptic-20261110-2050-1: if Nasdaq failed, blackout() falls back to Alpaca news (complete=false, PAST dates only), so names
    # reporting on D would be missing. Then the day is UNBUILDABLE, not empty.
    if j.get("source") != "nasdaq" or j.get("complete") is not True:
        sys.exit(f"UNBUILDABLE {D}: earnings/{D}.json source={j.get('source')} complete={j.get('complete')} (needs nasdaq + complete)")
    s = j["symbols"]; return {k for k, v in s.items() if D in v}, first
def daily(syms, start, end):
    out = {}
    for i in range(0, len(syms), 100):
        p = {"symbols": ",".join(syms[i:i + 100]), "timeframe": "1Day", "start": start, "end": end, "feed": "sip", "adjustment": "split", "limit": 10000}
        while True:
            r = requests.get("https://data.alpaca.markets/v2/stocks/bars", headers=H, params=p, timeout=30)
            if r.status_code == 429: time.sleep(3); continue
            r.raise_for_status(); j = r.json()
            for s, bs in (j.get("bars") or {}).items(): out.setdefault(s, []).extend(bs)
            if not j.get("next_page_token"): break
            p["page_token"] = j["next_page_token"]
        time.sleep(0.3)
    return {s: pd.DataFrame(b).assign(d=lambda x: pd.to_datetime(x.t).dt.tz_convert(ET).dt.strftime("%Y-%m-%d")).set_index("d") for s, b in out.items()}
def health(cal):
    """label-free check on every earlier report date whose reaction session has closed: share of flags with |gap| > 2x normal."""
    done = cal[pd.to_datetime(cal.report_date) + pd.offsets.BDay(1) <= pd.Timestamp(datetime.now(ET).date())]
    if done.empty: return None
    end = (datetime.now(ET).date() + timedelta(days=1)).isoformat(); start = (pd.Timestamp(done.report_date.min()) - pd.Timedelta(days=45)).strftime("%Y-%m-%d")
    B = daily(sorted(done.symbol.unique()), start, end); rows = []
    for _, r in done.iterrows():
        b = B.get(r.symbol); R = (pd.Timestamp(r.report_date) + pd.offsets.BDay(1)).strftime("%Y-%m-%d")
        if b is None or R not in b.index: continue
        b = b.sort_index(); gap = (b.o / b.c.shift(1) - 1).abs(); i = b.index.get_loc(R)
        norm = gap.iloc[max(0, i - 21):i - 1].median()
        rows.append(dict(report_date=r.report_date, symbol=r.symbol, reaction=R, gap=gap.iloc[i], normal=norm, ratio=gap.iloc[i] / norm if norm > 0 else np.nan))
    return pd.DataFrame(rows)
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--date", default=datetime.now(ET).strftime("%Y-%m-%d")); a = ap.parse_args(); D = a.date
    now = datetime.now(ET)
    if now.weekday() < 5 and 450 <= now.hour * 60 + now.minute < 960: sys.exit("refusing: 07:30-16:00 ET")
    if now < datetime.fromisoformat(D).replace(hour=20, tzinfo=ET): sys.exit(f"refusing: evening news for {D} is complete only after 20:00 ET")
    lab = set((Path("research/lab_symbols.txt")).read_text().split())
    listed, first = snapshot(D); q_at = datetime.now(ET)
    ev, am = news(D, 16, 19), news(D, 4, 15)
    morning = {(x.get("symbols") or [None])[0] for x in am if EARN.search(x.get("headline", "") or "") and not PREVIEW.search(x.get("headline", "") or "")}
    flags = sorted({x["symbols"][0] for x in ev if len(x.get("symbols") or []) == 1 and EARN.search(x.get("headline", "") or "")
                    and not PREVIEW.search(x.get("headline", "") or "") and x["symbols"][0] in lab and x["symbols"][0] not in morning and x["symbols"][0] in listed})
    cal = pd.read_csv(CAL); cal = cal[cal.report_date.astype(str) != D]
    new = pd.DataFrame(dict(symbol=flags, report_date=D, timing="amc", source="alpaca-news+live-snapshot(hybrid)", snapshot_at=q_at.isoformat(timespec="seconds")))
    cal = pd.concat([cal, new], ignore_index=True).sort_values(["report_date", "symbol"]); cal.to_csv(CAL, index=False)
    print(f"{D}: evening items {len(ev)}, morning items {len(am)}, live snapshot listed {len(listed)} (written by the pre-open job of {first:%Y-%m-%d %H:%M} ET), "
          f"AMC flags {len(flags)}: {' '.join(flags)}")
    h = health(cal)
    if h is not None and len(h):
        h.to_csv(HEALTH, index=False); by = h.groupby("report_date").ratio.apply(lambda s: (s > 2).mean())
        print(f"health (label-free): flags with reaction |gap| > 2x normal: {(h.ratio > 2).mean():.0%} of {len(h)}; by report date {by.round(2).to_dict()} "
              f"(true AMC ran 4-6x; a drop means precision is slipping)")
    else: print("health: no reaction session closed yet for any calendar row")
    print("Journal-only research data. Educational only - not financial advice.")
