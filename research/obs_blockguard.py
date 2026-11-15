"""Request-time guard for the research locked block (rule 19, checklist #43; Observer 2026-11-15).
Every Observer fetch passes its request params through check(p): refuses any request whose [start, end] touches
2024-11-01..2025-02-28, and any open-ended start before 2025-03-01. Educational only - not financial advice."""
BLOCK = ("2024-11-01", "2025-02-28")
def check(p):
    s = str(p.get("start", ""))[:10]; e = str(p.get("end", "9999-12-31"))[:10]
    if not s: raise AssertionError("rule 19: request without a start date (could reach the locked block)")
    if not (e < BLOCK[0] or s > BLOCK[1]): raise AssertionError(f"rule 19: request {s}..{e} touches the locked block {BLOCK[0]}..{BLOCK[1]}")
    return p
if __name__ == "__main__":
    ok = [{"start": "2025-03-01", "end": "2026-11-14"}, {"start": "2024-09-01", "end": "2024-10-31"}, {"start": "2026-11-12T16:00:00-05:00", "end": "2026-11-12T19:59:59-05:00"}]
    bad = [{"start": "2024-09-01", "end": "2026-11-14"}, {"start": "2025-02-28", "end": "2025-03-05"}, {"start": "2024-11-15"}, {"end": "2026-01-01"}]
    for p in ok: check(p)
    for p in bad:
        try: check(p); raise SystemExit(f"guard FAILED to refuse {p}")
        except AssertionError: pass
    print(f"blockguard selftest ok ({len(ok)} allowed, {len(bad)} refused)")
