# RAG常见框架模式

## Naive RAG (朴素RAG)

### **定义与特征**

Naive RAG 是最原始的 RAG 基线架构，仅包含 **“索引构建 → 向量检索 → LLM 生成”** 三段线性流水线。文档强调其具有 **4个“无”** 特征：

- **无前置优化**：入库前不做清洗、分块优化、重写、摘要。
- **无后置优化**：检索后不做重排（Rerank）、不过滤垃圾片段、不压缩上下文。
- **无校验**：不检查检索内容是否相关，不校验大模型回答是否与原文冲突（不防幻觉）。
- **无反馈闭环**：用户评价和日志不回传，系统无法自我迭代。

> **一句话概括**：文档切块入库 → 用户Query向量检索Top-K → 直接拼接上下文给LLM出答案。

![image-20260701193640247](./RAG常见框架模式.assets/image-20260701193640247.png)

### ==**完整执行流程**==

| 阶段                   | 步骤         | 关键动作                                                     |
| :--------------------- | :----------- | :----------------------------------------------------------- |
| **离线索引**（一次性） | 文档加载     | 读取PDF/Word/Markdown等                                      |
|                        | 固定长度切块 | **固定字符分割**（如chunk_size=1000），**文档指出这是Naive RAG最大短板** |
|                        | 向量化       | Embedding模型（如BGE）将chunk转为稠密向量                    |
|                        | 向量入库     | 存入Chroma/FAISS/Milvus等向量库                              |
| **在线问答**（实时）   | Query向量化  | 同一Embedding模型编码问题                                    |
|                        | 单路向量检索 | 余弦相似度计算，取Top-K（默认3-5条）                         |
|                        | 上下文拼接   | **不做过滤/去重/重排序**，全部塞入Prompt                     |
|                        | LLM生成      | 固定Prompt格式：`{上下文}\n问题：{query}`                    |

### 核心优点：

实现极简单、开发快	低延迟	成本低	易调试	适合窄域静态知识库

### **致命缺陷（面试/项目选型必问）**

- **索引层**：固定切块破坏语义（段落被截断，表格/代码丢失上下文）。
- **检索层**：单一向量检索噪声大；无BM25关键词融合（专有名词匹配差）；无重排序。
- **生成层**：无事实校验，易产生幻觉；无法处理多跳推理；多轮对话能力弱。
- **无反馈闭环**：检索、生成结果不回写优化流程，系统无法自动迭代改进。

### **适用场景**

- ✅ 适合：项目初期MVP验证、小型FAQ、简单内部wiki、基线对比。
- ❌ 不适合：海量企业文档、精确数字/专有名词查询、医疗金融等高可信度生产场景。



## Advanced RAG(高级 RAG ) 

`Advanced RAG`（高级 RAG）在朴素 RAG 的基础上，对检索前（Pre-retrieval）、检索中（Retrieval）、检索后（Post-retrieval）三个阶段进行系统优化。

`核心思想`：“不是检索一次就完事，而是让整个检索链路中的每个环节都尽可能优化”——从“查什么”（查询优化）→ “去哪查”（混合检索）→ “查得准”（重排序）→ “怎么用”（上下文压缩），形成完整的精度提升闭环。

以下是具体内容：

### 检索前优化（Pre-retrieval）

RAG 检索前优化（Pre-retrieval Optimization）的核心目标是：在查询真正进入向量数据库或搜索引擎之前，提升查询质量、缩小检索范围、降低噪声。

#### 六大策略总览

| 策略类别                 | 核心目标                         | 关键技术/方法                                              |
| :----------------------- | :------------------------------- | :--------------------------------------------------------- |
| **查询改写与扩展**       | 让模糊/口语化问题更贴近文档表述  | HyDE、查询扩展（同义词/上下位词）、多视角改写、反事实/澄清 |
| **查询分解**             | 将复杂多跳问题拆为子问题分别检索 | Least-to-Prompting、CoT分解、SubQuestionQueryEngine        |
| **文档分块优化**         | 保证分块语义完整、上下文不丢失   | 语义分块、重叠窗口、父子块（Small-to-Big）、元数据标注     |
| **结构化路由与过滤**     | 缩小检索范围，精准定位           | 意图路由、元数据预过滤、权限过滤                           |
| **查询向量化前文本优化** | 清洗噪声，标准化术语             | 去口语化、术语标准化、实体识别与链接                       |
| **索引层面预优化**       | 离线构建更丰富的索引结构         | 多表示索引（摘要+详细+倒排）、图索引（GraphRAG）           |

#### 文档分块优化（Chunking）

```tex
导入库  SentenceSplitter SemanticSplitterNodeParser 等  看需要导入
	↓
声明切割器对象  splitter = 切割器库(定义参数)
	↓
向量化模型(非必须)  embed_model = 模型库(模型名，api_key 等)
	↓
创建文档对象(可以自己写，也可以导入文档) 
自己写：documents = [Document(text='str')]
加载文档：documents = SimpleDirectoryReader(...)
	↓
分块操作  nodes = splitter.get_nodes_from_documents(documents)
```

#### 查询转换优化（Query Transformation）

`RRF 融合排序`:核心思想是**基于排序的融合**。针对同一个问题，多路检索器各自返回一组带排名（Rank）的文档。RRF 不直接使用原始相似度分数，而是将每一路中的排名转化为一个倒数惩罚分（1/(k+rank)），然后把**同一个文档跨各路获得的惩罚分累加**。最后，系统依据累加总分对文档进行全局重排，截取头部文档作为生成阶段的上下文

- 规则是：**只要你在本组排第 1，就给你 1/60 分；排第 2，给 1/61 分……**（公式 1/(60+rank)）。k = 60 所以k越小对第一名越有利，k越大相对公平
- **关键特性**：它**不看原始分数**，只看“名次”。哪怕文档 A 在第一组得分 0.99，文档 B 得分 0.98，只要它们分列第 1 和第 2，拿到的 RRF 基础分只差毫厘
- RRF 算完总分并排名后，截取总分最高的前 N 篇（比如 Top-5）。这 Top-5 **不是**直接显示给用户看的那段“最终回答”，而是**作为上下文喂给大模型（LLM）**。大模型看完这 5 篇文档后，才会总结生成出你看到的那个“最终答案文本”。

```tex
之前的naive rag 是直接将用户的问题向量化，直接检索知识库，然后匹配后输出答案

====================================  重写查询  ===================================

***************  HyDE 假答案  ***************
用户提出问题Query(这里不向量化)
	↓
交给 LLM 模型生成一个假答案(不私有化，是通用的，但是和真答案比较相似)
	↓
将 (Query + 假答案) 一起向量化 embedding 并建立索引
	↓
通过 假答案 的索引定位知识库内 真答案 的大概位置 (假答案和真答案相似)
	↓
用 Query 在真答案的大概位置找到 真答案
	↓
真答案 经过 LLM 模型处理返回最终回答


***************  自定义重写 Prompt  ***************
用户提出问题Query(这里不向量化)
	↓
交给 LLM 模型改写成 新query(更具体、带检索 友好术语)
	↓
将 (新query) 向量化 embedding 并建立索引
	↓
通过 新query 这个更具体的问题检索出的 答案 更准确
	↓
答案 经过 LLM 模型处理返回最终回答



========================================  查询扩展  ======================================
***************  Step-Back Prompting(退一步查询扩展)  ***************
用户提出问题Query(这里不向量化)
	↓
交给 Step-Back LLM 模型改写成 新query(更宽泛、更宏观)
	↓
将 (Query + 新query) 一起向量化 embedding 并建立索引
	↓
通过 新query 这个更宏观的问题检索出这个问题的 相关背景
	↓
通过 Query 在 相关背景 中检索寻找 答案
	↓
答案 经过 LLM 模型处理返回最终回答


***************  Multi-Query Expansion(多查询扩展)  ***************
用户提出问题Query(这里不向量化)
	↓
交给 Multi-Query LLM 模型生成 q1 q2 q3...qn(多方位，相同意思不同角度)
	↓
将 (Query + q1 + q2 + ... + qn) 一起向量化 embedding 并建立索引
	↓
并行检索 Query q1 q2 ... qn 这些问题(每个问题都会返回答案 可能相同可能不同 返回Top_K)
	↓
通过 (RRF 融合排序) 方法寻找 答案
RRF 融合排序：每个问题返回的答案 相对排名靠前的 比混合排名时返回的更多，更全
	↓
答案 经过 LLM 模型处理返回最终回答

=========================================  子查询  ======================================
用户提出问题Query(这个问题可以拆成多个问题 这里不向量化)
	↓
交给 LLM 模型拆分成 q1 q2 q3...qn(一句话内多个问题，拆开)
	↓
将 (Query + q1 + q2 + ... + qn) 一起向量化 embedding 并建立索引
	↓
(并行/顺序)检索 Query q1 q2 ... qn 这些问题(每个问题都到各自的分支寻找答案 返回Top_K)
	↓
通过 (RRF 融合排序) 方法寻找 答案
RRF 融合排序：每个问题返回的答案 相对排名靠前的，比混合排名时返回的更多，更全
	↓
答案 经过 LLM 模型处理返回最终回答
```

#### 代码实现：

```python
import os
from llama_index.core import (
    VectorStoreIndex, 
    SimpleDirectoryReader, 
    Document,
    StorageContext,
    Settings
)
from llama_index.core.node_parser import (
    SentenceSplitter,
    SemanticSplitterNodeParser,
    HierarchicalNodeParser
)
from llama_index.core.retrievers import VectorIndexRetriever, AutoMergingRetriever
from llama_index.core.query_engine import RetrieverQueryEngine, TransformQueryEngine
from llama_index.core.indices.query.query_transform import HyDEQueryTransform
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.embeddings.dashscope import DashScopeEmbedding
from llama_index.llms.dashscope import DashScope

# ====================== 1. 配置全局设置 ======================
Settings.embed_model = DashScopeEmbedding(
    model_name="text-embedding-v3",
    api_key=os.getenv("DASHSCOPE_API_KEY")
)
Settings.llm = DashScope(
    model_name="qwen3.7-max",  
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    temperature=0.1
)

# ====================== 2. 文档加载 ======================
# 方式一：从字符串创建（等效于文档中的 test_knowledge）
text = """
自然语言处理是人工智能领域的重要方向。它研究如何让计算机理解人类语言。

深度学习在 NLP 中取得了巨大突破。Transformer 架构成为了主流。
大语言模型如 GPT、BERT 等被广泛应用。它们能够完成翻译、摘要、问答等任务。

检索增强生成（RAG）是一种新兴技术。它将外部知识库与大模型结合，减少幻觉问题。
"""
documents = [Document(text=text)]

# 方式二：从目录加载
# documents = SimpleDirectoryReader(input_files="path").load_data()

# ====================== 3. 分块策略选择（三选一） ======================

# 策略 A：基础句子级分块（等效原生 split_text）
# node_parser = SentenceSplitter(
#     chunk_size=300,
#     chunk_overlap=100
# )

# 策略 B：语义分块（更智能的语义边界）
node_parser = SemanticSplitterNodeParser(
    buffer_size=1,                       
    breakpoint_percentile_threshold=95,
    embed_model=Settings.embed_model
)

# 策略 C：分层父子块（Small-to-Big）
# node_parser = HierarchicalNodeParser.from_defaults(
#     chunk_sizes=[512, 128],
#     chunk_overlap=20
# )

nodes = node_parser.get_nodes_from_documents(documents)

# ====================== 4. 构建索引 ======================
index = VectorStoreIndex(nodes)

# ====================== 5. 基础检索器 ======================
base_retriever = VectorIndexRetriever(
    index=index,          # 已构建好的向量索引（包含语义切分后的 nodes）
    similarity_top_k=3    # 每次查询返回相似度最高的 3 个 node
)

# 如果使用分层节点，启用 AutoMergingRetriever
# retriever = AutoMergingRetriever(
#     base_retriever=base_retriever,
#     storage_context=index.storage_context
# )

# ====================== 6. 查询转换（检索前优化） ======================

# 方式一：HyDE 查询转换（推荐，效果通常最好）
hyde_transform = HyDEQueryTransform(
    llm=Settings.llm,         # 用于生成假设性文档的 LLM
    include_original=True     # 🔑 关键参数：同时保留原始查询
)

# 方式二：自定义重写（等效文档中的 rewrite_query）
# from llama_index.core import PromptTemplate
# rewrite_prompt = PromptTemplate("...")
# 需要自定义 Transform 类

# ====================== 7. 组装查询引擎 ======================

# 基础查询引擎
base_query_engine = RetrieverQueryEngine.from_args(
    retriever=base_retriever     # 上边自己设置的基础检索器
)

# 带 HyDE 转换的查询引擎（检索前优化）
hyde_query_engine = TransformQueryEngine(
    query_engine=base_query_engine,
    query_transform=hyde_transform
)

# 子查询分解引擎（处理复杂多条件问题）
tools = [
    QueryEngineTool(
        query_engine=hyde_query_engine,
        metadata=ToolMetadata(
            name="rag_knowledge",
            description="关于RAG、NLP、大模型技术的知识库"
        )
    )
]

sub_question_engine = SubQuestionQueryEngine.from_defaults(
    query_engine_tools=tools,   # 🔑 可用的查询工具列表（每个工具封装了一个独立的 query_engine）
    llm=Settings.llm,           # 负责“问题分解”和“答案综合”的 LLM
    verbose=True                # 打印思考过程：生成了哪些子问题、调用了哪个工具、中间结果是什么
)

# ====================== 8. 查询 ======================
question = "RAG 技术能解决什么问题？"

# 简单问题：用 HyDE 引擎
response = hyde_query_engine.query(question)
print(f"[HyDE] {response}")

# 复杂问题：用子查询分解
complex_question = "RAG和微调有什么区别？各自适用于什么场景？"
response = sub_question_engine.query(complex_question)
print(f"[SubQuestion] {response}")
```

#### 代码解析：

`temperature=0.1`就是告诉模型：“**别自由发挥，给我最稳妥、最准确的答案。**”

理论取值 [0,+∞) ，实际有效取值范围通常为**[0,2.0]**

- **精确任务**（你当前的 RAG/改写场景）：锁定 **0 ~ 0.3**，优先试 0.1。
- **通用对话**：从 **0.7** 起步微调。
- **创意任务**：从 **0.9** 起步，不超过 1.2。
- **永远不要在生产环境使用 >1.5 的值**，除非你有明确的实验目的并已做好输出质量兜底。



`buffer_size = 1`窗口大小  buffer_size 决定「用多宽的窗口去理解一句话」，窗口越窄越盯单句，越宽越看上下文。

```tex
原文：A句 | B句 | C句 | D句

  buffer_size=1 时，大致是：
    向量1 ≈ A
    向量2 ≈ B
    向量3 ≈ C
    ……再算 A-B、B-C、C-D 之间的距离

  buffer_size=2 时，大致是：
    向量1 ≈ A+B
    向量2 ≈ B+C
    向量3 ≈ C+D
    ……相邻窗口有重叠，比较的是「小段文字」而非单句
```



` breakpoint_percentile_threshold=95`按分数对传入文件进行切割

两个句子间的 分数  = 1 - 相似度(相似度越高,分数越低,不切割)分数 >= 95 的地方都切

传入文件可以是文档的一部分，也可以是整个文档(更标准),取决于传入切割器的文件



`nodes = node_parser.get_nodes_from_documents(documents)`

nodes 是一个 List[TextNode] 列表

|             要素             |                             说明                             |
| :--------------------------: | :----------------------------------------------------------: |
|         `documents`          |        你传入的原始文档列表（每个元素是一篇完整文档）        |
|        `node_parser`         | 已配置好 `breakpoint_percentile_threshold=95` 的语义分割器实例 |
| `get_nodes_from_documents()` | 逐篇独立处理：对每篇文档执行完整的“句子拆分 → embedding → P95计算 → 切分”流程 |
|           `nodes`            |           输出的语义块列表，可直接用于向量化和索引           |

从 Documents 到 Nodes 的数据流转(底层数据结构)：

```tex
Document (原始文档)
  ├── doc_id: "doc_001"
  ├── text: "整篇文档内容..."
  └── metadata: {"file": "report.pdf", "page": 1}
        │
        ▼ node_parser.get_nodes_from_documents()
        
TextNode #1 (语义块1)          TextNode #2 (语义块2)
  ├── id_: "node_aaa"            ├── id_: "node_bbb"
  ├── text: "第一段完整论述"      ├── text: "第二段完整论述"
  ├── metadata: {同父文档}       ├── metadata: {同父文档}
  ├── relationships:             ├── relationships:
  │   ├── SOURCE → doc_001       │   ├── SOURCE → doc_001
  │   ├── PREVIOUS → None        │   ├── PREVIOUS → node_aaa
  │   └── NEXT → node_bbb        │   ├── NEXT → node_ccc
  ├── start_char_idx: 0          │   └── ...
  └── end_char_idx: 342          └── ...
```



### 检索中优化（Retrieval）

检索中优化处于 RAG 流程的**第 4 步（检索召回）**，其核心目标是：**提升召回率（Recall）和精确率（Precision）**。

- **召回率**：确保该找到的相关内容“全部捞出来”，不漏。
- **精确率**：确保捞出来的内容“真的有用”，不跑偏。

为了实现这一目标，学习两种互补的核心技术：**混合检索（Hybrid Search）** 和 **多路召回（Multi-channel Retrieval）**。它们共同构成了工业级 RAG 系统“横向扩展数据源、纵向深化单源质量”的标准检索架构。

**实际架构（嵌套关系）**：
多路召回（外层） → 路1（产品文档）内部做混合检索；路2（FAQ库）内部做混合检索... → 最终融合排序。

#### 两大策略总览：

|                 策略类别                 |                           核心目标                           |                       关键技术 / 方法                        |
| :--------------------------------------: | :----------------------------------------------------------: | :----------------------------------------------------------: |
|      **混合检索** （Hybrid Search）      | **纵向深化单源质量**：融合关键词精确匹配与向量语义理解，取长补短。既保证精确术语（如编号、人名）不被遗漏，又确保同义口语表达能被理解，从而兼顾召回率与精确率。 | 1. **双路检索**：稠密向量检索（语义，如DashScope/BGE）+ 稀疏BM25检索（关键词，配合`jieba`中文分词）。 <br />2. **融合排序**：采用**RRF（倒数排名融合）** 算法，将两路排名转化为统一分数（公式：1/(k+rank)1/(*k*+rank)），消除分数量纲差异，使“两路均靠前”的文档排在最前。 |
| **多路召回** （Multi-channel Retrieval） | **横向扩展覆盖面**：解决单一索引或数据源覆盖不全的问题。通过并行检索多个独立的数据源/索引，先将可能相关的文档“全部捞进来”，保证高召回率，防止漏检。 | 1. **多源异构索引**：针对不同数据源（如技术文档库、FAQ库、社区讨论库）分别独立建索引，每路可按需选择向量或BM25算法。 <br />2. **并行检索与融合**：各路独立召回Top-K，再通过**加权融合**（先归一化后加权）、**RRF** 或 **轮询（Round-Robin）** 等方式合并去重，得到最终候选集。 |

#### ==混合检索（Hybrid Search）==

```tex
用户提出问题Query(这里不向量化)
	↓
经过准备工作(清洗，切块，向量化，建立索引,存入向量库)后
	↓
稠密向量检索(embedding语义检索匹配)			稀疏向量检索(BM25/关键词匹配)
							底层是并行执行的
	↓
分别检索出两组排好序的 '相关文档' 经过 RRF 融合排序返回top_k个新的排好序的 '相关文档'
	↓
将(Query + Top-K 片段)拼成 Prompt，送给大模型
	↓
经过 LLM 模型处理返回最终回答
```

这里的代码实现（如 `QueryFusionRetriever`）本质上就是封装了上述**步骤 3、4、5**（双路并行检索 + RRF 融合 + 取 Top-K），对外暴露成一个统一的检索器接口。检索器吐出 Top-K 节点后，再交给 `RetrieverQueryEngine` 去做**步骤 6（LLM 生成）**



#### 多路召回（Multi-channel Retrieval）

```
离线准备：
	↓
加载多个文档(某问题不同方向的)
	↓

```



### 优缺点总结

|               方法               |                             优点                             |                         缺点 / 挑战                          |
| :------------------------------: | :----------------------------------------------------------: | :----------------------------------------------------------: |
| **混合检索** (向量 + BM25 + RRF) | 1. **语义与精确兼顾**：既能理解“登录超时”等同义表达，又能精准命中“错误码 404”等专有名词。 <br />2. **融合算法稳定**：RRF 基于排名融合，完美规避了不同分数体系（如 0~1 与 0~∞）不可比的问题，工业界最稳。 | 1. **存储与计算成本增加**：需同时存储向量索引和倒排索引（BM25），检索时双路计算耗时略增。 <br />2. **中文分词依赖**：BM25 依赖分词器（如 jieba），分词错误会直接影响关键词召回效果。 |
|  **多路召回** (多索引/多数据源)  | 1. **覆盖面极广**：能从不同颗粒度、不同格式（长文本/短文本）的知识库中捞取信息，显著降低漏检。 <br />2. **灵活性高**：每一路可独立选择最优算法（例如 FAQ 用 BM25，长文档用向量），并可独立调优。 | 1. **架构复杂**：维护多个索引的成本高，且需要设计复杂的路由策略（意图识别）。<br />2. **融合难度大**：加权融合时，权重的设定依赖业务经验（如 FAQ 权重给 1.2，社区给 0.8），设置不合理会引入偏差。 <br />3. **延迟增加**：虽然并发执行，但整体耗时取决于最慢的一路检索速度。 |
|         **两者结合使用**         | **鲁棒性极强**：既补全了单一算法的语义盲区，又补全了单一数据源的空间盲区，是目前企业级 RAG 召回层的“黄金标准”。 | **系统复杂度指数级上升**：调试难度大（需排查具体是哪一路、哪个算法出的问题），且对硬件资源（内存/显存/CPU）要求较高。 |







### 其他优化方法：

#### Self-RAG

```tex
用户提问 → [Retrieve] 需要检索？  → 否 不检索直接基于模型参数生成答案
→ 是 → 向量检索 → [ISREL] 资料相关？→ 否 检索出的知识块与用户问题不相关
→ 是 → 生成回答 → [ISSUP] 有原文支撑？→ 否 没有原文支撑，修改或重写当前句
→ 是 → [ISUSE] 打分当前句是否能解决问题 → 输出
```

![image-20260706113531590](./RAG常见框架模式.assets/image-20260706113531590.png)

**关键机制**：Self-RAG 在训练时引入了**反思标记（Reflection Tokens）**，让模型学会输出以下判断：

|     标记     |    全称    |     执行时机     |                       作用                        |
| :----------: | :--------: | :--------------: | :-----------------------------------------------: |
| **Retrieve** |  检索决策  |      生成前      |        判断问题是否需要查知识库（YES/NO）         |
|  **ISREL**   | 相关性校验 |  检索后，生成前  | 判断检索资料是否与问题相关（RELEVANT/IRRELEVANT） |
|  **ISSUP**   | 支持度校验 | 生成中（每句后） |   检查回答是否有原文依据（FULLY/PARTIALLY/NO）    |
|  **ISUSE**   | 有用性评估 |      生成后      |       评估最终回答对用户的有用程度（1~5分）       |

#### Corrective RAG (CRAG)

```tex
【阶段1】用户提问 → 本地知识库检索，拿回文档
【阶段2】质检员逐篇判断文档质量 → 分三类处理
         ✅ 合格：精简保留
         ⚠️ 模糊：改写查询 + 联网搜索补充
         ❌ 无效：直接丢弃
【阶段3】只拿高质量内容生成回答
```

![image-20260706114257229](./RAG常见框架模式.assets/image-20260706114257229.png)

**四大核心组件**

| 组件           | 功能                 | 简化实操          |
| :------------- | :------------------- | :---------------- |
| **检索评估器** | 判断文档好不好用     | 二选一（yes/no）  |
| **知识精炼**   | 删除文档中无关句子   | 分解→重组         |
| **知识搜索**   | 联网搜索补充         | Tavily/Google API |
| **答案生成器** | 合并内外知识生成回答 | 本地+外部混合     |



#### 对比`Self-RAG`和`CRAG`

|   对比维度   |                     Self-RAG (自反思RAG)                     |                       CRAG (纠正性RAG)                       |
| :----------: | :----------------------------------------------------------: | :----------------------------------------------------------: |
| **核心思想** | **自我反思 (Self-Reflection)**：模型在生成过程中通过特殊令牌不断评价自己的行为和输出。 | **纠正检索 (Corrective Retrieval)**：在生成前，对检索结果进行评估和修正。 |
| **工作重心** | **优化生成过程**：何时检索、生成的依据是否充分、答案是否有用。 |   **优化检索结果**：检索到的文档质量是高是低，该如何处理。   |
| **核心机制** | 生成 **“反思令牌” (Reflection Tokens)**，如`ISREL`(相关性)、`ISSUP`(证据支持度)。 | 使用**轻量级检索评估器**，将检索结果分为三类：**正确、错误、模糊**。 |
| **处理方式** | 根据反思结果，动态决策是**继续生成、重新检索还是修正回答**。 | 根据评估结果采取行动：**精炼**（正确）、**网络搜索**（错误）、**两者结合**（模糊）。 |
| **主要优势** |       **提高生成质量**，使模型的思考过程更透明、可控。       | **增强系统鲁棒性**，有效应对检索失败，减少因错误检索导致的幻觉。 |
| **核心代价** |     计算开销大，**推理速度慢**，需要对模型进行特定训练。     |  引入额外的评估和可能的网络搜索，**增加系统延迟和复杂性**。  |

| 技术           | 新增函数                       | 在流程中的位置            | 作用                   |
| :------------- | :----------------------------- | :------------------------ | :--------------------- |
| **Self-RAG**   | `_need_retrieve`               | **生成前（检索触发前）**  | 决定要不要查库         |
|                | `_is_relevant`                 | **检索后，生成前**        | 过滤不相关资料         |
|                | `_is_supported`                | **生成中（每句后）**      | 检查是否有原文依据     |
|                | `_usefulness`                  | **生成后**                | 评估答案有用性（日志） |
|                | `_correct`                     | **生成中（ISSUP不足时）** | 强制重写消除幻觉       |
| **CRAG离线版** | `_is_relevant`                 | **检索后，生成前**        | 逐篇判断文档质量       |
|                | `_filter_relevant`             | **检索后，生成前**        | 批量过滤无关文档       |
|                | 重写逻辑（在`custom_query`中） | **全部不相关时**          | 改写查询重试           |
| **CRAG联网版** | `transform_query`              | **评估后，生成前**        | 有`no`则联网搜索       |
