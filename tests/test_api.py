import sys
from pathlib import Path

from fastapi.testclient import TestClient
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app import config as config_module  # noqa: E402
from app import progress as progress_module  # noqa: E402
from app.config import settings  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture(autouse=True)
def no_llm_key(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "")
    monkeypatch.setattr(settings, "kimi_api_key", "")
    monkeypatch.setattr(settings, "llm_provider", "kimi")
    monkeypatch.setattr(settings, "llm_api_url", "https://api.moonshot.cn/v1/chat/completions")
    monkeypatch.setattr(settings, "llm_model", "moonshot-v1-128k")


@pytest.fixture()
def client():
    return TestClient(create_app())


def make_pdf(text: str) -> bytes:
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pdf = b"%PDF-1.4\n"
    offsets = []
    for idx, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf += f"{idx} 0 obj\n".encode("ascii") + obj + b"\nendobj\n"
    xref = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n".encode("ascii")
    pdf += b"0000000000 65535 f \n"
    for offset in offsets:
        pdf += f"{offset:010d} 00000 n \n".encode("ascii")
    pdf += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
    return pdf


def test_health_reports_local_mode(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["llmConfigured"] is False
    assert data["termsTotal"] > 0
    assert data["llmProvider"] == "kimi"
    assert data["llmModel"]


def test_config_status_and_local_save(client, tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    monkeypatch.setattr(config_module, "ENV_PATH", env_file)
    resp = client.get("/api/config")
    assert resp.status_code == 200
    assert resp.json()["llmConfigured"] is False

    providers = client.get("/api/config/providers")
    assert providers.status_code == 200
    assert any(p["id"] == "openai" for p in providers.json()["providers"])

    saved = client.post("/api/config/save", json={
        "provider": "openai",
        "apiKey": "sk-test-secret-value",
        "apiUrl": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o-mini",
        "timeout": 30,
    })
    assert saved.status_code == 200
    payload = saved.json()
    assert payload["llmConfigured"] is True
    assert "sk-test" not in str(payload)
    assert "sk-test-secret-value" in env_file.read_text(encoding="utf-8")


def test_text_analysis_degrades_without_key(client):
    text = (
        "The Transformer uses self-attention, encoder and decoder layers, CNN and RNN baselines, "
        "and neural network training ideas for sequence transduction models."
    )
    resp = client.post("/api/analyze", json={"text": text})
    assert resp.status_code == 200
    data = resp.json()
    assert data["llmStatus"] == "missing_key"
    assert data["knownTerms"]
    assert data["analysis"]["summary"]
    assert data["translationStatus"] == "missing_key"
    assert data["translationCoverage"] == 0
    assert "paperStructure" in data


def test_terms_and_related_papers(client):
    term_resp = client.get("/api/terms/Transformer")
    assert term_resp.status_code == 200
    term_data = term_resp.json()
    assert term_data["term"] == "Transformer"
    assert term_data["conceptChain"]["nodes"]

    papers_resp = client.post("/api/terms/Transformer/papers")
    assert papers_resp.status_code == 200
    assert papers_resp.json()["papers"]


def test_explain_endpoints_degrade_without_key(client):
    detail = client.get("/api/terms/Transformer/explain").json()
    academic = client.get("/api/terms/Transformer/explain-academic").json()
    assert detail["llmStatus"] == "missing_key"
    assert academic["llmStatus"] == "missing_key"


def test_learn_path_and_case_study(client):
    learn = client.post("/api/learn-path", json={"interest": "llm"})
    assert learn.status_code == 200
    learn_data = learn.json()
    assert learn_data["paths"]
    assert learn_data["paths"][0]["stages"][0]["paperItems"][0]["readerPrompt"]
    first_paper = learn_data["paths"][0]["stages"][0]["paperItems"][0]
    assert first_paper["resourceStatus"] in {"pdf", "abstract", "link"}
    assert first_paper.get("url") or first_paper.get("pdfUrl") or first_paper.get("shortDesc")

    case = client.post("/api/case-study", json={"text": "这个系统使用 CNN、Transformer 和强化学习做感知与决策。"})
    assert case.status_code == 200
    assert case.json()["llmStatus"] == "missing_key"


def test_pdf_analysis_and_failures(client):
    long_text = " ".join(["Transformer attention CNN RNN self-attention encoder decoder neural network model analysis text"] * 300)
    pdf = make_pdf(long_text)
    resp = client.post("/api/analyze-pdf", files={"file": ("paper.pdf", pdf, "application/pdf")})
    assert resp.status_code == 200
    data = resp.json()
    assert data["llmStatus"] == "missing_key"
    assert data["knownTerms"]
    assert data["textLength"] > 10000
    assert len(data["text"]) > 10000
    assert data["pageCount"] == 1
    assert data["pages"]
    assert "paperStructure" in data

    bad = client.post("/api/analyze-pdf", files={"file": ("bad.txt", b"not a pdf", "text/plain")})
    assert bad.status_code == 400

    blank = client.post("/api/analyze-pdf", files={"file": ("blank.pdf", make_pdf(""), "application/pdf")})
    assert blank.status_code == 200
    assert blank.json()["llmStatus"] == "error"


def test_chat_degrades_without_key(client):
    resp = client.post("/api/chat", json={
        "message": "解释一下当前论文里的 Transformer",
        "paperText": "Transformer self-attention encoder decoder neural network model analysis text.",
        "paperSummary": "一篇关于 Transformer 的论文。",
        "knownTerms": [{"term": "Transformer"}],
        "currentTerm": "Transformer",
        "masteredTerms": [],
        "history": [],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["llmStatus"] == "missing_key"
    assert data["reply"]


def test_learning_loop_endpoints(client, tmp_path, monkeypatch):
    monkeypatch.setattr(progress_module, "PROGRESS_PATH", tmp_path / "learning_progress.json")
    analysis = client.post("/api/analyze", json={
        "title": "Attention Is All You Need",
        "text": "Transformer self-attention encoder decoder neural network model analysis text. " * 8,
    })
    assert analysis.status_code == 200
    known_terms = analysis.json()["knownTerms"]

    session = client.post("/api/learning/session", json={
        "title": "Attention Is All You Need",
        "source": "text",
        "paperText": "Transformer self-attention encoder decoder neural network model analysis text.",
        "paperSummary": "A paper about the Transformer architecture.",
        "knownTerms": known_terms,
        "analysis": analysis.json()["analysis"],
    })
    assert session.status_code == 200
    payload = session.json()
    assert payload["session"]["termCount"] > 0
    assert payload["readingRoute"]
    assert payload["conceptNotes"]
    assert payload["conceptChains"]
    assert payload["knowledgeGraph"]["nodes"]
    removed_phrase = "你刚" + "遇到了"
    assert all(removed_phrase not in str(paper) for paper in payload["nextPapers"])

    mastery = client.post("/api/learning/mastery", json={"term": known_terms[0]["term"], "mastered": True})
    assert mastery.status_code == 200
    assert mastery.json()["termsMastered"] >= 1


def test_paper_search_and_evidence(client):
    search = client.get("/api/papers/search", params={"query": "Transformer", "limit": 3, "external": "false"})
    assert search.status_code == 200
    papers = search.json()["papers"]
    assert papers
    assert papers[0].get("readerText")
    assert papers[0].get("pdfUrl") or papers[0].get("openAccessUrl")

    load = client.post("/api/papers/load", json={
        "abstract": "This paper explains Transformer attention and encoder decoder learning for students.",
    })
    assert load.status_code == 200
    loaded = load.json()
    assert loaded["mode"] == "abstract"
    assert "Transformer" in loaded["text"]
    assert loaded["paper"]["resourceStatus"] == "abstract"

    evidence = client.post("/api/papers/evidence", json={
        "question": "What is self-attention used for?",
        "paperText": (
            "The Transformer uses self-attention to connect tokens in a sequence. "
            "The encoder and decoder rely on attention mechanisms for sequence transduction."
        ),
        "knownTerms": [{"term": "self-attention"}, {"term": "Transformer"}],
    })
    assert evidence.status_code == 200
    assert evidence.json()["snippets"]


def test_demo_cases_and_message_bridge(client):
    cases = client.get("/api/demo-cases")
    assert cases.status_code == 200
    payload = cases.json()
    assert len(payload["cases"]) >= 3
    assert payload["cases"][0]["paper"]["resourceStatus"] in {"pdf", "abstract", "link"}

    loaded = client.post("/api/demo-cases/transformer/load")
    assert loaded.status_code == 200
    loaded_data = loaded.json()
    assert loaded_data["case"]["id"] == "transformer"
    assert loaded_data["text"]

    status = client.get("/api/integrations/status")
    assert status.status_code == 200
    status_data = status.json()
    assert {item["channel"] for item in status_data["channels"]} == {"wechat", "qq"}
    assert "WECHAT_WEBHOOK_URL" not in str(status_data)

    inbound = client.post("/api/integrations/messages/inbound", json={
        "channel": "local",
        "text": "解释 Transformer",
        "sender": "pytest",
    })
    assert inbound.status_code == 200
    assert inbound.json()["action"] == "term_explain"
    assert "Transformer" in inbound.json()["reply"]

    learn = client.post("/api/integrations/messages/inbound", json={
        "channel": "qq",
        "text": "下一篇 llm",
        "sender": "pytest",
    })
    assert learn.status_code == 200
    assert learn.json()["action"] == "learning_path"

    send = client.post("/api/integrations/messages/send", json={
        "channel": "wechat",
        "text": "hello",
    })
    assert send.status_code == 200
    assert send.json()["status"] == "not_configured"
