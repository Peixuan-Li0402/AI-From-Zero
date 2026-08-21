# AI-From-Zero Agent v2 研究与决策记录

## 目标

把 AI-From-Zero 从“能接入清小搭的论文问答接口”升级为稳定的论文学习智能体：回答快、失败可降级、来源可核对、对新手友好，并能把清小搭对话持续映射到原版阅读器。

研究只参考项目官方仓库和官方文档。清小搭案例截图用于分析交互方式，不作为训练数据，也不复制其中的人物、数据库或专有内容。

## 研究样本（40 个）

| 项目 | 重点学习的搭建思路 | 本项目取舍 |
| --- | --- | --- |
| [LangGraph](https://github.com/langchain-ai/langgraph) | 显式状态、持久执行、可恢复流程 | 借鉴状态与阶段边界，不引入完整框架 |
| [LangChain](https://github.com/langchain-ai/langchain) | 模型、工具和数据源的适配层 | 借鉴 provider/tool adapter 思想 |
| [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) | 确定性工作流与非确定性 Agent 组合 | 采用“代码路由 + 模型生成”双层结构 |
| [AutoGen](https://github.com/microsoft/autogen) | 对话式多智能体协作 | 仅研究；项目已进入维护模式且多 Agent 会增加延迟 |
| [Semantic Kernel](https://github.com/microsoft/semantic-kernel) | 插件、会话、企业级编排 | 借鉴能力边界与会话状态 |
| [CrewAI](https://github.com/crewAIInc/crewAI) | Crews 与事件驱动 Flows 分离 | 借鉴“开放任务/确定流程”分治，不启用角色群聊 |
| [LlamaIndex](https://github.com/run-llama/llama_index) | 文档解析、索引、检索和 Agent 工具 | 借鉴分层检索与文档上下文包 |
| [Haystack](https://github.com/deepset-ai/haystack) | 显式检索、路由、记忆、生成流水线 | 借鉴可观察的检索管线 |
| [DSPy](https://github.com/stanfordnlp/dspy) | 用评测驱动模块和提示词优化 | 采用独立开发集与盲测集，不在生产中引入编译器 |
| [smolagents](https://github.com/huggingface/smolagents) | 小而清楚的模型—工具循环 | 借鉴最小运行时，避免重依赖 |
| [PydanticAI](https://github.com/pydantic/pydantic-ai) | 类型约束、依赖注入、结构化输出 | 延续 Pydantic 请求校验和严格布尔类型 |
| [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) | 工具、护栏、会话、追踪和 handoff | 借鉴会话与护栏；本项目暂不需要 handoff |
| [Google ADK](https://github.com/google/adk-python) | 确定步骤和模型推理交错、artifact | 借鉴学习笔记 artifact 与预算化执行 |
| [Agno](https://github.com/agno-agi/agno) | 轻量 Agent、会话和团队运行时 | 借鉴轻量会话，不引入团队调度 |
| [Mastra](https://github.com/mastra-ai/mastra) | 工作流、记忆、评测和可观测性 | 借鉴评测入口和运行指标 |
| [AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) | 长任务循环和 Agent 平台 | 不采用无限自治循环，避免清小搭超时 |
| [MetaGPT](https://github.com/FoundationAgents/MetaGPT) | 用 SOP 固化多角色协作 | 借鉴“流程先于角色”，不复制多角色结构 |
| [CAMEL](https://github.com/camel-ai/camel) | 角色协作与 Agent 社会模拟 | 仅用于理解多 Agent，不进入生产链路 |
| [OpenHands](https://github.com/All-Hands-AI/OpenHands) | action-observation 循环和隔离工作区 | 借鉴不可信附件边界，不开放代码执行 |
| [AgentScope](https://github.com/agentscope-ai/agentscope) | 让强模型发挥工具能力，减少僵硬提示 | 提示词改为目标和边界，不规定固定回答模板 |
| [Dify](https://github.com/langgenius/dify) | 模型供应商、工作流、知识库一体化 | 保留通用 OpenAI-compatible 配置与本地知识库 |
| [Flowise](https://github.com/FlowiseAI/Flowise) | 可视化 Agent/RAG 流程 | 不引入可视化编排，保持部署轻量 |
| [n8n](https://github.com/n8n-io/n8n) | 工作流连接器、重试和错误分支 | 借鉴来源级超时、错误隔离与回退 |
| [Langflow](https://github.com/langflow-ai/langflow) | 组件化工作流及 API/MCP 暴露 | 保持 OpenAI-compatible API，未来可加 MCP adapter |
| [Qwen-Agent](https://github.com/QwenLM/Qwen-Agent) | 工具使用、规划、记忆和评测 | 借鉴工具前路由和会话历史 |
| [Langroid](https://github.com/langroid/langroid) | Agent、任务、向量库和工具组合 | 借鉴任务边界，不采用多 Agent 消息循环 |
| [Mem0](https://github.com/mem0ai/mem0) | 选择性记忆与单次检索 | 仅保存学习相关状态，不把全部聊天塞回模型 |
| [Letta](https://github.com/letta-ai/letta) | 持久身份、记忆和跨端会话 | 借鉴清小搭—阅读器稳定会话映射 |
| [PaperQA2](https://github.com/Future-House/paper-qa) | 文档检索、证据选择和引用问答 | 采用页码证据片段和来源标签 |
| [GPT Researcher](https://github.com/assafelovic/gpt-researcher) | 并行研究、多来源和带引用报告 | 采用并发学术检索，不采用长时间深研循环 |
| [GraphRAG](https://github.com/microsoft/graphrag) | 用图结构组织长文档上下文 | 借鉴概念链；不引入高成本图索引服务 |
| [LightRAG](https://github.com/HKUDS/LightRAG) | 轻量图/向量检索、上下文返回与评测 | 借鉴“返回检索依据”和轻量概念关系 |
| [RAGFlow](https://github.com/infiniflow/ragflow) | 文档理解、RAG 与 Agent 上下文层 | 借鉴结构化 PDF 上下文；不增加重型服务依赖 |
| [Strands Agents](https://github.com/strands-agents/sdk-python) | model-driven 的小型工具循环 | 维持单 Agent 和有限工具集 |
| [NeMo Agent Toolkit](https://github.com/NVIDIA/NeMo-Agent-Toolkit) | 性能分析、可观测性和多框架适配 | 增加延迟指标和独立验收脚本 |
| [MCP reference servers](https://github.com/modelcontextprotocol/servers) | 标准工具边界与安全提示 | 后续可做 MCP；当前先保证清小搭协议稳定 |
| [LiteLLM](https://github.com/BerriAI/litellm) | 多模型统一网关、路由和回退 | 继续使用 OpenAI-compatible provider 层，不新增网关服务 |
| [Chroma](https://github.com/chroma-core/chroma) | 文档向量检索和元数据过滤 | 当前 820 条术语规模不需要向量数据库 |
| [Magentic-One](https://github.com/microsoft/autogen/tree/main/python/packages/autogen-ext/src/autogen_ext/teams/magentic_one) | 任务账本和经理—执行者分工 | 借鉴阶段状态，不引入多 Agent 成本 |
| [Rasa](https://github.com/RasaHQ/rasa) | 确定性对话流程与生成式能力组合 | 借鉴“可预测流程负责关键路径” |

## 共性结论

1. 高质量 Agent 的核心不是角色数量，而是状态、工具、证据、超时、回退和评测。
2. 能由普通函数可靠完成的步骤，不应交给模型自由决定。
3. 检索应返回来源和上下文，不能只把搜索结果藏在提示词里。
4. 多 Agent 适合长任务协作，但会增加调用次数、延迟和故障面，不适合清小搭当前的短时探测与聊天窗口。
5. 记忆应保存用户学习状态和会话连续性，而不是无限累积原始聊天。
6. 模型输出需要允许一定语言变化；事实、链接和证据边界必须稳定。

## 最终架构决策

### 1. 单智能体、双层执行

- 第一层是确定性代码：识别术语解释、概念关系、论文搜索、学习路径、论文证据问答和普通伴学。
- 第二层是模型生成：只处理需要归纳、解释或上下文推理的复杂问题。
- 术语和概念桥走本地快速路径，不等待模型。

### 2. 双源学习证据

- 自建知识：820 条双语术语、概念链、经典论文和 4 条论文学习路径。
- 实时知识：并发查询 arXiv、OpenAlex、Semantic Scholar。
- 回答明确显示“论文原文 / 自建术语库 / 实时论文源”，让用户知道答案从哪里来。

### 3. 有预算的实时搜索

- 三个学术来源并发，不串行累加等待。
- 每个来源有独立超时；失败后短时熔断。
- 相同查询短期缓存；缓存只保存公开论文元数据。
- 外部来源全部失败时，仍返回本地经典论文和术语结果。

### 4. 学习罗盘与概念桥

- 从对话自然推断入门/探索/进阶、学习目标和兴趣，不强迫填写问卷。
- 用户比较两个概念时，本地生成双语“概念桥”：定义、前置链、延伸链和区分方法。
- 清小搭每轮返回稳定阅读器网址，学习画像、来源、术语和对话同步显示。

### 5. 柔性提示词

- 只规定事实边界、附件安全、来源要求和交流目标。
- 不要求每次固定输出“总结—步骤—追问”模板。
- 用户跑题时先自然回应，再用一个轻量建议回到论文或学习目标。

### 6. 可复现评测

- `train` 只用于设计规则，`dev` 用于迭代，`test` 只在最终验收运行。
- 四个集合的 ID、主题和问题严格不重叠，并有自动泄漏检查。
- 本地评测关闭模型和外部搜索，随机生成措辞变体，验证路由、知识库回答和延迟。
- 模型质量、网络搜索和清小搭 SSE 协议分别测试，避免把不同故障混成一个分数。

## 明确不采用的高风险路径

- 不引入多 Agent 群聊：收益不足以抵消延迟和不稳定性。
- 不在首版部署向量数据库或图数据库：当前知识规模可以用内存索引稳定处理。
- 不让模型自行无限搜索或反思：所有工具调用都有次数和时间上限。
- 不把测试集放进提示词、知识库或运行时。
- 不依赖单一外部论文 API；任一来源故障都可降级。
- 不开放任意代码执行、内网访问或 Base64 附件。

## 验收标准

- 清小搭探测 `max_tokens=1` 在 1 秒内返回完整 SSE 顺序。
- 本地术语快路径在常规机器上保持毫秒级。
- 三路实时搜索的总等待接近最慢单路，而不是三路之和。
- 无模型 Key、模型超时、论文源失败、附件解析失败都不返回 500。
- 同一清小搭会话持续复用同一阅读器网址。
- 盲测集在冻结实现后一次运行，结果与开发集分开记录。

第一轮盲测中，`SSA` 和 `Fuzzing` 的规范英文名称正确，但回答标题没有保留用户使用的缩写/别名，因此按验收规则失败。修复“回答保留用户命名”这一通用问题后，原集合转为回归测试；另建主题完全不同的 `test_round2` 作为第二轮盲测。该过程保留失败事实，不把修复后的重跑冒充首次通过。

第二轮盲测同样没有一次通过：`LSM Tree` 和 `Property-Based Testing` 已被知识库正确识别，但“简单讲讲”“有什么用”未包含旧路由器要求的固定触发词，因此误入普通问答。修复采用通用语义优先级：先判断论文搜索、学习路径、原文证据和实时研究，其余明确命中知识库术语的请求直接进入术语教学，不针对两个失败样例写特例。修复后第二轮集合仅作为回归测试使用。

## 最终验收记录

- 全仓测试：`59 passed`。
- 评测隔离：`train=8`、`dev=8`、`test=8`、`test_round2=8`，ID、主题和规范化问题无交叉。
- 开发集：8 个案例、每题 3 个固定种子措辞变体全部通过，中位延迟 4.9ms，P95 27.4ms。
- 第二轮集合修复后回归：8 个案例、24 次运行全部通过，中位延迟 5.1ms，P95 27.5ms。
- 随机不变量审计：固定种子从完整术语库抽取 160 个术语，全部命中本地术语教学快路径。
- 清小搭协议：鉴权、`/v1/models`、最小对话、SSE role/content/stop/usage/`[DONE]`、完整非流式对话全部通过；最小对话 2ms，完整本地回退对话 13ms。
- 实时论文检索：arXiv、OpenAlex、Semantic Scholar 并发调用；单个来源失败时仍返回自建论文库与其他成功来源，FlashAttention 实测得到可打开的 arXiv 论文链接。
- 阅读器映射：清小搭会话网址、学习阶段、当前目标、来源和对话内容均能恢复；多术语句子会选择最近明确要求解释的概念。
- 浏览器验收：桌面端与 390px 手机端均无横向溢出，移动导航不遮挡正文，伴学栏只有一个实例。全页截图遇到滚动容器拼接伪影时，以 DOM 数量和普通视口截图复核。

已知技术债：当前 PDF 兼容层仍引用已弃用的 `PyPDF2`，测试只产生弃用警告，不影响运行；后续应迁移到 `pypdf`，但本轮不为消除警告贸然改动稳定解析链路。
