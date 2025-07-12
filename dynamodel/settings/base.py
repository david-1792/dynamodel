
from pydantic import BaseModel, Field


class BaseSettings(BaseModel):
    type_name: str | None = None

    access_patterns: dict = Field(default_factory=dict)

