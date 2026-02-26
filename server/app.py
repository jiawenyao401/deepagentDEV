from __future__ import annotations

from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse

from server.deep_agent import DeepAgent
from shared.models import ChatRequest

app = FastAPI(title="Deep Agents Server", version="0.1.0")
agent = DeepAgent()


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/chat/stream")
async def chat_stream(payload: ChatRequest) -> EventSourceResponse:
    async def event_publisher():
        yield {"event": "start", "data": payload.session_id}
        async for chunk in agent.stream(
            session_id=payload.session_id,
            user_input=payload.user_input,
        ):
            yield {"event": "token", "data": chunk}
        yield {"event": "end", "data": "[DONE]"}

    return EventSourceResponse(event_publisher())
