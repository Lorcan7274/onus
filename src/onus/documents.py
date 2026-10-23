"""Read the document being checked into blocks: one per text frame,
paragraph, or table cell, each with a location a reader can find. Pictures
are collected alongside, for the model to transcribe (images.py)."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

# A block that is only a short number is a page number or a list marker.
_BARE_NUMBER = re.compile(r"^\s*\d{1,3}\s*$")


@dataclass(frozen=True)
class Block:
    id: int
    label: str  # "slide 3", "paragraph 12", "line 40"
    text: str


@dataclass(frozen=True)
class Figure:
    label: str  # the slide or paragraph it sits on, as a Block's label
    ordinal: int
    data: bytes
    media_type: str
    width: int  # as placed on the page, in EMU
    height: int

    @property
    def location(self) -> str:
        return f"{self.label} (image {self.ordinal})"


@dataclass
class Document:
    path: Path
    format: str
    blocks: list[Block]
    figures: list[Figure] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(b.text for b in self.blocks)

    def extend(self, items: Iterable[tuple[str, str]]) -> None:
        seen = {(b.label, b.text) for b in self.blocks}
        for label, text in items:
            text = " ".join(text.split())
            if not text or _BARE_NUMBER.match(text):
                continue
            if (label, text) in seen:  # a slide repeats its eyebrow, a table its header
                continue
            seen.add((label, text))
            self.blocks.append(Block(len(self.blocks), label, text))


def _shapes(shapes):
    from pptx.shapes.group import GroupShape

    for shape in shapes:
        if isinstance(shape, GroupShape):
            yield from _shapes(shape.shapes)
        else:
            yield shape


def _pptx(path: Path) -> tuple[list[tuple[str, str]], list[Figure]]:
    from pptx import Presentation
    from pptx.shapes.picture import Picture

    texts: list[tuple[str, str]] = []
    figures: list[Figure] = []
    for n, slide in enumerate(Presentation(str(path)).slides, start=1):
        pictures = 0
        for shape in _shapes(slide.shapes):
            if isinstance(shape, Picture):
                pictures += 1
                try:
                    image = shape.image
                except KeyError:  # a linked picture has no bytes in the file
                    continue
                figures.append(Figure(f"slide {n}", pictures, image.blob, image.content_type,
                                      shape.width, shape.height))
                continue
            frames = []
            if shape.has_text_frame:
                frames = [shape.text_frame]
            elif getattr(shape, "has_table", False) and shape.has_table:
                frames = [c.text_frame for row in shape.table.rows for c in row.cells]
            for frame in frames:
                for paragraph in frame.text.split("\n"):
                    texts.append((f"slide {n}", paragraph))
    return texts, figures


def _docx(path: Path) -> tuple[list[tuple[str, str]], list[Figure]]:
    import docx

    d = docx.Document(str(path))
    texts: list[tuple[str, str]] = []
    figures: list[Figure] = []
    for i, p in enumerate(d.paragraphs, start=1):
        texts.append((f"paragraph {i}", p.text))
        pictures = 0
        for drawing in p._p.xpath(".//w:drawing"):
            rids = drawing.xpath(".//a:blip/@r:embed")
            if not rids:  # a native chart or SmartArt, not a picture
                continue
            pictures += 1
            part = d.part.related_parts[rids[0]]
            cx, cy = (int(v[0]) if v else 0 for v in (drawing.xpath(f".//wp:extent/@{a}") for a in ("cx", "cy")))
            figures.append(Figure(f"paragraph {i}", pictures, part.blob, part.content_type, cx, cy))
    for t, table in enumerate(d.tables, start=1):
        for row in table.rows:
            for cell in row.cells:
                texts.append((f"table {t}", cell.text))
    return texts, figures


def _text(path: Path) -> tuple[list[tuple[str, str]], list[Figure]]:
    return [(f"line {i}", line) for i, line in enumerate(path.read_text().splitlines(), start=1)], []


READERS = {".pptx": _pptx, ".docx": _docx, ".md": _text, ".txt": _text, ".markdown": _text}


def load(path: str | Path) -> Document:
    path = Path(path)
    reader = READERS.get(path.suffix.lower())
    if reader is None:
        raise ValueError(f"{path.name}: unsupported format (onus reads {', '.join(sorted(READERS))})")
    texts, figures = reader(path)
    doc = Document(path, path.suffix.lower().lstrip("."), [], figures)
    doc.extend(texts)
    return doc
