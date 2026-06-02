# AI-From-Zero - OpenClaw Skill

AI-From-Zero 是一个本地 AI 论文溯源阅读助手，可以作为 OpenClaw/Claw 的本地 Web 工具使用。它适合帮助用户分析论文文本、读取 PDF、解释术语、推荐学习路径，并通过右侧 AI 伴学回答上下文问题。

## 快速接入

OpenClaw 推荐按这个顺序准备项目：

```bash
git clone https://github.com/Peixuan-Li0402/AI-From-Zero.git
cd AI-From-Zero
python -m pip install -r backend/requirements.txt
python tools/bootstrap_openclaw_env.py
./start.sh
```

Windows PowerShell：

```powershell
cd C:\Users\lenovo\Documents\AI-FROM-ZERO
python -m pip install -r backend/requirements.txt
python tools/bootstrap_openclaw_env.py
.\start_windows.ps1
```

如果 PowerShell 拦截脚本：

```powershell
powershell -ExecutionPolicy Bypass -File .\start_windows.ps1
```

默认服务地址：

```text
http://127.0.0.1:8080
```

启动后先检查：

```bash
curl http://127.0.0.1:8080/api/health
```

Windows PowerShell：

```powershell
Invoke-RestMethod http://127.0.0.1:8080/api/health
```

`llmConfigured=true` 表示模型已经配置好。`llmConfigured=false` 时，项目仍可用本地术语库降级运行。

## 模型配置

优先让 OpenClaw 或当前 shell 暴露以下任一环境变量，然后运行 bootstrap：

```text
OPENAI_API_KEY
OPENROUTER_API_KEY
DEEPSEEK_API_KEY
KIMI_API_KEY
LLM_API_KEY
```

```bash
python tools/bootstrap_openclaw_env.py
```

bootstrap 只读取显式环境变量，不读取或复制 OpenClaw 私有配置文件里的密钥。如果 `.env` 已经有 `LLM_API_KEY`，它不会覆盖。

也可以手动创建 `.env`：

```env
LLM_PROVIDER=kimi
LLM_API_KEY=sk-your-key
LLM_API_URL=https://api.moonshot.cn/v1/chat/completions
LLM_MODEL=moonshot-v1-128k
LLM_TIMEOUT=60
APP_HOST=127.0.0.1
APP_PORT=8080
```

支持的供应商包括 Kimi、OpenAI、OpenRouter、DeepSeek、Ollama 和自定义 OpenAI-compatible endpoint。真实 Key 只保存在本地 `.env`，不要放进提示词、日志或 GitHub。

## 能力入口

- 文本分析：`POST /api/analyze`，输入论文正文，返回术语、高亮数据、摘要、翻译和 `llmStatus`。
- PDF 分析：`POST /api/analyze-pdf`，按页提取可复制文字 PDF，返回全文、页数、字符数、分块分析状态和术语结果。
- AI 伴学：`POST /api/chat`，结合当前论文、当前术语、已掌握术语和最近对话回答问题；无 Key 时走本地降级回答，也可传 `localOnly: true` 强制本地回答。
- 学习舱：`GET /api/learning/profile`、`POST /api/learning/session`、`POST /api/learning/mastery`，用于生成学习画像、阅读路线、概念笔记、概念链条和掌握状态。
- 论文增强：`GET /api/papers/search`、`POST /api/papers/evidence`，用于检索相关论文和抽取基于原文的证据片段；PDF 分析会返回本地结构化章节、引用和参考文献信息。
- 模型配置：`GET /api/config`、`GET /api/config/providers`、`POST /api/config/test`、`POST /api/config/save`。
- 术语库：`GET /api/terms`、`GET /api/terms/{name}`，返回双语术语字段和解释。
- 相关论文：`POST /api/terms/{name}/papers`。
- 术语解释：`GET /api/terms/{name}/explain`、`GET /api/terms/{name}/explain-academic`。
- 学习路径：`POST /api/learn-path`。
- 案例分析：`POST /api/case-study`。

分析类接口的 `llmStatus` 含义：

- `ok`：LLM 调用成功。
- `missing_key`：未配置模型 Key，已使用本地术语库降级。
- `error`：LLM 或解析失败，接口会尽量返回本地结果。

## Tool 配置示例

不同 OpenClaw 版本的注册格式可能不同。核心是把服务注册为本地 Web 工具：

```yaml
tools:
  - name: ai-from-zero
    description: "AI 论文阅读、术语溯源与伴学工具"
    url: "http://127.0.0.1:8080"
    endpoints:
      - path: "/api/health"
        method: "GET"
      - path: "/api/config"
        method: "GET"
      - path: "/api/analyze"
        method: "POST"
      - path: "/api/analyze-pdf"
        method: "POST"
      - path: "/api/chat"
        method: "POST"
      - path: "/api/learning/profile"
        method: "GET"
      - path: "/api/learning/session"
        method: "POST"
      - path: "/api/learning/mastery"
        method: "POST"
      - path: "/api/papers/search"
        method: "GET"
      - path: "/api/papers/evidence"
        method: "POST"
      - path: "/api/terms"
        method: "GET"
      - path: "/api/terms/{name}"
        method: "GET"
      - path: "/api/terms/{name}/papers"
        method: "POST"
      - path: "/api/terms/{name}/explain"
        method: "GET"
      - path: "/api/terms/{name}/explain-academic"
        method: "GET"
      - path: "/api/learn-path"
        method: "POST"
      - path: "/api/case-study"
        method: "POST"
```

如果 OpenClaw 和 AI-From-Zero 不在同一台机器上，把 `.env` 中的 `APP_HOST` 改成 `0.0.0.0`，并把工具 URL 改成服务机器的局域网地址。

## 冒烟检查

服务启动前可以检查术语库：

```bash
python tools/check_term_kb.py
```

服务启动后检查 API：

```bash
python tools/check_api_smoke.py --base-url http://127.0.0.1:8080
```

## 常见处理

- 没有 API Key：文本分析、PDF 分析和 AI 伴学会使用本地术语库降级，`llmStatus` 通常为 `missing_key`。
- 学习画像：本地记录保存在 `data/learning_progress.json`，不会进入 GitHub。
- 论文增强：外部 OpenAlex/Semantic Scholar 不可用时会保留本地术语库结果。
- 页面显示本地模式：检查 `.env` 或 `/api/config`，确认 `LLM_API_KEY`、`LLM_API_URL` 和 `LLM_MODEL` 是否正确。
- bootstrap 找不到 Key：先让运行环境暴露 `OPENAI_API_KEY`、`OPENROUTER_API_KEY`、`DEEPSEEK_API_KEY`、`KIMI_API_KEY` 或 `LLM_API_KEY`。
- 扫描版 PDF：当前不支持 OCR，需要先转换成可复制文本。
- 端口冲突：修改 `.env` 的 `APP_PORT` 后重启。
- 局域网访问：只有在可信网络里才把 `APP_HOST` 改成 `0.0.0.0`。
