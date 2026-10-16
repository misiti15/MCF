"""Load the topic tree and question bank, and check every question meets the accuracy rules.

Run `python -m trivia.content check` before committing content.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from . import config

STATUSES = ("draft", "verified", "flagged", "retired")


@dataclass
class Topic:
    id: str
    name: str
    parent: str | None
    aliases: list[str] = field(default_factory=list)
    kids: list[str] = field(default_factory=list)
    soon: bool = False


@dataclass
class Library:
    topics: dict[str, Topic]
    roots: list[str]
    questions: dict[str, dict]
    packs: list[dict]

    def lineage(self, topic_id: str) -> list[str]:
        """Root-first path to a topic, including itself."""
        path = []
        while topic_id:
            path.append(topic_id)
            topic_id = self.topics[topic_id].parent
        return path[::-1]

    def depth(self, topic_id: str) -> int:
        return len(self.lineage(topic_id)) - 1

    def under(self, topic_ids) -> set[str]:
        """All topic ids at or below any of the given topics."""
        out, stack = set(), list(topic_ids)
        while stack:
            t = stack.pop()
            if t in self.topics and t not in out:
                out.add(t)
                stack.extend(self.topics[t].kids)
        return out

    def servable(self, q: dict) -> bool:
        if q["status"] == "verified":
            return True
        return q["status"] == "draft" and config.SERVE_DRAFTS

    def questions_for(self, topic_ids) -> list[dict]:
        scope = self.under(topic_ids)
        return [q for q in self.questions.values() if q["topic"] in scope and self.servable(q)]

    def count(self, topic_id: str) -> int:
        return len(self.questions_for([topic_id]))


def _walk(nodes, parent, topics, problems):
    for n in nodes:
        if n["id"] in topics:
            problems.append(f"duplicate topic id {n['id']}")
        topics[n["id"]] = Topic(n["id"], n["name"], parent, n.get("aliases", []),
                                [k["id"] for k in n.get("kids", [])], bool(n.get("soon")))
        _walk(n.get("kids", []), n["id"], topics, problems)


def validate_question(q: dict, topics: dict[str, Topic]) -> list[str]:
    """Return a list of problems. Empty list = the question may ship."""
    p, qid = [], q.get("id", "?")
    for key in ("id", "topic", "level", "question", "options", "answer", "explanation", "tidbit", "source", "status"):
        if key not in q or q[key] in (None, ""):
            p.append(f"{qid}: missing {key}")
    if p:
        return p
    if q["topic"] not in topics:
        p.append(f"{qid}: unknown topic {q['topic']}")
    if q["level"] not in config.LEVEL_POINTS:
        p.append(f"{qid}: level must be 1-4")
    opts = q["options"]
    if len(opts) != 4:
        p.append(f"{qid}: needs exactly 4 options")
    if len({o.strip().lower() for o in opts}) != len(opts):
        p.append(f"{qid}: duplicate options")
    if not isinstance(q["answer"], int) or not 0 <= q["answer"] < len(opts):
        p.append(f"{qid}: answer index out of range")
    src = q["source"]
    url = urlparse(src.get("url", ""))
    if url.scheme != "https" or not url.netloc:
        p.append(f"{qid}: source url must be https")
    if not src.get("title"):
        p.append(f"{qid}: source needs a title")
    if q["status"] not in STATUSES:
        p.append(f"{qid}: status must be one of {STATUSES}")
    if q["status"] == "verified" and not src.get("checked"):
        p.append(f"{qid}: verified questions need source.checked (date a person checked it)")
    if q["status"] == "verified" and not src.get("excerpt"):
        p.append(f"{qid}: verified questions need source.excerpt (the passage that proves the answer)")
    if q.get("time_sensitive") and not q.get("as_of"):
        p.append(f"{qid}: time-sensitive facts need an as_of date")
    return p


def load(content_dir: Path | None = None) -> tuple[Library, list[str]]:
    d = Path(content_dir or config.CONTENT_DIR)
    tdoc = json.loads((d / "topics.json").read_text())
    qdoc = json.loads((d / "questions.json").read_text())
    problems: list[str] = []
    topics: dict[str, Topic] = {}
    _walk(tdoc["topics"], None, topics, problems)
    questions = {}
    for q in qdoc["questions"]:
        if q.get("id") in questions:
            problems.append(f"duplicate question id {q['id']}")
        problems += validate_question(q, topics)
        questions[q.get("id")] = q
    for pack in tdoc.get("packs", []):
        for t in pack["topics"]:
            if t not in topics:
                problems.append(f"pack {pack['id']}: unknown topic {t}")
    lib = Library(topics, [n["id"] for n in tdoc["topics"]], questions, tdoc.get("packs", []))
    return lib, problems


@lru_cache(maxsize=1)
def library() -> Library:
    lib, problems = load()
    if problems:
        raise ValueError("content problems:\n" + "\n".join(problems))
    return lib


def main(argv=None) -> int:
    lib, problems = load()
    drafts = sum(q["status"] == "draft" for q in lib.questions.values())
    for p in problems:
        print("ERROR", p)
    print(f"{len(lib.questions)} questions, {len(lib.topics)} topics, {drafts} still draft (sources not yet checked by a person)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
