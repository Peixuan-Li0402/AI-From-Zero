# 🧠 从零开始的人工智能生活 — AI 论文溯源阅读助手

> 由**小鸟游星野（Takanashi Hoshino）** 陪伴你读完第一篇AI论文。

## 痛点

刚进AI专业的高中生/大一新生，面对海量论文和专业名词时：
1. **名词链断层** — 读 Attention Is All You Need，里面提到 CNN/RNN 你全不知道，要反查半天
2. **方向迷茫** — AI 分那么多方向（LLM/CV/Robotics/Agent...），不知道从哪学起
3. **学用脱节** — 学的内容和论文成果之间隔着一层雾，不知道学了有什么用

## 解决方案

一个接入星野语音的桌面组件/网页工具：

| 功能 | 说明 |
|---|---|
| 📖 论文智能阅读 | 上传论文 → 标出专业名词 → 侧栏实时解释 |
| 🔗 溯源式学习 | 不懂的概念→给出原始论文引用→点进去继续读 |
| ✅ 已掌握标记 | 学会的概念下次不再解释 |
| 🗺️ 学习路径 | 按方向整理好的论文阅读路线 |
| 🎯 志趣推荐 | 告诉星野你喜欢啥 → 推荐适合的论文和技术路线 |

## 技术架构

```
用户上传论文/输入URL
      ↓
  Python 后端 (FastAPI)
      ├── PDF/HTML 文本提取
      ├── LLM Agent (Kimi/DeepSeek) → 术语提取+解释
      └── 术语知识库查询
      ↓
  HTML 前端阅读界面
      ├── 论文原文/译文
      ├── 术语侧栏（高亮标注+解释+溯源链接）
      ├── 已掌握标记系统
      └── 星野对话窗口
```

## 快速开始

```bash
# 安装后端依赖
cd backend
pip install -r requirements.txt

# 启动服务
python server.py

# 打开浏览器访问
http://localhost:8080
```

## 项目结构

```
ai-from-zero/
├── backend/          # Python 后端
│   ├── server.py     # FastAPI 服务
│   ├── paper_reader.py   # 论文解析
│   ├── term_extractor.py # 术语提取+LLM
│   └── requirements.txt
├── frontend/         # 前端页面
│   ├── index.html    # 主界面
│   ├── reader.html   # 阅读界面
│   └── style.css
├── knowledge/        # AI 术语知识库
│   ├── term_kb.json  # 结构化术语数据
│   └── paper_graph.json  # 论文引用关系
└── data/             # 运行时数据
```

## 开源协议

MIT
