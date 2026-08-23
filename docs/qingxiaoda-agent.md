# 清小搭智能体部署与验收

AI-From-Zero 通过清小搭“标准协议接入”上线。清小搭中的用户可以发送问题、论文链接、PDF、TXT 或 Markdown，获得论文导读、双语术语、概念链、原文证据和后续论文路径。

## 1. 官方协议对应关系

| 清小搭要求 | AI-From-Zero 实现 |
| --- | --- |
| `GET {baseUrl}/models` | `GET /v1/models`，Bearer 凭证错误返回 `401` |
| `POST {baseUrl}/chat/completions` | `POST /v1/chat/completions`，支持 JSON 与 SSE |
| `stream` 必须是 JSON 布尔值 | 使用严格布尔校验，字符串会返回 `422` |
| `model` 可缺失或未知 | 统一映射为 `ai-from-zero-agent` |
| `max_tokens:1` 探测 | 本地快速通道，不调用论文解析和外部模型 |
| SSE 帧顺序 | role 帧、content 帧、单个 stop 帧、`data: [DONE]` |
| `usage` | 非流式在响应顶层；流式在 stop 帧 |
| 文件只通过 URL 输入 | 支持 `file.url`；不接受 Base64；`file_id` 单独出现时友好降级 |
| 输出附件 | `x_soda.attachments`；流式只在 stop 帧出现一次 |
| 会话学习工作台 | 每轮返回稳定链接；同一会话恢复问答记录、论文正文、术语高亮和学习路径 |

不要把网站根地址或完整对话端点填入清小搭。`API 地址`必须精确填到 `/v1`：

```text
正确：https://your-domain.example/v1
错误：https://your-domain.example
错误：https://your-domain.example/v1/chat/completions
```

## 2. 本地验收

在本地 `.env` 中配置独立的清小搭访问凭证。它不能与模型供应商的 Key 混用：

```env
QXD_API_KEY=your-qxd-key
QXD_MODEL_ID=ai-from-zero-agent
QXD_MAX_ATTACHMENT_MB=25
QXD_MAX_CONCURRENCY=4
QXD_REQUEST_TIMEOUT=80
QXD_STREAM_HEARTBEAT=6
QXD_ARTIFACT_TTL=1800
QXD_WORKSPACE_TTL=604800
QXD_WORKSPACE_LIMIT=100
AGENT_LLM_TIMEOUT=28
AGENT_MAX_TOKENS=1000
AGENT_REALTIME_SEARCH=true
AGENT_SEARCH_TIMEOUT=4.5
PAPER_LLM_CONCURRENCY=4
AGENT_SEARCH_CACHE_TTL=600
```

生成随机凭证：

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

启动服务后运行与清小搭探测规则一致的检查：

```bash
python tools/check_qingxiaoda_compat.py --base-url http://127.0.0.1:8080/v1 --key YOUR_QXD_KEY
```

真实模型对话是独立的慢速检查，不影响平台最小探测：

```bash
python tools/check_qingxiaoda_compat.py --base-url http://127.0.0.1:8080/v1 --key YOUR_QXD_KEY --full-chat
```

## 3. 腾讯云 CloudBase Run 部署

推荐选择上海地域，使用仓库根目录的 `Dockerfile`。服务配置：

```text
构建目录：仓库根目录
Dockerfile：Dockerfile
监听端口：8080
公网访问：开启
最小实例：1
最大实例：1
日志：标准输出
```

最小实例不能为 0，否则冷启动可能超过清小搭单项 5 秒探测。当前学习笔记和会话工作台临时保存在实例本地，因此评审阶段固定为单实例；迁移到数据库和对象存储后再扩容。

环境变量使用以下模板：

```env
APP_HOST=0.0.0.0
APP_PORT=8080

QXD_API_KEY=your-qxd-key
QXD_MODEL_ID=ai-from-zero-agent
QXD_MAX_ATTACHMENT_MB=25
QXD_MAX_CONCURRENCY=4
QXD_REQUEST_TIMEOUT=80
QXD_STREAM_HEARTBEAT=6
QXD_ARTIFACT_TTL=1800
QXD_WORKSPACE_TTL=604800
QXD_WORKSPACE_LIMIT=100
QXD_ALLOW_PRIVATE_DNS_PROXY=false

AGENT_LLM_TIMEOUT=28
AGENT_MAX_TOKENS=1000
AGENT_REALTIME_SEARCH=true
AGENT_SEARCH_TIMEOUT=4.5
PAPER_LLM_CONCURRENCY=4
AGENT_SEARCH_CACHE_TTL=600

LLM_PROVIDER=custom
LLM_API_KEY=your-model-key
LLM_API_URL=https://your-provider.example/v1/chat/completions
LLM_MODEL=your-model-name
LLM_TIMEOUT=75

PUBLIC_BASE_URL=https://YOUR_CLOUDBASE_DOMAIN
```

注意：

- `PUBLIC_BASE_URL` 不带 `/v1`，用于生成学习笔记下载地址和会话学习工作台链接。
- `QXD_ARTIFACT_TTL` 只控制学习笔记下载时间；`QXD_WORKSPACE_TTL` 控制会话工作台保留时间，默认 7 天。
- 工作台使用不可猜测令牌。同一清小搭对话会复用同一链接；协议携带会话 ID 时优先使用，否则根据完整 `messages` 历史续接。
- `AGENT_SEARCH_TIMEOUT` 是每个实时论文来源的上限，三个来源并发执行；超时后使用缓存或本地知识库。
- `AGENT_LLM_TIMEOUT` 应小于 `QXD_REQUEST_TIMEOUT`，给协议封装、会话保存和本地回退留出时间。
- `QXD_REQUEST_TIMEOUT` 在代码中最高限制为 85 秒；流式等待期间按 `QXD_STREAM_HEARTBEAT` 返回进度帧，避免聊天窗口长时间静默。
- 工作台保存于单实例本地目录，重新部署或实例被替换时可能丢失。评审阶段保持最小/最大实例均为 1；长期运行应迁移到 CloudBase 数据库或对象存储。
- `LLM_API_URL` 必须是模型供应商的完整 OpenAI-compatible 对话端点。
- `QXD_API_KEY` 是清小搭访问本服务的门锁；`LLM_API_KEY` 是本服务访问模型的凭证。
- 初次接入不要设置 `QXD_ATTACHMENT_ALLOWED_HOSTS`，避免未知的清小搭 OSS 域名被误拦截。确认实际域名后再配置白名单。
- 云端不要启用 `QXD_ALLOW_PRIVATE_DNS_PROXY`。
- CloudBase 系统默认域名适合接入验证；正式长期运行应使用已备案的自定义域名并启用 HTTPS。

部署完成后先验证：

```bash
curl https://YOUR_CLOUDBASE_DOMAIN/api/health
python tools/check_qingxiaoda_compat.py --base-url https://YOUR_CLOUDBASE_DOMAIN/v1 --key YOUR_QXD_KEY
python tools/check_qingxiaoda_compat.py --base-url https://YOUR_CLOUDBASE_DOMAIN/v1 --key YOUR_QXD_KEY --full-chat
```

公网验收必须在关闭代理/VPN的中国大陆网络执行。脚本默认不读取 `HTTP_PROXY`、`HTTPS_PROXY` 等代理变量，并会拒绝把 `198.18.0.0/15` 等代理 fake-IP 当作直连证据。

## 4. 清小搭后台填写

```text
智能体平台：标准协议接入
API 地址：https://YOUR_CLOUDBASE_DOMAIN/v1
API 密钥：与 QXD_API_KEY 完全一致
鉴权方式：Bearer Token
流式终止符：[DONE]
usage 位置：stop 帧内
```

能力声明只勾选已经实测的能力：

- 流式输出：勾选。
- 文件输入（文档）：完成 PDF/TXT/Markdown 实测后勾选。
- 视觉、音频、工具：当前不要勾选。

点击“测试连接”后，立即在 CloudBase 日志中搜索 `qxd_request`：

- 有 `GET /v1/models` 且状态为 `200`：请求已到应用，继续看最小对话日志。
- 有请求但为 `401`：两端 `QXD_API_KEY` 不一致。
- 完全没有 `qxd_request`：问题在 DNS、网络路由或平台到云服务的连接，不在业务代码。
- 路径是 `/models` 而非 `/v1/models`：清小搭里填写的地址缺少 `/v1`。

## 5. 上线闸门

以下项目全部通过后再提交审核：

1. `/api/health` 中 `agentAuthConfigured`、`publicBaseUrlConfigured`、`llmConfigured` 均为 `true`。
2. 错误凭证访问 `/v1/models` 返回 `401`。
3. `/v1/models` 在 5 秒内返回 `200`。
4. `stream:true,max_tokens:1` 在 5 秒内完成，SSE 以 `[DONE]` 结束。
5. 整轮官方探测少于 15 秒。
6. 普通提问和真实模型回答少于 120 秒。
7. 文本型 PDF 能生成导读；扫描版 PDF 返回明确提示而不是 `500`。
8. 连续追问、术语解释、下一篇论文链接和学习笔记附件各完成一次实测。
9. CloudBase 最小实例为 1，评审期间不缩容到 0。
10. 云日志不会出现 API Key、Authorization 或完整论文正文。

## 6. 上次 Railway 失败的判读

现有 Railway 服务的协议响应是正确的：`/v1/models` 返回 `200`，错误凭证返回 `401`，官方最小 SSE 帧顺序完整。清小搭显示的 `SocketException` 属于建立 HTTP 连接之前的网络错误，不是 JSON、SSE、模型 Key 或 CORS 错误。

本机当时启用了系统代理和 fake-IP DNS；域名被解析到 `198.18.0.0/15`，访问经过代理出口，因而本机测试成功不能证明清小搭服务器能够直连 Railway。Railway 响应头显示请求经过境外边缘节点，也与清小搭国内服务器的直连路径不同。迁移到上海 CloudBase 的目的，是消除这段跨境路由不确定性。

以后只使用两类证据判断问题：

1. 无代理中国大陆网络运行官方探测脚本。
2. 云端 `qxd_request` 日志确认平台请求是否到达应用。

## 7. 附件边界

- 当前稳定读取 PDF、TXT、Markdown，单文件默认上限 25MB。
- 扫描版 PDF、音频、Word/Excel/PPT 会友好提示，不会导致整次对话失败。
- 输入和输出附件都只使用 URL，不接受 Base64。
- 默认拒绝 localhost、私网、链路本地地址、过多重定向和异常 DNS 变化。
- 学习笔记地址默认保留 30 分钟；清小搭收到响应后会转存。

## 8. 部署参考

- 清小搭《自研 Agent 接入清小搭广场 · 开发者指南（OpenAI 兼容协议）》
- 清小搭《多模态附件对端接口文档》v1.0
- 腾讯云 CloudBase Run：[服务设置](https://cloud.tencent.com/document/product/1243/77197)
- 腾讯云 CloudBase Run：[服务开发说明](https://cloud.tencent.com/document/product/1243/53551)
