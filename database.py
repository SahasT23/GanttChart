import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict
import os

DATABASE_FILE = "gantt_app.db"

def get_connection():
    """Get a database connection"""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def init_database():
    """Initialize the database with required tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            progress REAL DEFAULT 0.0,
            color TEXT DEFAULT '#4285f4',
            dependencies TEXT DEFAULT '[]',
            is_milestone INTEGER DEFAULT 0,
            parent_id TEXT,
            description TEXT,
            assigned_to TEXT,
            priority TEXT DEFAULT 'medium',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (parent_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
    ''')
    
    # Action logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS action_logs (
            id TEXT PRIMARY KEY,
            action TEXT NOT NULL,
            task_id TEXT NOT NULL,
            task_name TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            details TEXT NOT NULL,
            user TEXT DEFAULT 'system',
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
    ''')
    
    # Project settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT DEFAULT 'My Project',
            start_date TEXT,
            end_date TEXT,
            description TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_parent_id ON tasks(parent_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_task_id ON action_logs(task_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON action_logs(timestamp)')
    
    # Insert default project settings if not exists
    cursor.execute('SELECT COUNT(*) FROM project_settings')
    if cursor.fetchone()[0] == 0:
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO project_settings (id, name, created_at, updated_at)
            VALUES (1, 'My Project', ?, ?)
        ''', (now, now))
    
    conn.commit()
    conn.close()
    
    print(f"✓ Database initialized: {DATABASE_FILE}")

# Task operations
def create_task(task_data: Dict) -> Dict:
    """Create a new task in the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO tasks (
            id, name, start_date, end_date, progress, color, dependencies,
            is_milestone, parent_id, description, assigned_to, priority,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        task_data['id'],
        task_data['name'],
        task_data['start_date'],
        task_data['end_date'],
        task_data['progress'],
        task_data['color'],
        json.dumps(task_data['dependencies']),
        1 if task_data['is_milestone'] else 0,
        task_data.get('parent_id'),
        task_data.get('description'),
        task_data.get('assigned_to'),
        task_data['priority'],
        task_data['created_at'],
        task_data['updated_at']
    ))
    
    conn.commit()
    conn.close()
    
    return task_data

def get_task_by_id(task_id: str) -> Optional[Dict]:
    """Get a single task by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row_to_task_dict(row)
    return None

def get_all_tasks() -> List[Dict]:
    """Get all tasks from the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM tasks ORDER BY created_at')
    rows = cursor.fetchall()
    conn.close()
    
    return [row_to_task_dict(row) for row in rows]

def update_task(task_id: str, updates: Dict) -> Optional[Dict]:
    """Update a task in the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Build the update query dynamically
    set_clause = []
    values = []
    
    for key, value in updates.items():
        if key == 'dependencies':
            set_clause.append(f"{key} = ?")
            values.append(json.dumps(value))
        elif key == 'is_milestone':
            set_clause.append(f"{key} = ?")
            values.append(1 if value else 0)
        else:
            set_clause.append(f"{key} = ?")
            values.append(value)
    
    # Always update the updated_at timestamp
    set_clause.append("updated_at = ?")
    values.append(datetime.now().isoformat())
    
    values.append(task_id)
    
    query = f"UPDATE tasks SET {', '.join(set_clause)} WHERE id = ?"
    cursor.execute(query, values)
    
    conn.commit()
    conn.close()
    
    return get_task_by_id(task_id)

def delete_task(task_id: str) -> bool:
    """Delete a task and its subtasks from the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get all subtasks recursively
    def get_all_subtask_ids(parent_id):
        cursor.execute('SELECT id FROM tasks WHERE parent_id = ?', (parent_id,))
        subtask_ids = [row['id'] for row in cursor.fetchall()]
        all_ids = subtask_ids.copy()
        for subtask_id in subtask_ids:
            all_ids.extend(get_all_subtask_ids(subtask_id))
        return all_ids
    
    # Get all tasks to delete (task + all subtasks)
    task_ids_to_delete = [task_id] + get_all_subtask_ids(task_id)
    
    # Remove dependencies from other tasks
    cursor.execute('SELECT id, dependencies FROM tasks')
    for row in cursor.fetchall():
        deps = json.loads(row['dependencies'])
        updated_deps = [d for d in deps if d not in task_ids_to_delete]
        if len(updated_deps) != len(deps):
            cursor.execute('UPDATE tasks SET dependencies = ? WHERE id = ?',
                         (json.dumps(updated_deps), row['id']))
    
    # Delete the tasks
    placeholders = ','.join('?' * len(task_ids_to_delete))
    cursor.execute(f'DELETE FROM tasks WHERE id IN ({placeholders})', task_ids_to_delete)
    
    conn.commit()
    affected = cursor.rowcount > 0
    conn.close()
    
    return affected

def get_subtasks(parent_id: str) -> List[Dict]:
    """Get all direct subtasks of a parent task"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM tasks WHERE parent_id = ? ORDER BY created_at', (parent_id,))
    rows = cursor.fetchall()
    conn.close()
    
    return [row_to_task_dict(row) for row in rows]

# Action log operations
def create_log(log_data: Dict) -> Dict:
    """Create a new action log entry"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO action_logs (id, action, task_id, task_name, timestamp, details, user)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        log_data['id'],
        log_data['action'],
        log_data['task_id'],
        log_data['task_name'],
        log_data['timestamp'],
        json.dumps(log_data['details']),
        log_data.get('user', 'system')
    ))
    
    conn.commit()
    conn.close()
    
    return log_data

def get_logs(limit: int = 50) -> List[Dict]:
    """Get recent action logs"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM action_logs 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    return [row_to_log_dict(row) for row in reversed(rows)]

def get_task_logs(task_id: str) -> List[Dict]:
    """Get all logs for a specific task"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM action_logs 
        WHERE task_id = ? 
        ORDER BY timestamp DESC
    ''', (task_id,))
    rows = cursor.fetchall()
    conn.close()
    
    return [row_to_log_dict(row) for row in rows]

def cleanup_old_logs(days: int = 90):
    """Delete logs older than specified days"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
    cutoff_iso = datetime.fromtimestamp(cutoff_date).isoformat()
    
    cursor.execute('DELETE FROM action_logs WHERE timestamp < ?', (cutoff_iso,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    
    return deleted

# Project settings operations
def get_project_settings() -> Dict:
    """Get project settings"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM project_settings WHERE id = 1')
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'name': row['name'],
            'start_date': row['start_date'],
            'end_date': row['end_date'],
            'description': row['description'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }
    return {}

def update_project_settings(updates: Dict) -> Dict:
    """Update project settings"""
    conn = get_connection()
    cursor = conn.cursor()
    
    set_clause = []
    values = []
    
    for key, value in updates.items():
        if key not in ['id', 'created_at']:
            set_clause.append(f"{key} = ?")
            values.append(value)
    
    set_clause.append("updated_at = ?")
    values.append(datetime.now().isoformat())
    
    query = f"UPDATE project_settings SET {', '.join(set_clause)} WHERE id = 1"
    cursor.execute(query, values)
    
    conn.commit()
    conn.close()
    
    return get_project_settings()

# Helper functions
def row_to_task_dict(row) -> Dict:
    """Convert a database row to a task dictionary"""
    return {
        'id': row['id'],
        'name': row['name'],
        'start_date': row['start_date'],
        'end_date': row['end_date'],
        'progress': row['progress'],
        'color': row['color'],
        'dependencies': json.loads(row['dependencies']),
        'is_milestone': bool(row['is_milestone']),
        'parent_id': row['parent_id'],
        'description': row['description'],
        'assigned_to': row['assigned_to'],
        'priority': row['priority'],
        'created_at': row['created_at'],
        'updated_at': row['updated_at']
    }

def row_to_log_dict(row) -> Dict:
    """Convert a database row to a log dictionary"""
    return {
        'id': row['id'],
        'action': row['action'],
        'task_id': row['task_id'],
        'task_name': row['task_name'],
        'timestamp': row['timestamp'],
        'details': json.loads(row['details']),
        'user': row['user']
    }

# Migration function (optional - to migrate from JSON to SQLite)
def migrate_from_json():
    """Migrate data from JSON files to SQLite"""
    if not os.path.exists('gantt_data.json'):
        print("No JSON files to migrate")
        return
    
    print("Migrating data from JSON to SQLite...")
    
    # Load JSON data
    with open('gantt_data.json', 'r') as f:
        data = json.load(f)
        tasks = data.get('tasks', {})
    
    # Migrate tasks
    for task_id, task_data in tasks.items():
        create_task(task_data)
        print(f"  Migrated task: {task_data['name']}")
    
    # Migrate logs if they exist
    if os.path.exists('gantt_logs.json'):
        with open('gantt_logs.json', 'r') as f:
            logs_data = json.load(f)
            logs = logs_data.get('logs', [])
        
        for log in logs:
            create_log(log)
        print(f"  Migrated {len(logs)} log entries")
    
    # Migrate settings if they exist
    if os.path.exists('project_settings.json'):
        with open('project_settings.json', 'r') as f:
            settings = json.load(f)
            update_project_settings(settings)
        print(f"  Migrated project settings")
    
    print("✓ Migration complete!")
    print("  You can now delete the JSON files if desired")

if __name__ == "__main__":
    # Initialize database when run directly
    init_database()
    
    # Optionally migrate from JSON
    if os.path.exists('gantt_data.json'):
        migrate = input("JSON files found. Migrate to SQLite? (y/n): ")
        if migrate.lower() == 'y':
            migrate_from_json()