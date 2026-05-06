# Ravey AI Agent 工程脚手架

> 框架层 + 业务层分离，把 LangGraph 包装成开箱即用的 Agent 工程结构。

---

## 设计抽象

整个系统围绕三个核心概念，互相解耦、独立演进：

| 概念 | 职责 | 关键约束 |
|---|---|---|
| **Brain** | Agent 的推理循环 —— LLM 决策、工具路由、回复生成 | **无状态**：所有上下文都从 Session 重建，崩溃后新实例 `wake()` 即可恢复 |
| **Hand** | 工具执行接口 —— 本地函数 / MCP / 沙箱代码 | 统一签名 `execute(name, input) → string`，Brain 不关心实现 |
| **Session** | append-only 事件日志，独立持久层 | 事件不可变；`(session_id, seq)` 单调递增；支持切片读取 |

这套抽象的好处：
- Brain 是**牲口而非宠物**（cattle, not pet），可以随意重启 / 横向扩展
- Hand 替换不影响 Brain：本地函数升级到 MCP 服务，Brain 代码不动
- Session 是唯一的真相源：事件日志可回放、可审计、可调试

---

## 目录结构

```
project-root/
│
├── packages/agent-framework/                          # 框架包（pip install -e）
│   ├── pyproject.toml                            # name = ravey-ai-agent-framework
│   └── ravey/                                 # PEP 420 命名空间包（无 __init__.py）
│       └── ai/
│           └── agent_framework/                  # 实际代码包
│               ├── __init__.py                   # 顶层导出
│               ├── brain/                        # Brain 推理循环
│               │   ├── base.py                   # wake / step / run
│               │   ├── context_manager.py       # token 估算 + 压缩 prompt
│               │   ├── langgraph_brain.py       # LangGraph StateGraph 集成
│               │   └── orchestrator.py          # 多 Brain 管理
│               ├── hands/                        # 工具执行
│               │   ├── base.py                   # Hand 抽象
│               │   ├── local_hand.py            # 本地函数
│               │   └── mcp_hand.py              # MCP 远程
│               ├── session/                      # 事件日志
│               │   ├── events.py                # Event / EventType
│               │   ├── store.py                 # SessionStore + MySQL 实现
│               │   └── migrations.py            # 建表 SQL
│               └── llm/
│                   └── factory.py               # 多 provider LLM 工厂
│
├── packages/tasks/                                 # 业务应用（任务规划 Agent）
│   ├── pyproject.toml                            # name = ravey-ai-tasks
│   ├── agent_config.yaml                         # 业务唯一需要关心的配置
│   ├── main.py                                   # FastAPI 入口
│   ├── Dockerfile
│   └── ravey/
│       └── ai/
│           └── tasks/                            # ravey.ai.tasks
│               ├── domain.py                     # Task 领域模型
│               ├── tools.py                      # 5 个规划工具（纯函数）
│               └── agent.py                      # build_brain() 装配 Agent
│
├── tests/                                        # 测试（93 个用例 / 98% 覆盖率）
│   ├── test_session_store.py
│   ├── test_hands.py
│   ├── test_brain.py
│   ├── test_brain_extras.py
│   ├── test_mcp_hand_extras.py
│   ├── test_task_tools.py
│   ├── test_task_agent.py
│   └── test_integration.py
│
├── docker-compose.yml
├── pytest.ini
└── README.md
```

包命名约定：
- 框架：`ravey.ai.agent_framework`
- 业务：`ravey.ai.tasks`（任务规划场景）
- 后续新业务：继续放在 `ravey.ai.<domain>` 下，命名空间无需重复声明

---

## 业务示例：任务规划 Agent

输入一段自然语言需求，Agent 自动完成 5 步规划：

```
用户输入                  Brain 调度                       工具产出
─────────                ──────────                      ──────────
"- 用户中心模块"     →   ① parse_requirement      →    [{id, title, ...}]
                     →   ② split_task             →    带 subtasks
                     →   ③ estimate_effort        →    每个叶子有 hours
                     →   ④ schedule_tasks         →    填上 start/due_date
                     →   ⑤ save_task_tree         →    JSON 落盘
```

工具都是纯函数（`ravey/ai/tasks/tools.py`），不依赖 LLM、不依赖数据库，本地就能单元测试。Brain 通过 `LocalHand` 把它们包装成统一接口注入。

---

## 运行逻辑

启动一个完整应用走以下步骤：

```
┌─────────────────────────────────────────────────────┐
│ ① main.py 加载 agent_config.yaml                    │
│    ↓                                                │
│ ② 创建 MySQLSessionStore，setup() 建表（幂等）      │
│    ↓                                                │
│ ③ build_brain(store) 装配 task-planner Brain        │
│    - 注入 5 个 LocalHand                            │
│    - 配置 LLM provider / model                      │
│    ↓                                                │
│ ④ BrainOrchestrator 注册 Brain                      │
│    ↓                                                │
│ ⑤ FastAPI 暴露 4 个路由：                           │
│    POST /session                  创建 Session      │
│    GET  /session/{id}             查 Session 元信息 │
│    GET  /session/{id}/events      查事件日志        │
│    POST /session/{id}/message     发用户消息        │
│    ↓                                                │
│ ⑥ uvicorn 启动 HTTP 服务                            │
└─────────────────────────────────────────────────────┘
```

一次完整对话的事件流：

```
client → POST /session                      → 返回 session_id
client → POST /session/{id}/message         → server 写入 USER_MESSAGE
server → orchestrator.wake_brain()          → Brain 加载 Session 全量事件
server → brain.run()
        loop {
            写入 LLM_REQUEST 事件
            llm.invoke(messages)
            写入 LLM_RESPONSE 事件
            for 每个 tool_call {
                写入 TOOL_CALL 事件
                hand.execute()
                写入 TOOL_RESULT 事件
            }
            如果上下文超阈值 → 写入 COMPACTION 事件
        } 直到 LLM 不再调用工具
        update Session.status = "completed"
        return 最后一条 AI 消息

client ← reply
```

如果中途服务进程崩溃，下次请求只需对同一个 session_id 再发消息，新 Brain 实例从事件日志重建上下文继续工作。

---

## 快速开始

### 1. 启 MySQL（测试用）

```bash
docker run -d --name test-mysql \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=test_sessions \
  -p 3307:3306 \
  mysql:8.0
```

### 2. 装依赖

用 uv workspace 一键装好整个 monorepo（开发模式，源码即时生效）：

```bash
uv sync --extra dev
```

也可以传统方式一个一个装：

```bash
uv venv venv
uv pip install -e packages/agent-framework -e packages/tasks --python venv/bin/python
```

### 3. 跑测试

```bash
venv/bin/python -m pytest tests/ -v
```

带覆盖率：

```bash
venv/bin/python -m pytest tests/ \
  --cov=ravey.ai.tasks \
  --cov=ravey.ai.agent_framework \
  --cov-report=term-missing
```

当前结果：**93 个用例，98% 覆盖率**。

### 4. 起业务服务

```bash
cd packages/tasks
export DASHSCOPE_API_KEY=sk-xxx
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=root
export MYSQL_DATABASE=langgraph_sessions

../venv/bin/python main.py
```

服务起在 `http://localhost:8000`。

### 5. 试一次对话

```bash
# 创建 Session
SID=$(curl -s -X POST http://localhost:8000/session \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"alice"}' | python -c "import sys,json; print(json.load(sys.stdin)['session_id'])")

# 发消息
curl -X POST http://localhost:8000/session/$SID/message \
  -H 'Content-Type: application/json' \
  -d '{"message":"请帮我规划：- 用户中心模块\n- 修复登录 bug\n- 优化首页性能"}'

# 看事件日志
curl http://localhost:8000/session/$SID/events
```

---

## 写一个新业务

新建一个业务包，比如 `ravey.ai.support`（客服场景）：

1. **写工具函数**（`ravey/ai/support/tools.py`）—— 普通 Python 函数，加 docstring
2. **包装成 Hand**（`build_hands()` 返回 `{name: LocalHand(fn)}`）
3. **写 Agent 装配函数**（`build_brain(store) → Brain`），指定 system prompt 和工具集
4. **在 main.py 里注册到 Orchestrator**

无需改框架代码，无需配置注册中心。

---

## 关键模块速查

| 想做的事 | 改哪里 |
|---|---|
| 加业务工具 | `ravey/ai/<domain>/tools.py` 新增函数，注册进 `build_hands()` |
| 改 Agent 行为 | `ravey/ai/<domain>/agent.py` 改 `SYSTEM_PROMPT` |
| 换 LLM | `agent_config.yaml` 的 `llm.providers` |
| 加新 Session 后端 | 实现 `SessionStore` 协议，替换 `MySQLSessionStore` |
| 接 MCP 工具 | `MCPHand("tool_name", "http://mcp_server")` 注入 Brain |
| 加 HTTP 路由 | `packages/tasks/main.py` 的 `create_app()` |

---

## 参考

- Anthropic《Scaling Managed Agents: Decoupling the brain from the hands》
  - Brain 无状态、Session 独立持久、Hand 统一接口的核心思路来源
