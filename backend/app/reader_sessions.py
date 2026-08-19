from __future__ import annotations

import hashlib
import json
import re
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from .agent_attachments import ProcessedDocument
from .config import DATA_DIR, settings


SESSION_DIR = DATA_DIR / "reader_sessions"
SESSION_TEXT_LIMIT = 500_000
SESSION_MESSAGE_LIMIT = 80
SESSION_MESSAGE_TEXT_LIMIT = 8_000
_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{20,80}$")
_CONVERSATION_KEYS = (
    "conversation_id",
    "conversationId",
    "session_id",
    "sessionId",
    "chat_id",
    "chatId",
    "thread_id",
    "threadId",
)
_READER_LINK_RE = re.compile(
    r"^\s*(?:##\s*网页(?:阅读器|学习工作台)\s*)?"
    r"\[[^\]]*(?:阅读器|学习工作台)[^\]]*\]\(https?://[^)]+\)\s*",
    re.IGNORECASE,
)


def _iso_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _session_path(token: str) -> Path:
    if not _TOKEN_PATTERN.fullmatch(token):
        raise HTTPException(status_code=404, detail="阅读会话不存在或已过期")
    return SESSION_DIR / f"{token}.json"


def _read_payload(path: Path) -> dict | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _write_payload(path: Path, payload: dict) -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    temp_path.replace(path)


def _cleanup() -> None:
    if not SESSION_DIR.exists():
        return
    now = time.time()
    active: list[Path] = []
    for path in SESSION_DIR.glob("*.json"):
        payload = _read_payload(path)
        if not payload or float(payload.get("_expiresAtEpoch", 0)) <= now:
            try:
                path.unlink()
            except OSError:
                pass
            continue
        active.append(path)
    active.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    for path in active[settings.qxd_workspace_limit:]:
        try:
            path.unlink()
        except OSError:
            pass


def _hash_identity(value: str) -> str:
    seed = settings.qxd_api_key or "ai-from-zero-reader-workspace"
    return hashlib.sha256(f"{seed}\0{value}".encode("utf-8")).hexdigest()


def _request_extra(request: Any) -> dict:
    extra = getattr(request, "model_extra", None)
    return extra if isinstance(extra, dict) else {}


def _conversation_identity(request: Any) -> str:
    extra = _request_extra(request)
    containers = [extra]
    for name in ("metadata", "x_soda", "context", "client"):
        nested = extra.get(name)
        if isinstance(nested, dict):
            containers.append(nested)
    for container in containers:
        for key in _CONVERSATION_KEYS:
            value = str(container.get(key, "")).strip()
            if value:
                user = str(getattr(request, "user", "") or "").strip()
                return _hash_identity(f"{user}\0{key}\0{value}")
    return ""


def _user_identity(request: Any) -> str:
    user = str(getattr(request, "user", "") or "").strip()
    return _hash_identity(user) if user else ""


def _safe_content(value: Any) -> str:
    return str(value or "").strip()[:SESSION_MESSAGE_TEXT_LIMIT]


def _normalize_request_messages(request: Any) -> list[dict]:
    normalized: list[dict] = []
    for message in getattr(request, "messages", []):
        role = str(getattr(message, "role", "")).strip()
        if role not in {"user", "assistant"}:
            continue
        content = getattr(message, "content", "")
        text_parts: list[str] = []
        attachments: list[dict] = []
        if isinstance(content, str):
            if content.strip():
                text_parts.append(content.strip())
        elif isinstance(content, list):
            for part in content:
                if not isinstance(part, dict):
                    continue
                part_type = str(part.get("type", "")).lower()
                if part_type in {"text", "input_text"}:
                    text = _safe_content(part.get("text"))
                    if text:
                        text_parts.append(text)
                elif part_type == "file":
                    info = part.get("file", {})
                    info = info if isinstance(info, dict) else {}
                    filename = _safe_content(info.get("filename") or info.get("file_id") or "论文附件")
                    attachments.append({"type": "file", "name": filename})
                elif part_type == "image_url":
                    attachments.append({"type": "image", "name": "图片"})
                elif part_type == "input_audio":
                    attachments.append({"type": "audio", "name": "音频"})
        text = _safe_content("\n".join(text_parts))
        if not text and attachments:
            text = "已上传：" + "、".join(item["name"] for item in attachments)
        if not text:
            continue
        item = {"role": role, "content": text}
        if attachments:
            item["attachments"] = attachments[:3]
        normalized.append(item)
    return normalized[-SESSION_MESSAGE_LIMIT:]


def _strip_reader_link(content: str) -> str:
    return _READER_LINK_RE.sub("", content, count=1).strip()


def _display_messages(messages: list[dict]) -> list[dict]:
    result: list[dict] = []
    for message in messages:
        item = dict(message)
        if item.get("role") == "assistant":
            item["content"] = _strip_reader_link(_safe_content(item.get("content")))
        if item.get("content"):
            result.append(item)
    return result[-SESSION_MESSAGE_LIMIT:]


def _content_compatible(left: str, right: str, role: str) -> bool:
    if left == right:
        return True
    if role == "assistant" and min(len(left), len(right)) >= 20:
        return left.startswith(right) or right.startswith(left)
    return False


def _history_match_score(stored: list[dict], incoming: list[dict]) -> int:
    if not stored or not incoming:
        return 0
    compare_count = min(len(stored), len(incoming))
    score = 0
    for index in range(compare_count):
        old = stored[index]
        new = incoming[index]
        role = str(old.get("role", ""))
        if role != new.get("role") or not _content_compatible(
            _safe_content(old.get("content")),
            _safe_content(new.get("content")),
            role,
        ):
            break
        score += 1
    if score != len(stored):
        return 0
    return score


def _find_workspace(request: Any, incoming: list[dict]) -> tuple[Path, dict] | None:
    conversation_key = _conversation_identity(request)
    user_key = _user_identity(request)
    best: tuple[int, float, Path, dict] | None = None
    if not SESSION_DIR.exists():
        return None
    for path in SESSION_DIR.glob("*.json"):
        payload = _read_payload(path)
        if not payload:
            continue
        if conversation_key and payload.get("_conversationKey") == conversation_key:
            return path, payload
        if user_key and payload.get("_userKey") and payload.get("_userKey") != user_key:
            continue
        score = _history_match_score(payload.get("_matchMessages", []), incoming)
        if score:
            candidate = (score, path.stat().st_mtime, path, payload)
            if best is None or candidate[:2] > best[:2]:
                best = candidate
    return (best[2], best[3]) if best else None


def _workspace_url(token: str) -> str:
    return f"{settings.public_base_url}/?{urlencode({'session': token})}"


def _merge_conversation(existing: list[dict], incoming: list[dict]) -> list[dict]:
    clean_incoming = _display_messages(incoming)
    if not existing:
        return clean_incoming
    common_prefix = 0
    for old, new in zip(existing, clean_incoming):
        role = str(old.get("role", ""))
        if role != new.get("role") or not _content_compatible(
            _safe_content(old.get("content")),
            _safe_content(new.get("content")),
            role,
        ):
            break
        common_prefix += 1
    if common_prefix == len(existing):
        return clean_incoming
    merged = list(existing)
    for message in clean_incoming[common_prefix:]:
        if merged and merged[-1].get("role") == message.get("role") and merged[-1].get("content") == message.get("content"):
            continue
        merged.append(message)
    return merged[-SESSION_MESSAGE_LIMIT:]


def reserve_reader_workspace(request: Any) -> dict | None:
    if not settings.public_base_url:
        return None
    _cleanup()
    incoming = _normalize_request_messages(request)
    found = _find_workspace(request, incoming)
    if found:
        path, payload = found
        token = path.stem
    else:
        token = secrets.token_urlsafe(24)
        path = _session_path(token)
        payload = {
            "title": "清小搭学习会话",
            "source": "qingxiaoda-agent",
            "sessionMode": "conversation",
            "text": "",
            "textLength": 0,
            "pageCount": 0,
            "truncated": False,
            "paperStructure": {},
            "knownTerms": [],
            "analysis": {},
            "translation": "",
            "translationStatus": "not_requested",
            "translationCoverage": 0,
            "llmStatus": "ok" if settings.llm_configured else "missing_key",
            "extractionWarnings": [],
            "conversation": [],
        }
    now = time.time()
    expires_at = now + settings.qxd_workspace_ttl
    payload["_expiresAtEpoch"] = expires_at
    payload["_conversationKey"] = _conversation_identity(request)
    payload["_userKey"] = _user_identity(request)
    payload["_matchMessages"] = incoming
    payload["conversation"] = _merge_conversation(payload.get("conversation", []), incoming)
    payload["updatedAt"] = _iso_timestamp(now)
    payload["expiresAt"] = _iso_timestamp(expires_at)
    payload["turnCount"] = sum(1 for item in payload["conversation"] if item.get("role") == "user")
    _write_payload(path, payload)
    _cleanup()
    return {"token": token, "url": _workspace_url(token), "title": payload["title"], "expiresAt": payload["expiresAt"]}


def build_reader_context(
    documents: list[ProcessedDocument],
    known_terms: list[dict],
    summary: str,
) -> dict:
    if not documents:
        return {}
    pieces: list[str] = []
    total_pages = 0
    warnings: list[str] = []
    for document in documents[:3]:
        label = Path(document.filename).stem or "论文"
        pieces.append(f"===== {label} =====\n\n{document.text}" if len(documents) > 1 else document.text)
        total_pages += len(document.pages) or (1 if document.text else 0)
        warnings.extend(document.warnings)
    full_text = "\n\n".join(pieces)
    text = full_text[:SESSION_TEXT_LIMIT]
    first = documents[0]
    first_title = Path(first.filename).stem or "论文阅读"
    title = first_title if len(documents) == 1 else f"{first_title} 等 {len(documents)} 篇"
    return {
        "title": title,
        "sessionMode": "paper",
        "text": text,
        "textLength": len(text),
        "pageCount": total_pages,
        "truncated": len(full_text) > SESSION_TEXT_LIMIT,
        "paperStructure": first.structure or {},
        "knownTerms": known_terms[:20],
        "analysis": {
            "summary": summary,
            "hoshinoNote": "点击高亮术语继续学习。",
            "llmStatus": "ok" if settings.llm_configured else "missing_key",
        },
        "translation": "",
        "translationStatus": "not_requested",
        "translationCoverage": 0,
        "llmStatus": "ok" if settings.llm_configured else "missing_key",
        "extractionWarnings": warnings[:12],
        "documents": [
            {
                "title": Path(item.filename).stem or "论文",
                "filename": item.filename,
                "pageCount": len(item.pages) or (1 if item.text else 0),
            }
            for item in documents[:3]
        ],
    }


def finalize_reader_workspace(
    token: str,
    request: Any,
    delivered_assistant: str,
    display_assistant: str,
    reader_context: dict | None = None,
) -> None:
    path = _session_path(token)
    payload = _read_payload(path)
    if not payload:
        return
    incoming = _normalize_request_messages(request)
    match_messages = incoming + [{"role": "assistant", "content": _safe_content(delivered_assistant)}]
    display_messages = _display_messages(incoming)
    assistant_body = _safe_content(display_assistant)
    if assistant_body:
        display_messages.append({"role": "assistant", "content": assistant_body})
    payload["_matchMessages"] = match_messages[-SESSION_MESSAGE_LIMIT:]
    payload["conversation"] = _merge_conversation(payload.get("conversation", []), display_messages)
    if reader_context:
        payload.update(reader_context)
    now = time.time()
    expires_at = now + settings.qxd_workspace_ttl
    payload["_expiresAtEpoch"] = expires_at
    payload["updatedAt"] = _iso_timestamp(now)
    payload["expiresAt"] = _iso_timestamp(expires_at)
    payload["turnCount"] = sum(1 for item in payload["conversation"] if item.get("role") == "user")
    _write_payload(path, payload)


def save_reader_conversation(token: str, messages: list[dict]) -> dict:
    _cleanup()
    path = _session_path(token)
    payload = _read_payload(path)
    if not payload or float(payload.get("_expiresAtEpoch", 0)) <= time.time():
        raise HTTPException(status_code=404, detail="阅读会话不存在或已过期")
    clean: list[dict] = []
    for message in messages[-SESSION_MESSAGE_LIMIT:]:
        if not isinstance(message, dict):
            continue
        role = str(message.get("role", ""))
        content = _safe_content(message.get("content"))
        if role in {"user", "assistant"} and content:
            clean.append({"role": role, "content": content})
    payload["conversation"] = clean
    now = time.time()
    expires_at = now + settings.qxd_workspace_ttl
    payload["_expiresAtEpoch"] = expires_at
    payload["updatedAt"] = _iso_timestamp(now)
    payload["expiresAt"] = _iso_timestamp(expires_at)
    payload["turnCount"] = sum(1 for item in clean if item["role"] == "user")
    _write_payload(path, payload)
    return {"ok": True, "messageCount": len(clean), "expiresAt": payload["expiresAt"]}


def create_reader_session(
    document: ProcessedDocument,
    known_terms: list[dict],
    summary: str,
) -> dict | None:
    if not settings.public_base_url:
        return None
    _cleanup()
    token = secrets.token_urlsafe(24)
    expires_at = time.time() + settings.qxd_workspace_ttl
    payload = {
        "_expiresAtEpoch": expires_at,
        "_matchMessages": [],
        "_conversationKey": "",
        "_userKey": "",
        "source": "qingxiaoda-agent",
        "conversation": [],
        "updatedAt": _iso_timestamp(time.time()),
        "expiresAt": _iso_timestamp(expires_at),
        "turnCount": 0,
        **build_reader_context([document], known_terms, summary),
    }
    _write_payload(_session_path(token), payload)
    _cleanup()
    return {"token": token, "url": _workspace_url(token), "title": payload["title"], "expiresAt": payload["expiresAt"]}


def reader_session_response(token: str) -> JSONResponse:
    _cleanup()
    path = _session_path(token)
    payload = _read_payload(path)
    if not payload or float(payload.get("_expiresAtEpoch", 0)) <= time.time():
        try:
            path.unlink()
        except OSError:
            pass
        raise HTTPException(status_code=404, detail="阅读会话不存在或已过期")
    public_payload = {key: value for key, value in payload.items() if not key.startswith("_")}
    return JSONResponse(
        public_payload,
        headers={
            "Cache-Control": "private, no-store",
            "Referrer-Policy": "no-referrer",
            "X-Robots-Tag": "noindex, nofollow, noarchive",
        },
    )
