from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse

from .analysis import PDF_LLM_CHAR_LIMIT, analyze_case_study_text, build_analysis_response, build_pdf_analysis_response
from .chat import chat_with_context
from .config import FRONTEND_DIR, PROVIDER_PRESETS, provider_by_id, save_env_updates, settings
from .demo_cases import list_demo_cases, load_demo_case
from .integrations import integration_status, process_inbound_message, send_message
from .learning import get_learning_paths
from .llm import test_llm_config
from .models import (
    ChatRequest,
    ConfigSaveRequest,
    ConfigTestRequest,
    EvidenceRequest,
    LearningSessionRequest,
    MasteryUpdateRequest,
    PaperLoadRequest,
    PaperAnalysis,
    IntegrationInboundRequest,
    IntegrationSendRequest,
)
from .papers import evidence_snippets, load_paper_for_reader, search_papers
from .pdf import extract_pdf_pages
from .progress import create_learning_session, get_learning_profile, update_mastery
from .terms import get_term, list_terms_by_category, related_papers_for_term, serialize_term, term_kb, terms, terms_index


router = APIRouter()


def _is_local_request(request: Request) -> bool:
    host = request.client.host if request.client else ""
    return host in {"127.0.0.1", "::1", "localhost", "testclient", ""} or host.endswith("127.0.0.1")


def _config_payload() -> dict:
    return {
        "provider": settings.llm_provider,
        "apiUrl": settings.llm_api_url,
        "model": settings.llm_model,
        "timeout": settings.llm_timeout,
        "llmConfigured": settings.llm_configured,
        "maskedKey": settings.masked_key(),
        "configWritable": settings.config_writable,
    }


@router.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": settings.app_version,
        "termsTotal": len(terms),
        "termCount": len(terms),
        "termIndexSize": len(terms_index),
        "llmConfigured": settings.llm_configured,
        "llmProvider": settings.llm_provider,
        "llmModel": settings.llm_model,
        "model": settings.llm_model,
        "configWritable": settings.config_writable,
        "agentProtocol": "openai-compatible-v1",
        "agentModel": settings.qxd_model_id,
        "agentAuthConfigured": settings.qxd_configured,
        "publicBaseUrlConfigured": bool(settings.public_base_url),
        "attachmentLimitMb": settings.qxd_max_attachment_mb,
        "hoshino": "AI-From-Zero ready",
    }


@router.get("/api/config/providers")
async def config_providers():
    return {"providers": [preset.model_dump() for preset in PROVIDER_PRESETS]}


@router.get("/api/config")
async def get_config():
    return _config_payload()


@router.post("/api/config/test")
async def test_config(data: ConfigTestRequest):
    preset = provider_by_id(data.provider)
    api_url = data.apiUrl.strip() or preset.api_url
    model = data.model.strip() or preset.model
    api_key = data.apiKey.strip() or settings.llm_api_key
    if preset.requires_key and not api_key:
        return {"ok": False, "provider": data.provider, "message": "请先填写 API Key"}
    return test_llm_config(data.provider, api_url, api_key, model, data.timeout)


@router.post("/api/config/save")
async def save_config(data: ConfigSaveRequest, request: Request):
    if not _is_local_request(request):
        raise HTTPException(status_code=403, detail="配置只能从本机保存")
    preset = provider_by_id(data.provider)
    api_url = data.apiUrl.strip() or preset.api_url
    model = data.model.strip() or preset.model
    updates = {
        "LLM_PROVIDER": data.provider,
        "LLM_API_URL": api_url,
        "LLM_MODEL": model,
        "LLM_TIMEOUT": str(data.timeout or 60),
        "APP_HOST": settings.app_host,
        "APP_PORT": str(settings.app_port),
    }
    if data.apiKey.strip():
        updates["LLM_API_KEY"] = data.apiKey.strip()
    save_env_updates(updates)
    return _config_payload()


@router.get("/api/terms")
async def list_terms():
    return list_terms_by_category()


@router.get("/api/terms/{term_name}")
async def get_term_detail(term_name: str):
    info = get_term(term_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"术语 '{term_name}' 不在知识库中")
    return serialize_term(info)


@router.post("/api/terms/{term_name}/papers")
async def expand_term_papers(term_name: str):
    info = get_term(term_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"术语 '{term_name}' 不在知识库中")
    return {"term": info["term"], "papers": related_papers_for_term(info)}


@router.get("/api/terms/{term_name}/explain")
async def detailed_term_explain(term_name: str):
    info = get_term(term_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"术语 '{term_name}' 不在知识库中")
    if not settings.llm_configured:
        return {
            "term": info["term"],
            "fullName": info.get("fullName", ""),
            "basicExplanation": info.get("explanation", ""),
            "hoshinoNote": info.get("hoshinoNote", ""),
            "detailedExplanation": "还没有配置 KIMI_API_KEY，所以大叔先显示知识库里的基础解释。设置环境变量后，这里会生成更通俗、更完整的讲解。",
            "landmarkPapers": info.get("landmarkPapers", []),
            "prerequisiteTerms": info.get("prerequisiteTerms", []),
            "mastered": False,
            "llmStatus": "missing_key",
        }

    from .llm import call_kimi

    prompt = f"""你是小鸟游星野（AI小助手），用慵懒随性、自称大叔的风格解释AI概念。

请用星野的语气，对这个术语做一次非常详细、非常通俗、非常生活化的解释。
要求：
1. 先做一个超简单的比喻（用生活中的东西类比）
2. 再讲它的核心原理（易懂版）
3. 说它为什么重要、在哪儿用
4. 举一个具体的例子
5. 用星野的语气收尾：慵懒、带〜っす、自称大叔

术语：{info['term']}（{info['fullName']}）
分类：{info['category']}
现有解释参考：{info.get('explanation', '')[:200]}
前置知识：{', '.join(info.get('prerequisiteTerms', [])) if info.get('prerequisiteTerms') else '无'}

请用中文回复，字数500字以上，越详细越好。"""
    result = call_kimi("你是一个AI概念科普专家，用星野大叔的语气解释。", prompt, temperature=0.7)
    return {
        "term": info["term"],
        "fullName": info.get("fullName", ""),
        "basicExplanation": info.get("explanation", ""),
        "hoshinoNote": info.get("hoshinoNote", ""),
        "detailedExplanation": result,
        "landmarkPapers": info.get("landmarkPapers", []),
        "prerequisiteTerms": info.get("prerequisiteTerms", []),
        "mastered": False,
        "llmStatus": "ok",
    }


@router.get("/api/terms/{term_name}/explain-academic")
async def academic_term_explain(term_name: str):
    info = get_term(term_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"术语 '{term_name}' 不在知识库中")
    if not settings.llm_configured:
        return {
            "term": info["term"],
            "fullName": info.get("fullName", ""),
            "academicExplanation": "未配置 KIMI_API_KEY，暂时无法生成学术详细版。当前弹窗中的基础解释和经典论文仍可正常使用。",
            "llmStatus": "missing_key",
        }

    from .llm import call_kimi

    prompt = f"""你是清华大学AI专业的教授，正在给大一新生讲解AI概念。请用中文写一段严肃、专业、详细的学术解释。

要求：
1. 用教科书级别的严谨语言，解释该术语的数学/算法原理
2. 包含技术细节：公式推导思路、算法步骤、关键参数含义（如果有）
3. 解释该术语在AI发展史中的位置——它解决了什么问题？之前的方法有什么不足？
4. 说明它的局限性——这方法有什么缺点？后来的方法是怎么改进的？
5. 包含相关公式，用文字描述（不用LaTeX格式）
6. 给出具体的应用场景和实例
7. 引用经典论文时标出作者和年份
8. 篇幅：800字以上，越详细越好

术语：{info["term"]}（{info["fullName"]}）
分类：{info["category"]}
已有解释：{info.get("explanation", "")[:200]}
前置知识：{", ".join(info.get("prerequisiteTerms", [])) if info.get("prerequisiteTerms") else "无"}
相关论文：{"; ".join([p["title"] for p in info.get("landmarkPapers", [])])}

只输出纯文字学术解释，不要JSON包装。"""
    result = call_kimi("你是清华大学的AI教授，严谨专业的学术风格。", prompt, temperature=0.3)
    return {"term": info["term"], "fullName": info.get("fullName", ""), "academicExplanation": result, "llmStatus": "ok"}


@router.post("/api/case-study")
async def analyze_case_study(data: dict | None = None):
    text = (data or {}).get("text", "").strip()
    if not text or len(text) < 10:
        raise HTTPException(status_code=400, detail="案例描述至少需要10个字符")
    return analyze_case_study_text(text)


@router.post("/api/chat")
async def chat(request: ChatRequest):
    text = request.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="消息不能为空")
    return chat_with_context(request)


@router.get("/api/learning/profile")
async def learning_profile():
    return get_learning_profile()


@router.post("/api/learning/session")
async def learning_session(data: LearningSessionRequest):
    return create_learning_session(data)


@router.post("/api/learning/mastery")
async def learning_mastery(data: MasteryUpdateRequest):
    try:
        return update_mastery(data.term, data.mastered)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/demo-cases")
async def demo_cases():
    return list_demo_cases()


@router.post("/api/demo-cases/{case_id}/load")
async def demo_case_load(case_id: str):
    try:
        return load_demo_case(case_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/api/integrations/status")
async def integrations_status():
    return integration_status()


@router.post("/api/integrations/messages/inbound")
async def integrations_inbound(data: IntegrationInboundRequest):
    try:
        return process_inbound_message(data.channel, data.text, sender=data.sender, token=data.token, metadata=data.metadata)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/integrations/messages/send")
async def integrations_send(data: IntegrationSendRequest):
    try:
        return send_message(data.channel, data.text, token=data.token, markdown=data.markdown)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/papers/search")
async def paper_search(query: str = "", limit: int = 8, external: bool = True):
    return search_papers(query, limit=limit, external=external)


@router.post("/api/papers/load")
async def paper_load(data: PaperLoadRequest):
    if not data.title.strip() and not data.url.strip() and not data.pdfUrl.strip() and not data.abstract.strip():
        raise HTTPException(status_code=400, detail="至少需要提供论文标题、链接、PDF 或摘要")
    return load_paper_for_reader(data.model_dump())


@router.post("/api/papers/evidence")
async def paper_evidence(data: EvidenceRequest):
    if not data.paperText.strip():
        raise HTTPException(status_code=400, detail="paperText is required")
    return evidence_snippets(data.question, data.paperText, data.knownTerms)


@router.post("/api/analyze-pdf")
async def analyze_pdf(file: UploadFile = File(...)):
    filename = file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只接受PDF文件")
    try:
        extracted = extract_pdf_pages(await file.read())
        text = extracted["text"]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        return {
            "error": str(e),
            "text": "",
            "pages": [],
            "pageCount": 0,
            "textLength": 0,
            "truncated": False,
            "extractionWarnings": [],
            "paperStructure": {},
            "knownTerms": [],
            "unknownTerms": [],
            "analysis": {},
            "translation": "",
            "llmStatus": "error",
        }

    if not text.strip() or len(text.strip()) < 50:
        return {
            "error": "PDF文本提取失败，可能是扫描版PDF或文字太少。",
            "text": "",
            "pages": extracted.get("pages", []),
            "pageCount": extracted.get("pageCount", 0),
            "textLength": extracted.get("textLength", 0),
            "truncated": False,
            "extractionWarnings": extracted.get("warnings", []),
            "paperStructure": extracted.get("structure", {}),
            "knownTerms": [],
            "unknownTerms": [],
            "analysis": {},
            "translation": "",
            "llmStatus": "error",
        }

    truncated = len(text) > PDF_LLM_CHAR_LIMIT
    response = build_pdf_analysis_response(text, title=filename.replace(".pdf", ""), truncated=truncated)
    response["text"] = text
    response["pages"] = extracted.get("pages", [])
    response["pageCount"] = extracted.get("pageCount", 0)
    response["textLength"] = extracted.get("textLength", len(text))
    response["truncated"] = truncated
    response["extractionWarnings"] = extracted.get("warnings", [])
    response["paperStructure"] = extracted.get("structure", response.get("paperStructure", {}))
    if truncated:
        response["extractionWarnings"].append(
            f"PDF 已完整提取，但 LLM 分析只使用前 {PDF_LLM_CHAR_LIMIT} 个字符；阅读区展示全文。"
        )
    return response


@router.post("/api/analyze")
async def analyze_text(request: PaperAnalysis):
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="文本不能为空")
    if len(text) < 50:
        raise HTTPException(status_code=400, detail="文本太短，至少50个字符")
    return build_analysis_response(text, title=request.title)


@router.post("/api/learn-path")
async def learn_path(data: dict | None = None):
    return get_learning_paths((data or {}).get("interest", "").strip())


@router.get("/")
async def index():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(index_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>AI From Zero</h1><p>欢迎！请先构建前端。</p>")
