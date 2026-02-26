# Deep Agents 平台（CLI / Server 分离 + SSE）

这是一个最小可运行的智能体平台骨架，满足你描述的调用链路：

`前端 -> CLI -> Server(Deep Agents) -> SSE流式返回`

## 架构说明

- **server/**：智能体服务端（FastAPI）
  - 提供 `/v1/chat/stream` SSE 接口
  - 封装 `DeepAgent`，便于后续接入 LangChain Deep Agents 工作流
- **cli/**：命令行客户端（Typer）
  - 接收前端传入参数
  - 调用 server SSE 接口并实时输出 token
- **shared/**：请求模型共享定义（Pydantic）

## 快速开始

> Windows / macOS / Linux 通用，先安装 editable 包。

```bash
python -m pip install -e .
```

启动服务端：

```bash
python -m uvicorn server.app:app --host 0.0.0.0 --port 8000
```

另一个终端调用 CLI（两种方式都可以）：

```bash
deepagent-cli chat "请介绍一下这个平台"
# 或
python -m cli.main chat "请介绍一下这个平台"
```

如果前端要把 JSON 串直接传给 CLI：

```bash
deepagent-cli request-json '{"message":"hello","session_id":"web-001"}'
```

## SSE 协议（server -> cli）

- `event: start`：开始，`data` 为 session_id
- `event: token`：增量 token
- `event: end`：结束，`data` 为 `[DONE]`

## 生产化改造建议

1. 在 `server/deep_agent.py` 中将 `_generate_text` 替换为 LangChain Deep Agents 编排。
2. 增加会话存储（Redis/Postgres）和可观测性（LangSmith/OTel）。
3. CLI 侧增加鉴权与重试策略，配合前端做超时/取消。
