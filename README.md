# AgentFlow

面向企业与开发者的 **AI Agent 工作流平台**。集成知识库 RAG、智能体编排、可视化 Workflow、Graph RAG 与多模型接入，支持 Docker 一键部署。

## 功能特性

- **知识库管理** — 文档上传、分段、向量检索、混合搜索配置
- **RAG 问答** — 检索增强生成，支持 Rerank
- **Graph RAG** — 基于 Neo4j 的知识图谱抽取与查询
- **智能体 (Agent)** — 自定义 Prompt、技能绑定、工具调用、流式对话
- **Workflow** — 可视化节点编排，支持条件分支与 LLM 节点
- **Assistant** — 多轮会话助手，会话记忆与归档
- **Skills** — 可扩展技能/工具注册
- **多模型 Provider** — DashScope / 智谱 / 混元 / 千帆（OpenAI 兼容接口）
- **向量存储** — Milvus 或本地 FAISS

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11 · FastAPI · SQLAlchemy · LangChain / LangGraph |
| 前端 | Vue 3 · Vite · Element Plus |
| 数据库 | MySQL 8 |
| 向量库 | Milvus 2.x / FAISS |
| 图数据库 | Neo4j 5 |
| 缓存 | Redis 7 |

## 项目结构

```
agentflow/
├── api/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/         # REST API
│   │   ├── models/         # ORM 模型
│   │   ├── services/       # 业务逻辑
│   │   └── utils/          # 向量库、Neo4j、文档解析等
│   ├── .env.example        # 环境变量模板
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── web/                    # Vue 3 前端
│   ├── src/
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml      # 一键部署
├── LICENSE
└── SECURITY.md
```

## 快速开始（Docker）

**前置：** Docker · Docker Compose · 至少 8GB 内存（Milvus 栈占用较高）

```bash
# 1. 克隆仓库
git clone <your-repo-url>
cd agentflow

# 2. 配置环境变量
cp api/.env.example api/.env
# 编辑 api/.env，至少填写：
#   SECRET_KEY
#   DASHSCOPE_API_KEY / LLM_API_KEY

# 3. 启动全部服务
docker compose up -d --build

# 4. 访问
# Web UI:  http://localhost
# API:     http://localhost:8000
# API 文档: http://localhost:8000/docs
```

首次启动后，通过注册接口或 API 创建账号：

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-password","email":"admin@example.com","nickname":"Admin"}'
```

### Docker 服务一览

| 服务 | 端口 | 说明 |
|------|------|------|
| web | 80 | Nginx 托管前端，反代 `/api` |
| api | 8000 | FastAPI |
| mysql | 3306 | 业务数据 |
| redis | 6379 | 缓存 |
| neo4j | 7474 / 7687 | 图数据库 |
| milvus | 19530 | 向量库（含 etcd + minio） |

## 本地开发

### 后端

```bash
cd api
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# 编辑 .env，本地开发时 DB/Milvus/Neo4j host 改为 localhost

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

需自行安装并启动 MySQL、Redis、Neo4j、Milvus（或使用 `VECTOR_STORE_TYPE=faiss` 跳过 Milvus）。

### 前端

```bash
cd web
pnpm install   # 或 npm install
pnpm dev       # http://127.0.0.1:5173，已配置 /api 代理到 :8000
```

## 环境变量

完整说明见 [`api/.env.example`](api/.env.example)。核心项：

| 变量 | 说明 |
|------|------|
| `SECRET_KEY` | JWT 签名密钥，生产环境务必更换 |
| `LLM_PROVIDER` | 模型供应商：`dashscope` / `zhipu` / `hunyuan` / `qianfan` |
| `DASHSCOPE_API_KEY` | 阿里百炼 API Key |
| `LLM_MODEL` | 对话模型，如 `qwen-plus` |
| `VECTOR_STORE_TYPE` | `milvus` 或 `faiss`（轻量本地开发推荐 faiss） |
| `DB_*` | MySQL 连接 |
| `NEO4J_*` | Neo4j 连接（Graph RAG 可选） |

## 轻量模式（无 Milvus）

本地调试可跳过 Milvus 全家桶：

```env
VECTOR_STORE_TYPE=faiss
VECTOR_FAISS_INDEX_PATH=./data/faiss_index
```

仅启动 MySQL + API + Web 即可验证大部分功能；Graph RAG 仍需 Neo4j。

## API 概览

| 模块 | 前缀 | 说明 |
|------|------|------|
| 认证 | `/api/v1/auth` | 登录、注册 |
| 知识库 | `/api/v1/knowledge` | CRUD、文档、检索 |
| RAG | `/api/v1/rag` | 问答 |
| 智能体 | `/api/v1/agents` | Agent CRUD、对话 |
| Workflow | `/api/v1/workflows` | 工作流编排与执行 |
| Assistant | `/api/v1/assistant` | 助手会话 |
| Skills | `/api/v1/skills` | 技能管理 |

交互式文档：启动 API 后访问 `/docs`。

## 开源发布 Checklist

- [ ] 确认 `api/.env` 未提交（已在 `.gitignore`）
- [ ] 轮换曾在 git 历史中出现过的 API Key（见 [SECURITY.md](SECURITY.md)）
- [ ] 生产环境修改所有默认密码
- [ ] 选择合适的 [LICENSE](LICENSE)（当前为 MIT）

## 常见问题

**Q: Milvus 启动慢或 API 连不上？**  
Milvus standalone 需 1–2 分钟就绪。可查看 `docker compose logs milvus`，或先用 `faiss` 模式。

**Q: 注册页面不见了？**  
当前前端仅保留登录页，注册请走 `/api/v1/auth/register` 接口。

**Q: `settings.toml` 和 `.env` 哪个优先？**  
以 `.env` 为准；`settings.toml` 为可选补充，详见 `config.py`。

## License

[MIT](LICENSE)
