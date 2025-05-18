from enum import Enum
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, HttpUrl, constr

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class TaskCreate(BaseModel):
    name: constr(min_length=1, strip_whitespace=True)
    parameters: Dict[str, Any]
    callback_url: HttpUrl

class TaskResponse(BaseModel):
    task_id: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    progress: float
    message: Optional[str] = None

class TaskResult(BaseModel):
    task_id: str
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    completed_at: Optional[datetime] = None 