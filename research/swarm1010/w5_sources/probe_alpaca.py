"""Read-only probe of Alpaca endpoints (GET only). Prints status + shape, never keys. Educational only - not financial advice."""
import json, os, sys
import requests

H = {"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]}
D = "https://data.alpaca.markets"
P = "https://paper-api.alpaca.markets"
probes = {
    "bars_sip": f"{D}/v2/stocks/bars?symbols=AAPL&timeframe=1Day&start=2026-10-01&feed=sip&limit=5",
    "quotes_sip": f"{D}/v2/stocks/quotes?symbols=AAPL&start=2026-10-08T13:30:00Z&end=2026-10-08T13:30:01Z&feed=sip&limit=5",
    "trades_sip": f"{D}/v2/stocks/trades?symbols=AAPL&start=2026-10-08T13:30:00Z&end=2026-10-08T13:30:01Z&feed=sip&limit=5",
    "quotes_old_2016": f"{D}/v2/stocks/quotes?symbols=AAPL&start=2016-01-05T15:00:00Z&end=2016-01-05T15:00:01Z&feed=sip&limit=2",
    "snapshot": f"{D}/v2/stocks/snapshots?symbols=AAPL&feed=sip",
    "auctions": f"{D}/v2/stocks/auctions?symbols=AAPL&start=2026-10-01&feed=sip&limit=2",
    "corporate_actions": f"{D}/v1/corporate-actions?symbols=AAPL,NVDA&start=2024-01-01&end=2026-10-08&limit=5",
    "corporate_actions_all": f"{D}/v1/corporate-actions?types=forward_split,reverse_split&start=2026-09-01&end=2026-10-08&limit=5",
    "news": f"{D}/v1beta1/news?symbols=AAPL&start=2016-01-01T00:00:00Z&end=2016-01-31T00:00:00Z&limit=3",
    "news_recent": f"{D}/v1beta1/news?limit=3",
    "movers": f"{D}/v1beta1/screener/stocks/movers?top=5",
    "most_actives": f"{D}/v1beta1/screener/stocks/most-actives?top=5",
    "options_contracts": f"{P}/v2/options/contracts?underlying_symbols=AAPL&limit=3",
    "options_snapshot": f"{D}/v1beta1/options/snapshots/AAPL?limit=3",
    "options_bars": f"{D}/v1beta1/options/bars?symbols=AAPL261016C00250000&timeframe=1Day&start=2026-09-01",
    "logos": f"{D}/v1beta1/logos/AAPL",
    "calendar": f"{P}/v2/calendar?start=2026-10-01&end=2026-10-09",
    "assets_one": f"{P}/v2/assets/AAPL",
    "crypto_bars": f"{D}/v1beta3/crypto/us/bars?symbols=BTC/USD&timeframe=1Day&start=2026-10-01",
    "account_activities_fill": f"{P}/v2/account/activities/FILL?page_size=3",
    "orders_closed": f"{P}/v2/orders?status=closed&limit=3",
}
sel = sys.argv[1:] or list(probes)
for k in sel:
    try:
        r = requests.get(probes[k], headers=H, timeout=20)
        body = r.text
        try:
            j = r.json()
            if isinstance(j, dict):
                shape = {kk: (len(v) if isinstance(v, (list, dict)) else v) for kk, v in j.items()}
                if isinstance(j.get("quotes"), dict):
                    shape["sample"] = json.dumps(next(iter(j["quotes"].values()))[:1])[:300]
                if isinstance(j.get("trades"), dict):
                    shape["sample"] = json.dumps(next(iter(j["trades"].values()))[:1])[:300]
                if "news" in j:
                    shape["sample"] = json.dumps([{x: n.get(x) for x in ("created_at", "headline", "symbols", "source")} for n in j["news"][:2]])[:400]
                if "corporate_actions" in j:
                    shape["sample"] = json.dumps(j["corporate_actions"])[:400]
            else:
                shape = f"list[{len(j)}] " + json.dumps(j[:1])[:300]
        except Exception:
            shape = body[:200]
        print(k, r.status_code, str(shape)[:600])
    except Exception as e:
        print(k, "ERR", type(e).__name__, str(e)[:150])
