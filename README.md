# AI-From-Zero

AI-From-Zero 是一个面向 AI 初学者的本地论文学习助手。它把论文原文、术语高亮、双语术语库、下一篇论文推荐、学习路径和 AI 伴学连成一个学习闭环，帮助同学从“读不懂一篇论文”逐步走到“知道概念来源、知道下一步读什么、能用自己的话解释出来”。

项目默认在本机运行，不需要账号系统，也不会把你的 API Key 提交到 GitHub。

GitHub: https://github.com/Peixuan-Li0402/AI-From-Zero

## 能力概览

无 API Key 也能使用：

- 粘贴论文文本或上传可复制文字的 PDF。
- 自动识别并高亮 AI、计算机系统、软件工程等领域术语。
- 点击高亮术语查看双语解释、前置概念、概念链条和经典论文。
- 生成基础论文分析、学习路径和下一篇推荐论文。
- 使用本地术语库进行 AI 伴学降级回答。
- 通过本地消息桥接模拟 QQ/微信提问，验证机器人连接流程。

配置 API Key 后会增强：

- 更完整的论文摘要、创新点、局限和阅读建议。
- 分块中文翻译，尽量覆盖全文，并显示翻译覆盖状态。
- 更自然的右侧 AI 伴学问答。
- 术语通俗解释和学术解释按需生成。
- 配置微信或 QQ Webhook 后，把导读结果推送到群聊或机器人桥。

## 清小搭智能体

项目现在可以作为 OpenAI-compatible 论文学习智能体接入清小搭：

- 在对话中直接解释术语、生成概念链和论文学习路径。
- 接收 PDF、TXT、Markdown 和论文链接，返回结构化导读与原文证据。
- 每轮回答都返回同一个会话学习工作台链接；网页恢复清小搭问答、论文全文、术语高亮和学习路径。
- 用户可在工作台继续使用原版阅读器、术语库、学习路径和网页伴学，新增问答会写回会话记录。
- 支持标准 JSON 和 SSE 流式回答。
- 可生成清小搭能够下载的 Markdown 学习笔记附件。
- 无模型 Key、附件解析失败或外部服务中断时自动降级，不中断整次会话。
- Agent v2 会先用确定性路由判断任务：术语和概念桥直接走本地知识库，复杂论文问题才调用模型。
- arXiv、OpenAlex、Semantic Scholar 实时并发检索，带短期缓存、来源级超时和熔断。
- 回答区分论文原文、自建知识库和实时论文来源；阅读器同步显示学习阶段、本轮目标和依据。

完整的官方协议映射、腾讯云部署参数和上线闸门见 [清小搭智能体部署与验收](docs/qingxiaoda-agent.md)。本地验证：

```bash
python tools/check_qingxiaoda_compat.py --base-url http://127.0.0.1:8080/v1 --key your_qxd_key
```

公网验收脚本默认绕过环境代理，并拒绝把代理 fake-IP 当作清小搭可直连的证据。

## 快速开始

### Windows

```powershell
git clone https://github.com/Peixuan-Li0402/AI-From-Zero.git
cd AI-From-Zero
.\start_windows.ps1
```

如果 PowerShell 拦截脚本，使用一次性绕过命令：

```powershell
powershell -ExecutionPolicy Bypass -File .\start_windows.ps1
```

启动后打开：

```text
http://127.0.0.1:8080
```

验证服务：

```powershell
Invoke-RestMethod http://127.0.0.1:8080/api/health
```

### macOS / Linux / WSL

```bash
git clone https://github.com/Peixuan-Li0402/AI-From-Zero.git
cd AI-From-Zero
./start.sh
```

启动后打开：

```text
http://127.0.0.1:8080
```

验证服务：

```bash
curl http://127.0.0.1:8080/api/health
```

### 通用手动启动

如果你不想使用启动脚本，也可以手动安装依赖并启动：

```bash
python -m pip install -r requirements.txt
python backend/server.py
```

默认端口是 `8080`。如果端口被占用，可以在 `.env` 中设置：

```env
APP_PORT=8081
```

## 模型配置

推荐三种方式，任选一种即可。

### 方式一：网页配置

启动项目后打开首页，点击页面顶部的“配置模型”，选择供应商、填写 API Key，测试连接后保存。Key 会写入本地 `.env`，不会通过接口明文回传。

### 方式二：手动创建 `.env`

可以复制 `.env.example` 为 `.env`，然后填写自己的配置：

```env
LLM_PROVIDER=kimi
LLM_API_KEY=your_key_here
LLM_API_URL=https://api.moonshot.cn/v1/chat/completions
LLM_MODEL=moonshot-v1-128k
LLM_TIMEOUT=60
APP_HOST=127.0.0.1
APP_PORT=8080
```

常见供应商示例：

```env
# OpenAI
LLM_PROVIDER=openai
LLM_API_KEY=your_key_here
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_MODEL=gpt-4o-mini
```

```env
# OpenRouter
LLM_PROVIDER=openrouter
LLM_API_KEY=your_key_here
LLM_API_URL=https://openrouter.ai/api/v1/chat/completions
LLM_MODEL=openai/gpt-4o-mini
```

```env
# DeepSeek
LLM_PROVIDER=deepseek
LLM_API_KEY=your_key_here
LLM_API_URL=https://api.deepseek.com/chat/completions
LLM_MODEL=deepseek-chat
```

```env
# Ollama local model
LLM_PROVIDER=ollama
LLM_API_KEY=
LLM_API_URL=http://localhost:11434/v1/chat/completions
LLM_MODEL=llama3.1
```

`APP_HOST=127.0.0.1` 更安全，只允许本机访问。只有需要局域网其他设备访问时，才改成：

```env
APP_HOST=0.0.0.0
```

### 方式三：OpenClaw 自动配置

OpenClaw 或当前 shell 先暴露任意一个环境变量：

```text
OPENAI_API_KEY
OPENROUTER_API_KEY
DEEPSEEK_API_KEY
KIMI_API_KEY
LLM_API_KEY
```

然后运行：

```bash
python tools/bootstrap_openclaw_env.py
```

这个脚本只读取显式环境变量，不读取或复制 OpenClaw 私有配置文件里的密钥。

## QQ / 微信桥接

项目支持轻量消息桥接，适合比赛现场验证“本地部署 + QQ/微信连接”。真实 Webhook 只放在本地 `.env`：

```env
WECHAT_WEBHOOK_URL=
QQ_BOT_WEBHOOK_URL=
MESSAGE_BRIDGE_TOKEN=
```

没有真实平台凭证时，可以用本地模拟：

```bash
python tools/openclaw_ai_from_zero.py integrations
python tools/openclaw_ai_from_zero.py message "解释 Transformer" --channel local
python tools/openclaw_ai_from_zero.py message "下一篇 llm" --channel qq
```

配好 Webhook 后，可以发送测试消息：

```bash
python tools/openclaw_ai_from_zero.py send-message "AI-From-Zero 已连接" --channel wechat
python tools/openclaw_ai_from_zero.py send-message "AI-From-Zero 已连接" --channel qq
```

## OpenClaw 使用方式

启动服务后，OpenClaw 可以把它当成本地 Web 工具调用，也可以直接使用命令行辅助工具：

```bash
python tools/openclaw_ai_from_zero.py health
python tools/openclaw_ai_from_zero.py search-papers "Transformer attention" --limit 5
python tools/openclaw_ai_from_zero.py load-paper "Attention Is All You Need"
python tools/openclaw_ai_from_zero.py demo-cases
python tools/openclaw_ai_from_zero.py load-demo transformer
python tools/openclaw_ai_from_zero.py analyze-text --file paper.txt --title "My Paper"
python tools/openclaw_ai_from_zero.py chat "解释这篇论文的方法" --paper-file paper.txt --local-only
```

推荐流程：

1. 用 `/api/learn-path` 或 `search-papers` 找到推荐论文。
2. 用 `/api/papers/load` 或 `load-paper` 载入论文资源。
3. 把返回的 `text` 交给 `/api/analyze` 做术语高亮和基础分析。
4. 用 `/api/chat` 带着论文上下文继续追问。

## 发布自检

项目提供一键自检，适合 clone 后或提交前运行：

```bash
python tools/check_release_readiness.py
```

服务启动后可以连同 API 一起检查：

```bash
python tools/check_release_readiness.py --base-url http://127.0.0.1:8080
python tools/check_api_smoke.py --base-url http://127.0.0.1:8080
```

开发测试：

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
python tools/check_term_kb.py
python tools/check_agent_eval_split.py
python tools/eval_agent_v2.py --split dev
```

GitHub Actions 会自动运行这些核心检查，确保公开版本不会轻易退化。

最终盲测使用 `python tools/eval_agent_v2.py --split test`。第一轮盲测曾暴露术语别名显示问题，修复后另建不重叠的 `test_round2` 做最终验收；失败记录没有被删除或伪装成首次通过。所有评测文件都不会被运行时代码或提示词读取，主题、问题和 ID 由脚本检查为互不重叠。Agent v2 的研究样本与架构取舍见 [研究与决策记录](docs/agent-v2-research.md)。

## 主要接口

- `GET /api/health`：服务健康状态、术语数量、模型配置状态。
- `GET /v1/models`、`POST /v1/chat/completions`：清小搭 OpenAI-compatible Agent，使用独立 Bearer 凭证。
- `GET /api/reader-sessions/{token}`：通过不可猜测令牌恢复清小搭会话学习工作台。
- `POST /api/reader-sessions/{token}/conversation`：从网页端保存该工作台的伴学对话。
- `GET /api/config`、`POST /api/config/test`、`POST /api/config/save`：本地模型配置；测试和保存只允许本机调用。
- `POST /api/analyze`：分析论文文本。
- `POST /api/analyze-pdf`：读取并分析 PDF。
- `POST /api/chat`：AI 伴学问答。
- `GET /api/demo-cases`、`POST /api/demo-cases/{case_id}/load`：固定演示案例。
- `GET /api/integrations/status`、`POST /api/integrations/messages/inbound`、`POST /api/integrations/messages/send`：QQ/微信消息桥接。
- `GET /api/terms`、`GET /api/terms/{name}`：术语库。
- `POST /api/terms/{name}/papers`：展开术语相关论文。
- `POST /api/learning/session`：创建学习会话和下一篇推荐。
- `POST /api/learn-path`：生成学习路径。
- `GET /api/papers/search`、`POST /api/papers/load`、`POST /api/papers/evidence`：论文搜索、载入和证据片段。

分析类接口会返回 `llmStatus`：

- `ok`：模型调用成功。
- `missing_key`：没有配置 Key，已使用本地模式。
- `error`：模型或解析失败，接口会尽量返回本地可用结果。

## 常见问题

### 页面能打开，但显示本地模式

说明没有配置 API Key，或模型连接测试失败。可以使用网页“配置模型”，也可以检查 `.env` 中的 `LLM_API_KEY`、`LLM_API_URL` 和 `LLM_MODEL`。

### 端口 8080 被占用

修改 `.env`：

```env
APP_PORT=8081
```

然后重新启动，访问 `http://127.0.0.1:8081`。

### Python 或依赖安装失败

先确认 Python 版本：

```bash
python --version
```

需要 Python 3.10 或更高版本。然后重新安装：

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### PowerShell 不允许运行脚本

使用：

```powershell
powershell -ExecutionPolicy Bypass -File .\start_windows.ps1
```

### PDF 无法读取

当前支持可复制文字的 PDF。扫描版 PDF 暂不支持 OCR，会返回明确错误。可以先把扫描版转换成可复制文本，再粘贴到文本分析框。

### 下一篇论文无法下载全文

项目会优先加载 PDF 原文；如果 PDF 不可访问或无法提取文本，会自动降级为摘要导读，并保留来源链接。

### OpenClaw bootstrap 找不到 Key

确认当前运行环境真的有这些变量之一：

```bash
echo $OPENAI_API_KEY
echo $OPENROUTER_API_KEY
echo $DEEPSEEK_API_KEY
echo $KIMI_API_KEY
echo $LLM_API_KEY
```

Windows PowerShell：

```powershell
$env:OPENAI_API_KEY
$env:OPENROUTER_API_KEY
$env:DEEPSEEK_API_KEY
$env:KIMI_API_KEY
$env:LLM_API_KEY
```

## 项目结构

```text
backend/app/          后端配置、路由、LLM、PDF、论文、术语和学习路径
frontend/             静态前端页面
knowledge/            双语术语库
tests/                后端接口测试和发布稳定性测试
tools/                OpenClaw、术语检查、API 冒烟和发布自检工具
```

## 当前边界

- 不支持扫描版 PDF OCR。
- 不做账号系统和云端同步。
- `data/` 中的学习记录只保存在本地，不进入 Git。
- 外部论文 API 不可用时会自动降级到本地术语库和内置论文资源。
- GROBID、Marker、PaperQA 等结构化论文增强仍是后续方向。

## License

MIT
