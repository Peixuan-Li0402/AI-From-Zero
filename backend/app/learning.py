import json

from .config import KNOWLEDGE_DIR


LEARNING_PATHS_PATH = KNOWLEDGE_DIR / "learning_paths.json"


def load_learning_paths() -> dict:
    return json.loads(LEARNING_PATHS_PATH.read_text(encoding="utf-8"))


def get_learning_paths(interest: str = "") -> dict:
    paths = load_learning_paths()
    if interest:
        interest_lower = interest.lower()
        matches = []
        for key, path in paths.items():
            if key in interest_lower or any(kw in interest_lower for kw in path["title"].lower().split()):
                matches.append({"id": key, **path})
        if matches:
            return {"type": "matched", "paths": matches}

    return {
        "type": "all",
        "paths": [{"id": key, **value} for key, value in paths.items()],
        "hoshinoNote": "呜嘿～sensei想往哪个方向走？告诉大叔你的兴趣，大叔给你量身定制っす！",
    }

