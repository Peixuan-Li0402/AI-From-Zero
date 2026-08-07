# 清小搭智能体接入

AI-From-Zero 提供 OpenAI-compatible Agent 端点。清小搭中的用户可以直接发送论文问题、PDF、TXT 或 Markdown，获得论文导读、双语术语、概念链、原文证据和后续论文路径。

## 1. 本地验证

在 `.env` 中增加独立的清小搭访问凭证。不要复用模型 API Key：

```env
QXD_API_KEY=YOUR_QXD_KEY
QXD_MODEL_ID=ai-from-zero-agent
QXD_MAX_ATTACHMENT_MB=25
QXD_MAX_CONCURRENCY=4
```

可以用 Python 生成随机凭证：

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

启动服务后运行：

```bash
python tools/check_qingxiaoda_compat.py --base-url http://127.0.0.1:8080/v1 --key YOUR_QXD_KEY
```

清小搭使用的两个端点是：

- `GET /v1/models`
- `POST /v1/chat/completions`

错误或缺失凭证返回 `401`；服务未配置 `QXD_API_KEY` 时返回 `503`。

## 2. Railway 部署

1. 登录 Railway，选择 **New Project → Deploy from GitHub repo**。
2. 选择 `Peixuan-Li0402/AI-From-Zero` 和 `master` 分支。
3. Railway 会自动识别根目录的 `Dockerfile` 和 `railway.toml`。
4. 在 Variables 中配置：

```env
QXD_API_KEY=YOUR_QXD_KEY
PUBLIC_BASE_URL=https://your-service.up.railway.app
LLM_PROVIDER=your_provider
LLM_API_KEY=your_model_key
LLM_API_URL=https://your-provider.example/v1/chat/completions
LLM_MODEL=your_model
APP_HOST=0.0.0.0
```

`PORT` 由 Railway 自动注入，不要手动填写。`LLM_*` 未配置时，智能体仍会用本地知识库运行，但回答质量会受限。

部署完成后执行公网探测：

```bash
python tools/check_qingxiaoda_compat.py --base-url https://your-service.up.railway.app/v1 --key YOUR_QXD_KEY
```

评审期间不要启用自动休眠。建议设置费用提醒，并确保服务在比赛检查期间保持运行。

## 3. 清小搭后台

填写以下信息：

```text
Base URL: https://your-service.up.railway.app/v1
Auth: Bearer Token
Credential: 与 QXD_API_KEY 完全一致
Stream terminator: [DONE]
Usage position: stop 帧
Model: ai-from-zero-agent
```

先运行接入探测，再依次试聊：

1. `解释 Transformer，并给出概念链。`
2. 上传文本型论文 PDF，发送 `给我一条阅读路线。`
3. 继续追问 `论文在哪一页支持这个结论？`
4. 发送 `推荐下一篇论文，必须给可访问链接。`
5. 发送 `生成学习笔记。`，确认出现 Markdown 附件。

## 4. 附件规则

- PDF、TXT、Markdown 会被下载并解析，单文件默认上限 25MB。
- 图片会在上游模型支持视觉输入时使用；否则只处理文字问题。
- 扫描版 PDF、音频和其他暂不支持的文件会返回提示，不会导致整次对话失败。
- 所有输入和输出附件都只使用 URL，不接受 Base64。
- 默认拒绝 localhost、私网、链路本地地址和异常 DNS 变化。
- `QXD_ATTACHMENT_ALLOWED_HOSTS` 留空时允许通过安全检查的公网域名；确认清小搭附件域名后，可填写逗号分隔白名单进一步收紧。
- 某些校园网或企业代理会把公网域名解析到代理私网地址。仅在可信的本地代理环境中可设置 `QXD_ALLOW_PRIVATE_DNS_PROXY=true`；公网部署必须保持 `false`。

## 5. 学习笔记附件

设置 `PUBLIC_BASE_URL` 后，用户请求生成学习笔记时，服务会返回 `x_soda.attachments`。文件使用随机临时地址并默认保留 30 分钟，清小搭收到响应后会转存文件。

没有配置 `PUBLIC_BASE_URL` 时，笔记正文仍会直接显示，但不会产生下载附件。

## 6. 排障

- `/models` 返回 `503`：云端没有配置 `QXD_API_KEY`。
- 返回 `401`：清小搭凭证与 `QXD_API_KEY` 不一致。
- 探测超时：确认填写的是到 `/v1` 为止的公网 HTTPS 地址，并关闭自动休眠。
- PDF 无法解析：确认 PDF 可以选中文字；扫描版需要先进行 OCR。
- 模型回答降级：检查 `/api/health` 中的 `llmConfigured`，并验证 `LLM_*` 变量。
- 附件无法下载：检查文件是否超过限制、是否为公网 URL，以及附件域名白名单。
- 公网域名被提示为私网：当前网络可能使用私网代理 DNS。本地可按上一节启用兼容开关，Railway 中不要启用。
