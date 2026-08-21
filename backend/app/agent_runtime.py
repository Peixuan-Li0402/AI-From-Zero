from __future__ import annotations

import re
from dataclasses import dataclass, field

from .config import settings
from .learning import get_learning_paths
from .papers import search_papers, search_papers_realtime
from .terms import extract_terms_from_text, serialize_term


@dataclass(slots=True)
class LearnerProfile:
    level: str = "探索中"
    goal: str = "系统学习"
    interests: list[str] = field(default_factory=list)
    concise: bool = False

    def prompt_line(self) -> str:
        interests = "、".join(self.interests[:4]) or "尚未明确"
        return f"学习阶段={self.level}；目标={self.goal}；兴趣={interests}；偏好={'简洁' if self.concise else '适中'}"


@dataclass(slots=True)
class AgentPlan:
    intent: str
    search_query: str = ""
    realtime_search: bool = False
    use_llm: bool = True
    max_tokens: int = 800
    progress: str = "正在整理学习线索"


@dataclass(slots=True)
class KnowledgePacket:
    terms: list[dict] = field(default_factory=list)
    papers: list[dict] = field(default_factory=list)
    learning_paths: list[dict] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    search_status: dict = field(default_factory=dict)
    search_latency_ms: int = 0


_REALTIME_WORDS = (
    "最新", "最近", "今年", "当前", "进展", "趋势", "联网", "搜索", "查找",
    "arxiv", "sota", "state of the art", "2025", "2026",
)
_TERM_WORDS = ("解释", "概念", "是什么", "含义", "区别", "关系", "term")
_PATH_WORDS = ("学习路径", "学习路线", "怎么学", "从零学", "roadmap")
_PAPER_WORDS = ("下一篇", "推荐论文", "找论文", "搜论文", "论文推荐", "paper recommendation")
_EVIDENCE_WORDS = ("原文", "证据", "第几页", "依据", "论文里", "作者说", "实验", "消融", "结论")


def _has_any(text: str, phrases: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(phrase in lower for phrase in phrases)


def _clean_search_query(text: str) -> str:
    value = re.sub(
        r"(请|帮我|给我|一下|最新|最近|联网|搜索|查找|推荐|下一篇|论文|学习路径|学习路线|是什么)",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    value = re.sub(r"https?://\S+", " ", value)
    value = re.sub(r"\s+", " ", value).strip(" ，。！？:：")
    return value[:160] or text[:160]


def infer_learner_profile(history: list[dict], latest_text: str) -> LearnerProfile:
    user_text = "\n".join(
        str(item.get("content", ""))
        for item in history[-12:]
        if item.get("role") == "user"
    )
    combined = f"{user_text}\n{latest_text}".lower()
    if any(word in combined for word in ("零基础", "新手", "刚开始", "看不懂", "大一", "高中生")):
        level = "入门"
    elif any(word in combined for word in ("复现", "消融", "研究生", "投稿", "benchmark", "推导", "源码")):
        level = "进阶"
    else:
        level = "探索中"

    if any(word in combined for word in ("比赛", "竞赛", "项目")):
        goal = "做出可落地项目"
    elif any(word in combined for word in ("科研", "论文", "研究", "投稿")):
        goal = "读懂并追踪论文"
    elif any(word in combined for word in ("考试", "课程", "作业")):
        goal = "补齐课程基础"
    else:
        goal = "系统学习"

    interests: list[str] = []
    category_aliases = {
        "大语言模型": ("llm", "大模型", "语言模型", "transformer", "agent", "rag"),
        "计算机视觉": ("cv", "视觉", "图像", "检测", "分割", "diffusion"),
        "强化学习": ("强化学习", "reinforcement", "policy", "reward"),
        "软件工程": ("软件工程", "代码生成", "coding", "repository", "测试"),
        "系统与工程": ("系统", "分布式", "数据库", "网络", "推理优化", "部署"),
    }
    for label, words in category_aliases.items():
        if any(word in combined for word in words):
            interests.append(label)
    concise = any(word in combined for word in ("简短", "简单说", "简单讲", "一句话", "别太长", "精简"))
    return LearnerProfile(level=level, goal=goal, interests=interests, concise=concise)


def route_agent_request(text: str, *, has_documents: bool, has_focus_term: bool) -> AgentPlan:
    lower = text.lower().strip()
    wants_realtime = settings.agent_realtime_search and _has_any(lower, _REALTIME_WORDS)
    wants_notes = any(phrase in text for phrase in ("生成学习笔记", "导出学习笔记", "下载学习笔记"))
    asks_for_papers = _has_any(lower, _PAPER_WORDS) or (
        "论文" in lower and any(word in lower for word in ("搜", "找", "推荐"))
    )
    if asks_for_papers:
        return AgentPlan(
            intent="paper_search",
            search_query=_clean_search_query(text),
            realtime_search=settings.agent_realtime_search,
            use_llm=False,
            max_tokens=900,
            progress="正在查找可直接阅读的论文",
        )
    if _has_any(lower, _PATH_WORDS):
        return AgentPlan(
            intent="learning_path",
            search_query=_clean_search_query(text),
            realtime_search=wants_realtime,
            use_llm=False,
            max_tokens=1000,
            progress="正在匹配论文学习路线",
        )
    if has_documents and (_has_any(lower, _EVIDENCE_WORDS) or lower.endswith(("吗", "呢", "?", "？"))):
        return AgentPlan(
            intent="evidence_qa",
            realtime_search=wants_realtime,
            use_llm=True,
            max_tokens=900,
            progress="正在定位论文原文证据",
        )
    if has_documents:
        return AgentPlan(
            intent="paper_guide",
            realtime_search=wants_realtime,
            use_llm=True,
            max_tokens=1100,
            progress="正在生成论文阅读路线",
        )
    if has_focus_term:
        return AgentPlan(
            intent="term",
            use_llm=False,
            max_tokens=700,
            progress="正在读取双语术语知识库",
        )
    if wants_realtime:
        return AgentPlan(
            intent="topic_research",
            search_query=_clean_search_query(text),
            realtime_search=True,
            use_llm=True,
            max_tokens=900,
            progress="正在核对实时论文来源",
        )
    return AgentPlan(
        intent="notes" if wants_notes else "general",
        use_llm=True,
        max_tokens=700,
        progress="正在整理最有用的学习回答",
    )


def select_terms(text: str, paper_text: str, history: list[dict], limit: int = 20) -> list[dict]:
    context = "\n".join(
        str(item.get("content", ""))
        for item in history[-6:]
        if item.get("role") == "user"
    )
    matches = extract_terms_from_text(f"{text}\n{context}\n{paper_text[:120_000]}")
    return matches[:limit]


async def build_knowledge_packet(
    plan: AgentPlan,
    question: str,
    terms: list[dict],
    profile: LearnerProfile,
) -> KnowledgePacket:
    packet = KnowledgePacket(terms=[serialize_term(term) for term in terms[:12]])
    if packet.terms:
        packet.sources.append(f"AI-From-Zero 双语术语库（命中 {len(packet.terms)} 个概念）")

    if plan.intent == "learning_path":
        interest = plan.search_query or " ".join(profile.interests) or question
        payload = get_learning_paths(interest)
        packet.learning_paths = payload.get("paths", [])[:2]
        packet.sources.append("AI-From-Zero 自建论文学习路径")

    if plan.realtime_search:
        term_query = " ".join(
            str(term.get("termEn") or term.get("term") or "") for term in packet.terms[:3]
        ).strip()
        query = term_query or plan.search_query or question
        payload = await search_papers_realtime(
            query,
            6,
            timeout=settings.agent_search_timeout,
            cache_ttl=settings.agent_search_cache_ttl,
        )
        packet.papers = payload.get("papers", [])
        packet.search_status = payload.get("sourceStatus", {})
        packet.search_latency_ms = int(payload.get("latencyMs", 0))
    elif plan.intent == "paper_search":
        term_query = " ".join(
            str(term.get("termEn") or term.get("term") or "") for term in packet.terms[:3]
        ).strip()
        payload = search_papers(term_query or plan.search_query or question, 6, external=False)
        packet.papers = payload.get("papers", [])
        packet.search_status = payload.get("sourceStatus", {})

    source_labels = {
        "local-kb": "自建经典论文库",
        "arxiv": "arXiv 实时检索",
        "openalex": "OpenAlex 实时检索",
        "semantic-scholar": "Semantic Scholar 实时检索",
        "curated": "自建经典论文库",
    }
    for paper in packet.papers:
        label = source_labels.get(str(paper.get("source", "")), "论文公开元数据")
        if label not in packet.sources:
            packet.sources.append(label)
    return packet


def knowledge_packet_prompt(packet: KnowledgePacket) -> str:
    term_lines = []
    for term in packet.terms[:8]:
        label = term.get("termEn") or term.get("term")
        zh = term.get("termZh") or ""
        explanation = term.get("explanationZh") or term.get("explanation") or ""
        chain = term.get("conceptChain", {}).get("learningOrder", [])
        term_lines.append(
            f"- {label}{f' | {zh}' if zh and zh != label else ''}: {explanation[:260]}"
            + (f"；概念链={' -> '.join(chain[:6])}" if chain else "")
        )
    paper_lines = []
    for paper in packet.papers[:6]:
        paper_lines.append(
            f"- {paper.get('title', '')} ({paper.get('year', '')}) "
            f"source={paper.get('source', '')} url={paper.get('pdfUrl') or paper.get('openAccessUrl') or paper.get('url') or ''} "
            f"summary={(paper.get('shortDesc') or paper.get('abstract') or '')[:260]}"
        )
    return (
        "本地知识库：\n" + ("\n".join(term_lines) or "无")
        + "\n\n论文检索：\n" + ("\n".join(paper_lines) or "无")
    )


def wants_concept_bridge(text: str, term_count: int) -> bool:
    return term_count >= 2 and any(word in text.lower() for word in ("区别", "关系", "对比", "联系", " vs ", "和", "与"))


def format_concept_bridge(terms: list[dict]) -> str:
    selected = [serialize_term(term) for term in terms[:3]]
    if len(selected) < 2:
        return ""
    labels = [str(term.get("termEn") or term.get("term") or "") for term in selected]
    lines = [f"## 概念桥：{' ↔ '.join(labels)}", ""]
    for term, label in zip(selected, labels):
        zh = term.get("termZh") or ""
        explanation = term.get("explanationZh") or term.get("explanation") or "暂无解释。"
        lines.append(f"**{label}{f'｜{zh}' if zh and zh != label else ''}**：{explanation[:240]}")
    chains = []
    for term in selected:
        chain = term.get("conceptChain", {}).get("learningOrder", [])
        if chain:
            chains.append(" → ".join(chain[:6]))
    if chains:
        lines.extend(["", "**概念链**"])
        lines.extend(f"- {chain}" for chain in chains)
    categories = [str(term.get("category", "")) for term in selected if term.get("category")]
    if len(set(categories)) > 1:
        lines.extend(["", f"它们处在不同知识层：{'、'.join(dict.fromkeys(categories))}。先看各自在论文流程中解决什么问题，再比较实现细节。"])
    else:
        lines.extend(["", "先用一句话分别说清“它解决什么问题”，再对照输入、输出和训练方式，关系会更清楚。"])
    return "\n".join(lines)


def format_paper_results(packet: KnowledgePacket, profile: LearnerProfile) -> str:
    lines = ["## 推荐阅读"]
    if not packet.papers:
        lines.extend(["", "目前没有拿到可靠的公开论文链接。可以把方向说得更具体些，比如“RAG 检索优化”或“代码智能体”。"])
        return "\n".join(lines)
    for index, paper in enumerate(packet.papers[:5], 1):
        title = paper.get("title", "推荐论文")
        url = paper.get("pdfUrl") or paper.get("openAccessUrl") or paper.get("url")
        source = paper.get("source", "paper")
        desc = paper.get("shortDesc") or paper.get("abstract", "")[:150]
        lines.append(f"{index}. **[{title}]({url})**" if url else f"{index}. **{title}**")
        details = " · ".join(str(value) for value in (paper.get("year"), source) if value)
        if details:
            lines.append(f"   {details}")
        if desc:
            lines.append(f"   {desc[:180]}")
    if profile.level == "入门":
        lines.extend(["", "先读第 1 篇的摘要和引言，遇到术语直接点进阅读器里的概念链。"])
    else:
        lines.extend(["", "先比较前两篇的问题设定、基线和消融实验，再决定是否深读。"])
    return "\n".join(lines)


def format_learning_paths(packet: KnowledgePacket, profile: LearnerProfile) -> str:
    lines = ["## 论文学习路径"]
    if not packet.learning_paths:
        return "还没匹配到合适的内置路线。告诉我你想学大模型、视觉、强化学习还是 AI Agent。"
    for path in packet.learning_paths:
        lines.extend(["", f"### {path.get('title', path.get('id', '学习路线'))}"])
        for stage in path.get("stages", [])[:4]:
            lines.append(f"**{stage.get('name') or stage.get('title') or '学习阶段'}**")
            items = stage.get("paperItems", [])
            for paper in items[:2]:
                url = paper.get("pdfUrl") or paper.get("openAccessUrl") or paper.get("url")
                title = paper.get("title", "推荐论文")
                lines.append(f"- [{title}]({url})" if url else f"- {title}")
    if profile.level == "入门":
        lines.extend(["", "每一阶段先完成第一篇；读懂摘要、核心术语和方法图后再进入下一篇。"])
    return "\n".join(lines)


def source_footer(packet: KnowledgePacket, evidence_count: int = 0) -> str:
    sources = list(packet.sources)
    if evidence_count:
        sources.insert(0, f"论文原文证据（{evidence_count} 处）")
    if not sources:
        return ""
    return "\n\n**依据：** " + "；".join(sources[:6])
