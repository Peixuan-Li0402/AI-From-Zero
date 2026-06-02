from __future__ import annotations

from .papers import CANONICAL_PAPERS, enrich_paper_resource


DEMO_CASES: list[dict] = [
    {
        "id": "transformer",
        "title": "Transformer classic reading",
        "label": "Transformer 经典论文",
        "track": "AI / NLP",
        "paperKey": "transformer",
        "goal": "从 Attention、Self-Attention、Encoder-Decoder 理解现代大模型的基础结构。",
        "guide": "先看摘要，再点开 Transformer、Self-Attention、Multi-Head Attention，最后读下一篇 BERT。",
    },
    {
        "id": "rag-agent",
        "title": "RAG and Agent reading path",
        "label": "RAG / Agent 热点路线",
        "track": "LLM Application",
        "paperKey": "rag",
        "goal": "理解检索增强生成如何把外部知识接入语言模型，并连接到 Agent 工具调用。",
        "guide": "先读 RAG，再看 ReAct 或 Toolformer，把检索、推理和行动串起来。",
    },
    {
        "id": "systems",
        "title": "FlashAttention systems reading",
        "label": "系统工程方向",
        "track": "AI Systems",
        "paperKey": "flash attention",
        "goal": "理解高性能 AI 系统如何从内存 IO、算子和硬件约束优化模型训练。",
        "guide": "先读 FlashAttention，再把 Attention 计算和 GPU 内存访问联系起来。",
    },
]


def list_demo_cases() -> dict:
    cases = []
    for case in DEMO_CASES:
        paper = enrich_paper_resource(CANONICAL_PAPERS.get(case["paperKey"], {}), case["guide"])
        cases.append({
            **case,
            "paper": {
                "title": paper.get("title", ""),
                "authors": paper.get("authors", ""),
                "year": paper.get("year", ""),
                "url": paper.get("url", ""),
                "pdfUrl": paper.get("pdfUrl", ""),
                "resourceStatus": paper.get("resourceStatus", ""),
                "shortDesc": paper.get("shortDesc", ""),
                "readerText": paper.get("readerText", ""),
            },
        })
    return {"cases": cases}


def load_demo_case(case_id: str) -> dict:
    normalized = (case_id or "").strip().lower()
    for case in DEMO_CASES:
        if case["id"] == normalized:
            paper = enrich_paper_resource(CANONICAL_PAPERS.get(case["paperKey"], {}), case["guide"])
            text = "\n\n".join([
                paper.get("readerText", ""),
                "Demo reading focus:",
                case["goal"],
                case["guide"],
                "Key concepts to inspect: Transformer, Attention, Self-Attention, RAG, Agent, GPU, Memory, Optimization.",
            ]).strip()
            return {
                "loadStatus": "ok",
                "mode": "demo_guide",
                "case": case,
                "paper": paper,
                "text": text,
                "textLength": len(text),
                "pageCount": 0,
                "warnings": [],
            }
    raise ValueError(f"Unknown demo case: {case_id}")
