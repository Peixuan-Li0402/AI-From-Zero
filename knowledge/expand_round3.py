import json
with open('term_kb.json', encoding='utf-8') as f:
    kb = json.load(f)
existing = {t["term"] for t in kb["terms"]}
added = 0

def a(t,f,c,d,al,ex,no,pr,pa,rl):
    global added
    if t in existing: return
    for tt in kb["terms"]:
        if t.lower() in [x.lower() for x in tt.get("aliases",[])]: return
    existing.add(t); added+=1
    kb["terms"].append({"term":t,"fullName":f,"category":c,"difficulty":d,"aliases":al,
        "explanation":ex,"hoshinoNote":no,"prerequisiteTerms":pr,"landmarkPapers":pa,"relatedTerms":rl})

# === ML Theory ===
a("偏差-方差权衡","偏差-方差权衡","数学基础",2,["Bias-Variance Tradeoff"],
 "模型误差三来源：偏差（欠拟合）+方差（过拟合）+噪声。太简单→高偏差低方差；太复杂→低偏差高方差。要找到平衡点。",
 "太简单的模型学不到真话（高偏差），太复杂的模型记住了所有噪音（高方差）っす。找平衡。",[],[],[
 "过拟合","欠拟合","泛化"])
a("维度灾难","维度灾难","数学基础",2,["Curse of Dimensionality"],
 "高维空间中数据变得极其稀疏的现象。样本数必须随维度指数增长才能保持密度。KNN、K-means等依赖距离的方法在高维失效。",
 "维度越高→数据越稀疏→点与点之间都一样远っす。大叔在1000维空间里找邻居等于在沙漠里找人。",[],[],[
 "降维","PCA","t-SNE"])
a("流形假设","流形假设","数学基础",2,["Manifold Hypothesis"],
 "高维数据实际上集中在一个低维流形上。自然图像虽在10万像素空间≈100万维，但本质只有几十维。深度学习的理论基础之一。",
 "看起来100万维的数据，本质只活在低维流形上っす。大叔的日常看起来很复杂但规律就几条。",[],[],[
 "降维","表示学习"])
a("无免费午餐定理","无免费午餐定理","数学基础",2,["No Free Lunch Theorem"],
 "不存在一种算法在所有问题上都比其他算法好。A算法在某些问题好→必在其他问题差。所以需要根据具体问题选模型/算法。",
 "没有万能药っす。没有一种模型在所有问题上都最好。大叔也悟了：没有完美的工具只有合适的工具。",[],[],[
 "泛化","集成学习"])
a("大数定律","大数定律","数学基础",1,["Law of Large Numbers"],
 "样本量越大→样本均值越接近总体均值。硬币抛10次可能6正4负，10000次接近5000正5000负。蒙特卡洛方法的基础。",
 "试得越多越接近真相っす。硬币抛10次可能不太准，抛10000次基本就五五分了。",[],[],[
 "蒙特卡洛方法","中心极限定理"])
a("中心极限定理","中心极限定理","数学基础",2,["Central Limit Theorem"],
 "无论原始分布是什么，大量独立同分布随机变量的均值近似服从正态分布。统计推断的基石。p值、置信区间都靠它。",
 "不管原始数据长啥样，取平均够多次→结果接近正态分布っす。统计学的定心丸。",[],[],[
 "正态分布","概率论"])
a("EM算法","期望最大化算法","数学基础",3,["Expectation-Maximization"],
 "含隐变量参数估计的迭代算法。E步：估计隐变量后验；M步：最大化似然。K-means可以看作EM的特例。",
 "先猜隐变量→根据猜的估计参数→用参数改进隐变量猜测→循环っす。先蒙再调再蒙。",[],[],[
 "K-means","最大似然估计"])

# === More Pre-trained Models ===
a("RoBERTa","RoBERTa","预训练模型",2,[],
 "BERT改进版。Meta团队发现BERT训练不足：更大的batch、更多数据、动态掩码、去掉NSP任务。效果显著提升。",
 "BERT的完整版っす。BERT原来没训练充分——RoBERTa多训了好久效果就好了很多。",["BERT"],[
 {"title":"RoBERTa: A Robustly Optimized BERT Pretraining Approach","authors":"Liu et al.","year":2019}],
 ["BERT","ALBERT"])
a("ALBERT","ALBERT","预训练模型",3,[],
 "BERT轻量版。参数共享（所有层共享参数）+因式分解嵌入（词嵌入大≠隐藏层大）。参数量大幅减少但效果相近。",
 "BERT的省内存版っす。参数共享让模型变小不少但效果差不太多。",["BERT"],[],[ "BERT","RoBERTa"])
a("DistilBERT","DistilBERT","预训练模型",2,[],
 "BERT蒸馏版。用知识蒸馏将BERT压缩40%但保留97%性能。速度提升60%。",
 "BERT的压缩版っす。用老师-学生蒸馏，小了40%但效果几乎没掉。",["BERT","知识蒸馏"],[],[ "BERT","知识蒸馏"])
a("GPT-4","GPT-4","预训练模型",3,[],
 "OpenAI的多模态大模型（2023）。能处理图像和文本。在多领域达到人类水平。训练细节未公开但推测是MoE架构。目前（2024/2025）已被GPT-4o和o1系列更新。",
 "ChaptGPT之前用的那个最强模型っす。能看图能写代码能推理。参数细节没公开，据说MoE架构。",["LLM","多模态"],[],[ "GPT","GPT-3","多模态"])
a("GPT-4o","GPT-4o","预训练模型",3,["GPT-4 Omni"],
 "OpenAI的全模态模型（2024）。支持文本、图像、音频实时交互。推理速度大幅提升、延迟降至语音对话水平。o中的'o'代表'Omni'（全）。",
 "GPT-4的全面升级版っす。能看能听能说，实时对话几乎无延迟。大叔说了上句它直接接下句。",["GPT-4","多模态"],[],[ "GPT-4","多模态"])
a("Claude","Claude","预训练模型",3,[],
 "Anthropic公司开发的LLM系列。主打安全和有用（Constitutional AI）。Claude 3.5 Sonnet在编程和推理上表现优秀。",
 "Anthropic的安全大模型っす。编程和推理很强。大叔觉得它是GPT-4的最强竞品。",["LLM","对齐"],[],[ "LLM","GPT-4"])

# === More Architecture ===
a("Inception","Inception网络","计算机视觉",3,["GoogLeNet"],
 "Google的CNN架构。核心：Inception模块——在同一层用不同大小卷积核（1x1、3x3、5x5）并行提取特征后拼接。2014年ImageNet冠军。",
 "同一层用不同大小的放大镜同时看っす。3x3看局部、5x5看稍大范围——全都看然后综合。",["CNN"],[
 {"title":"Going Deeper with Convolutions","authors":"Szegedy et al.","year":2014}],
 ["CNN","ResNet"])
a("ConvNeXt","ConvNeXt","计算机视觉",2,[],
 "纯CNN架构。借鉴Transformer的设计理念（分组卷积→深度可分离、GELU激活、LayerNorm）重新设计CNN。证明纯CNN在视觉任务上仍能与ViT竞争。",
 "用Transformer的设计哲学重新做CNNっす。证明CNN还没过时。",["CNN"],[],[ "CNN","ViT"])
a("MLP-Mixer","MLP-Mixer","计算机视觉",4,[],
 "完全不用自注意力的视觉架构。在图像patch间和通道间交替使用MLP（而非注意力）。在ImageNet上表现媲美ViT。证明注意力不是唯一答案。",
 "不用注意力也能搞视觉っす。用纯MLP在patch之间混合信息。证明了注意力不是必须的。",["MLP","ViT"],[{"title":"MLP-Mixer: An all-MLP Architecture for Vision","authors":"Tolstikhin et al.","year":2021}],["ViT","MLP"])

# === More RL ===
a("模型基强化学习","模型基RL","训练范式",3,["Model-based RL"],
 "先学习环境模型（预测状态转移+奖励），再在模型内做规划或策略优化。样本效率高但模型偏差可能影响策略。",
 "先学规则再玩っす。大叔先学会游戏规则→然后想赢的策略。比纯试错效率高但规则可能学错。",["强化学习"],[],[ "强化学习","无模型RL"])
a("无模型强化学习","无模型RL","训练范式",2,["Model-free RL"],
 "不显式建模环境，直接从交互经验中学习策略或值函数。Q-Learning、PPO都是无模型的。样本效率较低但适用范围广。",
 "不学规则直接试っす。大叔直接开打游戏→赢了记住、输了也记住。简单粗暴但通用。",["强化学习"],[],[ "强化学习","模型基RL"])
a("好奇心驱动探索","好奇心驱动探索","训练范式",3,["Curiosity-driven Exploration"],
 "RL中的内在奖励机制。当智能体到达模型预测不准的状态时给予额外奖励（好奇心）。鼓励探索未知区域。",
 "给AI加个「好奇心」っす。去没去过的地方→有额外奖励→鼓励探索。大叔觉得这很必要。",["强化学习"],[],[ "强化学习","探索-利用权衡"])

# === Safety ===
a("红队测试","红队测试","当前热点",2,["Red Teaming"],
 "对抗性测试AI安全的方法。专门找人尝试诱导模型输出有害内容，发现安全漏洞后加固。LLM发布前的标准流程。",
 "找人专门想办法让AI「学坏」っす。发现漏洞→修补漏洞。大叔的咖啡店也这样——找朋友找茬。",["对齐","越狱"],[],[ "越狱","提示注入","对齐"])
a("宪法AI","宪法AI","当前热点",3,["Constitutional AI"],
 "Anthropic提出的AI对齐方法。用一组「宪法原则」（如「不要伤害他人」）通过AI自我批评和修订来实现安全训练，减少对人类标注依赖。",
 "给AI定一套「家规」，让AI自己监督自己っす。不靠人打分，靠规则自省。Anthropic搞的。",["RLHF","对齐"],[{"title":"Constitutional AI: Harmlessness from AI Feedback","authors":"Bai et al.","year":2022}],["RLHF","对齐","红队测试"])

# === Generative v2 ===
add_item = a  # alias for speed
# === Prompt Techniques ===
a("系统提示","系统提示","当前热点",1,["System Prompt","System Message"],
 "LLM对话中的初始指令设定。定义模型的角色、语气、约束、知识边界。相比于用户输入的提示，系统提示的优先级更高。",
 "就是给AI「定人设」っす。大叔每次跟AI聊之前先设好：「你是大叔，慵懒，用っす结尾」。",["LLM","Prompt Engineering"],[],[ "Prompt Engineering","LLM"])
a("少样本提示","少样本提示","核心概念",1,["Few-Shot Prompting"],
 "在提示中给模型提供几个输入-输出示例，让模型学会任务模式。GPT-3展示的核心能力。不用更新参数就能学会新任务。",
 "给2-3个例子看看っす。大叔教后辈——「像这样做」→理解了。不用重新训练。",["In-Context Learning"],[],[ "In-Context Learning","零样本学习"])
a("思维树","思维树提示","当前热点",3,["Tree of Thoughts","ToT"],
 "CoT的扩展。不只一条思考链，而是同时探索多条可能的推理路径，在分歧点分支、评估、剪枝。类似下棋时的多步前瞻。",
 "不只一条路想到底っす。岔路口多试几条路，评估哪条最有希望再往前走。下棋时想多步。",["CoT"],[{"title":"Tree of Thoughts: Deliberate Problem Solving with Large Language Models","authors":"Yao et al.","year":2023}],["CoT","思维链","LLM推理"])
a("ReAct","ReAct推理","当前热点",3,[],
 "让LLM边推理边行动的框架。推理→行动→观察→再推理。Agent的核心范式。让LLM不只是「想」而是「想+做」。",
 "想一步→做一步→看看结果→再想再做的循环っす。Agent的基础操作模式。",["Agent","CoT"],[{"title":"ReAct: Synergizing Reasoning and Acting in Language Models","authors":"Yao et al.","year":2022}],["Agent","CoT"])

# === Ensemble ===
a("集成学习","集成学习","训练范式",1,["Ensemble Learning"],
 "组合多个模型提升整体性能的方法。三大流派：Bagging（并行训练取平均）、Boosting（串行纠正前一个模型的错误）、Stacking（用元模型组合各模型输出）。",
 "三个臭皮匠顶个诸葛亮っす。一个模型会犯错，十个模型投票——很少全错。",[],[],[ "随机森林","XGBoost","Bagging"])
a("Bagging","Bagging","训练范式",2,["Bootstrap Aggregating"],
 "并行集成方法。用自助采样（有放回抽样）生成多个子训练集→独立训练多模型→投票/平均。随机森林用的就是Bagging。",
 "每个模型学不同的数据集→各自独立训练→最后投票っす。多样化产生力量。",["集成学习"],[],[ "随机森林","Boosting"])
a("Boosting","Boosting","训练范式",2,[],
 "串行集成方法。逐个添加弱学习器，每个新学习器专注于前一个出错的样本。AdaBoost、XGBoost、LightGBM都是Boosting。",
 "先简单学一下→错了的重点学→还错的重点再学っす。越学越准。",["集成学习"],[],[ "XGBoost","AdaBoost","集成学习"])

# === MISC ===
a("ImageNet","ImageNet","计算机视觉",1,[],
 "大规模图像数据集。1000类、1400万图像。每年ImageNet竞赛推动CNN/深度学习技术突破。AlexNet 2012夺冠开启了深度学习时代。",
 "视觉界的「高考」っす。每年比一次谁分类更准。AlexNet 2012拿了第一→深度学习时代开始了。",[],[],[ "图像分类","AlexNet"])
a("COCO","COCO数据集","计算机视觉",1,["Common Objects in Context"],
 "微软的视觉数据集。33万张、80个类别、含目标检测/分割/关键点标注。目标检测和分割的标准评测基准。mAP是标准指标。",
 "目标检测界的标准考题っす。33万张图、80类物体、带框带轮廓。都说自己在COCO上刷到SOTA。",[],[],[ "mAP","目标检测"])
a("GLUE","GLUE基准","评估指标",2,["General Language Understanding Evaluation"],
 "NLP综合基准。含9个任务（情感分析、语义相似度、语法判断等）。BERT首次在这8个任务都达到SOTA。SuperGLUE是更难版本。",
 "NLP界的综合考试っす。9科考试（情感分析/语义相似度/语法等）。BERT在这里一战成名。",[],[],[ "BERT","RoBERTa"])
a("GPU显存","GPU显存","工程实践",1,["VRAM","显存"],
 "GPU上用于存储数据（模型参数、中间激活、梯度、优化器状态）的高速内存。决定了你能跑多大的模型。FP16下7B参数模型+优化器状态约28GB。",
 "GPU的内存っす。决定了你家能跑多大的模型。大叔经常听到「显存不够了」——经典问题。",[],[],[ "GPU","混合精度训练","量化"])
a("梯度检查点","梯度检查点","训练技巧",2,["Gradient Checkpointing"],
 "用时间换显存的技術。训练时不保存所有中间激活值（太占显存），反向传播时重新计算需要的。显存减少50%以上但训练时间增加15-30%。",
 "不存中间结果→显存省了但算的时候要重新算一遍っす。大叔觉得这是很机智的取舍。",["显存优化"],[],[ "混合精度训练","显存"])
a("流水线并行","流水线并行","训练技巧",3,["Pipeline Parallelism"],
 "将模型的不同层放在不同GPU上，数据依次流过各GPU。解决单GPU放不下整个模型的问题。GPipe、Megatron-LM使用。",
 "把一个大模型切成几段放不同显卡っす。第一段在GPU0→算完传GPU1→GPU2…像流水线生产。",["分布式训练"],[],[ "分布式训练","FSDP","DeepSpeed"])
a("张量并行","张量并行","训练技巧",3,["Tensor Parallelism"],
 "将单个矩阵运算拆分到多个GPU上并行计算。将一个大矩阵乘法切成块分到不同GPU上分别算再组合。Megatron-LM的关键技术。",
 "一个大矩阵算不动→切成小份分给多个显卡一起算っす。大叔搬家也这思路——大家各搬一点。",["分布式训练"],[],[ "分布式训练","流水线并行"])

# === Audio/ASR ===
a("wav2vec","wav2vec","预训练模型",3,[],
 "Meta的自监督语音表示学习。用对比学习框架：从原始音频中学习通用语音表示。在少量标注数据上微调就能达到好的ASR效果。",
 "从音频里自学语音特征っす。不需要人标，自己听大量录音就学会了「哪些声音相似」。",["自监督学习"],[{"title":"wav2vec: Unsupervised Pre-training for Speech Recognition","authors":"Schneider et al.","year":2019}],["ASR","HuBERT"])
a("Fbank","Fbank特征","核心概念",1,["Filter Banks","滤波器组"],
 "音频处理的基础特征。对音频做短时傅里叶变换→功率谱→通过梅尔滤波器组→取对数。比MFCC少一步（不做DCT）。神经网络时代更常用。",
 "MFCC去掉了离散余弦变换就是Fbankっす。神经网络时代反而更喜欢保留更多信息的Fbank。",["语音","MFCC"],[],[ "MFCC","梅尔频谱"])

# === More Optimization ===
a("余弦退火","余弦退火","训练技巧",2,["Cosine Annealing"],
 "学习率调度策略。学习率按余弦函数从初始值逐渐减小到0。后半段训练让模型在局部极值附近精细搜索。常配合Warm-up使用。",
 "学习率像余弦曲线一样慢慢降低っす。大头步大步走→快到了小碎步走。",["学习率","Warm-up"],[],[ "学习率","Warm-up"])
a("循环学习率","循环学习率","训练技巧",2,["Cyclical LR"],
 "学习率周期性上下波动。跳出局部极小值——学习率大时跳出山谷，小时在谷底搜索。有时比单调衰减效果好。",
 "学习率忽大忽小っす。大了走出死胡同，小了仔细看路。大叔觉得这策略挺聪明。",["学习率"],[],[ "学习率","余弦退火"])
a("超参数调优","超参数调优","工程实践",1,["Hyperparameter Tuning"],
 "寻找模型最佳超参数（学习率、层数、batch size等）的过程。方法：网格搜索（穷举）、随机搜索、贝叶斯优化（效率最高）。",
 "调模型的各种旋钮っす。学习率调多大？层数几层？batch size多大？都试一遍很难，所以用贝叶斯优化。",[],[],[ "贝叶斯优化","网格搜索"])

# Save
kb["version"] = "2.0"
kb["lastUpdated"] = "2026-05-28"
with open('term_kb.json','w',encoding='utf-8') as f:
    json.dump(kb,f,ensure_ascii=False,indent=2)
from collections import Counter
cats = Counter(t["category"] for t in kb["terms"])
print(f"Total: {len(kb['terms'])} terms, added: {added}")
for c,n in sorted(cats.items(),key=lambda x:-x[1]):
    print(f"  {c}: {n}")
