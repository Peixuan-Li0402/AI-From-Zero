#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KB_PATH = ROOT / "knowledge" / "term_kb.json"


CATEGORY_NOTES = {
    "机器学习与AI": "建模、训练、推理和评估智能系统",
    "自然语言处理": "文本、语言理解、生成和检索增强",
    "计算机视觉": "图像、视频和视觉感知系统",
    "机器人与具身智能": "感知、规划、控制和环境交互",
    "软件工程": "需求、设计、测试、交付和维护",
    "计算机系统": "操作系统、并发、存储和性能工程",
    "数据库与数据工程": "数据建模、查询、事务和分析系统",
    "网络与分布式系统": "通信协议、分布式一致性和服务治理",
    "安全与隐私": "系统安全、密码学、隐私保护和攻防分析",
    "编程语言与编译": "语言设计、程序分析、编译优化和运行时",
    "工程实践": "云原生、MLOps、可观测性和可靠性",
}


RAW_TERMS = {
    "机器学习与AI": """
Gradient Descent|梯度下降|batch gradient descent
Stochastic Gradient Descent|随机梯度下降|SGD
Mini-batch Training|小批量训练|mini batch
Adam Optimizer|Adam优化器|Adam
AdamW|AdamW优化器|decoupled weight decay
RMSProp|RMSProp优化器|
Momentum|动量法|momentum optimizer
Learning Rate Schedule|学习率调度|learning rate scheduler
Warmup|学习率预热|LR warmup
Cosine Decay|余弦退火|cosine annealing
Weight Decay|权重衰减|L2 regularization
Regularization|正则化|
Dropout|随机失活|
Batch Normalization|批归一化|BatchNorm
Layer Normalization|层归一化|LayerNorm
Group Normalization|组归一化|GroupNorm
Activation Function|激活函数|nonlinearity
ReLU|线性整流单元|Rectified Linear Unit
GELU|高斯误差线性单元|Gaussian Error Linear Unit
Swish|Swish激活函数|SiLU
Loss Function|损失函数|objective function
Cross Entropy|交叉熵|cross-entropy loss
Mean Squared Error|均方误差|MSE
Hinge Loss|合页损失|
KL Divergence|KL散度|Kullback-Leibler divergence
Maximum Likelihood Estimation|极大似然估计|MLE
Maximum A Posteriori|最大后验估计|MAP
Bayesian Inference|贝叶斯推断|
Probabilistic Graphical Model|概率图模型|PGM
Expectation Maximization|期望最大化|EM algorithm
Gaussian Mixture Model|高斯混合模型|GMM
Hidden Markov Model|隐马尔可夫模型|HMM
Support Vector Machine|支持向量机|SVM
Kernel Method|核方法|
Decision Tree|决策树|
Random Forest|随机森林|
Gradient Boosting|梯度提升|
XGBoost|极端梯度提升|
LightGBM|LightGBM|
CatBoost|CatBoost|
K-Means|K均值聚类|K-means clustering
DBSCAN|基于密度的聚类|Density-Based Spatial Clustering
Hierarchical Clustering|层次聚类|
Principal Component Analysis|主成分分析|PCA
t-SNE|t分布随机邻域嵌入|
UMAP|统一流形逼近与投影|
Autoencoder|自编码器|AE
Variational Autoencoder|变分自编码器|VAE
Generative Adversarial Network|生成对抗网络|GAN
Diffusion Model|扩散模型|denoising diffusion
Score Matching|得分匹配|
Energy-Based Model|能量模型|EBM
Contrastive Learning|对比学习|
Metric Learning|度量学习|
Triplet Loss|三元组损失|
Few-Shot Learning|少样本学习|
Zero-Shot Learning|零样本学习|
Meta-Learning|元学习|learning to learn
Transfer Learning|迁移学习|
Domain Adaptation|领域自适应|
Domain Generalization|领域泛化|
Semi-Supervised Learning|半监督学习|
Active Learning|主动学习|
Curriculum Learning|课程学习|
Multi-Task Learning|多任务学习|
Continual Learning|持续学习|lifelong learning
Catastrophic Forgetting|灾难性遗忘|
Federated Learning|联邦学习|
Self-Training|自训练|
Pseudo-Labeling|伪标签|
Knowledge Distillation|知识蒸馏|
Teacher-Student Model|师生模型|
Model Compression|模型压缩|
Quantization|量化|
Pruning|剪枝|
Low-Rank Adaptation|低秩适配|LoRA
Parameter-Efficient Fine-Tuning|参数高效微调|PEFT
Prompt Tuning|提示调优|
Prefix Tuning|前缀调优|
Instruction Tuning|指令微调|
RLHF|人类反馈强化学习|Reinforcement Learning from Human Feedback
DPO|直接偏好优化|Direct Preference Optimization
Reward Model|奖励模型|
Alignment|模型对齐|
Hallucination|幻觉|
Calibration|校准|
Uncertainty Estimation|不确定性估计|
Out-of-Distribution Detection|分布外检测|OOD detection
Robustness|鲁棒性|
Adversarial Example|对抗样本|
Explainable AI|可解释人工智能|XAI
SHAP|SHAP解释|
LIME|LIME解释|
Feature Importance|特征重要性|
Data Leakage|数据泄漏|
Train-Test Split|训练测试划分|
Cross Validation|交叉验证|
Hyperparameter Tuning|超参数调优|
Grid Search|网格搜索|
Random Search|随机搜索|
Bayesian Optimization|贝叶斯优化|
Online Learning|在线学习|
Offline Learning|离线学习|
Batch Inference|批量推理|
Online Inference|在线推理|
Model Serving|模型服务|
Feature Engineering|特征工程|
Representation Learning|表示学习|
Manifold Learning|流形学习|
Ensemble Learning|集成学习|
Stacking|堆叠集成|
Bagging|装袋法|
Boosting|提升法|
Bias-Variance Tradeoff|偏差方差权衡|
Overfitting|过拟合|
Underfitting|欠拟合|
Early Stopping|早停|
Label Smoothing|标签平滑|
Class Imbalance|类别不平衡|
Resampling|重采样|
Synthetic Minority Oversampling|少数类合成过采样|SMOTE
""",
    "自然语言处理": """
Tokenization|分词|tokenizer
Subword Tokenization|子词分词|BPE SentencePiece WordPiece
Byte Pair Encoding|字节对编码|BPE
WordPiece|WordPiece分词|
SentencePiece|SentencePiece分词|
Vocabulary|词表|
Embedding|嵌入表示|word embedding
Word2Vec|词向量模型|
GloVe|全局词向量|
Contextual Embedding|上下文嵌入|
Language Model|语言模型|LM
Masked Language Modeling|掩码语言建模|MLM
Causal Language Modeling|因果语言建模|CLM
Encoder-Decoder Model|编码器-解码器模型|seq2seq
Sequence-to-Sequence|序列到序列|Seq2Seq
Beam Search|束搜索|
Greedy Decoding|贪心解码|
Top-k Sampling|Top-k采样|
Top-p Sampling|核采样|nucleus sampling
Temperature Sampling|温度采样|
Perplexity|困惑度|PPL
Named Entity Recognition|命名实体识别|NER
Part-of-Speech Tagging|词性标注|POS tagging
Dependency Parsing|依存句法分析|
Constituency Parsing|成分句法分析|
Coreference Resolution|共指消解|
Text Classification|文本分类|
Sentiment Analysis|情感分析|
Question Answering|问答系统|QA
Machine Reading Comprehension|机器阅读理解|MRC
Information Extraction|信息抽取|IE
Relation Extraction|关系抽取|
Event Extraction|事件抽取|
Text Summarization|文本摘要|
Abstractive Summarization|生成式摘要|
Extractive Summarization|抽取式摘要|
Machine Translation|机器翻译|MT
Dialogue System|对话系统|
Retrieval-Augmented Generation|检索增强生成|RAG
Dense Retrieval|稠密检索|
Sparse Retrieval|稀疏检索|
BM25|BM25检索|
Vector Database|向量数据库|vector store
Chunking|文本切块|document chunking
Reranker|重排序模型|
In-Context Learning|上下文学习|ICL
Prompt Engineering|提示工程|
Prompt Injection|提示注入|
Function Calling|函数调用|tool calling
Agent Planning|智能体规划|
Tool Use|工具使用|
Long Context|长上下文|
Context Window|上下文窗口|
Position Encoding|位置编码|
Rotary Position Embedding|旋转位置编码|RoPE
ALiBi|线性位置偏置|
KV Cache|键值缓存|
Speculative Decoding|推测解码|
Mixture of Experts|混合专家模型|MoE
Routing|专家路由|
""",
    "计算机视觉": """
Image Classification|图像分类|
Object Detection|目标检测|
Semantic Segmentation|语义分割|
Instance Segmentation|实例分割|
Panoptic Segmentation|全景分割|
Image Captioning|图像描述|
Visual Question Answering|视觉问答|VQA
Optical Character Recognition|光学字符识别|OCR
Face Recognition|人脸识别|
Pose Estimation|姿态估计|
Depth Estimation|深度估计|
Stereo Matching|双目匹配|
Optical Flow|光流|
Visual Tracking|视觉跟踪|
Image Retrieval|图像检索|
Feature Pyramid Network|特征金字塔网络|FPN
Region Proposal Network|区域建议网络|RPN
Anchor Box|锚框|
Intersection over Union|交并比|IoU
Non-Maximum Suppression|非极大值抑制|NMS
Mean Average Precision|平均精度均值|mAP
Data Augmentation|数据增强|
Mixup|Mixup增强|
CutMix|CutMix增强|
RandAugment|随机增强|
Vision Transformer|视觉Transformer|ViT
Swin Transformer|Swin Transformer|
CLIP|图文对比预训练|
ImageNet|ImageNet数据集|
COCO Dataset|COCO数据集|
Mask R-CNN|Mask R-CNN|
YOLO|YOLO检测器|
DETR|DETR检测器|
Stable Diffusion|稳定扩散|
ControlNet|控制网络|
NeRF|神经辐射场|
Gaussian Splatting|高斯泼溅|
Multimodal Learning|多模态学习|
Visual Grounding|视觉定位|
Document AI|文档智能|
""",
    "机器人与具身智能": """
Robot Operating System|机器人操作系统|ROS
SLAM|同时定位与建图|Simultaneous Localization and Mapping
Localization|定位|
Mapping|建图|
Path Planning|路径规划|
Motion Planning|运动规划|
Trajectory Optimization|轨迹优化|
Inverse Kinematics|逆运动学|IK
Forward Kinematics|正运动学|FK
PID Control|PID控制|
Model Predictive Control|模型预测控制|MPC
Imitation Learning|模仿学习|
Behavior Cloning|行为克隆|
Sim-to-Real Transfer|仿真到现实迁移|
Reinforcement Learning for Robotics|机器人强化学习|
Embodied AI|具身智能|
World Model|世界模型|
Visual Servoing|视觉伺服|
Grasp Planning|抓取规划|
Manipulation|机器人操作|
Navigation|机器人导航|
Occupancy Grid|占据栅格|
Point Cloud|点云|
LiDAR|激光雷达|
Sensor Fusion|传感器融合|
""",
    "软件工程": """
Requirements Engineering|需求工程|
Use Case|用例|
User Story|用户故事|
Acceptance Criteria|验收标准|
Software Architecture|软件架构|
Architectural Pattern|架构模式|
Design Pattern|设计模式|
SOLID Principles|SOLID原则|
Coupling|耦合|
Cohesion|内聚|
Modularity|模块化|
Abstraction|抽象|
Encapsulation|封装|
Interface Segregation|接口隔离|
Dependency Injection|依赖注入|
Inversion of Control|控制反转|IoC
Refactoring|重构|
Technical Debt|技术债|
Code Smell|代码异味|
Clean Code|整洁代码|
Code Review|代码评审|
Static Analysis|静态分析|
Dynamic Analysis|动态分析|
Unit Testing|单元测试|
Integration Testing|集成测试|
System Testing|系统测试|
End-to-End Testing|端到端测试|E2E testing
Regression Testing|回归测试|
Property-Based Testing|性质测试|
Mutation Testing|变异测试|
Fuzz Testing|模糊测试|fuzzing
Test Coverage|测试覆盖率|
Test Double|测试替身|
Mock Object|模拟对象|mock
Stub|桩|
Continuous Integration|持续集成|CI
Continuous Delivery|持续交付|CD
Continuous Deployment|持续部署|
Build System|构建系统|
Dependency Management|依赖管理|
Semantic Versioning|语义化版本|SemVer
API Compatibility|API兼容性|
Backward Compatibility|向后兼容|
Feature Flag|功能开关|
Canary Release|金丝雀发布|
Blue-Green Deployment|蓝绿部署|
A/B Testing|AB测试|
Observability|可观测性|
Logging|日志|
Metrics|指标|
Tracing|链路追踪|
Incident Response|故障响应|
Postmortem|故障复盘|
""",
    "计算机系统": """
Operating System|操作系统|OS
Kernel|内核|
System Call|系统调用|
Process|进程|
Thread|线程|
Coroutine|协程|
Context Switch|上下文切换|
Scheduler|调度器|
Preemption|抢占|
Concurrency|并发|
Parallelism|并行|
Synchronization|同步|
Mutex|互斥锁|
Semaphore|信号量|
Condition Variable|条件变量|
Deadlock|死锁|
Livelock|活锁|
Race Condition|竞态条件|
Atomic Operation|原子操作|
Memory Model|内存模型|
Virtual Memory|虚拟内存|
Page Table|页表|
TLB|快表|Translation Lookaside Buffer
Cache|缓存|
Cache Coherence|缓存一致性|
NUMA|非统一内存访问|
File System|文件系统|
Journaling|日志文件系统|
RAID|磁盘阵列|
I/O Scheduler|IO调度器|
DMA|直接内存访问|
Interrupt|中断|
Polling|轮询|
Memory Leak|内存泄漏|
Garbage Collection|垃圾回收|GC
Reference Counting|引用计数|
Heap|堆|
Stack|栈|
Profiling|性能剖析|
Benchmarking|基准测试|
Latency|延迟|
Throughput|吞吐量|
Tail Latency|尾延迟|
Backpressure|背压|
Load Shedding|负载削减|
""",
    "数据库与数据工程": """
Relational Database|关系型数据库|
NoSQL Database|NoSQL数据库|
Document Database|文档数据库|
Key-Value Store|键值存储|
Columnar Database|列式数据库|
Graph Database|图数据库|
Time-Series Database|时序数据库|
SQL|结构化查询语言|
Query Optimizer|查询优化器|
Execution Plan|执行计划|
Index|索引|
B-Tree|B树|
LSM Tree|日志结构合并树|
Hash Index|哈希索引|
Transaction|事务|
ACID|ACID特性|
Isolation Level|隔离级别|
MVCC|多版本并发控制|
Two-Phase Commit|两阶段提交|2PC
Write-Ahead Log|预写日志|WAL
Checkpoint|检查点|
Replication|复制|
Sharding|分片|
Partitioning|分区|
CAP Theorem|CAP定理|
Eventual Consistency|最终一致性|
Data Warehouse|数据仓库|
Data Lake|数据湖|
Lakehouse|湖仓一体|
ETL|抽取转换加载|
ELT|抽取加载转换|
Data Pipeline|数据流水线|
Stream Processing|流处理|
Batch Processing|批处理|
Apache Spark|Spark计算引擎|
Apache Flink|Flink流处理|
Kafka|Kafka消息系统|
Data Lineage|数据血缘|
Data Quality|数据质量|
Schema Evolution|模式演进|
Feature Store|特征库|
""",
    "网络与分布式系统": """
TCP|传输控制协议|
UDP|用户数据报协议|
HTTP|超文本传输协议|
HTTPS|安全HTTP|
HTTP/2|HTTP二代协议|
HTTP/3|HTTP三代协议|
QUIC|QUIC协议|
DNS|域名系统|
CDN|内容分发网络|
Load Balancer|负载均衡器|
Reverse Proxy|反向代理|
API Gateway|API网关|
RPC|远程过程调用|
gRPC|gRPC框架|
Message Queue|消息队列|
Publish-Subscribe|发布订阅|
Distributed Consensus|分布式共识|
Raft|Raft共识算法|
Paxos|Paxos算法|
Leader Election|主节点选举|
Distributed Lock|分布式锁|
Distributed Transaction|分布式事务|
Clock Synchronization|时钟同步|
Vector Clock|向量时钟|
Lamport Clock|Lamport时钟|
Consistent Hashing|一致性哈希|
Service Discovery|服务发现|
Service Mesh|服务网格|
Circuit Breaker|熔断器|
Retry|重试|
Timeout|超时|
Rate Limiting|限流|
Idempotency|幂等性|
Exactly-Once Semantics|恰好一次语义|
At-Least-Once Semantics|至少一次语义|
At-Most-Once Semantics|至多一次语义|
""",
    "安全与隐私": """
Authentication|身份认证|
Authorization|授权|
Access Control|访问控制|
OAuth|OAuth协议|
OpenID Connect|OpenID Connect|
JWT|JSON Web Token|
TLS|传输层安全|
Public Key Cryptography|公钥密码学|
Symmetric Encryption|对称加密|
Hash Function|哈希函数|
Digital Signature|数字签名|
Certificate Authority|证书颁发机构|CA
Key Management|密钥管理|
Threat Model|威胁模型|
Attack Surface|攻击面|
Vulnerability|漏洞|
Exploit|漏洞利用|
SQL Injection|SQL注入|
Cross-Site Scripting|跨站脚本|XSS
Cross-Site Request Forgery|跨站请求伪造|CSRF
Buffer Overflow|缓冲区溢出|
Privilege Escalation|权限提升|
Sandboxing|沙箱|
Zero Trust|零信任|
Secure Coding|安全编码|
Static Application Security Testing|静态应用安全测试|SAST
Dynamic Application Security Testing|动态应用安全测试|DAST
Software Bill of Materials|软件物料清单|SBOM
Supply Chain Security|供应链安全|
Differential Privacy|差分隐私|
Homomorphic Encryption|同态加密|
Secure Multi-Party Computation|安全多方计算|MPC
Trusted Execution Environment|可信执行环境|TEE
Model Extraction Attack|模型窃取攻击|
Membership Inference Attack|成员推断攻击|
Data Poisoning|数据投毒|
""",
    "编程语言与编译": """
Abstract Syntax Tree|抽象语法树|AST
Intermediate Representation|中间表示|IR
Control Flow Graph|控制流图|CFG
Data Flow Analysis|数据流分析|
Static Single Assignment|静态单赋值|SSA
Type System|类型系统|
Type Inference|类型推断|
Polymorphism|多态|
Generics|泛型|
Trait|特征|
Ownership|所有权|
Borrow Checker|借用检查器|
Memory Safety|内存安全|
Null Safety|空安全|
Exception Handling|异常处理|
Pattern Matching|模式匹配|
Functional Programming|函数式编程|
Object-Oriented Programming|面向对象编程|OOP
Logic Programming|逻辑编程|
Metaprogramming|元编程|
Macro|宏|
Just-In-Time Compilation|即时编译|JIT
Ahead-of-Time Compilation|提前编译|AOT
Linker|链接器|
Loader|加载器|
Register Allocation|寄存器分配|
Instruction Scheduling|指令调度|
Loop Optimization|循环优化|
Inlining|内联|
Dead Code Elimination|死代码消除|DCE
Common Subexpression Elimination|公共子表达式消除|CSE
Escape Analysis|逃逸分析|
Runtime System|运行时系统|
Virtual Machine|虚拟机|VM
Bytecode|字节码|
WebAssembly|WebAssembly|WASM
""",
    "工程实践": """
DevOps|开发运维一体化|
MLOps|机器学习运维|
LLMOps|大模型运维|
AI Gateway|AI网关|
Prompt Cache|提示缓存|
Semantic Cache|语义缓存|
Batch API|批量API|
Token Budget|Token预算|
Context Compression|上下文压缩|
Embedding Service|嵌入服务|
Retrieval Pipeline|检索流水线|
Groundedness Evaluation|忠实性评测|
Answer Relevance|答案相关性|
Faithfulness|事实忠实性|
Toxicity Detection|毒性检测|
PII Redaction|个人信息脱敏|
Secret Scanning|密钥扫描|
Policy as Code|策略即代码|
Progressive Delivery|渐进式交付|
Shadow Traffic|影子流量|
Synthetic Monitoring|合成监控|
Chaos Engineering|混沌工程|
DataOps|数据运维|
GitOps|GitOps|
Infrastructure as Code|基础设施即代码|IaC
Containerization|容器化|
Docker|Docker|
Kubernetes|Kubernetes|K8s
Pod|Pod|
Deployment|部署对象|
Service|服务对象|
Ingress|入口网关|
Helm|Helm包管理|
Autoscaling|自动扩缩容|
Horizontal Pod Autoscaler|水平自动扩缩容|HPA
Serverless|无服务器|
Cloud Native|云原生|
Microservices|微服务|
Monolith|单体架构|
Event-Driven Architecture|事件驱动架构|
Command Query Responsibility Segregation|命令查询职责分离|CQRS
Event Sourcing|事件溯源|
Model Registry|模型注册表|
Experiment Tracking|实验追踪|
Model Monitoring|模型监控|
Data Drift|数据漂移|
Concept Drift|概念漂移|
Prompt Versioning|提示版本管理|
Evaluation Harness|评测框架|
Red Teaming|红队测试|
Guardrails|安全护栏|
Content Filtering|内容过滤|
Human-in-the-Loop|人在回路|
SLO|服务等级目标|
SLA|服务等级协议|
Error Budget|错误预算|
Runbook|运行手册|
Capacity Planning|容量规划|
Cost Optimization|成本优化|
Service Level Indicator|服务等级指标|SLI
Mean Time To Recovery|平均恢复时间|MTTR
Mean Time Between Failures|平均故障间隔|MTBF
Root Cause Analysis|根因分析|RCA
Change Management|变更管理|
Release Train|发布列车|
Platform Engineering|平台工程|
Internal Developer Platform|内部开发者平台|IDP
Developer Experience|开发者体验|DevEx
Golden Path|黄金路径|
Self-Service Portal|自助服务门户|
FinOps|云成本运营|
Service Catalog|服务目录|
Configuration Drift|配置漂移|
Drift Detection|漂移检测|
Policy Engine|策略引擎|
Admission Controller|准入控制器|
Sidecar Proxy|边车代理|
Control Plane|控制平面|
Data Plane|数据平面|
""",
}


def split_aliases(raw: str) -> list[str]:
    return [item.strip() for item in raw.replace(",", " ").split() if item.strip()]


def is_english(value: str) -> bool:
    return any("a" <= ch.lower() <= "z" for ch in value)


def enrich_existing(term: dict) -> None:
    aliases = [a for a in term.get("aliases", []) if isinstance(a, str)]
    english_aliases = [a for a in aliases if is_english(a)]
    zh_aliases = [a for a in aliases if any("\u4e00" <= ch <= "\u9fff" for ch in a)]
    term_has_english = is_english(term["term"])
    term["termEn"] = term.get("termEn") or (term["term"] if term_has_english else (english_aliases[0] if english_aliases else term["term"]))
    term["termZh"] = term.get("termZh") or (term["term"] if not term_has_english else term.get("fullName") or term["term"])
    term["fullNameEn"] = term.get("fullNameEn") or term["termEn"]
    term["fullNameZh"] = term.get("fullNameZh") or term.get("fullName") or term["termZh"]
    term["aliasesEn"] = sorted(set(term.get("aliasesEn", []) + english_aliases))
    term["aliasesZh"] = sorted(set(term.get("aliasesZh", []) + zh_aliases))
    term["explanationZh"] = term.get("explanationZh") or term.get("explanation", "")
    term["explanationEn"] = term.get("explanationEn") or (
        f"{term['termEn']} is an important concept in {term.get('category', 'computer science')}. "
        f"It is used to reason about {term.get('fullName', term['termZh'])} in practical systems and research papers."
    )
    term["academicExplanationZh"] = term.get("academicExplanationZh") or (
        f"{term['termZh']}（{term['termEn']}）通常需要结合定义、算法假设、适用场景和局限性理解。"
        "阅读论文时可以关注它解决的问题、输入输出、优化目标、评估指标以及与相邻概念的区别。"
    )


def make_term(en: str, zh: str, category: str, aliases: list[str]) -> dict:
    note = CATEGORY_NOTES[category]
    aliases_en = sorted({a for a in aliases if is_english(a) and a.lower() != en.lower()})
    aliases_zh = sorted({a for a in aliases if any("\u4e00" <= ch <= "\u9fff" for ch in a) and a != zh})
    all_aliases = sorted({zh, en, *aliases_en, *aliases_zh})
    return {
        "term": en,
        "termEn": en,
        "termZh": zh,
        "fullName": zh,
        "fullNameEn": en,
        "fullNameZh": zh,
        "category": category,
        "difficulty": 2,
        "aliases": all_aliases,
        "aliasesEn": aliases_en,
        "aliasesZh": aliases_zh,
        "explanation": f"{zh}（{en}）是{note}里的常用概念。理解它有助于把论文中的方法、系统设计和工程取舍连接起来。",
        "explanationZh": f"{zh}（{en}）是{note}里的常用概念。阅读论文时可以从定义、解决的问题、典型用法、优缺点和评估方式五个角度理解它。",
        "explanationEn": f"{en} is a core concept in {category}. It helps describe problems, methods, trade-offs, and evaluation criteria in research and engineering practice.",
        "academicExplanationZh": f"{zh}（{en}）在{category}中通常用于刻画问题建模、系统约束或算法机制。学习时应关注其形式化定义、适用假设、复杂度或成本、常见评估指标以及与相关概念的边界。",
        "hoshinoNote": f"{zh}这个词先抓住用途就好：它帮你看懂论文里到底在优化什么、牺牲什么、验证什么。",
        "prerequisiteTerms": [],
        "landmarkPapers": [],
        "relatedTerms": [],
    }


def parse_raw_terms() -> list[dict]:
    items = []
    for category, raw in RAW_TERMS.items():
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            en, zh, aliases = (line.split("|") + ["", ""])[:3]
            items.append(make_term(en.strip(), zh.strip(), category, split_aliases(aliases)))
    return items


def normalize_aliases(terms: list[dict]) -> None:
    term_names = {t["term"].strip().lower(): t["term"] for t in terms}
    alias_owner = {}
    for term in terms:
        cleaned = []
        for alias in term.get("aliases", []):
            if not isinstance(alias, str) or not alias.strip():
                continue
            alias = alias.strip()
            key = alias.lower()
            if key == term["term"].lower():
                continue
            if key in term_names and term_names[key] != term["term"]:
                continue
            if key in alias_owner and alias_owner[key] != term["term"]:
                continue
            alias_owner[key] = term["term"]
            cleaned.append(alias)
        term["aliases"] = cleaned
        term["aliasesEn"] = sorted({a for a in term.get("aliasesEn", []) if isinstance(a, str) and a.strip() and a.strip().lower() not in term_names})
        term["aliasesZh"] = sorted({a for a in term.get("aliasesZh", []) if isinstance(a, str) and a.strip()})


def main() -> None:
    kb = json.loads(KB_PATH.read_text(encoding="utf-8"))
    terms = kb["terms"]
    for term in terms:
        enrich_existing(term)

    existing_keys = set()
    for term in terms:
        existing_keys.add(term["term"].strip().lower())
        existing_keys.add(term.get("termZh", "").strip().lower())
        for alias in term.get("aliases", []):
            existing_keys.add(str(alias).strip().lower())

    added = 0
    for term in parse_raw_terms():
        keys = {term["term"].lower(), term["termZh"].lower(), *[a.lower() for a in term["aliases"]]}
        if keys & existing_keys:
            continue
        terms.append(term)
        existing_keys.update(keys)
        added += 1

    normalize_aliases(terms)
    kb["version"] = "3.0"
    kb["lastUpdated"] = "2026-06-01"
    kb["terms"] = terms
    KB_PATH.write_text(json.dumps(kb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Added {added} terms; total {len(terms)}")


if __name__ == "__main__":
    main()
