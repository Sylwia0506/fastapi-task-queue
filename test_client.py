import json
import requests
import time
from datetime import datetime
from typing import Dict, Any


API_BASE_URL = "http://web:8000"
CALLBACK_URL = "http://localhost:8000/callback"

def create_task(name: str, parameters: Dict[str, Any]) -> str:
    response = requests.post(
        f"{API_BASE_URL}/api/tasks",
        json={
            "name": name,
            "parameters": parameters,
            "callback_url": CALLBACK_URL
        }
    )
    response.raise_for_status()
    return response.json()["task_id"]

def get_task_status(task_id: str) -> Dict[str, Any]:
    response = requests.get(f"{API_BASE_URL}/api/tasks/{task_id}/state")
    response.raise_for_status()
    return response.json()

def stream_task_status(task_id: str):
    response = requests.get(f"{API_BASE_URL}/api/tasks/{task_id}", stream=True)
    response.raise_for_status()
    
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data = json.loads(line[6:])
                print(f"\nTask {task_id} status:")
                print(f"  Status: {data['status']}")
                print(f"  Progress: {data['progress']*100:.1f}%")
                print(f"  Message: {data['message']}")
                
                if data['status'] in ['COMPLETED', 'FAILED']:
                    break

def main():
    print("=== Task System Test ===")
    
    task_name = "test_task"
    task_params = {
        "param1": "value1",
        "param2": 42,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    print(f"\nCreating task '{task_name}'...")
    task_id = create_task(task_name, task_params)
    print(f"Task created with ID: {task_id}")
    
    print("\nChecking initial status...")
    initial_status = get_task_status(task_id)
    print(f"Initial status: {initial_status['status']}")
    
    print("\nStarting to stream task status...")
    print("(Press Ctrl+C to interrupt)")
    try:
        stream_task_status(task_id)
    except KeyboardInterrupt:
        print("\nStreaming interrupted")

    print("\nChecking final status...")
    final_status = get_task_status(task_id)
    print(f"Final status: {final_status['status']}")
    print(f"Final progress: {final_status['progress']*100:.1f}%")
    print(f"Final message: {final_status['message']}")

if __name__ == "__main__":
    main()
