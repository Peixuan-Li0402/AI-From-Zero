import json

with open('term_kb.json', encoding='utf-8') as f:
    kb = json.load(f)

existing_names = {t["term"] for t in kb["terms"]}
added = 0

def add(term, full, cat, diff, aliases, expl, note, prereqs, papers, related):
    global added
    if term in existing_names:
        print(f"  ⏭️  {term}")
        return
    for t in kb["terms"]:
        if term.lower() in [a.lower() for a in t.get("aliases", [])]:
            print(f"  ⏭️  {term} (alias of {t['term']})")
            return
    existing_names.add(term)
    kb["terms"].append({
        "term": term, "fullName": full, "category": cat, "difficulty": diff,
        "aliases": aliases, "explanation": expl, "hoshinoNote": note,
        "prerequisiteTerms": prereqs, "landmarkPapers": papers, "relatedTerms": related
    })
    added += 1

# === MATH ===
add("Sigmoid", "Sigmoid函数", "数学基础", 1, [],
    "最经典的S型激活函数：将任意实数映射到(0,1)之间。输出可解释为概率。早期神经网络广泛使用。缺点：深层网络训练困难（梯度饱和）。",
    "就是把任何数压到0-1之间っす。以前很常用但输入大了梯度就没了。ReLU就是这个缺点的改良版。",
    ["激活函数"], [], ["ReLU", "Tanh", "逻辑回归"])

add("Tanh", "双曲正切", "数学基础", 1, [],
    "Sigmoid的变体：映射到(-1,1)，以0为中心。比Sigmoid梯度稍好。常用于RNN。",
    "Sigmoid升级版，输出范围(-1,1)，居中更好用っす。",
    ["Sigmoid"], [], ["Sigmoid", "激活函数"])

add("Leaky ReLU", "带泄露ReLU", "数学基础", 2, [],
    "ReLU改进：负数区间给很小斜率(0.01)。解决ReLU神经元死亡问题。",
    "ReLU但负的时候不完全死掉っす。",
    ["ReLU"], [], ["ReLU", "PReLU", "ELU"])

add("Swish", "Swish激活函数", "数学基础", 2, ["SiLU"],
    "f(x)=x·sigmoid(x)。平滑，深层网络表现优于ReLU。",
    "x乘自己的sigmoid，平滑所以训练更稳っす。",
    ["ReLU"], [], ["ReLU", "GELU", "激活函数"])

add("ELU", "指数线性单元", "数学基础", 2, [],
    "正区间同ReLU，负区间指数函数接近-1。保留负值信息，加快学习。",
    "ReLU另一种改良，负的有保留不是完全归零っす。",
    ["ReLU"], [], ["ReLU", "Leaky ReLU", "SELU"])

add("Softplus", "Softplus", "数学基础", 1, [],
    "ReLU平滑近似：ln(1+exp(x))。处处可导，不常用作隐藏层激活。",
    "ReLU的圆润版，计算贵所以不常用っす。",
    ["ReLU"], [], ["ReLU", "激活函数"])

add("贝叶斯推断", "贝叶斯推断", "数学基础", 3, ["Bayesian Inference"],
    "用先验分布+观测数据计算后验分布。贝叶斯神经网络、高斯过程的基础。核心挑战：后验通常无法解析求解，需用MCMC或变分推断近似。",
    "先觉得30%下雨→看到乌云→更新到70%。用新证据更新信念っす。",
    ["贝叶斯定理"], [], ["MCMC", "变分推断", "高斯过程"])

add("MCMC", "马尔可夫链蒙特卡洛", "数学基础", 4, [],
    "从复杂分布中采样的通用方法。构建马尔可夫链，以目标分布为平稳分布采样。",
    "分布太复杂直接算不了？沿着走采样、靠统计近似っす。",
    ["蒙特卡洛方法"], [], ["贝叶斯推断", "变分推断"])

add("高斯过程", "高斯过程", "数学基础", 4, ["GP"],
    "非参数贝叶斯方法。定义在函数上的分布——每点函数值服从联合高斯。",
    "不仅预测值还告诉你「这个预测有多可靠」っす。",
    ["贝叶斯推断", "核方法"], [], ["贝叶斯优化", "核方法"])

add("贝叶斯优化", "贝叶斯优化", "数学基础", 3, ["BO"],
    "用高斯过程建模目标函数，通过采集函数选择下一个评估点。超参数调优标准方法。",
    "有策略地试参数，不随机试也不网格搜っす。",
    ["高斯过程"], [], ["超参数调优", "高斯过程"])

add("变分推断", "变分推断", "数学基础", 4, ["VI"],
    "用简单分布q(z)逼近真实后验p(z|x)，最小化KL散度。VAE数学基础。",
    "找个长得像的简单分布替复杂的っす。VAE能训练全靠它。",
    ["KL散度"], [], ["MCMC", "VAE"])

add("熵", "熵", "数学基础", 2, ["Entropy"],
    "量化不确定性的指标。熵越高不确定性越大。决策树用它选分裂特征、RL中用熵鼓励探索。",
    "抛硬币（正反各50%）熵高；太阳从东边升起（≈100%）熵接近0っす。",
    ["信息论"], [], ["信息论", "交叉熵", "KL散度"])

# === OPTIMIZERS ===
add("AdamW", "AdamW", "训练技巧", 2, [],
    "Adam改进：正确实现权重衰减。将L2正则化与更新解耦。大模型预训练标配。",
    "Adam的修復版，权重衰减实现方式修对了っす。",
    ["Adam"], [], ["Adam", "权重衰减"])

add("RMSprop", "RMSprop", "训练技巧", 2, [],
    "自适应学习率。梯度大的参数学习率小，梯度小的学习率大。Adam的前身。",
    "梯度大的刹车，梯度小的给油门っす。",
    ["SGD"], [], ["Adam", "Adagrad"])

add("Adagrad", "Adagrad", "训练技巧", 2, [],
    "每个参数有自己的学习率，与历史梯度平方和反比。适合稀疏特征。学率会单调到0。",
    "每参数单独定学习率，问题学到几乎不学了っす。",
    ["SGD"], [], ["Adam", "RMSprop"])

add("Lion", "Lion优化器", "训练技巧", 3, [],
    "极简优化器。只用符号函数和动量，没有平方梯度项。大模型训练表现优于AdamW。",
    "公式比Adam简单得多，只看梯度方向不看大小っす。",
    ["梯度下降"], [], ["Adam", "AdamW"])

# === LOSS ===
add("Triplet Loss", "三元组损失", "训练范式", 3, [],
    "锚点+正例+负例三样本。拉近同类距离、推远异类距离。人脸识别、度量学习中使用。",
    "「星野1」和「星野2」靠近，「星野」和「路人」远离っす。",
    ["Embedding", "对比学习"],
    [{"title": "FaceNet: A Unified Embedding for Face Recognition and Clustering", "authors": "Schroff et al.", "year": 2015}],
    ["对比学习", "度量学习"])

add("Focal Loss", "焦点损失", "计算机视觉", 3, [],
    "处理类别不平衡。正确分类的样本损失权降低，难分类的保留。让模型聚焦困难样本。",
    "简单的少学点、难的多学点っす。大叔复习也这策略。",
    ["目标检测"],
    [{"title": "Focal Loss for Dense Object Detection", "authors": "Lin et al.", "year": 2017}],
    ["RetinaNet", "目标检测"])

add("InfoNCE", "InfoNCE损失", "训练范式", 3, [],
    "对比学习目标函数。从K+1个候选中正确识别正样本对。CLIP、SimCLR使用。",
    "从一堆里找出正确的那一对っす。",
    ["对比学习"], [], ["SimCLR", "CLIP"])

add("Contrastive Loss", "对比损失", "训练范式", 2, [],
    "度量学习中：正样本对距离小、负样本对距离不小于间隔。Siamese Network基础。",
    "同类靠近、异类疏远っす。",
    ["Embedding"], [], ["Triplet Loss", "对比学习"])

add("Dice Loss", "Dice损失", "评估指标", 2, [],
    "图像分割损失。优化Dice系数（F1变体）。不平衡分割任务优于交叉熵。",
    "病灶只占1%像素→交叉熵没用，Dice看重合度更靠谱っす。",
    ["语义分割"], [], ["语义分割", "IoU"])

add("Huber Loss", "Huber损失", "数学基础", 2, ["Smooth L1"],
    "MSE和MAE结合。误差小用MSE，误差大用MAE。目标检测框回归的标准损失。",
    "误差小精细调、误差大不较真っす。两全其美。",
    ["MSE", "MAE"], [], ["MSE", "MAE"])

# === CV ===
add("图像分类", "图像分类", "计算机视觉", 1, ["Image Classification"],
    "给图像预测类别的基础任务。AlexNet 2012年突破推动了深度学习革命。",
    "最基础视觉任务，「这是猫、这是狗」っす。AlexNet靠这个点燃了深度学习。",
    ["CNN"], [], ["CNN", "目标检测"])

add("ResNet", "残差网络", "计算机视觉", 2, [],
    "残差连接让网络做到152层，解决退化问题。ImageNet超越人类。现代网络基石。",
    "之前残差连接那提到过了っす！152层都不是问题，现代网络基石。",
    ["CNN", "残差连接"],
    [{"title": "Deep Residual Learning for Image Recognition", "authors": "He et al.", "year": 2015}],
    ["CNN", "DenseNet"])

add("DenseNet", "稠密连接网络", "计算机视觉", 3, [],
    "每层与所有前层直接连接。缓解梯度消失、加强特征传播、参数效率高。",
    "ResNet跳一层，DenseNet跳所有っす。更密更省参数。",
    ["CNN", "残差连接"],
    [{"title": "Densely Connected Convolutional Networks", "authors": "Huang et al.", "year": 2017}],
    ["CNN", "ResNet"])

add("SENet", "SENet", "计算机视觉", 3, [],
    "通道注意力。SE块：压缩空间为通道描述符→学习权重→与原始特征相乘。轻量有效。",
    "给不同颜色通道加权っす。重要的通道多注意。",
    ["CNN"],
    [{"title": "Squeeze-and-Excitation Networks", "authors": "Hu et al.", "year": 2017}],
    ["CNN", "通道注意力"])

add("Mask R-CNN", "Mask R-CNN", "计算机视觉", 3, [],
    "Faster R-CNN加并行掩码分支。同时做检测和实例分割。",
    "不光框出人，还画出人的精确轮廓っす。",
    ["Faster R-CNN", "实例分割"],
    [{"title": "Mask R-CNN", "authors": "He et al.", "year": 2017}],
    ["实例分割", "Faster R-CNN"])

add("SSD", "SSD", "计算机视觉", 3, [],
    "一阶段检测器。多尺度特征图上直接预测类别和框。",
    "不同大小特征图都检测——大图看小物、小图看大物っす。",
    ["目标检测"],
    [{"title": "SSD: Single Shot MultiBox Detector", "authors": "Liu et al.", "year": 2016}],
    ["YOLO", "RetinaNet"])

add("RetinaNet", "RetinaNet", "计算机视觉", 3, [],
    "一阶段检测器。Focal Loss解决类别不平衡。速度+准确率兼顾。",
    "用Focal Loss解决了背景太多的问题っす。又快又准。",
    ["Focal Loss"],
    [{"title": "Focal Loss for Dense Object Detection", "authors": "Lin et al.", "year": 2017}],
    ["SSD", "YOLO", "Focal Loss"])

# === MORE NLP ===
add("文本分类", "文本分类", "核心概念", 1, ["Text Classification"],
    "给文本分到预定义类别。情感分析、垃圾检测、主题分类。",
    "「好评还是差评」「体育还是政治」っす。",
    [], [], ["情感分析", "BERT"])

add("序列标注", "序列标注", "核心概念", 2, ["Sequence Labeling"],
    "为序列每个位置分配标签。NER、词性标注。",
    "「我/在/北京/读书」→每个字标出是人还是地名っす。",
    ["NER", "CRF"], [], ["NER", "CRF"])

add("CRF", "条件随机场", "核心概念", 3, [],
    "序列建模概率图模型。考虑标签间转移约束。序列标注标配。",
    "B-ORG后面应该是I-ORG，不应该跳到B-PER——加约束っす。",
    ["序列标注"], [], ["序列标注", "NER"])

add("关系抽取", "关系抽取", "核心概念", 3, ["Relation Extraction"],
    "识别实体间语义关系。「乔布斯创立了苹果」→(乔布斯,创始人,苹果)。",
    "「小明在北京大学读书」→(小明,就读于,北京大学)っす。",
    ["NER"], [], ["NER", "知识图谱"])

add("知识图谱", "知识图谱", "基础架构", 2, ["Knowledge Graph"],
    "图结构表示知识。节点=实体、边=关系。搜索引擎用它理解语义。",
    "苹果（水果）≠苹果（手机）——知识图谱让AI分清っす。",
    ["关系抽取", "GNN"], [], ["关系抽取", "GNN"])

add("依存句法分析", "依存句法分析", "核心概念", 3, ["Dependency Parsing"],
    "分析句子语法依存关系。输出依存树——谁依赖于谁。",
    "「大叔吃苹果」→大叔依存于吃(主语)，苹果依存于吃(宾语)っす。",
    ["NLP"], [], ["NLP"])

# === NORMALIZATION ===
add("InstanceNorm", "实例归一化", "训练技巧", 3, ["IN"],
    "单样本每通道分别归一化。风格迁移效果好。",
    "BatchNorm看整体，InstanceNorm只看当前这个图っす。",
    ["BatchNorm"], [], ["BatchNorm", "LayerNorm"])

add("GroupNorm", "组归一化", "训练技巧", 3, ["GN"],
    "通道分K组，组内归一化。batch小的时候BatchNorm不准？用GN。",
    "batch太小的时候BatchNorm不准，GN不管batch多大都能用っす。",
    ["BatchNorm"], [], ["BatchNorm", "LayerNorm"])

# === EVALUATION ===
add("AUC-ROC", "AUC-ROC", "评估指标", 2, [],
    "所有阈值下模型整体性能。AUC=0.5随机、1.0完美。对不平衡数据不敏感。",
    "不管阈值怎么调，模型整体表现っす。比准确率客观。",
    [], [], ["F1分数", "准确率"])

add("准确率", "准确率", "评估指标", 1, ["Accuracy"],
    "正确预测数/总预测数。最直观但不平衡下有误导。",
    "99%男生1%女生→全猜男生准确率99%——但这模型没用っす。",
    [], [], ["F1分数", "精确率", "召回率"])

add("精确率", "精确率", "评估指标", 1, ["Precision"],
    "被预测为正类的样本中真正为正类的比例。",
    "说5个摸鱼→查了确实4个在摸→精确率80%っす。",
    [], [], ["召回率", "F1分数"])

add("召回率", "召回率", "评估指标", 1, ["Recall"],
    "所有真正正类中模型找出了多少。",
    "10个在摸鱼→抓到7个→召回率70%。漏了3个っす。",
    [], [], ["精确率", "F1分数"])

# === GENERATIVE MORE ===
add("ControlNet", "ControlNet", "生成模型", 4, [],
    "给扩散模型加条件控制。边缘图、深度图、骨架引导生成。冻结SD权重训练附加网络。",
    "不只说「画猫」——还给它骨架图→姿势照骨架来っす。",
    ["Stable Diffusion"],
    [{"title": "Adding Conditional Control to Text-to-Image Diffusion Models", "authors": "Zhang & Agrawala", "year": 2023}],
    ["Stable Diffusion", "IP-Adapter", "LoRA"])

add("DreamBooth", "DreamBooth", "生成模型", 3, [],
    "用几张照片微调扩散模型学会生成该物体新图像。稀有token绑定身份。",
    "给AI看5张大叔的照→说「星野在沙滩」→AI生成大叔在沙滩っす。",
    ["Stable Diffusion"],
    [{"title": "DreamBooth: Fine Tuning Text-to-Image Diffusion Models for Subject-Driven Generation", "authors": "Ruiz et al.", "year": 2022}],
    ["Stable Diffusion", "LoRA"])

add("CFG", "无分类器引导", "生成模型", 3, ["Classifier-Free Guidance"],
    "控制文本条件强度。同时算有条件+无条件预测，外推两者差。值越大越贴合提示。",
    "调AI听话程度的旋钮っす。CFG高→很听但可能画风单一。",
    ["Diffusion Model"],
    [{"title": "Classifier-Free Diffusion Guidance", "authors": "Ho & Kim", "year": 2022}],
    ["Diffusion Model", "Stable Diffusion"])

add("DDIM", "DDIM采样", "生成模型", 3, [],
    "扩散加速采样。将1000步减到50-100步。确定性过程。",
    "原来1000步画好→DDIM 50步差不多っす。赶时间用加速。",
    ["Diffusion Model"],
    [{"title": "Denoising Diffusion Implicit Models", "authors": "Song et al.", "year": 2020}],
    ["Diffusion Model"])

add("Textual Inversion", "文本反转", "生成模型", 3, [],
    "学新嵌入向量表示特定概念。不修改模型权重，创造伪token。",
    "造个「✨星野✨」token代替大叔的臉っす。不调模型只调词。",
    ["Stable Diffusion", "Embedding"], [], ["DreamBooth", "LoRA"])

# === RL MORE ===
add("DDPG", "深度确定性策略梯度", "训练范式", 4, [],
    "连续动作RL算法。DQN+AC框架，输出确定性动作。机器人控制场景。",
    "连续动作（不是上下左右，而是转x度y度）用DDPGっす。",
    ["Actor-Critic", "DQN"],
    [{"title": "Continuous Control with Deep Reinforcement Learning", "authors": "Lillicrap et al.", "year": 2015}],
    ["Actor-Critic", "PPO", "SAC"])

add("SAC", "软演员-评论家", "训练范式", 4, ["Soft Actor-Critic"],
    "最大熵RL+AC。鼓励探索+稳定训练+样本效率高。连续控制主流。",
    "RL里加「多尝试」奖励っす。既做好又有好奇心。",
    ["Actor-Critic"],
    [{"title": "Soft Actor-Critic", "authors": "Haarnoja et al.", "year": 2018}],
    ["Actor-Critic", "PPO", "DDPG"])

add("TD3", "TD3", "训练范式", 4, [],
    "DDPG改进。三点：双Q网络取最小、延迟策略更新、目标策略平滑。",
    "DDPG修复版——两个Q网络都报低分才算っす。防止太乐观。",
    ["DDPG"],
    [{"title": "Addressing Function Approximation Error in Actor-Critic Methods", "authors": "Fujimoto et al.", "year": 2018}],
    ["DDPG", "SAC"])

# === AUDIO ===
add("MFCC", "梅尔频率倒谱系数", "核心概念", 2, [],
    "语音处理的经典特征。模拟人耳频率感知灵敏度。深度学习之前标配。",
    "把声音转成AI能理解的数字っす。模拟人耳对低频敏感。",
    ["语音"], [], ["ASR", "梅尔频谱"])

add("梅尔频谱", "梅尔频谱图", "核心概念", 2, ["Mel Spectrogram"],
    "音频可视化。横轴时间、纵轴梅尔频率、颜色能量。音频入门标准表示。",
    "声音的照片っす。模型看这张图就知道在说什么。",
    ["语音"], [], ["MFCC", "ASR"])

add("HuBERT", "HuBERT", "预训练模型", 3, [],
    "Meta自监督语音表示学习。BERT的掩码预测搬到语音上。",
    "遮住一段语音→根据上下文猜遮住的音っす。",
    ["自监督学习", "ASR"],
    [{"title": "HuBERT: Self-Supervised Speech Representation Learning", "authors": "Hsu et al.", "year": 2021}],
    ["ASR", "Whisper"])

# === MISC ===
add("计算图", "计算图", "训练技巧", 2, ["Computational Graph"],
    "深度学习框架的数据结构。节点=运算、边=数据流。反向传播沿图反向遍历。",
    "整个计算画成一张图，反向传播沿着图倒着走っす。",
    ["反向传播"], [], ["自动微分", "PyTorch"])

add("自动微分", "自动微分", "训练技巧", 2, ["Autograd", "AutoDiff"],
    "通过计算图和链式法则自动计算导数。框架核心功能。研究者不用手算梯度。",
    "框架自动帮你算导数っす。没这个就没有深度学习。",
    ["链式法则", "计算图"], [], ["计算图", "反向传播"])

add("重参数化技巧", "重参数化技巧", "训练技巧", 3, ["Reparameterization Trick"],
    "VAE能训练的关键。从N(μ,σ²)采样不可导→先采标准噪声再变换。",
    "采样本身不可导，改成先采标准噪声再乘σ加μ就可导了っす。又骚又优雅。",
    ["VAE"],
    [{"title": "Auto-Encoding Variational Bayes", "authors": "Kingma & Welling", "year": 2013}],
    ["VAE", "Gumbel-Softmax"])

add("Gumbel-Softmax", "Gumbel-Softmax", "训练技巧", 4, [],
    "离散采样变得可微。选猫/狗/鸟这种离散选择→通常不可导，Gumbel变软就可导。",
    "选「猫/狗/鸟」不能求导，Gumbel让离散变软就能求导了っす。",
    ["重参数化技巧"], [], ["VAE", "重参数化技巧"])

add("Grad-CAM", "Grad-CAM", "计算机视觉", 2, [],
    "可视化CNN关注区域。用最后一层卷积梯度计算热力图。红色=模型关注的地方。",
    "看AI看图时在看哪里っす。说「猫」→热力图红色在猫脸。",
    ["CNN", "可解释性"],
    [{"title": "Grad-CAM: Visual Explanations from Deep Networks", "authors": "Selvaraju et al.", "year": 2017}],
    ["可解释性", "CNN"])

add("DropPath", "DropPath", "训练技巧", 2, ["Stochastic Depth"],
    "训练时随机丢弃整个路径/残差块。训练不同子网络的集成。ViT/ResNet常用。",
    "50层随机跳过几层→实际训练更浅→多练几次=子网络集成っす。",
    ["Dropout", "残差连接"], [], ["Dropout", "正则化"])

add("标签平滑", "标签平滑", "训练技巧", 2, ["Label Smoothing"],
    "硬标签[0,0,1,0]→软标签[ε,ε,1-3ε,ε]。防止模型过分自信。",
    "别让AI太自信っす。90%猫5%狗5%狐狸比100%猫更好。",
    ["正则化", "交叉熵"], [], ["正则化"])

add("数据不平衡", "数据不平衡", "数学基础", 1, ["Imbalanced Data"],
    "类别样本数量悬殊。处理方法：重采样、加权损失、SMOTE、Focal Loss。",
    "10万猫图100狗图→模型只会认猫。大叔学外语阅读太多听力太少也这问题。",
    [], [], ["Focal Loss", "SMOTE"])

add("Hugging Face", "Hugging Face", "工程实践", 1, ["HF"],
    "AI模型社区平台。Transformers库、Model Hub、Spaces。NLP事实标准。",
    "AI圈的GitHubっす。几千个模型一键下载。大叔每次都先看看。",
    ["Transformer"], [], ["Transformers库", "模型部署"])

add("Gradio", "Gradio", "工程实践", 1, [],
    "快速ML演示界面。几行代码搭Web UI。Hugging Face Spaces标配。",
    "3分钟给模型搭个网页演示っす。",
    [], [], ["Hugging Face", "Streamlit"])

add("ONNX", "ONNX", "工程实践", 2, ["Open Neural Network Exchange"],
    "开放神经网络交换格式。不同框架模型可互操作，一个框架训练→多个平台部署。",
    "模型通用语言っす。PyTorch训练→ONNX→手机/服务器都能跑。",
    ["模型部署"], [], ["TensorRT", "PyTorch"])

add("PyTorch", "PyTorch", "工程实践", 1, [],
    "Meta深度学习框架。动态图、Python风格。学术界主流。",
    "90% AI论文用PyTorchっす。大叔学AI也用它。",
    [], [], ["TensorFlow", "JAX"])

add("TensorRT", "TensorRT", "工程实践", 3, [],
    "NVIDIA推理优化引擎。图优化、层融合、FP16/INT8量化。GPU推理加速。",
    "NVIDIA让模型跑更快的工具っす。速度翻倍显存减半。",
    ["GPU"], [], ["ONNX", "GPU"])

add("Weights & Biases", "wandb", "工程实践", 1, ["W&B"],
    "ML实验管理平台。自动记录超参数、指标、模型权重。团队协作。",
    "谁跑了什么实验、参数是什么、结果怎样一目了然っす。",
    [], [], ["TensorBoard", "MLflow"])

# Save
kb["version"] = "1.5"
kb["lastUpdated"] = "2026-05-28"
with open('term_kb.json', 'w', encoding='utf-8') as f:
    json.dump(kb, f, ensure_ascii=False, indent=2)

from collections import Counter
cats = Counter(t["category"] for t in kb["terms"])
print(f"\n{'='*60}")
print(f"✅ 总计: {len(kb['terms'])} 个术语")
print(f"本次新增: {added} 个")
print(f"{'='*60}")
for cat, count in sorted(cats.items(), key=lambda x:-x[1]):
    print(f"  {cat}: {count}")
