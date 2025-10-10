import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict
import os

DATABASE_FILE = "gantt_app.db"

def get_connection():
    """Get a database connection"""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize the database with required tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Projects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            start_date TEXT,
            end_date TEXT,
            color TEXT DEFAULT '#4285f4',
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    # Tasks table - now with project_id
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
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
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
    ''')
    
    # Project notes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_notes (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            note_date TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    ''')
    
    # Action logs table - now with project_id
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS action_logs (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            action TEXT NOT NULL,
            task_id TEXT NOT NULL,
            task_name TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            details TEXT NOT NULL,
            user TEXT DEFAULT 'system',
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_parent_id ON tasks(parent_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_project_id ON action_logs(project_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_task_id ON action_logs(task_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON action_logs(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_notes_project_date ON project_notes(project_id, note_date)')
    
    # Create default project if none exists
    cursor.execute('SELECT COUNT(*) FROM projects')
    if cursor.fetchone()[0] == 0:
        now = datetime.now().isoformat()
        default_project_id = 'default-project-001'
        cursor.execute('''
            INSERT INTO projects (id, name, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (default_project_id, 'My First Project', 'Default project', now, now))
        
        # Migrate any existing tasks to the default project
        cursor.execute('UPDATE tasks SET project_id = ? WHERE project_id IS NULL', (default_project_id,))
        cursor.execute('UPDATE action_logs SET project_id = ? WHERE project_id IS NULL', (default_project_id,))
    
    conn.commit()
    conn.close()
    
    print(f"✓ Database initialized: {DATABASE_FILE}")

# Project operations
def create_project(project_data: Dict) -> Dict:
    """Create a new project"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO projects (id, name, description, start_date, end_date, color, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        project_data['id'],
        project_data['name'],
        project_data.get('description'),
        project_data.get('start_date'),
        project_data.get('end_date'),
        project_data.get('color', '#4285f4'),
        project_data['created_at'],
        project_data['updated_at']
    ))
    
    conn.commit()
    conn.close()
    return project_data

def get_project_by_id(project_id: str) -> Optional[Dict]:
    """Get a single project by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_all_projects() -> List[Dict]:
    """Get all projects"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM projects ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_active_project() -> Optional[Dict]:
    """Get the currently active project"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM projects WHERE is_active = 1 LIMIT 1')
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def set_active_project(project_id: str) -> bool:
    """Set a project as active"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Deactivate all projects
    cursor.execute('UPDATE projects SET is_active = 0')
    # Activate the selected project
    cursor.execute('UPDATE projects SET is_active = 1 WHERE id = ?', (project_id,))
    
    conn.commit()
    affected = cursor.rowcount > 0
    conn.close()
    return affected

def update_project(project_id: str, updates: Dict) -> Optional[Dict]:
    """Update a project"""
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
    values.append(project_id)
    
    query = f"UPDATE projects SET {', '.join(set_clause)} WHERE id = ?"
    cursor.execute(query, values)
    
    conn.commit()
    conn.close()
    
    return get_project_by_id(project_id)

def delete_project(project_id: str) -> bool:
    """Delete a project and all its associated data"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
    
    conn.commit()
    affected = cursor.rowcount > 0
    conn.close()
    return affected

# Project notes operations
def create_note(note_data: Dict) -> Dict:
    """Create a new project note"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO project_notes (id, project_id, note_date, content, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        note_data['id'],
        note_data['project_id'],
        note_data['note_date'],
        note_data['content'],
        note_data['created_at'],
        note_data['updated_at']
    ))
    
    conn.commit()
    conn.close()
    return note_data

def get_note_by_date(project_id: str, note_date: str) -> Optional[Dict]:
    """Get a note for a specific project and date"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM project_notes 
        WHERE project_id = ? AND note_date = ?
    ''', (project_id, note_date))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_all_notes_for_project(project_id: str) -> List[Dict]:
    """Get all notes for a project"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM project_notes 
        WHERE project_id = ?
        ORDER BY note_date DESC
    ''', (project_id,))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def update_note(note_id: str, updates: Dict) -> Optional[Dict]:
    """Update a project note"""
    conn = get_connection()
    cursor = conn.cursor()
    
    set_clause = []
    values = []
    
    for key, value in updates.items():
        if key not in ['id', 'project_id', 'created_at']:
            set_clause.append(f"{key} = ?")
            values.append(value)
    
    set_clause.append("updated_at = ?")
    values.append(datetime.now().isoformat())
    values.append(note_id)
    
    query = f"UPDATE project_notes SET {', '.join(set_clause)} WHERE id = ?"
    cursor.execute(query, values)
    
    conn.commit()
    conn.close()
    
    cursor.execute('SELECT * FROM project_notes WHERE id = ?', (note_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

def delete_note(note_id: str) -> bool:
    """Delete a project note"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM project_notes WHERE id = ?', (note_id,))
    
    conn.commit()
    affected = cursor.rowcount > 0
    conn.close()
    return affected

# Task operations (updated to include project_id)
def create_task(task_data: Dict) -> Dict:
    """Create a new task in the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO tasks (
            id, project_id, name, start_date, end_date, progress, color, dependencies,
            is_milestone, parent_id, description, assigned_to, priority,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        task_data['id'],
        task_data['project_id'],
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

def get_all_tasks(project_id: str = None) -> List[Dict]:
    """Get all tasks, optionally filtered by project"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if project_id:
        cursor.execute('SELECT * FROM tasks WHERE project_id = ? ORDER BY created_at', (project_id,))
    else:
        cursor.execute('SELECT * FROM tasks ORDER BY created_at')
    
    rows = cursor.fetchall()
    conn.close()
    
    return [row_to_task_dict(row) for row in rows]

def update_task(task_id: str, updates: Dict) -> Optional[Dict]:
    """Update a task in the database"""
    conn = get_connection()
    cursor = conn.cursor()
    
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
    
    def get_all_subtask_ids(parent_id):
        cursor.execute('SELECT id FROM tasks WHERE parent_id = ?', (parent_id,))
        subtask_ids = [row['id'] for row in cursor.fetchall()]
        all_ids = subtask_ids.copy()
        for subtask_id in subtask_ids:
            all_ids.extend(get_all_subtask_ids(subtask_id))
        return all_ids
    
    task_ids_to_delete = [task_id] + get_all_subtask_ids(task_id)
    
    cursor.execute('SELECT id, dependencies FROM tasks')
    for row in cursor.fetchall():
        deps = json.loads(row['dependencies'])
        updated_deps = [d for d in deps if d not in task_ids_to_delete]
        if len(updated_deps) != len(deps):
            cursor.execute('UPDATE tasks SET dependencies = ? WHERE id = ?',
                         (json.dumps(updated_deps), row['id']))
    
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

# Action log operations (updated to include project_id)
def create_log(log_data: Dict) -> Dict:
    """Create a new action log entry"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO action_logs (id, project_id, action, task_id, task_name, timestamp, details, user)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        log_data['id'],
        log_data['project_id'],
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

def get_logs(project_id: str = None, limit: int = 50) -> List[Dict]:
    """Get recent action logs, optionally filtered by project"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if project_id:
        cursor.execute('''
            SELECT * FROM action_logs 
            WHERE project_id = ?
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (project_id, limit))
    else:
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

# Helper functions
def row_to_task_dict(row) -> Dict:
    """Convert a database row to a task dictionary"""
    return {
        'id': row['id'],
        'project_id': row['project_id'],
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
        'project_id': row['project_id'],
        'action': row['action'],
        'task_id': row['task_id'],
        'task_name': row['task_name'],
        'timestamp': row['timestamp'],
        'details': json.loads(row['details']),
        'user': row['user']
    }

if __name__ == "__main__":
    init_database()