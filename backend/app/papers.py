from __future__ import annotations

import asyncio
import re
import time
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime

import httpx

from .pdf import extract_pdf_pages
from .terms import related_papers_for_term, terms


MAX_PDF_BYTES = 24 * 1024 * 1024
ARXIV_NS = {"atom": "http://www.w3.org/2005/Atom"}
_SEARCH_CACHE: dict[str, tuple[float, dict]] = {}
_PROVIDER_COOLDOWN_UNTIL: dict[str, float] = {}
_SEARCH_CACHE_TTL_SECONDS = 600.0
_PROVIDER_COOLDOWN_SECONDS = 45.0
_SEARCH_CACHE_LIMIT = 128

CANONICAL_PAPERS: dict[str, dict] = {
    "word2vec": {
        "title": "Efficient Estimation of Word Representations in Vector Space",
        "authors": "Tomas Mikolov, Kai Chen, Greg Corrado, Jeffrey Dean",
        "year": "2013",
        "url": "https://arxiv.org/abs/1301.3781",
        "pdfUrl": "https://arxiv.org/pdf/1301.3781",
        "shortDesc": "Word2Vec 的核心论文，提出 Skip-gram 和 CBOW，用预测上下文的方式学习词向量。",
    },
    "glove": {
        "title": "GloVe: Global Vectors for Word Representation",
        "authors": "Jeffrey Pennington, Richard Socher, Christopher Manning",
        "year": "2014",
        "url": "https://nlp.stanford.edu/projects/glove/",
        "pdfUrl": "https://nlp.stanford.edu/pubs/glove.pdf",
        "shortDesc": "把全局词共现统计和词向量学习结合起来，是理解词表示的重要起点。",
    },
    "seq2seq": {
        "title": "Sequence to Sequence Learning with Neural Networks",
        "authors": "Ilya Sutskever, Oriol Vinyals, Quoc V. Le",
        "year": "2014",
        "url": "https://arxiv.org/abs/1409.3215",
        "pdfUrl": "https://arxiv.org/pdf/1409.3215",
        "shortDesc": "用编码器-解码器结构处理序列到序列任务，为神经机器翻译和后续 Transformer 铺路。",
    },
    "attention": {
        "title": "Neural Machine Translation by Jointly Learning to Align and Translate",
        "authors": "Dzmitry Bahdanau, Kyunghyun Cho, Yoshua Bengio",
        "year": "2014",
        "url": "https://arxiv.org/abs/1409.0473",
        "pdfUrl": "https://arxiv.org/pdf/1409.0473",
        "shortDesc": "早期注意力机制代表作，让模型在生成时动态关注输入序列的不同位置。",
    },
    "transformer": {
        "title": "Attention Is All You Need",
        "authors": "Ashish Vaswani et al.",
        "year": "2017",
        "url": "https://arxiv.org/abs/1706.03762",
        "pdfUrl": "https://arxiv.org/pdf/1706.03762",
        "shortDesc": "Transformer 经典论文，用多头自注意力替代循环结构，是现代大模型的基础。",
    },
    "attention is all you need": {
        "title": "Attention Is All You Need",
        "authors": "Ashish Vaswani et al.",
        "year": "2017",
        "url": "https://arxiv.org/abs/1706.03762",
        "pdfUrl": "https://arxiv.org/pdf/1706.03762",
        "shortDesc": "Transformer 经典论文，用多头自注意力替代循环结构，是现代大模型的基础。",
    },
    "bert": {
        "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "authors": "Jacob Devlin, Ming-Wei Chang, Kenton Lee, Kristina Toutanova",
        "year": "2018",
        "url": "https://arxiv.org/abs/1810.04805",
        "pdfUrl": "https://arxiv.org/pdf/1810.04805",
        "shortDesc": "提出双向 Transformer 预训练，是理解预训练语言模型和微调范式的关键论文。",
    },
    "gpt-1": {
        "title": "Improving Language Understanding by Generative Pre-Training",
        "authors": "Alec Radford et al.",
        "year": "2018",
        "url": "https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_paper.pdf",
        "pdfUrl": "https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_paper.pdf",
        "shortDesc": "GPT 系列的起点，展示生成式预训练加任务微调可以提升语言理解任务。",
    },
    "gpt-2": {
        "title": "Language Models are Unsupervised Multitask Learners",
        "authors": "Alec Radford et al.",
        "year": "2019",
        "url": "https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf",
        "pdfUrl": "https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf",
        "shortDesc": "展示大规模语言模型的零样本/多任务能力，是 GPT-3 前的重要过渡论文。",
    },
    "gpt-3": {
        "title": "Language Models are Few-Shot Learners",
        "authors": "Tom Brown et al.",
        "year": "2020",
        "url": "https://arxiv.org/abs/2005.14165",
        "pdfUrl": "https://arxiv.org/pdf/2005.14165",
        "shortDesc": "展示大规模语言模型的少样本学习能力，是大模型规模化路线的代表作。",
    },
    "scaling laws": {
        "title": "Scaling Laws for Neural Language Models",
        "authors": "Jared Kaplan et al.",
        "year": "2020",
        "url": "https://arxiv.org/abs/2001.08361",
        "pdfUrl": "https://arxiv.org/pdf/2001.08361",
        "shortDesc": "研究模型规模、数据量和计算量之间的经验规律，是理解大模型训练投入的基础。",
    },
    "chinchilla": {
        "title": "Training Compute-Optimal Large Language Models",
        "authors": "Jordan Hoffmann et al.",
        "year": "2022",
        "url": "https://arxiv.org/abs/2203.15556",
        "pdfUrl": "https://arxiv.org/pdf/2203.15556",
        "shortDesc": "重新讨论模型参数量和训练 token 的配比，强调计算最优训练策略。",
    },
    "instructgpt": {
        "title": "Training Language Models to Follow Instructions with Human Feedback",
        "authors": "Long Ouyang et al.",
        "year": "2022",
        "url": "https://arxiv.org/abs/2203.02155",
        "pdfUrl": "https://arxiv.org/pdf/2203.02155",
        "shortDesc": "用人类反馈强化学习让语言模型更会遵循指令，是对齐技术的重要论文。",
    },
    "chain-of-thought": {
        "title": "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models",
        "authors": "Jason Wei et al.",
        "year": "2022",
        "url": "https://arxiv.org/abs/2201.11903",
        "pdfUrl": "https://arxiv.org/pdf/2201.11903",
        "shortDesc": "展示逐步推理提示能提升大模型复杂推理能力。",
    },
    "llama": {
        "title": "LLaMA: Open and Efficient Foundation Language Models",
        "authors": "Hugo Touvron et al.",
        "year": "2023",
        "url": "https://arxiv.org/abs/2302.13971",
        "pdfUrl": "https://arxiv.org/pdf/2302.13971",
        "shortDesc": "开源基础模型路线的重要代表，适合学习高效训练和开放模型生态。",
    },
    "lora": {
        "title": "LoRA: Low-Rank Adaptation of Large Language Models",
        "authors": "Edward Hu et al.",
        "year": "2021",
        "url": "https://arxiv.org/abs/2106.09685",
        "pdfUrl": "https://arxiv.org/pdf/2106.09685",
        "shortDesc": "通过低秩适配高效微调大模型，是参数高效微调的经典方法。",
    },
    "rag": {
        "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        "authors": "Patrick Lewis et al.",
        "year": "2020",
        "url": "https://arxiv.org/abs/2005.11401",
        "pdfUrl": "https://arxiv.org/pdf/2005.11401",
        "shortDesc": "把检索和生成结合起来，是构建可信问答和知识增强应用的基础论文。",
    },
    "react": {
        "title": "ReAct: Synergizing Reasoning and Acting in Language Models",
        "authors": "Shunyu Yao et al.",
        "year": "2022",
        "url": "https://arxiv.org/abs/2210.03629",
        "pdfUrl": "https://arxiv.org/pdf/2210.03629",
        "shortDesc": "让语言模型交替进行推理和行动，是理解 Agent 工具调用的重要论文。",
    },
    "mamba": {
        "title": "Mamba: Linear-Time Sequence Modeling with Selective State Spaces",
        "authors": "Albert Gu, Tri Dao",
        "year": "2023",
        "url": "https://arxiv.org/abs/2312.00752",
        "pdfUrl": "https://arxiv.org/pdf/2312.00752",
        "shortDesc": "用选择性状态空间模型处理长序列，是 Transformer 替代路线的重要代表。",
    },
    "flash attention": {
        "title": "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness",
        "authors": "Tri Dao et al.",
        "year": "2022",
        "url": "https://arxiv.org/abs/2205.14135",
        "pdfUrl": "https://arxiv.org/pdf/2205.14135",
        "shortDesc": "从内存 IO 角度优化注意力计算，是高效训练和推理的关键工程论文。",
    },
    "alexnet": {
        "title": "ImageNet Classification with Deep Convolutional Neural Networks",
        "authors": "Alex Krizhevsky, Ilya Sutskever, Geoffrey Hinton",
        "year": "2012",
        "url": "https://papers.nips.cc/paper/4824-imagenet-classification-with-deep-convolutional-neural-networks",
        "pdfUrl": "https://papers.nips.cc/paper_files/paper/2012/file/c399862d3b9d6b76c8436e924a68c45b-Paper.pdf",
        "shortDesc": "深度 CNN 在 ImageNet 上取得突破，是现代计算机视觉深度学习路线的起点。",
    },
    "resnet": {
        "title": "Deep Residual Learning for Image Recognition",
        "authors": "Kaiming He et al.",
        "year": "2015",
        "url": "https://arxiv.org/abs/1512.03385",
        "pdfUrl": "https://arxiv.org/pdf/1512.03385",
        "shortDesc": "提出残差连接，解决深层网络训练困难，是视觉模型架构的基础论文。",
    },
    "vit": {
        "title": "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale",
        "authors": "Alexey Dosovitskiy et al.",
        "year": "2020",
        "url": "https://arxiv.org/abs/2010.11929",
        "pdfUrl": "https://arxiv.org/pdf/2010.11929",
        "shortDesc": "把 Transformer 直接用于图像 patch，是视觉 Transformer 的代表作。",
    },
    "clip": {
        "title": "Learning Transferable Visual Models From Natural Language Supervision",
        "authors": "Alec Radford et al.",
        "year": "2021",
        "url": "https://arxiv.org/abs/2103.00020",
        "pdfUrl": "https://arxiv.org/pdf/2103.00020",
        "shortDesc": "用图文对比学习连接视觉和语言，是多模态模型的重要起点。",
    },
    "stable diffusion": {
        "title": "High-Resolution Image Synthesis with Latent Diffusion Models",
        "authors": "Robin Rombach et al.",
        "year": "2022",
        "url": "https://arxiv.org/abs/2112.10752",
        "pdfUrl": "https://arxiv.org/pdf/2112.10752",
        "shortDesc": "在潜空间中进行扩散生成，是文生图模型的重要基础。",
    },
    "sam": {
        "title": "Segment Anything",
        "authors": "Alexander Kirillov et al.",
        "year": "2023",
        "url": "https://arxiv.org/abs/2304.02643",
        "pdfUrl": "https://arxiv.org/pdf/2304.02643",
        "shortDesc": "提出通用图像分割基础模型，适合学习视觉基础模型和提示式分割。",
    },
    "tree of thoughts": {
        "title": "Tree of Thoughts: Deliberate Problem Solving with Large Language Models",
        "authors": "Shunyu Yao et al.",
        "year": "2023",
        "url": "https://arxiv.org/abs/2305.10601",
        "pdfUrl": "https://arxiv.org/pdf/2305.10601",
        "shortDesc": "把推理过程组织成树搜索，是理解复杂推理 Agent 的实用入口。",
    },
    "toolformer": {
        "title": "Toolformer: Language Models Can Teach Themselves to Use Tools",
        "authors": "Timo Schick et al.",
        "year": "2023",
        "url": "https://arxiv.org/abs/2302.04761",
        "pdfUrl": "https://arxiv.org/pdf/2302.04761",
        "shortDesc": "研究语言模型如何学习调用外部工具，是 Agent 工具使用方向的核心论文。",
    },
    "webgpt": {
        "title": "WebGPT: Browser-assisted question-answering with human feedback",
        "authors": "Reiichiro Nakano et al.",
        "year": "2021",
        "url": "https://arxiv.org/abs/2112.09332",
        "pdfUrl": "https://arxiv.org/pdf/2112.09332",
        "shortDesc": "让模型借助浏览器回答问题，是带检索和人类反馈的问答系统代表作。",
    },
    "voyager": {
        "title": "Voyager: An Open-Ended Embodied Agent with Large Language Models",
        "authors": "Guanzhi Wang et al.",
        "year": "2023",
        "url": "https://arxiv.org/abs/2305.16291",
        "pdfUrl": "https://arxiv.org/pdf/2305.16291",
        "shortDesc": "展示 LLM 驱动的开放式具身 Agent，适合学习技能库、探索和长期任务。",
    },
    "pointnet": {
        "title": "PointNet: Deep Learning on Point Sets for 3D Classification and Segmentation",
        "authors": "Charles R. Qi et al.",
        "year": "2017",
        "url": "https://arxiv.org/abs/1612.00593",
        "pdfUrl": "https://arxiv.org/pdf/1612.00593",
        "shortDesc": "直接处理点云集合，是三维感知和机器人视觉的基础论文。",
    },
    "ppo": {
        "title": "Proximal Policy Optimization Algorithms",
        "authors": "John Schulman et al.",
        "year": "2017",
        "url": "https://arxiv.org/abs/1707.06347",
        "pdfUrl": "https://arxiv.org/pdf/1707.06347",
        "shortDesc": "强化学习中稳定高效的策略优化方法，是机器人控制和 RLHF 的重要基础。",
    },
    "dqn": {
        "title": "Playing Atari with Deep Reinforcement Learning",
        "authors": "Volodymyr Mnih et al.",
        "year": "2013",
        "url": "https://arxiv.org/abs/1312.5602",
        "pdfUrl": "https://arxiv.org/pdf/1312.5602",
        "shortDesc": "把深度学习用于强化学习值函数，是深度强化学习的起点之一。",
    },
}


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _paper_key(paper: dict) -> str:
    return _clean(paper.get("title", "")).lower()


def _norm_query(value: str) -> str:
    value = re.sub(r"^\s*\d+\.\s*", "", str(value or "")).strip().lower()
    value = re.sub(r"\s*\([^)]*\)\s*$", "", value)
    value = value.replace("_", " ").replace("-", " ")
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _canonical_for_query(query: str) -> dict | None:
    q = _norm_query(query)
    if not q:
        return None
    candidates = {q, q.replace(" ", "-"), q.replace(" ", "")}
    for key, paper in CANONICAL_PAPERS.items():
        nk = _norm_query(key)
        if nk in candidates:
            item = dict(paper)
            item["source"] = item.get("source", "curated")
            item.setdefault("openAccessUrl", item.get("pdfUrl", ""))
            item.setdefault("abstract", item.get("shortDesc", ""))
            return item
    for paper in CANONICAL_PAPERS.values():
        nt = _norm_query(paper.get("title", ""))
        if nt and (nt in candidates or nt in q or q in nt):
            item = dict(paper)
            item["source"] = item.get("source", "curated")
            item.setdefault("openAccessUrl", item.get("pdfUrl", ""))
            item.setdefault("abstract", item.get("shortDesc", ""))
            return item
    padded_q = f" {q} "
    for key, paper in sorted(CANONICAL_PAPERS.items(), key=lambda item: len(_norm_query(item[0])), reverse=True):
        nk = _norm_query(key)
        if len(nk) >= 4 and (f" {nk} " in padded_q or padded_q.strip() in nk):
            item = dict(paper)
            item["source"] = item.get("source", "curated")
            item.setdefault("openAccessUrl", item.get("pdfUrl", ""))
            item.setdefault("abstract", item.get("shortDesc", ""))
            return item
    return None


def _arxiv_pdf_from_url(url: str) -> str:
    match = re.search(r"arxiv\.org/(?:abs|html)/([0-9]{4}\.[0-9]{4,5}(?:v\d+)?)", url or "")
    return f"https://arxiv.org/pdf/{match.group(1)}" if match else ""


def _arxiv_year_from_url(url: str) -> str:
    match = re.search(r"arxiv\.org/(?:abs|html|pdf)/([0-9]{2})([0-9]{2})\.[0-9]{4,5}", url or "")
    if not match:
        return ""
    month = int(match.group(2))
    return str(2000 + int(match.group(1))) if 1 <= month <= 12 else ""


def _paper_reader_text(paper: dict, note: str = "") -> str:
    title = _clean(paper.get("title", "")) or "未命名论文"
    authors = _clean(paper.get("authors", ""))
    year = _clean(str(paper.get("year", "")))
    abstract = _clean(paper.get("abstract") or paper.get("shortDesc") or paper.get("whyRelated") or "")
    source_url = paper.get("openAccessUrl") or paper.get("pdfUrl") or paper.get("url") or ""
    lines = [
        f"标题：{title}",
        f"作者：{authors}" if authors else "",
        f"年份：{year}" if year else "",
        f"来源：{source_url}" if source_url else "",
        "",
        "摘要：",
        abstract or "未取得摘要。下载 PDF 或粘贴摘要。",
        "",
        "阅读顺序：摘要 -> 方法 -> 实验 -> 局限",
        note,
    ]
    return "\n".join(line for line in lines if line is not None).strip()


def enrich_paper_resource(paper: dict, why: str = "") -> dict:
    item = dict(paper)
    canonical = _canonical_for_query(item.get("title", ""))
    if canonical:
        merged = dict(item)
        for key, value in canonical.items():
            if value not in (None, "", []):
                merged[key] = value
        for key in ("fromTerm", "whyRelated"):
            if item.get(key):
                merged[key] = item[key]
        item = merged
    if item.get("url") and not item.get("pdfUrl"):
        item["pdfUrl"] = _arxiv_pdf_from_url(item.get("url", ""))
    if item.get("openAccessUrl") and not item.get("pdfUrl"):
        item["pdfUrl"] = _arxiv_pdf_from_url(item.get("openAccessUrl", ""))
    if item.get("source") == "arxiv":
        for field in ("url", "openAccessUrl", "pdfUrl"):
            arxiv_year = _arxiv_year_from_url(str(item.get(field, "")))
            if arxiv_year:
                item["year"] = arxiv_year
                break
    item.setdefault("openAccessUrl", item.get("pdfUrl") or item.get("url", ""))
    item.setdefault("abstract", item.get("shortDesc", ""))
    item.setdefault("whyRelated", why)
    item["resourceStatus"] = "pdf" if item.get("pdfUrl") else ("abstract" if item.get("abstract") or item.get("shortDesc") else "link")
    item["readerText"] = _paper_reader_text(item)
    item["learningHint"] = (
        "PDF 可载入" if item["resourceStatus"] == "pdf"
        else "摘要可读"
    )
    return item


def _local_paper_search(query: str, limit: int) -> list[dict]:
    q = query.lower().strip()
    scored = []
    for term in terms:
        haystack = " ".join([
            term.get("term", ""),
            term.get("termEn", ""),
            term.get("termZh", ""),
            term.get("category", ""),
            " ".join(term.get("aliases", [])),
            " ".join(term.get("aliasesEn", [])),
            " ".join(term.get("aliasesZh", [])),
        ]).lower()
        if q and q not in haystack:
            continue
        score = 4 if q and term.get("term", "").lower() == q else 1
        for paper in related_papers_for_term(term):
            item = enrich_paper_resource(paper, f"{term.get('term', '')} 的经典溯源论文")
            item["source"] = "local-kb"
            item["fromTerm"] = term.get("term", "")
            scored.append((score, item))
    seen = set()
    results = []
    for _, paper in sorted(scored, key=lambda item: item[0], reverse=True):
        key = _paper_key(paper)
        if not key or key in seen:
            continue
        seen.add(key)
        results.append(paper)
        if len(results) >= limit:
            break
    return results


def _openalex_search(query: str, limit: int) -> list[dict]:
    params = {
        "search": query,
        "per-page": min(limit, 10),
        "select": "title,publication_year,authorships,cited_by_count,doi,open_access,primary_location,abstract_inverted_index",
    }
    with httpx.Client(timeout=6.0, follow_redirects=True) as client:
        resp = client.get("https://api.openalex.org/works", params=params)
        resp.raise_for_status()
        data = resp.json()
    results = []
    for work in data.get("results", []):
        authors = ", ".join(
            item.get("author", {}).get("display_name", "")
            for item in work.get("authorships", [])[:4]
            if item.get("author", {}).get("display_name")
        )
        location = work.get("primary_location") or {}
        pdf_url = ""
        landing_url = ""
        if isinstance(location, dict):
            pdf_url = location.get("pdf_url") or ""
            landing_url = location.get("landing_page_url") or ""
        oa_url = (work.get("open_access") or {}).get("oa_url") or ""
        abstract = _openalex_abstract(work.get("abstract_inverted_index") or {})
        results.append(enrich_paper_resource({
            "title": _clean(work.get("title", "")),
            "authors": authors,
            "year": work.get("publication_year") or "",
            "citationCount": work.get("cited_by_count") or 0,
            "url": work.get("doi") or landing_url or oa_url or pdf_url or "",
            "openAccessUrl": pdf_url or oa_url or landing_url or "",
            "pdfUrl": pdf_url or _arxiv_pdf_from_url(oa_url),
            "source": "openalex",
            "abstract": abstract,
            "shortDesc": abstract[:260] if abstract else "OpenAlex scholarly metadata result.",
        }))
    return [item for item in results if item.get("title")]


def _openalex_abstract(index: dict) -> str:
    if not isinstance(index, dict) or not index:
        return ""
    words: list[tuple[int, str]] = []
    for word, positions in index.items():
        if isinstance(positions, list):
            words.extend((int(pos), word) for pos in positions if isinstance(pos, int))
    return " ".join(word for _, word in sorted(words))


def _semantic_scholar_search(query: str, limit: int) -> list[dict]:
    params = {
        "query": query,
        "limit": min(limit, 10),
        "fields": "title,authors,year,citationCount,url,abstract,openAccessPdf,externalIds",
    }
    with httpx.Client(timeout=6.0, follow_redirects=True) as client:
        resp = client.get("https://api.semanticscholar.org/graph/v1/paper/search", params=params)
        resp.raise_for_status()
        data = resp.json()
    results = []
    for paper in data.get("data", []):
        authors = ", ".join(a.get("name", "") for a in paper.get("authors", [])[:4] if a.get("name"))
        pdf = paper.get("openAccessPdf") or {}
        results.append(enrich_paper_resource({
            "title": _clean(paper.get("title", "")),
            "authors": authors,
            "year": paper.get("year") or "",
            "citationCount": paper.get("citationCount") or 0,
            "url": paper.get("url") or "",
            "openAccessUrl": pdf.get("url", "") if isinstance(pdf, dict) else "",
            "pdfUrl": pdf.get("url", "") if isinstance(pdf, dict) else "",
            "source": "semantic-scholar",
            "abstract": _clean(paper.get("abstract", "")),
            "shortDesc": _clean(paper.get("abstract", ""))[:260],
        }))
    return [item for item in results if item.get("title")]


def _arxiv_search(query: str, limit: int) -> list[dict]:
    params = {
        "search_query": f'all:"{query}"',
        "start": 0,
        "max_results": min(limit, 8),
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    headers = {"User-Agent": "AI-From-Zero/0.1 (local learning tool)"}
    with httpx.Client(timeout=8.0, follow_redirects=True, headers=headers) as client:
        resp = client.get("https://export.arxiv.org/api/query", params=params)
        resp.raise_for_status()
    root = ET.fromstring(resp.text)
    results = []
    for entry in root.findall("atom:entry", ARXIV_NS):
        title = _clean(entry.findtext("atom:title", default="", namespaces=ARXIV_NS))
        summary = _clean(entry.findtext("atom:summary", default="", namespaces=ARXIV_NS))
        published = entry.findtext("atom:published", default="", namespaces=ARXIV_NS)
        year = ""
        try:
            year = str(datetime.fromisoformat(published.replace("Z", "+00:00")).year)
        except ValueError:
            year_match = re.search(r"(19|20)\d{2}", published)
            year = year_match.group(0) if year_match else ""
        authors = ", ".join(
            _clean(author.findtext("atom:name", default="", namespaces=ARXIV_NS))
            for author in entry.findall("atom:author", ARXIV_NS)[:4]
        )
        url = entry.findtext("atom:id", default="", namespaces=ARXIV_NS)
        pdf_url = ""
        for link in entry.findall("atom:link", ARXIV_NS):
            if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
                pdf_url = link.attrib.get("href", "")
                break
        if not pdf_url:
            pdf_url = _arxiv_pdf_from_url(url)
        results.append(enrich_paper_resource({
            "title": title,
            "authors": authors,
            "year": year,
            "url": url,
            "openAccessUrl": pdf_url or url,
            "pdfUrl": pdf_url,
            "source": "arxiv",
            "abstract": summary,
            "shortDesc": summary[:260],
        }))
    return [item for item in results if item.get("title")]


def search_papers(query: str, limit: int = 8, external: bool = True) -> dict:
    query = _clean(query)
    limit = max(1, min(int(limit or 8), 20))
    if not query:
        return {"query": query, "papers": [], "sourceStatus": {"local": "skipped", "external": "skipped"}}

    papers = []
    seen = set()

    def add_unique(paper: dict) -> bool:
        key = _paper_key(paper)
        if not key or key in seen:
            return False
        seen.add(key)
        papers.append(paper)
        return True

    canonical = _canonical_for_query(query)
    if canonical:
        canonical_item = enrich_paper_resource(canonical, "本地经典论文映射")
        canonical_item.setdefault("source", "curated")
        add_unique(canonical_item)
    local_items = _local_paper_search(query, limit)
    for paper in local_items:
        add_unique(paper)
    status = {"curated": "1 result" if canonical else "skipped", "local": f"{len(local_items)} results", "arxiv": "skipped", "openalex": "skipped", "semanticScholar": "skipped"}

    if external and len(papers) < limit:
        for name, fn in (("arxiv", _arxiv_search), ("openalex", _openalex_search), ("semanticScholar", _semantic_scholar_search)):
            try:
                external_items = fn(query, limit - len(papers))
                status[name] = f"{len(external_items)} results"
                for paper in external_items:
                    key = _paper_key(paper)
                    if not key or key in seen:
                        continue
                    add_unique(paper)
                    if len(papers) >= limit:
                        break
            except Exception as exc:  # External search should never break local reading.
                status[name] = f"error: {type(exc).__name__}"
            if len(papers) >= limit:
                break

    return {"query": query, "papers": papers[:limit], "sourceStatus": status}


def _copy_search_payload(payload: dict) -> dict:
    return {
        "query": payload.get("query", ""),
        "papers": [dict(item) for item in payload.get("papers", [])],
        "sourceStatus": dict(payload.get("sourceStatus", {})),
        "cached": bool(payload.get("cached", False)),
        "latencyMs": int(payload.get("latencyMs", 0)),
    }


def _cache_search(key: str, payload: dict, ttl_seconds: float) -> None:
    if len(_SEARCH_CACHE) >= _SEARCH_CACHE_LIMIT:
        oldest = min(_SEARCH_CACHE, key=lambda item: _SEARCH_CACHE[item][0])
        _SEARCH_CACHE.pop(oldest, None)
    _SEARCH_CACHE[key] = (time.monotonic() + ttl_seconds, _copy_search_payload(payload))


def _paper_matches_query(paper: dict, query: str) -> bool:
    tokens = list(dict.fromkeys(
        token.lower() for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9+.#-]{1,}|[\u4e00-\u9fff]{2,}", query)
    ))
    if not tokens:
        return True
    haystack = " ".join(
        str(paper.get(field, ""))
        for field in ("title", "shortDesc", "abstract", "whyRelated")
    ).lower()
    matched = sum(token in haystack for token in tokens)
    return matched >= (1 if len(tokens) <= 2 else 2)


async def search_papers_realtime(
    query: str,
    limit: int = 8,
    *,
    timeout: float = 4.5,
    cache_ttl: float = _SEARCH_CACHE_TTL_SECONDS,
    local_query: str = "",
) -> dict:
    """Run bounded concurrent scholarly search while preserving local results."""
    started = time.perf_counter()
    query = _clean(query)
    limit = max(1, min(int(limit or 8), 20))
    local_payload = search_papers(_clean(local_query) or query, limit, external=False)
    if not query:
        local_payload["cached"] = False
        local_payload["latencyMs"] = round((time.perf_counter() - started) * 1000)
        return local_payload

    cache_key = f"{query.lower()}::{(_clean(local_query) or query).lower()}::{limit}"
    cached = _SEARCH_CACHE.get(cache_key)
    if cached and cached[0] > time.monotonic():
        payload = _copy_search_payload(cached[1])
        payload["cached"] = True
        payload["latencyMs"] = round((time.perf_counter() - started) * 1000)
        return payload
    if cached:
        _SEARCH_CACHE.pop(cache_key, None)

    providers = {
        "arxiv": _arxiv_search,
        "openalex": _openalex_search,
        "semanticScholar": _semantic_scholar_search,
    }
    remaining = limit
    provider_timeout = max(1.0, min(float(timeout), 5.0))

    async def run_provider(name: str, function) -> tuple[str, list[dict], str]:
        if _PROVIDER_COOLDOWN_UNTIL.get(name, 0.0) > time.monotonic():
            return name, [], "cooldown"
        try:
            items = await asyncio.wait_for(
                asyncio.to_thread(function, query, remaining),
                timeout=provider_timeout,
            )
            _PROVIDER_COOLDOWN_UNTIL.pop(name, None)
            return name, items, f"{len(items)} results"
        except asyncio.TimeoutError:
            _PROVIDER_COOLDOWN_UNTIL[name] = time.monotonic() + _PROVIDER_COOLDOWN_SECONDS
            return name, [], "timeout"
        except Exception as exc:
            _PROVIDER_COOLDOWN_UNTIL[name] = time.monotonic() + _PROVIDER_COOLDOWN_SECONDS
            return name, [], f"error: {type(exc).__name__}"

    tasks = [run_provider(name, function) for name, function in providers.items()]
    results = await asyncio.gather(*tasks)
    papers: list[dict] = []
    seen: set[str] = set()
    status = dict(local_payload.get("sourceStatus", {}))
    for name, items, provider_status in results:
        status[name] = provider_status
        for item in items:
            if not _paper_matches_query(item, query):
                continue
            key = _paper_key(item)
            if not key or key in seen:
                continue
            seen.add(key)
            papers.append(item)
            if len(papers) >= limit:
                break

    papers.sort(
        key=lambda item: (
            int(str(item.get("year", "0"))) if str(item.get("year", "")).isdigit() else 0,
            int(item.get("citationCount") or 0),
        ),
        reverse=True,
    )
    for item in local_payload.get("papers", []):
        if str(item.get("source", "")) not in {"curated"} and not _paper_matches_query(item, query):
            continue
        key = _paper_key(item)
        if not key or key in seen:
            continue
        seen.add(key)
        papers.append(item)
        if len(papers) >= limit:
            break

    payload = {
        "query": query,
        "papers": papers[:limit],
        "sourceStatus": status,
        "cached": False,
        "latencyMs": round((time.perf_counter() - started) * 1000),
    }
    _cache_search(cache_key, payload, max(30.0, float(cache_ttl)))
    return payload


def _download_pdf_text(url: str) -> dict:
    if not url or not url.startswith(("http://", "https://")):
        raise ValueError("no pdf url")
    content = bytearray()
    headers = {"User-Agent": "AI-From-Zero/0.1 (local learning tool)"}
    with httpx.Client(timeout=24.0, follow_redirects=True, headers=headers) as client:
        with client.stream("GET", url) as resp:
            resp.raise_for_status()
            for chunk in resp.iter_bytes():
                content.extend(chunk)
                if len(content) > MAX_PDF_BYTES:
                    raise ValueError("PDF 超过自动载入上限。下载后上传。")
    if not content.startswith(b"%PDF"):
        raise ValueError("链接没有返回 PDF 内容")
    extracted = extract_pdf_pages(bytes(content))
    text = extracted.get("text", "")
    if len(text.strip()) < 80:
        raise ValueError("PDF 文本提取失败，可能是扫描版或受保护文件。")
    return extracted


def load_paper_for_reader(payload: dict) -> dict:
    title = _clean(payload.get("title", ""))
    base = {
        "title": title,
        "url": payload.get("url", ""),
        "openAccessUrl": payload.get("openAccessUrl", ""),
        "pdfUrl": payload.get("pdfUrl", ""),
        "abstract": payload.get("abstract", "") or payload.get("shortDesc", ""),
        "shortDesc": payload.get("shortDesc", ""),
        "source": "request",
    }
    resolved = enrich_paper_resource(base)

    if title:
        search = search_papers(title, limit=5, external=True)
        for paper in search.get("papers", []):
            if _paper_key(paper) == _paper_key(resolved) or not resolved.get("abstract"):
                merged = dict(paper)
                merged.update({k: v for k, v in resolved.items() if v not in (None, "", [])})
                resolved = enrich_paper_resource(merged)
                break
        if not resolved.get("pdfUrl") and search.get("papers"):
            resolved = enrich_paper_resource({**search["papers"][0], **{k: v for k, v in resolved.items() if v not in (None, "", [])}})

    warnings = []
    pdf_url = resolved.get("pdfUrl") or _arxiv_pdf_from_url(resolved.get("openAccessUrl", "")) or _arxiv_pdf_from_url(resolved.get("url", ""))
    if pdf_url:
        try:
            extracted = _download_pdf_text(pdf_url)
            return {
                "loadStatus": "ok",
                "mode": "pdf_text",
                "paper": enrich_paper_resource({**resolved, "pdfUrl": pdf_url}),
                "text": extracted.get("text", ""),
                "textLength": extracted.get("textLength", len(extracted.get("text", ""))),
                "pageCount": extracted.get("pageCount", 0),
                "warnings": extracted.get("warnings", []),
            }
        except Exception as exc:
            warnings.append(f"PDF 自动载入失败：{exc}")

    text = _paper_reader_text(resolved, "全文：下载 PDF 后上传")
    return {
        "loadStatus": "fallback",
        "mode": "abstract",
        "paper": resolved,
        "text": text,
        "textLength": len(text),
        "pageCount": 0,
        "warnings": warnings,
    }


def evidence_snippets(question: str, paper_text: str, known_terms: list[dict], limit: int = 4) -> dict:
    question = _clean(question)
    chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n|(?<=[.!?。！？])\s+", paper_text or "") if chunk.strip()]
    terms_in_question = [
        str(item.get("term", ""))
        for item in known_terms
        if isinstance(item, dict) and item.get("term") and item.get("term", "").lower() in question.lower()
    ]
    query_tokens = [token.lower() for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}|[\u4e00-\u9fff]{2,}", question)]
    scored = []
    for idx, chunk in enumerate(chunks):
        lower = chunk.lower()
        score = sum(2 for term in terms_in_question if term.lower() in lower)
        score += sum(1 for token in query_tokens if token in lower)
        if score:
            scored.append((score, idx, chunk[:700]))
    scored.sort(key=lambda item: (-item[0], item[1]))
    snippets = [
        {"index": idx, "score": score, "text": text}
        for score, idx, text in scored[:limit]
    ]
    top_terms = Counter(terms_in_question).most_common(5)
    return {
        "question": question,
        "snippets": snippets,
        "terms": [name for name, _ in top_terms],
        "suggestedUse": "交给伴学，按证据回答。",
    }
