# AI-From-Zero - OpenClaw Skill

AI-From-Zero 可以作为 OpenClaw/Claw 的本地论文学习 Skill 使用。它适合完成论文文本分析、PDF 读取、术语解释、下一篇论文推荐、学习路径和上下文伴学问答。

GitHub: https://github.com/Peixuan-Li0402/AI-From-Zero

## 准备项目

推荐让 OpenClaw 按下面顺序准备：

```bash
git clone https://github.com/Peixuan-Li0402/AI-From-Zero.git
cd AI-From-Zero
python -m pip install -r requirements.txt
python tools/bootstrap_openclaw_env.py
./start.sh
```

Windows PowerShell：

```powershell
git clone https://github.com/Peixuan-Li0402/AI-From-Zero.git
cd AI-From-Zero
python -m pip install -r requirements.txt
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

`llmConfigured=true` 表示模型已配置。`llmConfigured=false` 时，项目仍可用本地术语库降级运行。

## 模型配置

OpenClaw 自动配置只读取显式环境变量，不读取或复制私有配置文件中的密钥。

支持的环境变量：

```text
OPENAI_API_KEY
OPENROUTER_API_KEY
DEEPSEEK_API_KEY
KIMI_API_KEY
LLM_API_KEY
```

生成本地 `.env`：

```bash
python tools/bootstrap_openclaw_env.py
```

也可以手动写 `.env`：

```env
LLM_PROVIDER=kimi
LLM_API_KEY=your_key_here
LLM_API_URL=https://api.moonshot.cn/v1/chat/completions
LLM_MODEL=moonshot-v1-128k
LLM_TIMEOUT=60
APP_HOST=127.0.0.1
APP_PORT=8080
```

如果 OpenClaw 和服务不在同一台机器上，把 `APP_HOST` 改成 `0.0.0.0`，并把工具 URL 改成服务机器的局域网地址。只在可信网络里这样做。

## 命令行工具

服务启动后，OpenClaw 可以直接调用：

```bash
python tools/openclaw_ai_from_zero.py health
python tools/openclaw_ai_from_zero.py integrations
python tools/openclaw_ai_from_zero.py demo-cases
python tools/openclaw_ai_from_zero.py load-demo transformer
python tools/openclaw_ai_from_zero.py search-papers "Transformer attention" --limit 5
python tools/openclaw_ai_from_zero.py load-paper "Attention Is All You Need"
python tools/openclaw_ai_from_zero.py analyze-text --file paper.txt --title "My Paper"
python tools/openclaw_ai_from_zero.py chat "解释这篇论文的方法" --paper-file paper.txt --local-only
python tools/openclaw_ai_from_zero.py message "解释 Transformer" --channel local
```

推荐工作流：

1. 用 `search-papers` 或 `/api/learn-path` 找到推荐论文。
2. 用 `load-paper` 或 `/api/papers/load` 载入 PDF 原文；失败时使用摘要导读和来源链接。
3. 把返回的 `text` 交给 `/api/analyze`，得到术语、高亮数据、摘要、翻译和学习建议。
4. 用 `/api/chat` 带着论文文本、当前术语和用户问题继续伴学。
5. 用 `/api/integrations/messages/inbound` 或 CLI `message` 模拟 QQ/微信消息；配置 Webhook 后用 `send-message` 推送结果。

## HTTP 工具注册示例

不同 OpenClaw 版本的注册格式可能不同，核心是把本地服务暴露为 Web 工具：

```yaml
tools:
  - name: ai-from-zero
    description: "AI paper learning, terminology tracing, and guided reading"
    url: "http://127.0.0.1:8080"
    endpoints:
      - path: "/api/health"
        method: "GET"
      - path: "/api/analyze"
        method: "POST"
      - path: "/api/analyze-pdf"
        method: "POST"
      - path: "/api/chat"
        method: "POST"
      - path: "/api/demo-cases"
        method: "GET"
      - path: "/api/demo-cases/{case_id}/load"
        method: "POST"
      - path: "/api/integrations/status"
        method: "GET"
      - path: "/api/integrations/messages/inbound"
        method: "POST"
      - path: "/api/integrations/messages/send"
        method: "POST"
      - path: "/api/learning/session"
        method: "POST"
      - path: "/api/papers/search"
        method: "GET"
      - path: "/api/papers/load"
        method: "POST"
      - path: "/api/papers/evidence"
        method: "POST"
      - path: "/api/terms"
        method: "GET"
      - path: "/api/terms/{name}"
        method: "GET"
      - path: "/api/terms/{name}/papers"
        method: "POST"
      - path: "/api/learn-path"
        method: "POST"
```

## 核心接口

- `GET /api/health`：检查服务、术语库和模型配置。
- `POST /api/analyze`：分析论文文本，返回术语、结构、摘要和翻译状态。
- `POST /api/analyze-pdf`：读取可复制文字 PDF，返回全文、页数、术语和分析结果。
- `POST /api/chat`：带论文上下文的 AI 伴学；无 Key 时本地降级。
- `GET /api/terms`、`GET /api/terms/{name}`：双语术语库。
- `POST /api/terms/{name}/papers`：术语相关论文。
- `POST /api/learning/session`：学习会话和下一篇论文推荐。
- `POST /api/learn-path`：学习路径。
- `GET /api/papers/search`、`POST /api/papers/load`、`POST /api/papers/evidence`：论文检索、载入和证据片段。
- `GET /api/config`、`POST /api/config/save`：本地模型配置。
- `GET /api/demo-cases`、`POST /api/demo-cases/{case_id}/load`：竞赛演示案例。
- `GET /api/integrations/status`、`POST /api/integrations/messages/inbound`、`POST /api/integrations/messages/send`：QQ/微信桥接与本地消息模拟。

分析类接口中的 `llmStatus`：

- `ok`：模型调用成功。
- `missing_key`：没有 Key，使用本地降级。
- `error`：模型或解析失败，尽量返回本地结果。

## 自检命令

启动前：

```bash
python tools/check_release_readiness.py
python tools/check_term_kb.py
```

启动后：

```bash
python tools/check_api_smoke.py --base-url http://127.0.0.1:8080
python tools/check_release_readiness.py --base-url http://127.0.0.1:8080
```

## 常见处理

- 没有 API Key：仍可运行，术语高亮、基础分析和本地伴学可用。
- 页面显示本地模式：检查 `.env` 或 `/api/config`。
- 端口冲突：修改 `.env` 的 `APP_PORT`。
- 扫描版 PDF：当前不支持 OCR，需要先转换成可复制文本。
- 外部论文服务不可用：项目会降级到本地论文资源、摘要和来源链接。
- 局域网访问：只在可信网络中把 `APP_HOST` 改为 `0.0.0.0`。
