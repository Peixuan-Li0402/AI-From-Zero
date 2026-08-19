from __future__ import annotations

import asyncio
import json
import math
import secrets
import time
from collections.abc import AsyncIterator

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from .agent_core import AgentResult, generate_agent_response, parse_conversation
from .artifacts import artifact_response
from .config import settings
from .models import QingxiaodaChatRequest, ReaderConversationSaveRequest
from .reader_sessions import (
    finalize_reader_workspace,
    reader_session_response,
    reserve_reader_workspace,
    save_reader_conversation,
)


router = APIRouter()
_AGENT_SEMAPHORE = asyncio.Semaphore(settings.qxd_max_concurrency)


def _authenticate(authorization: str | None) -> None:
    if not settings.qxd_configured:
        raise HTTPException(status_code=503, detail="Agent credential is not configured")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing credential", headers={"WWW-Authenticate": "Bearer"})
    supplied = authorization[len("Bearer "):].strip()
    if not supplied or not secrets.compare_digest(supplied, settings.qxd_api_key):
        raise HTTPException(status_code=401, detail="invalid credential", headers={"WWW-Authenticate": "Bearer"})


def _completion_id() -> str:
    return f"chatcmpl-afz-{secrets.token_hex(10)}"


def _token_count(text: str) -> int:
    if not text:
        return 0
    ascii_count = sum(1 for char in text if ord(char) < 128)
    other_count = len(text) - ascii_count
    return max(1, math.ceil(ascii_count / 4) + math.ceil(other_count / 1.5))


def _prompt_text(request: QingxiaodaChatRequest) -> str:
    parsed = parse_conversation(request)
    return parsed.all_user_text or parsed.latest_user_text


def _limit_content(content: str, max_tokens: int | None) -> tuple[str, str]:
    if not max_tokens:
        return content, "stop"
    max_chars = max_tokens * 4
    if content.startswith("[在 AI-From-Zero 阅读器继续学习]"):
        link_end = content.find("\n\n")
        if link_end >= 0:
            max_chars = max(max_chars, link_end + 2)
    if len(content) <= max_chars:
        return content, "stop"
    return content[:max_chars].rstrip(), "length"


def _usage(prompt: str, completion: str) -> dict:
    prompt_tokens = _token_count(prompt)
    completion_tokens = _token_count(completion)
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }


def _workspace_content(request: QingxiaodaChatRequest, result: AgentResult) -> tuple[str, dict | None, str]:
    if request.max_tokens is not None and request.max_tokens <= 1:
        return result.content, None, ""
    try:
        workspace = reserve_reader_workspace(request)
    except Exception:
        workspace = None
    if not workspace:
        return result.content, None, ""
    prefix = f"[在 AI-From-Zero 阅读器继续学习]({workspace['url']})\n\n"
    return prefix + result.content, workspace, prefix


def _finalize_workspace(
    request: QingxiaodaChatRequest,
    result: AgentResult,
    workspace: dict | None,
    delivered_content: str,
    prefix: str,
) -> None:
    if not workspace:
        return
    display_content = delivered_content[len(prefix):].strip() if delivered_content.startswith(prefix) else ""
    try:
        finalize_reader_workspace(
            workspace["token"],
            request,
            delivered_content,
            display_content,
            result.reader_context,
        )
    except Exception:
        pass


async def _run_agent(request: QingxiaodaChatRequest) -> AgentResult:
    if request.max_tokens is not None and request.max_tokens <= 1:
        return AgentResult(content="OK")

    async def run_bounded() -> AgentResult:
        async with _AGENT_SEMAPHORE:
            return await generate_agent_response(request)

    # Queueing time counts toward the gateway deadline as well as processing time.
    return await asyncio.wait_for(run_bounded(), timeout=settings.qxd_request_timeout)


def _frame(
    completion_id: str,
    created: int,
    delta: dict,
    *,
    finish_reason: str | None = None,
    usage: dict | None = None,
    attachments: list[dict] | None = None,
) -> str:
    payload = {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": settings.qxd_model_id,
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
    }
    if usage is not None:
        payload["usage"] = usage
    if attachments:
        payload["x_soda"] = {"attachments": attachments}
    return "data: " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n\n"


async def _stream_completion(request: QingxiaodaChatRequest, completion_id: str, created: int) -> AsyncIterator[str]:
    prompt = _prompt_text(request)
    yield _frame(completion_id, created, {"role": "assistant"})
    is_probe = request.max_tokens is not None and request.max_tokens <= 1
    if not is_probe:
        yield _frame(completion_id, created, {"reasoning": "正在读取论文与学习上下文"})
    try:
        result = await _run_agent(request)
    except asyncio.TimeoutError:
        result = AgentResult(content="本次处理超过时间限制。请缩小论文范围或稍后重试。")
    except Exception:
        result = AgentResult(content="当前服务暂时无法完成分析，请稍后重试。")
    workspace_content, workspace, prefix = _workspace_content(request, result)
    content, finish_reason = _limit_content(workspace_content, request.max_tokens)
    _finalize_workspace(request, result, workspace, content, prefix)
    for offset in range(0, len(content), 80):
        yield _frame(completion_id, created, {"content": content[offset:offset + 80]})
    yield _frame(
        completion_id,
        created,
        {},
        finish_reason=finish_reason,
        usage=_usage(prompt, content),
        attachments=result.attachments,
    )
    yield "data: [DONE]\n\n"


@router.get("/models", include_in_schema=False)
@router.get("/v1/models")
async def qingxiaoda_models(authorization: str | None = Header(default=None)):
    _authenticate(authorization)
    return {
        "object": "list",
        "data": [
            {
                "id": settings.qxd_model_id,
                "object": "model",
                "created": 0,
                "owned_by": "ai-from-zero",
            }
        ],
    }


@router.post("/chat/completions", include_in_schema=False)
@router.post("/v1/chat/completions")
async def qingxiaoda_chat_completions(
    request: QingxiaodaChatRequest,
    authorization: str | None = Header(default=None),
):
    _authenticate(authorization)
    completion_id = _completion_id()
    created = int(time.time())
    if request.stream:
        return StreamingResponse(
            _stream_completion(request, completion_id, created),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    prompt = _prompt_text(request)
    try:
        result = await _run_agent(request)
    except asyncio.TimeoutError:
        result = AgentResult(content="本次处理超过时间限制。请缩小论文范围或稍后重试。")
    except Exception:
        result = AgentResult(content="当前服务暂时无法完成分析，请稍后重试。")
    workspace_content, workspace, prefix = _workspace_content(request, result)
    content, finish_reason = _limit_content(workspace_content, request.max_tokens)
    _finalize_workspace(request, result, workspace, content, prefix)
    payload = {
        "id": completion_id,
        "object": "chat.completion",
        "created": created,
        "model": settings.qxd_model_id,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": finish_reason,
            }
        ],
        "usage": _usage(prompt, content),
    }
    if result.attachments:
        payload["x_soda"] = {"attachments": result.attachments}
    return JSONResponse(payload)


@router.get("/artifacts/{token}")
async def download_agent_artifact(token: str):
    return artifact_response(token)


@router.get("/api/reader-sessions/{token}")
async def get_reader_session(token: str):
    return reader_session_response(token)


@router.post("/api/reader-sessions/{token}/conversation")
async def save_reader_session_conversation(token: str, request: ReaderConversationSaveRequest):
    return save_reader_conversation(token, [item.model_dump() for item in request.messages])
