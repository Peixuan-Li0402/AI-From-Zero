from __future__ import annotations

import re

import httpx

from .analysis import build_analysis_response
from .chat import chat_with_context
from .config import settings
from .learning import get_learning_paths
from .models import ChatRequest
from .papers import search_papers
from .terms import get_term, serialize_term, terms


SUPPORTED_CHANNELS = {"wechat", "qq", "local"}


def _configured_url(channel: str) -> str:
    if channel == "wechat":
        return settings.wechat_webhook_url
    if channel == "qq":
        return settings.qq_bot_webhook_url
    return ""


def _require_token(token: str) -> None:
    expected = settings.message_bridge_token
    if expected and token != expected:
        raise ValueError("Invalid message bridge token")


def _masked_channel(channel: str) -> dict:
    url = _configured_url(channel)
    return {
        "channel": channel,
        "configured": bool(url),
        "maskedWebhook": settings.mask_secret(url),
    }


def integration_status() -> dict:
    return {
        "status": "ok",
        "channels": [_masked_channel("wechat"), _masked_channel("qq")],
        "tokenConfigured": bool(settings.message_bridge_token),
        "inboundEndpoint": "/api/integrations/messages/inbound",
        "sendEndpoint": "/api/integrations/messages/send",
        "localSimulation": "python tools/openclaw_ai_from_zero.py message \"解释 Transformer\" --channel local",
    }


def _find_term(text: str) -> dict | None:
    query = re.sub(r"^(术语|解释|term|explain)[:：\s]*", "", text.strip(), flags=re.I)
    candidates = [query]
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}|[\u4e00-\u9fff]{2,}", query)
    candidates.extend(tokens)
    for item in candidates:
        term = get_term(item)
        if term:
            return term
    lower = text.lower()
    for term in terms[:300]:
        name = str(term.get("term", ""))
        if name and name.lower() in lower:
            return term
    return None


def _reply_for_term(term: dict) -> dict:
    data = serialize_term(term)
    prereq = "、".join(data.get("prerequisiteTerms", [])[:4]) or "暂无明确前置概念"
    papers = data.get("landmarkPapers", [])[:2]
    paper_text = "；".join(p.get("title", "") for p in papers if p.get("title")) or "暂无内置经典论文"
    reply = (
        f"术语：{data.get('term')} / {data.get('termZh') or data.get('fullNameZh')}\n"
        f"解释：{data.get('explanationZh') or data.get('explanation')}\n"
        f"前置概念：{prereq}\n"
        f"经典论文：{paper_text}"
    )
    return {"action": "term_explain", "reply": reply, "term": data}


def _reply_for_learning_path(text: str) -> dict:
    interest = re.sub(r"^(学习路径|路线|下一篇|learn)[:：\s]*", "", text.strip(), flags=re.I) or "llm"
    data = get_learning_paths(interest)
    stages = []
    for path in data.get("paths", [])[:1]:
        for stage in path.get("stages", [])[:3]:
            papers = stage.get("paperItems") or []
            first = papers[0] if papers else {}
            title = first.get("title") or first.get("display") or "待推荐论文"
            link = first.get("pdfUrl") or first.get("url") or first.get("openAccessUrl") or ""
            stages.append(f"{stage.get('title', '')}: {title} {link}".strip())
    reply = "推荐学习路径：\n" + "\n".join(f"{idx + 1}. {line}" for idx, line in enumerate(stages))
    return {"action": "learning_path", "reply": reply, "paths": data.get("paths", [])}


def _reply_for_paper_text(text: str) -> dict:
    analysis = build_analysis_response(text[:50000], title="Message paper")
    terms_found = [item.get("term", "") for item in analysis.get("knownTerms", [])[:8] if item.get("term")]
    next_papers = search_papers(" ".join(terms_found[:3]) or "Transformer", limit=3, external=False).get("papers", [])
    paper_line = next_papers[0].get("title", "") if next_papers else "暂无推荐论文"
    reply = (
        f"论文导读：{analysis.get('analysis', {}).get('summary', '已完成本地导读')}\n"
        f"识别术语：{'、'.join(terms_found) or '暂未识别到核心术语'}\n"
        f"下一篇：{paper_line}"
    )
    return {"action": "paper_analysis", "reply": reply, "analysis": analysis, "nextPapers": next_papers}


def process_inbound_message(channel: str, text: str, sender: str = "", token: str = "", metadata: dict | None = None) -> dict:
    channel = (channel or "local").lower()
    if channel not in SUPPORTED_CHANNELS:
        raise ValueError("Unsupported channel")
    _require_token(token)
    text = (text or "").strip()
    if not text:
        raise ValueError("text is required")

    if len(text) > 600 or text.count("\n") >= 4:
        result = _reply_for_paper_text(text)
    elif any(word in text.lower() for word in ["学习路径", "路线", "下一篇", "learn path", "next paper"]):
        result = _reply_for_learning_path(text)
    else:
        term = _find_term(text)
        if term:
            result = _reply_for_term(term)
        else:
            chat = chat_with_context(ChatRequest(message=text, localOnly=not settings.llm_configured))
            result = {"action": "chat", "reply": chat.get("reply", ""), "llmStatus": chat.get("llmStatus", "")}

    return {
        "channel": channel,
        "sender": sender,
        "received": text[:2000],
        "metadata": metadata or {},
        **result,
    }


def send_message(channel: str, text: str, token: str = "", markdown: bool = False) -> dict:
    channel = (channel or "").lower()
    if channel not in {"wechat", "qq"}:
        raise ValueError("channel must be wechat or qq")
    _require_token(token)
    text = (text or "").strip()
    if not text:
        raise ValueError("text is required")

    url = _configured_url(channel)
    if not url:
        return {
            "channel": channel,
            "sent": False,
            "status": "not_configured",
            "message": f"{channel} webhook is not configured",
        }

    payload = (
        {"msgtype": "markdown", "markdown": {"content": text}}
        if channel == "wechat" and markdown
        else {"msgtype": "text", "text": {"content": text}}
        if channel == "wechat"
        else {"content": text, "msg_type": "text"}
    )
    with httpx.Client(timeout=10.0) as client:
        resp = client.post(url, json=payload)
    return {
        "channel": channel,
        "sent": 200 <= resp.status_code < 300,
        "statusCode": resp.status_code,
        "status": "ok" if 200 <= resp.status_code < 300 else "error",
        "responsePreview": resp.text[:300],
    }
