from pydantic import BaseModel, Field
from typing import Any

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, examples=["Hello, how are you?"])

class ChatResponse(BaseModel):
    response: str | list[str | Any]
    sources: list[str]