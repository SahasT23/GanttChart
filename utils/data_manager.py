"""
Data persistence and management utilities
"""

import json
import os
from typing import Optional
from datetime import datetime
import shutil

from models.task import Project

class DataManager:
    """Handles saving and loading project data"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.default_file = os.path.join(data_dir, "default_project.json")
        self.backup_dir = os.path.join(data_dir, "backups")
        
        # Create directories if they don't exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def save_project(self, project: Project, file_path: str = None) -> bool:
        """Save project to JSON file"""
        try:
            if file_path is None:
                file_path = self.default_file
            
            # Create backup if file exists
            if os.path.exists(file_path):
                self.create_backup(file_path)
            
            # Save project
            data = project.to_dict()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error saving project: {e}")
            return False
    
    def load_project(self, file_path: str = None) -> Optional[Project]:
        """Load project from JSON file"""
        try:
            if file_path is None:
                file_path = self.default_file
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return Project.from_dict(data)
            
        except Exception as e:
            print(f"Error loading project: {e}")
            return None
    
    def create_backup(self, file_path: str):
        """Create a timestamped backup of the file"""
        try:
            if os.path.exists(file_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.basename(file_path)
                name, ext = os.path.splitext(filename)
                backup_name = f"{name}_backup_{timestamp}{ext}"
                backup_path = os.path.join(self.backup_dir, backup_name)
                
                shutil.copy2(file_path, backup_path)
                
                # Keep only the last 10 backups
                self.cleanup_old_backups()
                
        except Exception as e:
            print(f"Error creating backup: {e}")
    
    def cleanup_old_backups(self, max_backups: int = 10):
        """Remove old backup files, keeping only the most recent ones"""
        try:
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.endswith('.json') and '_backup_' in file:
                    file_path = os.path.join(self.backup_dir, file)
                    backup_files.append((file_path, os.path.getmtime(file_path)))
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Remove excess backups
            for file_path, _ in backup_files[max_backups:]:
                os.remove(file_path)
                
        except Exception as e:
            print(f"Error cleaning up backups: {e}")
    
    def get_recent_projects(self, max_count: int = 5) -> list:
        """Get list of recent project files"""
        try:
            project_files = []
            
            # Check data directory for JSON files
            if os.path.exists(self.data_dir):
                for file in os.listdir(self.data_dir):
                    if file.endswith('.json') and not file.startswith('_'):
                        file_path = os.path.join(self.data_dir, file)
                        project_files.append((file_path, os.path.getmtime(file_path)))
            
            # Sort by modification time (newest first) and limit
            project_files.sort(key=lambda x: x[1], reverse=True)
            return [file_path for file_path, _ in project_files[:max_count]]
            
        except Exception as e:
            print(f"Error getting recent projects: {e}")
            return []
    
    def export_to_csv(self, project: Project, file_path: str) -> bool:
        """Export project tasks to CSV format"""
        try:
            import csv
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Task ID', 'Task Name', 'Start Date', 'End Date', 'Duration', 
                             'Progress', 'Assignee', 'Priority', 'Dependencies', 'Notes']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for task in project.get_tasks_sorted_by_date():
                    writer.writerow({
                        'Task ID': task.task_id,
                        'Task Name': task.name,
                        'Start Date': task.start_date.strftime('%Y-%m-%d'),
                        'End Date': task.end_date.strftime('%Y-%m-%d'),
                        'Duration': task.duration,
                        'Progress': f"{task.progress}%",
                        'Assignee': task.assignee,
                        'Priority': task.priority,
                        'Dependencies': ', '.join(task.dependencies),
                        'Notes': task.notes
                    })
            
            return True
            
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False
    
    def import_from_csv(self, file_path: str) -> Optional[Project]:
        """Import project from CSV format"""
        try:
            import csv
            from models.task import Task, TaskType
            
            project = Project("Imported Project")
            
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    task = Task(
                        task_id=row.get('Task ID', ''),
                        name=row['Task Name'],
                        start_date=datetime.strptime(row['Start Date'], '%Y-%m-%d'),
                        duration=int(row.get('Duration', 1)),
                        progress=float(row.get('Progress', '0%').replace('%', '')),
                        assignee=row.get('Assignee', ''),
                        priority=row.get('Priority', 'Normal'),
                        dependencies=row.get('Dependencies', '').split(', ') if row.get('Dependencies') else [],
                        notes=row.get('Notes', '')
                    )
                    project.add_task(task)
            
            return project
            
        except Exception as e:
            print(f"Error importing from CSV: {e}")
            return None

class AutoSaveManager:
    """Handles automatic saving of project data"""
    
    def __init__(self, data_manager: DataManager, interval_ms: int = 30000):
        self.data_manager = data_manager
        self.interval_ms = interval_ms
        self.project = None
        self.root = None
        self.auto_save_id = None
        self.is_enabled = True
    
    def start_auto_save(self, root, project: Project):
        """Start the auto-save timer"""
        self.root = root
        self.project = project
        self.schedule_next_save()
    
    def stop_auto_save(self):
        """Stop the auto-save timer"""
        if self.auto_save_id:
            self.root.after_cancel(self.auto_save_id)
            self.auto_save_id = None
    
    def schedule_next_save(self):
        """Schedule the next auto-save"""
        if self.is_enabled and self.root and self.project:
            self.auto_save_id = self.root.after(self.interval_ms, self.perform_auto_save)
    
    def perform_auto_save(self):
        """Perform the auto-save operation"""
        if self.project and len(self.project.tasks) > 0:
            self.data_manager.save_project(self.project)
        
        # Schedule next save
        self.schedule_next_save()
    
    def enable_auto_save(self, enabled: bool):
        """Enable or disable auto-save"""
        self.is_enabled = enabled
        if not enabled:
            self.stop_auto_save()
        elif self.root and self.project:
            self.schedule_next_save()