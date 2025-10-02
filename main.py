# from fastapi import FastAPI, HTTPException, Request
# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import FileResponse
# from pydantic import BaseModel
# from typing import List, Optional, Dict
# import json
# import os
# from datetime import datetime, date
# import uuid

# # Need to add SQLite or other DB for production use
# # For simplicity, using JSON file storage here

# app = FastAPI(title="Gantt Chart API", description="A comprehensive Gantt chart application API")

# # Data models
# class Task(BaseModel):
#     id: str
#     name: str
#     start_date: str
#     end_date: str
#     progress: float = 0.0
#     color: str = "#4285f4"
#     dependencies: List[str] = []
#     is_milestone: bool = False
#     parent_id: Optional[str] = None
#     created_at: str
#     updated_at: str
#     description: Optional[str] = None
#     assigned_to: Optional[str] = None
#     priority: str = "medium"  # low, medium, high, critical

# class TaskCreate(BaseModel):
#     name: str
#     start_date: str
#     end_date: str
#     progress: float = 0.0
#     color: str = "#4285f4"
#     dependencies: List[str] = []
#     is_milestone: bool = False
#     parent_id: Optional[str] = None
#     description: Optional[str] = None
#     assigned_to: Optional[str] = None
#     priority: str = "medium"

# class TaskUpdate(BaseModel):
#     name: Optional[str] = None
#     start_date: Optional[str] = None
#     end_date: Optional[str] = None
#     progress: Optional[float] = None
#     color: Optional[str] = None
#     dependencies: Optional[List[str]] = None
#     is_milestone: Optional[bool] = None
#     description: Optional[str] = None
#     assigned_to: Optional[str] = None
#     priority: Optional[str] = None

# class ActionLog(BaseModel):
#     id: str
#     action: str
#     task_id: str
#     task_name: str
#     timestamp: str
#     details: Dict
#     user: Optional[str] = "system"

# class ProjectSettings(BaseModel):
#     name: str = "My Project"
#     start_date: Optional[str] = None
#     end_date: Optional[str] = None
#     description: Optional[str] = None
#     created_at: str
#     updated_at: str

# # Data storage
# DATA_FILE = "gantt_data.json"
# LOGS_FILE = "gantt_logs.json"
# SETTINGS_FILE = "project_settings.json"

# def load_data():
#     """Load tasks, logs, and settings from JSON files"""
#     tasks = {}
#     logs = []
#     settings = None
    
#     if os.path.exists(DATA_FILE):
#         with open(DATA_FILE, 'r') as f:
#             data = json.load(f)
#             tasks = {k: Task(**v) for k, v in data.get('tasks', {}).items()}
    
#     if os.path.exists(LOGS_FILE):
#         with open(LOGS_FILE, 'r') as f:
#             logs_data = json.load(f)
#             logs = [ActionLog(**log) for log in logs_data.get('logs', [])]
    
#     if os.path.exists(SETTINGS_FILE):
#         with open(SETTINGS_FILE, 'r') as f:
#             settings_data = json.load(f)
#             settings = ProjectSettings(**settings_data)
#     else:
#         # Create default settings
#         now = datetime.now().isoformat()
#         settings = ProjectSettings(
#             created_at=now,
#             updated_at=now
#         )
#         # Save default settings
#         with open(SETTINGS_FILE, 'w') as f:
#             json.dump(settings.model_dump(), f, indent=2)
    
#     return tasks, logs, settings

# def save_data(tasks, logs):
#     """Save tasks and logs to JSON files"""
#     # Save tasks
#     tasks_dict = {k: v.dict() for k, v in tasks.items()}
#     with open(DATA_FILE, 'w') as f:
#         json.dump({'tasks': tasks_dict}, f, indent=2)
    
#     # Save logs (keep only last 1000 entries)
#     logs_dict = [log.dict() for log in logs[-1000:]]
#     with open(LOGS_FILE, 'w') as f:
#         json.dump({'logs': logs_dict}, f, indent=2)

# def save_settings(settings: ProjectSettings):
#     """Save project settings"""
#     with open(SETTINGS_FILE, 'w') as f:
#         json.dump(settings.dict(), f, indent=2)

# def log_action(action: str, task_id: str, task_name: str, details: Dict, logs: List[ActionLog], user: str = "system"):
#     """Add an action to the log"""
#     log_entry = ActionLog(
#         id=str(uuid.uuid4()),
#         action=action,
#         task_id=task_id,
#         task_name=task_name,
#         timestamp=datetime.now().isoformat(),
#         details=details,
#         user=user
#     )
#     logs.append(log_entry)
#     return logs

# def validate_dependencies(task_id: str, dependencies: List[str], tasks: Dict[str, Task]) -> List[str]:
#     """Validate and filter dependencies to prevent circular references"""
#     valid_deps = []
    
#     def has_circular_dependency(current_id: str, target_id: str, visited: set = None) -> bool:
#         if visited is None:
#             visited = set()
        
#         if current_id in visited:
#             return True
        
#         if current_id == target_id:
#             return True
        
#         visited.add(current_id)
        
#         current_task = tasks.get(current_id)
#         if current_task:
#             for dep in current_task.dependencies:
#                 if has_circular_dependency(dep, target_id, visited.copy()):
#                     return True
        
#         return False
    
#     for dep_id in dependencies:
#         if dep_id in tasks and not has_circular_dependency(dep_id, task_id):
#             valid_deps.append(dep_id)
    
#     return valid_deps

# def calculate_critical_path(tasks: Dict[str, Task]) -> List[str]:
#     """Calculate the critical path through the project"""
#     # This is a simplified critical path calculation
#     # In a full implementation, you'd use proper CPM algorithms
    
#     # For now, return the longest chain of dependencies
#     def get_chain_length(task_id: str, visited: set = None) -> int:
#         if visited is None:
#             visited = set()
        
#         if task_id in visited:
#             return 0
        
#         visited.add(task_id)
#         task = tasks.get(task_id)
#         if not task:
#             return 0
        
#         if not task.dependencies:
#             return 1
        
#         max_length = 0
#         for dep_id in task.dependencies:
#             length = get_chain_length(dep_id, visited.copy())
#             max_length = max(max_length, length)
        
#         return max_length + 1
    
#     # Find the task with the longest dependency chain
#     max_length = 0
#     critical_task = None
    
#     for task_id in tasks:
#         length = get_chain_length(task_id)
#         if length > max_length:
#             max_length = length
#             critical_task = task_id
    
#     # Trace back the critical path
#     critical_path = []
#     if critical_task:
#         def trace_path(task_id: str):
#             critical_path.append(task_id)
#             task = tasks.get(task_id)
#             if task and task.dependencies:
#                 # Find the dependency with the longest chain
#                 longest_dep = None
#                 max_dep_length = 0
#                 for dep_id in task.dependencies:
#                     dep_length = get_chain_length(dep_id)
#                     if dep_length > max_dep_length:
#                         max_dep_length = dep_length
#                         longest_dep = dep_id
                
#                 if longest_dep:
#                     trace_path(longest_dep)
        
#         trace_path(critical_task)
    
#     return critical_path

# # Initialize data
# tasks_db, logs_db, project_settings = load_data()

# # Middleware for CORS (if needed)
# @app.middleware("http")
# async def add_cors_header(request: Request, call_next):
#     response = await call_next(request)
#     response.headers["Access-Control-Allow-Origin"] = "*"
#     response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
#     response.headers["Access-Control-Allow-Headers"] = "*"
#     return response

# # API Routes
# @app.get("/")
# async def read_root():
#     """Serve the main application"""
#     return FileResponse("static/index.html")

# @app.get("/api/tasks")
# async def get_tasks():
#     """Get all tasks with additional metadata"""
#     tasks_list = list(tasks_db.values())
#     critical_path = calculate_critical_path(tasks_db)
    
#     return {
#         "tasks": tasks_list,
#         "total_tasks": len(tasks_list),
#         "completed_tasks": len([t for t in tasks_list if t.progress >= 100]),
#         "critical_path": critical_path,
#         "project_settings": project_settings.dict()
#     }

# @app.get("/api/tasks/{task_id}")
# async def get_task(task_id: str):
#     """Get a specific task"""
#     if task_id not in tasks_db:
#         raise HTTPException(status_code=404, detail="Task not found")
    
#     task = tasks_db[task_id]
#     task_logs = [log for log in logs_db if log.task_id == task_id]
    
#     return {
#         "task": task,
#         "logs": task_logs[-10:]  # Last 10 logs for this task
#     }

# @app.post("/api/tasks")
# async def create_task(task_data: TaskCreate):
#     """Create a new task"""
#     global tasks_db, logs_db
    
#     task_id = str(uuid.uuid4())
#     now = datetime.now().isoformat()
    
#     # Validate dependencies
#     valid_dependencies = validate_dependencies(task_id, task_data.dependencies, tasks_db)
    
#     # Default color based on task type
#     default_color = "#666666" if task_data.is_milestone else "#4285f4"
    
#     task = Task(
#         id=task_id,
#         name=task_data.name,
#         start_date=task_data.start_date,
#         end_date=task_data.end_date,
#         progress=task_data.progress,
#         color=task_data.color if task_data.color != "#4285f4" else default_color,
#         dependencies=valid_dependencies,
#         is_milestone=task_data.is_milestone,
#         parent_id=task_data.parent_id,
#         description=task_data.description,
#         assigned_to=task_data.assigned_to,
#         priority=task_data.priority,
#         created_at=now,
#         updated_at=now
#     )
    
#     tasks_db[task_id] = task
#     logs_db = log_action("CREATE", task_id, task.name, task.dict(), logs_db)
#     save_data(tasks_db, logs_db)
    
#     return {"task": task, "message": "Task created successfully"}

# @app.put("/api/tasks/{task_id}")
# async def update_task(task_id: str, updates: TaskUpdate):
#     """Update an existing task"""
#     global tasks_db, logs_db
    
#     if task_id not in tasks_db:
#         raise HTTPException(status_code=404, detail="Task not found")
    
#     task = tasks_db[task_id]
#     old_data = task.dict()
    
#     # Apply updates
#     update_data = updates.dict(exclude_unset=True)
    
#     # Validate dependencies if being updated
#     if 'dependencies' in update_data:
#         update_data['dependencies'] = validate_dependencies(task_id, update_data['dependencies'], tasks_db)
    
#     for field, value in update_data.items():
#         setattr(task, field, value)
    
#     task.updated_at = datetime.now().isoformat()
    
#     logs_db = log_action("UPDATE", task_id, task.name, {
#         "old": old_data,
#         "new": task.dict(),
#         "changes": update_data
#     }, logs_db)
    
#     save_data(tasks_db, logs_db)
    
#     return {"task": task, "message": "Task updated successfully"}

# @app.delete("/api/tasks/{task_id}")
# async def delete_task(task_id: str):
#     """Delete a task"""
#     global tasks_db, logs_db
    
#     if task_id not in tasks_db:
#         raise HTTPException(status_code=404, detail="Task not found")
    
#     task = tasks_db[task_id]
#     task_name = task.name
    
#     # Remove dependencies from other tasks
#     for other_task in tasks_db.values():
#         if task_id in other_task.dependencies:
#             other_task.dependencies.remove(task_id)
#             other_task.updated_at = datetime.now().isoformat()
    
#     # Delete child tasks if any
#     child_tasks = [t for t in tasks_db.values() if t.parent_id == task_id]
#     for child in child_tasks:
#         del tasks_db[child.id]
#         logs_db = log_action("DELETE", child.id, child.name, 
#                            {"reason": "Parent task deleted", "parent_id": task_id}, logs_db)
    
#     del tasks_db[task_id]
#     logs_db = log_action("DELETE", task_id, task_name, task.dict(), logs_db)
#     save_data(tasks_db, logs_db)
    
#     return {"message": "Task deleted successfully"}

# @app.post("/api/tasks/{task_id}/duplicate")
# async def duplicate_task(task_id: str):
#     """Duplicate an existing task"""
#     global tasks_db, logs_db
    
#     if task_id not in tasks_db:
#         raise HTTPException(status_code=404, detail="Task not found")
    
#     original_task = tasks_db[task_id]
#     new_task_id = str(uuid.uuid4())
#     now = datetime.now().isoformat()
    
#     # Create duplicate with new ID and name
#     duplicate_data = original_task.dict()
#     duplicate_data.update({
#         'id': new_task_id,
#         'name': f"{original_task.name} (Copy)",
#         'progress': 0.0,  # Reset progress
#         'dependencies': [],  # Clear dependencies
#         'created_at': now,
#         'updated_at': now
#     })
    
#     new_task = Task(**duplicate_data)
#     tasks_db[new_task_id] = new_task
    
#     logs_db = log_action("DUPLICATE", new_task_id, new_task.name, {
#         "original_task_id": task_id,
#         "original_task_name": original_task.name
#     }, logs_db)
    
#     save_data(tasks_db, logs_db)
    
#     return {"task": new_task, "message": "Task duplicated successfully"}

# @app.get("/api/logs")
# async def get_logs(limit: int = 50):
#     """Get recent action logs"""
#     return {"logs": logs_db[-limit:]}

# @app.get("/api/logs/task/{task_id}")
# async def get_task_logs(task_id: str):
#     """Get logs for a specific task"""
#     task_logs = [log for log in logs_db if log.task_id == task_id]
#     return {"logs": task_logs}

# @app.get("/api/analytics")
# async def get_analytics():
#     """Get project analytics and statistics"""
#     if not tasks_db:
#         return {"message": "No tasks available for analytics"}
    
#     total_tasks = len(tasks_db)
#     completed_tasks = len([t for t in tasks_db.values() if t.progress >= 100])
#     in_progress_tasks = len([t for t in tasks_db.values() if 0 < t.progress < 100])
#     not_started_tasks = len([t for t in tasks_db.values() if t.progress == 0])
#     milestones = len([t for t in tasks_db.values() if t.is_milestone])
    
#     # Calculate average progress
#     avg_progress = sum(t.progress for t in tasks_db.values()) / total_tasks
    
#     # Task priority distribution
#     priority_dist = {}
#     for task in tasks_db.values():
#         priority_dist[task.priority] = priority_dist.get(task.priority, 0) + 1
    
#     # Tasks by month (creation date)
#     tasks_by_month = {}
#     for task in tasks_db.values():
#         month = task.created_at[:7]  # YYYY-MM
#         tasks_by_month[month] = tasks_by_month.get(month, 0) + 1
    
#     critical_path = calculate_critical_path(tasks_db)
    
#     return {
#         "total_tasks": total_tasks,
#         "completed_tasks": completed_tasks,
#         "in_progress_tasks": in_progress_tasks,
#         "not_started_tasks": not_started_tasks,
#         "milestones": milestones,
#         "completion_rate": (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0,
#         "average_progress": avg_progress,
#         "priority_distribution": priority_dist,
#         "tasks_by_month": tasks_by_month,
#         "critical_path_length": len(critical_path),
#         "critical_path": critical_path
#     }

# @app.get("/api/settings")
# async def get_settings():
#     """Get project settings"""
#     return project_settings

# @app.put("/api/settings")
# async def update_settings(settings_update: dict):
#     """Update project settings"""
#     global project_settings
    
#     for key, value in settings_update.items():
#         if hasattr(project_settings, key):
#             setattr(project_settings, key, value)
    
#     project_settings.updated_at = datetime.now().isoformat()
#     save_settings(project_settings)
    
#     return {"settings": project_settings.model_dump(), "message": "Settings updated successfully"}

# # Export functionality
# @app.get("/api/export")
# async def export_data(format: str = "json"):
#     """Export project data in various formats"""
#     if format.lower() == "json":
#         return {
#             "tasks": [task.dict() for task in tasks_db.values()],
#             "logs": [log.dict() for log in logs_db],
#             "settings": project_settings.dict(),
#             "exported_at": datetime.now().isoformat()
#         }
#     else:
#         raise HTTPException(status_code=400, detail="Unsupported export format")

# # Health check
# @app.get("/api/health")
# async def health_check():
#     """Health check endpoint"""
#     return {
#         "status": "healthy",
#         "timestamp": datetime.now().isoformat(),
#         "tasks_count": len(tasks_db),
#         "logs_count": len(logs_db)
#     }

# # Mount static files
# app.mount("/static", StaticFiles(directory="static"), name="static")

# if __name__ == "__main__":
#     import uvicorn
#     print("Starting Gantt Chart Application...")
#     print("Access the application at: http://localhost:8000")
#     uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import uuid

# Import database module
import database as db

app = FastAPI(title="Gantt Chart API", description="A comprehensive Gantt chart application API with SQLite storage")

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
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: str = "medium"

class TaskCreate(BaseModel):
    name: str
    start_date: str
    end_date: str
    progress: float = 0.0
    color: str = "#4285f4"
    dependencies: List[str] = []
    is_milestone: bool = False
    parent_id: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: str = "medium"

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    progress: Optional[float] = None
    color: Optional[str] = None
    dependencies: Optional[List[str]] = None
    is_milestone: Optional[bool] = None
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: Optional[str] = None
    parent_id: Optional[str] = None

class ActionLog(BaseModel):
    id: str
    action: str
    task_id: str
    task_name: str
    timestamp: str
    details: Dict
    user: Optional[str] = "system"

class ProjectSettings(BaseModel):
    name: str = "My Project"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    created_at: str
    updated_at: str

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize the database when the app starts"""
    db.init_database()
    print("✓ Database ready")

def validate_dependencies(task_id: str, dependencies: List[str]) -> List[str]:
    """Validate and filter dependencies to prevent circular references"""
    valid_deps = []
    all_tasks = {task['id']: task for task in db.get_all_tasks()}
    
    def has_circular_dependency(current_id: str, target_id: str, visited: set = None) -> bool:
        if visited is None:
            visited = set()
        
        if current_id in visited:
            return True
        
        if current_id == target_id:
            return True
        
        visited.add(current_id)
        
        current_task = all_tasks.get(current_id)
        if current_task:
            for dep in current_task['dependencies']:
                if has_circular_dependency(dep, target_id, visited.copy()):
                    return True
        
        return False
    
    for dep_id in dependencies:
        if dep_id in all_tasks and not has_circular_dependency(dep_id, task_id):
            valid_deps.append(dep_id)
    
    return valid_deps

def calculate_critical_path() -> List[str]:
    """Calculate the critical path through the project"""
    all_tasks = {task['id']: task for task in db.get_all_tasks()}
    
    def get_chain_length(task_id: str, visited: set = None) -> int:
        if visited is None:
            visited = set()
        
        if task_id in visited:
            return 0
        
        visited.add(task_id)
        task = all_tasks.get(task_id)
        if not task:
            return 0
        
        if not task['dependencies']:
            return 1
        
        max_length = 0
        for dep_id in task['dependencies']:
            length = get_chain_length(dep_id, visited.copy())
            max_length = max(max_length, length)
        
        return max_length + 1
    
    max_length = 0
    critical_task = None
    
    for task_id in all_tasks:
        length = get_chain_length(task_id)
        if length > max_length:
            max_length = length
            critical_task = task_id
    
    critical_path = []
    if critical_task:
        def trace_path(task_id: str):
            critical_path.append(task_id)
            task = all_tasks.get(task_id)
            if task and task['dependencies']:
                longest_dep = None
                max_dep_length = 0
                for dep_id in task['dependencies']:
                    dep_length = get_chain_length(dep_id)
                    if dep_length > max_dep_length:
                        max_dep_length = dep_length
                        longest_dep = dep_id
                
                if longest_dep:
                    trace_path(longest_dep)
        
        trace_path(critical_task)
    
    return critical_path

def log_action(action: str, task_id: str, task_name: str, details: Dict, user: str = "system"):
    """Add an action to the log"""
    log_data = {
        'id': str(uuid.uuid4()),
        'action': action,
        'task_id': task_id,
        'task_name': task_name,
        'timestamp': datetime.now().isoformat(),
        'details': details,
        'user': user
    }
    db.create_log(log_data)

# Middleware for CORS
@app.middleware("http")
async def add_cors_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# API Routes
@app.get("/")
async def read_root():
    """Serve the main application"""
    return FileResponse("static/index.html")

@app.get("/api/tasks")
async def get_tasks():
    """Get all tasks with additional metadata, organized hierarchically"""
    tasks_list = db.get_all_tasks()
    critical_path = calculate_critical_path()
    
    # Organize tasks hierarchically
    root_tasks = []
    task_children = {}
    
    for task in tasks_list:
        parent_id = task.get('parent_id')
        if parent_id:
            if parent_id not in task_children:
                task_children[parent_id] = []
            task_children[parent_id].append(task)
        else:
            root_tasks.append(task)
    
    def add_children_recursive(task):
        task_id = task['id']
        if task_id in task_children:
            task['subtasks'] = task_children[task_id]
            for child in task['subtasks']:
                add_children_recursive(child)
        else:
            task['subtasks'] = []
        return task
    
    hierarchical_tasks = [add_children_recursive(task) for task in root_tasks]
    project_settings = db.get_project_settings()
    
    return {
        "tasks": tasks_list,
        "hierarchical_tasks": hierarchical_tasks,
        "total_tasks": len(tasks_list),
        "completed_tasks": len([t for t in tasks_list if t['progress'] >= 100]),
        "critical_path": critical_path,
        "project_settings": project_settings
    }

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    """Get a specific task"""
    task = db.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_logs = db.get_task_logs(task_id)
    
    return {
        "task": task,
        "logs": task_logs[-10:]
    }

@app.post("/api/tasks")
async def create_task(task_data: TaskCreate):
    """Create a new task"""
    task_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    # Validate dependencies
    valid_dependencies = validate_dependencies(task_id, task_data.dependencies)
    
    # Default color based on task type
    default_color = "#666666" if task_data.is_milestone else "#4285f4"
    
    task_dict = {
        'id': task_id,
        'name': task_data.name,
        'start_date': task_data.start_date,
        'end_date': task_data.end_date,
        'progress': task_data.progress,
        'color': task_data.color if task_data.color != "#4285f4" else default_color,
        'dependencies': valid_dependencies,
        'is_milestone': task_data.is_milestone,
        'parent_id': task_data.parent_id,
        'description': task_data.description,
        'assigned_to': task_data.assigned_to,
        'priority': task_data.priority,
        'created_at': now,
        'updated_at': now
    }
    
    db.create_task(task_dict)
    log_action("CREATE", task_id, task_data.name, task_dict)
    
    return {"task": task_dict, "message": "Task created successfully"}

@app.put("/api/tasks/{task_id}")
async def update_task(task_id: str, updates: TaskUpdate):
    """Update an existing task"""
    task = db.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    old_data = task.copy()
    update_data = updates.model_dump(exclude_unset=True)
    
    # Validate dependencies if being updated
    if 'dependencies' in update_data:
        update_data['dependencies'] = validate_dependencies(task_id, update_data['dependencies'])
    
    updated_task = db.update_task(task_id, update_data)
    
    log_action("UPDATE", task_id, updated_task['name'], {
        "old": old_data,
        "new": updated_task,
        "changes": update_data
    })
    
    return {"task": updated_task, "message": "Task updated successfully"}

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task"""
    task = db.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_name = task['name']
    
    # Log before deleting
    log_action("DELETE", task_id, task_name, task)
    
    # Delete the task (CASCADE will handle subtasks)
    db.delete_task(task_id)
    
    return {"message": "Task deleted successfully"}

@app.post("/api/tasks/{parent_id}/subtask")
async def create_subtask(parent_id: str, task_data: TaskCreate):
    """Create a new subtask under a parent task"""
    parent_task = db.get_task_by_id(parent_id)
    if not parent_task:
        raise HTTPException(status_code=404, detail="Parent task not found")
    
    if parent_task['is_milestone']:
        raise HTTPException(status_code=400, detail="Cannot create subtasks under milestones")
    
    task_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    valid_dependencies = validate_dependencies(task_id, task_data.dependencies)
    default_color = "#666666" if task_data.is_milestone else "#4285f4"
    
    task_dict = {
        'id': task_id,
        'name': task_data.name,
        'start_date': task_data.start_date,
        'end_date': task_data.end_date,
        'progress': task_data.progress,
        'color': task_data.color if task_data.color != "#4285f4" else default_color,
        'dependencies': valid_dependencies,
        'is_milestone': task_data.is_milestone,
        'parent_id': parent_id,
        'description': task_data.description,
        'assigned_to': task_data.assigned_to,
        'priority': task_data.priority,
        'created_at': now,
        'updated_at': now
    }
    
    db.create_task(task_dict)
    log_action("CREATE_SUBTASK", task_id, task_data.name, {
        **task_dict,
        "parent_task_name": parent_task['name']
    })
    
    return {"task": task_dict, "message": f"Subtask created under '{parent_task['name']}'"}

@app.put("/api/tasks/{task_id}/promote")
async def promote_to_parent_task(task_id: str):
    """Promote a subtask to become a parent task"""
    task = db.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    old_parent_id = task['parent_id']
    if not old_parent_id:
        raise HTTPException(status_code=400, detail="Task is already a parent task")
    
    updated_task = db.update_task(task_id, {'parent_id': None})
    
    log_action("PROMOTE_TASK", task_id, updated_task['name'], {
        "old_parent_id": old_parent_id,
        "action": "promoted_to_parent"
    })
    
    return {"task": updated_task, "message": "Task promoted to parent task"}

@app.get("/api/tasks/{task_id}/subtasks")
async def get_subtasks(task_id: str):
    """Get all subtasks for a given parent task"""
    if not db.get_task_by_id(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    subtasks = db.get_subtasks(task_id)
    return {"subtasks": subtasks, "count": len(subtasks)}

@app.post("/api/tasks/{task_id}/duplicate")
async def duplicate_task(task_id: str):
    """Duplicate an existing task"""
    original_task = db.get_task_by_id(task_id)
    if not original_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    new_task_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    duplicate_data = original_task.copy()
    duplicate_data.update({
        'id': new_task_id,
        'name': f"{original_task['name']} (Copy)",
        'progress': 0.0,
        'dependencies': [],
        'created_at': now,
        'updated_at': now
    })
    
    db.create_task(duplicate_data)
    log_action("DUPLICATE", new_task_id, duplicate_data['name'], {
        "original_task_id": task_id,
        "original_task_name": original_task['name']
    })
    
    return {"task": duplicate_data, "message": "Task duplicated successfully"}

@app.get("/api/logs")
async def get_logs(limit: int = 50):
    """Get recent action logs"""
    logs = db.get_logs(limit)
    return {"logs": logs}

@app.get("/api/logs/task/{task_id}")
async def get_task_logs(task_id: str):
    """Get logs for a specific task"""
    task_logs = db.get_task_logs(task_id)
    return {"logs": task_logs}

@app.get("/api/analytics")
async def get_analytics():
    """Get project analytics and statistics"""
    tasks_list = db.get_all_tasks()
    
    if not tasks_list:
        return {"message": "No tasks available for analytics"}
    
    total_tasks = len(tasks_list)
    completed_tasks = len([t for t in tasks_list if t['progress'] >= 100])
    in_progress_tasks = len([t for t in tasks_list if 0 < t['progress'] < 100])
    not_started_tasks = len([t for t in tasks_list if t['progress'] == 0])
    milestones = len([t for t in tasks_list if t['is_milestone']])
    
    avg_progress = sum(t['progress'] for t in tasks_list) / total_tasks
    
    priority_dist = {}
    for task in tasks_list:
        priority_dist[task['priority']] = priority_dist.get(task['priority'], 0) + 1
    
    tasks_by_month = {}
    for task in tasks_list:
        month = task['created_at'][:7]
        tasks_by_month[month] = tasks_by_month.get(month, 0) + 1
    
    critical_path = calculate_critical_path()
    
    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "in_progress_tasks": in_progress_tasks,
        "not_started_tasks": not_started_tasks,
        "milestones": milestones,
        "completion_rate": (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0,
        "average_progress": avg_progress,
        "priority_distribution": priority_dist,
        "tasks_by_month": tasks_by_month,
        "critical_path_length": len(critical_path),
        "critical_path": critical_path
    }

@app.get("/api/settings")
async def get_settings():
    """Get project settings"""
    return db.get_project_settings()

@app.put("/api/settings")
async def update_settings(settings_update: dict):
    """Update project settings"""
    updated_settings = db.update_project_settings(settings_update)
    return {"settings": updated_settings, "message": "Settings updated successfully"}

@app.get("/api/export")
async def export_data(format: str = "json"):
    """Export project data in various formats"""
    if format.lower() == "json":
        tasks = db.get_all_tasks()
        logs = db.get_logs(limit=1000)
        settings = db.get_project_settings()
        
        return {
            "tasks": tasks,
            "logs": logs,
            "settings": settings,
            "exported_at": datetime.now().isoformat()
        }
    else:
        raise HTTPException(status_code=400, detail="Unsupported export format")

@app.post("/api/import")
async def import_data(data: dict):
    """Import project data from JSON"""
    try:
        # Import tasks
        if 'tasks' in data:
            for task in data['tasks']:
                # Check if task already exists
                existing = db.get_task_by_id(task['id'])
                if not existing:
                    db.create_task(task)
        
        # Import logs
        if 'logs' in data:
            for log in data['logs']:
                db.create_log(log)
        
        # Import settings
        if 'settings' in data:
            db.update_project_settings(data['settings'])
        
        return {"message": "Data imported successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")

@app.delete("/api/logs/cleanup")
async def cleanup_logs(days: int = 90):
    """Delete logs older than specified days"""
    deleted = db.cleanup_old_logs(days)
    return {"message": f"Deleted {deleted} old log entries"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    tasks_count = len(db.get_all_tasks())
    logs_count = len(db.get_logs(limit=10000))
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "sqlite",
        "tasks_count": tasks_count,
        "logs_count": logs_count
    }

@app.get("/api/database/stats")
async def database_stats():
    """Get database statistics"""
    import os
    
    db_size = 0
    if os.path.exists(db.DATABASE_FILE):
        db_size = os.path.getsize(db.DATABASE_FILE)
    
    tasks_count = len(db.get_all_tasks())
    logs_count = len(db.get_logs(limit=10000))
    
    return {
        "database_file": db.DATABASE_FILE,
        "database_size_bytes": db_size,
        "database_size_mb": round(db_size / (1024 * 1024), 2),
        "total_tasks": tasks_count,
        "total_logs": logs_count
    }

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    print("Starting Gantt Chart Application with SQLite...")
    print("Access the application at: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)