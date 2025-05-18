# FastAPI Task Execution API

A containerized FastAPI application for asynchronous task execution with status streaming.

## Run

```bash
docker-compose up --build
```

## API

- POST /api/tasks
- GET /api/tasks/{task_id}
- GET /api/tasks/{task_id}/state

## Examples

### 1. Submit a Task
```bash
curl -X POST "http://localhost:8000/api/tasks" \
  -H "Content-Type: application/json" \
  -d '{"name": "test-task", "parameters": {}, "callback_url": "http://webhook.site/your-unique-url"}'
```
**Response:**
```json
{"task_id":"<unique-task-id>"}
```

### 2. Stream Task Status (every 5 seconds)
```bash
curl -N http://localhost:8000/api/tasks/<unique-task-id>
```
**You will see lines like:**
```
data: {"task_id": "...", "status": "PENDING", ...}
data: {"task_id": "...", "status": "RUNNING", ...}
data: {"task_id": "...", "status": "COMPLETED", ...}
```

### 3. Get Task Status via API
```bash
curl http://localhost:8000/api/tasks/<unique-task-id>/state
```
**Response:**
```json
{"task_id":"...","status":"COMPLETED", ...}
```

### 4. Monitoring and Queues (Flower)
Open in your browser:
```
http://localhost:5555
```
You will see the Celery dashboard with all tasks and their statuses.

### 5. Callback with Result
Use a [webhook.site](https://webhook.site/) URL as `callback_url` in your POST request. After task completion, the result will appear there automatically.

### 6. Multiple Tasks (Queuing)
```bash
for i in {1..5}; do
  curl -X POST "http://localhost:8000/api/tasks" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"test-$i\", \"parameters\": {}, \"callback_url\": \"http://webhook.site/your-unique-url\"}" &
done
```
Each task gets its own `task_id` and is visible in Flower.

### 7. Automated Tests
```bash
docker-compose run web pytest
```

## Requirements Checklist

- Containerized FastAPI application (Docker)
- Platform and OS independent
- Can run on a cluster (e.g., Kubernetes)
- Long-running async tasks via POST /api/tasks (multiple requests supported)
- Returns task identifier
- Streams task status every 5 seconds until completion
- Sends task result as JSON to the callback URL provided in the POST request
- Task status available via API and Flower dashboard
- Task queuing supported

## Switching to RabbitMQ Instead of Redis

To use RabbitMQ as the task queue broker:

1. Add the RabbitMQ service to `docker-compose.yml`:

```yaml
rabbitmq:
  image: rabbitmq:3-management
  ports:
    - "5672:5672"
    - "15672:15672"
  environment:
    RABBITMQ_DEFAULT_USER: user
    RABBITMQ_DEFAULT_PASS: password
```

2. Change the Celery configuration (e.g., in `app/tasks/celery_tasks.py`):

```python
celery = Celery(
    "tasks",
    broker="amqp://user:password@rabbitmq:5672//",
    backend="redis://redis:6379/0"
)
```

3. Restart the containers:
```bash
docker-compose down
docker-compose up --build
```

4. The RabbitMQ dashboard will be available at http://localhost:15672 (login: user, password: password).

## Kubernetes Deployment

- The application is fully containerized (Docker), so you can run it on any system (Linux, Windows, Mac, cloud, cluster).
- In cluster environments (e.g., Kubernetes), prepare the appropriate manifests (deployment, service, configmap).
- You can scale Celery workers (e.g., `docker-compose up --scale celery_worker=4`).
