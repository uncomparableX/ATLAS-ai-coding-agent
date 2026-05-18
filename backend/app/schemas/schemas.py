from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None


class UserRead(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RepoConnectRequest(BaseModel):
    github_url: str
    branch: Optional[str] = "main"


class RepoRead(BaseModel):
    id: str
    name: str
    full_name: Optional[str]
    github_url: Optional[str]
    status: str
    language: Optional[str]
    description: Optional[str]
    architecture_summary: Optional[str]
    file_count: int
    indexed_chunks: int
    size_mb: float
    last_indexed_at: Optional[datetime]
    created_at: datetime
    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    repository_id: str
    title: str = Field(max_length=500)
    description: str


class TaskRead(BaseModel):
    id: str
    repository_id: str
    title: str
    description: str
    status: str
    plan: Optional[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    retry_count: int
    total_tokens: int
    estimated_cost_usd: float
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    repository_id: str
    message: str
    task_id: Optional[str] = None
    use_rag: bool = True


class ChatMessageRead(BaseModel):
    id: str
    role: str
    content: str
    tokens: int
    created_at: datetime
    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    message: ChatMessageRead
    sources: List[Dict[str, Any]] = []
    total_tokens: int


class AgentRunRead(BaseModel):
    id: str
    task_id: str
    agent_type: str
    iteration: int
    thoughts: Optional[str]
    actions: Optional[List[Any]]
    tokens_used: int
    duration_ms: int
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}


class ExecutionRead(BaseModel):
    id: str
    task_id: str
    command: str
    status: str
    exit_code: Optional[int]
    stdout: Optional[str]
    stderr: Optional[str]
    duration_ms: int
    created_at: datetime
    completed_at: Optional[datetime]
    model_config = {"from_attributes": True}


class FileDiffRead(BaseModel):
    id: str
    task_id: str
    file_path: str
    original_content: Optional[str]
    modified_content: Optional[str]
    diff_unified: Optional[str]
    patch_applied: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class MemoryRead(BaseModel):
    id: str
    memory_type: str
    content: str
    importance: float
    access_count: int
    created_at: datetime
    model_config = {"from_attributes": True}


class WSEvent(BaseModel):
    type: str
    task_id: Optional[str] = None
    agent_type: Optional[str] = None
    data: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)
