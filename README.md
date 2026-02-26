# Deep Agents 平台（CLI / Server 分离 + SSE）

本项目现在按你要求，优先对接 **LangChain 官方 Deep Agents API**（`create_deep_agent`）。
官方文档：<https://docs.langchain.com/oss/python/deepagents/overview>

调用链路：`前端 -> CLI -> Server(Deep Agent) -> SSE`

## 架构说明

- **server/**：FastAPI 服务端，提供 `POST /v1/chat/stream` SSE
- **cli/**：Typer CLI，负责调用 server 并打印流式结果
- **shared/**：请求模型

## Deep Agents 对接方式（官方 API）

`server/deep_agent.py` 会按顺序尝试加载以下官方/兼容入口：

1. `deepagents.create_deep_agent`
2. `langchain_deepagents.create_deep_agent`
3. `langchain.agents.create_deep_agent`

如果找到 `create_deep_agent`，则会创建 agent 并通过 `agent.ainvoke({"messages": ...})` 执行。
如果环境缺依赖或模型配置错误，会返回明确的回退提示，并附官方文档链接。

## 环境变量

- `LLM_PROVIDER=mock`（默认，使用 FakeListChatModel 方便本地调试）
- `LLM_PROVIDER=openai`（示例）
- `LLM_MODEL=gpt-4o-mini`（示例）

## 快速开始

```bash
python -m pip install -e .
python -m uvicorn server.app:app --host 0.0.0.0 --port 8000
```

另一个终端调用：

```bash
deepagent-cli chat "我需要一个前端->CLI->Server->SSE的 Deep Agents 平台"
```

## SSE 协议

- `event: start`
- `event: token`
- `event: end` (`[DONE]`)
