#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import date
from pathlib import Path


KB_PATH = Path("knowledge/term_kb.json")

PLACEHOLDER_PHRASES = [
    "当前条目用于保证知识链路可点击",
    "后续可继续补充",
    "这个坑先占住",
    "经典相关论文。",
    "TODO",
    "placeholder",
]


def is_placeholder(value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return True
    return any(phrase in text for phrase in PLACEHOLDER_PHRASES)


def term_label(term: dict) -> tuple[str, str, str]:
    name = term.get("term", "")
    en = term.get("termEn") or term.get("fullNameEn") or name
    zh = term.get("termZh") or term.get("fullNameZh") or name
    return name, en, zh


def fill_term(term: dict) -> int:
    changed = 0
    name, en, zh = term_label(term)
    category = term.get("category") or "AI 与计算机科学"
    prereqs = [p for p in term.get("prerequisiteTerms", []) or [] if p]
    related = [r for r in term.get("relatedTerms", []) or [] if r]
    prereq_text = "、".join(prereqs[:3]) if prereqs else "线性代数、概率统计或基础编程直觉"
    related_text = "、".join(related[:3]) if related else "相邻模型、算法或工程实践"

    explanation_zh = (
        f"{zh}（{en}）是{category}中常见的学习节点。理解它时可以先抓住三个问题："
        f"它解决什么问题、依赖哪些输入或假设、在论文的方法或实验里怎样被验证。"
        f"阅读相关论文时，建议先补 {prereq_text}，再比较它和{related_text}的区别。"
    )
    explanation_en = (
        f"{en} is a concept in {category}. A useful reading strategy is to identify the problem it addresses, "
        "the assumptions or inputs it relies on, and how a paper validates it through methods or experiments."
    )
    academic_zh = (
        f"从学术阅读角度看，{zh}通常可以放在“问题定义—方法机制—实验验证—局限讨论”的链条中理解。"
        f"它与{related_text}之间的关系，往往体现为建模假设、优化目标、表示方式或系统取舍的差异。"
        "初学者不必先记住所有公式，先能在论文中定位它出现的位置和作用，再逐步补齐形式化定义。"
    )
    note = (
        f"{zh}先别背定义，先问自己：它在这篇论文里帮作者解决了什么卡点？"
        "能回答这个问题，再看公式和实验会轻松很多。"
    )

    replacements = {
        "explanation": explanation_zh,
        "explanationZh": explanation_zh,
        "explanationEn": explanation_en,
        "academicExplanationZh": academic_zh,
        "hoshinoNote": note,
    }
    for field, value in replacements.items():
        if is_placeholder(term.get(field, "")):
            term[field] = value
            changed += 1

    for paper in term.get("landmarkPapers", []) or []:
        if is_placeholder(paper.get("shortDesc", "")):
            paper["shortDesc"] = (
                f"这篇论文与 {name} 相关，适合用来观察该概念在真实研究中的问题设定、方法设计和实验验证。"
            )
            changed += 1
    return changed


def main() -> None:
    kb = json.loads(KB_PATH.read_text(encoding="utf-8"))
    changed = sum(fill_term(term) for term in kb.get("terms", []))
    kb["lastUpdated"] = date.today().isoformat()
    KB_PATH.write_text(json.dumps(kb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Filled placeholder fields: {changed}")


if __name__ == "__main__":
    main()
