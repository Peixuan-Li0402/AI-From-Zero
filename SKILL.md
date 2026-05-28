# 🧠 AI From Zero — OpenClaw Skill

从零开始的人工智能生活：AI 论文溯源阅读助手，由星野大叔陪伴。

## 概述

这个 Skill 让 OpenClaw 用户获得一个完整的 AI 论文阅读与学习辅助工具，包含：

- **论文智能阅读** — 粘贴论文 → AI 分析摘要 + 术语高亮 + 中文翻译
- **301 个 AI 术语知识库** — 专业名词解释 + 溯源论文 + 难易分级
- **术语通俗/学术解释** — 点术语 → AI 生成详细讲解
- **学习路径推荐** — 4 个方向（LLM/CV/Agent/机器人），各 22-31 篇经典论文
- **案例分析** — 贴真实案例 → AI 识别技术领域 + 推荐学习路径
- **星野大叔聊天** — 关键词即时回复 + LLM 对话双模式

## 技术架构

```
用户浏览器 (Web UI)
      ↕ HTTP
FastAPI 服务器 (Python)
      ↕ API
Kimi / 其他 LLM API
```

## 安装与配置

### 前置要求

- Python 3.10+
- 一个 LLM API Key（支持 Kimi、DeepSeek、OpenAI 等）

### 安装步骤

```bash
# 1. 克隆到 OpenClaw 工作区
git clone https://github.com/Peixuan-Li0402/AI-From-Zero.git ~/.openclaw/workspace/ai-from-zero

# 2. 安装 Python 依赖
pip install -r ~/.openclaw/workspace/ai-from-zero/backend/requirements.txt

# 3. 配置 API Key
#    编辑 ~/.openclaw/workspace/ai-from-zero/backend/server.py
#    找到 KIMI_API_KEY 配置项，替换为你的 Key
```

### 启动

```bash
cd ~/.openclaw/workspace/ai-from-zero/backend
python3 server.py
```

访问 `http://localhost:8080` 即可使用。

## 接入 OpenClaw

### 方式一：作为 Web 工具（推荐）

启动服务器后，OpenClaw 可以通过 HTTP 调用所有 API 端点。

**核心 API 端点：**

| 端点 | 方法 | 说明 |
|---|---|---|
| `/api/analyze` | POST | 分析论文文本，返回摘要+术语+翻译 |
| `/api/terms` | GET | 获取全部术语列表 |
| `/api/terms/{name}` | GET | 查询单个术语详情 |
| `/api/terms/{name}/explain` | GET | 获取术语通俗解释（AI 生成） |
| `/api/terms/{name}/explain-academic` | GET | 获取术语学术解释（AI 生成） |
| `/api/learn-path` | POST | 获取学习路径推荐 |
| `/api/case-study` | POST | 分析案例，返回技术领域+学习路径 |
| `/api/chat` | POST | 星野大叔聊天 |

### 方式二：作为 OpenClaw Tool

在 OpenClaw 配置中添加以下 tool：

```yaml
tools:
  - name: ai-from-zero
    description: "AI 论文阅读与学习辅助工具"
    url: "http://localhost:8080"
    endpoints:
      - path: "/api/analyze"
        method: "POST"
        description: "分析论文，提取术语和摘要"
      - path: "/api/terms/{name}/explain"
        method: "GET"
        description: "获取术语的详细解释"
      - path: "/api/learn-path"
        method: "POST"
        description: "获取学习路径推荐"
      - path: "/api/case-study"
        method: "POST"
        description: "分析案例中的AI技术"
```

### 方式三：作为 Custom Skill

将本项目目录放入 OpenClaw 的 `skills/` 目录，OpenClaw 会自动识别 SKILL.md。

## 术语知识库

包含 **301 个 AI 核心术语**，按 14 个分类组织：

- 训练范式 (40)、训练技巧 (34)、数学基础 (34)、核心概念 (29)
- 基础架构 (28)、当前热点 (24)、计算机视觉 (24)、工程实践 (21)
- 评估指标 (18)、预训练模型 (17)、生成模型 (16)、高级方向 (6)
- 机器人 (6)、基础模型 (4)

每个术语包含：通俗解释、星野吐槽、前置知识引用、经典论文溯源。

## 自定义配置

### 更换 LLM 模型

编辑 `backend/server.py`，修改 `call_kimi()` 函数中的 API 地址和模型名即可切换为 DeepSeek、OpenAI 等。

### 添加更多术语

编辑 `knowledge/term_kb.json`，按格式添加新的术语条目。

### 调整学习路径

编辑 `backend/server.py` 中的 `paths` 字典，添加或修改学习方向。

## 开源协议

MIT
