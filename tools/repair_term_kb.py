#!/usr/bin/env python3
import json
from pathlib import Path


KB_PATH = Path("knowledge/term_kb.json")
DEFAULT_PAPER_DESC = "经典相关论文。"


def normalize(value: str) -> str:
    return value.strip().lower()


def make_stub_term(name: str) -> dict:
    return {
        "term": name,
        "fullName": name,
        "category": "基础概念",
        "difficulty": 1,
        "aliases": [],
        "explanation": f"{name} 是理解 AI 论文时经常遇到的基础概念。当前条目用于保证知识链路可点击，后续可继续补充更完整解释。",
        "hoshinoNote": f"{name} 这个坑先占住了っす，后面大叔再慢慢补详细讲解。",
        "prerequisiteTerms": [],
        "landmarkPapers": [],
        "relatedTerms": [],
    }


def main() -> None:
    kb = json.loads(KB_PATH.read_text(encoding="utf-8"))
    terms = kb.get("terms", [])

    term_keys = {normalize(t["term"]) for t in terms if t.get("term")}
    alias_owner: dict[str, str] = {}

    for term in terms:
        term["difficulty"] = term.get("difficulty") if isinstance(term.get("difficulty"), int) and 1 <= term.get("difficulty") <= 5 else 1

        cleaned_aliases = []
        seen_local = set()
        for alias in term.get("aliases", []) or []:
            if not isinstance(alias, str) or not alias.strip():
                continue
            alias = alias.strip()
            alias_key = normalize(alias)
            term_key = normalize(term["term"])
            if alias_key == term_key or alias_key in term_keys or alias_key in alias_owner or alias_key in seen_local:
                continue
            seen_local.add(alias_key)
            alias_owner[alias_key] = term["term"]
            cleaned_aliases.append(alias)
        term["aliases"] = cleaned_aliases

        for paper in term.get("landmarkPapers", []) or []:
            for field in ["title", "authors", "year"]:
                paper.setdefault(field, "")
            if not paper.get("shortDesc"):
                paper["shortDesc"] = DEFAULT_PAPER_DESC

    known = {normalize(t["term"]) for t in terms if t.get("term")}
    known |= {normalize(alias) for t in terms for alias in t.get("aliases", []) or []}

    missing_prereqs = sorted({
        ref.strip()
        for term in terms
        for ref in term.get("prerequisiteTerms", []) or []
        if isinstance(ref, str) and ref.strip() and normalize(ref) not in known
    })
    for ref in missing_prereqs:
        terms.append(make_stub_term(ref))
        known.add(normalize(ref))

    for term in terms:
        related_tags = list(term.get("relatedTags", []) or [])
        cleaned_related = []
        seen_related = set()
        for ref in term.get("relatedTerms", []) or []:
            if not isinstance(ref, str) or not ref.strip():
                continue
            ref = ref.strip()
            ref_key = normalize(ref)
            if ref_key in known:
                if ref_key not in seen_related:
                    cleaned_related.append(ref)
                    seen_related.add(ref_key)
            elif ref not in related_tags:
                related_tags.append(ref)
        term["relatedTerms"] = cleaned_related
        if related_tags:
            term["relatedTags"] = related_tags
        elif "relatedTags" in term:
            del term["relatedTags"]

    kb["terms"] = terms
    KB_PATH.write_text(json.dumps(kb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Repaired term KB: {len(terms)} terms, added {len(missing_prereqs)} prerequisite stubs")


if __name__ == "__main__":
    main()
