import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import settings
from .llm import call_kimi
from .pdf import analyze_text_structure
from .terms import extract_terms_from_text, is_known_term, serialize_term


PDF_LLM_CHAR_LIMIT = 120000
PDF_CHUNK_SIZE = 10000
PDF_MAX_CHUNKS = 12
TRANSLATION_CHUNK_SIZE = 4200
TRANSLATION_CHAR_LIMIT = 240000


def local_analysis_fallback(text: str, known_terms: list, status: str, message: str = "") -> dict:
    term_names = [t["term"] for t in known_terms[:8]]
    term_text = "、".join(term_names) if term_names else "暂未在术语库中匹配到明显术语"
    summary = (
        f"本地术语：{term_text}。"
        "配置模型后生成摘要、创新点和翻译。"
    )
    return {
        "summary": summary,
        "tags": [],
        "keyTerms": term_names,
        "innovations": [],
        "translation": "",
        "translationStatus": status,
        "translationCoverage": 0,
        "translatedChars": 0,
        "translationTotalChars": len(text),
        "hoshinoNote": "先看高亮术语；完整分析需要配置模型。",
        "llmStatus": status,
        "llmMessage": message,
    }


def _looks_mostly_chinese(text: str) -> bool:
    sample = text[:6000]
    if not sample:
        return False
    chinese = sum(1 for ch in sample if "\u4e00" <= ch <= "\u9fff")
    letters = sum(1 for ch in sample if ch.isalpha())
    return chinese > 200 and chinese / max(letters, 1) > 0.45


def translate_text_with_llm(text: str, title: str = "") -> dict:
    total_chars = len(text or "")
    if not text.strip():
        return {
            "translation": "",
            "translationStatus": "empty",
            "translationCoverage": 0,
            "translatedChars": 0,
            "translationTotalChars": total_chars,
            "translationMessage": "没有可翻译文本。",
        }
    if not settings.llm_configured:
        return {
            "translation": "",
            "translationStatus": "missing_key",
            "translationCoverage": 0,
            "translatedChars": 0,
            "translationTotalChars": total_chars,
            "translationMessage": "未配置模型，无法生成全文翻译。",
        }
    if _looks_mostly_chinese(text):
        return {
            "translation": "原文已主要是中文，无需翻译。",
            "translationStatus": "source_chinese",
            "translationCoverage": 100,
            "translatedChars": total_chars,
            "translationTotalChars": total_chars,
            "translationMessage": "",
        }

    source_text = text[:TRANSLATION_CHAR_LIMIT]
    chunks = _chunk_text(source_text, TRANSLATION_CHUNK_SIZE)
    def translate_chunk(idx: int, chunk: str) -> tuple[int, str, int, str]:
        prompt = f"""请把下面论文原文第 {idx}/{len(chunks)} 段完整翻译成中文。

要求：
1. 只输出译文，不要总结，不要省略，不要解释你做了什么。
2. 保留公式、变量名、引用编号、表格/图编号和专有名词；英文术语可在首次出现时保留括号原文。
3. 如果某句难以翻译，也要忠实直译，不要跳过。

论文标题：{title}

原文片段：
{chunk}
"""
        raw = call_kimi(
            "你是严谨的论文全文翻译助手。只输出中文译文，绝不省略原文内容。",
            prompt,
            temperature=0.1,
            timeout=min(settings.llm_timeout, 28.0),
            max_tokens=6000,
        )
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {}
        if parsed.get("error"):
            return idx, "", 0, str(parsed.get("error", ""))
        return idx, f"【译文 {idx}/{len(chunks)}】\n{raw.strip()}", len(chunk), ""

    translated: dict[int, tuple[str, int]] = {}
    errors: list[str] = []
    workers = min(settings.paper_llm_concurrency, max(1, len(chunks)))
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="paper-translate") as pool:
        futures = [pool.submit(translate_chunk, idx, chunk) for idx, chunk in enumerate(chunks, 1)]
        for future in as_completed(futures):
            idx, translated_text, char_count, error = future.result()
            if error:
                errors.append(error)
            else:
                translated[idx] = (translated_text, char_count)

    translated_parts = [translated[idx][0] for idx in sorted(translated)]
    translated_chars = sum(translated[idx][1] for idx in translated)
    if errors:
        status = "partial_error" if translated_parts else ("missing_key" if "missing_key" in errors else "error")
        return {
            "translation": "\n\n".join(translated_parts),
            "translationStatus": status,
            "translationCoverage": round(translated_chars / max(total_chars, 1) * 100, 1),
            "translatedChars": translated_chars,
            "translationTotalChars": total_chars,
            "translationMessage": errors[0],
        }

    status = "ok" if total_chars <= TRANSLATION_CHAR_LIMIT else "partial_limit"
    return {
        "translation": "\n\n".join(translated_parts),
        "translationStatus": status,
        "translationCoverage": round(min(translated_chars, total_chars) / max(total_chars, 1) * 100, 1),
        "translatedChars": min(translated_chars, total_chars),
        "translationTotalChars": total_chars,
        "translationMessage": "" if status == "ok" else f"文本超过 {TRANSLATION_CHAR_LIMIT} 字符，已翻译前 {TRANSLATION_CHAR_LIMIT} 字符。",
    }


def analyze_paper_with_llm(text: str, title: str = "", known_terms: list | None = None) -> dict:
    known_terms = known_terms or []
    if not settings.llm_configured:
        return local_analysis_fallback(text, known_terms, "missing_key", "KIMI_API_KEY is not configured.")

    truncated = text[:12000]
    prompt = f"""你是AI论文分析助手。分析论文，输出JSON。翻译会由另一个全文翻译流程完成，所以这里不要输出长篇翻译。

{{
  "summary": "2-3句话中文概括论文核心内容",
  "tags": ["标签1"],
  "keyTerms": ["术语1"],
  "innovations": ["创新点1"],
  "translation": "",
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
    translation = translate_text_with_llm(text, title)
    parsed["translation"] = translation["translation"]
    parsed["translationStatus"] = translation["translationStatus"]
    parsed["translationCoverage"] = translation["translationCoverage"]
    parsed["translatedChars"] = translation["translatedChars"]
    parsed["translationTotalChars"] = translation["translationTotalChars"]
    parsed["translationMessage"] = translation["translationMessage"]
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
        "translationStatus": llm_result.get("translationStatus", ""),
        "translationCoverage": llm_result.get("translationCoverage", 0),
        "translatedChars": llm_result.get("translatedChars", 0),
        "translationTotalChars": llm_result.get("translationTotalChars", len(text)),
        "translationMessage": llm_result.get("translationMessage", ""),
        "paperStructure": analyze_text_structure(text),
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

    def summarize_chunk(idx: int, chunk: str) -> tuple[int, dict]:
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
        raw = call_kimi(
            "你是一个严谨的论文片段总结助手。始终输出有效JSON。",
            prompt,
            0.2,
            timeout=min(settings.llm_timeout, 24.0),
            max_tokens=1200,
        )
        try:
            parsed = json.loads(re.sub(r"^```json\s*|\s*```$", "", raw.strip()))
        except json.JSONDecodeError:
            parsed = {"summary": raw[:500], "keyTerms": [], "innovations": []}
        return idx, parsed

    summaries: dict[int, dict] = {}
    workers = min(settings.paper_llm_concurrency, max(1, len(chunks)))
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="paper-summary") as pool:
        futures = [pool.submit(summarize_chunk, idx, chunk) for idx, chunk in enumerate(chunks, 1)]
        for future in as_completed(futures):
            idx, parsed = future.result()
            if parsed.get("error"):
                return local_analysis_fallback(text, known_terms, "error", str(parsed.get("error", "")))
            summaries[idx] = parsed
    chunk_summaries = [summaries[idx] for idx in sorted(summaries)]

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
  "translation": "",
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
    translation = translate_text_with_llm(text, title)
    parsed["translation"] = translation["translation"]
    parsed["translationStatus"] = translation["translationStatus"]
    parsed["translationCoverage"] = translation["translationCoverage"]
    parsed["translatedChars"] = translation["translatedChars"]
    parsed["translationTotalChars"] = translation["translationTotalChars"]
    parsed["translationMessage"] = translation["translationMessage"]
    parsed.setdefault("hoshinoNote", "")
    parsed["llmStatus"] = "ok"
    parsed["llmMessage"] = "PDF 已按片段完成综合分析。" + (" 超长内容仅前 120000 个字符送入 LLM。" if truncated else "")
    return parsed


def build_pdf_analysis_response(text: str, title: str = "", truncated: bool = False) -> dict:
    known_terms = extract_terms_from_text(text)
    llm_result = analyze_long_paper_with_llm(text, title, known_terms, truncated)
    llm_terms = llm_result.get("keyTerms", [])
    unknown_terms = [t for t in llm_terms if isinstance(t, str) and not is_known_term(t)]
    return {
        "knownTerms": [serialize_term(t) for t in known_terms],
        "unknownTerms": unknown_terms,
        "analysis": llm_result,
        "translation": llm_result.get("translation", ""),
        "translationStatus": llm_result.get("translationStatus", ""),
        "translationCoverage": llm_result.get("translationCoverage", 0),
        "translatedChars": llm_result.get("translatedChars", 0),
        "translationTotalChars": llm_result.get("translationTotalChars", len(text)),
        "translationMessage": llm_result.get("translationMessage", ""),
        "paperStructure": analyze_text_structure(text),
        "llmStatus": llm_result.get("llmStatus", "ok"),
        "llmMessage": llm_result.get("llmMessage", ""),
    }


def analyze_case_study_text(text: str) -> dict:
    if not settings.llm_configured:
        local_terms = extract_terms_from_text(text)
        return {
            "hoshinoAnalysis": "本地术语匹配。完整案例分析需要配置模型。",
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
