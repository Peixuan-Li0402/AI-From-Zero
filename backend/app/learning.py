import json
import re

from .config import KNOWLEDGE_DIR


LEARNING_PATHS_PATH = KNOWLEDGE_DIR / "learning_paths.json"


def load_learning_paths() -> dict:
    return json.loads(LEARNING_PATHS_PATH.read_text(encoding="utf-8"))


def _parse_paper_reference(value: str) -> dict:
    raw = str(value or "").strip()
    cleaned = re.sub(r"^\s*\d+\.\s*", "", raw)
    match = re.match(r"(?P<title>.+?)\s*\((?P<meta>[^()]*(?:19|20)\d{2}[^()]*)\)\s*$", cleaned)
    title = cleaned
    meta = ""
    year = ""
    if match:
        title = match.group("title").strip()
        meta = match.group("meta").strip()
        year_match = re.search(r"(19|20)\d{2}", meta)
        year = year_match.group(0) if year_match else ""
    return {
        "display": raw,
        "title": title,
        "meta": meta,
        "year": year,
        "searchQuery": title,
        "readerPrompt": (
            f"学习目标：阅读 {title}。\n\n"
            "请先找到论文 PDF 或摘要粘贴到这里，再点击“开始分析”。\n"
            "建议阅读顺序：摘要 -> 关键术语 -> 方法段 -> 实验结果 -> 局限与后续论文。"
        ),
    }


def _enrich_path(path: dict) -> dict:
    enriched = dict(path)
    stages = []
    for stage in path.get("stages", []):
        new_stage = dict(stage)
        new_stage["paperItems"] = [_parse_paper_reference(item) for item in stage.get("papers", [])]
        stages.append(new_stage)
    enriched["stages"] = stages
    return enriched


def get_learning_paths(interest: str = "") -> dict:
    paths = load_learning_paths()
    if interest:
        interest_lower = interest.lower()
        matches = []
        for key, path in paths.items():
            if key in interest_lower or any(kw in interest_lower for kw in path["title"].lower().split()):
                matches.append({"id": key, **_enrich_path(path)})
        if matches:
            return {"type": "matched", "paths": matches}

    return {
        "type": "all",
        "paths": [{"id": key, **_enrich_path(value)} for key, value in paths.items()],
        "hoshinoNote": "呜嘿～sensei想往哪个方向走？告诉大叔你的兴趣，大叔给你量身定制っす！",
    }

