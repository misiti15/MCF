"""Observer: option C on the FULL denominator (Skeptic skeptic-20261110-1650-1). Rule frozen here before the run:
  For evening D, pull EVERY Alpaca news item created D 16:00:00-19:59:59 ET (no symbol filter, paginated; truncation counted).
  A lab name X is flagged 'AMC on D' if some item has: headline matching EARN, NOT matching PREVIEW, and X is the item's ONLY symbol
  (strict) or its FIRST symbol (loose; reported separately).
  Reference = Yahoo earnings_yf session 'amc' with date D (lab names). False flags are classified: Yahoo BMO on D+1 (a preview of the
  next morning), any Yahoo/Nasdaq event within +-3 days, or none.
Run outside 07:30-16:00 ET only. 0 configs (one frozen rule, two symbol strictness variants reported). Educational only - not financial advice.
Reference note (found in look 1): Yahoo earnings_yf labels AMC events from 2026-11-02 on as 'dmh' placeholders (fetched 10-11, future
events unlabelled), so only evenings <= 2026-10-30 have a usable AMC reference; later evenings are excluded from precision/recall.
usage: python fulldenom.py <earnings_yf.parquet> <earnings_cal.parquet> D1 [D2 ...]"""
import os, re, sys, time
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd, requests
ET = ZoneInfo("America/New_York"); now = datetime.now(ET)
if now.weekday() < 5 and 450 <= now.hour * 60 + now.minute < 960: sys.exit("refusing: 07:30-16:00 ET")
EARN = re.compile(r"\b(earnings|results|quarter|Q[1-4]|revenue|EPS|guidance|beats?|miss(es)?|reports?|reported|profit|sales)\b", re.I)
PREVIEW = re.compile(r"\b(to report|will report|ahead of|preview|expected to|expects to|scheduled|set to|on deck|what to expect|earnings date|to announce|will announce|conference call|webcast|upcoming|week ahead|next week|this week)\b", re.I)
H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
lab = set(open("research/lab_symbols.txt").read().split())
Y = pd.read_parquet(sys.argv[1]); Y["d"] = pd.to_datetime(Y.date).dt.tz_localize(None).dt.strftime("%Y-%m-%d")
N = pd.read_parquet(sys.argv[2]); N["d"] = pd.to_datetime(N.date).dt.tz_localize(None).dt.strftime("%Y-%m-%d")
def items(D, h0=16, h1=19):
    a = datetime.fromisoformat(D).replace(hour=h0, tzinfo=ET); b = a.replace(hour=h1, minute=59, second=59)
    p = {"start": a.isoformat(), "end": b.isoformat(), "limit": 50, "sort": "asc"}; out, pages = [], 0
    while True:
        r = requests.get("https://data.alpaca.markets/v1beta1/news", headers=H, params=p, timeout=30)
        if r.status_code == 429: time.sleep(3); continue
        r.raise_for_status(); j = r.json(); out += j.get("news", []); pages += 1; time.sleep(0.3)
        if not j.get("next_page_token"): break
        p["page_token"] = j["next_page_token"]
    return out, pages
rows = []; FL = []
for D in sys.argv[3:]:
    it, pages = items(D)
    D1 = (pd.Timestamp(D) + pd.offsets.BDay(1)).strftime("%Y-%m-%d")
    ref = set(Y[(Y.d == D) & (Y.session == "amc") & Y.symbol.isin(lab)].symbol)
    near = lambda s: bool(((Y.symbol == s) & (abs(pd.to_datetime(Y.d) - pd.Timestamp(D)).dt.days <= 3)).any() or ((N.symbol == s) & (abs(pd.to_datetime(N.d) - pd.Timestamp(D)).dt.days <= 3)).any())
    bmo_next = set(Y[(Y.d == D1) & (Y.session == "bmo")].symbol)
    multi = sum(len(x.get("symbols", [])) > 1 for x in it)
    # LOOK 2 (amendment, counted, added after look 1 showed same-day BMO follow-ups as false flags): 'fresh' = X had NO earnings headline
    # (EARN, not PREVIEW, X first symbol) earlier that day 04:00-15:59 ET, i.e. the evening story is the first earnings news of the day.
    am, _ = items(D, 4, 15)
    morning = {(x.get("symbols") or [None])[0] for x in am if EARN.search(x.get("headline", "") or "") and not PREVIEW.search(x.get("headline", "") or "")}
    # LOOK 3 (counted): 'hybrid' = strict+fresh AND X listed with report date D in the live job's PRE-OPEN snapshot mcf-data/earnings/<D>.json
    # (Nasdaq dates only, written before 09:30 on D: point-in-time). Snapshot dir via env SNAP (files <D>.json).
    import json as _j
    snap = _j.load(open(os.path.join(os.environ["SNAP"], f"{D}.json")))["symbols"]; listed = {k for k, v in snap.items() if D in v}
    for mode in ("strict", "loose", "strict+fresh", "hybrid"):
        fl = set()
        for x in it:
            h = x.get("headline", "") or ""; s = x.get("symbols", []) or []
            if not s or not EARN.search(h) or PREVIEW.search(h): continue
            if mode.startswith("strict") and len(s) != 1: continue
            if mode in ("strict+fresh", "hybrid") and s[0] in morning: continue
            if mode == "hybrid" and s[0] not in listed: continue
            if s[0] in lab: fl.add(s[0])
        tp = fl & ref; fp = fl - ref
        cls = {"bmo_next_morning": len([s for s in fp if s in bmo_next]), "event_within_3d": len([s for s in fp if s not in bmo_next and near(s)])}
        cls["no_event"] = len(fp) - sum(cls.values())
        if mode == "hybrid": FL.extend((D, x, x in ref) for x in sorted(fl))
        rows.append(dict(D=D, mode=mode, items=len(it), pages=pages, multi_symbol_items=multi, ref_amc=len(ref), flagged=len(fl), tp=len(tp),
                         precision=len(tp) / len(fl) if fl else float("nan"), recall=len(tp) / len(ref) if ref else float("nan"), **cls))
R = pd.DataFrame(rows); pd.set_option("display.width", 220)
pd.DataFrame(FL, columns=["D", "symbol", "yahoo_amc"]).to_csv(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "fulldenom_hybrid_flags.csv"), index=False)
print(R.round(3).to_string(index=False))
for mode, g in R.groupby("mode"):
    print(f"\n{mode}: pooled precision {g.tp.sum() / g.flagged.sum():.3f} ({int(g.tp.sum())}/{int(g.flagged.sum())}), recall {g.tp.sum() / g.ref_amc.sum():.3f} ({int(g.tp.sum())}/{int(g.ref_amc.sum())}); "
          f"false flags: bmo_next_morning {int(g.bmo_next_morning.sum())}, event_within_3d {int(g.event_within_3d.sum())}, no_event {int(g.no_event.sum())}")
print("\nTruncation: every evening is fully paginated (pages column); limit=50 per page is not a cap here. Educational only - not financial advice.")
