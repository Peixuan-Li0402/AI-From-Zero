# 评分映射

## 部署与连接完整性

- `start_windows.ps1` 和 `start.sh` 提供本地一键启动。
- `tools/check_release_readiness.py` 提供发布自检。
- `/v1/models` 和 `/v1/chat/completions` 提供清小搭 OpenAI-compatible 接入，包含 Bearer 鉴权和 SSE 流式响应。
- `Dockerfile`、`railway.toml` 和清小搭兼容探测脚本支持公网部署与平台验收。
- `/api/integrations/status`、`/api/integrations/messages/inbound`、`/api/integrations/messages/send` 支持 QQ/微信桥接。
- `tools/openclaw_ai_from_zero.py message` 支持无真实平台凭证时的本地模拟验收。

## 技能/项目完成度

- `/api/analyze`、`/api/analyze-pdf` 支持论文文本和 PDF。
- `/api/terms`、`/api/terms/{name}` 支持双语术语解释。
- `/api/papers/load` 和 `/api/demo-cases/{id}/load` 支持推荐论文进入阅读器。
- `/api/learning/session` 支持学习记录和下一篇推荐。
- `/api/chat` 支持上下文伴学。

## 技术探索与真实性

- PDF page-aware 抽取和全文展示。
- arXiv / OpenAlex / Semantic Scholar 轻量论文搜索。
- OpenAI-compatible 模型配置。
- URL 附件输入、SSRF 防护、PDF 解析缓存和 `x_soda.attachments` 学习笔记输出。
- 无 Key 降级模式。
- GitHub Actions CI 和本地测试套件。

## 创新性

- 核心不是“问答”，而是“论文 -> 术语 -> 概念链 -> 下一篇论文 -> 伴学”的学习闭环。
- 内置双语术语库和固定演示案例，降低初学者入门门槛。

## 展示表达

- README 提供从零启动路径。
- SKILL.md 提供 OpenClaw 接入路径。
- `docs/competition/demo-script.md` 提供答辩演示脚本。
