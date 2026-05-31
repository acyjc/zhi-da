# LLM 抽象层——统一 LLMClient 接口，支持 OpenAI 实现和测试用 Mock 实现
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator
from config.settings import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


@dataclass
class LLMResponse:
    content: str = ""
    finish_reason: str = "stop"
    usage: dict = field(default_factory=dict)


@dataclass
class LLMChunk:
    content: str = ""
    finish_reason: str = ""


# LLM 客户端抽象基类
class LLMClient(ABC):
    @abstractmethod
    async def complete(self, messages: list[dict], tools: list[dict] = None) -> LLMResponse:
        ...

    @abstractmethod
    async def stream(self, messages: list[dict], tools: list[dict] = None) -> AsyncIterator[LLMChunk]:
        ...


# OpenAI 异步客户端实现
class OpenAIClient(LLMClient):
    def __init__(self):
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

    async def complete(self, messages: list[dict], tools: list[dict] = None) -> LLMResponse:
        kwargs = {"model": LLM_MODEL, "messages": messages, "temperature": 0.3}
        if tools:
            kwargs["tools"] = tools
        response = await self._client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            finish_reason=choice.finish_reason or "stop",
            usage={"prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                   "completion_tokens": response.usage.completion_tokens if response.usage else 0},
        )

    async def stream(self, messages: list[dict], tools: list[dict] = None) -> AsyncIterator[LLMChunk]:
        kwargs = {"model": LLM_MODEL, "messages": messages, "temperature": 0.3, "stream": True}
        if tools:
            kwargs["tools"] = tools
        stream = await self._client.chat.completions.create(**kwargs)
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield LLMChunk(content=delta.content, finish_reason=chunk.choices[0].finish_reason or "")
            elif chunk.choices and chunk.choices[0].finish_reason:
                yield LLMChunk(content="", finish_reason=chunk.choices[0].finish_reason)


# 无 API Key 时的 Mock 实现
class MockLLMClient(LLMClient):
    async def complete(self, messages: list[dict], tools: list[dict] = None) -> LLMResponse:
        import json
        return LLMResponse(
            content=json.dumps({"result": "mock_response", "message": "LLM not configured - using mock"}, ensure_ascii=False),
            usage={"prompt_tokens": 10, "completion_tokens": 10},
        )

    async def stream(self, messages: list[dict], tools: list[dict] = None) -> AsyncIterator[LLMChunk]:
        yield LLMChunk(content='{"result": "mock_stream"}', finish_reason="stop")


# 获取 LLM 客户端实例，优先 OpenAI，无 Key 则降级为 Mock
def get_llm_client() -> LLMClient:
    if LLM_API_KEY:
        try:
            return OpenAIClient()
        except ImportError:
            pass
    return MockLLMClient()
