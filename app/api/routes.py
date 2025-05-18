from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.models.task import TaskCreate, TaskResponse, TaskStatusResponse
from app.tasks.task_manager import TaskManager, task_manager

router = APIRouter()


async def get_task_manager() -> TaskManager:
    await task_manager.initialize()
    return task_manager


@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    task_create: TaskCreate, tm: TaskManager = Depends(get_task_manager)
) -> TaskResponse:
    """
    Create a new task

    - Returns a task ID immediately
    - Task will be executed asynchronously
    - Results will be sent to the callback URL when the task is completed
    """
    task_id = await tm.create_task(
        name=task_create.name,
        parameters=task_create.parameters,
        callback_url=str(task_create.callback_url),
    )

    return TaskResponse(task_id=task_id)


@router.get("/tasks/{task_id}", response_class=StreamingResponse)
async def stream_task_status(
    task_id: str, tm: TaskManager = Depends(get_task_manager)
) -> StreamingResponse:
    """
    Stream task status updates

    - Returns Server-Sent Events (SSE) with task status updates
    - Updates are sent every 5 seconds
    - Stream ends when the task is completed or failed
    """
    return StreamingResponse(
        tm.stream_task_status(task_id), media_type="text/event-stream"
    )


@router.get("/tasks/{task_id}/state", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str, tm: TaskManager = Depends(get_task_manager)
) -> TaskStatusResponse:
    """
    Get the current status of a task

    - Returns the current status, progress, and message
    - Does not stream updates
    """
    return await tm.get_task_status(task_id)
