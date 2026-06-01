import json
import re

from .config import settings
from .llm import call_kimi
from .terms import extract_terms_from_text, is_known_term, serialize_term


PDF_LLM_CHAR_LIMIT = 120000
PDF_CHUNK_SIZE = 10000
PDF_MAX_CHUNKS = 12


def local_analysis_fallback(text: str, known_terms: list, status: str, message: str = "") -> dict:
    term_names = [t["term"] for t in known_terms[:8]]
    term_text = "、".join(term_names) if term_names else "暂未在术语库中匹配到明显术语"
    summary = (
        "已完成本地术语匹配。"
        f"当前文本识别到的重点术语包括：{term_text}。"
        "配置 KIMI_API_KEY 后可以继续生成论文摘要、创新点和中文翻译。"
    )
    return {
        "summary": summary,
        "tags": [],
        "keyTerms": term_names,
        "innovations": [],
        "translation": "",
        "hoshinoNote": "本地术语先标出来了っす；如果要完整分析和翻译，记得先设置 KIMI_API_KEY。",
        "llmStatus": status,
        "llmMessage": message,
    }


def analyze_paper_with_llm(text: str, title: str = "", known_terms: list | None = None) -> dict:
    known_terms = known_terms or []
    if not settings.llm_configured:
        return local_analysis_fallback(text, known_terms, "missing_key", "KIMI_API_KEY is not configured.")

    truncated = text[:12000]
    prompt = f"""你是AI论文分析助手。分析论文，输出JSON。JSON必须包含translation字段（完整中文翻译，必须逐句翻译，不能省略）。

{{
  "summary": "2-3句话中文概括论文核心内容",
  "tags": ["标签1"],
  "keyTerms": ["术语1"],
  "innovations": ["创新点1"],
  "translation": "完整中文翻译（必须！如果原文是英文则全部翻译成中文；如果原文已经是中文则写：原文已是中文）",
  "hoshinoNote": "用星野大叔的口吻（慵懒、带〜っす、自称大叔）写一段点评"
}}

论文标题：{title}
论文：{truncated[:6000]}

只输出JSON，不要其他文字。"""

    result = call_kimi("你是一个论文分析助手。始终输出有效JSON。", prompt, temperature=0.2)
    json_str = re.sub(r"^```json\s*", "", result.strip())
    json_str = re.sub(r"\s*```$", "", json_str)
    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError:
        return local_analysis_fallback(text, known_terms, "error", "LLM returned non-JSON content.")

    if parsed.get("error"):
        status = "missing_key" if parsed.get("error") == "missing_key" else "error"
        return local_analysis_fallback(text, known_terms, status, str(parsed.get("error", "")))

    parsed.setdefault("summary", "（暂无摘要）")
    parsed.setdefault("tags", [])
    parsed.setdefault("keyTerms", [])
    parsed.setdefault("innovations", [])
    parsed.setdefault("translation", "")
    parsed.setdefault("hoshinoNote", "")
    parsed["llmStatus"] = "ok"
    parsed["llmMessage"] = ""
    return parsed


def build_analysis_response(text: str, title: str = "") -> dict:
    known_terms = extract_terms_from_text(text)
    llm_result = analyze_paper_with_llm(text, title=title, known_terms=known_terms)
    llm_terms = llm_result.get("keyTerms", [])
    unknown_terms = [t for t in llm_terms if isinstance(t, str) and not is_known_term(t)]
    return {
        "knownTerms": [serialize_term(t) for t in known_terms],
        "unknownTerms": unknown_terms,
        "analysis": llm_result,
        "translation": llm_result.get("translation", ""),
        "llmStatus": llm_result.get("llmStatus", "ok"),
        "llmMessage": llm_result.get("llmMessage", ""),
    }


def _chunk_text(text: str, chunk_size: int = PDF_CHUNK_SIZE) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        paragraph_break = text.rfind("\n\n", start, end)
        if paragraph_break > start + chunk_size // 2:
            end = paragraph_break
        chunks.append(text[start:end].strip())
        start = end
    return [chunk for chunk in chunks if chunk]


def analyze_long_paper_with_llm(text: str, title: str, known_terms: list, truncated: bool = False) -> dict:
    if not settings.llm_configured or len(text) <= 12000:
        result = analyze_paper_with_llm(text, title=title, known_terms=known_terms)
        if truncated and result.get("llmStatus") == "ok":
            result["llmMessage"] = "PDF 很长，只有前 120000 个字符送入 LLM 分块分析，阅读区仍展示已提取全文。"
        return result

    chunks = _chunk_text(text[:PDF_LLM_CHAR_LIMIT])[:PDF_MAX_CHUNKS]
    chunk_summaries = []
    for idx, chunk in enumerate(chunks, 1):
        prompt = f"""你是论文阅读助手。请总结 PDF 第 {idx}/{len(chunks)} 个片段，输出JSON。
{{
  "summary": "这个片段的中文摘要",
  "keyTerms": ["术语"],
  "innovations": ["可能的创新点或方法"]
}}

论文标题：{title}
片段内容：
{chunk[:9000]}

只输出JSON。"""
        raw = call_kimi("你是一个严谨的论文片段总结助手。始终输出有效JSON。", prompt, 0.2)
        try:
            parsed = json.loads(re.sub(r"^```json\s*|\s*```$", "", raw.strip()))
        except json.JSONDecodeError:
            parsed = {"summary": raw[:500], "keyTerms": [], "innovations": []}
        if parsed.get("error"):
            return local_analysis_fallback(text, known_terms, "error", str(parsed.get("error", "")))
        chunk_summaries.append(parsed)

    combined = "\n".join(
        f"片段{i+1}: {item.get('summary', '')}\n术语: {', '.join(item.get('keyTerms', []))}\n创新点: {', '.join(item.get('innovations', []))}"
        for i, item in enumerate(chunk_summaries)
    )
    final_prompt = f"""你是 AI 论文分析助手。下面是对一篇长 PDF 的分块摘要，请合并为完整阅读结果，输出JSON。
{{
  "summary": "2-4句话中文概括整篇论文",
  "tags": ["标签"],
  "keyTerms": ["术语"],
  "innovations": ["创新点"],
  "translation": "这是一篇长文档，请说明已完成全文提取；如需逐段翻译，可在右侧伴学中继续提问。",
  "hoshinoNote": "用星野大叔口吻写一段阅读建议"
}}

论文标题：{title}
本地已识别术语：{', '.join([t['term'] for t in known_terms[:30]])}
是否因过长只送入部分内容：{truncated}

分块摘要：
{combined}

只输出JSON。"""
    raw = call_kimi("你是一个论文分析助手。始终输出有效JSON。", final_prompt, 0.2)
    json_str = re.sub(r"^```json\s*", "", raw.strip())
    json_str = re.sub(r"\s*```$", "", json_str)
    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError:
        return local_analysis_fallback(text, known_terms, "error", "LLM returned non-JSON content.")
    if parsed.get("error"):
        return local_analysis_fallback(text, known_terms, "error", str(parsed.get("error", "")))
    parsed.setdefault("summary", "（暂无摘要）")
    parsed.setdefault("tags", [])
    parsed.setdefault("keyTerms", [])
    parsed.setdefault("innovations", [])
    parsed.setdefault("translation", "")
    parsed.setdefault("hoshinoNote", "")
    parsed["llmStatus"] = "ok"
    parsed["llmMessage"] = "PDF 已按片段完成综合分析。" + (" 超长内容仅前 120000 个字符送入 LLM。" if truncated else "")
    return parsed


def build_pdf_analysis_response(text: str, title: str = "", truncated: bool = False) -> dict:
    known_terms = extract_terms_from_text(text)
    llm_text = text[:PDF_LLM_CHAR_LIMIT]
    llm_result = analyze_long_paper_with_llm(llm_text, title, known_terms, truncated)
    llm_terms = llm_result.get("keyTerms", [])
    unknown_terms = [t for t in llm_terms if isinstance(t, str) and not is_known_term(t)]
    return {
        "knownTerms": [serialize_term(t) for t in known_terms],
        "unknownTerms": unknown_terms,
        "analysis": llm_result,
        "translation": llm_result.get("translation", ""),
        "llmStatus": llm_result.get("llmStatus", "ok"),
        "llmMessage": llm_result.get("llmMessage", ""),
    }


def analyze_case_study_text(text: str) -> dict:
    if not settings.llm_configured:
        local_terms = extract_terms_from_text(text)
        return {
            "hoshinoAnalysis": "还没有配置 KIMI_API_KEY，所以大叔先做本地术语匹配。配置 Key 后可以生成完整案例分析っす。",
            "involvedFields": sorted({t.get("category", "其他") for t in local_terms}),
            "keyTerms": [t["term"] for t in local_terms[:12]],
            "learningPath": [],
            "careerDirections": "",
            "llmStatus": "missing_key",
        }

    prompt_content = (
        "你是一个AI应用分析专家+学习路径规划专家。分析以下案例用了什么AI技术，给出详细学习路径。"
        "JSON格式：{hoshinoAnalysis:星野语气分析（自称大叔、带〜っす）,involvedFields:[技术领域],"
        "keyTerms:[核心术语],learningPath:[{fieldName:领域名,recommendation:学习建议,"
        "skills:[Python/PyTorch/数据结构],startPapers:[入门论文],advancedPapers:[进阶论文]}],"
        "careerDirections:发展建议}。案例："
        + text[:3000]
    )
    result_str = call_kimi("你是星野大叔和AI技术分析专家。回答中文。", prompt_content, 0.7)
    try:
        json_match = re.search(r"\{.*\}", result_str, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception:
        pass
    try:
        return json.loads(result_str)
    except Exception:
        return {"hoshinoAnalysis": "呜嘿～大叔没完全分析出来", "involvedFields": [], "keyTerms": [], "learningPath": [], "careerDirections": "", "llmStatus": "error"}
