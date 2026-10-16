"""Turn whatever a person types ("herd football", "lambos", "big red machine") into topics.

No external service: aliases from topics.json, token overlap, and difflib for typos.
Anything that doesn't match well becomes a topic request that waits for research.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher

from .content import Library

STOPWORDS = {"the", "a", "an", "of", "and", "about", "trivia", "history", "facts", "fact", "stuff", "questions", "i", "like", "love", "my"}
STRONG = 0.8   # confident enough to add with one tap
WEAK = 0.5     # show as "Did you mean...?"


def normalize(text: str) -> str:
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return " ".join(w for w in text.split() if w not in STOPWORDS)


def _score(query: str, phrase: str) -> float:
    q, p = normalize(query), normalize(phrase)
    if not q or not p:
        return 0.0
    if q == p:
        return 1.0
    qt, pt = set(q.split()), set(p.split())
    overlap = len(qt & pt) / len(qt | pt)
    contained = 0.9 if (f" {p} " in f" {q} " or f" {q} " in f" {p} ") else 0.0
    fuzzy = SequenceMatcher(None, q, p).ratio()
    return max(overlap, contained, fuzzy * 0.95)


def match(lib: Library, text: str, limit: int = 3) -> list[dict]:
    """Best topic matches for free text, deepest first on ties (niche wins)."""
    scored = []
    for t in lib.topics.values():
        best = max(_score(text, phrase) for phrase in [t.name, *t.aliases])
        if best >= WEAK:
            scored.append((best, lib.depth(t.id), t))
    scored.sort(key=lambda s: (-round(s[0], 2), -s[1]))
    out = []
    for score, depth, t in scored[:limit]:
        out.append({
            "id": t.id, "name": t.name, "score": round(score, 2), "depth": depth,
            "path": [lib.topics[x].name for x in lib.lineage(t.id)],
            "questions": lib.count(t.id), "soon": t.soon,
            "confident": score >= STRONG,
        })
    return out


def suggest_deeper(lib: Library, topic_id: str) -> list[dict]:
    """Children worth offering after someone picks a topic ("Go deeper")."""
    t = lib.topics[topic_id]
    return [{"id": k, "name": lib.topics[k].name, "questions": lib.count(k), "soon": lib.topics[k].soon}
            for k in t.kids]


def tree(lib: Library) -> list[dict]:
    def node(tid):
        t = lib.topics[tid]
        return {"id": t.id, "name": t.name, "depth": lib.depth(t.id), "soon": t.soon,
                "questions": lib.count(t.id), "kids": [node(k) for k in t.kids]}
    return [node(r) for r in lib.roots]
