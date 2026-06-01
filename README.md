# AI-From-Zero

AI 论文溯源阅读助手：面向刚入门 AI 的高中生/大一新生，帮助你把论文里的专业术语、经典论文来源、学习路径和伴学问答串起来。

## 当前能力

- 文本/PDF 分析：粘贴论文或上传可复制文字的 PDF，自动匹配本地术语库并高亮显示。
- PDF 全文阅读：按页提取文本，不再固定截断 8000/10000 字；超长 PDF 会提示 LLM 分析上限。
- 通用模型配置：网页内可配置 OpenAI-compatible API，支持 Kimi、OpenAI、OpenRouter、DeepSeek、Ollama 和自定义 endpoint。
- 双语术语库：820 条计算机、软件工程和 AI 术语，保留中英文名称、别名、解释和论文元数据。
- AI 伴学：右侧聊天框接入 `/api/chat`，能结合当前论文、已识别术语、当前打开术语和学习状态回答。
- 本地降级：未配置 API Key 时，文本分析、PDF 分析和伴学都会回退到本地术语库。

## 快速开始（Windows）

```powershell
cd C:\Users\lenovo\Documents\AI-FROM-ZERO
python -m pip install -r backend/requirements.txt
.\start_windows.ps1
```

打开浏览器访问：

```text
http://localhost:8080
```

首次启动如果没有配置模型，点击页面顶部“配置模型”即可填写供应商、API 地址、模型和 Key。Key 只会保存到本地 `.env`，不会提交到仓库。

## 快速开始（通用 / OpenClaw）

```bash
git clone https://github.com/Peixuan-Li0402/AI-From-Zero.git
cd AI-From-Zero
python -m pip install -r backend/requirements.txt
./start.sh
```

如果 OpenClaw 或你的 shell 已经暴露了 API Key，可以自动生成本地 `.env`：

```bash
python tools/bootstrap_openclaw_env.py
```

脚本只读取显式环境变量：`OPENAI_API_KEY`、`OPENROUTER_API_KEY`、`DEEPSEEK_API_KEY`、`KIMI_API_KEY`、`LLM_API_KEY`。它不会读取 OpenClaw 私有配置文件。

## 配置

配置优先读取环境变量，其次读取项目根目录 `.env`。旧的 `KIMI_*` 变量仍然兼容。

| 变量 | 默认值 | 说明 |
|---|---|---|
| `LLM_PROVIDER` | `kimi` | `kimi`、`openai`、`openrouter`、`deepseek`、`ollama`、`custom` |
| `LLM_API_KEY` | 空 | OpenAI-compatible API Key；Ollama 可为空 |
| `LLM_API_URL` | Kimi chat/completions | OpenAI-compatible chat completions 地址 |
| `LLM_MODEL` | `moonshot-v1-128k` | 模型名 |
| `LLM_TIMEOUT` | `60` | 请求超时时间，单位秒 |
| `APP_HOST` | `127.0.0.1` | 默认只监听本机 |
| `APP_PORT` | `8080` | 服务端口 |

## API

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | 前端页面 |
| `/api/health` | GET | 服务状态、术语库数量、LLM provider/model、配置写入状态 |
| `/api/config` | GET | 当前模型配置状态，Key 只脱敏显示 |
| `/api/config/providers` | GET | 供应商预设 |
| `/api/config/test` | POST | 测试临时模型配置 |
| `/api/config/save` | POST | 保存本地 `.env`，仅允许本机调用 |
| `/api/analyze` | POST | 分析论文文本 |
| `/api/analyze-pdf` | POST | 上传并分析 PDF，返回 `pages/pageCount/textLength/truncated/extractionWarnings` |
| `/api/chat` | POST | 右侧 AI 伴学 |
| `/api/terms` | GET | 获取术语分类列表和双语字段 |
| `/api/terms/{name}` | GET | 获取单个术语详情 |
| `/api/terms/{name}/papers` | POST | 展开相关论文 |
| `/api/terms/{name}/explain` | GET | 通俗解释 |
| `/api/terms/{name}/explain-academic` | GET | 学术解释 |
| `/api/learn-path` | POST | 获取学习路径 |
| `/api/case-study` | POST | 分析 AI 应用案例 |

分析类接口会返回 `llmStatus`：

- `ok`：LLM 调用成功。
- `missing_key`：未配置模型 Key，已使用本地术语库降级。
- `error`：LLM 或文件解析失败，接口会尽量返回可用的本地结果。

## 开发检查

```powershell
python -m pip install -r requirements-dev.txt
python tools/check_term_kb.py
python -m pytest
```

服务启动后可以跑 API 冒烟检查：

```powershell
python tools/check_api_smoke.py --base-url http://127.0.0.1:8080
```

## 项目结构

```text
backend/app/          # 配置、路由、LLM、PDF、术语、伴学、学习路径
frontend/             # 静态前端
knowledge/            # 双语术语库与学习路径
tests/                # FastAPI 接口测试
tools/                # 术语检查、扩充、OpenClaw bootstrap、API 冒烟
```

## 已知边界

- 扫描版 PDF 暂不支持 OCR，会返回明确错误。
- 伴学第一版不做账号、长期记忆、复杂 RAG 或流式输出。
- `.env` 是本地开发文件，真实 Key 不进入版本控制。

## License

MIT
