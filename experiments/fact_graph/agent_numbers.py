"""List every number in agent briefs, one row per (brief, line, raw), for labelling."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from onus import numbers  # noqa: E402


def rows(path: Path):
    for n, line in enumerate(path.read_text().splitlines(), start=1):
        seen = {}
        for q in numbers.find(line):
            if q.temporal:
                continue
            k = seen[q.raw] = seen.get(q.raw, 0) + 1
            yield {"brief": path.stem, "line": n, "raw": q.raw, "k": k, "text": line.strip()}


if __name__ == "__main__":
    out = [r for p in sorted(Path(sys.argv[1]).glob("brief_*.md")) for r in rows(p)]
    Path(sys.argv[2]).write_text("\n".join(json.dumps(r) for r in out) + "\n")
    print(len(out), "numbers")
