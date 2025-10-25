"""
Database Migration Script
Handles schema upgrades for the Gantt Chart application
"""
import sqlite3
import os
from datetime import datetime

DATABASE_FILE = "gantt_app.db"
MIGRATION_VERSION = 2  # Current migration version

def get_connection():
    """Get a database connection"""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_current_version():
    """Get the current database schema version"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return row['version'] if row else 0
    except sqlite3.OperationalError:
        conn.close()
        return 0

def create_version_table():
    """Create the schema version tracking table"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def apply_migration(version, description, migration_sql):
    """Apply a migration and record it"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print(f"Applying migration v{version}: {description}")
    
    try:
        # Execute migration
        for statement in migration_sql.split(';'):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        
        # Record migration
        cursor.execute('''
            INSERT INTO schema_version (version, description, applied_at)
            VALUES (?, ?, ?)
        ''', (version, description, datetime.now().isoformat()))
        
        conn.commit()
        print(f"✓ Migration v{version} applied successfully")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Migration v{version} failed: {e}")
        return False
    finally:
        conn.close()

def migration_v1():
    """Migration v1: Add weekly planner tables"""
    description = "Add weekly planner and xlsx storage tables"
    
    migration_sql = '''
        CREATE TABLE IF NOT EXISTS weekly_planners (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            week_start_date TEXT NOT NULL,
            week_end_date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        
        CREATE TABLE IF NOT EXISTS time_blocks (
            id TEXT PRIMARY KEY,
            planner_id TEXT NOT NULL,
            day_index INTEGER NOT NULL,
            time_slot TEXT NOT NULL,
            title TEXT,
            description TEXT,
            color TEXT DEFAULT '#4285f4',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (planner_id) REFERENCES weekly_planners(id) ON DELETE CASCADE
        );
        
        CREATE TABLE IF NOT EXISTS xlsx_files (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            filename TEXT NOT NULL,
            file_data BLOB NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        
        CREATE INDEX IF NOT EXISTS idx_planners_project ON weekly_planners(project_id);
        CREATE INDEX IF NOT EXISTS idx_planners_dates ON weekly_planners(week_start_date, week_end_date);
        CREATE INDEX IF NOT EXISTS idx_blocks_planner ON time_blocks(planner_id);
        CREATE INDEX IF NOT EXISTS idx_blocks_day_time ON time_blocks(day_index, time_slot);
        CREATE INDEX IF NOT EXISTS idx_xlsx_project ON xlsx_files(project_id)
    '''
    
    return apply_migration(1, description, migration_sql)

def migration_v2():
    """Migration v2: Add custom rows/columns support"""
    description = "Add support for custom rows and columns in weekly planner"
    
    migration_sql = '''
        ALTER TABLE weekly_planners ADD COLUMN custom_rows TEXT DEFAULT '[]';
        ALTER TABLE weekly_planners ADD COLUMN custom_columns TEXT DEFAULT '[]'
    '''
    
    return apply_migration(2, description, migration_sql)

def run_migrations():
    """Run all pending migrations"""
    if not os.path.exists(DATABASE_FILE):
        print(f"✗ Database file {DATABASE_FILE} not found")
        print("Please run the application first to initialize the database")
        return False
    
    create_version_table()
    current_version = get_current_version()
    
    print(f"Current database version: v{current_version}")
    print(f"Target version: v{MIGRATION_VERSION}")
    
    if current_version >= MIGRATION_VERSION:
        print("✓ Database is up to date")
        return True
    
    migrations = [
        (1, migration_v1),
        (2, migration_v2)
    ]
    
    success = True
    for version, migration_func in migrations:
        if version > current_version:
            if not migration_func():
                success = False
                break
    
    if success:
        print(f"\n✓ All migrations completed successfully")
        print(f"Database is now at version v{MIGRATION_VERSION}")
    else:
        print(f"\n✗ Migration failed. Database is at version v{get_current_version()}")
    
    return success

if __name__ == "__main__":
    print("=" * 60)
    print("Gantt Chart Application - Database Migration")
    print("=" * 60)
    print()
    run_migrations()