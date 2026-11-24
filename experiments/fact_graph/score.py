"""Score the graph prototype and current onus on the labelled claims."""
import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import graph_check as g  # noqa: E402
import xbrl  # noqa: E402

from onus import evidence as ev  # noqa: E402

CASES = __import__(sys.argv[1] if len(sys.argv) > 1 else "cases").CASES
FLAG = {"wrong", "unsupported"}

g.MODE = os.environ.get("MODE", "lexical")
g.TAU = float(os.environ.get("TAU", "0"))
g.DELTA = float(os.environ.get("DELTA", "0.02"))
if g.MODE != "lexical":
    from emb_map import Mapper
    g.MAPPER = Mapper(os.environ.get("MODEL", "BAAI/bge-small-en-v1.5"), g.SEGMENTS)
graph = g.Graph(xbrl.load(str(g.FILING_HTML)))
presence = ev.load([g.FILING_TEXT])
end = xbrl.period_end(str(g.FILING_HTML))

doc = HERE / f"{sys.argv[1] if len(sys.argv) > 1 else 'cases'}_doc.md"
lines = ["Beyond Meat reported results for its second quarter ended June 28, 2025.", ""]
where = []
for _, _, text in CASES:
    where.append(len(lines) + 1)
    lines += [text, ""]
doc.write_text("\n".join(lines))
out = subprocess.run(["uv", "run", "-q", "--project", str(g.ROOT), "onus", str(doc), "-e",
                      str(g.FILING_TEXT), "--no-llm", "--format", "json"],
                     capture_output=True, text=True).stdout
report = json.loads(out)
report = report[0] if isinstance(report, list) else report
onus_flagged = {int(f["label"].split()[-1]) for f in report["findings"]}

rows, by_cat = [], defaultdict(lambda: {"n": 0, "graph": 0, "onus": 0})
for (cat, truth, text), line in zip(CASES, where, strict=True):
    verdicts = [v for _, v in g.check(text, graph, presence, end) if v.status != "skipped"]
    gflag = any(v.status in FLAG for v in verdicts)
    weak = any(v.status == "weak" for v in verdicts)
    oflag = line in onus_flagged
    right_g, right_o = gflag != truth, oflag != truth
    c = by_cat[cat]
    c["n"] += 1
    c["graph"] += right_g
    c["onus"] += right_o
    why = "; ".join(f"{v.raw}: {v.status} ({v.path[:60]})" for v in verdicts)
    rows.append((cat, truth, text, right_g, right_o, weak, why))

print(f"{'category':14} {'claims':>6} {'graph':>6} {'onus':>6}")
for cat, c in by_cat.items():
    print(f"{cat:14} {c['n']:>6} {c['graph']:>6} {c['onus']:>6}")
n = len(rows)
gr, orr = sum(r[3] for r in rows), sum(r[4] for r in rows)
print(f"{'total right':14} {n:>6} {gr:>6} {orr:>6}")
false_claims = [r for r in rows if not r[1]]
true_claims = [r for r in rows if r[1]]
print(f"\nfalse claims caught:  graph {sum(r[3] for r in false_claims)}/{len(false_claims)}"
      f"   onus {sum(r[4] for r in false_claims)}/{len(false_claims)}")
print(f"true claims passed:   graph {sum(r[3] for r in true_claims)}/{len(true_claims)}"
      f"   onus {sum(r[4] for r in true_claims)}/{len(true_claims)}")
print(f"graph passes resting on presence only (weak): {sum(1 for r in rows if r[5] and r[3])}")
print("\nwhere either is wrong:")
for _cat, truth, text, rg, ro, _weak, why in rows:
    if not (rg and ro):
        marks = f"[{'T' if truth else 'F'}] graph {'ok ' if rg else 'BAD'} onus {'ok ' if ro else 'BAD'}"
        print(f"  {marks} {text[:72]:72} | {why[:110]}")
print(f"RESULT n={n} graph={gr} onus={orr} graph_false_caught={sum(r[3] for r in false_claims)}/{len(false_claims)} "
      f"graph_true_passed={sum(r[3] for r in true_claims)}/{len(true_claims)}")
