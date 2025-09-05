from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
import os
from datetime import datetime, date
import uuid

app = FastAPI()

# Data models
class Task(BaseModel):
    id: str
    name: str
    start_date: str
    end_date: str
    progress: float = 0.0
    color: str = "#4285f4"
    dependencies: List[str] = []
    is_milestone: bool = False
    parent_id: Optional[str] = None
    created_at: str
    updated_at: str

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    progress: Optional[float] = None
    color: Optional[str] = None
    dependencies: Optional[List[str]] = None
    is_milestone: Optional[bool] = None

class ActionLog(BaseModel):
    id: str
    action: str
    task_id: str
    task_name: str
    timestamp: str
    details: Dict

# Data storage
DATA_FILE = "gantt_data.json"
LOGS_FILE = "gantt_logs.json"

def load_data():
    """Load tasks and logs from JSON files"""
    tasks = {}
    logs = []
    
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            tasks = {k: Task(**v) for k, v in data.get('tasks', {}).items()}
    
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, 'r') as f:
            logs_data = json.load(f)
            logs = [ActionLog(**log) for log in logs_data.get('logs', [])]
    
    return tasks, logs

def save_data(tasks, logs):
    """Save tasks and logs to JSON files"""
    # Save tasks
    tasks_dict = {k: v.dict() for k, v in tasks.items()}
    with open(DATA_FILE, 'w') as f:
        json.dump({'tasks': tasks_dict}, f, indent=2)
    
    # Save logs
    logs_dict = [log.dict() for log in logs]
    with open(LOGS_FILE, 'w') as f:
        json.dump({'logs': logs_dict}, f, indent=2)

def log_action(action: str, task_id: str, task_name: str, details: Dict, logs: List[ActionLog]):
    """Add an action to the log"""
    log_entry = ActionLog(
        id=str(uuid.uuid4()),
        action=action,
        task_id=task_id,
        task_name=task_name,
        timestamp=datetime.now().isoformat(),
        details=details
    )
    logs.append(log_entry)
    return logs

# Initialize data
tasks_db, logs_db = load_data()

# API Routes
@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.get("/api/tasks")
async def get_tasks():
    """Get all tasks"""
    return {"tasks": list(tasks_db.values())}

@app.post("/api/tasks")
async def create_task(task_data: dict):
    """Create a new task"""
    global tasks_db, logs_db
    
    task_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    # Default color based on task type
    default_color = "#666666" if task_data.get('is_milestone', False) else "#4285f4"
    
    task = Task(
        id=task_id,
        name=task_data['name'],
        start_date=task_data['start_date'],
        end_date=task_data['end_date'],
        progress=task_data.get('progress', 0.0),
        color=task_data.get('color', default_color),
        dependencies=task_data.get('dependencies', []),
        is_milestone=task_data.get('is_milestone', False),
        parent_id=task_data.get('parent_id'),
        created_at=now,
        updated_at=now
    )
    
    tasks_db[task_id] = task
    logs_db = log_action("CREATE", task_id, task.name, task.dict(), logs_db)
    save_data(tasks_db, logs_db)
    
    return {"task": task, "message": "Task created successfully"}

@app.put("/api/tasks/{task_id}")
async def update_task(task_id: str, updates: TaskUpdate):
    """Update an existing task"""
    global tasks_db, logs_db
    
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks_db[task_id]
    old_data = task.dict()
    
    # Apply updates
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    task.updated_at = datetime.now().isoformat()
    
    logs_db = log_action("UPDATE", task_id, task.name, {
        "old": old_data,
        "new": task.dict(),
        "changes": update_data
    }, logs_db)
    
    save_data(tasks_db, logs_db)
    
    return {"task": task, "message": "Task updated successfully"}

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task"""
    global tasks_db, logs_db
    
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks_db[task_id]
    task_name = task.name
    
    # Remove dependencies from other tasks
    for other_task in tasks_db.values():
        if task_id in other_task.dependencies:
            other_task.dependencies.remove(task_id)
    
    del tasks_db[task_id]
    logs_db = log_action("DELETE", task_id, task_name, task.dict(), logs_db)
    save_data(tasks_db, logs_db)
    
    return {"message": "Task deleted successfully"}

@app.get("/api/logs")
async def get_logs():
    """Get action logs"""
    return {"logs": logs_db[-50:]}  # Return last 50 logs

@app.get("/api/logs/task/{task_id}")
async def get_task_logs(task_id: str):
    """Get logs for a specific task"""
    task_logs = [log for log in logs_db if log.task_id == task_id]
    return {"logs": task_logs}

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)