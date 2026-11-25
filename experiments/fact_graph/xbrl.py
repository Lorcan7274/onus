"""Inline XBRL facts from a filing, each with its period, segment, scale, sign and the row label it sits beside."""
import re
from dataclasses import dataclass
from datetime import date, datetime
from html import unescape


@dataclass(frozen=True)
class Fact:
    concept: str
    value: float          # signed, in units (dollars, shares, pure)
    decimals: int | None
    unit: str
    start: date | None
    end: date
    members: tuple[str, ...]  # segment dimension members; () is the whole company
    label: str            # the table row's first cell, or the sentence around it

    @property
    def months(self) -> int:
        if self.start is None:
            return 0
        return round(((self.end - self.start).days + 1) / 30.4)

    @property
    def words(self) -> str:
        name = re.sub(r"([a-z])([A-Z])", r"\1 \2", self.concept.split(":")[-1])
        return f"{self.label} {name}"


def _text(html: str) -> str:
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", html)).split())


def _date(s: str) -> date:
    return date.fromisoformat(s.strip())


NUMBER_WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
    "seventeen eighteen nineteen twenty".split())} | {"no": 0, "none": 0, "thirty": 30, "forty": 40, "fifty": 50,
                                                      "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}


def _number_word(text: str) -> float:
    """A number written in words, "four" or "twenty-one"; one not written so is 0, as a nil fact is."""
    parts = re.split(r"[-\s]+", text.lower().strip())
    return float(sum(NUMBER_WORDS.get(p, 0) for p in parts))


def _facts(s: str):
    """Each fact tag as (attributes, start, inner HTML), a tag nested inside another included."""
    stack = []
    for m in re.finditer(r"<ix:nonFraction\b([^>]*?)(/?)>|</ix:nonFraction>", s):
        if m.group(0).startswith("</"):
            attrs, start, inner = stack.pop()
            yield attrs, start, s[inner:m.start()]
        elif m.group(2):
            yield m.group(1), m.start(), ""
        else:
            stack.append((m.group(1), m.start(), m.end()))


def period_end(path: str) -> date:
    """The end of the period a filing reports on, from its cover page."""
    s = open(path, encoding="utf-8", errors="replace").read()
    text = _text(re.search(r'name="dei:DocumentPeriodEndDate"[^>]*>(.*?)</ix:nonNumeric>', s, re.S).group(1))
    return datetime.strptime(text, "%B %d, %Y").date()


def load(path: str) -> list[Fact]:
    s = open(path, encoding="utf-8", errors="replace").read()
    contexts = {}
    for m in re.finditer(r'<xbrli:context id="([^"]+)">(.*?)</xbrli:context>', s, re.S):
        body = m.group(2)
        members = tuple(sorted(re.findall(r"<xbrldi:explicitMember[^>]*>([^<]+)<", body)))
        if (inst := re.search(r"<xbrli:instant>([^<]+)<", body)):
            contexts[m.group(1)] = (None, _date(inst.group(1)), members)
        else:
            a = re.search(r"<xbrli:startDate>([^<]+)<", body).group(1)
            b = re.search(r"<xbrli:endDate>([^<]+)<", body).group(1)
            contexts[m.group(1)] = (_date(a), _date(b), members)
    units = {m.group(1): _text(m.group(2))
             for m in re.finditer(r'<xbrli:unit id="([^"]+)">(.*?)</xbrli:unit>', s, re.S)}
    facts = []
    for attrs, at, html in _facts(s):
        inner = _text(html)
        def get(k, attrs=attrs):
            return (re.search(rf'\b{k}="([^"]*)"', attrs) or [None, None])[1]
        if "numwords" in (get("format") or ""):
            value = _number_word(inner) * 10 ** int(get("scale") or 0)
        elif not re.search(r"\d", inner):
            value = 0.0
        else:
            value = float(inner.replace(",", "")) * 10 ** int(get("scale") or 0)
        if get("sign") == "-":
            value = -value
        start, end, members = contexts[get("contextRef")]
        # the row label: the first cell of the <tr> holding the fact, else the sentence around it
        tr_start = s.rfind("<tr", 0, at)
        tr_end = s.find("</tr>", at)
        row = s[tr_start:tr_end] if 0 <= tr_start and s.rfind("</tr>", 0, at) < tr_start else ""
        if row:
            cells = [_text(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
            label = next((c for c in cells if c and not re.fullmatch(r"[\s$()%,.\d—-]*", c)), "")
        else:
            chunk = s[max(0, at - 600):at]
            close, open_ = chunk.find(">"), chunk.find("<")
            if close != -1 and (open_ == -1 or close < open_):
                chunk = chunk[close + 1:]  # the window began inside a tag
            left = _text(chunk)
            label = re.split(r"(?<=[.;])\s", left)[-1][-200:]
        dec = get("decimals")
        facts.append(Fact(get("name"), value, None if dec in (None, "INF") else int(dec),
                          units.get(get("unitRef"), ""), start, end, members, label))
    return facts


if __name__ == "__main__":
    import sys
    fs = load(sys.argv[1])
    print(len(fs), "facts")
    for f in fs[:20]:
        print(f.concept, f.start, f.end, f.members, f.value, "|", f.label[:60])
