# Deep Agents 平台（CLI / Server 分离 + SSE）

这是一个最小可运行的智能体平台骨架，满足你描述的调用链路：

`前端 -> CLI -> Server(Deep Agents) -> SSE流式返回`

## 架构说明

- **server/**：智能体服务端（FastAPI）
  - 提供 `/v1/chat/stream` SSE 接口
  - `DeepAgent` 已使用 **LangChain 标准 Runnable 编排** 实现 `PLAN -> ACT -> STREAM`
- **cli/**：命令行客户端（Typer）
  - 接收前端传入参数
  - 调用 server SSE 接口并实时输出 token
- **shared/**：请求模型共享定义（Pydantic）

## LangChain / Deep Agents 标准化实现点

当前 `server/deep_agent.py` 里已经落地：

1. **PLAN 阶段**：先生成 3 步执行计划（可替换成更复杂 planner）。
2. **ACT 阶段**：根据 PLAN 生成最终答复（可扩展工具调用/多代理协作）。
3. **STREAM 阶段**：将结果按 token chunk 推送给 SSE 客户端。

你可以通过环境变量切换：

- `LLM_PROVIDER=mock`（默认，本地可直接跑）
- `LLM_PROVIDER=openai`（示例，需要你本地安装对应 provider 依赖并配置密钥）
- `LLM_MODEL=gpt-4o-mini`（示例）

## 快速开始

```bash
python -m pip install -e .
```

启动服务端：

```bash
python -m uvicorn server.app:app --host 0.0.0.0 --port 8000
```

另一个终端调用 CLI：

```bash
deepagent-cli chat "帮我设计 Deep Agents 平台"
```

前端如果直接传 JSON 给 CLI：

```bash
deepagent-cli request-json '{"message":"hello","session_id":"web-001"}'
```

## SSE 协议（server -> cli）

- `event: start`：开始，`data` 为 session_id
- `event: token`：增量 token
- `event: end`：结束，`data` 为 `[DONE]`
