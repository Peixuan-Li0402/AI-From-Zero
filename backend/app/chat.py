import json
import re

from .config import settings
from .llm import call_llm
from .models import ChatRequest
from .terms import extract_terms_from_text, get_term


def _term_names(known_terms: list[dict]) -> list[str]:
    names = []
    for item in known_terms:
        if isinstance(item, dict) and item.get("term"):
            names.append(str(item["term"]))
    return names[:20]


def local_chat_response(request: ChatRequest) -> dict:
    text = request.message.strip()
    lower = text.lower()
    current = get_term(request.currentTerm) if request.currentTerm else None
    local_terms = extract_terms_from_text(" ".join([text, request.paperText[:4000]]))
    names = _term_names(request.knownTerms) or [term["term"] for term in local_terms[:8]]

    if current and ("解释" in text or "这个" in text or "term" in lower):
        answer = (
            f"「{current['term']}」：{current.get('explanation', '')}\n\n"
            f"先补：{', '.join(current.get('prerequisiteTerms', []) or ['暂无'])}。\n"
            "回到论文：看它解决哪一步卡点。"
        )
    elif "概念链" in text or "chain" in lower or "关联" in text or "关系" in text:
        focus = names[:3] or ["Transformer", "Attention", "Neural Network"]
        answer = (
            "概念顺序：\n"
            f"先补基础：{focus[0]}\n"
            f"再看核心：{focus[1] if len(focus) > 1 else focus[0]}\n"
            f"最后延伸：{focus[-1]}\n\n"
            "点高亮术语，再回方法段。"
        )
    elif "下一步" in text or "学习" in text or "learn" in lower:
        answer = "下一步：看 " + "、".join(names[:8]) + "。目标：说清它们在论文里做什么。"
    elif "摘要" in text or "总结" in text or "summary" in lower:
        answer = request.paperSummary or "重点术语：" + "、".join(names[:8])
    elif names:
        answer = "先看：" + "、".join(names[:8]) + "。可继续问：它在方法里起什么作用？"
    else:
        answer = "上传论文，或点一个术语。"

    return {
        "reply": answer,
        "llmStatus": "missing_key",
        "usedContext": {"terms": names, "currentTerm": request.currentTerm or ""},
    }


def chat_with_context(request: ChatRequest) -> dict:
    if request.localOnly or not settings.llm_configured:
        return local_chat_response(request)

    history = "\n".join(
        f"{item.get('role', 'user')}: {str(item.get('content', ''))[:500]}"
        for item in request.history[-8:]
        if isinstance(item, dict)
    )
    term_names = _term_names(request.knownTerms)
    current_term = get_term(request.currentTerm) if request.currentTerm else None
    current_term_text = ""
    if current_term:
        current_term_text = json.dumps({
            "term": current_term.get("term"),
            "fullName": current_term.get("fullName"),
            "explanation": current_term.get("explanation"),
            "prerequisiteTerms": current_term.get("prerequisiteTerms", []),
            "relatedTerms": current_term.get("relatedTerms", []),
        }, ensure_ascii=False)
    evidence_text = "\n".join(
        f"- {str(item.get('text', ''))[:800]}"
        for item in request.evidenceSnippets[:5]
        if isinstance(item, dict) and item.get("text")
    )

    prompt = f"""你是 AI-From-Zero 的右侧 AI 伴学助手，风格参考“小鸟游星野”：慵懒、温柔、像可靠前辈，可称用户 sensei，可自称“大叔”，偶尔使用“呜嘿～”“っす”。
但你首先是论文学习教练：回答要中文、准确、适合 AI 入门学习者；不要过度卖萌，不要用语气掩盖不确定性。
你可以结合当前论文、术语库和已掌握术语来回答。不要编造不存在的论文细节；不确定时说明需要更多上下文。
每次回复尽量做到：先安抚一下，再给出 2-4 个可执行学习步骤，最后提醒用户回到论文中的具体段落或术语。

当前论文摘要：
{request.paperSummary[:1500]}

当前论文片段：
{request.paperText[:8000]}

已识别术语：
{', '.join(term_names)}

当前打开术语：
{current_term_text or '无'}

证据片段（如果有，请优先基于这些片段回答）：
{evidence_text or '无'}

已掌握术语：
{', '.join(request.masteredTerms[:30])}

最近对话：
{history or '无'}

用户问题：
{request.message}

请直接给出伴学回复，可以包含简短步骤或建议。"""
    result = call_llm("你是小鸟游星野式的 AI 论文伴学教练，温柔但严谨。", prompt, temperature=0.55)
    try:
        parsed = json.loads(result)
    except json.JSONDecodeError:
        parsed = {}
    if parsed.get("error"):
        fallback = local_chat_response(request)
        fallback["llmStatus"] = "error"
        fallback["llmMessage"] = str(parsed.get("error", "LLM unavailable"))
        return fallback
    return {
        "reply": result.strip(),
        "llmStatus": "ok",
        "usedContext": {"terms": term_names, "currentTerm": request.currentTerm or ""},
    }
