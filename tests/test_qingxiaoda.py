import asyncio
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from fastapi.testclient import TestClient
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app import agent_attachments as attachment_module  # noqa: E402
from app import agent_core as agent_core_module  # noqa: E402
from app import artifacts as artifact_module  # noqa: E402
from app import qingxiaoda as qingxiaoda_module  # noqa: E402
from app.agent_attachments import (  # noqa: E402
    AttachmentError,
    AttachmentInput,
    ProcessedDocument,
    download_url,
    process_document,
    validate_public_url,
)
from app.config import settings  # noqa: E402
from app.main import create_app  # noqa: E402


TEST_KEY = "qxd-test-secret-that-is-not-real"


@pytest.fixture(autouse=True)
def agent_settings(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "qxd_api_key", TEST_KEY)
    monkeypatch.setattr(settings, "qxd_model_id", "ai-from-zero-agent")
    monkeypatch.setattr(settings, "public_base_url", "")
    monkeypatch.setattr(settings, "qxd_attachment_allowed_hosts", [])
    monkeypatch.setattr(settings, "qxd_max_attachment_mb", 25)
    monkeypatch.setattr(settings, "qxd_allow_private_dns_proxy", False)
    monkeypatch.setattr(settings, "qxd_request_timeout", 5.0)
    monkeypatch.setattr(settings, "llm_api_key", "")
    monkeypatch.setattr(settings, "kimi_api_key", "")
    monkeypatch.setattr(settings, "llm_provider", "kimi")
    monkeypatch.setattr(artifact_module, "ARTIFACT_DIR", tmp_path / "artifacts")
    artifact_module._ARTIFACTS.clear()
    attachment_module._CACHE.clear()


@pytest.fixture()
def client():
    return TestClient(create_app())


def auth_headers(key=TEST_KEY):
    return {"Authorization": f"Bearer {key}"}


def parse_sse(text: str):
    payloads = []
    done = False
    for line in text.splitlines():
        if not line.startswith("data: "):
            continue
        value = line[6:]
        if value == "[DONE]":
            done = True
        else:
            payloads.append(json.loads(value))
    return payloads, done


def test_plain_arxiv_url_becomes_secure_pdf_input():
    from app.models import QingxiaodaChatRequest

    parsed = agent_core_module.parse_conversation(QingxiaodaChatRequest(
        messages=[{"role": "user", "content": "学习 https://arxiv.org/abs/1706.03762"}],
    ))
    assert parsed.files[0].url == "https://arxiv.org/pdf/1706.03762"


def test_html_paper_page_is_converted_to_plain_text(monkeypatch):
    async def fake_download(_url):
        return (
            b"<html><head><style>hidden</style></head><body><h1>Paper</h1><p>Transformer attention method and results for learning.</p></body></html>",
            "text/html",
            "paper.html",
        )

    monkeypatch.setattr(attachment_module, "download_url", fake_download)
    document = asyncio.run(process_document(AttachmentInput(kind="file", url="https://papers.example/view")))
    assert "Transformer attention" in document.text
    assert "<html>" not in document.text
    assert "hidden" not in document.text


def test_models_auth_and_shape(client, monkeypatch):
    assert client.get("/v1/models").status_code == 401
    assert client.get("/v1/models", headers=auth_headers("wrong")).status_code == 401

    response = client.get("/v1/models", headers=auth_headers())
    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == "ai-from-zero-agent"
    assert response.headers["x-afz-request-id"]
    assert TEST_KEY not in response.text

    monkeypatch.setattr(settings, "qxd_api_key", "")
    assert client.get("/v1/models", headers=auth_headers()).status_code == 503


def test_unversioned_models_alias_uses_same_auth_and_shape(client):
    assert client.get("/models").status_code == 401
    response = client.get("/models", headers=auth_headers())
    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == "ai-from-zero-agent"


def test_qingxiaoda_web_origin_can_preflight_agent_endpoint(client):
    response = client.options(
        "/v1/models",
        headers={
            "Origin": "https://www.xiaoda.tsinghua.edu.cn",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://www.xiaoda.tsinghua.edu.cn"


def test_non_stream_completion_and_unknown_model(client):
    response = client.post(
        "/v1/chat/completions",
        headers=auth_headers(),
        json={"model": "ignored-model", "messages": [{"role": "user", "content": "解释 Transformer 是什么"}]},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["object"] == "chat.completion"
    assert payload["model"] == "ai-from-zero-agent"
    assert "Transformer" in payload["choices"][0]["message"]["content"]
    assert payload["choices"][0]["finish_reason"] == "stop"
    assert payload["usage"]["total_tokens"] > 0


def test_unversioned_chat_alias_supports_platform_probe(client):
    response = client.post(
        "/chat/completions",
        headers=auth_headers(),
        json={"stream": True, "max_tokens": 1, "messages": [{"role": "user", "content": "你好"}]},
    )
    assert response.status_code == 200
    payloads, done = parse_sse(response.text)
    assert payloads[0]["choices"][0]["delta"]["role"] == "assistant"
    assert payloads[-1]["choices"][0]["finish_reason"] == "stop"
    assert done is True


def test_stream_probe_is_fast_and_has_exact_frame_order(client):
    started = time.perf_counter()
    response = client.post(
        "/v1/chat/completions",
        headers=auth_headers(),
        json={"stream": True, "max_tokens": 1, "messages": [{"role": "user", "content": "你好"}]},
    )
    elapsed = time.perf_counter() - started
    assert response.status_code == 200
    assert elapsed < 1.0
    payloads, done = parse_sse(response.text)
    assert payloads[0]["choices"][0]["delta"] == {"role": "assistant"}
    assert any(item["choices"][0]["delta"].get("content") for item in payloads[1:-1])
    assert payloads[-1]["choices"][0]["delta"] == {}
    assert payloads[-1]["choices"][0]["finish_reason"] == "stop"
    assert payloads[-1]["usage"]["total_tokens"] > 0
    assert done is True


def test_stream_must_be_json_boolean(client):
    response = client.post(
        "/v1/chat/completions",
        headers=auth_headers(),
        json={"stream": "true", "messages": [{"role": "user", "content": "你好"}]},
    )
    assert response.status_code == 422


def test_tool_role_is_accepted_and_ignored_safely(client):
    response = client.post(
        "/v1/chat/completions",
        headers=auth_headers(),
        json={
            "max_tokens": 1,
            "messages": [
                {"role": "tool", "content": "untrusted tool output"},
                {"role": "user", "content": "probe"},
            ],
        },
    )
    assert response.status_code == 200
    assert response.json()["choices"][0]["message"]["content"] == "OK"


def test_queue_wait_counts_toward_agent_timeout(monkeypatch):
    from app.models import QingxiaodaChatRequest

    monkeypatch.setattr(qingxiaoda_module, "_AGENT_SEMAPHORE", asyncio.Semaphore(0))
    monkeypatch.setattr(settings, "qxd_request_timeout", 0.01)
    request = QingxiaodaChatRequest(messages=[{"role": "user", "content": "分析论文"}])
    with pytest.raises(asyncio.TimeoutError):
        asyncio.run(qingxiaoda_module._run_agent(request))


def test_pdf_content_part_uses_existing_learning_pipeline(client, monkeypatch):
    async def fake_process(_item):
        return ProcessedDocument(
            url="https://files.example/paper.pdf",
            filename="paper.pdf",
            text="Transformer self-attention encoder decoder method experiment. " * 20,
            pages=[{"page": 1, "text": "Transformer uses self-attention in the encoder."}],
            structure={"abstract": "A paper about Transformer and self-attention.", "sections": []},
        )

    monkeypatch.setattr(agent_core_module, "process_document", fake_process)
    response = client.post(
        "/v1/chat/completions",
        headers=auth_headers(),
        json={
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": "分析这篇论文并给出阅读顺序"},
                    {"type": "file", "file": {"url": "https://files.example/paper.pdf", "filename": "paper.pdf"}},
                ],
            }],
        },
    )
    assert response.status_code == 200
    content = response.json()["choices"][0]["message"]["content"]
    assert "学习导读" in content
    assert "阅读顺序" in content
    assert "Transformer" in content


def test_unsupported_file_id_degrades_without_500(client):
    response = client.post(
        "/v1/chat/completions",
        headers=auth_headers(),
        json={
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": "总结附件"},
                    {"type": "file", "file": {"file_id": "file-only", "filename": "paper.docx"}},
                ],
            }],
        },
    )
    assert response.status_code == 200
    assert "file_id" in response.json()["choices"][0]["message"]["content"]


def test_learning_note_attachment_non_stream_and_download(client, monkeypatch):
    monkeypatch.setattr(settings, "public_base_url", "http://testserver")
    response = client.post(
        "/v1/chat/completions",
        headers=auth_headers(),
        json={"messages": [{"role": "user", "content": "解释 Transformer 并生成学习笔记"}]},
    )
    assert response.status_code == 200
    attachment = response.json()["x_soda"]["attachments"][0]
    assert attachment["fileType"] == "text"
    assert attachment["mimeType"] == "text/markdown"
    download = client.get(urlparse(attachment["fileUrl"]).path)
    assert download.status_code == 200
    assert "Transformer" in download.content.decode("utf-8")


def test_learning_note_attachment_only_on_stream_stop_frame(client, monkeypatch):
    monkeypatch.setattr(settings, "public_base_url", "http://testserver")
    response = client.post(
        "/v1/chat/completions",
        headers=auth_headers(),
        json={"stream": True, "messages": [{"role": "user", "content": "解释 Transformer 并生成学习笔记"}]},
    )
    payloads, done = parse_sse(response.text)
    frames_with_attachments = [item for item in payloads if "x_soda" in item]
    assert len(frames_with_attachments) == 1
    assert frames_with_attachments[0]["choices"][0]["finish_reason"] == "stop"
    assert "usage" in frames_with_attachments[0]
    assert done is True


def test_attachment_security_rejects_base64_private_network_and_bad_allowlist(monkeypatch):
    with pytest.raises(AttachmentError):
        asyncio.run(validate_public_url("data:application/pdf;base64,AAAA"))

    async def private_dns(_hostname, _port):
        return {"127.0.0.1"}

    monkeypatch.setattr(attachment_module, "_resolve_host", private_dns)
    with pytest.raises(AttachmentError):
        asyncio.run(validate_public_url("https://files.example/paper.pdf"))

    monkeypatch.setattr(settings, "qxd_attachment_allowed_hosts", ["xiaoda.example"])
    with pytest.raises(AttachmentError):
        asyncio.run(validate_public_url("https://evil.example/paper.pdf"))


def test_private_dns_proxy_override_never_allows_literal_private_ip(monkeypatch):
    async def private_dns(_hostname, _port):
        return {"10.20.30.40"}

    monkeypatch.setattr(attachment_module, "_resolve_host", private_dns)
    monkeypatch.setattr(settings, "qxd_allow_private_dns_proxy", True)
    hostname, addresses = asyncio.run(validate_public_url("https://papers.example/paper.pdf"))
    assert hostname == "papers.example"
    assert addresses == {"10.20.30.40"}
    with pytest.raises(AttachmentError):
        asyncio.run(validate_public_url("http://10.20.30.40/paper.pdf"))


def test_attachment_download_rejects_oversized_content_length(monkeypatch):
    class FakeResponse:
        status_code = 200
        headers = {"content-length": str(26 * 1024 * 1024), "content-type": "application/pdf"}

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        def raise_for_status(self):
            return None

        async def aiter_bytes(self):
            yield b"unused"

    class FakeClient:
        def __init__(self, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        def stream(self, *_args, **_kwargs):
            return FakeResponse()

    async def public_url(_url):
        return "files.example", {"1.1.1.1"}

    monkeypatch.setattr(attachment_module.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(attachment_module, "validate_public_url", public_url)
    with pytest.raises(AttachmentError, match="25MB"):
        asyncio.run(download_url("https://files.example/paper.pdf"))


def test_attachment_download_rechecks_dns_after_fetch(monkeypatch):
    class FakeResponse:
        status_code = 200
        headers = {"content-type": "text/plain"}

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        def raise_for_status(self):
            return None

        async def aiter_bytes(self):
            yield b"paper text"

    class FakeClient:
        def __init__(self, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        def stream(self, *_args, **_kwargs):
            return FakeResponse()

    async def public_url(_url):
        return "files.example", {"1.1.1.1"}

    async def rebound_dns(_hostname, _port):
        return {"127.0.0.1"}

    monkeypatch.setattr(attachment_module.httpx, "AsyncClient", FakeClient)
    monkeypatch.setattr(attachment_module, "validate_public_url", public_url)
    monkeypatch.setattr(attachment_module, "_resolve_host", rebound_dns)
    with pytest.raises(AttachmentError, match="私有网络"):
        asyncio.run(download_url("https://files.example/paper.txt"))


def test_agent_timeout_returns_parseable_response(client, monkeypatch):
    async def timeout(_request):
        raise asyncio.TimeoutError

    monkeypatch.setattr("app.qingxiaoda.generate_agent_response", timeout)
    response = client.post(
        "/v1/chat/completions",
        headers=auth_headers(),
        json={"messages": [{"role": "user", "content": "分析论文"}]},
    )
    assert response.status_code == 200
    assert "时间限制" in response.json()["choices"][0]["message"]["content"]
