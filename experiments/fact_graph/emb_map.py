"""Rank a filing's facts by how closely their labels mean what a claim's words say."""
import re

import numpy as np

STRIP = re.compile(r"[$\d.,%()-]+|\b(?:million|billion|thousand|was|were|is|the|a|an|of|in|at|to|for|from|"
                   r"quarter|year|years|first|half|end|ended|six|months|2024|2025|compared|year-over-year|"
                   r"fell|rose|grew|declined|decreased|increased|reached|totaled|came|stood|consumed|improved|"
                   r"widened|narrowed|nearly|doubled|about|approximately|roughly)\b", re.I)


def describe(fact, segments: dict) -> str:
    """A fact as words: its row label, its concept's name and the segments it belongs to."""
    concept = re.sub(r"([a-z])([A-Z])", r"\1 \2", fact.concept.split(":")[-1])
    seg = " ".join(segments.get(m, "") for m in fact.members)
    return " ".join(f"{seg} {fact.label} ({concept})".split())


class Mapper:
    def __init__(self, model_name: str, segments: dict):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name, device="cpu")
        self.segments = segments
        self._cache: dict[str, np.ndarray] = {}

    def _embed(self, texts):
        todo = [t for t in dict.fromkeys(texts) if t not in self._cache]
        if todo:
            for t, v in zip(todo, self.model.encode(todo, normalize_embeddings=True, batch_size=64), strict=True):
                self._cache[t] = v
        return np.stack([self._cache[t] for t in texts])

    def phrase(self, window: str) -> str:
        return " ".join(STRIP.sub(" ", window).split())

    def rank(self, window: str, facts: list) -> list[tuple[float, object]]:
        phrase = self.phrase(window)
        if not phrase or not facts:
            return []
        descs = [describe(f, self.segments) for f in facts]
        sims = self._embed(descs) @ self._embed([phrase])[0]
        return sorted(zip(sims.tolist(), facts, strict=True), key=lambda x: -x[0])
