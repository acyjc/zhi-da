# ToolRegistry — 工具注册中心，管理 LLM 可调用函数的注册与调用
import asyncio
from typing import Callable, Any


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Callable] = {}

    def register(self, name: str, func: Callable):
        self._tools[name] = func

    def get(self, name: str) -> Callable | None:
        return self._tools.get(name)

    def list_definitions(self) -> list[dict]:
        return [
            {"type": "function", "function": {"name": name, "description": func.__doc__ or ""}}
            for name, func in self._tools.items()
        ]

    async def call(self, name: str, **kwargs) -> Any:
        func = self._tools.get(name)
        if not func:
            raise ValueError(f"Tool '{name}' not found")
        result = func(**kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result
