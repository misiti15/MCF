"""Print the text of given post ids from the dump (untrusted data, read-only). Educational only."""
import gzip, json, sys, glob
from pathlib import Path
ids = set(sys.argv[2:]); n = int(sys.argv[1])
for f in sorted(glob.glob(str(Path(__file__).parent / "data/dump/*/posts_*.jsonl.gz"))):
    with gzip.open(f, "rt") as fh:
        for line in fh:
            d = json.loads(line)
            if d["id"] in ids:
                print("=" * 8, d["id"], d["score"], d.get("permalink"), "\n", d["title"], "\n", (d.get("selftext") or "")[:n].replace("\n\n", "\n"), "\n")
