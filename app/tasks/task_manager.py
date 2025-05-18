import asyncio
import json
import uuid
import logging
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Optional

import redis.asyncio as redis
from fastapi import HTTPException

from app.core.config import settings
from app.models.task import TaskResult, TaskStatus, TaskStatusResponse
from app.tasks.celery_tasks import execute_task

logger = logging.getLogger(__name__)

class TaskManager:
    _instance: Optional["TaskManager"] = None
    _redis: Optional[redis.Redis] = None
    _tasks: Dict[str, Dict[str, Any]] = {}
    _max_retries = 5
    _retry_delay = 2

    def __new__(cls) -> "TaskManager":
        if cls._instance is None:
            cls._instance = super(TaskManager, cls).__new__(cls)
        return cls._instance

    async def initialize(self) -> None:
        if self._redis is None:
            for attempt in range(self._max_retries):
                try:
                    self._redis = redis.Redis(
                        host=settings.REDIS_HOST,
                        port=settings.REDIS_PORT,
                        db=0,
                        decode_responses=True,
                        socket_timeout=5,
                        socket_connect_timeout=5,
                        retry_on_timeout=True,
                        health_check_interval=30
                    )
                    
                    await asyncio.wait_for(self._redis.ping(), timeout=5.0)
                    logger.info("Successfully connected to Redis")
                    return
                except asyncio.TimeoutError:
                    logger.warning(f"Redis connection timeout (attempt {attempt + 1}/{self._max_retries})")
                except Exception as e:
                    logger.warning(f"Failed to connect to Redis (attempt {attempt + 1}/{self._max_retries}): {str(e)}")
                
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay)
                else:
                    logger.error("Failed to connect to Redis after all retries")
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to connect to Redis. Please try again later."
                    )

    async def create_task(
        self, name: str, parameters: Dict[str, Any], callback_url: str
    ) -> str:
        try:
            if self._redis is None:
                await self.initialize()

            task_id = str(uuid.uuid4())
            created_at = datetime.utcnow().isoformat()

            task_data = {
                "task_id": task_id,
                "name": name,
                "parameters": parameters,
                "callback_url": callback_url,
                "status": TaskStatus.PENDING,
                "created_at": created_at,
                "updated_at": created_at,
                "progress": 0.0,
                "message": "Task created",
            }

            await asyncio.wait_for(
                self._redis.set(f"task:{task_id}", json.dumps(task_data)),
                timeout=5.0
            )
            logger.info(f"Created task {task_id}")

            task = execute_task.delay(task_id, name, parameters, callback_url)
            if not task:
                raise Exception("Failed to create Celery task")
            
            logger.info(f"Started execution of task {task_id}")
            return task_id

        except asyncio.TimeoutError:
            logger.error("Redis operation timed out")
            raise HTTPException(
                status_code=500,
                detail="Redis operation timed out. Please try again later."
            )
        except Exception as e:
            logger.error(f"Failed to create task: {str(e)}")
            if 'task_id' in locals():
                try:
                    await self._redis.delete(f"task:{task_id}")
                except Exception:
                    pass
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create task: {str(e)}"
            )

    async def get_task_status(self, task_id: str) -> TaskStatusResponse:
        try:
            if self._redis is None:
                await self.initialize()

            task_data = await asyncio.wait_for(
                self._redis.get(f"task:{task_id}"),
                timeout=5.0
            )
            if not task_data:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

            task_data = json.loads(task_data)
            return TaskStatusResponse(
                task_id=task_id,
                status=TaskStatus(task_data["status"]),
                progress=task_data["progress"],
                message=task_data["message"],
            )
        except asyncio.TimeoutError:
            logger.error("Redis operation timed out")
            raise HTTPException(
                status_code=500,
                detail="Redis operation timed out. Please try again later."
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get task status: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get task status: {str(e)}"
            )

    async def stream_task_status(self, task_id: str) -> AsyncGenerator[str, None]:
        try:
            if self._redis is None:
                await self.initialize()

            while True:
                task_data = await asyncio.wait_for(
                    self._redis.get(f"task:{task_id}"),
                    timeout=5.0
                )
                if not task_data:
                    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

                task_data = json.loads(task_data)
                status = TaskStatus(task_data["status"])

                status_response = TaskStatusResponse(
                    task_id=task_id,
                    status=status,
                    progress=task_data["progress"],
                    message=task_data["message"],
                )

                yield f"data: {json.dumps(status_response.dict())}\n\n"

                if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    logger.info(f"Task {task_id} finished with status {status}")
                    break

                await asyncio.sleep(5.0)

        except asyncio.TimeoutError:
            logger.error("Redis operation timed out")
            raise HTTPException(
                status_code=500,
                detail="Redis operation timed out. Please try again later."
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to stream task status: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to stream task status: {str(e)}"
            )

task_manager = TaskManager()
