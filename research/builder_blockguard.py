"""Builder request-time guard (checklist #43, Lead lead-20261115-0700-1): refuse any market-data request touching the locked block
2024-11-01..2025-02-28 or with no start. split(a, b) returns the sub-ranges of [a, b] that avoid the block (for callers that want
the data on both sides). Educational only - not financial advice."""
B0, B1 = "2024-11-01", "2025-02-28"


def check(start: str, end: str) -> None:
    if not start:
        raise ValueError("blockguard: a request needs an explicit start date")
    s, e = str(start)[:10], str(end)[:10] if end else "9999-12-31"
    if s <= B1 and e >= B0:
        raise ValueError(f"blockguard: request {s}..{e} touches the locked block {B0}..{B1} (rule 19)")


def split(start: str, end: str) -> list[tuple[str, str]]:
    s, e = str(start)[:10], str(end)[:10]; out = []
    if s < B0: out.append((s, min(e, "2024-10-31")))
    if e > B1: out.append((max(s, "2025-03-01"), e))
    for a, b in out: check(a, b)
    return [(a, b) for a, b in out if a <= b]


if __name__ == "__main__":
    ok = [("2023-09-01", "2024-10-31"), ("2025-03-01", "2026-11-13"), ("2026-11-12", "2026-11-13")]
    bad = [("2024-09-01", "2026-11-14"), ("2024-12-01", "2024-12-02"), ("2025-02-28", "2025-03-05"), ("", "2025-04-01")]
    for a, b in ok: check(a, b)
    for a, b in bad:
        try: check(a, b); raise SystemExit(f"FAILED: {a}..{b} allowed")
        except ValueError: pass
    assert split("2024-09-16", "2026-11-13") == [("2024-09-16", "2024-10-31"), ("2025-03-01", "2026-11-13")]
    print("blockguard selftest ok: 3 allowed, 4 refused, split ok")
