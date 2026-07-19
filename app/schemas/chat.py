from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, examples=["Hello, how are you?"])

class ChatResponse(BaseModel):
    response: str
    sources: list[str]