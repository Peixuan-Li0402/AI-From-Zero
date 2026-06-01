#!/usr/bin/env python3
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


REQUIRED_TERM_FIELDS = [
    "term",
    "fullName",
    "category",
    "difficulty",
    "explanation",
    "termEn",
    "termZh",
    "fullNameEn",
    "fullNameZh",
    "aliasesEn",
    "aliasesZh",
    "explanationEn",
    "explanationZh",
    "academicExplanationZh",
]
REQUIRED_PAPER_FIELDS = ["title", "authors", "year", "shortDesc"]


def normalize(value: str) -> str:
    return value.strip().lower()


def main() -> int:
    kb_path = Path("knowledge/term_kb.json")
    kb = json.loads(kb_path.read_text(encoding="utf-8"))
    terms = kb.get("terms", [])
    issues: dict[str, list] = defaultdict(list)

    term_names = [t.get("term", "") for t in terms]
    term_counter = Counter(normalize(t) for t in term_names if t)
    for key, count in term_counter.items():
        if count > 1:
            issues["duplicate_terms"].append(key)

    alias_owner = {}
    known_names = set(term_counter)
    for term in terms:
        term_key = normalize(term.get("term", ""))
        for field in REQUIRED_TERM_FIELDS:
            if field not in term or term.get(field) in (None, ""):
                issues["missing_term_fields"].append([term.get("term", ""), field])
        if not isinstance(term.get("aliasesEn", []), list) or not isinstance(term.get("aliasesZh", []), list):
            issues["invalid_bilingual_fields"].append([term.get("term", ""), "aliases"])
        if not any("\u4e00" <= ch <= "\u9fff" for ch in str(term.get("explanationZh", ""))):
            issues["invalid_bilingual_fields"].append([term.get("term", ""), "explanationZh"])
        if not any("a" <= ch.lower() <= "z" for ch in str(term.get("explanationEn", ""))):
            issues["invalid_bilingual_fields"].append([term.get("term", ""), "explanationEn"])
        difficulty = term.get("difficulty")
        if not isinstance(difficulty, int) or not 1 <= difficulty <= 5:
            issues["invalid_difficulty"].append([term.get("term", ""), difficulty])

        for alias in term.get("aliases", []) or []:
            if not isinstance(alias, str) or not alias.strip():
                continue
            alias_key = normalize(alias)
            if alias_key == term_key:
                issues["self_aliases"].append([term.get("term", ""), alias])
            elif alias_key in alias_owner:
                issues["duplicate_aliases"].append([alias, alias_owner[alias_key], term.get("term", "")])
            elif alias_key in known_names:
                issues["alias_conflicts_with_terms"].append([term.get("term", ""), alias])
            else:
                alias_owner[alias_key] = term.get("term", "")

    known = set(term_counter) | set(alias_owner)
    for term in terms:
        name = term.get("term", "")
        for ref in term.get("prerequisiteTerms", []) or []:
            if not isinstance(ref, str) or normalize(ref) not in known:
                issues["broken_prerequisite_terms"].append([name, ref])
        for ref in term.get("relatedTerms", []) or []:
            if not isinstance(ref, str) or normalize(ref) not in known:
                issues["broken_related_terms"].append([name, ref])
        for paper in term.get("landmarkPapers", []) or []:
            for field in REQUIRED_PAPER_FIELDS:
                if paper.get(field) in (None, "", []):
                    issues["missing_paper_fields"].append([name, paper.get("title", ""), field])

    if issues:
        print(json.dumps(issues, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps({
        "status": "ok",
        "terms": len(terms),
        "categories": len({t.get("category", "") for t in terms}),
        "version": kb.get("version"),
        "lastUpdated": kb.get("lastUpdated"),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
