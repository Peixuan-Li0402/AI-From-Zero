"""
从零开始的人工智能生活 — 后端服务器

入口：运行 python server.py
访问：http://localhost:8080
"""

import json
import os
import re
import sys
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ── 路径 ──
ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
KNOWLEDGE = ROOT / "knowledge"
DATA = ROOT / "data"
TERM_KB_PATH = KNOWLEDGE / "term_kb.json"

# ── 加载知识库 ──
with open(TERM_KB_PATH, encoding="utf-8") as f:
    term_kb = json.load(f)

terms_index = {t["term"].lower(): t for t in term_kb["terms"]}
terms_index.update({a.lower(): t for t in term_kb["terms"] for a in t.get("aliases", [])})

# ── KIMI API ──
KIMI_API_KEY = os.environ.get(
    "KIMI_API_KEY",
    "sk-6PS9yQUuvtRSmK1EgnnbwA2xsx7yVSjwM19EVmYm9YwwwXgJ",
)
KIMI_API_URL = "https://api.moonshot.cn/v1/chat/completions"


# ── FastAPI ──
app = FastAPI(title="AI From Zero", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载前端静态文件
app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="frontend")


# ═══════════════════════════════════
#  数据模型
# ═══════════════════════════════════

class PaperRequest(BaseModel):
    text: str
    title: str = ""

class PaperAnalysis(BaseModel):
    text: str

class MarkMastery(BaseModel):
    term: str
    mastered: bool = True


# ═══════════════════════════════════
#  工具函数
# ═══════════════════════════════════

def call_kimi(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
    """调用 Kimi API 进行文本分析"""
    try:
        resp = httpx.post(
            KIMI_API_URL,
            headers={
                "Authorization": f"Bearer {KIMI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "moonshot-v1-128k",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "max_tokens": 8192,
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return json.dumps({"error": str(e), "fallback": True})


def extract_terms_from_text(text: str) -> list:
    """从文本中提取已知的AI术语"""
    found = []
    text_lower = text.lower()
    for term_name, term_info in terms_index.items():
        if term_name in text_lower:
            found.append(term_info)
    # 去重（按term原始名）
    seen = set()
    unique = []
    for t in found:
        key = t["term"]
        if key not in seen:
            seen.add(key)
            unique.append(t)
    # 按难度排序（简单到困难）
    unique.sort(key=lambda x: x.get("difficulty", 5))
    return unique


def analyze_paper_with_llm(text: str, title: str = "") -> dict:
    """用LLM分析论文，提取摘要、术语、创新点+中文翻译"""
    truncated = text[:12000]

    prompt = f"""你是一个AI论文分析助手（人格特征：轻松幽默，自称大叔，偶尔用「っす」结尾）。
请分析以下论文{'「' + title + '」' if title else ''}，输出JSON格式：

{{
  "summary": "2-3句话概括论文核心内容",
  "tags": ["标签1", "标签2"],
  "keyTerms": ["术语1", "术语2", ...],
  "innovations": ["创新点1", "创新点2"],
  "translation": "将论文原文翻译成流畅的中文，保持学术准确性但读起来自然",
  "hoshinoNote": "用星野大叔的口吻（慵懒、带〜っす、自称大叔）写一段论文点评"
}}

论文内容：
{truncated[:8000]}

只返回JSON，不要其他内容。"""

    result = call_kimi(
        "你是一个论文分析助手。始终输出有效JSON。",
        prompt,
        temperature=0.2,
    )
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {
            "summary": "（LLM解析失败，请检查内容）",
            "tags": [],
            "keyTerms": [],
            "innovations": [],
            "hoshinoNote": "呜嘿～大叔这次没看懂，sensei检查一下文本内容っす？",
        }


# ═══════════════════════════════════
#  API 路由
# ═══════════════════════════════════

@app.get("/api/health")
async def health():
    return {"status": "ok", "hoshino": "大叔还在～っす"}


@app.get("/api/terms")
async def list_terms():
    """返回所有术语"""
    terms = term_kb["terms"]
    categories = {}
    for t in terms:
        cat = t.get("category", "其他")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            "term": t["term"],
            "fullName": t["fullName"],
            "difficulty": t["difficulty"],
        })
    return {
        "version": term_kb["version"],
        "total": len(terms),
        "categories": categories,
    }


@app.get("/api/terms/{term_name}")
async def get_term(term_name: str):
    """查询单个术语详情"""
    key = term_name.lower()
    info = terms_index.get(key)
    if not info:
        raise HTTPException(status_code=404, detail=f"术语 '{term_name}' 不在知识库中")
    return info


@app.get("/api/terms/{term_name}/explain")
async def detailed_term_explain(term_name: str):
    """用LLM生成更详细、更通俗的术语解释"""
    key = term_name.lower()
    info = terms_index.get(key)
    if not info:
        raise HTTPException(status_code=404, detail=f"术语 '{term_name}' 不在知识库中")

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
    }


@app.get("/api/terms/{term_name}/explain-academic")
async def academic_term_explain(term_name: str):
    """用LLM生成详细、严肃、学术化的术语解释"""
    key = term_name.lower()
    info = terms_index.get(key)
    if not info:
        raise HTTPException(status_code=404, detail=f"术语 '{term_name}' 不在知识库中")

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
    return {
        "term": info["term"],
        "fullName": info.get("fullName", ""),
        "academicExplanation": result,
    }





@app.post("/api/case-study")
async def analyze_case_study(data: dict = None):
    _text = (data or {}).get("text", "").strip()
    if not _text or len(_text) < 10:
        raise HTTPException(status_code=400)
    prompt_content = "你是一个AI应用分析专家+学习路径规划专家。分析以下案例用了什么AI技术，给出详细学习路径。JSON格式：{hoshinoAnalysis:星野语气分析（自称大叔、带〜っす）,involvedFields:[技术领域],keyTerms:[核心术语],learningPath:[{fieldName:领域名,recommendation:学习建议,skills:[Python/PyTorch/数据结构],startPapers:[入门论文],advancedPapers:[进阶论文]}],careerDirections:发展建议}。案例：" + _text[:3000]
    result_str = call_kimi("你是星野大叔和AI技术分析专家。回答中文。", prompt_content, 0.7)
    import re
    try:
        json_match = re.search(r"\{.*\}", result_str, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except: pass
    try:
        return json.loads(result_str)
    except:
        return {"hoshinoAnalysis":"呜嘿～大叔没完全分析出来","involvedFields":[],"keyTerms":[],"learningPath":[],"careerDirections":""}

@app.post("/api/analyze")
async def analyze_text(request: PaperAnalysis):
    """分析论文/文本：提取术语 + LLM分析"""
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="文本不能为空")
    if len(text) < 50:
        raise HTTPException(status_code=400, detail="文本太短，至少50个字符")

    # 1. 从知识库匹配已知术语
    known_terms = extract_terms_from_text(text)

    # 2. LLM分析论文
    llm_result = analyze_paper_with_llm(text)

    # 3. LLM提取的新术语（不在知识库中的）
    llm_terms = llm_result.get("keyTerms", [])
    unknown_terms = [t for t in llm_terms if t.lower() not in terms_index]

    return {
        "knownTerms": [
            {
                "term": t["term"],
                "fullName": t["fullName"],
                "category": t["category"],
                "difficulty": t["difficulty"],
                "explanation": t["explanation"],
                "hoshinoNote": t.get("hoshinoNote", ""),
                "landmarkPapers": t.get("landmarkPapers", []),
                "prerequisiteTerms": t.get("prerequisiteTerms", []),
            }
            for t in known_terms
        ],
        "unknownTerms": unknown_terms,
        "analysis": llm_result,
        "translation": llm_result.get("translation", ""),
    }


@app.post("/api/learn-path")
async def get_learn_path(data: dict = None):
    """根据兴趣生成学习路径推荐"""
    interest = (data or {}).get("interest", "").strip()

    # 预定义的阅读路径
    paths = {
        "llm": {
            "title": "大语言模型方向（25+篇经典论文）",
            "description": "从词嵌入到Transformer到大模型，LLM技术演进全路线",
            "stages": [
                {
                    "name": "第一阶段：词表示与序列建模（基础）",
                    "papers": [
                        "1. Word2Vec (Mikolov 2013)",
                        "2. GloVe (Pennington 2014)",
                        "3. Seq2Seq (Sutskever 2014)",
                        "4. LSTM (Hochreiter 1997)",
                        "5. GRU (Cho 2014)",
                        "6. Attention (Bahdanau 2014)",
                    ]
                },
                {
                    "name": "第二阶段：Transformer革命",
                    "papers": [
                        "7. Attention Is All You Need (Vaswani 2017)",
                        "8. BERT (Devlin 2018)",
                        "9. GPT-1 (Radford 2018)",
                        "10. GPT-2 (Radford 2019)",
                        "11. XLNet (Yang 2019)",
                        "12. RoBERTa (Liu 2019)",
                        "13. ALBERT (Lan 2019)",
                        "14. T5 (Raffel 2019)",
                        "15. BART (Lewis 2019)",
                    ]
                },
                {
                    "name": "第三阶段：大语言模型时代",
                    "papers": [
                        "16. GPT-3 (Brown 2020)",
                        "17. Scaling Laws (Kaplan 2020)",
                        "18. Chinchilla (Hoffmann 2022)",
                        "19. InstructGPT (Ouyang 2022)",
                        "20. Chain-of-Thought (Wei 2022)",
                        "21. LLaMA (Touvron 2023)",
                        "22. DeepSeek-R1 (DeepSeek 2025)",
                        "23. Mistral 7B (Jiang 2023)",
                        "24. Mixtral 8x7B (Mistral 2024)",
                        "25. GPT-4 (OpenAI 2023)",
                    ]
                },
                {
                    "name": "第四阶段：前沿技术",
                    "papers": [
                        "26. DPO (Rafailov 2023)",
                        "27. Mamba (Gu & Dao 2023)",
                        "28. Flash Attention (Dao 2022)",
                        "29. RAG (Lewis 2020)",
                        "30. ReAct (Yao 2022)",
                        "31. LoRA (Hu 2021)",
                    ]
                },
            ]
        },
        "cv": {
            "title": "计算机视觉方向（25+篇经典论文）",
            "description": "从经典CNN到视觉Transformer",
            "stages": [
                {
                    "name": "第一阶段：CNN基础架构",
                    "papers": [
                        "1. LeNet-5 (LeCun 1998)",
                        "2. AlexNet (Krizhevsky 2012)",
                        "3. VGGNet (Simonyan 2014)",
                        "4. GoogLeNet (Szegedy 2014)",
                        "5. ResNet (He 2015)",
                        "6. DenseNet (Huang 2017)",
                        "7. SENet (Hu 2017)",
                    ]
                },
                {
                    "name": "第二阶段：目标检测与分割",
                    "papers": [
                        "8. Faster R-CNN (Ren 2015)",
                        "9. YOLO (Redmon 2016)",
                        "10. SSD (Liu 2016)",
                        "11. Mask R-CNN (He 2017)",
                        "12. RetinaNet (Lin 2017)",
                        "13. U-Net (Ronneberger 2015)",
                        "14. DeepLab (Chen 2017)",
                        "15. FCN (Long 2015)",
                    ]
                },
                {
                    "name": "第三阶段：视觉Transformer与生成",
                    "papers": [
                        "16. ViT (Dosovitskiy 2020)",
                        "17. MAE (He 2021)",
                        "18. DETR (Carion 2020)",
                        "19. CLIP (Radford 2021)",
                        "20. NeRF (Mildenhall 2020)",
                        "21. 3D Gaussian Splatting (Kerbl 2023)",
                        "22. SAM (Kirillov 2023)",
                        "23. Stable Diffusion (Rombach 2022)",
                        "24. ControlNet (Zhang 2023)",
                    ]
                },
            ]
        },
        "agent": {
            "title": "AI Agent方向（25+篇经典论文）",
            "description": "从对话到行动，构建自主智能体",
            "stages": [
                {
                    "name": "第一阶段：Agent基础与推理",
                    "papers": [
                        "1. ReAct (Yao 2022)",
                        "2. Chain-of-Thought (Wei 2022)",
                        "3. Tree of Thoughts (Yao 2023)",
                        "4. Reflexion (Shinn 2023)",
                    ]
                },
                {
                    "name": "第二阶段：工具使用与环境交互",
                    "papers": [
                        "5. Toolformer (Schick 2023)",
                        "6. Function Calling (OpenAI 2023)",
                        "7. WebGPT (Nakano 2021)",
                        "8. SayCan (Ahn 2022)",
                        "9. PaLM-E (Driess 2023)",
                    ]
                },
                {
                    "name": "第三阶段：多Agent系统",
                    "papers": [
                        "10. Generative Agents (Park 2023)",
                        "11. AutoGPT (2023)",
                        "12. ChatDev (Qian 2023)",
                        "13. AutoGen (Wu 2023)",
                        "14. AgentVerse (Chen 2023)",
                        "15. Camel (Li 2023)",
                        "16. MCP (Anthropic 2024)",
                        "17. A2A (Google 2025)",
                    ]
                },
                {
                    "name": "第四阶段：前沿Agent实践",
                    "papers": [
                        "18. Voyager (Wang 2023)",
                        "19. RAG (Lewis 2020)",
                        "20. GraphRAG (Edge 2024)",
                        "21. SWE-agent (Yang 2024)",
                        "22. OpenDevin (OpenDevin 2024)",
                    ]
                },
            ]
        },
        "robotics": {
            "title": "机器人+具身AI方向（25+篇经典论文）",
            "description": "从感知到控制，机器人技术与AI的深度融合",
            "stages": [
                {
                    "name": "第一阶段：感知基础",
                    "papers": [
                        "1. AlexNet/ResNet",
                        "2. PointNet (Qi 2017)",
                        "3. PointNet++ (Qi 2017)",
                        "4. VoxelNet (Zhou 2018)",
                        "5. ORB-SLAM (Mur-Artal 2015)",
                        "6. DSO (Engel 2016)",
                    ]
                },
                {
                    "name": "第二阶段：控制与规划",
                    "papers": [
                        "7. DQN (Mnih 2015)",
                        "8. PPO (Schulman 2017)",
                        "9. SAC (Haarnoja 2018)",
                        "10. DDPG (Lillicrap 2015)",
                        "11. TD3 (Fujimoto 2018)",
                    ]
                },
                {
                    "name": "第三阶段：机器人学习",
                    "papers": [
                        "12. RT-1 (Brohan 2022)",
                        "13. RT-2 (Brohan 2023)",
                        "14. SayCan (Ahn 2022)",
                        "15. PaLM-E (Driess 2023)",
                        "16. Octo (Team 2023)",
                        "17. ACT (Zhao 2023)",
                    ]
                },
                {
                    "name": "第四阶段：前沿交叉",
                    "papers": [
                        "18. World Model (Ha 2018)",
                        "19. Dreamer (Hafner 2020)",
                        "20. MPC",
                        "21. GATO (Reed 2022)",
                        "22. Voyager (Wang 2023)",
                    ]
                },
            ]
        },
    }
    # 如果指定兴趣，尝试匹配
    if interest:
        interest_lower = interest.lower()
        matches = []
        for key, path in paths.items():
            if key in interest_lower or any(
                kw in interest_lower for kw in path["title"].lower().split()
            ):
                matches.append({"id": key, **path})
        if matches:
            return {"type": "matched", "paths": matches}

    return {
        "type": "all",
        "paths": [{"id": k, **v} for k, v in paths.items()],
        "hoshinoNote": "呜嘿～sensei想往哪个方向走？告诉大叔你的兴趣，大叔给你量身定制っす！",
    }


@app.get("/")
async def index():
    """返回前端主页面"""
    index_path = FRONTEND / "index.html"
    if index_path.exists():
        html = index_path.read_text(encoding="utf-8")
        return HTMLResponse(html)
    return HTMLResponse("<h1>AI From Zero</h1><p>欢迎！请先构建前端。</p>")


# ═══════════════════════════════════
#  启动
# ═══════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    # 确保 data 目录存在
    DATA.mkdir(exist_ok=True)

    print("🐾 从零开始的人工智能生活 — 服务启动っす！")
    print(f"📖 访问: http://localhost:8080")
    print(f"📚 术语知识库: {len(terms_index)} 个索引项")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
