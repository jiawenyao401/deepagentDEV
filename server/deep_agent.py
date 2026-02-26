from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator


class DeepAgent:
    """A minimal Deep Agents style wrapper.

    Replace `_generate_text` with real LangChain graph/agent pipeline when integrating
    production model providers.
    """

    async def stream(self, session_id: str, user_input: str) -> AsyncIterator[str]:
        text = await self._generate_text(session_id=session_id, user_input=user_input)
        for token in text.split():
            yield token + " "
            await asyncio.sleep(0.03)

    async def _generate_text(self, session_id: str, user_input: str) -> str:
        provider = os.getenv("LLM_PROVIDER", "mock")
        if provider == "mock":
            return (
                f"[session={session_id}] 已收到请求。"
                "这是一个Deep Agents标准化接口示例，"
                f"你输入的是：{user_input}"
            )

        # TODO: Plug in LangChain Deep Agents flow here.
        return (
            f"[session={session_id}] provider={provider} 尚未实现，"
            f"请接入LangChain工作流。输入：{user_input}"
        )
