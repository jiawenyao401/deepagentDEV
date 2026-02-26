from __future__ import annotations

import asyncio
import importlib
import importlib.util
import os
from collections.abc import AsyncIterator
from typing import Any


class DeepAgent:
    """LangChain Deep-Agents-style orchestrator.

    This implementation follows a standardized multi-stage agent flow:
    1) PLAN  : build a concise execution plan
    2) ACT   : generate a final response using the plan
    3) STREAM: return incremental chunks to SSE consumers

    If LangChain is unavailable at runtime, a deterministic local fallback is used.
    """

    async def stream(self, session_id: str, user_input: str) -> AsyncIterator[str]:
        result = await self._run_deep_agent(session_id=session_id, user_input=user_input)
        for token in result.split():
            yield token + " "
            await asyncio.sleep(0.02)

    async def _run_deep_agent(self, session_id: str, user_input: str) -> str:
        chain = self._build_langchain_chain()
        if chain is None:
            return self._fallback_response(session_id=session_id, user_input=user_input)

        inputs = {
            "session_id": session_id,
            "user_input": user_input,
            "platform_goal": "前端调用CLI，CLI调用Server，并通过SSE流式返回",
        }
        output = await chain.ainvoke(inputs)
        return str(output)

    def _build_langchain_chain(self) -> Any | None:
        """Build a LangChain-standardized PLAN->ACT chain when dependencies exist."""
        if importlib.util.find_spec("langchain_core") is None:
            return None

        prompts = importlib.import_module("langchain_core.prompts")
        output_parsers = importlib.import_module("langchain_core.output_parsers")
        runnables = importlib.import_module("langchain_core.runnables")

        ChatPromptTemplate = prompts.ChatPromptTemplate
        StrOutputParser = output_parsers.StrOutputParser
        RunnableLambda = runnables.RunnableLambda

        plan_prompt = ChatPromptTemplate.from_template(
            """
你是 Deep Agents 平台架构师。请基于用户诉求，先输出一个3步执行计划。
要求：
- 每步一句话
- 聚焦架构与调用链
- 用中文输出

会话: {session_id}
平台目标: {platform_goal}
用户输入: {user_input}
            """.strip()
        )

        act_prompt = ChatPromptTemplate.from_template(
            """
你是 Deep Agents 执行智能体。根据 PLAN 给出可执行答复：
- 先给架构结论
- 再给调用流程（前端->CLI->Server->SSE）
- 最后给最小落地建议

会话: {session_id}
用户输入: {user_input}
PLAN:
{plan}
            """.strip()
        )

        parser = StrOutputParser()

        provider = os.getenv("LLM_PROVIDER", "mock")
        if provider == "mock":
            plan_chain = plan_prompt | RunnableLambda(
                lambda x: (
                    "1) CLI 作为前端入口，统一参数与鉴权。\n"
                    "2) Server 运行 Deep Agent 编排并产出增量 token。\n"
                    "3) 通过 SSE 持续回传 token，直到 [DONE]。"
                )
            )
            act_chain = act_prompt | RunnableLambda(
                lambda x: (
                    f"[session={x['session_id']}] 已按 LangChain Deep Agents 标准化流程执行。\n"
                    "架构结论：采用 CLI/Server 解耦，Server 统一智能体编排。\n"
                    "调用流程：前端 -> CLI -> Server -> SSE(token流) -> 前端渲染。\n"
                    f"最小落地建议：保留当前SSE协议并把业务工具注册到Agent工具层。\nPLAN:\n{x['plan']}"
                )
            )
            return (
                {
                    "plan": plan_chain | parser,
                    "session_id": runnables.RunnableLambda(lambda x: x["session_id"]),
                    "user_input": runnables.RunnableLambda(lambda x: x["user_input"]),
                }
                | act_chain
                | parser
            )

        if importlib.util.find_spec("langchain.chat_models") is None:
            return None

        init_chat_model = importlib.import_module("langchain.chat_models").init_chat_model
        model = init_chat_model(model=os.getenv("LLM_MODEL", "gpt-4o-mini"), model_provider=provider)

        plan_chain = plan_prompt | model | parser
        act_chain = act_prompt | model | parser
        return (
            {
                "plan": plan_chain,
                "session_id": RunnableLambda(lambda x: x["session_id"]),
                "user_input": RunnableLambda(lambda x: x["user_input"]),
            }
            | act_chain
        )

    def _fallback_response(self, session_id: str, user_input: str) -> str:
        return (
            f"[session={session_id}] LangChain 依赖未就绪，已使用本地回退路径。"
            "建议安装 langchain 并配置 LLM_PROVIDER/LLM_MODEL。"
            f"你的输入是：{user_input}"
        )
