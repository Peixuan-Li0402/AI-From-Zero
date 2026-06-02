# AI-From-Zero

AI-From-Zero 是一个本地 AI 论文溯源阅读助手，面向刚入门 AI、计算机和软件工程论文阅读的学习者。它可以把论文里的专业术语、相关经典论文、学习路径和右侧 AI 伴学串起来，让用户从“看不懂一篇论文”逐步走到“知道术语从哪里来、下一步该学什么”。

## 现在可以做什么

- 文本和 PDF 分析：粘贴论文正文，或上传可复制文字的 PDF，自动匹配本地双语术语库并高亮显示。
- PDF 全文阅读：按页提取文本，并用多策略修复英文单词粘连；超长文档会明确提示 LLM 分析上限。
- 中文翻译：模型已配置时，翻译走全文分块流程并返回覆盖率，不再只翻前几千字。
- 双语术语库：内置约 820 条 AI、计算机系统、软件工程和工程实践术语，保留中英文名、别名、解释和论文元数据。
- 模型配置：支持 OpenAI-compatible API，包括 Kimi、OpenAI、OpenRouter、DeepSeek、Ollama 和自定义 endpoint。
- AI 伴学：右侧聊天框接入 `/api/chat`，可结合当前论文、已识别术语、当前打开术语和学习状态回答问题。
- AI 学习舱：每次分析后在论文原文下方只保留“下一篇推荐论文”，优先提供 PDF/摘要/来源链接，并可一键载入阅读器继续学习。
- 论文增强：提供章节/引用/参考文献结构化识别、本地经典论文映射、arXiv/OpenAlex/Semantic Scholar 轻量搜索、PDF 自动载入和基于原文的证据片段抽取。
- 学习路径联动阅读器：学习路径里的推荐论文带来源链接或 PDF 地址，点击“开始学习”会自动载入论文全文或摘要导读。
- 本地降级：不配置 API Key 也能启动，文本/PDF 分析和伴学会使用本地术语库给出基础结果。

## 先选一种启动方式

如果你只是想先看看项目，可以不配置 API Key，直接启动。页面会显示本地模式，术语高亮和基础解释仍然可用。

### Windows

```powershell
cd C:\Users\lenovo\Documents\AI-FROM-ZERO
python -m pip install -r backend/requirements.txt
.\start_windows.ps1
```

如果 PowerShell 提示脚本不能运行，使用这个备用命令：

```powershell
powershell -ExecutionPolicy Bypass -File .\start_windows.ps1
```

启动后打开：

```text
http://127.0.0.1:8080
```

验证服务状态：

```powershell
Invoke-RestMethod http://127.0.0.1:8080/api/health
```

### macOS / Linux / WSL

```bash
git clone https://github.com/Peixuan-Li0402/AI-From-Zero.git
cd AI-From-Zero
python -m pip install -r backend/requirements.txt
./start.sh
```

启动后打开：

```text
http://127.0.0.1:8080
```

验证服务状态：

```bash
curl http://127.0.0.1:8080/api/health
```

### OpenClaw / Claw

OpenClaw 可以把这个项目当作一个本地 Web 工具来使用。推荐流程是：克隆仓库，生成本地 `.env`，启动服务，再让 OpenClaw 调用本地接口。

```bash
git clone https://github.com/Peixuan-Li0402/AI-From-Zero.git
cd AI-From-Zero
python -m pip install -r backend/requirements.txt
python tools/bootstrap_openclaw_env.py
./start.sh
```

`tools/bootstrap_openclaw_env.py` 只读取显式环境变量，不会读取或复制 OpenClaw 私有配置文件里的密钥。它会按顺序寻找这些变量：

```text
OPENAI_API_KEY
OPENROUTER_API_KEY
DEEPSEEK_API_KEY
KIMI_API_KEY
LLM_API_KEY
```

如果脚本提示没有找到 Key，可以先在 OpenClaw 或当前 shell 里暴露其中一个变量，再重新运行 bootstrap。服务启动后访问：

```text
http://127.0.0.1:8080/api/health
```

如果返回里的 `llmConfigured` 是 `true`，说明模型配置已经生效；如果是 `false`，项目仍能以本地模式运行。

OpenClaw 也可以直接调用项目 Skill 工具，不必打开网页：

```bash
python tools/openclaw_ai_from_zero.py health
python tools/openclaw_ai_from_zero.py search-papers "Transformer attention" --limit 5
python tools/openclaw_ai_from_zero.py load-paper "Attention Is All You Need"
python tools/openclaw_ai_from_zero.py analyze-text --file paper.txt --title "My Paper"
python tools/openclaw_ai_from_zero.py chat "带我读这篇论文" --paper-file paper.txt --local-only
```

## 配置模型

模型配置有三种方式，选一种即可。

### 方式 1：网页配置

启动后打开首页，点击顶部“配置模型”。这里可以选择供应商，填写 API 地址、模型名和 Key。保存后会写入项目根目录的 `.env`。

### 方式 2：手动写 `.env`

复制 `.env.example` 为 `.env`，再按你的供应商修改。真实 Key 只放在本地 `.env`，不要提交到 GitHub。

```env
LLM_PROVIDER=kimi
LLM_API_KEY=你的_API_KEY
LLM_API_URL=https://api.moonshot.cn/v1/chat/completions
LLM_MODEL=moonshot-v1-128k
LLM_TIMEOUT=60
APP_HOST=127.0.0.1
APP_PORT=8080
```

### 方式 3：OpenClaw 自动生成

让 OpenClaw 或 shell 暴露 `OPENAI_API_KEY`、`OPENROUTER_API_KEY`、`DEEPSEEK_API_KEY`、`KIMI_API_KEY` 或 `LLM_API_KEY`，然后运行：

```bash
python tools/bootstrap_openclaw_env.py
```

如果当前 `.env` 已经有 `LLM_API_KEY`，脚本不会覆盖。

## 常用供应商示例

下面的 Key 都是占位符，请替换成你自己的真实 Key。

### Kimi / Moonshot

```env
LLM_PROVIDER=kimi
LLM_API_KEY=sk-your-key
LLM_API_URL=https://api.moonshot.cn/v1/chat/completions
LLM_MODEL=moonshot-v1-128k
```

### OpenAI

```env
LLM_PROVIDER=openai
LLM_API_KEY=sk-your-key
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_MODEL=gpt-4o-mini
```

### OpenRouter

```env
LLM_PROVIDER=openrouter
LLM_API_KEY=sk-or-your-key
LLM_API_URL=https://openrouter.ai/api/v1/chat/completions
LLM_MODEL=openai/gpt-4o-mini
```

### DeepSeek

```env
LLM_PROVIDER=deepseek
LLM_API_KEY=sk-your-key
LLM_API_URL=https://api.deepseek.com/chat/completions
LLM_MODEL=deepseek-chat
```

### Ollama 本地模型

Ollama 通常不需要真实 API Key，但为了兼容配置读取，可以填一个占位值。

```env
LLM_PROVIDER=ollama
LLM_API_KEY=ollama
LLM_API_URL=http://127.0.0.1:11434/v1/chat/completions
LLM_MODEL=llama3.1
```

### 自定义 OpenAI-compatible endpoint

```env
LLM_PROVIDER=custom
LLM_API_KEY=sk-your-key
LLM_API_URL=https://your-provider.example.com/v1/chat/completions
LLM_MODEL=your-model-name
```

## 配置项说明

配置优先读取环境变量，其次读取项目根目录 `.env`。旧的 `KIMI_*` 变量仍然兼容，但推荐使用统一的 `LLM_*`。

| 变量 | 默认值 | 说明 |
|---|---|---|
| `LLM_PROVIDER` | `kimi` | `kimi`、`openai`、`openrouter`、`deepseek`、`ollama`、`custom` |
| `LLM_API_KEY` | 空 | OpenAI-compatible API Key；Ollama 可用占位值 |
| `LLM_API_URL` | Kimi chat completions | OpenAI-compatible chat completions 地址 |
| `LLM_MODEL` | `moonshot-v1-128k` | 模型名 |
| `LLM_TIMEOUT` | `60` | 请求超时时间，单位秒 |
| `APP_HOST` | `127.0.0.1` | 默认只监听本机，更安全 |
| `APP_PORT` | `8080` | 服务端口 |

`APP_HOST=127.0.0.1` 表示只有本机可以访问。只有你明确需要局域网内其他设备访问时，才改成 `0.0.0.0`。

## API 概览

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | 前端页面 |
| `/api/health` | GET | 服务状态、术语库数量、LLM provider/model、配置写入状态 |
| `/api/config` | GET | 当前模型配置状态，Key 只脱敏显示 |
| `/api/config/providers` | GET | 供应商预设 |
| `/api/config/test` | POST | 测试临时模型配置 |
| `/api/config/save` | POST | 保存本地 `.env`，仅允许本机调用 |
| `/api/analyze` | POST | 分析论文文本，模型已配置时按全文分块生成中文翻译 |
| `/api/analyze-pdf` | POST | 上传并分析 PDF，返回 `pages/pageCount/textLength/truncated/extractionWarnings` |
| `/api/chat` | POST | 右侧 AI 伴学；请求中可传 `localOnly: true` 强制本地降级回答 |
| `/api/learning/profile` | GET | 当前本地学习画像和阅读记录 |
| `/api/learning/session` | POST | 把一次论文分析沉淀为阅读会话，并推荐下一篇可学习论文 |
| `/api/learning/mastery` | POST | 标记或取消标记术语掌握状态 |
| `/api/papers/search` | GET | 从本地经典映射、术语库和可选外部元数据源搜索论文 |
| `/api/papers/load` | POST | 根据标题/链接/PDF/摘要载入论文；优先抽取 PDF 全文，失败时返回摘要导读 |
| `/api/papers/evidence` | POST | 从当前论文文本中抽取和问题相关的证据片段 |
| `/api/terms` | GET | 获取术语分类列表和双语字段 |
| `/api/terms/{name}` | GET | 获取单个术语详情 |
| `/api/terms/{name}/papers` | POST | 展开相关论文 |
| `/api/terms/{name}/explain` | GET | 生成通俗解释 |
| `/api/terms/{name}/explain-academic` | GET | 生成学术解释 |
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

## OpenClaw 工具配置示例

不同 OpenClaw 版本的工具注册格式可能不同。核心思想是让它访问本地服务地址：

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
      - path: "/api/case-study"
        method: "POST"
```

如果 OpenClaw 和服务不在同一台机器上，需要把 `APP_HOST` 改成 `0.0.0.0`，并把工具里的 URL 改成服务所在机器的局域网地址。

## 常见问题

### 页面能打开，但提示本地模式

说明没有配置 API Key，或连接测试失败。可以点击页面顶部“配置模型”，也可以检查 `.env` 里的 `LLM_API_KEY`、`LLM_API_URL` 和 `LLM_MODEL`。

### OpenClaw bootstrap 找不到 Key

先确认当前运行环境里真的有支持的环境变量：

```bash
echo $OPENAI_API_KEY
echo $OPENROUTER_API_KEY
echo $DEEPSEEK_API_KEY
echo $KIMI_API_KEY
echo $LLM_API_KEY
```

Windows PowerShell 可以用：

```powershell
$env:OPENAI_API_KEY
$env:OPENROUTER_API_KEY
$env:DEEPSEEK_API_KEY
$env:KIMI_API_KEY
$env:LLM_API_KEY
```

### 端口 8080 被占用

修改 `.env`：

```env
APP_PORT=8081
```

然后重新启动，访问 `http://127.0.0.1:8081`。

### PowerShell 不允许运行脚本

使用一次性绕过命令：

```powershell
powershell -ExecutionPolicy Bypass -File .\start_windows.ps1
```

### Python 或依赖安装失败

确认 Python 版本可用：

```powershell
python --version
```

然后重新安装依赖：

```powershell
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

### PDF 无法读取

当前支持可复制文字的 PDF。扫描版 PDF 暂不支持 OCR，会返回明确错误。可以先用其他工具把扫描 PDF 转成可复制文本，再粘贴到文本分析框。

### 想让局域网其他设备访问

把 `.env` 里的 host 改成：

```env
APP_HOST=0.0.0.0
```

然后用服务所在机器的局域网 IP 访问。这样会让同一网络里的设备也能访问服务，请只在你信任的网络里使用。

## 项目结构

```text
backend/app/          # 配置、路由、LLM、PDF、术语、伴学、学习路径
frontend/             # 静态前端
knowledge/            # 双语术语库与学习路径
tests/                # FastAPI 接口测试
tools/                # 术语检查、扩充、OpenClaw bootstrap、API 冒烟
```

## 已知边界

- 扫描版 PDF 暂不支持 OCR。
- AI 伴学第一版不做账号、长期记忆、复杂 RAG 或流式输出。
- 学习画像保存在本地 `data/learning_progress.json`，`data/` 默认不进入版本控制。
- 论文搜索会优先使用本地经典映射和术语库；外部 arXiv/OpenAlex/Semantic Scholar 不可用时会自动降级。
- GROBID、Marker、PaperQA 仍是下一阶段增强方向，当前版本先提供本地结构化解析、adapter 入口和证据片段能力。
- `.env` 是本地开发文件，真实 Key 不进入版本控制。

## License

MIT
