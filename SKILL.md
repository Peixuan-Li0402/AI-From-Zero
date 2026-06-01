# AI From Zero — OpenClaw Skill

AI-From-Zero 是一个本地 AI 论文溯源阅读助手，适合接入 OpenClaw 作为 Web 工具或 Custom Skill。

## 能力入口

- 文本分析：`POST /api/analyze`，输入论文正文，返回术语、高亮数据、摘要、翻译和 `llmStatus`。
- PDF 分析：`POST /api/analyze-pdf`，按页提取可复制文字 PDF，返回全文、页数、字符数、分块分析状态和术语结果。
- AI 伴学：`POST /api/chat`，结合当前论文、当前术语、已掌握术语和最近对话回答问题。
- 模型配置：`GET /api/config`、`GET /api/config/providers`、`POST /api/config/test`、`POST /api/config/save`。
- 术语库：`GET /api/terms`、`GET /api/terms/{name}`，返回双语术语字段和解释。
- 相关论文：`POST /api/terms/{name}/papers`。
- 学习路径：`POST /api/learn-path`。
- 案例分析：`POST /api/case-study`。

## 启动

Windows PowerShell：

```powershell
cd C:\Users\lenovo\Documents\AI-FROM-ZERO
python -m pip install -r backend/requirements.txt
.\start_windows.ps1
```

通用命令：

```bash
cd AI-From-Zero
python -m pip install -r backend/requirements.txt
./start.sh
```

访问地址默认是：

```text
http://localhost:8080
```

## OpenClaw 配置建议

如果 OpenClaw 启动环境里已经有模型 Key，先运行：

```bash
python tools/bootstrap_openclaw_env.py
```

脚本只读取这些显式环境变量：`OPENAI_API_KEY`、`OPENROUTER_API_KEY`、`DEEPSEEK_API_KEY`、`KIMI_API_KEY`、`LLM_API_KEY`。它不会读取或复制 OpenClaw 私有配置文件里的密钥。

也可以在网页顶部点“配置模型”，手动填写 OpenAI-compatible endpoint：

```env
LLM_PROVIDER=kimi
LLM_API_KEY=
LLM_API_URL=https://api.moonshot.cn/v1/chat/completions
LLM_MODEL=moonshot-v1-128k
LLM_TIMEOUT=60
APP_HOST=127.0.0.1
APP_PORT=8080
```

## Tool 配置示例

```yaml
tools:
  - name: ai-from-zero
    description: "AI 论文阅读、术语溯源与伴学工具"
    url: "http://localhost:8080"
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

## 冒烟检查

```bash
python tools/check_term_kb.py
python tools/check_api_smoke.py --base-url http://127.0.0.1:8080
```

## 注意

- 未配置 Key 时，文本分析、PDF 分析和伴学都会使用本地术语库降级。
- 扫描版 PDF 暂不支持 OCR。
- 术语库已升级为双语字段；旧字段仍保留，便于前端和旧调用兼容。
