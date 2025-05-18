import json
import logging
import random
import time
from datetime import datetime
from typing import Any, Dict
import requests
from celery import Celery
from redis import Redis
from redis.exceptions import RedisError
from app.core.config import settings
from app.models.task import TaskResult, TaskStatus

logger = logging.getLogger(__name__)

celery = Celery(
    "tasks",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

def get_redis_connection() -> Redis:
    try:
        redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        return redis
    except RedisError as e:
        logger.error(f"Failed to connect to Redis: {str(e)}")
        raise

@celery.task(bind=True, name="execute_task")
def execute_task(self, task_id: str, name: str, parameters: Dict[str, Any], callback_url: str) -> None:
    redis = None
    try:
        redis = get_redis_connection()
        update_task_status.delay(task_id, TaskStatus.RUNNING, 0.0, "Task started")
        total_steps = random.randint(5, 15)
        start_time = time.time()
        for step in range(1, total_steps + 1):
            work_time = random.uniform(1.0, 3.0)
            time.sleep(work_time)
            progress = step / total_steps
            message = f"Processing step {step}/{total_steps} ({(progress * 100):.1f}%)"
            update_task_status.delay(task_id, TaskStatus.RUNNING, progress, message)
        execution_time = time.time() - start_time
        result = {
            "name": name,
            "parameters": parameters,
            "completed_at": datetime.utcnow().isoformat(),
            "result_data": {
                "message": "Task completed successfully",
                "total_steps": total_steps,
                "execution_time": execution_time
            }
        }
        update_task_status.delay(task_id, TaskStatus.COMPLETED, 1.0, "Task completed")
        task_result = TaskResult(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            result=result,
            completed_at=datetime.utcnow()
        )
        send_callback.delay(callback_url, task_result.dict())
    except Exception as e:
        error_message = f"Task failed: {str(e)}"
        update_task_status.delay(task_id, TaskStatus.FAILED, 0.0, error_message)
        task_result = TaskResult(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error=error_message,
            completed_at=datetime.utcnow()
        )
        send_callback.delay(callback_url, task_result.dict())

@celery.task(name="update_task_status")
def update_task_status(task_id: str, status: TaskStatus, progress: float, message: str) -> None:
    redis = None
    try:
        redis = get_redis_connection()
        task_data = redis.get(f"task:{task_id}")
        if not task_data:
            return
        task_data = json.loads(task_data)
        task_data.update({
            "status": status,
            "progress": progress,
            "message": message,
            "updated_at": datetime.utcnow().isoformat()
        })
        redis.set(f"task:{task_id}", json.dumps(task_data))
    except Exception as e:
        logger.error(f"Failed to update task {task_id} status: {str(e)}")

@celery.task(name="send_callback", bind=True, max_retries=3)
def send_callback(self, callback_url: str, data: Dict[str, Any]) -> None:
    try:
        response = requests.post(
            callback_url,
            json=data,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code >= 400:
            if response.status_code >= 500 or response.status_code == 429:
                retry_delay = 2 ** self.request.retries
                raise self.retry(exc=Exception("Callback error"), countdown=retry_delay)
    except requests.exceptions.Timeout:
        retry_delay = 2 ** self.request.retries
        raise self.retry(exc=requests.exceptions.Timeout(), countdown=retry_delay)
    except requests.exceptions.RequestException as e:
        retry_delay = 2 ** self.request.retries
        raise self.retry(exc=e, countdown=retry_delay)