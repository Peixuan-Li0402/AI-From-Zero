# Project Structure

```text
AI-From-Zero/
├── backend/
│   ├── app/
│   │   ├── agent_attachments.py # 清小搭附件下载、SSRF 防护和解析缓存
│   │   ├── agent_core.py     # 论文学习智能体编排
│   │   ├── analysis.py      # 文本/PDF 分析、长文分块
│   │   ├── artifacts.py     # 临时学习笔记附件
│   │   ├── chat.py          # 右侧 AI 伴学
│   │   ├── config.py        # LLM_* / KIMI_* / .env 配置
│   │   ├── learning.py
│   │   ├── llm.py           # OpenAI-compatible 调用
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── papers.py        # 论文搜索、资源载入、元数据适配、证据片段抽取
│   │   ├── pdf.py           # page-aware PDF 提取
│   │   ├── progress.py      # 本地学习画像、阅读会话、下一篇论文推荐
│   │   ├── qingxiaoda.py    # /v1 OpenAI-compatible 协议与 SSE
│   │   ├── routes.py
│   │   └── terms.py
│   ├── requirements.txt
│   └── server.py
├── frontend/
│   ├── index.html           # 静态前端、配置弹窗、阅读器、伴学
│   └── style.css
├── knowledge/
│   ├── learning_paths.json
│   ├── term_kb.json         # 820 条双语术语
│   └── term_kb.json.bak
├── tests/
│   ├── test_api.py
│   ├── test_qingxiaoda.py
│   └── test_release_readiness.py
├── tools/
│   ├── bootstrap_openclaw_env.py
│   ├── check_api_smoke.py
│   ├── check_qingxiaoda_compat.py
│   ├── check_term_kb.py
│   ├── expand_term_kb_bilingual.py
│   ├── fill_term_placeholders.py
│   ├── openclaw_ai_from_zero.py
│   ├── pdf2text.py
│   └── repair_term_kb.py
├── .env.example
├── Dockerfile
├── railway.toml
├── requirements-dev.txt
├── start.sh
└── start_windows.ps1
```
