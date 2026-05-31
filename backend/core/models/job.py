# Pydantic 模型——岗位创建/查询响应
from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    title: str
    category: str = ""
    requirements: dict = Field(default_factory=dict)
    weight_config: dict = Field(default_factory=dict)
    description: str = ""
    company: str = ""


class JobResponse(BaseModel):
    id: str
    title: str
    category: str
    requirements: dict
    weight_config: dict
    description: str
    company: str

    class Config:
        from_attributes = True
