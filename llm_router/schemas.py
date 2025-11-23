from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Backend(str, Enum):
    VLLM = "vllm"
    OLLAMA = "ollama"
    LLAMACPP = "llamacpp"


class Message(BaseModel):
    role: str
    content: str


class ToolSchema(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class InferenceRequest(BaseModel):
    backend: Backend
    model: str
    messages: List[Message]
    tools: Optional[List[ToolSchema]] = None
    temperature: float = 0.2
    max_tokens: int = 512
    response_format: str = "text"
    stream: bool = False


class ToolCall(BaseModel):
    tool: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None


class InferenceResponse(BaseModel):
    backend: Backend
    model: str
    output: str
    tool_calls: List[ToolCall] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    stream_chunks: Optional[List[str]] = None
