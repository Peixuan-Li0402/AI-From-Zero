import json
import re
from collections import defaultdict

from .config import KNOWLEDGE_DIR


TERM_KB_PATH = KNOWLEDGE_DIR / "term_kb.json"


def normalize_key(value: str) -> str:
    return value.strip().lower()


def load_term_kb() -> dict:
    return json.loads(TERM_KB_PATH.read_text(encoding="utf-8"))


term_kb = load_term_kb()
terms = term_kb["terms"]
terms_by_name = {normalize_key(t["term"]): t for t in terms}
terms_index: dict[str, dict] = {}
for term in terms:
    terms_index[normalize_key(term["term"])] = term
    for alias in term.get("aliases", []):
        if isinstance(alias, str) and alias.strip():
            terms_index.setdefault(normalize_key(alias), term)


def is_known_term(value: str) -> bool:
    return normalize_key(value) in terms_index


def get_term(term_name: str) -> dict | None:
    return terms_index.get(normalize_key(term_name))


def _is_ascii_word(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_+.#-]+", value))


def _contains_alias(text: str, alias: str) -> bool:
    alias = alias.strip()
    if not alias:
        return False
    if _is_ascii_word(alias):
        return re.search(rf"(?<![A-Za-z0-9_]){re.escape(alias)}(?![A-Za-z0-9_])", text, re.IGNORECASE) is not None
    return alias.lower() in text.lower()


def extract_terms_from_text(text: str) -> list[dict]:
    found: list[dict] = []
    for term in terms:
        names = [term["term"], *term.get("aliases", [])]
        if any(isinstance(name, str) and _contains_alias(text, name) for name in names):
            found.append(term)

    seen = set()
    unique = []
    for term in found:
        key = term["term"]
        if key not in seen:
            seen.add(key)
            unique.append(term)
    unique.sort(key=lambda x: (x.get("difficulty", 5), x.get("term", "")))
    return unique


def serialize_term(term: dict) -> dict:
    return {
        "term": term["term"],
        "termEn": term.get("termEn", term["term"]),
        "termZh": term.get("termZh", term.get("fullName", term["term"])),
        "fullName": term.get("fullName", ""),
        "fullNameEn": term.get("fullNameEn", ""),
        "fullNameZh": term.get("fullNameZh", ""),
        "category": term.get("category", ""),
        "difficulty": term.get("difficulty", 5),
        "aliases": term.get("aliases", []),
        "aliasesEn": term.get("aliasesEn", []),
        "aliasesZh": term.get("aliasesZh", []),
        "explanation": term.get("explanation", ""),
        "explanationEn": term.get("explanationEn", ""),
        "explanationZh": term.get("explanationZh", term.get("explanation", "")),
        "academicExplanationZh": term.get("academicExplanationZh", ""),
        "hoshinoNote": term.get("hoshinoNote", ""),
        "landmarkPapers": term.get("landmarkPapers", []),
        "prerequisiteTerms": term.get("prerequisiteTerms", []),
        "relatedTerms": term.get("relatedTerms", []),
        "relatedTags": term.get("relatedTags", []),
        "conceptChain": concept_chain_for_term(term),
    }


def concept_chain_for_term(term: dict) -> dict:
    name = term.get("term", "")
    prereqs = [item for item in term.get("prerequisiteTerms", [])[:5] if item]
    related = [item for item in term.get("relatedTerms", [])[:5] if item]
    nodes = [
        *[{"term": item, "role": "prerequisite", "label": "前置知识"} for item in prereqs],
        {"term": name, "role": "current", "label": "当前概念"},
        *[{"term": item, "role": "related", "label": "延伸概念"} for item in related],
    ]
    return {
        "term": name,
        "nodes": nodes,
        "learningOrder": [node["term"] for node in nodes],
        "hint": f"建议先补 {', '.join(prereqs[:3])}，再回到论文中看 {name} 的具体用法。" if prereqs else f"先建立 {name} 的直觉，再顺着相关概念继续扩展。",
    }


def list_terms_by_category() -> dict:
    categories = defaultdict(list)
    for term in terms:
        categories[term.get("category", "其他")].append({
            "term": term["term"],
            "termEn": term.get("termEn", term["term"]),
            "termZh": term.get("termZh", term.get("fullName", term["term"])),
            "fullName": term.get("fullName", ""),
            "fullNameEn": term.get("fullNameEn", ""),
            "fullNameZh": term.get("fullNameZh", ""),
            "difficulty": term.get("difficulty", 5),
        })
    return {
        "version": term_kb["version"],
        "total": len(terms),
        "categories": dict(categories),
    }


def related_papers_for_term(info: dict) -> list[dict]:
    papers = []
    seen = set()

    def add_paper(paper: dict, why: str):
        title = str(paper.get("title", "")).strip()
        if not title or title.lower() in seen:
            return
        seen.add(title.lower())
        papers.append({
            "title": title,
            "authors": paper.get("authors", ""),
            "year": paper.get("year", ""),
            "shortDesc": paper.get("shortDesc", ""),
            "whyRelated": why,
        })

    for paper in info.get("landmarkPapers", []):
        add_paper(paper, f"{info['term']} 的经典溯源论文")

    for related_name in info.get("relatedTerms", []):
        related = get_term(str(related_name))
        if not related:
            continue
        for paper in related.get("landmarkPapers", []):
            add_paper(paper, f"来自相关概念：{related.get('term', related_name)}")

    return papers[:12]
