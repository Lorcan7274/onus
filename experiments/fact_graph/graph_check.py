"""Prototype: check a release's numbers against a filing's XBRL facts as a graph, with no model.

Nodes are facts (concept, period, segment, unit, value). A claim's number gets a key from code:
period from the document and "compared to", metric from the words around it, segment if named.
It is matched by key, else recomputed along one derivation edge (share of revenue, change,
difference), else checked for presence in the filing's text as a weak fallback.
"""
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "src"))
FILING_HTML = HERE / "data" / "q2_2025_10q.htm"
FILING_TEXT = ROOT / "evals" / "fixtures" / "beyond_meat" / "q2_2025_10q.md"
import xbrl  # noqa: E402

from onus import evidence as ev  # noqa: E402
from onus import numbers  # noqa: E402
from onus.evidence import GENERIC, _stems  # noqa: E402

# A finance profile's segment vocabulary, as this filer's members name them.
SEGMENTS = {"country:US": "u.s.", "us-gaap:NonUsMember": "international",
            "us-gaap:SalesChannelDirectlyToConsumerMember": "retail",
            "us-gaap:SalesChannelThroughIntermediaryMember": "foodservice"}
SEGMENT_CUE = {"u.s.": re.compile(r"\bU\.S\.", re.I), "international": re.compile(r"\binternational\b", re.I),
               "retail": re.compile(r"\bretail\b", re.I), "foodservice": re.compile(r"\bfoodservice\b", re.I)}
PRIOR = re.compile(r"\bcompared (?:to|with)\b|\bfrom\s*$|\byear-ago\b|\bprior-year\b", re.I)
SHARE = re.compile(r"\bmargin\b|% of (?:net )?revenues?\b|\bof (?:total )?net revenues\b", re.I)
# A finance profile's abbreviations, written out before a claim's words are matched to facts.
ABBREV = [(re.compile(p, re.I), r) for p, r in [
    (r"\bEPS\b", "net loss per share"), (r"\bopex\b", "operating expenses"), (r"\bCOGS\b", "cost of goods sold"),
    (r"\bSG&A\b", "selling, general and administrative expenses"), (r"\bR&D\b", "research and development expenses"),
    (r"\bcapex\b", "purchases of property, plant and equipment"), (r"\bint'l\b", "international")]]
CHANGE = re.compile(r"\b(?:increase|decrease|grew|grow|fell|declin|rose|up|down|wide|widen|narrow|year-over-year)",
                    re.I)
# Geographies a claim may name that this filer's segments do not; naming one is a segment no fact has.
GEOGRAPHY = re.compile(r"\b(?:europe|emea|asia|apac|canada|china|latin america|north america)\b", re.I)
# After these, a number is a part or a driver of the sentence's subject, not the subject itself.
PART = re.compile(r"\b(?:included|including|consisting of|of which|driven by|due to|attributable to|offset by)\b", re.I)
PER_SHARE = re.compile(r"\bper (?:common |diluted |basic )?share\b", re.I)
IGNORED = GENERIC | _stems("second first third fourth half fiscal primarily decreased increased decrease increase "
                           "grew fell declined rose wider widened narrower narrowed year-over-year u.s. international "
                           "retail foodservice europe emea asia apac canada china america latin north margin "
                           "first-half h1 1h ytd january february march april may june july august september "
                           "october november december channel loss income was were mix derived")
FUTURE = re.compile(r"\bexpect|\bestimat|\bwill\b|\bguidance\b|\boutlook\b|\bthird quarter of 2025\b", re.I)
REVENUE = "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"
SIX_MONTHS = re.compile(r"\bsix[- ]months?\b|\bfirst[- ]half\b|\b[hH]1\b|\b1H\b|\byear[- ]to[- ]date\b|\bYTD\b",
                        re.I)
# How a claim's words find their fact: "lexical" word overlap, "fallback" to embeddings when overlap finds
# none, or "embed" ranking by embeddings alone. Code checks period, segment, unit and value either way.
MODE, TAU, MAPPER, DELTA = "lexical", 0.0, None, 0.02
# A comma that starts a clause; one inside a label ("Property, plant and equipment") or a date does not.
CLAUSE = re.compile(r";|,\s+(?=(?:or|compared|and|which|while|a|an|up|down|from|versus|vs)\b)",
                    re.I)


@dataclass
class Verdict:
    raw: str
    status: str  # matched | derived | wrong | weak | unsupported | skipped
    path: str = ""


@dataclass
class Graph:
    facts: list
    by_key: dict = field(default_factory=dict)

    def __post_init__(self):
        for f in self.facts:
            self.by_key.setdefault((f.concept, f.months, f.end, f.members), []).append(f)

    def value(self, concept, months, end, members=()):
        for (c, m, e, mem), fs in self.by_key.items():
            if c == concept and m == months and abs((e - end).days) <= 7 and mem == members:
                return fs[0]
        return None


def segment_of(text: str) -> set[str]:
    return {name for name, cue in SEGMENT_CUE.items() if cue.search(text)}


def unit_ok(q, f, per_share=False) -> bool:
    if q.kind in ("currency",):
        return f.unit == ("iso4217:USD xbrli:shares" if per_share else "iso4217:USD")
    if q.kind == "amount":
        return f.unit in ("iso4217:USD", "xbrli:shares")
    if q.kind == "percent":
        return f.unit == "xbrli:pure"
    return f.unit not in ("iso4217:USD", "iso4217:USD xbrli:shares")


def content(window: str) -> set[str]:
    return (_stems(window) - IGNORED) or (_stems(window) & _stems("loss income"))


def metric(window: str, graph: Graph, q, months, end, segments, ok=lambda f: True, relaxed=False):
    """Candidate concepts for the words around a number: those explaining at least half of them,
    best first; "loss" and "income" only break ties, since a loss is the sign of an income concept."""
    signed = _stems(window) & _stems("loss income")
    words = content(window) or signed  # "Net loss" names only its sign, which then names the concept
    if not words:
        return []
    out = []
    seen = set()
    for f in graph.facts:
        if f.months not in (months, 0) or abs((f.end - end).days) > 7 or not ok(f):
            continue  # a period's flow, or a balance at its end
        fseg = {SEGMENTS[m] for m in f.members if m in SEGMENTS}
        if (not fseg >= segments if relaxed else fseg != segments) or any(m not in SEGMENTS for m in f.members):
            continue
        label = _stems(f.words) - GENERIC
        if not label or (f.concept, f.members) in seen:
            continue
        hit = len(label & words)
        cover = hit / len(words)
        if hit and cover > 0.5:
            seen.add((f.concept, f.members))
            row = _stems(f.label) - GENERIC or label
            out.append(((cover, len(label & signed)), len(row & words) / len(row), f))
    if not out:
        return []
    top = max(k for k, _, _ in out)
    return [f for _, _, f in sorted((x for x in out if x[0] == top), key=lambda x: -x[1])]


def keys(window, graph, q, months, when, segs, ok):
    lex = metric(window, graph, q, months, when, segs, ok)
    if MODE == "lexical" or (MODE == "fallback" and lex):
        return lex
    pool, seen = [], set()
    for f in graph.facts:
        if f.months not in (months, 0) or abs((f.end - when).days) > 7 or not ok(f):
            continue
        if any(m not in SEGMENTS for m in f.members):
            continue
        if segs and {SEGMENTS[m] for m in f.members} != segs:
            continue
        if (f.concept, f.members) not in seen:
            seen.add((f.concept, f.members))
            pool.append(f)
    ranked = MAPPER.rank(window, pool)
    if not ranked or ranked[0][0] < TAU:
        return []
    return [f for sim, f in ranked[:3] if sim >= ranked[0][0] - DELTA]  # a near-tie is kept, as word overlap keeps one


def close(q, value: float) -> bool:
    return abs(abs(value) - q.value) <= q.tolerance + 1e-9


def expand(text: str) -> str:
    for pattern, words in ABBREV:
        text = pattern.sub(words, text)
    return text


def check(text: str, graph: Graph, presence: ev.Evidence, end: date):
    out = []
    for para in text.split("\n"):
        months = 3
        for sentence in numbers.sentences(expand(para).replace("U.S. ", "U.S.\u200b")):
            if SIX_MONTHS.search(sentence):
                months = 6
            elif re.search(r"\bquarter\b|\bQ[1-4]\b|\bthree months\b", sentence, re.I):
                months = 3
            qs = [q for q in numbers.find(sentence) if not q.temporal]
            if not qs:
                continue
            future = bool(FUTURE.search(sentence))
            subject = None
            prev_end = 0
            for i, q in enumerate(qs):
                nxt = qs[i + 1].start if i + 1 < len(qs) else len(sentence)
                before = CLAUSE.split(sentence[prev_end:q.start])[-1]
                # "included $Y" makes a part; "including restricted cash, was $Y" only modifies
                part = bool(PART.search(before)) and not content(PART.split(before)[-1])
                if part:
                    before = PART.split(before)[-1]
                after = re.split(rf"{CLAUSE.pattern}|\band\b|\bwas\b|\bwere\b", sentence[q.end:nxt], maxsplit=1,
                                 flags=re.I)[0]
                if before.rstrip().endswith((",", ":")) and content(after):
                    before = ""  # "$4.5M SG&A, $2.5M legal fees": each label follows its own number
                window = f"{before} {after}"
                if q.kind == "percent" and re.match(r"\s*of (?:total )?(?:net )?(?:revenues?|sales)\b", after, re.I):
                    window += " % of net revenues"  # "43.9% of revenue": the sign is part of the number
                # "of net revenues" names the denominator, not the subject
                mwindow = re.sub(r"%?\s*\bof (?:total )?(?:net )?(?:revenues?|sales)\b", " ", window, flags=re.I)
                clause = CLAUSE.split(sentence[:q.start])[-1] + after
                # "U.S. retail fell to 43.9%; international rose to 41.3%": each clause names its own segment
                segs = segment_of(clause) or segment_of(sentence)
                if segs and SHARE.search(window) and not content(mwindow):
                    mwindow += " net revenues"  # a segment's share of revenue is its revenue over the total
                per_share = bool(PER_SHARE.search(window))
                prior = bool(PRIOR.search(sentence[:q.start]))
                when = end.replace(year=end.year - 1) if prior else end
                v = Verdict(q.raw, "skipped")
                elsewhere = GEOGRAPHY.search(mwindow) if re.search(r"\brevenue|\bsales\b", mwindow, re.I) else None
                if elsewhere and not future:
                    fits = lambda f, q=q, ps=per_share: unit_ok(q, f, ps)  # noqa: E731
                    hits = [f for f in metric(mwindow, graph, q, months, when, segs, fits, relaxed=True)
                            if close(q, f.value)]
                    where = ", ".join(SEGMENTS[m] for m in hits[0].members if m in SEGMENTS) if hits else ""
                    v = Verdict(q.raw, "wrong" if hits else "unsupported",
                                f"{q.raw} is {where or 'company'} {_n(hits[0])}, not {elsewhere.group(0)}" if hits
                                else f"no {elsewhere.group(0)} segment in the facts")
                elif future:
                    v = Verdict(q.raw, "weak" if _present(q, sentence, presence) else "unsupported",
                                "guidance: no facts")
                else:
                    cands = keys(mwindow, graph, q, months, when, segs,
                                 lambda f, q=q, ps=per_share: unit_ok(q, f, ps) or q.kind == "percent")
                    stated = [f for f in cands if unit_ok(q, f, per_share)]
                    named = bool(content(mwindow))
                    if not cands and not named and subject is not None and not part:
                        if unit_ok(q, subject, per_share):
                            stated = cands = [graph.value(subject.concept, months, when, subject.members) or subject]
                        else:
                            cands = [subject]
                    if any(close(q, f.value * (100 if f.unit == "xbrli:pure" else 1)) for f in stated):
                        f = next(f for f in stated if close(q, f.value * (100 if f.unit == "xbrli:pure" else 1)))
                        how = f"{f.concept.split(':')[-1]} {f.months}m to {f.end} = {f.value:,.0f}"
                        # a lower-ranked tie only fails to contradict the claim
                        v = (Verdict(q.raw, "matched", how) if f is stated[0]
                             else Verdict(q.raw, "weak", f"ambiguous key: {how}, ranked below {_n(stated[0])}"))
                    else:
                        subj = (subject if subject and SHARE.search(window) and not part
                                else cands[0] if cands else None if named or part else subject)
                        v = derive(q, window, subj, graph, months, when, end, segs, cands[1:]) or v
                        if v.status == "skipped":
                            if stated:
                                f = stated[0]
                                what = f"{f.concept.split(':')[-1]} {f.months}m to {f.end} is {f.value:,.2f}"
                                v = Verdict(q.raw, "wrong", what)
                            elif (q.kind == "percent" and subj is not None
                                  and (SHARE.search(window) or CHANGE.search(window))):
                                hint = derive_hint(q, window, subj, graph, months, when, end, segs)
                                v = Verdict(q.raw, "wrong", hint)
                            else:
                                v = Verdict(q.raw, "weak" if _present(q, sentence, presence) else "unsupported",
                                            "no key: presence only")
                    if not part and q.kind in ("currency", "amount"):
                        subject = stated[0] if stated else None if named else subject
                    elif cands and not part and subject is None:
                        subject = cands[0]
                out.append((sentence, v))
                prev_end = q.end
    return out


def _formulas(q, window, subj, graph, months, when, end, segs):
    cur = graph.value(subj.concept, months, when, subj.members)
    if cur is None:
        return []
    out = []
    if q.kind == "percent" and SHARE.search(window):
        total = "total net revenues" in window.lower() or subj.concept == REVENUE
        rev = graph.value(REVENUE, months, when, () if total else subj.members)
        if rev and rev.value:
            out.append((cur.value / rev.value * 100, f"{_n(subj)} / net revenues ({months}m to {when})"))
    if CHANGE.search(window) or q.kind == "percent":
        base = graph.value(subj.concept, months, when.replace(year=when.year - 1), subj.members)
        if base and base.value:
            if q.kind == "percent" and not SHARE.search(window):
                how = f"change in {_n(subj)}, {when.year} vs {when.year - 1}"
                out.append(((cur.value / base.value - 1) * 100, how))
            if q.kind in ("currency", "amount"):
                out.append((cur.value - base.value, f"{_n(subj)} {when.year} - {when.year - 1}"))
    return out


def derive(q, window, subj, graph, months, when, end, segs, also=()):
    for s in [subj, *also]:
        if s is None:
            continue
        for value, how in _formulas(q, window, s, graph, months, when, end, segs):
            if close(q, value):
                return Verdict(q.raw, "derived", f"{how} = {value:,.2f}")
    return None


def derive_hint(q, window, subj, graph, months, when, end, segs):
    fs = _formulas(q, window, subj, graph, months, when, end, segs)
    return "; ".join(f"{how} = {v:,.2f}" for v, how in fs) or f"no formula for {_n(subj)}"


def _n(f):
    return f.label or f.concept.split(":")[-1]


def _present(q, sentence, presence) -> bool:
    return any(q.matches(e) and p.can_support(e, sentence) for p in presence.passages for e in p.quantities)


if __name__ == "__main__":
    release = sys.argv[1]
    graph = Graph(xbrl.load(str(FILING_HTML)))
    presence = ev.load([FILING_TEXT])
    text = Path(release).read_text()
    m = re.search(r"quarter ended (\w+ \d{1,2}, \d{4})", text)
    from datetime import datetime
    end = datetime.strptime(m.group(1), "%B %d, %Y").date()
    results = check(text, graph, presence, end)
    show = sys.argv[2:] or ["wrong", "unsupported"]
    from collections import Counter
    print(Counter(v.status for _, v in results))
    for sentence, v in results:
        if v.status in show:
            print(f"  {v.status:11} {v.raw:16} {v.path[:90]:90} | {sentence[:70]}")


# -- tables and a claim's own arithmetic -------------------------------------------------------------

COL_CHANGE = re.compile(r"\bchange\b|\byoy\b|\by/y\b", re.I)
COL_PRIOR = re.compile(r"\b2024\b|'24\b|\b24\b|year-ago|prior", re.I)
COL_CURRENT = re.compile(r"\b2025\b|'25\b|\b25\b", re.I)
COL_SHARE = re.compile(r"share of (?:net )?revenue|% of revenue|\bmix\b", re.I)
TABLE_MILLIONS = re.compile(r"\(\s*\$\s*M\b|\$M\b|in millions", re.I)
BARE = re.compile(r"^\(?-?\d[\d,]*(?:\.\d+)?\)?$")
FLAGGED = {"wrong", "unsupported"}


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


PERIOD_WORDS = re.compile(r"\bQ[1-4]\b|\b20\d\d\b|'?\b\d\d\b|year-ago|\(|\)", re.I)


MONEY_CELL = re.compile(r"^[-+−]?\(?[-+−]?\$?\s?\(?[-−]?\d[\d,]*(?:\.\d+)?\)?$")
# A unit stated once for a whole document: "in $M unless noted", "($ in millions)".
DOC_MILLIONS = re.compile(r"\bin \$\s?M\b|\$M unless|\$ in millions|\bin \$?\s?millions\b|\(\$\s?M\)", re.I)
MARGIN_PART = re.compile(r"^(?P<a>.*?\S)\s*\((?P<b>[-+−]?\d[\d.,]*\s*(?:%|bp\b|pts?\b))\)\s*$")
OPERATOR = re.compile(r"^[\s()]*(?:(?P<op>[+\-−x×*/])|(?P<word>plus|minus|less|times|over|divided by))[\s()]*$",
                      re.I)


def _money(cell: str, millions: bool, label: str) -> str:
    """A cell with no scale under a table or document that states "$M", written as the money it is; a
    per-share row is dollars per share."""
    text = cell.strip()
    if not MONEY_CELL.match(text):
        return cell
    num = re.sub(r"[^\d.,]", "", text)
    if PER_SHARE.search(expand(label)):
        return f"${num} per share"
    return f"${num} million" if millions else cell


def split_row(label: str, cells: list[str]) -> list[tuple[str, list[str], int]]:
    """A row as one or more metrics: "U.S. retail / U.S. foodservice | $32.9 / $11.1" is two rows, and
    "Gross profit (margin) | $8.6 (11.5%)" is gross profit and its margin. Each part keeps its place."""
    names = [n.strip() for n in label.split(" / ")]
    filled = [c for c in cells if c.strip()]
    if len(names) > 1 and filled and all(len(c.split(" / ")) == len(names) for c in filled):
        period = " ".join(SIX_MONTHS.findall(label))
        parts = [[c.split(" / ")[i].strip() if c.strip() else "" for c in cells] for i in range(len(names))]
        return [(n if not period or SIX_MONTHS.search(n) else f"{period} {n}", parts[i], i)
                for i, n in enumerate(names)]
    paren = re.match(r"^(?P<head>.*?\S)\s*\((?P<sub>[^)]*)\)\s*$", label)
    if paren and any(MARGIN_PART.match(c.strip()) for c in cells):
        matches = [MARGIN_PART.match(c.strip()) for c in cells]
        return [(paren["head"], [m["a"] if m else c for m, c in zip(matches, cells, strict=True)], 0),
                (f"{paren['head']} {paren['sub']}", [m["b"] if m else "" for m in matches], 1)]
    return [(label, cells, 0)]


def table_sentences(header: list[str], row: list[str], millions: bool = False) -> list[tuple[str, tuple]]:
    """Each value cell of a row as a sentence that names its metric and its period, with the cell and part
    it came from, so verdicts can be put back in the row's order."""
    millions = millions or bool(TABLE_MILLIONS.search(" ".join(header)))
    out = []
    for name, cells, part in split_row(row[0].replace("**", ""), row[1:]):
        label = name
        if segment_of(expand(label)) and not content(expand(label)):
            label = f"{label} net revenues"  # a row that names only a segment is that segment's revenue
        for col, (h, cell) in enumerate(zip(header[1:], cells, strict=False)):
            if not cell.strip():
                continue
            value = _money(cell, millions, label)
            if COL_SHARE.search(h):
                qs = re.findall(r"\d[\d.,]*%", cell)
                if not qs:
                    continue
                prior = f", compared to {qs[1]} of total net revenues in the year-ago period." if len(qs) > 1 else "."
                sentence = f"{label} net revenues were {qs[0]} of total net revenues{prior}"
            elif COL_CHANGE.search(h):
                sentence = f"{label} changed by {value} year-over-year."
            elif COL_PRIOR.search(h) and not COL_CURRENT.search(h):
                sentence = f"Compared to the year-ago period, {label} was {value}."
            elif COL_CURRENT.search(h):
                sentence = f"{label} was {value}."
            else:
                sentence = f"{label} {h} was {value}."
            out.append((sentence, (col, part)))
    return out


def written_formulas(text: str, items: list) -> list[tuple[float, str, tuple]]:
    """Arithmetic an agent wrote out between numbers in `text` ("($8.6 + $1.7) / $75.0", "$59.4M operating
    burn plus $6.4M capex", "$26.0M x 4"), evaluated left to right, with the verdicts of its operands."""
    out = []
    for start in range(len(items)):
        value, how, used = items[start][0].value, items[start][0].raw, [items[start][1]]
        for k in range(start + 1, len(items)):
            between = text[items[k - 1][0].end:items[k][0].start]
            between = re.sub(r"\b(?:operating|burn|capex|charges?|costs?|items?|the|of)\b", " ", between, flags=re.I)
            m = OPERATOR.match(between)
            if m is None:
                break
            op = (m["op"] or m["word"]).lower()
            b = items[k][0].value
            if op in ("+", "plus"):
                value += b
            elif op in ("-", "−", "minus", "less"):
                value -= b
            elif op in ("x", "×", "*", "times"):
                value *= b
            elif b:
                value /= b
            how, used = f"{how} {op} {items[k][0].raw}", [*used, items[k][1]]
            out.append((value, how, tuple(used)))
    return out


def _pairs(target, operands):
    """Values two of a sentence's other numbers produce: a sum, a difference, a ratio or a change."""
    money = [o for o in operands if o[0].group == "money"]
    for i, (a, va) in enumerate(money):
        for j, (b, vb) in enumerate(money):
            if i == j:
                continue
            if target.group == "money":
                if i < j:
                    yield a.value + b.value, f"{a.raw} + {b.raw}", (va, vb)
                yield a.value - b.value, f"{a.raw} - {b.raw}", (va, vb)
            elif target.kind == "percent" and b.value:
                yield a.value / b.value * 100, f"{a.raw} / {b.raw}", (va, vb)
                yield (a.value / b.value - 1) * 100, f"change from {b.raw} to {a.raw}", (va, vb)
            elif target.kind == "multiple" and b.value:
                yield a.value / b.value, f"{a.raw} / {b.raw}", (va, vb)


def _formula_matches(q, value: float) -> bool:
    """A written formula's result states `q`: as itself, or as a percent when the formula is a ratio."""
    return close(q, value) or (q.kind == "percent" and close(q, value * 100))


def _judge(q, v, how, used):
    if any(x.status == "wrong" and "built on" not in x.path and " = " not in x.path[:12] for x in used):
        return Verdict(q.raw, "wrong", f"{q.raw} = {how}, built on a wrong number")
    if all(x.status in ("matched", "derived") for x in used):
        return Verdict(q.raw, "derived", f"{q.raw} = {how}, from verified numbers")
    return Verdict(q.raw, "weak", f"{q.raw} = {how}, from numbers only present")


def own_arithmetic(items, groups, formulas):
    """A number no fact keys, checked against arithmetic the document wrote out, then against pairs of the
    other numbers in its own sentence or table row: derived when the inputs are verified, wrong when one is
    wrong, weak when they are only present."""
    out = []
    for n, (q, v) in enumerate(items):
        if v.status not in ("weak", "unsupported") or q.temporal:
            out.append((q, v))
            continue
        hit = next(((how, used) for value, how, used in formulas
                    if _formula_matches(q, value) and v not in used), None)
        if hit is None:
            operands = [(o, ov) for m, (o, ov) in enumerate(items) if m != n and groups[m] == groups[n]
                        and not o.temporal]
            hit = next(((how, used) for value, how, used in _pairs(q, operands) if close(q, value)), None)
        out.append((q, _judge(q, v, *hit) if hit else v))
    return out


def check_document(text: str, graph: Graph, presence: ev.Evidence, end: date) -> dict[int, list]:
    """Verdicts per line, in the order its numbers appear: table cells by row and column (a row or cell that
    combines two metrics split apart, a unit stated for the document applied), prose by sentence, then
    arithmetic the document wrote out and pairs within a sentence or row."""
    lines = text.split("\n")
    per_line: dict[int, tuple[list, list]] = {}
    header, millions = None, False
    for n, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            header = None
            millions = millions or bool(DOC_MILLIONS.search(line))
            if not stripped:
                per_line[n] = ([], [])
                continue
            protected = expand(line).replace("U.S. ", "U.S.​")
            verdicts = [v for _, v in check(line, graph, presence, end) if v.status != "skipped"]
            qs = [q for q in numbers.find(protected) if not q.temporal]
            bounds, pos = [], 0
            for sentence in numbers.sentences(protected):
                pos = protected.find(sentence, pos)
                bounds.append(pos + len(sentence))
            groups = [next((i for i, b in enumerate(bounds) if q.start < b), len(bounds)) for q in qs]
            per_line[n] = (list(zip(qs, verdicts, strict=False)), groups, protected)
            continue
        if header is None:
            header = _cells(stripped)
            per_line[n] = ([], [])
            continue
        if set(stripped) <= set("|-: "):
            per_line[n] = ([], [])
            continue
        keyed = []
        for sentence, (col, part) in table_sentences(header, _cells(stripped), millions):
            verdicts = [v for _, v in check(sentence, graph, presence, end) if v.status != "skipped"]
            qs = [q for q in numbers.find(expand(sentence)) if not q.temporal]
            keyed += [((col, part, j), q, v) for j, (q, v) in enumerate(zip(qs, verdicts, strict=False))]
        keyed.sort(key=lambda x: x[0])
        per_line[n] = ([(q, v) for _, q, v in keyed], [0] * len(keyed))
    formulas = [f for entry in per_line.values() if len(entry) == 3 for f in written_formulas(entry[2], entry[0])]
    return {n: own_arithmetic(entry[0], entry[1], formulas) for n, entry in per_line.items()}
