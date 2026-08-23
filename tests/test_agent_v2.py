import asyncio
import random
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "tools"))

from app import agent_core as agent_core_module  # noqa: E402
from app import agent_runtime as agent_runtime_module  # noqa: E402
from app import papers as papers_module  # noqa: E402
from app.agent_attachments import AttachmentInput, ProcessedDocument  # noqa: E402
from app.agent_runtime import infer_learner_profile, route_agent_request  # noqa: E402
from app.config import settings  # noqa: E402
from app.models import QingxiaodaChatRequest  # noqa: E402
from app.terms import extract_terms_from_text, terms  # noqa: E402
from check_agent_eval_split import validate_splits  # noqa: E402


def test_router_keeps_simple_terms_local_and_search_explicit(monkeypatch):
    monkeypatch.setattr(settings, "agent_realtime_search", True)
    term = route_agent_request("解释 Transformer 是什么", has_documents=False, has_focus_term=True)
    search = route_agent_request("搜索最新 RAG 论文", has_documents=False, has_focus_term=True)
    assert term.intent == "term"
    assert term.use_llm is False
    assert term.realtime_search is False
    assert search.intent == "paper_search"
    assert search.realtime_search is True


def test_router_treats_a_resolved_term_as_a_learning_request():
    questions = (
        "简单讲讲 LSM Tree",
        "Property-Based Testing 有什么用",
        "我刚在论文里看到 Transformer",
    )
    for question in questions:
        matches = extract_terms_from_text(question)
        plan = route_agent_request(question, has_documents=False, has_focus_term=bool(matches))
        assert matches
        assert plan.intent == "term"
        assert plan.use_llm is False


def test_router_does_not_confuse_term_mentions_with_user_tasks(monkeypatch):
    monkeypatch.setattr(settings, "agent_realtime_search", True)
    cases = (
        "帮我写一个用 Python 实现 Softmax 的函数",
        "请翻译这句话：Attention is all you need",
        "总结 Transformer 的三项优点",
        "帮我调试包含 Cache 的这段代码",
    )
    for question in cases:
        matches = extract_terms_from_text(question)
        assert matches
        plan = route_agent_request(question, has_documents=False, has_focus_term=True)
        assert plan.intent == "task", question
        assert plan.use_llm is True


def test_router_treats_fresh_research_questions_as_realtime_search(monkeypatch):
    monkeypatch.setattr(settings, "agent_realtime_search", True)
    plan = route_agent_request(
        "今天 Agent 研究有哪些新进展",
        has_documents=False,
        has_focus_term=True,
    )
    assert plan.intent == "topic_research"
    assert plan.realtime_search is True


def test_randomized_known_terms_keep_the_fast_learning_path():
    sample = random.Random(20260821).sample(terms, min(160, len(terms)))
    for term in sample:
        question = f"简单讲讲 {term['term']}"
        matches = extract_terms_from_text(question)
        plan = route_agent_request(question, has_documents=False, has_focus_term=bool(matches))
        assert matches, term["term"]
        assert plan.intent == "term", term["term"]


def test_short_uppercase_aliases_do_not_match_common_lowercase_words():
    matches = extract_terms_from_text("The method is trained in the lab and evaluated on the test set.")
    names = {term["term"] for term in matches}
    assert "InstanceNorm" not in names
    assert "TLB" not in names


def test_profile_is_inferred_without_forcing_a_questionnaire():
    profile = infer_learner_profile(
        [{"role": "user", "content": "我是大一新手，想做一个 Agent 项目"}],
        "先给我简单讲讲 RAG",
    )
    assert profile.level == "入门"
    assert profile.goal == "做出可落地项目"
    assert "大语言模型" in profile.interests
    assert profile.concise is True


def test_realtime_search_runs_providers_concurrently_and_caches(monkeypatch):
    papers_module._SEARCH_CACHE.clear()
    papers_module._PROVIDER_COOLDOWN_UNTIL.clear()
    calls = []

    def provider(name):
        def run(_query, _limit):
            calls.append(name)
            time.sleep(0.12)
            return [{"title": f"{name} result", "url": f"https://example.com/{name}", "source": name}]
        return run

    monkeypatch.setattr(papers_module, "_arxiv_search", provider("arxiv"))
    monkeypatch.setattr(papers_module, "_openalex_search", provider("openalex"))
    monkeypatch.setattr(papers_module, "_semantic_scholar_search", provider("semantic-scholar"))
    monkeypatch.setattr(papers_module, "_local_paper_search", lambda *_args: [])
    monkeypatch.setattr(papers_module, "_canonical_for_query", lambda *_args: None)

    started = time.perf_counter()
    first = asyncio.run(papers_module.search_papers_realtime("held-out query", 6, timeout=1.0))
    elapsed = time.perf_counter() - started
    second = asyncio.run(papers_module.search_papers_realtime("held-out query", 6, timeout=1.0))
    assert elapsed < 0.28
    assert len(first["papers"]) == 3
    assert second["cached"] is True
    assert len(calls) == 3


def test_attachment_processing_is_concurrent(monkeypatch):
    async def fake_process(item):
        await asyncio.sleep(0.1)
        return ProcessedDocument(url=item.url, filename=item.filename, text="paper text")

    monkeypatch.setattr(agent_core_module, "process_document", fake_process)
    parsed = agent_core_module.ParsedConversation(files=[
        AttachmentInput(kind="file", url="https://example.com/a.pdf", filename="a.pdf"),
        AttachmentInput(kind="file", url="https://example.com/b.pdf", filename="b.pdf"),
    ])
    started = time.perf_counter()
    documents, warnings = asyncio.run(agent_core_module._load_documents(parsed))
    elapsed = time.perf_counter() - started
    assert elapsed < 0.18
    assert len(documents) == 2
    assert warnings == []


def test_plain_text_agent_prompt_uses_openai_string_content(monkeypatch):
    captured = {}

    def fake_llm(messages, *_args, **_kwargs):
        captured["messages"] = messages
        return "任务已完成"

    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(agent_core_module, "call_llm_messages", fake_llm)
    result = asyncio.run(agent_core_module._ask_agent_llm(
        "用 Python 写一个 Softmax 函数",
        "先完成任务",
        "Softmax 是归一化函数",
        "入门学习者",
        "",
        [],
        [],
        [{"role": "user", "content": "用 Python 写一个 Softmax 函数"}],
        600,
    ))

    assert result == "任务已完成"
    assert isinstance(captured["messages"][1]["content"], str)
    assert "用 Python 写一个 Softmax 函数" in captured["messages"][1]["content"]


def test_image_agent_prompt_keeps_multimodal_content(monkeypatch):
    captured = {}

    def fake_llm(messages, *_args, **_kwargs):
        captured["messages"] = messages
        return "图片已分析"

    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(agent_core_module, "call_llm_messages", fake_llm)
    result = asyncio.run(agent_core_module._ask_agent_llm(
        "解释这张图",
        "先看图",
        "",
        "入门学习者",
        "",
        [],
        ["https://example.com/figure.png"],
        [{"role": "user", "content": "解释这张图"}],
        600,
    ))

    content = captured["messages"][1]["content"]
    assert result == "图片已分析"
    assert isinstance(content, list)
    assert content[0]["type"] == "text"
    assert content[1]["type"] == "image_url"


def test_term_fast_path_skips_llm_and_records_agent_state(monkeypatch):
    def fail_llm(*_args, **_kwargs):
        raise AssertionError("term fast path should not call the LLM")

    monkeypatch.setattr(agent_core_module, "call_llm_messages", fail_llm)
    request = QingxiaodaChatRequest(messages=[{"role": "user", "content": "解释 FlashAttention 是什么"}])
    result = asyncio.run(agent_core_module.generate_agent_response(request))
    assert "FlashAttention" in result.content
    assert result.reader_context["agentState"]["intent"] == "term"
    assert "双语术语库" in " ".join(result.reader_context["agentState"]["sources"])


def test_focus_term_prefers_longest_specific_alias():
    request = QingxiaodaChatRequest(messages=[{"role": "user", "content": "解释 Unit Testing 的作用"}])
    result = asyncio.run(agent_core_module.generate_agent_response(request))
    assert result.content.startswith("## Unit Testing")
    assert not result.content.startswith("## End-to-End Testing")


def test_focus_term_follows_the_latest_explanation_request():
    request = QingxiaodaChatRequest(messages=[{
        "role": "user",
        "content": "我想从 Transformer 开始系统学习，先简单讲讲 Attention",
    }])
    result = asyncio.run(agent_core_module.generate_agent_response(request))
    assert result.content.startswith("## Attention")


def test_focus_term_stops_before_the_question_reason_clause():
    request = QingxiaodaChatRequest(messages=[{
        "role": "user",
        "content": "解释 KV Cache 为什么能加速推理",
    }])
    result = asyncio.run(agent_core_module.generate_agent_response(request))
    assert "KV Cache" in result.content.splitlines()[0]


def test_term_answer_keeps_the_alias_used_by_the_learner():
    for question, alias in (("编译器里的 SSA 是什么", "SSA"), ("Fuzzing 的用途是什么", "Fuzzing")):
        request = QingxiaodaChatRequest(messages=[{"role": "user", "content": question}])
        result = asyncio.run(agent_core_module.generate_agent_response(request))
        assert alias in result.content.splitlines()[0]


def test_concept_bridge_compares_two_known_terms_without_llm(monkeypatch):
    def fail_llm(*_args, **_kwargs):
        raise AssertionError("concept bridge should use the local knowledge base")

    monkeypatch.setattr(agent_core_module, "call_llm_messages", fail_llm)
    request = QingxiaodaChatRequest(messages=[{"role": "user", "content": "LoRA 和 Fine-tuning 有什么区别"}])
    result = asyncio.run(agent_core_module.generate_agent_response(request))
    assert "概念桥" in result.content
    assert "LoRA" in result.content
    assert "Fine-tuning" in result.content
    assert len(result.reader_context["agentState"]["concepts"]) >= 2


def test_realtime_paper_answer_exposes_source_and_link_without_llm(monkeypatch):
    async def fake_search(_query, _limit, **_kwargs):
        return {
            "papers": [{
                "title": "A Reliable RAG Paper",
                "year": 2026,
                "source": "arxiv",
                "pdfUrl": "https://arxiv.org/pdf/2601.00001",
                "shortDesc": "A held-out search result.",
            }],
            "sourceStatus": {"arxiv": "1 result"},
            "latencyMs": 12,
        }

    def fail_llm(*_args, **_kwargs):
        raise AssertionError("paper search should not require the LLM")

    monkeypatch.setattr(settings, "agent_realtime_search", True)
    monkeypatch.setattr(agent_runtime_module, "search_papers_realtime", fake_search)
    monkeypatch.setattr(agent_core_module, "call_llm_messages", fail_llm)
    request = QingxiaodaChatRequest(messages=[{"role": "user", "content": "搜索最新 RAG 论文"}])
    result = asyncio.run(agent_core_module.generate_agent_response(request))
    assert "https://arxiv.org/pdf/2601.00001" in result.content
    assert "arXiv 实时检索" in result.content
    assert result.reader_context["agentState"]["searchLatencyMs"] == 12


def test_eval_splits_are_disjoint():
    assert validate_splits() == {"train": 8, "dev": 8, "test": 8, "test_round2": 8}
