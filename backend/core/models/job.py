# Pydantic 模型——岗位创建/查询响应
from pydantic import BaseModel, ConfigDict, Field


class JobCreate(BaseModel):
    title: str
    category: str = ""
    requirements: dict = Field(default_factory=dict)
    weight_config: dict = Field(default_factory=dict)
    description: str = ""
    company: str = ""


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    category: str
    requirements: dict
    weight_config: dict
    description: str
    company: str
