# 🗑️ ai-Form: 披着“企业级”外衣的半成品 AI-BI 工作区
## ⚠️ 极其严肃的警告 (WARNING)
别被文档里吹嘘的“Multi-Agent”、“HTAP读写分离”、“CQRS架构”骗了。目前这只是一个用胶水代码、硬编码和 setTimeout 勉强粘合起来的 MVP（最小可行性玩具）。
本系统目前极度脆弱，毫无鲁棒性可言，毫无高并发承载能力。绝对不要将其部署到任何生产环境中，否则你的数据将在大模型的幻觉和前端的幽灵重渲染中灰飞烟灭。

## 🏗️ 所谓“完整”的架构图 (Architecture Illusion)
这是一张画大饼的架构图。图上画得很美，但实际上中间件（Celery/Redis/DuckDB）目前全在“摸鱼”或者根本没接入，真实的流量全靠 FastAPI 单节点同步阻塞硬抗。


```mermaid
graph TD
    subgraph 前端 (React + Vite) - 脆弱的状态缝合怪
        UI[UI 三栏布局]
        FS[FortuneSheet 表格] -->|防抖延迟| API_Save
        Chat[DeepSeek Copilot] -->|同步阻塞调用| API_Chat
        Charts[ECharts 动态渲染]
    end

    subgraph 网关层 (FastAPI) - 随时会被打满的单点
        API_Save[POST /sheet/save/] --> PG[(PostgreSQL)]
        API_Chat[POST /chat/] --> LangGraph
        API_WS[WS /ws/{id}] -.-> |写了但没用的废代码| Redis_PubSub
        API_Upload[POST /upload/] --> MemDB[(玩具级内存知识库)]
    end

    subgraph Agent 层 (LangGraph) - 缓慢的推理黑盒
        LangGraph --> Planner[意图路由: 画图/改表/QA]
        Planner --> SQLAgent[SQL 生成]
        SQLAgent --> Reviewer[AST 拦截与查询]
        Reviewer --> BIRender[ECharts JSON 生成]
    end

    subgraph 数据底座 - 存在单点故障风险
        PG[(PostgreSQL - OLTP)] -.-> |企图同步但还没写| DuckDB[(DuckDB - OLAP)]
        MemDB -.-> |企图用 Qdrant 但目前只是个 List| RAG
    end

    graph TD
    subgraph 前端 (React + Vite) - 脆弱的状态缝合怪
        UI[UI 三栏布局]
        FS[FortuneSheet 表格] -->|防抖延迟| API_Save
        Chat[DeepSeek Copilot] -->|同步阻塞调用| API_Chat
        Charts[ECharts 动态渲染]
    end

    subgraph 网关层 (FastAPI) - 随时会被打满的单点
        API_Save[POST /sheet/save/] --> PG[(PostgreSQL)]
        API_Chat[POST /chat/] --> LangGraph
        API_WS[WS /ws/{id}] -.-> |写了但没用的废代码| Redis_PubSub
        API_Upload[POST /upload/] --> MemDB[(玩具级内存知识库)]
    end

    subgraph Agent 层 (LangGraph) - 缓慢的推理黑盒
        LangGraph --> Planner[意图路由: 画图/改表/QA]
        Planner --> SQLAgent[SQL 生成]
        SQLAgent --> Reviewer[AST 拦截与查询]
        Reviewer --> BIRender[ECharts JSON 生成]
    end

    subgraph 数据底座 - 存在单点故障风险
        PG[(PostgreSQL - OLTP)] -.-> |企图同步但还没写| DuckDB[(DuckDB - OLAP)]
        MemDB -.-> |企图用 Qdrant 但目前只是个 List| RAG
    end
```

## 📂 目录结构树与文件内部剖析 (Directory Structure & Code Debt)
不要被看似规范的 DDD（领域驱动设计）目录骗了。里面充斥着过度耦合的逻辑和待重构的技术债。
```
Plaintext
📦 ai-Form
 ┣ 📂 frontend                 # 前端微服务 (勉强能跑的 React 缝合怪)
 ┃ ┣ 📂 src
 ┃ ┃ ┣ 📂 components
 ┃ ┃ ┃ ┗ 📜 DataCanvas.jsx   # 【雷区】为了驯服 FortuneSheet 的“幽灵保存”，里面塞满了丑陋的 setTimeout、深拷贝和魔改的数据切除逻辑，极易引发内存泄漏。
 ┃ ┃ ┣ 📜 App.jsx            # 【面条代码】一个文件塞进了聊天 UI、图表挂载、状态管理、甚至 AI 操作拦截卡片的业务逻辑，极其臃肿。
 ┃ ┃ ┗ 📜 main.jsx           # React 应用挂载入口。
 ┃ ┣ 📜 package.json         # Node 依赖配置。
 ┃ ┗ ...
 ┣ 📂 backend                  # 后端核心服务 (同步阻塞的重灾区)
 ┃ ┣ 📂 app
 ┃ ┃ ┣ 📂 core               # 核心配置 (勉强做到了环境变量隔离)
 ┃ ┃ ┃ ┗ 📜 config.py        # 全局配置，存放那些绝不能提交的 API Key。
 ┃ ┃ ┣ 📂 agents             # Multi-Agent 编排引擎
 ┃ ┃ ┃ ┣ 📜 reviewer.py      # AST 语法树拦截器，目前只能防君子防不了小人。
 ┃ ┃ ┃ ┣ 📜 workflow.py      # LangGraph 状态机定义。
 ┃ ┃ ┃ ┣ 📜 nodes.py         # 堆砌了大量 System Prompt 的业务节点。
 ┃ ┃ ┃ ┗ 📜 state.py         # LangGraph 运行态上下文定义。
 ┃ ┃ ┣ 📂 models             # ORM 模型定义
 ┃ ┃ ┃ ┗ 📜 schema.py        # 包含 Workspace 和 SheetData (硬核塞入 JSONB 的表结构)。
 ┃ ┃ ┣ 📂 api                # REST API 网关
 ┃ ┃ ┃ ┣ 📂 v1
 ┃ ┃ ┃ ┃ ┣ 📜 websockets.py  # 【摆设】写了个 ConnectionManager 记录用户和收发心跳，但核心业务根本没接上来。
 ┃ ┃ ┃ ┃ ┗ 📜 endpoints.py   # 【交通堵塞点】包含了处理表格同步、大模型对话、文件上传的 API。大模型聊天接口是完全同步阻塞的，并发一上就死机。
 ┃ ┃ ┣ 📂 worker             # 【画饼区】原本计划放 Celery 和 DuckDB 同步逻辑的地方，现在还是空的。
 ┃ ┃ ┣ 📂 services           # 基础服务
 ┃ ┃ ┃ ┗ 📜 document_parser.py # 极度简陋的 PDF 解析器，毫无 Chunking 策略，直接把全量文本塞给大模型。
 ┃ ┃ ┗ 📜 main.py            # FastAPI 启动入口。
 ┣ 📂 deploy                   # 部署文件 (纸上谈兵)
 ┣ 📜 requirements.txt         # 后端依赖清单。
 ┗ 📜 .gitignore               # 唯一能看的文件，防止你把 API Key 和 node_modules 传上去裸奔。
```

📉 客观差距分析 (Gap Analysis / The Harsh Reality)
如果你想接手这个项目，请先了解你要面对的烂摊子：

1. 虚假的“异步通信” (Fake Asynchronous)
号称采用了 Celery + Redis Pub/Sub + WebSocket 的高并发全双工架构。实际上： 右侧 Copilot 聊天调用的是极度原始的 HTTP POST ``。大模型思考 10 秒，前端就得傻等 10 秒，FastAPI 的 worker 进程就被白白挂起 10 秒。

2. 玩具级的 RAG 知识库 (Toy-Level RAG)
所谓的知识库，仅仅是在后端内存里定义了一个全局变量 global_knowledge_base = [] ``。

没有持久化：只要重启服务器，所有上传的 PDF 全部清空。

没有向量化 (Embedding)：没有 Qdrant，没有 Milvus。它仅仅是把 PDF 拍平截取前 3000 字，然后暴力拼接到 Prompt 里发送给 DeepSeek。一旦文件稍微长一点，立刻触发大模型 Token 上限报错。

3. 千疮百孔的 FortuneSheet (Fragile Spreadsheet)
虽然在 DataCanvas.jsx 中利用 delete sheet.celldata 和 setTimeout 强行阻断了由于开源组件自身设计缺陷带来的“白板覆盖死循环” ``，但这种基于定时器的防御机制极其脆弱。网络稍微抖动，依然存在数据被洗白的风险。

4. 纸上谈兵的 HTAP 读写分离 (Vaporware HTAP)
吹嘘了“PostgreSQL 存事务，DuckDB 做极速分析”。目前的现状是：DuckDB 根本没接进来，大模型生成的查询大概率直接砸在无辜的事务数据库上（或者只是基于微小的假数据在做过家家）。

🎯 结论
这是一个典型的“为了证明可行性而牺牲一切工程严谨性”的堆砌产物。如果作为毕业设计或者技术验证原型，它勉强够格；如果想拿去商业化或应对真实的复杂业务，建议直接 rm -rf 从头重构基础设施。

