from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .config import DATA_DIR
from .models import LearningSessionRequest
from .papers import enrich_paper_resource
from .terms import get_term, related_papers_for_term


PROGRESS_PATH = DATA_DIR / "learning_progress.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_progress() -> dict:
    return {
        "version": 1,
        "createdAt": _now(),
        "updatedAt": _now(),
        "masteredTerms": {},
        "seenTerms": {},
        "sessions": [],
    }


def _load_progress() -> dict:
    if not PROGRESS_PATH.exists():
        return _empty_progress()
    try:
        data = json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return _empty_progress()
    base = _empty_progress()
    base.update(data)
    return base


def _save_progress(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data["updatedAt"] = _now()
    PROGRESS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _term_name(item: dict | str) -> str:
    if isinstance(item, dict):
        return str(item.get("term") or item.get("termEn") or item.get("termZh") or "").strip()
    return str(item or "").strip()


def _term_info(item: dict | str) -> dict:
    name = _term_name(item)
    info = get_term(name) if name else None
    if info:
        return info
    return item if isinstance(item, dict) else {"term": name}


def _unique_terms(items: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for item in items:
        info = _term_info(item)
        name = _term_name(info)
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        result.append(info)
    result.sort(key=lambda term: (term.get("difficulty", 5), term.get("term", "")))
    return result


def get_learning_profile() -> dict:
    data = _load_progress()
    mastered = data.get("masteredTerms", {})
    seen = data.get("seenTerms", {})
    sessions = data.get("sessions", [])

    category_counter = Counter()
    weak_counter = Counter()
    concept_candidates = []
    for name, count in seen.items():
        info = get_term(name) or {"term": name, "category": "未分类", "difficulty": 3}
        category = info.get("category", "未分类")
        category_counter[category] += int(count or 0)
        if not mastered.get(name):
            weak_counter[category] += int(info.get("difficulty", 3) or 3)
            concept_candidates.append({
                "term": name,
                "category": category,
                "difficulty": info.get("difficulty", 3),
                "note": info.get("explanationZh") or info.get("explanation") or "",
                "nextStep": f"点开 {name} 的概念链条，先补前置知识，再回到论文方法段。",
            })

    mastered_count = sum(1 for value in mastered.values() if value)
    total_seen = len(seen)
    completion = round(mastered_count / total_seen * 100, 1) if total_seen else 0
    weak_areas = [
        {"category": category, "weight": weight}
        for category, weight in weak_counter.most_common(5)
    ]

    return {
        "updatedAt": data.get("updatedAt"),
        "sessionsTotal": len(sessions),
        "termsSeen": total_seen,
        "termsMastered": mastered_count,
        "completionRate": completion,
        "topCategories": [{"category": k, "count": v} for k, v in category_counter.most_common(6)],
        "weakAreas": weak_areas,
        "todayConceptNotes": concept_candidates[:6],
        "recentSessions": sessions[-5:][::-1],
    }


def build_reading_route(terms: list[dict], summary: str, source: str) -> list[dict]:
    top_terms = [term.get("term", "") for term in terms[:8] if term.get("term")]
    hard_terms = [term.get("term", "") for term in terms if int(term.get("difficulty", 3) or 3) >= 4][:5]
    return [
        {
            "id": "overview",
            "title": "1. 先读摘要和结论",
            "goal": "用 3 句话说清论文要解决什么问题、方法是什么、结果有什么意义。",
            "action": summary or "先定位摘要、引言最后一段和结论，写下论文主张。",
            "terms": top_terms[:3],
        },
        {
            "id": "terms",
            "title": "2. 扫清关键术语",
            "goal": "先理解高频术语，再回到正文看方法细节。",
            "action": "优先点开高亮术语，标记真正掌握的概念。",
            "terms": top_terms,
        },
        {
            "id": "method",
            "title": "3. 拆方法链路",
            "goal": "找出输入、模型/算法、训练或推理流程、输出。",
            "action": "把方法部分改写成步骤列表，不懂的步骤交给右侧伴学追问。",
            "terms": hard_terms or top_terms[:4],
        },
        {
            "id": "evidence",
            "title": "4. 看实验和证据",
            "goal": "确认论文用什么指标证明方法有效，和哪些 baseline 比较。",
            "action": "记录数据集、指标、对比方法和消融实验。",
            "terms": [t.get("term", "") for t in terms if "评估" in t.get("category", "")][:5],
        },
        {
            "id": "limits",
            "title": "5. 总结贡献和局限",
            "goal": "说出这篇论文真正推进了什么，以及还没有解决什么。",
            "action": "让伴学追问你 2 个问题，检查是否真的读懂。",
            "terms": top_terms[:5],
        },
    ]


def build_concept_notes(terms: list[dict]) -> list[dict]:
    notes = []
    for term in terms[:8]:
        name = term.get("term", "")
        if not name:
            continue
        prereq = term.get("prerequisiteTerms", []) or []
        notes.append({
            "term": name,
            "category": term.get("category", ""),
            "difficulty": term.get("difficulty", 3),
            "oneLine": term.get("explanationZh") or term.get("explanation") or "",
            "learningFocus": f"先补：{', '.join(prereq[:3])}" if prereq else "先建立直觉，再回到论文中看它如何被使用。",
            "paperFocus": f"在正文中找出 {name} 出现的位置，看看作者把它用在问题、方法还是实验里。",
        })
    return notes


def build_concept_chains(terms: list[dict]) -> list[dict]:
    chains = []
    for term in terms[:8]:
        name = term.get("term", "")
        if not name:
            continue
        prereqs = [p for p in term.get("prerequisiteTerms", [])[:4] if p]
        related = [r for r in term.get("relatedTerms", [])[:4] if r]
        chain_nodes = [
            *[{"term": p, "role": "prerequisite", "label": "前置"} for p in prereqs],
            {"term": name, "role": "current", "label": "当前"},
            *[{"term": r, "role": "related", "label": "延伸"} for r in related],
        ]
        chains.append({
            "term": name,
            "category": term.get("category", ""),
            "difficulty": term.get("difficulty", 3),
            "nodes": chain_nodes,
            "learningOrder": [node["term"] for node in chain_nodes],
        })
    return chains


def build_knowledge_graph(terms: list[dict]) -> dict:
    nodes = {}
    edges = []
    selected = terms[:12]
    selected_names = {term.get("term") for term in selected}
    for term in selected:
        name = term.get("term")
        if not name:
            continue
        nodes[name] = {
            "id": name,
            "label": name,
            "category": term.get("category", ""),
            "difficulty": term.get("difficulty", 3),
            "mastered": False,
        }
        for prereq in term.get("prerequisiteTerms", [])[:3]:
            nodes.setdefault(prereq, {"id": prereq, "label": prereq, "category": "前置知识", "difficulty": 2, "mastered": False})
            edges.append({"source": prereq, "target": name, "type": "prerequisite"})
        for related in term.get("relatedTerms", [])[:2]:
            if related in selected_names:
                edges.append({"source": name, "target": related, "type": "related"})
    return {"nodes": list(nodes.values())[:24], "edges": edges[:36]}


def recommend_next_papers(terms: list[dict]) -> list[dict]:
    seen = set()
    papers = []
    for term in terms[:8]:
        for paper in related_papers_for_term(term):
            title = str(paper.get("title", "")).strip()
            if not title or title.lower() in seen:
                continue
            seen.add(title.lower())
            item = enrich_paper_resource(paper, f"来自你刚读到的术语：{term.get('term', '')}")
            item["fromTerm"] = term.get("term", "")
            papers.append(item)
            if len(papers) >= 8:
                return papers
    return papers


def create_learning_session(request: LearningSessionRequest) -> dict:
    terms = _unique_terms(request.knownTerms)
    data = _load_progress()
    session_id = uuid4().hex[:12]
    term_names = [term.get("term", "") for term in terms if term.get("term")]
    category_counts = Counter(term.get("category", "未分类") for term in terms)
    session = {
        "id": session_id,
        "createdAt": _now(),
        "title": request.title or "未命名论文",
        "source": request.source or "text",
        "termCount": len(term_names),
        "terms": term_names[:30],
        "topCategories": [{"category": k, "count": v} for k, v in category_counts.most_common(5)],
    }
    data.setdefault("sessions", []).append(session)
    data["sessions"] = data["sessions"][-80:]
    seen = data.setdefault("seenTerms", {})
    for name in term_names:
        seen[name] = int(seen.get(name, 0)) + 1
    _save_progress(data)

    summary = request.paperSummary or str(request.analysis.get("summary", ""))
    return {
        "session": session,
        "profile": get_learning_profile(),
        "readingRoute": build_reading_route(terms, summary, request.source),
        "conceptNotes": build_concept_notes(terms),
        "conceptChains": build_concept_chains(terms),
        "knowledgeGraph": build_knowledge_graph(terms),
        "nextPapers": recommend_next_papers(terms),
    }


def update_mastery(term: str, mastered: bool) -> dict:
    name = _term_name(term)
    if not name:
        raise ValueError("term is required")
    data = _load_progress()
    data.setdefault("masteredTerms", {})[name] = bool(mastered)
    data.setdefault("seenTerms", {}).setdefault(name, 1)
    _save_progress(data)
    return get_learning_profile()
