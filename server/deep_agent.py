from __future__ import annotations

import asyncio
import importlib
import importlib.util
import os
from collections.abc import AsyncIterator
from typing import Any


class DeepAgent:
    """Deep Agent runtime using LangChain official Deep Agents API when available."""

    async def stream(self, session_id: str, user_input: str) -> AsyncIterator[str]:
        text = await self._run(session_id=session_id, user_input=user_input)
        for token in text.split():
            yield token + " "
            await asyncio.sleep(0.02)

    async def _run(self, session_id: str, user_input: str) -> str:
        create_deep_agent = self._load_official_deep_agent_factory()
        if create_deep_agent is None:
            return self._fallback(
                session_id=session_id,
                user_input=user_input,
                reason="未检测到官方 Deep Agents API（create_deep_agent）",
            )

        model = self._build_model()
        if model is None:
            return self._fallback(
                session_id=session_id,
                user_input=user_input,
                reason="模型初始化失败（检查 LLM_PROVIDER / LLM_MODEL / API Key）",
            )

        system_prompt = (
            "你是一个基于 LangChain Deep Agents 官方标准实现的架构智能体。"
            "请围绕前端->CLI->Server->SSE流程给出可执行方案。"
        )

        try:
            agent = create_deep_agent(
                model=model,
                tools=[],
                system_prompt=system_prompt,
            )

            result = await agent.ainvoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": (
                                f"session_id={session_id}。"
                                "请给出该需求的架构结论、调用流程和最小落地步骤。"
                                f"用户输入：{user_input}"
                            ),
                        }
                    ]
                }
            )
            extracted = self._extract_text(result)
            if extracted:
                return extracted
            return str(result)
        except Exception as exc:  # noqa: BLE001
            return self._fallback(session_id=session_id, user_input=user_input, reason=str(exc))

    def _load_official_deep_agent_factory(self) -> Any | None:
        candidates = [
            ("deepagents", "create_deep_agent"),
            ("langchain_deepagents", "create_deep_agent"),
            ("langchain.agents", "create_deep_agent"),
        ]
        for module_name, func_name in candidates:
            try:
                spec = importlib.util.find_spec(module_name)
            except ModuleNotFoundError:
                spec = None
            if spec is None:
                continue
            module = importlib.import_module(module_name)
            factory = getattr(module, func_name, None)
            if factory is not None:
                return factory
        return None

    def _build_model(self) -> Any | None:
        provider = os.getenv("LLM_PROVIDER", "mock")

        if provider == "mock":
            if importlib.util.find_spec("langchain_core.language_models.fake") is None:
                return None
            FakeListChatModel = importlib.import_module(
                "langchain_core.language_models.fake"
            ).FakeListChatModel
            return FakeListChatModel(
                responses=[
                    "架构结论：使用 CLI/Server 解耦 + Server 统一 Deep Agent 编排。\n"
                    "调用流程：前端 -> CLI -> Server -> SSE token 流 -> 前端渲染。\n"
                    "落地步骤：1) 定义请求协议 2) Server 接 Deep Agent 3) SSE 回传。"
                ]
            )

        try:
            chat_models_spec = importlib.util.find_spec("langchain.chat_models")
        except ModuleNotFoundError:
            chat_models_spec = None
        if chat_models_spec is None:
            return None
        init_chat_model = importlib.import_module("langchain.chat_models").init_chat_model
        return init_chat_model(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            model_provider=provider,
        )

    def _extract_text(self, result: Any) -> str:
        if isinstance(result, str):
            return result
        if isinstance(result, dict):
            messages = result.get("messages")
            if isinstance(messages, list) and messages:
                last = messages[-1]
                content = getattr(last, "content", None)
                if isinstance(content, str):
                    return content
                if isinstance(last, dict) and isinstance(last.get("content"), str):
                    return last["content"]
        return ""

    def _fallback(self, session_id: str, user_input: str, reason: str) -> str:
        return (
            f"[session={session_id}] 当前走回退路径：{reason}。"
            "请按官方文档安装/配置 Deep Agents 后重试："
            "https://docs.langchain.com/oss/python/deepagents/overview 。"
            f"输入：{user_input}"
        )
