"""Score four checkers on every number in the agent briefs, against hand labels."""
import importlib.util
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
BRIEFS = HERE / "agent_briefs"
sys.path.insert(0, str(HERE))
import graph_check as g  # noqa: E402
import xbrl  # noqa: E402
from agent_labels import LABELS  # noqa: E402
from agent_numbers import rows as numbers_in  # noqa: E402

from onus import evidence as ev  # noqa: E402

rows = [r for p in sorted(BRIEFS.glob("brief_*.md")) for r in numbers_in(p)]
for r in rows:
    r["label"] = None
by_line = defaultdict(list)
for r in rows:
    by_line[(r["brief"], r["line"])].append(r)
for (brief, line), rs in by_line.items():
    for r, c in zip(rs, LABELS[brief[6:]][line], strict=True):
        r["label"] = c


def onus_flags(project):
    flagged = set()
    for brief in sorted({r["brief"] for r in rows}):
        out = subprocess.run(["uv", "run", "-q", "--project", str(project), "onus", str(BRIEFS / f"{brief}.md"),
                              "-e", str(g.FILING_TEXT), "--no-llm", "--format", "json"],
                             capture_output=True, text=True).stdout
        rep = json.loads(out)
        rep = rep[0] if isinstance(rep, list) else rep
        for f in rep["findings"]:
            flagged.add((brief, int(f["label"].split()[-1]), f["message"].split(":")[0]))
    return {id(r): ("flag" if (r["brief"], r["line"], r["raw"]) in flagged else "pass") for r in rows}


def graph_flags(mode):
    g.MODE, g.TAU, g.DELTA = mode, 0.7, 0.02
    if mode != "lexical" and g.MAPPER is None:
        from emb_map import Mapper
        g.MAPPER = Mapper("BAAI/bge-small-en-v1.5", g.SEGMENTS)
    graph = g.Graph(xbrl.load(str(g.FILING_HTML)))
    presence = ev.load([g.FILING_TEXT])
    out = {}
    for rs in by_line.values():
        verdicts = [v for _, v in g.check(rs[0]["text"], graph, presence, date(2025, 6, 28)) if v.status != "skipped"]
        pool = defaultdict(list)
        for v in verdicts:
            pool[v.raw].append(v)
        for r in rs:
            vs = pool.get(r["raw"], [])
            v = vs[r["k"] - 1] if len(vs) >= r["k"] else None
            st = v.status if v else "none"
            out[id(r)] = "flag" if st in ("wrong", "unsupported") else "weak" if st in ("weak", "none") else "pass"
            r.setdefault("why", {})[mode] = f"{st}: {v.path[:70]}" if v else "not parsed"
    return out


def graph_v2():
    g.MODE = "lexical"
    graph = g.Graph(xbrl.load(str(g.FILING_HTML)))
    presence = ev.load([g.FILING_TEXT])
    out = {}
    for brief in sorted({r["brief"] for r in rows}):
        per_line = g.check_document((BRIEFS / f"{brief}.md").read_text(), graph, presence, date(2025, 6, 28))
        for (b, line), rs in by_line.items():
            if b != brief:
                continue
            items = per_line.get(line, [])
            if rs[0]["text"].startswith("|") and len(items) == len(rs):
                pairs = list(zip(rs, [v for _, v in items], strict=True))
            else:
                pool = defaultdict(list)
                for q, v in items:
                    pool[q.raw].append(v)
                pairs = [(r, pool[r["raw"]][r["k"] - 1] if len(pool.get(r["raw"], [])) >= r["k"] else None)
                         for r in rs]
            for r, v in pairs:
                st = v.status if v else "none"
                out[id(r)] = "flag" if st in ("wrong", "unsupported") else "weak" if st in ("weak", "none") else "pass"
                r.setdefault("why", {})["v2"] = f"{st}: {v.path[:80]}" if v else "not parsed"
    return out


# ONUS_BASELINE: a checkout of another onus revision to score alongside this one (e.g. a worktree of main).
baseline = {"onus baseline": onus_flags(Path(os.environ["ONUS_BASELINE"]))} if os.environ.get("ONUS_BASELINE") else {}
tools = {**baseline, "onus (this checkout)": onus_flags(g.ROOT),
         "graph lexical": graph_flags("lexical"),
         **({"graph embed": graph_flags("embed")} if importlib.util.find_spec("sentence_transformers") else {}),
         "graph +tables+arith": graph_v2()}
print(f"{'':16} {'F caught':>10} {'T passed':>10} {'T verified':>11} {'U flagged':>10} {'R flagged':>10}")
for name, res in tools.items():
    c = Counter((r["label"], res[id(r)]) for r in rows)
    n = Counter(r["label"] for r in rows)
    verified = c["T", "pass"] if "graph" in name else "-"
    print(f"{name:16} {c['F','flag']:>4}/{n['F']:<5} {c['T','pass'] + c['T','weak']:>4}/{n['T']:<5} "
          f"{verified:>5}/{n['T']:<5} {c['U','flag']:>4}/{n['U']:<5} {c['R','flag']:>4}/{n['R']:<5}")
json.dump([{**{k: v for k, v in r.items() if k != "why"}, "why": r.get("why", {}),
            **{name: res[id(r)] for name, res in tools.items()}} for r in rows],
          open(HERE / "agent_scored.json", "w"), indent=1)
