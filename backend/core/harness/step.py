# Pipeline 步骤基类与状态容器——吸收 LangGraph 的 State/Node 思想
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


# 步骤间共享的状态容器
@dataclass
class PipelineState:
    input: dict = field(default_factory=dict)
    results: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    extra: dict = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.results.get(key, default)

    def set(self, key: str, value: Any):
        self.results[key] = value

    def add_error(self, error: str):
        self.errors.append(error)

    def has_errors(self) -> bool:
        return len(self.errors) > 0


# PipelineStep 抽象基类，每个诊断阶段对应一个子类
class PipelineStep(ABC):
    def __init__(self, name: str, depends_on: list[str] = None):
        self.name = name
        self.depends_on = depends_on or []

    @abstractmethod
    async def execute(self, state: PipelineState) -> PipelineState:
        ...
